#!/usr/bin/env python3
"""Choose the human proteins we profile and scan (a profile for all 27,960 proteins of RefSeq
Build 35.1 would take about 4,000 CPU hours here).

A stratified random sample by the flags of Additional file 3 (seed 1): 100 proteins flagged by
both Andreini et al. 2006 and the SPCH-SVM, 50 by Andreini only, 50 by the SPCH-SVM only, and 100
of the 24,162 proteins not in the file. Added in full: the ubiquitin-specific proteases and the
ADAM-TS proteases named in the text, and the two proteins of Figs 8 and 9.

Usage: sample_proteome.py PROTEIN_FA_GZ S3_TXT OUT_FASTA OUT_TSV
"""
import gzip
import random
import re
import sys

SIZES = {"X/X": 100, "X/-": 50, "-/X": 50, "none": 100}
FIG = ("NP_060357.1", "XP_374396.2")
USP = re.compile(r"ubiquitin[- ]specific (protease|peptidase)", re.I)
ADAMTS = re.compile(r"thrombospondin", re.I)
ADAMTS2 = re.compile(r"disintegrin|ADAMTS", re.I)


def main(fa, s3, out_fa, out_tsv):
    seqs, heads, order = {}, {}, []
    name = None
    for line in gzip.open(fa, "rt"):
        if line.startswith(">"):
            name = line.split("|")[3]
            heads[name] = line[1:].strip()
            seqs[name] = []
            order.append(name)
        else:
            seqs[name].append(line.strip())
    flags = {}
    for line in open(s3, encoding="latin-1"):
        p = [x.strip() for x in line.split("|")]
        if len(p) == 3 and p[1] in ("X", "-") and p[2] in ("X", "-"):
            flags[p[0]] = f"{p[1]}/{p[2]}"
    strata = {k: [n for n in order if flags.get(n, "none") == k] for k in SIZES}
    rng = random.Random(1)
    chosen = {}
    for k, n in SIZES.items():
        for name in rng.sample(strata[k], n):
            chosen[name] = f"sample:{k}"
    for name in order:
        h = heads[name]
        if USP.search(h):
            chosen.setdefault(name, "family:USP")
        elif ADAMTS.search(h) and ADAMTS2.search(h):
            chosen.setdefault(name, "family:ADAMTS")
    for name in FIG:
        chosen.setdefault(name, "figure")
    with open(out_fa, "w") as f, open(out_tsv, "w") as g:
        g.write("protein\tgroup\tflags\tstratum_size\tlength\n")
        for name in order:
            if name in chosen:
                s = "".join(seqs[name])
                f.write(f">{name}\n{s}\n")
                st = flags.get(name, "none")
                g.write(f"{name}\t{chosen[name]}\t{st}\t{len(strata[st])}\t{len(s)}\n")
    print(len(chosen), {k: len(v) for k, v in strata.items()})


if __name__ == "__main__":
    main(*sys.argv[1:5])
