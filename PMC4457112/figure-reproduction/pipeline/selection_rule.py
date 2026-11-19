#!/usr/bin/env python3
"""Hypothesis test: forward selection with AUC compared at three decimals instead of four.

The paper does not say how a set's improvement was judged; a coarser rule stops earlier and keeps
fewer sets (the paper kept 7 and 10). Adds "selection_3_decimals" to OUT_DIR/variants.json.
Usage: selection_rule.py DATA_DIR OUT_DIR [--workers 3]
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from featurize import load_hashed  # noqa: E402

import rctconf  # noqa: E402
from rctconf.model import FeatureSpace  # noqa: E402

data_dir, out_dir = sys.argv[1:3]
workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 3
sel = json.load(open(os.path.join(out_dir, "selection.json")))
hashed, y, _ = load_hashed(os.path.join(data_dir, "train_sample.features.npz"))
cands = {"citation_only": list(rctconf.CITATION_SETS),
         "citation_plus_mesh": list(rctconf.CITATION_SETS) + list(rctconf.MESH_SETS)}
blocks = {s: FeatureSpace.fit(hashed, [s]).matrix(hashed) for s in cands["citation_plus_mesh"]}
del hashed
res = {}
for kind, cs in cands.items():
    r = rctconf.forward_select(blocks, y, cs, repeats=sel.get("repeats", 1), seed=0, workers=workers, auc_decimals=3,
                               log=lambda *a: print(*a, flush=True))
    res[kind] = {"chosen": r["chosen"], "n_sets": len(r["chosen"]), "auc": r["auc"], "f1": r["f1"]}
    print(kind, "three decimals:", r["chosen"], flush=True)
path = os.path.join(out_dir, "variants.json")
v = json.load(open(path))
v["selection_3_decimals"] = res
json.dump(v, open(path, "w"), indent=1)
