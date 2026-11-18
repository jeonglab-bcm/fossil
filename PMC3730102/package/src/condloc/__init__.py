"""condloc: conditional protein location maps (CoLP).

Rebuilt from the text of
Lee K, Byun K, Hong W, Chuang HY, Pack CG, Bayarsaikhan E, et al. Proteome-wide discovery of mislocated
proteins in cancer. Genome Research 23(8):1283-1294 (2013). doi:10.1101/gr.155499.113
and of the DC-kNN method it reuses:
Lee K, Chuang HY, Beyer A, Sung MK, Huh WK, Lee B, Ideker T. Protein networks markedly improve prediction
of subcellular localization in multiple eukaryotic species. Nucleic Acids Research 36:e136 (2008).
doi:10.1093/nar/gkn619

The authors' CoLP server is gone and its code was never released; this package implements the method
from the two papers' text and equations.
"""

from __future__ import annotations

import csv
from importlib import resources
from pathlib import Path

from .coherence import coherence, fill_missing, knn_impute, quantile_normalize
from .dcknn import auc, forward_select, neighbours, null_threshold, possibility, roc_curve
from .features import S_SETS, single_features
from .model import (LOCATIONS, Model, Proteome, condition_link_weights, knn_counts, leave_two_out,
                    network_sets, possibility_map, train, weighted_adjacency)
from .network import RHO_HUMAN, adjacency, l_features, location_masks, n_features, neighbourhood_weights, plcp

__version__ = "0.1.0"

__all__ = [
    "LOCATIONS", "Model", "Proteome", "RHO_HUMAN", "S_SETS", "adjacency", "auc", "coherence",
    "condition_link_weights", "example_path", "fill_missing", "forward_select", "knn_counts", "knn_impute",
    "l_features", "leave_two_out", "link_coherence", "location_masks", "n_features", "neighbourhood_weights",
    "neighbours", "network_sets", "null_threshold", "plcp", "possibility", "possibility_map",
    "quantile_normalize", "read_expression", "read_links", "roc_curve", "single_features", "train",
    "weighted_adjacency",
]


def example_path(name: str = "example_expression.tsv") -> Path:
    """Path of a bundled example file. See data/README.md for what each file is."""
    path = resources.files(__name__) / "data" / name
    if not path.is_file():
        raise FileNotFoundError(f"no bundled example file {name!r}")
    return Path(str(path))


def read_expression(path) -> tuple[list[str], "list[list[float]]"]:
    """A tab-separated table: first column the protein, then one column per sample."""
    import numpy as np

    genes, rows = [], []
    with open(path, newline="") as h:
        r = csv.reader(h, delimiter="\t")
        next(r)
        for row in r:
            if row:
                genes.append(row[0])
                rows.append([float(x) for x in row[1:]])
    return genes, np.array(rows)


def read_links(path) -> list[tuple[str, str]]:
    """A tab-separated table of interacting pairs with a header line."""
    with open(path, newline="") as h:
        r = csv.reader(h, delimiter="\t")
        next(r)
        return [(row[0], row[1]) for row in r if row]


def link_coherence(expression_path, links_path) -> list[tuple[str, str, float]]:
    """Expression coherence of every link in one study (missing values filled as in the paper)."""
    genes, x = read_expression(expression_path)
    links = read_links(links_path)
    phi = fill_missing(coherence(x, genes, links), links)
    return [(a, b, float(p)) for (a, b), p in zip(links, phi)]
