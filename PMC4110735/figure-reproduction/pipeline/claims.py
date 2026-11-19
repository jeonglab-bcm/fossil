"""Claims of the text: first recomputed from the paper's own Table 2 (arithmetic check), then from our run.

Usage: claims.py PAPER_VALUES.json DREAM.json PROFILES.json ENRICH.json TIMING.json OUT.json
"""
import json, sys
import numpy as np

M = ["gecon", "aracne", "clr", "mrnet"]
KEYS = {"aupr": "aupr", "auroc": "auroc", "f": "f_max"}


def fmt(x, ref):
    """x at the printed precision of the string ref."""
    dec = len(ref.split(".")[1]) if "." in ref else 0
    return f"{x:.{dec}f}"


def main():
    pv, dream, prof, enr, tim = [json.load(open(p)) for p in sys.argv[1:6]]
    out = sys.argv[6]
    t2 = pv["table2"]
    ds = [f"D{i}" for i in range(1, 14)]
    arith = {"average": [], "improvement_from_printed_averages": [], "improvement_from_rows": [], "gecon_best": {}, "aupr_times": None}
    for key in ("aupr", "auroc", "f"):
        means = {m: float(np.mean([float(t2[key][d][m]) for d in ds])) for m in M}
        for m in M:
            exp = t2["average"][key][m]
            arith["average"].append({"name": f"{key} {m}", "expected": exp, "observed": fmt(means[m], exp)})
        for m in M[1:]:
            exp = t2["improvement_percent"][key][m]
            pa = {mm: float(t2["average"][key][mm]) for mm in M}
            arith["improvement_from_printed_averages"].append(
                {"name": f"{key} over {m}", "expected": exp, "observed": fmt(100 * (pa["gecon"] - pa[m]) / pa[m], exp)})
            arith["improvement_from_rows"].append(
                {"name": f"{key} over {m}", "expected": exp, "observed": fmt(100 * (means["gecon"] - means[m]) / means[m], exp)})
        arith["gecon_best"][key] = [d for d in ds if float(t2[key][d]["gecon"]) <= max(float(t2[key][d][m]) for m in M[1:])]
    arith["aupr_times"] = {m: round(float(t2["average"]["aupr"]["gecon"]) / float(t2["average"]["aupr"][m]), 2) for m in M[1:]}

    # ours
    D = dream["datasets"]
    ours = {"gecon_best": {}, "means": {}, "d6": {}}
    for key, k in KEYS.items():
        ours["gecon_best"][key] = [d for d in ds if D[d]["gecon"][k] > max(D[d][m][k] for m in M[1:])]
        ours["means"][key] = {m: round(float(np.mean([D[d][m][k] for d in ds])), 4) for m in M}
        ours["d6"][key] = round(D["D6"]["gecon"][k], 4)
    ours["improvement"] = {key: {m: round(100 * (ours["means"][key]["gecon"] - ours["means"][key][m]) / ours["means"][key][m], 2)
                                 for m in M[1:]} for key in KEYS}
    # Figs 2 and 3: the regulation GeCON assigns (theta 0.5)
    s = prof["supports"]
    ours["fig2_negative"] = s["fig2 Mrps26-Pfn2"]["neg"] > 0.5 and s["fig2 Mrps26-Pfn2"]["pos"] <= 0.5
    ours["fig3_002_003_positive"] = s["fig3 YBL002W-YBL003C"]["pos"] > 0.5
    ours["fig3_006_inverted"] = s["fig3 YBL002W-YBL006W"]["neg"] > 0.5 and s["fig3 YBL003C-YBL006W"]["neg"] > 0.5
    # modules enriched
    ky = enr["datasets"]["Yeast KY"]["modules"]
    ours["modules_enriched"] = {d: sum(bool(m["significant"]) for m in v["modules"]) for d, v in enr["datasets"].items()}
    ours["modules_total"] = {d: len(v["modules"]) for d, v in enr["datasets"].items()}
    # Fig. 5
    rows = tim["rows"]
    ours["faster"] = {str(r["genes"]): r["gecon_s"] < r["aracne_total_s"] for r in rows}
    ours["ratio_3000"] = round(rows[-1]["aracne_total_s"] / rows[-1]["gecon_s"], 2)
    json.dump({"arithmetic": arith, "ours": ours}, open(out, "w"), indent=1)
    print(json.dumps(arith["gecon_best"]), arith["aupr_times"])
    print([f for f in arith["average"] if f["expected"] != f["observed"]])
    print([f for f in arith["improvement_from_printed_averages"] if f["expected"] != f["observed"]])
    print([f for f in arith["improvement_from_rows"] if f["expected"] != f["observed"]])
    print(ours["gecon_best"], ours["improvement"])


if __name__ == "__main__":
    main()
