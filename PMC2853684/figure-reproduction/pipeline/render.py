"""Our figures, and our values drawn on the published ones.

    render.py analysis.json published_values.json PUBLISHED_DIR OUT_DIR

For each figure:
- `<fig>_ours.png`: our values drawn on their own, on the published figure's frame: the same pixel
  size as the published crop (300 dpi), the axes box where the published one is (read from the PDF),
  the same data limits, ticks, bar positions, line extents and point sizes;
- `<fig>_overlay.png`: the published figure in grey with our values on top in magenta (points and
  lines of Figs 2 and S1; bar tops, error-bar ends and least-squares lines of Figs 4 and S2; cell
  counts and margins of Fig. 3).
Our values are placed with the axis calibrations read from the PDFs (read_published.py), so a
magenta mark sits on the published mark when the two agree.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image, ImageDraw, ImageOps  # noqa: E402

from pdfvec import linear_map  # noqa: E402
from read_published import FIG2_PANELS, FIG4_AXES, S1_AXES  # noqa: E402

matplotlib.rcParams.update({"font.family": "DejaVu Sans", "axes.linewidth": 0.6, "xtick.major.width": 0.6,
                            "ytick.major.width": 0.6, "savefig.dpi": 300})
MAGENTA = (220, 0, 160)
# R colours and point characters of Fig. 2 (the supplement's RGB values); matplotlib markers alike.
STYLE = {
    "Neighborhood": ("#0000FF", "s"), "Oti1": ("#00FF00", "^"), "Oti2": ("#008B8B", "+"), "Oti3": ("#FF00FF", "s"),
    "GS1": ("#FF0000", "D"), "GS2": ("#FFA500", "X"), "GS3": ("#9966FF", "v"), "GS-All": ("#000000", "x"),
    "MCL": ("#008000", "o"), "VI-CutL": ("#808000", "*"), "VI-CutS": ("#FF6347", "o"), "Prop": ("#808080", "^"),
    "RW": ("#00FFFF", "s"), "Consensus": ("#8B4513", "D"),
}
FIVE = ["Neighborhood", "GS-All", "VI-CutL", "RW", "Prop"]
FIVE_STYLE = {"Neighborhood": ("#3050b0", "s"), "GS-All": ("#000000", "x"), "VI-CutL": ("#808000", "*"),
              "RW": ("#66d0e0", "p"), "Prop": ("#999999", "D")}
BAR_MAIN = "#bdbe32"  # Fig. 4 bars (publisher's CMYK 0.30 0.14 1 0)
BAR_SUPP = "#bfbf00"  # Supp. Fig. S2 bars (RGB 0.75 0.75 0)
# Placement of the supplement's figure XObjects on their pages: (x, y, scale).
S1_PLACE = (153.901, 277.641, 0.40237)
S2_PLACE = {"a_precision": (79.544, 463.814, 0.40506), "a_recall": (307.818, 463.814, 0.40773),
            "b_precision": (79.544, 293.646, 0.40295), "b_recall": (307.818, 293.646, 0.4019)}
# Axes boxes in PDF points (x0, y0, x1, y1), from the content streams.
BOX = {
    "fig2a": (137.855, 639.19, 137.855 + 192.005, 639.19 + 188.292),
    "fig2b": (135.799, 413.461, 135.799 + 192.004, 413.461 + 188.292),
    "fig3": (141.9, 659.7, 308.4, 826.1),
    "fig3_bar": (319.1, 659.7, 327.4, 826.1),
    "fig4a": (407.922, 685.322, 407.922 + 10 * 168.0 / 9, 685.322 + 1.05 * 137.638),
    "fig4b": (411.272, 515.51, 411.272 + 5 * 149.34 / 4, 515.51 + 1.05 * 137.638),
}
S1_BOX = (95.40, 81.00, 747.00, 720.00)  # in the XObject
S2_BOX = (72.0, 43.2, 518.4, 388.8)  # in each XObject
BIN_A = ["<10", "10-19", "20-29", "30-39", "40-49", "50-59", "60-69", "70-79", "80-89", "90-100"]
BIN_B = ["1-2", "2-3", "3-4", "4-5", "> 5"]


class Placer:
    """PDF points of a page -> pixels of a published crop."""

    def __init__(self, crop, dpi):
        self.x0, self.top = crop["box_points"][0], crop["box_points"][1]
        self.h = crop["page_height"]
        self.s = dpi / 72
        self.size = crop["size_px"]

    def __call__(self, x, y):
        return ((x - self.x0) * self.s, (self.h - y - self.top) * self.s)


def placed(box, place):
    if place is None:
        return box
    x, y, s = place
    return (x + s * box[0], y + s * box[1], x + s * box[2], y + s * box[3])


def canvas(crop, dpi):
    w, h = crop["size_px"]
    fig = plt.figure(figsize=(w / dpi, h / dpi), dpi=dpi)
    return fig, Placer(crop, dpi)


def axes_at(fig, P, box):
    """Axes whose plotting box is `box` (PDF points of the page)."""
    W, H = P.size
    (l, t), (r, b) = P(box[0], box[3]), P(box[2], box[1])
    return fig.add_axes([l / W, 1 - b / H, (r - l) / W, (b - t) / H])


def inv(cal):
    p0, v0, p1, v1 = cal
    return lambda v: p0 + (v - v0) * (p1 - p0) / (v1 - v0)


def limits(cal, lo, hi):
    f = linear_map(*cal)
    return f(lo), f(hi)


def grey(path):
    im = Image.open(path).convert("L")
    im = ImageOps.autocontrast(im)
    im = Image.eval(im, lambda v: 255 - int((255 - v) * 0.45))
    return im.convert("RGB")


def mark(d, x, y, r=4, w=2):
    d.ellipse([x - r, y - r, x + r, y + r], outline=MAGENTA, width=w)


# ------------------------------------------------------------------ Figs 2 and S1 (curves)
def ours_curves(series, crop, dpi, box, cal_x, cal_y, ticks_x, ticks_y, out, fs, legend_methods, place=None, ms=5.5):
    fig, P = canvas(crop, dpi)
    b = placed(box, place)
    ax = axes_at(fig, P, b)
    for m, pts in series.items():
        if not pts:
            continue
        col, mk = STYLE[m]
        ax.plot([p[0] for p in pts], [p[1] for p in pts], "-", color=col, lw=fs["lw"], marker=mk, ms=ms, mfc="none",
                mew=fs["lw"] * 0.8, label=m if m in legend_methods else None)
    ax.set_xlim(*limits(cal_x, box[0], box[2]))
    ax.set_ylim(*limits(cal_y, box[1], box[3]))
    ax.set_xticks(ticks_x)
    ax.set_yticks(ticks_y)
    ax.tick_params(labelsize=fs["tick"], length=2.6 * fs["scale"], width=0.5)
    for lab in ax.get_yticklabels():
        lab.set_rotation(90)
        lab.set_va("center")
    ax.set_xlabel("Recall (% disease associations recovered)", fontsize=fs["label"])
    ax.set_ylabel("Precision (% predictions correct)", fontsize=fs["label"])
    leg = ax.legend(fontsize=fs["legend"], loc="upper right", frameon=True, fancybox=False, edgecolor="black",
                    handlelength=0, markerscale=0.7, borderpad=0.5, labelspacing=0.25)
    leg.get_frame().set_linewidth(0.5)
    fig.savefig(out)
    plt.close(fig)


def overlay_curves(pub_png, crop, dpi, series, fx, fy, out, place=None):
    im = grey(pub_png)
    d = ImageDraw.Draw(im)
    P = Placer(crop, dpi)
    for m, pts in series.items():
        xy = []
        for r, p in pts:
            X, Y = fx(r), fy(p)
            if place:
                X, Y = place[0] + place[2] * X, place[1] + place[2] * Y
            xy.append(P(X, Y))
        if len(xy) > 1:
            d.line(xy, fill=MAGENTA, width=2)
        for x, y in xy:
            mark(d, x, y)
    im.save(out, optimize=True)


# ------------------------------------------------------------- Figs 4 and S2 (homophily bars)
def homophily_axes(ax, bars, err, counts, fits, panel, ylabel, xlabel, fs, legend_loc, show_counts=True):
    """Bars, error bars, disease counts and the five lines, on the bar-index axis of the paper:
    panel a puts homophily h at x = 10 h (bars of width 0.8 at 0..9); panel b puts distance d at
    x = d - 1 (bars of width 0.5 at 0..4)."""
    n = 10 if panel == "a" else 5
    width = 0.8 if panel == "a" else 0.5
    to_x = (lambda v: 10 * v) if panel == "a" else (lambda v: v - 1)
    colour = BAR_MAIN if fs.get("main", True) else BAR_SUPP
    ax.bar(np.arange(n), [b or 0 for b in bars], width=width, align="edge", color=colour, edgecolor="black",
           linewidth=0.6 * fs["scale"], zorder=1)
    for i, e in enumerate(err):
        if e:
            ax.errorbar(i + width / 2, bars[i] or 0, yerr=e, color="black", lw=0.5 * fs["scale"], capsize=1.6 * fs["scale"],
                        capthick=0.5 * fs["scale"], zorder=3)
    if show_counts:
        for i, c in enumerate(counts):
            ax.text(i + width / 2, 0.03, str(c), ha="center", fontsize=fs["count"], zorder=4)
    for m in FIVE:
        f = fits[m]
        xs = np.array([to_x(v) for v in f["x"]])
        ys = f["intercept"] + f["slope"] * np.array(f["x"])
        col, mk = FIVE_STYLE[m]
        ax.plot(xs, ys, "-", color=col, lw=1.0 * fs["scale"], marker=mk, ms=2.2 * fs["scale"], mec="black",
                mew=0.3 * fs["scale"], zorder=2, label=f"{m} ({f['r']:.2f})")
    ax.set_xlim(0, n)
    ax.set_ylim(0, 1.05)
    ax.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_xticks(np.arange(n) + width / 2)
    ax.set_xticklabels(BIN_A if panel == "a" else BIN_B)
    ax.tick_params(labelsize=fs["tick"], length=2.5 * fs["scale"], width=0.5 * fs["scale"], direction="in",
                   top=True, right=True)
    ax.tick_params(axis="x", labelsize=fs["xtick"], top=False)
    ax.set_xlabel(xlabel, fontsize=fs["label"], labelpad=1)
    ax.set_ylabel(ylabel, fontsize=fs["label"], labelpad=1)
    for sp in ax.spines.values():
        sp.set_linewidth(0.6 * fs["scale"])
    leg = ax.legend(fontsize=fs["legend"], loc=legend_loc, frameon=True, fancybox=False, edgecolor="black",
                    handlelength=2.2, borderpad=0.4, labelspacing=0.35)
    leg.get_frame().set_linewidth(0.6 * fs["scale"])


def overlay_homophily(im, P, box, panel, bars, err, fits, place=None, ymax=1.05):
    """Our bar tops, error-bar ends and lines on a published homophily panel."""
    d = ImageDraw.Draw(im)
    b = placed(box, place)
    n = 10 if panel == "a" else 5
    width = 0.8 if panel == "a" else 0.5
    fx = lambda x: b[0] + (b[2] - b[0]) * x / n  # noqa: E731
    fy = lambda y: b[1] + (b[3] - b[1]) * y / ymax  # noqa: E731
    to_x = (lambda v: 10 * v) if panel == "a" else (lambda v: v - 1)
    for i, h in enumerate(bars):
        if h is None:
            continue
        d.line([P(fx(i), fy(h)), P(fx(i + width), fy(h))], fill=MAGENTA, width=3)
        e = err[i]
        if e:
            for v in (h - e, h + e):
                c = i + width / 2
                d.line([P(fx(c - 0.12 * width), fy(v)), P(fx(c + 0.12 * width), fy(v))], fill=MAGENTA, width=3)
    for m in FIVE:
        f = fits[m]
        x0, x1 = to_x(min(f["x"])), to_x(max(f["x"]))
        y0 = f["intercept"] + f["slope"] * min(f["x"])
        y1 = f["intercept"] + f["slope"] * max(f["x"])
        d.line([P(fx(x0), fy(y0)), P(fx(x1), fy(y1))], fill=MAGENTA, width=2)


def main(argv):
    a = json.load(open(argv[1]))
    pub = json.load(open(argv[2]))
    pdir = Path(argv[3])
    out = Path(argv[4])
    out.mkdir(parents=True, exist_ok=True)
    meta = json.load(open(pdir / "crops.json"))
    dpi = meta["dpi"]
    crops = meta["crops"]
    single = ["Neighborhood", "Oti1", "Oti2", "Oti3", "GS1", "GS2", "GS3", "GS-All", "MCL", "VI-CutL", "VI-CutS", "Prop", "RW"]

    # Fig. 2a, 2b and S1: fonts and marks at the published sizes (points)
    fs2 = {"tick": 10.0, "label": 8.8, "legend": 6.3, "lw": 0.9, "scale": 1.0}
    pa, pb = FIG2_PANELS["fig2a"], FIG2_PANELS["fig2b"]
    series = dict(a["fig2a"])
    ours_curves(series, crops["fig2a"], dpi, BOX["fig2a"], pa["x"], pa["y"], [0, 10, 20, 30, 40],
                [0, 20, 40, 60, 80, 100], out / "fig2a_ours.png", fs2, single + ["Consensus"])
    overlay_curves(pdir / "fig2a.png", crops["fig2a"], dpi, series, inv(pa["x"]), inv(pa["y"]), out / "fig2a_overlay.png")
    b_methods = ["Oti2", "Oti3", "GS1", "GS2", "GS-All", "MCL", "VI-CutL", "VI-CutS"]
    series_b = {m: [p for p in a["fig2a"][m] if 0 <= p[0] <= 20 and 20 <= p[1] <= 80] for m in b_methods}
    ours_curves(series_b, crops["fig2b"], dpi, BOX["fig2b"], pb["x"], pb["y"], [0, 5, 10, 15, 20],
                [20, 30, 40, 50, 60, 70, 80], out / "fig2b_ours.png", fs2, b_methods, ms=7.5)
    overlay_curves(pdir / "fig2b.png", crops["fig2b"], dpi, series_b, inv(pb["x"]), inv(pb["y"]), out / "fig2b_overlay.png")
    s = S1_PLACE[2]
    fsS1 = {"tick": 36 * s, "label": 33 * s, "legend": 23 * s, "lw": 3 * s, "scale": s}
    ours_curves(a["figS1"], crops["figS1"], dpi, S1_BOX, S1_AXES["x"], S1_AXES["y"], [0, 10, 20, 30, 40],
                [0, 20, 40, 60, 80, 100], out / "figS1_ours.png", fsS1, single, place=S1_PLACE, ms=20 * s)
    overlay_curves(pdir / "figS1.png", crops["figS1"], dpi, a["figS1"], inv(S1_AXES["x"]), inv(S1_AXES["y"]),
                   out / "figS1_overlay.png", place=S1_PLACE)

    # Fig. 3: heat map on the published box, colour bar alongside
    f3 = a["fig3"]
    mat = np.array(f3["matrix"], dtype=float)
    fig, P = canvas(crops["fig3"], dpi)
    ax = axes_at(fig, P, BOX["fig3"])
    # the published colour bar: pink at 0, bright red by 15, dark red near 60, black at 135
    cmap = matplotlib.colors.LinearSegmentedColormap.from_list(
        "r", [(0.0, "#f4a9a9"), (0.04, "#ef5050"), (0.1, "#e82424"), (0.42, "#8e1616"), (1.0, "#000000")])
    cmap.set_bad("white")
    im = ax.imshow(np.where(mat > 0, mat, np.nan), origin="lower", extent=(0, 1, 0, 1), cmap=cmap, vmin=0, vmax=142,
                   aspect="auto", interpolation="nearest")
    for i in range(10):
        for j in range(10):
            if mat[i][j]:
                ax.text((j + 0.5) / 10, (i + 0.5) / 10, str(int(mat[i][j])), ha="center", va="center", fontsize=4.5,
                        color="white" if mat[i][j] > 60 else "black")
    for j, c in enumerate(f3["columns"]):
        ax.text((j + 0.5) / 10, 1.012, str(c), ha="center", va="bottom", fontsize=5.8)
    for i, c in enumerate(f3["rows_top_down"]):
        ax.text(1.008, 1 - (i + 0.5) / 10, str(c), va="center", fontsize=5.8)
    ax.set_xticks([0, 0.2, 0.4, 0.6, 0.8])
    ax.set_yticks([0, 0.2, 0.4, 0.6, 0.8])
    ax.set_xticks(np.arange(0.1, 1.0, 0.1), minor=True)
    ax.set_yticks(np.arange(0.1, 1.0, 0.1), minor=True)
    ax.grid(True, which="both", ls="--", color="k", lw=0.4)
    ax.tick_params(labelsize=7.5, length=2, which="both")
    ax.set_xlabel("Max. recall amongst all 13 methods", fontsize=9)
    ax.set_ylabel("Max. precision amongst all 13 methods", fontsize=9)
    cax = axes_at(fig, P, BOX["fig3_bar"])
    cb = fig.colorbar(im, cax=cax, ticks=list(range(0, 142, 15)))
    cb.ax.tick_params(labelsize=7.5, length=2)
    fig.savefig(out / "fig3_ours.png")
    plt.close(fig)
    im3 = grey(pdir / "fig3.png")
    d = ImageDraw.Draw(im3)
    P = Placer(crops["fig3"], dpi)
    x0, y0, x1, y1 = BOX["fig3"]
    cw, ch = (x1 - x0) / 10, (y1 - y0) / 10
    for i in range(10):
        for j in range(10):
            if mat[i][j]:
                px, py = P(x0 + (j + 0.5) * cw, y0 + (i + 0.5) * ch)
                d.text((px - 6, py - 6), str(int(mat[i][j])), fill=MAGENTA)
    for j, c in enumerate(f3["columns"]):
        px, py = P(x0 + (j + 0.5) * cw, y1 + 9)
        d.text((px - 6, py - 22), str(c), fill=MAGENTA)
    for i, c in enumerate(f3["rows_top_down"]):
        px, py = P(x1 + 14, y1 - (i + 0.5) * ch)
        d.text((px + 18, py - 6), str(c), fill=MAGENTA)
    im3.save(out / "fig3_overlay.png", optimize=True)

    # Fig. 4: on the published boxes (bar-index x axis, y 0 to 1.05)
    fs4 = {"tick": 8.2, "xtick": 5.2, "label": 8.4, "legend": 5.6, "count": 6.8, "scale": 1.0, "main": True}
    for k, panel, xl, loc in (("fig4a", "a", "Neighborhood Homophily (%)", "upper left"),
                              ("fig4b", "b", "Avg. pairwise distance among disease-associated proteins", "upper right")):
        fs4 = dict(fs4, label=8.4 if panel == "a" else 6.6, xtick=5.2 if panel == "a" else 7.8)
        fig, P = canvas(crops[k], dpi)
        ax = axes_at(fig, P, BOX[k])
        homophily_axes(ax, a[k]["bars"], a[k]["spreads"]["var_values"], a[k]["counts"], a[k]["fits"], panel,
                       "F1-measure of disease predictions", xl, fs4, loc)
        fig.savefig(out / f"{k}_ours.png")
        plt.close(fig)
        im4 = grey(pdir / f"{k}.png")
        overlay_homophily(im4, Placer(crops[k], dpi), BOX[k], panel, a[k]["bars"], a[k]["spreads"]["var_values"], a[k]["fits"])
        im4.save(out / f"{k}_overlay.png", optimize=True)

    # Supp. Fig. S2: four matplotlib panels at the supplement's scale
    fig, P = canvas(crops["figS2"], dpi)
    im2 = grey(pdir / "figS2.png")
    PS = Placer(crops["figS2"], dpi)
    for panel, place in S2_PLACE.items():
        sc = place[2]
        fsS2 = {"tick": 12 * sc, "xtick": 10 * sc, "label": 12 * sc, "legend": 10 * sc, "count": 10 * sc, "scale": sc * 2,
                "main": False}
        ax = axes_at(fig, P, placed(S2_BOX, place))
        part = panel.split("_")[0]
        key = panel.split("_")[1]
        counts = a["fig4a" if part == "a" else "fig4b"]["counts"]
        homophily_axes(ax, a["figS2"][panel], a["figS2"]["variance"][panel], counts, a["figS2"]["fits"][panel], part,
                       f"{key.capitalize()} of disease predictions",
                       "Neighborhood Homophily (%)" if part == "a" else "Avg. pairwise distance among disease-associated proteins",
                       fsS2, "upper left" if part == "a" else "upper right")
        overlay_homophily(im2, PS, S2_BOX, part, a["figS2"][panel], a["figS2"]["variance"][panel], a["figS2"]["fits"][panel],
                          place=place)
    fig.savefig(out / "figS2_ours.png")
    plt.close(fig)
    im2.save(out / "figS2_overlay.png", optimize=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
