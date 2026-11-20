"""Run a multi-chain convergence study for one dataset and write the pooled
posterior plus convergence diagnostics.

Runs ``n_chains`` independent chains (seeds 1..n) at ``iters`` iterations, in
parallel processes, then calls diagnostics.py to compute R-hat, ESS, tree
stability, a trace plot, and the pooled posterior. The pooled posterior is what
the committed figures and reported medians are built from; the diagnostics back
the claim that the inference has converged.

    converge.py y2007 --sources DIR --iters 100000 --n-chains 4 --out-dir DIR
    converge.py test  --iters 100000 --n-chains 4 --out-dir DIR

The pooled posterior's sample arrays are thinned to keep the committed file small.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
LABELS = {"y2007": "Fig. 3 (2007 outbreak)", "y2001": "Fig. 4 (2001 Darlington cluster)",
          "test": "Fig. 2 (simulated outbreak)"}


def run_chain(dataset, sources, iters, seed, out, sim_seed=0, n=20):
    cmd = [sys.executable, os.path.join(HERE, "analyze.py"), dataset,
           "--iters", str(iters), "--seed", str(seed), "--out", out]
    if dataset == "test":
        cmd += ["--sim-seed", str(sim_seed), "--n", str(n)]
    else:
        cmd += ["--sources", sources]
    return subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT,
                            env={**os.environ, "OMP_NUM_THREADS": "1"})


def thin_pooled(path, keep=4000):
    """Thin the pooled sample arrays in place to keep the committed file small."""
    d = json.load(open(path))
    for k, v in d.get("samples", {}).items():
        v = np.asarray(v)
        if len(v) > keep:
            step = len(v) // keep
            d["samples"][k] = v[::step][:keep].tolist()
    # drop the large per-premise arrays not needed downstream
    json.dump(d, open(path, "w"), indent=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dataset", choices=["y2007", "y2001", "test"])
    ap.add_argument("--sources", default=None)
    ap.add_argument("--iters", type=int, default=100000)
    ap.add_argument("--n-chains", type=int, default=4)
    ap.add_argument("--sim-seed", type=int, default=0)
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)

    import tempfile
    tmp = tempfile.mkdtemp(prefix="transtree_chains_")
    procs, chain_files = [], []
    for seed in range(1, args.n_chains + 1):
        cf = os.path.join(tmp, f"{args.dataset}_chain{seed}.json")
        chain_files.append(cf)
        procs.append(run_chain(args.dataset, args.sources, args.iters, seed, cf,
                               args.sim_seed, args.n))
    for p in procs:
        if p.wait() != 0:
            raise RuntimeError("a chain failed")

    diag = os.path.join(args.out_dir, f"{args.dataset}_diagnostics.json")
    trace = os.path.join(args.out_dir, f"{args.dataset}_trace.png")
    pooled = os.path.join(args.out_dir, f"{args.dataset}_converged.json")
    subprocess.run([sys.executable, os.path.join(HERE, "diagnostics.py"), *chain_files,
                    "--label", f"{LABELS[args.dataset]}, {args.n_chains} chains x {args.iters}",
                    "--out-diag", diag, "--out-trace", trace, "--out-pooled", pooled],
                   check=True)
    thin_pooled(pooled)
    print(f"wrote {pooled}, {diag}, {trace}")


if __name__ == "__main__":
    main()
