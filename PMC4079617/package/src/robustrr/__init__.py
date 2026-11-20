"""robustrr: relative risks for common binary outcomes by robust Poisson and log-binomial (COPY) regression.

Implemented from the text of: Chen W, Shi J, Qian L, Azen SP. Comparison of robustness to outliers between
robust poisson models and log-binomial models when estimating relative risks for common binary outcomes: a
simulation study. BMC Medical Research Methodology 14:82 (2014). doi:10.1186/1471-2288-14-82

The authors' SAS 9.2 program and the COPY macro they used were not released; this package is not a port.
"""

from importlib import resources
from pathlib import Path

from .core import DEFAULT_COPIES, log_binomial, log_binomial_coef, poisson_coef, robust_poisson
from .api import fit_relative_risk, read_table
from .simulation import (CONTAMINATION, SCENARIOS, contaminate, generate, population_cutoffs, run_scenario, scenario,
                         summarize)

__version__ = "0.1.0"
CITATION = ("Chen W, Shi J, Qian L, Azen SP. Comparison of robustness to outliers between robust poisson models "
            "and log-binomial models when estimating relative risks for common binary outcomes: a simulation "
            "study. BMC Medical Research Methodology 14:82 (2014). doi:10.1186/1471-2288-14-82")

__all__ = ["CITATION", "CONTAMINATION", "DEFAULT_COPIES", "SCENARIOS", "contaminate", "example_path",
           "fit_relative_risk", "generate", "log_binomial", "log_binomial_coef", "poisson_coef", "population_cutoffs", "read_table",
           "robust_poisson", "run_scenario", "scenario", "summarize"]


def example_path(name: str = "cohort.csv") -> Path:
    """Path of a bundled example file. See data/README.md for what each file is."""
    path = resources.files(__name__) / "data" / name
    if not path.is_file():
        raise FileNotFoundError(f"no bundled example file {name!r}")
    return Path(str(path))
