"""Network (N and L) feature sets of Lee et al. 2008, with optional condition weights (CoLP).

A protein's distance-D neighbourhood C_i^D holds the protein itself and every protein
within D links. Each member k gets the weight w_ki = 1 / (Psi_ki + rho), where Psi_ki is
the number of distinct locations covered by the proteins along the path from i to k
(the protein's own locations are hidden, so its features never see its own label), and
the largest weight is kept over the shortest paths. CoLP makes the weights depend on a
condition by multiplying each path's weight by the product of the expression coherence
scores along it (Lee et al. 2013, Methods).

N^D_i is the weighted mean of the members' S feature vectors. L^D_i(y) is the weighted
mean, over the other members, of max_{x in Gamma_k} p(y | x), with p the pair-location
conditional probability (PLCP) matrix of the network.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from scipy import sparse

RHO_HUMAN = 2.0  # Lee et al. 2008: rho = 2 for H. sapiens
_POP = np.array([bin(i).count("1") for i in range(1 << 16)], dtype=np.float64)


def adjacency(n: int, edges: np.ndarray, weights: np.ndarray | None = None) -> sparse.csr_matrix:
    """Symmetric CSR adjacency from an (m, 2) array of node indices; self-loops dropped, duplicates merged."""
    e = np.asarray(edges, dtype=np.int64).reshape(-1, 2)
    keep = e[:, 0] != e[:, 1]
    e = e[keep]
    w = np.ones(len(e)) if weights is None else np.asarray(weights, dtype=float)[keep]
    a = sparse.coo_matrix((np.r_[w, w], (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), shape=(n, n)).tocsr()
    # merged duplicates sum their weights: take the maximum instead
    a.sum_duplicates()
    if weights is None:
        a.data[:] = 1.0
    else:
        m = sparse.coo_matrix((np.r_[w, w], (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), shape=(n, n))
        order = np.lexsort((-m.data, m.col, m.row))
        r, c, d = m.row[order], m.col[order], m.data[order]
        first = np.r_[True, (r[1:] != r[:-1]) | (c[1:] != c[:-1])]
        a = sparse.csr_matrix((d[first], (r[first], c[first])), shape=(n, n))
    return a


def location_masks(labels: Sequence[Sequence[int]], n_locations: int) -> np.ndarray:
    """Bit mask of known locations per protein (0 when unknown)."""
    if n_locations > 16:
        raise ValueError("at most 16 locations are supported")
    m = np.zeros(len(labels), dtype=np.int64)
    for i, ls in enumerate(labels):
        for loc in ls:
            m[i] |= 1 << int(loc)
    return m


def neighbourhood_weights(adj: sparse.csr_matrix, masks: np.ndarray, distance: int, rho: float = RHO_HUMAN,
                          coherence: sparse.csr_matrix | None = None) -> sparse.csr_matrix:
    """Weights w_ki of the distance-D neighbourhood (D = 1 or 2), self included, as a CSR matrix (row = i).

    coherence, when given, has the structure of adj and holds each link's condition weight;
    a path's weight is multiplied by the product of the link weights along it.
    """
    if distance not in (1, 2):
        raise ValueError("distance must be 1 or 2")
    n = adj.shape[0]
    adj = adj.tocsr()
    adj.sort_indices()
    coh = adj.copy() if coherence is None else coherence.tocsr()
    if coherence is None:
        coh.data[:] = 1.0
    coh.sort_indices()
    if coh.nnz != adj.nnz or not np.array_equal(coh.indices, adj.indices):
        raise ValueError("coherence must have the structure of the adjacency")
    indptr, indices, cdata = adj.indptr, adj.indices, coh.data
    pop = _POP[masks]
    rows, cols, vals = [np.arange(n)], [np.arange(n)], [np.full(n, 1.0 / rho)]
    for i in range(n):
        s, e = indptr[i], indptr[i + 1]
        js = indices[s:e]
        if len(js) == 0:
            continue
        cij = cdata[s:e]
        w1 = cij / (pop[js] + rho)
        rows.append(np.full(len(js), i))
        cols.append(js)
        vals.append(w1)
        if distance == 1:
            continue
        starts, ends = indptr[js], indptr[js + 1]
        lens = ends - starts
        if lens.sum() == 0:
            continue
        idx = np.repeat(starts - np.r_[0, np.cumsum(lens)[:-1]], lens) + np.arange(lens.sum())
        ks = indices[idx]
        jrep = np.repeat(js, lens)
        w2 = np.repeat(cij, lens) * cdata[idx] / (_POP[masks[jrep] | masks[ks]] + rho)
        near = np.zeros(n, dtype=bool)
        near[js] = True
        near[i] = True
        sel = ~near[ks]
        ks, w2 = ks[sel], w2[sel]
        if len(ks) == 0:
            continue
        order = np.lexsort((-w2, ks))
        ks, w2 = ks[order], w2[order]
        first = np.r_[True, ks[1:] != ks[:-1]]
        rows.append(np.full(int(first.sum()), i))
        cols.append(ks[first])
        vals.append(w2[first])
    return sparse.csr_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=(n, n))


def plcp(adj: sparse.csr_matrix, labels: np.ndarray) -> np.ndarray:
    """Pair-location conditional probability p(l_j | l_i) from a binary (n, L) label matrix (Lee et al. 2008)."""
    lab = np.asarray(labels, dtype=float)
    na = lab.sum(axis=1)
    scaled = np.divide(lab, na[:, None], out=np.zeros_like(lab), where=na[:, None] > 0)
    a = adj.copy().tocsr()
    a.setdiag(0)
    a.eliminate_zeros()
    a.data[:] = 1.0
    pair = scaled.T @ (a @ scaled)
    nl = lab.sum(axis=0)
    inter = pair / (nl[:, None] + nl[None, :])
    tot = inter.sum(axis=1, keepdims=True)
    return np.divide(inter, tot, out=np.zeros_like(inter), where=tot > 0)


def n_features(weights: sparse.csr_matrix, s: np.ndarray) -> np.ndarray:
    """Weighted mean of the S vectors over each neighbourhood (self included)."""
    tot = np.asarray(weights.sum(axis=1)).ravel()
    return (np.asarray(weights @ s) / tot[:, None]).astype(np.float32)


def l_features(weights: sparse.csr_matrix, labels: np.ndarray, p: np.ndarray) -> np.ndarray:
    """L^D: weighted mean over the other members of max_{x in Gamma_k} p(y | x); self weight stays in the total."""
    lab = np.asarray(labels, dtype=bool)
    best = np.zeros((lab.shape[0], p.shape[1]))
    for x in range(lab.shape[1]):
        rows = lab[:, x]
        best[rows] = np.maximum(best[rows], p[x])
    tot = np.asarray(weights.sum(axis=1)).ravel()
    off = weights.tocsr(copy=True)
    off.setdiag(0)
    off.eliminate_zeros()
    return (np.asarray(off @ best) / tot[:, None]).astype(np.float32)
