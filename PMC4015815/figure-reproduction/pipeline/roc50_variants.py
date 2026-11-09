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
  roc_on_cut_list  ordinary ROC on the ranking cut at the 50th false positive (roc.roc_on_cut_list):
                the same area divided by the true positives found by the 50th false positive
                instead of by all positives. Fits both published values; not the stated definition
  rocr_unscaled ROCR's performance(pred, "auc", fpr.stop = 50 / N) as commonly called: the raw
                trapezoid area to that FPR, not divided by fpr.stop (equals gribskov * 50 / N)
  fpr_0.1, fpr_0.5  area to FPR 0.1 or 0.5, divided by that FPR ("50" read as 50 percent and a
                looser cut)
  roc_n_search  ROC_n for n = 50..250

Every family has at least 275 test negatives, so the 50th false positive always exists.
"""
import glob
import json
import os
import sys

import numpy as np

import features
import roc


def partial_area(s, y, fpr):
    """Trapezoid area under the ROC curve up to `fpr`, interpolated there (as ROCR does)."""
    o = np.argsort(-s, kind="mergesort")
    yy = y[o]
    x = np.r_[0, np.cumsum(~yy)] / (~y).sum()
    t = np.r_[0, np.cumsum(yy)] / y.sum()
    i = int(np.max(np.flatnonzero(x <= fpr)))
    t_end = np.interp(fpr, x[i:i + 2], t[i:i + 2]) if x[i] < fpr else t[i]
    x, t = np.r_[x[:i + 1], fpr], np.r_[t[:i + 1], t_end]
    return float(np.sum(0.5 * np.diff(x) * (t[1:] + t[:-1])))


def variants(s, y):
    pos = np.sort(s[y])
    neg = np.sort(s[~y])[::-1]
    P, N = len(pos), len(neg)
    assert N >= 50
    t = P - np.searchsorted(pos, neg[:50], side="right")
    g = roc.roc_n(s, y, 50)
    out = {"gribskov": g, "tpr_at_50": float(t[49] / P),
           "first_50_fps": float((t / P).sum() / N * N / 50),
           "roc_on_cut_list": roc.roc_on_cut_list(s, y, 50),
           "rocr_unscaled": partial_area(s, y, 50 / N),
           "fpr_0.1": partial_area(s, y, 0.1) / 0.1,
           "fpr_0.5": partial_area(s, y, 0.5) / 0.5}
    for n in (50, 100, 150, 200, 250):
        out[f"roc_{n}"] = roc.roc_n(s, y, n)
    return out


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
    res["about"] = ("ROC50 under other readings of 'the area under the ROC curve up to the first 50 "
                    "false positives', from the dMAX " + str(dmax) + " test discriminants "
                    "(run_sweep.py --save-weights); hypothesis tests, not part of the pipeline.")
    json.dump(res, open(out, "w"), indent=1)
    for k, v in res.items():
        if k not in ("published", "about"):
            print(k, v["families"], v["means"])


if __name__ == "__main__":
    main(*sys.argv[1:])
