"""SCOP 1.53 benchmark loader and the distance-based feature vectors (DR and DT).

Feature vector of a sequence S over the 20-letter alphabet (paper, Eq. 1-2 and Fig. 2):
  d = 0:        T0_i  = occurrences of letter t_i                         (20 values)
  d = 1..dMAX:  Td_ij = occurrences of t_i at position k and t_j at k + d (400 values each)
Dimension 20 + 400 dMAX. DR uses the residues; DT the Top-1-gram sequence (the most frequent
amino acid in each column of the PSI-BLAST frequency profile). Letters outside the alphabet
(x and X, 529 of 4,352 x 129 residues in the benchmark) are not counted, alone or in a pair.

With a linear kernel only dot products are needed, and they add over distances:
  K_dMAX(x, y) = K_0(x, y) + sum_{d=1..dMAX} K_d(x, y),
so one pass over d = 0..200 gives the kernel at every dMAX of the sweep. Counts are integers and
every dot product is below 2^53, so the float64 sums are exact whatever the summation order.
"""
import numpy as np

ALPHABET = "ARDCQEHIGNLKMFPSTWYV"   # the paper's alphabet order (Fig. 2 caption, Fig. 4 axes)
INDEX = {a: i for i, a in enumerate(ALPHABET)}


def read_fasta(path):
    names, seqs, cur = [], [], []
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if line.startswith(">"):
                if cur:
                    seqs.append("".join(cur))
                names.append(line[1:].split()[0])
                cur = []
            elif line:
                cur.append(line)
    if cur:
        seqs.append("".join(cur))
    return names, [s.upper() for s in seqs]


def read_membership(path):
    """all_seq_fam_membership.txt: codes 1 pos train, 2 neg train, 3 pos test, 4 neg test."""
    with open(path) as fh:
        header = fh.readline().split()[1:]
        names, rows = [], []
        for line in fh:
            f = line.split()
            names.append(f[0])
            rows.append([int(x) for x in f[1:]])
    return header, names, np.array(rows, dtype=np.int8)


def load_benchmark(fasta, membership):
    names, seqs = read_fasta(fasta)
    families, mnames, codes = read_membership(membership)
    assert mnames == names, "FASTA and membership rows differ"
    return names, seqs, families, codes


def encode(seq):
    return np.array([INDEX.get(c, -1) for c in seq], dtype=np.int64)


def count_matrix(encoded, d):
    """Rows: sequences; columns: 20 letters (d = 0) or 400 ordered pairs (d >= 1)."""
    n = len(encoded)
    C = np.zeros((n, 20 if d == 0 else 400))
    for r, e in enumerate(encoded):
        if d == 0:
            e = e[e >= 0]
            np.add.at(C[r], e, 1.0)
        elif len(e) > d:
            a, b = e[:-d], e[d:]
            ok = (a >= 0) & (b >= 0)
            np.add.at(C[r], a[ok] * 20 + b[ok], 1.0)
    return C


def kernels_by_dmax(encoded, dmax_values):
    """Yield (dMAX, raw linear kernel) for each dMAX in ascending order."""
    targets = sorted(set(dmax_values))
    K = None
    for d in range(0, targets[-1] + 1):
        C = count_matrix(encoded, d)
        Kd = C @ C.T
        K = Kd if K is None else K + Kd
        if d in targets:
            yield d, K.copy()


def feature_vectors(encoded, dmax):
    """Explicit vectors, (n, 20 + 400 dmax): [T0, T1 (400), ..., T_dmax (400)]."""
    return np.hstack([count_matrix(encoded, d) for d in range(dmax + 1)])
