#!/usr/bin/env python3
"""Score every citation of the 1987-2012 dataset with the CITATION_PLUS_MESH model.

Writes DATA_DIR/all_scores.npz (pmid, year, rct, margin, confidence for every dataset citation) and
OUT_DIR/disagreements.json: the counts of the paper's Results (confidence >= 0.95 and >= 0.50 without
the RCT publication type, <= 0.05 with it, the RCT total) and the PMIDs of the extreme sets.

Usage: score_all.py MEDLINE_DIR DATA_DIR OUT_DIR [--workers 4] [--summary-only]
"""
import argparse
import glob
import json
import os
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pyarrow.compute as pc
import pyarrow.parquet as pq

from rctconf.model import RCTModel

_M = {}


def _score(path):
    m = _M.get("model")
    if m is None:
        m = _M["model"] = RCTModel.load(_M["path"])
    t = pq.read_table(path)
    t = t.filter(pc.and_(t["english"], t["has_abstract"]))
    if t.num_rows == 0:
        return None
    f = m.margins(t.to_pylist())
    return {"pmid": t["pmid"].to_numpy(), "year": t["year"].to_numpy(),
            "rct": t["rct"].to_numpy(zero_copy_only=False).astype(bool), "margin": f.astype(np.float64)}


def _init(path):
    _M["path"] = path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("medline_dir")
    ap.add_argument("data_dir")
    ap.add_argument("out_dir")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--summary-only", action="store_true", help="recount from DATA_DIR/all_scores.npz")
    a = ap.parse_args()
    model_path = os.path.join(a.data_dir, "model_citation_plus_mesh.npz")
    if a.summary_only:
        summarize(a.data_dir, a.out_dir, list(RCTModel.load(model_path).sigmoid))
        return
    files = sorted(glob.glob(os.path.join(a.medline_dir, "pubmed*.parquet")))
    with ProcessPoolExecutor(a.workers, initializer=_init, initargs=(model_path,)) as ex:
        parts = [p for p in ex.map(_score, files, chunksize=4) if p is not None]
    cols = {k: np.concatenate([p[k] for p in parts]) for k in ("pmid", "year", "rct", "margin")}
    # one row per PMID (the last baseline file wins, as in build_dataset.py)
    pm = cols["pmid"]
    _, last = np.unique(pm[::-1], return_index=True)
    keep = np.sort(len(pm) - 1 - last)
    cols = {k: v[keep] for k, v in cols.items()}
    model = RCTModel.load(model_path)
    cols["confidence"] = model.confidence_from_margins(cols["margin"])
    np.savez(os.path.join(a.data_dir, "all_scores.npz"), **cols)
    summarize(a.data_dir, a.out_dir, list(model.sigmoid))


def summarize(data_dir, out_dir, sigmoid):
    z = np.load(os.path.join(data_dir, "all_scores.npz"))
    cols = {k: z[k] for k in z.files}
    conf, rct = cols["confidence"], cols["rct"]
    hi95 = (conf >= 0.95) & ~rct
    hi50 = (conf >= 0.50) & ~rct
    lo05 = (conf <= 0.05) & rct
    order = np.argsort(conf[lo05])
    lowest10 = cols["pmid"][lo05][order[:10]]
    # hypothesis test: the same counts with the paper's baseline confidence, a zero-centred sigmoid
    sig = 1 / (1 + np.exp(-cols["margin"]))
    out = {
        "dataset": int(len(conf)),
        "rct_pt": int(rct.sum()),
        "conf_ge_0.95_without_rct_pt": int(hi95.sum()),
        "conf_ge_0.50_without_rct_pt": int(hi50.sum()),
        "conf_le_0.05_with_rct_pt": int(lo05.sum()),
        "lowest10_max_confidence": float(np.sort(conf[lo05])[:10].max()) if lo05.sum() >= 10 else None,
        "lowest10_pmids": [int(p) for p in lowest10],
        "sigmoid_baseline": {"conf_ge_0.95_without_rct_pt": int(((sig >= 0.95) & ~rct).sum()),
                             "conf_ge_0.50_without_rct_pt": int(((sig >= 0.50) & ~rct).sum()),
                             "conf_le_0.05_with_rct_pt": int(((sig <= 0.05) & rct).sum())},
        "by_year": {int(yv): {"n": int((cols["year"] == yv).sum()), "rct": int((rct & (cols["year"] == yv)).sum())}
                    for yv in np.unique(cols["year"])},
        "sigmoid": sigmoid,
    }
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "disagreements.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    # the extreme sets themselves, for anyone who wants to review them (PMIDs and our confidence)
    with open(os.path.join(out_dir, "disagreements_pmids.tsv"), "w") as fh:
        fh.write("set\tpmid\tyear\tconfidence\n")
        for name, sel in (("conf_ge_0.95_without_rct_pt", hi95), ("conf_le_0.05_with_rct_pt", lo05)):
            idx = np.nonzero(sel)[0]
            idx = idx[np.argsort(cols["pmid"][idx])]
            for i in idx:
                fh.write(f"{name}\t{cols['pmid'][i]}\t{cols['year'][i]}\t{conf[i]:.4f}\n")
    print(json.dumps({k: v for k, v in out.items() if k != "by_year"}, indent=1))


if __name__ == "__main__":
    main()
