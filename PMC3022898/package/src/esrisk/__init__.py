"""esrisk: exposure-specific risk from two independent samples.

The simple and revised product-based estimators of an exposure-specific risk (ESR), with log-based
and binomial 95% confidence intervals, and the simulation study that compares them, from

Reichmann WM, Gagnon D, Horsburgh CR, Losina E. Evaluation of exposure-specific risks from two
independent samples: a simulation study. BMC Medical Research Methodology 11:1 (2011).
doi:10.1186/1471-2288-11-1

Implemented from the paper's text; the authors' SAS programs were never released.
"""

from importlib import resources
from pathlib import Path

from .core import (
    ZERO_CELL_RULES,
    Estimates,
    binomial_ci,
    draw_samples,
    esr_from_summaries,
    esr_revised,
    esr_simple,
    estimate,
    evaluate,
    log_ci,
    make_population,
    p_unexposed,
    simulate,
    var_ln_proportion,
    var_ln_rr,
)
from .io import estimate_table, read_counts, write_rows

__version__ = "0.1.0"

CITATION = (
    "Reichmann WM, Gagnon D, Horsburgh CR, Losina E. Evaluation of exposure-specific risks from two "
    "independent samples: a simulation study. BMC Med Res Methodol 11:1 (2011). doi:10.1186/1471-2288-11-1"
)

__all__ = [
    "CITATION",
    "ZERO_CELL_RULES",
    "Estimates",
    "binomial_ci",
    "draw_samples",
    "esr_from_summaries",
    "esr_revised",
    "esr_simple",
    "estimate",
    "estimate_table",
    "evaluate",
    "example_path",
    "log_ci",
    "make_population",
    "p_unexposed",
    "read_counts",
    "simulate",
    "var_ln_proportion",
    "var_ln_rr",
    "write_rows",
]


def example_path(name: str = "two_samples.csv") -> Path:
    """Path of a bundled example file. See data/README.md for what each file is."""
    path = resources.files(__name__) / "data" / name
    if not path.is_file():
        raise FileNotFoundError(f"no bundled example file {name!r}")
    return Path(str(path))
