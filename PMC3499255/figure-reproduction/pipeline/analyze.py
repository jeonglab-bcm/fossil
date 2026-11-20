"""Run the MCMC on one dataset and write a JSON summary of the posterior.

Usage:
    analyze.py y2007 --sources DIR --iters 100000 --seed 1 --out out/y2007.json
    analyze.py y2001 --sources DIR --iters 100000 --seed 1 --out out/y2001.json
    analyze.py test  --seed 0      --iters  40000 --seed 1 --out out/test.json
"""

from __future__ import annotations

import argparse
import json

import numpy as np

from transtree.core import MCMCConfig, run_mcmc
import datasets as D


def summarize(post, data, truth=None) -> dict:
    def mci(x):
        return dict(median=float(np.median(x)),
                    lo=float(np.quantile(x, 0.025)),
                    hi=float(np.quantile(x, 0.975)),
                    q25=float(np.quantile(x, 0.25)),
                    q75=float(np.quantile(x, 0.75)))

    # thin parameter samples for histograms (cap size)
    def thin(x, k=3000):
        x = np.asarray(x)
        if len(x) <= k:
            return x.tolist()
        step = len(x) // k
        return x[::step][:k].tolist()

    out = dict(
        names=list(data.names),
        trans_prob=post.trans_prob.tolist(),
        best_tree=[int(s) for s in post.best_tree],
        best_tree_prob=float(post.best_tree_prob),
        n_samples=int(post.n_samples),
        accept={k: float(v) for k, v in post.accept.items()},
        mean_latency=mci(post.mean_latency),
        mean_distance=mci(post.mean_distance),
        alpha1=mci(post.alpha1), alpha2=mci(post.alpha2),
        beta1=mci(post.beta1), beta2=mci(post.beta2),
        samples=dict(
            mean_latency=thin(post.mean_latency),
            mean_distance=thin(post.mean_distance),
            alpha1=thin(post.alpha1), alpha2=thin(post.alpha2),
            beta1=thin(post.beta1), beta2=thin(post.beta2),
        ),
        infection_time_median=np.median(post.infection_times, axis=0).tolist(),
        latency_median_per_premise=np.median(
            post.infectiousness_times - post.infection_times, axis=0).tolist(),
        X=data.X.tolist(),
        Tobs=data.Tobs.tolist(), Tend=data.Tend.tolist(), Dobs=data.Dobs.tolist(),
        s=data.s, m=data.m,
    )
    if truth is not None:
        out["truth"] = dict(
            J=[int(x) for x in truth["J"]],
            alpha=[float(x) for x in truth["alpha"]],
            beta=[float(x) for x in truth["beta"]],
            mean_latency=float(truth["beta"][0]),
            mean_distance=float(2.0 * truth["alpha"][1]),
        )
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dataset", choices=["y2007", "y2001", "test"])
    ap.add_argument("--sources", default=None)
    ap.add_argument("--iters", type=int, default=100000)
    ap.add_argument("--burn", type=float, default=0.4)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--sim-seed", type=int, default=0, help="seed for the test simulation")
    ap.add_argument("--n", type=int, default=20, help="premises for the test simulation")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    truth = None
    if args.dataset == "test":
        data, truth = D.load_test(seed=args.sim_seed, n=args.n)
    else:
        data = D.load_real(args.sources, args.dataset)

    post = run_mcmc(data, MCMCConfig(iters=args.iters, burn_in_frac=args.burn, seed=args.seed))
    out = summarize(post, data, truth)
    out["config"] = dict(iters=args.iters, burn=args.burn, seed=args.seed,
                         dataset=args.dataset, sim_seed=args.sim_seed, n=args.n)
    with open(args.out, "w") as fh:
        json.dump(out, fh, indent=1)
    print(f"{args.dataset}: lat {out['mean_latency']['median']:.1f} "
          f"({out['mean_latency']['lo']:.0f},{out['mean_latency']['hi']:.0f}) "
          f"dist {out['mean_distance']['median']:.1f} "
          f"({out['mean_distance']['lo']:.0f},{out['mean_distance']['hi']:.0f}) "
          f"best_tree_p={out['best_tree_prob']:.2f} -> {args.out}")


if __name__ == "__main__":
    main()
