"""Plot the three eras of code and data sharing on one log-scale panel of PMC share.

Highlights the period of interest, 2004-2015. Reads counts.csv; reuses the
colors and loader from plot_trends.py so each group keeps one color everywhere.
"""
import math
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import FixedLocator, FuncFormatter, NullLocator  # noqa: E402

from plot_trends import AXIS, COLORS, ENV, GRID, INK, INK2, MUTED, PARTIAL, SURFACE, load  # noqa: E402

SERIES = ["NCBI GEO", "CRAN + Bioconductor", "SourceForge", "GitHub + GitLab", "Python + PyPI",
          "Zenodo + figshare", ENV]
COLOR = COLORS
LABEL = {ENV: "Docker, Jupyter, Conda,\nSnakemake, Nextflow"}
FOCUS = (2004, 2015)
BAND = "#efede6"
ERAS = [  # (number, name, first year, last year, strip row)
    (1, "Data first", 2004, 2014, 1),
    (2, "Code moves to GitHub", 2015, 2017, 0),
    (3, "Archived copies, environments", 2016, PARTIAL, 1),
]
MILESTONES = [  # (series, year, text, text position)
    ("NCBI GEO", 2010, "GEO passes 1% (2010)", (2003.2, 3.2)),
    ("GitHub + GitLab", 2015, "GitHub passes SourceForge (2015)", (2016.0, 0.025)),
    ("GitHub + GitLab", 2017, "GitHub passes GEO and CRAN/Bioconductor (2017)", (2006.0, 6.0)),
    ("Zenodo + figshare", 2022, "Zenodo + figshare pass GEO (2022)", (2017.8, 9.0)),
]


def end_labels(ax, data):
    lo, hi = (math.log10(v) for v in ax.get_ylim())
    gap = 0.05 * (hi - lo)
    ys = {g: math.log10(data[g]["share"][-1]) for g in SERIES}
    order = sorted(ys, key=ys.get)
    pos = [ys[g] for g in order]
    for i in range(1, len(pos)):
        pos[i] = max(pos[i], pos[i - 1] + gap)
    shift = sum(p - ys[g] for g, p in zip(order, pos)) / len(pos)  # re-center the nudged stack
    pos = [p - shift for p in pos]
    for g, p in zip(order, pos):
        ax.annotate(LABEL.get(g, g), xy=(PARTIAL + 0.7, 10 ** p), va="center", ha="left",
                    fontsize=9, color=INK2, annotation_clip=False, linespacing=1.1)


def main(src="counts.csv", out="publication_eras"):
    data = load(src)
    fig, (top, ax) = plt.subplots(2, 1, figsize=(11, 6.8), sharex=True, facecolor=SURFACE,
                                  gridspec_kw={"height_ratios": [1, 5.2], "hspace": 0.04})

    for a in (top, ax):
        a.set_facecolor(SURFACE)
        a.axvspan(FOCUS[0] - 0.5, FOCUS[1] + 0.5, color=BAND, lw=0, zorder=0)

    # era strip
    top.set_ylim(-0.5, 1.6)
    top.axis("off")
    for n, name, y0, y1, row in ERAS:
        top.barh(row, y1 - y0 + 1, left=y0 - 0.5, height=0.62, color="#d9d8d1", lw=0, zorder=2)
        text = f"{n}  {name}  ({y0}–{'' if y1 == PARTIAL else y1})"
        if y1 - y0 >= 6:
            top.text(y0 - 0.2, row, text, va="center", ha="left", fontsize=9.5, color=INK, zorder=3)
        else:
            top.text(y1 + 0.8, row, text, va="center", ha="left", fontsize=9.5, color=INK, zorder=3)
    top.text(1999.5, 1.0, "Eras", va="center", ha="left", fontsize=9.5, color=MUTED, fontweight="bold")
    top.text(FOCUS[0] - 0.3, 0, f"Period of interest, {FOCUS[0]}–{FOCUS[1]}", va="center", ha="left",
             fontsize=10, fontweight="bold", color=INK)

    # lines
    for g in SERIES:
        d, c = data[g], COLOR[g]
        y = [v if v > 0 else math.nan for v in d["share"]]
        lw = 1.6 if g == ENV else 2.2
        ax.plot(d["year"][:-1], y[:-1], color=c, lw=lw, label=LABEL.get(g, g).replace("\n", " "),
                zorder=3, solid_capstyle="round")
        ax.plot(d["year"][-2:], y[-2:], color=c, lw=lw, ls=(0, (2, 2)), zorder=2)
        ax.plot(d["year"][-1], y[-1], marker="o", ms=5, mfc=SURFACE, mec=c, mew=1.4, zorder=3)

    for g, year, text, (tx, ty) in MILESTONES:
        y = data[g]["share"][data[g]["year"].index(year)]
        ax.plot(year, y, marker="o", ms=7, mfc=SURFACE, mec=INK, mew=1.2, zorder=4)
        ax.annotate(text, xy=(year, y), xytext=(tx, ty), fontsize=8.5, color=INK, va="center",
                    arrowprops={"arrowstyle": "-", "color": MUTED, "lw": 0.8,
                                "shrinkA": 2, "shrinkB": 4}, zorder=4)

    ax.set_yscale("log")
    ax.set_ylim(8e-4, 12)
    ax.yaxis.set_major_locator(FixedLocator([0.001, 0.01, 0.1, 1, 10]))
    ax.yaxis.set_minor_locator(NullLocator())
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}%"))
    ax.set_xlim(1999.5, PARTIAL + 0.5)
    ax.set_xticks(range(2000, PARTIAL + 1, 2))
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(AXIS)
    ax.tick_params(colors=MUTED, labelcolor=INK2, labelsize=9)
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    ax.set_ylabel("Share of all PMC articles mentioning it (log)", color=INK2, fontsize=10)
    end_labels(ax, data)

    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, -0.07), ncol=4,
              frameon=False, fontsize=8.5, labelcolor=INK2, handlelength=1.6, columnspacing=1.2)
    fig.suptitle("Data sharing became routine years before code sharing", x=0.065, y=0.985,
                 ha="left", fontsize=13, fontweight="bold", color=INK)
    fig.text(0.065, -0.025,
             "Source: PubMed Central full-text search (NCBI E-utilities, db=pmc, publication year); full "
             "text includes reference lists. Zero counts are omitted on the log scale.\nHollow marker and "
             "dashed segment = 2026, partial year (indexed through late Oct). Environment tools are counted from 2012; "
             "earlier \"docker\" and \"conda\" hits are other things.\nSRA / ENA is shown "
             "in publication_trends.png. Python + PyPI excludes articles that mention snakes.",
             fontsize=7.8, color=MUTED, ha="left", va="top")
    fig.subplots_adjust(left=0.065, right=0.84, top=0.93, bottom=0.12)
    for ext in ("png", "svg"):
        fig.savefig(f"{out}.{ext}", dpi=200, bbox_inches="tight", facecolor=SURFACE)


if __name__ == "__main__":
    main(*sys.argv[1:])
