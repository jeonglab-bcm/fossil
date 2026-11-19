#!/usr/bin/env python3
"""The paper's preliminary result: the best single feature is the term "randomized" (F1 about 0.72).

For every feature of every citation set in the training sample, the F1 of the rule "RCT when the
feature is present"; the same for "randomized" anywhere in the title or abstract; and, as tests of the
gap, for "randomized or randomised", any word starting with "random", and any word starting with
"randomiz" or "randomis".
Usage: single_feature.py DATA_DIR OUT.json
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from featurize import load_hashed  # noqa: E402

import rctconf  # noqa: E402
from rctconf.features import feature_hash  # noqa: E402

data_dir, out = sys.argv[1:3]
h, y, _ = load_hashed(os.path.join(data_dir, "train_sample.features.npz"))
npos = int(y.sum())
best = []
for s in rctconf.CITATION_SETS:
    ptr, hs = h[s]
    rows = np.repeat(np.arange(len(ptr) - 1), np.diff(ptr))
    u, inv, n1_ = np.unique(hs, return_inverse=True, return_counts=True)
    n11 = np.bincount(inv, weights=y[rows].astype(float), minlength=len(u))
    f1 = 2 * n11 / (n1_ + npos)
    top = np.argsort(-f1)[:5]
    best += [(float(f1[i]), s, int(u[i])) for i in top]
best.sort(reverse=True)


def has(s, value):
    ptr, hs = h[s]
    hv = np.uint64(feature_hash(s, value))
    rows = np.repeat(np.arange(len(ptr) - 1), np.diff(ptr))
    m = np.zeros(len(y), dtype=bool)
    m[rows[hs == hv]] = True
    return m


r_title = has("title_unigrams", "randomized")
r_abs = has("abstract_unigrams", "randomized")
res = {}
for name, m in (("title_or_abstract", r_title | r_abs), ("abstract", r_abs), ("title", r_title)):
    res[name] = rctconf.binary_measures(y, m)
named = {}
for f1, s, hv in best[:10]:
    named[f"{s}:{hv}"] = f1
known = {feature_hash("abstract_unigrams", w): w for w in ("randomized", "randomised", "placebo", "randomly", "trial")}
known.update({feature_hash("title_unigrams", w): w for w in ("randomized", "trial", "placebo")})
known.update({feature_hash("abstract_bigrams", w): w for w in ("randomized controlled", "randomly assigned", "double blind")})
# name the top features by finding them in the training records
import pyarrow.parquet as pq  # noqa: E402
want = {(s, hv) for _, s, hv in best[:10]}
names = {}
recs = pq.read_table(os.path.join(data_dir, "train_sample.parquet")).to_pylist()
for rec in recs:
    raw = rctconf.raw_features(rec, sorted({s for s, _ in want}), None)
    for s, vals in raw.items():
        for v in vals:
            hv = feature_hash(s, v)
            if (s, hv) in want:
                names[(s, hv)] = v
    if len(names) == len(want):
        break
top = [{"set": s, "feature": names.get((s, hv), known.get(hv, f"hash {hv}")), "f1": f1} for f1, s, hv in best[:10]]
# hypothesis tests for the gap to the paper's F1 of about 0.72: other spellings and word forms
import re  # noqa: E402
text = [((r.get("title") or "") + " " + (r.get("abstract") or "")).lower() for r in recs]
yy = np.array([bool(r["rct"]) for r in recs])
hyp = {}
for name, pat in (("randomized_or_randomised", r"\brandomi[sz]ed\b"), ("random_prefix", r"\brandom\w*"),
                  ("randomi_stem", r"\brandomi[sz]\w*")):
    rx = re.compile(pat)
    m = np.array([bool(rx.search(t)) for t in text])
    hyp[name] = rctconf.binary_measures(yy, m)
json.dump({"randomized": res, "top_single_features": top, "hypotheses": hyp,
           "best_is_randomized": top[0]["feature"] == "randomized"}, open(out, "w"), indent=1)
print(json.dumps(res["title_or_abstract"]), top[:3])
