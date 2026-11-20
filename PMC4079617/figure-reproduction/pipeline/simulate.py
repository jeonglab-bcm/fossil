"""Run the simulation study of Chen et al. (2014) with the package robustrr, and its hypothesis variants.

Usage: simulate.py OUT_JSON [--jobs N] [--reps R]

Runs (each 24 scenarios x 3 contamination rates x R = 1,000 replicates, both models):
  main     n = 1500 and n = 500, the reading of the Methods in robustrr.simulation (records whose true p_y is
           beyond the population's rate/2 and 1 - rate/2 quantiles flipped, Z^2 fitted for the quadratic
           confounder)
  second   the same with other seeds: how far two runs of one design fall apart
Variants (n = 1500, the main run's seeds, so they differ from it only in the reading):
  sample   exactly ceil(n rate/2) records per tail in every data set, ranked by p_y within it (15 and 38)
  sample500  the same at n = 500 (5 and 13 per tail)
  floor    the same with floor(n rate/2) records per tail (37 instead of 38 at 5%)
  bottom   the whole rate flipped at the bottom of p_y (population cut-off)
  top      the whole rate flipped at the top of p_y (population cut-off)
  fitted   a fixed number per data set ranked by p_y fitted by the uncontaminated log-binomial model
  noquad   Z^2 left out of the fitted models (quadratic-confounder scenarios)
Each cell keeps the summaries of both models (relative bias, SE, MSE and their Monte Carlo SEs), the paired
LB - RP difference in relative bias with its Monte Carlo SE, and how often COPY was used.
"""
import json
import math
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np

import robustrr as rr

SEEDS = {"main": 20140626, "second": 82}
VARIANTS = {
    "sample": {"cutoffs": "sample", "rates": (0.02, 0.05)},
    "sample500": {"cutoffs": "sample", "rates": (0.02, 0.05), "n": 500},
    "floor": {"cutoffs": "sample", "count": "floor", "rates": (0.05,)},
    "bottom": {"tails": "bottom", "rates": (0.02, 0.05)},
    "top": {"tails": "top", "rates": (0.02, 0.05)},
    "fitted": {"cutoffs": "sample", "rank_by": "fitted", "rates": (0.02, 0.05)},
    "noquad": {"quadratic": False, "rates": (0.0, 0.02, 0.05), "forms": ("nonlinear",)},
}


def key_str(k):
    rr_, py, form, lev = k
    return f"{rr_:.1f}|{py}%|{form}|{lev}"


def r4(x):
    return round(float(x), 6)


def cell(s, d):
    lb, rp = rr.summarize(d["lb"], s["beta1"]), rr.summarize(d["rp"], s["beta1"])
    diff = (d["lb"] - d["rp"]) * 100 / s["beta1"]
    return {"LB": {k: r4(v) for k, v in lb.items()}, "RP": {k: r4(v) for k, v in rp.items()},
            "diff_relbias": r4(diff.mean()), "diff_relbias_mcse": r4(diff.std(ddof=1) / math.sqrt(diff.size)),
            "flipped_mean": r4(d["flipped"].mean()), "flipped_sd": r4(d["flipped"].std(ddof=1)),
            "copy_used": int(d["copy"].sum()), "lb_converged": int(d["converged"].sum()), "reps": int(d["lb"].size)}


def job(args):
    run, n, idx, key, opts, reps = args
    s = rr.scenario(*key)
    rates = opts.pop("rates", rr.CONTAMINATION)
    opts.pop("forms", None)
    opts.pop("n", None)
    seed = [SEEDS["second" if run == "second" else "main"], n, idx]
    res = rr.run_scenario(s, n=n, reps=reps, seed=seed, rates=rates, **opts)
    return run, n, key_str(key), {f"{int(round(100 * r))}%": cell(s, d) for r, d in res.items()}


def main():
    args = sys.argv[1:]
    jobs = os.cpu_count() or 1
    reps = 1000
    if "--jobs" in args:
        i = args.index("--jobs"); jobs = int(args[i + 1]); del args[i:i + 2]
    if "--reps" in args:
        i = args.index("--reps"); reps = int(args[i + 1]); del args[i:i + 2]
    out, = args
    tasks = []
    for run in ("main", "second"):
        for n in (1500, 500):
            for i, k in enumerate(rr.SCENARIOS):
                tasks.append((run, n, i, k, {}, reps))
    for name, v in VARIANTS.items():
        for i, k in enumerate(rr.SCENARIOS):
            if k[2] in v.get("forms", ("linear", "nonlinear")):
                tasks.append((name, v.get("n", 1500), i, k, {kk: vv for kk, vv in v.items()}, reps))
    t0 = time.time()
    runs = {}
    with ProcessPoolExecutor(max_workers=jobs) as ex:
        for run, n, key, cells in ex.map(job, tasks):
            runs.setdefault(run, {}).setdefault(f"n{n}", {})[key] = cells
    doc = {"about": __doc__.strip().splitlines()[0], "reps": reps, "seeds": SEEDS,
           "robustrr": rr.__version__, "copies": rr.DEFAULT_COPIES,
           "flipped_per_tail_sample": {f"n{n}": {f"{int(100 * r)}%": rr.simulation.n_flipped(n, r) for r in (0.02, 0.05)}
                                       for n in (1500, 500)},
           "population_cutoffs": {key_str(k): {f"{int(100 * r)}%": [round(c, 6) for c in rr.population_cutoffs(rr.scenario(*k), r)]
                                               for r in (0.02, 0.05)} for k in rr.SCENARIOS},
           "variants": {k: {kk: vv for kk, vv in v.items() if kk not in ("rates", "forms", "n")} for k, v in VARIANTS.items()},
           "runs": {r: {nn: dict(sorted(v.items(), key=lambda kv: [key_str(k) for k in rr.SCENARIOS].index(kv[0])))
                        for nn, v in d.items()} for r, d in runs.items()}}
    with open(out, "w") as f:
        json.dump(doc, f, indent=1)
        f.write("\n")
    print(f"{out}: {len(tasks)} scenario runs in {time.time() - t0:.0f} s on {jobs} processes", file=sys.stderr)


if __name__ == "__main__":
    main()
