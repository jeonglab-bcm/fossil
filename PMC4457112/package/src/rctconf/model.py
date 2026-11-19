"""Linear SVM (LIBLINEAR) on binary feature sets, with a calibrated confidence.

Cohen et al. (2015) trained LIBLINEAR on binary features and turned the signed margin into a
confidence "using an extension to the method of Ruping" that is described only in the journal
supplement. Here the confidence is a sigmoid of the margin fitted to out-of-fold margins
(Platt 1999 with Lin, Lin and Weng's 2007 algorithm), and the paper's baseline, a zero-centred
sigmoid of the margin, is kept beside it.
"""

from __future__ import annotations

import ctypes
import json
import math

import numpy as np
import scipy.sparse as sp

from .features import hashed_features
from .mdl import mdl_cut_points

LIBLINEAR_OPTIONS = "-s 1 -c 1 -B 1 -q"  # L2-regularized L2-loss SVM (dual), LIBLINEAR's default solver


class FeatureSpace:
    """Column index of each feature hash, one block per feature set, in the order given."""

    def __init__(self, vocab: dict[str, np.ndarray]):
        self.sets = list(vocab)
        self.vocab = {s: np.asarray(v, dtype=np.uint64) for s, v in vocab.items()}
        self.offsets = {}
        off = 0
        for s in self.sets:
            self.offsets[s] = off
            off += len(self.vocab[s])
        self.n_features = off

    @classmethod
    def fit(cls, hashed: dict, sets, min_count: int = 1):
        vocab = {}
        for s in sets:
            _, h = hashed[s]
            u, c = np.unique(h, return_counts=True)
            vocab[s] = u[c >= min_count]
        return cls(vocab)

    def matrix(self, hashed: dict) -> sp.csr_matrix:
        """Binary CSR matrix of hashed features; hashes not in the vocabulary are dropped."""
        blocks = []
        for s in self.sets:
            ptr, h = hashed[s]
            v = self.vocab[s]
            pos = np.searchsorted(v, h)
            pos = np.minimum(pos, max(len(v) - 1, 0))
            ok = (v[pos] == h) if len(v) else np.zeros(len(h), dtype=bool)
            rows = np.repeat(np.arange(len(ptr) - 1), np.diff(ptr))
            m = sp.csr_matrix((np.ones(ok.sum(), dtype=np.float64), (rows[ok], pos[ok])),
                              shape=(len(ptr) - 1, len(v)))
            blocks.append(m)
        return sp.hstack(blocks, format="csr", dtype=np.float64)


def _reset_rand() -> None:
    """LIBLINEAR's solvers draw from the C library's rand(); its state is per process, so a fit in a
    reused worker would depend on the fits before it. Reset it to the C default seed (1), the state of
    a fresh process, before every fit, so the same data always give the same model."""
    try:
        ctypes.CDLL(None).srand(1)
    except (OSError, AttributeError):  # pragma: no cover - no C library symbols (unusual platforms)
        pass


def _decfun(m):
    """Weights and bias of a two-class LIBLINEAR model, read from its weight array in one copy.

    The same numbers as m.get_decfun() (LIBLINEAR's get_w_value for two classes: w[i] for the first
    label, the bias term bias * w[nr_feature]), without one ctypes call per feature."""
    n = m.nr_feature
    has_bias = m.bias > 0
    arr = np.ctypeslib.as_array(m.w, shape=(n + (1 if has_bias else 0),)).copy()
    return arr[:n], (float(m.bias * arr[n]) if has_bias else 0.0)


def train_svm(X: sp.csr_matrix, y, options: str = LIBLINEAR_OPTIONS):
    """Train LIBLINEAR; return (weights, bias) with the margin of x being x @ w + b."""
    from liblinear import liblinearutil as ll

    _reset_rand()

    yy = np.where(np.asarray(y).astype(bool), 1.0, -1.0)
    m = ll.train(yy, X, options)
    w, b = _decfun(m)
    labels = m.get_labels()
    if labels[0] != 1:  # LIBLINEAR's decision value is for its first label
        w, b = -w, -b
    return w, b


def margins(X: sp.csr_matrix, w: np.ndarray, b: float) -> np.ndarray:
    return np.asarray(X @ w).ravel() + b


def zero_sigmoid(f) -> np.ndarray:
    """The paper's baseline confidence: a zero-centred sigmoid of the margin."""
    return 1.0 / (1.0 + np.exp(-np.asarray(f, dtype=float)))


def fit_sigmoid(f, y, max_iter: int = 100) -> tuple[float, float]:
    """Platt's sigmoid P(RCT | f) = 1 / (1 + exp(A f + B)), fitted by Newton's method with
    Platt's target smoothing (Lin, Lin and Weng 2007)."""
    f = np.asarray(f, dtype=float)
    y = np.asarray(y).astype(bool)
    n1, n0 = int(y.sum()), int((~y).sum())
    t = np.where(y, (n1 + 1.0) / (n1 + 2.0), 1.0 / (n0 + 2.0))
    A, B = 0.0, math.log((n0 + 1.0) / (n1 + 1.0))
    sigma, eps = 1e-12, 1e-5

    def objective(A, B):
        z = f * A + B
        return float(np.sum(np.where(z >= 0, t * z + np.log1p(np.exp(-z)), (t - 1) * z + np.log1p(np.exp(z)))))

    fval = objective(A, B)
    for _ in range(max_iter):
        z = f * A + B
        p = np.where(z >= 0, np.exp(-z) / (1 + np.exp(-z)), 1 / (1 + np.exp(z)))
        q = 1 - p
        d2 = p * q
        h11 = sigma + np.sum(f * f * d2)
        h22 = sigma + np.sum(d2)
        h21 = np.sum(f * d2)
        d1 = t - p
        g1, g2 = np.sum(f * d1), np.sum(d1)
        if abs(g1) < eps and abs(g2) < eps:
            break
        det = h11 * h22 - h21 * h21
        dA = -(h22 * g1 - h21 * g2) / det
        dB = -(-h21 * g1 + h11 * g2) / det
        gd = g1 * dA + g2 * dB
        step = 1.0
        while step >= 1e-10:
            nA, nB = A + step * dA, B + step * dB
            nf = objective(nA, nB)
            if nf < fval + 1e-4 * step * gd:
                A, B, fval = nA, nB, nf
                break
            step /= 2
        else:
            break
    return float(A), float(B)


def platt(f, A: float, B: float) -> np.ndarray:
    z = np.asarray(f, dtype=float) * A + B
    return np.where(z >= 0, np.exp(-z) / (1 + np.exp(-z)), 1 / (1 + np.exp(z)))


class RCTModel:
    """A trained RCT confidence model: feature space, LIBLINEAR weights and the confidence sigmoid."""

    def __init__(self, space: FeatureSpace, w, b, sigmoid=(None, None), author_bins=None, meta=None):
        self.space, self.w, self.b = space, np.asarray(w), float(b)
        self.sigmoid = sigmoid
        self.author_bins = None if author_bins is None else np.asarray(author_bins, dtype=float)
        self.meta = meta or {}

    @property
    def sets(self):
        return self.space.sets

    @property
    def n_features(self) -> int:
        return self.space.n_features

    def hashed(self, records):
        return hashed_features(records, self.sets, self.author_bins)

    def margins_hashed(self, hashed) -> np.ndarray:
        return margins(self.space.matrix(hashed), self.w, self.b)

    def margins(self, records) -> np.ndarray:
        return self.margins_hashed(self.hashed(records))

    def confidence_from_margins(self, f) -> np.ndarray:
        A, B = self.sigmoid
        if A is None:
            raise ValueError("the model has no fitted confidence sigmoid")
        return platt(f, A, B)

    def confidence(self, records) -> np.ndarray:
        """RCT confidence of each citation, between 0 and 1."""
        return self.confidence_from_margins(self.margins(records))

    def save(self, path) -> None:
        arrays = {f"vocab__{s}": self.space.vocab[s] for s in self.sets}
        arrays["w"] = self.w.astype(np.float32 if self.meta.get("float32") else np.float64)
        meta = dict(self.meta, sets=self.sets, b=self.b, sigmoid=list(self.sigmoid),
                    author_bins=None if self.author_bins is None else self.author_bins.tolist())
        arrays["meta"] = np.frombuffer(json.dumps(meta).encode("utf-8"), dtype=np.uint8)
        np.savez_compressed(path, **arrays)

    @classmethod
    def load(cls, path) -> "RCTModel":
        z = np.load(path)
        meta = json.loads(bytes(z["meta"]).decode("utf-8"))
        space = FeatureSpace({s: z[f"vocab__{s}"] for s in meta["sets"]})
        return cls(space, z["w"].astype(np.float64), meta["b"], tuple(meta["sigmoid"]), meta.get("author_bins"),
                   {k: v for k, v in meta.items() if k not in ("sets", "b", "sigmoid", "author_bins")})


def author_bins_for(records, labels) -> np.ndarray:
    counts = [int(r.get("n_authors") if r.get("n_authors") is not None else len(str(r.get("authors") or "").split("|")))
              for r in records]
    return mdl_cut_points(counts, labels)


def out_of_fold_margins(X, y, folds: int = 2, seed: int = 0, options: str = LIBLINEAR_OPTIONS) -> np.ndarray:
    """Margins of each row from a model trained without its fold."""
    y = np.asarray(y).astype(bool)
    rng = np.random.default_rng(seed)
    fold = rng.permutation(len(y)) % folds
    f = np.empty(len(y))
    for k in range(folds):
        tr, te = fold != k, fold == k
        w, b = train_svm(X[tr], y[tr], options)
        f[te] = margins(X[te], w, b)
    return f


def train(records, labels, sets, options: str = LIBLINEAR_OPTIONS, seed: int = 0) -> RCTModel:
    """Train an RCT confidence model on citations and their 0/1 labels (RCT publication type).

    The author-count bins come from the Fayyad-Irani MDLP on these labels; the confidence sigmoid is
    fitted to 2-fold out-of-fold margins.
    """
    records = list(records)
    y = np.asarray(labels).astype(bool)
    bins = author_bins_for(records, y) if "author_count" in sets else None
    hashed = hashed_features(records, sets, bins)
    space = FeatureSpace.fit(hashed, sets)
    X = space.matrix(hashed)
    w, b = train_svm(X, y, options)
    A, B = fit_sigmoid(out_of_fold_margins(X, y, 2, seed, options), y)
    return RCTModel(space, w, b, (A, B), bins, {"options": options, "seed": seed, "n_train": int(len(y)),
                                                 "n_pos": int(y.sum())})
