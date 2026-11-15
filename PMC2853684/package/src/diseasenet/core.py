"""Network-based gene-disease association scores and their evaluation.

Methods of Navlakha and Kingsford (2010), as described in the paper and its supplement:

- Neighborhood: A(p, d) is the fraction of p's network neighbours annotated with d.
- Oti: A(p, d) is the number of p's neighbours annotated with d (Oti1, Oti2 and Oti3 predict
  when A >= 1, 2 and 3).
- RW (Kohler et al. 2008): random walk with restart r = 0.75 from the genes of d,
  p(t+1) = (1 - r) W p(t) + r p(0), W the column-normalised adjacency matrix, until the L2
  change is below 1e-6. A(p, d) is the visiting probability of p.
- Prop (Vanunu and Sharan 2008): F(t) = alpha W' F(t-1) + (1 - alpha) Y with
  W'_ij = W_ij / sqrt(D_ii D_jj) and alpha = 0.6, until the L2 change is below 1e-6, then one
  more step with alpha = 1. A(p, d) is the flow at p.
- Clusters (MCL, graph summarization, VI-Cut): A(p, d) is the fraction of the other members of
  p's cluster annotated with d.

Every score is leave-one-out: when p is scored, all of p's own disease associations are
discarded. A pair p-d is predicted when A(p, d) > theta and p lies in a linkage interval of d.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Mapping, Sequence

import numpy as np
import scipy.sparse as sp

RESTART = 0.75
ALPHA = 0.6
TOL = 1e-6


# ----------------------------------------------------------------------------------- input
@dataclass
class Network:
    """An unweighted, undirected protein interaction network.

    `adjacency` is symmetric with 1 for every listed interaction, self-interactions included
    (HPRD lists 1,839 of them); `neighbours` leaves a protein out of its own neighbour set.
    """

    nodes: list[str]
    adjacency: sp.csr_matrix
    index: dict[str, int] = field(default_factory=dict)

    def __post_init__(self):
        if not self.index:
            self.index = {n: i for i, n in enumerate(self.nodes)}
        a = self.adjacency
        self._nbrs = [
            frozenset(int(j) for j in a.indices[a.indptr[i] : a.indptr[i + 1]] if j != i) for i in range(len(self.nodes))
        ]

    def __len__(self) -> int:
        return len(self.nodes)

    @property
    def n_interactions(self) -> int:
        """Number of listed interactions, self-interactions included."""
        return int(sp.triu(self.adjacency).nnz)

    def neighbours(self, i: int) -> frozenset[int]:
        return self._nbrs[i]


def network_from_edges(edges: Iterable[tuple[str, str]], self_loops: bool = False) -> Network:
    """Build a Network from (protein, protein) pairs. Repeated pairs count once.

    With `self_loops`, every protein also interacts with itself. The paper's OPHID scores (RW and
    Prop) were computed that way; its HPRD scores used HPRD's own self-interactions only.
    Neighbourhood, Oti and cluster scores never count a protein as its own neighbour.
    """
    nodes: list[str] = []
    index: dict[str, int] = {}
    rows, cols = [], []
    seen = set()
    for a, b in edges:
        for x in (a, b):
            if x not in index:
                index[x] = len(nodes)
                nodes.append(x)
        i, j = index[a], index[b]
        k = (min(i, j), max(i, j))
        if k in seen:
            continue
        seen.add(k)
        rows.append(i)
        cols.append(j)
        if i != j:
            rows.append(j)
            cols.append(i)
    n = len(nodes)
    if self_loops:
        for i in range(n):
            if (i, i) not in seen:
                rows.append(i)
                cols.append(i)
    adj = sp.csr_matrix((np.ones(len(rows)), (rows, cols)), shape=(n, n))
    return Network(nodes, adj, index)


def read_network(path: str | Path, self_loops: bool = False) -> Network:
    """Read a network file: one interaction per line, two protein names separated by white space.

    `self_loops` adds a self-interaction to every protein (see network_from_edges)."""
    edges = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            parts = line.split()
            if len(parts) >= 2:
                edges.append((parts[0], parts[1]))
    return network_from_edges(edges, self_loops)


@dataclass
class Candidates:
    """Gene-disease pairs to score: every gene in a linkage interval of each disease.

    `known` marks the pairs where the gene is known to be associated with the disease.
    """

    genes: list[str]
    diseases: list[str]
    known: np.ndarray

    def __len__(self) -> int:
        return len(self.genes)

    def annotations(self) -> dict[str, set[str]]:
        """Disease -> its known genes."""
        out: dict[str, set[str]] = defaultdict(set)
        for g, d, k in zip(self.genes, self.diseases, self.known):
            if k:
                out[d].add(g)
        return dict(out)


def read_candidates(path: str | Path) -> Candidates:
    """Read candidate pairs.

    Accepts the DiseaseNet prediction-file layout of the paper's web site (six tab-separated
    columns: method, gene, disease, gene, CORRECT or INCORRECT, score) or a CSV with columns
    gene, disease, known (1 or 0).
    """
    genes, diseases, known = [], [], []
    with open(path, encoding="utf-8", newline="") as f:
        first = f.readline()
        f.seek(0)
        if first.count("\t") >= 4:
            for line in f:
                parts = line.rstrip("\n").split("\t")
                if len(parts) < 5:
                    continue
                genes.append(parts[1])
                diseases.append(parts[2])
                known.append(parts[4] == "CORRECT")
        else:
            for row in csv.DictReader(f):
                genes.append(row["gene"])
                diseases.append(row["disease"])
                known.append(str(row["known"]).strip() in ("1", "True", "true", "yes"))
    return Candidates(genes, diseases, np.array(known, dtype=bool))


def read_scores(path: str | Path) -> dict[str, dict[tuple[str, str], float]]:
    """Read a DiseaseNet prediction file: {method: {(gene, disease): score}}."""
    out: dict[str, dict[tuple[str, str], float]] = defaultdict(dict)
    with open(path, encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 6:
                out[parts[0]][(parts[1], parts[2])] = float(parts[5])
    return dict(out)


# ------------------------------------------------------------------------------ the methods
def _seed_sets(net: Network, annotations: Mapping[str, set[str]]) -> dict[str, frozenset[int]]:
    return {d: frozenset(net.index[g] for g in gs if g in net.index) for d, gs in annotations.items()}


def neighborhood_scores(net: Network, annotations: Mapping[str, set[str]], cands: Candidates) -> np.ndarray:
    """Fraction of each candidate gene's neighbours annotated with the disease (leave-one-out)."""
    seeds = _seed_sets(net, annotations)
    out = np.zeros(len(cands))
    for k, (g, d) in enumerate(zip(cands.genes, cands.diseases)):
        i = net.index.get(g)
        if i is None:
            continue
        nb = net.neighbours(i)
        if nb:
            out[k] = len(nb & (seeds.get(d, frozenset()) - {i})) / len(nb)
    return out


def oti_scores(net: Network, annotations: Mapping[str, set[str]], cands: Candidates) -> np.ndarray:
    """Number of each candidate gene's neighbours annotated with the disease (leave-one-out)."""
    seeds = _seed_sets(net, annotations)
    out = np.zeros(len(cands))
    for k, (g, d) in enumerate(zip(cands.genes, cands.diseases)):
        i = net.index.get(g)
        if i is not None:
            out[k] = len(net.neighbours(i) & (seeds.get(d, frozenset()) - {i}))
    return out


def walk_matrix(net: Network) -> sp.csr_matrix:
    """Column-normalised adjacency matrix W (W_ij = A_ij / deg_j); a self-interaction counts once."""
    deg = np.asarray(net.adjacency.sum(axis=0)).ravel()
    deg[deg == 0] = 1.0
    return (net.adjacency @ sp.diags(1.0 / deg)).tocsr()


def flow_matrix(net: Network) -> sp.csr_matrix:
    """W'_ij = A_ij / sqrt(D_ii D_jj), D the row sums of the adjacency matrix."""
    deg = np.asarray(net.adjacency.sum(axis=1)).ravel()
    deg[deg == 0] = 1.0
    s = sp.diags(1.0 / np.sqrt(deg))
    return (s @ net.adjacency @ s).tocsr()


def random_walk(w: sp.csr_matrix, seeds: Sequence[int], restart: float = RESTART, tol: float = TOL) -> np.ndarray:
    """Random walk with restart from `seeds` (equal start probability) until the L2 change < tol."""
    n = w.shape[0]
    p0 = np.zeros(n)
    if len(seeds) == 0:
        return p0
    p0[list(seeds)] = 1.0 / len(seeds)
    p = p0.copy()
    while True:
        q = (1.0 - restart) * (w @ p) + restart * p0
        if np.linalg.norm(q - p) < tol:
            return q
        p = q


def propagate(w: sp.csr_matrix, seeds: Sequence[int], alpha: float = ALPHA, tol: float = TOL) -> np.ndarray:
    """Network propagation from `seeds` (prior 1 on each), then one smoothing step with alpha = 1.

    The flow starts at zero: F(0) = 0. Starting it at the prior Y instead changes the scores by a
    median 8e-5 (relative) and does not reproduce the paper's prediction files.
    """
    n = w.shape[0]
    y = np.zeros(n)
    if len(seeds) == 0:
        return y
    y[list(seeds)] = 1.0
    f = np.zeros(n)
    while True:
        g = alpha * (w @ f) + (1.0 - alpha) * y
        if np.linalg.norm(g - f) < tol:
            return w @ g
        f = g


def _diffusion_scores(net, annotations, cands, run, w) -> np.ndarray:
    seeds = _seed_sets(net, annotations)
    by_disease: dict[str, list[int]] = defaultdict(list)
    for k, d in enumerate(cands.diseases):
        by_disease[d].append(k)
    out = np.zeros(len(cands))
    for d, ks in by_disease.items():
        s = seeds.get(d, frozenset())
        base = None
        for k in ks:
            i = net.index.get(cands.genes[k])
            if i is None:
                continue
            if i in s:  # leave-one-out: run again without p's own association
                out[k] = run(w, sorted(s - {i}))[i]
            else:
                if base is None:
                    base = run(w, sorted(s))
                out[k] = base[i]
    return out


def rw_scores(net: Network, annotations, cands: Candidates, restart: float = RESTART, tol: float = TOL) -> np.ndarray:
    """RW visiting probability of each candidate gene for its disease (leave-one-out)."""
    return _diffusion_scores(net, annotations, cands, lambda w, s: random_walk(w, s, restart, tol), walk_matrix(net))


def prop_scores(net: Network, annotations, cands: Candidates, alpha: float = ALPHA, tol: float = TOL) -> np.ndarray:
    """Prop flow at each candidate gene for its disease (leave-one-out)."""
    return _diffusion_scores(net, annotations, cands, lambda w, s: propagate(w, s, alpha, tol), flow_matrix(net))


def cluster_scores(clusters: Iterable[Iterable[str]], annotations, cands: Candidates) -> np.ndarray:
    """Fraction of the other members of the gene's cluster annotated with the disease.

    A gene in no cluster, or alone in its cluster, scores 0.
    """
    member: dict[str, int] = {}
    groups: list[list[str]] = []
    for c in clusters:
        c = list(c)
        for g in c:
            member[g] = len(groups)
        groups.append(c)
    out = np.zeros(len(cands))
    for k, (g, d) in enumerate(zip(cands.genes, cands.diseases)):
        c = member.get(g)
        if c is None:
            continue
        others = [x for x in groups[c] if x != g]
        if others:
            known = annotations.get(d, set())
            out[k] = sum(1 for x in others if x in known) / len(others)
    return out


# ------------------------------------------------------------------------------- evaluation
def predictions(scores: np.ndarray, theta: float) -> np.ndarray:
    """A pair is predicted when its score is strictly greater than theta."""
    return np.asarray(scores) > theta


def precision_recall(predicted: np.ndarray, known: np.ndarray, n_known: int | None = None) -> tuple[float, float, int]:
    """(precision, recall, number of predictions), precision and recall in percent.

    Recall is over all known pairs (`n_known`, by default the known pairs among the candidates).
    """
    predicted = np.asarray(predicted, dtype=bool)
    known = np.asarray(known, dtype=bool)
    tp = int((predicted & known).sum())
    n = int(predicted.sum())
    nk = int(known.sum()) if n_known is None else n_known
    precision = 100.0 * tp / n if n else float("nan")
    recall = 100.0 * tp / nk if nk else float("nan")
    return precision, recall, n


def pr_curve(scores: np.ndarray, known: np.ndarray, thetas: Sequence[float]) -> list[dict]:
    """Precision and recall (percent) at each threshold, in the order given."""
    out = []
    for t in thetas:
        p, r, n = precision_recall(predictions(scores, t), known)
        out.append({"theta": float(t), "precision": p, "recall": r, "n": n})
    return out


def per_disease(predicted: np.ndarray, cands: Candidates) -> dict[str, dict]:
    """Per-disease precision, recall and F1 (fractions; precision None when nothing is predicted)."""
    tp: dict[str, int] = defaultdict(int)
    npred: dict[str, int] = defaultdict(int)
    nknown: dict[str, int] = defaultdict(int)
    for p, k, d in zip(predicted, cands.known, cands.diseases):
        nknown[d] += int(k)
        npred[d] += int(p)
        tp[d] += int(p and k)
    out = {}
    for d in nknown:
        prec = tp[d] / npred[d] if npred[d] else None
        rec = tp[d] / nknown[d] if nknown[d] else None
        f1 = 2 * prec * rec / (prec + rec) if prec and rec else 0.0
        out[d] = {"tp": tp[d], "predicted": npred[d], "known": nknown[d], "precision": prec, "recall": rec, "f1": f1}
    return out


# --------------------------------------------------------------------------------- homophily
def neighborhood_homophily(net: Network, genes: Iterable[str]) -> float | None:
    """Mean, over the disease's genes in the network, of the fraction of each gene's neighbours
    that are also genes of the disease. None when no gene of the disease has a neighbour."""
    s = {net.index[g] for g in genes if g in net.index}
    vals = []
    for i in s:
        nb = net.neighbours(i)
        if nb:
            vals.append(len(nb & (s - {i})) / len(nb))
    return float(np.mean(vals)) if vals else None


def average_pairwise_distance(net: Network, genes: Iterable[str]) -> float | None:
    """Mean shortest-path length (number of interactions) over the connected pairs of the
    disease's genes. None for fewer than two genes or no connected pair."""
    from scipy.sparse.csgraph import shortest_path

    s = sorted({net.index[g] for g in genes if g in net.index})
    if len(s) < 2:
        return None
    d = shortest_path(net.adjacency, unweighted=True, directed=False, indices=s)[:, s]
    vals = d[np.triu_indices(len(s), 1)]
    vals = vals[np.isfinite(vals)]
    return float(vals.mean()) if len(vals) else None
