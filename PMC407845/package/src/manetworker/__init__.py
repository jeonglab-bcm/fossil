"""manetworker: transcription factor activity profiles and regulatory coupling (MA-Networker).

A Python implementation, from the paper's Methods, of
Gao F, Foat BC, Bussemaker HJ. Defining transcriptional networks through integrative modeling of
mRNA expression and transcription factor binding data. BMC Bioinformatics 5:31 (2004).
doi:10.1186/1471-2105-5-31

The authors' MA-Networker code was never released. See the README for what was checked.
"""

from importlib import resources
from pathlib import Path

from .core import (
    CLASSES,
    backward_select,
    bh_reject,
    class_counts,
    classify,
    coupled,
    coupling,
    fill_binding,
    log_ratio,
    read_matrix,
    regress_activities,
    run,
    to_json,
    write_counts,
    write_matrix,
)

__version__ = "0.1.0"

__all__ = [
    "CLASSES",
    "backward_select",
    "bh_reject",
    "class_counts",
    "classify",
    "coupled",
    "coupling",
    "example_path",
    "fill_binding",
    "log_ratio",
    "read_matrix",
    "regress_activities",
    "run",
    "to_json",
    "write_counts",
    "write_matrix",
]


def example_path(name: str = "expression.tsv") -> Path:
    """Path of a bundled example file. See data/README.md for what each file is."""
    path = resources.files(__name__) / "data" / name
    if not path.is_file():
        raise FileNotFoundError(f"no bundled example file {name!r}")
    return Path(str(path))
