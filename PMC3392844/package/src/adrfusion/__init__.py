"""adrfusion: adverse drug reaction prediction from chemical, biological and phenotypic drug properties.

A rebuild, from the paper's text, of the method of

    Liu M, Wu Y, Chen Y, Sun J, Zhao Z, Chen XW, Matheny ME, Xu H. Large-scale prediction of adverse drug
    reactions using chemical, biological, and phenotypic properties of drugs. J Am Med Inform Assoc
    19(e1):e28-e35 (2012). doi:10.1136/amiajnl-2011-000699

One classifier per ADR (SVM with an RBF kernel, g = 0.008, C = 2, by default), trained by cross-validation
on binary drug features, and the paper's micro-averaged AUC, accuracy, precision and recall over a global
ROC curve. The authors' code was never released.
"""

from importlib import resources
from pathlib import Path

from .core import (
    ALGORITHMS,
    BLOCKS,
    FEATURE_SETS,
    ADRData,
    Metrics,
    auc,
    block_distances,
    cross_validated_scores,
    expand,
    features_for,
    informative_features,
    ks_larger,
    micro_metrics,
    paper_weights,
    per_adr_auc,
    predict_held_out,
    read_dataset,
    roc,
    score_table,
    stratified_folds,
    true_positives,
    write_dataset,
)

__version__ = "0.1.0"

CITATION = ("Liu M, Wu Y, Chen Y, Sun J, Zhao Z, Chen XW, Matheny ME, Xu H. Large-scale prediction of adverse drug "
            "reactions using chemical, biological, and phenotypic properties of drugs. J Am Med Inform Assoc "
            "19(e1):e28-e35 (2012). doi:10.1136/amiajnl-2011-000699")

__all__ = [
    "ALGORITHMS", "BLOCKS", "CITATION", "FEATURE_SETS", "ADRData", "Metrics", "auc", "block_distances",
    "cross_validated_scores", "example_path", "expand", "features_for", "informative_features", "ks_larger",
    "micro_metrics", "paper_weights", "per_adr_auc", "predict_held_out", "read_dataset", "roc", "score_table",
    "stratified_folds", "true_positives", "write_dataset",
]


def example_path(name: str = "example_drugs.txt") -> Path:
    """Path of a bundled example file. See data/README.md for what each file is."""
    path = resources.files(__name__) / "data" / name
    if not path.is_file():
        raise FileNotFoundError(f"no bundled example file {name!r}")
    return Path(str(path))
