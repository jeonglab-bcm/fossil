"""ROC50 under other definitions, from saved test discriminants (hypothesis tests for Table 1).

usage: roc50_variants.py FASTA MEMBERSHIP DISC_DIR DMAX OUT_JSON [DISC_DIR_DT]

The paper defines ROC50 as "the area under the ROC curve up to the first 50 false positives".
Our ROC (all negatives) matches Table 1 and Figure 3, but our ROC50 (Gribskov and Robinson's
normalized area, roc.py) does not. Each variant here is one reading of that sentence, averaged
over the 54 families:
  gribskov      (1 / 50 P) sum_{i=1..50} TP above the i-th false positive    (ours)
  tpr_at_50     the share of positives above the 50th false positive
  first_50_fps  area up to 50 FPs with the curve's x normalized by all negatives and the result
                rescaled by N / 50 (identical to gribskov; kept as a check)
"""
import glob
import json
import os
import sys

import numpy as np

import features
import roc


def variants(s, y):
    pos = np.sort(s[y])
    neg = np.sort(s[~y])[::-1]
    P, N = len(pos), len(neg)
    t = P - np.searchsorted(pos, neg[:50], side="right")
    g = roc.roc_n(s, y, 50)
    return {"gribskov": g, "tpr_at_50": float(t[-1] / P),
            "first_50_fps": float((t / P).sum() / N * N / 50)}


def run(fasta, membership, ddir, dmax):
    names, seqs, fams, codes = features.load_benchmark(fasta, membership)
    per = {}
    for f in sorted(glob.glob(os.path.join(ddir, f"*_d{dmax}_s*.npz"))):
        fam = os.path.basename(f).split("_d")[0]
        z = np.load(f)
        y = codes[z["test"], fams.index(fam)] == 3
        per[fam] = variants(z["discriminants"], y)
    keys = next(iter(per.values())).keys()
    return {"families": len(per),
            "means": {k: round(float(np.mean([v[k] for v in per.values()])), 4) for k in keys},
            "per_family": per}


def main(fasta, membership, ddir, dmax, out, ddir_dt=None):
    res = {"SVM-DR": run(fasta, membership, ddir, dmax)}
    if ddir_dt:
        res["SVM-DT"] = run(fasta, membership, ddir_dt, dmax)
    res["published"] = {"SVM-DR": 0.715, "SVM-DT": 0.800}
    json.dump(res, open(out, "w"), indent=1)
    for k, v in res.items():
        if k != "published":
            print(k, v["families"], v["means"])


if __name__ == "__main__":
    main(*sys.argv[1:])
