"""Pack the ASCII PSSMs of one PSI-BLAST run into one compressed file that the pipeline commits.

Usage: pack_pssms.py FASTA_DIR PSSM_DIR OUT.npz

OUT.npz holds, for the benchmark then PDB186 (in FASTA order): set, id, label, sequence, length,
and the integer log-odds scores of all PSSMs stacked (sum of lengths x 20, int8). Each PSSM's
query sequence must equal the FASTA sequence.

PSI-BLAST writes no PSSM when a query finds no hits (the DNA strands of the benchmark). Those
sequences get the BLOSUM62 row of each residue instead, the PSSM PSI-BLAST starts from, as the
authors' later toolkit (BioSeq-Analysis2.0) does; their ids are stored in "blosum_fallback".
"""
import sys
from pathlib import Path

import numpy as np
from pssmdt import AMINO_ACIDS, read_pssm

# BLOSUM62 (Henikoff and Henikoff 1992), rows and columns in PSI-BLAST order ARNDCQEGHILKMFPSTWYV
BLOSUM62 = """
 4 -1 -2 -2  0 -1 -1  0 -2 -1 -1 -1 -1 -2 -1  1  0 -3 -2  0
-1  5  0 -2 -3  1  0 -2  0 -3 -2  2 -1 -3 -2 -1 -1 -3 -2 -3
-2  0  6  1 -3  0  0  0  1 -3 -3  0 -2 -3 -2  1  0 -4 -2 -3
-2 -2  1  6 -3  0  2 -1 -1 -3 -4 -1 -3 -3 -1  0 -1 -4 -3 -3
 0 -3 -3 -3  9 -3 -4 -3 -3 -1 -1 -3 -1 -2 -3 -1 -1 -2 -2 -1
-1  1  0  0 -3  5  2 -2  0 -3 -2  1  0 -3 -1  0 -1 -2 -1 -2
-1  0  0  2 -4  2  5 -2  0 -3 -3  1 -2 -3 -1  0 -1 -3 -2 -2
 0 -2  0 -1 -3 -2 -2  6 -2 -4 -4 -2 -3 -3 -2  0 -2 -2 -3 -3
-2  0  1 -1 -3  0  0 -2  8 -3 -3 -1 -2 -1 -2 -1 -2 -2  2 -3
-1 -3 -3 -3 -1 -3 -3 -4 -3  4  2 -3  1  0 -3 -2 -1 -3 -1  3
-1 -2 -3 -4 -1 -2 -3 -4 -3  2  4 -2  2  0 -3 -2 -1 -2 -1  1
-1  2  0 -1 -3  1  1 -2 -1 -3 -2  5 -1 -3 -1  0 -1 -3 -2 -2
-1 -1 -2 -3 -1  0 -2 -3 -2  1  2 -1  5  0 -2 -1 -1 -1 -1  1
-2 -3 -3 -3 -2 -3 -3 -3 -1  0  0 -3  0  6 -4 -2 -2  1  3 -1
-1 -2 -2 -1 -3 -1 -1 -2 -2 -3 -3 -1 -2 -4  7 -1 -1 -4 -3 -2
 1 -1  1  0 -1  0  0  0 -1 -2 -2  0 -1 -2 -1  4  1 -3 -2 -2
 0 -1  0 -1 -1 -1 -1 -2 -2 -1 -1 -1 -1 -2 -1  1  5 -2 -2  0
-3 -3 -4 -4 -2 -2 -3 -2 -2 -3 -2 -3 -1  1 -4 -3 -2 11  2 -3
-2 -2 -2 -3 -2 -1 -2 -3  2 -1 -1 -2 -1  3 -3 -2 -2  2  7 -1
 0 -3 -3 -3 -1 -2 -2 -3 -3  3  1 -2  1 -1 -2 -2  0 -3 -1  4
"""
B62 = np.array(BLOSUM62.split(), dtype=np.int64).reshape(20, 20)


def blosum_pssm(seq):
    """BLOSUM62 row of each residue; X (and anything else) scores -1 against everything."""
    return np.array([B62[AMINO_ACIDS.index(c)] if c in AMINO_ACIDS else -np.ones(20, int) for c in seq])


def read_fasta(path):
    lines = Path(path).read_text().split()
    for h, s in zip(lines[0::2], lines[1::2]):
        pid, label = h[1:].split("|")
        yield pid, int(label), s


def main(fasta_dir, pssm_dir, out):
    sets, ids, labels, seqs, scores = [], [], [], [], []
    fallback = []
    for name in ("benchmark", "pdb186"):
        for pid, label, seq in read_fasta(Path(fasta_dir) / f"{name}.fasta"):
            f = Path(pssm_dir) / f"{name}_{pid}.pssm"
            if f.exists():
                q, s = read_pssm(f)
                assert q == seq, (name, pid)
            else:
                s = blosum_pssm(seq)
                fallback.append(f"{name}_{pid}")
            assert s.min() >= -128 and s.max() <= 127
            sets.append(name); ids.append(pid); labels.append(label); seqs.append(seq)
            scores.append(s.astype(np.int8))
    if len(fallback) > 20:
        sys.exit(f"{len(fallback)} PSSMs missing (more than the no-hit queries), e.g. {fallback[:5]}")
    np.savez_compressed(out, set=np.array(sets), id=np.array(ids), label=np.array(labels),
                        sequence=np.array(seqs), length=np.array([len(s) for s in seqs]),
                        scores=np.concatenate(scores), blosum_fallback=np.array(fallback, dtype=str))
    print(f"{len(ids)} PSSMs packed into {out}; BLOSUM62 for {fallback}")


if __name__ == "__main__":
    main(*sys.argv[1:4])
