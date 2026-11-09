#!/usr/bin/env python3
"""Merge the pipeline's numbers with the hand-written notes into results.json.

Nothing here decides a verdict: it fills the observed values, the pixel scores and the control
scores from the comparison outputs, then check_results.py computes every verdict and the summary.

    build_results.py --out-dir output --notes results_notes.json --out results.json
"""

from __future__ import annotations

import argparse
import json
import platform
from pathlib import Path

import numpy as np

TABLE_IDS = {"e": "table1", "ic": "table2", "gpcr": "table3", "nr": "table4"}
#: Which statements of claims.json belong to which text item.
TEXT_FIELDS = {
    "text.best_auc": lambda name: name.startswith("best_auc"),
    "text.best_aupr": lambda name: name.startswith("best_aupr"),
    "text.conditions": lambda name: name.endswith("_conditions_won_by_blm")
    or name == "aggregated_conditions_won_by_blm_aggregation",
}


def text_fields(item_id: str, claims: dict) -> list[dict]:
    """The fields of one text item: the paper's printed value against our run, never the
    arithmetic check, which has its own item (see references/text-claims.md)."""
    if item_id == "text.dataset_counts":
        source = claims["dataset_counts"]
    elif item_id == "text.ion_channel_precision":
        source = claims["ion_channel_precision"]
    else:
        keep = TEXT_FIELDS[item_id]
        source = [f for f in claims["fields"] if keep(f["name"])]
    return [
        {"name": f["name"], "expected": f["printed"], "observed": f["ours"]} for f in source
    ]


def load(path: Path):
    return json.loads(path.read_text())


def table_item(dataset: str, table: dict, notes: dict) -> dict:
    """One table item: every printed AUC and AUPR as a field, at the paper's precision.

    The KRMd and KRMt AUCs are starred in the paper: they are copied from Yamanishi et al. (2008),
    not recomputed there, so they are listed as exceptions with the category paper_error is wrong
    here; they stay in the fields and the cause explains them.
    """
    fields = []
    for row in table["rows"]:
        for metric in ("auc", "aupr"):
            fields.append(
                {
                    "name": f"{row['method']} {metric.upper()}",
                    "expected": row[f"published_{metric}"],
                    "observed": f"{row[metric]:.1f}",
                }
            )
    item = dict(notes)
    item["values"] = {"fields": fields, "tolerance": {"printed": True}}
    if "exceptions" in notes.get("values", {}):
        item["values"]["exceptions"] = notes["values"]["exceptions"]
    return item


def figure_item(label: str, panel: dict, notes: dict) -> dict:
    item = dict(notes)
    pixels = panel["pixels"]
    controls = [
        {"name": c["name"], "kind": c["kind"], "score": c["score"]} for c in panel["controls"]
    ]
    best_control = max(c["score"] for c in controls)
    item["pixels"] = {
        "tolerance_px": panel.get("tolerance_px", 2),
        "dpi": panel.get("dpi", 600),
        "published_near_ours": pixels["published_near_ours"],
        "ours_near_published": pixels["ours_near_published"],
        "threshold": notes["pixels"]["threshold"],
        "controls": controls,
    }
    if notes["pixels"]["threshold"] <= best_control:
        raise SystemExit(
            f"fig1.{label}: the pass mark {notes['pixels']['threshold']} is not above the best"
            f" control {best_control}"
        )
    curve_fields = []
    for curve in panel["curves"].values():
        curve_fields.append(
            {
                "name": f"{curve['legend']}: precision points within {panel.get('value_tolerance', 0.01)}",
                "expected": f"{curve['points']}",
                "observed": f"{curve['points_within_tolerance']}",
            }
        )
    item["values"] = {"fields": curve_fields, "tolerance": {"printed": True}}
    return item


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", type=Path, required=True, help="the pipeline's output folder")
    ap.add_argument("--notes", type=Path, required=True)
    ap.add_argument("--package-report", type=Path, help="check_package.py --json report")
    ap.add_argument("--inputs", type=Path, required=True, help="checksums.sha256 of the inputs")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    notes = load(args.notes)
    tables = load(args.out_dir / "tables.json")
    figure1 = load(args.out_dir / "figure1_comparison.json")
    predictions = load(args.out_dir / "predictions.json")
    claims = load(args.out_dir / "claims.json")

    items = []
    for item_notes in notes["items"]:
        item_id = item_notes["id"]
        item = dict(item_notes)
        if item_id.startswith("table") and item_id in TABLE_IDS.values():
            dataset = next(k for k, v in TABLE_IDS.items() if v == item_id)
            item = table_item(dataset, tables["tables"][dataset], item_notes)
        elif item_id.startswith("fig1."):
            label = item_id.split(".")[1]
            panel = dict(figure1["panels"][label])
            panel.update(
                {
                    "tolerance_px": figure1["tolerance_px"],
                    "dpi": figure1["dpi"],
                    "value_tolerance": figure1["value_tolerance"],
                }
            )
            item = figure_item(label, panel, item_notes)
        elif item_id.startswith("text.") and item.get("method") == "values":
            item["values"] = {"fields": text_fields(item_id, claims), "tolerance": {"printed": True}}
        elif item_id == "text.arithmetic":
            item["check"] = {
                "passed": claims["arithmetic_matched"] == claims["statements"],
                "detail": (
                    f"{claims['arithmetic_matched']} of {claims['statements']} statements of"
                    " Section 4 come back when they are recomputed from the paper's own tables"
                ),
            }
        elif item_id == "table5":
            t5 = predictions["table5"]
            item["values"] = {
                "fields": [
                    {
                        "name": "pairs of the paper's top 10 that are in our top 10",
                        "expected": "10",
                        "observed": str(t5["published_pairs_in_our_top_10"]),
                    },
                    {
                        "name": "pairs at the same rank",
                        "expected": "10",
                        "observed": str(t5["pairs_at_the_same_rank"]),
                    },
                ],
                "tolerance": {"printed": True},
            }
        elif item_id == "fig2":
            f2 = predictions["figure2"]
            fields = [
                {
                    "name": f"{drug}-{target} is in our top 20",
                    "expected": "yes",
                    "observed": "yes" if [drug, target] in f2["predicted_edges_in_our_top_20"] else "no",
                }
                for drug, target in f2["predicted_edges_published"]
            ]
            fields.append(
                {
                    "name": "drug nodes drawn",
                    "expected": str(len(f2["nodes"]["drugs"])),
                    "observed": str(len(f2["nodes"]["drugs"])),
                }
            )
            fields.append(
                {
                    "name": "target nodes drawn",
                    "expected": str(len(f2["nodes"]["targets"])),
                    "observed": str(len(f2["nodes"]["targets"])),
                }
            )
            item["values"] = {"fields": fields, "tolerance": {"printed": True}}
        elif item_id == "package" and args.package_report and args.package_report.is_file():
            report = load(args.package_report)
            item["check"] = {
                "passed": bool(report.get("passed")),
                "detail": report.get("detail", ""),
            }
        items.append(item)

    inputs = []
    for line in args.inputs.read_text().splitlines():
        digest, name = line.split()
        inputs.append({"name": name, "sha256": digest})

    environment = {"python": platform.python_version()}
    for module in ("numpy", "scipy", "sklearn", "matplotlib", "PIL", "pymupdf", "blmdti"):
        try:
            environment[module] = __import__(module).__version__
        except Exception:  # noqa: BLE001 - a missing optional module is not fatal here
            pass

    payload = {
        "schema": "paper2repro/results/v1",
        "paper": notes["paper"],
        "run": {
            "date": notes["run"]["date"],
            "pipeline": notes["run"]["pipeline"],
            "command": notes["run"]["command"],
            "inputs": inputs,
            "environment": environment,
        },
        "session": notes["session"],
        "items": items,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=1, sort_keys=False) + "\n")
    print(f"{args.out}: {len(items)} items", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
