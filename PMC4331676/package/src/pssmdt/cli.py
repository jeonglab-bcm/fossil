"""Command line: pssmdt PSSM [PSSM ...] [-o OUT.csv] [--lg 5] [--encoding PSSM-DT]."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from . import DEFAULT_LG, ENCODINGS, __version__, encode, example_path, feature_names, read_pssm


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="pssmdt",
        description="Encode PSI-BLAST ASCII PSSMs as PSSM-DT (or a comparator) feature vectors: "
                    "one CSV row per file.",
    )
    ap.add_argument("pssm", nargs="*", help="ASCII PSSM files (psiblast -out_ascii_pssm)")
    ap.add_argument("-o", "--output", help="output CSV (default: standard output)")
    ap.add_argument("--lg", type=int, default=DEFAULT_LG, help=f"largest lag LG (default {DEFAULT_LG})")
    ap.add_argument("--encoding", default="PSSM-DT", choices=ENCODINGS, help="default PSSM-DT")
    ap.add_argument("--example-path", action="store_true",
                    help="print the folder of the bundled example PSSMs and exit")
    ap.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = ap.parse_args(argv)

    if args.example_path:
        print(example_path("pssm"))
        return 0
    if not args.pssm:
        ap.error("give at least one PSSM file")
    rows = []
    for p in args.pssm:
        seq, s = read_pssm(p)
        rows.append((Path(p).stem, encode(s, seq, args.encoding, args.lg)))
    n = len(rows[0][1])
    names = feature_names(args.lg) if args.encoding == "PSSM-DT" else [f"f{i + 1}" for i in range(n)]
    out = open(args.output, "w", newline="", encoding="utf-8") if args.output else sys.stdout
    try:
        w = csv.writer(out)
        w.writerow(["id", *names])
        for name, v in rows:
            w.writerow([name, *(repr(float(x)) for x in v)])
    finally:
        if args.output:
            out.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
