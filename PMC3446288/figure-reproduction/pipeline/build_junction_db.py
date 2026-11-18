#!/usr/bin/env python3
"""Build the combinatorial exon-exon junction database (FASTA for bowtie-build) and its size.

Usage: build_junction_db.py ANNOT_DIR GENOME.fa OUT.fa STATS.json [--flank 71]
Flank 71 = 75-nt reads minus the 4-nt overhang. Junctions with an exon shorter than 4 nt are left out
of the FASTA (no read can overhang them); they still count in the database size.
"""

import argparse
import json

import pysam

from nmdsplice.annotation import read_genepred, refseq_genes
from nmdsplice.junctiondb import combinatorial_junctions, write_fasta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("annot")
    ap.add_argument("genome")
    ap.add_argument("out")
    ap.add_argument("stats")
    ap.add_argument("--flank", type=int, default=71)
    a = ap.parse_args()
    fa = pysam.FastaFile(a.genome)
    chroms = set(fa.references)
    sets = {s: read_genepred(f"{a.annot}/{s}.txt.gz", s) for s in ("refGene", "knownGene", "ensGene", "genscan", "exoniphy")}
    genes = refseq_genes(sets["refGene"], chroms)
    J = combinatorial_junctions(genes, sets)
    with open(a.out, "w") as f:
        n = write_fasta(J, fa, f, a.flank)
    canonical = set()
    for g in genes:
        for t in g.refseq:
            canonical.update((g.chrom, d, ac) for d, ac in t.junctions())
    stats = {"junctions": len(J), "in_fasta": n, "refseq_genes": len(genes),
             "refseq_junctions_in_db": sum(1 for j in J if (j.chrom, j.donor, j.acceptor) in canonical)}
    json.dump(stats, open(a.stats, "w"), indent=1)
    print(json.dumps(stats))


if __name__ == "__main__":
    main()
