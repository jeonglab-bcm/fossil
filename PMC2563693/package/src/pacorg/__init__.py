"""pacorg: pathway activity inference with condition-responsive genes (CORGs).

A re-implementation, from the paper's text, of the PAC method of
Lee E, Chuang HY, Kim JW, Ideker T, Lee D. Inferring pathway activity toward precise disease
classification. PLoS Computational Biology 4(11):e1000217 (2008). doi:10.1371/journal.pcbi.1000217
"""

from importlib import resources
from pathlib import Path

from .core import (
    PathwayResult,
    activity,
    auc,
    find_corgs,
    fit_logistic,
    infer_pathways,
    mean_activity,
    median_activity,
    pca_activity,
    predict_logistic,
    read_cls,
    read_gct,
    read_gmt,
    read_results,
    sequential_selection,
    t_pvalues,
    t_scores,
    tian_scores,
    write_results,
    zscore,
)

__version__ = "0.1.0"

CITATION = (
    "Lee E, Chuang HY, Kim JW, Ideker T, Lee D. Inferring pathway activity toward precise disease "
    "classification. PLoS Comput Biol 4(11):e1000217 (2008). doi:10.1371/journal.pcbi.1000217"
)

__all__ = [
    "CITATION",
    "PathwayResult",
    "activity",
    "auc",
    "example_path",
    "find_corgs",
    "fit_logistic",
    "infer_pathways",
    "mean_activity",
    "median_activity",
    "pca_activity",
    "predict_logistic",
    "read_cls",
    "read_gct",
    "read_gmt",
    "read_results",
    "sequential_selection",
    "t_pvalues",
    "t_scores",
    "tian_scores",
    "write_results",
    "zscore",
]


def example_path(name: str) -> Path:
    """Path of a bundled example file. See data/README.md for what each file is."""
    path = resources.files(__name__) / "data" / name
    if not path.is_file():
        raise FileNotFoundError(f"no bundled example file {name!r}")
    return Path(str(path))
