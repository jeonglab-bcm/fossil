"""Network properties of You et al. (2010), Table 2, and the 18 pair features built from them.

Weighted measures (degree, clustering, betweenness, closeness, eigenvector centrality, shortest path)
use the FGN weights; shortest paths run on the inverted weights 1/w (Dijkstra), so a strong tie is a
short edge. Stress, information and flow-betweenness centrality and mutual neighbours use the binary
graph, as Table 2 says.

Pair features (our layout; the paper names 18 features from 10 properties but not their order):
the average and the absolute difference of the two genes' values for the 8 node properties
(16 features), the shortest-path length between the two genes, and their number of mutual neighbours.
"""

from __future__ import annotations

import igraph as ig
import numba
import numpy as np

NODE_PROPERTIES = (
    "degree", "clustering", "betweenness", "closeness", "eigenvector", "stress", "information", "flow",
)
FEATURE_NAMES = tuple(
    [f"avg_{p}" for p in NODE_PROPERTIES] + [f"diff_{p}" for p in NODE_PROPERTIES]
    + ["shortest_path", "mutual_neighbors"]
)


def make_graph(n: int, edges: np.ndarray, weights: np.ndarray | None = None) -> ig.Graph:
    g = ig.Graph(n=n, edges=[tuple(map(int, e)) for e in edges], directed=False)
    if weights is not None:
        w = np.asarray(weights, dtype=float)
        if np.any(w <= 0):
            raise ValueError("weights must be positive")
        g.es["weight"] = w.tolist()
        g.es["dist"] = (1.0 / w).tolist()
    return g


def _csr(g: ig.Graph):
    n = g.vcount()
    adj = g.get_adjlist()
    ptr = np.zeros(n + 1, dtype=np.int64)
    ptr[1:] = np.cumsum([len(a) for a in adj])
    idx = np.fromiter((v for a in adj for v in a), dtype=np.int64, count=int(ptr[-1]))
    return ptr, idx


@numba.njit(cache=True)
def _stress(ptr, idx, n):
    out = np.zeros(n)
    dist = np.empty(n, dtype=np.int64)
    sigma = np.empty(n)
    below = np.empty(n)
    order = np.empty(n, dtype=np.int64)
    for s in range(n):
        dist[:] = -1
        sigma[:] = 0.0
        dist[s] = 0
        sigma[s] = 1.0
        head = 0
        tail = 1
        order[0] = s
        while head < tail:
            v = order[head]
            head += 1
            for k in range(ptr[v], ptr[v + 1]):
                w = idx[k]
                if dist[w] < 0:
                    dist[w] = dist[v] + 1
                    order[tail] = w
                    tail += 1
                if dist[w] == dist[v] + 1:
                    sigma[w] += sigma[v]
        # below[v]: number of shortest paths from v down the BFS DAG to all later nodes
        below[:] = 0.0
        for q in range(tail - 1, -1, -1):
            v = order[q]
            for k in range(ptr[v], ptr[v + 1]):
                w = idx[k]
                if dist[w] == dist[v] + 1:
                    below[v] += 1.0 + below[w]
            if v != s:
                out[v] += sigma[v] * (below[v])
    # each s-t path through v counted from both ends of the pair? No: for source s we count paths s->t
    # through v for every t, so every unordered pair is counted twice.
    return out / 2.0


def stress_centrality(g: ig.Graph) -> np.ndarray:
    """Number of shortest paths (binary) between other pairs that pass through each node."""
    ptr, idx = _csr(g)
    return _stress(ptr, idx, g.vcount())


def _components(g: ig.Graph):
    return [np.array(c, dtype=np.int64) for c in g.connected_components()]


def information_centrality(g: ig.Graph) -> np.ndarray:
    """Stephenson and Zelen (1989) information centrality, per connected component (binary)."""
    out = np.zeros(g.vcount())
    for comp in _components(g):
        n = len(comp)
        if n < 2:
            continue
        sub = g.induced_subgraph(comp.tolist())
        L = np.array(sub.laplacian(), dtype=float)
        C = np.linalg.inv(L + 1.0)
        T = np.trace(C)
        R = C.sum(axis=1)
        out[comp] = n / (n * np.diag(C) + T - 2.0 * R)
    return out


def _pair_abs_sum(F: np.ndarray) -> np.ndarray:
    """For each row a, sum over i<j of |a_i - a_j|."""
    S = np.sort(F, axis=1)
    n = S.shape[1]
    coef = 2.0 * np.arange(n) - n + 1.0
    return S @ coef


def flow_betweenness(g: ig.Graph, chunk: int = 2048) -> np.ndarray:
    """Current-flow (random-walk) betweenness (Newman 2005; Brandes and Fleischer 2005), binary.

    For each component, the throughput of node v summed over pairs s < t not containing v,
    divided by the number of such pairs, (n - 1)(n - 2) / 2.
    """
    out = np.zeros(g.vcount())
    for comp in _components(g):
        n = len(comp)
        if n < 3:
            continue
        sub = g.induced_subgraph(comp.tolist())
        L = np.array(sub.laplacian(), dtype=float)
        C = np.linalg.pinv(L, hermitian=True)
        E = np.array(sub.get_edgelist(), dtype=np.int64)
        P = np.empty(len(E))
        for a in range(0, len(E), chunk):
            e = E[a:a + chunk]
            P[a:a + chunk] = _pair_abs_sum(C[e[:, 0]] - C[e[:, 1]])
        raw = np.zeros(n)
        np.add.at(raw, E[:, 0], P)
        np.add.at(raw, E[:, 1], P)
        raw = 0.5 * raw - 0.5 * (n - 1)  # remove the pairs with v as an endpoint (throughput 1/2 each)
        out[comp] = raw / ((n - 1) * (n - 2) / 2.0)
    return out


def node_properties(g: ig.Graph, weighted: bool) -> dict[str, np.ndarray]:
    """The 8 node properties of Table 2, weighted (FGN) or all binary."""
    n = g.vcount()
    props: dict[str, np.ndarray] = {}
    if weighted:
        props["degree"] = np.array(g.strength(weights="weight"))
        props["clustering"] = np.nan_to_num(np.array(
            g.transitivity_local_undirected(mode="zero", weights="weight"), dtype=float))
        props["betweenness"] = np.array(g.betweenness(directed=False, weights="dist"))
        props["closeness"] = np.nan_to_num(np.array(g.closeness(weights="dist"), dtype=float))
        props["eigenvector"] = np.array(g.eigenvector_centrality(scale=True, weights="weight"))
    else:
        props["degree"] = np.array(g.degree(), dtype=float) / max(n - 1, 1)
        props["clustering"] = np.nan_to_num(np.array(g.transitivity_local_undirected(mode="zero"), dtype=float))
        props["betweenness"] = np.array(g.betweenness(directed=False))
        props["closeness"] = np.nan_to_num(np.array(g.closeness(), dtype=float))
        props["eigenvector"] = np.array(g.eigenvector_centrality(scale=True))
    props["stress"] = stress_centrality(g)
    props["information"] = information_centrality(g)
    props["flow"] = flow_betweenness(g)
    return props


def shortest_paths(g: ig.Graph, pairs: np.ndarray, weighted: bool) -> np.ndarray:
    """Shortest-path length between the genes of each pair (inf when unreachable)."""
    pairs = np.asarray(pairs, dtype=np.int64)
    out = np.empty(len(pairs))
    w = "dist" if weighted else None
    for src in np.unique(pairs[:, 0]):
        rows = np.where(pairs[:, 0] == src)[0]
        d = g.distances(source=[int(src)], target=pairs[rows, 1].tolist(), weights=w)[0]
        out[rows] = d
    return out


def mutual_neighbors(g: ig.Graph, pairs: np.ndarray) -> np.ndarray:
    nb = [set(a) for a in g.get_adjlist()]
    return np.array([len(nb[int(a)] & nb[int(b)]) for a, b in pairs], dtype=float)


def pair_features(g: ig.Graph, props: dict[str, np.ndarray], pairs: np.ndarray, weighted: bool) -> np.ndarray:
    """The 18 features of each pair, in the order of FEATURE_NAMES.

    An unreachable pair gets a shortest-path length of twice the largest finite length over all pairs.
    """
    pairs = np.asarray(pairs, dtype=np.int64)
    a, b = pairs[:, 0], pairs[:, 1]
    cols = [(props[p][a] + props[p][b]) / 2.0 for p in NODE_PROPERTIES]
    cols += [np.abs(props[p][a] - props[p][b]) for p in NODE_PROPERTIES]
    sp = shortest_paths(g, pairs, weighted)
    finite = np.isfinite(sp)
    if not finite.all():
        sp[~finite] = 2.0 * (sp[finite].max() if finite.any() else 1.0)
    cols.append(sp)
    cols.append(mutual_neighbors(g, pairs))
    return np.column_stack(cols)
