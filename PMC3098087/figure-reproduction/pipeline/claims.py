#!/usr/bin/env python3
"""The paper's claims in the text, as fields: recomputed from the paper's own figures and tables
first (the arithmetic check), then from our run.

  claims.py published_values.json summary.csv data_counts.json claims.json

Each field has the paper's printed value or statement ('expected'), the same quantity computed from
the paper's own published values ('arithmetic', where the paper prints what it needs) and from our
run ('observed'). Comparisons are 'yes'/'no'. 'About x' is read as x within 0.05 (our reading,
recorded as an assumption); other numbers carry the Monte Carlo tolerance of compare.py.
"""

import csv
import json
import math
import sys
from statistics import NormalDist

NINE = ["1-NN", "3-NN", "5-NN", "DLDA", "DQDA", "RF", "SVM", "PAM", "PLR"]
K19 = [round(0.05 * i, 2) for i in range(1, 20)]
ABOUT = 0.05


def yn(b):
    return None if b is None else ("yes" if b else "no")


class Ours:
    def __init__(self, path):
        self.s = {}
        with open(path) as f:
            for r in csv.DictReader(f):
                self.s[(r["setting"], r["test"], r["method"], r["metric"])] = r

    def get(self, setting, test, method, metric, what="mean_avail"):
        r = self.s.get((setting, test, method, metric))
        if r is None or r[what] in ("NA", ""):
            return None
        return float(r[what])

    def se(self, setting, test, method, metric):
        r = self.s.get((setting, test, method, metric))
        return float(r["sd"]) / math.sqrt(int(r["n"])) if r and r["sd"] not in ("NA", "") else None

    def nsel(self, setting):
        for k, r in self.s.items():
            if k[0] == setting and r.get("nsel_all") not in (None, "NA", ""):
                return float(r["nsel_all"])
        return None


class Paper:
    def __init__(self, path):
        d = json.load(open(path))
        self.figs = d["figures"]
        self.tabs = d["tables"]

    def point(self, fig, x, **kw):
        for r in self.figs:
            if r["figure"] == fig and all(r.get(k) == v for k, v in kw.items()):
                for px, py in r["points"]:
                    if abs(px - x) < 1e-9:
                        return py
        return None

    def cell(self, table, **kw):
        for c in self.tabs:
            if c["table"] == table and all(c.get(k) == v for k, v in kw.items()):
                try:
                    return float(c["value"])
                except ValueError:
                    return None
        return None


def num_field(name, expected, arithmetic, observed, se=None, about=False, z=3.0, digits=None):
    exp = float(expected)
    dec = len(expected.split(".")[1]) if "." in expected else 0
    tol = ABOUT if about else 0.5 * 10 ** -dec + (z * math.sqrt(2) * se if se else 0)
    f = {"name": name, "expected": expected, "tolerance": {"abs": round(tol, 6)},
         "arithmetic": None if arithmetic is None else round(arithmetic, 4),
         "observed": None if observed is None else round(observed, 4)}
    return f


def claim(statement, source, fields, note=""):
    return {"statement": statement, "source": source, "fields": fields, "note": note}


def main():
    P, O = Paper(sys.argv[1]), Ours(sys.argv[2])
    counts = json.load(open(sys.argv[3]))
    C = {}
    k = lambda x: f"{x:.2f}"  # noqa: E731

    # --- Null case ---
    pa_ok_paper = all(abs(P.cell("af1", classifier=c, k1train=kk, ntest=n, metric="PA") - 0.5) < 0.006
                      for c in NINE for kk in (0.1, 0.2, 0.3, 0.4, 0.5) for n in (20, 500))
    pa_ok_ours = all(abs(O.get(f"null_p40_k{k(kk)}", t, c, "PA") - 0.5) <= 0.01
                     for c in NINE for kk in K19 for t in ("bal20", "bal500") if O.get(f"null_p40_k{k(kk)}", t, c, "PA") is not None)
    auc_paper = all(abs(P.cell("af1", classifier=c, k1train=kk, ntest=n, metric="AUC") - 0.5) <= 0.015
                    for c in NINE for kk in (0.1, 0.2, 0.3, 0.4, 0.5) for n in (20, 500))
    auc_ours = all(abs(O.get(f"null_p40_k{k(kk)}", "bal500", c, "AUC") - 0.5) <= 0.015
                   for c in NINE for kk in K19 if O.get(f"null_p40_k{k(kk)}", "bal500", c, "AUC") is not None)
    C["text.null_balanced"] = claim(
        "Under the null case the overall PA was 0.5 for every classifier with a balanced test set, and the AUC 0.5.",
        "Results, null case; Additional file 1",
        [{"name": "PA within 0.01 of 0.5, every classifier and k1train, balanced test sets", "expected": "yes",
          "arithmetic": yn(pa_ok_paper), "observed": yn(pa_ok_ours)},
         {"name": "AUC within 0.015 of 0.5, every classifier and k1train, 500 test samples", "expected": "yes",
          "arithmetic": yn(auc_paper), "observed": yn(auc_ours)}])

    # Fig. 2 text: 1-NN, k1train 0.1, G = 40.
    f = []
    for p, e1, e2 in ((1000, "0.02", "0.98"), (10000, "0.00", "1.00")):
        s = f"null_p{p}_k0.10"
        f.append(num_field(f"1-NN PA1, p = {p}", e1, P.point("fig2", 0.1, classifier="1-NN", p=p), O.get(s, "bal20", "1-NN", "PA1"), O.se(s, "bal20", "1-NN", "PA1")))
        f.append(num_field(f"1-NN PA2, p = {p}", e2, None, O.get(s, "bal20", "1-NN", "PA2"), O.se(s, "bal20", "1-NN", "PA2")))
    C["text.fig2_1nn"] = claim("For 1-NN with k1train = 0.1, p = 1000 and 10000 and G = 40: PA1 = 0.02 and 0.00, PA2 = 0.98 and 1.00.",
                               "Results, null case (Fig. 2)", f, "Fig. 2 plots PA1 only; PA2 has no arithmetic check.")

    def sel_bias(get):
        lower = [c for c in NINE if None not in (get(c, 40), get(c, 1000)) and get(c, 1000) < get(c, 40) - 0.01]
        return len(lower)
    paper_n = sel_bias(lambda c, p: P.point("fig2", 0.1, classifier=c, p=p))
    ours_n = sel_bias(lambda c, p: O.get(f"null_p{p}_k0.10", "bal20", c, "PA1"))
    C["text.selection_bias"] = claim(
        "For most classifiers, variable selection further increased the probability of classifying a new sample in the training-set majority class.",
        "Results, null case (Fig. 2)",
        [{"name": "classifiers whose PA1 at k1train 0.1 is lower (by over 0.01) with p = 1000 than with p = 40 (G = 40): at least 5 of 9",
          "expected": "yes", "arithmetic": yn(paper_n >= 5), "observed": yn(ours_n >= 5),
          "arithmetic_count": paper_n, "observed_count": ours_n}])

    def gap(get):
        g = {}
        for c in NINE:
            v = [abs(get(c, x, "PA2") - get(c, x, "PA1")) for x in (0.2, 0.8) if None not in (get(c, x, "PA1"), get(c, x, "PA2"))]
            g[c] = sum(v) / len(v) if len(v) == 2 else None
        top = sorted([c for c in g if g[c] is not None], key=lambda c: -g[c])[:3]
        return set(top) == {"RF", "SVM", "PAM"}, top
    pa_, ptop = gap(lambda c, x, m: P.point("fig1", x, classifier=c, metric=m))
    oa_, otop = gap(lambda c, x, m: O.get(f"null_p40_k{k(x)}", "match20", c, m))
    C["text.most_sensitive_null"] = claim(
        "Without variable selection RF, SVM and PAM were the most sensitive to class imbalance (largest difference between the class-specific PA, Fig. 1).",
        "Results, null case (Fig. 1)",
        [{"name": "the three classifiers with the largest |PA2 - PA1| at k1train 0.2 and 0.8 (mean of the two; Fig. 1) are RF, SVM and PAM", "expected": "yes",
          "arithmetic": yn(pa_), "observed": yn(oa_), "arithmetic_top3": ptop, "observed_top3": otop}])

    f = []
    for base in ("RF", "PLR"):
        def spread(m):
            a, b = O.get("null_p40_k0.10", "bal20", m, "PA1"), O.get("null_p40_k0.90", "bal20", m, "PA1")
            return None if None in (a, b) else b - a
        s0, s1 = spread(base), spread(base + "-THR")
        f.append({"name": f"{base}-THR: PA1 rises less from k1train 0.1 to 0.9 than with {base}, but by more than 0.05 (null, p = 40)", "expected": "yes",
                  "observed": yn(None if None in (s0, s1) else (s1 < s0 and s1 > 0.05)), "observed_spread": s1, "observed_spread_plain": s0})
    C["text.thr_null"] = claim("When the classification rules of RF and PLR were adjusted to the class imbalance (RF-THR, PLR-THR), the dependency of the class-specific PA on class imbalance diminished but did not disappear.",
                               "Results, null case", f, "Data not shown in the paper: no arithmetic check.")

    # --- Alternative case ---
    def dlda_best(get, p):
        v = {c: get(c, p) for c in NINE}
        v = {c: x for c, x in v.items() if x is not None}
        return (max(v, key=v.get) == "DLDA") if v else None
    C["text.dlda_least_sensitive"] = claim(
        "DLDA showed the smallest decrease in the PA of the minority class.",
        "Results, alternative case (Fig. 3, Additional file 4)",
        [{"name": f"DLDA has the highest PA1 of the nine at k1train 0.1, pDE = 20, p = {p}", "expected": "yes",
          "arithmetic": yn(dlda_best(lambda c, p: P.point("af4", 0.1, classifier=c, p=p), p)),
          "observed": yn(dlda_best(lambda c, p: O.get(f"alt20_p{p}_k0.10", "bal20", c, "PA1"), p))} for p in (40, 1000, 10000)])

    # Fig. 4.
    mus = [0.0] + [round(0.1 * i, 1) for i in range(1, 21)] + [3.0]
    def first_mu(get, thr=0.98):
        for m in mus:
            v = get(m)
            if v is not None and v >= thr:
                return m
        return None
    f1, f2 = [], []
    for c in ("1-NN", "DLDA", "PLR"):
        pm = first_mu(lambda m: P.point("fig4", m, classifier=c, center="samples", k1train=0.5))
        om = first_mu(lambda m: O.get(f"mu_samples_k0.5_mu{m:.1f}", "bal20", c, "PA"))
        f1.append({"name": f"{c}: smallest mu2 with PA >= 0.98 at k1train 0.5 lies in [1, 1.5]", "expected": "yes",
                   "arithmetic": yn(pm is not None and 1 <= pm <= 1.5), "observed": yn(om is not None and 1 <= om <= 1.5),
                   "arithmetic_mu": pm, "observed_mu": om})
        pm = first_mu(lambda m: P.point("fig4", m, classifier=c, center="samples", k1train=0.9))
        om = first_mu(lambda m: O.get(f"mu_samples_k0.9_mu{m:.1f}", "bal20", c, "PA"))
        f2.append({"name": f"{c}: smallest mu2 with PA >= 0.98 at k1train 0.9 is at least 2", "expected": "yes",
                   "arithmetic": yn(pm is not None and pm >= 2), "observed": yn(om is not None and om >= 2),
                   "arithmetic_mu": pm, "observed_mu": om})
    for c in ("3-NN", "5-NN", "DQDA", "RF", "SVM", "PAM"):
        pm = first_mu(lambda m: P.point("af7", m, classifier=c, center="samples", k1train=0.5))
        om = first_mu(lambda m: O.get(f"mu_samples_k0.5_mu{m:.1f}", "bal20", c, "PA"))
        f1.append({"name": f"{c}: smallest mu2 with PA >= 0.98 at k1train 0.5 lies in [1, 1.5]", "expected": "yes",
                   "arithmetic": yn(pm is not None and 1 <= pm <= 1.5), "observed": yn(om is not None and 1 <= om <= 1.5),
                   "arithmetic_mu": pm, "observed_mu": om})
    C["text.fig4_balanced"] = claim("For the balanced training set the overall PA reached 1 when mu2 was between 1 and 1.5 for all the classifiers.",
                                    "Results (Fig. 4, Additional file 7)", f1,
                                    "Reaching 1 is read as a mean PA of 0.98 or more. Fig. 4 plots 1-NN, DLDA and PLR; the other six are read from Additional file 7.")
    C["text.fig4_imbalanced"] = claim("Much larger differences (mu2 >= 2) were needed for the highly imbalanced data (k1train = 0.1).",
                                      "Results (Fig. 4)", f2,
                                      "Fig. 4 shows k1train = 0.5 to 0.9 with the shift in Class 2; the text's k1train = 0.1 is the same imbalance with the classes swapped, so 0.9 is compared.")
    f = []
    for kk in (0.5, 0.6, 0.7, 0.8, 0.9):
        v = O.nsel(f"mu_samples_k{kk:.1f}_mu1.5")
        f.append({"name": f"all 20 non-null variables selected in at least 95% of runs, mu2 = 1.5, k1train {kk}", "expected": "yes",
                  "observed": yn(None if v is None else v >= 0.95), "observed_share": v})
    C["text.fig4_selection"] = claim("All the non-null variables were selected in almost all simulations when mu2 >= 1.5.",
                                     "Results (Fig. 4)", f, "Data not shown in the paper: no arithmetic check. 'Almost all' is read as 95% of runs or more.")
    f = []
    for c in ("1-NN", "DLDA", "PLR"):
        a = [P.point("fig4", 1.0, classifier=c, center=cc, k1train=0.9) for cc in ("variables", "samples")]
        o = [O.get(f"mu_{cc}_k0.9_mu1.0", "bal20", c, "PA") for cc in ("variables", "samples")]
        f.append({"name": f"{c}: PA at k1train 0.9, mu2 = 1 lower with centred variables than with centred samples", "expected": "yes",
                  "arithmetic": yn(None if None in a else a[0] < a[1]), "observed": yn(None if None in o else o[0] < o[1])})
    C["text.variable_centering"] = claim("Normalizing the variables worsened the PA on class-imbalanced data.", "Results (Fig. 4)", f)

    # --- Solutions ---
    def af8(c, corr, x, m):
        return P.point("af8", x, classifier=c, correction=corr, metric=m)
    def ours_corr(c, corr, x, m, t="bal20", what="mean_avail"):
        name = {"none": "alt20", "over": "over", "down": "down", "multds": "multds"}[corr]
        return O.get(f"{name}_p1000_k{k(x)}", t, c, m, what)
    f = []
    for c in NINE:
        def mean_gain(get):
            v = [(get(c, "over", x, "PA"), get(c, "none", x, "PA")) for x in K19]
            v = [a - b for a, b in v if None not in (a, b)]
            return sum(v) / len(v) if len(v) == len(K19) else None
        a, o = mean_gain(af8), mean_gain(ours_corr)
        if c in ("3-NN", "5-NN"):
            name, test = f"{c}: over-sampling raises the overall PA by more than 0.05 on average over k1train", lambda g: g > 0.05
        elif c == "1-NN":
            name, test = f"{c}: over-sampling changes the overall PA by less than 0.02 on average over k1train", lambda g: abs(g) < 0.02
        else:
            name, test = f"{c}: over-sampling changes the overall PA by less than 0.05 on average over k1train", lambda g: abs(g) < 0.05
        f.append({"name": name, "expected": "yes", "arithmetic": yn(None if a is None else test(a)),
                  "observed": yn(None if o is None else test(o)), "arithmetic_gain": a, "observed_gain": o})
    C["text.oversampling"] = claim("Over-sampling produced almost no change in PA for most classifiers; only 3-NN and 5-NN benefitted, while 1-NN was not modified at all.",
                                   "Results, over-sampling (Fig. 5, Additional file 8)", f, "'Benefitted' is read as a mean rise of more than 0.05 in the overall PA over the 19 imbalance levels, 'almost no change' as less than 0.05 and 'not modified at all' as less than 0.02.")
    f = []
    for c in NINE:
        for m in ("PA1", "PA2"):
            f.append(num_field(f"{c}: down-sizing, k1train 0.1, {m}", "0.70", af8(c, "down", 0.1, m), ours_corr(c, "down", 0.1, m), about=True))
    for c in NINE:
        f.append(num_field(f"{c}: no correction, n1 = 4, n2 = 76 (k1train 0.05), PA1", "0", af8(c, "none", 0.05, "PA1"), ours_corr(c, "none", 0.05, "PA1"), about=True))
    C["text.downsizing"] = claim("Using only 4 samples per class (k1train = 0.1), all the classifiers achieved a PA of about 0.70 for both classes, while the full-data analysis gave PA1 = 0 and PA2 = 1 (n1 = 4 and n2 = 76).",
                                 "Results, down-sizing (Fig. 5, Additional file 8)", f,
                                 "The sentence mixes two imbalances: k1train = 0.1 is 8 samples per class, n1 = 4 is k1train = 0.05. Down-sizing is compared at 0.1 (as the text names), the full data at 0.05 (as its n1 = 4).")
    a0, a1 = af8("PAM", "none", 0.2, "PA1"), af8("PAM", "down", 0.2, "PA1")
    f = [num_field("PAM, k1train 0.2, no correction, PA1", "0.5", a0, ours_corr("PAM", "none", 0.2, "PA1"), O.se("alt20_p1000_k0.20", "bal20", "PAM", "PA1")),
         num_field("PAM, k1train 0.2, down-sizing, PA1", "0.8", a1, ours_corr("PAM", "down", 0.2, "PA1"), O.se("down_p1000_k0.20", "bal20", "PAM", "PA1"))]
    C["text.pam_downsizing"] = claim("PA1 increased from 0.5 (full data) to 0.8 when we down-sized the training set using PAM with k1train = 0.2.",
                                     "Results, down-sizing (Additional file 8)", f)

    def pi(fig_corr, c, x):
        for r in P.figs:
            if r["figure"] == "af10" and r["classifier"] == c and r["correction"] == fig_corr:
                for px, lo, hi in r["points"]:
                    if abs(px - x) < 1e-9:
                        return lo, hi
        return None, None
    f = []
    for c in ("3-NN", "DLDA", "RF", "PLR"):
        for x, elo, ehi in ((0.5, "0.8", "1.0"), (0.1, "0.50", "0.90")):
            lo, hi = pi("down", c, x)
            f.append({"name": f"{c}: down-sizing, k1train {x}, 95% PI lower end", "expected": elo, "tolerance": {"abs": 0.0505},
                      "arithmetic": lo, "observed": ours_corr(c, "down", x, "PA", "bal20", "q025")})
            f.append({"name": f"{c}: down-sizing, k1train {x}, 95% PI upper end", "expected": ehi, "tolerance": {"abs": 0.0505},
                      "arithmetic": hi, "observed": ours_corr(c, "down", x, "PA", "bal20", "q975")})
    C["text.downsizing_pi"] = claim("The 95% prediction intervals obtained by down-sizing were between 0.8 and 1.0 for k1train = 0.5 and between 0.50 and 0.90 for k1train = 0.10.",
                                    "Results, down-sizing (Additional file 10)", f,
                                    "Percentiles of the PA on a 20-sample test set move in steps of 0.05; the tolerance is one step. Additional file 10's intervals match a 20-sample test set, not the 500 of its caption (item af10).")
    f = []
    for c in ("3-NN", "DLDA", "PLR", "1-NN", "5-NN", "DQDA"):
        def flat(get):
            v = [get(x) for x in K19 if 0.2 <= x <= 0.8 and x != 0.5]
            return None if None in v or not v else max(v) - min(v) <= 0.03
        f.append({"name": f"{c}: MultDS PA varies by 0.03 or less over k1train 0.20-0.80 (0.5 left out)", "expected": "yes",
                  "arithmetic": yn(flat(lambda x: af8(c, "multds", x, "PA"))), "observed": yn(flat(lambda x: ours_corr(c, "multds", x, "PA")))})
    C["text.multds_flat"] = claim("With MultDS the PA of all classifiers did not vary for k1train = 0.20 to 0.80.", "Results, MultDS (Fig. 5)", f,
                                  "'Did not vary' is read as a range of 0.03 or less. At k1train = 0.5 the training set is balanced and MultDS is a single classifier, so its PA dips there, in the paper as in ours; that point is left out. MultDS was run for six classifiers (not RF, SVM, PAM).")
    f = []
    for c in ("3-NN", "DLDA", "PLR", "1-NN", "5-NN", "DQDA"):
        f.append(num_field(f"{c}: MultDS, k1train 0.1, mean PA", "0.85", af8(c, "multds", 0.1, "PA"), ours_corr(c, "multds", 0.1, "PA"), about=True))
    for c in ("3-NN", "DLDA", "PLR"):
        lo, hi = pi("multds", c, 0.1)
        f.append({"name": f"{c}: MultDS, k1train 0.1, 95% PI lower end", "expected": "0.7", "tolerance": {"abs": 0.0505}, "arithmetic": lo,
                  "observed": ours_corr(c, "multds", 0.1, "PA", "bal20", "q025")})
        f.append({"name": f"{c}: MultDS, k1train 0.1, 95% PI upper end", "expected": "1.0", "tolerance": {"abs": 0.0505}, "arithmetic": hi,
                  "observed": ours_corr(c, "multds", 0.1, "PA", "bal20", "q975")})
    C["text.multds_k01"] = claim("When k1train = 0.1 the average PA of MultDS was around 0.85 for most classifiers and the 95% prediction intervals were between 0.7 and 1.0.",
                                 "Results, MultDS (Additional file 10)", f)
    f = []
    for c in ("3-NN", "DLDA", "PLR", "1-NN", "5-NN", "DQDA"):
        def better(get):
            v = [(get(c, "multds", x, "PA"), get(c, "down", x, "PA")) for x in K19]
            if any(None in t for t in v):
                return None
            return all(a >= b - 0.005 for a, b in v)
        f.append({"name": f"{c}: MultDS PA at least that of down-sizing at every k1train", "expected": "yes",
                  "arithmetic": yn(better(af8)), "observed": yn(better(ours_corr))})
    C["text.multds_vs_down"] = claim("MultDS was similar but consistently better than down-sizing in terms of average PA.", "Results, MultDS (Fig. 5)", f,
                                     "'At least' allows 0.005 for Monte Carlo noise.")

    # --- Breast cancer data ---
    f = [{"name": "tumours", "expected": "99", "observed": str(counts["arrays"])},
         {"name": "probes", "expected": "7650", "observed": str(counts["probes"])},
         {"name": "ER-", "expected": "34", "observed": str(counts["er_neg"])},
         {"name": "ER+", "expected": "65", "observed": str(counts["er_pos"])},
         {"name": "grade 1 or 2", "expected": "54", "observed": str(counts["grade12"])},
         {"name": "grade 3", "expected": "45", "observed": str(counts["grade3"])}]
    for x in f:
        x["tolerance"] = {"printed": True}
    C["text.data_counts"] = claim("99 tumours, 7650 probes; ER- 34, ER+ 65; grade 1 or 2: 54, grade 3: 45.", "Methods, microarray data", f,
                                  "Counted in the BRB-ArrayTools project of the NCI archive (read_sotiriou.R).")
    er = lambda corr, neg, pos, c, m, what="mean_avail": O.get(f"er_samples_{corr}_neg{neg}_pos{pos}", "bal40", c, m, what)  # noqa: E731
    t13 = lambda c, m: P.cell("af13", classifier=c, n_pos=20, n_neg=5, metric=m)  # noqa: E731
    paper = {m: [t13(c, m) for c in NINE] for m in ("PA_ER+", "PA_ER-", "PV_ER+", "PV_ER-", "AUC")}
    ours = {m: [er("none", 5, 20, c, mm) for c in NINE] for m, mm in (("PA_ER+", "PA1"), ("PA_ER-", "PA2"), ("PV_ER+", "PV1"), ("PV_ER-", "PV2"), ("AUC", "AUC"))}
    def ok(v, f):
        return None if any(x is None for x in v) else f(v)
    f = [{"name": "PA ER+ above 0.90 for all nine", "expected": "yes", "arithmetic": yn(ok(paper["PA_ER+"], lambda v: min(v) > 0.9)),
          "observed": yn(ok(ours["PA_ER+"], lambda v: min(v) > 0.9))},
         num_field("PA ER-, smallest of the nine", "0.2", ok(paper["PA_ER-"], min), ok(ours["PA_ER-"], min), about=True),
         num_field("PA ER-, largest of the nine", "0.6", ok(paper["PA_ER-"], max), ok(ours["PA_ER-"], max), about=True),
         {"name": "PV ER+ about 0.9 (0.85-0.95) for all nine", "expected": "yes", "arithmetic": yn(ok(paper["PV_ER+"], lambda v: all(0.85 <= x <= 0.95 for x in v))),
          "observed": yn(ok(ours["PV_ER+"], lambda v: all(0.85 <= x <= 0.95 for x in v)))},
         {"name": "PV ER- between 0.7 and 0.8 for all nine (within 0.005)", "expected": "yes", "arithmetic": yn(ok(paper["PV_ER-"], lambda v: all(0.695 <= x <= 0.805 for x in v))),
          "observed": yn(ok(ours["PV_ER-"], lambda v: all(0.695 <= x <= 0.805 for x in v)))},
         {"name": "AUC between 0.8 and 0.9 for all nine (within 0.005)", "expected": "yes", "arithmetic": yn(ok(paper["AUC"], lambda v: all(0.795 <= x <= 0.905 for x in v))),
          "observed": yn(ok(ours["AUC"], lambda v: all(0.795 <= x <= 0.905 for x in v)))}]
    C["text.er_20_5"] = claim("With 20 ER+ and 5 ER- training samples PA ER+ was above 0.90 for all classifiers, PA ER- ranged from about 0.2 to 0.6, PV ER+ was about 0.9, PV ER- ranged between 0.7 and 0.8, and the AUC was between 0.8 and 0.9.",
                              "Results, breast cancer data (Additional file 13)", f)
    f = []
    for neg, e in ((5, "0.75"), (10, "0.85")):
        vals = [er("down", neg, pos, c, m) for pos in ((10, 20, 30, 45) if neg == 5 else (20, 30, 45)) for c in NINE for m in ("PA1", "PA2")]
        f.append(num_field(f"down-sizing to {neg} per class: mean class-specific PA over classifiers, classes and ER+ counts", e, None,
                           None if None in vals else sum(vals) / len(vals), about=True))
    C["text.er_downsizing"] = claim("Using the smaller balanced training set (down-sizing) the class-specific PA were approximately the same (about 0.75 and 0.85, using 5 or 10 samples per class).",
                                    "Results, breast cancer data", f, "Data not shown in the paper: no arithmetic check.")
    gapo = None if None in (er("over", 10, 20, "DQDA", "PA1"), er("over", 10, 20, "DQDA", "PA2")) else er("over", 10, 20, "DQDA", "PA1") - er("over", 10, 20, "DQDA", "PA2")
    C["text.er_oversampling"] = claim("Over-sampling did not remove the dependency of class-specific PA on class imbalance, with differences as large as 0.22 (20 ER+ against 10 ER-, DQDA).",
                                      "Results, breast cancer data",
                                      [num_field("DQDA over-sampling, 20 ER+ / 10 ER-: PA ER+ minus PA ER-", "0.22", None, gapo,
                                                 math.sqrt((O.se("er_samples_over_neg10_pos20", "bal40", "DQDA", "PA1") or 0) ** 2 + (O.se("er_samples_over_neg10_pos20", "bal40", "DQDA", "PA2") or 0) ** 2))],
                                      "Data not shown in the paper: no arithmetic check.")
    f6 = lambda c, corr, pos, m, what: next((r[what] for r in P.figs if r["figure"] == "fig6" and r["classifier"] == c and r["center"] == "samples"  # noqa: E731
                                             and r["correction"] == corr and r["n_neg"] == 5 and r["n_pos"] == pos and r["metric"] == m), None)
    lows_o = [er("multds", 5, 45, c, m, "q025") for c in NINE for m in ("PA1", "PA2")]
    a12 = lambda c, corr, pos, m: next((r["lo"] for r in P.figs if r["figure"] == "af12" and r["classifier"] == c and r["center"] == "samples"  # noqa: E731
                                        and r["correction"] == corr and r["n_neg"] == 5 and r["n_pos"] == pos and r["metric"] == m), None)
    f = []
    for m, mm in (("PA_ER+", "PA1"), ("PA_ER-", "PA2")):
        lp = [a12(c, "multds", 45, m) for c in NINE]
        lo = [er("multds", 5, 45, c, mm, "q025") for c in NINE]
        f.append({"name": f"MultDS, 45 ER+ / 5 ER-: lower limit of the {m.replace('PA_', '')} prediction interval above 0.60 for most (5 or more) of the nine", "expected": "yes",
                  "arithmetic": yn(None if None in lp else sum(x > 60.05 for x in lp) >= 5),
                  "observed": yn(None if None in lo else sum(x > 0.6005 for x in lo) >= 5),
                  "arithmetic_values": lp, "observed_values": lo})
    downs_p = [a12(c, "none", 5, m) for c in NINE for m in ("PA_ER+", "PA_ER-")]
    downs_o = [er("none", 5, 5, c, m, "q025") for c in NINE for m in ("PA1", "PA2")]
    f.append({"name": "5 ER+ / 5 ER- (the down-sized set): the prediction interval includes 0.50 for all nine classifiers (both classes)", "expected": "yes",
              "arithmetic": yn(None if None in downs_p else all(x <= 50.5 for x in downs_p)),
              "observed": yn(None if None in downs_o else all(x <= 0.505 for x in downs_o))})
    C["text.er_multds_pi"] = claim("With 5 ER- samples the lower limits of the prediction intervals obtained by MultDS were above 0.60 for most classifiers even for the largest degree of class imbalance.",
                                   "Results, breast cancer data (Fig. 6, Additional file 12)", f,
                                   "Arithmetic from the bars of Additional file 12 (all nine classifiers, in %). Down-sizing to 5 per class is the balanced 5 / 5 design, which the figure shows for every imbalance.")
    imb = [(5, 10), (5, 20), (5, 30), (5, 45), (10, 20), (10, 30), (10, 45)]
    def gain(c):
        v = [(er("multds", n, p, c, "PA"), er("down", n, p, c, "PA")) for n, p in imb]
        return None if any(None in t for t in v) else sum(a - b for a, b in v) / len(v)
    gains_o = {c: gain(c) for c in NINE}
    C["text.pam_multds"] = claim("PAM seemed to benefit the most from MultDS; the gains over simple down-sizing were not as large as in the simulations.",
                                 "Results, breast cancer data", [
                                     {"name": "PAM has the largest mean gain in overall PA of MultDS over down-sizing (7 imbalanced ER designs)", "expected": "yes",
                                      "observed": yn(None if None in gains_o.values() else max(gains_o, key=gains_o.get) == "PAM"),
                                      "observed_gains": {c: None if v is None else round(v, 4) for c, v in gains_o.items()}}],
                                 "The paper prints no down-sizing results for the ER data (Fig. 6 and Additional file 13 show no correction), so there is no arithmetic check.")
    f = []
    for c in ("3-NN", "DLDA", "PLR"):
        a = [f6(c, "none", 45, "PA_ER-", "value"), None]
        a[1] = next((r["value"] for r in P.figs if r["figure"] == "fig6" and r["classifier"] == c and r["center"] == "variables"
                     and r["correction"] == "none" and r["n_neg"] == 5 and r["n_pos"] == 45 and r["metric"] == "PA_ER-"), None)
        o = [er("none", 5, 45, c, "PA2"), O.get("er_variables_none_neg5_pos45", "bal40", c, "PA2")]
        f.append({"name": f"{c}: PA ER- at 45 ER+ / 5 ER- lower with centred variables than with centred samples", "expected": "yes",
                  "arithmetic": yn(None if None in a else a[1] < a[0]), "observed": yn(None if None in o else o[1] < o[0])})
    C["text.er_variable_centering"] = claim("Variable normalization further increased the effect of class imbalance, causing even more cases to be classified in the training set majority class.",
                                            "Results, breast cancer data (Fig. 6)", f)
    json.dump(C, open(sys.argv[4], "w"), indent=1)
    for cid, c in C.items():
        print(cid, [(x["expected"], x.get("arithmetic"), x.get("observed")) for x in c["fields"]][:4])


if __name__ == "__main__":
    main()
