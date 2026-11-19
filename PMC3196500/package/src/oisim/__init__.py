"""oisim: the risk of overestimated pooled effects in cumulative meta-analysis, and the optimal information size.

Implemented from the text and Appendices S1 and S2 of:
Thorlund K, Imberger G, Walsh M, Chu R, Gluud C, Wetterslev J, Guyatt G, Devereaux PJ, Thabane L.
The number of patients and events required to limit the risk of overestimation of intervention effects in
meta-analysis - a simulation study. PLoS ONE 6(10):e25491 (2011). doi:10.1371/journal.pone.0025491
"""

from importlib import resources
from pathlib import Path

from .core import (
    BIN_RULES,
    COCHRANE_SIZES,
    COMMON_SIZES,
    PC_MIDPOINTS,
    PC_RANGES,
    READ_RULES,
    Scenario,
    Simulation,
    cumulative_dl,
    draw_trials,
    format_required,
    log_rr_and_variance,
    ois,
    ois_table,
    overestimation_curve,
    required_number,
    required_table,
    round_ois,
    round_ois_footnote,
    simulate,
)
from .io import cumulative, read_trials, write_cumulative

__version__ = "0.1.0"

CITATION = ("Thorlund K, Imberger G, Walsh M, et al. The number of patients and events required to limit the risk "
            "of overestimation of intervention effects in meta-analysis - a simulation study. PLoS ONE 6(10):e25491 "
            "(2011). doi:10.1371/journal.pone.0025491")

__all__ = [
    "BIN_RULES", "CITATION", "COCHRANE_SIZES", "COMMON_SIZES", "PC_MIDPOINTS", "PC_RANGES", "READ_RULES",
    "Scenario", "Simulation", "cumulative", "cumulative_dl", "draw_trials", "example_path", "format_required",
    "log_rr_and_variance", "ois", "ois_table", "overestimation_curve", "read_trials", "required_number",
    "required_table", "round_ois", "round_ois_footnote", "simulate", "write_cumulative",
]


def example_path(name: str = "cumulative_trials.csv") -> Path:
    """Path of a bundled example file. See data/README.md for what each file is."""
    path = resources.files(__name__) / "data" / name
    if not path.is_file():
        raise FileNotFoundError(f"no bundled example file {name!r}")
    return Path(str(path))
