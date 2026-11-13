"""Tests of the hypotheses behind the results that do not come back: hypotheses.json.

Usage: hypotheses.py DATA SOURCES ANNOTATION VARIANTS_DIR OUT.json

Recomputed here (a few minutes):
  tian_rank       where Table 1's pathways rank in their marker dataset under six pathway scores
  usa_preprocess  Table S2's USA CORG lists under 24 ways of preparing GSE2034 (scale x collapse x
                  probe filter), and with each of the 107 relapses relabelled in turn
Read from VARIANTS_DIR (summaries of cross-validation runs with PAC_VARIANT set, made on the
cluster; see README, Run):
  random_nocorg   PAC_random without the CORG search
  cross_all       cross-dataset markers from all pathways (no Tian pre-selection)
  seq_stop        sequential selection stopped at the first marker that does not help
  nfkb_alt        NF-kB as series 180, 220 and 266 at all time points
"""

from __future__ import annotations

import gzip
import itertools
import json
import sys
from pathlib import Path

import numpy as np
from scipy import stats

import prepare_data as P
from common import Dataset, top_count
from compare import TABLE1, TABLE_S2
from pacorg import activity, find_corgs, t_scores, tian_scores, zscore


def tian_rank(data):
    out = {}
    for (s, t), rows in TABLE1.items():
        D = Dataset(data, s)
        Z = zscore(D.X)
        tt = t_scores(Z, D.y)
        names, sc = [], {k: [] for k in ("mean_t", "abs_mean_t", "mean_abs_t", "fisher", "corg_activity", "tian_sum_sqrt")}
        for n, r in zip(D.set_names, D.set_rows):
            if not r:
                continue
            names.append(n)
            x = tt[r]
            sc["mean_t"].append(x.mean())
            sc["abs_mean_t"].append(abs(x.mean()))
            sc["mean_abs_t"].append(np.abs(x).mean())
            sc["fisher"].append(-2 * np.log(2 * stats.t.sf(np.abs(x), len(D.y) - 2)).sum() / len(r))
            sc["corg_activity"].append(abs(float(t_scores(activity(Z, find_corgs(Z, D.y, r, tt)), D.y))))
            sc["tian_sum_sqrt"].append(abs(float(tian_scores(tt, [r])[0])))
        res = {}
        for k, v in sc.items():
            rank = np.argsort(np.argsort(-np.array(v), kind="stable"), kind="stable") + 1
            rk = [int(rank[names.index(r[1])]) for r in rows]
            res[k] = {"ranks": rk, "all_in_top52": max(rk) <= top_count(0.10)}
        out[f"{s} -> {t}"] = {"pathways": [r[1] for r in rows], "scores": res}
    return out


def usa_preprocess(src, ann):
    meta, ids, X0 = P.series_matrix(src / "geo/GSE2034_series_matrix.txt.gz")
    gsm = meta["ID_REF"][0]
    clin = {l.split("\t")[1]: int(l.split("\t")[4]) for l in open(src / "geo/gse2034_miniml/GSE2034-tbl-2.txt")}
    y0 = np.array([clin[g] == 1 for g in gsm])
    c2 = P.read_gmt(src / "gsea/c2.symbols.gmt")
    rows = TABLE_S2[("breast_usa", "breast_netherlands")]
    expected = [[ann.entrez(s) for s in r[4].split()] for r in rows]
    single = ann.probe["GPL96"]

    def build(scale, how):
        X = X0.copy()
        if scale == "log2_floor1":
            X = np.log2(np.maximum(X, 1))
        elif scale == "log2_floor20":
            X = np.log2(np.maximum(X, 20))
        keys = [single.get(i) for i in ids]
        if how in ("max", "mean"):
            return P.collapse(keys, X, how)
        groups = {}
        for i, k in enumerate(keys):
            if k:
                groups.setdefault(k, []).append(i)
        crit = X.mean(1) if how == "highest_mean" else X.var(1)
        g = list(groups)
        return g, np.array([X[max(groups[k], key=lambda i: crit[i])] for k in g])

    def score(g, Y, y):
        idx = {k: i for i, k in enumerate(g)}
        keep = Y.std(1) > 0
        Z = np.zeros_like(Y)
        Z[keep] = zscore(Y[keep])
        tt = t_scores(Z, y)
        ordered = sets = 0
        for r, e in zip(rows, expected):
            members = []
            for m in c2[r[1]]:
                k = ann.entrez(m)
                if k in idx and keep[idx[k]] and idx[k] not in members:
                    members.append(idx[k])
            c = [g[i] for i in find_corgs(Z, y, members, tt)]
            ordered += c == e
            sets += set(c) == set(e)
        return ordered, sets

    grid = {}
    for scale, how in itertools.product(["none", "log2_floor1", "log2_floor20"], ["max", "mean", "highest_mean", "highest_variance"]):
        g, Y = build(scale, how)
        o, s = score(g, Y, y0)
        grid[f"{scale}/{how}"] = {"exact_lists": o, "same_sets": s}
    g, Y = build("none", "max")
    flips = []
    for i in np.where(y0)[0]:
        y = y0.copy()
        y[i] = False
        o, s = score(g, Y, y)
        flips.append({"sample": gsm[i], "exact_lists": o, "same_sets": s})
    best = max(flips, key=lambda f: (f["same_sets"], f["exact_lists"]))
    return {"lists": len(rows), "grid": grid, "best_grid_sets": max(v["same_sets"] for v in grid.values()),
            "relabel_one_relapse": {"tried": len(flips), "best": best}}


def main(data, src, annotation, variants, out):
    res = {"tian_rank": tian_rank(Path(data)),
           "usa_preprocess": usa_preprocess(Path(src), P.Annotation(Path(annotation)))}
    for p in sorted(Path(variants).glob("*.json")):
        res[p.stem] = json.loads(p.read_text())
    Path(out).write_text(json.dumps(res, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k in ("tian_rank",)}, indent=1)[:2000])
    print(json.dumps(res["usa_preprocess"]["grid"]), res["usa_preprocess"]["relabel_one_relapse"]["best"])


if __name__ == "__main__":
    main(*sys.argv[1:6])
