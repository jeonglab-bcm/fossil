"""Command line: hivrecomb ALIGNMENT.fasta [-o OUT.csv] [--bins ...] [--min-count 3]."""

from __future__ import annotations

import argparse
import csv
import sys

from . import __version__, example_path
from .align import read_fasta
from .recombination import as_array, bin_events, concat_events, pair_events


def read_alignment(path):
    """An aligned FASTA whose names end in '|<time>' (the sample's time, in generations)."""
    seqs = read_fasta(path)
    names = list(seqs)
    if not names:
        raise SystemExit(f"no sequences in {path}")
    try:
        times = [float(n.rsplit("|", 1)[1]) for n in names]
    except (IndexError, ValueError):
        raise SystemExit("every sequence name must end in '|<time in generations>'") from None
    return as_array([seqs[n] for n in names]), times


def write_rows(binned, out) -> None:
    w = csv.writer(out)
    w.writerow(["bin_low", "bin_high", "pairs", "found", "probability", "error"])
    for k in range(len(binned.centers)):
        pairs = int(binned.pairs[k])
        found = int(binned.counts[k])
        w.writerow([f"{binned.edges[k]:g}", f"{binned.edges[k + 1]:g}", pairs, found,
                    "" if not pairs else f"{found / pairs:.6f}",
                    "" if not found else f"{found / pairs / found ** 0.5:.6f}"])


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="hivrecomb",
        description="Probability of the missing haplotype per distance bin, from a time series "
                    "alignment (Neher and Leitner 2010).")
    ap.add_argument("input", nargs="?", help="aligned FASTA, names '<id>|<time in generations>'")
    ap.add_argument("-o", "--output", help="output CSV (default: standard output)")
    ap.add_argument("--bins", nargs="+", type=float, default=[0, 30, 60, 90],
                    help="bin edges in alignment columns (default: 0 30 60 90)")
    ap.add_argument("--min-count", type=int, default=3,
                    help="least number of times each allele must be seen (default: 3)")
    ap.add_argument("--by-distance-time", action="store_true",
                    help="bin by distance x elapsed generations instead of by distance")
    ap.add_argument("--example-path", action="store_true",
                    help="print the path of the bundled example alignment and exit")
    ap.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    a = ap.parse_args(argv)

    if a.example_path:
        print(example_path())
        return 0
    if not a.input:
        ap.error("INPUT is required")
    X, times = read_alignment(a.input)
    ev = concat_events([pair_events(X, times, min_count=a.min_count)])
    x = ev["d"] * ev["dt"] if a.by_distance_time else ev["d"]
    binned = bin_events(x, ev["found"], a.bins)
    if a.output:
        with open(a.output, "w", newline="", encoding="utf-8") as f:
            write_rows(binned, f)
    else:
        write_rows(binned, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
