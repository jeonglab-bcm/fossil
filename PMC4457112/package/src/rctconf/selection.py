"""Forward selection of whole feature sets by cross-validation (Cohen et al. 2015).

"Starting with no feature sets in the model, the addition of each feature set not yet included in
the model is tested for improvement using cross-validation and evaluation of AUC and F1. The feature
set that improves the model the most is added to the current model and the process repeated until no
remaining feature sets improve the model."

The paper does not say how AUC and F1 are combined. As in the same group's 2018 tagger
(PMC6146117), the set with the largest AUC gain is taken, F1 breaks ties in AUC, and neither may
fall. AUC is compared at four decimals unless auc_decimals says otherwise.
"""

from __future__ import annotations

import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import scipy.sparse as sp

from .metrics import auc, binary_measures
from .model import LIBLINEAR_OPTIONS, train_svm


def cv_splits(n: int, repeats: int = 5, seed: int = 0):
    """repeats x 2 cross-validation: for each repeat a random half-split, each half tested once."""
    rng = np.random.default_rng(seed)
    for _ in range(repeats):
        perm = rng.permutation(n)
        half = n // 2
        a, b = np.sort(perm[:half]), np.sort(perm[half:])
        yield a, b
        yield b, a


def _as_blocks(X):
    return list(X) if isinstance(X, (list, tuple)) else [X]


def _rows(blocks, idx):
    return sp.hstack([b[idx] for b in blocks], format="csr", dtype=np.float64)


def _block_margins(blocks, idx, w, b):
    f = np.full(len(idx), b, dtype=float)
    off = 0
    for blk in blocks:
        k = blk.shape[1]
        f += np.asarray(blk[idx] @ w[off : off + k]).ravel()
        off += k
    return f


def cross_validate(X, y, repeats: int = 5, seed: int = 0, options: str = LIBLINEAR_OPTIONS,
                   keep_margins: bool = False) -> dict:
    """Mean AUC, F1 and accuracy over repeats x 2 cross-validation.

    X is a CSR matrix or a list of CSR blocks (one per feature set) with the same rows; blocks are
    joined only for the training rows of each fold. With keep_margins, also each fold's test rows
    and margins.
    """
    blocks = _as_blocks(X)
    y = np.asarray(y).astype(bool)
    rows, folds = [], []
    for tr, te in cv_splits(len(y), repeats, seed):
        Xtr = _rows(blocks, tr)
        w, b = train_svm(Xtr, y[tr], options)
        del Xtr
        f = _block_margins(blocks, te, w, b)
        bm = binary_measures(y[te], f > 0)
        rows.append((auc(y[te], f), bm["f1"], bm["accuracy"]))
        if keep_margins:
            folds.append((te, f))
    r = np.array(rows)
    out = {"auc": float(r[:, 0].mean()), "f1": float(r[:, 1].mean()), "accuracy": float(r[:, 2].mean()),
           "folds": len(rows)}
    if keep_margins:
        out["fold_margins"] = folds
    return out


_SHARED: dict = {}


def _trial(args):
    sets, repeats, seed, options = args
    return cross_validate([_SHARED["blocks"][s] for s in sets], _SHARED["y"], repeats, seed, options)


def forward_select(blocks: dict, y, candidates, repeats: int = 5, seed: int = 0, options: str = LIBLINEAR_OPTIONS,
                   workers: int = 1, log=print, resume: dict | None = None, checkpoint=None,
                   auc_decimals: int = 4) -> dict:
    """Greedy forward selection over feature sets.

    blocks: {set name: CSR matrix, one row per citation}. Each candidate is scored by repeats x 2
    cross-validation of the chosen sets plus the candidate. workers > 1 scores candidates in
    parallel processes (fork). Returns the chosen sets in order and every step.
    resume: a partial result from checkpoint (its chosen sets and steps) to continue from;
    checkpoint(result): called after every step with the result so far.
    auc_decimals: AUC is compared rounded to this many decimals (4 by default).
    """
    y = np.asarray(y).astype(bool)
    _SHARED.update(blocks=blocks, y=y)
    chosen: list[str] = []
    best = {"auc": 0.0, "f1": 0.0}
    steps = []
    if resume:
        chosen = list(resume["chosen"])
        steps = list(resume["steps"])
        best = {"auc": resume["auc"], "f1": resume["f1"]}
        if steps and not steps[-1]["added"]:
            return {"chosen": chosen, "auc": best["auc"], "f1": best["f1"], "steps": steps}
    remaining = [s for s in candidates if s not in chosen]
    ctx = mp.get_context("fork") if workers > 1 else None
    try:
        while remaining:
            jobs = [(chosen + [s], repeats, seed, options) for s in remaining]
            if workers > 1:
                with ProcessPoolExecutor(min(workers, len(jobs)), mp_context=ctx) as ex:
                    res = list(ex.map(_trial, jobs))
            else:
                res = [_trial(j) for j in jobs]
            trials = dict(zip(remaining, res))
            for s in remaining:
                log(f"  + {s}: AUC {trials[s]['auc']:.4f} F1 {trials[s]['f1']:.4f}")
            d = auc_decimals
            pick = max(remaining, key=lambda s: (round(trials[s]["auc"], d), trials[s]["f1"]))
            r = trials[pick]
            improves = (round(r["auc"], d) > round(best["auc"], d)
                        or (round(r["auc"], d) == round(best["auc"], d) and r["f1"] > best["f1"]))
            steps.append({"step": len(chosen) + 1, "trials": trials, "best": pick, "auc": r["auc"], "f1": r["f1"],
                          "added": bool(improves)})
            if not improves:
                break
            chosen.append(pick)
            best = r
            remaining.remove(pick)
            log(f"step {len(chosen)}: {pick} (AUC {r['auc']:.4f}, F1 {r['f1']:.4f})")
            if checkpoint:
                checkpoint({"chosen": chosen, "auc": best["auc"], "f1": best["f1"], "steps": steps})
    finally:
        _SHARED.clear()
    return {"chosen": chosen, "auc": best["auc"], "f1": best["f1"], "steps": steps}
