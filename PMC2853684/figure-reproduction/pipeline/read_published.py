"""Read the plotted values of the published figures from the vector drawings in the PDFs.

    read_published.py PAPER.pdf SUPPLEMENT.pdf published_values.json

Figure 2 (main PDF, page 1060) and Supplementary Figure S1 (supplement page 7) are R scatter
plots: each method is a polyline through its precision-recall points, in plotting order. The
polyline vertices are the plotted values; the axes are calibrated from the tick marks. Figure 4
(page 1061) and Supplementary Figure S2 (supplement page 8) are matplotlib bar charts: the bar
heights, error bars and least-squares lines are read the same way.

The main PDF was recoloured to CMYK by the publisher; the supplement keeps R's RGB colours. Each
colour is mapped to its method from the figure legend (comments below).
"""

from __future__ import annotations

import json
import sys

from pdfvec import extent, linear_map, paths, stream_of

# Figure 2, main PDF (page index 3). Colour of each method's line and markers, from the legend.
FIG2_COLOURS = {
    (0.88235, 0.76863, 0.0, 0.0): "Neighborhood",
    (0.62745, 0.0, 1.0, 0.0): "Oti1",
    (0.83922, 0.26274, 0.46275, 0.039216): "Oti2",
    (0.26667, 0.81569, 0.0, 0.0): "Oti3",
    (0.0, 0.99216, 1.0, 0.0): "GS1",
    (0.0, 0.40784, 1.0, 0.0): "GS2",
    (0.56863, 0.65098, 0.0, 0.0): "GS3",
    (0.0, 0.0, 0.0, 1.0): "GS-All",
    (0.87451, 0.24314, 1.0, 0.12941): "MCL",
    (0.5098, 0.36078, 1.0, 0.13333): "VI-CutL",
    (0.0, 0.76078, 0.73333, 0.0): "VI-CutS",
    (0.0, 0.0, 0.0, 0.498): "Prop",
    (0.51765, 0.0, 0.12549, 0.0): "RW",
    (0.43529, 0.63137, 0.56078, 0.22745): "Consensus",
}
# Supplementary Figure S1 (R's colour names in RGB).
S1_COLOURS = {
    (0.0, 0.0, 1.0): "Neighborhood",
    (0.0, 1.0, 0.0): "Oti1",
    (0.0, 0.545, 0.545): "Oti2",
    (1.0, 0.0, 1.0): "Oti3",
    (1.0, 0.0, 0.0): "GS1",
    (1.0, 0.647, 0.0): "GS2",
    (0.6, 0.4, 1.0): "GS3",
    (0.0, 0.0, 0.0): "GS-All",
    (0.0, 0.502, 0.0): "MCL",
    (0.502, 0.502, 0.0): "VI-CutL",
    (1.0, 0.388, 0.278): "VI-CutS",
    (0.502, 0.502, 0.502): "Prop",
    (0.0, 1.0, 1.0): "RW",
}

# Panel boxes (PDF points) and axis calibration from the tick marks in the content streams.
FIG2_PANELS = {
    # name: (x0, y0, x1, y1) box of the plotting region; x ticks (pos, value) x2; y ticks x2
    "fig2a": {"box": (137.0, 639.0, 331.0, 830.0), "x": (144.965, 0.0, 322.749, 40.0), "y": (646.165, 0.0, 820.507, 100.0)},
    "fig2b": {"box": (135.0, 413.0, 331.0, 600.0), "x": (142.907, 0.0, 320.692, 20.0), "y": (420.437, 20.0, 594.777, 80.0)},
}
S1_AXES = {"x": (119.53, 0.0, 722.87, 40.0), "y": (104.67, 0.0, 696.33, 100.0)}


def key(c, table):
    for k, v in table.items():
        if c is not None and len(c) == len(k) and all(abs(a - b) < 2e-3 for a, b in zip(c, k)):
            return v
    return None


def series(ps, table, line_width, box=None, min_extent=4.0):
    """Polylines drawn at the series line width, in drawing order, as {method: [(x, y), ...]}.

    A method with a single point is drawn as a zero-length line. Stroked glyph outlines (labels)
    use the same width but span less than `min_extent` points, so they are skipped.
    """
    out: dict[str, list] = {}
    cands: dict[str, list] = {}
    for p in ps:
        if "op" not in p or p["op"] != "S" or abs(p["w"] - line_width) > 1e-3:
            continue
        m = key(p["stroke"], table)
        if m is None:
            continue
        for s in p["subs"]:
            v = s["v"]
            if s["rect"] is not None or s["closed"] or s["curve"] or len(v) < 2:
                continue
            if box and not all(box[0] <= x <= box[2] and box[1] <= y <= box[3] for x, y in v):
                continue
            degenerate = extent(v) < 1e-6
            if not degenerate and extent(v) < min_extent:
                continue
            if not degenerate and abs(v[0][0] - v[-1][0]) < 1e-3 and abs(v[0][1] - v[-1][1]) < 1e-3:
                continue  # a closed outline (a diamond or triangle marker), not a series line
            cands.setdefault(m, []).append((degenerate, v))
    # The series is the polyline with the most vertices; a method with one point is drawn as a
    # zero-length line, preferred over the two-vertex strokes of '+' and 'x' markers.
    for m, lst in cands.items():
        most = max(len(v) for d, v in lst if not d) if any(not d for d, _ in lst) else 0
        if most > 2:
            out[m] = next(v for d, v in lst if not d and len(v) == most)
        else:
            deg = [v for d, v in lst if d]
            out[m] = [deg[0][0]] if deg else next(v for d, v in lst)
    return out


def calibrate(pts, ax):
    fx = linear_map(*ax["x"])
    fy = linear_map(*ax["y"])
    return [[round(fx(x), 4), round(fy(y), 4)] for x, y in pts]


def fig2(main_pdf):
    ps = paths(stream_of(main_pdf, 3))
    out = {}
    for name, panel in FIG2_PANELS.items():
        s = series(ps, FIG2_COLOURS, 0.884, panel["box"])
        out[name] = {m: calibrate(v, panel) for m, v in s.items()}
    return out


def fig_s1(supp_pdf):
    ps = paths(stream_of(supp_pdf, 6, "Im1"))
    s = series(ps, S1_COLOURS, 3.0, (95.4, 81.0, 747.0, 720.0), min_extent=8.0)
    return {m: calibrate(v, S1_AXES) for m, v in s.items()}


# ---------------------------------------------------------------- Figure 4 and S2 (matplotlib)
BAR_FILL_MAIN = (0.30196, 0.13725, 1.0, 0.0)
FIG4_LINE = {
    (0.88235, 0.76863, 0.0, 0.0): "Neighborhood",
    (0.0, 0.0, 0.0, 1.0): "GS-All",
    (0.5098, 0.36078, 1.0, 0.13333): "VI-CutL",
    (0.51765, 0.0, 0.12549, 0.0): "RW",
    (0.0, 0.0, 0.0, 0.49804): "Prop",
}


def _bars(ps, fill, box):
    bars = []
    for p in ps:
        if "op" not in p or p["fill"] is None or key(p["fill"], {fill: 1}) is None:
            continue
        for s in p["subs"]:
            xs = [v[0] for v in s["v"]]
            ys = [v[1] for v in s["v"]]
            if not (box[0] - 1 <= min(xs) and max(xs) <= box[2] + 1 and box[1] - 1 <= min(ys) and max(ys) <= box[3] + 1):
                continue
            if max(xs) - min(xs) < 3:
                continue
            bars.append((round(min(xs), 3), round(max(xs), 3), round(min(ys), 3), round(max(ys), 3)))
    return sorted(set(bars))


def _lines(ps, table, box, min_len=40.0):
    """Least-squares lines: the longest straight 2-vertex stroke of each method colour."""
    out = {}
    for p in ps:
        if "op" not in p or p["op"] != "S":
            continue
        m = key(p["stroke"], table)
        if m is None:
            continue
        for s in p["subs"]:
            v = s["v"]
            if s["rect"] is not None or s["curve"] or len(v) < 2:
                continue
            if not all(box[0] - 1 <= x <= box[2] + 1 and box[1] - 1 <= y <= box[3] + 1 for x, y in v):
                continue
            ln = ((v[-1][0] - v[0][0]) ** 2 + (v[-1][1] - v[0][1]) ** 2) ** 0.5
            if ln >= min_len and (m not in out or ln > out[m][0]):
                out[m] = (ln, v[0], v[-1])
    return {m: (a, b) for m, (_, a, b) in out.items()}


def _errorbars(ps, box, bars):
    """Vertical black strokes centred on a bar: (x, y_low, y_high)."""
    centres = [((b[0] + b[1]) / 2) for b in bars]
    out = []
    for p in ps:
        if "op" not in p or p["op"] != "S":
            continue
        if key(p["stroke"], {(0.0, 0.0, 0.0, 1.0): 1}) is None:
            continue
        for s in p["subs"]:
            v = s["v"]
            if len(v) != 2 or abs(v[0][0] - v[1][0]) > 1e-3 or abs(v[0][1] - v[1][1]) < 1:
                continue
            x = v[0][0]
            if not (box[0] <= x <= box[2] and box[1] - 1 <= min(v[0][1], v[1][1]) and max(v[0][1], v[1][1]) <= box[3] + 1):
                continue
            if min(abs(x - c) for c in centres) < 0.5:
                out.append((round(x, 3), round(min(v[0][1], v[1][1]), 3), round(max(v[0][1], v[1][1]), 3)))
    return sorted(set(out))


FIVE = ["Neighborhood", "GS-All", "VI-CutL", "RW", "Prop"]  # legend order, which is the drawing order


def fit_lines(ps, width, box, to_data, slack=40.0):
    """The five least-squares lines of a homophily panel, in drawing order (= legend order).

    matplotlib draws each as a polyline through the fitted value at every disease; the publisher's
    colour conversion drew GS-All in blue, so lines are identified by order, not colour. Returns
    {method: {slope, intercept, vertices, x_min, x_max}} in data units.
    """
    import numpy as np

    found = []
    for p in ps:
        if "op" not in p or p["op"] != "S" or abs(p["w"] - width) > 1e-3:
            continue
        for s in p["subs"]:
            v = s["v"]
            if len(v) >= 5 and extent(v) > 50 and all(
                    box[0] - 1 <= x <= box[2] + 1 and box[1] - slack <= y <= box[3] + slack for x, y in v):
                found.append(v)
    out = {}
    for m, v in zip(FIVE, found):
        xy = np.array([to_data(x, y) for x, y in v])
        slope, icpt = np.polyfit(xy[:, 0], xy[:, 1], 1)
        out[m] = {"slope": round(float(slope), 5), "intercept": round(float(icpt), 5), "vertices": len(v),
                  "x_min": round(float(xy[:, 0].min()), 4), "x_max": round(float(xy[:, 0].max()), 4)}
    return out


# x calibration of Figure 4 (bar index axis): homophily h is drawn at x = 10 h (panel a, bars of
# width 0.8 at 0, 1, ..., 9); pairwise distance d at x = d - 1 (panel b, bars of width 0.5). One x
# unit is the spacing of the bars (18.667 pt in panel a, 37.335 pt in panel b).
FIG4_X = {"fig4a": (407.922, None, lambda x: x / 10), "fig4b": (411.272, None, lambda x: x + 1)}


def fig4(main_pdf, axes):
    """Bars (mean F1 per homophily bin), error bars and fitted lines of Figure 4a and 4b."""
    ps = paths(stream_of(main_pdf, 4))
    out = {}
    for name, ax in axes.items():
        fy = linear_map(*ax["y"])
        box = ax["box"]
        bars = _bars(ps, BAR_FILL_MAIN, box)
        errs = _errorbars(ps, box, bars)
        x0, _, measure = FIG4_X[name]
        unit = (bars[-1][0] - bars[0][0]) / (len(bars) - 1)  # bar spacing = one x unit
        rec = {
            "bars": [{"x0": b[0], "x1": b[1], "height": round(fy(b[3]), 5)} for b in bars],
            "errorbars": [{"x": e[0], "low": round(fy(e[1]), 5), "high": round(fy(e[2]), 5)} for e in errs],
            "lines": fit_lines(ps, 0.836, box, lambda x, y: (measure((x - x0) / unit), fy(y))),
        }
        out[name] = rec
    return out


# Figure 4 (main PDF, page index 4): y ticks 0.0-1.0 at these PDF y positions (axis 0 to 1.05);
# x is the bar index, read from the bar centres.
FIG4_AXES = {
    "fig4a": {"box": (407.9, 685.3, 594.7, 829.9), "y": (685.322, 0.0, 822.96, 1.0)},
    "fig4b": {"box": (411.2, 515.5, 598.0, 660.1), "y": (515.51, 0.0, 653.148, 1.0)},
}
# Supplementary Figure S2 (page index 7): four matplotlib panels, axes box 72-518.4 x 43.2-388.8,
# y from 0 to 1.05 as in Figure 4 (the bars of Figure 4 fit this scale to 0.001).
S2_PANELS = {"a_precision": "Im2", "a_recall": "Im3", "b_precision": "Im4", "b_recall": "Im5"}
S2_FILL = (0.75, 0.75, 0.0)


def fig_s2(supp_pdf):
    out = {}
    fy = linear_map(43.2, 0.0, 388.8, 1.05)
    for name, im in S2_PANELS.items():
        ps = paths(stream_of(supp_pdf, 7, im))
        bars = []
        for p in ps:
            if "op" not in p or p["fill"] is None or key(p["fill"], {S2_FILL: 1}) is None:
                continue
            for s in p["subs"]:
                v = s["v"]
                xs = [a for a, _ in v]
                ys = [b for _, b in v]
                if abs(min(ys) - 43.2) < 0.01 and max(xs) - min(xs) > 5:
                    bars.append((round(min(xs), 3), round(max(xs), 3), round(max(ys), 4)))
        bars = sorted(set(bars))
        out[name] = [round(fy(h), 5) for _, _, h in bars]
        out.setdefault("_x", {})[name] = [[a, b] for a, b, _ in bars]
        # panel a: homophily h at x = 72 + 446.4 h; panel b: distance d at x = 72 + 89.28 (d - 1)
        if name.startswith("a"):
            to_data = lambda x, y: ((x - 72.0) / 446.4, fy(y))  # noqa: E731
        else:
            to_data = lambda x, y: ((x - 72.0) / 89.28 + 1, fy(y))  # noqa: E731
        out.setdefault("_lines", {})[name] = fit_lines(ps, 2.0, (72.0, 43.2, 518.4, 388.8), to_data, slack=400.0)
        errs = []
        for p in ps:
            if "op" not in p or p["op"] != "S" or abs(p["w"] - 1.0) > 1e-3:
                continue  # error bars are 1-pt vertical strokes at the bar centres
            for s in p["subs"]:
                v = s["v"]
                if len(v) == 2 and abs(v[0][0] - v[1][0]) < 1e-3 and abs(v[0][1] - v[1][1]) > 0.5 and 72 < v[0][0] < 518.4:
                    errs.append((round(v[0][0], 3), round(fy(min(v[0][1], v[1][1])), 5), round(fy(max(v[0][1], v[1][1])), 5)))
        out.setdefault("_errorbars", {})[name] = [list(e) for e in sorted(set(errs))]
    return out


def main(argv):
    main_pdf, supp_pdf, out_path = argv[1:4]
    res = {"source": {"paper": "PMC2853684.1.pdf", "supplement": "btq076_1.pdf"}}
    res.update(fig2(main_pdf))
    res["figS1"] = fig_s1(supp_pdf)
    res.update(fig4(main_pdf, FIG4_AXES))
    res["figS2"] = fig_s2(supp_pdf)
    with open(out_path, "w") as f:
        json.dump(res, f, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
