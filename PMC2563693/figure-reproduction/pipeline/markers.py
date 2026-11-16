"""CORGs of every C2 pathway in every whole dataset, Fig. 4 and Fig. S4 activities, and C2 counts.

Usage: markers.py DATA SOURCES ANNOTATION OUTDIR

Writes OUTDIR/corgs/<dataset>.json ({pathway: CORG keys and symbols, Tian score}),
OUTDIR/figure4.json (t of the CORG activity, Poor minus Good, of the glycolysis and
estrogen-signalling pathways the text names, in each lung dataset; and the activity matrices the
heatmaps draw), OUTDIR/c2_counts.json and OUTDIR/symbol_map.json (the paper's printed CORG
symbols as Entrez Gene IDs, for the breast datasets).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

import prepare_data as P
from common import DATASETS, Dataset, top_count
from compare import TABLE1, TABLE_S2
from cv import tian
from pacorg import activity, find_corgs, t_scores, zscore

FIG4_PATHWAYS = ["GLYCOL", "breast_cancer_estrogen_signalling", "FRASOR_ER_DOWN"]


def main(data: Path, src: Path, annotation: Path, out: Path):
    (out / "corgs").mkdir(parents=True, exist_ok=True)
    acts = {}
    for name in DATASETS:
        D = Dataset(data, name)
        Z = zscore(D.X)
        t = t_scores(Z, D.y)
        tn = tian(t, D.set_rows)
        res = {"corgs": {}, "corg_symbols": {}, "tian": {}, "t": {}}
        top = set(np.argsort(-tn, kind="stable")[: top_count(0.10)])
        res["top10"] = [D.set_names[i] for i in sorted(top, key=lambda i: -tn[i])]
        for i, (p, rows) in enumerate(zip(D.set_names, D.set_rows)):
            if not rows:
                continue
            c = find_corgs(Z, D.y, rows, t)
            res["corgs"][p] = [D.genes[r] for r in c]
            res["corg_symbols"][p] = [D.symbols[r] for r in c]
            res["tian"][p] = float(tn[i])
            a = activity(Z, c)
            res["t"][p] = float(t_scores(a, D.y))
            acts.setdefault(name, {})[p] = a
        (out / "corgs" / f"{name}.json").write_text(json.dumps(res, indent=1))
        acts[name]["_y"] = D.y
        acts[name]["_t"] = res["t"]

    fig4 = {"t": {}, "heatmap": {}}
    for d in ("lung_michigan", "lung_boston"):
        fig4["t"][d] = {p: acts[d]["_t"][p] for p in FIG4_PATHWAYS}
    for tid, table in (("fig4", TABLE1), ("fig_s4", TABLE_S2)):
        names = sorted({r[1] for rows in table.values() for r in rows})
        for d in sorted({s for s, _ in table}):
            y = acts[d]["_y"]
            order = np.argsort(~y, kind="stable")  # cases (Poor, Metastatic) first
            fig4["heatmap"].setdefault(tid, {})[d] = {
                "pathways": names, "cases": int(y.sum()),
                "activity": [[round(float(v), 4) for v in acts[d][p][order]] for p in names]}
    (out / "figure4.json").write_text(json.dumps(fig4))

    c2 = P.read_gmt(src / "gsea/c2.symbols.gmt")
    (out / "c2_counts.json").write_text(json.dumps({
        "sets": len(c2), "genes": len({g for m in c2.values() for g in m}), "top10": top_count(0.10),
        "sizes": {k: len(v) for k, v in c2.items()}}, indent=1))

    ann = P.Annotation(annotation)
    smap = {}
    for (s, _), rows in TABLE_S2.items():
        for r in rows:
            for sym in r[4].split():
                smap.setdefault(s, {})[sym] = ann.entrez(sym)
    (out / "symbol_map.json").write_text(json.dumps(smap, indent=1))


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4]))
