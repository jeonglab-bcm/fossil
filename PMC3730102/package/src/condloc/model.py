"""CoLP end to end: feature sets, DC-kNN training with leave-two-out selection, and conditional location maps.

The objects here hold plain numpy arrays and take plain inputs (lists of accessions,
sequences, interaction pairs and expression matrices), so they run on any proteome.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

import numpy as np
from scipy import sparse

from .coherence import coherence as link_phi, fill_missing
from . import dcknn, features, network

LOCATIONS = ["AT", "CC", "CT", "CY", "ER", "GL", "LS", "MT", "NO", "NU", "PX", "PM", "VU"]


@dataclass
class Proteome:
    """Proteins, their S features, known locations and the interaction network."""

    accessions: list[str]
    labels: np.ndarray            # (n, L) bool; all False where the location is unknown
    s: dict[str, np.ndarray]      # S feature sets, one row per protein
    adj: sparse.csr_matrix        # symmetric 0/1 adjacency
    edges: np.ndarray             # (m, 2) node indices of the links, a < b
    locations: list[str] = field(default_factory=lambda: list(LOCATIONS))

    @classmethod
    def build(cls, accessions: Sequence[str], sequences: Sequence[str], motifs: Sequence[Sequence[str]],
              go_terms: Sequence[Sequence[str]], locations: Sequence[Sequence[str]],
              links: Sequence[tuple[str, str]], location_names: Sequence[str] = LOCATIONS) -> "Proteome":
        acc = list(accessions)
        idx = {a: i for i, a in enumerate(acc)}
        lab = np.zeros((len(acc), len(location_names)), dtype=bool)
        li = {name: j for j, name in enumerate(location_names)}
        for i, ls in enumerate(locations):
            for name in ls:
                lab[i, li[name]] = True
        known = lab.any(axis=1)
        motif_vocab = sorted({m for i, ms in enumerate(motifs) if known[i] for m in ms})
        go_vocab = sorted({t for i, ts in enumerate(go_terms) if known[i] for t in ts})
        s = features.single_features(sequences, motifs, go_terms, motif_vocab, go_vocab)
        e = np.array(sorted({tuple(sorted((idx[a], idx[b]))) for a, b in links
                             if a in idx and b in idx and a != b}), dtype=np.int64).reshape(-1, 2)
        adj = network.adjacency(len(acc), e)
        return cls(acc, lab, s, adj, e, list(location_names))

    @property
    def known(self) -> np.ndarray:
        return self.labels.any(axis=1)

    def masks(self) -> np.ndarray:
        return network.location_masks([np.flatnonzero(r) for r in self.labels], self.labels.shape[1])


def network_sets(p: Proteome, adj: sparse.csr_matrix | None = None, link_weight: sparse.csr_matrix | None = None,
                 rho: float = network.RHO_HUMAN, prefix: str = "", plcp_adj: sparse.csr_matrix | None = None
                 ) -> dict[str, np.ndarray]:
    """N1_X, N2_X for every S set X, and L1, L2, on the given network (default: the proteome's)."""
    a = p.adj if adj is None else adj
    masks = p.masks()
    pl = network.plcp(p.adj if plcp_adj is None else plcp_adj, p.labels)
    out = {}
    for d in (1, 2):
        w = network.neighbourhood_weights(a, masks, d, rho, link_weight)
        for name, x in p.s.items():
            out[f"{prefix}N{d}_{name}"] = network.n_features(w, x)
        out[f"{prefix}L{d}"] = network.l_features(w, p.labels, pl)
    return out


def knn_counts(sets: Mapping[str, np.ndarray], p: Proteome, query: np.ndarray | None = None,
               train: np.ndarray | None = None, k: int = dcknn.K) -> dict[str, np.ndarray]:
    """n_ml for the query proteins (default: all) against the training proteins (default: known ones)."""
    train = np.flatnonzero(p.known) if train is None else train
    query = np.arange(len(p.accessions)) if query is None else query
    pos = np.full(len(p.accessions), -1)
    pos[train] = np.arange(len(train))
    out = {}
    for name, x in sets.items():
        nb = dcknn.neighbours(x[query], x[train], k, self_index=pos[query])
        out[name] = dcknn.label_counts(nb, p.labels[train])
    return out


@dataclass
class Model:
    """Selected feature sets and their weights for each location."""

    selected: dict[int, list[str]]
    weights: dict[int, dict[str, float]]
    k: int = dcknn.K

    def confidence(self, counts: Mapping[str, np.ndarray]) -> np.ndarray:
        n = next(iter(counts.values())).shape[0]
        out = np.zeros((n, len(self.selected)))
        for loc, sel in self.selected.items():
            out[:, loc] = dcknn.confidence(counts, sel, self.weights[loc], loc, self.k)
        return out


def train(counts: Mapping[str, np.ndarray], labels: np.ndarray, rows: np.ndarray, candidates: Sequence[str],
          k: int = dcknn.K) -> tuple[Model, dict[int, list[float]]]:
    """Forward selection for every location on the given rows of the gold standard."""
    sel, wts, paths = {}, {}, {}
    for loc in range(labels.shape[1]):
        s, single, path = dcknn.forward_select(counts, labels, loc, rows, list(candidates), k)
        sel[loc], wts[loc], paths[loc] = s, single, path
    return Model(sel, wts, k), paths


def leave_two_out(counts: Mapping[str, np.ndarray], labels: np.ndarray, candidates: Sequence[str], seed: int,
                  k: int = dcknn.K) -> dict:
    """Leave-two-out evaluation: the gold standard is split in two halves at random; feature sets are chosen
    on one half and the AUC is reported on the other, both ways round. Every protein is scored by
    neighbours that never include itself. Returns per-location AUCs (mean of the two directions) and the
    pooled report-half confidences for drawing ROC curves."""
    n = labels.shape[0]
    rng = np.random.default_rng(seed)
    half = rng.permutation(n) < n // 2
    a, b = np.flatnonzero(half), np.flatnonzero(~half)
    aucs = np.zeros((2, labels.shape[1]))
    conf = np.zeros(labels.shape)
    for j, (sel_rows, rep_rows) in enumerate(((a, b), (b, a))):
        model, _ = train(counts, labels, sel_rows, candidates, k)
        c = model.confidence({m: v[rep_rows] for m, v in counts.items()})
        conf[rep_rows] = c
        for loc in range(labels.shape[1]):
            aucs[j, loc] = dcknn.auc(c[:, loc], labels[rep_rows, loc])
    return {"auc": aucs.mean(axis=0), "auc_by_half": aucs, "confidence": conf}


def condition_link_weights(p: Proteome, studies: Sequence[tuple[Sequence[str], np.ndarray]]) -> np.ndarray:
    """Coherence of every link under one condition: Phi per study (missing values filled), averaged over the
    studies with weights equal to their sample counts, then divided by its median so a typical link weighs 1."""
    pairs = [(p.accessions[i], p.accessions[j]) for i, j in p.edges]
    tot = np.zeros(len(pairs))
    wsum = 0.0
    for genes, x in studies:
        phi = fill_missing(link_phi(x, list(genes), pairs), pairs)
        tot += phi * x.shape[1]
        wsum += x.shape[1]
    phi = tot / wsum
    med = np.median(phi[phi > 0]) if (phi > 0).any() else 1.0
    return phi / med


def weighted_adjacency(p: Proteome, link_weight: np.ndarray) -> sparse.csr_matrix:
    a = network.adjacency(len(p.accessions), p.edges, np.maximum(link_weight, 1e-9))
    a.sort_indices()
    return a


def possibility_map(conf: np.ndarray, gold_conf: np.ndarray, gold_labels: np.ndarray) -> np.ndarray:
    """Degrees of possibility for every protein and location from the gold standard's own confidences."""
    out = np.zeros_like(conf)
    for loc in range(conf.shape[1]):
        y = gold_labels[:, loc]
        out[:, loc] = dcknn.possibility(conf[:, loc], gold_conf[y, loc], gold_conf[~y, loc])
    return out
