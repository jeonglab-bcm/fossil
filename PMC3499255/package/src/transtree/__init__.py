"""transtree: Bayesian reconstruction of transmission trees from genetic and
epidemiological data.

A reimplementation, from the paper's text and Text S1, of

    Morelli MJ, Thebaud G, Chadoeuf J, King DP, Haydon DT, Soubeyrand S.
    A Bayesian inference framework to reconstruct transmission trees using
    epidemiological and genetic data. PLoS Comput Biol 8(11):e1002768 (2012).
    doi:10.1371/journal.pcbi.1002768

The authors never released their R implementation; this package is reconstructed
from the equations in the paper. See the reproduction for the full-data runs:
https://github.com/jeonglab-bcm/fossil/tree/main/PMC3499255
"""

from .core import (
    Data,
    MCMCConfig,
    Posterior,
    divergence_premise,
    example_path,
    genetic_log_pseudo_likelihood,
    hamming_matrix,
    lonlat_to_km,
    read_epi_table,
    read_dataset,
    read_fasta,
    run_mcmc,
    simulate_outbreak,
)

__version__ = "0.1.0"

CITATION = (
    "Morelli MJ, Thebaud G, Chadoeuf J, King DP, Haydon DT, Soubeyrand S. "
    "A Bayesian inference framework to reconstruct transmission trees using "
    "epidemiological and genetic data. PLoS Comput Biol 8(11):e1002768 (2012). "
    "doi:10.1371/journal.pcbi.1002768"
)

__all__ = [
    "Data",
    "MCMCConfig",
    "Posterior",
    "CITATION",
    "divergence_premise",
    "example_path",
    "genetic_log_pseudo_likelihood",
    "hamming_matrix",
    "lonlat_to_km",
    "read_epi_table",
    "read_dataset",
    "read_fasta",
    "run_mcmc",
    "simulate_outbreak",
    "__version__",
]
