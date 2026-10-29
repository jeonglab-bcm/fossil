"""Local ASH, rebuilt: double dynamic programming seeds for NER maximization (RASH without crossover).

From the papers:
  - Local environment of residue i: vectors from its beta carbon to those of residues within the
    alignment radius (14 A), in a local frame of residue i, ordered by sequence (2005 GASH paper),
    restricted to a sequence window of +/-10 residues (2007 paper).
  - Lower DP aligns two environments with s(x, y) = a / (|V_ix - V_jy|^2 + b) (Toh, US patent
    6,125,331, FIG. 5); internal gaps open 10, extend 0.5, terminal gaps free (2005).
  - The lower DP runs only for residues with the same secondary structure (2007); otherwise
    s(i, j) = 0 (patent).
  - Upper DP: Smith-Waterman, gaps 10 and 0.5; repeated traceback with the path cleared, up to
    25 alignments (2005).
  - Each alignment is split into geometrically consistent sub-alignments: a pair joins a
    sub-alignment when every intramolecular distance to its members agrees within 10 A; a pair
    may join several (2005). Each sub-alignment goes through NER maximization; the best NER wins.
Not in the papers, so chosen here: a = 100, b = 10; the local frame (x along CA->CB, z normal to
CA->CB and CA->N); virtual CB for glycine; Smith-Waterman scores offset by the mean of s so that
alignments stay local; the path clearing removes only the path's own cells.
"""
import numpy as np
from numba import njit

import ash

A_CONST, B_CONST = 100.0, 10.0
RADIUS, WINDOW = 14.0, 10
GAP_OPEN, GAP_EXT = 10.0, 0.5
N_ALIGN, PARSE_TOL = 25, 10.0


def beta_carbons(dom):
    """Ideal CB from N, CA, C (used for every residue, as its position is defined for glycine too)."""
    b = dom.ca - dom.n
    c = dom.c - dom.ca
    a = np.cross(b, c)
    return -0.58273431 * a + 0.56802827 * b - 0.54067466 * c + dom.ca


def environments(dom, cb):
    """For each residue: (sequence offsets, vectors in its local frame)."""
    L = len(cb)
    out = []
    for i in range(L):
        x = cb[i] - dom.ca[i]
        x /= np.linalg.norm(x)
        nvec = dom.n[i] - dom.ca[i]
        z = np.cross(x, nvec)
        z /= np.linalg.norm(z)
        y = np.cross(z, x)
        lo, hi = max(0, i - WINDOW), min(L, i + WINDOW + 1)
        ks = [k for k in range(lo, hi) if k != i and np.linalg.norm(cb[k] - cb[i]) < RADIUS]
        v = (cb[ks] - cb[i]) @ np.array([x, y, z]).T if ks else np.zeros((0, 3))
        out.append(np.ascontiguousarray(v))
    return out


@njit
def lower_dp(u, v, a, b, go, ge):
    """Global alignment of two vector lists, free terminal gaps; returns the best score."""
    n, m = u.shape[0], v.shape[0]
    if n == 0 or m == 0:
        return 0.0
    NEG = -1e18
    M = np.zeros((n + 1, m + 1))
    X = np.full((n + 1, m + 1), NEG)
    Y = np.full((n + 1, m + 1), NEG)
    best = 0.0
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            d = 0.0
            for k in range(3):
                t = u[i - 1, k] - v[j - 1, k]
                d += t * t
            s = a / (d + b)
            M[i, j] = max(M[i - 1, j - 1], X[i - 1, j - 1], Y[i - 1, j - 1]) + s
            X[i, j] = max(M[i - 1, j] - go, X[i - 1, j] - ge)
            Y[i, j] = max(M[i, j - 1] - go, Y[i, j - 1] - ge)
            if (i == n or j == m) and M[i, j] > best:
                best = M[i, j]
    return best


def similarity(env_q, env_t, ss_q, ss_t):
    n, m = len(env_q), len(env_t)
    S = np.zeros((n, m))
    for i in range(n):
        for j in range(m):
            if ss_q[i] == ss_t[j]:
                S[i, j] = lower_dp(env_q[i], env_t[j], A_CONST, B_CONST, GAP_OPEN, GAP_EXT)
    return S


@njit
def smith_waterman(S, go, ge):
    """Local alignment with affine gaps and explicit traceback pointers."""
    n, m = S.shape
    NEG = -1e18
    H = np.zeros((n + 1, m + 1))
    E = np.full((n + 1, m + 1), NEG)
    F = np.full((n + 1, m + 1), NEG)
    pH = np.zeros((n + 1, m + 1), dtype=np.int8)   # 0 start, 1 diagonal, 2 from E, 3 from F
    pE = np.zeros((n + 1, m + 1), dtype=np.int8)   # 0 opened from H, 1 extended
    pF = np.zeros((n + 1, m + 1), dtype=np.int8)
    bi, bj, bv = 0, 0, 0.0
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            a, b = H[i - 1, j] - go, E[i - 1, j] - ge
            E[i, j], pE[i, j] = (a, 0) if a >= b else (b, 1)
            a, b = H[i, j - 1] - go, F[i, j - 1] - ge
            F[i, j], pF[i, j] = (a, 0) if a >= b else (b, 1)
            h, p = 0.0, 0
            d = H[i - 1, j - 1] + S[i - 1, j - 1]
            if d > h:
                h, p = d, 1
            if E[i, j] > h:
                h, p = E[i, j], 2
            if F[i, j] > h:
                h, p = F[i, j], 3
            H[i, j], pH[i, j] = h, p
            if h > bv:
                bi, bj, bv = i, j, h
    out = np.empty((min(n, m), 2), dtype=np.int64)
    k, i, j, state = 0, bi, bj, 0
    while i > 0 and j > 0:
        if state == 0:
            p = pH[i, j]
            if p == 0:
                break
            if p == 1:
                out[k, 0], out[k, 1] = i - 1, j - 1
                k += 1
                i -= 1
                j -= 1
            else:
                state = p - 1
        elif state == 1:
            state = 0 if pE[i, j] == 0 else 1
            i -= 1
        else:
            state = 0 if pF[i, j] == 0 else 2
            j -= 1
    return out[:k][::-1].copy(), bv


def local_alignments(S):
    S = S - S.mean()
    out = []
    for _ in range(N_ALIGN):
        path, score = smith_waterman(S, GAP_OPEN, GAP_EXT)
        if len(path) < 3 or score <= 0:
            break
        out.append(path)
        S = S.copy()
        S[path[:, 0], path[:, 1]] = -1e6    # declump: the next traceback cannot reuse these cells
    return out


def parse(pairs, Xq, Xt, tol=PARSE_TOL):
    dq = np.sqrt(((Xq[pairs[:, 0], None] - Xq[None, pairs[:, 0]]) ** 2).sum(2))
    dt = np.sqrt(((Xt[pairs[:, 1], None] - Xt[None, pairs[:, 1]]) ** 2).sum(2))
    ok = np.abs(dq - dt) < tol
    subs = []
    for k in range(len(pairs)):
        placed = False
        for s in subs:
            if ok[k, s].all():
                s.append(k)
                placed = True
        if not placed:
            subs.append([k])
    return [pairs[s] for s in subs if len(s) >= 3]


def seeds(q, t, ss_q, ss_t):
    env_q, env_t = environments(q, beta_carbons(q)), environments(t, beta_carbons(t))
    S = similarity(env_q, env_t, ss_q, ss_t)
    subs = []
    for path in local_alignments(S):
        subs += parse(path, q.ca, t.ca)
    return subs


def rash(q, t, ss_q, ss_t, extra_seeds=()):
    """Best NER over the NER maximization of every seed."""
    best = None
    for seed in list(seeds(q, t, ss_q, ss_t)) + list(extra_seeds):
        pairs, R, tr = ash.ner_maximization(q.ca, t.ca, seed)
        ner = ash.ner_value(q.ca @ R.T + tr, t.ca, pairs)
        if best is None or ner > best[0]:
            best = (ner, pairs, R, tr)
    return best
