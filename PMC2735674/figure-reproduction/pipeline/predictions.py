#!/usr/bin/env python3
"""Table 5 and Figure 2: the top predicted nuclear-receptor pairs, and the drawn sub-network.

Table 5 lists the ten highest scoring nuclear-receptor drug-target pairs that were not known
interactions, ranked by the aggregated BLM score of the paper's third experimental condition
(Section 4.5). This step ranks every non-edge by m(BLMd,BLMt), writes the top 20, and compares the
top 10 with the paper's printed list, pair by pair and rank by rank.

Figure 2 draws part of the predicted network: its nodes and its solid (known) edges come from the
benchmark network, and its dashed edges are "some of the 20 highest scoring predicted
interactions". The nodes and the dashed edges were read off the published figure and are listed in
params/published_figure2.json, so the comparison asks two questions that our run can answer: are
the solid edges of those nodes the known interactions, and is every dashed edge in our top 20?

The drug and gene names of Table 5 are the paper's own (KEGG, 2009). They are annotation, not a
result of the method, so they are printed from the published file and not fetched again.

    predictions.py --scores scores --published params --out-dir output
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

import blmdti as B  # noqa: E402

TOP = 20


def ranked_non_edges(scores_dir: Path, dataset: str = "nr") -> list[dict]:
    """Every pair that is not a known interaction, ranked by the aggregated BLM score."""
    with np.load(scores_dir / f"{dataset}_blmd.npz", allow_pickle=False) as f:
        adjacency, blmd = f["adjacency"], f["scores"]
        drugs = [str(x) for x in f["drugs"]]
        targets = [str(x) for x in f["targets"]]
    with np.load(scores_dir / f"{dataset}_blmt.npz", allow_pickle=False) as f:
        blmt = f["scores"]
    combined = B.aggregate(blmd, blmt)
    rows = []
    for i, drug in enumerate(drugs):
        for j, target in enumerate(targets):
            if adjacency[i, j] > 0:
                continue
            rows.append(
                {
                    "drug": drug,
                    "target": target.replace("hsa", "hsa:") if not target.startswith("hsa:") else target,
                    "score": float(combined[i, j]),
                    "blmd": float(blmd[i, j]),
                    "blmt": float(blmt[i, j]),
                }
            )
    rows.sort(key=lambda r: -r["score"])
    for rank, row in enumerate(rows, start=1):
        row["rank"] = rank
    return rows


def compare_table5(ours: list[dict], published: list[dict]) -> dict:
    """Our top 10 against the paper's Table 5, as pairs and as ranks."""
    our_top = ours[:10]
    our_pairs = [(r["drug"], r["target"]) for r in our_top]
    their_pairs = [(r["drug"], r["target"]) for r in published]
    in_top_10 = [p for p in their_pairs if p in our_pairs]
    in_top_20 = [p for p in their_pairs if p in [(r["drug"], r["target"]) for r in ours[:TOP]]]
    same_rank = [p for i, p in enumerate(their_pairs) if i < len(our_pairs) and our_pairs[i] == p]
    return {
        "published": [
            {"rank": i + 1, "drug": d, "target": t} for i, (d, t) in enumerate(their_pairs)
        ],
        "ours": [
            {"rank": r["rank"], "drug": r["drug"], "target": r["target"], "score": round(r["score"], 6)}
            for r in our_top
        ],
        "published_pairs_in_our_top_10": len(in_top_10),
        "published_pairs_in_our_top_20": len(in_top_20),
        "pairs_at_the_same_rank": len(same_rank),
        "our_rank_of_each_published_pair": [
            next((r["rank"] for r in ours if (r["drug"], r["target"]) == p), None)
            for p in their_pairs
        ],
    }


def compare_figure2(ours: list[dict], scores_dir: Path, published: dict) -> dict:
    """The published sub-network's edges against our network and our top 20."""
    with np.load(scores_dir / "nr_blmd.npz", allow_pickle=False) as f:
        adjacency = f["adjacency"]
        drugs = [str(x) for x in f["drugs"]]
        targets = [str(x).replace("hsa", "hsa:") for x in f["targets"]]
    known = {
        (drugs[i], targets[j])
        for i in range(adjacency.shape[0])
        for j in range(adjacency.shape[1])
        if adjacency[i, j] > 0
    }
    nodes_drugs = published["drugs"]
    nodes_targets = published["targets"]
    our_solid = sorted((d, t) for d, t in known if d in nodes_drugs and t in nodes_targets)
    top = [(r["drug"], r["target"]) for r in ours[:TOP]]
    dashed = [tuple(e) for e in published["predicted_edges"]]
    return {
        "nodes": {"drugs": nodes_drugs, "targets": nodes_targets},
        "known_edges_rule": published["known_edges_rule"],
        "known_edges_ours": [list(e) for e in our_solid],
        "known_edges_ours_count": len(our_solid),
        "predicted_edges_published": [list(e) for e in dashed],
        "predicted_edges_in_our_top_20": [list(e) for e in dashed if e in top],
        "predicted_edges_in_our_top_20_count": sum(1 for e in dashed if e in top),
        "predicted_edges_count": len(dashed),
        "our_rank_of_each_predicted_edge": [
            next((r["rank"] for r in ours if (r["drug"], r["target"]) == e), None) for e in dashed
        ],
    }


def draw_figure2(comparison: dict, ours: list[dict], path: Path) -> None:
    """Our version of Figure 2: the same nodes, known edges solid, our top-20 edges dashed.

    The published figure's layout is manual, so ours is drawn with a fixed circular layout: the
    drugs on the left half, the targets on the right half, in the published order.
    """
    drugs = comparison["nodes"]["drugs"]
    targets = comparison["nodes"]["targets"]
    positions = {}
    for i, drug in enumerate(drugs):
        angle = np.pi / 2 + np.pi * (i + 0.5) / len(drugs)
        positions[drug] = (np.cos(angle), np.sin(angle))
    for j, target in enumerate(targets):
        angle = -np.pi / 2 + np.pi * (j + 0.5) / len(targets)
        positions[target] = (np.cos(angle), np.sin(angle))

    top = [(r["drug"], r["target"]) for r in ours[:TOP]]
    fig, ax = plt.subplots(figsize=(5.4, 4.4))
    for drug, target in comparison["known_edges_ours"]:
        x0, y0 = positions[drug]
        x1, y1 = positions[target]
        ax.plot([x0, x1], [y0, y1], "-", color="0.45", linewidth=0.7, zorder=1)
    for drug, target in top:
        if drug in positions and target in positions:
            x0, y0 = positions[drug]
            x1, y1 = positions[target]
            ax.plot([x0, x1], [y0, y1], "--", color="black", linewidth=1.3, zorder=2)
    for name, (x, y) in positions.items():
        marker = "o" if name.startswith("D") else "s"
        ax.plot([x], [y], marker, markersize=26, markerfacecolor="white", markeredgecolor="black", zorder=3)
        ax.annotate(name, (x, y), fontsize=5.5, ha="center", va="center", zorder=4)
    ax.set_xlim(-1.35, 1.35)
    ax.set_ylim(-1.3, 1.3)
    ax.axis("off")
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=200)
    plt.close(fig)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scores", type=Path, required=True)
    ap.add_argument("--published", type=Path, required=True, help="folder with the params files")
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()

    ours = ranked_non_edges(args.scores)
    table5 = json.loads((args.published / "published_table5.json").read_text())
    figure2 = json.loads((args.published / "published_figure2.json").read_text())

    report = {
        "top_20": [
            {"rank": r["rank"], "drug": r["drug"], "target": r["target"], "score": round(r["score"], 6)}
            for r in ours[:TOP]
        ],
        "table5": compare_table5(ours, table5["pairs"]),
        "figure2": compare_figure2(ours, args.scores, figure2),
        "annotation_source": table5["_source"],
    }
    draw_figure2(report["figure2"], ours, args.out_dir / "fig2_ours.png")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "predictions.json").write_text(json.dumps(report, indent=1, sort_keys=True) + "\n")

    t5 = report["table5"]
    print(
        f"Table 5: {t5['published_pairs_in_our_top_10']}/10 of the paper's pairs in our top 10,"
        f" {t5['published_pairs_in_our_top_20']}/10 in our top 20,"
        f" {t5['pairs_at_the_same_rank']}/10 at the same rank",
        flush=True,
    )
    f2 = report["figure2"]
    print(
        f"Figure 2: {f2['known_edges_ours_count']} known edges among its nodes;"
        f" {f2['predicted_edges_in_our_top_20_count']}/{f2['predicted_edges_count']}"
        " of its dashed edges are in our top 20",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
