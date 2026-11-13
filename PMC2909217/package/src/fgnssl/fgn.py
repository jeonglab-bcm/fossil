"""The weighted functional gene network (FGN) of You et al. (2010).

Expression profiles are clustered by divisive correlation clustering, then each edge of the
binary network (protein interactions plus complex co-membership) gets the weight of eq. 2:

    W(x_i, x_j) = L1 * (||x_i - C_i||^2 + ||x_j - C_j||^2) + (1 - L1) * ||C_i - C_j||^2

with C_i the centroid of gene i's cluster and L1 = 0.3.
"""

from __future__ import annotations

import numpy as np

L1_DEFAULT = 0.3


def impute_column_means(X: np.ndarray) -> np.ndarray:
    """Replace missing values (NaN) by the mean of their condition (column), as in the paper."""
    X = np.array(X, dtype=float, copy=True)
    means = np.nanmean(X, axis=0)
    means = np.where(np.isnan(means), 0.0, means)
    idx = np.where(np.isnan(X))
    X[idx] = means[idx[1]]
    return X


def pearson_matrix(X: np.ndarray) -> np.ndarray:
    """Pearson correlation between all rows of X. Constant rows correlate 0 with everything."""
    Xc = X - X.mean(axis=1, keepdims=True)
    norm = np.sqrt((Xc * Xc).sum(axis=1))
    norm[norm == 0] = np.inf
    Z = Xc / norm[:, None]
    R = Z @ Z.T
    np.clip(R, -1.0, 1.0, out=R)
    return R


def dcca(X: np.ndarray, max_clusters: int | None = None) -> np.ndarray:
    """Divisive correlation clustering as the paper describes it (Bhattacharya and De 2008).

    Start with one cluster. Repeatedly take the cluster that holds the most negative Pearson
    correlation between two of its genes x_i and x_j, and split it: every gene goes with x_i if
    its correlation with x_i is larger than with x_j, else with x_j. Stop when no cluster holds
    a negative correlation. Returns a cluster label (0, 1, ...) for each row of X.
    """
    X = np.asarray(X, dtype=float)
    n = X.shape[0]
    if n == 0:
        return np.zeros(0, dtype=int)
    R = pearson_matrix(X)
    labels = np.zeros(n, dtype=int)

    def most_negative(members: np.ndarray):
        sub = R[np.ix_(members, members)]
        k = int(np.argmin(sub))
        a, b = divmod(k, len(members))
        return sub[a, b], members[a], members[b]

    clusters = {0: np.arange(n)}
    worst = {0: most_negative(clusters[0])}
    next_id = 1
    while True:
        cid = min(worst, key=lambda c: worst[c][0])
        value, i, j = worst[cid]
        if value >= 0 or (max_clusters is not None and len(clusters) >= max_clusters):
            break
        members = clusters.pop(cid)
        del worst[cid]
        to_i = R[members, i] > R[members, j]
        to_i[members == i] = True
        to_i[members == j] = False
        for part in (members[to_i], members[~to_i]):
            clusters[next_id] = part
            worst[next_id] = most_negative(part) if len(part) > 1 else (0.0, part[0], part[0])
            next_id += 1
    # relabel in order of first member, so labels do not depend on split order
    order = sorted(clusters.values(), key=lambda m: int(m.min()))
    for k, members in enumerate(order):
        labels[members] = k
    return labels


def centroids(X: np.ndarray, labels: np.ndarray) -> np.ndarray:
    """Centroid of each cluster, one row per label."""
    k = int(labels.max()) + 1
    C = np.zeros((k, X.shape[1]))
    np.add.at(C, labels, X)
    counts = np.bincount(labels, minlength=k)[:, None]
    return C / counts


def edge_weights(X: np.ndarray, labels: np.ndarray, edges: np.ndarray, l1: float = L1_DEFAULT) -> np.ndarray:
    """Eq. 2 for each edge (i, j) given as rows of an integer array of shape (m, 2)."""
    C = centroids(X, labels)
    cen = C[labels]
    own = ((X - cen) ** 2).sum(axis=1)
    i, j = edges[:, 0], edges[:, 1]
    between = ((cen[i] - cen[j]) ** 2).sum(axis=1)
    return l1 * (own[i] + own[j]) + (1.0 - l1) * between
