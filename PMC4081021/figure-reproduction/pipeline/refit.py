"""Independent multi-start refit of one ODE-MM, as in the authors' optimizeMultiStart.m:
Latin hypercube starts inside the parameter bounds, a local gradient-based optimiser from each.
fmincon (interior point) is replaced by L-BFGS-B with the same bounds; bounds and number of
starts are taken from the authors' saved run (parameters.min/max, options_MS.n_starts)."""

import argparse
import json
import multiprocessing as mp
import os
import sys
import time
from collections import Counter

import numpy as np
from scipy.optimize import minimize
from scipy.stats import qmc

_F = None


def _init(sources, study, model):
    os.environ.setdefault("XLA_FLAGS", "--xla_cpu_multi_thread_eigen=false "
                          "intra_op_parallelism_threads=1")
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    global _F
    from odemm_jax import build
    from saved import load_model, to_D
    spec, m = load_model(sources, study, model)
    _, g = build(spec, to_D(m["D"]))
    _F = g


def _fun(x):
    v, gr = _F(x)
    v = float(v)
    if not np.isfinite(v):
        return 1e20, np.zeros_like(x)
    return -v, -np.asarray(gr, float)


def _run(args):
    i, x0, lo, hi = args
    t = time.time()
    v0, _ = _fun(x0)
    if v0 >= 1e20:
        return {"start": i, "logL": None, "status": "infeasible start", "sec": time.time() - t}
    r = minimize(_fun, x0, jac=True, method="L-BFGS-B", bounds=list(zip(lo, hi)),
                 options={"maxiter": 3000, "maxfun": 6000, "ftol": 1e-15, "gtol": 1e-8})
    return {"start": i, "logL": -float(r.fun) if r.fun < 1e20 else None, "xi": r.x.tolist(),
            "nit": int(r.nit), "status": str(r.message), "sec": time.time() - t}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources", required=True)
    ap.add_argument("--study", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--starts", type=int, default=None, help="default: the authors' n_starts")
    ap.add_argument("--workers", type=int, default=max(1, os.cpu_count() - 1))
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--until-repeats", type=int, default=0,
                    help="Supporting Information S1: if the best value was not found this many "
                         "times, add starts (batches of the initial size) up to --max-starts")
    ap.add_argument("--max-starts", type=int, default=0)
    ap.add_argument("--resume", action="store_true", help="add to the runs already in --out")
    args = ap.parse_args()

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from saved import load_model, to_D
    from odemm import bic
    spec, m = load_model(args.sources, args.study, args.model)
    p = m["parameters"]
    lo, hi = np.asarray(p.min, float), np.asarray(p.max, float)
    n_authors = int(m["options_MS"].n_starts)
    n = args.starts or n_authors
    runs, wall = [], 0.0
    if args.resume and os.path.exists(args.out):
        prev = json.load(open(args.out))
        runs = [{"logL": v, "status": "previous run"} for v in prev["runs_logL"]]
        wall = prev["wall_sec"]

    def repeats(rs):
        ok = [r for r in rs if r["logL"] is not None]
        if not ok:
            return 0
        b = max(r["logL"] for r in ok)
        return sum(1 for r in ok if r["logL"] > b - 1e-2)

    t0 = time.time()
    ctx = mp.get_context("spawn")
    with ctx.Pool(args.workers, initializer=_init,
                  initargs=(args.sources, args.study, args.model)) as pool:
        batch = 0 if not runs else len(runs) // n
        while not runs or (args.until_repeats and repeats(runs) < args.until_repeats
                           and len(runs) < max(args.max_starts, n)):
            X0 = lo + (hi - lo) * qmc.LatinHypercube(d=len(lo), seed=args.seed + batch).random(n)
            start = len(runs)
            runs += pool.map(_run, [(start + i, X0[i], lo, hi) for i in range(n)], chunksize=1)
            batch += 1
    ok = [r for r in runs if r["logL"] is not None]
    best = max(ok, key=lambda r: r["logL"])
    D = to_D(m["D"])
    out = {"study": args.study, "model": args.model, "n_par": len(lo), "n_starts": len(runs),
           "n_starts_authors": n_authors, "seed": args.seed, "optimizer": "L-BFGS-B",
           "wall_sec": wall + time.time() - t0,
           "best_logL": best["logL"], "best_BIC": float(bic(best["logL"], len(lo), D)),
           "best_xi": best["xi"], "saved_logL": float(p.MS.MAP.logPost),
           "saved_BIC": float(p.MS.MAP.BIC),
           "n_at_best": repeats(runs),
           # every start's final log-likelihood (None: the ODE solve failed at the start point)
           "runs_logL": [None if r["logL"] is None else round(r["logL"], 6) for r in runs],
           "runs_status": dict(Counter(r["status"].split(":")[0] for r in runs))}
    json.dump(out, open(args.out, "w"))
    print(f"{args.study} {args.model}: best {best['logL']:.4f} saved {out['saved_logL']:.4f} "
          f"({out['n_at_best']}/{len(runs)} starts at best, {out['wall_sec']:.0f} s)")


if __name__ == "__main__":
    main()
