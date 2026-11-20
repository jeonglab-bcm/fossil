"""Read the plotted values out of the paper's vector figures.

The article PDF (PMC open-access copy) holds Figures 1 to 8 as vector drawings. Each axis is
mapped to data units from its tick marks and the printed tick labels (listed below, read
from the figure); nothing inside the plot is fitted. Each series is the chain of line
segments of one colour, whose vertices are the plotted points; series that share a colour
are told apart by the marker drawn at their vertices, matched against the legend.

    python3 extract_published.py PMC2824146.1.pdf published_values.json
"""

import json
import math
import sys
from collections import defaultdict

import pymupdf

# Figure pages (0-based) and the printed tick labels of each panel, row by row: y ticks as
# (first, step, count) from the bottom; x ticks likewise from the left.
X_MISS = (0, 25, 4)
FIGS = {
    "fig2": {"page": 6, "panels": [
        ("X1", (-0.012, 0.002, 5)), ("X2", (0.035, 0.005, 5)), ("X3", (-0.003, 0.0005, 5)),
        ("X4", (-4e-4, 2e-4, 5)), ("X5", (-0.40, 0.05, 4)), ("X6", (0.15, 0.05, 5)),
        ("X7", (0.55, 0.05, 6)), ("X8d1", (0.15, 0.05, 4)), ("X8d2", (0.25, 0.05, 4))],
        "legend": ["CC", "SI", "AREG", "MICE", "MICE_PMM", "MICE_PMM_notrans", "MIX_notrunc"]},
    "fig3": {"page": 8, "panels": [
        ("X1", (0.0, 0.005, 4)), ("X2", (0.0, 0.005, 4)), ("X3", (0.0, 2e-4, 5)),
        ("X4", (0.0, 1e-4, 6)), ("X5", (0.0, 0.05, 5)), ("X6", (0.0, 0.05, 7)),
        ("X7", (0.0, 0.1, 5)), ("X8d1", (0.0, 0.05, 6)), ("X8d2", (0.0, 0.05, 6))],
        "legend": ["CC", "SI", "AREG", "MICE", "MICE_PMM", "MICE_PMM_notrans", "MIX_notrunc"]},
    "fig4": {"page": 9, "panels": [(v, (0, 20, 6)) for v in
        ["X1", "X2", "X3", "X4", "X5", "X6", "X7", "X8d1", "X8d2"]],
        "legend": ["CC", "SI", "AREG", "MICE", "MICE_PMM", "MICE_PMM_notrans", "MIX_notrunc"]},
    "fig5": {"page": 10, "panels": [
        ("X1", (0.0, 0.1, 6)), ("X2", (0.0, 0.02, 6)), ("X3", (0.0, 0.02, 6)),
        ("X4", (0.0, 0.1, 7)), ("X5", (0.0, 0.05, 5)), ("X6", (0.0, 0.1, 5)),
        ("X7", (0.0, 0.05, 4)), ("X8d1", (0.0, 0.1, 5)), ("X8d2", (0.0, 0.1, 5))],
        "legend": ["CC", "SI", "AREG", "MICE", "MICE_PMM", "MICE_PMM_notrans", "MIX_notrunc"]},
    "fig6": {"page": 11, "panels": [
        ("lr_p", (0.0, 0.001, 6)), ("r2", (0.0, 0.1, 5)), ("d", (0.0, 0.5, 4)),
        ("surv", (0.0, 0.2, 6))],
        "legend": ["CC", "SI", "AREG", "MICE", "MICE_PMM", "MICE_PMM_notrans", "MIX_notrunc"]},
    "fig7": {"page": 12, "panels": [
        ("X2", (0.035, 0.005, 6)), ("X3", (-0.003, 0.0005, 5)), ("X4", (-4e-4, 2e-4, 5)),
        ("X5", (-0.45, 0.05, 5))],
        "legend": ["MAR:MICE_PMM", "MAR:MICE_PMM_notrans", "MAR:AREG", "MNAR:MICE_PMM",
                   "MNAR:MICE_PMM_notrans", "MNAR:AREG", "MNAR:MICE"]},
    "fig8": {"page": 13, "panels": [(v, (0, 20, 6)) for v in ["X2", "X3", "X4"]],
        "legend": ["MAR:MICE_PMM", "MAR:MICE_PMM_notrans", "MAR:AREG", "MNAR:MICE_PMM",
                   "MNAR:MICE_PMM_notrans", "MNAR:AREG", "MNAR:MICE"]},
}
# Figure 1: histograms. y ticks (first, step, count); x ticks (first, step, count).
FIG1 = {"page": 2, "panels": [
    ("age", (0, 20, 8), (20, 10, 7)), ("pnodes", (0, 100, 5), (0, 10, 6)),
    ("progrec", (0, 100, 6), (0, 500, 5)), ("estrec", (0, 100, 6), (0, 200, 7)),
    ("horTh", (0, 100, 5), (0, 0.2, 6)), ("menostat", (0, 100, 5), (1, 0.2, 6)),
    ("tgrade", (0, 100, 5), (1, 0.5, 5)), ("tsize", (0, 50, 6), (0, 20, 7)),
    ("log_pnodes", (0, 50, 4), (0, 1, 5)), ("log_progrec", (0, 20, 8), (0, 2, 5)),
    ("log_estrec", (0, 20, 5), (0, 2, 4)), ("log_tsize", (0, 50, 7), (1, 1, 5))]}

DATA_X = [0, 5, 10, 25, 50, 75]
EPS = 0.06


def segments(page):
    """Line segments of a page: stroked lines, and thin filled rectangles as lines."""
    out = []
    for order, d in enumerate(page.get_drawings()):
        col = d.get("color") or d.get("fill")
        col = tuple(round(c, 2) for c in col) if col else None
        for it in d["items"] if d["type"] != "f" else []:
            if it[0] == "l":
                a, b = it[1], it[2]
                out.append({"x0": a.x, "y0": a.y, "x1": b.x, "y1": b.y, "col": col,
                            "order": order, "path": order})
        pts = [it[1] for it in d["items"] if it[0] == "l"]
        if (d["type"] == "f" and len(d["items"]) in (3, 4) and len(pts) == len(d["items"])):
            # a stroke drawn as a thin filled quadrilateral: its centre line
            q = [pts[0]] + [it[2] for it in d["items"] if it[0] == "l"]
            q = q[:4]
            if len(q) == 4:
                edges = [(math.dist(q[i], q[(i + 1) % 4]), i) for i in range(4)]
                short = sorted(edges)[:2]
                if short[0][0] < 1.2 and short[1][0] < 1.2 and sorted(edges)[2][0] > 0.8:
                    i, j = short[0][1], short[1][1]
                    m1 = ((q[i].x + q[(i + 1) % 4].x) / 2, (q[i].y + q[(i + 1) % 4].y) / 2)
                    m2 = ((q[j].x + q[(j + 1) % 4].x) / 2, (q[j].y + q[(j + 1) % 4].y) / 2)
                    out.append({"x0": m1[0], "y0": m1[1], "x1": m2[0], "y1": m2[1], "col": col,
                                "order": order, "path": order, "thin": True})
                    continue
        for it in d["items"]:
            if it[0] == "l" and d["type"] == "f":
                continue
            if it[0] == "re" and d["type"] == "f":
                r = it[1]
                if r.width < 0.8 and r.height > 0.8:
                    x = (r.x0 + r.x1) / 2
                    out.append({"x0": x, "y0": r.y0, "x1": x, "y1": r.y1, "col": col,
                                "order": order, "path": order, "thin": True})
                elif r.height < 0.8 and r.width > 0.8:
                    y = (r.y0 + r.y1) / 2
                    out.append({"x0": r.x0, "y0": y, "x1": r.x1, "y1": y, "col": col,
                                "order": order, "path": order, "thin": True})
    return out


def is_black(c):
    return c is not None and max(c) < 0.06


def length(s):
    return math.hypot(s["x1"] - s["x0"], s["y1"] - s["y0"])


def find_axes(segs):
    """Axis lines with their tick marks: (kind, coordinate of ticks sorted, line)."""
    blk = [s for s in segs if is_black(s["col"])]
    vert = [s for s in blk if abs(s["x0"] - s["x1"]) < EPS and length(s) > 15]
    hor = [s for s in blk if abs(s["y0"] - s["y1"]) < EPS and length(s) > 15]
    short_h = [s for s in blk if abs(s["y0"] - s["y1"]) < EPS and 1.5 < length(s) < 6]
    short_v = [s for s in blk if abs(s["x0"] - s["x1"]) < EPS and 1.5 < length(s) < 6]
    yaxes, xaxes = [], []
    for v in vert:
        x, lo, hi = v["x0"], min(v["y0"], v["y1"]), max(v["y0"], v["y1"])
        ticks = sorted({round(t["y0"], 2) for t in short_h
                        if abs(max(t["x0"], t["x1"]) - x) < 0.3 and lo - 0.3 <= t["y0"] <= hi + 0.3})
        if len(ticks) >= 2 and abs(ticks[0] - lo) < 0.3 and abs(ticks[-1] - hi) < 0.3:
            yaxes.append({"x": x, "ticks": ticks[::-1], "lo": lo, "hi": hi})
    for h in hor:
        y, lo, hi = h["y0"], min(h["x0"], h["x1"]), max(h["x0"], h["x1"])
        ticks = sorted({round(t["x0"], 2) for t in short_v
                        if abs(min(t["y0"], t["y1"]) - y) < 0.3 and lo - 0.3 <= t["x0"] <= hi + 0.3})
        if len(ticks) >= 2 and abs(ticks[0] - lo) < 0.3 and abs(ticks[-1] - hi) < 0.3:
            xaxes.append({"y": y, "ticks": ticks, "lo": lo, "hi": hi})
    yaxes = dedupe(yaxes, "x")
    xaxes = dedupe(xaxes, "y")
    return yaxes, xaxes


def dedupe(axes, key):
    out = []
    for a in sorted(axes, key=lambda a: (a[key], a["lo"])):
        if not any(abs(a[key] - b[key]) < 0.5 and abs(a["lo"] - b["lo"]) < 0.5 for b in out):
            out.append(a)
    return out


def pair_panels(yaxes, xaxes):
    """Each y axis with the x axis just below it and starting to its right."""
    panels = []
    for ya in yaxes:
        cands = [xa for xa in xaxes if xa["y"] > ya["hi"] - 1 and xa["lo"] > ya["x"] - 1
                 and xa["lo"] - ya["x"] < 40 and xa["y"] - ya["hi"] < 40]
        if not cands:
            continue
        xa = min(cands, key=lambda a: (a["y"] - ya["hi"]) + (a["lo"] - ya["x"]))
        panels.append((ya, xa))
    # row-major: rows by the x axis' y (within 20 pt), then left to right
    panels.sort(key=lambda p: (round(p[1]["y"] / 40), p[0]["x"]))
    return panels


def linear_fit(ticks_px, first, step, count):
    vals = [first + k * step for k in range(count)]
    n = count
    mx = sum(ticks_px) / n
    my = sum(vals) / n
    b = sum((p - mx) * (v - my) for p, v in zip(ticks_px, vals)) / sum((p - mx) ** 2 for p in ticks_px)
    return [my - b * mx, b]


def linear_map(ticks_px, first, step, count):
    if len(ticks_px) != count:
        raise ValueError(f"expected {count} ticks, found {len(ticks_px)}: {ticks_px}")
    vals = [first + k * step for k in range(count)]
    n = count
    mx = sum(ticks_px) / n
    my = sum(vals) / n
    sxx = sum((p - mx) ** 2 for p in ticks_px)
    b = sum((p - mx) * (v - my) for p, v in zip(ticks_px, vals)) / sxx
    a = my - b * mx
    resid = max(abs(a + b * p - v) for p, v in zip(ticks_px, vals))
    return (lambda p: a + b * p), resid, abs(b)


def chains(segs, region):
    """Polylines: consecutive (in drawing order) same-colour segments joined end to start."""
    x0, x1, y0, y1 = region
    inside = [s for s in segs if s["col"] is not None and length(s) > 0.3
              and x0 <= (s["x0"] + s["x1"]) / 2 <= x1 and y0 <= (s["y0"] + s["y1"]) / 2 <= y1]
    out, cur = [], None

    def near(p, q):
        return abs(p[0] - q[0]) < 0.3 and abs(p[1] - q[1]) < 0.3

    for s in inside:
        a, b = (s["x0"], s["y0"]), (s["x1"], s["y1"])
        if cur and s["col"] == cur["col"]:
            if len(cur["pts"]) == 2 and not (near(a, cur["pts"][-1]) or near(b, cur["pts"][-1])) \
                    and (near(a, cur["pts"][0]) or near(b, cur["pts"][0])):
                cur["pts"].reverse()
            if near(a, cur["pts"][-1]):
                cur["pts"].append(b)
                continue
            if near(b, cur["pts"][-1]):
                cur["pts"].append(a)
                continue
        if cur:
            out.append(cur)
        cur = {"col": s["col"], "pts": [a, b], "order": s["order"]}
    if cur:
        out.append(cur)
    for c in out:
        if c["pts"][0][0] > c["pts"][-1][0]:
            c["pts"].reverse()
    return out


def marker_signature(segs, curves, quads, col, x, y, used, r=2.6):
    """Shape of the marker of colour col drawn at (x, y)."""
    sig = defaultdict(int)
    for s in segs:
        if s["col"] != col or id(s) in used or length(s) > 2.2 * r:
            continue
        mx, my = (s["x0"] + s["x1"]) / 2, (s["y0"] + s["y1"]) / 2
        if abs(mx - x) > r or abs(my - y) > r:
            continue
        dx, dy = abs(s["x1"] - s["x0"]), abs(s["y1"] - s["y0"])
        if dy < 0.05:
            sig["h"] += 1
            sig["hy"] += (my - y)
            sig["h_c" if abs(my - y) < 0.5 else "h_off"] += 1
        elif dx < 0.05:
            sig["v"] += 1
            sig["v_c" if abs(mx - x) < 0.5 else "v_off"] += 1
        else:
            sig["d"] += 1
            sig["dy"] += (my - y)
    for (cx, cy, c) in curves:
        if c == col and abs(cx - x) < r and abs(cy - y) < r:
            sig["c"] += 1
    for (cx, cy, c) in quads:
        if c == col and abs(cx - x) < r and abs(cy - y) < r:
            sig["q"] += 1
    return classify(sig)


def classify(sig):
    if sig["c"]:
        return "circle"
    if sig["q"] or sig["h_off"] >= 2 or sig["v_off"] >= 2:
        return "square"
    if sig["d"] >= 2 and sig["h_c"] >= 1 and sig["v_c"] >= 1:
        return "star"
    if sig["h_c"] >= 1 and sig["v_c"] >= 1:
        return "plus"
    if sig["d"] >= 2 and sig["h"] >= 1:
        # triangle: the horizontal side is the base, below the apex when pointing up
        return "tri_up" if sig["hy"] > 0 else "tri_down"
    if sig["d"] >= 2:
        return "x"
    return "none"


def shapes(page):
    curves, quads = [], []
    for d in page.get_drawings():
        col = d.get("color") or d.get("fill")
        if not col:
            continue
        col = tuple(round(c, 2) for c in col)
        r = d["rect"]
        kinds = {it[0] for it in d["items"]}
        if r.width < 9 and r.height < 9:
            if "c" in kinds:
                curves.append(((r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2, col))
            if "qu" in kinds or ("re" in kinds and r.width > 0.8 and r.height > 0.8):
                quads.append(((r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2, col))
    return curves, quads


def read_legend(segs, curves, quads, labels, top):
    """Legend samples below `top`: a coloured line with a marker at its middle."""
    samples = [s for s in segs if s["col"] is not None and abs(s["y0"] - s["y1"]) < EPS
               and 18 < length(s) < 60 and s["y0"] > top]
    entries = []
    for s in samples:
        x = (s["x0"] + s["x1"]) / 2
        y = s["y0"]
        if any(abs(e["x"] - x) < 1 and abs(e["y"] - y) < 1 for e in entries):
            continue
        entries.append({"x": x, "y": y, "col": s["col"],
                        "marker": marker_signature(segs, curves, quads, s["col"], x, y,
                                                   {id(s)}, r=5.0)})
    # column-major: left column top to bottom, then the next column
    cols = sorted({round(e["x"] / 60) for e in entries})
    entries.sort(key=lambda e: (cols.index(round(e["x"] / 60)), e["y"]))
    if len(entries) != len(labels):
        raise ValueError(f"legend: expected {len(labels)} entries, found {len(entries)}")
    for e, lab in zip(entries, labels):
        e["label"] = lab
    return entries


def coldist(a, b):
    return sum((x - y) ** 2 for x, y in zip(a, b))


def extract_lines(doc, key, cfg):
    page = doc[cfg["page"]]
    segs = segments(page)
    curves, quads = shapes(page)
    yaxes, xaxes = find_axes(segs)
    panels = pair_panels(yaxes, xaxes)
    if len(panels) != len(cfg["panels"]):
        raise ValueError(f"{key}: expected {len(cfg['panels'])} panels, found {len(panels)}")
    bottom = max(xa["y"] for _, xa in panels)
    legend = read_legend(segs, curves, quads, cfg["legend"], bottom + 20)
    out = {"page": cfg["page"] + 1, "legend": [{k: e[k] for k in ("label", "col", "marker")}
                                                for e in legend], "panels": {}}
    for (name, yt), (ya, xa) in zip(cfg["panels"], panels):
        fy, ry, sy = linear_map(ya["ticks"], *yt)
        fx, rx, sx = linear_map(xa["ticks"], *X_MISS)
        region = (ya["x"] + 0.5, xa["hi"] + 12, ya["hi"] - (ya["lo"] - ya["hi"]) * 0
                  - 30, xa["y"] - 0.5)
        region = (ya["x"] + 0.5, xa["hi"] + 12, min(ya["ticks"]) - 30, xa["y"] - 0.5)
        series_chains = []
        for c in chains(segs, region):
            xs = [fx(p[0]) for p in c["pts"]]
            seglen = [math.dist(c["pts"][i], c["pts"][i + 1]) for i in range(len(c["pts"]) - 1)]
            if min(seglen) < 5:
                continue
            if not all(min(abs(x - d) for d in DATA_X) < 0.4 for x in xs):
                continue
            series_chains.append(c)
        used = set()
        # reference lines: short dashes at one height across the panel
        dashes = defaultdict(list)
        for s in segs:
            if (s["col"] is not None and abs(s["y0"] - s["y1"]) < EPS and length(s) < 12
                    and region[0] <= s["x0"] <= region[1] and region[2] <= s["y0"] <= region[3]):
                dashes[(s["col"], round(s["y0"], 1))].append(s)
        refs = sorted(fy(y) for (col, y), v in dashes.items()
                      if len(v) >= 8 and (max(t["x1"] for t in v) - min(t["x0"] for t in v)) > 60)
        # assign chains to legend entries: colour first, then marker
        panel = {"y_tick_residual": ry, "x_tick_residual": rx, "units_per_pt": sy,
                 "y_map": linear_fit(ya["ticks"], *yt), "x_map": linear_fit(xa["ticks"], *X_MISS),
                 "axes": {"y_axis_x": ya["x"], "y_ticks": ya["ticks"], "x_axis_y": xa["y"],
                          "x_ticks": xa["ticks"]},
                 "reference_lines": refs, "series": {}}
        frags = defaultdict(list)
        by_col = defaultdict(list)
        starts = {e["label"]: e for e in legend if e["label"] in ("CC", "SI")}
        for c in series_chains:
            best = [e for e in legend if coldist(e["col"], c["col"]) < 0.01]
            # Only CC and SI have a 0% point. A line of another colour that starts at 0%
            # and carries SI's markers is SI drawn in the wrong colour (Fig. 6b).
            if ("SI" in starts and abs(fx(c["pts"][0][0])) < 0.4 and best
                    and best[0]["label"] not in starts):
                si = starts["SI"]
                hits = sum(marker_signature(segs, curves, quads, si["col"], px, py, used)
                           == si["marker"] for (px, py) in c["pts"])
                if hits >= len(c["pts"]) - 1:
                    frags["SI"].append(c)
                    panel.setdefault("anomalies", []).append(
                        f"SI line drawn in the colour of {best[0]['label']}, with SI markers")
                    continue
            if best:
                by_col[tuple(best[0]["col"])].append((c, best))
        for col, items in by_col.items():
            labels = items[0][1]
            if len(labels) == 1:
                frags[labels[0]["label"]].extend(c for c, _ in items)
                continue
            # Two series in one colour: R draws one completely before the next, so split the
            # fragments at the widest gap in drawing order, then name each group by the
            # markers at its vertices (legend order when they tie).
            items.sort(key=lambda t: t[0]["order"])
            orders = [c["order"] for c, _ in items]
            groups = [[c for c, _ in items]]
            if len(items) > 1:
                gaps = [(orders[i + 1] - orders[i], i) for i in range(len(orders) - 1)]
                g, i = max(gaps)
                others = [c["order"] for c in series_chains
                          if orders[i] < c["order"] < orders[i + 1] and tuple(c["col"]) != col]
                if others:
                    groups = [[c for c, _ in items[:i + 1]], [c for c, _ in items[i + 1:]]]
            def votes(group):
                v = defaultdict(int)
                for c in group:
                    for (px, py) in c["pts"]:
                        v[marker_signature(segs, curves, quads, c["col"], px, py, used)] += 1
                return v
            vs = [votes(g) for g in groups]
            if len(groups) == 2:
                keep = sum(vs[0].get(labels[0]["marker"], 0) for _ in [0]) + vs[1].get(labels[1]["marker"], 0)
                swap = vs[0].get(labels[1]["marker"], 0) + vs[1].get(labels[0]["marker"], 0)
                order = [0, 1] if keep >= swap else [1, 0]
                for gi, li in zip(order, [0, 1]):
                    frags[labels[li]["label"]].extend(groups[gi])
            else:
                best = max(labels, key=lambda e: vs[0].get(e["marker"], 0))
                frags[best["label"]].extend(groups[0])
                other = [e for e in labels if e is not best][0]
                # the other series hides under this one when its marker sits at every vertex
                if vs[0].get(other["marker"], 0) + vs[0].get(best["marker"], 0) > 0 and \
                        vs[0].get(other["marker"], 0) >= 0.5 * vs[0].get(best["marker"], 0):
                    frags[other["label"]].extend(groups[0])
                    panel.setdefault("coincident", []).append([best["label"], other["label"]])
        for lab, cs in frags.items():
            pts = {}
            merged = set()
            for c in sorted(cs, key=lambda c: -len(c["pts"])):
                q = [(min(DATA_X, key=lambda d: abs(d - fx(px))), fy(py)) for (px, py) in c["pts"]]
                for (xa_, ya_), (xb_, yb_) in zip(q, q[1:]):
                    pts.setdefault(xa_, ya_)
                    pts.setdefault(xb_, yb_)
                    # collinear points merged into one segment by the PDF writer
                    for d in DATA_X:
                        if min(xa_, xb_) < d < max(xa_, xb_) and d not in pts:
                            pts[d] = ya_ + (yb_ - ya_) * (d - xa_) / (xb_ - xa_)
                            merged.add(d)
            panel["series"][lab] = [[x, pts[x]] for x in sorted(pts)]
            if merged:
                panel.setdefault("collinear_points", {})[lab] = sorted(merged)
        out["panels"][name] = panel
    return out


def extract_fig1(doc):
    page = doc[FIG1["page"]]
    segs = segments(page)
    yaxes, xaxes = find_axes(segs)
    panels = pair_panels(yaxes, xaxes)
    if len(panels) != len(FIG1["panels"]):
        raise ValueError(f"fig1: expected {len(FIG1['panels'])} panels, found {len(panels)}")
    out = {"page": FIG1["page"] + 1, "panels": {}}
    for (name, yt, xt), (ya, xa) in zip(FIG1["panels"], panels):
        fy, ry, _ = linear_map(ya["ticks"], *yt)
        fx, rx, _ = linear_map(xa["ticks"], *xt)
        base = ya["ticks"][0]  # y of the zero tick
        x_lo, x_hi = ya["x"] + 1, xa["hi"] + 12
        y_top = min(ya["ticks"]) - 40
        # bar sides: vertical black segments standing on the baseline
        sides = [s for s in segs if is_black(s["col"]) and abs(s["x0"] - s["x1"]) < EPS
                 and x_lo < s["x0"] < x_hi and y_top < min(s["y0"], s["y1"])
                 and abs(max(s["y0"], s["y1"]) - base) < 0.6]
        tops = [s for s in segs if is_black(s["col"]) and abs(s["y0"] - s["y1"]) < EPS
                and x_lo < min(s["x0"], s["x1"]) and max(s["x0"], s["x1"]) < x_hi
                and y_top < s["y0"] < base - 0.3 and length(s) > 1]
        edges = sorted({round(s["x0"], 1) for s in sides})
        bars = []
        for t in tops:
            a, b = sorted((t["x0"], t["x1"]))
            # a bar top meets a bar side at each end
            if not (any(abs(sd["x0"] - a) < 0.3 for sd in sides)
                    and any(abs(sd["x0"] - b) < 0.3 for sd in sides)):
                continue
            bars.append([fx(a), fx(b), fy(t["y0"])])
        bars.sort()
        out["panels"][name] = {"y_tick_residual": ry, "x_tick_residual": rx,
                               "y_map": linear_fit(ya["ticks"], *yt), "x_map": linear_fit(xa["ticks"], *xt),
                               "axes": {"y_axis_x": ya["x"], "y_ticks": ya["ticks"], "x_axis_y": xa["y"],
                                        "x_ticks": xa["ticks"]},
                               "edges": [fx(e) for e in edges], "bars": bars}
    return out


def main():
    pdf, dest = sys.argv[1], sys.argv[2]
    doc = pymupdf.open(pdf)
    res = {"source": "PMC2824146.1.pdf (PMC open-access copy)", "figures": {}}
    res["figures"]["fig1"] = extract_fig1(doc)
    for key, cfg in FIGS.items():
        res["figures"][key] = extract_lines(doc, key, cfg)
    with open(dest, "w") as f:
        json.dump(res, f, indent=1)


if __name__ == "__main__":
    main()
