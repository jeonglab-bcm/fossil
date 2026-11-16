"""Table 2, multi-hit column: significant-term counts under several readings of the method (issue #33).

Usage: python multihit_readings.py PUBLISHED_TABLE2.csv OUT_DIR NAME=DIR [NAME=DIR ...]

Each DIR holds empirical.py counts for one reading, one file per null:
<sp>_<size>[.<tag>].counts.tsv[.gz]; the first NAME is the reference (the one Table 2 uses).
Each reading changes one thing against the reference (see README, "The multi-hit algorithm").
A term is significant when its Benjamini-Hochberg adjusted empirical P < 0.05, as in table2.py.

Writes
  OUT_DIR/multihit_readings.csv  per list: the paper's count, the count under every reading,
      the reference count at FDR 0.025 and 0.1, the FDR at which the reference ranking gives the
      paper's count (the adjusted P of its k-th term), terms significant in every reading (core) and in any
      (union), and the Jaccard index of each reading's term set with the reference's;
  OUT_DIR/multihit_terms.tsv.gz  per list and term significant in any reading: 1/0 per reading.
"""
import csv
import glob
import gzip
import io
import os
import sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from table2 import bh  # noqa: E402


def read_dir(d):
    """study -> {go_id: multi-hit empirical P}."""
    out = defaultdict(dict)
    files = sorted(glob.glob(os.path.join(d, "*.counts.tsv")) + glob.glob(os.path.join(d, "*.counts.tsv.gz")))
    for f in files:
        op = gzip.open if f.endswith(".gz") else open
        with op(f, "rt") as fh:
            for r in csv.DictReader(fh, delimiter="\t"):
                out[r["study"]][r["go_id"]] = int(r["multi_ge"]) / int(r["iterations"])
    return out


def significant(pv, alpha=0.05):
    terms = sorted(pv)
    q = bh(np.array([pv[t] for t in terms]))
    return {t for t, x in zip(terms, q) if x < alpha}, q


def main(published, out, *readings):
    names = [r.split("=", 1)[0] for r in readings]
    data = {n: read_dir(r.split("=", 1)[1]) for n, r in zip(names, readings)}
    ref = names[0]
    os.makedirs(out, exist_ok=True)
    rows, term_rows = [], []
    for p in csv.DictReader(open(published)):
        s = p["study"]
        sets = {}
        for n in names:
            if s in data[n]:
                sets[n], q = significant(data[n][s])
                if n == ref:
                    q_ref = q
        if ref not in sets:
            continue
        row = {"study": s, "species": p["species"], "mirnas": p["mirnas"], "paper_multi_hit": p["multi_hit"]}
        for n in names:
            row[n] = len(sets[n]) if n in sets else ""
        row[f"{ref}_fdr0.025"] = int((q_ref < 0.025).sum())
        row[f"{ref}_fdr0.1"] = int((q_ref < 0.1).sum())
        k = int(p["multi_hit"])
        row[f"{ref}_fdr_at_paper_count"] = f"{np.sort(q_ref)[k - 1]:.3g}" if k else ""
        have = [n for n in names if n in sets]
        row["core"] = len(set.intersection(*(sets[n] for n in have)))
        row["union"] = len(set.union(*(sets[n] for n in have)))
        for n in names[1:]:
            if n in sets:
                u = sets[ref] | sets[n]
                row[f"jaccard_{n}"] = f"{len(sets[ref] & sets[n]) / len(u):.3f}" if u else ""
            else:
                row[f"jaccard_{n}"] = ""
        rows.append(row)
        for t in sorted(set.union(*(sets[n] for n in have))):
            term_rows.append([s, t] + [("1" if t in sets[n] else "0") if n in sets else "" for n in names])
    with open(os.path.join(out, "multihit_readings.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    with gzip.GzipFile(os.path.join(out, "multihit_terms.tsv.gz"), "wb", mtime=0) as gz, \
            io.TextIOWrapper(gz, encoding="utf-8", newline="") as f:
        f.write("\t".join(["study", "go_id"] + names) + "\n")
        for r in term_rows:
            f.write("\t".join(r) + "\n")
    for r in rows:
        print(" ".join(f"{k}={v}" for k, v in r.items() if not k.startswith("jaccard")))


if __name__ == "__main__":
    main(*sys.argv[1:])
