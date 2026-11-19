"""GeCON: signed gene co-expression networks from local expression patterns.

Implemented from the text of Roy, Bhattacharyya and Kalita (2014), Eqs. (4) to (11).
Settings the paper does not state are arguments, with the defaults documented below.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np

#: tau, the angle tolerance in degrees. The paper reports good results "with tau ranging between 15 to 25".
DEFAULT_TAU = 20.0
#: theta, the support threshold as a fraction of the M - 1 edges ("above 50% of the total number of edges").
DEFAULT_THETA = 0.5


def edge_patterns(profile: Sequence[float] | np.ndarray, tie: int = 1) -> tuple[np.ndarray, np.ndarray]:
    """Regulation r_k (Eq. 4) and degree of fluctuation a_k in degrees (Eq. 5) of the M - 1 edges.

    ``profile`` is one gene (a 1-D array of M values) or a genes x M matrix; the result has the same
    leading shape with M - 1 columns. Eq. (4) does not cover equal neighbours (O_{k-1} = O_k); ``tie`` is
    the regulation given to them (default +1, the "otherwise" branch of Eq. 5).

    The paper's worked example (Figure 7): ``edge_patterns([343, 314, 409])`` gives angles 137.5 and 52.5
    (printed as 138 and 52) and regulation -1 and +1.
    """
    x = np.asarray(profile, dtype=float)
    prev, cur = x[..., :-1], x[..., 1:]
    r = np.where(prev < cur, 1, np.where(prev > cur, -1, tie)).astype(np.int8)
    ang = np.abs(np.degrees(np.arctan2(cur, prev)))
    a = np.where(cur < prev, 180.0 - ang, ang)
    return r, a


def _valid_edges(m: int, segments: Sequence[int] | None) -> np.ndarray:
    """Boolean mask of the M - 1 edges that do not join two separate segments (time series)."""
    ok = np.ones(m - 1, dtype=bool)
    if segments:
        if sum(segments) != m:
            raise ValueError(f"segments sum to {sum(segments)}, the data have {m} columns")
        pos = 0
        for s in segments[:-1]:
            pos += s
            ok[pos - 1] = False  # the edge from the last point of one segment to the first of the next
    return ok


@dataclass
class Supports:
    """Pairwise positive and negative supports (Eqs. 8 and 9), genes x genes, as fractions of the edges."""

    pos: np.ndarray
    neg: np.ndarray
    n_edges: int

    @property
    def total(self) -> np.ndarray:
        return self.pos + self.neg


def supports(
    data: np.ndarray,
    tau: float = DEFAULT_TAU,
    segments: Sequence[int] | None = None,
    neg_rule: str = "text",
    tie: int = 1,
    block: int = 512,
) -> Supports:
    """Pairwise Pos_support and Neg_support of every gene pair (the correlogram matrix, Eqs. 6 to 9).

    ``data`` is genes x conditions (M columns, in their order). ``segments`` splits the columns into
    separate series (for example five time series of 21 points); edges that join two series are left out
    and the supports are divided by the number of edges used.

    ``neg_rule`` picks the inverted-pattern test of Eq. (7):

    - ``"text"`` (default): |a_i + a_j - 180| < tau, as the text says ("we subtract 180 from the sum of
      degree of fluctuation values").
    - ``"printed"``: |180 - a_i + a_j| < tau, Eq. (7) as printed.
    """
    x = np.asarray(data, dtype=float)
    if x.ndim != 2 or x.shape[1] < 2:
        raise ValueError("data must be a genes x conditions matrix with at least two conditions")
    if not np.isfinite(x).all():
        raise ValueError("data contain missing or infinite values")
    r, a = edge_patterns(x, tie=tie)
    keep = _valid_edges(x.shape[1], segments)
    r, a = r[:, keep], a[:, keep]
    n, e = r.shape
    pos = np.zeros((n, n), dtype=np.int32)
    neg = np.zeros((n, n), dtype=np.int32)
    for i0 in range(0, n, block):
        ri, ai = r[i0:i0 + block], a[i0:i0 + block]
        for k in range(e):
            rr = ri[:, k][:, None] * r[:, k][None, :]  # +1 same regulation, -1 inverted
            ai_k, aj_k = ai[:, k][:, None], a[:, k][None, :]
            pos[i0:i0 + block] += (rr == 1) & (np.abs(ai_k - aj_k) < tau)
            if neg_rule == "text":
                nd = np.abs(ai_k + aj_k - 180.0)
            elif neg_rule == "printed":
                nd = np.abs(180.0 - ai_k + aj_k)
            else:
                raise ValueError("neg_rule must be 'text' or 'printed'")
            neg[i0:i0 + block] += (rr == -1) & (nd < tau)
    if neg_rule == "printed":
        neg = np.maximum(neg, neg.T)  # the printed test is not symmetric; count a pair if either order holds
    np.fill_diagonal(pos, 0)
    np.fill_diagonal(neg, 0)
    return Supports(pos / e, neg / e, e)


def network(sup: Supports, theta: float = DEFAULT_THETA) -> np.ndarray:
    """Signed adjacency matrix A (Eqs. 10 and 11): +1, -1 or 0 for each gene pair.

    Two genes are strongly connected when Pos_support + Neg_support > theta (Definition 3). The sign is +1
    when Pos_support > theta and -1 when Neg_support > theta (Eq. 10). The paper does not say which sign a
    connected pair gets when neither support alone exceeds theta; we give it the sign of the larger support
    (+1 on a tie).
    """
    total = sup.total
    conn = total > theta
    sign = np.where(sup.pos >= sup.neg, 1, -1)
    A = np.where(conn, sign, 0).astype(np.int8)
    np.fill_diagonal(A, 0)
    return A


def gecon(
    data: np.ndarray,
    theta: float = DEFAULT_THETA,
    tau: float = DEFAULT_TAU,
    segments: Sequence[int] | None = None,
    **kwargs,
) -> tuple[np.ndarray, Supports]:
    """Run GeCON (Algorithm 1): the signed adjacency matrix and the supports behind it."""
    sup = supports(data, tau=tau, segments=segments, **kwargs)
    return network(sup, theta=theta), sup


def edge_list(A: np.ndarray, sup: Supports, genes: Sequence[str] | None = None) -> list[dict]:
    """The connected pairs (i < j) as dicts with gene names, sign and both supports, strongest first."""
    n = A.shape[0]
    names = list(genes) if genes is not None else [f"G{i + 1}" for i in range(n)]
    iu, ju = np.nonzero(np.triu(A != 0, 1))
    rows = [
        {
            "gene1": names[i],
            "gene2": names[j],
            "sign": int(A[i, j]),
            "pos_support": float(sup.pos[i, j]),
            "neg_support": float(sup.neg[i, j]),
        }
        for i, j in zip(iu, ju)
    ]
    rows.sort(key=lambda d: (-(d["pos_support"] + d["neg_support"]), d["gene1"], d["gene2"]))
    return rows


def modules(A: np.ndarray, min_size: int = 2) -> list[list[int]]:
    """Connected components of the network (genes sharing a co-expression network), largest first."""
    n = A.shape[0]
    seen = np.zeros(n, dtype=bool)
    out = []
    adj = [np.nonzero(A[i])[0] for i in range(n)]
    for s in range(n):
        if seen[s]:
            continue
        stack, comp = [s], []
        seen[s] = True
        while stack:
            v = stack.pop()
            comp.append(v)
            for w in adj[v]:
                if not seen[w]:
                    seen[w] = True
                    stack.append(w)
        if len(comp) >= min_size:
            out.append(sorted(comp))
    out.sort(key=lambda c: (-len(c), c[0]))
    return out


# ---------------------------------------------------------------------------------------------- input / output


def read_matrix(path: str | Path) -> tuple[list[str], list[str], np.ndarray]:
    """Read a tab- or comma-separated matrix: a header row (first cell ignored), then one row per gene with
    its name in the first column. Returns (genes, conditions, genes x conditions array)."""
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    delim = "\t" if "\t" in text.splitlines()[0] else ","
    rows = list(csv.reader(text.splitlines(), delimiter=delim))
    header = rows[0][1:]
    genes, vals = [], []
    for row in rows[1:]:
        if not row or not row[0].strip():
            continue
        genes.append(row[0].strip())
        vals.append([float(v) for v in row[1:1 + len(header)]])
    return genes, header, np.array(vals, dtype=float)


def write_edges(rows: Iterable[dict], f) -> None:
    """Write an edge list (from :func:`edge_list`) as CSV."""
    w = csv.writer(f, lineterminator="\n")
    w.writerow(["gene1", "gene2", "sign", "pos_support", "neg_support"])
    for d in rows:
        w.writerow([d["gene1"], d["gene2"], d["sign"], f"{d['pos_support']:.6g}", f"{d['neg_support']:.6g}"])


def read_edges(path: str | Path) -> list[dict]:
    """Read an edge list written by :func:`write_edges`."""
    with open(path, newline="", encoding="utf-8") as f:
        return [
            {
                "gene1": d["gene1"],
                "gene2": d["gene2"],
                "sign": int(d["sign"]),
                "pos_support": float(d["pos_support"]),
                "neg_support": float(d["neg_support"]),
            }
            for d in csv.DictReader(f)
        ]
