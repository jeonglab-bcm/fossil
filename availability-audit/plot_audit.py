"""Plot the availability audit: links by publication year and host, and the other artifacts.

Reads url_audit.csv (from summarize.py), accession_status.csv, accessions.csv, and
install_results.csv; writes figures/availability_links.* and figures/availability_artifacts.*.
Reuses the colors, ink and save() from publication-trends/plot_trends.py.
"""
import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "publication-trends"))
from plot_trends import AXIS, FIGURES, GRID, INK, INK2, MUTED, SURFACE, save  # noqa: E402

# Ordered: reachable, then broken (unreachable, gone), then unknown. Validated with the dataviz
# validator: adjacent pairs pass CVD and normal-vision separation; the gray is the neutral
# "can't tell" slot, and every segment carries a direct label or sits in a table in README.md.
STATUS = [("Reachable", "#256abf"), ("Unreachable", "#ef8a6a"), ("Gone", "#9e1f18"), ("Can't tell", "#a8a69d")]
FOLD = {"alive": "Reachable", "moved": "Reachable", "unreachable": "Unreachable", "gone": "Gone",
        "indeterminate": "Can't tell", "untestable": "Can't tell"}
LABEL_INK = {"Reachable": "#ffffff", "Unreachable": INK, "Gone": "#ffffff", "Can't tell": INK}


def read(name):
    with open(HERE / name) as f:
        return list(csv.DictReader(f))


def style(ax):
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(AXIS)
    ax.tick_params(colors=INK2, labelsize=8.5, length=0)


def stacked(ax, labels, counts, horizontal, min_label=0.06):
    """100% stacked bars; counts is a list of Counter keyed by STATUS names."""
    pos = range(len(labels))
    left = [0.0] * len(labels)
    for name, color in STATUS:
        share = [c[name] / max(1, sum(c.values())) for c in counts]
        kw = dict(color=color, edgecolor=SURFACE, linewidth=1.5, label=name)
        if horizontal:
            ax.barh(pos, share, left=left, height=0.72, **kw)
        else:
            ax.bar(pos, share, bottom=left, width=0.72, **kw)
        for i, (s, l) in enumerate(zip(share, left)):
            if s >= min_label:
                xy = (l + s / 2, i) if horizontal else (i, l + s / 2)
                ax.annotate(f"{100 * s:.0f}", xy, ha="center", va="center", fontsize=7.5,
                            color=LABEL_INK[name])
        left = [l + s for l, s in zip(left, share)]


def links_figure(out=FIGURES / "availability_links"):
    rows = read("url_audit.csv")
    by_year, by_group = defaultdict(Counter), defaultdict(Counter)
    for r in rows:
        if r["category"] == "unchecked":
            continue
        s = FOLD[r["category"]]
        by_year[int(r["year"]) if int(r["year"]) <= 2015 else 2015][s] += 1
        by_group[r["group"]][s] += 1
    years = sorted(by_year)
    groups = sorted(by_group, key=lambda g: by_group[g]["Reachable"] / sum(by_group[g].values()))
    fig, (a, b) = plt.subplots(1, 2, figsize=(12.5, 4.8), facecolor=SURFACE,
                               gridspec_kw={"width_ratios": [1.05, 1], "wspace": 0.55})
    for ax in (a, b):
        style(ax)
    stacked(a, years, [by_year[y] for y in years], horizontal=False)
    a.set_xticks(range(len(years)), [str(y) for y in years], rotation=0)
    a.set_ylim(0, 1)
    a.set_yticks([0, 0.25, 0.5, 0.75, 1], ["0", "25", "50", "75", "100%"])
    a.yaxis.grid(True, color=GRID, lw=0.6)
    a.set_axisbelow(True)
    a.set_title("A  Links in the paper text, by publication year", loc="left", color=INK, fontsize=11,
                fontweight="bold", pad=10)
    for i, y in enumerate(years):
        a.annotate(f"{sum(by_year[y].values()):,}", (i, 1.01), ha="center", va="bottom", fontsize=7, color=MUTED)
    stacked(b, groups, [by_group[g] for g in groups], horizontal=True)
    b.set_yticks(range(len(groups)), [f"{g}  ({sum(by_group[g].values()):,})" for g in groups])
    b.set_xlim(0, 1)
    b.set_xticks([0, 0.25, 0.5, 0.75, 1], ["0", "25", "50", "75", "100%"])
    b.xaxis.grid(True, color=GRID, lw=0.6)
    b.set_axisbelow(True)
    b.set_title("B  By where the link points (links)", loc="left", color=INK, fontsize=11,
                fontweight="bold", pad=10)
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for _, c in STATUS]
    fig.legend(handles, [n for n, _ in STATUS], loc="lower center", ncol=4, frameon=False, fontsize=9,
               labelcolor=INK2, bbox_to_anchor=(0.5, -0.06))
    fig.text(0.01, -0.12, "Checked October 2026. Each bar is 100% of paper x link pairs (count above A, in "
             "parentheses in B). Labels are percentages. Reachable includes 'moved' notices; Can't tell = refused "
             "this client, bot check, ftp://, non-standard port.", fontsize=7.5, color=MUTED, ha="left", va="top")
    save(fig, out)


def artifacts_figure(out=FIGURES / "availability_artifacts"):
    fig, (a, b) = plt.subplots(1, 2, figsize=(12.5, 4.2), facecolor=SURFACE,
                               gridspec_kw={"width_ratios": [1, 1], "wspace": 0.6})
    for ax in (a, b):
        style(ax)
    acc = Counter()
    by_type = defaultdict(Counter)
    for r in read("accession_status.csv"):
        name = {"live": "Reachable", "obsolete": "Gone", "not_found": "Gone", "error": "Can't tell"}[r["status"]]
        if r["type"] == "PDB" and r["status"] == "not_found":
            name = "Can't tell"  # often a four-character false positive, not a lost entry
        by_type[r["type"]][name] += 1
        acc[name] += 1
    types = sorted(by_type, key=lambda t: sum(by_type[t].values()))
    stacked(a, types, [by_type[t] for t in types], horizontal=True)
    a.set_yticks(range(len(types)), [f"{t}  ({sum(by_type[t].values()):,})" for t in types])
    a.set_xlim(0, 1)
    a.set_xticks([0, 0.25, 0.5, 0.75, 1], ["0", "25", "50", "75", "100%"])
    a.xaxis.grid(True, color=GRID, lw=0.6)
    a.set_axisbelow(True)
    a.set_title("A  Repository accessions cited (distinct)", loc="left", color=INK, fontsize=11,
                fontweight="bold", pad=10)
    inst = read("install_results.csv") if (HERE / "install_results.csv").exists() else []
    bands = defaultdict(Counter)
    years = {}
    with open(HERE / "papers.csv") as f:
        for r in csv.DictReader(l for l in f if not l.startswith("#")):
            years["PMC" + r["pmcid"].removeprefix("PMC")] = int(r["year"])
    for r in inst:
        y = years[r["pmcid"]]
        band = "2004-07" if y <= 2007 else "2008-11" if y <= 2011 else "2012-15"
        bands[band]["Papers"] += 1
        bands[band]["Released software"] += r["kind"] not in ("none", "request", "webserver") or r["via"] == "alternate"
        bands[band]["Source obtained"] += r["obtained"] == "yes"
        bands[band]["Installs today"] += r["installed"] == "yes"
    steps = ["Released software", "Source obtained", "Installs today"]
    shades = ["#86b6ef", "#3987e5", "#184f95"]
    names = sorted(bands)
    w = 0.26
    for k, (step, col) in enumerate(zip(steps, shades)):
        vals = [bands[n][step] for n in names]
        xs = [i + (k - 1) * w for i in range(len(names))]
        b.bar(xs, vals, width=w - 0.03, color=col, label=step)
        for x, v in zip(xs, vals):
            b.annotate(str(v), (x, v), ha="center", va="bottom", fontsize=7.5, color=INK2, xytext=(0, 2),
                       textcoords="offset points")
    b.set_xticks(range(len(names)), [f"{n}\n(n={bands[n]['Papers']})" for n in names])
    b.yaxis.grid(True, color=GRID, lw=0.6)
    b.set_axisbelow(True)
    b.set_ylabel("Papers", color=INK2, fontsize=9)
    b.set_title("B  Install test, random sample by publication years", loc="left", color=INK, fontsize=11,
                fontweight="bold", pad=10)
    b.legend(frameon=False, fontsize=8.5, labelcolor=INK2, loc="upper left")
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for _, c in STATUS[:1] + STATUS[2:]]
    a.legend(handles, ["Resolves", "Obsolete or not found", "Can't tell"], frameon=False, fontsize=8.5,
             labelcolor=INK2, loc="lower center", ncol=3, bbox_to_anchor=(0.45, -0.28))
    fig.text(0.01, -0.16, "Checked October 2026. A: PDB 'not found' counts as Can't tell (IDs taken from text "
             "after 'PDB' can be false positives). B: 'Installs today' = the build/install step exits 0 on "
             "Ubuntu 24.04, R 4.6, Bioconductor 3.23, Python 3.13.", fontsize=7.5, color=MUTED, ha="left", va="top")
    save(fig, out)


if __name__ == "__main__":
    links_figure()
    if (HERE / "accession_status.csv").exists():
        artifacts_figure()
