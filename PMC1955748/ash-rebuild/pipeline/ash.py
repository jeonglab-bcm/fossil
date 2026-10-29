"""A rebuilt ASH: NER maximization (Standley et al. 2005, GASH) and the ASH score (Standley et al. 2007).

What follows the papers as written:
  - NER = sum over aligned pairs of exp(-(d/d0)^2), d0 = 4 A (2005 eq. 1-2; 2007 eq. 2-3).
  - NER maximization: minimize the CA RMSD of the aligned pairs, maximize NER over the
    superposition by conjugate gradients (Polak-Ribiere), then realign by ordinary dynamic
    programming on exp(-(d/d0)^2) with internal gap opening 0.25 and extension 0.125 and free
    terminal gaps (2005, "NER maximization").
  - The score terms and weights of the 2007 paper: eq. 1 to 6 and Table 1.
What does not: the seed alignments. ASH seeds from Local ASH (double dynamic programming,
14 A local environments, up to 25 alignments parsed by distance matrix); its code is lost.
We seed from TM-align instead (tmtools).
"""
import numpy as np
from numba import njit
from scipy.optimize import minimize
from scipy.spatial.transform import Rotation

D0 = 4.0
AA = 'ARNDCQEGHILKMFPSTWYV'

# Weights: 2007 paper, text (eq. 1 terms) and Table 1 (Dist descriptors).
WEIGHTS = {
    'full': dict(ner=0.12, seq=1.0, sas=0.85, gap=0.01, dist=1.1,
                 nr=51.94, rg=-0.33, co=0.96, alpha=3.21, beta=1.71),
    'reduced': dict(ner=3.0, seq=0.14, sas=10.9, gap=-0.1, dist=7.12,
                    nr=5.92, rg=-0.54, co=0.42, alpha=0.68, beta=0.76),
}


def read_matrix(path):
    """Additional File 2 (our transcription): lower triangle, rows A R N D ... V."""
    m = np.zeros((20, 20))
    for i, line in enumerate(open(path)):
        f = line.split()
        for j, v in enumerate(f[1:]):
            m[i, j] = m[j, i] = float(v)
    return m


def kabsch(P, Q):
    """R, t minimizing |R P + t - Q| over paired rows."""
    pc, qc = P.mean(0), Q.mean(0)
    H = (P - pc).T @ (Q - qc)
    U, _, Vt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    R = Vt.T @ np.diag([1, 1, d]) @ U.T
    return R, qc - R @ pc


def ner_value(Xs, Y, pairs):
    d2 = ((Xs[pairs[:, 0]] - Y[pairs[:, 1]]) ** 2).sum(1)
    return np.exp(-d2 / D0 ** 2).sum()


def maximize_ner(X, Y, pairs, R, t):
    """Maximize NER over rotation and translation from (R, t), by Polak-Ribiere conjugate gradients."""
    P, Q = X[pairs[:, 0]], Y[pairs[:, 1]]
    c = P.mean(0)
    r0 = Rotation.from_matrix(R)

    def f(v):
        rot = Rotation.from_rotvec(v[:3]) * r0
        diff = rot.apply(P - c) + (R @ c + t + v[3:]) - Q
        w = np.exp(-(diff ** 2).sum(1) / D0 ** 2)
        g_tr = (-2 / D0 ** 2) * (w[:, None] * diff).sum(0)
        # gradient in the rotation vector, at small v: d(diff)/dv = -[rot(P - c)]_x
        Pr = rot.apply(P - c)
        g_rot = (-2 / D0 ** 2) * (w[:, None] * np.cross(Pr, diff)).sum(0)
        return -w.sum(), -np.concatenate([g_rot, g_tr])

    res = minimize(f, np.zeros(6), jac=True, method='CG', options={'gtol': 1e-6, 'maxiter': 500})
    v = res.x
    rot = Rotation.from_rotvec(v[:3]) * r0
    Rn = rot.as_matrix()
    tn = R @ c + t + v[3:] - Rn @ c
    return Rn, tn


@njit
def dp_align(S, go, ge):
    """Global alignment maximizing sum S - gap penalties; terminal gaps free; affine internal gaps
    (a gap of length L costs go + (L - 1) ge). Returns aligned index pairs."""
    n, m = S.shape
    NEG = -1e18
    M = np.full((n + 1, m + 1), NEG)
    X = np.full((n + 1, m + 1), NEG)   # gap in Y (i advances)
    Yg = np.full((n + 1, m + 1), NEG)  # gap in X (j advances)
    for i in range(n + 1):
        M[i, 0] = 0.0
    for j in range(m + 1):
        M[0, j] = 0.0
    tb = np.zeros((3, n + 1, m + 1), dtype=np.int8)
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            # match state
            best, arg = M[i - 1, j - 1], 0
            if X[i - 1, j - 1] > best:
                best, arg = X[i - 1, j - 1], 1
            if Yg[i - 1, j - 1] > best:
                best, arg = Yg[i - 1, j - 1], 2
            M[i, j] = best + S[i - 1, j - 1]
            tb[0, i, j] = arg
            # gap states: open from M, extend from self (no free end gaps inside)
            a, b = M[i - 1, j] - go, X[i - 1, j] - ge
            if a >= b:
                X[i, j], tb[1, i, j] = a, 0
            else:
                X[i, j], tb[1, i, j] = b, 1
            a, b = M[i, j - 1] - go, Yg[i, j - 1] - ge
            if a >= b:
                Yg[i, j], tb[2, i, j] = a, 0
            else:
                Yg[i, j], tb[2, i, j] = b, 2
    # free terminal gaps: best M cell in the last row or column
    bi, bj, bv = n, m, M[n, m]
    for i in range(1, n + 1):
        if M[i, m] > bv:
            bi, bj, bv = i, m, M[i, m]
    for j in range(1, m + 1):
        if M[n, j] > bv:
            bi, bj, bv = n, j, M[n, j]
    out = np.empty((min(n, m), 2), dtype=np.int64)
    k, i, j, s = 0, bi, bj, 0
    while i > 0 and j > 0:
        if s == 0:
            if M[i, j] <= 0.0 and (i == 0 or j == 0):
                break
            out[k, 0], out[k, 1] = i - 1, j - 1
            k += 1
            s = tb[0, i, j]
            i -= 1
            j -= 1
            if s == 0 and (i == 0 or j == 0):
                break
        elif s == 1:
            s = 0 if tb[1, i, j] == 0 else 1
            i -= 1
        else:
            s = 0 if tb[2, i, j] == 0 else 2
            j -= 1
    return out[:k][::-1].copy()


def realign(X, Y, R, t, go=0.25, ge=0.125):
    Xs = X @ R.T + t
    d2 = ((Xs[:, None, :] - Y[None, :, :]) ** 2).sum(2)
    return dp_align(np.exp(-d2 / D0 ** 2), go, ge)


def ner_maximization(X, Y, pairs):
    """One round as in the GASH paper: RMSD fit, NER fit, realign, then the optimal NER of the new alignment."""
    R, t = kabsch(X[pairs[:, 0]], Y[pairs[:, 1]])
    R, t = maximize_ner(X, Y, pairs, R, t)
    new = realign(X, Y, R, t)
    # the optimal NER of the new alignment, maximized from the superposition that produced it
    R2, t2 = maximize_ner(X, Y, new, R, t)
    return new, R2, t2


# ---- descriptors (Table 1) ----

def radius_of_gyration(ca):
    return float(np.sqrt(((ca - ca.mean(0)) ** 2).sum(1).mean()))


def contact_order(ca, cutoff=10.0):
    """Absolute contact order of CA pairs within the cutoff: mean sequence separation."""
    d = np.sqrt(((ca[:, None] - ca[None]) ** 2).sum(2))
    i, j = np.where(np.triu(d < cutoff, 1))
    return float((j - i).mean()) if len(i) else 0.0


def descriptors(dom, ss):
    n = len(dom.seq)
    return dict(n=n, rg=radius_of_gyration(dom.ca), co=contact_order(dom.ca),
                alpha=ss.count('H'), beta=ss.count('E'))


def dist_term(dq, dt, w):
    nq, nt = dq['n'], dt['n']
    terms = {
        'nr': (nq - nt) / ((nq + nt) / 2),
        'rg': dq['rg'] - dt['rg'],
        'co': dq['co'] / nq - dt['co'] / nt,
        'alpha': dq['alpha'] / nq - dt['alpha'] / nt,
        'beta': dq['beta'] / nq - dt['beta'] / nt,
    }
    num = sum(w[k] * v ** 2 for k, v in terms.items())
    den = sum(w[k] ** 2 for k in terms)
    return float(np.sqrt(abs(num / den))), terms


def boundaries(S, window=5, cut=0.55):
    """First and last aligned pair whose mean similarity over the next (previous) 5 pairs exceeds 0.55."""
    n = len(S)
    first = next((k for k in range(n) if S[k:k + window].mean() > cut), None)
    last = next((k for k in range(n - 1, -1, -1) if S[max(0, k - window + 1):k + 1].mean() > cut), None)
    return first, last


def internal_gaps(pairs, first, last):
    if first is None or last is None or last <= first:
        return 0
    p = pairs[first:last + 1]
    di, dj = np.diff(p[:, 0]), np.diff(p[:, 1])
    return int((di > 1).sum() + (dj > 1).sum())


def score_terms(q, t, dq, dt, pairs, R, tr, A, weights):
    Xs = q.ca @ R.T + tr
    d2 = ((Xs[pairs[:, 0]] - t.ca[pairs[:, 1]]) ** 2).sum(1)
    S = np.exp(-d2 / D0 ** 2)
    n = len(pairs)
    ner = float(S.sum())
    idx = {a: k for k, a in enumerate(AA)}
    a = np.array([A[idx.get(q.seq[i], 0), idx.get(t.seq[j], 0)] for i, j in pairs])
    fseq = float((S * a).sum() / S.sum())
    rmsd_sup = float(np.sqrt(d2.mean()))
    Rk, tk = kabsch(q.ca[pairs[:, 0]], t.ca[pairs[:, 1]])
    rmsd_fit = float(np.sqrt((((q.ca[pairs[:, 0]] @ Rk.T + tk) - t.ca[pairs[:, 1]]) ** 2).sum(1).mean()))
    first, last = boundaries(S)
    gaps = internal_gaps(pairs, first, last)
    dist, parts = dist_term(dq, dt, weights)
    ident = sum(q.seq[i] == t.seq[j] for i, j in pairs)
    return dict(d=np.sqrt(d2).round(3).tolist(), pairs=pairs.tolist(), first=first, last=last,
                n_aligned=n, ner=ner, ner_rel=ner / ((len(q.seq) + len(t.seq)) / 2), fseq=fseq,
                sas_sup=100 * rmsd_sup / n, sas_fit=100 * rmsd_fit / n, rmsd_fit=rmsd_fit,
                gaps=gaps, dist=dist, seqid_aligned=100 * ident / n,
                seqid_shorter=100 * ident / min(len(q.seq), len(t.seq)), **{'d_' + k: v for k, v in parts.items()})


def ash_score(ner_rel, fseq, sas, gaps, dist, w):
    """Eq. 1. NER_rel enters in percent: with the printed weights, only that reading matches the
    scores of Additional File 3 (compare_af3.py)."""
    return w['ner'] * 100 * ner_rel + w['seq'] * fseq - w['sas'] * sas - w['gap'] * gaps - w['dist'] * dist
