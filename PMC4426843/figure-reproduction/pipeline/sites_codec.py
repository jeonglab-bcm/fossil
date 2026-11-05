"""Pack and unpack gene-level miRanda site tables (mirna, gene, sites) for the repository.

pack:   python sites_codec.py pack SITES.tsv OUT.txt.xz
unpack: python sites_codec.py unpack IN.txt.xz SITES.tsv

Packed format (xz-compressed text): line 1 '#genes' then the gene names tab-separated (sorted);
then one line per miRNA: name, tab, comma-separated 'delta:sites' pairs, where delta is the gap
from the previous gene index (first: the index itself) and ':sites' is left out when sites = 1.
unpack(pack(x)) == x, row for row.
"""
import csv
import lzma
import sys
from collections import defaultdict


def pack(src, dst):
    rows = defaultdict(dict)
    for r in csv.DictReader(open(src), delimiter="\t"):
        rows[r["mirna"]][r["gene"]] = int(r["sites"])
    genes = sorted({g for d in rows.values() for g in d})
    gi = {g: i for i, g in enumerate(genes)}
    with lzma.open(dst, "wt", preset=9 | lzma.PRESET_EXTREME) as f:
        f.write("#genes\t" + "\t".join(genes) + "\n")
        for m in sorted(rows):
            prev, parts = 0, []
            for i, s in sorted((gi[g], s) for g, s in rows[m].items()):
                parts.append(f"{i - prev}" if s == 1 else f"{i - prev}:{s}")
                prev = i
            f.write(f"{m}\t{','.join(parts)}\n")


def unpack(src, dst):
    with lzma.open(src, "rt") as f, open(dst, "w") as out:
        genes = f.readline().rstrip("\n").split("\t")[1:]
        out.write("mirna\tgene\tsites\n")
        rows = []
        for line in f:
            m, body = line.rstrip("\n").split("\t")
            i = 0
            for p in body.split(","):
                d, _, s = p.partition(":")
                i += int(d)
                rows.append((m, genes[i], int(s or 1)))
        for m, g, s in sorted(rows):
            out.write(f"{m}\t{g}\t{s}\n")


if __name__ == "__main__":
    {"pack": pack, "unpack": unpack}[sys.argv[1]](*sys.argv[2:4])
