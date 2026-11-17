"""diseasenet: network-based gene-disease association scores and their evaluation.

The methods compared by
Navlakha S, Kingsford C. The power of protein interaction networks for associating genes with
diseases. Bioinformatics 26(8):1057-1063 (2010). doi:10.1093/bioinformatics/btq076

Neighborhood, Oti, random walk with restart (RW), network propagation (Prop) and cluster-based
scores, all leave-one-out, with the paper's precision and recall over linkage-interval candidates
and its two measures of disease homophily.
"""

from importlib import resources
from pathlib import Path

from .core import (
    ALPHA,
    RESTART,
    TOL,
    Candidates,
    Network,
    average_pairwise_distance,
    cluster_scores,
    flow_matrix,
    neighborhood_homophily,
    neighborhood_scores,
    network_from_edges,
    oti_scores,
    per_disease,
    pr_curve,
    precision_recall,
    predictions,
    prop_scores,
    propagate,
    random_walk,
    read_candidates,
    read_network,
    read_scores,
    rw_scores,
    walk_matrix,
)

__version__ = "0.1.0"

CITATION = (
    "Navlakha S, Kingsford C. The power of protein interaction networks for associating genes "
    "with diseases. Bioinformatics 26(8):1057-1063 (2010). doi:10.1093/bioinformatics/btq076"
)

__all__ = [
    "ALPHA",
    "CITATION",
    "RESTART",
    "TOL",
    "Candidates",
    "Network",
    "average_pairwise_distance",
    "cluster_scores",
    "example_path",
    "flow_matrix",
    "neighborhood_homophily",
    "neighborhood_scores",
    "network_from_edges",
    "oti_scores",
    "per_disease",
    "pr_curve",
    "precision_recall",
    "predictions",
    "prop_scores",
    "propagate",
    "random_walk",
    "read_candidates",
    "read_network",
    "read_scores",
    "rw_scores",
    "walk_matrix",
]


def example_path(name: str = "network.tsv") -> Path:
    """Path of a bundled example file. See data/README.md for what each file is."""
    path = resources.files(__name__) / "data" / name
    if not path.is_file():
        raise FileNotFoundError(f"no bundled example file {name!r}")
    return Path(str(path))
