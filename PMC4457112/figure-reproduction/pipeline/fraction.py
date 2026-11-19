#!/usr/bin/env python3
"""The paper's training-fraction study: "classifier performance is basically flat between 5% and 10%
sampling of the training data", with all title and abstract features, by cross-validation.

We rerun it at 5%, 7.5% and 10% with one 2-fold split each (the paper used 5x2) to keep the run short.
Usage: fraction.py DATA_DIR OUT.json [--workers 4]
"""
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pyarrow.parquet as pq

import rctconf
from rctconf.model import FeatureSpace

SETS = [s for s in rctconf.CITATION_SETS if s.startswith(("title_", "abstract_"))]


def _feat(args):
    path, start, stop = args
    return rctconf.hashed_features(pq.read_table(path).slice(start, stop - start).to_pylist(), SETS)


def hashed(path, workers):
    n = pq.ParquetFile(path).metadata.num_rows
    jobs = [(path, s, min(s + 20000, n)) for s in range(0, n, 20000)]
    with ProcessPoolExecutor(workers) as ex:
        parts = list(ex.map(_feat, jobs))
    out = {}
    for s in SETS:
        ptrs, hs, off = [np.zeros(1, dtype=np.int64)], [], 0
        for p in parts:
            ptr, h = p[s]
            ptrs.append(ptr[1:] + off)
            hs.append(h)
            off += len(h)
        out[s] = (np.concatenate(ptrs), np.concatenate(hs))
    return out


def main():
    data_dir, out = sys.argv[1:3]
    workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 4
    res = {}
    for fr, path in (("0.05", "train_fraction_0.05.parquet"), ("0.075", "train_sample.parquet"),
                     ("0.1", "train_fraction_0.1.parquet")):
        p = os.path.join(data_dir, path)
        y = pq.read_table(p, columns=["rct"])["rct"].to_numpy(zero_copy_only=False).astype(bool)
        h = hashed(p, workers)
        sp_ = FeatureSpace.fit(h, SETS)
        blocks = [FeatureSpace.fit(h, [s]).matrix(h) for s in SETS]
        del h
        r = rctconf.cross_validate(blocks, y, repeats=1, seed=0)
        res[fr] = {"n": int(len(y)), "auc": r["auc"], "f1": r["f1"], "features": int(sp_.n_features)}
        print(fr, res[fr], flush=True)
        del blocks
    json.dump(res, open(out, "w"), indent=1)


if __name__ == "__main__":
    main()
