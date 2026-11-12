"""Export the two Bioconductor data packages to tab-separated files, without R.

Usage: export_bioc.py SEVENTYGENEDATA_RDA STJUDE_RDA OUTDIR

  vanDeVijver (seventyGeneData): the 295 arrays of van de Vijver et al. 2002 as an ExpressionSet
    -> vdv_exprs.tsv.gz (probes x samples), vdv_pdata.tsv, vdv_fdata.tsv
  stjude (stjudem): the 327 arrays of Yeoh et al. 2002 as a MACATData list
    -> stjude_exprs.tsv.gz (probes x samples), stjude_pdata.tsv (sample, label)
"""

from __future__ import annotations

import csv
import gzip
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import rdata


def load(path):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        parsed = rdata.parser.parse_file(path)
        conv = rdata.conversion.convert(parsed, default_encoding="utf8")
    return conv[list(conv)[0]]


def frame_rows(df):
    """An R data.frame (pandas) as (column names, row names, rows of strings)."""
    cols = [str(c) for c in df.columns]
    rows = []
    for _, r in df.iterrows():
        out = []
        for v in r.tolist():
            if v is None or v is pd.NA or (isinstance(v, float) and np.isnan(v)):
                out.append("NA")
            elif isinstance(v, (bool, np.bool_)):
                out.append("TRUE" if v else "FALSE")
            elif isinstance(v, float) and v.is_integer():
                out.append(str(int(v)))
            else:
                out.append(str(v))
        rows.append(out)
    return cols, [str(i) for i in df.index], rows


def fmt(v):
    return "NA" if np.isnan(v) else repr(float(v))


def write_matrix(path, rows, cols, X):
    with gzip.open(path, "wt", encoding="utf-8") as f:
        f.write("\t" + "\t".join(cols) + "\n")
        for name, row in zip(rows, X):
            f.write(name + "\t" + "\t".join(fmt(v) for v in row) + "\n")


def write_frame(path, df):
    cols, index, rows = frame_rows(df)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow([""] + cols)
        for i, r in zip(index, rows):
            w.writerow([i] + r)


def main(vdv_rda, stjude_rda, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    e = load(vdv_rda)
    expr = e.assayData["exprs"]  # pandas DataFrame, probes x samples
    write_matrix(out / "vdv_exprs.tsv.gz", [str(p) for p in expr.index], [str(c) for c in expr.columns],
                 np.asarray(expr.values, dtype=float))
    write_frame(out / "vdv_pdata.tsv", e.phenoData.data)
    write_frame(out / "vdv_fdata.tsv", e.featureData.data)

    s = load(stjude_rda)
    X = s["expr"]
    probes = [str(p) for p in X.coords[X.dims[0]].values]
    labels = [str(l) for l in np.asarray(s["labels"])]
    cols = [str(c) for c in X.coords[X.dims[1]].values] if X.dims[1] in X.coords else [str(i + 1) for i in range(X.shape[1])]
    write_matrix(out / "stjude_exprs.tsv.gz", probes, cols, np.asarray(X.values, dtype=float))
    with open(out / "stjude_pdata.tsv", "w", encoding="utf-8") as f:
        f.write("sample\tlabel\n")
        for c, l in zip(cols, labels):
            f.write(f"{c}\t{l}\n")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], Path(sys.argv[3]))
