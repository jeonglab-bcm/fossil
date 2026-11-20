"""geodenoise: geometric de-noising of protein-protein interaction networks.

Embeds a network in low-dimensional Euclidean space by multidimensional scaling of shortest-path
lengths, then predicts missing interactions (non-edges that lie close together) and flags
doubtful ones (edges that lie far apart), with confidence scores from Gaussian-mixture densities.

Kuchaiev O, Rasajski M, Higham DJ, Przulj N. Geometric de-noising of protein-protein interaction
networks. PLoS Comput Biol 5(8):e1000454 (2009). doi:10.1371/journal.pcbi.1000454
"""

from importlib import resources
from pathlib import Path

from .core import (
    DELTA,
    EM_STOP,
    LEARN_SET_SIZE,
    MAX_PATH,
    N_COMPONENTS,
    PRIOR_EDGE,
    UNREACHABLE,
    Mixture,
    Network,
    auc,
    candidate_false_positives,
    confidence_scores,
    embed,
    fit_mixture,
    largest_component,
    learn_densities,
    network_from_edges,
    pairwise_distances,
    path_lengths,
    predict,
    read_network,
    read_scores,
    roc_curve,
    write_scores,
)

__version__ = "0.1.0"

CITATION = (
    "Kuchaiev O, Rasajski M, Higham DJ, Przulj N. Geometric de-noising of protein-protein "
    "interaction networks. PLoS Comput Biol 5(8):e1000454 (2009). doi:10.1371/journal.pcbi.1000454"
)

__all__ = [
    "CITATION", "DELTA", "EM_STOP", "LEARN_SET_SIZE", "MAX_PATH", "N_COMPONENTS", "PRIOR_EDGE",
    "UNREACHABLE", "Mixture", "Network", "auc", "candidate_false_positives", "confidence_scores",
    "embed", "example_path", "fit_mixture", "largest_component", "learn_densities",
    "network_from_edges", "pairwise_distances", "path_lengths", "predict", "read_network",
    "read_scores", "roc_curve", "write_scores",
]


def example_path(name: str = "geometric_network.tsv") -> Path:
    """Path of a bundled example file. See data/README.md for what each file is."""
    path = resources.files(__name__) / "data" / name
    if not path.is_file():
        raise FileNotFoundError(f"no bundled example file {name!r}")
    return Path(str(path))
