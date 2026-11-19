"""gecon: signed gene co-expression networks from local expression patterns (GeCON).

Implemented from the text of:
Roy S, Bhattacharyya DK, Kalita JK. Reconstruction of gene co-expression network from microarray data
using local expression patterns. BMC Bioinformatics 15(Suppl 7):S10 (2014). doi:10.1186/1471-2105-15-S7-S10

The authors' Java program is lost; this is a reimplementation from the paper's Eqs. (4) to (11).
"""

from importlib import resources
from pathlib import Path

from .core import (
    DEFAULT_TAU,
    DEFAULT_THETA,
    Supports,
    edge_list,
    edge_patterns,
    gecon,
    modules,
    network,
    read_edges,
    read_matrix,
    supports,
    write_edges,
)
from .evaluate import aupr, auroc, fbeta, max_fbeta, score_network

__version__ = "0.1.0"

CITATION = (
    "Roy S, Bhattacharyya DK, Kalita JK. Reconstruction of gene co-expression network from microarray data "
    "using local expression patterns. BMC Bioinformatics 15(Suppl 7):S10 (2014). doi:10.1186/1471-2105-15-S7-S10"
)

__all__ = [
    "CITATION", "DEFAULT_TAU", "DEFAULT_THETA", "Supports", "aupr", "auroc", "edge_list", "edge_patterns",
    "example_path", "fbeta", "gecon", "max_fbeta", "modules", "network", "read_edges", "read_matrix",
    "score_network", "supports", "write_edges",
]


def example_path(name: str = "yeast_ybl.tsv") -> Path:
    """Path of a bundled example file. See data/README.md for what each file is."""
    path = resources.files(__name__) / "data" / name
    if not path.is_file():
        raise FileNotFoundError(f"no bundled example file {name!r}")
    return Path(str(path))
