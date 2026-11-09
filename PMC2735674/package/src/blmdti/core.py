"""Bipartite local models for drug-target interaction prediction.

The method comes from:

> Bleakley K, Yamanishi Y. Supervised prediction of drug-target interactions using bipartite
> local models. *Bioinformatics* 25(18):2397-2403 (2009). doi:10.1093/bioinformatics/btp433

A drug-target network is a bipartite graph: drugs on one side, target proteins on the other, an
edge where the drug binds the target. The method scores every candidate pair (drug i, target j)
twice, with a local support vector machine each time:

- `blm_drug_scores` (BLMd in the paper): the local model of target j over drugs. Drugs other than
  i are labelled +1 when they bind target j and -1 otherwise; the kernel is the chemical
  similarity between drugs; the score of the pair is the decision value at drug i.
- `blm_target_scores` (BLMt): the local model of drug i over targets, labelled by whether they are
  bound by drug i, with the sequence-similarity kernel, scored at target j.

Each of the two leaves the scored vertex out of training, so a score is what the method would give
for a drug (or a target) it has never seen. `aggregate` combines the two with the paper's
m(x, y) = max(x, y).

This module also holds the two comparison methods the paper reports, so that a reproduction has
one implementation of each: `nn_drug_scores`/`nn_target_scores` (the nearest-neighbour baseline)
and `krm_drug_scores`/`krm_target_scores` (the kernel regression method of Yamanishi et al. 2008,
doi:10.1093/bioinformatics/btn162), together with the ranking metrics `auc` and `aupr`.
"""

from __future__ import annotations

import csv
from collections.abc import Sequence
from pathlib import Path
from typing import IO

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import shortest_path
from sklearn.svm import SVC

#: What a local model returns when it has no positive training example, that is when the scored
#: pair is the only known edge of that target (BLMd) or of that drug (BLMt). The paper does not
#: say; see the reproduction's results.json for the effect of each rule.
NO_POSITIVE_RULES = ("minus_one", "zero", "nan")

_NO_POSITIVE_VALUES = {"minus_one": -1.0, "zero": 0.0, "nan": np.nan}


def make_psd(similarity: np.ndarray, eps: float = 0.0) -> tuple[np.ndarray, float]:
    """Make a similarity matrix a valid kernel, as the paper's Section 3.5 describes.

    Symmetrize it ((S + S.T) / 2), then add a multiple of the identity until no eigenvalue is
    negative. Returns the kernel and the shift that was added.
    """
    s = np.asarray(similarity, dtype=float)
    if s.ndim != 2 or s.shape[0] != s.shape[1]:
        raise ValueError(f"similarity matrix must be square, got {s.shape}")
    sym = (s + s.T) / 2.0
    smallest = float(np.linalg.eigvalsh(sym).min())
    shift = 0.0 if smallest >= 0 else -smallest + eps
    if shift:
        sym = sym + shift * np.eye(sym.shape[0])
    return sym, shift


def _local_scores(kernel: np.ndarray, labels: np.ndarray, C: float, no_positive: str) -> np.ndarray:
    """Score every vertex from the local model trained on all the others.

    `labels` holds the +1/-1 label of each vertex for one local model. The vertex being scored is
    left out of training. Returns one score per vertex.
    """
    if no_positive not in _NO_POSITIVE_VALUES:
        raise ValueError(f"unknown no_positive rule {no_positive!r}; use one of {NO_POSITIVE_RULES}")
    n = kernel.shape[0]
    scores = np.empty(n, dtype=float)
    positives = int((labels > 0).sum())
    negatives = n - positives
    for v in range(n):
        left_positives = positives - (1 if labels[v] > 0 else 0)
        left_negatives = negatives - (0 if labels[v] > 0 else 1)
        if left_positives == 0 or left_negatives == 0:
            # One class only: the paper does not define this case.
            scores[v] = _NO_POSITIVE_VALUES[no_positive]
            continue
        keep = np.ones(n, dtype=bool)
        keep[v] = False
        model = SVC(C=C, kernel="precomputed")
        model.fit(kernel[np.ix_(keep, keep)], labels[keep])
        value = float(model.decision_function(kernel[v, keep].reshape(1, -1))[0])
        # LIBSVM orients the decision value by the label it sees first; classes_ is sorted, so the
        # second class is +1 and a positive value then means "interacting".
        scores[v] = value if model.classes_[1] > 0 else -value
    return scores


def blm_drug_scores(
    adjacency: np.ndarray,
    drug_kernel: np.ndarray,
    C: float = 1.0,
    no_positive: str = "minus_one",
    targets: Sequence[int] | None = None,
) -> np.ndarray:
    """BLMd: score every pair with the local model of its target over the drugs.

    `adjacency` is drugs x targets with 1 for a known interaction. `drug_kernel` is the positive
    semi-definite chemical-similarity kernel between drugs, in the same drug order. Returns a
    drugs x targets array of scores. Each score leaves its own drug out of training, so it is a
    prediction for a drug with no known target (rows 1 to 3 of the paper's Tables 1 to 4).

    `targets` restricts the work to those target columns and leaves the others NaN, which lets a
    pipeline split the columns across processes.
    """
    adjacency = np.asarray(adjacency)
    scores = np.full(adjacency.shape, np.nan, dtype=float)
    columns = range(adjacency.shape[1]) if targets is None else targets
    for j in columns:
        labels = np.where(adjacency[:, j] > 0, 1, -1)
        scores[:, j] = _local_scores(drug_kernel, labels, C, no_positive)
    return scores


def blm_target_scores(
    adjacency: np.ndarray,
    target_kernel: np.ndarray,
    C: float = 1.0,
    no_positive: str = "minus_one",
    drugs: Sequence[int] | None = None,
) -> np.ndarray:
    """BLMt: score every pair with the local model of its drug over the targets.

    The mirror of `blm_drug_scores`, with the sequence-similarity kernel between targets: a
    prediction for a target protein with no known targeting drug (rows 4 to 6 of Tables 1 to 4).
    `drugs` restricts the work to those drug rows and leaves the others NaN.
    """
    adjacency = np.asarray(adjacency)
    scores = np.full(adjacency.shape, np.nan, dtype=float)
    rows = range(adjacency.shape[0]) if drugs is None else drugs
    for i in rows:
        labels = np.where(adjacency[i, :] > 0, 1, -1)
        scores[i, :] = _local_scores(target_kernel, labels, C, no_positive)
    return scores


def aggregate(*score_matrices: np.ndarray, standardize: bool = False) -> np.ndarray:
    """The paper's m(x, y) = max(x, y), over two or more score matrices (Section 3.2).

    With `standardize`, each matrix is turned into z-scores (its own mean and standard deviation
    over all pairs) before the maximum is taken. The paper does not say whether it did this, and
    its discussion notes that the scores of two methods are not on the same scale; standardizing
    reproduces its aggregated rows, plain maximum does not (see the reproduction's results.json).
    """
    if not score_matrices:
        raise ValueError("aggregate needs at least one score matrix")
    matrices = [np.asarray(s, dtype=float) for s in score_matrices]
    if standardize:
        matrices = [
            (s - np.nanmean(s)) / np.nanstd(s) if np.nanstd(s) > 0 else s - np.nanmean(s)
            for s in matrices
        ]
    return np.nanmax(np.stack(matrices), axis=0)


def nn_drug_scores(adjacency: np.ndarray, drug_similarity: np.ndarray) -> np.ndarray:
    """Nearest-neighbour baseline for a new drug (NNd in the paper, Section 3.4).

    The nearest-profile method of Yamanishi et al. (2008), equation 1: find the drug most similar
    to drug i (drug i itself left out), and give the pair (i, j) that similarity when the nearest
    drug binds target j, and 0 otherwise. Scores therefore tie in blocks, one block per drug.
    """
    adjacency = np.asarray(adjacency, dtype=float)
    s = np.array(drug_similarity, dtype=float)
    np.fill_diagonal(s, -np.inf)  # the drug itself is left out
    nearest = np.argmax(s, axis=1)
    similarity = s[np.arange(s.shape[0]), nearest]
    return np.where(adjacency[nearest] > 0, similarity[:, None], 0.0)


def nn_target_scores(adjacency: np.ndarray, target_similarity: np.ndarray) -> np.ndarray:
    """Nearest-neighbour baseline for a new target (NNt): the mirror of `nn_drug_scores`."""
    return nn_drug_scores(np.asarray(adjacency).T, target_similarity).T


def shortest_paths(edges: np.ndarray) -> np.ndarray:
    """Unweighted shortest-path distances on a graph; unreachable pairs are infinite."""
    graph = csr_matrix(np.asarray(edges) > 0)
    return shortest_path(graph, method="D", unweighted=True, directed=False)


def pharmacological_space(
    adjacency: np.ndarray, h: float = 2.0, dimension: int | None = None
) -> tuple[np.ndarray, np.ndarray]:
    """Embed the drugs and targets of a bipartite network in the pharmacological space.

    Yamanishi et al. (2008), Section 3.3: a Gaussian of the shortest-path distance on the
    bipartite graph, eigen-decomposed as K = U U.T. Returns the drug rows and the target rows of U.
    Unreachable pairs have distance infinity, so their kernel entry is 0. `dimension` keeps only
    that many leading components; by default every positive eigenvalue is kept.
    """
    adjacency = np.asarray(adjacency, dtype=float)
    n_d, n_t = adjacency.shape
    n = n_d + n_t
    big = np.zeros((n, n), dtype=float)
    big[:n_d, n_d:] = adjacency
    big[n_d:, :n_d] = adjacency.T
    with np.errstate(over="ignore"):
        distance = shortest_paths(big)
        kernel = np.exp(-(distance**2) / (h**2))
    kernel[~np.isfinite(distance)] = 0.0
    values, vectors = np.linalg.eigh((kernel + kernel.T) / 2.0)
    order = np.argsort(values)[::-1]
    values, vectors = values[order], vectors[:, order]
    keep = values > 1e-10
    if dimension is not None:
        cut = np.zeros_like(keep)
        cut[: min(dimension, int(keep.sum()))] = True
        keep &= cut
    u = vectors[:, keep] * np.sqrt(values[keep])
    return u[:n_d], u[n_d:]


#: Relative cut-off for the small singular values of the similarity matrix in the kernel
#: regression solve. The paper's loss has no explicit regularizer, but the chemical similarity
#: matrix is ill conditioned and an unregularized solve overfits; see the reproduction's
#: results.json for the effect of this value.
KRM_RCOND = 1e-2


def krm_drug_scores(
    adjacency: np.ndarray,
    drug_similarity: np.ndarray,
    h: float = 2.0,
    dimension: int | None = None,
    drugs: Sequence[int] | None = None,
    rcond: float = KRM_RCOND,
) -> np.ndarray:
    """KRM for a new drug (KRMd): the kernel regression method of Yamanishi et al. (2008).

    For each drug in turn, the network without that drug is embedded in the pharmacological
    space, a kernel regression (their equations 5 to 7, minimised by W = pinv(S) U) maps the
    chemical-similarity profile of the held-out drug into that space, and the score of pair (i, j)
    is the inner product with the embedding of target j. `drugs` restricts the work to those rows;
    `rcond` regularizes the solve.
    """
    adjacency = np.asarray(adjacency, dtype=float)
    drug_similarity = np.asarray(drug_similarity, dtype=float)
    n_d, n_t = adjacency.shape
    scores = np.full((n_d, n_t), np.nan, dtype=float)
    rows = range(n_d) if drugs is None else drugs
    for i in rows:
        keep = np.ones(n_d, dtype=bool)
        keep[i] = False
        u_d, u_t = pharmacological_space(adjacency[keep], h, dimension)
        weights = np.linalg.pinv(drug_similarity[np.ix_(keep, keep)], rcond=rcond) @ u_d
        scores[i] = u_t @ (drug_similarity[i, keep] @ weights)
    return scores


def krm_target_scores(
    adjacency: np.ndarray,
    target_similarity: np.ndarray,
    h: float = 2.0,
    dimension: int | None = None,
    targets: Sequence[int] | None = None,
    rcond: float = KRM_RCOND,
) -> np.ndarray:
    """KRM for a new target (KRMt): the mirror of `krm_drug_scores`."""
    return krm_drug_scores(
        np.asarray(adjacency).T, target_similarity, h, dimension, drugs=targets, rcond=rcond
    ).T


def _ranking(labels: np.ndarray, scores: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    labels = np.asarray(labels, dtype=float).ravel()
    scores = np.asarray(scores, dtype=float).ravel()
    if labels.shape != scores.shape:
        raise ValueError(f"labels and scores differ in size: {labels.shape} {scores.shape}")
    finite = np.isfinite(scores)
    if not finite.all():
        labels, scores = labels[finite], scores[finite]
    order = np.argsort(-scores, kind="stable")
    return labels[order] > 0, scores[order]


def auc(labels: np.ndarray, scores: np.ndarray) -> float:
    """Area under the ROC curve, with tied scores given their average rank."""
    positive, sorted_scores = _ranking(labels, scores)
    n_pos = int(positive.sum())
    n_neg = positive.size - n_pos
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    ascending_scores = sorted_scores[::-1]
    ascending_positive = positive[::-1]
    ranks = np.empty(ascending_scores.size, dtype=float)
    start = 0
    for end in np.flatnonzero(np.diff(ascending_scores)).tolist() + [ascending_scores.size - 1]:
        ranks[start : end + 1] = (start + end) / 2.0 + 1.0
        start = end + 1
    rank_sum = ranks[ascending_positive].sum()
    return float((rank_sum - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg))


def precision_recall(labels: np.ndarray, scores: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Precision and recall at each distinct score threshold, in order of increasing recall.

    Pairs with equal scores share one threshold, so a block of ties gives a single point.
    """
    positive, sorted_scores = _ranking(labels, scores)
    n_pos = int(positive.sum())
    if n_pos == 0:
        return np.empty(0), np.empty(0)
    cuts = np.flatnonzero(np.diff(sorted_scores)).tolist() + [sorted_scores.size - 1]
    true_positives = np.cumsum(positive)
    index = np.asarray(cuts, dtype=int)
    precision = true_positives[index] / (index + 1.0)
    recall = true_positives[index] / n_pos
    return precision, recall


def aupr(labels: np.ndarray, scores: np.ndarray, rule: str = "trapezoid") -> float:
    """Area under the precision-recall curve.

    `rule` is `trapezoid` (the points joined by straight lines, as R's ROCR draws them) or `step`
    (the average precision: each step weighted by its gain in recall). The paper does not say
    which it used; the reproduction's results.json records the effect of the choice.
    """
    precision, recall = precision_recall(labels, scores)
    if precision.size == 0:
        return float("nan")
    if rule == "trapezoid":
        return float(np.trapezoid(precision, recall) + recall[0] * precision[0])
    if rule == "step":
        gains = np.diff(np.concatenate(([0.0], recall)))
        return float((precision * gains).sum())
    raise ValueError(f"unknown AUPR rule {rule!r}; use 'trapezoid' or 'step'")


def interactions(adjacency: np.ndarray) -> np.ndarray:
    """The 1/0 label of every pair, flattened in the order of the score matrices."""
    return (np.asarray(adjacency) > 0).astype(int).ravel()


def scores_table(
    adjacency: np.ndarray, score_matrices: dict[str, np.ndarray], aupr_rule: str = "trapezoid"
) -> list[dict]:
    """AUC and AUPR of each named score matrix against the known interactions, as percentages."""
    labels = interactions(adjacency)
    return [
        {
            "method": name,
            "auc": 100.0 * auc(labels, scores),
            "aupr": 100.0 * aupr(labels, scores, rule=aupr_rule),
        }
        for name, scores in score_matrices.items()
    ]


def read_matrix(path: str | Path) -> tuple[list[str], list[str], np.ndarray]:
    """Read a tab-separated matrix with a header row and a label column.

    Returns the row labels, the column labels and the values. This is the format of the Yamanishi
    et al. (2008) benchmark files (adjacency and similarity matrices).
    """
    with open(path, encoding="utf-8") as f:
        header = f.readline().rstrip("\n").split("\t")[1:]
        rows, values = [], []
        for line in f:
            if not line.strip():
                continue
            fields = line.rstrip("\n").split("\t")
            rows.append(fields[0])
            values.append([float(x) for x in fields[1:]])
    return rows, header, np.array(values, dtype=float)


def read_network(path: str | Path) -> tuple[list[str], list[str], np.ndarray]:
    """Read a benchmark adjacency file and return (drugs, targets, drugs x targets).

    The benchmark files have targets as rows and drugs as columns; every function here takes
    drugs x targets.
    """
    target_labels, drug_labels, matrix = read_matrix(path)
    return drug_labels, target_labels, matrix.T


def write_matrix(
    rows: Sequence[str], columns: Sequence[str], values: np.ndarray, out: IO[str]
) -> None:
    """Write a labelled matrix in the same tab-separated format, at full float precision."""
    writer = csv.writer(out, delimiter="\t", lineterminator="\n")
    writer.writerow([""] + list(columns))
    for label, row in zip(rows, np.asarray(values, dtype=float)):
        writer.writerow([label] + [repr(float(x)) for x in row])
