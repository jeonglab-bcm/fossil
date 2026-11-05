"""Cut the 3' UTR of every Ensembl transcript from a GTF and its genome.

Usage: python extract_utrs.py GTF.gz GENOME.fa.gz OUT.fa [CORE_PREFIX]

CORE_PREFIX: path prefix of the Ensembl core tables seq_region and assembly_exception
(CORE_PREFIX__seq_region.txt.gz, CORE_PREFIX__assembly_exception.txt.gz). In the toplevel FASTA a
haplotype or patch sequence holds N wherever it equals its parent chromosome; Ensembl (and
BioMart, from which the paper took its sequences) reads those bases from the parent. With
CORE_PREFIX the same is done here: alt = parent[:start-1] + alt[start-1:end] + parent[parent_end:].

Ensembl GTFs (release 75) give UTR exons as 'UTR' features without saying which end they belong
to. A UTR exon lies in the 3' UTR when it is downstream of the stop codon (or of the last CDS base
when the transcript has no stop codon feature). The exons are spliced in transcript order.

Header: >transcript_id|gene_id|gene_name|gene_biotype|transcript_biotype|seqname
Transcripts without CDS (no 3' UTR by definition) are skipped.
"""
import gzip
import re
import sys
from collections import defaultdict

COMP = str.maketrans("ACGTNacgtn", "TGCANtgcan")
ATTR = re.compile(r'(\S+) "([^"]*)"')


def read_gtf(path):
    tx = {}
    utr = defaultdict(list)
    cds = defaultdict(list)
    for line in gzip.open(path, "rt"):
        if line.startswith("#"):
            continue
        f = line.rstrip("\n").split("\t")
        feat = f[2]
        if feat not in ("UTR", "CDS", "stop_codon"):
            continue
        a = dict(ATTR.findall(f[8]))
        t = a["transcript_id"]
        if t not in tx:
            tx[t] = (a["gene_id"], a.get("gene_name", ""), a.get("gene_biotype", ""),
                     f[1] if "transcript_biotype" not in a else a["transcript_biotype"], f[0], f[6])
        s, e = int(f[3]), int(f[4])
        if feat == "UTR":
            utr[t].append((s, e))
        else:
            cds[t].append((s, e))
    return tx, utr, cds


def read_genome(path, wanted):
    seqs = {}
    name, buf = None, []
    for line in gzip.open(path, "rt"):
        if line.startswith(">"):
            if name in wanted:
                seqs[name] = "".join(buf)
            name, buf = line[1:].split()[0], []
        elif name in wanted:
            buf.append(line.strip())
    if name in wanted:
        seqs[name] = "".join(buf)
    return seqs


def fill_alt(g, core):
    names = {}
    for line in gzip.open(f"{core}__seq_region.txt.gz", "rt"):
        f = line.rstrip("\n").split("\t")
        names[f[0]] = f[1]
    n = 0
    for line in gzip.open(f"{core}__assembly_exception.txt.gz", "rt"):
        f = line.rstrip("\n").split("\t")
        alt, s, e, kind, ref, rs, re_ = names[f[1]], int(f[2]), int(f[3]), f[4], names[f[5]], int(f[6]), int(f[7])
        if kind == "PAR" or alt not in g or ref not in g:
            continue
        if s != rs:
            raise SystemExit(f"{alt}: exception starts at {s}, parent at {rs}")
        a = g[alt]
        filled = g[ref][:s - 1] + a[s - 1:e] + g[ref][re_:]
        if len(filled) != len(a):
            raise SystemExit(f"{alt}: filled length {len(filled)} != {len(a)}")
        g[alt] = filled
        n += 1
    print(f"{n} haplotype and patch sequences filled from their parent chromosomes", file=sys.stderr)


def main(gtf, genome, out, core=None):
    tx, utr, cds = read_gtf(gtf)
    seqnames = {v[4] for v in tx.values()}
    g = read_genome(genome, seqnames | ({str(c) for c in range(1, 23)} | {"X", "Y", "MT"}
                                        if core else set()))
    if core:
        fill_alt(g, core)
    n = skipped = 0
    with open(out, "w") as fo:
        for t, (gid, gname, gbt, tbt, chrom, strand) in tx.items():
            if t not in cds or t not in utr:
                continue
            if chrom not in g:
                skipped += 1
                continue
            if strand == "+":
                end = max(e for _, e in cds[t])
                parts = sorted((s, e) for s, e in utr[t] if s > end)
                seq = "".join(g[chrom][s - 1:e] for s, e in parts)
            else:
                start = min(s for s, _ in cds[t])
                parts = sorted(((s, e) for s, e in utr[t] if e < start), reverse=True)
                seq = "".join(g[chrom][s - 1:e][::-1].translate(COMP) for s, e in parts)
            if not seq:
                continue
            fo.write(f">{t}|{gid}|{gname}|{gbt}|{tbt}|{chrom}\n{seq.upper()}\n")
            n += 1
    print(f"{n} 3' UTRs written; {skipped} transcripts on sequences missing from the genome",
          file=sys.stderr)


if __name__ == "__main__":
    main(*sys.argv[1:5])
