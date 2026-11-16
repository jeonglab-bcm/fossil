"""pssmdt: PSSM distance transformation (PSSM-DT) and SVM-PSSM-DT for DNA-binding proteins.

Implemented from the paper's text (no code was released; the web server is gone):

Xu R, Zhou J, Wang H, He Y, Wang X, Liu B. Identifying DNA-binding proteins by combining support
vector machine and PSSM distance transformation. BMC Systems Biology 9(Suppl 1):S10 (2015).
doi:10.1186/1752-0509-9-S1-S10
"""

from importlib import resources
from pathlib import Path

from .core import (
    AMINO_ACIDS,
    DEFAULT_LG,
    ENCODINGS,
    acc,
    ave_pscore_20,
    ave_pscore_400,
    encode,
    feature_names,
    logistic,
    pscore_100,
    pssm_ddt,
    pssm_dt,
    pssm_sdt,
    read_pssm,
    sdt_mask,
)
from .svm import (
    PSSMDTClassifier,
    cross_validation,
    grid_search,
    jackknife,
    metrics,
    pair_weights,
    roc_curve_points,
    scale,
)

__version__ = "0.1.0"

CITATION = (
    "Xu R, Zhou J, Wang H, He Y, Wang X, Liu B. Identifying DNA-binding proteins by combining "
    "support vector machine and PSSM distance transformation. BMC Syst Biol 9(Suppl 1):S10 (2015). "
    "doi:10.1186/1752-0509-9-S1-S10"
)

__all__ = [
    "AMINO_ACIDS", "CITATION", "DEFAULT_LG", "ENCODINGS", "PSSMDTClassifier", "acc",
    "ave_pscore_20", "ave_pscore_400", "cross_validation", "encode", "example_path",
    "feature_names", "grid_search", "jackknife", "logistic", "metrics", "pair_weights",
    "pscore_100", "pssm_ddt", "pssm_dt", "pssm_sdt", "read_pssm", "roc_curve_points", "scale",
    "sdt_mask",
]


def example_path(name: str = "") -> Path:
    """Path of a bundled example file or, with no name, of the example folder.
    See data/README.md for what each file is."""
    path = resources.files(__name__) / "data" / name
    if name and not (path.is_file() or path.is_dir()):
        raise FileNotFoundError(f"no bundled example file {name!r}")
    return Path(str(path))
