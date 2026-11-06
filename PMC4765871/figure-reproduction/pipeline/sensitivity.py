"""One-off hypothesis tests for the causes in results.json (not part of the pipeline).

usage: sensitivity.py RUN_DIR OUT_JSON [--cpus N]

Each test changes one setting the paper does not give and refits; the record is
output/sensitivity.json. Tests:
  ffl_prior_sd_0.0025     FFL OR model with an informative lambda prior ten times tighter
  ffl_scale_100           FFL OR model with pseudo time on [0, 100] (the axis of Fig. 2D)
  ffl_sigma_s_{5,10}      FFL data simulated with more system noise (OR, inverted OR, AND)
  toggle_prior_sd_0.0025  joint gC/gD AND fit with a tighter lambda prior
  genie3_grid             GENIE3 tree method x candidate inputs x normalisation on the qPCR data
"""
import argparse
import json
import os
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))


def ffl_test(args):
    name, spec, prior_sd, scale_kind, sigma_s = args
    import ffl
    import simulate as sim
    if sigma_s is not None:
        sim.PAR["ffl"]["sigma_s"] = sigma_s
    X, ta, ts, T = ffl.data()
    starts, reps = ffl.pseudo_time(X)
    scale = T if scale_kind == "t_stop" else 100.0
    lam = (0.25, prior_sd) if prior_sd else None
    r = ffl._fit((spec, "gZ", lam, 11, X, reps, T, scale))
    return {"test": name, "model": spec, "loglik": r["loglik"], "aic": r["aic"], "map": r["map"],
            "rel_error": ffl.rel_error(r["map"])[0] if spec == "or(gX+,gY-)" else None}


def toggle_test(args):
    import toggle as tg
    import simulate as sim
    name, sd = args
    ds = tg.dataset(None, sim.PAR["toggle"]["seed"], tg.P["sigma"])
    r = tg._fit(("and(A+,D-)", [(ds, "C", ["C", "D"], None), (ds, "D", ["C", "D"], {"D": "C"})],
                 (0.25, sd), 51, False))
    return {"test": name, "mean": r["mean"], "map": r["map"], "rel_error_mean": tg.rel_error(r["mean"])[0],
            "rel_error_map": tg.rel_error(r["map"])[0]}


def genie3_grid(xlsx):
    import haem
    from sklearn.ensemble import ExtraTreesRegressor, RandomForestRegressor
    _, types, CT, _ = haem.load(xlsx)
    E = 20 - CT
    up = [haem.UPPER[g] for g in haem.TFS]
    pub = {tuple(e) for e in json.loads((HERE / "params" / "published_networks.json").read_text())["fig7c_edges"]}
    Z = (E - E.mean(0)) / E.std(0, ddof=1)
    out = []
    for method, Est in (("RF", RandomForestRegressor), ("ET", ExtraTreesRegressor)):
        for mf in ("sqrt", None):
            W = np.zeros((18, 18))
            for j in range(18):
                ins = [i for i in range(18) if i != j]
                m = Est(n_estimators=1000, max_features=mf, random_state=2013 + j).fit(Z[:, ins], Z[:, j])
                W[ins, j] = m.feature_importances_
            ours = {(up[i], up[j]) for i in range(18) for j in range(18) if i != j and W[i, j] > 0.08}
            out.append({"tree_method": method, "max_features": mf or "all", "edges": len(ours),
                        "shared": len(ours & pub), "jaccard": len(ours & pub) / len(ours | pub),
                        "max_weight": float(W.max())})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("xlsx")
    ap.add_argument("out")
    ap.add_argument("--cpus", type=int, default=int(os.environ.get("SLURM_CPUS_PER_TASK", 4)))
    a = ap.parse_args()
    jobs = [("ffl_prior_sd_0.0025", "or(gX+,gY-)", 0.0025, "t_stop", None),
            ("ffl_scale_100", "or(gX+,gY-)", None, "100", None)]
    for s in (5.0, 10.0):
        for m in ("or(gX+,gY-)", "or(gX-,gY+)", "and(gX+,gY-)"):
            jobs.append((f"ffl_sigma_s_{int(s)}", m, None, "t_stop", s))
    with Pool(a.cpus) as pool:
        r1 = pool.map_async(ffl_test, jobs, chunksize=1)
        r2 = pool.map_async(toggle_test, [("toggle_prior_sd_0.0025", 0.0025)])
        res = {"ffl": r1.get(), "toggle": r2.get(), "genie3_grid": genie3_grid(a.xlsx)}
    Path(a.out).write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1)[:4000])


if __name__ == "__main__":
    main()
