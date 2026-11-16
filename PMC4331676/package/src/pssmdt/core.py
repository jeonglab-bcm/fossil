"""PSSM distance transformation (PSSM-DT) and the PSSM encodings it was compared with.

PSSM-DT (Xu et al. 2015, Eqs. 3 and 4). For a PSSM S of L rows (positions) and 20 columns
(amino acids, in PSI-BLAST order ARNDCQEGHILKMFPSTWYV) and a lag lg = 1..LG:

    DT(a1, a2, lg) = sum_{j=1}^{L-lg} S[j, a1] * S[j+lg, a2] / (L - lg)

The 20 features with a1 == a2 are PSSM-SDT and the 380 with a1 != a2 are PSSM-DDT. The vector is
lag-major: for each lg, the 20 x 20 matrix flattened row by row (a1 first), 400 * LG values. The
scores are the raw integer log-odds scores of the ASCII PSSM, as in the authors' later
reimplementation (BioSeq-Analysis2.0, mode PSSM-DT).

Comparators (Table 2 of the paper), defined by Lou et al. 2014 (PLoS One 9:e86703) on the PSSM
normalised with the logistic function 1 / (1 + exp(-x)):

* AvePscore-20: the mean of each column (20 values).
* AvePscore-400: for each residue type r and column a, the mean of column a over the positions
  where the sequence has r (0 when r does not occur); 400 values, r-major.
* Pscore-100: the 0, 25, 50, 75 and 100th percentiles of each column (100 values, column-major).
* ACC: auto-cross covariance of the normalised PSSM (Dong et al. 2009) for lg = 1..LG:
  sum_j (S[j,a1] - m[a1]) * (S[j+lg,a2] - m[a2]) / (L - lg), 400 * LG values in the PSSM-DT order.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import numpy as np

AMINO_ACIDS = "ARNDCQEGHILKMFPSTWYV"
DEFAULT_LG = 5


def read_pssm(path: str | Path) -> tuple[str, np.ndarray]:
    """Read an ASCII PSSM written by PSI-BLAST (``-out_ascii_pssm``).

    Returns the query sequence and the L x 20 integer log-odds scores (columns ARNDCQEGHILKMFPSTWYV).
    """
    seq = []
    rows = []
    header_seen = False
    for line in Path(path).read_text().splitlines():
        fields = line.split()
        if not header_seen:
            if len(fields) >= 20 and "".join(fields[:20]) == AMINO_ACIDS:
                header_seen = True
            continue
        if not fields or not fields[0].isdigit():
            if rows:
                break
            continue
        seq.append(fields[1])
        rows.append([int(x) for x in fields[2:22]])
    if not header_seen or not rows:
        raise ValueError(f"{path}: not an ASCII PSSM from PSI-BLAST")
    return "".join(seq), np.asarray(rows, dtype=np.int64)


def _check(pssm: np.ndarray, lg_max: int) -> np.ndarray:
    s = np.asarray(pssm, dtype=np.float64)
    if s.ndim != 2 or s.shape[1] != 20:
        raise ValueError(f"PSSM must be L x 20, got shape {s.shape}")
    if lg_max < 1:
        raise ValueError("LG must be at least 1")
    if s.shape[0] <= lg_max:
        raise ValueError(f"sequence of length {s.shape[0]} is too short for LG = {lg_max}")
    return s


def pssm_dt(pssm: np.ndarray, lg_max: int = DEFAULT_LG) -> np.ndarray:
    """PSSM-DT vector (400 * LG values): PSSM-SDT and PSSM-DDT for lg = 1..LG."""
    s = _check(pssm, lg_max)
    n = s.shape[0]
    out = [(s[: n - lg].T @ s[lg:]).ravel() / (n - lg) for lg in range(1, lg_max + 1)]
    return np.concatenate(out)


def feature_names(lg_max: int = DEFAULT_LG) -> list[str]:
    """Names of the PSSM-DT features, in vector order: ``A-R_lg1`` is DT(A, R, 1)."""
    return [f"{a}-{b}_lg{lg}" for lg in range(1, lg_max + 1) for a in AMINO_ACIDS for b in AMINO_ACIDS]


def sdt_mask(lg_max: int = DEFAULT_LG) -> np.ndarray:
    """Boolean mask of the PSSM-SDT features (same amino acid) within a PSSM-DT vector."""
    return np.tile(np.eye(20, dtype=bool).ravel(), lg_max)


def pssm_sdt(pssm: np.ndarray, lg_max: int = DEFAULT_LG) -> np.ndarray:
    """PSSM-SDT vector (20 * LG values)."""
    return pssm_dt(pssm, lg_max)[sdt_mask(lg_max)]


def pssm_ddt(pssm: np.ndarray, lg_max: int = DEFAULT_LG) -> np.ndarray:
    """PSSM-DDT vector (380 * LG values)."""
    return pssm_dt(pssm, lg_max)[~sdt_mask(lg_max)]


def logistic(pssm: np.ndarray) -> np.ndarray:
    """The normalisation of Lou et al. 2014: 1 / (1 + exp(-x))."""
    return 1.0 / (1.0 + np.exp(-np.asarray(pssm, dtype=np.float64)))


def ave_pscore_20(pssm: np.ndarray) -> np.ndarray:
    """AvePscore-20: mean of each column of the normalised PSSM."""
    return logistic(pssm).mean(axis=0)


def ave_pscore_400(pssm: np.ndarray, sequence: str) -> np.ndarray:
    """AvePscore-400: mean normalised score of column a over the residues of type r (r-major)."""
    p = logistic(pssm)
    if len(sequence) != p.shape[0]:
        raise ValueError("sequence and PSSM lengths differ")
    seq = np.array(list(sequence.upper()))
    out = np.zeros((20, 20))
    for i, r in enumerate(AMINO_ACIDS):
        rows = p[seq == r]
        if len(rows):
            out[i] = rows.mean(axis=0)
    return out.ravel()


def pscore_100(pssm: np.ndarray, percents: Iterable[float] = (0, 25, 50, 75, 100)) -> np.ndarray:
    """Pscore-100: percentiles of each column of the normalised PSSM (column-major)."""
    p = logistic(pssm)
    return np.percentile(p, list(percents), axis=0).T.ravel()


def acc(pssm: np.ndarray, lg_max: int = DEFAULT_LG) -> np.ndarray:
    """Auto-cross covariance of the normalised PSSM, 400 * LG values."""
    p = logistic(pssm)
    p = _check(p - p.mean(axis=0), lg_max)
    n = p.shape[0]
    return np.concatenate([(p[: n - lg].T @ p[lg:]).ravel() / (n - lg) for lg in range(1, lg_max + 1)])


ENCODINGS = ("PSSM-DT", "PSSM-SDT", "PSSM-DDT", "AvePscore-20", "AvePscore-400", "Pscore-100", "ACC")


def encode(pssm: np.ndarray, sequence: str | None = None, encoding: str = "PSSM-DT",
           lg_max: int = DEFAULT_LG) -> np.ndarray:
    """One encoding of one PSSM, by name (see ``ENCODINGS``)."""
    if encoding == "PSSM-DT":
        return pssm_dt(pssm, lg_max)
    if encoding == "PSSM-SDT":
        return pssm_sdt(pssm, lg_max)
    if encoding == "PSSM-DDT":
        return pssm_ddt(pssm, lg_max)
    if encoding == "AvePscore-20":
        return ave_pscore_20(pssm)
    if encoding == "AvePscore-400":
        if sequence is None:
            raise ValueError("AvePscore-400 needs the sequence")
        return ave_pscore_400(pssm, sequence)
    if encoding == "Pscore-100":
        return pscore_100(pssm)
    if encoding == "ACC":
        return acc(pssm, lg_max)
    raise ValueError(f"unknown encoding {encoding!r}; choose one of {', '.join(ENCODINGS)}")
