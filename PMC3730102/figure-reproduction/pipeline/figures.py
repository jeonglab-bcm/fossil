"""Draw every attempted panel from our numbers, in the style of the published panel, and overlay the two.

figures.py PAPER_DIR OUT_DIR RUN_DIR OUTDIR

PAPER_DIR holds PMC's open-access PDF of the paper (PMC3730102.1.pdf). Its figures are vector graphics: the
pages are rendered at 600 dpi with pdftoppm and each published panel is cropped from them
(published/fig*.png). Each of our panels is drawn at the same pixel size and the same physical size, in the
published panel's layout (fig*_ours.png). The overlay puts the published panel in the red channel and ours
in green and blue (fig*_overlay.png): cyan is ink only in the paper, red ink only in ours, black both.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from PIL import Image  # noqa: E402
from scipy.cluster import hierarchy  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from settings import CONDITIONS, LOCATIONS  # noqa: E402

Image.MAX_IMAGE_PIXELS = None
DPI = 600
JET = plt.get_cmap("jet")
# Liberation Sans has Arial's metrics (the paper's figures are set in Arial); DejaVu Sans is the fallback.
FONT = "Liberation Sans" if any(f.name == "Liberation Sans" for f in font_manager.fontManager.ttflist) else "DejaVu Sans"
plt.rcParams.update({"font.family": FONT, "font.size": 6, "font.weight": "bold", "axes.labelweight": "bold",
                     "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
                     "xtick.major.size": 2, "ytick.major.size": 2, "svg.hashsalt": "colp",
                     "mathtext.fontset": "custom", "mathtext.rm": FONT, "mathtext.it": f"{FONT}:italic:bold",
                     "mathtext.bf": f"{FONT}:bold"})
LOC_LABELS = [x if x != "VU" else "VO" for x in LOCATIONS]  # the figures write vacuole as VO

# Where each figure sits in the PDF: its page and the top-left corner of the figure in the 600 dpi page render.
# Found once by normalised cross-correlation of PMC's figure JPEG against the render (0.92 to 0.98).
FIGURES = {
    "fig2": {"page": 4, "x0": 539, "y0": 606},
    "fig3": {"page": 5, "x0": 539, "y0": 580},
    "fig4": {"page": 7, "x0": 813, "y0": 598},
    "fig5": {"page": 8, "x0": 1084, "y0": 599},
    "fig6": {"page": 9, "x0": 1068, "y0": 600},
}
# Published panels: figure and crop box (left, top, right, bottom) in 600 dpi pixels from the figure's corner.
PANELS = {
    "fig2a": ("fig2", (0, 0, 1353, 1328)), "fig2b": ("fig2", (1353, 0, 2698, 1262)),
    "fig2c": ("fig2", (0, 1330, 1353, 2531)), "fig2d": ("fig2", (1353, 1290, 2698, 2531)),
    "fig2e": ("fig2", (2639, 0, 3992, 2531)),
    "fig3a": ("fig3", (0, 0, 450, 1060)), "fig3e": ("fig3", (0, 1068, 450, 2336)),
    "fig3i": ("fig3", (0, 2387, 1935, 3517)),
    "fig4a": ("fig4", (0, 0, 830, 1120)),
    "fig5a": ("fig5", (0, 0, 2897, 1030)), "fig5b": ("fig5", (0, 1027, 537, 2055)),
    "fig5c": ("fig5", (0, 2146, 537, 3117)),
    "fig6a": ("fig6", (0, 0, 406, 971)), "fig6b": ("fig6", (1131, 0, 1526, 971)),
    "fig6c": ("fig6", (0, 1024, 406, 2152)),
}
CLM_PANELS = {"fig3a": "NKX2-2", "fig3e": "CPB1", "fig4a": "KIF13A", "fig5b": "RNF138", "fig5c": "TLX3",
              "fig6a": "GFRA4", "fig6b": "PSPN", "fig6c": "RET"}
CLM_TITLES = {"fig4a": "Prediction", "fig6a": "GFRA4", "fig6b": "PSPN", "fig6c": "RET"}


def page_box(key):
    name, (l, t, r, b) = PANELS[key]
    f = FIGURES[name]
    return f["page"], (f["x0"] + l, f["y0"] + t, f["x0"] + r, f["y0"] + b)


def published_panels(pdf: Path, dest: Path) -> dict[str, tuple[int, int]]:
    """Render the figure pages at 600 dpi and crop every published panel; returns each panel's pixel size."""
    sizes = {}
    with tempfile.TemporaryDirectory() as tmp:
        for page in sorted({f["page"] for f in FIGURES.values()}):
            subprocess.run(["pdftoppm", "-r", str(DPI), "-f", str(page), "-l", str(page), "-png",
                            "-singlefile", str(pdf), f"{tmp}/p{page}"], check=True)
        for key in PANELS:
            page, box = page_box(key)
            im = Image.open(f"{tmp}/p{page}.png").convert("RGB").crop(box)
            im.save(dest / f"{key}.png", optimize=True)
            sizes[key] = im.size
    return sizes


SIZES: dict[str, tuple[int, int]] = {}


def figure_for(key):
    w, h = SIZES[key]
    return plt.figure(figsize=(w / DPI, h / DPI), dpi=DPI)


def save(fig, key, out):
    fig.savefig(out / f"{key}_ours.png", dpi=DPI, metadata={"Software": None})
    plt.close(fig)
    im = Image.open(out / f"{key}_ours.png")
    if im.size != SIZES[key]:  # rounding of the figure size: pad or crop to the published pixel size
        canvas = Image.new("RGBA", SIZES[key], "white")
        canvas.paste(im, (0, 0))
        canvas.save(out / f"{key}_ours.png", optimize=True)


def overlay(key, pub_dir, out):
    pub = Image.open(pub_dir / f"{key}.png").convert("L")
    ours = Image.open(out / f"{key}_ours.png").convert("L")
    rgb = np.stack([np.asarray(pub), np.asarray(ours), np.asarray(ours)], axis=2)
    Image.fromarray(rgb.astype(np.uint8)).save(out / f"{key}_overlay.png", optimize=True)


# ---------------------------------------------------------------- Fig. 2
def fig2a(d, out):
    fig = figure_for("fig2a")
    ax = fig.add_axes([0.17, 0.12, 0.8, 0.85])
    a, p = d["all_pairs"], d["ppi"]
    xs = [0, 1, 2, 4, 5, 6, 8]
    vals = [a["positive"], a["none"], a["negative"], p["positive"], p["none"], p["negative"], d["random"]]
    ax.bar(xs, vals, color="black", width=0.8)
    ax.errorbar([8], [d["random"]], yerr=[d["random_sd"]], color="black", capsize=2, lw=0.6)
    ax.axhline(d["random"], color="black", ls=(0, (2, 1)), lw=0.4)
    ax.set_xticks(xs[:6], ["+", "0", "−", "+", "0", "−"], fontsize=7)
    ax.tick_params(axis="x", length=0)
    ax.set_xlim(-0.7, 8.8)
    ax.set_ylim(0, 0.9)
    ax.set_yticks(np.arange(0, 0.91, 0.1), [f"{v:.1f}" for v in np.arange(0, 0.91, 0.1)])
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_ylabel("Location-sharing fraction", fontsize=6.5)
    for x0, x1, label in ((-0.4, 2.4, "All pairs"), (3.6, 6.4, "PPIs")):
        ax.annotate("", xy=(x0, -0.075), xytext=(x1, -0.075), xycoords=("data", "axes fraction"),
                    textcoords=("data", "axes fraction"), arrowprops={"arrowstyle": "-", "lw": 0.6})
        ax.text((x0 + x1) / 2, -0.13, label, ha="center", transform=ax.get_xaxis_transform(), fontsize=6.5)
    ax.text(8, -0.1, "Random", ha="center", transform=ax.get_xaxis_transform(), fontsize=6.5)
    top, low = p["positive"], p["negative"]
    ax.plot([4, 7], [top, top], color="black", lw=0.5)
    ax.plot([6, 7], [low, low], color="black", lw=0.5)
    ax.annotate("", xy=(7, low), xytext=(7, top), arrowprops={"arrowstyle": "<->", "lw": 0.5})
    pv = d["ppi_pos_minus_neg_p"]
    ax.text(7.2, (top + low) / 2, f"{top - low:.2f}\n(p {'< 0.001' if pv < 0.001 else f'= {pv:.3f}'})",
            va="center", fontsize=5.5)
    for i, (sym, txt) in enumerate((("+", "Positive correlation"), ("0", "No"), ("−", "Negative"))):
        ax.text(0.0, 0.86 - i * 0.065, f"{sym} : ", fontsize=6.5)
        ax.text(0.55, 0.86 - i * 0.065, txt, fontsize=6, style="italic")
    fig.text(0.0, 0.97, "A", fontsize=10, va="top")
    save(fig, "fig2a", out)


def fig2b(d, out):
    fig = figure_for("fig2b")
    ax = fig.add_axes([0.16, 0.13, 0.8, 0.83])
    styles = [("single+physical+correlated", "#e00000", "-", "XXX"), ("physical+correlated", "#00a050", "-.", " XX"),
              ("physical", "#0000c0", (0, (2, 1)), " X "), ("correlated", "black", (0, (6, 3)), "  X")]
    for key, c, ls, _ in styles:
        ax.plot(d[key]["roc_fpr"], d[key]["roc_tpr"], color=c, ls=ls, lw=0.9)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ticks = np.arange(0, 1.01, 0.2)
    ax.set_xticks(ticks, [f"{t:.1f}" for t in ticks])
    ax.set_yticks(ticks, [f"{t:.1f}" for t in ticks])
    ax.set_xlabel("1-Specificity", fontsize=6.5)
    ax.set_ylabel("Sensitivity", fontsize=6.5)
    # the legend table: line, AUC value, and an X under each kind of feature used
    cols = [0.70, 0.78, 0.92]  # single-protein features, physical binding pairs, correlated pairs
    for i, (key, c, ls, marks) in enumerate(styles):
        y = 0.07 + (3 - i) * 0.06
        ax.plot([0.36, 0.48], [y, y], color=c, ls=ls, lw=0.9, transform=ax.transAxes)
        ax.text(0.51, y, f"{d[key]['mean_auc']:.2f}", va="center", fontsize=5, transform=ax.transAxes)
        for j, mk in enumerate(marks):
            if mk == "X":
                ax.text(cols[j], y, "X", va="center", ha="center", fontsize=5, transform=ax.transAxes)
    for x, h in zip([0.54] + cols, ["AUC value", "Single protein features", "Physical binding pairs",
                                     "Correlated pairs"]):
        ax.text(x, 0.33, h, rotation=90, va="bottom", ha="center", fontsize=4.5, style="italic",
                transform=ax.transAxes)
    ax.plot([0.66, 0.82], [0.66, 0.66], color="black", lw=0.4, transform=ax.transAxes)
    ax.text(0.74, 0.675, "static features", fontsize=4.5, style="italic", ha="center", transform=ax.transAxes)
    ax.text(0.92, 0.58, "dynamic", fontsize=4.5, style="italic", ha="center", transform=ax.transAxes)
    fig.text(0.0, 0.99, "B", fontsize=10, va="top")
    save(fig, "fig2b", out)


def fig2c(d, out):
    fig = figure_for("fig2c")
    ax = fig.add_axes([0.2, 0.17, 0.72, 0.75])
    for k, c in (("common", "black"), ("normal", "#00a050"), ("low", "#0000c0"), ("high", "#e00000")):
        y = np.array(d[k], dtype=float)
        ax.plot(d["x"], np.where(y > 0, y, np.nan), color=c, lw=0.9, label=k.capitalize())
    ax.axhline(d["random"], color="black", ls=(0, (3, 2)), lw=0.6, label="Random expection")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(1e2, 1e6)
    ax.set_ylim(1e-6, 1)
    ax.set_xticks([1e2, 1e3, 1e4, 1e5, 1e6], ["1.0E+2", "1.0E+3", "1.0E+4", "1.0E+5", "1.0E+6"])
    ax.set_yticks([10.0 ** -k for k in range(6, -1, -1)], [f"1.E{-k}" if k else "1.E+0" for k in range(6, -1, -1)])
    ax.minorticks_off()
    ax.set_xlabel("No. of protein pairs with high correlation", fontsize=6.5)
    ax.set_ylabel("Fraction of protein pairs", fontsize=6.5)
    ax.legend(fontsize=5, frameon=False, loc="lower left", bbox_to_anchor=(0.18, 0.1), handlelength=2.5)
    fig.text(0.0, 0.99, "C", fontsize=10, va="top")
    save(fig, "fig2c", out)


def fig2d(d, out):
    fig = figure_for("fig2d")
    ax = fig.add_axes([0.16, 0.18, 0.8, 0.76])
    keys = ["S", "N1", "N2", "L1", "L2", "TR"]
    xs = [0, 1, 2, 3, 4, 5.6]
    vals = [d[k] for k in keys]
    ax.bar(xs, vals, color="black", width=0.8)
    for x, v in zip(xs, vals):
        ax.text(x, v + 0.02, f"{v:.2f}", ha="center", fontsize=6)
    ax.set_xticks(xs, ["$S$", "$N^1$", "$N^2$", "$L^1$", "$L^2$", "TR"], fontsize=6.5)
    ax.tick_params(axis="x", length=0)
    ax.set_ylim(0, 1)
    ticks = np.arange(0, 1.01, 0.2)
    ax.set_yticks(ticks, [f"{t:.1f}" for t in ticks])
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_ylabel("AUC value", fontsize=6.5)
    ax.set_xlabel("Kinds of feature", fontsize=6.5)
    fig.text(0.0, 0.99, "D", fontsize=10, va="top")
    save(fig, "fig2d", out)


def set_label(name):
    """S_GO -> $S$_GO, N1_dAA -> $N^1$_dAA, as the figure writes them."""
    if name in ("L1", "L2"):
        return f"$L^{name[1]}$"
    if name.startswith(("N1_", "N2_")):
        return f"$N^{name[1]}$_{name[3:]}"
    return f"$S$_{name}"


def fig2e(d, out):
    sets, locs = d["sets"], d["locations"]
    m = np.array([[d["single_auc"][s][j] for j in range(len(locs))] for s in sets])
    row_order = hierarchy.leaves_list(hierarchy.linkage(m, "average"))
    col_order = hierarchy.leaves_list(hierarchy.linkage(m.T, "average"))
    kinds = {"S": [s for s in sets if "_" not in s[:3] and s not in ("L1", "L2")],
             "N": [s for s in sets if s.startswith("N")], "L": ["L1", "L2"]}
    avg_rows = [m[[sets.index(s) for s in kinds[k]]].mean(axis=0) for k in ("S", "N", "L")] + [m.mean(axis=0)]
    final = np.array([d["location_auc"][loc] for loc in locs])
    body = m[row_order][:, col_order]
    extra = np.array(avg_rows)[:, col_order]
    grid = np.vstack([body, extra, final[col_order]])
    grid = np.hstack([grid, np.r_[body.mean(axis=1), extra.mean(axis=1), final.mean()][:, None]])
    nr, nc = grid.shape
    fig = figure_for("fig2e")
    ax = fig.add_axes([0.03, 0.12, 0.6, 0.86])
    ax.imshow(grid, cmap=JET, vmin=0.5, vmax=1.0, aspect="auto", interpolation="nearest")
    rows = [sets[i] for i in row_order]
    cols = [locs[j] for j in col_order]
    for j, loc in enumerate(cols):
        for s in d["selected"][loc]:
            i = rows.index(s)
            best = s == d["first"][loc]
            ax.add_patch(plt.Rectangle((j - 0.42, i - 0.42), 0.84, 0.84, fill=False,
                                       ec="white" if best else "black", lw=0.9))
    ax.set_yticks(range(nr), [set_label(s) for s in rows] + ["Avg. of $S$s", "Avg. of $N$s", "Avg. of $L$s",
                                                               "Avg. of All", "Final Composite"], fontsize=4.6,
                  fontweight="normal")
    ax.yaxis.tick_right()
    ax.set_xticks(range(nc), [c if c != "VU" else "VO" for c in cols] + ["Avg."], rotation=90, fontsize=4.6)
    ax.tick_params(length=0)
    for sp in ax.spines.values():
        sp.set_visible(False)
    cax = fig.add_axes([0.87, 0.03, 0.08, 0.035])
    cax.imshow(np.linspace(0.5, 1, 64)[None, :], cmap=JET, aspect="auto")
    cax.set_xticks([])
    cax.set_yticks([])
    fig.text(0.96, 0.06, "1.0", fontsize=4.5)
    fig.text(0.96, 0.02, "0.5", fontsize=4.5)
    fig.text(0.0, 0.995, "E", fontsize=10, va="top")
    save(fig, "fig2e", out)


# ---------------------------------------------------------------- location maps
def clm(P, known, key, out):
    """Conditional location map: GO and the three conditions (columns) by 13 locations (rows), white grid,
    H on the location with the highest possibility of each condition, as in the paper."""
    m = np.column_stack([known.astype(float), P])  # 13 x 4
    fig = figure_for(key)
    title = CLM_TITLES.get(key)
    top = 0.9 if title else 0.97
    ax = fig.add_axes([0.38, 0.17, 0.58, top - 0.17])
    ax.imshow(m, cmap=JET, vmin=0, vmax=1, aspect="auto", interpolation="nearest")
    for x in np.arange(-0.5, 4, 1):
        ax.axvline(x, color="white", lw=0.5)
    for y in np.arange(-0.5, 13, 1):
        ax.axhline(y, color="white", lw=0.5)
    for c in range(1, 4):
        r = int(np.argmax(m[:, c]))
        ax.text(c - 0.42, r + 0.38, "H", fontsize=3.2, color="black", fontweight="bold",
                bbox={"boxstyle": "square,pad=0.08", "fc": "white", "ec": "none"})
    ax.set_yticks(range(13), LOC_LABELS, fontsize=6)
    ax.set_xticks(range(4), ["GO", "Normal", "Low", "High"], rotation=90, fontsize=5.5)
    ax.tick_params(length=2, color="black")
    if title:
        ax.set_title(title, fontsize=6, pad=2)
    save(fig, key, out)


def fig3i(cells, out):
    prots, conds = [], []
    for c in cells:
        if c["protein"] not in prots:
            prots.append(c["protein"])
            conds.append(c["condition"])
    locs = ["CY", "ER", "GL", "NU", "PM"]
    m = np.full((5, len(prots)), np.nan)
    for c in cells:
        if c["P"] is not None:
            m[locs.index(c["location"]), prots.index(c["protein"])] = c["P"]
    fig = figure_for("fig3i")
    ax = fig.add_axes([0.065, 0.22, 0.925, 0.48])
    ax.imshow(m, cmap=JET, vmin=0, vmax=1, aspect="auto", interpolation="nearest")
    for x in np.arange(-0.5, len(prots), 1):
        ax.axvline(x, color="black", lw=0.3)
    for y in np.arange(-0.5, 5, 1):
        ax.axhline(y, color="black", lw=0.3)
    for c in cells:
        i, j = locs.index(c["location"]), prots.index(c["protein"])
        if c["predicted"]:
            ax.add_patch(plt.Rectangle((j - 0.46, i - 0.46), 0.92, 0.92, fill=False, ec="black", lw=1.2))
        right = c["predicted"] == c["actual"]
        ax.text(j, i + 0.05, "+" if c["actual"] else "−", ha="center", va="center", fontsize=8,
                color="black" if right else "white", fontweight="bold")
    ax.set_yticks(range(5), locs, fontsize=7)
    ax.set_xticks(range(len(prots)), prots, rotation=90, fontsize=6)
    ax.xaxis.tick_top()
    ax.tick_params(length=0)
    for cond, label in (("normal", "Normal"), ("low", "Low"), ("high", "High")):
        idx = [j for j, c in enumerate(conds) if c == cond]
        x0, x1 = (min(idx) - 0.3) / len(prots), (max(idx) + 0.3) / len(prots)
        fig.add_artist(plt.Line2D([0.05 + 0.93 * x0, 0.05 + 0.93 * x1], [0.95, 0.95], color="black", lw=1.5))
        fig.text(0.05 + 0.93 * (x0 + x1) / 2, 0.965, label, ha="center", fontsize=7)
    cax = fig.add_axes([0.05, 0.065, 0.12, 0.04])
    cax.imshow(np.linspace(0, 1, 64)[None, :], cmap=JET, aspect="auto")
    cax.set_xticks([])
    cax.set_yticks([])
    fig.text(0.035, 0.07, "0", fontsize=6)
    fig.text(0.175, 0.07, "1", fontsize=6)
    fig.text(0.06, 0.0, "possibility degree", fontsize=5.5, style="italic")
    fig.text(0.26, 0.11, "Predicted", fontsize=6.5)
    fig.add_artist(plt.Rectangle((0.262, 0.055), 0.010, 0.035, fill=False, ec="black", lw=1.0,
                                 transform=fig.transFigure))
    fig.text(0.276, 0.06, ": present", fontsize=5.5, style="italic")
    fig.text(0.262, 0.01, "others : absent", fontsize=5.5, style="italic")
    fig.text(0.45, 0.11, "Actual", fontsize=6.5)
    fig.text(0.45, 0.06, "+ : present     \u2212 : absent", fontsize=5.5, style="italic")
    fig.text(0.45, 0.01, "white : wrong prediction", fontsize=5.5, style="italic")
    fig.text(0.0, 0.99, "I", fontsize=10, va="top")
    save(fig, "fig3i", out)


def fig5a(d, out):
    """The landscape of mislocations: share of each kind (normal-brain location to glioma location) as a surface,
    with strips for the total share leaving (normal brain) and entering (glioma) each location."""
    n = len(LOCATIONS)
    m = np.zeros((n, n))  # [from, to]
    tot = max(sum(d["by_kind"].values()), 1)
    for k, v in d["by_kind"].items():
        f, t = k.split(">")
        m[LOCATIONS.index(f), LOCATIONS.index(t)] = 100.0 * v / tot
    fig = figure_for("fig5a")
    ax = fig.add_axes([-0.02, -0.22, 0.9, 1.44], projection="3d")
    ax.set_box_aspect((1.6, 1.6, 0.5), zoom=1.0)
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.pane.set_facecolor((1, 1, 1, 0))
        axis._axinfo["grid"].update(color=(0.85, 0.85, 0.85, 1), linewidth=0.3)
    # x runs along glioma (to) and y along normal brain (from), so that, seen from the AT-AT corner, normal
    # brain is on the left and glioma on the right as in the paper
    m = m.T
    xx, yy = np.meshgrid(np.arange(n), np.arange(n), indexing="ij")
    ax.plot_surface(xx, yy, m, cmap=JET, vmin=0, vmax=40, rstride=1, cstride=1, linewidth=0.2,
                    edgecolor=(0.2, 0.2, 0.6, 0.4), antialiased=True)
    ax.view_init(elev=24, azim=-135)
    ax.set_zlim(0, 20)
    ax.set_zticks([0, 5, 10, 15, 20])
    ax.set_xticks(range(n), LOC_LABELS, fontsize=5)
    ax.set_yticks(range(n), LOC_LABELS, fontsize=5)
    ax.tick_params(axis="both", pad=0)
    ax.set_xlabel("Glioma", fontsize=7, labelpad=2)
    ax.set_ylabel("Normal Brain", fontsize=7, labelpad=2)
    for k, v in sorted(d["by_kind"].items(), key=lambda t: -t[1])[:7]:
        f, t = k.split(">")
        i, j = LOCATIONS.index(f), LOCATIONS.index(t)
        ax.text(j, i, m[j, i] + 1.0, f"{f} → {t} ({m[j, i]:.2f})", fontsize=5.5)
    cax = fig.add_axes([0.9, 0.45, 0.02, 0.2])
    cax.imshow(np.linspace(40, 0, 64)[:, None], cmap=JET, aspect="auto", vmin=0, vmax=40)
    cax.set_xticks([])
    cax.set_yticks([])
    fig.text(0.925, 0.64, "40%", fontsize=6)
    fig.text(0.925, 0.45, "0", fontsize=6)
    fig.text(0.0, 0.98, "A", fontsize=10, va="top")
    save(fig, "fig5a", out)


def main(paper: Path, outdir: Path, run: Path, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    pub_dir = dest / "published"
    pub_dir.mkdir(exist_ok=True)
    SIZES.update(published_panels(paper / "PMC3730102.1.pdf", pub_dir))
    f2 = json.load(open(outdir / "fig2.json"))
    cl = json.load(open(outdir / "clm.json"))
    z = np.load(run / "clm.npz")
    symbols, known = {}, {}
    for line in list(open(run / "proteins.tsv"))[1:]:
        a, s, locs = line.split("\t")[:3]
        symbols.setdefault(s.upper(), a)
        known[a] = {x for x in locs.split(",") if x}
    pos = {a: i for i, a in enumerate(z["accessions"])}
    fig2a(f2["fig2a"], dest)
    fig2b(f2["fig2b"], dest)
    fig2c(f2["fig2c"], dest)
    fig2d(f2["fig2d"], dest)
    fig2e(f2["fig2e"], dest)
    for key, sym in CLM_PANELS.items():
        acc = symbols[sym]
        k = np.array([loc in known[acc] for loc in LOCATIONS])
        clm(z["P"][pos[acc]], k, key, dest)
    fig3i(cl["fig3i"]["cells"], dest)
    fig5a(cl["mislocations"], dest)
    for key in sorted(PANELS):
        overlay(key, pub_dir, dest)
    json.dump({"panels": sorted(PANELS), "dpi": DPI, "font": FONT, "figures": FIGURES,
               "boxes": {k: v[1] for k, v in PANELS.items()}, "sizes": SIZES},
              open(dest / "figures.json", "w"), indent=1, sort_keys=True)


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4]))
