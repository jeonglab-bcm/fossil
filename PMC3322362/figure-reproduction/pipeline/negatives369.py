"""Generate negative pairs for RPI369 by the rule in the paper's Methods.

The paper publishes RPI369's positives (Additional File 3) but not its negatives, and the
authors' lab repository (Dobbs-Lab/RPIMotif) only holds RPI2241's. The Methods say negatives
were made by pairing RNAs and proteins at random and discarding a pair A-B "if there exists a
positive interaction pair C-B, and A and C share >= 30% sequence identity". Here proteins and
RNAs are drawn from RPI369's positive pairs (each pair equally likely), and a draw is also
rejected if it repeats a negative already drawn.

Identity is the number of identical aligned residues of a global alignment (BLOSUM62, gap open
-10, gap extension -0.5) divided by the length of the shorter sequence.

Usage: python negatives369.py POS_RPI2241.rpi S3.txt SEED OUT.rpi
"""

import random
import sys

from Bio import Align
from Bio.Align import substitution_matrices

sys.path.insert(0, __import__("os").path.dirname(__file__))
from encode import read_rpi, read_s3  # noqa: E402

aligner = Align.PairwiseAligner()
aligner.mode = "global"
aligner.substitution_matrix = substitution_matrices.load("BLOSUM62")
aligner.open_gap_score = -10
aligner.extend_gap_score = -0.5

_cache = {}


def identity(a, b):
    if a == b:
        return 1.0
    key = (a, b) if a < b else (b, a)
    if key not in _cache:
        # Align in a fixed order: tie-breaking among optimal alignments depends on it.
        x, y = key
        aln = aligner.align(x.replace("X", "A").replace("U", "C"), y.replace("X", "A").replace("U", "C"))[0]
        same = sum(1 for x, y in zip(*aln) if x == y and x != "-")
        _cache[key] = same / min(len(a), len(b))
    return _cache[key]


def main(pos_path, s3_path, seed, out):
    keep = read_s3(s3_path)
    pos = [p for p in read_rpi(pos_path) if p[0] in keep]
    partners = {}  # RNA sequence -> protein sequences that bind it
    for _, p, r in pos:
        partners.setdefault(r, set()).add(p)
    rng = random.Random(int(seed))
    seen = set()
    neg = []
    while len(neg) < len(pos):
        pname, p, _ = rng.choice(pos)
        rname, _, r = rng.choice(pos)
        if (p, r) in seen or any(identity(p, c) >= 0.30 for c in partners[r]):
            continue
        seen.add((p, r))
        neg.append((f"{pname.split(',')[0]},{rname.split(',')[1]}", p, r))
    with open(out, "w") as f:
        for name, p, r in neg:
            f.write(f">{name}\n{p}\n{r}\n")


if __name__ == "__main__":
    main(*sys.argv[1:5])
