"""fgnssl: synthetic genetic interaction prediction from a weighted functional gene network.

A Python implementation, from the paper's text, of
You ZH, Yin Z, Han K, Huang DS, Zhou X. A semi-supervised learning approach to predict synthetic
genetic interactions by combining functional and topological properties of functional gene network.
BMC Bioinformatics 11:343 (2010). doi:10.1186/1471-2105-11-343

The authors' code (GeneticInterPred) is lost. This package rebuilds the method: divisive correlation
clustering of expression profiles, the eq. 2 edge weights, the 10 network properties of Table 2 and
the 18 pair features built from them, and the graph-based semi-supervised classifier (label spreading,
Zhou et al. 2004).
"""

from importlib import resources
from pathlib import Path

from .classify import auc, roc_curve, scale_features
from .core import FGN, build_fgn, node_properties, pair_features, predict
from .fgn import L1_DEFAULT, dcca, edge_weights
from .io import read_edges, read_expression, read_pairs, read_table, write_table
from .network import FEATURE_NAMES, NODE_PROPERTIES
from .ssl import label_spreading, select_sigma

__version__ = "0.1.0"

__all__ = [
    "FEATURE_NAMES", "FGN", "L1_DEFAULT", "NODE_PROPERTIES", "auc", "build_fgn", "dcca", "edge_weights",
    "example_path", "label_spreading", "node_properties", "pair_features", "predict", "read_edges",
    "read_expression", "read_pairs", "read_table", "roc_curve", "scale_features", "select_sigma", "write_table",
]


def example_path(name: str = "expression.csv") -> Path:
    """Path of a bundled example file. See data/README.md for what each file is."""
    path = resources.files(__name__) / "data" / name
    if not path.is_file():
        raise FileNotFoundError(f"no bundled example file {name!r}")
    return Path(str(path))
