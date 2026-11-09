"""Sensitivity of the PSSM-DT jackknife (Tables 1 and 2) to the settings the paper does not state.

Usage: sensitivity.py PSSMS.npz PSSM_DIR BLASTP.tsv OUT.json [--jobs N]

Each variant changes one input of the main run (UniRef100 2014_01 PSSMs, raw scores, all 1,075
sequences, features scaled to [-1, 1], C and gamma from a 5-fold grid with split seed 0) and reruns
the grid search and the jackknife:

* uniref90: PSSMs from UniRef90 2014_01 instead (PSSM_DIR/pssm_uniref90_2014_01.npz);
* logistic: the PSSM passed through 1 / (1 + exp(-x)) before the transformation;
* no_defects: without the 7 DNA strands and the 5 X-containing chains of the supplement;
* split_seed_1: C and gamma chosen on another 5-fold split;
* unscaled: the transformation fed to the SVM without scaling.

For Table 4 the PSSM-DT model is trained, with the main run's C and gamma, on the benchmark after
removing chains whose identity to a same-class PDB186 chain (cd-hit-2d's definition, from the
blastp alignments) exceeds 25 (the main run), 30, 40 (cd-hit's lowest threshold), 50, 60, 70, 80,
90 or 99 %, or nothing at all.

For Fig. 2, the rank among the 400 pairs of (R,R), (R,P), (P,R) and (A,R) is computed from the
discriminant weights of the full-benchmark model with scaled or unscaled features in Eq. 12, with
either sign taken as "DNA-binding", for the raw and the logistic PSSM, and from the plain
difference of the class means of the features.

For Table 2 the four comparator encodings are rerun (grid search and jackknife) on the UniRef90
PSSMs, and on the raw scores instead of the logistic ones. For Table 4 the PDB186 test is also
repeated with the UniRef90 PSSMs, with and without the 25 % filter.

These are hypothesis tests for the causes in results.json; none of them is the reproduction.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pssmdt

from experiments import features, grid, jackknife, load, rounded, subset

DEFECTS = {"1AOII", "3THWD", "4FCYC", "4GNXL", "4GNXK", "4JJNJ", "4JJNI",
           "1XMZA", "2C15A", "2V5IA", "2QM0A", "2Y0GA"}


def run(X, y, jobs, seed=0, scale=True):
    Xs = pssmdt.scale(X) if scale else X
    g, _ = grid(Xs, y, jobs, seed)
    dec = jackknife(Xs, y, 2.0 ** g["log2C"], 2.0 ** g["log2gamma"], jobs)
    return {"log2C": g["log2C"], "log2gamma": g["log2gamma"], "jackknife": rounded(pssmdt.metrics(y, dec))}


def filters(D, X, y, idx, blastp, main_run):
    """PDB186 metrics after removing benchmark chains above each identity threshold."""
    label = {str(D["id"][i]): int(D["label"][i]) for i in range(len(D["id"])) if D["set"][i] == "benchmark"}
    plabel = {str(D["id"][i]): int(D["label"][i]) for i in range(len(D["id"])) if D["set"][i] == "pdb186"}
    best = {}
    for line in Path(blastp).read_text().splitlines():
        q, s_, nident, length, qlen, slen, ev = line.split("\t")
        q, s_ = q.split("|")[0], s_.split("|")[0]
        if label[q] != plabel[s_]:
            continue
        best[q] = max(best.get(q, 0.0), int(nident) / min(int(qlen), int(slen)))
    te = subset(D, "pdb186")
    Xte, yte = features(D, te, "PSSM-DT"), D["label"][te]
    ids = [str(D["id"][i]) for i in idx]
    out = []
    for t in (0.25, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.99, None):
        keep = [k for k, pid in enumerate(ids) if t is None or best.get(pid, 0.0) <= t]
        clf = pssmdt.PSSMDTClassifier(2.0 ** main_run["log2C"], 2.0 ** main_run["log2gamma"]).fit(X[keep], y[keep])
        m = rounded(pssmdt.metrics(yte, clf.decision_function(Xte)))
        out.append({"max_identity": t, "training": len(keep), "removed": len(ids) - len(keep), "pdb186": m})
        print("filter", t, len(ids) - len(keep), m, flush=True)
    return out


PAIRS = ("RR", "RP", "PR", "AR")


def raw_encoding(pssm, seq, e):
    """A comparator encoding on the raw scores: undo the logistic by passing logit-free values."""
    orig = pssmdt.core.logistic
    try:
        pssmdt.core.logistic = lambda x: np.asarray(x, dtype=np.float64)
        return pssmdt.encode(pssm, seq, e, 5)
    finally:
        pssmdt.core.logistic = orig


def ranks(W):
    """Rank (1 = largest) of the four pairs by the root sum of squares of positive weights."""
    aa = pssmdt.AMINO_ACIDS
    P = pssmdt.pair_weights(W, 5).ravel()
    order = list(np.argsort(-P, kind="stable"))
    return {p: order.index(aa.index(p[0]) * 20 + aa.index(p[1])) + 1 for p in PAIRS} | \
        {"top4": ["".join((aa[k // 20], aa[k % 20])) for k in order[:4]]}


def weight_variants(X, y, run_res):
    clf = pssmdt.PSSMDTClassifier(2.0 ** run_res["log2C"], 2.0 ** run_res["log2gamma"]).fit(X, y)
    A = clf.model_.dual_coef_.ravel()
    sv = clf.model_.support_
    sign = 1.0 if clf.model_.classes_[1] == 1 else -1.0
    out = {}
    for name, M in (("scaled", clf.Xs_), ("unscaled", X)):
        W = sign * (A @ M[sv])
        out[name] = ranks(W)
        out[name + "_other_sign"] = ranks(-W)
    out["class_mean_difference"] = ranks(X[y == 1].mean(0) - X[y == 0].mean(0))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pssms"); ap.add_argument("pssm_dir"); ap.add_argument("blastp"); ap.add_argument("out")
    ap.add_argument("--jobs", type=int, default=4)
    a = ap.parse_args()
    D = load(a.pssms)
    idx = subset(D, "benchmark")
    y = D["label"][idx]
    X = features(D, idx, "PSSM-DT")
    res = {"main": run(X, y, a.jobs)}
    print("main", res["main"], flush=True)
    D90 = load(Path(a.pssm_dir) / "pssm_uniref90_2014_01.npz")
    i90 = subset(D90, "benchmark")
    assert [str(D90["id"][i]) for i in i90] == [str(D["id"][i]) for i in idx]
    res["uniref90"] = run(features(D90, i90, "PSSM-DT"), D90["label"][i90], a.jobs)
    print("uniref90", res["uniref90"], flush=True)
    Xl = np.array([pssmdt.pssm_dt(pssmdt.logistic(D["pssm"][i]), 5) for i in idx])
    res["logistic"] = run(Xl, y, a.jobs)
    print("logistic", res["logistic"], flush=True)
    keep = [k for k, i in enumerate(idx) if str(D["id"][i]) not in DEFECTS]
    res["no_defects"] = run(X[keep], y[keep], a.jobs)
    res["no_defects"]["n"] = len(keep)
    print("no_defects", res["no_defects"], flush=True)
    res["split_seed_1"] = run(X, y, a.jobs, seed=1)
    print("split_seed_1", res["split_seed_1"], flush=True)
    res["unscaled"] = run(X, y, a.jobs, scale=False)
    print("unscaled", res["unscaled"], flush=True)
    res["fig2_weights"] = {"raw_pssm": weight_variants(X, y, res["main"]),
                           "logistic_pssm": weight_variants(Xl, y, res["logistic"])}
    print("fig2", res["fig2_weights"], flush=True)
    res["pdb186_filters"] = filters(D, X, y, idx, a.blastp, res["main"])
    res["pdb186_uniref90"] = filters(D90, features(D90, i90, "PSSM-DT"), D90["label"][i90], i90, a.blastp,
                                     res["uniref90"])
    res["pdb186_uniref90"] = [f for f in res["pdb186_uniref90"] if f["max_identity"] in (0.25, None)]
    enc = {}
    for e in ("AvePscore-20", "AvePscore-400", "Pscore-100", "ACC"):
        enc[e] = {"uniref90": run(features(D90, i90, e), D90["label"][i90], a.jobs)["jackknife"]}
        raw = np.array([raw_encoding(D["pssm"][i], str(D["sequence"][i]), e) for i in idx])
        enc[e]["raw_scores"] = run(raw, y, a.jobs)["jackknife"]
        print(e, enc[e], flush=True)
    res["encodings"] = enc
    Path(a.out).write_text(json.dumps(res, indent=1) + "\n")


if __name__ == "__main__":
    main()
