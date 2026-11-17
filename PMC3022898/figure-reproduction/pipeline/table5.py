"""Table 5, the knee osteoarthritis case study, with the package esrisk.

Usage: table5.py PUBLISHED.json OUT.json

1. Point estimates from the printed inputs: overall risk P1(D) by age (0.0040, 0.0087, 0.0147), RR 1.91
   and P(obese) 0.371 (eqs 2 and 9).
2. The inputs are printed rounded. For each age, the interval of P1(D) that rounds to the printed value
   and gives both printed estimates is found by a fine scan; the hypothesis "rounded inputs" holds if it
   is not empty for every age.
3. The CIs need n1 (Oliveria et al. 1995 person-years by age) and Var(ln RR2) (Niu et al. 2009), which
   the paper does not print. With P1(D) at the middle of its interval from step 2: n1 is solved from the
   width of the binomial CI of ESR_R (eq. 12), and Var(ln RR2) from the log CI of ESR_S (eqs 5-6), one
   per age. Their mean over the three ages is then used to predict the log CI of ESR_R (eq. 10), which
   was not used in the fit, both as eq. 10 is printed and without its first term (the Table S6
   hypothesis).
"""
import json
import math
import sys

import numpy as np

import esrisk as E

RR, PE = 1.91, 0.371
Z = 1.96


def rnd(x, d=4):
    return f"{x:.{d}f}"


def interval_of_p1(printed_p, printed_s, printed_r):
    """P1(D) values that round to printed_p and give the printed ESR_S and ESR_R."""
    lo, hi = float(printed_p) - 5e-5, float(printed_p) + 5e-5
    grid = np.linspace(lo, hi, 20001)[:-1]
    ok = [(abs(E.esr_simple(p, RR) - float(printed_s)) <= 5e-5 + 1e-12) and
          (abs(E.esr_revised(p, RR, PE) - float(printed_r)) <= 5e-5 + 1e-12) for p in grid]
    sel = grid[np.array(ok)]
    return (float(sel.min()), float(sel.max())) if sel.size else None


def ci(s):
    a, b = s.split("-")
    return float(a), float(b)


def main():
    pub_p, out_p = sys.argv[1:3]
    T5 = json.load(open(pub_p))["table5"]
    res = {"inputs": {"rr2": RR, "p2_e": PE, "z": Z}, "ages": {}}
    for age, row in T5.items():
        p = float(row["overall_risk"])
        s, r = float(E.esr_simple(p, RR)), float(E.esr_revised(p, RR, PE))
        iv = interval_of_p1(row["overall_risk"], row["esr_s"], row["esr_r"])
        res["ages"][age] = {"printed": row, "from_printed_inputs": {"esr_s": rnd(s), "esr_r": rnd(r), "esr_s_exact": s, "esr_r_exact": r},
                            "p1_interval_consistent": iv}
    # n1 and Var(ln RR2) from the binomial CI of ESR_R and the log CI of ESR_S.
    fits = {}
    for age, a in res["ages"].items():
        row = a["printed"]
        iv = a["p1_interval_consistent"]
        p = (iv[0] + iv[1]) / 2 if iv else float(row["overall_risk"])
        r = float(E.esr_revised(p, RR, PE))
        bl, bh = ci(row["esr_r_binomial_ci"])
        n1 = r * (1 - r) * Z * Z / (((bh - bl) / 2) ** 2 * PE)
        sl, sh = ci(row["esr_s_log_ci"])
        v_s = (math.log(sh / sl) / (2 * Z)) ** 2
        v_rr = v_s - float(E.var_ln_proportion(p, n1))
        fits[age] = {"p1_d": p, "n1": n1, "var_ln_rr2": v_rr}
    v_rr = float(np.mean([f["var_ln_rr2"] for f in fits.values()]))
    res["fit"] = {"per_age": fits, "var_ln_rr2_mean": v_rr,
                  "rr2_ci_implied": [RR * math.exp(-Z * math.sqrt(v_rr)), RR * math.exp(Z * math.sqrt(v_rr))]}
    for age, f in fits.items():
        p, n1 = f["p1_d"], f["n1"]
        r = float(E.esr_revised(p, RR, PE))
        pu = float(E.p_unexposed(p, RR, PE))
        out = {}
        for how, first in (("eq10", float(E.var_ln_proportion(pu, n1))), ("no_first_term", 0.0)):
            lo, hi = E.log_ci(r, first + v_rr, Z)
            out[how] = {"lower": rnd(float(lo)), "upper": rnd(float(hi)), "lower_exact": float(lo), "upper_exact": float(hi)}
        s = float(E.esr_simple(p, RR))
        sl, sh = E.log_ci(s, float(E.var_ln_proportion(p, n1)) + v_rr, Z)
        bl, bh = E.binomial_ci(r, n1, PE, Z)
        out["refit"] = {"esr_s_log": [rnd(float(sl)), rnd(float(sh))], "esr_r_binomial": [rnd(float(bl)), rnd(float(bh))]}
        res["ages"][age]["esr_r_log_ci_predicted"] = out
    # How far rounding alone moves the predicted log CI of ESR_R: P1(D) across its consistent interval,
    # n1 and Var(ln RR2) solved again at each value (the CIs they come from are printed to 4 decimals).
    for age, a in res["ages"].items():
        iv = a["p1_interval_consistent"]
        row = a["printed"]
        lows, highs = [], []
        for p in np.linspace(iv[0], iv[1], 41):
            r = float(E.esr_revised(p, RR, PE))
            for db in (-5e-5, 0.0, 5e-5):
                bl, bh = ci(row["esr_r_binomial_ci"])
                half = (bh - bl) / 2 + db
                n1 = r * (1 - r) * Z * Z / (half ** 2 * PE)
                sl, sh = ci(row["esr_s_log_ci"])
                for ds in (-5e-5, 0.0, 5e-5):
                    v_i = (math.log((sh + ds) / (sl - ds)) / (2 * Z)) ** 2 - float(E.var_ln_proportion(p, n1))
                    lo, hi = E.log_ci(r, float(E.var_ln_proportion(E.p_unexposed(p, RR, PE), n1)) + v_i, Z)
                    lows.append(float(lo))
                    highs.append(float(hi))
        a["esr_r_log_ci_rounding_range"] = {"lower": [rnd(min(lows)), rnd(max(lows))], "upper": [rnd(min(highs)), rnd(max(highs))]}
    # Discussion: "the largest over-estimation occurring in those ages 70-79 by 0.71%"
    diffs = {age: a["from_printed_inputs"]["esr_s_exact"] - a["from_printed_inputs"]["esr_r_exact"] for age, a in res["ages"].items()}
    res["largest_overestimation"] = {"age": max(diffs, key=diffs.get), "percent": f"{100 * max(diffs.values()):.2f}"}
    # Fields for results.json: point estimates at printed precision; the predicted log CI of ESR_R.
    res["point"] = {"fields": [
        {"name": f"{age}, ESR_{e}", "expected": a["printed"][f"esr_{e.lower()}"], "observed": a["from_printed_inputs"][f"esr_{e.lower()}"],
         "tolerance": {"printed": True}} for age, a in res["ages"].items() for e in ("S", "R")]}
    res["ci"] = {"fields": [
        {"name": f"{age}, {side}", "expected": a["printed"]["esr_r_log_ci"].split("-")[i],
         "observed": a["esr_r_log_ci_predicted"]["eq10"][side], "tolerance": {"printed": True},
         "without_eq10_first_term": a["esr_r_log_ci_predicted"]["no_first_term"][side]}
        for age, a in res["ages"].items() for i, side in enumerate(("lower", "upper"))]}
    json.dump(res, open(out_p, "w"), indent=1)
    for age, a in res["ages"].items():
        pr = a["esr_r_log_ci_predicted"]
        print(f"{age}: ESR_S {a['from_printed_inputs']['esr_s']} ({a['printed']['esr_s']}), ESR_R {a['from_printed_inputs']['esr_r']} "
              f"({a['printed']['esr_r']}); P1(D) interval {a['p1_interval_consistent']}; n1 {fits[age]['n1']:.0f}; "
              f"ESR_R log CI eq. 10 {pr['eq10']['lower']}-{pr['eq10']['upper']}, no first term "
              f"{pr['no_first_term']['lower']}-{pr['no_first_term']['upper']} (paper {a['printed']['esr_r_log_ci']})", file=sys.stderr)
    for age, a in res["ages"].items():
        print(f"{age}: with rounding of the printed inputs and CIs, eq. 10 gives lower {a['esr_r_log_ci_rounding_range']['lower']}, "
              f"upper {a['esr_r_log_ci_rounding_range']['upper']}", file=sys.stderr)
    print(f"Var(ln RR2) {v_rr:.4f}, implied RR CI {res['fit']['rr2_ci_implied']}", file=sys.stderr)


if __name__ == "__main__":
    main()
