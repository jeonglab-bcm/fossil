"""hivrecomb: recombination rate and selection strength from time series sequence samples.

The methods of Neher RA, Leitner T. Recombination rate and selection strength in HIV
intra-patient evolution. PLoS Comput Biol 6(1):e1000660 (2010).
doi:10.1371/journal.pcbi.1000660

The paper's own scripts were never released; this package is written from its text. See
https://github.com/jeonglab-bcm/fossil/tree/main/PMC2813257 for the reproduction.
"""

from importlib import resources
from pathlib import Path

from .align import codon_align, read_fasta, translate, write_fasta
from .recombination import (
    as_array,
    bin_events,
    bootstrap_rho,
    concat_events,
    estimate_rho,
    mean_MpApB,
    pair_events,
    saturation,
)
from .selection import (
    concat_rates,
    cumulative,
    frequency_changes,
    ks,
    linked_mask,
    share_above,
)

__version__ = "0.1.0"
CITATION = ("Neher RA, Leitner T. Recombination rate and selection strength in HIV intra-patient "
            "evolution. PLoS Comput Biol 6(1):e1000660 (2010). doi:10.1371/journal.pcbi.1000660")

__all__ = [
    "CITATION", "__version__", "as_array", "bin_events", "bootstrap_rho", "codon_align",
    "concat_events", "concat_rates", "cumulative", "estimate_rho", "example_path",
    "frequency_changes", "ks", "linked_mask", "mean_MpApB", "pair_events", "read_fasta",
    "saturation", "share_above", "translate", "write_fasta",
]


def example_path(name: str = "example_alignment.fasta") -> Path:
    """Path of a bundled example file. See data/README.md for what each file is."""
    path = resources.files(__name__) / "data" / name
    if not path.is_file():
        raise FileNotFoundError(f"no bundled example file {name!r}")
    return Path(str(path))
