"""Toggle switch analysis: Figs 1B-D and 1H, 5, 6; supp. Tables 1, 6, 7; supp. Figs 6, 17, 25, 33.

usage: toggle.py OUTDIR [--mcmc-from DIR] [--cpus N]

1. 400 cells of the six-gene toggle switch (supp. 2.2.1); diffusion map (sigma 1000, supp. Table 10)
   and <d>(sigma) (supp. Fig. 33).
2. Start cell where the late genes are lowest (the centre of the X, supp. 1.2); end cells at the
   four tips; branch clustering with Nn = 15; Wanderlust (k = 18, l = 6) per branch, 3 replicates.
3. GENIE3 with thresholds 0.3 and 0.1 and correlation signs (|r| > 0.5): supp. Figs 17 and 25.
4. The seven gC models of Fig. 6 on the two branches where gA is high; scores (AIC - m)/max(AIC - m).
5. gC and gD fitted together with AND models and an informative prior on lambda (Fig. 1H, 6.8%).
6. Robustness to observation noise (supp. Table 6) and clustering errors in low and high dimension
   (supp. Table 1).
7. The 94 models of supp. Table 7 (GENIE3 threshold 0.1, no correlation filter) and thermodynamic
   integration for its two best.
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
import emulate as em  # noqa: E402
import geometry as geo  # noqa: E402
import grn  # noqa: E402
import simulate as sim  # noqa: E402
from util import save_npz  # noqa: E402

P = json.loads((HERE / "params" / "analysis.json").read_text())["toggle"]
K = sim.PAR["toggle"]["kinetics"]
TRUE_VEC = [K["alpha"], K["lambda"], K["kp"], K["hp"], K["km"], K["hm"]]
G = ["A", "B", "C", "D", "E", "F"]
FIG6 = ["D-", "D+", "A-", "and(A+,D-)", "and(A+,D+)", "or(A+,D-)", "or(A+,D+)"]
NOISE = {"none": None, "add20": ("add", 20.0), "add40": ("add", 40.0), "mul0.04": ("mul", 0.04),
         "mul0.12": ("mul", 0.12)}


def rel_error(est):
    e = np.abs(np.array(est) - np.array(TRUE_VEC)) / np.array(TRUE_VEC)
    return float(e.mean() * 100), (e * 100).tolist()


def regions(X):
    """True cluster labels (supp. 1.2.1): early cells by the side of the A-B toggle, committed cells
    by the late gene that won."""
    late = X[:, 2:]
    early = late.max(1) < P["early_threshold"]
    side = np.where(X[:, 0] > X[:, 1], "A", "B")
    fate = np.array(["C", "D", "E", "F"])[late.argmax(1)]
    return early, side, fate


def branch_ok(fate_b, early, side, fate):
    s = "A" if fate_b in "CD" else "B"
    return (early & (side == s)) | (~early & (fate == fate_b))


def analyse_geometry(Xo, X, seed, sigma):
    Y, ev = geo.diffusion_map(Xo, sigma)
    start = int(np.argmin(Xo[:, 2:].sum(1)))
    # four tips: farthest-point sampling from the start among cells in dense regions
    from scipy.spatial.distance import cdist
    D = cdist(Y, Y)
    kd = np.sort(D, 1)[:, 10]
    ok = kd <= np.quantile(kd, 0.9)
    tips = []
    for _ in range(4):
        d = np.min([D[i] for i in [start] + tips], axis=0)
        d[~ok] = -1
        tips.append(int(np.argmax(d)))
    early, side, fate = regions(X)
    out = {"start": start, "tips": tips, "eigenvalues": ev.tolist(), "branches": {}}
    Dh = cdist(Xo, Xo)
    # name the four branches jointly: the assignment of fates to tips with the most matching
    # committed cells among each tip's 20 nearest cells
    import itertools
    counts = []
    for end in tips:
        near = np.argsort(D[end])[:20]
        counts.append({f: int(((fate[near] == f) & ~early[near]).sum()) for f in "CDEF"})
    best = max(itertools.permutations("CDEF"), key=lambda pm: sum(counts[i][f] for i, f in enumerate(pm)))
    for end, fb in zip(tips, best):
        cells, path = geo.branch_cluster(Y, start, end, P["Nn"], k_graph=P["branch_k_graph"])
        okc = branch_ok(fb, early, side, fate)
        cells_h, _ = geo.branch_cluster(Xo, start, end, P["Nn"], k_graph=P["branch_k_graph"])
        out["branches"][fb] = {"end": end, "cells": cells.tolist(), "n": int(len(cells)),
                               "error_low": float(100 * (~okc[cells]).mean()),
                               "error_high": float(100 * (~okc[cells_h]).mean())}
    return Y, out


def pseudo_time(Xo, cells, Y, start, seed):
    sub = Xo[cells]
    d = ((Y[cells] - Y[start]) ** 2).sum(1)
    starts = np.argsort(d)[:3]
    reps = []
    for r, s in enumerate(starts):
        traj, _ = geo.wanderlust(sub, int(s), l=P["wanderlust_l"], k=P["wanderlust_l"] // 3,
                                 num_graphs=P["num_graphs"], num_landmarks=P["num_landmarks"],
                                 seed=seed + r)
        reps.append(traj)
    return np.array(reps)


def dataset(obs_noise, seed, sigma, with_pt=True):
    Xo, X, ta, ts, fate = sim.toggle_snapshot(sim.PAR["toggle"]["n_cells"], seed, obs_noise=obs_noise)
    Y, geom = analyse_geometry(Xo, X, seed, sigma)
    T = float(ts.mean())
    pts = {}
    if with_pt:
        for b, info in geom["branches"].items():
            pts[b] = pseudo_time(Xo, np.array(info["cells"]), Y, geom["start"], seed + ord(b))
    return {"Xo": Xo, "X": X, "ta": ta, "ts": ts, "fate": fate, "Y": Y, "geom": geom, "T": T, "pts": pts}


def series_for(ds, target, inputs, branches, rename=None):
    """Series of gene `target` on the given branches; inputs emulated by GPs. rename maps model
    input names to genes (for the joint gC/gD fit)."""
    rename = rename or {}
    ser = []
    for b in branches:
        cells = np.array(ds["geom"]["branches"][b]["cells"])
        for r, traj in enumerate(ds["pts"][b]):
            pt = traj * ds["T"]
            emus = {}
            for name in inputs:
                g = rename.get(name, name)
                f, _, _ = em.gp_fit(pt, ds["Xo"][cells, G.index(g)], seed=r)
                emus[name] = f
            y = ds["Xo"][cells, G.index(target)]
            fy, sy, _ = em.gp_fit(pt, y, seed=r)
            ser.append(grn.Series(pt, y, emus, fy(np.array([0.0]))[0], sy, dt=P["dt"], t1=ds["T"]))
    return ser


def _fit(args):
    spec, parts, lam_prior, seed, keep_samples = args
    m = grn.Model(spec)
    ser = []
    for ds, target, branches, rename in parts:
        ser += series_for(ds, target, m.inputs, branches, rename)
    pr = grn.Problem(m, ser, lam_prior=lam_prior)
    mc = grn.run_mcmc(pr, seed, n_sample=P["n_sample"], thin=P["thin"])
    th, ll = grn.map_estimate(pr, mc)
    aic, bic = grn.info_criteria(ll, m.n_params, pr.n_obs)
    S = np.exp(mc["logtheta"])
    return {"model": spec, "names": m.names, "map": th.tolist(), "mean": S.mean(0).tolist(),
            "loglik": ll, "aic": aic, "bic": bic, "n_obs": pr.n_obs, "accept": mc["accept"],
            "samples": S[::2].tolist() if keep_samples else []}


def _ti(args):
    spec, parts, seed = args
    m = grn.Model(spec)
    ser = []
    for ds, target, branches, rename in parts:
        ser += series_for(ds, target, m.inputs, branches, rename)
    pr = grn.Problem(m, ser)
    out = grn.thermodynamic_integration(pr, seed, n_temps=P["ti_temps"], n_burn=P["ti_burn"],
                                        n_sample=P["ti_sample"])
    out["model"] = spec
    return out


def strip(ds):
    return {k: v for k, v in ds.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("outdir")
    ap.add_argument("--mcmc-from")
    ap.add_argument("--cpus", type=int, default=int(os.environ.get("SLURM_CPUS_PER_TASK", 4)))
    a = ap.parse_args()
    out = Path(a.outdir)
    out.mkdir(parents=True, exist_ok=True)
    seed0 = sim.PAR["toggle"]["seed"]
    res = {}

    main_ds = dataset(None, seed0, P["sigma"])
    Xo = main_ds["Xo"]
    ls = np.round(np.arange(0.5, 4.0001, 0.02), 2)
    dim = geo.intrinsic_dimension(Xo, ls)
    res["dimension_curve"] = {"log10_sigma": ls.tolist(), "d": dim.tolist(),
                              "local_maxima": geo.local_maxima(ls, dim)}
    res["geometry"] = {k: v for k, v in main_ds["geom"].items()}
    res["T_f"] = main_ds["T"]
    res["fates"] = np.bincount(main_ds["fate"], minlength=4).tolist()
    W = geo.genie3(Xo, ntrees=P["genie3_trees"], seed=P["seed"], tree_method=P["genie3_method"])
    R = np.corrcoef(Xo.T)
    res["genie3"] = {f"{G[i]}->{G[j]}": float(W[i, j]) for i in range(6) for j in range(6) if i != j}
    for thr in (0.3, 0.1):
        ins = [G[i] for i in range(6) if i != 2 and W[i, 2] > thr]
        res[f"gC_inputs_{thr}"] = {g: {"w": float(W[G.index(g), 2]), "r": float(R[G.index(g), 2]),
                                       "sign": (int(np.sign(R[G.index(g), 2])) if abs(R[G.index(g), 2]) > 0.5 else 0)}
                                   for g in ins}
        res[f"edges_{thr}"] = int((W > thr).sum())
    br = res["geometry"]["branches"]
    res["branches"] = sorted(br)
    save_npz(out / "toggle_data.npz", Xo=Xo, X=main_ds["X"], ta=main_ds["ta"], ts=main_ds["ts"],
                        fate=main_ds["fate"], Y=main_ds["Y"],
                        **{f"pt_{b}": v for b, v in main_ds["pts"].items()})
    (out / "toggle_geometry.json").write_text(json.dumps(res["geometry"]))

    # supp. Table 1: clustering in low and high dimension, 3 datasets per noise level
    t1 = {}
    for sg in (20.0, 80.0):
        lows, highs = [], []
        for k in range(3):
            ds = dataset(("add", sg), seed0 + 100 * int(sg) + k, P["sigma"], with_pt=False)
            for b in ds["geom"]["branches"].values():
                lows.append(b["error_low"])
                highs.append(b["error_high"])
        t1[str(int(sg))] = {"low_mean": float(np.mean(lows)), "low_sd": float(np.std(lows, ddof=1)),
                            "high_mean": float(np.mean(highs)), "high_sd": float(np.std(highs, ddof=1))}
    res["table1"] = t1

    if a.mcmc_from:
        fits = json.loads((Path(a.mcmc_from) / "toggle_fits.json").read_text())
        if (Path(a.mcmc_from) / "toggle_fits.json").resolve() != (out / "toggle_fits.json").resolve():
            (out / "toggle_fits.json").write_text((Path(a.mcmc_from) / "toggle_fits.json").read_text())
    else:
        dsets = {"none": main_ds}
        for name, nz in NOISE.items():
            if nz is not None:
                dsets[name] = dataset(nz, seed0 + 7, P["sigma"])
        AB = ["C", "D"]
        lam = (K["lambda"], P["lambda_prior_sd"])
        jobs = []
        for i, m in enumerate(FIG6):
            jobs.append((m, [(main_ds, "C", AB, None)], None, P["seed"] + i, False))
        # joint gC and gD (Fig. 1H): one parameter set, gD's inputs renamed onto the gC model
        jobs.append(("and(A+,D-)", [(main_ds, "C", AB, None), (main_ds, "D", AB, {"D": "C"})], lam,
                     P["seed"] + 50, True))
        for j, (name, ds) in enumerate(dsets.items()):
            jobs.append(("and(A+,D-)", [(ds, "C", AB, None)], lam, P["seed"] + 60 + j, False))
        t7 = [l.split("\t")[0] for l in (HERE / "params" / "supp_table7.tsv").read_text().splitlines()[1:]]
        t7 = sorted(set(m.replace("B+D-", "B+,D-") for m in t7))
        for i, m in enumerate(t7):
            jobs.append((m, [(main_ds, "C", AB, None)], None, P["seed"] + 100 + i, False))
        tijobs = [(m, [(main_ds, "C", AB, None)], P["seed"] + 300 + i)
                  for i, m in enumerate(["and(A+,D-)", "and(or(A+,B-),D-)"])]
        with Pool(a.cpus) as pool:
            r1 = pool.map_async(_fit, jobs, chunksize=1)
            r2 = pool.map_async(_ti, tijobs)
            fl, ti = r1.get(), r2.get()
        n6 = len(FIG6)
        fits = {"fig6": fl[:n6], "joint": fl[n6], "noise": dict(zip(dsets, fl[n6 + 1:n6 + 1 + len(dsets)])),
                "table7": fl[n6 + 1 + len(dsets):], "ti": ti}
        (out / "toggle_fits.json").write_text(json.dumps(fits))

    f6 = fits["fig6"]
    aics = np.array([f["aic"] for f in f6])
    m_ = aics.min()
    res["fig6"] = [{"model": f["model"], "aic": f["aic"], "bic": f["bic"],
                    "score": float((f["aic"] - m_) / (aics - m_).max())} for f in f6]
    res["fig6_best"] = max(f6, key=lambda f: f["aic"])["model"]
    j = fits["joint"]
    res["joint"] = {"map": dict(zip(j["names"], j["map"])), "mean": dict(zip(j["names"], j["mean"]))}
    res["joint_rel_error_mean"], res["joint_rel_error_mean_each"] = rel_error(j["mean"])
    res["joint_rel_error_map"], _ = rel_error(j["map"])
    res["table6"] = {k: rel_error(v["map"])[0] for k, v in fits["noise"].items()}
    t7 = sorted(fits["table7"], key=lambda f: -f["bic"])
    res["table7"] = [{"model": f["model"], "abs_bic": -f["bic"], "abs_aic": -f["aic"]} for f in t7]
    res["table7_best_bic"] = t7[0]["model"]
    res["table7_best_aic"] = max(fits["table7"], key=lambda f: f["aic"])["model"]
    tl = {t["model"]: t["log_evidence"] for t in fits["ti"]}
    res["table7_ti"] = tl
    res["table7_bayes_factor"] = float(np.exp(tl["and(A+,D-)"] - tl["and(or(A+,B-),D-)"]))
    (out / "toggle.json").write_text(json.dumps(res, indent=1))
    print(json.dumps({k: res[k] for k in ("fates", "branches", "gC_inputs_0.3", "gC_inputs_0.1", "fig6", "fig6_best",
                                          "joint_rel_error_mean", "joint_rel_error_map", "table6", "table1",
                                          "table7_best_bic", "table7_best_aic", "table7_ti", "table7_bayes_factor")}, indent=1))


if __name__ == "__main__":
    main()
