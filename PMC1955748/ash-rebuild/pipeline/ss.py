"""Secondary structure by the DSSP rules (Kabsch and Sander 1983), helix (H) and strand (E) only.

H-bond energy E = 0.084 * 332 * (1/r_ON + 1/r_CH - 1/r_OH - 1/r_CN) kcal/mol, bonded below -0.5.
The amide H sits 1 A from N, opposite the previous residue's C=O. Two consecutive 4-turns at
i-1 and i make residues i to i+3 helical; residues in a parallel or antiparallel bridge are strand.
The 2007 paper does not say which assignment ASH used; DSSP is the usual one.
"""
import numpy as np


def hbond_matrix(n, ca, c, o):
    L = len(ca)
    ok = ~(np.isnan(n).any(1) | np.isnan(c).any(1) | np.isnan(o).any(1))
    h = n.copy()
    co = c[:-1] - o[:-1]
    co /= np.linalg.norm(co, axis=1, keepdims=True)
    h[1:] = n[1:] + co
    # no amide H after a chain break or at the first residue
    brk = np.ones(L, bool)
    brk[1:] = np.linalg.norm(n[1:] - c[:-1], axis=1) > 2.5
    hok = ok & ~brk
    d = lambda a, b: np.linalg.norm(a[:, None] - b[None], axis=2)
    with np.errstate(divide='ignore', invalid='ignore'):
        e = 0.084 * 332 * (1 / d(o, n) + 1 / d(c, h) - 1 / d(o, h) - 1 / d(c, n))
    hb = (e < -0.5) & ok[:, None] & hok[None, :]      # hb[i, j]: C=O of i bonded to N-H of j
    idx = np.arange(L)
    hb[np.abs(idx[:, None] - idx[None]) < 2] = False
    return np.nan_to_num(hb)


def assign(n, ca, c, o):
    L = len(ca)
    hb = hbond_matrix(n, ca, c, o)
    ss = np.array(['-'] * L)
    turn4 = np.array([i + 4 < L and hb[i, i + 4] for i in range(L)])
    for i in range(1, L - 3):
        if turn4[i - 1] and turn4[i]:
            ss[i:i + 4] = 'H'
    bridge = np.zeros(L, bool)
    for i in range(1, L - 1):
        for j in range(1, L - 1):
            if abs(i - j) < 3:
                continue
            par = (hb[i - 1, j] and hb[j, i + 1]) or (hb[j - 1, i] and hb[i, j + 1])
            anti = (hb[i, j] and hb[j, i]) or (hb[i - 1, j + 1] and hb[j - 1, i + 1])
            if par or anti:
                bridge[i] = True
    ss[bridge & (ss != 'H')] = 'E'
    return ''.join(ss)
