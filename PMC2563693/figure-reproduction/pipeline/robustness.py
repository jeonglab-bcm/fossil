"""Fig. S1 (marker overlap between the two halves of 100 random splits) and Fig. S5 (CORGs per
pathway in the top 10%).

Usage: robustness.py DATA OUT.json [SPLITS]

Fig. S1: each split divides a dataset into two halves at random (stratified by class). In each
half, pathways are ranked by Tian's statistic, genes by |t|, and CORGs are found for the top
pathways. The overlap of the top n markers of the two halves is |A n B| / |A u B|; for CORGs, A
and B pool the CORGs of the top n pathways. n is 1, 2, 3, 5, 10 and 20% of the 522 pathways or
of the dataset's genes. The figure plots the mean over the splits.

Fig. S5: the number of CORGs of each of the top 52 pathways (Tian's statistic on the whole
dataset), summarized as MATLAB's boxplot draws it: quartiles, whiskers at the most extreme value
within 1.5 IQR of the box, and the values beyond them.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
from sklearn.model_selection import StratifiedKFold

from common import DATASETS, LABELS, Dataset, top_count
from cv import seed_for, tian
from pacorg import find_corgs, t_scores, zscore

FRACTIONS = [0.01, 0.02, 0.03, 0.05, 0.10, 0.20]


def jaccard(a, b):
    a, b = set(a), set(b)
    return len(a & b) / len(a | b) if a | b else math.nan


def matlab_prctile(x, p):
    """MATLAB prctile: sorted values sit at percentiles 100 * (i - 0.5) / n, linear in between."""
    x = np.sort(np.asarray(x, dtype=float))
    n = len(x)
    pos = np.clip(p / 100 * n + 0.5, 1, n)
    lo = int(math.floor(pos))
    hi = min(lo + 1, n)
    return float(x[lo - 1] + (pos - lo) * (x[hi - 1] - x[lo - 1]))


def boxstats(x):
    q1, med, q3 = (matlab_prctile(x, p) for p in (25, 50, 75))
    lo, hi = q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)
    inside = [v for v in x if lo <= v <= hi]
    return {"q1": q1, "median": med, "q3": q3, "whisker_low": float(min(inside)),
            "whisker_high": float(max(inside)), "outliers": sorted({float(v) for v in x if v < lo or v > hi})}


def half_markers(D, Z, idx, n_path_max, n_gene_max):
    t = t_scores(Z[:, idx], D.y[idx])
    order = np.argsort(-tian(t, D.set_rows), kind="stable")[:n_path_max]
    corgs = [find_corgs(Z[:, idx], D.y[idx], D.set_rows[p], t) for p in order]
    genes = np.argsort(-np.abs(t), kind="stable")[:n_gene_max]
    return list(order), corgs, list(genes)


def overlap(D, splits):
    Z = zscore(D.X)
    n_path = [top_count(f) for f in FRACTIONS]
    n_gene = [int(round(f * len(D.genes))) for f in FRACTIONS]
    # "CORGs": pooled CORGs of each half's own top pathways (the main reading). Two other
    # readings, kept as hypotheses: "CORGs_same_pathways", the mean Jaccard of the two halves' CORG
    # sets of each pathway in both tops; "CORGs_first_half_pathways", the pooled CORGs both halves
    # find for the first half's top pathways.
    res = {"Pathways": [], "CORGs": [], "Genes": [], "CORGs_same_pathways": [], "CORGs_first_half_pathways": []}
    for s in range(splits):
        skf = StratifiedKFold(2, shuffle=True, random_state=seed_for(D.name, "split", s) % (2**31))
        a, b = [v for _, v in skf.split(np.zeros(len(D.y)), D.y)]
        pa, ca, ga = half_markers(D, Z, a, max(n_path), max(n_gene))
        pb, cb, gb = half_markers(D, Z, b, max(n_path), max(n_gene))
        res["Pathways"].append([jaccard(pa[:k], pb[:k]) for k in n_path])
        res["CORGs"].append([jaccard({r for c in ca[:k] for r in c}, {r for c in cb[:k] for r in c}) for k in n_path])
        res["Genes"].append([jaccard(ga[:k], gb[:k]) for k in n_gene])
        cpa, cpb = dict(zip(pa, ca)), dict(zip(pb, cb))
        res["CORGs_same_pathways"].append([float(np.mean([jaccard(cpa[p], cpb[p]) for p in set(pa[:k]) & set(pb[:k])]))
                                           if set(pa[:k]) & set(pb[:k]) else 0.0 for k in n_path])
        tb = t_scores(Z[:, b], D.y[b])
        cb_same = {p: (cpb[p] if p in cpb else find_corgs(Z[:, b], D.y[b], D.set_rows[p], tb)) for p in pa}
        res["CORGs_first_half_pathways"].append([jaccard({r for p in pa[:k] for r in cpa[p]}, {r for p in pa[:k] for r in cb_same[p]})
                                                 for k in n_path])
    return {k: [float(v) for v in np.mean(np.array(x), axis=0)] for k, x in res.items()}


def corg_sizes(D):
    Z = zscore(D.X)
    t = t_scores(Z, D.y)
    top = np.argsort(-tian(t, D.set_rows), kind="stable")[: top_count(0.10)]
    return [len(find_corgs(Z, D.y, D.set_rows[p], t)) for p in top]


def main(data: Path, out: Path, splits: int = 100):
    res = {"figS1": {}, "figS5": {}, "figS5_sizes": {}, "splits": splits}
    for name in DATASETS:
        D = Dataset(data, name)
        sizes = corg_sizes(D)
        res["figS5_sizes"][LABELS[name]] = sizes
        res["figS5"][LABELS[name]] = boxstats(sizes)
        res["figS1"][LABELS[name]] = overlap(D, splits)
        print(name, res["figS5"][LABELS[name]], {k: [round(x, 3) for x in v] for k, v in res["figS1"][LABELS[name]].items()}, flush=True)
    out.write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]), int(sys.argv[3]) if len(sys.argv) > 3 else 100)
