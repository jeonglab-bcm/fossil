"""The GO universe against the paper: 15,733 human genes, Supplementary Table S1's 9,462 terms and sizes.

Usage: python go_universe.py S1_TERMS.tsv HSA_GO.tsv MMU_GO.tsv OUT.json
Genes are counted by gene name (Ensembl 'Associated Gene Name'); terms are used as annotated
(no propagation to ancestor terms), all evidence codes.
"""
import csv
import json
import sys
from collections import defaultdict


def terms(path):
    t = defaultdict(set)
    for r in csv.DictReader(open(path), delimiter="\t"):
        t[r["go_id"]].add(r["gene_name"])
    return t


def main(s1_path, hsa, mmu, out):
    s1 = {r["go_id"]: int(r["term_size"]) for r in csv.DictReader(open(s1_path), delimiter="\t")}
    h, m = terms(hsa), terms(mmu)
    rep = {
        "human_genes": len(set().union(*h.values())), "paper_human_genes": 15733,
        "human_terms": len(h), "s1_terms": len(s1),
        "s1_terms_present": len(set(s1) & set(h)),
        "s1_term_sizes_equal": sum(1 for g, k in s1.items() if len(h.get(g, ())) == k),
        "ion_transport_size": len(h["GO:0006811"]), "paper_ion_transport_size": 327,
        "mouse_genes": len(set().union(*m.values())), "mouse_terms": len(m),
    }
    json.dump(rep, open(out, "w"), indent=1)
    print(json.dumps(rep))


if __name__ == "__main__":
    main(*sys.argv[1:5])
