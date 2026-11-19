#!/usr/bin/env python3
"""RefSeq stop codons: Fig. S2 (distances) and the background bars of Fig. 7b (codon identity).

Fig. S2: for the longest coding RefSeq model of each gene, (A) the distance from the stop codon to
the 3' end of the mRNA when the stop is in the last exon, (B) the distance to the nearest downstream
exon-exon junction when it is in the second-to-last exon.
Fig. 7b: stop-codon identity of the RefSeq stops, and the TAA/TAG/TGA shares of all mm9
trinucleotides (all three frames) in exonic, intronic and intergenic sequence.

Usage: refseq_stops.py ANNOT_DIR GENOME.fa OUT.json
"""

import json
import sys
from collections import Counter

import numpy as np
import pysam

from nmdsplice.annotation import read_genepred, refseq_genes
from nmdsplice.ptc import first_stop, spliced

CODE = np.full(256, 4, np.uint8)
for i, b in enumerate(b"ACGT"):
    CODE[b] = i
    CODE[b + 32] = i
STOPS = {"TAA": (3, 0, 0), "TAG": (3, 0, 2), "TGA": (3, 2, 0)}
RC = {"TAA": "TTA", "TAG": "CTA", "TGA": "TCA"}  # reverse complements, read on the forward strand


def longest_models(genes):
    out = []
    for g in genes:
        coding = [t for t in g.refseq if t.coding]
        if coding:
            out.append(max(coding, key=lambda t: (t.length, t.name)))
    return out


def main(annot, genome, out):
    fa = pysam.FastaFile(genome)
    chroms = set(fa.references)
    ref = read_genepred(f"{annot}/refGene.txt.gz", "refGene")
    genes = refseq_genes(ref, chroms)
    models = longest_models(genes)
    last, penult = [], []
    codons = Counter()
    for t in models:
        start = t.cds_start if t.strand == "+" else t.cds_end - 1
        seq = spliced(fa, t.chrom, t.exons, t.strand)
        r = first_stop(t.exons, t.strand, start, seq)
        if r is None or r[1] is None:
            continue
        tpos, stop, juncs, total = r
        codons[seq[stop : stop + 3]] += 1
        # exon of the stop (transcript order)
        bounds = juncs + [total]
        k = next(i for i, b in enumerate(bounds) if stop < b)
        n_ex = len(bounds)
        if k == n_ex - 1:
            last.append(total - (stop + 3))
        elif k == n_ex - 2:
            penult.append(juncs[-1] - (stop + 3))
    res = {"models": len(models), "models_with_stop": sum(codons.values()),
           "refseq_stop_codons": dict(codons),
           "figS2a_last_exon_distance": last, "figS2b_penultimate_distance": penult}

    # trinucleotide background: exonic (RefSeq exons, transcript strand), intronic (RefSeq introns,
    # transcript strand), intergenic (outside RefSeq genes, forward strand)
    region_counts = {k: Counter() for k in ("exonic", "intronic", "intergenic")}
    by_chrom = {}
    for t in ref:
        if t.chrom in chroms:
            by_chrom.setdefault(t.chrom, []).append(t)
    for chrom in fa.references:
        s = np.frombuffer(fa.fetch(chrom).encode(), np.uint8)
        c = CODE[s]
        n = c.size
        lab = np.zeros(n, np.int8)  # 0 intergenic, 1 intronic, 2 exonic
        strand = np.zeros(n, np.int8)  # +1 / -1 for genic positions
        for t in by_chrom.get(chrom, ()):
            lab[t.tx_start : t.tx_end] = np.maximum(lab[t.tx_start : t.tx_end], 1)
            strand[t.tx_start : t.tx_end] = 1 if t.strand == "+" else -1
        for t in by_chrom.get(chrom, ()):
            for a, b in t.exons:
                lab[a:b] = 2
        tri_ok = (c[:-2] < 4) & (c[1:-1] < 4) & (c[2:] < 4)
        same = (lab[:-2] == lab[2:])
        for name, codes in STOPS.items():
            fw = (c[:-2] == codes[0]) & (c[1:-1] == codes[1]) & (c[2:] == codes[2])
            rcs = RC[name]
            rc = (c[:-2] == "ACGT".index(rcs[0])) & (c[1:-1] == "ACGT".index(rcs[1])) & (c[2:] == "ACGT".index(rcs[2]))
            l0 = lab[:-2]
            st = strand[:-2]
            region_counts["intergenic"][name] += int((fw & tri_ok & same & (l0 == 0)).sum())
            for lv, key in ((1, "intronic"), (2, "exonic")):
                m = tri_ok & same & (l0 == lv)
                region_counts[key][name] += int((fw & m & (st == 1)).sum() + (rc & m & (st == -1)).sum())
        print(chrom, file=sys.stderr)
    res["trinucleotide_stop_counts"] = {k: dict(v) for k, v in region_counts.items()}
    with open(out, "w") as f:
        json.dump(res, f)


if __name__ == "__main__":
    main(*sys.argv[1:4])
