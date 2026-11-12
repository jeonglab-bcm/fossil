"""Shared helpers: load a prepared dataset and its gene sets."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

DATASETS = ["nfkb", "leukemia", "prostate", "breast_netherlands", "breast_usa", "lung_michigan", "lung_boston"]
LABELS = {
    "nfkb": "NF-kB",
    "leukemia": "Leukemia",
    "prostate": "Prostate",
    "breast_netherlands": "Breast Netherlands",
    "breast_usa": "Breast USA",
    "lung_michigan": "Lung Michigan",
    "lung_boston": "Lung Boston",
}
# Cross-dataset pairs in the order of Fig. 3B: (marker dataset, test dataset).
PAIRS = [
    ("breast_netherlands", "breast_usa"),
    ("breast_usa", "breast_netherlands"),
    ("lung_michigan", "lung_boston"),
    ("lung_boston", "lung_michigan"),
]
TOP_FRACTIONS = [0.01, 0.02, 0.03, 0.05, 0.10]
N_PATHWAYS = 522  # MSigDB v1.0 C2


def top_count(fraction: float, n: int = N_PATHWAYS) -> int:
    """Pathways in the top fraction: 1% of 522 = 5, ..., 10% = 52 (the paper's count)."""
    return int(round(fraction * n))


class Dataset:
    def __init__(self, folder: Path, name: str):
        d = np.load(Path(folder) / f"{name}.npz")
        self.name = name
        self.genes = [str(g) for g in d["genes"]]
        self.symbols = [str(s) for s in d["symbols"]]
        self.samples = [str(s) for s in d["samples"]]
        self.X = d["X"]
        self.y = d["y"].astype(bool)
        self.classes = [str(c) for c in d["classes"]]
        sets = json.loads((Path(folder) / f"{name}_sets.json").read_text())
        self.set_names = list(sets)
        self.set_size = [sets[s]["size"] for s in self.set_names]
        self.set_rows = [sets[s]["rows"] for s in self.set_names]
        self.index = {g: i for i, g in enumerate(self.genes)}

    def rows_in(self, other: "Dataset", rows):
        """Rows of this dataset's genes in another dataset (genes it does not measure dropped)."""
        return [other.index[self.genes[r]] for r in rows if self.genes[r] in other.index]
