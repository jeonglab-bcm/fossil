#!/usr/bin/env python3
"""Fig. 1a read categories and per-gene read counts of one mapped sample.

Genome reads are placed by their midpoint (leftmost position + 37): exonic when it lies in any RefSeq
exon, intronic when inside a RefSeq transcript but not an exon, intergenic otherwise. Junction reads
are the reads assigned to the junction database (full length and truncated). Gene counts are the
exonic reads of the longest RefSeq model of each gene plus the junction reads of junctions inside
that model's span (Additional file 1: "Longest RefSeq model per MGI mouse gene symbol were used as
gene boundary").

Usage: summarize_mapping.py MAPDIR ANNOT_DIR GENOME.fa.fai SAMPLE OUTDIR
Writes OUTDIR/<SAMPLE>_categories.json and OUTDIR/<SAMPLE>_gene_counts.tsv.
"""

import json
import sys
from collections import defaultdict

import numpy as np

from nmdsplice.annotation import read_genepred, refseq_genes

MID = 37


def main(mapdir, annot, fai, sample, outdir):
    sizes = {l.split("\t")[0]: int(l.split("\t")[1]) for l in open(fai)}
    ref = read_genepred(f"{annot}/refGene.txt.gz", "refGene")
    ref = [t for t in ref if t.chrom in sizes]
    genes = refseq_genes(ref, set(sizes))
    stats = json.load(open(f"{mapdir}/mapping_stats.json"))
    h = np.load(f"{mapdir}/genome_hits.npz")
    names = list(h["chroms"])
    chrom_idx = np.concatenate([h["chrom"], h["trunc_chrom"]])
    pos = np.concatenate([h["pos"], h["trunc_pos"]]).astype(np.int64) + MID
    longest = [g.longest() for g in genes]
    by_chrom = defaultdict(list)
    for t in ref:
        by_chrom[t.chrom].append(t)
    # Hypothesis test for Fig. 1a: exons and transcripts of all five repositories instead of RefSeq only
    others = []
    for src in ("knownGene", "ensGene", "genscan", "exoniphy"):
        others += [t for t in read_genepred(f"{annot}/{src}.txt.gz", src) if t.chrom in sizes]
    oth_by_chrom = defaultdict(list)
    for t in others:
        oth_by_chrom[t.chrom].append(t)
    alt = {"exonic": 0, "intronic": 0, "intergenic": 0}
    counts = np.zeros(len(genes), np.int64)
    cat = {"exonic": 0, "intronic": 0, "intergenic": 0}
    for ci, c in enumerate(names):
        n = sizes[c]
        exon = np.zeros(n, bool)
        genic = np.zeros(n, bool)
        gene_id = np.full(n, -1, np.int32)
        for t in by_chrom.get(c, ()):
            genic[t.tx_start : t.tx_end] = True
            for a, b in t.exons:
                exon[a:b] = True
        for gi, (g, t) in enumerate(zip(genes, longest)):
            if g.chrom == c:
                for a, b in t.exons:
                    gene_id[a:b] = gi
        sel = chrom_idx == ci
        p = np.clip(pos[sel], 0, n - 1)
        e = exon[p]
        gn = genic[p]
        cat["exonic"] += int(e.sum())
        cat["intronic"] += int((gn & ~e).sum())
        cat["intergenic"] += int((~gn).sum())
        for t in oth_by_chrom.get(c, ()):
            if t.source in ("knownGene", "ensGene"):
                genic[t.tx_start : t.tx_end] = True
            for a, b in t.exons:
                exon[a:b] = True
        e2 = exon[p]
        g2 = genic[p]
        alt["exonic"] += int(e2.sum())
        alt["intronic"] += int((g2 & ~e2).sum())
        alt["intergenic"] += int((~g2).sum())
        gid = gene_id[p]
        gid = gid[gid >= 0]
        counts += np.bincount(gid, minlength=len(genes))
        del exon, genic, gene_id

    # junction reads
    jreads = 0
    span = defaultdict(list)
    for gi, t in enumerate(longest):
        span[t.chrom].append((t.tx_start, t.tx_end, gi))
    for c in span:
        span[c].sort()
    starts = {c: np.array([s for s, _, _ in v]) for c, v in span.items()}
    with open(f"{mapdir}/junction_counts.tsv") as f:
        next(f)
        for line in f:
            jid, r, rt = line.rstrip("\n").split("\t")
            n = int(r) + int(rt)
            jreads += n
            chrom, rest = jid.rsplit(":", 1)
            d, a = (int(x) for x in rest.split("-"))
            if chrom not in span:
                continue
            k = np.searchsorted(starts[chrom], d, side="right")
            for s, e, gi in span[chrom][max(0, k - 50) : k]:
                if s < d and a < e:
                    counts[gi] += n
    cat["junction"] = jreads
    # Reads, not alignments: a truncated read whose two halves both map has two alignments in the
    # categories above but is one mapped read.
    cat["total_mapped"] = stats["genome"] + stats["junction"] + stats["truncation_recovered"]
    cat["alignments_in_categories"] = cat["exonic"] + cat["intronic"] + cat["intergenic"] + cat["junction"]
    cat["reads"] = stats["reads"]
    cat["mapping_frequency"] = cat["total_mapped"] / stats["reads"]
    cat["truncation_recovered"] = stats["truncation_recovered"]
    cat["junction_full_length"] = stats["junction_reads_full_length"]
    cat["all_repositories"] = alt
    with open(f"{outdir}/{sample}_categories.json", "w") as fo:
        json.dump(cat, fo, indent=1)
    with open(f"{outdir}/{sample}_gene_counts.tsv", "w") as fo:
        fo.write("gene\tmodel\tchrom\tstrand\tstart\tend\tlength\treads\n")
        for g, t, n in zip(genes, longest, counts):
            fo.write(f"{g.symbol}\t{t.name}\t{g.chrom}\t{g.strand}\t{t.tx_start}\t{t.tx_end}\t{t.length}\t{n}\n")
    print(json.dumps(cat))


if __name__ == "__main__":
    main(*sys.argv[1:6])
