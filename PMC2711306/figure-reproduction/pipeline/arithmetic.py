"""Claims in the text recomputed from the paper's own numbers (Text S1 and the Results).

This checks that we compute each statistic the way the paper did; it says nothing about our run.
Usage: arithmetic.py OUT.json
"""
import json
import sys

from scipy.stats import hypergeom


def p(x, M, K, N):
    return float(hypergeom.sf(x - 1, M, K, N))


def main(out):
    checks = [
        # (claim, printed, recomputed, rule)
        ("pairs among 7,513 HumanBG proteins (Text S1 M)", "28218828", str(7513 * 7512 // 2), "equal"),
        ("pairs among 6,278 GO BP/CC-annotated proteins (M)", "19703503", str(6278 * 6277 // 2), "equal"),
        ("pairs among 5,864 GO BP-annotated proteins (M)", "17190316", str(5864 * 5863 // 2), "equal"),
        ("HPRD p-value, Text S1 (12 of 251, K = 34,119)", "7.5e-8", f"{p(12, 28218828, 34119, 251):.1e}", "printed"),
        ("HPRD p-value, main text", "7e-8", f"{p(12, 28218828, 34119, 251):.0e}", "printed"),
        ("GO BP or CC p-value (105 of 159)", "7.26e-8", f"{p(105, 19703503, 7400424, 159):.2e}", "printed"),
        ("GO BP p-value (55 of 129)", "1.4e-8", f"{p(55, 17190316, 1354495, 129):.1e}", "printed"),
        ("annotated pairs, 251 - 92", "159", str(251 - 92), "equal"),
        ("share of GO-annotated predictions sharing a term (%)", "66", f"{100 * 105 / 159:.0f}", "equal"),
        ("high-confidence pairs, 1,434 edges + 251 new", "1685", str(1434 + 251), "equal"),
        ("candidate false positives, share of edges (%)", "12", f"{100 * 2838 / 23372:.0f}", "equal"),
        ("KEGG: predictions with both proteins in a pathway (% of 251)", "10", f"{100 * 26 / 251:.0f}", "equal"),
        ("KEGG: same pathway (% of 26)", "46", f"{100 * 12 / 26:.0f}", "equal"),
        ("KEGG: same pathway (% of 251), 'about 5%'", "5", f"{100 * 12 / 251:.0f}", "equal"),
        ("validated in HPRD or BioGRID 2.0.50: 12 + 5 - 4", "13", str(12 + 5 - 4), "equal"),
        ("recall 0.35 of 154,000 human interactions", "53900", str(round(0.35 * 154000)), "equal"),
        ("Collins: 12,122 - 7,504 kept, + 4,456 new", "9074", str(12122 - 7504 + 4456), "equal"),
    ]
    rows = []
    for claim, printed, ours, rule in checks:
        if rule == "printed":
            ok = float(printed) == float(ours)
        else:
            ok = printed == ours
        rows.append({"claim": claim, "printed": printed, "recomputed": ours, "agrees": ok})
    res = {"checks": rows, "agree": sum(r["agrees"] for r in rows), "total": len(rows)}
    json.dump(res, open(out, "w"), indent=1)
    for r in rows:
        print(("ok  " if r["agrees"] else "DIFF"), r["claim"], r["printed"], r["recomputed"])


if __name__ == "__main__":
    main(sys.argv[1])
