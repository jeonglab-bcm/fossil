#!/usr/bin/env python3
"""Build the paper's dataset from the extracted baseline records.

Dataset: human-related MEDLINE citations of 1987-2012 with an abstract, in English
(humans[mh] AND hasabstract AND english[la]; see the README for why). Training years 1987-2010, test
years 2011 and 2012. The training sample is 7.5% of the training years, drawn with a fixed seed, as
in the paper ("7.5% sampling was selected for cross-validation and final model training").

Rows are chosen from a few small columns first; only the chosen rows' text is then read, file by
file, so memory stays small. A PMID found in more than one baseline file is kept once (the last file).

Writes train_sample.parquet, test2011.parquet, test2012.parquet (and train_fraction_<f>.parquet with
--extra-fractions) and dataset.json (counts).
Usage: build_dataset.py MEDLINE_DIR OUT_DIR [--fraction 0.075] [--seed 0] [--extra-fractions F ...]
"""
import argparse
import glob
import json
import os

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("medline_dir")
    ap.add_argument("out_dir")
    ap.add_argument("--fraction", type=float, default=0.075)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--last-train-year", type=int, default=2010)
    ap.add_argument("--test-years", type=int, nargs="+", default=[2011, 2012])
    ap.add_argument("--extra-fractions", type=float, nargs="*", default=[],
                    help="also write train_fraction_<f>.parquet samples (the training-fraction check)")
    a = ap.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)
    files = sorted(glob.glob(os.path.join(a.medline_dir, "pubmed*.parquet")))
    if not files:
        raise SystemExit(f"no parquet files in {a.medline_dir}")
    cols = {k: [] for k in ("pmid", "year", "english", "has_abstract", "rct", "file", "row")}
    for i, f in enumerate(files):
        t = pq.read_table(f, columns=["pmid", "year", "english", "has_abstract", "rct"])
        for k in ("pmid", "year"):
            cols[k].append(t[k].to_numpy())
        for k in ("english", "has_abstract", "rct"):
            cols[k].append(t[k].to_numpy(zero_copy_only=False).astype(bool))
        cols["file"].append(np.full(t.num_rows, i, dtype=np.int32))
        cols["row"].append(np.arange(t.num_rows, dtype=np.int64))
    c = {k: np.concatenate(v) for k, v in cols.items()}
    pm = c["pmid"]
    _, last = np.unique(pm[::-1], return_index=True)
    keep = np.sort(len(pm) - 1 - last)
    c = {k: v[keep] for k, v in c.items()}
    year, rct = c["year"], c["rct"]
    ds = c["english"] & c["has_abstract"]
    counts = {
        "baseline_files": len(files),
        "humans_1987_2012": int(len(pm)),
        "humans_1987_2012_unique": int(len(keep)),
        "humans_rct_1987_2012": int(rct.sum()),
        "dataset": int(ds.sum()),
        "dataset_rct": int((ds & rct).sum()),
        "by_year": {int(y): {"n": int((ds & (year == y)).sum()), "rct": int((ds & rct & (year == y)).sum())}
                    for y in range(1987, 2013)},
    }
    idx = np.nonzero(ds & (year <= a.last_train_year))[0]
    rng = np.random.default_rng(a.seed)
    sample = np.sort(rng.choice(idx, size=int(round(a.fraction * len(idx))), replace=False))
    counts.update({"train_years": int(len(idx)), "train_rct": int(rct[idx].sum()), "train_sample": int(len(sample)),
                   "train_sample_rct": int(rct[sample].sum()), "fraction": a.fraction, "seed": a.seed})
    outputs = {"train_sample.parquet": (sample, None)}
    for k, fr in enumerate(a.extra_fractions):
        r2 = np.random.default_rng(1000 + k)
        sub = np.sort(r2.choice(idx, size=int(round(fr * len(idx))), replace=False))
        outputs[f"train_fraction_{fr:g}.parquet"] = (sub, ["pmid", "title", "abstract", "rct"])
        counts[f"train_fraction_{fr:g}"] = int(len(sub))
    for y in a.test_years:
        sel = np.nonzero(ds & (year == y))[0]
        outputs[f"test{y}.parquet"] = (sel, None)
        counts[f"test{y}"] = int(len(sel))
        counts[f"test{y}_rct"] = int(rct[sel].sum())
    # rows are in file order (keep is sorted), so each output's rows of file i are one slice
    by_file = {name: (s, c["file"][s]) for name, (s, _) in outputs.items()}
    writers = {}
    try:
        for i, f in enumerate(files):
            parts = {}
            for name, (s, fs) in by_file.items():
                lo, hi = np.searchsorted(fs, [i, i + 1])
                parts[name] = c["row"][s[lo:hi]]
            if not any(len(r) for r in parts.values()):
                continue
            t = pq.read_table(f)
            for name, rows in parts.items():
                if not len(rows):
                    continue
                sub = t.take(pa.array(rows))
                colsel = outputs[name][1]
                if colsel:
                    sub = sub.select(colsel)
                if name not in writers:
                    writers[name] = pq.ParquetWriter(os.path.join(a.out_dir, name), sub.schema, compression="zstd")
                writers[name].write_table(sub)
    finally:
        for w in writers.values():
            w.close()
    with open(os.path.join(a.out_dir, "dataset.json"), "w") as fh:
        json.dump(counts, fh, indent=1)
    print(json.dumps({k: v for k, v in counts.items() if k != "by_year"}, indent=1))


if __name__ == "__main__":
    main()
