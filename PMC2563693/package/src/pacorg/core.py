"""Pathway activity inference with condition-responsive genes (PAC), after Lee et al. 2008.

The method, as the paper's Methods describe it:

1. Each gene's expression is z-transformed over all samples (mean 0, standard deviation 1).
2. The activity of a gene set G in sample j is the sum of the member z-scores divided by the
   square root of the number of members.
3. The discriminative score S(G) is the two-sample t statistic of the activity between the two
   classes.
4. Condition-responsive genes (CORGs): rank a pathway's member genes by their own t statistic,
   descending if the members' mean t is positive and ascending otherwise; start from the top
   gene and add the next gene while |S(G)| increases; stop at the first addition that does not.
5. Pathways are pre-selected by the score of Tian et al. 2005. The paper's Methods call it the
   average of the member genes' t statistics; Tian et al.'s statistic, and the one the paper's
   Table 1 and Fig. 2 follow, is that average standardized by the set size: sum of member t over
   the square root of the number of members (``tian_scores``).

Pathway markers are then used as features of a logistic-regression classifier, adding markers
in increasing order of p-value and choosing the number by the AUC on a validation set
(``sequential_selection``).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Iterable, Mapping, Sequence

import numpy as np
from scipy.special import expit as _expit

__all__ = [
    "PathwayResult",
    "activity",
    "auc",
    "find_corgs",
    "fit_logistic",
    "infer_pathways",
    "mean_activity",
    "median_activity",
    "pca_activity",
    "predict_logistic",
    "read_cls",
    "read_gct",
    "read_gmt",
    "read_results",
    "sequential_selection",
    "t_pvalues",
    "t_scores",
    "tian_scores",
    "write_results",
    "zscore",
]


# ----------------------------------------------------------------------------- file formats

def read_gct(path) -> tuple[list[str], list[str], np.ndarray]:
    """Read a GCT 1.2 file. Returns (gene names, sample names, genes x samples matrix)."""
    with open(path, encoding="utf-8") as f:
        lines = [l.rstrip("\r") for l in f.read().split("\n")]
    if not lines or not lines[0].startswith("#1.2"):
        raise ValueError(f"{path}: not a GCT 1.2 file")
    header = lines[2].rstrip("\t").split("\t")
    samples = header[2:]
    genes, rows = [], []
    for line in lines[3:]:
        if not line.strip():
            continue
        parts = line.split("\t")
        values = parts[2 : 2 + len(samples)]
        if len(values) != len(samples):
            raise ValueError(f"{path}: row {parts[0]} has {len(values)} values, expected {len(samples)}")
        genes.append(parts[0])
        rows.append([float(v) if v.strip() not in ("", "NA", "NaN") else math.nan for v in values])
    return genes, samples, np.asarray(rows, dtype=float)


def read_cls(path) -> list[str]:
    """Read a categorical CLS file and return one label per sample."""
    with open(path, encoding="utf-8") as f:
        lines = [l for l in f.read().split("\n") if l.strip()]
    if len(lines) < 3:
        raise ValueError(f"{path}: a CLS file has three lines")
    labels = lines[2].split()
    n = int(lines[0].split()[0])
    if len(labels) != n:
        raise ValueError(f"{path}: header says {n} samples, found {len(labels)} labels")
    return labels


def read_gmt(path) -> dict[str, list[str]]:
    """Read a GMT file: {set name: member genes in file order, duplicates removed}."""
    sets: dict[str, list[str]] = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 3:
                continue
            seen, members = set(), []
            for g in parts[2:]:
                if g and g not in seen:
                    seen.add(g)
                    members.append(g)
            sets[parts[0]] = members
    return sets


# ----------------------------------------------------------------------------- statistics

def zscore(X: np.ndarray) -> np.ndarray:
    """z-transform each row (gene) over all columns (samples): mean 0, standard deviation 1."""
    X = np.asarray(X, dtype=float)
    if X.ndim != 2:
        raise ValueError("expression must be a genes x samples matrix")
    if not np.all(np.isfinite(X)):
        raise ValueError("expression contains missing or infinite values; impute them first")
    sd = X.std(axis=1, ddof=1, keepdims=True)
    if np.any(sd == 0):
        raise ValueError("a gene has zero variance; drop it first")
    return (X - X.mean(axis=1, keepdims=True)) / sd


def _labels(y) -> np.ndarray:
    y = np.asarray(y)
    if y.dtype != bool:
        values = np.unique(y)
        if len(values) != 2:
            raise ValueError("labels must have exactly two classes")
        y = y == values[1]
    if y.sum() < 2 or (~y).sum() < 2:
        raise ValueError("each class needs at least two samples")
    return y


def t_scores(X: np.ndarray, y) -> np.ndarray:
    """Student's two-sample t statistic (pooled variance) of each row of X, class True minus False.

    X may be one vector (samples) or a matrix (rows x samples).
    """
    y = _labels(y)
    X = np.asarray(X, dtype=float)
    a, b = X[..., y], X[..., ~y]
    na, nb = a.shape[-1], b.shape[-1]
    ma, mb = a.mean(-1), b.mean(-1)
    ssa = ((a - ma[..., None]) ** 2).sum(-1)
    ssb = ((b - mb[..., None]) ** 2).sum(-1)
    sp2 = (ssa + ssb) / (na + nb - 2)
    with np.errstate(divide="ignore", invalid="ignore"):
        return (ma - mb) / np.sqrt(sp2 * (1.0 / na + 1.0 / nb))


def t_pvalues(t: np.ndarray, n: int) -> np.ndarray:
    """Two-sided p-values of t statistics with n - 2 degrees of freedom."""
    from scipy import stats

    return 2 * stats.t.sf(np.abs(t), n - 2)


def activity(Z: np.ndarray, rows: Sequence[int]) -> np.ndarray:
    """Combined z-score of a gene set: sum of the member rows of Z over sqrt(number of members)."""
    rows = list(rows)
    if not rows:
        raise ValueError("a gene set needs at least one member")
    return Z[rows].sum(axis=0) / math.sqrt(len(rows))


def tian_scores(t: np.ndarray, sets: Sequence[Sequence[int]]) -> np.ndarray:
    """Score of Tian et al. 2005: sum of each set's member t statistics over sqrt(members).

    Rank pathways by its absolute value. Empty sets score NaN.
    """
    return np.array([float(np.sum(t[list(s)])) / math.sqrt(len(s)) if len(s) else math.nan for s in sets])


def find_corgs(Z: np.ndarray, y, rows: Sequence[int], t: np.ndarray | None = None) -> list[int]:
    """Condition-responsive genes of one gene set (greedy search of the paper's Methods).

    Z: z-scored expression (genes x samples); y: two-class labels; rows: the member rows of Z;
    t: per-gene t statistics for all rows of Z (computed from Z and y when not given).
    Returns the CORG rows in the order they were added.
    """
    rows = list(rows)
    if not rows:
        raise ValueError("a gene set needs at least one member")
    y = _labels(y)
    member_t = t_scores(Z[rows], y) if t is None else np.asarray(t)[rows]
    # Stable sort, so ties keep the gene set's order.
    order = np.argsort(-member_t if member_t.mean() > 0 else member_t, kind="stable")
    ranked = [rows[i] for i in order]
    selected = [ranked[0]]
    running = Z[ranked[0]].copy()
    best = abs(t_scores(running, y))
    for r in ranked[1:]:
        trial = running + Z[r]
        score = abs(t_scores(trial / math.sqrt(len(selected) + 1), y))
        if score > best:
            selected.append(r)
            running, best = trial, score
        else:
            break
    return selected


@dataclass
class PathwayResult:
    """One pathway's CORGs and activity."""

    name: str
    members: int  # members in the gene set file
    measured: int  # members measured in the data
    corgs: list[str]
    tian: float  # Tian et al.'s score: sum of member t / sqrt(measured members)
    score: float  # S(G): t statistic of the CORG activity
    activity: np.ndarray = field(repr=False)


def infer_pathways(
    expression: np.ndarray,
    genes: Sequence[str],
    labels,
    gene_sets: Mapping[str, Iterable[str]],
    *,
    min_size: int = 1,
    zscored: bool = False,
) -> list[PathwayResult]:
    """CORGs, activity and scores of every gene set, in the order of ``gene_sets``.

    expression: genes x samples; genes: row names; labels: one class label per sample (two
    classes; the second class in sorted order, or True, is the case class of the t statistic).
    Gene sets with fewer than ``min_size`` measured members are left out.
    """
    y = _labels(labels)
    Z = np.asarray(expression, dtype=float) if zscored else zscore(expression)
    index = {g: i for i, g in enumerate(genes)}
    t = t_scores(Z, y)
    out = []
    for name, members in gene_sets.items():
        members = list(members)
        rows = [index[g] for g in members if g in index]
        if len(rows) < max(min_size, 1):
            continue
        corgs = find_corgs(Z, y, rows, t)
        a = activity(Z, corgs)
        out.append(
            PathwayResult(
                name=name,
                members=len(members),
                measured=len(rows),
                corgs=[genes[r] for r in corgs],
                tian=float(tian_scores(t, [rows])[0]),
                score=float(t_scores(a, y)),
                activity=a,
            )
        )
    return out


RESULT_COLUMNS = ["pathway", "members", "measured", "n_corgs", "corgs", "tian", "score"]


def write_results(results, file) -> None:
    """Write PathwayResult rows as CSV: pathway, members, measured, n_corgs, corgs, tian, score."""
    import csv

    w = csv.writer(file, lineterminator="\n")
    w.writerow(RESULT_COLUMNS)
    for r in results:
        w.writerow([r.name, r.members, r.measured, len(r.corgs), " ".join(r.corgs), repr(r.tian), repr(r.score)])


def read_results(path) -> list[dict]:
    """Read a results CSV (write_results) into dicts with typed values."""
    import csv

    out = []
    with open(path, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            out.append({
                "pathway": row["pathway"], "members": int(row["members"]), "measured": int(row["measured"]),
                "n_corgs": int(row["n_corgs"]), "corgs": row["corgs"].split(),
                "tian": float(row["tian"]), "score": float(row["score"]),
            })
    return out


# ----------------------------------------------------------------------------- other summaries

def mean_activity(X: np.ndarray, rows: Sequence[int]) -> np.ndarray:
    """Mean of the member rows (Guo et al. 2005)."""
    return np.asarray(X)[list(rows)].mean(axis=0)


def median_activity(X: np.ndarray, rows: Sequence[int]) -> np.ndarray:
    """Median of the member rows (Guo et al. 2005)."""
    return np.median(np.asarray(X)[list(rows)], axis=0)


def pca_activity(X: np.ndarray, rows: Sequence[int], fit_columns=None) -> np.ndarray:
    """First principal component score of the member rows (Bild et al. 2006).

    The component is fitted on ``fit_columns`` (all samples when None) and applied to every
    sample; its sign is set so that it correlates positively with the members' mean.
    """
    M = np.asarray(X, dtype=float)[list(rows)]
    fit = M if fit_columns is None else M[:, fit_columns]
    mu = fit.mean(axis=1, keepdims=True)
    if M.shape[0] == 1:
        return (M - mu)[0]
    _, _, vt = np.linalg.svd((fit - mu).T, full_matrices=False)
    w = vt[0]
    if w.sum() < 0:
        w = -w
    return w @ (M - mu)


# ----------------------------------------------------------------------------- classification

def auc(scores: np.ndarray, y) -> float:
    """Area under the ROC curve (ties count one half)."""
    y = np.asarray(y, dtype=bool)
    s = np.asarray(scores, dtype=float)
    pos, neg = s[y], s[~y]
    if len(pos) == 0 or len(neg) == 0:
        return math.nan
    from scipy.stats import rankdata

    r = rankdata(np.concatenate([pos, neg]))
    return float((r[: len(pos)].sum() - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg)))


def fit_logistic(X: np.ndarray, y, ridge: float = 1e-8, max_iter: int = 100) -> np.ndarray:
    """Logistic regression by Newton's method with a small ridge penalty (Weka's default 1e-8).

    X: samples x features (an intercept is added). Returns the coefficients, intercept first.
    With separable classes the coefficients grow until the iteration limit; the ranking of the
    samples, which is all an AUC uses, is settled long before.
    """
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=float)
    A = np.hstack([np.ones((X.shape[0], 1)), X])
    w = np.zeros(A.shape[1])
    pen = np.full(A.shape[1], ridge)
    pen[0] = 0.0

    def loss(w):
        z = A @ w
        return float(np.sum(np.logaddexp(0, z) - y * z) + 0.5 * np.sum(pen * w * w))

    current = loss(w)
    for _ in range(max_iter):
        p = _expit(A @ w)
        g = A.T @ (p - y) + pen * w
        H = (A * (p * (1 - p))[:, None]).T @ A + np.diag(pen + 1e-12)
        try:
            step = np.linalg.solve(H, g)
        except np.linalg.LinAlgError:
            step = np.linalg.lstsq(H, g, rcond=None)[0]
        s = 1.0
        while s > 1e-6:
            trial = w - s * step
            new = loss(trial)
            if new <= current:
                break
            s /= 2
        if s <= 1e-6:
            break
        w = trial
        if current - new < 1e-10 * (1 + abs(current)):
            current = new
            break
        current = new
    return w


def predict_logistic(w: np.ndarray, X: np.ndarray) -> np.ndarray:
    """Linear predictor (log odds) of fitted coefficients on samples x features."""
    return w[0] + np.asarray(X, dtype=float) @ w[1:]


def sequential_selection(
    train: np.ndarray,
    y_train,
    valid: np.ndarray,
    y_valid,
    order: Sequence[int],
    max_markers: int | None = None,
    ridge: float = 1e-8,
) -> tuple[int, np.ndarray, list[float]]:
    """Add markers one at a time in the given order and keep the count with the best validation AUC.

    train, valid: samples x markers. Returns (number of markers, coefficients, validation AUCs).
    Ties keep the smaller count.
    """
    order = list(order)
    if max_markers is not None:
        order = order[:max_markers]
    best_k, best_auc, best_w, aucs = 0, -1.0, None, []
    for k in range(1, len(order) + 1):
        cols = order[:k]
        w = fit_logistic(train[:, cols], y_train, ridge=ridge)
        a = auc(predict_logistic(w, valid[:, cols]), y_valid)
        aucs.append(a)
        if a > best_auc:
            best_k, best_auc, best_w = k, a, w
    return best_k, best_w, aucs
