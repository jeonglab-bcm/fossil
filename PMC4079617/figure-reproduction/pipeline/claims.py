"""The statements of the text, computed from the paper's own tables (arithmetic) and from our run (observed);
and the design check of Additional file 1.

Usage: claims.py PUBLISHED_VALUES_JSON SIMULATION_JSON OUT_JSON

Each claim is a list of fields {name, expected (the paper's statement, as printed or 'yes'), arithmetic (the
same computed from the paper's Tables 1-3 and A1-A3), observed (from our main run), tolerance}. A yes/no field is
computed the same way from both; a number field carries a tolerance of 0.1 (two printed values differenced) plus
3 x sqrt(2) Monte Carlo SEs of the paired LB - RP difference.
"""
import json
import math
import sys

import numpy as np

import robustrr as rr

FORMS = ("linear", "nonlinear")
LEVELS = ("moderate", "strong")
RRS = ("1.5", "2.0")
PYS = ("10%", "25%", "40%")
CONT = ("2%", "5%")


def yn(b):
    return "yes" if b else "no"


class Source:
    """One set of values: the paper's printed tables or our run, addressed the same way."""

    def __init__(self, pub=None, sim=None):
        self.pub, self.sim = pub, sim

    def get(self, n, q, rr_, py, c, form, lev, m):
        if self.pub is not None:
            t = {("1500", "relbias"): "table1", ("1500", "se"): "table2", ("1500", "mse"): "table3",
                 ("500", "relbias"): "tableA1", ("500", "se"): "tableA2", ("500", "mse"): "tableA3"}[(n, q)]
            row = next(r for r in self.pub["tables"][t]["rows"] if r["rr"] == rr_ and r["py"] == py and r["contamination"] == c)
            return float(row["cells"][f"{form}|{lev}|{m}"])
        return self.sim["runs"]["main"][f"n{n}"][f"{rr_}|{py}|{form}|{lev}"][c][m][q]

    def printed(self, x, q):
        """Our value at the paper's printed precision, for statements about printed values."""
        if self.pub is not None:
            return x
        d = {"relbias": 1, "se": 2, "mse": 3}[q]
        return float(f"{x:.{d}f}")


def cells(forms=FORMS, rrs=RRS, pys=PYS, conts=CONT, levels=LEVELS):
    return [(rr_, py, c, f, l) for rr_ in rrs for py in pys for c in conts for f in forms for l in levels]


def claims_for(S):
    """Every claim's fields computed from one source. Returns {claim: {field: value}}."""
    g = S.get
    out = {}
    # Results, relative bias
    out["text.contaminated_negative"] = {
        "Table 1: every relative bias of the contaminated rows is negative (96 values)":
            yn(all(g("1500", "relbias", *k[:3], k[3], k[4], m) < 0 for k in cells() for m in ("LB", "RP")))}
    out["text.outcome_rate"] = {
        "Table 1: |bias| at outcome 10% exceeds |bias| at 25%, every contaminated cell and model (32 pairs)":
            yn(all(abs(g("1500", "relbias", rr_, "10%", c, f, l, m)) > abs(g("1500", "relbias", rr_, "25%", c, f, l, m))
                   for rr_ in RRS for c in CONT for f in FORMS for l in LEVELS for m in ("LB", "RP"))),
        "Table 1: |bias| at outcome 25% exceeds |bias| at 40%, every contaminated cell and model (32 pairs)":
            yn(all(abs(g("1500", "relbias", rr_, "25%", c, f, l, m)) > abs(g("1500", "relbias", rr_, "40%", c, f, l, m))
                   for rr_ in RRS for c in CONT for f in FORMS for l in LEVELS for m in ("LB", "RP")))}
    # linear confounder: the gap LB - RP in |bias|
    gaps = {k: abs(g("1500", "relbias", *k[:3], k[3], k[4], "LB")) - abs(g("1500", "relbias", *k[:3], k[3], k[4], "RP"))
            for k in cells(forms=("linear",))}
    top4 = [gaps[(rr_, "10%", "5%", "linear", l)] for rr_ in RRS for l in LEVELS]
    rest = [v for k, v in gaps.items() if not (k[1] == "10%" and k[2] == "5%")]
    out["text.linear_gap"] = {
        "Linear Z: the largest LB - RP gaps in |bias| are at 5% contamination and 10% outcome": yn(min(top4) > max(rest)),
        "Linear Z, 5% contamination, 10% outcome: smallest gap (points)": round(min(top4), 3),
        "Linear Z, 5% contamination, 10% outcome: largest gap (points)": round(max(top4), 3)}
    # non-linear confounder
    ngap = {k: abs(g("1500", "relbias", *k[:3], k[3], k[4], "LB")) - abs(g("1500", "relbias", *k[:3], k[3], k[4], "RP"))
            for k in cells(forms=("nonlinear",))}
    out["text.nonlinear"] = {
        "Non-linear Z: RP less biased than LB in every contaminated cell (24)": yn(all(v > 0 for v in ngap.values())),
        "Non-linear Z: RP less biased than LB in every 2% cell (12)": yn(all(v > 0 for k, v in ngap.items() if k[2] == "2%")),
        "Non-linear Z: the gap is larger at outcome 10% than at 40% (8 pairs)":
            yn(all(ngap[(rr_, "10%", c, "nonlinear", l)] > ngap[(rr_, "40%", c, "nonlinear", l)]
                   for rr_ in RRS for c in CONT for l in LEVELS))}
    # standard errors
    pairs0 = [(rr_, py, "0%", f, l) for rr_ in RRS for py in PYS for f in FORMS for l in LEVELS]
    se_eq = [S.printed(g("1500", "se", *k, "LB"), "se") == S.printed(g("1500", "se", *k, "RP"), "se") for k in pairs0]
    out["text.se_uncontaminated"] = {
        "Table 2, 0% rows: LB and RP SEs equal at the 2nd decimal in all 24 pairs": yn(all(se_eq))}
    hi = [(k, g("1500", "se", *k[:3], k[3], k[4], "LB") - g("1500", "se", *k[:3], k[3], k[4], "RP"))
          for k in cells()]
    out["text.se_contaminated"] = {
        "Table 2, contaminated rows at outcome 10%: LB SE above RP SE in some cells":
            yn(any(S.printed(g("1500", "se", *k[:3], k[3], k[4], "LB"), "se") > S.printed(g("1500", "se", *k[:3], k[3], k[4], "RP"), "se")
                   for k, _ in hi if k[1] == "10%")),
        "Table 2, contaminated rows at outcome 25% and 40%: LB and RP SEs within 0.01 in every cell":
            yn(all(abs(S.printed(g("1500", "se", *k[:3], k[3], k[4], "LB"), "se") - S.printed(g("1500", "se", *k[:3], k[3], k[4], "RP"), "se")) <= 0.01 + 1e-9
                   for k, _ in hi if k[1] != "10%"))}
    # MSE
    mgap = {k: g("1500", "mse", *k[:3], k[3], k[4], "LB") - g("1500", "mse", *k[:3], k[3], k[4], "RP") for k in cells()}
    out["text.mse"] = {
        "Table 3, linear Z: LB MSE exceeds RP MSE by more than 0.005 only at outcome 10% and 5% contamination":
            yn(all((v > 0.005) == (k[1] == "10%" and k[2] == "5%") for k, v in mgap.items() if k[3] == "linear")),
        "Table 3, non-linear Z: LB MSE at least RP MSE in every 2% cell (12), as printed":
            yn(all(S.printed(g("1500", "mse", *k[:3], k[3], k[4], "LB"), "mse") >= S.printed(g("1500", "mse", *k[:3], k[3], k[4], "RP"), "mse")
                   for k in cells(forms=("nonlinear",), conts=("2%",))))}
    # n = 500
    allc = [(rr_, py, c, f, l, m) for rr_ in RRS for py in PYS for c in ("0%",) + CONT for f in FORMS for l in LEVELS for m in ("LB", "RP")]
    out["text.n500"] = {
        "Table A2 SE above Table 2 SE in every cell (144)": yn(all(g("500", "se", *k) > g("1500", "se", *k) for k in allc)),
        "Table A1, non-linear Z: RP less biased than LB in every contaminated cell (24)":
            yn(all(abs(g("500", "relbias", *k[:3], k[3], k[4], "LB")) > abs(g("500", "relbias", *k[:3], k[3], k[4], "RP"))
                   for k in cells(forms=("nonlinear",))))}
    # Discussion: no outliers
    d0 = [abs(g(n, "relbias", *k, "LB") - g(n, "relbias", *k, "RP")) for n in ("1500", "500") for k in pairs0]
    out["text.no_outliers"] = {
        "0% rows of Tables 1 and A1: LB and RP relative biases within 0.5 points in all 48 pairs": yn(max(d0) <= 0.5 + 1e-9)}
    # main claim
    lin_ok = all(abs(v) <= 2.0 for k, v in gaps.items() if not (k[1] == "10%" and k[2] == "5%"))
    out["text.main_claim"] = {
        "Linear Z: LB and RP |bias| within 2 points in every contaminated cell except outcome 10% at 5%": yn(lin_ok),
        "Non-linear Z: RP less biased than LB in every contaminated cell, from 2% on (24)": yn(all(v > 0 for v in ngap.values()))}
    return out


EXPECTED = {
    "text.contaminated_negative": {"*": "yes"},
    "text.outcome_rate": {"*": "yes"},
    "text.linear_gap": {"Linear Z: the largest LB - RP gaps in |bias| are at 5% contamination and 10% outcome": "yes",
                        "Linear Z, 5% contamination, 10% outcome: smallest gap (points)": "3.5",
                        "Linear Z, 5% contamination, 10% outcome: largest gap (points)": "6.7"},
    "text.nonlinear": {"*": "yes"}, "text.se_uncontaminated": {"*": "yes"}, "text.se_contaminated": {"*": "yes"},
    "text.mse": {"*": "yes"}, "text.n500": {"*": "yes"}, "text.no_outliers": {"*": "yes"}, "text.main_claim": {"*": "yes"},
}
STATEMENT = {
    "text.contaminated_negative": "When the data were contaminated, the relative biases were all negative (Results).",
    "text.outcome_rate": "Scenarios with lower outcome rates seemed to be associated with more elevated absolute relative biases (Results).",
    "text.linear_gap": "With a linear Z the largest differences occurred at 5% contamination and 10% outcome, where the log-binomial models had 3.5%-6.7% higher biases (Results).",
    "text.nonlinear": "With a non-linear Z the robust Poisson model outperformed the log-binomial model when the data were contaminated, visibly even at 2%; a larger difference went with smaller outcomes (Results).",
    "text.se_uncontaminated": "Without contamination the SEs of the two models were identical at the 2nd decimal point (Results).",
    "text.se_contaminated": "With contamination the SEs remained comparable at outcome rates of 25% and 40%; at 10% the log-binomial SEs seemed slightly higher in some scenarios (Results).",
    "text.mse": "The MSEs follow the pattern of the biases: comparable with a linear Z except at outcome 10% and 5% contamination; with a non-linear Z the models diverge even at 2% (Results).",
    "text.n500": "With n = 500 the same pattern was observed and the SEs were larger (Results, Additional file 2).",
    "text.no_outliers": "Without outliers the study did not observe any difference in biases or variances between the two models, for n = 1500 and n = 500 (Discussion).",
    "text.main_claim": "Comparable models with a linear confounder; the robust Poisson model consistently outperforms the log-binomial model with a quadratic confounder, even at 2% contamination (Abstract, Discussion, Conclusions).",
}


def design_check():
    """Exposure and outcome rates of the 24 scenarios of Additional file 1, by quadrature over Z ~ Beta(6, 2)."""
    x, w = np.polynomial.legendre.leggauss(200)
    z = 0.5 * (x + 1)
    w = 0.5 * w
    dens = 42 * z**5 * (1 - z)
    fields = []
    for k in rr.SCENARIOS:
        s = rr.scenario(*k)
        px = 1 / (1 + np.exp(-(s["alpha0"] + s["alpha1"] * z)))
        py = (dens * (px * rr.simulation.outcome_probability(s, 1.0, z)
                      + (1 - px) * rr.simulation.outcome_probability(s, 0.0, z)) * w).sum()
        pmax = float(rr.simulation.outcome_probability(s, 1.0, 1.0))
        name = f"RR {k[0]:.1f}, {k[1]}%, {'non-linear' if k[2] == 'nonlinear' else 'linear'} {k[3]}"
        fields.append({"name": f"{name}: P(X = 1) (%)", "expected": "50", "observed": round(100 * float((dens * px * w).sum()), 3)})
        fields.append({"name": f"{name}: P(Y = 1) (%)", "expected": str(k[1]), "observed": round(100 * float(py), 3),
                       "largest_p_y": round(pmax, 4)})
    return fields


def main():
    pub_path, sim_path, out = sys.argv[1:4]
    pub = json.load(open(pub_path))
    sim = json.load(open(sim_path))
    paper, ours = claims_for(Source(pub=pub)), claims_for(Source(sim=sim))
    cells_ = sim["runs"]["main"]["n1500"]
    doc = {"_about": __doc__.strip().splitlines()[0]}
    for cid, fields in paper.items():
        fl = []
        for name, a in fields.items():
            exp = EXPECTED[cid].get(name, EXPECTED[cid].get("*"))
            f = {"name": name, "expected": exp, "arithmetic": a if isinstance(a, str) else f"{a:.1f}",
                 "observed": ours[cid][name]}
            if not isinstance(a, str):
                # a gap between two printed values: 0.1, plus 3 sqrt(2) Monte Carlo SEs of our paired difference
                mc = max(cells_[f"{rr_}|10%|linear|{l}"]["5%"]["diff_relbias_mcse"] for rr_ in RRS for l in LEVELS)
                f["tolerance"] = {"abs": round(0.1 + 3 * math.sqrt(2) * mc, 3)}
            fl.append(f)
        doc[cid] = {"statement": STATEMENT[cid], "fields": fl}
    # the gaps behind text.linear_gap, ours with their Monte Carlo SEs
    doc["text.linear_gap"]["gaps"] = [
        {"cell": f"RR {rr_}, 10%, 5%, linear {l}",
         "paper": round(abs(Source(pub=pub).get("1500", "relbias", rr_, "10%", "5%", "linear", l, "LB"))
                        - abs(Source(pub=pub).get("1500", "relbias", rr_, "10%", "5%", "linear", l, "RP")), 2),
         "ours": round(-cells_[f"{rr_}|10%|linear|{l}"]["5%"]["diff_relbias"], 2),
         "ours_mcse": cells_[f"{rr_}|10%|linear|{l}"]["5%"]["diff_relbias_mcse"]} for rr_ in RRS for l in LEVELS]
    # SE differences before rounding at 0% (ours only: the paper prints rounded values)
    d = [abs(cells_[k]["0%"]["LB"]["se"] - cells_[k]["0%"]["RP"]["se"]) for k in cells_]
    doc["text.se_uncontaminated"]["ours_largest_unrounded_difference"] = round(max(d), 5)
    doc["text.se_uncontaminated"]["fields"].append(
        {"name": "Table 2, 0% rows: LB and RP SEs differ by less than 0.005 before rounding (24 pairs)", "expected": "yes",
         "observed": yn(max(d) < 0.005)})
    # convergence (Discussion): scenarios = design x contaminated rate x sample size (12 x 2 x 2 = 48 per form)
    conv = {}
    for form in FORMS:
        ks = [(n, k, c) for n in ("n1500", "n500") for k, v in sim["runs"]["main"][n].items() if f"|{form}|" in k for c in CONT]
        allc = sum(sim["runs"]["main"][n][k][c]["lb_converged"] == sim["runs"]["main"][n][k][c]["reps"] for n, k, c in ks)
        need = sum(sim["runs"]["main"][n][k][c]["copy_used"] > 0 for n, k, c in ks)
        copies = [sim["runs"]["main"][n][k][c]["copy_used"] for n, k, c in ks]
        conv[form] = {"scenarios": len(ks), "all_converged": allc, "copy_needed_in_some_fit": need,
                      "copy_used_median": float(np.median(copies)), "copy_used_max": int(max(copies))}
    doc["text.convergence"] = {
        "statement": "COPY (C = 1,000,000) converged in all 1,000 simulations in all 48 scenarios with the linear confounder and in 30 of 48 with the non-linear one; in the other 18, convergence rates 0.983-0.999 (median 0.996) (Discussion).",
        "fields": [{"name": "Linear Z: scenarios with every log-binomial fit converged (of 48)", "expected": "48",
                    "observed": str(conv["linear"]["all_converged"])},
                   {"name": "Non-linear Z: scenarios with every log-binomial fit converged (of 48)", "expected": "30",
                    "observed": str(conv["nonlinear"]["all_converged"])}],
        "ours": conv}
    doc["design"] = {"statement": "alpha0 and beta0 of Additional file 1 give 50% exposure and 10, 25 or 40% outcome.",
                     "fields": design_check()}
    json.dump(doc, open(out, "w"), indent=1)
    open(out, "a").write("\n")
    for cid, c in doc.items():
        if cid.startswith("_"):
            continue
        bad = [f for f in c["fields"] if "arithmetic" in f and f["arithmetic"] != f["expected"]]
        print(cid, [(f["name"][:50], f["expected"], f.get("arithmetic"), f["observed"]) for f in c["fields"]][:4] if cid != "design" else len(c["fields"]),
              "ARITH-MISMATCH" if bad else "", file=sys.stderr)


if __name__ == "__main__":
    main()
