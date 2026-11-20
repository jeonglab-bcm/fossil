"""The paper's claims in the text, as fields: the printed value, ours, and the paper's own arithmetic.

Usage: claims.py PUBLISHED_VALUES SIMULATION_JSON COMPARISON_JSON OUT.json

Each field has 'expected' (the paper's words or number, as printed), 'observed' (computed from our run:
the only kind that sets a verdict) and, where the claim can be recomputed from the paper's own tables or
formula, 'arithmetic' (that recomputation; it says nothing about our run). '_table1_arithmetic' recomputes
Table 1's RRR and NNT columns from its own CER column with Fig. 1A's formula.
"""
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from compare import tol_power  # noqa: E402


def yn(b):
    return "yes" if b else "no"


def f(x):
    return float(x)


def main(pv_path, sim_path, cmp_path, out):
    pv = json.load(open(pv_path, encoding="utf-8"))
    sim = json.load(open(sim_path))
    P = sim["primary"]
    n_it = sim["settings"]["iterations"]

    def tol(pub, q, pct=False):
        """A number that restates a simulated power: the same Monte Carlo tolerance as the tables."""
        return {"abs": round(tol_power(pub, q, n_it, 100.0 if pct else 1.0), 6)}
    det = sim["deterministic"]
    t2p, t3p, t4p, t5p, f1p = pv["table2"], pv["table3"], pv["table4"], pv["table5"], pv["fig1b"]
    nr = det["fig1a"]["net_rrr_at"]
    claims = {}

    # Fig. 1A, Results: net harm below a pre-treatment risk of 3%; a steep gain from 2% to 5%, modest above.
    zero_formula = 0.003 * 5 / 0.5  # from the formula printed in Fig. 1A
    claims["text_fig1a"] = {"label": "Fig. 1A in the text: net harm below a 3% pre-treatment risk; a steep gain from 2% to 5%, modest above",
                            "fields": [
        {"name": "pre-treatment risk where net RRR is 0", "expected": "0.03", "observed": det["fig1a"]["zero_at"], "arithmetic": zero_formula},
        {"name": "gain in net RRR from 2% to 5% larger than from 5% to 9%", "expected": "yes",
         "observed": yn(nr["0.05"] - nr["0.02"] > nr["0.09"] - nr["0.05"]),
         "arithmetic": yn((0.5 - 0.015 / 0.05) - (0.5 - 0.015 / 0.02) > (0.5 - 0.015 / 0.09) - (0.5 - 0.015 / 0.05))},
    ]}

    # Methods: N = 8,800 gives 80% power for an RRR of 25%. The CER of that calculation is not given;
    # ours is at the Table 1 population's average CER.
    dp = sim["design_power"]
    claims["text_design_power"] = {"label": "Methods: N = 8,800 gives 80% power to detect an RRR of 25%",
                                   "fields": [{"name": "power for an RRR of 25% at the Table 1 population's average CER",
                                               "expected": "0.80", "observed": round(dp["table1_population"]["power"], 4),
                                               "tolerance": tol("0.80", dp["table1_population"]["power"])}]}

    # Fig. 1B: the 4-RF score beats one RF at every average CER; power falls as the average CER rises.
    rows = ["1.5%", "3%", "6%", "9%"]
    ours_one = [P[f"fig1b/{r}"]["one_rf"]["power"] for r in rows]
    ours_four = [P[f"fig1b/{r}"]["four_rf"]["power"] for r in rows]
    pub_one = [f(f1p[r]["one_rf"][0]) for r in rows]
    pub_four = [f(f1p[r]["four_rf"][0]) for r in rows]
    claims["text_fig1b"] = {"label": "Fig. 1B in the text: the 4-RF score has more power than one RF, and power falls as the population's CER rises",
                            "fields": [
        {"name": "the 4-RF score has more power than one RF at every average CER", "expected": "yes",
         "observed": yn(all(a > b for a, b in zip(ours_four, ours_one))), "arithmetic": yn(all(a > b for a, b in zip(pub_four, pub_one)))},
        {"name": "one RF: power falls as the average CER rises", "expected": "yes",
         "observed": yn(all(a > b for a, b in zip(ours_one, ours_one[1:]))), "arithmetic": yn(all(a > b for a, b in zip(pub_one, pub_one[1:])))},
        {"name": "4-RF score: power falls as the average CER rises", "expected": "yes",
         "observed": yn(all(a > b for a, b in zip(ours_four, ours_four[1:]))), "arithmetic": yn(all(a > b for a, b in zip(pub_four, pub_four[1:])))},
    ]}

    # Table 2 in the text
    t2 = lambda eff, prev: P[f"table2/{eff}/{prev}"]["conventional"]["power"]
    claims["text_table2"] = {"label": "Table 2 in the text: OR 2, prevalence 50% against 25%: .22 against .21; OR 3, prevalence 50%: 44%",
                             "fields": [
        {"name": "OR 2, prevalence 50%", "expected": ".22", "observed": round(t2("2.0", "50%"), 4), "tolerance": tol(".22", t2("2.0", "50%")), "arithmetic": f(t2p["2.0"]["50%"])},
        {"name": "OR 2, prevalence 25%", "expected": ".21", "observed": round(t2("2.0", "25%"), 4), "tolerance": tol(".21", t2("2.0", "25%")), "arithmetic": f(t2p["2.0"]["25%"])},
        {"name": "OR 3, prevalence 50% (%)", "expected": "44", "observed": round(100 * t2("3.0", "50%"), 2), "tolerance": tol("44", t2("3.0", "50%"), True), "arithmetic": 100 * f(t2p["3.0"]["50%"])},
        {"name": "prevalence 50% gives only slightly more power than 25% (OR 2)", "expected": "yes",
         "observed": yn(0 < t2("2.0", "50%") - t2("2.0", "25%") < 0.05),
         "arithmetic": yn(0 < f(t2p["2.0"]["50%"]) - f(t2p["2.0"]["25%"]) < 0.05)},
    ]}

    # Table 3 in the text
    t3 = lambda eff, k: P[f"table3/{eff}/{k}"]["index"]
    better = all(t3(e, k)["power"] > t3(e, "1")["power"] for e in ("1.5", "2.0", "3.0") for k in ("3", "6"))
    better_pub = all(f(t3p[e][k]["power"]) > f(t3p[e]["1"]["power"]) for e in ("1.5", "2.0", "3.0") for k in ("3", "6"))
    claims["text_table3"] = {"label": "Table 3 in the text: 3 RFs of 1.5 give an AUROC of 0.55; combining RFs always beats one RF",
                             "fields": [
        {"name": "AUROC of a score of 3 RFs of 1.5", "expected": "0.55", "observed": round(t3("1.5", "3")["auroc"], 4), "arithmetic": f(t3p["1.5"]["3"]["auroc"])},
        {"name": "every score of 3 or 6 RFs has more power than one RF of the same OR", "expected": "yes", "observed": yn(better), "arithmetic": yn(better_pub)},
    ]}

    # Table 4 in the text
    t4 = P["table4"]
    claims["text_table4"] = {"label": "Table 4 in the text: perfect to reverse weighting takes power from 82% to 69%; one RF of 2.5 alone has 37%",
                             "fields": [
        {"name": "perfect weighting (%)", "expected": "82", "observed": round(100 * t4["perfect"]["power"], 2), "tolerance": tol("82", t4["perfect"]["power"], True), "arithmetic": 100 * f(t4p["perfect"]["power"])},
        {"name": "reverse weighting (%)", "expected": "69", "observed": round(100 * t4["reverse"]["power"], 2), "tolerance": tol("69", t4["reverse"]["power"], True), "arithmetic": 100 * f(t4p["reverse"]["power"])},
        {"name": "conventional analysis of one RF with RR 2.5 (%)", "expected": "37", "observed": round(100 * t4["conventional_rf5"]["power"], 2),
         "tolerance": tol("37", t4["conventional_rf5"]["power"], True)},
    ]}

    # Table 5 in the text: power rises with the rate of complications, for both analyses
    t5c = [P[f"table5/{h}"]["conventional"]["power"] for h in (1, 2, 3, 4)]
    t5r = [P[f"table5/{h}"]["risk_stratified"]["power"] for h in (1, 2, 3, 4)]
    p5c = [f(t5p[str(h)]["conventional"]) for h in (1, 2, 3, 4)]
    p5r = [f(t5p[str(h)]["risk_stratified"]) for h in (1, 2, 3, 4)]
    claims["text_table5"] = {"label": "Table 5 in the text: power rises with the rate of treatment complications",
                             "fields": [
        {"name": "conventional power rises with the complication rate", "expected": "yes",
         "observed": yn(all(a < b for a, b in zip(t5c, t5c[1:]))), "arithmetic": yn(all(a < b for a, b in zip(p5c, p5c[1:])))},
        {"name": "risk-stratified power rises with the complication rate", "expected": "yes",
         "observed": yn(all(a < b for a, b in zip(t5r, t5r[1:]))), "arithmetic": yn(all(a < b for a, b in zip(p5r, p5r[1:])))},
    ]}

    # Abstract: conventional analysis had at best moderate power (30% to 45%), even for a RF of OR 3
    best = [t2("3.0", "25%"), t2("3.0", "50%")]
    best_pub = [f(t2p["3.0"]["25%"]), f(t2p["3.0"]["50%"])]
    claims["text_abstract"] = {"label": "Abstract: conventional subgroup analysis has at best 30% to 45% power, even for a RF of OR 3",
                               "fields": [
        {"name": "one RF of OR 3 at prevalence 25% and 50%: power between 30% and 45%", "expected": "yes",
         "observed": yn(all(0.295 <= b <= 0.455 for b in best)), "arithmetic": yn(all(0.295 <= b <= 0.455 for b in best_pub))},
    ]}

    # Main claim: the risk-stratified analysis has more power than the conventional one wherever both are run
    pairs = [(P["table1"]["continuous"]["power"], P["table1"]["conventional"]["power"])]
    pairs += list(zip(t5r, t5c)) + list(zip(ours_four, ours_one))
    pairs_pub = [(f(pv["table1"]["power"]["continuous"]), f(pv["table1"]["power"]["conventional"]))]
    pairs_pub += list(zip(p5r, p5c)) + list(zip(pub_four, pub_one))
    gain = min(a - b for a, b in pairs)
    gain_pub = min(a - b for a, b in pairs_pub)
    claims["text_main_claim"] = {"label": "Main claim: a multivariable risk-stratified analysis has much more power than conventional subgroup analysis",
                                 "fields": [
        {"name": "risk-stratified power above conventional in every paired setting (Tables 1 and 5, Fig. 1B)", "expected": "yes",
         "observed": yn(all(a > b for a, b in pairs)), "arithmetic": yn(all(a > b for a, b in pairs_pub))},
        {"name": "the smallest gain is at least 20 points", "expected": "yes", "observed": yn(gain >= 0.2), "arithmetic": yn(gain_pub >= 0.2)},
    ]}

    # Table 1's RRR and NNT, recomputed from its own printed CER column with Fig. 1A's formula
    rows1 = []
    for g, r in pv["table1"]["groups"].items():
        c = f(r["cer"]) / 100
        e = 0.5 * c + 0.015
        rows1.append({"group": g, "rrr_printed": r["rrr"], "rrr_from_cer": (c - e) / c,
                      "nnt_printed": r["nnt"], "nnt_from_cer": (1 / (c - e)) if c != e else None})  # None: infinite
    claims["_table1_arithmetic"] = rows1
    json.dump(claims, open(out, "w"), indent=1)


if __name__ == "__main__":
    main(*sys.argv[1:5])
