"""Command line: manetworker EXPRESSION BINDING_RATIO BINDING_P [-o OUTDIR] [options]."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

from . import CLASSES, __version__, log_ratio, read_matrix, run, write_counts, write_matrix


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="manetworker",
        description="TF activity profiles and regulatory coupling from expression and ChIP data (MA-Networker, Gao et al. 2004).",
    )
    ap.add_argument("expression", nargs="?", help="TSV, genes x experiments, log2 ratios (blank = missing)")
    ap.add_argument("binding_ratio", nargs="?", help="TSV, genes x TFs, ChIP enrichment ratios (not logged)")
    ap.add_argument("binding_p", nargs="?", help="TSV, genes x TFs, ChIP P-values")
    ap.add_argument("-o", "--outdir", default=".", help="output folder (default: current folder)")
    ap.add_argument("--alpha", type=float, help="backward selection threshold (default 0.005 / experiments)")
    ap.add_argument("--bind-p", type=float, default=1e-3, help="ChIP P-value below which a gene is bound (default 1e-3)")
    ap.add_argument("--fdr", type=float, default=0.05, help="false discovery rate for coupling (default 0.05)")
    ap.add_argument("--no-select", action="store_true", help="keep every TF (no backward selection)")
    ap.add_argument("--example", action="store_true", help="run on the bundled example data")
    ap.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = ap.parse_args(argv)

    if args.example:
        from . import example_path
        args.expression, args.binding_ratio, args.binding_p = (
            str(example_path(n)) for n in ("expression.tsv", "binding_ratio.tsv", "binding_p.tsv"))
    if not (args.expression and args.binding_ratio and args.binding_p):
        ap.error("EXPRESSION, BINDING_RATIO and BINDING_P are required (or --example)")
    genes, arrays, E = read_matrix(args.expression)
    g2, tfs, R = read_matrix(args.binding_ratio)
    g3, tfs3, P = read_matrix(args.binding_p)
    if g2 != genes or g3 != genes:
        ap.error("the three files must list the same genes in the same order")
    if tfs3 != tfs:
        ap.error("the two ChIP files must list the same TFs in the same order")
    res = run(E, log_ratio(R), P, tfs, alpha=args.alpha, bind_p=args.bind_p, q=args.fdr, select=not args.no_select)
    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    write_counts(out / "counts.csv", res["tfs"], res["counts"])
    write_matrix(out / "activity.tsv", res["tfs"], arrays, res["activity_t"], "%.4f")
    write_matrix(out / "coupling_r.tsv", genes, res["tfs"], res["coupling"]["r"], "%.4f")
    with open(out / "classes.tsv", "w", encoding="utf-8") as f:
        f.write("gene\t" + "\t".join(res["tfs"]) + "\n")
        for g, row in zip(genes, res["classes"]):
            f.write(g + "\t" + "\t".join(CLASSES[int(c)] for c in row) + "\n")
    sel = res["selection"]
    (out / "selection.json").write_text(json.dumps({
        "selected": res["tfs"],
        "dropped": [{"tf": tfs[i], "min_p": p} for i, p in (sel["dropped"] if sel else [])],
        "alpha": sel["alpha"] if sel else None,
    }, indent=1) + "\n")
    print(f"{len(res['tfs'])} of {len(tfs)} TFs kept: {', '.join(res['tfs'])}; outputs in {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
