"""Convergence diagnostics for the MCMC: R-hat, effective sample size (ESS),
transmission-tree stability across chains, trace plots, and the pooled posterior.

Reads several per-chain posterior JSONs (written by analyze.py with different
seeds), each holding thinned samples of the continuous parameters and the
per-chain transmission-probability matrix and most-likely tree. Writes:

* ``<id>_diagnostics.json`` : per-parameter R-hat and ESS, and tree-stability
  measures (agreement of the most-likely tree across chains, the largest
  disagreement in posterior transmission probabilities, and the stability of the
  paper's headline structural claim);
* ``<id>_trace.png``        : trace and running-median plots of the parameters;
* ``<id>_pooled.json``      : the posterior pooled over all chains, in the same
  shape analyze.py writes, used for the committed figures and the reported medians.

R-hat is the split-chain Gelman-Rubin statistic; ESS is the autocorrelation-based
bulk effective sample size (Vehtari et al. 2021), computed with numpy only.
"""

from __future__ import annotations

import argparse
import json

import numpy as np

PARAMS = ["mean_latency", "mean_distance", "alpha1", "alpha2", "beta1", "beta2"]
PARAM_LABELS = {
    "mean_latency": "mean latency duration (days)",
    "mean_distance": "mean transmission distance (km)",
    "alpha1": "source strength alpha1",
    "alpha2": "dispersion alpha2",
    "beta1": "latency mean beta1",
    "beta2": "latency sd beta2",
}


def _split(chains):
    """Split each chain in half (split-R-hat), truncating to a common length."""
    n = min(len(c) for c in chains)
    n = (n // 2) * 2
    half = n // 2
    out = []
    for c in chains:
        c = np.asarray(c[:n], dtype=float)
        out.append(c[:half]); out.append(c[half:])
    return np.array(out)   # (2M, half)


def rhat(chains):
    """Split-chain Gelman-Rubin R-hat for a list of 1-D chains."""
    x = _split(chains)
    m, n = x.shape
    if n < 2:
        return float("nan")
    chain_means = x.mean(axis=1)
    chain_vars = x.var(axis=1, ddof=1)
    W = chain_vars.mean()
    B = n * chain_means.var(ddof=1)
    if W <= 0:
        return float("nan")
    var_hat = (n - 1) / n * W + B / n
    return float(np.sqrt(var_hat / W))


def _autocorr(x):
    """Normalised autocorrelation of a 1-D series via FFT."""
    x = np.asarray(x, dtype=float) - np.mean(x)
    n = len(x)
    f = np.fft.rfft(x, n=2 * n)
    acf = np.fft.irfft(f * np.conjugate(f))[:n].real
    if acf[0] == 0:
        return np.zeros(n)
    return acf / acf[0]


def ess(chains):
    """Bulk effective sample size (Vehtari et al. 2021), numpy only."""
    x = _split(chains)
    m, n = x.shape
    if n < 4:
        return float("nan")
    # mean autocorrelation across chains, weighted into the combined estimate
    rho_hat = np.zeros(n)
    chain_vars = x.var(axis=1, ddof=1)
    W = chain_vars.mean()
    chain_means = x.mean(axis=1)
    B = n * chain_means.var(ddof=1)
    var_hat = (n - 1) / n * W + B / n
    if var_hat <= 0:
        return float("nan")
    acov = np.array([_autocorr(c) * np.var(c) for c in x])  # per-chain autocov
    mean_acov = acov.mean(axis=0)
    rho = 1.0 - (W - mean_acov) / var_hat
    rho[0] = 1.0
    # Geyer initial monotone sequence: sum paired autocorrelations while positive
    t = 1
    tau = 1.0
    while t + 1 < n:
        p = rho[t] + rho[t + 1]
        if p < 0:
            break
        tau += 2 * p
        t += 2
    if tau < 1:
        tau = 1.0
    return float(m * n / tau)


def tree_stability(posts):
    """Agreement of the most-likely tree and the transmission probabilities
    across chains, plus the paper's headline structural claim."""
    names = posts[0]["names"]
    I = len(names)
    best = [p["best_tree"] for p in posts]
    tps = [np.array(p["trans_prob"]) for p in posts]
    # per-premise agreement of the argmax source across chains
    argmax_src = [np.argmax(tp, axis=1) for tp in tps]
    agree = np.mean([
        np.mean([argmax_src[a][i] == argmax_src[b][i] for i in range(I)])
        for a in range(len(posts)) for b in range(a + 1, len(posts))
    ]) if len(posts) > 1 else 1.0
    max_tp_diff = 0.0
    for a in range(len(posts)):
        for b in range(a + 1, len(posts)):
            max_tp_diff = max(max_tp_diff, float(np.max(np.abs(tps[a] - tps[b]))))
    # headline structural claim
    headline = None
    if "IP5" in names:
        i5 = names.index("IP5")
        phase1 = [names.index(x) for x in ("IP1b", "IP2b") if x in names]
        vals = [float(sum(tp[i5, j] for j in phase1)) for tp in tps]
        headline = {"claim": "IP5 infected from phase 1 (IP1b/IP2b)",
                    "per_chain": [round(v, 3) for v in vals],
                    "min": round(min(vals), 3)}
    elif "K" in names:
        ki = names.index("K")
        from collections import Counter
        hubs = []
        for tp in tps:
            src = np.argmax(tp, axis=1)
            c = Counter(int(s) for s in src if s != I)
            hubs.append(names[max(c, key=c.get)] if c else None)
        headline = {"claim": "K is the hub (max out-degree) in the most-likely tree",
                    "per_chain": hubs,
                    "all_K": all(h == "K" for h in hubs)}
    return {"most_likely_source_agreement": round(float(agree), 3),
            "max_trans_prob_diff": round(max_tp_diff, 3),
            "best_tree_prob_per_chain": [round(p["best_tree_prob"], 3) for p in posts],
            "headline": headline}


def pooled_summary(posts):
    """Pool the chains into one posterior summary, in analyze.py's shape."""
    base = dict(posts[0])
    def pool(key):
        return np.concatenate([np.array(p["samples"][key]) for p in posts])
    def mci(x):
        return dict(median=float(np.median(x)), lo=float(np.quantile(x, 0.025)),
                    hi=float(np.quantile(x, 0.975)), q25=float(np.quantile(x, 0.25)),
                    q75=float(np.quantile(x, 0.75)))
    pooled = {k: pool(k) for k in PARAMS}
    for k in PARAMS:
        base[k] = mci(pooled[k])
    base["samples"] = {k: v.tolist() for k, v in pooled.items()}
    # pool transmission probabilities (weighted equally across chains)
    tps = np.mean([np.array(p["trans_prob"]) for p in posts], axis=0)
    base["trans_prob"] = tps.tolist()
    # most-likely tree = per-premise argmax of the pooled transmission probs
    I = len(base["names"])
    argmax = np.argmax(tps, axis=1)
    base["best_tree"] = [(-1 if int(s) == I else int(s)) for s in argmax]
    # best_tree_prob keeps its single-chain meaning: the posterior probability of
    # the most-likely *labelled* tree, averaged over chains (not cross-chain
    # agreement, which the tree-stability diagnostics report separately). This is
    # the quantity the paper's ">99% of posterior probability" refers to.
    base["best_tree_prob"] = float(np.mean([p["best_tree_prob"] for p in posts]))
    base["n_chains"] = len(posts)
    return base


def trace_plot(posts, out_png, title):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(len(PARAMS), 2, figsize=(10, 1.6 * len(PARAMS)))
    for r, k in enumerate(PARAMS):
        axt, axm = axes[r]
        for p in posts:
            s = np.array(p["samples"][k])
            axt.plot(s, lw=0.4, alpha=0.7)
            run_med = np.array([np.median(s[: i + 1]) for i in
                                np.linspace(10, len(s) - 1, 100).astype(int)])
            axm.plot(np.linspace(10, len(s) - 1, 100), run_med, lw=0.9)
        axt.set_ylabel(k, fontsize=7); axt.tick_params(labelsize=6)
        axm.tick_params(labelsize=6)
        if r == 0:
            axt.set_title("traces (thinned samples)", fontsize=8)
            axm.set_title("running median", fontsize=8)
    fig.suptitle(title, fontsize=9)
    fig.tight_layout(rect=[0, 0, 1, 0.98])
    fig.savefig(out_png, dpi=110)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("chains", nargs="+", help="per-chain posterior JSON files")
    ap.add_argument("--label", required=True)
    ap.add_argument("--out-diag", required=True)
    ap.add_argument("--out-trace", required=True)
    ap.add_argument("--out-pooled", required=True)
    args = ap.parse_args()
    posts = [json.load(open(c)) for c in args.chains]
    diag = {
        "label": args.label,
        "n_chains": len(posts),
        "iters_per_chain": posts[0].get("config", {}).get("iters"),
        "seeds": [p.get("config", {}).get("seed") for p in posts],
        "rhat": {k: round(rhat([p["samples"][k] for p in posts]), 4) for k in PARAMS},
        "ess": {k: round(ess([p["samples"][k] for p in posts]), 1) for k in PARAMS},
        "tree_stability": tree_stability(posts),
        "param_labels": PARAM_LABELS,
    }
    diag["converged"] = all(
        (diag["rhat"][k] < 1.05 and diag["ess"][k] > 200) for k in PARAMS
        if not np.isnan(diag["rhat"][k]))
    json.dump(diag, open(args.out_diag, "w"), indent=1)
    trace_plot(posts, args.out_trace, f"{args.label}: MCMC traces and running medians")
    json.dump(pooled_summary(posts), open(args.out_pooled, "w"), indent=1)
    print(f"{args.label}: R-hat " +
          " ".join(f"{k}={diag['rhat'][k]}" for k in PARAMS))
    print(f"{args.label}: ESS  " +
          " ".join(f"{k}={diag['ess'][k]:.0f}" for k in PARAMS))
    print(f"{args.label}: tree {diag['tree_stability']['most_likely_source_agreement']} agree, "
          f"max tp diff {diag['tree_stability']['max_trans_prob_diff']}; "
          f"converged={diag['converged']}")


if __name__ == "__main__":
    main()
