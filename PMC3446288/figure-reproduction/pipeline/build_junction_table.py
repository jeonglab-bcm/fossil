#!/usr/bin/env python3
"""Merge the combinatorial-database counts (our mapping) and the TopHat junctions (the authors' TopHat
1.0.14 alignments from GEO GSE26561) of the four samples into one table.

A junction's reads in a sample are its database reads (full length and truncated) when the database
found it there, otherwise its TopHat reads (alignments weighted by 1/NH, rounded).

Usage: build_junction_table.py OUT.tsv.gz --db S1 DIR1 ... --tophat S1 FILE1 ...
Samples in order: BMM_WT BMM_KO Liver_WT Liver_KO.
"""

import argparse
import gzip
from collections import defaultdict

SAMPLES = ["BMM_WT", "BMM_KO", "Liver_WT", "Liver_KO"]


def gz_text(path):
    """A gzip text file without a timestamp, so reruns give the same bytes."""
    import io
    return io.TextIOWrapper(gzip.GzipFile(path, "wb", mtime=0), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--db", nargs=2, action="append", metavar=("SAMPLE", "COUNTS_TSV"), required=True)
    ap.add_argument("--tophat", nargs=2, action="append", metavar=("SAMPLE", "TSV"), required=True)
    a = ap.parse_args()
    db = defaultdict(lambda: [0] * 4)
    th = defaultdict(lambda: [0.0] * 4)
    for s, path in a.db:
        k = SAMPLES.index(s)
        with open(path) as f:
            next(f)
            for line in f:
                jid, r, rt = line.rstrip("\n").split("\t")
                chrom, rest = jid.rsplit(":", 1)
                d, ac = rest.split("-")
                db[(chrom, int(d), int(ac))][k] = int(r) + int(rt)
    for s, path in a.tophat:
        k = SAMPLES.index(s)
        with open(path) as f:
            for line in f:
                chrom, d, ac, w, _u = line.rstrip("\n").split("\t")
                th[(chrom, int(d), int(ac))][k] = float(w)
    keys = sorted(set(db) | set(th), key=lambda j: (j[0], j[1], j[2]))
    with gz_text(a.out) as fo:
        fo.write("chrom\tdonor\tacceptor\t" + "\t".join(f"db_{s}" for s in SAMPLES) + "\t"
                 + "\t".join(f"tophat_{s}" for s in SAMPLES) + "\n")
        for j in keys:
            d = db.get(j, [0] * 4)
            t = th.get(j, [0.0] * 4)
            fo.write(f"{j[0]}\t{j[1]}\t{j[2]}\t" + "\t".join(map(str, d)) + "\t"
                     + "\t".join(f"{x:g}" for x in t) + "\n")


if __name__ == "__main__":
    main()
