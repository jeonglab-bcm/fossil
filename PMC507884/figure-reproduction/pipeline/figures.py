#!/usr/bin/env python3
"""Draw Figs 1-3 of Szabo et al. (2004) from our run on the published pixel grid, overlay them on
the published figures, and score them with negative controls.

  figures.py PUBLISHED_DIR DATA_DIR OUTDIR

PUBLISHED_DIR holds Fig1.png, Fig2.png and Fig3.png (the publisher's vector EPS files rendered at
300 dpi). DATA_DIR holds what analysis.R writes: breast.csv and vandesompele.csv (the data, for
Figs 1 and 2) and fig3_bars.csv (our bias and variance of each gene in each tissue type).

Every map from data to pixels comes from the axes alone: the y map is fitted to the published tick
marks and their printed values, sample columns are the published grid lines (one per sample), and
Fig. 3's bar centres are the published tick marks of the tissue axis. Nothing inside a panel is
fitted. Markers are cut from the published legend, so ours have the published shape, size and
colour. Our figure is the published one with the panel contents removed (each pixel replaced by its
column's median, which is the background: white or a grid line) and our points or bars drawn in.

Scores: each ink pixel inside a panel is labelled by its nearest legend colour (Fig. 3: bar fill or
bar outline). Score one way is the share of published labelled pixels with a pixel of the same
label in ours within 2 px; the other way the reverse; the item's score is the smaller. Controls
are drawn and scored with the same code. Writes fig{1,2,3}_ours.png, fig{1,2,3}_overlay.png and
figures.json.
"""
import csv
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

TOL = 2  # pixels at 300 dpi (0.17 mm)


def load(path):
    return np.asarray(Image.open(path).convert("RGB")).astype(np.int16)


def runs(idx):
    out = []
    for i in idx:
        if out and i == out[-1][1] + 1:
            out[-1][1] = i
        else:
            out.append([i, i])
    return out


def centres(rs):
    return [(a + b) / 2 for a, b in rs]


def grey(a):
    return a.mean(axis=2)


def sat(a):
    return a.max(axis=2) - a.min(axis=2)


def frame_lines(a, axis, frac):
    """Rows (axis=0) or columns (axis=1) where more than frac of the image is dark: frame lines."""
    dark = grey(a) < 90
    s = dark.sum(axis=1 - axis)
    n = a.shape[1 - axis]
    return runs([i for i in range(len(s)) if s[i] > frac * n])


def y_ticks(a, x_from, x_to, y0, y1):
    """Centres of short dark horizontal tick marks in the column band [x_from, x_to) between rows y0, y1."""
    band = grey(a[y0:y1, x_from:x_to]) < 110
    rows = [y0 + i for i in range(band.shape[0]) if band[i].mean() > 0.6]
    return centres(runs(rows))


def x_ticks(a, y_from, y_to, x0, x1):
    band = grey(a[y_from:y_to, x0:x1]) < 110
    cols = [x0 + i for i in range(band.shape[1]) if band[:, i].mean() > 0.6]
    return centres(runs(cols))


def grid_columns(a, box):
    """Centres of the light grey vertical grid lines inside box (x0, y0, x1, y1)."""
    x0, y0, x1, y1 = box
    sub = a[y0 + 3:y1 - 2, x0 + 3:x1 - 2]
    g, s = grey(sub), sat(sub)
    gridlike = (g > 200) & (g < 246) & (s < 14)
    cols = [x0 + 3 + i for i in range(sub.shape[1]) if gridlike[:, i].mean() > 0.5]
    return centres(runs(cols))


def fit_line(px, val):
    """Least squares pixel = a + b * value; returns (a, b, max residual in px)."""
    px, val = np.asarray(px, float), np.asarray(val, float)
    b, a = np.polyfit(val, px, 1)
    return a, b, float(np.max(np.abs(a + b * val - px)))


def background(a, box):
    """The panel without its contents: each interior pixel replaced by its column's median colour."""
    x0, y0, x1, y1 = box
    out = a.copy()
    inner = a[y0 + 2:y1 - 1, x0 + 2:x1 - 1]
    med = np.median(inner, axis=0).astype(np.int16)
    out[y0 + 2:y1 - 1, x0 + 2:x1 - 1] = med[None, :, :]
    return out


def legend_glyphs(a, y0, y1, colours_order):
    """Coloured legend markers between rows y0 and y1, as (mask, colour) templates, in the order
    given by colours_order: a function from the list of (y, x) bbox centres to their order."""
    sub = a[y0:y1]
    m = sat(sub) > 35
    lab = np.zeros(m.shape, int)
    comps = []
    for y, x in zip(*np.nonzero(m)):
        if lab[y, x]:
            continue
        lab[y, x] = len(comps) + 1
        st, pts = [(y, x)], []
        while st:
            cy, cx = st.pop()
            pts.append((cy, cx))
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    yy, xx = cy + dy, cx + dx
                    if 0 <= yy < m.shape[0] and 0 <= xx < m.shape[1] and m[yy, xx] and not lab[yy, xx]:
                        lab[yy, xx] = len(comps) + 1
                        st.append((yy, xx))
        p = np.array(pts)
        if len(p) >= 30:
            comps.append(p)
    glyphs = []
    for p in comps:
        ya, xa, yb, xb = p[:, 0].min() - 2, p[:, 1].min() - 2, p[:, 0].max() + 2, p[:, 1].max() + 2
        crop = sub[ya:yb + 1, xa:xb + 1]
        # Ink of the glyph: anything clearly not white (antialiased edges included).
        mask = (255 - crop.min(axis=2)) > 40
        colour = np.median(sub[p[:, 0], p[:, 1]], axis=0).astype(int)
        glyphs.append({"cy": y0 + (ya + yb) / 2, "cx": (xa + xb) / 2, "mask": mask, "rgb": crop, "colour": colour})
    return [glyphs[i] for i in colours_order([(g["cy"], g["cx"]) for g in glyphs])]


def paste(img, glyph, cx, cy, clip):
    """Paste a legend glyph centred at (cx, cy) inside clip (x0, y0, x1, y1). False if outside."""
    h, w = glyph["mask"].shape
    x0, y0 = int(round(cx - (w - 1) / 2)), int(round(cy - (h - 1) / 2))
    cx0, cy0, cx1, cy1 = clip
    if not (cx0 <= cx <= cx1 and cy0 <= cy <= cy1):
        return False
    for dy in range(h):
        for dx in range(w):
            y, x = y0 + dy, x0 + dx
            if glyph["mask"][dy, dx] and cy0 <= y <= cy1 and cx0 <= x <= cx1:
                img[y, x] = glyph["rgb"][dy, dx]
    return True


def label_map(a, box, colours, max_dist=70):
    """Label each ink pixel inside box by its nearest colour (index), -1 elsewhere."""
    x0, y0, x1, y1 = box
    sub = a[y0 + 3:y1 - 2, x0 + 3:x1 - 2].astype(float)
    ink = sat(sub) > 35
    d = np.stack([np.sqrt(((sub - np.asarray(c, float)) ** 2).sum(axis=2)) for c in colours])
    lab = d.argmin(axis=0)
    lab[~ink | (d.min(axis=0) > max_dist)] = -1
    full = -np.ones(a.shape[:2], int)
    full[y0 + 3:y1 - 2, x0 + 3:x1 - 2] = lab
    return full


def dilate(mask, r):
    out = mask.copy()
    H, W = mask.shape
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy > r * r or (dx == 0 and dy == 0):
                continue
            ys, yd = (slice(dy, H), slice(0, H - dy)) if dy >= 0 else (slice(0, H + dy), slice(-dy, H))
            xs, xd = (slice(dx, W), slice(0, W - dx)) if dx >= 0 else (slice(0, W + dx), slice(-dx, W))
            out[yd, xd] |= mask[ys, xs]
    return out


def two_way(lab_pub, lab_ours, n_labels, exclude=None):
    hit_p = tot_p = hit_o = tot_o = 0
    for k in range(n_labels):
        p, o = lab_pub == k, lab_ours == k
        if exclude is not None:
            p, o = p & ~exclude, o & ~exclude
        hit_p += int((p & dilate(o, TOL)).sum())
        tot_p += int(p.sum())
        hit_o += int((o & dilate(p, TOL)).sum())
        tot_o += int(o.sum())
    return {"published_near_ours": hit_p / tot_p if tot_p else 0.0,
            "ours_near_published": hit_o / tot_o if tot_o else 0.0,
            "published_pixels": tot_p, "our_pixels": tot_o}


def overlay(pub, ours):
    a = Image.fromarray(pub.astype(np.uint8)).convert("L")
    b = Image.fromarray(ours.astype(np.uint8)).convert("L")
    return Image.merge("RGB", (a, b, b))


def read_csv(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------- Figs 1 and 2: points by sample

def point_figure(a, panels, glyphs, columns, values, order):
    """Draw points. panels: list of dicts with box and y map (a, b, log). columns: per panel, list of
    x pixel positions of its samples. values: per panel, array samples x genes (in glyph order),
    already ordered as plotted. order: drawing order of the genes. Returns (image, off-panel count)."""
    img = a.copy()
    for p in panels:
        img = background(img, p["box"])
    off = 0
    for p, xs, V in zip(panels, columns, values):
        x0, y0, x1, y1 = p["box"]
        clip = (x0 + 2, y0 + 2, x1 - 2, y1 - 2)
        for g in order:
            for i, x in enumerate(xs):
                v = V[i, g]
                y = p["a"] + p["b"] * (math.log10(v) if p["log"] else v)
                off += not paste(img, glyphs[g], x, y, clip)
    return img, off


def score_points(a, img, panels, glyphs):
    colours = [g["colour"] for g in glyphs]
    tot = {"published_near_ours": 0, "ours_near_published": 0, "published_pixels": 0, "our_pixels": 0}
    hits_p = hits_o = 0
    for p in panels:
        s = two_way(label_map(a, p["box"], colours), label_map(img, p["box"], colours), len(colours))
        hits_p += s["published_near_ours"] * s["published_pixels"]
        hits_o += s["ours_near_published"] * s["our_pixels"]
        tot["published_pixels"] += s["published_pixels"]
        tot["our_pixels"] += s["our_pixels"]
    tot["published_near_ours"] = hits_p / tot["published_pixels"]
    tot["ours_near_published"] = hits_o / tot["our_pixels"]
    return tot


def fig1(pub_dir, data_dir, out):
    a = load(pub_dir / "Fig1.png")
    rows = read_csv(data_dir / "breast.csv")
    genes = ["ACTB", "GAPD", "MRPL19", "PSMC4", "PUM1", "SF3A1"]   # legend order, left to right
    X = np.array([[float(r[g]) for g in genes] for r in rows])
    hl = frame_lines(a, 0, 0.5)
    vl = frame_lines(a, 1, 0.3)
    assert len(hl) == 4 and len(vl) == 2, (hl, vl)
    xl, xr = vl[0][0], vl[1][1]
    boxes = [(xl, hl[0][1], xr, hl[1][0]), (xl, hl[2][1], xr, hl[3][0])]
    glyphs = legend_glyphs(a, 30, boxes[0][1] - 2, lambda c: sorted(range(len(c)), key=lambda i: c[i][1]))
    assert len(glyphs) == 6
    panels, cal = [], []
    for box, vals, log in ((boxes[0], [2000, 1000, 0], False), (boxes[1], [1000, 100, 10, 1], True)):  # top to bottom
        t = y_ticks(a, box[0] - 22, box[0] - 3, box[1] + 2, box[3] - 1)
        assert len(t) == len(vals), (box, t)
        av, bv, res = fit_line(t, [math.log10(v) if log else v for v in vals])
        panels.append({"box": box, "a": av, "b": bv, "log": log})
        cal.append({"ticks_px": t, "tick_values": vals, "max_residual_px": res})
    cols = grid_columns(a, boxes[0])
    assert len(cols) == len(X), len(cols)

    def order_by(stat):
        return np.argsort(stat, kind="stable")

    def render(V, ordr, glyph_order=range(6), shift=0, scale=1.0):
        xs = cols[shift:] if shift >= 0 else cols[:shift]
        Vo = V[ordr][: len(xs)] if shift >= 0 else V[ordr][-shift:]
        img, off = point_figure(a, panels, glyphs, [xs, xs], [Vo * scale, Vo * scale], list(glyph_order))
        return img, off

    logmean = np.log(X).mean(axis=1)
    ours, off = render(X, order_by(logmean))
    score = score_points(a, ours, panels, glyphs)
    rng = np.random.default_rng(1)
    controls = []
    for name, kind, kw in [
        ("samples in a random order (seed 1)", "wrong_input", dict(V=X, ordr=rng.permutation(len(X)))),
        ("genes swapped in pairs (ACTB-GAPD, MRPL19-PSMC4, PUM1-SF3A1)", "wrong_input",
         dict(V=X[:, [1, 0, 3, 2, 5, 4]], ordr=order_by(logmean))),
        ("samples ordered by the mean of the raw values", "near_miss", dict(V=X, ordr=order_by(X.mean(axis=1)))),
        ("every sample one column to the right", "near_miss", dict(V=X, ordr=order_by(logmean), shift=1)),
        ("values x 1.05", "near_miss", dict(V=X, ordr=order_by(logmean), scale=1.05)),
        ("values x 0.95", "near_miss", dict(V=X, ordr=order_by(logmean), scale=0.95)),
    ]:
        img, _ = render(**kw)
        ss = [score_points(a, img, [p], glyphs) for p in panels]
        controls.append({"name": name, "kind": kind,
                         "score_by_panel": [min(s["published_near_ours"], s["ours_near_published"]) for s in ss]})
    Image.fromarray(ours.astype(np.uint8)).save(out / "fig1_ours.png", optimize=True)
    overlay(a, ours).save(out / "fig1_overlay.png", optimize=True)
    # Per panel, for the README
    per_panel = []
    for i, (p, name) in enumerate(zip(panels, ("a", "b"))):
        s = score_points(a, ours, [p], glyphs)
        per_panel.append({"panel": name, **s, "controls": [{"name": c["name"], "kind": c["kind"], "score": c["score_by_panel"][i]}
                                                          for c in controls]})
    return {"score": score, "per_panel": per_panel, "calibration": cal,
            "samples": len(cols), "points_off_panel": off, "glyph_colours": [g["colour"].tolist() for g in glyphs]}


def fig2(pub_dir, data_dir, out):
    a = load(pub_dir / "Fig2.png")
    rows = read_csv(data_dir / "vandesompele.csv")
    # Legend: two rows of five, read down the columns.
    genes = ["ACTB", "B2M", "GAPD", "HMBS", "HPRT1", "RPL13A", "SDHA", "TBP", "UBC", "YWHAZ"]
    tissues = ["BM", "FIB", "LEU", "NB", "POOL"]
    hl = frame_lines(a, 0, 0.5)
    vl = frame_lines(a, 1, 0.2)
    assert len(vl) == 6, vl
    top, bottom = hl[-2][1], hl[-1][0]     # strip bottom, panel bottom
    boxes = [(vl[i][0] if i == 0 else vl[i][1], top, vl[i + 1][0], bottom) for i in range(5)]
    glyphs = legend_glyphs(a, 30, hl[0][0] - 2,
                           lambda c: sorted(range(len(c)), key=lambda i: (round(c[i][1] / 100), c[i][0])))
    assert len(glyphs) == 10
    vals = [10, 1, 1e-1, 1e-2, 1e-3, 1e-4, 1e-5]     # top to bottom
    t = y_ticks(a, boxes[0][0] - 22, boxes[0][0] - 3, top + 2, bottom - 1)
    assert len(t) == len(vals), t
    av, bv, res = fit_line(t, [math.log10(v) for v in vals])
    panels = [{"box": b, "a": av, "b": bv, "log": True} for b in boxes]
    data = {k: np.array([[float(r[g]) for g in genes] for r in rows if r["tissue"] == k]) for k in tissues}
    # Wide panels have empty padding grid lines at both edges (FIB one each side, NB two): the
    # samples are the central n_k grid lines.
    cols, padding = [], []
    for b, k in zip(boxes, tissues):
        c = grid_columns(a, b)
        extra = len(c) - len(data[k])
        assert extra >= 0 and extra % 2 == 0, (k, len(c), len(data[k]))
        cols.append(c[extra // 2: len(c) - extra // 2])
        padding.append(extra // 2)

    def render(D, key=lambda V: np.log(V).mean(axis=1), scale=1.0, shift=0, perm=None):
        Vs, xs_all = [], []
        for k, xs in zip(tissues, cols):
            V = D[k]
            o = np.argsort(key(V), kind="stable") if perm is None else perm[k]
            V = V[o]
            if shift:
                xs = xs[shift:]
                V = V[: len(xs)]
            Vs.append(V * scale)
            xs_all.append(xs)
        return point_figure(a, panels, glyphs, xs_all, Vs, list(range(10)))

    ours, off = render(data)
    score = score_points(a, ours, panels, glyphs)
    rng = np.random.default_rng(1)
    swapped = {tissues[i]: data[tissues[(i + 1) % 5]] for i in range(5)}
    # Wrong input that keeps each panel's sample count: each tissue type drawn with the samples of
    # the next tissue type, as many as fit (resampled with replacement when there are too few).
    swapped = {k: v[rng.choice(len(v), len(data[k]), replace=len(v) < len(data[k]))] for k, v in swapped.items()}
    controls = []
    for name, kind, kw in [
        ("each tissue type drawn with samples of the next one", "wrong_input", dict(D=swapped)),
        ("samples in a random order within each tissue type (seed 1)", "wrong_input",
         dict(D=data, perm={k: rng.permutation(len(data[k])) for k in tissues})),
        ("genes swapped in pairs along the legend", "wrong_input",
         dict(D={k: v[:, [1, 0, 3, 2, 5, 4, 7, 6, 9, 8]] for k, v in data.items()})),
        ("samples ordered by the mean of the raw values", "near_miss", dict(D=data, key=lambda V: V.mean(axis=1))),
        ("every sample one column to the right", "near_miss", dict(D=data, shift=1)),
        ("values x 1.05", "near_miss", dict(D=data, scale=1.05)),
        ("values x 0.95", "near_miss", dict(D=data, scale=0.95)),
    ]:
        img, _ = render(**kw)
        s = score_points(a, img, panels, glyphs)
        controls.append({"name": name, "kind": kind, "score": min(s["published_near_ours"], s["ours_near_published"])})
    Image.fromarray(ours.astype(np.uint8)).save(out / "fig2_ours.png", optimize=True)
    overlay(a, ours).save(out / "fig2_overlay.png", optimize=True)
    return {"score": score, "controls": controls,
            "calibration": [{"ticks_px": t, "tick_values": vals, "max_residual_px": res}],
            "samples": [len(c) for c in cols], "padding_grid_lines_each_side": padding, "points_off_panel": off,
            "glyph_colours": [g["colour"].tolist() for g in glyphs]}


# ---------------------------------------------------------------- Fig 3: signed MSE bars

FILL = (240, 78, 40)       # sampled below from the legend; this is only the fallback


def fig3(pub_dir, data_dir, out):
    a = load(pub_dir / "Fig3.png")
    bars = read_csv(data_dir / "fig3_bars.csv")
    genes_top = ["ACTB", "B2M", "GAPD", "HMBS", "HPRT1"]
    genes_bottom = ["RPL13A", "SDHA", "TBP", "UBC", "YWHAZ"]
    tissues = ["BM", "FIB", "LEU", "NB", "POOL"]
    # Panel rows: solid full-width lines (the dashed zero lines cover about half the width).
    ys = [r for r in frame_lines(a, 0, 0.8) if r[0] > 160]
    assert len(ys) == 4, ys
    vl = frame_lines(a, 1, 0.25)
    xs = [v for v in vl]
    assert len(xs) >= 6, xs
    left, right = xs[0][0], xs[-1][1]
    # Columns: the five panels share equal widths between left and right frame lines.
    edges = np.linspace(left, right, 6)
    row_top = (ys[0][1], ys[1][0])      # top row panel: below its strip, above the second strip
    row_bot = (ys[2][1], ys[3][0])
    fill = np.median(a[(sat(a) > 100) & (a[:, :, 0] > 200)][:200], axis=0) if ((sat(a) > 100) & (a[:, :, 0] > 200)).any() else np.array(FILL)
    panels = []
    for (y0, y1), genes, tick_side in ((row_top, genes_top, "right"), (row_bot, genes_bottom, "left")):
        if tick_side == "left":
            t = y_ticks(a, left - 12, left - 2, y0 + 2, y1 - 1)
        else:
            t = y_ticks(a, right + 2, right + 12, y0 + 2, y1 - 1)
        assert len(t) == 3, (tick_side, t)
        av, bv, res = fit_line(t, [5, 0, -5])
        for i, g in enumerate(genes):
            box = (int(round(edges[i])), y0, int(round(edges[i + 1])), y1)
            panels.append({"gene": g, "box": box, "a": av, "b": bv, "res": res})
    # Tissue tick marks below the bottom row give the bar centres of each column.
    tx = x_ticks(a, row_bot[1] + 3, row_bot[1] + 20, left, right)
    assert len(tx) == 25, tx
    spacing = float(np.median(np.diff(tx[:5])))
    width = spacing * 2 / 3            # lattice barchart's default box.ratio = 2
    zero_rows = {}
    for p in panels:
        zero_rows[p["gene"]] = p["a"]
    D = {(r["gene"], r["tissue"]): (float(r["bias"]), float(r["variance"])) for r in bars}

    # Outline width: measured on the legend's white key (the dark run across its left edge).
    lw = 3

    def draw(D, scale=1.0, gene_shift=0, flip=False):
        img = a.copy()
        for p in panels:
            x0, y0, x1, y1 = p["box"]
            inner = img[y0 + 2:y1 - 1, x0 + 2:x1 - 1]
            zr = int(round(p["a"]))
            keep = img[zr - 2:zr + 3, x0 + 2:x1 - 1].copy()
            inner[:] = 255
            img[zr - 2:zr + 3, x0 + 2:x1 - 1] = keep      # the dashed zero line
        pil = Image.fromarray(img.astype(np.uint8))
        dr = ImageDraw.Draw(pil)
        allg = genes_top + genes_bottom
        for pi, p in enumerate(panels):
            g = allg[(pi + gene_shift) % 10] if gene_shift else p["gene"]
            col = pi % 5
            for ti, t in enumerate(tissues):
                bias, var = D[(g, t)]
                b2, mse = bias * bias * scale, (bias * bias + var) * scale
                sgn = -1 if (bias < 0) != flip else 1
                cx = tx[col * 5 + ti]
                xa, xb = cx - width / 2, cx + width / 2
                y_zero, y_b2, y_mse = p["a"], p["a"] + p["b"] * sgn * b2, p["a"] + p["b"] * sgn * mse
                dr.rectangle([xa, min(y_zero, y_b2), xb, max(y_zero, y_b2)], fill=tuple(int(v) for v in fill), outline=(0, 0, 0), width=lw)
                dr.rectangle([xa, min(y_b2, y_mse), xb, max(y_b2, y_mse)], fill=(253, 253, 251), outline=(0, 0, 0), width=lw)
        return np.asarray(pil).astype(np.int16)

    def labels(img):
        lab = -np.ones(img.shape[:2], int)
        for p in panels:
            x0, y0, x1, y1 = p["box"]
            sub = img[y0 + 3:y1 - 2, x0 + 3:x1 - 2]
            l = -np.ones(sub.shape[:2], int)
            l[(sat(sub) > 100) & (sub[:, :, 0] > 180)] = 0          # bar fill
            l[grey(sub) < 90] = 1                                     # bar outline
            zr = int(round(p["a"])) - (y0 + 3)
            l[max(zr - 3, 0):zr + 4] = -1                              # the zero line is not scored
            lab[y0 + 3:y1 - 2, x0 + 3:x1 - 2] = l
        return lab

    lab_pub = labels(a)
    ours = draw(D)
    score = two_way(lab_pub, labels(ours), 2)
    controls = []
    for name, kind, kw in [
        ("each panel drawn with the next gene's bars", "wrong_input", dict(D=D, gene_shift=1)),
        ("every bar's sign flipped", "wrong_input", dict(D=D, flip=True)),
        ("bars x 1.05", "near_miss", dict(D=D, scale=1.05)),
        ("bars x 0.95", "near_miss", dict(D=D, scale=0.95)),
    ]:
        s = two_way(lab_pub, labels(draw(**kw)), 2)
        controls.append({"name": name, "kind": kind, "score": min(s["published_near_ours"], s["ours_near_published"])})
    Image.fromarray(ours.astype(np.uint8)).save(out / "fig3_ours.png", optimize=True)
    overlay(a, ours).save(out / "fig3_overlay.png", optimize=True)
    return {"score": score, "controls": controls,
            "calibration": [{"row": "top", "max_residual_px": panels[0]["res"]},
                            {"row": "bottom", "max_residual_px": panels[5]["res"]}],
            "bar_spacing_px": spacing, "bar_width_px": width, "fill_colour": [int(v) for v in fill]}


def main():
    pub, data, out = map(Path, sys.argv[1:4])
    out.mkdir(parents=True, exist_ok=True)
    res = {"tolerance_px": TOL, "dpi": 300, "fig1": fig1(pub, data, out), "fig2": fig2(pub, data, out),
           "fig3": fig3(pub, data, out)}

    def clean(o):
        if isinstance(o, dict):
            return {k: clean(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)):
            return [clean(v) for v in o]
        if isinstance(o, (np.floating, float)):
            return round(float(o), 6)
        if isinstance(o, np.integer):
            return int(o)
        return o
    (out / "figures.json").write_text(json.dumps(clean(res), indent=1) + "\n")
    for k, s, cs in [("fig1.a", res["fig1"]["per_panel"][0], res["fig1"]["per_panel"][0]["controls"]),
                     ("fig1.b", res["fig1"]["per_panel"][1], res["fig1"]["per_panel"][1]["controls"]),
                     ("fig2", res["fig2"]["score"], res["fig2"]["controls"]), ("fig3", res["fig3"]["score"], res["fig3"]["controls"])]:
        print(k, f"{100 * min(s['published_near_ours'], s['ours_near_published']):.2f}%",
              "best control", f"{100 * max(c['score'] for c in cs):.1f}%")


if __name__ == "__main__":
    main()
