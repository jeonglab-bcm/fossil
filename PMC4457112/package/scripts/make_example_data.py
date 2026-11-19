#!/usr/bin/env python3
"""Make the bundled example data from the PubMed 2026 baseline (run once; the output is committed).

Input: the Parquet files written by figure-reproduction/pipeline/extract_medline.py for the baseline
files named below. Output, in src/rctconf/data/:
  citations_train.csv.gz         1,500 human-related English citations of 2010 with an abstract
                                 (300 with the RCT publication type, 1,200 without), with their label
  citations_test.csv.gz          500 such citations of 2011 (100 RCT, 400 not), without the label
  citations_test_expected.csv    the test citations' RCT publication type in MEDLINE (the expected output)
Only the title, journal, author count, MeSH descriptors and substances are kept: NLM distributes these
freely; abstracts are left out because publishers may hold their copyright. RCTs are over-sampled
(20% against about 4.5% in MEDLINE) so a small example holds enough of them.

Usage: make_example_data.py MEDLINE_PARQUET_DIR OUT_DIR
"""
import csv
import io
import glob
import gzip
import os
import sys

import numpy as np
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

FILES = range(650, 701)  # pubmed26n0650-0700: 2010 and 2011 citations
COLS = ["pmid", "title", "journal", "n_authors", "mesh", "chemicals"]


def pick(t, year, n_pos, n_neg, seed):
    t = t.filter(pc.and_(pc.equal(t["year"], year), pc.and_(t["english"], t["has_abstract"])))
    rct = t["rct"].to_numpy(zero_copy_only=False)
    rng = np.random.default_rng(seed)
    pos = rng.choice(np.nonzero(rct)[0], n_pos, replace=False)
    neg = rng.choice(np.nonzero(~rct)[0], n_neg, replace=False)
    idx = np.sort(np.r_[pos, neg])
    return t.take(pa.array(idx))


def write(path, t, label):
    rows = t.to_pylist()
    if path.endswith(".gz"):  # mtime 0: the same input gives the same bytes
        raw = gzip.GzipFile(filename="", mode="wb", fileobj=open(path, "wb"), compresslevel=9, mtime=0)
        fh = io.TextIOWrapper(raw, encoding="utf-8", newline="")
    else:
        fh = open(path, "w", encoding="utf-8", newline="")
    with fh:
        w = csv.writer(fh, lineterminator="\n")
        cols = COLS + (["rct"] if label else [])
        w.writerow(cols)
        for r in rows:
            w.writerow([int(r["rct"]) if c == "rct" else r[c] for c in cols])


def main():
    src, out = sys.argv[1:3]
    files = [f for n in FILES for f in glob.glob(os.path.join(src, f"pubmed26n{n:04d}.parquet"))]
    t = pa.concat_tables([pq.read_table(f) for f in files])
    train = pick(t, 2010, 300, 1200, 1)
    test = pick(t, 2011, 100, 400, 2)
    write(os.path.join(out, "citations_train.csv.gz"), train, True)
    write(os.path.join(out, "citations_test.csv.gz"), test, False)
    with open(os.path.join(out, "citations_test_expected.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["pmid", "rct"])
        for r in test.to_pylist():
            w.writerow([r["pmid"], int(r["rct"])])
    for f in ("citations_train.csv.gz", "citations_test.csv.gz", "citations_test_expected.csv"):
        print(f, os.path.getsize(os.path.join(out, f)), "bytes")


if __name__ == "__main__":
    main()
