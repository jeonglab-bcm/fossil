"""Write the reproduction report and fail if a result moves.

Usage: python check_reproduction.py af2_check.txt cath_scop.json matrices.json arithmetic.json > report.md
"""

import json
import sys

# Our results, pinned: a change in inputs or code that moves one of them fails the run.
EXPECTED = {
    "af1_domains": 2911,
    "af1_in_cath_3_0_0": 2911,
    "af1_without_scop_equivalent": 12,
    "queries_with_same_topology_and_fold_template": 2325,
    "cath_domains_compared": 71578,
    "cath_domains_equivalent": 51173,
    "af3_rows": 69,
    "af3_nres_equal_cath_length": 207,
    "af3_tn_same_in_both": 69,
    "af3_fp_differs_in_both": 63,
    "af3_fp_score_above_tn": 62,
    "blosum62_third_bit": {"slope": 0.286, "r": 0.925},
    "aaindex2_top": "CROG050101",
    "gonnet_rank": 6,
}


def main(af2_check, cath_scop, matrices, arithmetic):
    a2 = open(af2_check).read().strip()
    cs = json.load(open(cath_scop))["summary"]
    mx = json.load(open(matrices))
    ar = json.load(open(arithmetic))
    got = {k: cs[k] for k in EXPECTED if k in cs}
    got["af1_without_scop_equivalent"] = len(cs["af1_without_scop_equivalent"])
    got["blosum62_third_bit"] = {k: mx["blosum62_third_bit"][k] for k in ("slope", "r")}
    got["aaindex2_top"] = mx["aaindex2"]["top5_dot_product"][0]["id"]
    got["gonnet_rank"] = mx["aaindex2"]["gonnet_GONG920101"]["rank"]
    failures = [f"{k}: {got[k]} (expected {v})" for k, v in EXPECTED.items() if got[k] != v]
    if not a2.startswith("884 glyphs, 0 closer"):
        failures.append("Additional File 2 transcription: " + a2)

    t2 = ar["table2"]
    diag = mx["af4"]["diagonal_with_unique_x"]
    ag = mx["aaindex2"]
    print("# PMC1955748 reproduction report\n")
    print("| Item | Paper | Ours |")
    print("| --- | --- | --- |")
    rows = [
        ("Additional File 2 transcription", "image of 210 values", a2),
        ("Training set (Additional File 1)", "2911 sequence-unique domains",
         f"{cs['af1_domains']} IDs, {cs['af1_unique']} unique, {cs['af1_in_cath_3_0_0']} in CATH 3.0.0"),
        ("CATH and SCOP domains compared, equivalent (75% of the larger)", "63,010, 43,773",
         f"{cs['cath_domains_compared']} CATH domains ({cs['scop_domains_compared']} SCOP domains) in "
         f"{cs['pdb_entries_in_both']} shared PDB entries; {cs['cath_domains_equivalent']} equivalent"),
        ("Training domains without a SCOP 1.69 equivalent", "0 (all were chosen from equivalent domains)",
         f"{len(cs['af1_without_scop_equivalent'])} under the stated rule, "
         f"{len(cs['af1_without_scop_equivalent_75pct_of_smaller'])} under 75% of the smaller domain"),
        ("Queries with a template of the same CATH topology and SCOP fold", "1,641",
         f"{cs['queries_with_same_topology_and_fold_template']} (of the {cs['af1_domains'] - len(cs['af1_without_scop_equivalent'])} with a SCOP fold)"),
        ("Additional File 3 rows (top template false)", "69", str(cs["af3_rows"])),
        ("Additional File 3 domain lengths equal to CATH 3.0.0", "", f"{cs['af3_nres_equal_cath_length']} of {3 * cs['af3_rows']}"),
        ("Additional File 3 true negatives with same topology and fold", "", f"{cs['af3_tn_same_in_both']} of {cs['af3_rows']}"),
        ("Additional File 3 false positives with different topology and fold", "all (\"according to both\")", f"{cs['af3_fp_differs_in_both']} of {cs['af3_rows']}"),
        ("Additional File 3 false positive scoring above the true negative", "all", f"{cs['af3_fp_score_above_tn']} of {cs['af3_rows']}"),
        ("ASH matrix vs BLOSUM62 (1/3 bit, AF4's axis): slope, r", ".52, .94",
         f"{mx['blosum62_third_bit']['slope']}, {mx['blosum62_third_bit']['r']} (Additional File 2)"),
        ("Additional File 4 black diagonal points vs Additional File 2", "same matrix",
         "; ".join(f"{k}: {v['af4']} vs {v['af2']}" for k, v in diag.items())),
        ("AAindex entries", "98", f"{ag['entries']} (AAindex2 today)"),
        ("Closest AAindex matrix by dot product", "Gonnet (.89)",
         f"{ag['top5_dot_product'][0]['id']} ({ag['top5_dot_product'][0]['dot']}); Gonnet {ag['gonnet_GONG920101']['dot']}, rank {ag['gonnet_GONG920101']['rank']}"),
        ("Closest AAindex matrix by RMSD", "SDM (.13)",
         f"same order as the dot product for unit-length matrices; no tried normalization gives Gonnet first by dot product and SDM first by RMSD"),
        ("Table 2, CPU/Align = CPU (s) / 2071", ", ".join(v["printed_cpu_per_align"] for v in t2.values()),
         ", ".join(str(v["cpu_s_over_2071"]) for v in t2.values())),
        ("Table 2, Rel. to FAST", ", ".join(v["printed_rel_to_fast"] for v in t2.values()),
         ", ".join(str(v["cpu_over_fast"]) for v in t2.values())),
        ("Test-set pairs, 2930 domains", "4,298,905 (abstract); 2930 x 2929/2 (text)", str(ar["test_set_pairs"]["n_choose_2_of_2930"])),
        ("LASH CPU, 891 h over 2930 x 2930 pairs", ".37 s per alignment", str(ar["lash_cpu"]["s_per_alignment_2930x2930"])),
        ("Reduced training set, 2911 minus 2514 removed", "1397", str(ar["reduced_training_set"]["full_minus_removed"])),
    ]
    for r in rows:
        print("| " + " | ".join(r) + " |")
    print("\n## Check\n")
    if failures:
        print("FAILED: " + "; ".join(failures))
        sys.exit(1)
    print("Every result is as recorded.")


if __name__ == "__main__":
    main(*sys.argv[1:5])
