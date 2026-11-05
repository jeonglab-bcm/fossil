"""Gene-level miRNA targets and site counts from miRanda per-pair summaries.

Usage: python gene_sites.py MAP.tsv OUT.tsv PAIRS.tsv [PAIRS.tsv ...] [--sites max|sum|longest]

MAP.tsv: dedup_utrs.py output (uid -> transcripts and gene names).
PAIRS.tsv: run_miranda.sh output, one line per miRNA-UTR pair with at least one site
(miRanda defaults: site score >= 140): mirna, uid, total score, total energy, max score,
max energy, strand, len1, len2, positions.

A pair passes when its total score >= 155 and total energy <= -20 kcal/mol. The paper states
"score > 155, free energy < -20"; Supplementary Table S3's miRanda target lists are reproduced by
the inclusive thresholds on the totals (miRanda's own -sc/-en semantics), not by strict ones and not
by per-site filtering (see README). A miRNA targets a gene (by gene name) when any of the gene's
3' UTRs passes.

Sites per (miRNA, gene) for the multi-hit algorithm, over the gene's passing UTRs:
  max      the largest number of sites on one UTR (default)
  sum      sites summed over the gene's distinct passing UTR sequences
  longest  sites on the longest passing UTR
  sum_tx   sites summed over the gene's passing transcripts (a UTR shared by k transcripts counts k times)

OUT.tsv: mirna, gene, sites.
"""
import csv
import sys
from collections import defaultdict


def main(argv):
    mode = "max"
    if "--sites" in argv:
        i = argv.index("--sites")
        mode = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    map_path, out, *pairs = argv
    genes = defaultdict(set)
    length = {}
    ntx = defaultdict(int)
    for r in csv.DictReader(open(map_path), delimiter="\t"):
        genes[r["uid"]].add(r["gene_name"])
        length[r["uid"]] = int(r["length"])
        ntx[(r["uid"], r["gene_name"])] += 1
    best = {}
    for p in pairs:
        for line in open(p):
            f = line.rstrip("\n").split("\t")
            m, u, tot_sc, tot_en = f[0], f[1], float(f[2]), float(f[3])
            if not (tot_sc >= 155 and tot_en <= -20):
                continue
            n = len(f[9].split())
            for g in genes[u]:
                k = (m, g)
                if mode == "max":
                    best[k] = max(best.get(k, 0), n)
                elif mode == "sum":
                    best[k] = best.get(k, 0) + n
                elif mode == "sum_tx":
                    best[k] = best.get(k, 0) + n * ntx[(u, g)]
                else:
                    cur = best.get(k)
                    if cur is None or length[u] > cur[0]:
                        best[k] = (length[u], n)
    with open(out, "w") as fo:
        fo.write("mirna\tgene\tsites\n")
        for (m, g), v in sorted(best.items()):
            fo.write(f"{m}\t{g}\t{v[1] if isinstance(v, tuple) else v}\n")
    print(f"{len(best)} miRNA-gene pairs, {len({m for m, _ in best})} miRNAs, "
          f"{len({g for _, g in best})} genes", file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1:])
