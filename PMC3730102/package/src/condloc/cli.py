"""Command line: condloc EXPRESSION.tsv LINKS.tsv [-o OUTPUT.tsv] writes the coherence of every link."""

from __future__ import annotations

import argparse
import sys

from . import __version__, example_path, link_coherence


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="condloc", description="Expression coherence of interacting proteins "
                                 "(CoLP, Lee et al. 2013): Phi = -log2 Psi[min(med a, med b) / MEDIAN * r(a, b)].")
    ap.add_argument("expression", nargs="?", help="TSV: protein, then one column per sample")
    ap.add_argument("links", nargs="?", help="TSV with a header: protein_a, protein_b")
    ap.add_argument("-o", "--output", help="output TSV (default: standard output)")
    ap.add_argument("--example-path", action="store_true", help="print the bundled example paths and exit")
    ap.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = ap.parse_args(argv)
    if args.example_path:
        print(example_path("example_expression.tsv"))
        print(example_path("example_network.tsv"))
        return 0
    if not args.expression or not args.links:
        ap.error("EXPRESSION and LINKS are required")
    rows = link_coherence(args.expression, args.links)
    out = open(args.output, "w") if args.output else sys.stdout
    out.write("protein_a\tprotein_b\tcoherence\n")
    for a, b, p in rows:
        out.write(f"{a}\t{b}\t{p + 0.0:.12g}\n")
    if args.output:
        out.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
