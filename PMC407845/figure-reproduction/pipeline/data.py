"""Read the PMC407845 inputs: the expression compendium (SGD archives), Lee 2002 and Simon 2001 ChIP.

compendium(downloads) -> dict(genes, arrays, source, E) with E in log2 ratios, genes x arrays.
lee(downloads)        -> dict(genes, tfs, ratio, p, spot)  (genes x TFs; blank ratio = NaN)
simon(downloads)      -> dict(genes, tfs, ratio, p)
"""

from __future__ import annotations

import csv
import io
import math
import re
import zipfile
from pathlib import Path

import numpy as np

# The 19 sources of the paper's 751-array library (archived dataset_info page) and the arrays in
# each; the SGD archive holds 15 of them (Casagrande 2000, Rutherford 2001, Diehn 2000 are not there).
PAPER_SOURCES = {
    "Hughes_2000": 300, "Gasch_2000": 156, "Spellman_1998": 60, "Roberts_2000": 56, "Gasch_2001": 53,
    "Yoshimoto_2002": 40, "Zhu_2000": 26, "Sudarsanam_2000": 12, "Ogawa_2000": 8, "Chu_1998": 7,
    "DeRisi_1997": 7, "Gross_2000": 6, "Keller_2001": 4, "Protchenko_2001": 4, "Yun_2000": 4,
    "Kuhn_2001": 3, "Casagrande_2000": 2, "Rutherford_2001": 2, "Diehn_2000": 1,
}
ARCHIVES = [
    "Chu_1998_PMID_9784122", "DeRisi_1997_PMID_9381177", "Gasch_2000_PMID_11102521",
    "Gasch_2001_PMID_11598186", "Gross_2000_PMID_10922376", "Hughes_2000_PMID_10929718",
    "Keller_2001_PMID_11504737", "Kuhn_2001_PMID_11154278", "Ogawa_2000_PMID_11102525",
    "Protchenko_2001_PMID_11673473", "Roberts_2000_PMID_10657304", "Spellman_1998_PMID_9843569",
    "Sudarsanam_2000_PMID_10725359", "Yoshimoto_2002_PMID_12058033", "Yun_2000_PMID_10744769",
    "Zhu_2000_PMID_10894548",
]
# Rosetta (Hughes 2000) ratios are log10 in the SGD file; every other file is log2.
LOG10_SOURCES = {"Hughes_2000"}
# SGD stores the same file (identical SHA-256) for Yun 2000 and Protchenko 2001: keep it once.
DUPLICATE_OF = {"Protchenko_2001": "Yun_2000"}


def _num(x: str) -> float:
    x = x.strip()
    return float(x) if x else math.nan


def read_pcl(text: str):
    rows = [r for r in csv.reader(io.StringIO(text), delimiter="\t") if r]
    h = rows[0]
    off = 3 if len(h) > 2 and h[2] == "GWEIGHT" else 2
    start = 2 if len(rows) > 1 and rows[1][0] == "EWEIGHT" else 1
    arrays = [a.strip() for a in h[off:]]
    genes, vals = [], []
    for r in rows[start:]:
        orf = r[0].strip().upper()
        if not orf:
            continue
        v = [_num(x) for x in r[off:off + len(arrays)]]
        v += [math.nan] * (len(arrays) - len(v))
        genes.append(orf)
        vals.append(v)
    return genes, arrays, np.array(vals, float)


def compendium(downloads: str | Path) -> dict:
    """Assemble the expression library from the SGD archives, genes x arrays in log2 ratios.

    Arrays keep the order of the archives (alphabetical) and of the files and columns in each.
    A gene repeated within a file is averaged.
    """
    downloads = Path(downloads)
    blocks = []
    for name in ARCHIVES:
        src = "_".join(name.split("_")[:2])
        if src in DUPLICATE_OF:
            continue
        with zipfile.ZipFile(downloads / f"{name}.zip") as z:
            pcls = sorted(n for n in z.namelist() if n.endswith(".pcl"))
            for pcl in pcls:
                genes, arrays, v = read_pcl(z.read(pcl).decode("latin-1"))
                if src in LOG10_SOURCES:
                    v = v * math.log2(10)
                blocks.append((src, Path(pcl).name, genes, arrays, v))
    all_genes = sorted({g for b in blocks for g in b[2]})
    gi = {g: i for i, g in enumerate(all_genes)}
    cols, source, files = [], [], []
    mats = []
    for src, fname, genes, arrays, v in blocks:
        m = np.full((len(all_genes), len(arrays)), np.nan)
        cnt = np.zeros((len(all_genes), 1))
        acc = np.zeros((len(all_genes), len(arrays)))
        idx = np.array([gi[g] for g in genes])
        ok = ~np.isnan(v)
        np.add.at(acc, idx, np.where(ok, v, 0.0))
        nn = np.zeros((len(all_genes), len(arrays)))
        np.add.at(nn, idx, ok.astype(float))
        with np.errstate(invalid="ignore"):
            m = np.where(nn > 0, acc / np.maximum(nn, 1), np.nan)
        mats.append(m)
        cols += arrays
        source += [src] * len(arrays)
        files += [fname] * len(arrays)
    E = np.concatenate(mats, axis=1)
    return {"genes": all_genes, "arrays": cols, "source": source, "file": files, "E": E}


def _read_young(path: Path, gene_col: int, first: int, name_row: int, data_row: int):
    with open(path, newline="", encoding="latin-1") as f:
        rows = list(csv.reader(f, delimiter="\t"))
    names = rows[name_row]
    tfs, pcols = [], []
    j = first
    while j + 1 < len(names) and names[j].strip() and not names[j + 1].strip():
        tfs.append(names[j].strip())
        pcols.append(j)
        j += 2
    genes, P, R, spot = [], [], [], []
    for r in rows[data_row:]:
        if len(r) <= gene_col or not r[gene_col].strip():
            continue
        genes.append(r[gene_col].strip().upper())
        P.append([_num(r[c]) if c < len(r) else math.nan for c in pcols])
        R.append([_num(r[c + 1]) if c + 1 < len(r) else math.nan for c in pcols])
        spot.append(r[1] if gene_col == 0 else r[0])
    return genes, tfs, np.array(R), np.array(P), spot


def lee(downloads: str | Path) -> dict:
    """Lee et al. 2002: 6270 genes x 113 TFs, P-value and ratio (blank ratio = not measured)."""
    genes, tfs, R, P, spot = _read_young(Path(downloads) / "binding_by_gene.tsv", 0, 4, 1, 2)
    return {"genes": genes, "tfs": [canon(t) for t in tfs], "ratio": R, "p": P, "spot": spot}


def simon(downloads: str | Path) -> dict:
    """Simon et al. 2001: genes x 9 cell cycle TFs, P-value and ratio."""
    genes, tfs, R, P, spot = _read_young(Path(downloads) / "simon_all_genes.tsv", 6, 8, 0, 2)
    return {"genes": genes, "tfs": [canon(t) for t in tfs], "ratio": R, "p": P, "spot": spot}


def canon(tf: str) -> str:
    """'GRF10(Pho2)' -> 'Grf10', 'ABF1' -> 'Abf1' (the paper's capitalisation)."""
    tf = re.sub(r"\(.*\)", "", tf).strip()
    return tf[:1].upper() + tf[1:].lower()


def align(compendium_: dict, lee_: dict) -> dict:
    """Put expression and ChIP on one gene list: the union of the compendium's and Lee's genes.

    Returns E (genes x arrays), ratio and p (genes x TFs; NaN where the gene is not in Lee's file).
    """
    genes = sorted(set(compendium_["genes"]) | set(lee_["genes"]))
    gi = {g: i for i, g in enumerate(genes)}
    E = np.full((len(genes), compendium_["E"].shape[1]), np.nan)
    E[[gi[g] for g in compendium_["genes"]]] = compendium_["E"]
    R = np.full((len(genes), len(lee_["tfs"])), np.nan)
    P = np.full_like(R, np.nan)
    li = [gi[g] for g in lee_["genes"]]
    R[li] = lee_["ratio"]
    P[li] = lee_["p"]
    return {"genes": genes, "E": E, "ratio": R, "p": P, "tfs": lee_["tfs"]}
