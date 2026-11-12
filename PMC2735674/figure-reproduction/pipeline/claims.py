#!/usr/bin/env python3
"""The paper's quantitative statements, computed twice.

Each statement is computed first from the paper's own printed tables (the arithmetic check: it
shows that we form each statistic the way the paper did, and says nothing about our run), then
from our run. Only the second sets a verdict; references/text-claims.md explains the rule.

    claims.py --tables tables.json --published params/published_tables.json --out claims.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

DATASETS = ("e", "ic", "gpcr", "nr")
NAMES = {"e": "enzyme", "ic": "ion channel", "gpcr": "GPCR", "nr": "nuclear receptor"}
#: The three method rows of each part of a table. Sections 4.1 to 4.3 say "rows 1-3 and 10" and
#: so on, but the counts they then give only come back when the comparison is between the KRM row,
#: the BLM row and their aggregate, with the nearest-neighbour baseline left out, and when a tie
#: between a KRM row and a BLM row is not counted as a win for the BLM method. Both readings are
#: checked against the paper's own tables by the arithmetic check in this file.
NEW_DRUG = ["KRMd", "BLMd", "m(KRMd,BLMd)"]
NEW_TARGET = ["KRMt", "BLMt", "m(KRMt,BLMt)"]
AGGREGATED = ["m(KRMd,KRMt)", "m(BLMd,BLMt)", "m(KRMd,KRMt,BLMd,BLMt)"]
#: The rows Section 4.1 and 4.2 call "the BLM method or the aggregation of the two methods".
BLM_OR_BOTH = {"BLMd", "m(KRMd,BLMd)", "BLMt", "m(KRMt,BLMt)"}
#: The rows Section 4.3 calls "aggregating across the BLM method or across the two methods".
AGGREGATED_BLM = {"m(BLMd,BLMt)", "m(KRMd,KRMt,BLMd,BLMt)"}
KRM_ROWS = ["KRMd", "KRMt"]


def best_rows(values: dict, rows: list[str], metric: str) -> list[str]:
    """The row names with the largest value of `metric` among `rows` (ties kept)."""
    best = max(values[row][metric] for row in rows)
    return [row for row in rows if values[row][metric] == best]


def statements(values: dict[str, dict[str, dict[str, float]]]) -> dict:
    """Every statement of the paper's Section 4, from one set of table values.

    `values` is dataset -> row name -> {"auc": float, "aupr": float}.
    """
    out = {}
    for metric in ("auc", "aupr"):
        for dataset in DATASETS:
            rows = values[dataset]
            out[f"best_{metric}_krm_{dataset}"] = max(rows[row][metric] for row in KRM_ROWS)
            out[f"best_{metric}_new_{dataset}"] = max(r[metric] for r in rows.values())
    for name, rows, winners in (
        ("new_drug_conditions_won_by_blm", NEW_DRUG, BLM_OR_BOTH),
        ("new_target_conditions_won_by_blm", NEW_TARGET, BLM_OR_BOTH),
        ("aggregated_conditions_won_by_blm_aggregation", AGGREGATED, AGGREGATED_BLM),
    ):
        out[name] = sum(
            set(best_rows(values[dataset], rows, metric)) <= winners
            for dataset in DATASETS
            for metric in ("auc", "aupr")
        )
    return out


def from_published(published: dict) -> dict:
    return {
        dataset: {
            row: {"auc": float(v["auc"]), "aupr": float(v["aupr"])}
            for row, v in published[dataset].items()
            if not row.startswith("_")
        }
        for dataset in DATASETS
    }


def from_ours(tables: dict) -> dict:
    return {
        dataset: {row["method"]: {"auc": row["auc"], "aupr": row["aupr"]} for row in table["rows"]}
        for dataset, table in tables["tables"].items()
    }


#: What the paper states, as printed. The arithmetic check is these against the paper's tables.
PRINTED = {
    "best_auc_krm_e": "92.9", "best_auc_new_e": "97.6",
    "best_auc_krm_ic": "91.7", "best_auc_new_ic": "97.3",
    "best_auc_krm_gpcr": "87.3", "best_auc_new_gpcr": "95.5",
    "best_auc_krm_nr": "83.6", "best_auc_new_nr": "88.1",
    "best_aupr_krm_e": "80.6", "best_aupr_new_e": "84.1",
    "best_aupr_krm_ic": "79.6", "best_aupr_new_ic": "81.3",
    "best_aupr_krm_gpcr": "57.7", "best_aupr_new_gpcr": "66.7",
    "best_aupr_krm_nr": "43.6", "best_aupr_new_nr": "61.2",
    "new_drug_conditions_won_by_blm": "7",
    "new_target_conditions_won_by_blm": "6",
    "aggregated_conditions_won_by_blm_aggregation": "8",
}
#: Where each statement is made.
WHERE = {
    "best_auc": "Section 4.4: the best AUC passes from the kernel regression method's to this article's",
    "best_aupr": "Section 4.4: the best AUPR also improves on all four datasets",
    "new_drug_conditions_won_by_blm": "Section 4.1: in seven of the eight experimental conditions the best result comes from BLM or m(KRMd,BLMd)",
    "new_target_conditions_won_by_blm": "Section 4.2: in six of the eight experimental conditions the best result comes from BLM or m",
    "aggregated_conditions_won_by_blm_aggregation": "Section 4.3: in all cases, aggregating across BLM or across the two methods gives the best AUC and AUPR",
}


#: The counts the paper's Section 2.1 prints for each dataset.
PRINTED_COUNTS = {
    "e": {"drugs": "445", "targets": "664", "interactions": "2926"},
    "ic": {"drugs": "210", "targets": "204", "interactions": "1476"},
    "gpcr": {"drugs": "223", "targets": "95", "interactions": "635"},
    "nr": {"drugs": "54", "targets": "26", "interactions": "90"},
}
#: Section 1: "for the ion channel benchmark dataset with 1476 known drug-target interactions (out
#: of a possible 42 840), this meant that we achieved nearly 90% precision at 60% recall".
ION_CHANNEL_RECALL = 0.6
NEARLY_NINETY = 0.85


def dataset_counts(tables: dict) -> list[dict]:
    fields = []
    for dataset, printed in PRINTED_COUNTS.items():
        table = tables["tables"][dataset]
        for key, value in printed.items():
            fields.append(
                {
                    "name": f"{NAMES[dataset]} {key}",
                    "printed": value,
                    "ours": str(table[key]),
                }
            )
    return fields


def ion_channel_precision(figure1: dict) -> list[dict]:
    """The best precision of the three ion channel curves at 60% recall, published and ours."""
    grid = figure1["recall_grid"]
    index = grid.index(ION_CHANNEL_RECALL)
    panel = figure1["panels"]["b"]["curves"]
    published = max(curve["published"][index] for curve in panel.values())
    ours = max(curve["ours"][index] for curve in panel.values())
    return [
        {
            "name": "precision at 60% recall is nearly 90%",
            "printed": "yes",
            "arithmetic": "yes" if published >= NEARLY_NINETY else "no",
            "ours": "yes" if ours >= NEARLY_NINETY else "no",
            "arithmetic_matches": published >= NEARLY_NINETY,
        },
        {
            "name": "precision at 60% recall, read from the published curve and from ours",
            "printed": "0.9",
            "arithmetic": f"{published:.2f}",
            "ours": f"{ours:.2f}",
            "arithmetic_matches": abs(published - 0.9) <= 0.05,
        },
    ]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tables", type=Path, required=True)
    ap.add_argument("--published", type=Path, required=True)
    ap.add_argument("--figure1", type=Path, required=True, help="figure1_comparison.json")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    published = json.loads(args.published.read_text())
    tables = json.loads(args.tables.read_text())
    arithmetic = statements(from_published(published))
    ours = statements(from_ours(tables))

    fields = []
    for name, printed in PRINTED.items():
        decimals = 1 if "." in printed else 0
        fields.append(
            {
                "name": name,
                "printed": printed,
                "arithmetic": f"{arithmetic[name]:.{decimals}f}",
                "ours": f"{ours[name]:.{decimals}f}",
                "arithmetic_matches": f"{arithmetic[name]:.{decimals}f}" == printed,
            }
        )
    counts = dataset_counts(tables)
    precision = ion_channel_precision(json.loads(args.figure1.read_text()))
    report = {
        "dataset_counts": counts,
        "ion_channel_precision": precision,
        "note": (
            "printed: the paper's own value. arithmetic: the same statement recomputed from the"
            " paper's printed tables, which checks our formula and not our run. ours: the"
            " statement computed from our run, which is the only column a verdict uses."
        ),
        "where": WHERE,
        "fields": fields,
        "arithmetic_matched": sum(f["arithmetic_matches"] for f in fields),
        "statements": len(fields),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=1, sort_keys=True) + "\n")
    report["arithmetic_matched"] += sum(f["arithmetic_matches"] for f in precision)
    report["statements"] += len(precision)
    print(
        f"claims: {report['arithmetic_matched']} of {report['statements']} recomputed from the"
        " paper's own tables and figures come back",
        flush=True,
    )
    for field in counts:
        mark = " " if field["printed"] == field["ours"] else "!"
        print(f" {mark} {field['name']:46s} paper {field['printed']:>5s}  ours {field['ours']:>5s}", flush=True)
    for field in precision:
        print(
            f"   {field['name'][:46]:46s} paper {field['printed']:>5s}"
            f"  published curve {field['arithmetic']:>5s}  ours {field['ours']:>5s}",
            flush=True,
        )
    for field in fields:
        mark = " " if field["arithmetic_matches"] else "!"
        print(
            f" {mark} {field['name']:46s} paper {field['printed']:>5s}"
            f"  arithmetic {field['arithmetic']:>5s}  ours {field['ours']:>5s}",
            flush=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
