"""Every quantitative statement of the text: first recomputed from the paper's own tables (arithmetic), then from
our run (observed).

Usage: claims.py PUBLISHED_VALUES_JSON SIMULATION_JSON NONCONVERGED_JSON OUT_JSON

Each claim is a list of fields with the printed value as a string ("expected"), our value ("observed") and,
where the paper's tables hold what the statement summarizes, the same computation on the paper's tables
("arithmetic"). A number from our Monte Carlo run is compared at a tolerance like the tables' (half a printed
unit + 3 x sqrt(2) Monte Carlo SE); yes/no statements are computed by the same rule on both sides.
Pooling rules: the text's overall biases and its convergence by factor are pooled over all data sets of the
factor level (each cell ran 1,000), so from the paper's tables they are the means of Table 1 weighted by its
% converged (bias) or unweighted (convergence).
"""
import json
import math
import sys

PARAMS = ["g00", "g01", "g10", "g11", "sigma0", "sigma1"]
FIXEDP = PARAMS[:4]
RANDP = PARAMS[4:]
K = 3 * math.sqrt(2)


def unit(printed):
    s = printed.strip().lstrip("-")
    return 10.0 ** -(len(s.split(".")[1])) if "." in s else 1.0


def num(name, printed, observed, mcse=0.0, arithmetic=None):
    f = {"name": name, "expected": printed, "observed": None if observed is None else round(observed, 4),
         "tolerance": {"abs": round(0.5 * unit(printed) + K * mcse, 4)}}
    if arithmetic is not None:
        f["arithmetic"] = round(arithmetic, 4) if isinstance(arithmetic, float) else arithmetic
    return f


def yn(name, expected, observed, arithmetic=None):
    f = {"name": name, "expected": expected, "observed": "yes" if observed else "no"}
    if arithmetic is not None:
        f["arithmetic"] = "yes" if arithmetic else "no"
    return f


def cid(g, n, icc):
    return f"J{g}_n{n}_icc{float(icc):.2f}"


def build(pub, sim, nc, run="main"):
    R = sim["runs"][run]
    C = R["cells"]
    t1, t3, t2, t4 = pub["table1"], pub["table3"], pub["table2"], pub["table4"]
    P1 = {cid(r["groups"], r["size"], r["icc"]): r for r in t1}
    P3 = {cid(r["groups"], r["size"], r["icc"]): r for r in t3}
    claims = {}

    def t1mean(key, sel, weight=False):
        rows = [r for r in t1 if sel(r)]
        if weight:
            w = [float(r["converged"]) for r in rows]
            return sum(float(r[key]) * wi for r, wi in zip(rows, w)) / sum(w)
        return sum(float(r[key]) for r in rows) / len(rows)

    # --- Methods: the design's arithmetic
    claims["methods_design"] = {
        "label": "Methods: random-intercept variances 0.13, 0.67 and 2.0 give ICC 0.04, 0.17 and 0.38 (with sigma_e^2 = pi^2/3) and sigma0 0.36, 0.82 and 1.42",
        "quote": "the variances of the random intercept were set at 0.13, 0.67, and 2.0, corresponding to intra-class correlation coefficients (ICC) of 0.04, 0.17, and 0.38 ... σ0 follows from the ICC and is set to 0.36, 0.82, and 1.42",
        "fields": []}
    for v, icc, sd in ((0.13, "0.04", "0.36"), (0.67, "0.17", "0.82"), (2.0, "0.38", "1.42")):
        i = v / (v + math.pi ** 2 / 3)
        claims["methods_design"]["fields"].append(num(f"ICC of variance {v}", icc, i, arithmetic=i))
        claims["methods_design"]["fields"].append(num(f"sigma0 = sqrt({v})", sd, math.sqrt(v), arithmetic=math.sqrt(v)))
    pp = sim["prevalence"]["pooled"]["all_cells"]
    claims["methods_prevalence"] = {
        "label": "Methods and Table 4: the outcome's prevalence is close to 30% in the main grid, and 0.10, 0.34 and 0.45 with Table 4's coefficients",
        "quote": "The overall prevalence of the outcome is close to 30 percent. ... We set the parameters ... at -3.0, 0.3, 0.3, and 0.3 for prevalence of 10%, at -1.0, 0.3, 0.3, and 0.3 for prevalence of 34% and -0.3, -0.3, -0.3, and -0.3 for prevalence of 45%.",
        "fields": [num("prevalence, all data sets of the main grid (%)", "30", 100 * sim_prev(sim))] +
                  [num(f"prevalence of the Table 4 column {k}", k, pp[k]["prevalence_observed"]) for k in ("0.10", "0.34", "0.45")]}

    # --- Convergence
    conv = R["converged_by_factor"]
    f = [num("lowest % converged of a cell", "56", R["converged_range"][0], cmcse(R["converged_range"][0], 1000),
             min(float(r["converged"]) for r in t1)),
         num("highest % converged of a cell", "100", R["converged_range"][1], cmcse(R["converged_range"][1], 1000),
             max(float(r["converged"]) for r in t1))]
    for fac, levels, printed in (("size", ("5", "30", "50"), ("80.4", "99.3", "99.9")),
                                 ("groups", ("30", "50", "100"), ("87.7", "93.8", "98.1")),
                                 ("icc", ("0.04", "0.17", "0.38"), ("89.2", "94.5", "95.9"))):
        for lev, pr in zip(levels, printed):
            o = conv[fac][lev]
            a = t1mean("converged", lambda r: (str(r[fac]) if fac != "icc" else r["icc"]) == lev)
            f.append(num(f"% converged, {fac} {lev}", pr, o, cmcse(o, 9000), a))
            f[-1]["arithmetic_tolerance"] = {"abs": 0.55}   # Table 1 prints whole percentages: a mean of nine is off by up to 0.5
    f.append(yn("convergence rises with the number of groups and with group size", "yes",
                increasing([conv["groups"][k] for k in ("30", "50", "100")]) and increasing([conv["size"][k] for k in ("5", "30", "50")]),
                increasing([t1mean("converged", lambda r, g=g: r["groups"] == g) for g in (30, 50, 100)])
                and increasing([t1mean("converged", lambda r, n=n: r["size"] == n) for n in (5, 30, 50)])))
    f.append({"name": "negative variance estimates in converged models", "expected": "none",
              "observed": "none" if R["negative_variances_in_converged"] == 0 else str(R["negative_variances_in_converged"])})
    claims["text_convergence"] = {"label": "Convergence: 56% to 100% by cell; 80.4/99.3/99.9% by group size, 87.7/93.8/98.1% by number of groups, 89.2/94.5/95.9% by ICC; no negative variances",
                                  "quote": "The overall rate of model convergence varied from 56% to 100%. There were no negative variance estimates in converged models ...", "fields": f}

    cv = R["converged_vs_not"]
    claims["text_converged_vs_not"] = {
        "label": "Converged against non-converged data sets: prevalence 30.4% vs 30.0%; z mean and SD 0.01 and 1.01 vs 0.02 and 1.00; x 0.00 and 1.00 vs 0.00 and 1.00",
        "quote": "no significant differences in prevalence (30.4% vs. 30.0%), mean and standard deviation of zj (0.01 and 1.01 versus 0.02 and 1.00), or mean and standard deviation of xij (0.00 and 1.00 vs. 0.00 and 1.00)",
        "fields": [num("prevalence of converged data sets (%)", "30.4", 100 * cv["prevalence"]["converged"], 100 * cv["prevalence"]["converged_se"]),
                   num("prevalence of non-converged data sets (%)", "30.0", 100 * cv["prevalence"]["not_converged"], 100 * cv["prevalence"]["not_converged_se"])]
        + [num(f"{lab}, {which.replace('_', ' ')}", pr, cv[k][which], cv[k][which + "_se"])
           for k, lab, which, pr in (("z_mean", "mean of z", "converged", "0.01"), ("z_sd", "SD of z", "converged", "1.01"),
                                      ("z_mean", "mean of z", "not_converged", "0.02"), ("z_sd", "SD of z", "not_converged", "1.00"),
                                      ("x_mean", "mean of x", "converged", "0.00"), ("x_sd", "SD of x", "converged", "1.00"),
                                      ("x_mean", "mean of x", "not_converged", "0.00"), ("x_sd", "SD of x", "not_converged", "1.00"))]}

    N = nc["nonconverged"]
    claims["text_nonconverged_followup"] = {
        "label": "Non-converged data sets of 30 groups x 5 refitted with a random intercept only and a random slope only: both significant in 2.4% (168 data sets)",
        "quote": "we examined 168 non-convergent simulated data sets with 30 groups and group size of 5 ... Both the random intercept and random slope were statistically significant in only a small proportion of these data sets (2.4%).",
        "fields": [{"name": "non-converged data sets of 30 groups x 5 examined", "expected": "168", "observed": N["datasets"]},
                   num("both random effects significant (%), likelihood-ratio tests", "2.4", N["lrt"]["both_significant_pct"],
                       100 * math.sqrt(0.024 * 0.976 / 168))]}

    nm = nc["normality"]

    def share_nonnormal(cells):
        tests = [nm[c][p]["normal"] for c in cells for p in FIXEDP]
        return sum(not t for t in tests), len(tests)

    a100_50 = share_nonnormal([cid(100, 50, i) for i in ("0.04", "0.17", "0.38")])
    a100_5 = share_nonnormal([cid(100, 5, i) for i in ("0.04", "0.17", "0.38")])
    a50_30 = share_nonnormal([cid(50, 30, i) for i in ("0.04", "0.17", "0.38")])
    claims["text_normality"] = {
        "label": "Shapiro-Wilk tests of the fixed-effect estimates: most non-normal with groups of 5 even with 100 groups, a few non-normal with groups of 30 and 50 groups, all normal with 100 groups of 50",
        "quote": "The majority of estimates from simulations with a group size of 5 were non-normal even with 100 groups. For simulations with a group size of 30 a few estimates were non-normal even with 50 groups. All estimates were normally distributed with 100 groups and group size of 50.",
        "fields": [yn("majority of the 12 fixed-effect estimates of 100 groups x 5 non-normal", "yes", a100_5[0] > a100_5[1] / 2),
                   yn("a few (some, not most) of the 12 of 50 groups x 30 non-normal", "yes", 0 < a50_30[0] <= a50_30[1] / 2),
                   yn("all 12 of 100 groups x 50 normal", "yes", a100_50[0] == 0)],
        "counts": {"100x5": a100_5, "50x30": a50_30, "100x50": a100_50}}

    # --- Fixed-effect bias
    pb = R["pooled_bias"]
    f = []
    for p, pr in zip(FIXEDP, ("0.6", "2.6", "1.4", "3.7")):
        f.append(num(f"overall % bias {p}", pr, pb[p], pooled_mcse(C, p), t1mean(p, lambda r: True, weight=True)))
    f.append(yn("γ11 has the largest overall bias of the fixed effects", "yes", max(FIXEDP, key=lambda p: abs(pb[p])) == "g11",
                max(FIXEDP, key=lambda p: abs(t1mean(p, lambda r: True, weight=True))) == "g11"))
    claims["text_fixed_bias_overall"] = {"label": "Overall fixed-effect bias 0.6%, 2.6%, 1.4% and 3.7% for γ00, γ01, γ10, γ11 ('data not shown'); γ11 the largest",
                                        "quote": "the overall biases for the fixed effect parameters γ00, γ01, γ10, and γ11 were 0.6%, 2.6%, 1.4%, and 3.7% respectively (data not shown). The cross-level interaction parameter (γ11) had the largest overall bias.",
                                        "fields": f}

    c0 = cid(30, 5, "0.04")
    f = []
    for p, pr in zip(FIXEDP, ("8.8", "11.1", "15.8", "13.3")):
        f.append(num(f"% bias {p} at 30 groups x 5, ICC 0.04", pr, C[c0][p]["bias_pct"], C[c0][p]["bias_mcse"], float(P1[c0][p])))
        f.append(yn(f"{p}: the largest bias of the 27 cells is at 30 groups x 5, ICC 0.04", "yes",
                    max(C, key=lambda c: C[c][p]["bias_pct"]) == c0,
                    max(P1, key=lambda c: float(P1[c][p])) == c0))
    for (g, n, lim, lab) in ((30, 30, 6, "below 6% at 30 groups x 30"), (50, 30, 4, "below 4% at 50 groups x 30"),
                             (100, 30, 1, "1% or less at 100 groups x 30")):
        cs = [cid(g, n, i) for i in ("0.04", "0.17", "0.38")]
        ours = max(abs(C[c][p]["bias_pct"]) for c in cs for p in FIXEDP)
        theirs = max(abs(float(P1[c][p])) for c in cs for p in FIXEDP)
        f.append(yn(f"every fixed-effect bias {lab}", "yes", ours <= lim if lim == 1 else ours < lim,
                    theirs <= lim if lim == 1 else theirs < lim))
    claims["text_fixed_bias_cells"] = {"label": "Largest fixed-effect biases 8.8%, 11.1%, 15.8%, 13.3% at 30 groups x 5, ICC 0.04; below 6% at 30 x 30, below 4% at 50 x 30, 1% or less at 100 x 30",
                                      "quote": "the largest biases (8.8%, 11.1%, 15.8%, and 13.3% for γ00, γ01, γ10, and γ11) were found under conditions where of the smallest variance for the random intercept (0.13), the smallest group size (5), and the lowest number of groups (30) ...",
                                      "fields": f}

    # --- Variance-component bias
    pbi = R["pooled_bias_by_icc"]
    f = [num("overall % bias σ0", "6.9", pb["sigma0"], pooled_mcse(C, "sigma0"), t1mean("sigma0", lambda r: True, True)),
         num("overall % bias σ1", "5.0", pb["sigma1"], pooled_mcse(C, "sigma1"), t1mean("sigma1", lambda r: True, True)),
         num("% bias σ0 at σ0 = 0.36 (ICC 0.04)", "21.2", pbi["0.04"]["sigma0"], pooled_mcse(C, "sigma0", "0.04"),
             t1mean("sigma0", lambda r: r["icc"] == "0.04", True))]
    for icc, pr in (("0.04", "21"), ("0.17", "0.5"), ("0.38", "0.1")):
        f.append(num(f"% bias σ0, ICC {icc}", pr, pbi[icc]["sigma0"], pooled_mcse(C, "sigma0", icc),
                     t1mean("sigma0", lambda r, i=icc: r["icc"] == i, True)))
    s1 = [pbi[i]["sigma1"] for i in ("0.04", "0.17", "0.38")]
    s1a = [t1mean("sigma1", lambda r, i=i: r["icc"] == i, True) for i in ("0.04", "0.17", "0.38")]
    f.append(num("lowest % bias σ1 over the ICCs", "4", min(s1), pooled_mcse(C, "sigma1", "0.04"), min(s1a)))
    f.append(num("highest % bias σ1 over the ICCs", "6", max(s1), pooled_mcse(C, "sigma1", "0.04"), max(s1a)))
    c = cid(100, 50, "0.04")
    cs = [cid(100, 50, i) for i in ("0.04", "0.17", "0.38")]
    f.append(yn("every variance-component bias below 4% at 100 groups x 50", "yes",
                max(abs(C[x][p]["bias_pct"]) for x in cs for p in RANDP) < 4, max(abs(float(P1[x][p])) for x in cs for p in RANDP) < 4))
    s5 = [x for x in C if "_n5_" in x]
    s30 = [x for x in C if "_n5_" not in x]
    f.append(yn("variance components positively biased in every cell of group size 5", "yes",
                all(C[x][p]["bias_pct"] > 0 for x in s5 for p in RANDP), all(float(P1[x][p]) > 0 for x in s5 for p in RANDP)))
    f.append(yn("variance components underestimated in every cell of group size 30 or 50", "yes",
                all(C[x][p]["bias_pct"] < 0 for x in s30 for p in RANDP), all(float(P1[x][p]) < 0 for x in s30 for p in RANDP)))
    claims["text_random_bias"] = {"label": "Variance components: overall bias 6.9% (σ0) and 5.0% (σ1); σ0 21.2% at σ0 0.36 (21%, 0.5%, 0.1% by ICC); σ1 4-6% by ICC; below 4% at 100 x 50; positive at group size 5, negative at 30 and 50",
                                  "quote": "The overall biases (data not shown) for σ0 and σ1 were 6.9% and 5.0% ... The overall relative bias for the random intercept was 21%, 0.5%, 0.1% for ICC 0.04, 0.17, 0.38",
                                  "fields": f}

    # --- Non-coverage
    M = R["marginals"]
    f = []

    def mg(p, fac, lev):
        return M[p][fac][lev]

    fixed_g = [mg(p, "groups", l) for p in FIXEDP for l in ("30", "50", "100")]
    fixed_g_a = [float(t2[p]["groups"][l]) for p in FIXEDP for l in ("30", "50", "100")]
    rnd_g = [mg(p, "groups", l) for p in RANDP for l in ("30", "50", "100")]
    rnd_g_a = [float(t2[p]["groups"][l]) for p in RANDP for l in ("30", "50", "100")]
    nse = lambda v, n: math.sqrt(v * (1 - v) / n)  # noqa: E731
    ng = M["g00"]["groups"]["n"] / 3
    f += [num("lowest fixed-effect non-coverage by number of groups (%)", "5", 100 * min(fixed_g), 100 * nse(0.05, ng), 100 * min(fixed_g_a)),
          num("highest fixed-effect non-coverage by number of groups (%)", "6", 100 * max(fixed_g), 100 * nse(0.06, ng), 100 * max(fixed_g_a)),
          num("lowest variance-component non-coverage by number of groups (%)", "7", 100 * min(rnd_g), 100 * nse(0.07, ng), 100 * min(rnd_g_a)),
          num("highest variance-component non-coverage by number of groups (%)", "11", 100 * max(rnd_g), 100 * nse(0.11, ng), 100 * max(rnd_g_a)),
          num("σ0 non-coverage, 30 groups (%)", "11", 100 * mg("sigma0", "groups", "30"), 100 * nse(0.11, ng), 100 * float(t2["sigma0"]["groups"]["30"])),
          num("σ1 non-coverage, 30 groups (%)", "10", 100 * mg("sigma1", "groups", "30"), 100 * nse(0.10, ng), 100 * float(t2["sigma1"]["groups"]["30"])),
          num("σ0 non-coverage, 100 groups (%)", "9", 100 * mg("sigma0", "groups", "100"), 100 * nse(0.09, ng), 100 * float(t2["sigma0"]["groups"]["100"])),
          num("σ1 non-coverage, 100 groups (%)", "7", 100 * mg("sigma1", "groups", "100"), 100 * nse(0.07, ng), 100 * float(t2["sigma1"]["groups"]["100"]))]
    allfix = [mg(p, fac, l) for p in FIXEDP for fac in ("groups", "size", "icc") for l in M[p][fac] if l not in ("p", "n", "p_trend")]
    allfix_a = [float(t2[p][fac][l]) for p in FIXEDP for fac in ("groups", "size", "icc") for l in t2[p][fac] if l != "p"]
    f += [num("lowest fixed-effect non-coverage in Table 2 (%)", "4", 100 * min(allfix), 100 * nse(0.04, ng), 100 * min(allfix_a)),
          num("highest fixed-effect non-coverage in Table 2 (%)", "6", 100 * max(allfix), 100 * nse(0.06, ng), 100 * max(allfix_a))]
    sl = [mg("sigma1", "size", l) for l in ("5", "30", "50")]
    sla = [float(t2["sigma1"]["size"][l]) for l in ("5", "30", "50")]
    f.append(yn("random-slope non-coverage rises with group size", "yes", increasing(sl), increasing(sla)))
    ic = [mg("sigma0", "icc", l) for l in ("0.04", "0.17", "0.38")]
    ica = [float(t2["sigma0"]["icc"][l]) for l in ("0.04", "0.17", "0.38")]
    f.append(yn("random-intercept non-coverage falls as ICC rises", "yes", decreasing(ic), decreasing(ica)))
    cellfix = [C[x][p]["noncoverage"] for x in C for p in FIXEDP if C[x][p]["noncoverage"] is not None]
    cellfix_a = [float(P3[x][p]) for x in P3 for p in FIXEDP]
    cellrnd = [C[x][p]["noncoverage"] for x in C for p in RANDP if C[x][p]["noncoverage"] is not None]
    cellrnd_a = [float(P3[x][p]) for x in P3 for p in RANDP]
    f += [num("lowest fixed-effect non-coverage of a cell (%)", "3", 100 * min(cellfix), 100 * nse(0.03, 1000), 100 * min(cellfix_a)),
          num("highest fixed-effect non-coverage of a cell (%)", "7", 100 * max(cellfix), 100 * nse(0.07, 1000), 100 * max(cellfix_a)),
          num("lowest variance-component non-coverage of a cell (%)", "7", 100 * min(cellrnd), 100 * nse(0.07, 1000), 100 * min(cellrnd_a)),
          num("highest variance-component non-coverage of a cell (%)", "17", 100 * max(cellrnd), 100 * nse(0.17, 1000), 100 * max(cellrnd_a))]
    claims["text_noncoverage"] = {"label": "Non-coverage: fixed effects 5-6% by number of groups (4-6% in Table 2, 3-7% by cell); variance components 7-11% (11% and 10% at 30 groups, 9% and 7% at 100; 7-17% by cell); σ1 rises with group size, σ0 falls with ICC",
                                  "quote": "the effect of number of groups on the standard errors of the fixed effect parameters is small with non-coverage rates ranging from 5% and 6% ... The rates of non-coverage for the variance-covariance components range from 7% and 17%.",
                                  "fields": f}

    # --- Prevalence
    PP = sim["prevalence"]["pooled"]
    f = []
    fx = lambda d: max(abs(d[p]["bias_pct"]) for p in FIXEDP)  # noqa: E731
    rx = lambda d: max(abs(d[p]["bias_pct"]) for p in RANDP)  # noqa: E731
    f.append(yn("the 10% prevalence has the largest fixed-effect bias", "yes",
                fx(PP["all_cells"]["0.10"]) > max(fx(PP["all_cells"]["0.34"]), fx(PP["all_cells"]["0.45"])),
                max(abs(float(t4[p]["bias"]["0.10"])) for p in FIXEDP) > max(abs(float(t4[p]["bias"][x])) for p in FIXEDP for x in ("0.34", "0.45"))))
    f.append(yn("the 10% prevalence has the largest variance-component bias", "yes",
                rx(PP["all_cells"]["0.10"]) > max(rx(PP["all_cells"]["0.34"]), rx(PP["all_cells"]["0.45"])),
                max(abs(float(t4[p]["bias"]["0.10"])) for p in RANDP) > max(abs(float(t4[p]["bias"][x])) for p in RANDP for x in ("0.34", "0.45"))))
    f.append(yn("convergence lowest at 10% prevalence", "yes",
                PP["all_cells"]["0.10"]["converged_pct"] < min(PP["all_cells"][x]["converged_pct"] for x in ("0.34", "0.45")),
                float(t4["g00"]["converged"]["0.10"]) < min(float(t4["g00"]["converged"][x]) for x in ("0.34", "0.45"))))
    fnc = [PP["all_cells"][x][p]["noncoverage"] for x in ("0.10", "0.34", "0.45") for p in FIXEDP]
    fnca = [float(t4[p]["noncoverage"][x]) for x in ("0.10", "0.34", "0.45") for p in FIXEDP]
    rnc = [PP["all_cells"][x][p]["noncoverage"] for x in ("0.10", "0.34", "0.45") for p in RANDP]
    rnca = [float(t4[p]["noncoverage"][x]) for x in ("0.10", "0.34", "0.45") for p in RANDP]
    n4 = PP["all_cells"]["0.10"]["g00"]["n_ci"]
    f += [num("lowest fixed-effect non-coverage over the prevalences (%)", "5", 100 * min(fnc), 100 * nse(0.05, n4), 100 * min(fnca)),
          num("highest fixed-effect non-coverage over the prevalences (%)", "6", 100 * max(fnc), 100 * nse(0.06, n4), 100 * max(fnca)),
          num("lowest variance-component non-coverage over the prevalences (%)", "8", 100 * min(rnc), 100 * nse(0.08, n4), 100 * min(rnca)),
          num("highest variance-component non-coverage over the prevalences (%)", "11", 100 * max(rnc), 100 * nse(0.11, n4), 100 * max(rnca))]
    ps5, pg30 = PP["size5"]["0.10"], PP["groups30"]["0.10"]
    f += [num("largest fixed-effect bias, group size 5 and 10% prevalence (%)", "12", fx(ps5), max(ps5[p]["bias_mcse"] for p in FIXEDP)),
          num("largest variance-component bias, group size 5 and 10% prevalence (%)", "50", rx(ps5), max(ps5[p]["bias_mcse"] for p in RANDP)),
          num("largest fixed-effect bias, 30 groups and 10% prevalence (%)", "9", fx(pg30), max(pg30[p]["bias_mcse"] for p in FIXEDP)),
          num("random-slope bias, 30 groups and 10% prevalence (%)", "15", abs(pg30["sigma1"]["bias_pct"]), pg30["sigma1"]["bias_mcse"])]
    claims["text_prevalence"] = {"label": "Prevalence: 10% gives the largest bias and the lowest convergence; non-coverage 5-6% (fixed) and 8-11% (random); largest bias 12% and 50% with groups of 5, 9% and 15% with 30 groups ('data not shown')",
                                 "quote": "Table 4 shows that for both fixed and random effect parameters the simulated data with 10% prevalence had the largest bias ... (12% for fixed effect and 50% for random effect) ... with 30 groups and a 10% prevalence the largest bias was 9% for the fixed effect parameters and 15% for the random slope.",
                                 "fields": f}

    # --- Robustness tests (Discussion, Table 5)
    RT = nc["robustness_tests"]
    t5 = pub["table5"]
    f = []
    paper_calls = {"2": "no difference", "3": "more likely", "4": "less likely", "5": "less likely",
                   "6": "more likely", "7": "more likely", "8": "more likely"}

    def t5conv(m, size):
        rows = [r for r in t5 if r["model"] == m and r["size"] == size]
        return sum(float(r["converged"]) for r in rows) / len(rows)

    def table_call(m, size):
        """The same test on Table 5's own % converged (100 data sets per cell, 300 per model and group size)."""
        k1, k2 = 3 * t5conv(1, size), 3 * t5conv(m, size)
        p = lr_two(k1, 300, k2, 300)
        return "no difference" if p >= 0.01 else ("more likely" if k2 > k1 else "less likely")

    for m, call in paper_calls.items():
        c = RT["convergence"]["5"][m]
        f.append({"name": f"model {m} against model 1, convergence with groups of 5 (p < 0.01)", "expected": call,
                  "observed": c["call"], "arithmetic": table_call(int(m), 5)})
    f.append(yn("no model differs from model 1 in convergence with groups of 30 or 50", "yes",
                all(RT["convergence"][n][m]["call"] == "no difference" for n in ("30", "50") for m in paper_calls),
                all(table_call(int(m), n) == "no difference" for n in (30, 50) for m in paper_calls)))
    f.append(yn("no fixed-effect estimate of models 2-8 differs from model 1 (t tests, p < 0.01)", "yes",
                not RT["fixed_t_tests"]["significant_at_0.01"]))
    for m in ("6", "7", "8"):
        for var, lab in (("var0", "random intercept"), ("var1", "random slope")):
            f.append(yn(f"model {m}: {lab} underestimated against model 1 (p < 0.01)", "yes",
                        RT["random_vs_model1"][m][var]["underestimated"]))
    for m in ("6", "7"):
        for var, lab in (("var0", "random intercept"), ("var1", "random slope")):
            f.append(yn(f"model {m}: {lab} coverage lower than model 1's (Fisher, p < 0.01)", "yes",
                        RT["coverage"][m][var]["lower_coverage"]))
    f.append(yn("fixed-effect coverage of models 2-8 equal to model 1's with groups of 30 or more and 50 or more groups (Fisher, p < 0.01)", "yes",
                not any(RT["coverage"][m]["fixed_significant_groups50plus_size30plus"] for m in paper_calls)))
    claims["text_robustness"] = {"label": "Non-normal models against model 1 (Discussion): convergence with groups of 5 higher for models 3, 6, 7, 8 and lower for 4, 5; no difference in fixed effects; variances underestimated for models 6-8; random-effect coverage lower for models 6 and 7",
                                 "quote": "Models 3, 6, 7, and 8 were more likely to converge while models 4 and 5 were less likely to converge (p-value < 0.01) when group size was 5 ... For models 6, 7, and 8 the random intercept and random slope were underestimated compare to model 1 (p < 0.01) ... The rates of coverage for the random components of models 6 and 7 were significantly lower",
                                 "fields": f}

    # --- Main claim (Abstract and Conclusion)
    c100_50 = [cid(100, 50, i) for i in ("0.04", "0.17", "0.38")]
    f = [yn("fixed effects unbiased at 100 groups x 50: every |bias| below 2%", "yes",
            max(abs(C[x][p]["bias_pct"]) for x in c100_50 for p in FIXEDP) < 2, max(abs(float(P1[x][p])) for x in c100_50 for p in FIXEDP) < 2),
         yn("variance components slightly biased at 100 groups x 50: largest |bias| between 1% and 4%", "yes",
            1 < max(abs(C[x][p]["bias_pct"]) for x in c100_50 for p in RANDP) < 4, 1 < max(abs(float(P1[x][p])) for x in c100_50 for p in RANDP) < 4),
         yn("biases severe with groups of 5: some fixed-effect bias above 10% and some variance bias above 50%", "yes",
            max(C[x][p]["bias_pct"] for x in s5 for p in FIXEDP) > 10 and max(C[x][p]["bias_pct"] for x in s5 for p in RANDP) > 50,
            max(float(P1[x][p]) for x in s5 for p in FIXEDP) > 10 and max(float(P1[x][p]) for x in s5 for p in RANDP) > 50),
         yn("fixed-effect standard errors unbiased: every cell's non-coverage within 2.5-7.5%", "yes",
            all(0.025 <= v <= 0.075 for v in cellfix), all(0.025 <= v <= 0.075 for v in cellfix_a)),
         yn("variance-component standard errors underestimated: non-coverage above 5% in every cell of group size 30 or 50", "yes",
            all(C[x][p]["noncoverage"] > 0.05 for x in s30 for p in RANDP), all(float(P3[x][p]) > 0.05 for x in s30 for p in RANDP)),
         claims["text_prevalence"]["fields"][0], claims["text_prevalence"]["fields"][1],
         yn("convergence problems where prevalence, the number of groups or group size is low (Conclusion i)", "yes",
            claims["text_prevalence"]["fields"][2]["observed"] == "yes" and claims["text_convergence"]["fields"][-2]["observed"] == "yes",
            claims["text_prevalence"]["fields"][2]["arithmetic"] == "yes" and claims["text_convergence"]["fields"][-2]["arithmetic"] == "yes"),
         yn("variance-component standard errors too small even with 100 groups of 50: non-coverage above 5% in all three cells (Conclusion iv)", "yes",
            all(C[x][p]["noncoverage"] > 0.05 for x in c100_50 for p in RANDP), all(float(P3[x][p]) > 0.05 for x in c100_50 for p in RANDP))]
    claims["text_main_claim"] = {"label": "Main claim (Abstract, Conclusion): fixed effects unbiased with 100 groups of 50, variance components slightly biased there, severe bias with groups of 5, fixed-effect SEs right and variance-component SEs too small, low prevalence needs larger samples",
                                 "quote": "The results show that the estimates of the fixed effect parameters are unbiased for 100 groups with group size of 50 or higher. The estimates of the variance covariance components are slightly biased even with 100 groups and group size of 50. The biases for both fixed and random effects are severe for group size of 5. ...",
                                 "fields": [dict(x) for x in f]}

    # Table 2 against Table 3 (arithmetic only): every pooled rate of Table 2 from Table 3 weighted by Table 1's % converged
    f = []
    for p in PARAMS:
        for fac in ("groups", "size", "icc"):
            for lev, printed in t2[p][fac].items():
                if lev == "p":
                    continue
                rows = [(r3, r1) for r3, r1 in zip(t3, t1) if (str(r3[fac]) if fac != "icc" else r3["icc"]) == lev]
                a = sum(float(r3[p]) * float(r1["converged"]) for r3, r1 in rows) / sum(float(r1["converged"]) for _, r1 in rows)
                f.append({"name": f"Table 2, {p}, {fac} {lev}", "expected": printed, "arithmetic": round(a, 4),
                          "tolerance": {"abs": 0.0015}})
    claims["_table2_from_table3"] = {"label": "Table 2 recomputed from Table 3 (weighted by Table 1's % converged)", "fields": f,
                                     "note": "tolerance 0.0015: Table 3's rounding (0.0005) and Table 1's (0.5 points of each weight)"}
    return claims


def main():
    pub = json.load(open(sys.argv[1]))
    sim = json.load(open(sys.argv[2]))
    nc = json.load(open(sys.argv[3]))
    out = sys.argv[4]
    claims = build(pub, sim, nc)
    # The same claims on our second run of the main grid (other seeds; Tables 4 and 5 and the record tests are the
    # main run's): how far a claim moves between two runs of one design.
    second = build(pub, sim, nc, run="second")
    for cid, c in claims.items():
        for f, f2 in zip(c["fields"], second[cid]["fields"]):
            if "observed" in f:
                f["second_run"] = f2.get("observed")
    with open(out, "w") as fh:
        json.dump(claims, fh, indent=1, ensure_ascii=False)
        fh.write("\n")


def lr_two(k1, n1, k2, n2):
    """LR test that two binomial proportions are equal; p from chi-square with 1 df."""
    def ll(k, n):
        p = k / n
        return (k * math.log(p) if k > 0 else 0.0) + ((n - k) * math.log(1 - p) if k < n else 0.0)
    stat = max(2 * (ll(k1, n1) + ll(k2, n2) - ll(k1 + k2, n1 + n2)), 0.0)
    return math.erfc(math.sqrt(stat / 2))


def sim_prev(sim):
    cv = sim["runs"]["main"]["converged_vs_not"]["prevalence"]
    st = sim["runs"]["main"]["status_counts"]
    n = sum(st.values())
    nconv = sum(v["n_converged"] for v in sim["runs"]["main"]["cells"].values())
    return (cv["converged"] * nconv + cv["not_converged"] * (n - nconv)) / n


def cmcse(pct, n):
    p = pct / 100
    return 100 * math.sqrt(max(p * (1 - p), 0.0) / n) if n else 0.0


def pooled_mcse(C, p, icc=None):
    """Monte Carlo SE of a bias pooled over cells: from each cell's SE, weighted by its converged fits."""
    cells = [c for k, c in C.items() if icc is None or k.endswith(f"icc{icc}")]
    w = [c["n_converged"] for c in cells]
    W = sum(w)
    return math.sqrt(sum((wi / W) ** 2 * c[p]["bias_mcse"] ** 2 for wi, c in zip(w, cells)))


def increasing(v):
    return all(a < b for a, b in zip(v, v[1:]))


def decreasing(v):
    return all(a > b for a, b in zip(v, v[1:]))


if __name__ == "__main__":
    main()
