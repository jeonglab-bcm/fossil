"""Check the Gist port on Gist's own sample run.

Gist ships doc/sample.mtx, doc/sample.labels and doc/sample.weights, the output of
`gist-train-svm -train sample.mtx -class sample.labels` written by Gist itself (header: Gist 2.0,
normalize=false, constant=1, positive and negative constraints 1, no diagonal factor,
convergence 1e-06, seed=1027461431, iterations=200, objective=0.0173686). Two checks:
1. kernel and classification: Gist's own printed weights through our kernel give its printed
   training discriminants (up to the 4-digit rounding of the weights);
2. training: the port, with those settings and the same seed, against the printed weights and
   the objective. The sample was written by Gist 2.0, and our port follows 2.3's source.

usage: port_check.py GIST_DOC_DIR OUT_JSON
"""
import json
import sys

import numpy as np
from numba import njit

import gist_port


def read_rdb(path):
    names, rows = [], []
    with open(path) as fh:
        lines = [l for l in fh if not l.startswith("#")]
    header = lines[0].rstrip("\n").split("\t")
    for line in lines[1:]:
        f = line.rstrip("\n").split("\t")
        if not f[0]:
            continue
        names.append(f[0])
        rows.append(f[1:])
    return header, names, rows


@njit(cache=True)
def dot_kernel(X):
    n, m = X.shape
    K = np.empty((n, n))
    for i in range(n):
        for j in range(n):
            s = 0.0
            for k in range(m):
                s += X[i, k] * X[j, k]
            K[i, j] = s
    return K


def main(doc, out):
    _, names, rows = read_rdb(f"{doc}/sample.mtx")
    X = np.array([[float(v) if v.strip() not in ("", "NaN") else 0.0 for v in r] for r in rows])
    _, lnames, lrows = read_rdb(f"{doc}/sample.labels")
    assert lnames == names
    positive = np.array([int(r[0]) == 1 for r in lrows])
    _, wnames, wrows = read_rdb(f"{doc}/sample.weights")
    assert wnames == names
    pub_w = np.array([float(r[1]) for r in wrows])
    pub_disc = np.array([float(r[3]) for r in wrows])

    K = dot_kernel(X)
    w, info = gist_port.train(K, positive, seed=1027461431, threshold=1e-6, diag_factor=0.0,
                              normalize=False, constant=1.0, pos_constraint=1.0,
                              neg_constraint=1.0)
    w4 = gist_port.printed(w)
    # Training discriminants: classify the training set with the unrounded weights
    # (train-main.c classifies before printing), printed with %.4g.
    disc = np.array([float("%.4g" % d) for d in gist_port._classify((K + 1.0), w)])
    # Kernel and classification alone: Gist's own printed weights through our kernel give
    # Gist's printed training discriminants?
    d_pub = np.array([float("%.4g" % d) for d in gist_port._classify((K + 1.0), pub_w)])
    same_w = int(np.sum(np.isclose(w4, pub_w, rtol=0, atol=0) | (w4 == pub_w)))
    near_w = int(np.sum(np.abs(w4 - pub_w) <= 1e-4 * np.maximum(1, np.abs(pub_w))))
    same_d = int(np.sum(disc == pub_disc))
    res = {
        "examples": len(names),
        "positives": int(positive.sum()),
        "published_iterations": 200,
        "port_iterations": info["iterations"],
        "published_support_vectors": int(np.sum(pub_w != 0)),
        "port_support_vectors": int(np.sum(w4 != 0)),
        "weights_equal_printed": same_w,
        "weights_within_1e-4": near_w,
        "train_discriminants_equal_printed": same_d,
        "max_abs_weight_difference": float(np.max(np.abs(w4 - pub_w))),
        "max_abs_discriminant_difference": float(np.max(np.abs(disc - pub_disc))),
        "objective": info["objective"],
        "published_objective": 0.0173686,
        "objective_difference": abs(info["objective"] - 0.0173686),
        "discriminants_from_published_weights_equal_printed": int(np.sum(d_pub == pub_disc)),
        "discriminants_from_published_weights_max_abs_difference":
            float(np.max(np.abs(d_pub - pub_disc))),
    }
    json.dump(res, open(out, "w"), indent=2)
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
