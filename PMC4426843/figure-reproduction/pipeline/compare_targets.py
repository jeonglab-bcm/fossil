"""Compare per-study target gene sets with Supplementary Table S3 ('miRanda Targets').

Usage: python compare_targets.py LISTS.tsv S3_TARGETS.tsv OUT.csv SITES_HUMAN.tsv GO_HUMAN.tsv \
           SITES_MOUSE.tsv GO_MOUSE.tsv

Targets of a list = union of genes targeted by its miRNAs, restricted to genes with at least one
biological-process GO term (the paper's universe).

Some S3 gene names were turned into dates by a spreadsheet: MARCH1 -> 36951.0 (1 March 2001),
SEPT7 -> 1 September 2007, SEP15 -> 1 September 2015, and so on (mouse: March1, Sept7). They are
mapped back before comparison; SEPT/SEP is resolved against the gene universe.
"""
import csv
import datetime
import sys
from collections import defaultdict


def undate(name, species="Human", known=()):
    try:
        v = float(name)
    except ValueError:
        return name
    d = datetime.date(1899, 12, 30) + datetime.timedelta(days=int(v))
    word = {3: "MARCH", 9: "SEPT", 12: "DEC"}.get(d.month)
    if not (word and d.day == 1):
        return name
    words = [word, "SEP"] if word == "SEPT" else [word]  # SEP15 (selenoprotein) -> 1 Sep 2015
    names = [f"{w if species == 'Human' else w.capitalize()}{d.year % 100}" for w in words]
    return next((n for n in names if n in known), names[0])


def main(lists, s3, out, sh, gh, sm, gm):
    univ, targets = {}, {}
    for sp, sites, go in (("Human", sh, gh), ("Mouse", sm, gm)):
        univ[sp] = {r["gene_name"] for r in csv.DictReader(open(go), delimiter="\t")}
        t = defaultdict(set)
        for r in csv.DictReader(open(sites), delimiter="\t"):
            t[r["mirna"]].add(r["gene"])
        targets[sp] = t
    studies = defaultdict(list)
    species = {}
    for r in csv.DictReader(open(lists), delimiter="\t"):
        studies[r["study"]].append(r["mirna"])
        species[r["study"]] = r["species"]
    pub = defaultdict(set)
    stated = {}
    for r in csv.DictReader(open(s3), delimiter="\t"):
        if r["prediction"] == "miranda":
            pub[r["study"]].add(undate(r["gene"], r["species"], univ[r["species"]]))
            stated[r["study"]] = int(r["stated_count"])
    with open(out, "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["study", "species", "mirnas", "s3_targets", "our_targets", "both", "only_s3",
                    "only_ours", "jaccard"])
        for s in sorted(studies, key=str.lower):
            sp = species[s]
            ours = set().union(*(targets[sp].get(m, set()) for m in studies[s])) & univ[sp]
            p = pub[s]
            both = ours & p
            w.writerow([s, sp, len(studies[s]), stated[s], len(ours), len(both), len(p - ours),
                        len(ours - p), f"{len(both) / len(ours | p):.4f}"])
            print(f"{s:15s} {sp:5s} {len(studies[s]):4d} S3 {stated[s]:6d} ours {len(ours):6d} "
                  f"only-S3 {len(p - ours):4d} only-ours {len(ours - p):4d}")


if __name__ == "__main__":
    main(*sys.argv[1:8])
