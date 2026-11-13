"""The method end to end: expression and interactions in, pair features and SGI scores out."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import classify, fgn, network, ssl


@dataclass
class FGN:
    """A functional gene network: genes, edges (index pairs), eq. 2 weights and expression clusters."""
    genes: list
    edges: np.ndarray
    weights: np.ndarray
    clusters: np.ndarray

    @property
    def index(self):
        return {g: i for i, g in enumerate(self.genes)}


def build_fgn(genes, X, interactions, l1: float = fgn.L1_DEFAULT) -> FGN:
    """Cluster the expression profiles (DCCA) and weight each interaction by eq. 2.

    genes: names of the rows of X. X: genes x conditions (NaN = missing, replaced by the condition mean).
    interactions: (gene_a, gene_b) pairs, e.g. protein interactions plus complex co-memberships.
    Interactions with a gene that has no expression row are dropped.
    """
    genes = list(genes)
    X = fgn.impute_column_means(X)
    idx = {g: i for i, g in enumerate(genes)}
    E = sorted({tuple(sorted((idx[a], idx[b]))) for a, b in interactions if a in idx and b in idx and a != b})
    if not E:
        raise ValueError("no interaction joins two genes of the expression table")
    E = np.array(E, dtype=np.int64)
    labels = fgn.dcca(X)
    w = fgn.edge_weights(X, labels, E, l1=l1)
    return FGN(genes, E, w, labels)


def node_properties(net: FGN, weighted: bool = True) -> dict:
    g = network.make_graph(len(net.genes), net.edges, net.weights if weighted else None)
    return network.node_properties(g, weighted)


def pair_features(net: FGN, pairs, weighted: bool = True, props: dict | None = None) -> np.ndarray:
    """The 18 features (network.FEATURE_NAMES) of each (gene_a, gene_b) pair."""
    idx = net.index
    missing = [p for p in pairs if p[0] not in idx or p[1] not in idx]
    if missing:
        raise KeyError(f"genes not in the network: {missing[:3]}")
    P = np.array([(idx[a], idx[b]) for a, b in pairs], dtype=np.int64)
    g = network.make_graph(len(net.genes), net.edges, net.weights if weighted else None)
    props = network.node_properties(g, weighted) if props is None else props
    return network.pair_features(g, props, P, weighted)


def predict(features, labels, sigma: float | None = None, alpha: float = ssl.ALPHA_DEFAULT,
            select: bool = False, seed: int = 0) -> np.ndarray:
    """Soft SGI labels in [0, 1] for every pair by label spreading on the scaled features.

    labels: 1 (SGI), 0 (non-SGI) or -1 (unlabelled). With select=True, sigma is chosen on the labels.
    """
    X = classify.scale_features(features)
    y = np.asarray(labels)
    if select and sigma is None:
        sigma = ssl.select_sigma(X, y, alpha=alpha, seed=seed)
    return ssl.label_spreading(X, y, sigma=sigma, alpha=alpha)
