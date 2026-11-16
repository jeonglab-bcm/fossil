"""Gene-level miRNA targets and site counts from miRanda per-pair summaries.

Usage: python gene_sites.py MAP.tsv OUT.tsv PAIRS.tsv [PAIRS.tsv ...]
       [--sites max|sum|longest|sum_tx|last|first] [--order ORDER.txt] [--key name|gene_id] [--all-pairs]

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
  last     sites on the gene's last passing transcript in ORDER.txt (default: MAP.tsv's order)
  first    sites on the gene's first passing transcript in ORDER.txt

last and first model a script that reads miRanda's transcript-level output and assigns
d[gene][mirna] = sites for every passing line, so that a later transcript overwrites an earlier
one (or, for first, keeps the first). miRanda writes the lines of one miRNA in the order of the
UTR FASTA, which for the authors was a BioMart export of unknown order (issue #33, PR #34 review);
ORDER.txt is one transcript ID per line.

--key gene_id aggregates per Ensembl gene ID first and then sums the IDs that share a gene name:
a script keyed by gene ID scores the copies of a gene on haplotypes and patches separately, and
each copy then counts once in the multi-hit sums of every term the name is in.

--all-pairs counts sites on every pair miRanda reports (each site scoring >= 140), not only on pairs
passing the thresholds above: a reading of the multi-hit algorithm in which the site counts, unlike
the target genes, are not filtered (issue #33).

OUT.tsv: mirna, gene, sites.
"""
import csv
import sys
from collections import defaultdict


def main(argv):
    all_pairs = "--all-pairs" in argv
    argv = [a for a in argv if a != "--all-pairs"]
    opts = {"--sites": "max", "--order": None, "--key": "name"}
    for o in list(opts):
        if o in argv:
            i = argv.index(o)
            opts[o] = argv[i + 1]
            argv = argv[:i] + argv[i + 2:]
    mode, key = opts["--sites"], opts["--key"]
    map_path, out, *pairs = argv
    col = "gene_name" if key == "name" else "gene_id"
    genes = defaultdict(set)
    length = {}
    ntx = defaultdict(int)
    txs = defaultdict(list)  # (uid, gene key) -> transcripts
    name_of = {}
    rows = list(csv.DictReader(open(map_path), delimiter="\t"))
    for r in rows:
        genes[r["uid"]].add(r[col])
        length[r["uid"]] = int(r["length"])
        ntx[(r["uid"], r[col])] += 1
        txs[(r["uid"], r[col])].append(r["transcript_id"])
        name_of[r[col]] = r["gene_name"]
    if opts["--order"]:
        pos = {t.strip(): i for i, t in enumerate(open(opts["--order"])) if t.strip()}
    else:
        pos = {r["transcript_id"]: i for i, r in enumerate(rows)}
    missing = {r["transcript_id"] for r in rows} - set(pos)
    if mode in ("last", "first") and missing:
        sys.exit(f"{len(missing)} transcripts of MAP.tsv are not in the order file")
    best = {}
    for p in pairs:
        for line in open(p):
            f = line.rstrip("\n").split("\t")
            m, u, tot_sc, tot_en = f[0], f[1], float(f[2]), float(f[3])
            if not all_pairs and not (tot_sc >= 155 and tot_en <= -20):
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
                elif mode in ("last", "first"):
                    p_ = (max if mode == "last" else min)(pos[t] for t in txs[(u, g)])
                    cur = best.get(k)
                    if cur is None or (p_ > cur[0] if mode == "last" else p_ < cur[0]):
                        best[k] = (p_, n)
                else:
                    cur = best.get(k)
                    if cur is None or length[u] > cur[0]:
                        best[k] = (length[u], n)
    final = defaultdict(int)  # by gene name; gene IDs sharing a name are summed
    for (m, g), v in best.items():
        final[(m, name_of[g])] += v[1] if isinstance(v, tuple) else v
    best = final
    with open(out, "w") as fo:
        fo.write("mirna\tgene\tsites\n")
        for (m, g), v in sorted(best.items()):
            fo.write(f"{m}\t{g}\t{v}\n")
    print(f"{len(best)} miRNA-gene pairs, {len({m for m, _ in best})} miRNAs, "
          f"{len({g for _, g in best})} genes", file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1:])
