"""Read the plotted values off the published figures (PMC open-access JPEGs, 600 px wide).

Bar charts (Figs 1, 2, 4, 5): the y axis is calibrated from its tick marks alone (a least-squares
line through the tick rows and the printed tick labels); bar edges are found as the grey outline
columns just above the baseline and fitted to R's barplot layout (groups of G bars of equal width,
one bar width between groups); each bar's value is the row of its top outline (the topmost row
where the outline runs across the bar), and an error bar's half-length is the distance from the
bar top to the topmost black pixel of the whisker above it.

Curves (Figs 3, 6): each panel's axes are calibrated from its tick marks, and each series is the set
of pixels of its colour inside the panel; for every x pixel column the curve value is the mean row
of the series pixels in that column (see curves()).

  read_published.py SOURCES_DIR OUT.json
"""

import json
import sys

import numpy as np
from PIL import Image

# Printed tick labels and layouts, read from the figures
BAR_FIGURES = {
    "fig1": {"file": "1471-2105-10-78-1.jpg", "ticks": [0.0, 0.5, 1.0, 1.5, 2.0], "groups": 5, "per_group": 8,
             "errors": True, "group_labels": ["0", "1", "2", "3", "4"], "masks": [(90, 340, 70)],
             "series": ["RF0:IM0 n", "RF0:IM0 r", "RF1:IM0 n", "RF1:IM0 r",
                        "RF0:IM1 n", "RF0:IM1 r", "RF1:IM1 n", "RF1:IM1 r"]},
    "fig2": {"file": "1471-2105-10-78-2.jpg", "ticks": [0.0, 0.2, 0.4, 0.6, 0.8, 1.0], "groups": 5, "per_group": 8,
             "errors": False, "group_labels": ["0", "1", "2", "3", "4"], "masks": [(90, 340, 70)],
             "series": ["RF0:IM0 n", "RF0:IM0 r", "RF1:IM0 n", "RF1:IM0 r",
                        "RF0:IM1 n", "RF0:IM1 r", "RF1:IM1 n", "RF1:IM1 r"]},
    "fig4": {"file": "1471-2105-10-78-4.jpg", "ticks": [0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4], "groups": 11,
             "per_group": 3, "errors": True, "group_labels": [f"{0.1 * i:.1f}" for i in range(11)],
             "masks": [(465, 600, 82)],
             "series": ["rSNP", "rHAP", "PRED.rHAP"]},
    "fig5": {"file": "1471-2105-10-78-5.jpg", "ticks": [0.0, 0.2, 0.4, 0.6, 0.8, 1.0], "groups": 11,
             "per_group": 3, "errors": False, "group_labels": [f"{0.1 * i:.1f}" for i in range(11)],
             "masks": [(457, 600, 87)],
             "series": ["rSNP", "rHAP", "PRED.rHAP"]},
}


def load(path):
    return np.asarray(Image.open(path).convert("RGB")).astype(int)


def is_grey_dark(px, level=150):
    mx = px.max(axis=-1)
    mn = px.min(axis=-1)
    return (mx - mn < 70) & (px.mean(axis=-1) < level)


def is_black(px, level=100):
    return px.max(axis=-1) < level


def y_axis(img):
    """Column of the y axis line (longest dark vertical run in the left 20%) and its row span."""
    h, w, _ = img.shape
    dark = is_grey_dark(img, 140)
    best = (0, 0, 0, 0)
    for c in range(int(0.2 * w)):
        col = dark[:, c]
        run = start = 0
        for r in range(h):
            if col[r]:
                if run == 0:
                    start = r
                run += 1
                if run > best[0]:
                    best = (run, c, start, r)
            else:
                run = 0
    return best[1], best[2], best[3]


def tick_rows(img, axis_col, top, bottom):
    """Rows of the tick marks: short horizontal dark segments just left of the axis."""
    dark = is_grey_dark(img, 160)
    rows = []
    for r in range(max(top - 3, 0), bottom + 4):
        if dark[r, axis_col - 8:axis_col - 1].sum() >= 6:
            rows.append(r)
    groups = []
    for r in rows:
        if groups and r - groups[-1][-1] <= 1:
            groups[-1].append(r)
        else:
            groups.append([r])
    return [float(np.mean(g)) for g in groups]


def calibrate(rows, labels):
    if len(rows) != len(labels):
        raise ValueError(f"found {len(rows)} ticks for {len(labels)} labels: {rows}")
    rows = np.asarray(rows)[::-1]  # bottom tick (largest row) first, matching ascending labels
    a, b = np.polyfit(labels, rows, 1)  # row = a*value + b
    resid = rows - (a * np.asarray(labels) + b)
    return a, b, float(np.max(np.abs(resid)))


def bar_layout(img, baseline, groups, per_group, x_lo, x_hi):
    """Fit R barplot's layout (edges at u = 1 + g*(G+1) + j) to the outline columns above the baseline."""
    r = int(round(baseline)) - 4
    row = img[r]
    cols = [c for c in range(x_lo, x_hi) if is_grey_dark(row[c:c + 1], 150)[0]]
    lines = []
    for c in cols:
        if lines and c - lines[-1][-1] <= 1:
            lines[-1].append(c)
        else:
            lines.append([c])
    xs = np.array([np.mean(l) for l in lines])
    edges = np.array([1 + g * (per_group + 1) + j for g in range(groups) for j in range(per_group + 1)], float)
    # bar width from the spacing of neighbouring outlines; offset by trying every outline against
    # every layout edge and keeping the alignment that matches most outlines (zero-height bars
    # have no outline, so the first outline need not be the first edge)
    d = np.diff(xs)
    w = float(np.median(d[(d > 6) & (d < 20)]))
    # The edge grid is uniform (the space between groups is one bar width), so the outlines alone
    # cannot tell a bar from the gap between groups; the gaps are white just above the baseline.
    L = img.mean(axis=2)
    band = slice(int(round(baseline)) - 8, int(round(baseline)) - 2)
    cands = []
    for x in xs:
        for e in edges:
            x0c = x - w * e
            if x0c + w * edges[0] < x_lo - 2 or x0c + w * edges[-1] > x_hi + 2:
                continue
            u = (xs - x0c) / w
            hits = int((np.abs(u - np.round(u)) * w < 1.5).sum())
            gaps = 0
            for g in range(groups - 1):
                gl = x0c + w * (1 + g * (per_group + 1) + per_group)
                cols = np.arange(int(np.ceil(gl + 2)), int(np.floor(gl + w - 2)) + 1)
                cols = cols[(cols >= 0) & (cols < L.shape[1])]
                if cols.size and (L[band, cols] < 230).mean() > 0.2:
                    gaps += 1
            cands.append((hits - 10 * gaps, x0c))
    x0 = max(cands)[1]
    for _ in range(20):
        u = (xs - x0) / w
        idx = np.argmin(np.abs(u[:, None] - edges[None, :]), axis=1)
        keep = np.abs(u - edges[idx]) < 0.25
        A = np.c_[np.ones(keep.sum()), edges[idx[keep]]]
        x0, w = np.linalg.lstsq(A, xs[keep], rcond=None)[0]
    resid = xs[keep] - (x0 + w * edges[idx[keep]])
    return x0, w, float(np.max(np.abs(resid))), int(keep.sum())


def read_bars(path, spec):
    img = load(path)
    axis_col, top, bottom = y_axis(img)
    rows = tick_rows(img, axis_col, top, bottom)
    a, b, tick_resid = calibrate(rows, spec["ticks"])
    baseline = b
    G, P = spec["groups"], spec["per_group"]
    x0, w, xres, nlines = bar_layout(img, baseline, G, P, axis_col + 3, img.shape[1] - 2)
    out = {"file": spec["file"], "axis_col": axis_col, "tick_rows": rows, "row_per_unit": a,
           "baseline_row": baseline, "tick_fit_max_resid_px": tick_resid, "bar_width_px": w,
           "bar_x0_px": x0, "layout_max_resid_px": xres, "outline_columns_matched": nlines,
           "groups": spec["group_labels"], "series": spec["series"], "values": [], "errors": [],
           "masks": [list(m) for m in spec.get("masks", [])],
           "bars_px": []}
    for g in range(G):
        vals, errs = [], []
        for j in range(P):
            u = 1 + g * (P + 1) + j
            xl = x0 + w * u
            xr = xl + w
            xc = (xl + xr) / 2
            span = np.arange(int(np.ceil(xl + 1)), int(np.floor(xr - 1)) + 1)
            r_start = int(top) + 3
            for (mx0, mx1, my1) in spec.get("masks", []):
                if xr > mx0 and xl < mx1:
                    r_start = max(r_start, my1 + 1)
            L = img[:, :, :].mean(axis=2)
            # top outline: the first row (from the top) dark across at least 90% of the bar; an
            # error-bar cap covers about 60% and a dotted gridline much less
            top_row = None
            for r in range(r_start, int(round(baseline)) - 1):
                if (L[r, span] < 170).mean() >= 0.9:
                    top_row = r
                    break
            if top_row is None:
                top_row = baseline
            val = (top_row - baseline) / a
            err = None
            if spec["errors"] and top_row < baseline:
                c = int(round(xc))
                cap = None
                for r in range(r_start, int(top_row)):
                    # a cap: dark at the centre and at least 4 dark pixels in a row around it
                    if L[r, c] < 150 and (L[r, c - 3:c + 4] < 170).sum() >= 4:
                        cap = r
                        break
                if cap is not None:
                    err = (top_row - cap) / -a
            vals.append(round(float(val), 4))
            errs.append(None if err is None else round(float(err), 4))
            out["bars_px"].append([round(float(xl), 2), round(float(xr), 2), int(top_row) if top_row is not None else None])
        out["values"].append(vals)
        out["errors"].append(errs)
    return out


# ---------------------------------------------------------------------------------------------
# Curve figures

# R colour names of the series, read from the legends
RCOL = {"black": (0, 0, 0), "grey": (190, 190, 190), "green": (0, 255, 0), "green4": (0, 139, 0),
        "blue": (0, 0, 255), "darkblue": (0, 0, 139), "purple": (160, 32, 240), "orange": (255, 165, 0),
        "orange4": (139, 90, 0), "darkred": (139, 0, 0), "red": (255, 0, 0)}
F6_COLS = ["black", "grey", "green", "green4", "blue", "darkblue", "purple", "orange", "orange4", "darkred", "red"]

CURVE_FIGURES = {
    "fig3": {"file": "1471-2105-10-78-3.jpg", "rows": [0, 300, 590, 829], "cols": [0, 300, 600],
             "panels": [
                 {"id": "fig3.a.left", "series": ["n0", "r1", "r2", "r3", "r4"], "colours": ["black", "blue", "green", "purple", "red"], "x": [5, 8, 10, 12, 15, 20, 25, 30, 40]},
                 {"id": "fig3.a.right", "series": ["n0", "r1", "r2", "r3", "r4"], "colours": ["black", "blue", "green", "purple", "red"], "x": [5, 8, 10, 12, 15, 20, 25, 30, 40]},
                 {"id": "fig3.b.left", "series": ["n0 rSNPs", "r1 rSNP/LD.rSNPs", "r1 rSNPs"], "colours": ["black", "red", "grey"], "x": [5, 8, 10, 12, 15, 20, 25, 30, 40]},
                 {"id": "fig3.b.right", "series": ["n0 rSNPs", "r4 rSNP/LD.rSNPs", "r4 rSNPs"], "colours": ["black", "red", "grey"], "x": [5, 8, 10, 12, 15, 20, 25, 30, 40]},
                 {"id": "fig3.c.left", "series": ["RF1:IM0", "RF0:IM0", "RF0:IM1", "RF1:IM1", "n0 RF0:IM0"], "colours": ["blue", "green", "red", "purple", "black"], "x": [5, 8, 10, 12, 15, 20, 25, 30, 40]},
                 {"id": "fig3.c.right", "series": ["RF1:IM0", "RF0:IM0", "RF0:IM1", "RF1:IM1", "n0 RF0:IM0"], "colours": ["blue", "green", "red", "purple", "black"], "x": [5, 8, 10, 12, 15, 20, 25, 30, 40]},
             ]},
    "fig6": {"file": "1471-2105-10-78-6.jpg", "rows": [0, 290, 560, 821], "cols": [0, 300, 600],
             "panels": [
                 {"id": "fig6.a.left", "series": [f"r2={0.1 * i:.1f}" for i in range(11)], "colours": F6_COLS,
                  "read": ["r2=0.0", "r2=0.2", "r2=0.4", "r2=0.7", "r2=1.0"], "x": [10, 20, 30, 40, 60, 80]},
                 {"id": "fig6.a.right", "series": [f"r2={0.1 * i:.1f}" for i in range(11)], "colours": F6_COLS,
                  "read": ["r2=0.0", "r2=0.2", "r2=0.4", "r2=0.7", "r2=1.0"], "x": [5, 10, 20, 30, 40, 60]},
                 {"id": "fig6.b.left", "series": [f"r2={0.1 * i:.1f}" for i in range(11)], "colours": F6_COLS,
                  "read": ["r2=0.0", "r2=0.2", "r2=0.4", "r2=0.7", "r2=1.0"], "x": [5, 10, 20, 30, 40, 60, 80]},
                 {"id": "fig6.b.right", "series": [f"r2={0.1 * i:.1f}" for i in range(11)], "colours": F6_COLS,
                  "read": ["r2=0.0", "r2=0.2", "r2=0.4", "r2=0.7", "r2=1.0"], "x": [5, 10, 20, 30, 40, 60, 80]},
                 {"id": "fig6.c.left", "series": ["SNP", "BEST.SNP", "HAP", "PRED.HAP"], "colours": ["black", "red", "blue", "purple"], "x": [5, 10, 20, 30, 40, 50]},
                 {"id": "fig6.c.right", "series": ["SNP", "BEST.SNP", "HAP", "PRED.HAP"], "colours": ["black", "red", "blue", "purple"], "x": [5, 10, 20, 30, 40, 50]},
             ]},
}


def _box(img, r0, r1, c0, c1):
    """Axes box of a panel: the outermost rows and columns of the region that are dark along at
    least half of the box (curves cross the box edges, so the longest line is not enough)."""
    dark = is_grey_dark(img[r0:r1, c0:c1], 170)
    h, w = dark.shape

    def longest(v):
        best = run = 0
        for x in v:
            run = run + 1 if x else 0
            best = max(best, run)
        return best

    row_len = np.array([longest(dark[r]) for r in range(h)])
    col_len = np.array([longest(dark[:, c]) for c in range(w)])
    rows = np.where(row_len >= 0.5 * row_len.max())[0]
    cols = np.where(col_len >= 0.5 * col_len.max())[0]
    return r0 + int(rows.min()), r0 + int(rows.max()), c0 + int(cols.min()), c0 + int(cols.max())


def _runs(mask):
    out = []
    start = None
    for i, v in enumerate(mask):
        if v and start is None:
            start = i
        if not v and start is not None:
            out.append((start, i - 1))
            start = None
    if start is not None:
        out.append((start, len(mask) - 1))
    return out


def _ticks(img, top, bottom, left, right):
    """Tick positions: y ticks are short dark runs just left of the box, x ticks just below it
    (Fig. 6 is a lower-resolution scan, so its 4 px ticks are grey rather than black)."""
    L = img.mean(axis=2)
    ys = [top - 3 + float(np.mean(r)) for r in
          _runs([(L[r, left - 5:left] < 215).sum() >= 3 for r in range(top - 3, bottom + 4)])]
    cols = range(left - 3, min(right + 4, img.shape[1]))
    xs = [left - 3 + float(np.mean(c)) for c in
          _runs([(L[bottom + 1:bottom + 5, c] < 215).sum() >= 3 for c in cols])]
    return ys, xs


def _legend_colours(img, top, bottom, left, right, n):
    """Colours of the n legend entries: the n lowest-placed groups of horizontal colour runs of
    10-30 px inside the box (legend line segments), read top to bottom."""
    sub = img[top + 3:bottom - 3, left + 3:right - 3]
    L = sub.mean(axis=2)
    cand = []
    for r in range(sub.shape[0]):
        ink = L[r] < 235
        for a, b in _runs(ink):
            if 10 <= b - a + 1 <= 30:
                seg = sub[r, a + 2:b - 1]
                if seg.size and np.ptp(seg, axis=0).max() < 70:
                    cand.append((r, a, b, np.median(seg, axis=0)))
    # legend segments line up in one column (same start); keep the most common start
    if not cand:
        return []
    starts = np.array([c[1] for c in cand])
    vals, counts = np.unique(np.round(starts / 3).astype(int), return_counts=True)
    best = vals[np.argmax(counts)]
    rows = [c for c in cand if abs(round(c[1] / 3) - best) <= 1]
    groups = []
    for c in rows:
        if groups and c[0] - groups[-1][-1][0] <= 2:
            groups[-1].append(c)
        else:
            groups.append([c])
    cols = [(int(np.mean([c[0] for c in g])) + top + 3, np.median([c[3] for c in g], axis=0)) for g in groups]
    seg_x = (int(min(c[1] for c in rows)) + left + 3, int(max(c[2] for c in rows)) + left + 3)
    return cols[-n:], seg_x


def read_curve_panel(img, region, spec):
    r0, r1, c0, c1 = region
    top, bottom, left, right = _box(img, r0, r1, c0, c1)
    ys, xs = _ticks(img, top, bottom, left, right)
    y_labels = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    ay, by, yres = calibrate(ys, y_labels)
    x_labels = [100 - 20 * i for i in range(len(xs))][::-1]
    ax_, bx_ = np.polyfit(x_labels, xs, 1)
    xres = float(np.max(np.abs(np.asarray(xs) - (ax_ * np.asarray(x_labels) + bx_))))
    colours = np.array([RCOL[c] for c in spec["colours"]], float)
    # each series' pixels: nearer its colour than any other series' colour or white, and within
    # 40% of that margin (anti-aliased edges of other curves fall outside)
    refs = np.vstack([colours, [255.0, 255.0, 255.0]])
    margin = [0.4 * min(np.linalg.norm(colours[i] - refs[j]) for j in range(len(refs)) if j != i)
              for i in range(len(colours))]
    out = {"id": spec["id"], "box": [top, bottom, left, right], "y_ticks": ys, "x_ticks": xs,
           "x_tick_labels": x_labels, "tick_fit_max_resid_px": max(yres, xres),
           "colours": spec["colours"], "series": spec["series"],
           "x": spec["x"], "values": {}, "px": {"ay": ay, "by": by, "ax": ax_, "bx": bx_}}
    sub = img.astype(float)
    for si, name in enumerate(spec["series"]):
        if name not in spec.get("read", spec["series"]):
            continue
        vals = []
        for X in spec["x"]:
            cx = int(round(ax_ * X + bx_))
            col = sub[top + 2:bottom - 1, cx - 1:cx + 2].reshape(-1, 3)
            rr = np.repeat(np.arange(top + 2, bottom - 1), 3)
            cc = np.tile(np.arange(cx - 1, cx + 2), bottom - 1 - top - 2)
            d = np.linalg.norm(col[:, None, :] - refs[None, :, :], axis=2)
            nearest = np.argmin(d, axis=1)
            hit = (nearest == si) & (d[:, si] < min(70.0, margin[si]))
            # drop pixels within 3 rows of a pixel of a darker series: anti-aliased edges of a
            # dark curve pass for a light grey one
            grey = np.ptp(colours[si]) < 30 and colours[si].sum() > 300
            darker = [j for j in range(len(colours)) if grey and colours[j].sum() < 100]
            if darker and hit.any():
                near_dark = np.zeros(len(col), bool)
                for j in darker:
                    near_dark |= (nearest == j) & (d[:, j] < min(70.0, margin[j]))
                dark_rows = rr[near_dark]
                if dark_rows.size:
                    hit &= np.min(np.abs(rr[:, None] - dark_rows[None, :]), axis=1) > 3
            # the series is the longest vertical run of its pixels in the column (allowing
            # one-pixel gaps); isolated hits are anti-aliasing halos of other curves
            rows_hit = np.unique(rr[hit])
            best = []
            cur = []
            for r_ in rows_hit:
                if cur and r_ - cur[-1] > 1:
                    cur = []
                cur.append(r_)
                if len(cur) > len(best):
                    best = list(cur)
            if len(best) < 2:
                vals.append(None)
                continue
            row = float(np.median(best))
            vals.append(round(float((row - by) / ay), 4))
        # a proportion of replicates cannot fall as X grows: a reading that does is a colour
        # confusion, and the series is not read in this panel
        seen = [v for v in vals if v is not None]
        if any(b < a - 0.03 for a, b in zip(seen, seen[1:])):
            out.setdefault("dropped_non_monotone", {})[name] = vals
            vals = [None] * len(vals)
        out["values"][name] = vals
    return out


def read_curves(path, spec):
    img = load(path)
    out = {"file": spec["file"], "panels": []}
    k = 0
    for i in range(3):
        for j in range(2):
            region = (spec["rows"][i], spec["rows"][i + 1], spec["cols"][j], spec["cols"][j + 1])
            out["panels"].append(read_curve_panel(img, region, spec["panels"][k]))
            k += 1
    return out


def main():
    src, outp = sys.argv[1], sys.argv[2]
    res = {k: read_bars(f"{src}/{v['file']}", v) for k, v in BAR_FIGURES.items()}
    res.update({k: read_curves(f"{src}/{v['file']}", v) for k, v in CURVE_FIGURES.items()})
    json.dump(res, open(outp, "w"), indent=1)
    for k, v in res.items():
        if "panels" in v:
            continue
        print(k, "tick resid", round(v["tick_fit_max_resid_px"], 2), "layout resid", round(v["layout_max_resid_px"], 2),
              "matched", v["outline_columns_matched"], file=sys.stderr)
        for g, vals in zip(v["groups"], v["values"]):
            print("  ", g, vals, file=sys.stderr)


if __name__ == "__main__":
    main()
