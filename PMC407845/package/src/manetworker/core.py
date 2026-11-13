"""MA-Networker: transcription factor activity and regulatory coupling (Gao, Foat and Bussemaker 2004).

Implemented from the paper's Methods; the authors' code was never released.

Step 1. For each microarray experiment t, regress the expression log-ratios E_gt of all genes on the
ChIP occupancy log-ratios B_fg of the transcription factors (TFs):

    E_gt = F_0t + sum_f F_ft B_fg + noise.

The regression coefficients F_ft, over all experiments, are the TF activity profile (TFAP) of f.
Backward selection drops uninformative TFs: rank TFs by their smallest coefficient P-value over all
experiments and drop the least significant until every TF is significant at P < alpha
(0.005 / number of experiments in the paper).

Step 2. The coupling of gene g to TF f is the Pearson correlation r between E_g. and F_f. across
experiments, with P from t = r sqrt((n - 2) / (1 - r^2)) on n - 2 degrees of freedom. Coupled (C+)
genes pass a Benjamini-Hochberg false discovery rate of 5%. Bound (B+) genes have a ChIP P-value
below 1e-3. Each gene is B-, B+/C+, B+/C- or unclassified (no expression or no ChIP ratio).

Missing values are NaN. Each regression uses the genes measured in that experiment, and each
correlation uses the experiments in which the gene was measured.
"""

from __future__ import annotations

import csv
import json
from collections.abc import Sequence
from pathlib import Path

import numpy as np
from scipy import stats

CLASSES = ("B-", "B+/C+", "B+/C-", "unclassified")


# ---------------------------------------------------------------------------------------------
# Step 1: regression and backward selection


def _mask_groups(E: np.ndarray) -> list[tuple[np.ndarray, np.ndarray]]:
    """Group the columns of E by their pattern of measured genes: [(gene mask, column indices)]."""
    ok = ~np.isnan(E)
    keys: dict[bytes, list[int]] = {}
    for j in range(E.shape[1]):
        keys.setdefault(np.packbits(ok[:, j]).tobytes(), []).append(j)
    return [(ok[:, cols[0]], np.asarray(cols)) for cols in keys.values()]


def _gram(E: np.ndarray, B: np.ndarray, groups) -> list:
    """Per pattern of measured genes: n, X'X, X'Y and Y'Y with X = [1, B] (all TFs)."""
    out = []
    for gmask, cols in groups:
        X = np.column_stack([np.ones(int(gmask.sum())), B[gmask]])
        Y = E[gmask][:, cols]
        out.append((cols, X.shape[0], X.T @ X, X.T @ Y, (Y**2).sum(0)))
    return out


def regress_activities(E: np.ndarray, B: np.ndarray, groups=None, keep=None, gram=None) -> dict:
    """Fit E[:, t] = F0_t + B @ F[:, t] by least squares for every experiment t.

    E: genes x experiments (NaN = not measured). B: genes x TFs, no NaN (fill missing ChIP
    log-ratios first, see fill_binding). keep: use only these columns of B (default all).
    Returns {'coef': TFs x experiments, 'intercept', 'se', 't', 'p', 'df'}. The P-value of each
    coefficient is the partial F-test (equal to the two-sided t-test) for dropping that TF.
    """
    E = np.asarray(E, float)
    B = np.asarray(B, float)
    if E.shape[0] != B.shape[0]:
        raise ValueError(f"E has {E.shape[0]} genes, B has {B.shape[0]}")
    if not np.isfinite(B).all():
        raise ValueError("B has missing or infinite values; fill them first (fill_binding)")
    if gram is None:
        gram = _gram(E, B, groups if groups is not None else _mask_groups(E))
    keep = list(range(B.shape[1])) if keep is None else list(keep)
    sub = np.array([0] + [k + 1 for k in keep])
    n_tf, n_exp = len(keep), E.shape[1]
    coef = np.full((n_tf, n_exp), np.nan)
    se = np.full((n_tf, n_exp), np.nan)
    icpt = np.full(n_exp, np.nan)
    df = np.zeros(n_exp, int)
    for cols, n, xtx, xty, yty in gram:
        k = len(sub)
        if n <= k:
            raise ValueError(f"{n} genes measured for {k} parameters in experiments {cols[:3]}...")
        A = xtx[np.ix_(sub, sub)]
        b = xty[sub]
        inv = np.linalg.inv(A)
        beta = inv @ b
        rss = np.maximum(yty - (beta * b).sum(0), 0.0)
        sigma2 = rss / (n - k)
        coef[:, cols] = beta[1:]
        icpt[cols] = beta[0]
        se[:, cols] = np.sqrt(np.outer(np.diag(inv)[1:], sigma2))
        df[cols] = n - k
    with np.errstate(invalid="ignore", divide="ignore"):
        t = coef / se
    p = 2 * stats.t.sf(np.abs(t), df[None, :])
    return {"coef": coef, "intercept": icpt, "se": se, "t": t, "p": p, "df": df}


def backward_select(E: np.ndarray, B: np.ndarray, alpha: float | None = None, names=None) -> dict:
    """Backward elimination of TFs (Step 1 of the paper).

    Each round fits all experiments with the remaining TFs, gives each TF its smallest coefficient
    P-value over all experiments, and drops the TF whose smallest P-value is largest, until every
    remaining TF has a smallest P-value below alpha (default 0.005 / number of experiments).
    Returns {'selected': indices into B's columns, 'dropped': [(index, min P when dropped)],
    'fit': the final regress_activities result, 'alpha'}.
    """
    E = np.asarray(E, float)
    if alpha is None:
        alpha = 0.005 / E.shape[1]
    keep = list(range(B.shape[1]))
    dropped = []
    gram = _gram(E, np.asarray(B, float), _mask_groups(E))
    while keep:
        fit = regress_activities(E, B, keep=keep, gram=gram)
        minp = np.nanmin(fit["p"], axis=1)
        worst = int(np.argmax(minp))
        if minp[worst] < alpha:
            break
        dropped.append((keep[worst], float(minp[worst])))
        del keep[worst]
    out = {"selected": keep, "dropped": dropped, "fit": fit, "alpha": alpha}
    if names is not None:
        out["selected_names"] = [names[i] for i in keep]
    return out


def fill_binding(log_ratio: np.ndarray, value: float = 0.0) -> np.ndarray:
    """Missing (NaN or infinite) ChIP log-ratios set to `value` (0: no enrichment)."""
    out = np.array(log_ratio, float)
    out[~np.isfinite(out)] = value
    return out


def log_ratio(ratio: np.ndarray) -> np.ndarray:
    """log2 of ChIP ratios; ratios that are missing or not positive become NaN."""
    r = np.array(ratio, float)
    out = np.full(r.shape, np.nan)
    ok = np.isfinite(r) & (r > 0)
    out[ok] = np.log2(r[ok])
    return out


# ---------------------------------------------------------------------------------------------
# Step 2: coupling


def coupling(E: np.ndarray, F: np.ndarray, min_n: int = 3) -> dict:
    """Pearson correlation of each gene's expression profile with each TF activity profile.

    E: genes x experiments (NaN allowed). F: TFs x experiments (no NaN). Each pair uses the
    experiments in which the gene was measured. Returns {'r', 't', 'p', 'n'} (genes x TFs); P is
    two-sided from t = r sqrt((n - 2) / (1 - r^2)) on n - 2 degrees of freedom.
    """
    E = np.asarray(E, float)
    F = np.asarray(F, float)
    if np.isnan(F).any():
        raise ValueError("F has missing values")
    M = (~np.isnan(E)).astype(float)
    X = np.where(M > 0, E, 0.0)
    n = M.sum(1)[:, None]
    sx = X.sum(1)[:, None]
    sxx = (X**2).sum(1)[:, None]
    sy = M @ F.T
    syy = M @ (F**2).T
    sxy = X @ F.T
    with np.errstate(invalid="ignore", divide="ignore"):
        cov = sxy - sx * sy / n
        vx = sxx - sx**2 / n
        vy = syy - sy**2 / n
        r = cov / np.sqrt(vx * vy)
        r = np.clip(r, -1.0, 1.0)
        dfree = n - 2
        t = r * np.sqrt(dfree / (1 - r**2))
    p = 2 * stats.t.sf(np.abs(t), np.maximum(dfree, 1))
    bad = (n[:, 0] < min_n) | ~np.isfinite(vx[:, 0]) | (vx[:, 0] <= 0)
    for a in (r, t, p):
        a[bad] = np.nan
    return {"r": r, "t": t, "p": p, "n": np.broadcast_to(n, r.shape).astype(int)}


def bh_reject(p: np.ndarray, q: float = 0.05) -> np.ndarray:
    """Benjamini-Hochberg: True where a P-value passes the false discovery rate q (NaN: False)."""
    p = np.asarray(p, float)
    flat = p.ravel()
    ok = ~np.isnan(flat)
    out = np.zeros(flat.shape, bool)
    pv = flat[ok]
    m = pv.size
    if m:
        order = np.argsort(pv, kind="mergesort")
        ranked = pv[order] * m / np.arange(1, m + 1)
        passed = ranked <= q
        if passed.any():
            kmax = np.nonzero(passed)[0].max()
            sel = np.zeros(m, bool)
            sel[order[: kmax + 1]] = True
            out[np.nonzero(ok)[0]] = sel
    return out.reshape(p.shape)


def coupled(p: np.ndarray, q: float = 0.05, scope: str = "per_tf", bound=None) -> np.ndarray:
    """C+ calls from coupling P-values (genes x TFs) at false discovery rate q.

    scope 'per_tf': BH over the genes of each TF separately; 'all': over every gene-TF pair;
    'bound': per TF, over its bound genes only (`bound`, genes x TFs boolean, required).
    """
    p = np.asarray(p, float)
    if scope == "all":
        return bh_reject(p, q)
    out = np.zeros(p.shape, bool)
    for j in range(p.shape[1]):
        col = p[:, j].copy()
        if scope == "bound":
            if bound is None:
                raise ValueError("scope 'bound' needs the bound matrix")
            col[~bound[:, j]] = np.nan
        elif scope != "per_tf":
            raise ValueError(f"unknown scope {scope!r}")
        out[:, j] = bh_reject(col, q)
    return out


def classify(bound: np.ndarray, coupled_: np.ndarray, available: np.ndarray) -> np.ndarray:
    """Class of each gene for each TF: 0 B-, 1 B+/C+, 2 B+/C-, 3 unclassified (genes x TFs)."""
    cls = np.where(bound, np.where(coupled_, 1, 2), 0)
    return np.where(available, cls, 3)


def class_counts(cls: np.ndarray) -> np.ndarray:
    """Counts of the four classes per TF: TFs x 4 (B-, B+/C+, B+/C-, unclassified)."""
    return np.stack([(cls == k).sum(0) for k in range(4)], axis=1)


def run(
    E: np.ndarray,
    B: np.ndarray,
    B_p: np.ndarray,
    tf_names: Sequence[str],
    alpha: float | None = None,
    bind_p: float = 1e-3,
    q: float = 0.05,
    scope: str = "per_tf",
    expr_available: np.ndarray | None = None,
    select: bool = True,
    profile: str = "coef",
    sided: str = "two",
) -> dict:
    """The whole method: backward selection, activity profiles, coupling and classification.

    E: genes x experiments log-ratios (NaN missing). B: genes x TFs ChIP log-ratios (NaN
    missing; see log_ratio). B_p: genes x TFs ChIP P-values. expr_available: genes measured well enough to be
    classified (default: genes with at least 3 measured experiments).
    profile: 'coef' (regression coefficients, as the paper's text says) or 't' (their t-values, as
    the paper's Fig. 1b plots). sided: 'two' (two-sided coupling test) or 'one' (positive
    correlation only, as the paper's Fig. 1c shows).
    Returns a dict with 'tfs' (selected names), 'activity' (TFs x experiments), 'coupling'
    (genes x TFs dict), 'classes' (genes x TFs) and 'counts' (TFs x 4).
    """
    E = np.asarray(E, float)
    B = np.asarray(B, float)
    B_p = np.asarray(B_p, float)
    Bf = fill_binding(B)
    if select:
        sel = backward_select(E, Bf, alpha)
        idx = sel["selected"]
        fit = sel["fit"]
    else:
        idx = list(range(Bf.shape[1]))
        fit = regress_activities(E, Bf)
        sel = None
    if profile not in ("coef", "t") or sided not in ("one", "two"):
        raise ValueError("profile must be 'coef' or 't', sided 'one' or 'two'")
    F = fit["coef"] if profile == "coef" else fit["t"]
    c = coupling(E, F)
    pc = c["p"] if sided == "two" else np.where(c["r"] > 0, c["p"] / 2, 1 - c["p"] / 2)
    if expr_available is None:
        expr_available = (~np.isnan(E)).sum(1) >= 3
    bnd = B_p[:, idx] < bind_p
    avail = expr_available[:, None] & np.isfinite(B[:, idx])
    cp = coupled(pc, q, scope, bound=bnd & avail)
    cls = classify(bnd, cp, avail)
    return {
        "coupling_p": pc,
        "tfs": [tf_names[i] for i in idx],
        "tf_index": idx,
        "selection": sel,
        "activity": F,
        "activity_t": fit["t"],
        "coupling": c,
        "classes": cls,
        "counts": class_counts(cls),
    }


# ---------------------------------------------------------------------------------------------
# File helpers


def read_matrix(path: str | Path) -> tuple[list[str], list[str], np.ndarray]:
    """Read a tab-separated matrix: first column row names, header row column names; blank = NaN."""
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f, delimiter="\t"))
    cols = rows[0][1:]
    names = [r[0] for r in rows[1:]]
    vals = np.array([[float(x) if x.strip() else np.nan for x in r[1:]] for r in rows[1:]], float)
    return names, cols, vals


def write_matrix(path, row_names, col_names, values, fmt="%.6g") -> None:
    """Write a matrix as read_matrix reads it (NaN written blank)."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow([""] + list(col_names))
        for name, row in zip(row_names, values):
            w.writerow([name] + ["" if np.isnan(v) else fmt % v for v in row])


def write_counts(path, tfs, counts) -> None:
    """Class counts per TF as CSV (tf, B-, B+/C+, B+/C-, unclassified)."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["tf", *CLASSES])
        for tf, row in zip(tfs, counts):
            w.writerow([tf, *map(int, row)])


def to_json(result: dict) -> str:
    """Selected TFs and class counts of a run() result as JSON."""
    return json.dumps(
        {"tfs": result["tfs"], "counts": {tf: dict(zip(CLASSES, map(int, row))) for tf, row in zip(result["tfs"], result["counts"])}},
        indent=1,
    )
