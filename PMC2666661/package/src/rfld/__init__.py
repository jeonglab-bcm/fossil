"""rfld: random forest variable importance for SNPs in linkage disequilibrium.

The revised random forest (RF1) and revised importance measure (IM1) of

    Meng YA, Yu Y, Cupples LA, Farrer LA, Lunetta KL. Performance of random forest when SNPs are in
    linkage disequilibrium. BMC Bioinformatics 10:78 (2009). doi:10.1186/1471-2105-10-78

on a port of Breiman and Cutler's Fortran Random Forests 5.1 for categorical predictors, with the
paper's simulation models (Lunetta et al. 2004) and two-SNP haplotype phasing by EM.
"""

import csv
from importlib import resources
from pathlib import Path

import numpy as np

from .forest import grow_forest, r2_matrix
from .haplo import haplotype_em, phase_posterior, sample_haplotype_pairs
from .simulate import (DESIGNS, LD_MODELS, MODELS, GeneticModel, haplo_genotype_code, haplotype_dataset,
                       haplotype_frequencies, snp_dataset, table1_statistics)

__version__ = "0.1.0"

CITATION = ("Meng YA, Yu Y, Cupples LA, Farrer LA, Lunetta KL. Performance of random forest when SNPs are "
            "in linkage disequilibrium. BMC Bioinformatics 10:78 (2009). doi:10.1186/1471-2105-10-78")

__all__ = [
    "CITATION", "DESIGNS", "LD_MODELS", "MODELS", "GeneticModel", "example_path", "grow_forest",
    "haplo_genotype_code", "haplotype_dataset", "haplotype_em", "haplotype_frequencies", "importance_table",
    "phase_posterior", "r2_matrix", "rank", "read_genotypes", "sample_haplotype_pairs", "snp_dataset",
    "table1_statistics", "write_table",
]


def example_path(name: str = "h4m4_r1.csv") -> Path:
    """Path of a bundled example file. See data/README.md for what each file is."""
    path = resources.files(__name__) / "data" / name
    if not path.is_file():
        raise FileNotFoundError(f"no bundled example file {name!r}")
    return Path(str(path))


def read_genotypes(path, status="status"):
    """Read a CSV with a 0/1 status column and one column per SNP (0, 1, 2 risk alleles, or any
    category codes 0..L-1). Returns (X, y, snp_names)."""
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.reader(fh))
    if not rows:
        raise ValueError(f"{path}: empty file")
    head = rows[0]
    if status not in head:
        raise ValueError(f"{path}: no column {status!r}")
    si = head.index(status)
    names = [h for i, h in enumerate(head) if i != si]
    try:
        data = np.array([[int(v) for v in r] for r in rows[1:]], dtype=np.int64)
    except ValueError as e:
        raise ValueError(f"{path}: every value must be an integer ({e})") from None
    if data.ndim != 2 or data.shape[0] < 2:
        raise ValueError(f"{path}: need at least two rows of data")
    y = data[:, si]
    X = np.delete(data, si, axis=1)
    return X, y, names


def rank(values):
    """Ranks, 1 = largest; tied values share the largest rank."""
    v = np.asarray(values, dtype=float)
    order = (-v)[:, None] <= (-v)[None, :]
    return order.sum(axis=0)


def importance_table(X, y, names=None, **kw):
    """Grow a forest (keywords as grow_forest) and return a list of dicts, one per SNP, with its
    importances IM0 and IM1, the number of trees that split on it and its ranks by IM0 and IM1."""
    res = grow_forest(X, y, **kw)
    names = names or [f"v{j + 1}" for j in range(np.asarray(X).shape[1])]
    r0, r1 = rank(res["im0"]), rank(res["im1"])
    return [{"snp": n, "im0": float(a), "im1": float(b), "trees": int(t), "rank_im0": int(i), "rank_im1": int(j)}
            for n, a, b, t, i, j in zip(names, res["im0"], res["im1"], res["trees"], r0, r1)]


def write_table(rows, fh):
    w = csv.writer(fh)
    w.writerow(["snp", "im0", "im1", "trees", "rank_im0", "rank_im1"])
    for r in rows:
        w.writerow([r["snp"], f"{r['im0']:.6f}", f"{r['im1']:.6f}", r["trees"], r["rank_im0"], r["rank_im1"]])
