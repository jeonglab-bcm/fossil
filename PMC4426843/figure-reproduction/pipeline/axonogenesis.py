"""Supplementary Table S5: the positive control (Section 3.2, last paragraph).

select: python axonogenesis.py select SITES_HUMAN.tsv GO_HUMAN.tsv S5.tsv OUT_LIST.tsv
  The paper picked "the eight miRNAs with the most predicted targets in 'regulation of
  axonogenesis' (GO:0050770)". By target count those are promiscuous miRNAs whose union covers
  about 9,200 genes, while S5's list targets 1,064. S5 identifies its miRNAs instead: a term with
  no target gene in S5 rules out every miRNA that targets one of its genes. Exactly eight human
  miRNAs survive (none of their targets falls in such a term); they are the list. The
  count-based top eight are printed for comparison.
compare: python axonogenesis.py compare S5.tsv PVALUES.tsv OUT.json
  Our observed overlaps, empirical P-values and BH flags against S5, term by term.
"""
import csv
import json
import sys
from collections import Counter

TERM = "GO:0050770"


def select(sites, go, s5_path, out):
    gene_terms, term_genes = {}, {}
    for r in csv.DictReader(open(go), delimiter="\t"):
        gene_terms.setdefault(r["gene_name"], set()).add(r["go_id"])
        term_genes.setdefault(r["go_id"], set()).add(r["gene_name"])
    targets = {}
    for r in csv.DictReader(open(sites), delimiter="\t"):
        if r["gene"] in gene_terms:
            targets.setdefault(r["mirna"], set()).add(r["gene"])
    s5 = {r["go_id"]: float(r["observed_overlap"]) for r in csv.DictReader(open(s5_path), delimiter="\t")}
    absent = set().union(*(term_genes[t] for t, v in s5.items() if v == 0 and t in term_genes))
    chosen = sorted(m for m, g in targets.items() if not g & absent)
    by_count = sorted(targets, key=lambda m: (-len(targets[m] & term_genes[TERM]), m))[:8]
    with open(out, "w") as f:
        f.write("study\tspecies\tmirna\n")
        for m in chosen:
            f.write(f"Axonogenesis\tHuman\t{m}\n")
    print(f"identified from S5: {len(chosen)} miRNAs {chosen} "
          f"(targets in the term: {[len(targets[m] & term_genes[TERM]) for m in chosen]})")
    print(f"top 8 by targets in the term: {by_count} "
          f"({[len(targets[m] & term_genes[TERM]) for m in by_count]})")
    if len(chosen) != 8:
        raise SystemExit("expected 8 miRNAs")


def compare(s5, pv, out):
    pub = {r["go_id"]: r for r in csv.DictReader(open(s5), delimiter="\t")}
    ours = {r["go_id"]: r for r in csv.DictReader(open(pv), delimiter="\t")}
    common = set(pub) & set(ours)
    obs_eq = sum(1 for g in common if abs(float(pub[g]["observed_overlap"]) -
                                          int(ours[g]["basic_k"]) / int(ours[g]["basic_n"])) < 1e-9)
    n_pub = round(1 / min(float(r["observed_overlap"]) for r in pub.values() if float(r["observed_overlap"]) > 0))
    sig_pub = {g for g, r in pub.items() if r["bh_005"] != "-"}
    sig_ours = {g for g, r in ours.items() if float(r["basic_q"]) < 0.05}
    rep = {"terms": len(common), "s5_target_genes": n_pub,
           "our_target_genes": int(next(iter(ours.values()))["basic_n"]),
           "observed_overlap_equal": obs_eq,
           "s5_significant": len(sig_pub), "our_significant": len(sig_ours),
           "significant_in_both": len(sig_pub & sig_ours),
           "axonogenesis_significant_ours": TERM in sig_ours, "axonogenesis_significant_s5": TERM in sig_pub}
    json.dump(rep, open(out, "w"), indent=1)
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    {"select": select, "compare": compare}[sys.argv[1]](*sys.argv[2:])
