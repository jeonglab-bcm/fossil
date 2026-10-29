"""TM-align seed alignment as index pairs."""
import numpy as np
import tmtools


def tm_pairs(q, t):
    r = tmtools.tm_align(q.ca, t.ca, q.seq, t.seq)
    out, i, j = [], 0, 0
    for a, b in zip(r.seqxA, r.seqyA):
        if a != '-' and b != '-':
            out.append((i, j))
        i += a != '-'
        j += b != '-'
    return np.array(out)
