"""mutbench: benchmark mutation effect predictors against functionally validated mutations.

The method of Martelotto LG, Ng CKY, De Filippo MR, et al. Benchmarking mutation effect prediction
algorithms using functionally validated cancer-related missense mutations. Genome Biology 15:484 (2014).
doi:10.1186/s13059-014-0484-1. Implemented from the paper's text; the authors' code was not released.
"""

from importlib import resources
from pathlib import Path

from .core import (
    LOW_CONFIDENCE_SCORE,
    MUTATIONTASTER_LOW,
    STATS,
    binary_call,
    binary_calls,
    bootstrap_ci,
    ci_better,
    clades,
    cohen_kappa,
    combination_calls,
    combination_name,
    combinations,
    evaluate,
    hamming_matrix,
    hclust_complete,
    kappa_categorical,
    kappa_matrix,
    label_vector,
    landis_koch,
    leaf_order,
    low_confidence,
    performance,
    random_splits,
    rank,
    read_calls_csv,
    recurrence,
    split_sample,
    write_rows,
)

__version__ = "0.1.0"

CITATION = (
    "Martelotto LG, Ng CKY, De Filippo MR, et al. Benchmarking mutation effect prediction algorithms "
    "using functionally validated cancer-related missense mutations. Genome Biology 15:484 (2014). "
    "doi:10.1186/s13059-014-0484-1"
)

__all__ = [
    "CITATION", "LOW_CONFIDENCE_SCORE", "MUTATIONTASTER_LOW", "STATS", "binary_call", "binary_calls",
    "bootstrap_ci", "ci_better", "clades", "cohen_kappa", "combination_calls", "combination_name",
    "combinations", "evaluate", "example_path", "hamming_matrix", "hclust_complete", "kappa_categorical",
    "kappa_matrix", "label_vector", "landis_koch", "leaf_order", "low_confidence", "performance",
    "random_splits", "rank", "read_calls_csv", "recurrence", "split_sample", "write_rows",
]


def example_path(name: str = "oncogene_snvs.csv") -> Path:
    """Path of a bundled example file. See data/README.md for what each file is."""
    path = resources.files(__name__) / "data" / name
    if not path.is_file():
        raise FileNotFoundError(f"no bundled example file {name!r}")
    return Path(str(path))
