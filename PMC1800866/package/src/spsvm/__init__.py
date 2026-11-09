"""spsvm: zinc-binding residues from PSI-BLAST profiles with the SP-SVM of Passerini et al. (2007).

Passerini A, Andreini C, Menchetti S, Rosato A, Frasconi P. Predicting zinc binding at the
proteome level. BMC Bioinformatics 8:39 (2007). doi:10.1186/1471-2105-8-39

Implemented from the paper's text (the authors' C++ "Zinc Finder" is no longer available).
"""

from importlib import resources
from pathlib import Path

from .core import (
    DE_GAPS,
    MAX_GAP,
    PAPER_PARAMS,
    SPSVM,
    Chain,
    Profile,
    auc_with_se,
    aurpc,
    chain_from_profile,
    descriptors,
    fit_platt,
    gate,
    local_features,
    platt,
    pr_curve,
    predict_protein,
    protein_scores,
    read_ascii_pssm,
    read_profiles,
    read_table,
    semipattern_features,
    semipattern_kernel,
    semipattern_pairs,
    write_profiles,
)

__version__ = "0.1.0"

__all__ = [
    "DE_GAPS", "MAX_GAP", "PAPER_PARAMS", "SPSVM", "Chain", "Profile", "auc_with_se", "aurpc",
    "chain_from_profile", "descriptors", "example_path", "fit_platt", "gate", "local_features", "platt",
    "pr_curve", "predict_protein", "protein_scores", "read_ascii_pssm", "read_profiles",
    "read_table", "semipattern_features", "semipattern_kernel", "semipattern_pairs",
    "write_profiles",
]


def example_path(name: str = "example_profiles.npz") -> Path:
    """Path of a bundled example file. See data/README.md for what each file is."""
    path = resources.files(__name__) / "data" / name
    if not path.is_file():
        raise FileNotFoundError(f"no bundled example file {name!r}")
    return Path(str(path))
