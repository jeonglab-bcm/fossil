"""prospectr_adtree: PROSPECTR disease-gene prioritisation and the alternating decision tree behind it.

Adie EA, Adams RR, Evans KL, Porteous DJ, Pickard BS. Speeding disease gene discovery by sequence
based candidate prioritization. BMC Bioinformatics 6:55 (2005). doi:10.1186/1471-2105-6-55

- ``ADTree``: a port of Weka 3.4's alternating decision tree learner, the one PROSPECTR was built with.
- ``cross_validate``: Weka's stratified k-fold cross-validation with the same shuffles.
- ``evaluate``: accuracy, precision, recall, kappa and ROC area as Weka reports them.
- ``published_tree``, ``score``, ``normalise``: the paper's Figure 2 tree as a gene scorer.
"""

from importlib import resources
from pathlib import Path

from .adtree import ADTree, cross_validate, weka_double
from .arff import Attribute, Dataset, read_arff
from .evaluation import confusion, evaluate, kappa, roc_area, roc_curve, roc_hull
from .prospectr import (
    FEATURE_GROUPS,
    FEATURES,
    average_contributions,
    contributions,
    features_from_prospectr_arff,
    normalise,
    published_tree,
    rank_in_locus,
    score,
)

__version__ = "0.1.0"

CITATION = ("Adie EA, Adams RR, Evans KL, Porteous DJ, Pickard BS. Speeding disease gene discovery by "
            "sequence based candidate prioritization. BMC Bioinformatics 6:55 (2005). "
            "doi:10.1186/1471-2105-6-55")

__all__ = [
    "ADTree", "Attribute", "CITATION", "Dataset", "FEATURES", "FEATURE_GROUPS", "average_contributions",
    "confusion", "contributions", "cross_validate", "evaluate", "example_path", "features_from_prospectr_arff",
    "kappa", "normalise", "published_tree", "rank_in_locus", "read_arff", "roc_area", "roc_curve",
    "roc_hull", "score", "weka_double",
]


def example_path(name: str = "example_train.arff") -> Path:
    """Path of a bundled example file. See data/README.md for what each file is."""
    path = resources.files(__name__) / "data" / name
    if not path.is_file():
        raise FileNotFoundError(f"no bundled example file {name!r}")
    return Path(str(path))
