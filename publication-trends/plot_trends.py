"""Plot counts.csv as small multiples by theme.

Columns are themes. Row A is articles per year (log), row B the share of all PMC
articles that year. Every panel shows the other groups as gray context lines.
"""
import csv
import math
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

ENV = "Docker, Jupyter, Conda, Snakemake, Nextflow"
COLORS = {  # color follows the group in every figure; the first seven pass all-pairs CVD checks
    "GitHub + GitLab": "#2a78d6",
    "NCBI GEO": "#008300",
    "CRAN + Bioconductor": "#eda100",
    "Zenodo + figshare": "#1baf7a",
    "Python + PyPI": "#e87ba4",
    "SourceForge": "#2f2e2b",  # the palette has five hues that survive all pairs; the rest are grays
    ENV: "#6b6a65",
    "SRA / ENA": "#6250d6",
}
THEMES = {
    "Code hosting": ["GitHub + GitLab", "SourceForge"],
    "R and Python ecosystems": ["CRAN + Bioconductor", "Python + PyPI"],
    "Archives with DOIs": ["Zenodo + figshare"],
    "Data repositories": ["NCBI GEO", "SRA / ENA"],
    "Software environments": [ENV],
}
LABELS = {ENV: "Docker, Jupyter, Conda/\nBioconda, Snakemake,\nNextflow"}
INK, INK2, MUTED, GRID, AXIS, SURFACE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#fcfcfb"
CONTEXT = "#d3d2cb"
PARTIAL = 2026


def load(path):
    rows = [r for r in csv.DictReader(l for l in open(path) if not l.startswith("#"))]
    data = {g: {"year": [], "count": [], "share": []} for g in COLORS}
    for r in rows:
        d = data[r["group"]]
        d["year"].append(int(r["year"]))
        d["count"].append(int(r["count"]) if r["count"] else math.nan)  # blank = not counted
        d["share"].append(100 * float(r["share"]) if r["share"] else math.nan)
    return data


def style(ax):
    ax.set_facecolor(SURFACE)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(AXIS)
    ax.tick_params(colors=MUTED, labelcolor=INK2, labelsize=9)
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    ax.set_xlim(1999.5, PARTIAL + 0.5)
    ax.set_xticks([2000, 2010, 2020])


def panel(ax, data, key, groups, log):
    def ys(g):  # log axis: omit zeros
        return [v if v > 0 or not log else math.nan for v in data[g][key]]

    for g in COLORS:
        if g not in groups:
            ax.plot(data[g]["year"][:-1], ys(g)[:-1], color=CONTEXT, lw=1, zorder=1)
    for g in groups:
        c, y, x = COLORS[g], ys(g), data[g]["year"]
        ax.plot(x[:-1], y[:-1], color=c, lw=2, label=LABELS.get(g, g), zorder=3)
        ax.plot(x[-2:], y[-2:], color=c, lw=2, ls=(0, (2, 2)), zorder=2)
        ax.plot(x[-1], y[-1], marker="o", ms=5, mfc=SURFACE, mec=c, mew=1.4, zorder=3)


def main(src="counts.csv", out="publication_trends"):
    data = load(src)
    n = len(THEMES)
    fig, axes = plt.subplots(2, n, figsize=(3.3 * n, 7.4), facecolor=SURFACE,
                             sharex=True, sharey="row",
                             gridspec_kw={"wspace": 0.12, "hspace": 0.12})
    for col, (theme, groups) in enumerate(THEMES.items()):
        a, b = axes[0, col], axes[1, col]
        panel(a, data, "count", groups, log=True)
        panel(b, data, "share", groups, log=False)
        style(a)
        style(b)
        a.set_title(theme, loc="left", color=INK, fontsize=11, fontweight="bold", pad=8)
        a.legend(loc="upper left", frameon=False, fontsize=8.5, labelcolor=INK2,
                 handlelength=1.6, borderaxespad=0.2)

    a0, b0 = axes[0, 0], axes[1, 0]
    a0.set_yscale("log")
    a0.set_ylim(0.7, 3e5)
    a0.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
    a0.set_ylabel("A  Articles per year (log)", color=INK, fontsize=10, fontweight="bold")
    b0.set_ylim(0, 8)
    b0.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}%"))
    b0.set_ylabel("B  Share of all PMC articles", color=INK, fontsize=10, fontweight="bold")

    fig.text(0.07, 0.035,
             "Source: PubMed Central full-text search (NCBI E-utilities, db=pmc, publication year); "
             "full text includes reference lists. Gray lines are the other groups, for comparison.\n"
             "Hollow marker and dashed segment = 2026, partial year (indexed through late Oct). "
             "Zero counts are omitted on the log scale. Environment tools are counted from 2012. "
             "Queries are listed in fetch_counts.py.",
             fontsize=8, color=MUTED, ha="left", va="top")
    fig.subplots_adjust(left=0.07, right=0.99, top=0.93, bottom=0.1)
    for ext in ("png", "svg"):
        fig.savefig(f"{out}.{ext}", dpi=200, bbox_inches="tight", facecolor=SURFACE)


if __name__ == "__main__":
    main(*sys.argv[1:])
