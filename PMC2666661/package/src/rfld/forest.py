"""Random forest for categorical predictors, after Breiman and Cutler's Fortran Random Forests 5.1,
with the two revisions of Meng et al. (2009):

* RF1, the revised tree builder: once a tree splits on a variable, every variable whose pairwise
  r^2 with it exceeds a threshold R leaves the pool from which that tree draws split candidates.
  Variables in LD (r^2 > R) therefore never appear in the same tree.
* IM1, the revised importance: the permutation importance summed over trees is divided by T_v,
  the number of trees that split on the variable, instead of by T, the number of trees (IM0).

The tree builder follows Random Forests 5.1 (prog.f, subroutines buildtree, findbestsplit,
catmax, varimp, testreeimp, permobmr) step by step, for the case the paper used: every predictor
categorical, two classes, equal class weights, node size 1. In particular:

* the mtry candidate variables of a node are drawn with replacement from the pool;
* a categorical split is the best of all 2^(L-1) - 1 subsets of the L declared categories by the
  weighted Gini criterion, where in-bag cases are weighted by their bootstrap multiplicity; a
  subset that leaves a side empty is skipped; the first best split wins ties;
* a node is terminal when it holds one distinct case, is pure, or none of its mtry candidates
  can split it;
* nodes are split in creation order (breadth first), which is the order in which RF1 removes
  variables from the pool;
* the permutation importance of variable v in tree j is (right - right_v) / N_j over the
  out-of-bag cases, computed only for variables the tree splits on (zero otherwise); a fresh
  permutation of the out-of-bag cases is drawn for each variable.

The printed importance is 100 times the mean over trees, as prog.f writes it (``100*avimp``).
"""

from __future__ import annotations

import numpy as np
from numba import njit

__all__ = ["grow_forest", "r2_matrix"]


@njit(cache=True)
def _gini_best_subset(tcc0, tcc1, lcat, pdo, critmax):
    """Best subset split of one categorical variable (prog.f catmax). Returns (crit, subset) with
    subset = 0 when no subset beats critmax."""
    best_sub = 0
    for sub in range(1, (1 << (lcat - 1))):
        l0 = 0.0
        l1 = 0.0
        for c in range(lcat):
            if (sub >> c) & 1:
                l0 += tcc0[c]
                l1 += tcc1[c]
        pld = l0 + l1
        prd = pdo - pld
        if pld <= 0.0 or prd <= 0.0:
            continue  # 0/0 in prog.f: the comparison with critmax is false
        r0 = 0.0
        r1 = 0.0
        for c in range(lcat):
            r0 += tcc0[c]
            r1 += tcc1[c]
        r0 -= l0
        r1 -= l1
        tdec = (l0 * l0 + l1 * l1) / pld + (r0 * r0 + r1 * r1) / prd
        if tdec > critmax:
            critmax = tdec
            best_sub = sub
    return critmax, best_sub


@njit(cache=True)
def _grow_tree(X, y, ncat, mtry, ld, use_ld, jin,
               bestvar, bestsub, left, right, status, nodeclass, used, drop_self):
    """Grow one tree on the in-bag cases (jin > 0). Fills the node arrays and returns the number
    of nodes. status: 1 split, -1 terminal."""
    n, p = X.shape
    nrnodes = bestvar.shape[0]
    maxcat = tcc_size = 0
    for v in range(p):
        if ncat[v] > maxcat:
            maxcat = ncat[v]
    tcc0 = np.zeros(maxcat)
    tcc1 = np.zeros(maxcat)

    # in-bag cases in index order (prog.f moda), and their node ranges
    cases = np.empty(n, np.int64)
    nuse = 0
    for i in range(n):
        if jin[i] > 0:
            cases[nuse] = i
            nuse += 1
    tmp = np.empty(n, np.int64)
    start = np.zeros(nrnodes, np.int64)
    pop = np.zeros(nrnodes, np.int64)
    cp0 = np.zeros(nrnodes)
    cp1 = np.zeros(nrnodes)
    for k in range(nrnodes):
        status[k] = 0
        bestvar[k] = -1
        bestsub[k] = 0
        left[k] = -1
        right[k] = -1
        nodeclass[k] = 0
    for v in range(p):
        used[v] = False

    pool = np.arange(p)
    npool = p
    for t in range(nuse):
        i = cases[t]
        if y[i] == 0:
            cp0[0] += jin[i]
        else:
            cp1[0] += jin[i]
    start[0] = 0
    pop[0] = nuse
    status[0] = 2
    ncur = 0  # index of the last node created

    for kb in range(nrnodes):
        if kb > ncur:
            break
        if status[kb] != 2:
            continue
        s = start[kb]
        e = s + pop[kb]
        pdo = cp0[kb] + cp1[kb]
        critmax = -1.0e20
        msplit = -1
        msub = 0
        for mv in range(mtry):
            k = int(npool * np.random.random())
            if k >= npool:
                k = npool - 1
            v = pool[k]
            lcat = ncat[v]
            for c in range(lcat):
                tcc0[c] = 0.0
                tcc1[c] = 0.0
            for t in range(s, e):
                i = cases[t]
                c = X[i, v]
                if y[i] == 0:
                    tcc0[c] += jin[i]
                else:
                    tcc1[c] += jin[i]
            crit, sub = _gini_best_subset(tcc0, tcc1, lcat, pdo, critmax)
            if sub != 0:
                critmax = crit
                msplit = v
                msub = sub
        if msplit < 0:
            status[kb] = -1
            continue
        if ncur + 2 >= nrnodes:
            status[kb] = -1
            break
        bestvar[kb] = msplit
        bestsub[kb] = msub
        used[msplit] = True
        # stable partition: left (category bit set) first
        nl = 0
        for t in range(s, e):
            i = cases[t]
            if (msub >> X[i, msplit]) & 1:
                tmp[nl] = i
                nl += 1
        nr = nl
        for t in range(s, e):
            i = cases[t]
            if not ((msub >> X[i, msplit]) & 1):
                tmp[nr] = i
                nr += 1
        for t in range(e - s):
            cases[s + t] = tmp[t]
        lft = ncur + 1
        rgt = ncur + 2
        start[lft] = s
        pop[lft] = nl
        start[rgt] = s + nl
        pop[rgt] = (e - s) - nl
        for t in range(s, s + nl):
            i = cases[t]
            if y[i] == 0:
                cp0[lft] += jin[i]
            else:
                cp1[lft] += jin[i]
        for t in range(s + nl, e):
            i = cases[t]
            if y[i] == 0:
                cp0[rgt] += jin[i]
            else:
                cp1[rgt] += jin[i]
        for ch in (lft, rgt):
            status[ch] = 2
            if pop[ch] <= 1:
                status[ch] = -1
            tot = cp0[ch] + cp1[ch]
            if cp0[ch] == tot or cp1[ch] == tot:
                status[ch] = -1
        left[kb] = lft
        right[kb] = rgt
        status[kb] = 1
        ncur += 2
        if use_ld:
            # RF1: drop every variable in LD (r^2 > R) with the one just used
            m = 0
            for q in range(npool):
                u = pool[q]
                if (u == msplit and not drop_self) or (u != msplit and not ld[msplit, u]):
                    pool[m] = u
                    m += 1
            npool = m
    nnodes = ncur + 1
    for k in range(nnodes):
        if status[k] == 2 or status[k] == 0:
            status[k] = -1
        if status[k] == -1:
            # class with the larger weight; ties go to the first class (prog.f)
            nodeclass[k] = 1 if cp1[k] > cp0[k] else 0
    return nnodes


@njit(cache=True)
def _predict_one(X, i, perm_var, perm_row, bestvar, bestsub, left, right, status, nodeclass):
    k = 0
    while status[k] != -1:
        v = bestvar[k]
        r = perm_row if v == perm_var else i
        if (bestsub[k] >> X[r, v]) & 1:
            k = left[k]
        else:
            k = right[k]
    return nodeclass[k]


@njit(cache=True)
def _forest(X, y, ncat, ntree, mtry, ld, use_ld, seed, drop_self):
    np.random.seed(seed)
    n, p = X.shape
    nrnodes = 2 * n + 1
    bestvar = np.empty(nrnodes, np.int64)
    bestsub = np.empty(nrnodes, np.int64)
    left = np.empty(nrnodes, np.int64)
    right = np.empty(nrnodes, np.int64)
    status = np.empty(nrnodes, np.int64)
    nodeclass = np.empty(nrnodes, np.int64)
    used = np.zeros(p, np.bool_)
    jin = np.zeros(n, np.int64)
    joob = np.empty(n, np.int64)
    pjoob = np.empty(n, np.int64)
    imp_sum = np.zeros(p)
    tv = np.zeros(p, np.int64)
    votes = np.zeros((n, 2), np.int64)
    for jb in range(ntree):
        for i in range(n):
            jin[i] = 0
        for i in range(n):
            k = int(np.random.random() * n)
            if k >= n:
                k = n - 1
            jin[k] += 1
        _grow_tree(X, y, ncat, mtry, ld, use_ld, jin,
                   bestvar, bestsub, left, right, status, nodeclass, used, drop_self)
        nout = 0
        rightc = 0
        for i in range(n):
            if jin[i] == 0:
                joob[nout] = i
                nout += 1
                cls = _predict_one(X, i, -1, i, bestvar, bestsub, left, right, status, nodeclass)
                votes[i, cls] += 1
                if cls == y[i]:
                    rightc += 1
        if nout == 0:
            continue
        for v in range(p):
            if not used[v]:
                continue
            tv[v] += 1
            # prog.f permobmr: shuffle a copy of the out-of-bag list
            for t in range(nout):
                pjoob[t] = joob[t]
            j = nout
            while j > 1:
                k = int(j * np.random.random())
                if k < j:
                    k += 1
                tmpv = pjoob[j - 1]
                pjoob[j - 1] = pjoob[k - 1]
                pjoob[k - 1] = tmpv
                j -= 1
            rimp = 0
            for t in range(nout):
                i = joob[t]
                cls = _predict_one(X, i, v, pjoob[t], bestvar, bestsub, left, right, status, nodeclass)
                if cls == y[i]:
                    rimp += 1
            imp_sum[v] += (rightc - rimp) / nout
    return imp_sum, tv, votes


def r2_matrix(X: np.ndarray) -> np.ndarray:
    """Pairwise squared Pearson correlation of genotype codes (columns of X). Constant columns get
    r^2 = 0 with every other column."""
    Z = np.asarray(X, dtype=float)
    Z = Z - Z.mean(axis=0)
    sd = np.sqrt((Z * Z).sum(axis=0))
    ok = sd > 0
    Z[:, ok] /= sd[ok]
    Z[:, ~ok] = 0.0
    r = Z.T @ Z
    r2 = r * r
    np.fill_diagonal(r2, 1.0)
    return r2


def grow_forest(X, y, *, ntree=5000, mtry=35, revised_tree=False, ld_threshold=0.5,
                ncat=None, seed=1, r2=None, drop_self=False):
    """Grow a forest and return its importances.

    Parameters
    ----------
    X : (n, p) integer array of category codes 0..L-1 (genotypes: number of risk alleles).
    y : (n,) array of classes 0 (control) and 1 (case).
    ntree, mtry : number of trees and of split candidates drawn (with replacement) at each node.
    revised_tree : False for the original tree builder (RF0), True for RF1.
    ld_threshold : RF1 removes variables with r^2 > ld_threshold with a variable already used.
    ncat : number of declared categories of each variable (default: max code + 1, at least 2).
    seed : random seed; the same inputs and seed give the same forest.
    r2 : optional precomputed (p, p) r^2 matrix (default: r2_matrix(X)).
    drop_self : RF1 only; also drop the variable just used from the tree's pool, so that every
        variable splits at most one node per tree (a reading of the paper we tested and rejected;
        see the reproduction's README).

    Returns a dict with ``im0`` (original importance, 100 x mean over all trees), ``im1`` (revised
    importance, 100 x mean over the trees that split on the variable; 0 if none), ``trees`` (T_v),
    ``ntree`` and ``oob_error``.
    """
    X = np.ascontiguousarray(X, dtype=np.int64)
    y = np.ascontiguousarray(y, dtype=np.int64)
    n, p = X.shape
    if y.shape != (n,):
        raise ValueError("y must have one class per row of X")
    if not set(np.unique(y)) <= {0, 1}:
        raise ValueError("y must hold classes 0 and 1")
    if X.min(initial=0) < 0:
        raise ValueError("X must hold category codes 0, 1, 2, ...")
    if ncat is None:
        ncat = np.maximum(X.max(axis=0) + 1, 2)
    ncat = np.ascontiguousarray(ncat, dtype=np.int64)
    if ncat.shape != (p,) or (X >= ncat).any():
        raise ValueError("ncat must give, for each column, more categories than its largest code")
    if ncat.max() > 30:
        raise ValueError("at most 30 categories per variable")
    if not 1 <= mtry:
        raise ValueError("mtry must be at least 1")
    if revised_tree:
        if r2 is None:
            r2 = r2_matrix(X)
        ld = np.ascontiguousarray(np.asarray(r2) > ld_threshold)
    else:
        ld = np.zeros((1, 1), np.bool_)
    imp_sum, tv, votes = _forest(X, y, ncat, int(ntree), int(mtry), ld, bool(revised_tree), int(seed),
                                 bool(drop_self and revised_tree))
    with np.errstate(invalid="ignore", divide="ignore"):
        im1 = np.where(tv > 0, 100.0 * imp_sum / np.maximum(tv, 1), 0.0)
    oob = votes.sum(axis=1) > 0
    pred = (votes[:, 1] > votes[:, 0]).astype(np.int64)
    err = float((pred[oob] != y[oob]).mean()) if oob.any() else float("nan")
    return {"im0": 100.0 * imp_sum / ntree, "im1": im1, "trees": tv, "ntree": int(ntree),
            "oob_error": err}
