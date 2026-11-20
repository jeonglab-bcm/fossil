"""Run every simulated setting of the paper with the package stratpower, and the hypothesis variants.

Usage: simulate.py OUT.json [--quick]

Primary design (fixed before the comparison; see results_notes.json, assumptions):
  * risk factors act on the odds scale (the paper's Tables 2 and 3 and Fig. 1B say odds ratio; the
    relative-risk scale cannot hold Table 3's six RFs of 3.0, whose risk would exceed 1);
  * EER = CER x .5 + .003 x 5 (Fig. 1A);
  * 4,400 per arm drawn with replacement from the (infinite) population; Wald test of the interaction;
  * 20,000 trials per setting (the paper ran 2,000), and a second run with another seed;
  * AUROC of the risk index for the outcome over both arms of the trial, from the population.
Hypothesis variants (10,000 trials each) change one of these at a time.
--quick: 2,000 trials everywhere (for a smoke test; not the committed outputs).
"""
import json
import math
import sys
import time

import numpy as np

import stratpower as sp

ITER = 20000
ITER_VARIANT = 10000
SEED, SEED2 = 20061, 20062
CER0 = 0.0075


def pop6(scale, eff=2.0, prev=0.25):
    return sp.population(6, prev, eff, CER0, scale)


def scenarios(scale, table2_others="or2", table3_population="six"):
    """(key, population, {subgroup name: variable}, extra kwargs, {name: AUROC wanted})."""
    out = []
    p = pop6(scale)
    k = p.count()
    out.append(("table1", p, {"conventional": p.patterns[:, 0], "dichotomized": (k >= 2) * 1.0, "continuous": k}, {}))
    for eff in (1.5, 2.0, 3.0):
        for prev in (0.10, 0.25, 0.50):
            others = [2.0] * 5 if table2_others == "or2" else [eff] * 5
            q = sp.Population([prev] + [0.25] * 5, [eff] + others, CER0, scale)
            out.append((f"table2/{eff:.1f}/{int(prev * 100)}%", q, {"conventional": q.patterns[:, 0]}, {}))
    for eff in (1.5, 2.0, 3.0):
        for nk in (1, 3, 6):
            try:
                if table3_population == "six":
                    q = sp.Population([0.25] * 6, [eff] * nk + [2.0] * (6 - nk), CER0, scale)
                else:
                    q = sp.Population([0.25] * nk, [eff] * nk, CER0, scale)
            except ValueError:
                out.append((f"table3/{eff:.1f}/{nk}", None, {}, {}))
                continue
            out.append((f"table3/{eff:.1f}/{nk}", q, {"index": q.count(range(nk))}, {}))
    q = sp.Population([0.25] * 6, [1.5, 1.5, 2.0, 2.0, 2.5, 2.5], CER0, scale)
    w = {"perfect": [1.5, 1.5, 2.0, 2.0, 2.5, 2.5], "uniform": [1] * 6, "reverse": [2.5, 2.5, 2.0, 2.0, 1.5, 1.5],
         "incomplete_reverse": [2.5, 2.5, 0, 0, 1.5, 1.5]}
    subs = {n: q.score(x) for n, x in w.items()}
    subs["conventional_rf5"] = q.patterns[:, 4]  # one RF of 2.5 analysed alone (the text's 37%)
    out.append(("table4", q, subs, {}))
    for h in (1, 2, 3, 4):
        out.append((f"table5/{h}", p, {"conventional": p.patterns[:, 0], "risk_stratified": k}, {"harm_per_year": h / 1000}))
    for m in (0.015, 0.03, 0.06, 0.09):
        c0 = sp.cer0_for_mean(m, 0.25, 2.0, scale, 4)
        q = sp.population(4, 0.25, 2.0, c0, scale)
        out.append((f"fig1b/{m * 100:g}%", q, {"one_rf": q.patterns[:, 0], "four_rf": q.count()}, {"cer0": c0}))
    return out


def run(scale, iterations, seed, test="wald", harm_model="additive", table2_others="or2", table3_population="six",
        only=None, population_size=None):
    res = {}
    for i, (key, pop, subs, extra) in enumerate(scenarios(scale, table2_others, table3_population)):
        if only and not any(key.startswith(o) for o in only):
            continue
        if pop is None:
            res[key] = None
            continue
        extra = dict(extra)
        c0 = extra.pop("cer0", None)
        r = sp.simulate_power(pop, subs, iterations=iterations, seed=seed + 1000 * i, test=test,
                              harm_model=harm_model, population_size=population_size, **extra)
        entry = {n: {"power": v["power"], "se": v["se"], "failed": v["failed"]} for n, v in r.items()}
        treat = {"harm_per_year": extra.get("harm_per_year", sp.HARM_PER_YEAR), "harm_model": harm_model}
        for n, z in subs.items():
            entry[n]["auroc"] = sp.population_auroc(pop, z, "both", **treat)
            entry[n]["auroc_control"] = sp.population_auroc(pop, z, "control", **treat)
        entry["mean_cer"] = pop.mean_cer
        if c0 is not None:
            entry["cer0"] = c0
        res[key] = entry
    return res


def deterministic():
    """Values that follow from the model without simulation: Table 1's subgroup columns and Fig. 1A."""
    out = {}
    for scale in ("or", "rr"):
        p = pop6(scale)
        k = p.count()
        groups = {"rf_absent": p.patterns[:, 0] == 0, "rf_present": p.patterns[:, 0] == 1,
                  "idx_0_1": k <= 1, "idx_ge2": k >= 2, "k0": k == 0, "k1": k == 1, "k2": k == 2,
                  "k3": k == 3, "k_ge4": k >= 4}
        # an infinite NNT (no net effect) is written as null: JSON has no infinity
        out[f"table1_{scale}"] = {r["group"]: {k: (None if isinstance(v, float) and math.isinf(v) else v) for k, v in r.items()}
                                  for r in sp.subgroup_table(p, groups)}
        out[f"table1_{scale}_mean_cer"] = p.mean_cer
    x = np.round(np.arange(0.016, 0.07501, 0.0005), 6)
    out["fig1a"] = {"cer": x.tolist(), "net_rrr": sp.net_rrr(x).tolist(),
                    "zero_at": 0.015 / 0.5, "net_rrr_at": {f"{c:g}": float(sp.net_rrr(c)) for c in (0.02, 0.03, 0.05, 0.06, 0.09)}}
    return out


def design_power(iterations, seed):
    """The Methods' design claim: N = 8,800 gives 80% power for an RRR of 25%, at the base case's CER."""
    out = {}
    for name, cer in (("table1_population", pop6("or").mean_cer),):
        p = sp.Population([0.0], [1.0], cer, "or")
        r = sp.simulate_power(p, {}, iterations=iterations, seed=seed, rrr=0.25, harm_per_year=0.0)
        out[name] = {"cer": cer, "power": r["main_effect"]["power"]}
    # the CER at which a two-arm trial of 4,400 per arm has 80% power for an RRR of 25% (normal approximation)
    lo, hi = 0.001, 0.2
    for _ in range(60):
        c = (lo + hi) / 2
        e = 0.75 * c
        se = ((c * (1 - c) + e * (1 - e)) / 4400) ** 0.5
        pw = 0.5 * (1 + math.erf(((c - e) / se - 1.959964) / 2 ** 0.5))
        lo, hi = (lo, c) if pw > 0.8 else (c, hi)
    out["cer_for_80pct"] = (lo + hi) / 2
    return out


def finite_population(iterations, seeds, size):
    """Power over several finite populations of `size` people (trials sampled with replacement from each)."""
    out = {}
    for key, pop, subs, extra in scenarios("or"):
        if key not in ("table1", "table2/3.0/25%"):
            continue
        vals = {n: [] for n in subs}
        for s in seeds:
            r = sp.simulate_power(pop, subs, iterations=iterations, seed=s, population_size=size)
            for n in subs:
                vals[n].append(r[n]["power"])
        out[key] = {n: {"mean": float(np.mean(v)), "sd": float(np.std(v, ddof=1)), "min": min(v), "max": max(v),
                        "powers": v} for n, v in vals.items()}
    return out


def main():
    args = sys.argv[1:]
    quick = "--quick" in args
    args = [a for a in args if a != "--quick"]
    out = args[0]
    it, itv = (2000, 2000) if quick else (ITER, ITER_VARIANT)
    t0 = time.time()
    sim = {"settings": {"iterations": it, "iterations_variants": itv, "seed": SEED, "seed_second_run": SEED2,
                        "n_per_arm": sp.N_PER_ARM, "cer0": CER0, "alpha": sp.ALPHA, "stratpower": sp.__version__},
           "primary": run("or", it, SEED),
           "second_run": run("or", it, SEED2)}
    sim["hypotheses"] = {
        "rr_scale": run("rr", itv, SEED + 7),
        "lr_test": run("or", itv, SEED + 11, test="lr"),
        "harm_independent": run("or", itv, SEED + 13, harm_model="independent"),
        "table2_others_same_or": run("or", itv, SEED + 17, table2_others="same", only=["table2"]),
        "table3_only_index_rfs": run("or", itv, SEED + 19, table3_population="only", only=["table3"]),
        "paper_iterations": run("or", 2000, SEED + 23),
    }
    sim["finite_population"] = {"8800": finite_population(2000, list(range(101, 121)), 8800),
                                "100000": finite_population(2000, list(range(201, 221)), 100000)}
    sim["deterministic"] = deterministic()
    sim["design_power"] = design_power(it, SEED + 29)
    sim["settings"]["seconds"] = None  # timing left out so a rerun is byte-comparable
    json.dump(sim, open(out, "w"), indent=1)
    print(f"simulation.json written in {time.time() - t0:.0f} s", file=sys.stderr)


if __name__ == "__main__":
    main()
