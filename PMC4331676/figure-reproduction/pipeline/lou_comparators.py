"""Table 4 comparator rows and their Fig. 5 ROC curves, recomputed from Lou et al. 2014 (Information S1).

Usage: lou_comparators.py LOU_S003.txt OUT.json

Section #1 holds the binary calls of six predictors on PDB186; section #2 the real-valued outputs
of DBPPred, DNAbinder and DNABIND. Metrics follow Eqs. 8 to 11 of the paper.
"""
import json
import sys
from pathlib import Path

import numpy as np
from pssmdt import metrics, roc_curve_points


def main(path, out):
    text = Path(path).read_text().replace("\r", "")
    s1, s2 = text.split("#2:")
    calls, reals = {}, {}
    names1 = names2 = None
    for line in s1.splitlines():
        f = line.split()
        if f[:2] == ["id", "actual"]:
            names1 = f[2:]
        elif names1 and len(f) == len(names1) + 2 and f[1] in "01":
            calls[f[0]] = [int(x) for x in f[1:]]
    for line in s2.splitlines():
        f = line.split()
        if f[:2] == ["id", "actual"]:
            names2 = f[2:]
        elif names2 and len(f) == len(names2) + 2 and f[1] in "01":
            reals[f[0]] = [int(f[1])] + [float(x) for x in f[2:]]
    assert len(calls) == 186 and len(reals) == 186, (len(calls), len(reals))
    ids = list(calls)
    y = np.array([calls[i][0] for i in ids])
    res = {"n": len(ids), "positives": int(y.sum()), "rows": {}, "roc": {}}
    for k, name in enumerate(names1):
        p = np.array([calls[i][k + 1] for i in ids])
        m = metrics(y, p - 0.5)
        row = {key: round(m[key], 4) for key in ("SN", "SP", "ACC", "MCC")}
        row.update({key: m[key] for key in ("TP", "TN", "FP", "FN")})
        res["rows"][name] = row
    yr = np.array([reals[i][0] for i in ids])
    assert (yr == y).all()
    for k, name in enumerate(names2):
        v = np.array([reals[i][k + 1] for i in ids])
        m = metrics(yr, v)
        res["rows"][name]["AUC"] = round(m["AUC"], 4)
        pos, neg = v[yr == 1], v[yr == 0]
        # the share of positive-negative pairs ranked strictly right (ties counted as misordered)
        res["rows"][name]["AUC_ties_misordered"] = round(100 * float((pos[:, None] > neg[None, :]).mean()), 4)
        fpr, tpr = roc_curve_points(yr, v)
        res["roc"][name] = {"fpr": np.round(fpr, 4).tolist(), "tpr": np.round(tpr, 4).tolist()}
    Path(out).write_text(json.dumps(res, indent=1) + "\n")
    for n, r in res["rows"].items():
        print(n, {k: r[k] for k in r if k in ("ACC", "MCC", "SN", "SP", "AUC")})


if __name__ == "__main__":
    main(*sys.argv[1:3])
