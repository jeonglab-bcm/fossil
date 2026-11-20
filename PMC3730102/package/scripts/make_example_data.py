"""Write the bundled example data and its expected outputs.

The example is synthetic: eight proteins in a small network, three known locations, and the expression of
the eight genes over eight samples. The expected outputs are computed here in plain Python straight from
the formulas of Lee et al. 2008 and 2013, by enumerating every path; nothing here imports condloc.

Run from the package folder: python scripts/make_example_data.py
"""

from __future__ import annotations

import itertools
import math
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "src" / "condloc" / "data"

PROTEINS = ["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8"]
LOCATIONS = {"P1": "NU", "P2": "NU", "P3": "CY", "P4": "", "P5": "CY,PM", "P6": "PM", "P7": "", "P8": "NU"}
LINKS = [("P1", "P2"), ("P1", "P4"), ("P2", "P3"), ("P3", "P5"), ("P4", "P5"), ("P4", "P8"), ("P5", "P6"),
         ("P6", "P7"), ("P2", "P8")]
SAMPLES = 8


def expression() -> dict[str, list[float]]:
    """Deterministic expression levels (log2 scale)."""
    out = {}
    for k, p in enumerate(PROTEINS):
        base = 6.0 + 0.5 * k
        out[p] = [round(base + math.sin(0.7 * (s + 1) * (1 + (k % 3))) + 0.1 * ((s * (k + 3)) % 5), 4)
                  for s in range(SAMPLES)]
    return out


def median(v):
    s = sorted(v)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def pearson(a, b):
    ma, mb = sum(a) / len(a), sum(b) / len(b)
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    da = math.sqrt(sum((x - ma) ** 2 for x in a))
    db = math.sqrt(sum((y - mb) ** 2 for y in b))
    return num / (da * db)


def coherence(expr):
    """Phi(a,b) = -log2 Psi[min(med a, med b) / MEDIAN * r(a,b)], Psi = share of links with a value >= x."""
    med = {p: median(v) for p, v in expr.items()}
    big = median(list(med.values()))
    x = [min(med[a], med[b]) / big * pearson(expr[a], expr[b]) for a, b in LINKS]
    return [-math.log2(sum(1 for y in x if y >= v) / len(x)) for v in x]


def weights(distance, rho=2.0):
    """w_ki = 1 / (Psi_ki + rho), Psi_ki the number of distinct locations on the path from i to k (i's own hidden),
    the largest weight over the shortest paths; the protein itself gets 1 / rho."""
    nb = {p: set() for p in PROTEINS}
    for a, b in LINKS:
        nb[a].add(b)
        nb[b].add(a)
    locs = {p: set(x for x in v.split(",") if x) for p, v in LOCATIONS.items()}
    out = []
    for i in PROTEINS:
        out.append((i, i, 1.0 / rho))
        for k in sorted(nb[i]):
            out.append((i, k, 1.0 / (len(locs[k]) + rho)))
        if distance == 2:
            for k in PROTEINS:
                if k == i or k in nb[i]:
                    continue
                best = None
                for j in nb[i]:
                    if k in nb[j]:
                        w = 1.0 / (len(locs[j] | locs[k]) + rho)
                        best = w if best is None else max(best, w)
                if best is not None:
                    out.append((i, k, best))
    return out


def possibility(c, pos, neg):
    lo, hi = min(pos), max(neg)
    if c > hi:
        return 1.0
    if c < lo:
        return 0.0
    p_in = [v for v in pos if lo <= v <= hi]
    n_in = [v for v in neg if lo <= v <= hi]
    return (sum(1 for v in p_in if v <= c) / len(p_in) + sum(1 for v in n_in if v <= c) / len(n_in)) / 2


SCORES_POS = [0.35, 0.5, 0.6, 0.8, 0.9]
SCORES_NEG = [0.0, 0.1, 0.2, 0.3, 0.4, 0.55, 0.7]
QUERIES = [0.0, 0.3, 0.35, 0.45, 0.6, 0.7, 0.75, 1.0]


def main() -> None:
    expr = expression()
    with open(DATA / "example_expression.tsv", "w") as h:
        h.write("protein\t" + "\t".join(f"s{s + 1}" for s in range(SAMPLES)) + "\n")
        for p in PROTEINS:
            h.write(p + "\t" + "\t".join(f"{v:.4f}" for v in expr[p]) + "\n")
    with open(DATA / "example_network.tsv", "w") as h:
        h.write("protein_a\tprotein_b\n")
        for a, b in LINKS:
            h.write(f"{a}\t{b}\n")
    with open(DATA / "example_locations.tsv", "w") as h:
        h.write("protein\tlocations\n")
        for p in PROTEINS:
            h.write(f"{p}\t{LOCATIONS[p]}\n")
    with open(DATA / "expected_coherence.tsv", "w") as h:
        h.write("protein_a\tprotein_b\tcoherence\n")
        for (a, b), phi in zip(LINKS, coherence(expr)):
            h.write(f"{a}\t{b}\t{phi + 0.0:.12g}\n")
    with open(DATA / "expected_weights.tsv", "w") as h:
        h.write("distance\tprotein\tneighbour\tweight\n")
        for d in (1, 2):
            for i, k, w in weights(d):
                h.write(f"{d}\t{i}\t{k}\t{w:.12g}\n")
    with open(DATA / "expected_possibility.tsv", "w") as h:
        h.write("# gold-standard positives: " + " ".join(map(str, SCORES_POS)) + "\n")
        h.write("# gold-standard negatives: " + " ".join(map(str, SCORES_NEG)) + "\n")
        h.write("confidence\tpossibility\n")
        for c in QUERIES:
            h.write(f"{c}\t{possibility(c, SCORES_POS, SCORES_NEG):.12g}\n")
    _ = itertools  # keeps the import list stable for readers comparing versions


if __name__ == "__main__":
    main()
