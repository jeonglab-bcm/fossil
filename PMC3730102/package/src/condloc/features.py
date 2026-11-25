"""Single-protein (S) feature sets of Lee et al. 2008 (NAR 36:e136), reused by CoLP.

Nine sets: amino acid composition (AA), dipeptide composition (dAA), gapped dipeptide
composition with a gap of one residue (gAA), three chemical-property window profiles
(cHPo, cHPi, cSCM; mean squared difference at lags 1 to 40), the pseudo amino acid
profile combining the three (pAA), and binary InterPro motif (Motif) and GO term (GO)
vectors. Normalised property values are those of Lee et al. 2008, Supplementary Table S6.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

import numpy as np

AMINO_ACIDS = "ACDEFGHIKLMNPQRSTVWY"
_INDEX = {a: i for i, a in enumerate(AMINO_ACIDS)}

# Lee et al. 2008, Supplementary Table S6: hydrophobicity, hydrophilicity, side-chain mass.
HPO = dict(zip(AMINO_ACIDS, [0.6201, 0.2901, -0.9002, -0.7402, 1.1903, 0.4801, -0.4001, 1.3803, -1.5003,
                             1.0602, 0.6401, -0.7802, 0.1200, -0.8502, -2.5306, -0.1800, -0.0500, 1.0802,
                             0.8102, 0.2601]))
HPI = dict(zip(AMINO_ACIDS, [-0.1887, -0.4404, 1.5729, 1.5729, -1.1954, 0.0629, -0.1887, -0.8431, 1.5729,
                             -0.8431, -0.5914, 1.0696, 0.0629, 0.1636, 1.5729, 0.2139, -0.1384, -0.6921,
                             -1.6484, -1.0947]))
SCM = dict(zip(AMINO_ACIDS, [-1.5516, -0.5161, -0.1278, 0.3252, 0.9077, -2.0047, 0.6164, -0.1925, 0.3252,
                             -0.1925, 0.3899, -0.1602, -0.6779, 0.2929, 1.2313, -1.0339, -0.5808, -0.6456,
                             2.1697, 1.4254]))

MAX_LAG = 40
S_SETS = ("AA", "dAA", "gAA", "cHPo", "cHPi", "cSCM", "pAA", "Motif", "GO")


def _codes(seq: str) -> np.ndarray:
    """Residue indices of a sequence; residues outside the 20 standard ones are dropped."""
    return np.array([_INDEX[a] for a in seq.upper() if a in _INDEX], dtype=np.int64)


def aa_composition(seq: str) -> np.ndarray:
    c = _codes(seq)
    out = np.bincount(c, minlength=20).astype(float)
    return out / max(len(c), 1)


def pair_composition(seq: str, gap: int = 0) -> np.ndarray:
    """Frequencies of the 400 ordered residue pairs (a_l, a_{l+1+gap})."""
    c = _codes(seq)
    step = 1 + gap
    if len(c) <= step:
        return np.zeros(400)
    pairs = c[:-step] * 20 + c[step:]
    out = np.bincount(pairs, minlength=400).astype(float)
    return out / len(pairs)


def _property(seq: str, table: dict[str, float]) -> np.ndarray:
    return np.array([table[a] for a in seq.upper() if a in table])


def lag_profile(values: np.ndarray, max_lag: int = MAX_LAG) -> np.ndarray:
    """Mean squared difference of a residue property at lags 1..max_lag (0 where the protein is too short)."""
    out = np.zeros(max_lag)
    n = len(values)
    for k in range(1, max_lag + 1):
        if n - k > 0:
            d = values[:-k] - values[k:]
            out[k - 1] = float(np.mean(d * d))
    return out


def chemical_profiles(seq: str, max_lag: int = MAX_LAG) -> dict[str, np.ndarray]:
    """cHPo, cHPi, cSCM and the pseudo amino acid profile pAA = mean of the three squared differences."""
    p = {name: _property(seq, t) for name, t in (("cHPo", HPO), ("cHPi", HPI), ("cSCM", SCM))}
    out = {name: lag_profile(v, max_lag) for name, v in p.items()}
    out["pAA"] = (out["cHPo"] + out["cHPi"] + out["cSCM"]) / 3.0
    return out


def binary_matrix(items: Sequence[Iterable[str]], vocabulary: Sequence[str]) -> np.ndarray:
    """One row per protein, one column per vocabulary term; 1 where the protein has the term."""
    col = {t: j for j, t in enumerate(vocabulary)}
    out = np.zeros((len(items), len(vocabulary)), dtype=np.float32)
    for i, terms in enumerate(items):
        for t in terms:
            j = col.get(t)
            if j is not None:
                out[i, j] = 1.0
    return out


def single_features(sequences: Sequence[str], motifs: Sequence[Iterable[str]], go_terms: Sequence[Iterable[str]],
                    motif_vocabulary: Sequence[str], go_vocabulary: Sequence[str]) -> dict[str, np.ndarray]:
    """The nine S feature sets for a list of proteins, as float32 matrices with one row per protein."""
    n = len(sequences)
    out = {name: np.zeros((n, d), dtype=np.float32) for name, d in
           (("AA", 20), ("dAA", 400), ("gAA", 400), ("cHPo", MAX_LAG), ("cHPi", MAX_LAG), ("cSCM", MAX_LAG),
            ("pAA", MAX_LAG))}
    for i, s in enumerate(sequences):
        out["AA"][i] = aa_composition(s)
        out["dAA"][i] = pair_composition(s, 0)
        out["gAA"][i] = pair_composition(s, 1)
        for name, v in chemical_profiles(s).items():
            out[name][i] = v
    out["Motif"] = binary_matrix(motifs, motif_vocabulary)
    out["GO"] = binary_matrix(go_terms, go_vocabulary)
    return out
