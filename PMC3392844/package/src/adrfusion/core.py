"""Adverse drug reaction (ADR) prediction from chemical, biological and phenotypic drug properties.

The method of Liu et al. (2012), rebuilt from the paper's text: one binary classifier per ADR, trained on
drugs described by binary features (PubChem substructures; DrugBank targets, transporters and enzymes and
their KEGG pathways; SIDER indications and the drug's other known ADRs), evaluated by cross-validation,
and summarized by micro-averaging: the scores of all (drug, ADR) pairs are merged into one global ROC.

Everything works on 0/1 matrices. A dataset is an :class:`ADRData`: drugs in rows, a label matrix ``Y``
(drugs x ADRs) and one matrix per feature block. Feature sets name blocks joined with ``+``; ``pheno``
is the indications plus the other ADRs, and "the other ADRs" of ADR j are the columns of ``Y`` except j
(except the whole group when ADRs are grouped).
"""

from __future__ import annotations

import math
import os
import warnings
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
from typing import Iterable, Sequence

import numpy as np

#: Blocks of the paper's Table 1, in the order of its data file.
BLOCKS = ("chem", "target", "transporter", "enzyme", "pathway", "indication")
#: Composite blocks: biological properties and phenotypic properties (``ade`` = the other known ADRs).
COMPOSITE = {"bio": ("target", "transporter", "enzyme", "pathway"), "pheno": ("indication", "ade")}
#: The six feature sets of the paper's Table 2 and Figs 2 and 3.
FEATURE_SETS = ("chem", "bio", "pheno", "chem+bio", "chem+pheno", "chem+bio+pheno")
#: The five algorithms of Table 3 and Fig. 4.
ALGORITHMS = ("lr", "nb", "knn", "rf", "svm")

#: Parameters the paper states (Results: Feature assessment and Method comparison).
SVM_GAMMA = 0.008
SVM_C = 2.0
LR_C = 10.0
LR_EPSILON = 1.0
KNN_K = 55
RF_TREES = 100


@dataclass
class ADRData:
    """Drugs (rows), their ADR labels and their binary feature blocks.

    ``Y`` is drugs x ADRs (1 = the drug has the ADR). ``blocks`` maps a block name (``chem``, ``target``,
    ``transporter``, ``enzyme``, ``pathway``, ``indication``, or any name of your own) to a drugs x
    features 0/1 matrix. ``folds`` (optional) is drugs x ADRs: the cross-validation fold of each drug
    for each ADR.
    """

    drugs: list[str]
    Y: np.ndarray
    blocks: dict[str, np.ndarray]
    adrs: list[str] = field(default_factory=list)
    names: list[str] = field(default_factory=list)
    folds: np.ndarray | None = None

    def __post_init__(self):
        self.Y = np.asarray(self.Y, dtype=np.uint8)
        n = self.Y.shape[0]
        if len(self.drugs) != n:
            raise ValueError(f"{len(self.drugs)} drug ids for {n} rows of Y")
        for k, v in list(self.blocks.items()):
            v = np.asarray(v, dtype=np.uint8)
            if v.ndim != 2 or v.shape[0] != n:
                raise ValueError(f"block {k!r} has shape {v.shape}; it needs {n} rows")
            if v.size and v.max() > 1:
                raise ValueError(f"block {k!r} is not 0/1")
            self.blocks[k] = v
        if self.Y.size and self.Y.max() > 1:
            raise ValueError("Y is not 0/1")
        if not self.adrs:
            self.adrs = [f"ADR{j}" for j in range(self.Y.shape[1])]
        if not self.names:
            self.names = list(self.drugs)
        if self.folds is not None:
            self.folds = np.asarray(self.folds, dtype=np.int16)
            if self.folds.shape != self.Y.shape:
                raise ValueError(f"folds has shape {self.folds.shape}; it needs {self.Y.shape}")

    @property
    def n_drugs(self) -> int:
        return self.Y.shape[0]

    @property
    def n_adrs(self) -> int:
        return self.Y.shape[1]

    def dimensions(self) -> dict[str, int]:
        """Number of features in each block (the paper's Table 1); ``ade`` is the other ADRs (m - 1)."""
        d = {k: v.shape[1] for k, v in self.blocks.items()}
        d["ade"] = self.n_adrs - 1
        return d


# ----------------------------------------------------------------------------------------------- input


def read_dataset(path: str | os.PathLike, adr_names: Sequence[str] | None = None) -> ADRData:
    """Read the pipe-delimited format of Liu et al.'s training file (``random_group_cv_data.indication``).

    One drug per line: ``drugBankID|name|CompoundID|ADR bits|chem bits|target bits|transporter bits|
    enzyme bits|pathway bits|indication bits|fold of each ADR (comma-separated)``. Bits are strings of
    0 and 1. The fold field may be empty (no folds).
    """
    drugs, names, cols, folds = [], [], [[] for _ in range(7)], []
    with open(path, encoding="utf-8") as f:
        for ln, line in enumerate(f, 1):
            line = line.rstrip("\r\n")
            if not line:
                continue
            p = line.split("|")
            if len(p) != 11:
                raise ValueError(f"{path}:{ln}: {len(p)} fields, expected 11")
            drugs.append(p[0])
            names.append(p[1])
            for i in range(7):
                s = p[3 + i]
                if s.strip("01"):
                    raise ValueError(f"{path}:{ln}: field {4 + i} is not a 0/1 string")
                cols[i].append(np.frombuffer(s.encode(), dtype=np.uint8) - 48)
            folds.append([int(x) for x in p[10].split(",")] if p[10] else None)
    mats = []
    for i, c in enumerate(cols):
        if len({len(r) for r in c}) != 1:
            raise ValueError(f"{path}: rows of field {4 + i} differ in length")
        mats.append(np.vstack(c).astype(np.uint8))
    Y = mats[0]
    F = None
    if all(f is not None for f in folds):
        F = np.array(folds, dtype=np.int16)
    blocks = dict(zip(BLOCKS, mats[1:]))
    return ADRData(drugs=drugs, Y=Y, blocks=blocks, adrs=list(adr_names) if adr_names else [], names=names, folds=F)


def write_dataset(data: ADRData, path: str | os.PathLike) -> None:
    """Write ``data`` in the pipe-delimited format that :func:`read_dataset` reads."""
    bits = lambda r: "".join("1" if v else "0" for v in r)  # noqa: E731
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for i, d in enumerate(data.drugs):
            parts = [d, data.names[i], ""] + [bits(data.Y[i])] + [bits(data.blocks[b][i]) for b in BLOCKS]
            parts.append(",".join(str(int(x)) for x in data.folds[i]) if data.folds is not None else "")
            f.write("|".join(parts) + "\n")


def stratified_folds(Y: np.ndarray, k: int = 5, seed: int = 0) -> np.ndarray:
    """A k-fold assignment for each ADR separately, stratified by its label (drugs x ADRs)."""
    rng = np.random.default_rng(seed)
    Y = np.asarray(Y)
    F = np.zeros(Y.shape, dtype=np.int16)
    for j in range(Y.shape[1]):
        for lab in (0, 1):
            idx = np.flatnonzero(Y[:, j] == lab)
            idx = idx[rng.permutation(len(idx))]
            F[idx, j] = (np.arange(len(idx)) + rng.integers(k)) % k
    return F


# ----------------------------------------------------------------------------------------- features


def expand(feature_set: str) -> tuple[str, ...]:
    """Base blocks of a feature set name, e.g. ``chem+bio`` -> chem, target, transporter, enzyme, pathway."""
    out: list[str] = []
    for part in feature_set.split("+"):
        part = part.strip()
        if not part:
            raise ValueError(f"empty block in feature set {feature_set!r}")
        for b in COMPOSITE.get(part, (part,)):
            if b not in out:
                out.append(b)
    return tuple(out)


def hamming(X: np.ndarray) -> np.ndarray:
    """Pairwise Hamming distances between the rows of a 0/1 matrix (= squared Euclidean distances)."""
    X = np.asarray(X, dtype=np.float64)
    s = X.sum(1)
    D = s[:, None] + s[None, :] - 2.0 * (X @ X.T)
    return np.rint(D)


def block_distances(data: ADRData) -> dict[str, np.ndarray]:
    """Hamming distance matrix of every block, and ``ade`` for the whole label matrix."""
    D = {k: hamming(v) for k, v in data.blocks.items()}
    D["ade"] = hamming(data.Y)
    return D


def _excluded(data: ADRData, j: int | Sequence[int]) -> list[int]:
    return [int(j)] if np.isscalar(j) else [int(x) for x in j]


def distance_for(data: ADRData, D: dict[str, np.ndarray], feature_set: str, j: int | Sequence[int]) -> np.ndarray:
    """Squared Euclidean distance between drugs on ``feature_set`` for predicting ADR j (or group j)."""
    blocks = expand(feature_set)
    out = np.zeros((data.n_drugs, data.n_drugs))
    for b in blocks:
        if b == "ade":
            ex = data.Y[:, _excluded(data, j)]
            out += D["ade"] - hamming(ex)
        else:
            out += D[b]
    return out


def features_for(data: ADRData, feature_set: str, j: int | Sequence[int]) -> np.ndarray:
    """The 0/1 feature matrix (drugs x features) of ``feature_set`` for predicting ADR j (or group j)."""
    parts = []
    for b in expand(feature_set):
        if b == "ade":
            parts.append(np.delete(data.Y, _excluded(data, j), axis=1))
        else:
            parts.append(data.blocks[b])
    return np.hstack(parts).astype(np.float64)


def group_label(data: ADRData, group: Sequence[int]) -> np.ndarray:
    """A grouped ADR: 1 when the drug has any ADR of the group."""
    return data.Y[:, list(group)].max(axis=1).astype(np.uint8)


# ------------------------------------------------------------------------------------------ learners


class _SVM:
    """scikit-learn's SVC (libsvm) on a precomputed kernel. scikit-learn 1.9 deprecates its probability
    option (LIBSVM's -b 1, Platt scaling with an internal 5-fold CV), which the paper's scores need;
    the warning is silenced here, and the package requires scikit-learn < 1.11."""

    def __init__(self, probability: bool, seed: int, C: float, class_weight=None):
        from sklearn.svm import SVC

        self.m = SVC(kernel="precomputed", C=C, probability=probability, random_state=seed, class_weight=class_weight)

    def fit(self, K, y):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", FutureWarning)
            self.m.fit(K, y)
        self.classes_ = self.m.classes_
        return self

    def decision_function(self, K):
        return self.m.decision_function(K)

    def predict_proba(self, K):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", FutureWarning)
            return self.m.predict_proba(K)


def _svm(probability: bool, seed: int, C: float, class_weight=None):
    return _SVM(probability, seed, C, class_weight)


def _knn_scores(Dte: np.ndarray, ytr: np.ndarray, k: int, prior: bool = False) -> np.ndarray:
    """Share of positive drugs among the k nearest training drugs, every drug tied with the k-th
    included (as WEKA IBk's neighbour search does). ``prior=True`` adds WEKA's correction of 1/n
    per class (n training drugs); the paper's Table 3 comes back without it."""
    n = len(ytr)
    k = min(k, n)
    out = np.empty(Dte.shape[0])
    corr = 1.0 / max(1, n) if prior else 0.0
    for a, row in enumerate(Dte):
        kth = np.partition(row, k - 1)[k - 1]
        nb = row <= kth
        out[a] = (ytr[nb].sum() + corr) / (nb.sum() + 2 * corr)
    return out


def _model(algorithm: str, seed: int, class_weight=None):
    if algorithm == "lr":
        from sklearn.linear_model import LogisticRegression

        # LIBLINEAR -s 0 (L2-regularized logistic regression), -c 10 -e 1, no bias term (LIBLINEAR's default).
        return LogisticRegression(solver="liblinear", C=LR_C, tol=LR_EPSILON, fit_intercept=False, class_weight=class_weight,
                                  random_state=seed)
    if algorithm == "nb":
        from sklearn.naive_bayes import BernoulliNB

        return BernoulliNB(alpha=1.0)
    if algorithm == "rf":
        from sklearn.ensemble import RandomForestClassifier

        # WEKA RandomForest: 100 trees, log2(M) + 1 features tried at each split, unpruned trees.
        return RandomForestClassifier(n_estimators=RF_TREES, max_features="log2_plus_1", random_state=seed, class_weight=class_weight)
    raise ValueError(f"unknown algorithm {algorithm!r}; use one of {ALGORITHMS}")


def paper_weights(y: np.ndarray) -> dict[int, float]:
    """The paper's class weights: weight = 1 - (class samples / total samples)."""
    y = np.asarray(y)
    return {c: 1.0 - float((y == c).mean()) for c in (0, 1)}


def _weights(class_weight, ytr):
    return paper_weights(ytr) if class_weight == "paper" else class_weight


def _fit_predict(algorithm, Xtr, ytr, Xte, seed, class_weight):
    m = _model(algorithm, seed, _weights(class_weight, ytr))
    if algorithm == "rf" and m.max_features == "log2_plus_1":
        m.max_features = int(math.log2(Xtr.shape[1])) + 1
    m.fit(Xtr, ytr)
    return m.predict_proba(Xte)[:, list(m.classes_).index(1)]


def _scores_one(data: ADRData, D, feature_set: str, algorithm: str, y: np.ndarray, fold: np.ndarray,
                exclude, seed: int, scores: str, class_weight) -> np.ndarray:
    """Cross-validated scores of every drug for one ADR (or group)."""
    n = data.n_drugs
    out = np.zeros(n)
    kernel_like = algorithm in ("svm", "knn")
    if kernel_like:
        Dist = distance_for(data, D, feature_set, exclude)
        K = np.exp(-SVM_GAMMA * Dist) if algorithm == "svm" else None
    else:
        X = features_for(data, feature_set, exclude)
    for k in np.unique(fold):
        te = np.flatnonzero(fold == k)
        tr = np.flatnonzero(fold != k)
        ytr = y[tr]
        if algorithm == "knn":
            out[te] = _knn_scores(Dist[np.ix_(te, tr)], ytr, KNN_K)
            continue
        if ytr.min() == ytr.max():
            # One class in the training drugs: no classifier; every test drug gets that class.
            out[te] = float(ytr[0]) if scores == "probability" else (1.0 if ytr[0] else -1.0)
            continue
        if algorithm == "svm":
            m = _svm(scores == "probability", seed, SVM_C, _weights(class_weight, ytr)).fit(K[np.ix_(tr, tr)], ytr)
            Kte = K[np.ix_(te, tr)]
            if scores == "probability":
                out[te] = m.predict_proba(Kte)[:, list(m.classes_).index(1)]
            else:
                out[te] = m.decision_function(Kte)
        else:
            out[te] = _fit_predict(algorithm, X[tr], ytr, X[te], seed, class_weight)
    return out


_W: dict = {}


def _init(data, D):
    _W["data"], _W["D"] = data, D


def _work(args):
    j, feature_set, algorithm, seed, scores, class_weight = args
    data, D = _W["data"], _W["D"]
    y = data.Y[:, j].astype(np.int8)
    return _scores_one(data, D, feature_set, algorithm, y, data.folds[:, j], j, seed, scores, class_weight)


def cross_validated_scores(data: ADRData, feature_set: str = "chem+bio+pheno", algorithm: str = "svm",
                           adrs: Iterable[int] | None = None, seed: int = 0, scores: str = "probability",
                           n_jobs: int = 1, class_weight: str | None = None,
                           distances: dict[str, np.ndarray] | None = None) -> np.ndarray:
    """Cross-validated score of every drug for each ADR: a drugs x len(adrs) matrix.

    One classifier per ADR and fold, on the folds of ``data.folds`` (make some with
    :func:`stratified_folds`). ``algorithm`` is ``svm`` (RBF kernel, g = 0.008, C = 2), ``lr``
    (L2-regularized logistic regression, C = 10, epsilon = 1), ``nb`` (Bernoulli naive Bayes), ``knn``
    (k = 55) or ``rf`` (100 trees). SVM scores are probability estimates (Platt scaling, as LIBSVM's
    ``-b 1``) unless ``scores='decision'``. ``class_weight='paper'`` weights each class by
    1 - its share of the training drugs, as the paper's further analysis does for RF and SVM.
    """
    if data.folds is None:
        raise ValueError("data has no folds; set data.folds = stratified_folds(data.Y)")
    if algorithm not in ALGORITHMS:
        raise ValueError(f"unknown algorithm {algorithm!r}; use one of {ALGORITHMS}")
    if scores not in ("probability", "decision"):
        raise ValueError("scores must be 'probability' or 'decision'")
    for b in expand(feature_set):
        if b != "ade" and b not in data.blocks:
            raise ValueError(f"feature set {feature_set!r} needs block {b!r}, which the data do not have")
    js = list(range(data.n_adrs)) if adrs is None else [int(j) for j in adrs]
    D = distances if distances is not None else (block_distances(data) if algorithm in ("svm", "knn") else {})
    tasks = [(j, feature_set, algorithm, seed, scores, class_weight) for j in js]
    if n_jobs == 1 or len(js) < 2:
        _init(data, D)
        cols = [_work(t) for t in tasks]
    else:
        if n_jobs in (-1, 0):
            n_jobs = os.cpu_count() or 1
        with ProcessPoolExecutor(n_jobs, initializer=_init, initargs=(data, D)) as ex:
            cols = list(ex.map(_work, tasks, chunksize=max(1, len(tasks) // (8 * n_jobs))))
    return np.column_stack(cols) if cols else np.zeros((data.n_drugs, 0))


def predict_held_out(data: ADRData, drug: int, adrs: Sequence[int] | Sequence[Sequence[int]],
                     feature_set: str = "chem+bio+pheno", seed: int = 0) -> list[dict]:
    """The paper's clinical validation: for each ADR (or group of ADRs, given as a list), train an SVM on
    every drug but ``drug`` and predict ``drug``. Returns the SVM's decision value, probability and
    call (``Yes`` when the decision value is positive, LIBSVM's predicted label) for each."""
    D = block_distances(data)
    others = np.array([i for i in range(data.n_drugs) if i != drug])
    out = []
    for a in adrs:
        group = [int(x) for x in a] if isinstance(a, (list, tuple, np.ndarray)) else [int(a)]
        y = group_label(data, group).astype(np.int8)
        K = np.exp(-SVM_GAMMA * distance_for(data, D, feature_set, group))
        m = _svm(True, seed, SVM_C).fit(K[np.ix_(others, others)], y[others])
        kt = K[np.ix_([drug], others)]
        dec = float(m.decision_function(kt)[0])
        prob = float(m.predict_proba(kt)[0, list(m.classes_).index(1)])
        out.append({"adrs": group, "known": int(y[drug]), "decision": dec, "probability": prob,
                    "call": "Yes" if dec > 0 else "No"})
    return out


# ----------------------------------------------------------------------------------------- evaluation


def roc(y: np.ndarray, s: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """ROC curve of scores ``s`` for labels ``y`` (any shape, flattened): FPR, TPR and the thresholds,
    one point per distinct score, from (0, 0) to (1, 1)."""
    y = np.asarray(y).ravel().astype(np.int64)
    s = np.asarray(s, dtype=np.float64).ravel()
    order = np.argsort(-s, kind="mergesort")
    s, y = s[order], y[order]
    last = np.r_[np.flatnonzero(np.diff(s)), len(s) - 1]
    tp = np.cumsum(y)[last]
    fp = (last + 1) - tp
    P, N = y.sum(), len(y) - y.sum()
    if P == 0 or N == 0:
        raise ValueError("ROC needs both positive and negative labels")
    tpr = np.r_[0.0, tp / P]
    fpr = np.r_[0.0, fp / N]
    return fpr, tpr, np.r_[np.inf, s[last]]


def auc(y: np.ndarray, s: np.ndarray) -> float:
    """Area under the ROC curve (trapezoids; ties count one half)."""
    fpr, tpr, _ = roc(y, s)
    return float(np.trapezoid(tpr, fpr))


@dataclass
class Metrics:
    """Micro-averaged performance: the paper's AUC, ACC, precision and recall."""

    auc: float
    acc: float
    precision: float
    recall: float
    acc_threshold: float
    f1_threshold: float
    positives: int
    pairs: int

    def as_dict(self) -> dict:
        return dict(self.__dict__)


def micro_metrics(Y: np.ndarray, S: np.ndarray) -> Metrics:
    """Micro-averaged metrics over every (drug, ADR) pair of ``Y`` and ``S`` merged into one global ROC.

    ACC is read at the point of the global ROC with the highest accuracy, precision and recall at the
    point with the highest F1 (the paper's "best cut-off points ... the best tradeoff between false
    positives and false negatives"; these are the two rules that give its Table 2)."""
    y = np.asarray(Y).ravel()
    fpr, tpr, th = roc(y, S)
    P = int(y.sum())
    N = y.size - P
    tp, fp = tpr * P, fpr * N
    acc = (tp + N - fp) / y.size
    f1 = 2 * tp / (tp + fp + P)
    ia, ib = int(np.argmax(acc)), int(np.argmax(f1))
    prec = tp[ib] / (tp[ib] + fp[ib]) if tp[ib] + fp[ib] > 0 else 1.0
    return Metrics(auc=float(np.trapezoid(tpr, fpr)), acc=float(acc[ia]), precision=float(prec), recall=float(tpr[ib]),
                   acc_threshold=float(th[ia]), f1_threshold=float(th[ib]), positives=P, pairs=int(y.size))


def per_adr_auc(Y: np.ndarray, S: np.ndarray) -> np.ndarray:
    """AUC of each ADR (column) over its drugs; NaN for an ADR with no positive or no negative drug."""
    out = np.full(Y.shape[1], np.nan)
    for j in range(Y.shape[1]):
        if 0 < Y[:, j].sum() < Y.shape[0]:
            out[j] = auc(Y[:, j], S[:, j])
    return out


def ks_larger(a: np.ndarray, b: np.ndarray, comparisons: int = 1) -> float:
    """One-sided two-sample Kolmogorov-Smirnov test that the values ``b`` are stochastically larger than
    ``a`` (per-ADR AUCs of two feature sets), Bonferroni-corrected for ``comparisons`` tests."""
    from scipy.stats import ks_2samp

    a = np.asarray(a)[~np.isnan(a)]
    b = np.asarray(b)[~np.isnan(b)]
    # alternative='greater': the CDF of the first sample lies above that of the second, i.e. b is larger.
    p = ks_2samp(a, b, alternative="greater").pvalue
    return float(min(1.0, p * comparisons))


def true_positives(Y: np.ndarray, S: np.ndarray, threshold: float) -> np.ndarray:
    """Boolean matrix of the (drug, ADR) pairs predicted positive at ``threshold`` (score >= threshold)
    that are positive."""
    return (np.asarray(S) >= threshold) & (np.asarray(Y) == 1)


def informative_features(data: ADRData, alpha: float = 0.05, correction: bool = False) -> dict[str, dict]:
    """The paper's Table S1: a chi-square test of every feature against every ADR (for ADR j the other
    ADRs are the features of block ``ade``); a pair is informative when p < alpha. Returns, per block,
    the number of informative pairs and their share of all informative pairs."""
    from scipy.stats import chi2

    Y = data.Y.astype(np.float64)
    n = data.n_drugs
    a1 = Y.sum(0)  # drugs with the ADR, per ADR

    def counts(X):
        X = np.asarray(X, dtype=np.float64)
        f1 = X.sum(0)
        both = X.T @ Y  # features x ADRs: drugs with the feature and the ADR
        return f1, both

    def informative(f1, both):
        # 2x2 table per (feature, ADR): [[both, f1-both], [a1-both, n-f1-a1+both]]
        a = both
        b = f1[:, None] - both
        c = a1[None, :] - both
        d = n - f1[:, None] - a1[None, :] + both
        num = (np.abs(a * d - b * c) - (n / 2 if correction else 0)).clip(min=0) ** 2 * n
        den = (a + b) * (c + d) * (a + c) * (b + d)
        with np.errstate(divide="ignore", invalid="ignore"):
            stat = np.where(den > 0, num / den, np.nan)
        p = chi2.sf(stat, 1)
        return np.nan_to_num(p, nan=1.0) < alpha

    res: dict[str, dict] = {}
    for b, X in data.blocks.items():
        f1, both = counts(X)
        res[b] = {"features": X.shape[1], "informative": int(informative(f1, both).sum())}
    f1, both = counts(data.Y)
    inf = informative(f1, both)
    np.fill_diagonal(inf, False)  # an ADR is not a feature of itself
    res["ade"] = {"features": data.n_adrs - 1, "informative": int(inf.sum())}
    total = sum(v["informative"] for v in res.values())
    for v in res.values():
        v["share"] = v["informative"] / total if total else math.nan
    return res


def score_table(data: ADRData, S: np.ndarray, adrs: Sequence[int] | None = None) -> list[dict]:
    """Rows (drug, ADR, label, score) of a score matrix, for writing to CSV."""
    js = list(range(data.n_adrs)) if adrs is None else list(adrs)
    return [{"drug": data.drugs[i], "adr": data.adrs[j], "label": int(data.Y[i, j]), "score": float(S[i, c])}
            for c, j in enumerate(js) for i in range(data.n_drugs)]

