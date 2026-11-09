"""blmdti: bipartite local models for drug-target interaction prediction.

The method comes from:

> Bleakley K, Yamanishi Y. Supervised prediction of drug-target interactions using bipartite
> local models. *Bioinformatics* 25(18):2397-2403 (2009). doi:10.1093/bioinformatics/btp433

Its reproduction (pipeline, scores against the published tables and figures) is in the fossil
repository at PMC2735674.
"""

from importlib import resources
from pathlib import Path

from .core import (
    KRM_RCOND,
    NO_POSITIVE_RULES,
    aggregate,
    auc,
    aupr,
    blm_drug_scores,
    blm_target_scores,
    interactions,
    krm_drug_scores,
    krm_target_scores,
    make_psd,
    nn_drug_scores,
    nn_target_scores,
    pharmacological_space,
    precision_recall,
    read_matrix,
    read_network,
    scores_table,
    shortest_paths,
    write_matrix,
)

__version__ = "0.1.0"

CITATION = (
    "Bleakley K, Yamanishi Y. Supervised prediction of drug-target interactions using "
    "bipartite local models. Bioinformatics 25(18):2397-2403 (2009). "
    "doi:10.1093/bioinformatics/btp433"
)

__all__ = [
    "CITATION",
    "KRM_RCOND",
    "NO_POSITIVE_RULES",
    "aggregate",
    "auc",
    "aupr",
    "blm_drug_scores",
    "blm_target_scores",
    "example_path",
    "interactions",
    "krm_drug_scores",
    "krm_target_scores",
    "make_psd",
    "nn_drug_scores",
    "nn_target_scores",
    "pharmacological_space",
    "precision_recall",
    "read_matrix",
    "read_network",
    "scores_table",
    "shortest_paths",
    "write_matrix",
]


def example_path(name: str = "example_admat.txt") -> Path:
    """Path of a bundled example file. See data/README.md for what each file is."""
    path = resources.files(__name__) / "data" / name
    if not path.is_file():
        raise FileNotFoundError(f"no bundled example file {name!r}")
    return Path(str(path))
