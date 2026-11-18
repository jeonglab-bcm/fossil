"""Make the package's example data: a synthetic drug file and its expected cross-validated SVM scores.

    python scripts/make_example_data.py           (from the package folder; needs numpy and libsvm-official)

Writes src/adrfusion/data/example_drugs.txt (the pipe-delimited format of Liu et al.'s training file) and
src/adrfusion/data/example_expected.csv (drug, adr, label, decision).

The drugs are synthetic: 120 drugs in four groups; each group has its own chance (0.7 or 0.05) of carrying each
chemical, biological and indication feature and each of 30 ADRs, so drugs of a group look alike and
share ADRs. Every ADR has at least 8 drugs, and each ADR's 5 folds are stratified, so every training set
has both classes. Seed 20120630.

The expected output is not computed by adrfusion. It is the decision value of the official LIBSVM
(libsvm-official, the C library of Chang and Lin) trained on the raw 0/1 features with the paper's
settings, -s 0 -t 2 -g 0.008 -c 2, one model per ADR and fold, the other ADRs as features. adrfusion
builds the same kernel from per-block Hamming distances and trains scikit-learn's copy of libsvm; the
two agree within the solvers' stopping tolerance (tested at 1e-3).
"""
from pathlib import Path

import numpy as np
from libsvm.svmutil import svm_parameter, svm_predict, svm_problem, svm_train

SEED = 20120630
N, M = 120, 30
DIMS = {"chem": 40, "target": 20, "transporter": 5, "enzyme": 6, "pathway": 10, "indication": 25}
HERE = Path(__file__).resolve().parent.parent / "src" / "adrfusion" / "data"


def make():
    rng = np.random.default_rng(SEED)
    group = np.repeat(np.arange(4), N // 4)
    rng.shuffle(group)
    blocks = {}
    for k, m in DIMS.items():
        p = np.where(rng.random((4, m)) < 0.3, 0.7, 0.05)
        blocks[k] = (rng.random((N, m)) < p[group]).astype(np.uint8)
    pY = np.where(rng.random((4, M)) < 0.3, 0.6, 0.04)
    Y = (rng.random((N, M)) < pY[group]).astype(np.uint8)
    for j in range(M):  # at least 8 drugs per ADR
        while Y[:, j].sum() < 8:
            Y[rng.integers(N), j] = 1
    folds = np.zeros((N, M), dtype=int)
    for j in range(M):
        for lab in (0, 1):
            idx = np.flatnonzero(Y[:, j] == lab)
            idx = idx[rng.permutation(len(idx))]
            folds[idx, j] = np.arange(len(idx)) % 5
    return Y, blocks, folds


def libsvm_scores(Y, blocks, folds):
    base = np.hstack([blocks[k] for k in DIMS])
    out = np.zeros(Y.shape)
    for j in range(M):
        X = np.hstack([base, np.delete(Y, j, axis=1)])
        rows = [{int(i) + 1: 1.0 for i in np.flatnonzero(r)} for r in X]
        y = Y[:, j].astype(int)
        for k in range(5):
            te = np.flatnonzero(folds[:, j] == k)
            tr = np.flatnonzero(folds[:, j] != k)
            m = svm_train(svm_problem(y[tr].tolist(), [rows[i] for i in tr]), svm_parameter("-s 0 -t 2 -g 0.008 -c 2 -q"))
            _, _, dv = svm_predict(y[te].tolist(), [rows[i] for i in te], m, "-q")
            sign = 1.0 if m.get_labels()[0] == 1 else -1.0  # LIBSVM's decision value favours its first label
            out[te, j] = [sign * v[0] for v in dv]
    return out


def main():
    Y, blocks, folds = make()
    bits = lambda r: "".join(str(int(v)) for v in r)  # noqa: E731
    drugs = [f"D{i + 1:03d}" for i in range(N)]
    with open(HERE / "example_drugs.txt", "w", encoding="utf-8", newline="\n") as f:
        for i in range(N):
            parts = [drugs[i], f"drug{i + 1}", ""] + [bits(Y[i])] + [bits(blocks[k][i]) for k in DIMS]
            parts.append(",".join(str(x) for x in folds[i]))
            f.write("|".join(parts) + "\n")
    S = libsvm_scores(Y, blocks, folds)
    with open(HERE / "example_expected.csv", "w", encoding="utf-8", newline="\n") as f:
        f.write("drug,adr,label,decision\n")
        for j in range(M):
            for i in range(N):
                f.write(f"{drugs[i]},ADR{j},{int(Y[i, j])},{S[i, j]:.10f}\n")
    print(f"wrote {N} drugs x {M} ADRs; {int(Y.sum())} positive pairs")


if __name__ == "__main__":
    main()
