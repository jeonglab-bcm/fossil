"""rommeta: the ratio of means (RoM) for meta-analysis of continuous outcomes, next to the mean
difference (MD) and the standardized mean difference (SMD), with DerSimonian-Laird random-effects
pooling and the simulation study that compares the three.

Friedrich JO, Adhikari NKJ, Beyene J. The ratio of means method as an alternative to mean differences
for analyzing continuous outcome variables in meta-analysis: a simulation study. BMC Medical Research
Methodology 8:32 (2008). doi:10.1186/1471-2288-8-32

Implemented from the paper's text (the authors' SAS 8.2 programs were not released) by the fossil
reproduction PMC2430201: https://github.com/jeonglab-bcm/fossil/tree/main/PMC2430201
"""

from importlib import resources
from pathlib import Path

from .core import MEASURES, Z95, MetaResult, effect_sizes, meta_analysis, pool, two_sided_p
from .io import COLUMNS, read_results, read_studies, results_text, write_results
from .simulation import SKEWED_MIXTURE, Scenario, draw_trials, mixture_moments, run_scenario, summarize

__version__ = "0.1.0"

CITATION = ("Friedrich JO, Adhikari NKJ, Beyene J. The ratio of means method as an alternative to mean "
            "differences for analyzing continuous outcome variables in meta-analysis: a simulation study. "
            "BMC Medical Research Methodology 8:32 (2008). doi:10.1186/1471-2288-8-32")

__all__ = [
    "CITATION", "COLUMNS", "MEASURES", "SKEWED_MIXTURE", "Z95", "MetaResult", "Scenario", "analyze",
    "draw_trials", "effect_sizes", "example_path", "meta_analysis", "mixture_moments", "pool",
    "read_results", "read_studies", "results_text", "run_scenario", "summarize", "two_sided_p", "write_results",
]


def analyze(studies: dict, measures=MEASURES, z: float = Z95) -> list:
    """Random-effects meta-analysis of a study table (as read by read_studies) with each measure."""
    args = [studies[c] for c in COLUMNS]
    return [meta_analysis(*args, measure=m, z=z) for m in measures]


def example_path(name: str = "trials.csv") -> Path:
    """Path of a bundled example file. See data/README.md for what each file is."""
    path = resources.files(__name__) / "data" / name
    if not path.is_file():
        raise FileNotFoundError(f"no bundled example file {name!r}")
    return Path(str(path))
