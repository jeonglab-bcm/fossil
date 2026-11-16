"""diabclass: support vector machine classifiers of diabetes and pre-diabetes from simple variables.

A reimplementation, from the paper's text, of the method of

    Yu W, Liu T, Valdez R, Gwinn M, Khoury MJ. Application of support vector machine modeling
    for prediction of common diseases: the case of diabetes and pre-diabetes.
    BMC Medical Informatics and Decision Making 10:16 (2010). doi:10.1186/1472-6947-10-16

The authors' web tool ("Diabetes Classifier") and code were never released and the tool is gone.
"""

from importlib import resources
from pathlib import Path

from .core import (
    DIVISORS,
    GRID_LOG2C,
    GRID_LOG2G,
    GRID_MAX_ITER,
    KERNELS,
    RACE_CODES,
    SCHEME_FEATURES,
    GridResult,
    SVMClassifier,
    auc,
    classification_metrics,
    delong_test,
    encode,
    grid_search,
    labels,
    logistic_probability,
    read_records,
    roc_curve,
    split_train_test,
    undersample,
    weighted_logistic,
)

__version__ = "0.1.0"

CITATION = (
    "Yu W, Liu T, Valdez R, Gwinn M, Khoury MJ. Application of support vector machine modeling "
    "for prediction of common diseases: the case of diabetes and pre-diabetes. BMC Medical "
    "Informatics and Decision Making 10:16 (2010). doi:10.1186/1472-6947-10-16"
)

__all__ = [
    "CITATION", "DIVISORS", "GRID_LOG2C", "GRID_LOG2G", "GRID_MAX_ITER", "KERNELS", "RACE_CODES",
    "SCHEME_FEATURES", "GridResult", "SVMClassifier", "auc", "classification_metrics",
    "delong_test", "encode", "example_path", "grid_search", "labels", "logistic_probability",
    "read_records", "roc_curve", "split_train_test", "undersample", "weighted_logistic",
]


def example_path(name: str = "nhanes_example.csv") -> Path:
    """Path of a bundled example file. See data/README.md for what each file is."""
    path = resources.files(__name__) / "data" / name
    if not path.is_file():
        raise FileNotFoundError(f"no bundled example file {name!r}")
    return Path(str(path))
