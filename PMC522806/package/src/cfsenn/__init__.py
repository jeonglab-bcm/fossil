"""cfsenn: combinational feature selection and ensemble neural networks for expression data.

A Python implementation, from the paper's text, of
Liu B, Cui Q, Jiang T, Ma S. A combinational feature selection and ensemble neural network method
for classification of gene expression data. BMC Bioinformatics 5:136 (2004).
doi:10.1186/1471-2105-5-136

The authors' Matlab code was never released. Settings the paper does not state are keyword
arguments of ``Ensemble``; their defaults are in ``DEFAULTS`` and the README.
"""

from importlib import resources
from pathlib import Path

from .core import (
    DEFAULTS,
    FEATURE_SETS,
    Ensemble,
    Net,
    accuracy,
    cross_validate,
    masked_cluster_genes,
    ranksum_scores,
    read_dbc,
    read_table,
    run,
    stratified_folds,
    t_scores,
    to_json,
)

__version__ = "0.1.0"

CITATION = (
    "Liu B, Cui Q, Jiang T, Ma S. A combinational feature selection and ensemble neural network "
    "method for classification of gene expression data. BMC Bioinformatics 5:136 (2004). "
    "doi:10.1186/1471-2105-5-136"
)

__all__ = [
    "CITATION",
    "DEFAULTS",
    "FEATURE_SETS",
    "Ensemble",
    "Net",
    "accuracy",
    "cross_validate",
    "example_path",
    "masked_cluster_genes",
    "ranksum_scores",
    "read_dbc",
    "read_table",
    "run",
    "stratified_folds",
    "t_scores",
    "to_json",
]


def example_path(name: str = "example_train.csv") -> Path:
    """Path of a bundled example file. See data/README.md for what each file is."""
    path = resources.files(__name__) / "data" / name
    if not path.is_file():
        raise FileNotFoundError(f"no bundled example file {name!r}")
    return Path(str(path))
