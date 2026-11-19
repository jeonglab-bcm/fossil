"""rctconf: confidence that a MEDLINE citation reports a randomized controlled trial.

A rebuild, from the paper's text, of the method of
Cohen AM, Smalheiser NR, McDonagh MS, Yu C, Adams CE, Davis JM, Yu PS. Automated confidence ranked
classification of randomized controlled trial articles: an aid to evidence-based medicine.
J Am Med Inform Assoc 22(3):707-717 (2015). doi:10.1093/jamia/ocu025

Binary feature sets from the citation (title and abstract n-grams, journal, authors, author count)
and optionally from MEDLINE indexing (MeSH, substances), chosen by forward selection, a LIBLINEAR
linear SVM, and a sigmoid that turns the SVM margin into a confidence.
"""

from importlib import resources
from pathlib import Path

from .features import ALL_SETS, CITATION_SETS, MESH_SETS, PUBTYPE_SETS, hashed_features, raw_features, tokens
from .io import read_citations, write_scores
from .mdl import mdl_cut_points
from .metrics import auc, auc_ci, average_precision, binary_measures, evaluate, hanley_mcneil_se, mse
from .model import LIBLINEAR_OPTIONS, FeatureSpace, RCTModel, fit_sigmoid, train, train_svm, zero_sigmoid
from .selection import cross_validate, cv_splits, forward_select

__version__ = "0.1.0"

# Feature sets the bundled example uses: the example has no abstracts (see data/README.md).
EXAMPLE_SETS = ("title_unigrams", "title_bigrams", "journal", "author_count", "mesh_terms", "mesh_major", "chemicals")

CITATION = (
    "Cohen AM, Smalheiser NR, McDonagh MS, Yu C, Adams CE, Davis JM, Yu PS. Automated confidence ranked "
    "classification of randomized controlled trial articles: an aid to evidence-based medicine. "
    "J Am Med Inform Assoc 22(3):707-717 (2015). doi:10.1093/jamia/ocu025"
)

__all__ = [
    "ALL_SETS", "CITATION", "EXAMPLE_SETS", "CITATION_SETS", "FeatureSpace", "LIBLINEAR_OPTIONS", "MESH_SETS", "PUBTYPE_SETS",
    "RCTModel", "auc", "auc_ci", "average_precision", "binary_measures", "cross_validate", "cv_splits",
    "evaluate", "example_path", "fit_sigmoid", "forward_select", "hanley_mcneil_se", "hashed_features",
    "mdl_cut_points", "mse", "raw_features", "read_citations", "tokens", "train", "train_svm",
    "write_scores", "zero_sigmoid",
]


def example_path(name: str = "citations_train.csv") -> Path:
    """Path of a bundled example file. See data/README.md for what each file is."""
    path = resources.files(__name__) / "data" / name
    if not path.is_file():
        raise FileNotFoundError(f"no bundled example file {name!r}")
    return Path(str(path))
