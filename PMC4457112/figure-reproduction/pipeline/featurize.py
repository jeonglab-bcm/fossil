#!/usr/bin/env python3
"""Hash every feature set of the training sample and the test years with rctconf.

The author-count ranges come from the Fayyad-Irani MDLP on the training sample.
Writes <split>.features.npz ({set}__indptr, {set}__hashes, pmid, rct) and author_bins.json.
Usage: featurize.py DATA_DIR [--workers 4]
"""
import argparse
import json
import os
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pyarrow.parquet as pq

import rctconf
from rctconf.features import ALL_SETS

CHUNK = 20000


def _work(args):
    records, bins = args
    return rctconf.hashed_features(records, ALL_SETS, None if bins is None else np.asarray(bins))


def featurize_file(path, bins, workers):
    """Hashed features of every row of a Parquet file, CHUNK rows per task, few tasks in flight."""
    pf = pq.ParquetFile(path)
    parts, pending = [], []
    with ProcessPoolExecutor(workers) as ex:
        for batch in pf.iter_batches(batch_size=CHUNK):
            pending.append(ex.submit(_work, (batch.to_pylist(), bins)))
            if len(pending) >= 2 * workers:
                parts.append(pending.pop(0).result())
        parts.extend(f.result() for f in pending)
    out = {}
    for s in ALL_SETS:
        ptrs, hs, off = [np.zeros(1, dtype=np.int64)], [], 0
        for p in parts:
            ptr, h = p[s]
            ptrs.append(ptr[1:] + off)
            hs.append(h)
            off += len(h)
        out[f"{s}__indptr"] = np.concatenate(ptrs)
        out[f"{s}__hashes"] = np.concatenate(hs) if hs else np.zeros(0, dtype=np.uint64)
    t = pq.read_table(path, columns=["pmid", "rct", "year"])
    out["pmid"] = t["pmid"].to_numpy()
    out["rct"] = t["rct"].to_numpy(zero_copy_only=False).astype(bool)
    out["year"] = t["year"].to_numpy()
    return out


def load_hashed(path):
    z = np.load(path)
    h = {s: (z[f"{s}__indptr"], z[f"{s}__hashes"]) for s in ALL_SETS}
    return h, z["rct"].astype(bool), z["pmid"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data_dir")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--test-years", type=int, nargs="+", default=[2011, 2012])
    ap.add_argument("--force", action="store_true", help="featurize splits that already have a features file")
    a = ap.parse_args()
    tr = pq.read_table(os.path.join(a.data_dir, "train_sample.parquet"), columns=["n_authors", "rct"])
    bins = rctconf.mdl_cut_points(tr["n_authors"].to_numpy(), tr["rct"].to_numpy(zero_copy_only=False))
    with open(os.path.join(a.data_dir, "author_bins.json"), "w") as fh:
        json.dump({"cut_points": bins.tolist()}, fh)
    print("author-count cut points:", bins.tolist(), flush=True)
    for split in ["train_sample"] + [f"test{y}" for y in a.test_years]:
        if os.path.exists(os.path.join(a.data_dir, f"{split}.features.npz")) and not a.force:
            print(split, "already featurized", flush=True)
            continue
        out = featurize_file(os.path.join(a.data_dir, f"{split}.parquet"), bins.tolist(), a.workers)
        np.savez(os.path.join(a.data_dir, f"{split}.features.npz"), **out)
        print(split, len(out["pmid"]), "citations", flush=True)


if __name__ == "__main__":
    main()
