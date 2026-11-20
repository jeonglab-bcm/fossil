"""mlagq: multilevel logistic regression by full maximum likelihood with adaptive Gauss-Hermite quadrature,
and the simulation study of Moineddin, Matheson and Glazier (2007).

Moineddin R, Matheson FI, Glazier RH. A simulation study of sample size for multilevel logistic regression
models. BMC Medical Research Methodology 7:34 (2007). doi:10.1186/1471-2288-7-34

The authors used SAS PROC NLMIXED and released no code; this package is implemented from the paper's text.
"""

from importlib import resources
from pathlib import Path

from .core import Fit, GroupedData, fit, group_data, loglik, select_qpoints
from .io import fit_table, read_long_csv
from .simulation import (
    GAMMA_MAIN,
    ROBUSTNESS_MODELS,
    generate,
    fit_replicate,
    replicate_record,
    seed_for,
    summarize,
)

__version__ = "0.1.0"

CITATION = ("Moineddin R, Matheson FI, Glazier RH. A simulation study of sample size for multilevel logistic "
            "regression models. BMC Medical Research Methodology 7:34 (2007). doi:10.1186/1471-2288-7-34")

__all__ = [
    "CITATION",
    "Fit",
    "GAMMA_MAIN",
    "GroupedData",
    "ROBUSTNESS_MODELS",
    "example_path",
    "fit",
    "fit_replicate",
    "fit_table",
    "generate",
    "group_data",
    "loglik",
    "read_long_csv",
    "replicate_record",
    "seed_for",
    "select_qpoints",
    "summarize",
]


def example_path(name: str = "clustered_binary.csv") -> Path:
    """Path of a bundled example file. See data/README.md for what each file is."""
    path = resources.files(__name__) / "data" / name
    if not path.is_file():
        raise FileNotFoundError(f"no bundled example file {name!r}")
    return Path(str(path))
