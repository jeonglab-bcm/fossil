"""Hypothesis test: Table S2's USA CORG lists from GSE2034 re-normalized from its CEL files.

Usage: usa_cel_check.py MATRIX.tsv.gz[,...] SOURCES ANNOTATION OUT.json

Each MATRIX is a probes x arrays table written by R from GSE2034_RAW.tar (affy 1.80: rma() on
log2 scale, mas5() on the linear scale; columns named by GSM). Probes are collapsed to Entrez Gene
IDs as in the main run (single-gene probes, per-sample maximum) and as gene means; the CORGs of
Table S2's ten USA pathways are compared with the paper's. Not part of the pipeline: the CEL
files are 1 GB and need R with affy; this ran once on the cluster and its result is committed as
variants/usa_cel.json.
"""

import csv
import gzip
import json
import sys
from pathlib import Path

import numpy as np

import prepare_data as P
from compare import TABLE_S2
from pacorg import find_corgs, t_scores, zscore


def load(path):
    with gzip.open(path, "rt") as f:
        r = csv.reader(f, delimiter="\t")
        cols = next(r)[1:]
        ids, rows = [], []
        for p in r:
            ids.append(p[0])
            rows.append([float(v) for v in p[1:]])
    return ids, [c.split(".")[0] for c in cols], np.array(rows)


def main(mats, src, annotation, out):
    src, ann = Path(src), P.Annotation(Path(annotation))
    clin = {l.split("\t")[1]: int(l.split("\t")[4]) for l in open(src / "geo/gse2034_miniml/GSE2034-tbl-2.txt")}
    c2 = P.read_gmt(src / "gsea/c2.symbols.gmt")
    rows = TABLE_S2[("breast_usa", "breast_netherlands")]
    expected = [[ann.entrez(s) for s in r[4].split()] for r in rows]
    res = {"variant": "usa_cel", "description": "GSE2034 re-normalized from its CEL files (RMA, MAS5); Table S2's ten USA CORG lists", "results": {}}
    for m in mats.split(","):
        ids, gsm, X = load(m)
        y = np.array([clin[g] == 1 for g in gsm])
        for how in ("max", "mean"):
            g, Y = P.collapse([ann.probe["GPL96"].get(i) for i in ids], X, how)
            idx = {k: i for i, k in enumerate(g)}
            Z = zscore(Y[Y.std(1) > 0])
            g = [k for k, keep in zip(g, Y.std(1) > 0) if keep]
            idx = {k: i for i, k in enumerate(g)}
            t = t_scores(Z, y)
            exact = sets = 0
            for r, e in zip(rows, expected):
                members = []
                for s in c2[r[1]]:
                    k = ann.entrez(s)
                    if k in idx and idx[k] not in members:
                        members.append(idx[k])
                c = [g[i] for i in find_corgs(Z, y, members, t)]
                exact += c == e
                sets += set(c) == set(e)
            res["results"][f"{Path(m).name}/{how}"] = {"exact_lists": exact, "same_sets": sets, "lists": len(rows)}
    Path(out).write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:5])
