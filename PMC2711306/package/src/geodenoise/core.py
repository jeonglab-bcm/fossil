"""Geometric de-noising of protein-protein interaction networks (Kuchaiev et al. 2009).

The method, in four steps:

1. Embed the network: shortest-path lengths L between all pairs of nodes play the role of squared
   distances (the paper's distance is sqrt(L)); pairs further apart than ``max_path`` steps, or in
   different components, get the value ``unreachable``. Classical multidimensional scaling
   (double centering, top eigenvectors) gives coordinates, and each coordinate is rescaled to
   [0, 1], as in the authors' Matlab function ``embed_novi``.
2. Algorithm 1: every non-adjacent pair closer than a threshold epsilon is a predicted interaction.
3. Algorithm 2: fit three-Gaussian mixtures by EM to the distances of edges and of non-edges,
   turn them into a posterior with a prior P(edge), and give every pair within distance delta a
   confidence score, divided by the largest score so that the best pair scores 1.
4. Pairs that are edges but lie far apart in the embedding are candidate false positives.

Settings the paper does not print were taken from the authors' Matlab code and web page
(kuchaev.com/Denoising, archived 2012-2018): ``max_path=29``, ``unreachable=200``, per-axis
scaling to [0, 1], P(edge) = 0.001, 18,000 training distances, EM stopping at a log-likelihood
change below 0.01. This module is an independent implementation in Python; it contains none of
the authors' code.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components, shortest_path
from scipy.sparse.linalg import LinearOperator, eigsh

MAX_PATH = 29
UNREACHABLE = 200
PRIOR_EDGE = 0.001
DELTA = 0.4
LEARN_SET_SIZE = 18000
EM_STOP = 0.01
N_COMPONENTS = 3

__all__ = [
    "Network",
    "Mixture",
    "read_network",
    "network_from_edges",
    "largest_component",
    "path_lengths",
    "embed",
    "pairwise_distances",
    "fit_mixture",
    "learn_densities",
    "confidence_scores",
    "predict",
    "candidate_false_positives",
    "roc_curve",
    "auc",
    "write_scores",
    "read_scores",
]


# ---------------------------------------------------------------------------------------------
# Networks


@dataclass
class Network:
    """An undirected simple graph: node names and edges as index pairs (i < j)."""

    nodes: list[str]
    edges: np.ndarray  # shape (m, 2), int, i < j, unique

    @property
    def n(self) -> int:
        return len(self.nodes)

    @property
    def m(self) -> int:
        return int(self.edges.shape[0])

    def adjacency(self) -> csr_matrix:
        i, j = self.edges[:, 0], self.edges[:, 1]
        data = np.ones(2 * self.m, dtype=np.int8)
        return csr_matrix((data, (np.r_[i, j], np.r_[j, i])), shape=(self.n, self.n))

    def edge_set(self) -> set[tuple[int, int]]:
        return {(int(a), int(b)) for a, b in self.edges}


def network_from_edges(pairs: Iterable[tuple[str, str]], nodes: Sequence[str] | None = None) -> Network:
    """Build a Network from name pairs. Self-loops and repeated pairs are dropped.

    Nodes are numbered in order of first appearance, unless ``nodes`` gives the order (nodes
    listed there but in no edge are kept as isolated nodes).
    """
    index: dict[str, int] = {}
    names: list[str] = []
    if nodes is not None:
        for v in nodes:
            if v not in index:
                index[v] = len(names)
                names.append(v)
    seen: set[tuple[int, int]] = set()
    for a, b in pairs:
        if a == b:
            continue
        for v in (a, b):
            if v not in index:
                if nodes is not None:
                    raise ValueError(f"node {v!r} is not in the given node list")
                index[v] = len(names)
                names.append(v)
        i, j = index[a], index[b]
        seen.add((min(i, j), max(i, j)))
    edges = np.array(sorted(seen), dtype=np.int64).reshape(-1, 2)
    return Network(names, edges)


def read_network(path: str | Path) -> Network:
    """Read an edge list: two columns of node names, tab, comma or space separated.

    Lines starting with '#' are skipped, and so is a first line whose first two fields are
    'a'/'b', 'source'/'target', 'node1'/'node2' or 'protein_a'/'protein_b' (any case).
    """
    pairs = []
    with open(path, encoding="utf-8") as f:
        for k, line in enumerate(f):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            sep = "\t" if "\t" in line else ("," if "," in line else None)
            parts = [p.strip() for p in line.split(sep) if p.strip()]
            if len(parts) < 2:
                raise ValueError(f"{path}: line {k + 1} has fewer than two columns")
            if k == 0 and (parts[0].lower(), parts[1].lower()) in {
                    ("a", "b"), ("source", "target"), ("node1", "node2"), ("protein_a", "protein_b")}:
                continue
            pairs.append((parts[0], parts[1]))
    if not pairs:
        raise ValueError(f"{path}: no edges")
    return network_from_edges(pairs)


def largest_component(net: Network) -> Network:
    """The largest connected component, nodes renumbered in their original order."""
    _, labels = connected_components(net.adjacency(), directed=False)
    big = np.bincount(labels).argmax()
    keep = np.flatnonzero(labels == big)
    new = -np.ones(net.n, dtype=np.int64)
    new[keep] = np.arange(keep.size)
    e = new[net.edges]
    e = e[(e >= 0).all(axis=1)]
    return Network([net.nodes[k] for k in keep], e)


# ---------------------------------------------------------------------------------------------
# Embedding


def path_lengths(net: Network, max_path: int = MAX_PATH) -> np.ndarray:
    """Shortest-path lengths as uint8; 0 on the diagonal and for pairs further than max_path."""
    if not 1 <= max_path <= 254:
        raise ValueError("max_path must be between 1 and 254")
    d = shortest_path(net.adjacency(), method="D", directed=False, unweighted=True)
    d[~np.isfinite(d) | (d > max_path)] = 0
    return d.astype(np.uint8)


def _mds_matvec(L: np.ndarray, unreachable: float):
    """Product with B = -1/2 J P J, where P = L - unreachable where L > 0 and P = 0 elsewhere
    (the authors' sparse form of the squared-distance matrix). As in the authors' code, the
    diagonal of L holds 2, the length of the shortest closed walk, for every node with an edge."""
    n = L.shape[0]
    P = L.astype(np.float64)
    if not np.any(np.diag(L)):
        P[np.diag_indices(n)] = np.where(L.any(axis=1), 2.0, 0.0)
    P[P > 0] -= unreachable
    psum = P.sum(axis=0)
    ptot = psum.sum()

    def mv(v):
        v = np.asarray(v, dtype=np.float64).reshape(n, -1)
        mvv = v.mean(axis=0)
        out = P @ v - np.outer(psum, mvv) + (mvv * ptot / n - (psum @ v) / n)[None, :]
        return -0.5 * out

    return mv


def embed(
    net: Network,
    dim: int,
    *,
    max_path: int = MAX_PATH,
    unreachable: float = UNREACHABLE,
    solver: str = "eigsh",
    seed: int = 0,
    tol: float = 1e-3,
    lengths: np.ndarray | None = None,
    return_eigenvalues: bool = False,
):
    """Coordinates of the nodes in ``dim`` dimensions, each axis scaled to [0, 1].

    solver "eigsh" computes the leading eigenpairs exactly (ARPACK); solver "subspace" runs the
    subspace iteration of the authors' code (random start from ``seed``, stop when no vector
    moves by more than ``tol``), which stops short of exact convergence. ``lengths`` may pass a
    precomputed ``path_lengths`` matrix.
    """
    if dim < 1:
        raise ValueError("dim must be at least 1")
    if net.n <= dim + 1:
        raise ValueError("the network needs more nodes than dim + 1")
    L = path_lengths(net, max_path) if lengths is None else lengths
    mv = _mds_matvec(L, unreachable)
    if solver == "eigsh":
        op = LinearOperator((net.n, net.n), matvec=lambda v: mv(v).ravel(), matmat=mv,
                            dtype=np.float64)
        # a fixed start vector (not the constant vector, which B maps to zero)
        v0 = np.random.default_rng(12345).standard_normal(net.n)
        lam, vec = eigsh(op, k=dim, which="LM", tol=0, v0=v0)
        order = np.argsort(-np.abs(lam))
        lam, vec = lam[order], vec[:, order]
    elif solver == "subspace":
        rng = np.random.default_rng(seed)
        V = rng.standard_normal((net.n, dim))
        while True:
            W = mv(V)
            Q = np.empty_like(W)
            for i in range(dim):  # Gram-Schmidt in order, as in the authors' code
                w = W[:, i] - Q[:, :i] @ (Q[:, :i].T @ W[:, i])
                Q[:, i] = w / np.linalg.norm(w)
            moved = np.linalg.norm(V - Q, axis=0).max()
            V = Q
            if moved <= tol:
                break
        lam = np.einsum("ij,ij->j", V, mv(V))
        vec = V
    else:
        raise ValueError("solver must be 'eigsh' or 'subspace'")
    if np.any(lam <= 0):
        raise ValueError("a leading eigenvalue is not positive; the embedding is undefined")
    X = vec * np.sqrt(lam)[None, :]
    X = X - X.min(axis=0)
    span = X.max(axis=0)
    span[span == 0] = 1.0
    X = X / span
    return (X, lam) if return_eigenvalues else X


def pairwise_distances(X: np.ndarray) -> np.ndarray:
    """Euclidean distance matrix of the rows of X (float64)."""
    X = np.asarray(X, dtype=np.float64)
    D = np.zeros((X.shape[0], X.shape[0]))
    for k in range(X.shape[1]):
        diff = X[:, k][:, None] - X[:, k][None, :]
        D += diff * diff
    np.sqrt(D, out=D)
    return D


# ---------------------------------------------------------------------------------------------
# Densities and scores


@dataclass
class Mixture:
    """A one-dimensional Gaussian mixture: weights, means and variances."""

    weights: np.ndarray
    means: np.ndarray
    variances: np.ndarray
    log_likelihood: float = float("nan")
    iterations: int = 0

    def pdf(self, x) -> np.ndarray:
        x = np.asarray(x, dtype=np.float64)[..., None]
        z = (x - self.means) ** 2 / self.variances
        return (self.weights * np.exp(-0.5 * z) / np.sqrt(2 * np.pi * self.variances)).sum(axis=-1)

    def to_dict(self) -> dict:
        return {"weights": self.weights.tolist(), "means": self.means.tolist(),
                "variances": self.variances.tolist(), "log_likelihood": self.log_likelihood,
                "iterations": self.iterations}


def fit_mixture(x, n_components: int = N_COMPONENTS, *, stop: float = EM_STOP, rng=None,
                max_iter: int = 100000) -> Mixture:
    """EM for a one-dimensional Gaussian mixture, with the authors' rules.

    Each component starts at the mean and the sample variance (n - 1) of 30 values drawn with
    replacement from the first 100 values of x, with equal weights. The log-likelihood is checked
    every 10 iterations, and EM stops when it changes by less than ``stop``.
    """
    x = np.asarray(x, dtype=np.float64).ravel()
    if x.size < 2:
        raise ValueError("need at least two values")
    rng = np.random.default_rng(rng)
    head = x[: min(100, x.size)]
    mu = np.empty(n_components)
    var = np.empty(n_components)
    for k in range(n_components):
        s = head[rng.integers(0, head.size, 30)]
        mu[k] = s.mean()
        var[k] = s.var(ddof=1)
    var[var <= 0] = max(float(x.var()), 1e-12)
    w = np.full(n_components, 1.0 / n_components)
    old = -1e6
    it = 1
    ll = float("nan")
    while it <= max_iter:
        dens = w * np.exp(-0.5 * (x[:, None] - mu) ** 2 / var) / np.sqrt(2 * np.pi * var)
        g = dens / dens.sum(axis=1, keepdims=True)
        nk = g.sum(axis=0)
        mu = (g * x[:, None]).sum(axis=0) / nk
        var = np.maximum((g * (x[:, None] - mu) ** 2).sum(axis=0) / nk, 1e-300)
        w = nk / x.size
        if it % 10 == 0:
            dens = w * np.exp(-0.5 * (x[:, None] - mu) ** 2 / var) / np.sqrt(2 * np.pi * var)
            ll = float(np.log(dens.sum(axis=1)).sum())
            if abs(ll - old) < stop:
                break
            old = ll
        it += 1
    return Mixture(w, mu, var, ll, it)


def _nonedge_pairs(net: Network):
    A = net.adjacency().toarray().astype(bool)
    iu, ju = np.triu_indices(net.n, 1)
    non = ~A[iu, ju]
    return iu[non], ju[non]


def learn_densities(net: Network, D: np.ndarray, *, size: int = LEARN_SET_SIZE,
                    n_components: int = N_COMPONENTS, stop: float = EM_STOP, rng=None):
    """p(dist|edge) and p(dist|nonedge): mixtures fitted to ``size`` distances drawn with
    replacement from the edges and from the non-adjacent pairs, as in the authors' code."""
    rng = np.random.default_rng(rng)
    ei, ej = net.edges[:, 0], net.edges[:, 1]
    k = rng.integers(0, net.m, size)
    edge_d = D[ei[k], ej[k]]
    ni, nj = _nonedge_pairs(net)
    k2 = rng.integers(0, ni.size, size)
    non_d = D[ni[k2], nj[k2]]
    f_edge = fit_mixture(edge_d, n_components, stop=stop, rng=rng)
    f_non = fit_mixture(non_d, n_components, stop=stop, rng=rng)
    return f_edge, f_non


def confidence_scores(net: Network, D: np.ndarray, f_edge: Mixture, f_non: Mixture, *,
                      prior_edge: float = PRIOR_EDGE, delta: float = DELTA):
    """Algorithm 2: every pair (i < j) with distance <= delta, its posterior P(edge|dist) and the
    confidence score (posterior divided by the largest posterior). Returns a structured array
    with fields i, j, distance, posterior, score, is_edge, sorted by score (high first)."""
    if not 0 < prior_edge < 1:
        raise ValueError("prior_edge must be between 0 and 1")
    iu, ju = np.triu_indices(net.n, 1)
    d = D[iu, ju]
    sel = d <= delta
    i, j, d = iu[sel], ju[sel], d[sel]
    pe = f_edge.pdf(d) * prior_edge
    pn = f_non.pdf(d) * (1 - prior_edge)
    post = pe / (pe + pn)
    score = post / post.max()
    is_edge = np.asarray(net.adjacency()[i, j]).ravel() > 0
    out = np.zeros(i.size, dtype=[("i", "i8"), ("j", "i8"), ("distance", "f8"),
                                  ("posterior", "f8"), ("score", "f8"), ("is_edge", "?")])
    out["i"], out["j"], out["distance"] = i, j, d
    out["posterior"], out["score"], out["is_edge"] = post, score, is_edge
    order = np.lexsort((out["j"], out["i"], -out["score"]))
    return out[order]


def predict(net: Network, D: np.ndarray, epsilon: float) -> np.ndarray:
    """Algorithm 1: non-adjacent pairs (i < j) closer than epsilon, as a (k, 2) array."""
    ni, nj = _nonedge_pairs(net)
    sel = D[ni, nj] < epsilon
    return np.stack([ni[sel], nj[sel]], axis=1)


def candidate_false_positives(net: Network, D: np.ndarray, delta: float = DELTA) -> np.ndarray:
    """Edges whose endpoints are further apart than delta, as a (k, 2) array."""
    d = D[net.edges[:, 0], net.edges[:, 1]]
    return net.edges[d > delta]


# ---------------------------------------------------------------------------------------------
# Evaluation


def roc_curve(scores, positive, *, higher_is_positive: bool = False):
    """ROC counts over every threshold on ``scores`` (distances by default: a pair is called
    positive when its score is at or below the threshold). Returns (thresholds, tp, fp, P, N),
    with tp and fp counted at each distinct threshold."""
    s = np.asarray(scores, dtype=np.float64)
    y = np.asarray(positive, dtype=bool)
    if s.shape != y.shape:
        raise ValueError("scores and positive must have the same length")
    if higher_is_positive:
        s = -s
    order = np.argsort(s, kind="stable")
    s, y = s[order], y[order]
    tp = np.cumsum(y)
    fp = np.cumsum(~y)
    last = np.r_[np.flatnonzero(np.diff(s)), s.size - 1]
    thr = -s[last] if higher_is_positive else s[last]
    return thr, tp[last], fp[last], int(y.sum()), int((~y).sum())


def auc(tp, fp, P: int, N: int) -> float:
    """Area under the ROC curve from cumulative counts (trapezoids from (0, 0) to (1, 1))."""
    x = np.r_[0.0, np.asarray(fp) / N, 1.0]
    y = np.r_[0.0, np.asarray(tp) / P, 1.0]
    return float(np.sum((x[1:] - x[:-1]) * (y[1:] + y[:-1]) / 2))


# ---------------------------------------------------------------------------------------------
# Files


SCORE_COLUMNS = ["protein_a", "protein_b", "distance", "posterior", "score", "is_edge"]


def write_scores(net: Network, scores: np.ndarray, f) -> None:
    """Write confidence scores as CSV (columns SCORE_COLUMNS)."""
    w = csv.writer(f, lineterminator="\n")
    w.writerow(SCORE_COLUMNS)
    for r in scores:
        w.writerow([net.nodes[r["i"]], net.nodes[r["j"]], f"{r['distance']:.6f}",
                    f"{r['posterior']:.6g}", f"{r['score']:.6f}", int(r["is_edge"])])


def read_scores(path: str | Path) -> list[dict]:
    """Read a CSV written by write_scores."""
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["distance"] = float(r["distance"])
        r["posterior"] = float(r["posterior"])
        r["score"] = float(r["score"])
        r["is_edge"] = r["is_edge"] == "1"
    return rows
