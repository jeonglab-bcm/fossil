"""Collapse identical 3' UTR sequences before running miRanda.

Usage: python dedup_utrs.py UTRS.fa UNIQUE.fa MAP.tsv
UNIQUE.fa: one record per distinct sequence (>u000001 ...).
MAP.tsv: uid, transcript_id, gene_id, gene_name, gene_biotype, transcript_biotype, seqname, length.
"""
import sys

seqs, order, rows = {}, [], []
name = None
for line in open(sys.argv[1]):
    if line.startswith(">"):
        name = line[1:].strip().split("|")
    else:
        s = line.strip()
        if s not in seqs:
            seqs[s] = f"u{len(seqs) + 1:06d}"
            order.append(s)
        rows.append([seqs[s]] + name + [str(len(s))])
with open(sys.argv[2], "w") as f:
    for s in order:
        f.write(f">{seqs[s]}\n{s}\n")
with open(sys.argv[3], "w") as f:
    f.write("uid\ttranscript_id\tgene_id\tgene_name\tgene_biotype\ttranscript_biotype\tseqname\tlength\n")
    for r in rows:
        f.write("\t".join(r) + "\n")
print(f"{len(rows)} UTRs, {len(seqs)} distinct, {sum(map(len, order))} nt", file=sys.stderr)
