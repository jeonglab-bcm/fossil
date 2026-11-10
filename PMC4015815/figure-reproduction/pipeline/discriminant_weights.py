"""Discriminant weights of family 2.5.1.3 (Figures 4 and 5).

usage: discriminant_weights.py --fasta F --membership M --sequences residues|top1:FILE
                               --out OUT.json [--family 2.5.1.3] [--dmax 150] [--seed 1]

Paper, Eq. 3: w = M alpha, with M the matrix of training feature vectors and alpha the weights
from SVM training. We take alpha as Gist's signed output weights as printed (4 significant
digits; the file gist-classify reads), and M as the raw count vectors (Gist normalizes inside
the kernel; the paper does not say, and normalized vectors would give weights below 1, against
the published scales of tens). For each ordered pair (t_i, t_j) the vector of weights over
d = 0..dMAX is reported: for i = j, distance 0 is the composition weight T0_i (Figure 1 counts
"Top-1-gram pairs at distance 0, 1, 2", the pairs at distance 0 being (t_i, t_i)). Figure 4's L2
norm per pair runs over d = 0..dMAX, so the diagonal includes T0_i; the variant without it is
kept as l2_without_d0 (it ranks (L,L) 36th, where the paper and the variant with d = 0 rank it
2nd).
"""
import argparse
import json

import numpy as np
from numba import njit

import features
import gist_port
import run_sweep


@njit(cache=True)
def weight_vector(alpha, X):
    """w = sum_i alpha_i x_i, summed in row order (no BLAS: the same bits on every machine)."""
    n, m = X.shape
    w = np.zeros(m)
    for i in range(n):
        a = alpha[i]
        if a == 0.0:
            continue
        for k in range(m):
            w[k] += a * X[i, k]
    return w


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fasta", required=True)
    ap.add_argument("--membership", required=True)
    ap.add_argument("--sequences", default="residues")
    ap.add_argument("--family", default="2.5.1.3")
    ap.add_argument("--dmax", type=int, default=150)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", required=True)
    ap.add_argument("--clip", choices=["cap", "gist"], default="cap")
    a = ap.parse_args()

    names, seqs, families, codes = features.load_benchmark(a.fasta, a.membership)
    seqs = run_sweep.load_sequences(a.sequences, names, seqs)
    j = families.index(a.family)
    c = codes[:, j]
    train = np.flatnonzero((c == 1) | (c == 2))
    enc = [features.encode(seqs[i]) for i in train]
    X = features.feature_vectors(enc, a.dmax)
    K = X @ X.T
    clip = gist_port.CLIP_CAP if a.clip == "cap" else gist_port.CLIP_GIST
    w, info = gist_port.train(K, c[train] == 1, seed=a.seed, clip=clip)
    alpha = gist_port.printed(w)
    W = weight_vector(alpha, X)                    # 20 + 400 dmax
    comp = W[:20]
    pairs = W[20:].reshape(a.dmax, 20, 20)         # [d-1, first, second]
    l2_without0 = np.sqrt((pairs ** 2).sum(axis=0))   # [first, second], d = 1..dMAX
    l2 = l2_without0.copy()
    for i in range(20):
        l2[i, i] = np.sqrt(l2[i, i] ** 2 + comp[i] ** 2)   # d = 0..dMAX
    A = features.ALPHABET
    order = np.argsort(-l2.ravel())
    top = [(A[k // 20], A[k % 20], float(l2.ravel()[k])) for k in order[:5]]
    out = {
        "family": a.family, "dmax": a.dmax, "seed": a.seed, "clip": a.clip,
        "sequences": a.sequences,
        "alphabet": A, "n_train": int(len(train)), "support_vectors": info["support_vectors"],
        "l2_first_second": l2.tolist(), "l2_without_d0": l2_without0.tolist(),
        "l2_max": float(l2.max()), "l2_max_without_d0": float(l2_without0.max()),
        "top_pairs": top,
        "weights": {f"{p},{p}": [float(comp[A.index(p)])] +
                    pairs[:, A.index(p), A.index(p)].tolist() for p in "GL"},
    }
    for p in "GL":
        v = np.array(out["weights"][f"{p},{p}"][1:])
        out[f"{p}{p}_share_negative_d1"] = float(np.mean(v < 0))
    json.dump(out, open(a.out, "w"), indent=1)
    print(json.dumps({k: out[k] for k in ["l2_max", "l2_max_without_d0", "top_pairs",
                                           "GG_share_negative_d1", "LL_share_negative_d1"]}))


if __name__ == "__main__":
    main()
