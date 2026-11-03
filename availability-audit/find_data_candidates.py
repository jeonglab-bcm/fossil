"""List papers whose code is unavailable but whose input data survives and is small.

Code unavailable: readiness tier D, E or G in paper_audit.csv (own-resource links dead, or no
own-resource link and no code supplement). Data available: data-type supplementary files that are
intact in the PMC dataset (20 MB in total at most), or a GEO / ArrayExpress / SRA accession that
still resolves. Papers are ranked by a heuristic score: supplement captions that describe input
data (dataset, benchmark, training/test set, gold standard, raw or expression data) count for,
captions that describe results (predictions, ranked lists) count against, and code that once
existed (tiers D and E) ranks above code never released (G). The ranking is a starting point;
check the files before choosing a paper.

Writes data_candidates.csv.
"""
import csv
import re
from collections import defaultdict

MAX_BYTES = 20e6
DATA_EXT = {"csv", "tsv", "txt", "tab", "xls", "xlsx", "dat", "fasta", "fa", "fas", "faa", "fna", "gff", "gtf",
            "bed", "vcf", "json", "xml", "zip", "gz", "tgz", "tar.gz", "bz2", "tar", "arff", "mat", "rdata", "rda",
            "sbml", "nex", "nwk", "phy", "aln", "obo", "owl", "sdf", "mol2", "pdb"}
INPUT = re.compile(r"(?i)\b(data ?sets?|benchmark|training (set|data)|test (set|data)|gold standard|raw data|input|"
                   r"expression (data|matrix|profiles?)|sequences? (used|analy[sz]ed)|simulated data|time.series|"
                   r"corpus|network (data|file)|interaction data|matrix of)\b")
OUTPUT = re.compile(r"(?i)\b(results? of|predict(ed|ions)|list of (genes|predicted)|top \d+|ranked|enriched|"
                    r"significant)\b")


def read(name):
    with open(name) as f:
        return list(csv.DictReader(f))


def main():
    papers = {r["pmcid"]: r for r in read("paper_audit.csv")}
    caption = {(r["pmcid"], r["href"]): r["caption"] for r in read("supplements.csv")}
    files = defaultdict(list)
    for s in read("supplement_status.csv"):
        if s["status"].startswith("ok") and s["ext"] in DATA_EXT and s["has_code"] != "True":
            files[s["pmcid"]].append(s)
    live = {(r["type"], r["accession"]) for r in read("accession_status.csv") if r["status"] == "live"}
    accs = defaultdict(set)
    for r in read("accessions.csv"):
        if r["type"] in ("GEO", "ArrayExpress", "SRA/ENA/DDBJ") and (r["type"], r["accession"]) in live:
            accs[r["pmcid"]].add(r["accession"])
    out = []
    for p, paper in papers.items():
        if paper["tier"] not in ("D", "E", "G"):
            continue
        size = sum(int(s["bytes"] or 0) for s in files[p])
        if not (files[p] and size <= MAX_BYTES) and not accs[p]:
            continue
        caps = [caption.get((p, s["href"]), "") for s in files[p]]
        n_in = sum(bool(INPUT.search(c)) for c in caps)
        n_out = sum(bool(OUTPUT.search(c)) and not INPUT.search(c) for c in caps)
        score = 3 * min(n_in, 2) - n_out + 2 * (paper["tier"] in ("D", "E")) + bool(accs[p])
        out.append({"pmcid": p, "year": paper["year"], "journal": paper["journal"], "tier": paper["tier"],
                    "score": score, "data_files": len(files[p]), "data_mb": round(size / 1e6, 2),
                    "input_data_captions": n_in, "live_accessions": " ".join(sorted(accs[p])),
                    "title": paper["title"],
                    "input_captions": " || ".join(c[:150] for c in caps if INPUT.search(c))})
    out.sort(key=lambda r: (-r["score"], r["data_mb"]))
    with open("data_candidates.csv", "w", newline="") as f:
        w = csv.DictWriter(f, list(out[0]))
        w.writeheader()
        w.writerows(out)
    print(len(out), "papers;", sum(r["input_data_captions"] > 0 for r in out), "with captions describing input data;",
          sum(r["input_data_captions"] > 0 and r["tier"] in ("D", "E") for r in out), "of those with lost code (D/E)")


if __name__ == "__main__":
    main()
