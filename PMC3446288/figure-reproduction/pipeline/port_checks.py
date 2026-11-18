#!/usr/bin/env python3
"""Executable checks: our PTC detection against the paper's printed PTC distances, our TMM against
edgeR on our junction counts, and the arithmetic of the paper's own claims from its own tables.

Usage: port_checks.py SUPP_DIR ANNOT_DIR GENOME.fa JUNCTION_MATRIX.tsv.gz PAPER_VALUES.json OUT.json [--rscript R]
"""

import argparse
import json
import subprocess
import warnings

import numpy as np
import pandas as pd

from nmdsplice.api import load_annotation
from nmdsplice.fasta import Fasta
from nmdsplice.ptc import ExonCatalog, ModelIndex, detect
from nmdsplice.quant import tmm_factors


def ptc_distance_check(supp, annot, genome):
    warnings.filterwarnings("ignore")
    ann = load_annotation(annot)
    cat, models = ExonCatalog(ann), ModelIndex(ann["refGene"], ann["ensGene"])
    fa = Fasta(genome)
    res = {}
    rows = []
    for f, mode in (("gb-2012-13-5-r35-S8.XLS", "inclusion"), ("gb-2012-13-5-r35-S9.XLS", "exclusion")):
        x = pd.read_excel(f"{supp}/{f}", header=None, skiprows=2)
        n = called = same = 0
        cur = None
        for _, r in x.iterrows():
            if isinstance(r[0], str):
                cur = (r[0], r[2], r[3], int(r[8]))
                first = True
            else:
                first = False
            if cur is None or pd.isna(r[4]) or not first:
                continue
            n += 1
            p = detect(fa, cat, models, cur[1], cur[2], int(r[4]), int(r[5]))
            called += p.ptc
            same += p.ptc and p.distance == cur[3]
            rows.append({"gene": cur[0], "event": mode, "paper_distance": cur[3], "status": p.status, "distance": p.distance})
        res[mode] = {"events": n, "ptc": called, "same_distance": same}
    e, i = res["exclusion"], res["inclusion"]
    passed = e["same_distance"] == e["events"]
    detail = (f"PTC-upon-exclusion events of Additional file 9: {e['ptc']} of {e['events']} called PTC+, "
              f"{e['same_distance']} with the printed PTC distance; PTC-upon-inclusion events of Additional file 8 "
              f"(first junction): {i['ptc']} of {i['events']} called PTC+, {i['same_distance']} with the printed distance. "
              "Pass mark: 90% of the exclusion events at the printed distance.")
    return {"passed": bool(passed), "detail": detail}, rows


def tmm_check(matrix, rscript):
    x = np.loadtxt(matrix, delimiter="\t")
    ours = tmm_factors(x)
    code = (f'x <- as.matrix(read.table(gzfile("{matrix}"))); suppressMessages(library(edgeR)); '
            'cat(sprintf("%.10f", calcNormFactors(x)), "\\n"); cat(as.character(packageVersion("edgeR")), "\\n")')
    out = subprocess.run([rscript, "-e", code], capture_output=True, text=True, check=True).stdout.split("\n")
    edger = np.array([float(v) for v in out[0].split()])
    ver = out[1].strip()
    diff = float(np.max(np.abs(ours - edger)))
    return {"passed": diff < 1e-6,
            "detail": f"nmdsplice.tmm_factors and edgeR {ver} calcNormFactors on the {x.shape[0]:,} x 4 junction count "
                      f"matrix: largest difference {diff:.1e} (ours {', '.join(f'{v:.4f}' for v in ours)})"}


def arithmetic(pv):
    """Each claim recomputed from the paper's own tables; the ones that do not come back are paper errors."""
    def n(s):
        return float(str(s).replace(",", ""))
    claims = []
    f2 = pv["fig2a"]
    claims.append(("up junctions per gene, BMM 2.3", round(n(f2["BMM"]["all"]["up"][0]) / n(f2["BMM"]["all"]["up"][1]), 1) == 2.3))
    claims.append(("up junctions per gene, liver 3.2", round(n(f2["Liver"]["all"]["up"][0]) / n(f2["Liver"]["all"]["up"][1]), 1) == 3.2))
    for t in ("BMM", "Liver"):
        tot = sum(n(f2[t]["ptc"][k][0]) for k in ("up", "unregulated", "down"))
        claims.append((f"PTC+ up share {t} 43-44%", 43 <= round(100 * n(f2[t]["ptc"]["up"][0]) / tot) <= 44))
    claims.append(("NMD share of AS, BMM 0.47 x 0.35 = 16%", round(100 * 0.47 * 0.35) == 16))
    claims.append(("NMD share of AS, liver 0.45 x 0.39 = 18%", round(100 * 0.45 * 0.39) == 18))
    for s, (a, b) in {"BMM_WT": ("8,107", 2.195), "BMM_KO": ("9,447", 2.470), "Liver_WT": ("25,390", 5.341), "Liver_KO": ("31,041", 4.573)}.items():
        # the paper truncates: 9,447 / 2.470 = 3,824.7 is printed 3,824
        claims.append((f"AS junctions per million, {s} (truncated)", int(n(a) / b) == n(pv["fig3b"]["per_million"][s])))
    for s in pv["fig1a"]:
        d = pv["fig1a"][s]
        claims.append((f"Fig. 1a total = sum of categories, {s}", sum(n(d[k]) for k in ("exonic", "junction", "intronic", "intergenic")) == n(d["total_mapped"])))
    for t in ("BMM", "Liver"):
        tb = pv["table1"][t]
        claims.append((f"Table 1 {t}: total ES = single + multiple", n(tb["Total ES"]["total"]) == n(tb["Single ES"]["total"]) + n(tb["Multiple ES"]["total"])))
        claims.append((f"Table 1 {t}: PTC+ ES = PTC upon exclusion + inclusion", n(tb["Total ES"]["ptc"]) == n(tb["Total ES"]["ptc_upon_exclusion"]) + n(tb["Total ES"]["ptc_upon_inclusion"])))
        s2 = pv["tableS2"][t]
        claims.append((f"Table S2 {t}: TopHat share of all junctions {s2['tophat_all_pct']}%", round(100 * n(s2["tophat_all"]) / n(s2["all"])) == n(s2["tophat_all_pct"])))
        claims.append((f"Table S2 {t}: TopHat share of PTC+ junctions {s2['tophat_ptc_pct']}%", round(100 * n(s2["tophat_ptc"]) / n(s2["ptc"])) == n(s2["tophat_ptc_pct"])))
    claims.append(("SES PTC+ share 40% (BMM) and 60% (liver), Table 1", round(100 * (148 + 80) / 511) == 40 and round(100 * (531 + 320) / 1505) == 60))
    claims.append(("PTC upon inclusion share of SES inclusion 40% BMM / 55% liver (320/573 = 55.8%)",
                   round(100 * 80 / 201) == 40 and round(100 * 320 / 573) == 55))
    liver = pv["tableS5"]["Liver"]
    with_asnmd = [g for g, v in liver.items() if v[3] is not None]
    up = [g for g in with_asnmd if n(liver[g][3]) > 1.5]
    down = [g for g in with_asnmd if n(liver[g][3]) < 1 / 1.5]
    claims.append(("Table S5: 19 liver factors with AS-NMD, 10 deregulated > 1.5-fold, 5 up and 5 down",
                   len(with_asnmd) == 19 and len(up) == 5 and len(down) == 5))
    ok = [c for c, v in claims if v]
    bad = [c for c, v in claims if not v]
    known = {"up junctions per gene, BMM 2.3", "PTC upon inclusion share of SES inclusion 40% BMM / 55% liver (320/573 = 55.8%)",
             "Table S2 BMM: TopHat share of all junctions 4%", "Table S2 BMM: TopHat share of PTC+ junctions 20%",
             "Table S2 Liver: TopHat share of all junctions 11%", "Table S2 Liver: TopHat share of PTC+ junctions 24%",
             "SES PTC+ share 40% (BMM) and 60% (liver), Table 1"}
    unexplained = [c for c in bad if c not in known]
    return {"passed": not unexplained,
            "detail": f"{len(ok)} of {len(claims)} claims come back from the paper's own tables; the other "
                      f"{len(bad)} are slips in the paper: {'; '.join(bad)}" + (f". Unexplained: {unexplained}" if unexplained else "")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("supp")
    ap.add_argument("annot")
    ap.add_argument("genome")
    ap.add_argument("matrix")
    ap.add_argument("paper_values")
    ap.add_argument("out")
    ap.add_argument("--rscript", default="Rscript")
    a = ap.parse_args()
    ptc, rows = ptc_distance_check(a.supp, a.annot, a.genome)
    out = {"ptc_distance": ptc, "ptc_distance_rows": rows, "tmm_edger": tmm_check(a.matrix, a.rscript),
           "arithmetic": arithmetic(json.load(open(a.paper_values)))}
    with open(a.out, "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "ptc_distance_rows"}, indent=1))


if __name__ == "__main__":
    main()
