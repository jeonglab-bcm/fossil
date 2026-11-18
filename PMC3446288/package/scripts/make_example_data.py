#!/usr/bin/env python3
"""Make the package's example data from the paper's Additional files 8 and 9 and the UCSC mm9 files.

Run from the repository root after the reproduction's inputs are downloaded:
  python PMC3446288/package/scripts/make_example_data.py PMC3446288/sources PMC3446288/package/src/nmdsplice/data

Writes:
  example_junctions.tsv   junctions of 12 PTC events from Additional files 8 and 9
  example_expected.tsv    the paper's printed PTC distance of each (the expected output)
  example_annotation/     the refGene, ensGene, knownGene, genscan and exoniphy rows of those genes
  example_genome.fa       mm9 sequence of each gene's region (records named chrom:start-end)
"""

import gzip
import os
import sys
import warnings

import pandas as pd
import pysam

GENES = ["Acot8", "Clk1", "Dpp7", "Fus", "Hnrnph1", "Mgea5", "Psmg2", "Snrpa1", "Vps29",  # exclusion
         "Dnajc5", "Hnrnpl", "2410004B18Rik"]  # inclusion
PAD = 2000


def main(sources, outdir):
    warnings.filterwarnings("ignore")
    os.makedirs(f"{outdir}/example_annotation", exist_ok=True)
    rows = []
    for f, mode in (("gb-2012-13-5-r35-S8.XLS", "inclusion"), ("gb-2012-13-5-r35-S9.XLS", "exclusion")):
        x = pd.read_excel(f"{sources}/supp/files/{f}", header=None, skiprows=2)
        cur = None
        for _, r in x.iterrows():
            if isinstance(r[0], str):
                cur = (r[0], r[2], r[3], int(r[8]))
                first = True
            else:
                first = False
            if cur is None or pd.isna(r[4]) or cur[0] not in GENES:
                continue
            if first:  # the paper prints the PTC distance on the event's first junction
                rows.append((cur[0], cur[1], cur[2], int(r[4]), int(r[5]), mode, cur[3]))
    regions = {}
    ann_rows = {}
    for t in ("refGene", "ensGene", "knownGene", "genscan", "exoniphy"):
        ann_rows[t] = []
    models = [l.split("\t") for t in ("refGene", "ensGene") for l in gzip.open(f"{sources}/annot/{t}.txt.gz", "rt")]
    for g, chrom, strand, d, a, mode, dist in rows:
        # every RefSeq and Ensembl model that overlaps the junction, so the model choice is the full run's
        spans = [(int(p[4]), int(p[5])) for p in models if p[2] == chrom and int(p[4]) < a and int(p[5]) > d]
        regions[g] = (chrom, min(s for s, _ in spans) - PAD, max(e for _, e in spans) + PAD)
    for t, (name_col, chrom_col) in {"refGene": (1, 2), "ensGene": (1, 2), "knownGene": (0, 1),
                                     "genscan": (1, 2), "exoniphy": (1, 2)}.items():
        for line in gzip.open(f"{sources}/annot/{t}.txt.gz", "rt"):
            p = line.split("\t")
            c, s, e = p[chrom_col], int(p[chrom_col + 2]), int(p[chrom_col + 3])
            if any(c == rc and s >= rs and e <= re_ for rc, rs, re_ in regions.values()):
                ann_rows[t].append(line)
        with gzip.open(f"{outdir}/example_annotation/{t}.txt.gz", "wt") as fo:
            fo.writelines(ann_rows[t])
    fa = pysam.FastaFile(f"{sources}/genome/mm9.fa")
    with open(f"{outdir}/example_genome.fa", "w") as fo:
        for g, (c, s, e) in sorted(regions.items()):
            seq = fa.fetch(c, s, e)
            fo.write(f">{c}:{s}-{e} {g}\n")
            for i in range(0, len(seq), 60):
                fo.write(seq[i : i + 60] + "\n")
    with open(f"{outdir}/example_junctions.tsv", "w") as fj, open(f"{outdir}/example_expected.tsv", "w") as fe:
        fj.write("gene\tchrom\tstrand\tdonor\tacceptor\n")
        fe.write("gene\tchrom\tdonor\tacceptor\tevent\tptc_distance\n")
        for g, c, st, d, a, mode, dist in rows:
            fj.write(f"{g}\t{c}\t{st}\t{d}\t{a}\n")
            fe.write(f"{g}\t{c}\t{d}\t{a}\tPTC upon {mode}\t{dist}\n")
    print(len(rows), "junctions")


if __name__ == "__main__":
    main(*sys.argv[1:3])
