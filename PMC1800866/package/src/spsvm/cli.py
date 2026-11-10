"""Command line: spsvm QUERY.pssm [QUERY.pssm ...] [--train PROFILES.npz --labels TABLE] [-o OUT.csv]."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from . import (
    SPSVM,
    __version__,
    chain_from_profile,
    descriptors,
    example_path,
    predict_protein,
    read_ascii_pssm,
    read_profiles,
    read_table,
)
from .core import Chain


def train_model(profiles_npz, labels, variant="CH"):
    """Fit the SP-SVM on profiles (``write_profiles`` format) and a label table (Additional file 1 format)."""
    profiles = read_profiles(profiles_npz)
    table = read_table(labels)
    chains = [Chain(n, profiles[n].sequence, descriptors(profiles[n]), table[n]) for n in sorted(table) if n in profiles]
    if not chains:
        raise SystemExit("no chain of the label table has a profile")
    return SPSVM(variant).fit(chains)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="spsvm",
        description="Zinc-binding probability of the C and H residues of proteins, from PSI-BLAST ASCII PSSMs "
        "(SP-SVM, Passerini et al. 2007).",
    )
    ap.add_argument("pssm", nargs="*", help="PSI-BLAST -out_ascii_pssm files, one protein each")
    ap.add_argument("--train", help="training profiles (.npz from spsvm.write_profiles; default: the bundled example)")
    ap.add_argument("--labels", help="training labels, rows 'class chain position residue' (default: the bundled example)")
    ap.add_argument("--min-weight", type=float, default=0.015, help="skip residues whose profile relative weight is below this (default 0.015)")
    ap.add_argument("--threshold", type=float, default=0.7, help="probability for the protein call (default 0.7)")
    ap.add_argument("-o", "--output", help="output CSV (default: standard output)")
    ap.add_argument("--example-path", action="store_true", help="print the path of the bundled example query and exit")
    ap.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = ap.parse_args(argv)
    if args.example_path:
        print(example_path("czib_NP_060357.1.pssm"))
        return 0
    if not args.pssm:
        ap.error("give at least one PSSM file")
    model = train_model(args.train or example_path("example_train_profiles.npz"),
                        args.labels or example_path("example_train_labels.txt"))
    out = open(args.output, "w", newline="", encoding="utf-8") if args.output else sys.stdout
    w = csv.writer(out)
    w.writerow(["protein", "position", "residue", "p_local", "p_semipattern", "p_gated", "protein_called"])
    for path in args.pssm:
        prof = read_ascii_pssm(path)
        chain = chain_from_profile(Path(path).stem, prof, residues="CH", min_weight=args.min_weight)
        probs = model.predict_chain(chain)
        call = int(predict_protein(probs, args.threshold, 3))
        for p in sorted(probs):
            v = probs[p]
            w.writerow([chain.name, p + 1, prof.sequence[p], f"{v['local']:.4f}", f"{v['semipattern']:.4f}", f"{v['gated']:.4f}", call])
    if args.output:
        out.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
