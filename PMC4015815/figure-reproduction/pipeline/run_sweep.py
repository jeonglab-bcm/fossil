"""Train and test the Gist SVM on all 54 families at each dMAX; write per-family ROC and ROC50.

usage: run_sweep.py --fasta F --membership M --sequences {residues|top1:FILE} --dmax 0,10,...
                    --out per_family.csv [--seed 1] [--workers 4] [--families 2.5.1.3,...]
                    [--save-weights DIR] [--clip cap|gist]

For each family: training set = codes 1 (positive) and 2 (negative), test set = codes 3 and 4,
in benchmark order. One Gist run per family and dMAX (gist_port.train, default options), test
discriminants from the printed weights (gist_port.classify).
"""
import argparse
import csv
import multiprocessing as mp
import os
import time

import numpy as np

import features
import gist_port
import roc

_K = None
_CODES = None
_FAMILIES = None
_SEED = 1
_SAVE = None
_DMAX = None
_CLIP = gist_port.CLIP_CAP


def load_sequences(spec, names, seqs):
    if spec == "residues":
        return seqs
    kind, path = spec.split(":", 1)
    assert kind == "top1"
    tnames, tseqs = features.read_fasta(path)
    assert tnames == names, "Top-1-gram FASTA rows differ from the benchmark"
    for s, t in zip(seqs, tseqs):
        assert len(s) == len(t)
    return tseqs


def run_family(j):
    codes = _CODES[:, j]
    train = np.flatnonzero((codes == 1) | (codes == 2))
    test = np.flatnonzero((codes == 3) | (codes == 4))
    pos_train = codes[train] == 1
    t0 = time.time()
    w, info = gist_port.train(_K[np.ix_(train, train)], pos_train, seed=_SEED, clip=_CLIP)
    wp = gist_port.printed(w)
    diag = np.diag(_K)
    disc = gist_port.classify(_K[np.ix_(test, train)], diag[test], diag[train], wp, clip=_CLIP)
    r, r50 = roc.roc_scores(disc, codes[test] == 3)
    if _SAVE:
        fam = _FAMILIES[j]
        np.savez_compressed(os.path.join(_SAVE, f"{fam}_d{_DMAX}_s{_SEED}.npz"),
                            train=train, test=test, weights=w, printed=wp, discriminants=disc)
    return {"family": _FAMILIES[j], "roc": r, "roc50": r50,
            "n_train": len(train), "n_pos_train": int(pos_train.sum()),
            "n_test": len(test), "n_pos_test": int((codes[test] == 3).sum()),
            "iterations": info["iterations"], "support_vectors": info["support_vectors"],
            "seconds": round(time.time() - t0, 2)}


def main():
    global _K, _CODES, _FAMILIES, _SEED, _SAVE, _DMAX, _CLIP
    ap = argparse.ArgumentParser()
    ap.add_argument("--fasta", required=True)
    ap.add_argument("--membership", required=True)
    ap.add_argument("--sequences", default="residues")
    ap.add_argument("--dmax", default="150")
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    ap.add_argument("--families", default=None)
    ap.add_argument("--save-weights", default=None)
    ap.add_argument("--clip", choices=["cap", "gist"], default="cap",
                    help="normalized values above 1: cap at 1 (default) or Gist's 0 off-diagonal")
    a = ap.parse_args()

    names, seqs, families, codes = features.load_benchmark(a.fasta, a.membership)
    seqs = load_sequences(a.sequences, names, seqs)
    enc = [features.encode(s) for s in seqs]
    _CODES, _FAMILIES, _SEED, _SAVE = codes, families, a.seed, a.save_weights
    _CLIP = gist_port.CLIP_CAP if a.clip == "cap" else gist_port.CLIP_GIST
    if _SAVE:
        os.makedirs(_SAVE, exist_ok=True)
    cols = list(range(len(families)))
    if a.families:
        want = a.families.split(",")
        cols = [families.index(f) for f in want]
    dmaxes = [int(x) for x in a.dmax.split(",")]
    rows = []
    for d, K in features.kernels_by_dmax(enc, dmaxes):
        _K, _DMAX = K, d
        t0 = time.time()
        ctx = mp.get_context("fork")
        with ctx.Pool(a.workers) as pool:
            res = pool.map(run_family, cols, chunksize=1)
        for r in res:
            r["dmax"] = d
            r["seed"] = a.seed
            r["clip"] = a.clip
        rows += res
        print(f"dMAX={d}: mean ROC {np.mean([r['roc'] for r in res]):.4f} "
              f"ROC50 {np.mean([r['roc50'] for r in res]):.4f} ({time.time() - t0:.0f} s)",
              flush=True)
    keys = ["dmax", "seed", "clip", "family", "roc", "roc50", "n_train", "n_pos_train", "n_test",
            "n_pos_test", "iterations", "support_vectors", "seconds"]
    with open(a.out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        for r in rows:
            r["roc"] = f"{r['roc']:.6f}"
            r["roc50"] = f"{r['roc50']:.6f}"
            w.writerow(r)


if __name__ == "__main__":
    main()
