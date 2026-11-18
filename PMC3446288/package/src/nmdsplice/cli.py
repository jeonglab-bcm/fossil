"""Command line.

  nmdsplice ptc JUNCTIONS.tsv --annotation DIR --genome GENOME.fa [-o OUT.tsv]
  nmdsplice tmm COUNTS.tsv
"""

from __future__ import annotations

import argparse
import sys

import numpy as np

from . import __version__, example_path, load_annotation, ptc_table, read_junctions, tmm_factors, write_table


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="nmdsplice", description="RAINMAN rebuilt: PTC calls and TMM factors.")
    ap.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("ptc", help="call PTCs for junctions (50-nt rule)")
    p.add_argument("junctions", help="TSV with columns chrom, strand, donor, acceptor")
    p.add_argument("--annotation", required=True, help="folder with UCSC refGene, ensGene, knownGene, genscan, exoniphy tables")
    p.add_argument("--genome", required=True, help="FASTA of the genome (or of the genes' regions)")
    p.add_argument("-o", "--output", help="output TSV (default: standard output)")
    t = sub.add_parser("tmm", help="TMM normalisation factors (edgeR) of a count matrix")
    t.add_argument("counts", help="tab-separated counts, one column per library, no header")
    sub.add_parser("example-path", help="print the folder of the bundled example data")
    a = ap.parse_args(argv)
    if a.cmd == "ptc":
        rows = ptc_table(read_junctions(a.junctions), load_annotation(a.annotation), a.genome)
        if a.output:
            with open(a.output, "w", encoding="utf-8") as f:
                write_table(rows, f)
        else:
            write_table(rows, sys.stdout)
    elif a.cmd == "tmm":
        x = np.loadtxt(a.counts, ndmin=2)
        print("\t".join(f"{v:.6f}" for v in tmm_factors(x)))
    elif a.cmd == "example-path":
        print(example_path("example_junctions.tsv").parent)
    else:
        ap.print_help()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
