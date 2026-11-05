"""Empirical GO enrichment for miRNA lists (Bleazard et al. 2015, Methods and Section 3.4).

Usage:
  python empirical.py --sites SITES.tsv --go GO.tsv --lists LISTS.tsv --species Human \
      --size M --iterations 999999 --seed S --out OUT_PREFIX [--hist GO:0006811] [--threads N]

SITES.tsv: mirna, gene, sites (gene-level counts of miRanda sites passing the thresholds).
GO.tsv: build_go.py output; genes are identified by gene name, as in the paper's universe.
LISTS.tsv: study, species, mirna (Supplementary Table S3).

For every study of the given species whose list has M miRNAs, and for the shared null of M
miRNAs drawn without replacement from all miRNAs of the species in SITES.tsv:

  basic:     overlap(term) = |targets in term| / |targets|, targets = union over the miRNAs;
  multi-hit: score(gene) = sites summed over the miRNAs; overlap(term) = sum of member-gene
             scores / sum of all gene scores.
The denominators count every predicted target gene, with or without a biological-process term
(--denominator all): Supplementary Table S5's overlaps are k/1064 for a list whose 1,064 targets
include genes without a term. Term counts k use the 15,733-gene universe (S1, S3).

Empirical P = (number of draws with overlap >= observed) / iterations. Supplementary Table S5
shows the published P-values are integer multiples of 1/999999 and include 0, so the default
is 999999 draws and no pseudo-count. Ties are compared exactly (integer cross-multiplication).

Writes OUT_PREFIX.counts.tsv (per study and term: observed numerator and denominator, number of
draws at or above it, for both algorithms), OUT_PREFIX.null.tsv (per term: mean target count and
mean overlap across draws) and, with --hist, the null distribution of target counts in that term.
"""
import argparse
import csv
from collections import defaultdict

import numpy as np
import scipy.sparse as sp


def load(args):
    go_rows = list(csv.DictReader(open(args.go), delimiter="\t"))
    univ = sorted({r["gene_name"] for r in go_rows})
    site_rows = list(csv.DictReader(open(args.sites), delimiter="\t"))
    # Genes without a biological-process term come after the universe: they count in the
    # all-genes denominator and in no term.
    genes = univ + sorted({r["gene"] for r in site_rows} - set(univ))
    gi = {g: i for i, g in enumerate(genes)}
    terms = sorted({r["go_id"] for r in go_rows})
    ti = {t: i for i, t in enumerate(terms)}
    pairs = {(gi[r["gene_name"]], ti[r["go_id"]]) for r in go_rows}
    r_, c_ = zip(*pairs)
    go = sp.csr_matrix((np.ones(len(pairs), np.float32), (c_, r_)), shape=(len(terms), len(genes)))

    sites = defaultdict(dict)
    for r in site_rows:
        sites[r["mirna"]][gi[r["gene"]]] = int(r["sites"])
    pool = sorted(args.pool_names) if args.pool_names else sorted(sites)
    S = np.zeros((len(pool), len(genes)), np.float32)
    for i, m in enumerate(pool):
        for g, n in sites.get(m, {}).items():
            S[i, g] = n
    return genes, len(univ), terms, go, pool, S


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sites", required=True)
    ap.add_argument("--go", required=True)
    ap.add_argument("--lists", required=True)
    ap.add_argument("--species", required=True)
    ap.add_argument("--pool", help="file with one miRNA name per line (default: all in SITES)")
    ap.add_argument("--size", type=int, required=True)
    ap.add_argument("--iterations", type=int, default=999999)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--batch", type=int, default=2000)
    ap.add_argument("--hist", action="append", default=[])
    ap.add_argument("--denominator", choices=["all", "universe"], default="all",
                    help="overlap = term genes / all target genes (default; Supplementary Table S5) "
                         "or / target genes with a biological-process term")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    args.pool_names = [l.strip() for l in open(args.pool) if l.strip()] if args.pool else None

    genes, G_univ, terms, go, pool, S = load(args)
    D = len(genes) if args.denominator == "all" else G_univ
    go = go.astype(np.float32)
    ST = np.ascontiguousarray(S.T)                      # genes x miRNAs, site counts
    AT = (ST > 0).astype(np.float32)                    # genes x miRNAs, targeted
    pi = {m: i for i, m in enumerate(pool)}
    studies = defaultdict(list)
    for r in csv.DictReader(open(args.lists), delimiter="\t"):
        if r["species"] == args.species:
            studies[r["study"]].append(r["mirna"])
    studies = {s: v for s, v in studies.items() if len(v) == args.size}
    for s, v in studies.items():
        miss = [m for m in v if m not in pi]
        if miss:
            print(f"warning: {s}: {len(miss)} miRNAs not in the pool: {miss}")

    def stats(XT):
        """XT: miRNAs x B 0/1 matrix. Basic: k (terms x B), n (B); multi-hit: w, tot.
        Float32 sums of 0/1 and small integer counts are exact here (all below 2**24)."""
        u = (AT @ XT > 0).astype(np.float32)          # genes x B, union of targets
        k = go @ u
        sc = ST @ XT                                    # genes x B, summed sites
        w = go @ sc
        return (k.astype(np.float64), u[:D].sum(0, dtype=np.float64),
                w.astype(np.float64), sc[:D].sum(0, dtype=np.float64))

    obs = {}
    for s, v in studies.items():
        XT = np.zeros((len(pool), 1), np.float32)
        for m in v:
            if m in pi:
                XT[pi[m], 0] = 1
        k, n, w, tot = stats(XT)
        obs[s] = (k[:, 0], n[0], w[:, 0], tot[0])

    rng = np.random.default_rng(args.seed)
    T = len(terms)
    ge_basic = {s: np.zeros(T, np.int64) for s in studies}
    ge_multi = {s: np.zeros(T, np.int64) for s in studies}
    sum_k = np.zeros(T)
    sum_ov = np.zeros(T)
    sum_n = 0.0
    hist_idx = [terms.index(h) for h in args.hist]
    hist = {h: np.zeros(G_univ + 1, np.int64) for h in args.hist}
    done = 0
    M = len(pool)
    while done < args.iterations:
        B = min(args.batch, args.iterations - done)
        if args.size == 1:
            idx = rng.integers(0, M, size=(B, 1))
        else:
            idx = np.argpartition(rng.random((B, M)), args.size - 1, axis=1)[:, :args.size]
        XT = np.zeros((M, B), np.float32)
        XT[idx.T, np.arange(B)[None, :]] = 1
        k, n, w, tot = stats(XT)
        # overlap_sim >= overlap_obs  <=>  k_sim * n_obs >= k_obs * n_sim (exact in float64)
        for s, (k0, n0, w0, t0) in obs.items():
            ge_basic[s] += (k * n0 >= k0[:, None] * n[None, :]).sum(1)
            ge_multi[s] += (w * t0 >= w0[:, None] * tot[None, :]).sum(1)
        sum_k += k.sum(1)
        sum_ov += (k / np.maximum(n, 1)[None, :]).sum(1)
        sum_n += n.sum()
        for h, j in zip(args.hist, hist_idx):
            hist[h] += np.bincount(k[j].astype(np.int64), minlength=G_univ + 1)
        done += B

    with open(args.out + ".counts.tsv", "w") as f:
        f.write("study\tgo_id\tbasic_k\tbasic_n\tbasic_ge\tmulti_w\tmulti_total\tmulti_ge\titerations\n")
        for s, (k0, n0, w0, t0) in sorted(obs.items()):
            for j, t in enumerate(terms):
                f.write(f"{s}\t{t}\t{int(k0[j])}\t{int(n0)}\t{ge_basic[s][j]}\t{int(w0[j])}\t{int(t0)}\t"
                        f"{ge_multi[s][j]}\t{args.iterations}\n")
    with open(args.out + ".null.tsv", "w") as f:
        f.write("go_id\tterm_size\tmean_k\tmean_overlap\tmean_n\n")
        size = np.asarray(go.sum(1)).ravel()
        for j, t in enumerate(terms):
            f.write(f"{t}\t{int(size[j])}\t{float(sum_k[j]) / args.iterations!r}\t"
                    f"{float(sum_ov[j]) / args.iterations!r}\t{float(sum_n) / args.iterations!r}\n")
    for h in args.hist:
        with open(args.out + f".hist_{h.replace(':', '')}.tsv", "w") as f:
            f.write("k\tdraws\n")
            for kk, c in enumerate(hist[h]):
                if c:
                    f.write(f"{kk}\t{c}\n")
    print(f"species {args.species} size {args.size}: {len(studies)} studies, pool {M}, "
          f"denominator {args.denominator} ({D} genes), "
          f"{args.iterations} draws, mean targets {sum_n / args.iterations:.1f}")


if __name__ == "__main__":
    main()
