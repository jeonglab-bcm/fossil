"""Table 2: significant GO terms per published miRNA list, basic and multi-hit algorithms.

Usage: python table2.py PUBLISHED_TABLE2.csv OUT_DIR COUNTS.tsv [COUNTS.tsv ...]

COUNTS.tsv: empirical.py output. Empirical P = draws at or above the observed overlap / draws.
Benjamini-Hochberg over all biological-process terms of the species; a term is significant when
its adjusted P < 0.05 (Supplementary Table S5 flags its terms this way: BH over all 9,462 terms).
Writes OUT_DIR/table2.csv (ours next to the paper's) and OUT_DIR/pvalues/<study>.tsv.
"""
import csv
import os
import sys
from collections import defaultdict

import numpy as np


def bh(p):
    n = len(p)
    o = np.argsort(p, kind="mergesort")
    q = p[o] * n / np.arange(1, n + 1)
    q = np.minimum.accumulate(q[::-1])[::-1]
    out = np.empty(n)
    out[o] = np.minimum(q, 1)
    return out


def main(published, out, *counts):
    rows = defaultdict(list)
    for c in counts:
        for r in csv.DictReader(open(c), delimiter="\t"):
            rows[r["study"]].append(r)
    os.makedirs(os.path.join(out, "pvalues"), exist_ok=True)
    res = {}
    for s, rs in rows.items():
        it = np.array([int(r["iterations"]) for r in rs])
        pb = np.array([int(r["basic_ge"]) for r in rs]) / it
        pm = np.array([int(r["multi_ge"]) for r in rs]) / it
        qb, qm = bh(pb), bh(pm)
        res[s] = (int((qb < 0.05).sum()), int((qm < 0.05).sum()), len(rs))
        with open(os.path.join(out, "pvalues", f"{s}.tsv"), "w") as f:
            f.write("go_id\tbasic_k\tbasic_n\tbasic_p\tbasic_q\tmulti_w\tmulti_total\tmulti_p\tmulti_q\n")
            for r, a, b, c, d in zip(rs, pb, qb, pm, qm):
                f.write(f"{r['go_id']}\t{r['basic_k']}\t{r['basic_n']}\t{float(a)!r}\t{float(b)!r}\t"
                        f"{r['multi_w']}\t{r['multi_total']}\t{float(c)!r}\t{float(d)!r}\n")
    with open(os.path.join(out, "table2.csv"), "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["study", "reference", "species", "mirnas", "paper_basic", "ours_basic",
                     "paper_multi_hit", "ours_multi_hit", "terms_tested"])
        for p in csv.DictReader(open(published)):
            b, m, n = res.get(p["study"], ("", "", ""))
            w.writerow([p["study"], p["reference"], p["species"], p["mirnas"], p["basic"], b,
                        p["multi_hit"], m, n])
            print(f"{p['study']:15s} basic {p['basic']:>5s} / {b!s:>5s}   multi {p['multi_hit']:>5s} / {m!s:>5s}")


if __name__ == "__main__":
    main(*sys.argv[1:])
