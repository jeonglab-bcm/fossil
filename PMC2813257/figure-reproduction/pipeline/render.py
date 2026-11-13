"""Draw Figures 2A, 2B, 3 and 4 from analysis.json, plus the negative controls.

Usage: render.py ANALYSIS.json PUBLISHED_DIR OUTDIR

Each panel is drawn at the published panel's pixel size, in the published colours, so the two
images overlay directly. Controls (`*_wrong_*`, `*_near_*`) are the same drawing code with a known
wrong input or a small plausible error.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib
import matplotlib.patches

matplotlib.use("Agg")
from PIL import Image  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

RED, GREEN, BLACK, BLUE = "#ff0000", "#008000", "#000000", "#0000bf"
# Stroke widths measured on the published panels: data lines 5 px, the weighted-mean and fit
# lines 3 px, the axes frame 2 px, ticks 11 px long.
LW = 3.6
THIN = 2.2
DPI = 100


def save(fig, path, size_px):
    """Save and force the exact published panel size (matplotlib rounds figsize x dpi)."""
    fig.savefig(path, dpi=DPI)
    plt.close(fig)
    im = Image.open(path).convert("RGB")
    if im.size != tuple(size_px):
        canvas = Image.new("RGB", tuple(size_px), "white")
        canvas.paste(im, (0, 0))
        canvas.save(path)


def panel(size_px):
    """Figure whose whole area is the axes box, at the published panel's pixel size."""
    w, h = size_px[0] / DPI, size_px[1] / DPI
    fig = plt.figure(figsize=(w, h), dpi=DPI)
    ax = fig.add_axes([0.0, 0.0, 1.0, 1.0])
    for s in ax.spines.values():
        s.set_linewidth(1.45)
    ax.tick_params(direction="in", length=7.9, width=1.6, labelbottom=False, labelleft=False,
                   top=True, right=True)
    return fig, ax


def errbars(ax, x, y, e, color, label=None):
    y = np.array([np.nan if v is None else v for v in y], float)
    e = np.array([np.nan if v is None else v for v in e], float)
    ok = np.isfinite(y)
    ax.errorbar(np.asarray(x)[ok], y[ok], yerr=e[ok], color=color, lw=LW, elinewidth=LW,
                capsize=10, capthick=2.0, label=label)


def fig2a(an, out, name="fig2a", scale_rec=1.0, other_as_rec=False):
    r = an["recombination"]
    size = (1146, 887)
    fig, ax = panel(size)
    rec = r["fig2a_other" if other_as_rec else "fig2a_recombinant"]
    y = [None if v is None else v * scale_rec for v in rec["p"]]
    errbars(ax, rec["centers"], y, rec["err"], RED)
    oth = r["fig2a_other"]
    errbars(ax, oth["centers"], oth["p"], oth["err"], GREEN)
    ax.axhline(r["fig2a_other_weighted_mean"], color=BLACK, lw=THIN)
    ax.set_xlim(0, 500)
    ax.set_ylim(0, 0.5)
    ax.set_xticks(range(0, 501, 100))
    ax.set_yticks(np.arange(0, 0.51, 0.1))
    save(fig, Path(out) / f"{name}.png", size)


def fig2b(an, out, name="fig2b", shift=0.0, no_fit=False):
    r = an["recombination"]
    size = (1146, 887)
    fig, ax = panel(size)
    b = r["fig2b"]
    y = [None if v is None else v + shift for v in b["p"]]
    errbars(ax, b["centers"], y, b["err"], RED)
    if not no_fit:
        ax.plot(r["fit_curve"]["x"], r["fit_curve"]["y"], color=BLACK, lw=THIN)
    ax.axhline(r["fit"]["c0"], color=BLACK, lw=THIN)
    ax.set_xlim(0, 65000)
    ax.set_ylim(0, 0.5)
    ax.set_xticks(range(0, 65001, 10000))
    ax.set_yticks(np.arange(0, 0.51, 0.1))
    save(fig, Path(out) / f"{name}.png", size)


def fig3(an, boot, out, name="fig3", bins=30, values=None):
    """The bootstrap histogram, on the published axes: 0 to 30 x 10^-6 and 0 to 160 counts."""
    size = (1086, 842)
    fig, ax = panel(size)
    v = (boot if values is None else values) * 1e6
    ax.hist(v, bins=np.linspace(0, 30, bins + 1), color=BLUE, edgecolor=BLACK, linewidth=1.5)
    ax.set_xlim(0, 30)
    ax.set_ylim(0, 160)
    ax.set_xticks(range(0, 31, 5))
    ax.set_yticks(range(0, 161, 20))
    save(fig, Path(out) / f"{name}.png", size)


#: Figure 4's inset, in the published panel's own fractions: its box, its 21 bins to 0.011 per
#: generation and the log range of its y axis, all read from the published panel.
INSET_BOX = (332 / 1146, 1 - 808 / 887, (1145 - 332) / 1146, (808 - 200) / 887)
INSET_X = (0.0, 0.011)
INSET_BINS = 21
INSET_Y = (3.0, 1380.0)
LEGEND_LABELS = ("Nonsynonymous", "Synonymous", "Synonymous w/o hitchhiking")


def fig4(an, rates, out, name="fig4", swap=False, shift=0.0):
    """The cumulative distributions, with the legend, the inset histograms and the bracket.

    The published panel carries all three, and they cover a third of it; drawing them here is what
    lets the two images be laid over each other.
    """
    size = (1146, 887)
    c = an["selection"]["cumulative"]
    fig, ax = panel(size)
    x = np.asarray(c["x"]) + shift
    ns, sy = ("synonymous", "nonsynonymous") if swap else ("nonsynonymous", "synonymous")
    order = [(ns, RED), (sy, GREEN), ("synonymous_no_hitchhiking", BLUE)]
    for key, colour in order:
        ax.plot(x, c[key], color=colour, lw=LW)
    ax.set_xlim(0, 0.01)
    ax.set_ylim(0, 1.0)
    ax.set_xticks(np.arange(0, 0.0101, 0.002))
    ax.set_yticks(np.arange(0, 1.01, 0.2))

    # the bracket at 0.002 per generation, from our own non-synonymous curve up to 1
    top = float(np.interp(0.002, np.asarray(c["x"]), c[ns]))
    share = 1.0 - top
    ax.annotate("", xy=(0.002, 1.0), xytext=(0.002, top),
                arrowprops=dict(arrowstyle="-", color=BLACK, lw=1.6))
    for y in (top, 1.0):
        ax.plot([0.00178, 0.00222], [y, y], color=BLACK, lw=1.6)
    ax.text(0.00218, 0.93, f"$\\approx${round(100 * share):.0f}%", fontsize=23, color=BLACK,
            va="center")

    # the inset: the three histograms over each other, on a log scale
    ins = fig.add_axes([INSET_BOX[0], INSET_BOX[1], INSET_BOX[2], INSET_BOX[3]])
    edges = np.linspace(INSET_X[0], INSET_X[1], INSET_BINS + 1)
    for key, colour in order:
        ins.hist(rates[key], bins=edges, color=colour, edgecolor=BLACK, linewidth=1.4, log=True)
    ins.set_xlim(*INSET_X)
    ins.set_ylim(*INSET_Y)
    ins.set_xticks([0.0, 0.003, 0.006, 0.009])
    ins.set_xticklabels(["0.000", "0.003", "0.006", "0.009"], fontsize=23)
    ins.set_ylabel("# of observations", fontsize=25)
    ins.tick_params(axis="y", labelsize=23)
    ins.tick_params(axis="x", direction="out", length=0, pad=8)
    for sp in ins.spines.values():
        sp.set_linewidth(1.45)

    # the legend box, at the published position
    handles = [matplotlib.patches.Patch(facecolor=col, edgecolor=col)
               for col in (RED, GREEN, BLUE)]
    ax.legend(handles, LEGEND_LABELS, loc="upper left",
              bbox_to_anchor=(437 / 1146, 1 - 82 / 887), fontsize=25.5, frameon=True,
              borderpad=0.45, labelspacing=0.42, handlelength=1.45, handleheight=0.95,
              handletextpad=0.55, borderaxespad=0.0, edgecolor=BLACK, facecolor="white")

    # the published figure draws the legend over the inset
    ax.set_zorder(ins.get_zorder() + 1)
    ax.patch.set_visible(False)
    save(fig, Path(out) / f"{name}.png", size)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("analysis")
    ap.add_argument("published")
    ap.add_argument("outdir")
    a = ap.parse_args(argv)
    an = json.load(open(a.analysis))
    boot = np.load(Path(a.analysis).parent / "bootstrap.npy")
    out = Path(a.outdir)
    out.mkdir(parents=True, exist_ok=True)

    fig2a(an, out)
    # wrong input: the "other haplotypes" series drawn as the recombinant curve
    fig2a(an, out, name="fig2a_wrong_other", other_as_rec=True)
    # near miss: the recombinant curve 10% low
    fig2a(an, out, name="fig2a_near_scale090", scale_rec=0.90)

    fig2b(an, out)
    fig2b(an, out, name="fig2b_wrong_flat", no_fit=True, shift=0.0)
    fig2b(an, out, name="fig2b_near_shift005", shift=0.05)

    fig3(an, boot, out)
    rng = np.random.default_rng(12345)
    fig3(an, boot, out, name="fig3_wrong_uniform", values=rng.uniform(0, 3e-5, len(boot)))
    fig3(an, boot, out, name="fig3_near_bins20", bins=20)

    rates = {k: np.load(Path(a.analysis).parent / f"rates_{k}.npy")
             for k in ("nonsynonymous", "synonymous", "synonymous_no_hitchhiking")}
    fig4(an, rates, out)
    fig4(an, rates, out, name="fig4_wrong_swapped", swap=True)
    fig4(an, rates, out, name="fig4_near_shift0005", shift=0.0005)
    print("rendered", len(list(out.glob("*.png"))), "panels", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
