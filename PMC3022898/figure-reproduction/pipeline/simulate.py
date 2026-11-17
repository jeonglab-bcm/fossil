"""Run the simulation study of Reichmann et al. (2011) with the package esrisk.

Usage: simulate.py OUT.json [--reps 1000] [--seed 20110105]

Settings (Table 1): four scenarios (P(E), P(D|not E)) = (.05,.02), (.05,.09), (.20,.02), (.20,.09);
RR 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0; N1/N2 1000/1000, 1000/5000, 5000/1000, 5000/5000; and 250/250 in
Scenario 4. For each setting: one population of 10 million, then 1,000 pairs of independent samples
drawn without replacement. Each setting has its own random stream (seed, scenario, N1, N2, 10 x RR),
so a setting gives the same numbers whatever else is run.

Besides the main run (eq. 10 as printed; a log interval of (0, infinity) when sample 2 has a zero
cell; the true ESR = RR x P(D|not E), unrounded), the same samples are analysed again under the hypotheses
tested in the README, and the whole grid is run a second time with another seed (`replicate`) to
measure how often two runs of the same design differ by more than the comparison tolerance.
"""
import argparse
import json
import sys

import numpy as np

import esrisk as E

SCENARIOS = {1: (0.05, 0.02), 2: (0.05, 0.09), 3: (0.20, 0.02), 4: (0.20, 0.09)}
RRS = (1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0)
SIZES = ((1000, 1000), (1000, 5000), (5000, 1000), (5000, 5000))
POPULATION = 10_000_000


def settings():
    for s in SCENARIOS:
        for n1, n2 in SIZES:
            for rr in RRS:
                yield s, n1, n2, rr
    for rr in RRS:
        yield 4, 250, 250, rr


def key(s, n1, n2, rr):
    return f"S{s}|{n1}/{n2}|{rr:.1f}"


def rng_for(seed, s, n1, n2, rr):
    return np.random.default_rng(np.random.SeedSequence(seed, spawn_key=(s, n1, n2, int(round(rr * 10)))))


def eq10_variant(est, n1, n2, s2, how):
    """Log interval of ESR_R with the first term of eq. 10 replaced (hypothesis tests for Table S6)."""
    n2e, n2u = s2[:, 0] + s2[:, 1], s2[:, 2] + s2[:, 3]
    v_rr = E.var_ln_rr(s2[:, 0] / n2e, n2e, s2[:, 2] / n2u, n2u)
    p1u = E.p_unexposed(est.p1_d, est.rr2, est.p2_e)
    first = {
        "eq10": E.var_ln_proportion(p1u, n1),                 # the paper's eq. 10
        "no_first_term": 0.0,                                 # first term left out
        "var_not_log": p1u * (1 - p1u) / n1,                  # Var(P1(D|~E)) in place of Var(ln P1(D|~E))
        "n2_for_n1": E.var_ln_proportion(p1u, n2),            # sample 2's size in the first term
        "p1d_for_p1u": E.var_ln_proportion(est.p1_d, n1),     # overall risk in place of the risk in the unexposed
    }[how]
    lo, hi = E.log_ci(est.esr_r, first + v_rr)
    return np.where(np.isnan(lo), 0.0, lo), np.where(np.isnan(hi), np.inf, hi)  # zero cells: (0, inf), as the main run


def summary(est, true_esr, boot_rng=None):
    """The paper's measures, plus the Monte Carlo standard errors the comparisons need.

    length_se: standard error of the expected length given coverage (sd of the covering lengths over
    the square root of their number). empirical_length_se: bootstrap standard error of the empirical
    CI length (200 resamples of the pairs of samples), when boot_rng is given.
    """
    ev = E.evaluate(est, true_esr)
    out = {}
    for name, x in (("esr_s", est.esr_s), ("esr_r", est.esr_r)):
        out[name] = {k: ev[name][k] for k in ("mean", "sd", "n", "relative_bias", "absolute_bias",
                                                 "empirical_lower", "empirical_upper", "empirical_length")}
        if boot_rng is not None:
            x = x[np.isfinite(x)]
            idx = boot_rng.integers(0, x.size, size=(200, x.size))
            q = np.percentile(x[idx], [2.5, 97.5], axis=1)
            out[name]["empirical_length_se"] = float(np.std(q[1] - q[0], ddof=1))
    for name in ("ci_s_log", "ci_r_log", "ci_r_binomial"):
        out[name] = dict(ev[name])
        lo, hi = getattr(est, name)
        cover = np.isfinite(lo) & np.isfinite(hi) & (lo <= true_esr) & (true_esr <= hi)  # finite covering intervals
        n = int(cover.sum())
        out[name]["length_se"] = float(np.std((hi - lo)[cover], ddof=1) / np.sqrt(n)) if n > 1 else float("nan")
    return out


def rounded(obj, digits=10):
    if isinstance(obj, float):
        return None if not np.isfinite(obj) else float(f"{obj:.{digits}g}")
    if isinstance(obj, dict):
        return {k: rounded(v, digits) for k, v in obj.items()}
    if isinstance(obj, list):
        return [rounded(v, digits) for v in obj]
    return obj


def run(reps, seed):
    main, variants, replicate, popvar = {}, {}, {}, {}
    for s, n1, n2, rr in settings():
        pe, p0 = SCENARIOS[s]
        true = rr * p0
        k = key(s, n1, n2, rr)
        rng = rng_for(seed, s, n1, n2, rr)
        pop = E.make_population(pe, p0, rr, POPULATION, rng)
        s1 = E.draw_samples(pop, n1, reps, rng)
        s2 = E.draw_samples(pop, n2, reps, rng)
        counts = (s1[:, 0] + s1[:, 2], n1, s2[:, 0], s2[:, 0] + s2[:, 1], s2[:, 2], s2[:, 2] + s2[:, 3])
        est = E.estimate(*counts, zero_cells="unbounded")
        main[k] = summary(est, true, boot_rng=rng_for(seed + 3, s, n1, n2, rr))
        main[k]["population"] = {"cells": [int(x) for x in pop], "realized_esr": pop[0] / (pop[0] + pop[1])}
        main[k]["zero_cell_pairs"] = int(np.sum((s2[:, 0] == 0) | (s2[:, 2] == 0)))
        v = {}
        for rule in ("missing", "not_covered", "half"):
            v[f"zero_{rule}"] = summary(E.estimate(*counts, zero_cells=rule), true)
        v["true_esr_label"] = summary(est, float(f"{true:.2f}"))
        v["true_esr_realized"] = summary(est, pop[0] / (pop[0] + pop[1]))
        for how in ("no_first_term", "var_not_log", "n2_for_n1", "p1d_for_p1u"):
            lo, hi = eq10_variant(est, n1, n2, s2, how)
            alt = E.Estimates(est.p1_d, est.rr2, est.p2_e, est.esr_s, est.esr_r, est.ci_s_log, (lo, hi), est.ci_r_binomial)
            v[f"eq10_{how}"] = {"ci_r_log": summary(alt, true)["ci_r_log"]}
        variants[k] = v
        # The same design with an independent random stream: two runs of one design.
        est2, *_ = E.simulate(pe, p0, rr, n1, n2, reps, POPULATION, rng_for(seed + 1, s, n1, n2, rr))
        replicate[k] = summary(est2, true)
        # Exact cell proportions in the population instead of Bernoulli draws.
        est3, *_ = E.simulate(pe, p0, rr, n1, n2, reps, POPULATION, rng_for(seed + 2, s, n1, n2, rr), exact_population=True)
        popvar[k] = summary(est3, true)
    return {"main": main, "variants": variants, "replicate": replicate, "exact_population": popvar}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out")
    ap.add_argument("--reps", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=20110105)
    a = ap.parse_args()
    res = run(a.reps, a.seed)
    res["design"] = {"reps": a.reps, "seed": a.seed, "population": POPULATION, "scenarios": SCENARIOS,
                     "rrs": RRS, "sizes": SIZES, "esrisk": E.__version__, "numpy": np.__version__}
    with open(a.out, "w") as f:
        json.dump(rounded(res), f, indent=1, sort_keys=True)
        f.write("\n")
    print(f"{a.out}: {len(res['main'])} settings x {a.reps} pairs of samples", file=sys.stderr)


if __name__ == "__main__":
    main()
