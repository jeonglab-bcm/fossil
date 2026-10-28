"""Write the reproduction report and fail if a reproduced figure no longer matches.

Usage: python check_reproduction.py <comparison.json> <tables.json> > report.md
"""

import json
import sys

# Panels that come back the same: both pixel shares must stay at or above these.
REQUIRED = {
    ("fig2", ""): 0.99,
    ("fig3", "a"): 0.99,
    ("fig3", "b"): 0.99,
    ("fig3", "c"): 0.99,
    ("fig3", "d"): 0.99,
    ("fig4", "c"): 0.98,
    ("fig6", "a"): 0.98,
    ("fig6", "b"): 0.98,
    ("fig6", "d"): 0.97,
    ("fig7", "LIMPIC"): 0.99,
    ("fig8", ""): 0.98,
}


def pct(v):
    return f"{100 * v:.2f}%"


def main(comparison, tables):
    c = json.load(open(comparison))
    t = json.load(open(tables))
    failures = []
    print("# PMC1847688 reproduction report\n")
    print("Share of published trace pixels within 2 px of ours / of ours within 2 px of the published.\n")
    print("| Figure | Panel | Published near ours | Ours near published | Markers |")
    print("| --- | --- | --- | --- | --- |")
    for fig in ["fig2", "fig3", "fig4", "fig5", "fig6", "fig7", "fig8"]:
        for r in c[fig]:
            markers = ""
            if "markers_ours" in r:
                markers = f"{r['published_marker_at_each_of_ours']} of {r['markers_ours']} at our peaks, {r['published_markers_without_ours']} extra"
                if "class_agreement" in r:
                    markers += f"; colour agrees for {r['class_agreement']}"
            print(f"| {fig} | {r['panel']} | {pct(r['published_within_2px'])} | {pct(r['ours_within_2px'])} | {markers} |")
            need = REQUIRED.get((fig, r["panel"]))
            if need and min(r["published_within_2px"], r["ours_within_2px"]) < need:
                failures.append(f"{fig} {r['panel']} below {pct(need)}")
            if fig in ("fig7", "fig8") and (
                r["published_marker_at_each_of_ours"] != r["markers_ours"] or r["published_markers_without_ours"]
            ):
                failures.append(f"{fig} peak markers differ")
    a, b = c["fig9"]["a"], c["fig9"]["b"]
    print(f"| fig9 | a (Additional File 4) | {pct(a['published_within_2px'])} | {pct(a['ours_within_2px'])} | |")
    print(f"\nFig. 9b, PDR histogram of Additional File 4: {b['S4_counts']}; published bars read as {b['published_bar_heights']}.\n")

    p = t["paper"]
    print("## LIMPIC rows of the tables\n")
    print("| Item | Paper | Ours |")
    print("| --- | --- | --- |")
    t1 = t["table1_limpic"]
    for key in ["average_intensity", "standard_deviation", "coefficient_of_variation"]:
        print(f"| Table 1 {key.replace('_', ' ')} (2.5 to 50 fmol) | {p['table1_limpic'][key]} | {t1[key]} |")
    print(f"| Table 1 replicates with a cytochrome C peak | 5 each | {t1['n_replicates_with_peak']} |")
    print(f"| Table 2 detected classes (PDR > 0.5) | {p['table2_limpic_detected_classes']} | {t['table2_limpic_detected_classes']} |")
    for k in ["in_vitro", "plasma"]:
        q, o = p["table3_limpic"][k], t["table3_limpic"][k]
        print(f"| Table 3 {k.replace('_', '-')}: peaks per spectrum, classes, hit-rate | {q['average_peaks']}, {q['classes']}, {q['hit_rate']} | {o['average_peaks']}, {o['classes']}, {o['hit_rate']} |")
    s4, ours, txt = t["plasma_additional_file_4"], t["plasma_ours"], p["plasma_text"]
    print(f"| Plasma peaks, classes, selected (text) | {txt['peaks']}, {txt['classes']}, {txt['selected_pdr_0.5']} | {ours['peaks']}, {ours['classes']}, {ours['selected_pdr_gt_0.5']} (> 0.5) or {ours['selected_pdr_ge_0.5']} (>= 0.5) |")
    print(f"| Plasma, Additional File 4 | | {s4['peaks']}, {s4['classes']}, {s4['selected_pdr_gt_0.5']} (> 0.5) or {s4['selected_pdr_ge_0.5']} (>= 0.5) |")

    print("\n## Check\n")
    if failures:
        print("FAILED: " + "; ".join(failures))
        sys.exit(1)
    print("Every reproduced panel matches at its required level.")


if __name__ == "__main__":
    main(*sys.argv[1:3])
