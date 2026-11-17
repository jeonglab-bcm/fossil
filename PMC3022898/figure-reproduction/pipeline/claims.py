"""The claims of the text: each recomputed from the paper's own tables (arithmetic) and from our run.

Usage: claims.py PUBLISHED.json FIGURE_VALUES.json SIMULATION.json TABLE5.json OUT.json

Every claim is a list of fields. A field has the paper's printed value or statement ("expected"),
the same statement computed from the paper's own tables and figures ("arithmetic"), and from our
simulation ("observed"). Numbers from our run carry the Monte Carlo tolerance of compare.py; yes/no
statements are computed by the same code from either source.
"""
import json
import math
import sys

from compare import TABLES, true_esr
from simulate import RRS, SIZES

Z = 3.0
SIZE_KEYS = [f"{a}/{b}" for a, b in SIZES]
RR_KEYS = [f"{r:.1f}" for r in RRS]


def yn(b):
    return "yes" if b else "no"


class Source:
    """One source of numbers in the paper's layout: the paper's printed tables, or our run."""

    def __init__(self, tables=None, sim=None, figs=None):
        self.tables, self.sim, self.figs = tables, sim, figs

    def cell(self, table, s, size, rr):
        k = f"S{s}|{size}|{rr}"
        if self.tables is not None:
            v = self.tables[table].get(k)
            return None if v is None else float(v)
        est, meas, scale = TABLES[table]
        v = self.sim[k][est][meas]
        return None if v is None else v * scale

    def row(self, table, s, size):
        return [self.cell(table, s, size, rr) for rr in RR_KEYS]

    def length(self, fig, rr, ser):
        """Expected length (or empirical length) of Fig. fig's bar."""
        if self.figs is not None:
            return self.figs[f"fig{fig}"]["bars"][f"{rr}|{ser}"]["value"]
        b = self.sim[f"S{fig}|5000/5000|{rr}"]
        return {"esr_s_log": b["ci_s_log"]["expected_length_given_coverage"],
                "esr_r_log": b["ci_r_log"]["expected_length_given_coverage"],
                "esr_r_binomial": b["ci_r_binomial"]["expected_length_given_coverage"],
                "empirical": b["esr_r"]["empirical_length"]}[ser]


def se_of(sim, table, s, size, rr):
    k = f"S{s}|{size}|{rr}"
    est, meas, scale = TABLES[table]
    b = sim[k][est]
    if meas == "coverage":
        p = b["coverage"]
        return math.sqrt(max(p * (1 - p), 1e-4 * 0.9999) / (b["n_defined"] or 1)) * scale
    se = b["sd"] / math.sqrt(b["n"]) * scale
    return se / true_esr(k) if meas == "relative_bias" else se


def num_field(name, expected, arith, ours, se, cell=None):
    half = 0.5 * 10 ** -(len(expected.split(".")[1]) if "." in expected else 0)
    return {"name": name, "expected": expected, "arithmetic": None if arith is None else round(arith, 4),
            "observed": None if ours is None else round(ours, 4),
            "tolerance": {"abs": round(half + Z * math.sqrt(2) * se, 6)}, "cell": cell}


def yn_field(name, expected, arith_b, ours_b):
    return {"name": name, "expected": expected, "arithmetic": yn(arith_b), "observed": yn(ours_b)}


def claims(P, F, S, T5):
    paper = Source(tables=P, figs=F)
    ours = Source(sim=S["main"])
    sim = S["main"]
    out = {}

    def both(f):
        return f(paper), f(ours)

    # --- Abstract and main claim -----------------------------------------------------------------------
    def max_bias(src, t):
        vals = [(src.cell(t, s, sz, rr), (s, sz, rr)) for s in (1, 2, 3, 4) for sz in SIZE_KEYS for rr in RR_KEYS]
        return max(vals)
    (pr, pk), (orr, ok) = both(lambda x: max_bias(x, "S2"))
    (ps, psk), (os_, osk) = both(lambda x: max_bias(x, "S1"))
    out["text.abstract_max_bias"] = {
        "label": "Abstract: largest relative bias, ESR_R 4.0% and ESR_S 93.9%",
        "fields": [num_field("largest relative bias of ESR_R (%)", "4.0", pr, orr, se_of(sim, "S2", ok[0], ok[1], ok[2])),
                   num_field("largest relative bias of ESR_S (%)", "93.9", ps, os_, se_of(sim, "S1", osk[0], osk[1], osk[2]))],
        "where": {"paper": [pk, psk], "ours": [ok, osk]}}

    def main_claim(src):
        r_small = all(abs(src.cell("S2", s, sz, rr)) < 5 for s in (1, 2, 3, 4) for sz in SIZE_KEYS for rr in RR_KEYS)
        s_large = max(src.cell("S1", s, sz, rr) for s in (1, 2, 3, 4) for sz in SIZE_KEYS for rr in RR_KEYS) > 50
        cov_r = sum(src.cell("S6", s, sz, rr) >= 95 for s in (1, 2, 3, 4) for sz in SIZE_KEYS for rr in RR_KEYS)
        cov_s = sum(src.cell("S5", s, sz, rr) >= 95 for s in (1, 2, 3, 4) for sz in SIZE_KEYS for rr in RR_KEYS)
        return r_small, s_large, cov_r > cov_s, cov_r, cov_s
    a, o = both(main_claim)
    out["text.main_claim"] = {
        "label": "Main claim: ESR_R has little bias and ESR_S a large one; the log CI of ESR_R covers better in most settings",
        "fields": [yn_field("relative bias of ESR_R within 5% in all 112 settings", "yes", a[0], o[0]),
                   yn_field("relative bias of ESR_S above 50% somewhere", "yes", a[1], o[1]),
                   yn_field("log CI of ESR_R reaches 95% in more settings than the CI of ESR_S", "yes", a[2], o[2])],
        "counts": {"paper": {"esr_r_log_95": a[3], "esr_s_log_95": a[4]}, "ours": {"esr_r_log_95": o[3], "esr_s_log_95": o[4]}}}

    # --- Scenario results ------------------------------------------------------------------------------
    def esrs_cov_rr2(src, s):
        return all(src.cell("S5", s, sz, rr) >= 95 for sz in SIZE_KEYS for rr in ("1.0", "1.5", "2.0"))
    out["text.s1_esrs_coverage_rr2"] = {
        "label": "Scenario 1: CI of ESR_S covers at least 95% when RR is 2.0 or less, for every N1/N2",
        "fields": [yn_field("Scenario 1, RR <= 2.0, all N1/N2", "yes", *both(lambda x: esrs_cov_rr2(x, 1)))]}

    def log_r_pattern(src, s):
        three = all(src.cell("S6", s, sz, rr) >= 95 for sz in ("1000/1000", "5000/1000", "5000/5000") for rr in RR_KEYS)
        below = all(src.cell("S6", s, "1000/5000", rr) < 95 for rr in RR_KEYS)
        return three, below
    fields = []
    for s in (1, 2, 3):
        a, o = both(lambda x: log_r_pattern(x, s))
        fields.append(yn_field(f"Scenario {s}: log CI of ESR_R at least 95% for every RR at 1000/1000, 5000/1000, 5000/5000", "yes", a[0], o[0]))
        fields.append(yn_field(f"Scenario {s}: log CI of ESR_R below 95% for every RR at 1000/5000", "yes", a[1], o[1]))
    out["text.log_ci_esrr_pattern"] = {
        "label": "Scenarios 1-3: log CI of ESR_R reaches 95% except at N1/N2 1000/5000, where it never does",
        "fields": fields}

    def binom(src, s):
        only = [sz for sz in SIZE_KEYS if all(src.cell("S7", s, sz, rr) >= 95 for rr in RR_KEYS)]
        others_below = all(min(src.row("S7", s, sz)) < 95 for sz in SIZE_KEYS if sz != "1000/5000")
        return only == ["1000/5000"], others_below, min(src.row("S7", s, "1000/5000")), all(v > 99 for v in src.row("S7", s, "1000/5000"))
    a1, o1 = both(lambda x: binom(x, 1))
    a2, o2 = both(lambda x: binom(x, 2))
    a3, o3 = both(lambda x: binom(x, 3))
    out["text.binomial_ci_1000_5000"] = {
        "label": "Binomial CI of ESR_R reaches 95% only at N1/N2 1000/5000 (Scenario 1, smallest 98.9%); above 99% there in Scenarios 2 and 3",
        "fields": [yn_field("Scenario 1: 95% reached only at 1000/5000", "yes", a1[0], o1[0]),
                   num_field("Scenario 1, 1000/5000: smallest coverage (%)", "98.9", a1[2], o1[2],
                             se_of(sim, "S7", 1, "1000/5000", "1.0")),
                   yn_field("Scenario 2: above 99% for every RR at 1000/5000", "yes", a2[3], o2[3]),
                   yn_field("Scenario 3: above 99% for every RR at 1000/5000", "yes", a3[3], o3[3])]}

    def s2_bias(src):
        return all(src.cell("S1", 2, sz, "5.0") >= 20 for sz in SIZE_KEYS)  # "greater than 20%"; 20.0 is printed once
    def s3_bias(src):
        return (all(src.cell("S1", 3, sz, "1.5") > 10 for sz in SIZE_KEYS),
                all(src.cell("S1", 3, sz, "2.0") > 20 for sz in SIZE_KEYS),
                all(src.cell("S1", 3, sz, "5.0") > 80 for sz in SIZE_KEYS))
    a, o = both(s3_bias)
    out["text.esrs_bias_thresholds"] = {
        "label": "Relative bias of ESR_S: over 20% at RR 5.0 in Scenario 2; over 10%, 20% and 80% at RR 1.5, 2.0 and 5.0 in Scenario 3",
        "fields": [yn_field("Scenario 2, RR 5.0: over 20% for every N1/N2", "yes", *both(s2_bias)),
                   yn_field("Scenario 3, RR 1.5: over 10% for every N1/N2", "yes", a[0], o[0]),
                   yn_field("Scenario 3, RR 2.0: over 20% for every N1/N2", "yes", a[1], o[1]),
                   yn_field("Scenario 3, RR 5.0: over 80% for every N1/N2", "yes", a[2], o[2])]}

    def s3_max_r(src):
        vals = [(abs(src.cell("S2", 3, sz, rr)), src.cell("S2", 3, sz, rr), (3, sz, rr)) for sz in SIZE_KEYS for rr in RR_KEYS]
        return max(vals)
    (_, pv, pk), (_, ov, okk) = both(s3_max_r)
    out["text.s3_esrr_largest_bias"] = {
        "label": "Scenario 3: the largest relative bias of ESR_R is -1.8% (RR 3.0, 1000/1000)",
        "fields": [num_field("Scenario 3: relative bias of ESR_R furthest from 0 (%)", "-1.8", pv, ov, se_of(sim, "S2", *okk))],
        "where": {"paper": pk, "ours": okk}}

    # "In most cases" statements, as a majority of the settings they speak of.
    def most(src):
        s2 = [src.cell("S5", 2, sz, rr) for sz in SIZE_KEYS for rr in RR_KEYS]
        eq = [src.cell("S7", s, sz, rr) for s in (1, 2, 3, 4) for sz in ("1000/1000", "5000/5000") for rr in RR_KEYS]
        return (sum(v < 95 for v in s2) > len(s2) / 2, sum(87 <= v <= 95 for v in eq) > len(eq) / 2,
                sum(v < 95 for v in s2), len(s2), sum(87 <= v <= 95 for v in eq), len(eq))
    a_, o_ = both(most)
    out["text.most_cases"] = {
        "label": "Scenario 2: the CI of ESR_S is below 95% in most cases; with equal N1 and N2 the binomial CI of ESR_R covers 87% to 95% in most cases",
        "fields": [yn_field("Scenario 2: CI of ESR_S below 95% in most of its 28 settings", "yes", a_[0], o_[0]),
                   yn_field("Equal N1/N2: binomial CI of ESR_R between 87% and 95% in most of the 56 settings", "yes", a_[1], o_[1])],
        "counts": {"paper": [a_[2], a_[3], a_[4], a_[5]], "ours": [o_[2], o_[3], o_[4], o_[5]]}}

    # Numbers that restate one table cell (Results and Discussion).
    restated = [("Scenario 1, 1000/1000, RR 5.0: relative bias of ESR_S (%)", "31.4", "S1", 1, "1000/1000", "5.0"),
                ("Scenario 1, 1000/1000, RR 5.0: relative bias of ESR_R (%)", "3.4", "S2", 1, "1000/1000", "5.0"),
                ("Scenario 1, 5000/5000, RR 5.0: coverage of the CI of ESR_S (%)", "87.1", "S5", 1, "5000/5000", "5.0"),
                ("Scenario 2, 5000/5000, RR 5.0: coverage of the CI of ESR_S, the smallest (%)", "45", "S5", 2, "5000/5000", "5.0"),
                ("Scenario 3, 5000/5000, RR 5.0: coverage of the CI of ESR_S (%)", "4.2", "S5", 3, "5000/5000", "5.0"),
                ("Discussion, Scenario 1, 1000/1000, RR 1.0: binomial coverage (%)", "66", "S7", 1, "1000/1000", "1.0"),
                ("Discussion, Scenario 1, 1000/1000, RR 1.5: binomial coverage (%)", "78", "S7", 1, "1000/1000", "1.5"),
                ("Discussion, Scenario 1, 1000/1000, RR 2.0: binomial coverage (%)", "83", "S7", 1, "1000/1000", "2.0")]
    out["text.restated_cells"] = {
        "label": "Numbers in the text that restate a table cell",
        "fields": [num_field(n, e, paper.cell(t, s, sz, rr), ours.cell(t, s, sz, rr), se_of(sim, t, s, sz, rr), f"{t}|S{s}|{sz}|{rr}")
                   for n, e, t, s, sz, rr in restated]}

    # --- Scenario 4 at 250/250 (text only) --------------------------------------------------------------
    def s250(table, rr):
        return ours.cell(table, 4, "250/250", rr), se_of(sim, table, 4, "250/250", rr)
    r_bias = [ours.cell("S2", 4, "250/250", rr) for rr in RR_KEYS]
    binom = [ours.cell("S7", 4, "250/250", rr) for rr in RR_KEYS]
    logr = [ours.cell("S6", 4, "250/250", rr) for rr in RR_KEYS]
    i_rmin, i_rmax = r_bias.index(min(r_bias)), r_bias.index(max(r_bias))
    i_bmin, i_bmax = binom.index(min(binom)), binom.index(max(binom))
    lengths = {rr: (sim[f"S4|250/250|{rr}"]["ci_r_binomial"]["expected_length_given_coverage"],
                    sim[f"S4|250/250|{rr}"]["ci_r_log"]["expected_length_given_coverage"],
                    sim[f"S4|250/250|{rr}"]["esr_r"]["empirical_length"]) for rr in RR_KEYS}
    shorter = all(b < l for b, l, e in lengths.values())
    closer = all(abs(b - e) < abs(l - e) for b, l, e in lengths.values())
    out["text.s4_250"] = {
        "label": "Scenario 4 at N1/N2 250/250 (numbers given only in the text)",
        "fields": [num_field("relative bias of ESR_S, RR 1.0 (%)", "7.8", None, *s250("S1", "1.0")),
                   num_field("relative bias of ESR_S, RR 5.0 (%)", "84.9", None, *s250("S1", "5.0")),
                   num_field("relative bias of ESR_R, smallest (%)", "-1.1", None, r_bias[i_rmin], se_of(sim, "S2", 4, "250/250", RR_KEYS[i_rmin])),
                   num_field("relative bias of ESR_R, largest (%)", "1.1", None, r_bias[i_rmax], se_of(sim, "S2", 4, "250/250", RR_KEYS[i_rmax])),
                   num_field("coverage of the CI of ESR_S, RR 1.0 (%)", "96.8", None, *s250("S5", "1.0")),
                   num_field("coverage of the CI of ESR_S, RR 1.5 (%)", "92.3", None, *s250("S5", "1.5")),
                   num_field("coverage of the CI of ESR_S, RR 5.0 (%)", "56.8", None, *s250("S5", "5.0")),
                   {"name": "log CI of ESR_R above 95% for every RR", "expected": "yes", "arithmetic": None, "observed": yn(min(logr) > 95)},
                   num_field("binomial CI of ESR_R, smallest coverage (%)", "85.7", None, binom[i_bmin], se_of(sim, "S7", 4, "250/250", RR_KEYS[i_bmin])),
                   num_field("binomial CI of ESR_R, largest coverage (%)", "92.5", None, binom[i_bmax], se_of(sim, "S7", 4, "250/250", RR_KEYS[i_bmax])),
                   {"name": "binomial CI shorter than the log CI of ESR_R at every RR", "expected": "yes", "arithmetic": None, "observed": yn(shorter)},
                   {"name": "binomial CI length closer to the empirical length than the log CI's, at every RR", "expected": "yes", "arithmetic": None, "observed": yn(closer)}],
        "zero_cell_pairs": {rr: sim[f"S4|250/250|{rr}"].get("zero_cell_pairs") for rr in RR_KEYS}}

    # --- Figures 1-3 -------------------------------------------------------------------------------------
    def fig1(src):
        s_long = all(src.length(1, rr, "esr_s_log") > max(src.length(1, rr, x) for x in ("esr_r_log", "esr_r_binomial", "empirical")) for rr in ("1.0", "2.0", "5.0"))
        b_short = all(src.length(1, rr, "esr_r_binomial") < src.length(1, rr, "esr_r_log") for rr in ("1.0", "2.0", "5.0"))
        return s_long, b_short
    a, o = both(fig1)
    def fig2(src):
        inc = all(src.length(2, "1.0", x) < src.length(2, "2.0", x) < src.length(2, "5.0", x) for x in ("esr_s_log", "esr_r_log", "esr_r_binomial", "empirical"))
        gap = [src.length(2, rr, "esr_s_log") / src.length(2, rr, "esr_r_log") for rr in ("1.0", "2.0", "5.0")]
        return inc, gap[0] < 1.05 and gap[2] > gap[0] and gap[2] > 1.10
    a2, o2 = both(fig2)
    def fig3(src):
        dec = all(src.length(3, rr, x) < min(src.length(1, rr, x), src.length(2, rr, x)) for rr in ("1.0", "2.0", "5.0") for x in ("esr_s_log", "esr_r_log", "esr_r_binomial", "empirical"))
        inc = all(src.length(3, "1.0", x) < src.length(3, "2.0", x) < src.length(3, "5.0", x) for x in ("esr_s_log", "esr_r_log", "esr_r_binomial", "empirical"))
        return dec, inc
    a3, o3 = both(fig3)
    out["text.figures"] = {
        "label": "Figs 1-3 as the text reads them (expected length given coverage, 5000/5000)",
        "fields": [yn_field("Fig. 1: the CI of ESR_S is the longest at each RR", "yes", a[0], o[0]),
                   yn_field("Fig. 1: the binomial CI of ESR_R is shorter than its log CI at each RR", "yes", a[1], o[1]),
                   yn_field("Fig. 2: every interval lengthens as RR rises", "yes", a2[0], o2[0]),
                   yn_field("Fig. 2: ESR_S and ESR_R log CIs similar at RR 1.0 (within 5%), ESR_S longer by over 10% at RR 5.0", "yes", a2[1], o2[1]),
                   yn_field("Fig. 3: every interval shorter than in Figs 1 and 2", "yes", a3[0], o3[0]),
                   yn_field("Fig. 3: every interval lengthens as RR rises", "yes", a3[1], o3[1])]}

    # --- Case study (Table 5) ------------------------------------------------------------------------------
    ages = T5["ages"]
    r_vals = [float(a["printed"]["esr_r"]) for a in ages.values()]
    r_ours = [float(a["from_printed_inputs"]["esr_r"]) for a in ages.values()]
    def overlap(get):
        ok = True
        for a in ages.values():
            ivs = [tuple(map(float, get(a, k).split("-"))) for k in ("esr_s_log_ci", "esr_r_log_ci", "esr_r_binomial_ci")]
            ok &= max(i[0] for i in ivs) <= min(i[1] for i in ivs)
        return ok
    paper_overlap = overlap(lambda a, k: a["printed"][k])
    out["text.case_study"] = {
        "label": "Case study: ESR_R 0.57% to 2.11%; ESR_S higher; the CIs overlap; largest over-estimation 0.71% at ages 70-79",
        "fields": [{"name": "ESR_R, smallest (%)", "expected": "0.57", "arithmetic": f"{100 * min(r_vals):.2f}", "observed": f"{100 * min(r_ours):.2f}"},
                   {"name": "ESR_R, largest (%)", "expected": "2.11", "arithmetic": f"{100 * max(r_vals):.2f}", "observed": f"{100 * max(r_ours):.2f}"},
                   {"name": "ESR_S above ESR_R in every age group", "expected": "yes",
                    "arithmetic": yn(all(float(a["printed"]["esr_s"]) > float(a["printed"]["esr_r"]) for a in ages.values())),
                    "observed": yn(all(a["from_printed_inputs"]["esr_s_exact"] > a["from_printed_inputs"]["esr_r_exact"] for a in ages.values()))},
                   {"name": "the three CIs overlap in every age group", "expected": "yes", "arithmetic": yn(paper_overlap), "observed": None},
                   {"name": "largest over-estimation (%)", "expected": "0.71",
                    "arithmetic": f"{100 * max(float(a['printed']['esr_s']) - float(a['printed']['esr_r']) for a in ages.values()):.2f}",
                    "observed": T5["largest_overestimation"]["percent"]},
                   {"name": "largest over-estimation at ages", "expected": "70-79",
                    "arithmetic": max(ages, key=lambda k: float(ages[k]["printed"]["esr_s"]) - float(ages[k]["printed"]["esr_r"])),
                    "observed": T5["largest_overestimation"]["age"]}]}
    # Statements of the Discussion checked against the paper itself only.
    out["text.discussion_self"] = {
        "label": "Discussion statements checked against the paper's own tables and methods",
        "fields": [{"name": "case study overall risk ranges from", "expected": "0.0087",
                    "arithmetic": min(a["printed"]["overall_risk"] for a in ages.values())},
                   {"name": "case study overall risk ranges to", "expected": "0.0132",
                    "arithmetic": max(a["printed"]["overall_risk"] for a in ages.values())},
                   {"name": "the scenario with exposure .20 and disease in the unexposed .02", "expected": "scenario two",
                    "arithmetic": "Scenario 3"},
                   {"name": "equation of the log-based variance of ESR_R", "expected": "11", "arithmetic": "10"},
                   {"name": "equation of the binomial variance of ESR_R", "expected": "12", "arithmetic": "11"}]}
    return out


def main():
    pub_p, fig_p, sim_p, t5_p, out_p = sys.argv[1:6]
    P, F, S, T5 = (json.load(open(p)) for p in (pub_p, fig_p, sim_p, t5_p))
    out = claims(P, F, S, T5)
    # The same claims on our second run (another seed) and on the run without eq. 10's first term:
    # evidence for the causes, never a verdict.
    alt_main = {}
    for k, v in S["main"].items():
        b = dict(v)
        b["ci_r_log"] = S["variants"][k]["eq10_no_first_term"]["ci_r_log"]
        alt_main[k] = b
    for tag, sim in (("second_run", S["replicate"]), ("without_eq10_first_term", alt_main)):
        other = claims(P, F, dict(S, main=sim), T5)
        for cid, c in out.items():
            for f, g in zip(c["fields"], other[cid]["fields"]):
                if "observed" in f and f.get("observed") is not None:
                    f[tag] = g.get("observed")
    # Inconsistencies between the paper's tables (Tables 2-4 restate Tables S1, S2, S5, S6, S7).
    mp = {"table2": {"S": "S1", "R": "S2"}, "table3": {"S": "S5", "R": "S6"}}
    incons = []
    for t in ("table2", "table3"):
        for k, v in P[t].items():
            s, size, rr, e = k.split("|")
            w = P[mp[t][e]][f"{s}|{size}|{rr}"]
            if w != v:
                incons.append({"table": t, "cell": k, "value": v, "supplement": mp[t][e], "supplement_value": w})
    for k, v in P["table4"].items():
        if P["S7"][k] != v:
            incons.append({"table": "table4", "cell": k, "value": v, "supplement": "S7", "supplement_value": P["S7"][k]})
    out["_table_inconsistencies"] = incons
    # Keys without dots, so tools/check_results.py paths can name them (text.s4_250 -> text_s4_250).
    json.dump({k.replace(".", "_"): v for k, v in out.items()}, open(out_p, "w"), indent=1)
    for cid, c in out.items():
        if cid.startswith("_"):
            continue
        for f in c["fields"]:
            print(f"{cid}: {f['name']}: paper {f['expected']} | from its tables {f.get('arithmetic')} | ours {f.get('observed')} "
                  f"| second run {f.get('second_run')} | without eq. 10's first term {f.get('without_eq10_first_term')}", file=sys.stderr)
    print("table inconsistencies:", incons, file=sys.stderr)


if __name__ == "__main__":
    main()
