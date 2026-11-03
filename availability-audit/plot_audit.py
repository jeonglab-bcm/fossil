"""Plot the availability audit: links by publication year and host, and the other artifacts.

Reads url_audit.csv (from summarize.py), accession_status.csv, install_sample.csv and
inspect_results.csv; writes figures/availability_links.* and figures/availability_artifacts.*.
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
sys.path.insert(0, str(HERE))
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
        by_group[r["group"]][s] += 1
        if r["group"] != "Journal / publisher":  # article self-links (mostly BMC boilerplate) only in B
            by_year[int(r["year"]) if int(r["year"]) <= 2015 else 2015][s] += 1
    years = sorted(by_year)
    groups = sorted(by_group, key=lambda g: by_group[g]["Reachable"] / sum(by_group[g].values()))
    fig, (a, b) = plt.subplots(1, 2, figsize=(12.5, 4.8), facecolor=SURFACE,
                               gridspec_kw={"width_ratios": [1.05, 1], "wspace": 0.55})
    for ax in (a, b):
        style(ax)
    stacked(a, years, [by_year[y] for y in years], horizontal=False)
    a.tick_params(axis="x", labelsize=7.5)
    a.set_xticks(range(len(years)), [f"{y}\n{sum(by_year[y].values()):,}" for y in years], rotation=0)
    a.set_ylim(0, 1)
    a.set_yticks([0, 0.25, 0.5, 0.75, 1], ["0", "25", "50", "75", "100%"])
    a.yaxis.grid(True, color=GRID, lw=0.6)
    a.set_axisbelow(True)
    a.set_title("A  Software and data links, by publication year", loc="left", color=INK, fontsize=11,
                fontweight="bold", pad=10)
    stacked(b, groups, [by_group[g] for g in groups], horizontal=True)
    b.set_yticks(range(len(groups)), [f"{g}  ({sum(by_group[g].values()):,})" for g in groups])
    b.set_xlim(0, 1)
    b.set_xticks([0, 0.25, 0.5, 0.75, 1], ["0", "25", "50", "75", "100%"])
    b.xaxis.grid(True, color=GRID, lw=0.6)
    b.set_axisbelow(True)
    b.set_title("B  All links, by where they point", loc="left", color=INK, fontsize=11,
                fontweight="bold", pad=10)
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for _, c in STATUS]
    fig.legend(handles, [n for n, _ in STATUS], loc="lower center", ncol=4, frameon=False, fontsize=9,
               labelcolor=INK2, bbox_to_anchor=(0.5, -0.06))
    fig.text(0.01, -0.13, "Checked October 2026. Links in the abstract, body and back matter (reference lists "
             "excluded); each bar is 100% of paper x link pairs (count under the year in A, in parentheses in B); labels "
             "are percentages. A leaves out links to the journal itself (mostly BioMed Central boilerplate). Reachable "
             "includes 'moved' notices; Can't tell = refused this client, bot check, ftp://, non-standard port.",
             fontsize=7.5, color=MUTED, ha="left", va="top", wrap=True)
    save(fig, out)


def artifacts_figure(out=FIGURES / "availability_artifacts"):
    fig, (a, b) = plt.subplots(1, 2, figsize=(12.5, 4.2), facecolor=SURFACE,
                               gridspec_kw={"width_ratios": [1, 1], "wspace": 0.6})
    for ax in (a, b):
        style(ax)
    acc = Counter()
    by_type = defaultdict(Counter)
    for r in read("accession_status.csv"):
        if r["status"] == "invalid":
            continue
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
    # B: install-test sample, by publication-year band (static inspection; no downloaded code run)
    from summarize import sample_outcome
    fold = {"Obtained: static check passes": "Obtained", "Obtained: static check inconclusive": "Obtained",
            "Obtained: not checkable": "Obtained", "Obtained: static check fails": "Obtained, fails static check",
            "Cited location unreachable from here": "Unreachable or can't tell",
            "Cited location can't be told": "Unreachable or can't tell", "Cited location gone": "Cited location gone",
            "No software released": "No public code", "Only on request": "No public code",
            "Web service only": "No public code"}
    groups = [("Obtained", "#256abf", "#ffffff"), ("Obtained, fails static check", "#6da7ec", INK),
              ("Unreachable or can't tell", "#ef8a6a", INK), ("Cited location gone", "#9e1f18", "#ffffff"),
              ("No public code", "#a8a69d", INK)]
    insp = {r["pmcid"]: r for r in read("inspect_results.csv")} if (HERE / "inspect_results.csv").exists() else {}
    with open(HERE / "install_sample.csv") as f:
        smp = list(csv.DictReader(l for l in f if not l.startswith("#")))
    years = {}
    with open(HERE / "papers.csv") as f:
        for r in csv.DictReader(l for l in f if not l.startswith("#")):
            years["PMC" + r["pmcid"].removeprefix("PMC")] = int(r["year"])
    bands = defaultdict(Counter)
    for r in smp:
        y = years[r["pmcid"]]
        band = "2004-07" if y <= 2007 else "2008-11" if y <= 2011 else "2012-15"
        g = fold[sample_outcome(r, insp.get(r["pmcid"], {}))]
        bands[band][g] += 1
        bands["All 150"][g] += 1
    names = ["All 150", "2012-15", "2008-11", "2004-07"]
    left = [0] * len(names)
    for g, col, ink in groups:
        vals = [bands[n][g] for n in names]
        b.barh(range(len(names)), vals, left=left, height=0.68, color=col, edgecolor=SURFACE, linewidth=1.5,
               label=g)
        for i, (v, l) in enumerate(zip(vals, left)):
            if v / sum(bands[names[i]].values()) >= 0.06:
                b.annotate(str(v), (l + v / 2, i), ha="center", va="center", fontsize=7.5, color=ink)
        left = [l + v for l, v in zip(left, vals)]
    b.set_yticks(range(len(names)), names)
    b.xaxis.grid(True, color=GRID, lw=0.6)
    b.set_axisbelow(True)
    b.set_xlabel("Papers", color=INK2, fontsize=9)
    b.set_title("B  Software of a random sample of 150 papers", loc="left", color=INK, fontsize=11,
                fontweight="bold", pad=10)
    b.legend(frameon=False, fontsize=8, labelcolor=INK2, loc="lower center", ncol=3, bbox_to_anchor=(0.45, -0.42))
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for _, c in STATUS[:1] + STATUS[2:]]
    a.legend(handles, ["Resolves", "Obsolete or not found", "Can't tell"], frameon=False, fontsize=8.5,
             labelcolor=INK2, loc="lower center", ncol=3, bbox_to_anchor=(0.45, -0.28))
    fig.text(0.01, -0.3, "Checked October 2026. A: PDB 'not found' counts as Can't tell (IDs taken from text after "
             "'PDB' can be false positives). B: stratified random sample, 50 papers per band. Obtained = source or "
             "package retrieved today (including from a PMC supplement); static checks parse or syntax-check the code "
             "without running it. No public code = none released, only on request, or web service only.",
             fontsize=7.5, color=MUTED, ha="left", va="top", wrap=True)
    save(fig, out)


if __name__ == "__main__":
    links_figure()
    if (HERE / "accession_status.csv").exists():
        artifacts_figure()
