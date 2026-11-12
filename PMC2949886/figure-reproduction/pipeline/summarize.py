"""Means over the simulated data sets from the chunk sums written by simulate.R.

Usage: python summarize.py <chunk_dir> <out.json>

Writes, for each set (curves, levels, wilcoxon), filter, method, alpha and
fraction removed: the mean achieved FDR, power and pi0, the mean number of
rejections, and the number of data sets (n). Also collects the per-data-set
rows of the post-FDR filtering comparison (data sets 1..200).
"""
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path


def summarize(chunk_dir):
    acc = defaultdict(lambda: defaultdict(float))
    for f in sorted(Path(chunk_dir).glob("chunk*_sums.csv")):
        with open(f) as fh:
            for r in csv.DictReader(fh):
                key = (r["set"], r["filter"], r["method"], r["alpha"], r["fraction"])
                for k in ("fdr", "power", "pi0", "rejected", "kept", "n"):
                    acc[key][k] += float(r[k])
    out = {}
    for (st, filt, meth, alpha, frac), v in sorted(acc.items()):
        n = v["n"]
        node = out.setdefault(st, {}).setdefault(filt, {}).setdefault(meth, {}).setdefault(f"{float(alpha):g}", {})
        node[f"{float(frac):g}"] = {"fdr": v["fdr"] / n, "power": v["power"] / n, "pi0": v["pi0"] / n,
                                    "rejected": v["rejected"] / n, "n": int(n)}
    post = []
    for f in sorted(Path(chunk_dir).glob("chunk*_post.csv")):
        with open(f) as fh:
            for r in csv.DictReader(fh):
                post.append({"dataset": int(r["dataset"]), "filter": r["filter"], "situation": r["situation"],
                             "fraction": float(r["fraction"]), "fdr": float(r["fdr"]), "power": float(r["power"])})
    out["post"] = sorted(post, key=lambda r: (r["dataset"], r["filter"], r["situation"], r["fraction"]))
    out["datasets"] = max(v["n"] for v in acc.values())
    return out


if __name__ == "__main__":
    res = summarize(sys.argv[1])
    Path(sys.argv[2]).write_text(json.dumps(res, indent=0))
    print("data sets:", res["datasets"])
