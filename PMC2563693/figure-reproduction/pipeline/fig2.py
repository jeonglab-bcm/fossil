"""Fig. 2: mean absolute t of the top 1-10% pathway markers, in the source and the verification dataset.

Usage: fig2.py DATA OUT.json

For each cross-dataset pair (source -> verification):
  CORGs of every C2 pathway from the whole source dataset; pathways ranked by |t| of their CORG
  activity in the source. For the top k pathways (k = 5, 10, 16, 26, 52):
    PAC      mean |t| of the CORG activities
    PAC_all  mean |t| of the activities over all measured members (same k pathways)
    CORGs    mean |t| of the CORG genes of those pathways, each gene once
    Genes    mean |t| of the same number of top genes ranked by their own |t| in the source
  in the source (panels A, C, E, G) and, with the same markers, in the verification dataset
  (B, D, F, H). Activities in the verification dataset are combined z-scores over its own samples.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

from common import PAIRS, TOP_FRACTIONS, Dataset, top_count
from pacorg import activity, find_corgs, t_scores, tian_scores, zscore

PANELS = {"breast_netherlands": ("A", "B"), "breast_usa": ("C", "D"), "lung_michigan": ("E", "F"), "lung_boston": ("G", "H")}


def run(data: Path, preselect: str = "tian_sum"):
    out = {}
    cache = {}
    for src_name, ver_name in PAIRS:
        S = cache.setdefault(src_name, Dataset(data, src_name))
        V = cache.setdefault(ver_name, Dataset(data, ver_name))
        Zs, Zv = zscore(S.X), zscore(V.X)
        ts, tv = t_scores(Zs, S.y), t_scores(Zv, V.y)
        pathways = []
        for name, rows in zip(S.set_names, S.set_rows):
            if not rows:
                continue
            corgs = find_corgs(Zs, S.y, rows, ts)
            pathways.append({
                "name": name,
                "corgs": corgs,
                "rows": rows,
                "pac": abs(float(t_scores(activity(Zs, corgs), S.y))),
                "pac_all": abs(float(t_scores(activity(Zs, rows), S.y))),
                "tian": float(np.mean(ts[rows])),
                "tian_meanabs": float(np.mean(np.abs(ts[rows]))),
                "tian_sum": float(tian_scores(ts, [rows])[0]),
            })
        if preselect != "none":
            key = {"tian_abs": lambda p: -abs(p["tian"]), "tian": lambda p: -p["tian"],
                   "tian_meanabs": lambda p: -p["tian_meanabs"], "tian_sum": lambda p: -abs(p["tian_sum"])}[preselect]
            pathways = sorted(pathways, key=key)[: top_count(0.10)]
        pathways.sort(key=lambda p: -p["pac"])
        gene_order = np.argsort(-np.abs(ts), kind="stable")
        src_series = {k: [] for k in ("PAC", "Genes", "CORGs", "PAC_all")}
        ver_series = {k: [] for k in ("PAC", "Genes", "CORGs", "PAC_all")}
        counts = []
        for f in TOP_FRACTIONS:
            top = pathways[: top_count(f)]
            corg_rows = sorted({r for p in top for r in p["corgs"]})
            genes = list(gene_order[: len(corg_rows)])
            counts.append({"pathways": len(top), "corgs": len(corg_rows)})
            src_series["PAC"].append(float(np.mean([p["pac"] for p in top])))
            src_series["PAC_all"].append(float(np.mean([p["pac_all"] for p in top])))
            src_series["CORGs"].append(float(np.mean(np.abs(ts[corg_rows]))))
            src_series["Genes"].append(float(np.mean(np.abs(ts[genes]))))
            # Verification dataset: the same markers.
            pac_v, all_v = [], []
            for p in top:
                cr = S.rows_in(V, p["corgs"])
                ar = S.rows_in(V, p["rows"])
                pac_v.append(abs(float(t_scores(activity(Zv, cr), V.y))) if cr else 0.0)
                all_v.append(abs(float(t_scores(activity(Zv, ar), V.y))) if ar else 0.0)
            ver_series["PAC"].append(float(np.mean(pac_v)))
            ver_series["PAC_all"].append(float(np.mean(all_v)))
            cv = S.rows_in(V, corg_rows)
            gv = S.rows_in(V, genes)
            ver_series["CORGs"].append(float(np.mean(np.abs(tv[cv]))))
            ver_series["Genes"].append(float(np.mean(np.abs(tv[gv]))))
        a, b = PANELS[src_name]
        out[a] = {"dataset": src_name, "kind": "source", "series": src_series, "counts": counts}
        out[b] = {"dataset": f"{src_name}->{ver_name}", "kind": "verification", "series": ver_series, "counts": counts}
    return dict(sorted(out.items()))


if __name__ == "__main__":
    res = run(Path(sys.argv[1]), *(sys.argv[3:4]))
    Path(sys.argv[2]).write_text(json.dumps(res, indent=1))
    for panel, r in res.items():
        print(panel, r["dataset"], {k: [round(v, 2) for v in s] for k, s in r["series"].items()})
