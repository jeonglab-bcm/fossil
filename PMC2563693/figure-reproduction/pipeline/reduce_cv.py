"""Summarize the per-repeat CV results: mean and standard error of every score, the Wilcoxon
signed-rank test of PAC against Gene, and how often each pathway was used across datasets.

Usage: reduce_cv.py CVDIR OUT.json

CVDIR holds <within|cross>/<name>.json.gz packs (pack_cv.py) or folders of repeat files.
"""

from __future__ import annotations

import gzip
import json
import math
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from scipy.stats import wilcoxon


def summarize(reps):
    folds = [f for r in reps for f in r["folds"]]
    keys = [k for k in folds[0]["scores"] if not k.endswith("draws")]
    out = {"repeats": len(reps), "partitions": len(folds), "scores": {}, "tests": {}}
    for k in keys:
        v = np.array([f["scores"][k] for f in folds], dtype=float)
        out["scores"][k] = {"mean": float(np.nanmean(v)), "ste": float(np.nanstd(v, ddof=1) / math.sqrt(len(v)))}
    for kind in ("lr", "knn3", "knn5", "nb", "lda", "fwd"):
        a, b = f"PAC/{kind}", f"Gene/{kind}"
        if a in keys and b in keys:
            x = np.array([f["scores"][a] for f in folds])
            y = np.array([f["scores"][b] for f in folds])
            if np.allclose(x, y):
                continue
            p = float(wilcoxon(x, y).pvalue)
            out["tests"][kind] = {"p": p, "neglog10p": -math.log10(p) if p > 0 else math.inf,
                                  "neglnp": -math.log(p) if p > 0 else math.inf,
                                  "pac_better": bool(np.mean(x) > np.mean(y))}
    used = Counter(p for f in folds for p in f.get("pac_used", []))
    out["pathway_frequency"] = dict(used.most_common())
    if "n_corgs" in folds[0]:
        out["n_genes_mean"] = float(np.mean([f["n_genes"] for f in folds]))
    return out


def main(cv: Path, out: Path):
    res = {"within": {}, "cross": {}}
    for kind in ("within", "cross"):
        for p in sorted((cv / kind).glob("*.json.gz")):  # packs (pack_cv.py)
            with gzip.open(p, "rt") as f:
                res[kind][p.name[: -len(".json.gz")]] = summarize(json.load(f)["repeats"])
        for d in sorted(x for x in (cv / kind).glob("*") if x.is_dir()):  # loose repeat files
            reps = [json.loads(r.read_text()) for r in sorted(d.glob("rep*.json"))]
            if reps:
                res[kind][d.name] = summarize(reps)
    out.write_text(json.dumps(res, indent=1))
    return res


if __name__ == "__main__":
    r = main(Path(sys.argv[1]), Path(sys.argv[2]))
    for kind, v in r.items():
        for name, s in v.items():
            sc = s["scores"]
            print(kind, name, s["partitions"], {k: round(sc[k]["mean"], 3) for k in sc if k.endswith("/lr")},
                  {k: round(t["neglog10p"], 1) for k, t in s["tests"].items()})
