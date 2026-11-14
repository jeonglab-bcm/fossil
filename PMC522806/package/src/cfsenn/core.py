"""Combinational feature selection and ensemble neural networks (Liu, Cui, Jiang and Ma 2004).

Implemented from the paper's text; the authors' Matlab code was never released. What the paper
states is used as stated. Every setting it does not state is a keyword argument whose default is
our choice, listed in ``DEFAULTS`` and in the package README.

Stated in the paper:

- 100 bootstrap resamples (bagging). On each resample, features are selected from the resample:
  the top 30 genes by the Wilcoxon rank-sum test, the top 15 principal components of all genes,
  and the top 30 genes by t-test after Jaeger's "masked out clustering" of the genes into 50
  clusters.
- One feed-forward network per feature set, with one hidden layer of 10 units and one output unit
  for two classes (one per class for more). The three networks' confidences are averaged.
- The 100 answers are combined by soft voting: each answer's confidence is its vote.

Our choices (not stated): the network's activation (tanh hidden units, logistic or softmax output),
its training (cross-entropy with weight decay, L-BFGS, 200 iterations, seeded uniform start), input
scaling (z-scores from the resample), the masked-out clustering (k-means with correlation distance
on the 500 genes with the largest t statistic; the best gene of a cluster masks the rest of that
cluster), the multi-class tests (Kruskal-Wallis and one-way F in place of rank-sum and t), and the
fill for missing values (the gene's mean over the training samples).
"""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from scipy import optimize
from scipy.stats import rankdata

DEFAULTS = {
    "n_bags": 100,
    "n_rank": 30,
    "n_pc": 15,
    "n_clusters": 50,
    "n_cluster_genes": 30,
    "n_prefilter": 500,
    "hidden": 10,
    "alpha": 1e-2,
    "maxiter": 200,
    "feature_sets": ("ranksum", "pca", "cluster"),
    "resample": "bagging",
    "vote": "soft",
    "select_per_bag": True,
    "seed": 0,
}

FEATURE_SETS = ("ranksum", "pca", "cluster", "random", "combined")


# ---------------------------------------------------------------------------------------------
# Reading data


def read_dbc(path):
    """Read an Elvira ``.dbc`` data base (the Kent Ridge "transformed" files on the UGR mirror).

    Returns ``(X, y, genes, classes)``: X is samples x genes (float, NaN for ``?``), y holds class
    indices into ``classes`` (in the file's declared order), genes are the attribute names.
    """
    names, states, rows = [], {}, []
    cur = None
    in_cases = False
    with open(path, encoding="latin-1") as f:
        for line in f:
            if not in_cases:
                m = re.match(r"node (\S+)\(", line)
                if m:
                    cur = m.group(1)
                    names.append(cur)
                    continue
                m = re.match(r"states = \((.*)\);", line)
                if m and cur is not None:
                    states[cur] = m.group(1).split()
                    continue
                if line.startswith("cases = ("):
                    in_cases = True
            else:
                s = line.strip()
                if s.startswith("["):
                    rows.append([t.strip() for t in s.strip("[] ,").split(",")])
    if not rows:
        raise ValueError(f"no cases in {path}")
    width = len(rows[0])
    if any(len(r) != width for r in rows):
        raise ValueError(f"rows of different length in {path}")
    class_name = names[0] if names else "SampleType"
    classes = states.get(class_name) or sorted({r[0] for r in rows})
    y = np.array([classes.index(r[0]) for r in rows])
    X = np.array([[np.nan if v == "?" else float(v) for v in r[1:]] for r in rows])
    genes = names[1:width] if len(names) >= width else [f"attribute{i}" for i in range(1, width)]
    return X, y, genes, list(classes)


def read_table(path):
    """Read a samples x genes table (CSV or TSV): first column ``class``, the rest genes.

    Returns ``(X, y, genes, classes)`` as ``read_dbc``; classes are sorted names.
    """
    path = Path(path)
    delim = "\t" if path.suffix in (".tsv", ".txt") else ","
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.reader(f, delimiter=delim)
        header = next(r)
        rows = [row for row in r if row]
    if header[0] != "class":
        raise ValueError("the first column must be named 'class'")
    labels = [row[0] for row in rows]
    classes = sorted(set(labels))
    y = np.array([classes.index(v) for v in labels])
    X = np.array([[np.nan if v in ("", "?", "NA", "nan") else float(v) for v in row[1:]] for row in rows])
    return X, y, header[1:], classes


# ---------------------------------------------------------------------------------------------
# Feature scores


def ranksum_scores(X, y):
    """Wilcoxon rank-sum |z| per gene for two classes; Kruskal-Wallis H for more."""
    R = rankdata(X, axis=0)
    n = X.shape[0]
    k = int(y.max()) + 1
    if k == 2:
        n1 = int((y == 0).sum())
        n2 = n - n1
        w = R[y == 0].sum(axis=0)
        mu = n1 * (n + 1) / 2.0
        sd = np.sqrt(n1 * n2 * (n + 1) / 12.0)
        return np.abs((w - mu) / sd)
    h = np.zeros(X.shape[1])
    for c in range(k):
        m = y == c
        nc = m.sum()
        if nc:
            h += R[m].sum(axis=0) ** 2 / nc
    return 12.0 / (n * (n + 1)) * h - 3 * (n + 1)


def t_scores(X, y):
    """Welch |t| per gene for two classes; one-way ANOVA F for more."""
    k = int(y.max()) + 1
    if k == 2:
        a, b = X[y == 0], X[y == 1]
        va = a.var(axis=0, ddof=1) / len(a)
        vb = b.var(axis=0, ddof=1) / len(b)
        d = np.sqrt(va + vb)
        d[d == 0] = np.inf
        return np.abs(a.mean(axis=0) - b.mean(axis=0)) / d
    grand = X.mean(axis=0)
    ssb = np.zeros(X.shape[1])
    ssw = np.zeros(X.shape[1])
    for c in range(k):
        g = X[y == c]
        if len(g):
            ssb += len(g) * (g.mean(axis=0) - grand) ** 2
            ssw += ((g - g.mean(axis=0)) ** 2).sum(axis=0)
    dfb, dfw = k - 1, X.shape[0] - k
    ssw[ssw == 0] = np.inf
    return (ssb / dfb) / (ssw / max(dfw, 1))


def top(scores, n):
    """Indices of the n largest scores, ties broken by the lower index."""
    order = np.lexsort((np.arange(len(scores)), -np.nan_to_num(scores, nan=-np.inf)))
    return order[:n]


def kmeans(Z, k, rng, iters=50):
    """k-means (k-means++ start) on the rows of Z. Returns labels."""
    n = Z.shape[0]
    k = min(k, n)
    centers = np.empty((k, Z.shape[1]))
    centers[0] = Z[rng.integers(n)]
    d2 = ((Z - centers[0]) ** 2).sum(axis=1)
    for j in range(1, k):
        p = d2 / d2.sum() if d2.sum() > 0 else np.full(n, 1.0 / n)
        centers[j] = Z[rng.choice(n, p=p)]
        d2 = np.minimum(d2, ((Z - centers[j]) ** 2).sum(axis=1))
    labels = np.full(n, -1)
    zz = (Z**2).sum(axis=1)[:, None]
    for _ in range(iters):
        dist = zz - 2 * Z @ centers.T + (centers**2).sum(axis=1)[None, :]
        new = dist.argmin(axis=1)
        if np.array_equal(new, labels):
            break
        labels = new
        for j in range(k):
            m = labels == j
            if m.any():
                centers[j] = Z[m].mean(axis=0)
    return labels


def masked_cluster_genes(X, y, n_genes=30, n_clusters=50, n_prefilter=500, rng=None):
    """Jaeger-style "masked out clustering": cluster genes, then take the best gene per cluster.

    The ``n_prefilter`` genes with the largest t statistic are clustered into ``n_clusters`` by
    k-means on their standardized profiles (correlation distance). Genes are then taken in order of
    t; each gene taken masks out the rest of its cluster. Returns the indices of ``n_genes`` genes.
    """
    rng = np.random.default_rng(0) if rng is None else rng
    t = t_scores(X, y)
    cand = top(t, min(n_prefilter, X.shape[1]))
    G = X[:, cand].T
    G = G - G.mean(axis=1, keepdims=True)
    s = np.linalg.norm(G, axis=1, keepdims=True)
    s[s == 0] = 1.0
    labels = kmeans(G / s, n_clusters, rng)
    chosen, used = [], set()
    for g, lab in zip(cand, labels):  # cand is already in order of t
        if lab in used:
            continue
        used.add(lab)
        chosen.append(g)
        if len(chosen) == n_genes:
            break
    return np.array(chosen, dtype=int)


# ---------------------------------------------------------------------------------------------
# Feature maps: fitted on a training resample, applied to any samples


@dataclass
class FeatureMap:
    kind: str
    genes: np.ndarray | None = None
    mean: np.ndarray | None = None
    components: np.ndarray | None = None
    mu: np.ndarray | None = None
    sd: np.ndarray | None = None

    def raw(self, X):
        if self.kind == "pca":
            return (X - self.mean) @ self.components.T
        return X[:, self.genes]

    def __call__(self, X):
        return (self.raw(X) - self.mu) / self.sd


def fit_feature_map(kind, X, y, rng, p):
    if kind == "ranksum":
        fm = FeatureMap(kind, genes=top(ranksum_scores(X, y), p["n_rank"]))
    elif kind == "cluster":
        fm = FeatureMap(
            kind,
            genes=masked_cluster_genes(X, y, p["n_cluster_genes"], p["n_clusters"], p["n_prefilter"], rng),
        )
    elif kind == "pca":
        mean = X.mean(axis=0)
        Xc = X - mean
        # Eigenvectors of the small n x n Gram matrix give the gene-space components.
        evals, evecs = np.linalg.eigh(Xc @ Xc.T)
        order = np.argsort(evals)[::-1]
        m = min(p["n_pc"], int((evals > evals.max() * 1e-12).sum()))
        V = Xc.T @ evecs[:, order[:m]]
        V /= np.linalg.norm(V, axis=0, keepdims=True)
        # Fix the sign so that the largest-magnitude loading is positive.
        sign = np.sign(V[np.abs(V).argmax(axis=0), np.arange(m)])
        fm = FeatureMap(kind, mean=mean, components=(V * sign).T)
    elif kind == "random":
        n = {"ranksum": p["n_rank"], "pca": p["n_pc"], "cluster": p["n_cluster_genes"]}[p["_slot"]]
        fm = FeatureMap(kind, genes=np.sort(rng.choice(X.shape[1], size=n, replace=False)))
    elif kind == "combined":
        parts = [fit_feature_map(k, X, y, rng, p) for k in ("ranksum", "pca", "cluster")]
        return CombinedMap(parts)
    else:
        raise ValueError(f"unknown feature set {kind!r}")
    F = fm.raw(X)
    fm.mu = F.mean(axis=0)
    sd = F.std(axis=0)
    sd[sd == 0] = 1.0
    fm.sd = sd
    return fm


@dataclass
class CombinedMap:
    parts: list = field(default_factory=list)
    kind: str = "combined"

    def __call__(self, X):
        return np.hstack([p(X) for p in self.parts])


# ---------------------------------------------------------------------------------------------
# One network: inputs -> 10 tanh units -> logistic (2 classes) or softmax (more)


class Net:
    def __init__(self, n_in, n_classes, hidden=10, alpha=1e-2, maxiter=200, rng=None):
        self.n_in, self.k, self.h = n_in, n_classes, hidden
        self.n_out = 1 if n_classes == 2 else n_classes
        self.alpha, self.maxiter = alpha, maxiter
        rng = np.random.default_rng(0) if rng is None else rng
        a1 = 1.0 / np.sqrt(n_in)
        a2 = 1.0 / np.sqrt(hidden)
        self.theta = np.concatenate(
            [
                rng.uniform(-a1, a1, n_in * hidden),
                np.zeros(hidden),
                rng.uniform(-a2, a2, hidden * self.n_out),
                np.zeros(self.n_out),
            ]
        )

    def _unpack(self, th):
        i = 0
        W1 = th[i : i + self.n_in * self.h].reshape(self.n_in, self.h)
        i += self.n_in * self.h
        b1 = th[i : i + self.h]
        i += self.h
        W2 = th[i : i + self.h * self.n_out].reshape(self.h, self.n_out)
        i += self.h * self.n_out
        b2 = th[i : i + self.n_out]
        return W1, b1, W2, b2

    def _out(self, A):
        if self.n_out == 1:
            return 1.0 / (1.0 + np.exp(-np.clip(A, -500, 500)))
        A = A - A.max(axis=1, keepdims=True)
        E = np.exp(A)
        return E / E.sum(axis=1, keepdims=True)

    def _loss(self, th, Z, T, w):
        W1, b1, W2, b2 = self._unpack(th)
        H = np.tanh(Z @ W1 + b1)
        P = self._out(H @ W2 + b2)
        eps = 1e-12
        if self.n_out == 1:
            ce = -(T * np.log(P + eps) + (1 - T) * np.log(1 - P + eps)).sum(axis=1)
        else:
            ce = -(T * np.log(P + eps)).sum(axis=1)
        loss = (w * ce).sum() + 0.5 * self.alpha * ((W1**2).sum() + (W2**2).sum())
        D2 = (P - T) * w[:, None]
        gW2 = H.T @ D2 + self.alpha * W2
        gb2 = D2.sum(axis=0)
        D1 = (D2 @ W2.T) * (1 - H**2)
        gW1 = Z.T @ D1 + self.alpha * W1
        gb1 = D1.sum(axis=0)
        return loss, np.concatenate([gW1.ravel(), gb1, gW2.ravel(), gb2])

    def fit(self, Z, y, sample_weight=None):
        if self.n_out == 1:
            T = (y == 1).astype(float)[:, None]
        else:
            T = np.eye(self.k)[y]
        w = np.full(len(y), 1.0 / len(y)) if sample_weight is None else sample_weight / sample_weight.sum()
        res = optimize.minimize(
            self._loss, self.theta, args=(Z, T, w), jac=True, method="L-BFGS-B",
            options={"maxiter": self.maxiter},
        )
        self.theta = res.x
        return self

    def predict_proba(self, Z):
        W1, b1, W2, b2 = self._unpack(self.theta)
        P = self._out(np.tanh(Z @ W1 + b1) @ W2 + b2)
        if self.n_out == 1:
            return np.hstack([1 - P, P])
        return P


# ---------------------------------------------------------------------------------------------
# The ensemble


def _params(**kw):
    p = dict(DEFAULTS)
    unknown = set(kw) - set(p)
    if unknown:
        raise TypeError(f"unknown settings: {sorted(unknown)}")
    p.update(kw)
    p["feature_sets"] = tuple(p["feature_sets"])
    if p["resample"] not in ("bagging", "adaboost", "none"):
        raise ValueError("resample must be 'bagging', 'adaboost' or 'none'")
    if p["vote"] not in ("soft", "hard"):
        raise ValueError("vote must be 'soft' or 'hard'")
    for fs in p["feature_sets"]:
        if fs not in FEATURE_SETS:
            raise ValueError(f"unknown feature set {fs!r}")
    return p


class Member:
    """One ensemble member: a feature map and a network per feature set."""

    def __init__(self, maps, nets):
        self.maps, self.nets = maps, nets

    def predict_proba(self, X):
        return np.mean([n.predict_proba(m(X)) for m, n in zip(self.maps, self.nets)], axis=0)


def _fit_maps(X, y, p, rng):
    slots = ("ranksum", "pca", "cluster")
    return [fit_feature_map(fs, X, y, rng, dict(p, _slot=slots[i % 3])) for i, fs in enumerate(p["feature_sets"])]


def _fit_member(X, y, k, p, rng, sample_weight=None, maps=None):
    """Networks on a resample. ``maps``: feature maps fitted beforehand (else fitted on X, y)."""
    if maps is None:
        maps = _fit_maps(X, y, p, rng)
    nets = []
    for fm in maps:
        Z = fm(X)
        nets.append(Net(Z.shape[1], k, p["hidden"], p["alpha"], p["maxiter"], rng).fit(Z, y, sample_weight))
    return Member(maps, nets)


def _bootstrap(y, rng, p=None):
    """A bootstrap resample with at least two distinct samples of every class."""
    n = len(y)
    k = int(y.max()) + 1
    for _ in range(1000):
        idx = rng.choice(n, size=n, replace=True, p=p)
        u = np.unique(idx)
        if all((y[u] == c).sum() >= 2 for c in range(k)):
            return idx
    raise ValueError("cannot draw a resample with two samples of every class")


class Ensemble:
    """The paper's classifier. ``fit(X, y)`` then ``predict_proba(X)`` or ``predict(X)``.

    X is samples x genes; y holds class indices 0..K-1. Missing values (NaN) are filled with the
    gene's mean over the training samples. Settings: see ``DEFAULTS``.
    """

    def __init__(self, **settings):
        self.p = _params(**settings)

    def fit(self, X, y):
        X = np.asarray(X, dtype=float)
        y = np.asarray(y, dtype=int)
        if X.ndim != 2 or len(X) != len(y):
            raise ValueError("X must be samples x genes with one label per sample")
        self.k = int(y.max()) + 1
        if self.k < 2 or any((y == c).sum() < 2 for c in range(self.k)):
            raise ValueError("need at least two samples of each of at least two classes")
        self.fill = None
        if np.isnan(X).any():
            seen = (~np.isnan(X)).sum(axis=0)
            total = np.where(np.isnan(X), 0.0, X).sum(axis=0)
            self.fill = np.where(seen > 0, total / np.maximum(seen, 1), 0.0)
        X = self._filled(X)
        p = self.p
        seeds = np.random.SeedSequence(p["seed"]).spawn(max(p["n_bags"], 1))
        self.members, self.weights = [], []
        n = len(y)
        # select_per_bag=False: the feature sets are chosen once, on all training samples.
        shared = None if p["select_per_bag"] else _fit_maps(X, y, p, np.random.default_rng(seeds[0]))
        if p["resample"] == "none":
            self.members.append(_fit_member(X, y, self.k, p, np.random.default_rng(seeds[0]), maps=shared))
            self.weights.append(1.0)
        elif p["resample"] == "bagging":
            for s in seeds:
                rng = np.random.default_rng(s)
                idx = _bootstrap(y, rng)
                self.members.append(_fit_member(X[idx], y[idx], self.k, p, rng, maps=shared))
                self.weights.append(1.0)
        else:  # AdaBoost.M1 (SAMME for more classes) by weighted resampling
            w = np.full(n, 1.0 / n)
            for s in seeds:
                rng = np.random.default_rng(s)
                idx = _bootstrap(y, rng, p=w)
                m = _fit_member(X[idx], y[idx], self.k, p, rng, maps=shared)
                wrong = m.predict_proba(X).argmax(axis=1) != y
                err = float(w[wrong].sum())
                if err >= 1 - 1.0 / self.k:
                    continue
                err = max(err, 1e-10)
                a = np.log((1 - err) / err) + np.log(self.k - 1)
                self.members.append(m)
                self.weights.append(a)
                w = w * np.exp(a * wrong)
                w /= w.sum()
                if err <= 1e-10:
                    break
            if not self.members:
                self.members.append(_fit_member(X, y, self.k, p, np.random.default_rng(seeds[0])))
                self.weights.append(1.0)
        self.weights = np.array(self.weights)
        return self

    def _filled(self, X):
        X = np.asarray(X, dtype=float)
        if np.isnan(X).any():
            fill = self.fill if getattr(self, "fill", None) is not None else np.zeros(X.shape[1])
            X = np.where(np.isnan(X), fill[None, :], X)
        return X

    def member_proba(self, X):
        """Each member's confidences: members x samples x classes."""
        X = self._filled(X)
        return np.stack([m.predict_proba(X) for m in self.members])

    def predict_proba(self, X):
        P = self.member_proba(X)
        w = self.weights / self.weights.sum()
        if self.p["vote"] == "hard":
            P = np.eye(self.k)[P.argmax(axis=2)]
        return np.tensordot(w, P, axes=1)

    def predict(self, X):
        return self.predict_proba(X).argmax(axis=1)


# ---------------------------------------------------------------------------------------------
# Evaluation


def stratified_folds(y, k, seed=0):
    """Fold number (0..k-1) of each sample; classes dealt round the folds in a seeded order."""
    rng = np.random.default_rng(seed)
    fold = np.empty(len(y), dtype=int)
    start = 0
    for c in np.unique(y):
        idx = np.flatnonzero(y == c)
        rng.shuffle(idx)
        fold[idx] = (np.arange(len(idx)) + start) % k
        start = (start + len(idx)) % k
    return fold


def cross_validate(X, y, folds, **settings):
    """Predicted class of each sample when its fold is held out. ``folds``: fold label per sample.

    Leave-one-out: ``folds=np.arange(len(y))``.
    """
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=int)
    pred = np.empty(len(y), dtype=int)
    for f in np.unique(folds):
        test = folds == f
        model = Ensemble(**settings).fit(X[~test], y[~test])
        pred[test] = model.predict(X[test])
    return pred


def accuracy(y, pred):
    """Correct count, total and percentage (two decimals, as the paper prints)."""
    y = np.asarray(y)
    pred = np.asarray(pred)
    c = int((y == pred).sum())
    return {"correct": c, "total": int(len(y)), "errors": int(len(y) - c), "percent": f"{100.0 * c / len(y):.2f}"}


def run(train, test=None, **settings):
    """Fit on a training table and classify a test table, both from ``read_table`` or ``read_dbc``.

    Returns a JSON-ready dict with the predictions and the accuracy.
    """
    Xtr, ytr, genes, classes = train
    model = Ensemble(**settings).fit(Xtr, ytr)
    out = {"classes": classes, "settings": {k: v for k, v in model.p.items() if not k.startswith("_")}}
    out["settings"]["feature_sets"] = list(out["settings"]["feature_sets"])
    if test is not None:
        Xte, yte, genes_te, classes_te = test
        if list(genes_te) != list(genes):
            raise ValueError("training and test tables have different genes")
        if classes_te != classes:
            yte = np.array([classes.index(classes_te[i]) for i in yte])
        P = model.predict_proba(Xte)
        pred = P.argmax(axis=1)
        out["predictions"] = [
            {"sample": i + 1, "true": classes[int(t)], "predicted": classes[int(q)],
             "confidence": round(float(P[i, q]), 6)}
            for i, (t, q) in enumerate(zip(yte, pred))
        ]
        out["accuracy"] = accuracy(yte, pred)
    return out


def to_json(obj, path=None):
    s = json.dumps(obj, indent=2) + "\n"
    if path is None:
        return s
    Path(path).write_text(s, encoding="utf-8")
    return s
