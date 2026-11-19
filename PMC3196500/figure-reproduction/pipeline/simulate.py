"""Run the paper's 36 simulation scenarios (Fig. 1) with the package oisim and store their curves.

Usage: simulate.py OUT.json [--n-meta N] [--workers W]

For each scenario (and each hypothesis variant) the output keeps, per binning rule, axis (cumulative
patients up to 50,000, cumulative events up to 5,000) and point spacing (100, 200, 500 patients; 10, 20, 50
events), the number of pooled estimates at each point and the number above RRR 30% and 20%, so the tables
and figures steps can try every binning rule, spacing and read-off rule without simulating again. The
replicate and the variants keep the 'nearest' and 'interval' rules only.

Runs:
  main          36 scenarios, 20,000 meta-analyses of 100 trials, our settings (0.5 correction for
                trials with a zero cell, trials with no events in either arm left out, binomial on the arm size)
  replicate     the same 36 with other seeds: how far chance alone moves a read-off
  correct_all   12 Cochrane-size scenarios, double-zero trials kept with the 0.5 correction
  binomial_total 12 Cochrane-size scenarios, events drawn as Binomial(n, P) on the whole trial size
"""
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np

import oisim
from oisim.core import BIN_RULES, Scenario, overestimation_curve, simulate

ENTROPY = 3196500
WIDTHS = {"patients": (100, 200, 500), "events": (10, 20, 50)}
CAPS = {"patients": 50000, "events": 5000}
THRESHOLDS = (0.30, 0.20)


def scenarios():
    """The 36 scenarios in the order of Tables 1, S4 and S3 (Fig. 1)."""
    out = []
    for sizes, pcs in (("cochrane", ("1-5", "5-15")), ("common", ("1-5", "5-15", "15-40", "40-80"))):
        for rrr in (0.0, 0.10):
            for pc in pcs:
                for tau2 in (0.05, 0.15, 0.25):
                    out.append(Scenario(sizes, pc, tau2, rrr))
    return out


def run_one(job):
    idx, sc, variant, n_meta = job
    sc = Scenario(sc.sizes, sc.pc, sc.tau2, sc.rrr, n_meta=n_meta)
    stream = {"main": 0, "replicate": 1, "correct_all": 0, "binomial_total": 2}[variant]
    seed = np.random.SeedSequence(ENTROPY, spawn_key=(stream, idx))
    kw = {"zero": "correct_all"} if variant == "correct_all" else {}
    if variant == "binomial_total":
        kw["binomial_n"] = "total"
    t0 = time.time()
    sim = simulate(sc, seed=seed, **kw)
    rrr = sim.rrr()
    res = {"key": sc.key, "variant": variant, "sizes": sc.sizes, "pc": sc.pc, "tau2": sc.tau2, "rrr": sc.rrr,
           "n_meta": sc.n_meta, "n_trials": sc.n_trials,
           "no_estimate_share": float(np.isnan(sim.log_rr).mean()),
           "mean_total_patients": float(sim.cum_patients[:, -1].mean()),
           "mean_total_events": float(sim.cum_events[:, -1].mean()),
           "curves": {}}
    rules = BIN_RULES if variant == "main" else ("nearest", "interval")
    for rule in rules:
        res["curves"][rule] = {}
        for axis, cum in (("patients", sim.cum_patients), ("events", sim.cum_events)):
            res["curves"][rule][axis] = {}
            for w in WIDTHS[axis]:
                c = {}
                for th in THRESHOLDS:
                    cur = overestimation_curve(cum, rrr, th, w, CAPS[axis], rule=rule)
                    c["n"] = cur["n"].astype(int).tolist()
                    c[f"over{int(th * 100)}"] = cur["hits"].tolist()
                last = max((i for i, v in enumerate(c["n"]) if v > 0), default=-1) + 1
                res["curves"][rule][axis][str(w)] = {k: v[:last] for k, v in c.items()}
    res["seconds"] = round(time.time() - t0, 1)
    return res


def main():
    args = sys.argv[1:]
    n_meta, workers = 20000, 4
    if "--n-meta" in args:
        i = args.index("--n-meta"); n_meta = int(args[i + 1]); del args[i:i + 2]
    if "--workers" in args:
        i = args.index("--workers"); workers = int(args[i + 1]); del args[i:i + 2]
    out = args[0]
    scs = scenarios()
    jobs = [(i, s, "main", n_meta) for i, s in enumerate(scs)]
    jobs += [(i, s, "replicate", n_meta) for i, s in enumerate(scs)]
    jobs += [(i, s, v, n_meta) for v in ("correct_all", "binomial_total") for i, s in enumerate(scs) if s.sizes == "cochrane"]
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=workers) as ex:
        runs = list(ex.map(run_one, jobs))
    doc = {"oisim": oisim.__version__, "entropy": ENTROPY, "widths": WIDTHS, "caps": CAPS, "n_meta": n_meta, "n_trials": 100,
           "runs": {}}
    for r in runs:
        doc["runs"].setdefault(r["variant"], {})[r["key"]] = r
    # Timings depend on the machine; keep them out of the committed file.
    for v in doc["runs"].values():
        for r in v.values():
            r.pop("seconds")
    with open(out, "w") as f:
        json.dump(doc, f, separators=(",", ":"))
        f.write("\n")
    print(f"{len(runs)} simulations in {time.time() - t0:.0f} s", file=sys.stderr)


if __name__ == "__main__":
    main()
