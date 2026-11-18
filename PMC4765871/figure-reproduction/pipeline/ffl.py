"""FFL analysis: Figs 2-4 and supp. Figs 12-15 and Table 4.

usage: ffl.py OUTDIR [--mcmc-from DIR] [--cpus N]

Steps (main text section 3, supp. section 2.1):
 1. simulate 300 cells of the OR-gate I1-FFL and the deterministic reference;
 2. GENIE3 and correlation signs (supp. Fig. 13);
 3. three Wanderlust replicates (k = 18, l = k/3) from the three cells with the lowest gX;
 4. GP emulators of gX and gY per replicate; the 12 candidate models for gZ (supp. Fig. 14),
    AIC and BIC; thermodynamic integration for the three best (OR and AND with gX+ gY-, OR with
    gX- gY+);
 5. posterior of the OR-gate model with uniform priors (Fig. 3) and with an informative prior on
    lambda (Table 4); relative errors of the MAP estimates;
 6. the gY model (gX+) and predictions under three perturbations (Fig. 4).

With --mcmc-from, step 4-6 samplers are not rerun: their outputs are read from DIR (the committed
outputs), and only the light steps are recomputed. That is what CI does; the samplers depend on
the floating-point details of the machine, so a rerun on another CPU gives another chain.
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

P = json.loads((HERE / "params" / "analysis.json").read_text())["ffl"]
TRUE = sim.PAR["ffl"]["kinetics"]
TRUE_VEC = [TRUE["alpha"], TRUE["lambda"], TRUE["kp"], TRUE["hp"], TRUE["km"], TRUE["hm"]]
GENES = ["gX", "gY", "gZ"]

# supp. Fig. 14: the 12 candidate models for gZ
MODELS = ["and(gX+,gY+)", "and(gX+,gY-)", "and(gX-,gY+)", "and(gX-,gY-)", "gX+", "gX-",
          "or(gX+,gY+)", "or(gX+,gY-)", "or(gX-,gY+)", "or(gX-,gY-)", "gY+", "gY-"]


def data():
    X, ta, ts = sim.ffl_snapshot(sim.PAR["ffl"]["n_cells"], sim.PAR["ffl"]["seed"])
    T = float(ts.mean())
    return X, ta, ts, T


def pseudo_time(X):
    starts = np.argsort(X[:, 0])[:3]
    reps = []
    for r, s in enumerate(starts):
        traj, _ = geo.wanderlust(X, int(s), l=P["wanderlust_l"], k=P["wanderlust_l"] // 3,
                                 num_graphs=P["num_graphs"], num_landmarks=P["num_landmarks"],
                                 seed=P["seed"] + r)
        reps.append(traj)
    return starts, np.array(reps)


def build_series(X, reps, T, target, inputs, scale):
    ser = []
    for r, traj in enumerate(reps):
        pt = traj * scale
        emus = {}
        for g in inputs:
            f, _, _ = em.gp_fit(pt, X[:, GENES.index(g)], seed=r)
            emus[g] = f
        fz, sz, _ = em.gp_fit(pt, X[:, GENES.index(target)], seed=r)
        ser.append(grn.Series(pt, X[:, GENES.index(target)], emus, fz(np.array([0.0]))[0], sz,
                              dt=P["dt"], t1=scale))
    return ser


def _fit(args):
    spec, target, lam_prior, seed, X, reps, T, scale = args
    m = grn.Model(spec)
    pr = grn.Problem(m, build_series(X, reps, T, target, m.inputs, scale), lam_prior=lam_prior)
    mc = grn.run_mcmc(pr, seed, n_sample=P["n_sample"], thin=P["thin"])
    th, ll = grn.map_estimate(pr, mc)
    aic, bic = grn.info_criteria(ll, m.n_params, pr.n_obs)
    return {"model": spec, "target": target, "lam_prior": lam_prior, "names": m.names,
            "map": th.tolist(), "loglik": ll, "aic": aic, "bic": bic, "n_obs": pr.n_obs,
            "n_params": m.n_params, "accept": mc["accept"],
            "samples": np.exp(mc["logtheta"]).tolist()}


def _ti(args):
    spec, seed, X, reps, T, scale = args
    m = grn.Model(spec)
    pr = grn.Problem(m, build_series(X, reps, T, "gZ", m.inputs, scale))
    out = grn.thermodynamic_integration(pr, seed, n_temps=P["ti_temps"], n_burn=P["ti_burn"],
                                        n_sample=P["ti_sample"])
    out["model"] = spec
    return out


def rel_error(est, true=TRUE_VEC):
    e = np.abs(np.array(est) - np.array(true)) / np.array(true)
    return float(e.mean() * 100), (e * 100).tolist()


def perturbations(fits, T, seed):
    """Fig. 4 (supp. 2.1.3): perturbed true system against the inferred one."""
    rng = np.random.default_rng(seed)
    gz = fits["gZ_informative"]["map"]  # alpha, lambda, kp, hp, km, hm
    gy = fits["gY"]["map"]              # alpha, lambda, kp, hp
    base = dict(TRUE)
    cases = {
        "deletion": {"delete_gy": True},
        "knockdown": {"lambda": 3 * TRUE["lambda"]},
        "simultaneous": {"kp": TRUE["kp"] / 10, "km": TRUE["km"] / 5},
    }
    out = {}
    for name, ch in cases.items():
        k = dict(base, **ch)
        ts, _ = sim.ffl_paths(P["perturb_runs"], int(rng.integers(2**31)), k=k)
        Tf = float(np.nanmean(ts))
        tt, det = sim.ffl_deterministic(Tf, k=k)
        # observations at integer times, as in the published Fig. 4 (t = 1, 2, ...)
        tobs = np.arange(1.0, np.floor(Tf) + 1)
        idx = np.searchsorted(tt, tobs - 1e-9)
        D = det[idx] + rng.normal(0, P["perturb_noise"], (len(idx), 3))
        fx, _, _ = em.gp_fit(tobs, D[:, 0], seed=1)
        # inferred system under the same perturbation, driven by the emulated input
        a_y, l_y, kp_y, hp_y = gy
        a_z, l_z, kp_z, hp_z, km_z, hm_z = gz
        if name == "knockdown":
            l_y, l_z = 3 * l_y, 3 * l_z
        if name == "simultaneous":
            kp_y, kp_z, km_z = kp_y / 10, kp_z / 10, km_z / 5
        dt = 0.01
        grid = np.arange(0, Tf + dt / 2, dt)
        xg = fx(grid)
        y = np.empty(len(grid))
        z = np.empty(len(grid))
        y[0], z[0] = D[0, 1], D[0, 2]
        for i in range(len(grid) - 1):
            fxy = sim.act(xg[i], kp_y, hp_y)
            fxz = sim.act(xg[i], kp_z, hp_z)
            rz = 0.0 if name == "deletion" else sim.rep(y[i], km_z, hm_z)
            y[i + 1] = y[i] + dt * (a_y * fxy - l_y * y[i])
            z[i + 1] = z[i] + dt * (a_z * (fxz + rz) - l_z * z[i])
        pred = np.interp(tobs, grid, z)
        resid = D[:, 2] - pred
        ss = ((D[:, 2] - D[:, 2].mean()) ** 2).sum()
        out[name] = {"T_f": Tf, "t": tobs.tolist(), "gZ_data": D[:, 2].tolist(),
                     "gZ_true": det[idx, 2].tolist(), "grid": grid[::10].tolist(),
                     "gZ_pred": z[::10].tolist(), "rmse": float(np.sqrt((resid**2).mean())),
                     "r2": float(1 - (resid**2).sum() / ss)}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("outdir")
    ap.add_argument("--mcmc-from")
    ap.add_argument("--cpus", type=int, default=int(os.environ.get("SLURM_CPUS_PER_TASK", 4)))
    a = ap.parse_args()
    out = Path(a.outdir)
    out.mkdir(parents=True, exist_ok=True)

    X, ta, ts, T = data()
    scale = T if P["time_scale"] == "t_stop" else float(P["time_scale"])
    res = {"n_cells": len(X), "T_f": T, "time_scale": scale}

    # GENIE3 and correlations (supp. Fig. 13)
    W = geo.genie3(X, ntrees=P["genie3_trees"], seed=P["seed"], tree_method=P["genie3_method"])
    R = np.corrcoef(X.T)
    res["genie3"] = {f"{GENES[i]}->{GENES[j]}": float(W[i, j]) for i in range(3) for j in range(3) if i != j}
    res["corr"] = {"gX,gY": float(R[0, 1]), "gX,gZ": float(R[0, 2]), "gY,gZ": float(R[1, 2])}

    starts, reps = pseudo_time(X)
    res["wanderlust_starts"] = starts.tolist()
    res["wanderlust_vs_true_time"] = [float(np.corrcoef(r, ta / ts)[0, 1]) for r in reps]
    # Fig. 2A: expression at pseudo time against the deterministic model at the same time
    tt, det = sim.ffl_deterministic(T)
    fig2a = {}
    for j, g in enumerate(GENES):
        real = np.interp(reps[0] * T, tt, det[:, j])
        fig2a[g] = {"real": real.tolist(), "pseudo": X[:, j].tolist(),
                    "r": float(np.corrcoef(real, X[:, j])[0, 1])}
    res["fig2a"] = fig2a
    save_npz(out / "ffl_data.npz", X=X, ta=ta, ts=ts, reps=reps, det_t=tt, det=det)

    if a.mcmc_from:
        prev = json.loads((Path(a.mcmc_from) / "ffl_fits.json").read_text())
        if (Path(a.mcmc_from) / "ffl_fits.json").resolve() != (out / "ffl_fits.json").resolve():
            (out / "ffl_fits.json").write_text((Path(a.mcmc_from) / "ffl_fits.json").read_text())
        fits, ti = prev["fits"], prev["ti"]
    else:
        jobs = [(m, "gZ", None, P["seed"] + 100 + i, X, reps, T, scale) for i, m in enumerate(MODELS)]
        lam = (TRUE["lambda"], P["lambda_prior_sd"])
        jobs.append(("or(gX+,gY-)", "gZ", lam, P["seed"] + 200, X, reps, T, scale))
        jobs.append(("gX+", "gY", None, P["seed"] + 201, X, reps, T, scale))
        tijobs = [(m, P["seed"] + 300 + i, X, reps, T, scale) for i, m in enumerate(P["ti_models"])]
        with Pool(a.cpus) as pool:
            r1 = pool.map_async(_fit, jobs)
            r2 = pool.map_async(_ti, tijobs)
            fl, ti = r1.get(), r2.get()
        fits = {f["model"]: f for f in fl[:len(MODELS)]}
        fits["gZ_informative"] = fl[len(MODELS)]
        fits["gY"] = fl[len(MODELS) + 1]
        # keep a thinned posterior only for the models drawn in Fig. 3
        for k, f in fits.items():
            if k not in ("or(gX+,gY-)", "gZ_informative"):
                f["samples"] = []
            else:
                f["samples"] = f["samples"][::2]
        (out / "ffl_fits.json").write_text(json.dumps({"fits": fits, "ti": ti}))

    table = []
    for m in MODELS:
        f = fits[m]
        table.append({"model": m, "aic": f["aic"], "bic": f["bic"], "loglik": f["loglik"]})
    res["model_selection"] = table
    best = max(table, key=lambda r: r["aic"])
    res["best_aic"] = best["model"]
    res["ti"] = {t["model"]: t["log_evidence"] for t in ti}
    lz = res["ti"]
    res["log10_bf_or_vs_and"] = (lz["or(gX+,gY-)"] - lz["and(gX+,gY-)"]) / np.log(10)
    res["log10_bf_or_vs_inverted"] = (lz["or(gX+,gY-)"] - lz["or(gX-,gY+)"]) / np.log(10)
    u = fits["or(gX+,gY-)"]
    inf = fits["gZ_informative"]
    res["map_uniform"] = dict(zip(u["names"], u["map"]))
    res["map_informative"] = dict(zip(inf["names"], inf["map"]))
    res["rel_error_uniform"], res["rel_error_uniform_each"] = rel_error(u["map"])
    res["rel_error_informative"], res["rel_error_informative_each"] = rel_error(inf["map"])
    S = np.array(u["samples"])
    ratio = S[:, 0] / S[:, 1]
    res["alpha_over_lambda"] = {"median": float(np.median(ratio)), "q05": float(np.quantile(ratio, 0.05)),
                                "q95": float(np.quantile(ratio, 0.95)), "true": TRUE["alpha"] / TRUE["lambda"]}
    res["map_gY"] = dict(zip(fits["gY"]["names"], fits["gY"]["map"]))
    res["perturbations"] = perturbations(fits, T, P["seed"] + 400)
    (out / "ffl.json").write_text(json.dumps(res, indent=1))
    print(json.dumps({k: res[k] for k in ("best_aic", "ti", "log10_bf_or_vs_and", "log10_bf_or_vs_inverted",
                                          "rel_error_uniform", "rel_error_informative", "alpha_over_lambda")}, indent=1))


if __name__ == "__main__":
    main()
