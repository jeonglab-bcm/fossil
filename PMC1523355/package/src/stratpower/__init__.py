"""stratpower: power of risk-stratified vs conventional subgroup analysis of clinical trials.

Implemented from the text of: Hayward RA, Kent DM, Vijan S, Hofer TP. Multivariable risk prediction can
greatly enhance the statistical power of clinical trial subgroup analysis. BMC Medical Research
Methodology 6:18 (2006). doi:10.1186/1471-2288-6-18
"""

from importlib import resources
from pathlib import Path

from .core import (
    ALPHA,
    HARM_PER_YEAR,
    N_PER_ARM,
    RRR,
    YEARS,
    Population,
    auroc_weighted,
    cer0_for_mean,
    fit_logit_grouped,
    interaction_test,
    net_rrr,
    population,
    population_auroc,
    read_trial,
    risk_score,
    simulate_power,
    subgroup_table,
    treated_risk,
)

__version__ = "0.1.0"
CITATION = (
    "Hayward RA, Kent DM, Vijan S, Hofer TP. Multivariable risk prediction can greatly enhance the "
    "statistical power of clinical trial subgroup analysis. BMC Medical Research Methodology 6:18 (2006). "
    "doi:10.1186/1471-2288-6-18"
)

__all__ = [
    "ALPHA", "CITATION", "HARM_PER_YEAR", "N_PER_ARM", "RRR", "YEARS", "Population", "auroc_weighted",
    "cer0_for_mean", "example_path", "fit_logit_grouped", "interaction_test", "net_rrr", "population",
    "population_auroc", "read_trial", "risk_score", "simulate_power", "subgroup_table", "treated_risk",
]


def example_path(name: str = "trial.csv") -> Path:
    """Path of a bundled example file. See data/README.md for what each file is."""
    path = resources.files(__name__) / "data" / name
    if not path.is_file():
        raise FileNotFoundError(f"no bundled example file {name!r}")
    return Path(str(path))
