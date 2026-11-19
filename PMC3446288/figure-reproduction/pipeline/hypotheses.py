#!/usr/bin/env python3
"""Hypothesis tests behind the causes in results_notes.json (run once; the record is output/hypotheses.json).

Usage: hypotheses.py JUNCTIONS_ANNOTATED.tsv.gz ANNOT_DIR FASTQ_DIR OUT.json
Not part of the default pipeline: it needs the reads (FASTQ_DIR) for the N-content test.
"""
import gzip
import json
import sys
from collections import Counter

import numpy as np

from nmdsplice.annotation import read_genepred
from nmdsplice.classes import infer_events

S = ["BMM_WT", "BMM_KO", "Liver_WT", "Liver_KO"]
T = {"BMM": ("BMM_WT", "BMM_KO"), "Liver": ("Liver_WT", "Liver_KO")}
jann, annot, fq, out = sys.argv[1:5]
rows = []
with gzip.open(jann, "rt") as f:
    hdr = next(f).rstrip("\n").split("\t")
    for line in f:
        rows.append(dict(zip(hdr, line.rstrip("\n").split("\t"))))
res = {}
# 1. PTC calls without the false-positive gene filter, and the share that is unannotated
for t, (w, k) in T.items():
    ev = [r for r in rows if int(r[w]) >= 3 or int(r[k]) >= 3]
    res[f"ptc_{t}"] = {"evident": len(ev), "ptc_after_filter": sum(r["ptc"] == "1" for r in ev),
                       "ptc_without_filter": sum(r["ptc_status"] == "ptc" for r in ev),
                       "unannotated": sum(r["ptc_status"] == "unannotated" for r in ev)}
# 2. AS junctions per sample with at least 3 reads (Fig. 3b caption says no cutoff)
for s in S:
    res[f"as_min3_{s}"] = sum(1 for r in rows if r["gene"] and r["canonical"] == "0" and int(r[s]) >= 3)
for t, (w, k) in T.items():
    res[f"as_min3_union_{t}"] = sum(1 for r in rows if r["gene"] and r["canonical"] == "0" and (int(r[w]) >= 3 or int(r[k]) >= 3))
# 3. Table 1 without the 3-read evidence cut-off
sets = {s: read_genepred(f"{annot}/{s}.txt.gz", s) for s in ("refGene", "knownGene", "ensGene", "genscan", "exoniphy")}
exons = {(t.chrom, t.strand, a, b) for ts in sets.values() for t in ts for a, b in t.exons}
first, last = set(), set()
for src in ("refGene", "knownGene", "ensGene"):
    for t in sets[src]:
        if len(t.exons) > 1:
            f_, l_ = (t.exons[0], t.exons[-1]) if t.strand == "+" else (t.exons[-1], t.exons[0])
            first.add((t.chrom, t.strand, *f_))
            last.add((t.chrom, t.strand, *l_))
key = lambda r: (r["chrom"], int(r["donor"]), int(r["acceptor"]))
ptc = {key(r): r["ptc"] == "1" for r in rows}
gene = {key(r): r["gene"] for r in rows}
strand = {key(r): r["strand"] for r in rows}
for t, (w, k) in T.items():
    jd = {key(r): (int(r[w]), int(r[k])) for r in rows if r["gene"] and int(r[w]) + int(r[k]) > 0}
    evs = [e for e in infer_events(jd, exons, first, last, ptc, gene, strand) if e.regulated]
    c = Counter(e.cls for e in evs)
    res[f"table1_no_cutoff_{t}"] = {"ES": c["SES"] + c["MES"], **{k_: c[k_] for k_ in ("SES", "MES", "A5SS", "A3SS", "AFE", "ALE", "MXE")}}
# 4. reads with an N (a quality filter the paper may have applied)
for r_ in ("SRR094621", "SRR094622", "SRR094623", "SRR094624"):
    n = withn = 0
    with gzip.open(f"{fq}/{r_}.fastq.gz", "rt") as f:
        for i, line in enumerate(f):
            if i % 4 == 1:
                n += 1
                withn += "N" in line
            if n >= 2_000_000:
                break
    res[f"reads_with_N_{r_}"] = withn / n
json.dump(res, open(out, "w"), indent=1)
print(json.dumps(res, indent=1))
