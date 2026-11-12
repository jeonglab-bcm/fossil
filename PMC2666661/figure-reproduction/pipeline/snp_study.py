"""SNP simulation of Meng et al. (2009), Figures 1-3: H4M4 model, K4S4 design, 13 LD models
(Table 5), 100 replicates of 250 cases and 250 controls, RF0 and RF1 with 5000 trees, mtry 35.

  snp_study.py run OUTDIR --ld-model r1 --reps 0-99 [--R 0.5 ...] [--ntree 5000]
  snp_study.py merge OUTDIR MERGED.json

`run` writes one JSON per replicate (OUTDIR/<ld>/<rep>.json) with the column classes and, for RF0
and for RF1 at each threshold R, the importances IM0 and IM1 and T_v of every column. Each
replicate's data and forests have their own seeds, derived from (study, LD model, replicate), so
any subset reruns to the same numbers.
"""

import argparse
import json
import os
import sys
import time

import numpy as np

from rfld.forest import grow_forest, r2_matrix
from rfld.simulate import DESIGNS, LD_MODELS, MODELS, snp_dataset

STUDY = 2666661
LD_ORDER = list(LD_MODELS)


def seeds(ld_model, rep, model="H4M4", ld_data="incremental"):
    """incremental (default): the 13 LD models of a replicate are built on the same n0 data set
    (the same data seed for every LD model), as the paper says it did for the other genetic models
    and as the smooth LD.nSNP series of Figs 1 and 2 suggest it did for H4M4. independent: every
    LD model of H4M4 has its own data sets (the sensitivity variant)."""
    ld_key = LD_ORDER.index(ld_model) if ld_data == "independent" else 99
    ss = np.random.SeedSequence([STUDY, list(MODELS).index(model), ld_key, rep])
    data_seed, forest_seed = ss.generate_state(2)
    return int(data_seed), int(forest_seed % (2**31 - 1))


def run_one(ld_model, rep, Rs, ntree, mtry, model="H4M4", ld_data="incremental"):
    dseed, fseed = seeds(ld_model, rep, model, ld_data)
    rng = np.random.default_rng(dseed)
    X, y, kinds = snp_dataset(rng, MODELS[model], ld_model, design=DESIGNS[model])
    r2 = r2_matrix(X)
    k = DESIGNS[model][0]
    out = {"model": model, "ld_model": ld_model, "ld_data": ld_data, "rep": rep, "data_seed": dseed, "forest_seed": fseed,
           "ntree": ntree, "mtry": mtry, "kinds": [k for k, _ in kinds], "partner": [p for _, p in kinds],
           "max_offdiag_r2_noise": float(np.max(np.triu(r2[k:100, k:100], 1))), "forests": {}}
    f = grow_forest(X, y, ntree=ntree, mtry=mtry, seed=fseed)
    out["forests"]["RF0"] = _pack(f)
    for R in Rs:
        f = grow_forest(X, y, ntree=ntree, mtry=mtry, seed=fseed, revised_tree=True, ld_threshold=R, r2=r2)
        out["forests"][f"RF1_R{R:g}"] = _pack(f)
    return out


def _pack(f):
    return {"im0": [round(float(v), 10) for v in f["im0"]],
            "im1": [round(float(v), 10) for v in f["im1"]],
            "trees": [int(v) for v in f["trees"]], "oob_error": f["oob_error"]}


def parse_reps(s):
    out = []
    for part in s.split(","):
        if "-" in part:
            a, b = part.split("-")
            out.extend(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return out


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("outdir")
    r.add_argument("--ld-model", required=True, choices=LD_ORDER)
    r.add_argument("--reps", default="0-99")
    r.add_argument("--R", type=float, nargs="*", default=[0.5])
    r.add_argument("--ntree", type=int, default=5000)
    r.add_argument("--mtry", type=int, default=35)
    r.add_argument("--model", default="H4M4", choices=list(MODELS))
    r.add_argument("--ld-data", default="incremental", choices=["incremental", "independent"])
    m = sub.add_parser("merge")
    m.add_argument("outdir")
    m.add_argument("merged")
    m.add_argument("--model", default="H4M4", choices=list(MODELS))
    a = ap.parse_args()
    if a.cmd == "run":
        d = os.path.join(a.outdir, a.ld_model) if a.model == "H4M4" else os.path.join(a.outdir, a.model, a.ld_model)
        os.makedirs(d, exist_ok=True)
        for rep in parse_reps(a.reps):
            path = os.path.join(d, f"{rep:03d}.json")
            if os.path.exists(path):
                continue
            t = time.time()
            res = run_one(a.ld_model, rep, a.R, a.ntree, a.mtry, a.model, a.ld_data)
            with open(path + ".tmp", "w") as fh:
                json.dump(res, fh)
            os.replace(path + ".tmp", path)
            print(f"{a.ld_model} {rep} {time.time() - t:.1f}s", flush=True)
    else:
        merged = {}
        for ld in LD_ORDER:
            d = os.path.join(a.outdir, ld) if a.model == "H4M4" else os.path.join(a.outdir, a.model, ld)
            if not os.path.isdir(d):
                continue
            reps = sorted(f for f in os.listdir(d) if f.endswith(".json"))
            merged[ld] = [json.load(open(os.path.join(d, f))) for f in reps]
        json.dump(merged, open(a.merged, "w"))
        print({k: len(v) for k, v in merged.items()}, file=sys.stderr)


if __name__ == "__main__":
    main()
