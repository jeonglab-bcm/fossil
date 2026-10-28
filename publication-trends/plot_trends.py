"""Plot counts.csv as two panels: article counts (log) and share of all PMC articles."""
import csv
import math
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

COLORS = {  # categorical slots 1-5, fixed order
    "GitHub + GitLab": "#2a78d6",
    "SourceForge": "#eb6834",
    "NCBI GEO": "#1baf7a",
    "PyPI": "#eda100",
    "CRAN + Bioconductor": "#e87ba4",
}
MARKERS = dict(zip(COLORS, "osD^v"))
INK, INK2, MUTED, GRID, AXIS, SURFACE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#fcfcfb"
PARTIAL = 2026


def load(path):
    rows = [r for r in csv.DictReader(l for l in open(path) if not l.startswith("#"))]
    data = {g: {"year": [], "count": [], "share": []} for g in COLORS}
    for r in rows:
        d = data[r["group"]]
        d["year"].append(int(r["year"]))
        d["count"].append(int(r["count"]))
        d["share"].append(100 * float(r["share"]))
    return data


def end_labels(ax, data, key):
    """Direct-label each line at its last point, nudged apart to avoid collisions."""
    ys = {g: d[key][-1] for g, d in data.items()}
    log = ax.get_yscale() == "log"
    tr = (lambda v: math.log10(v)) if log else (lambda v: v)
    inv = (lambda v: 10 ** v) if log else (lambda v: v)
    lo, hi = (tr(v) for v in ax.get_ylim())
    gap = 0.055 * (hi - lo)
    order = sorted(ys, key=lambda g: tr(ys[g]))
    pos = [tr(ys[g]) for g in order]
    for i in range(1, len(pos)):
        pos[i] = max(pos[i], pos[i - 1] + gap)
    for g, p in zip(order, pos):
        ax.annotate(g, xy=(PARTIAL + 0.55, inv(p)), xycoords="data",
                    va="center", ha="left", fontsize=8.5, color=INK2, annotation_clip=False)
        ax.plot([PARTIAL + 0.25, PARTIAL + 0.5], [inv(p)] * 2, color=COLORS[g], lw=2,
                clip_on=False, solid_capstyle="round")


def style(ax):
    ax.set_facecolor(SURFACE)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(AXIS)
    ax.tick_params(colors=MUTED, labelcolor=INK2, labelsize=9)
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    ax.set_xlim(1999.5, PARTIAL + 0.3)
    ax.set_xticks(range(2000, PARTIAL + 1, 4))


def panel(ax, data, key, log=False):
    for g, d in data.items():
        c, m = COLORS[g], MARKERS[g]
        ys = [v if v > 0 or not log else math.nan for v in d[key]]  # log axis: omit zeros
        ax.plot(d["year"][:-1], ys[:-1], color=c, lw=2, marker=m, ms=5,
                mec=SURFACE, mew=1, label=g, zorder=3)
        ax.plot(d["year"][-2:], ys[-2:], color=c, lw=2, ls=(0, (2, 2)), zorder=2)
        ax.plot(d["year"][-1], ys[-1], marker=m, ms=6, mfc=SURFACE, mec=c, mew=1.6, zorder=3)


def main(src="counts.csv", out="publication_trends"):
    data = load(src)
    fig, (a, b) = plt.subplots(1, 2, figsize=(13, 5.2), facecolor=SURFACE,
                               gridspec_kw={"wspace": 0.62})

    panel(a, data, "count", log=True)
    style(a)
    a.set_yscale("log")
    a.set_ylim(0.7, 1.5e5)
    a.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
    a.set_ylabel("PMC articles mentioning term (log scale)", color=INK2, fontsize=10)
    a.set_title("A  Articles per year", loc="left", color=INK, fontsize=12, fontweight="bold")
    end_labels(a, data, "count")

    panel(b, data, "share")
    style(b)
    b.set_ylim(0, 7)
    b.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}%"))
    b.set_ylabel("Share of all PMC articles that year", color=INK2, fontsize=10)
    b.set_title("B  Share of all articles", loc="left", color=INK, fontsize=12, fontweight="bold")
    end_labels(b, data, "share")

    handles, labels = a.get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=5, frameon=False, fontsize=9.5,
               bbox_to_anchor=(0.5, 1.0), labelcolor=INK2)
    fig.text(0.01, -0.02,
             "Source: PubMed Central full-text search (NCBI E-utilities, db=pmc, publication year). "
             "Hollow marker and dashed segment = 2026, partial year (indexed through late Oct).\n"
             "NCBI GEO = \"Gene Expression Omnibus\" or \"NCBI GEO\"; PyPI = \"PyPI\" or \"Python Package Index\". "
             "Zero counts are omitted on the log scale. Full text includes reference lists.",
             fontsize=8, color=MUTED, ha="left", va="top")
    fig.subplots_adjust(left=0.07, right=0.86, top=0.84, bottom=0.1)
    for ext in ("png", "svg"):
        fig.savefig(f"{out}.{ext}", dpi=200, bbox_inches="tight", facecolor=SURFACE)


if __name__ == "__main__":
    main(*sys.argv[1:])
