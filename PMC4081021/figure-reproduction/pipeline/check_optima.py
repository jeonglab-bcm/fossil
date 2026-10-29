"""Check that each saved optimum is a local maximum of the likelihood: the gradient there (exact,
by automatic differentiation; components at an active bound are excluded) and the gain of a
local L-BFGS-B run started from it."""

import argparse
import json
import multiprocessing as mp
import os
import sys

import numpy as np


def check(args):
    sources, study, model = args
    os.environ.setdefault("XLA_FLAGS", "--xla_cpu_multi_thread_eigen=false "
                          "intra_op_parallelism_threads=1")
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from scipy.optimize import minimize
    from odemm_jax import build
    from saved import load_model, to_D
    spec, m = load_model(sources, study, model)
    p = m["parameters"]
    lo, hi = np.asarray(p.min, float), np.asarray(p.max, float)
    xi = np.clip(np.asarray(p.MS.MAP.par, float), lo, hi)
    _, g = build(spec, to_D(m["D"]))
    v, gr = g(xi)
    gr = np.asarray(gr, float)
    free = ~(((xi <= lo + 1e-6) & (gr < 0)) | ((xi >= hi - 1e-6) & (gr > 0)))

    def fun(x):
        a, b = g(x)
        a = float(a)
        return (1e20, np.zeros_like(x)) if not np.isfinite(a) else (-a, -np.asarray(b, float))
    r = minimize(fun, xi, jac=True, method="L-BFGS-B", bounds=list(zip(lo, hi)),
                 options={"maxiter": 2000, "ftol": 1e-15, "gtol": 1e-8})
    return {"study": study, "model": model, "saved_logL": float(p.MS.MAP.logPost),
            "logL_at_saved": float(v), "max_abs_grad_free": float(np.abs(gr[free]).max()),
            "n_at_bound": int((~free).sum()), "local_logL": -float(r.fun),
            "local_gain": -float(r.fun) - float(v), "local_shift": float(np.abs(r.x - xi).max())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from saved import STUDIES, model_list
    jobs = [(a.sources, s, m) for s in STUDIES for m in model_list(s)]
    with mp.get_context("spawn").Pool(a.workers) as pool:
        res = pool.map(check, jobs, chunksize=1)
    json.dump(res, open(a.out, "w"), indent=1)
    for r in res:
        print(f"{r['study']:5s} {r['model']:20s} |grad| {r['max_abs_grad_free']:9.2e}  "
              f"local gain {r['local_gain']:9.2e}")


if __name__ == "__main__":
    main()
