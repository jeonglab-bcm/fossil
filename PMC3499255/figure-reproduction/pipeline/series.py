"""Performance over a series of simulations: Table 1 and Table S1.

For each of the three series (test, 2007, 2001) the paper simulated 100 outbreaks
from the model and, for each, ran the inference and measured

  Table 1  : the fraction of pairwise transmissions whose highest-posterior source
             equals the true source, and the mean posterior probability assigned
             to the true source;
  Table S1 : the fraction of true values of six quantities (infection times,
             infectiousness times, source strength alpha1, dispersion 2*alpha2,
             latency mean beta1, latency sd beta2) falling inside their 95%
             posterior intervals.

Each series uses its own premise count and generating parameters: the test series
uses the simulation parameters alpha=(80,10), beta=(5,1); the 2007 and 2001 series
use the posterior medians estimated from the real data (passed in).

This is a scaled-down run (fewer simulations and shorter chains than the paper's
100 x 5e5); the counts are recorded as deviations. Monte Carlo spread is reported
as the standard deviation across simulations, as in the paper.
"""

from __future__ import annotations

import argparse
import json

import numpy as np

from transtree.core import MCMCConfig, run_mcmc, simulate_outbreak
import datasets as D


SERIES = {
    "test": dict(n=20, alpha=(80.0, 10.0), beta=(5.0, 1.0), domain=(22.0, 11.0), real=None),
    "y2007": dict(n=9, domain=(15.0, 20.0), real="y2007"),
    "y2001": dict(n=12, domain=(24.0, 16.0), real="y2001"),
}


def _coverage(samples_lo_hi, true_val):
    lo, hi = samples_lo_hi
    return 1.0 if lo <= true_val <= hi else 0.0


def run_series(name, n_sims, iters, seed0, params, fixed_X=None):
    n = params["n"]
    alpha = params["alpha"]
    beta = params["beta"]
    domain = params["domain"]
    s, m = D.SIM_S, D.SIM_M
    frac_correct = []
    mean_post_true = []
    cov = {k: [] for k in ["infection_times", "infectiousness_times", "source_strength",
                           "dispersion", "latency_mean", "latency_sd"]}
    done = 0
    for k in range(n_sims):
        try:
            data, truth = simulate_outbreak(n, alpha, beta, s, m, domain=domain,
                                            seed=seed0 + k, fixed_X=fixed_X)
        except RuntimeError:
            continue
        post = run_mcmc(data, MCMCConfig(iters=iters, burn_in_frac=0.4, seed=1000 + k))
        I = data.I
        tp = post.trans_prob
        # pairwise transmission accuracy: for each premise, argmax source vs true
        correct = 0
        ptrue = []
        for i in range(I):
            ts = truth["J"][i]
            col = I if ts == -1 else ts
            pred = int(np.argmax(tp[i]))
            if pred == col:
                correct += 1
            ptrue.append(tp[i, col])
        frac_correct.append(correct / I)
        mean_post_true.append(float(np.mean(ptrue)))
        # Table S1 coverages
        inf_t = post.infection_times                      # (nsamp, I)
        lo = np.quantile(inf_t, 0.025, axis=0); hi = np.quantile(inf_t, 0.975, axis=0)
        cov["infection_times"].append(np.mean([(lo[i] <= truth["Tinf"][i] <= hi[i]) for i in range(I)]))
        infc = post.infectiousness_times                  # (nsamp, I) = Tinf + L
        clo = np.quantile(infc, 0.025, axis=0); chi = np.quantile(infc, 0.975, axis=0)
        true_infc = truth["Tinf"] + truth["L"]
        cov["infectiousness_times"].append(np.mean([(clo[i] <= true_infc[i] <= chi[i]) for i in range(I)]))
        cov["source_strength"].append(_coverage((np.quantile(post.alpha1, 0.025), np.quantile(post.alpha1, 0.975)), alpha[0]))
        cov["dispersion"].append(_coverage((np.quantile(post.mean_distance, 0.025), np.quantile(post.mean_distance, 0.975)), 2 * alpha[1]))
        cov["latency_mean"].append(_coverage((np.quantile(post.beta1, 0.025), np.quantile(post.beta1, 0.975)), beta[0]))
        cov["latency_sd"].append(_coverage((np.quantile(post.beta2, 0.025), np.quantile(post.beta2, 0.975)), beta[1]))
        done += 1
    return dict(
        series=name, n_sims=done, iters=iters, n_premises=n,
        frac_correct_mean=float(np.mean(frac_correct)), frac_correct_sd=float(np.std(frac_correct)),
        mean_post_true_mean=float(np.mean(mean_post_true)), mean_post_true_sd=float(np.std(mean_post_true)),
        coverage={k: float(np.mean(v)) for k, v in cov.items()},
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-sims", type=int, default=30)
    ap.add_argument("--iters", type=int, default=6000)
    ap.add_argument("--seed0", type=int, default=0)
    ap.add_argument("--medians", help="JSON mapping y2007/y2001 to their posterior medians")
    ap.add_argument("--out", required=True)
    ap.add_argument("--only", default=None, help="run only this series")
    ap.add_argument("--sources", default=None, help="sources dir, to reuse real premise layouts")
    args = ap.parse_args()

    params = {k: dict(v) for k, v in SERIES.items()}
    if args.medians:
        med = json.load(open(args.medians))
        for key in ("y2007", "y2001"):
            if key in med:
                params[key]["alpha"] = (med[key]["alpha1"], med[key]["alpha2"])
                params[key]["beta"] = (med[key]["beta1"], med[key]["beta2"])
    results = {}
    names = [args.only] if args.only else ["test", "y2007", "y2001"]
    for name in names:
        fixed_X = None
        if params[name].get("real") and args.sources:
            fixed_X = D.load_real(args.sources, params[name]["real"]).X
        results[name] = run_series(name, args.n_sims, args.iters, args.seed0, params[name], fixed_X)
        print(results[name])
    with open(args.out, "w") as fh:
        json.dump(results, fh, indent=1)


if __name__ == "__main__":
    main()
