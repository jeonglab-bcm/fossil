"""Haematopoiesis analysis: Figs 7-9, supp. Figs 29-32, supp. section 2.3 and Tables 8-9.

usage: haem.py MOIGNARD_XLSX OUTDIR [--mcmc-from DIR] [--cpus N]

1. Moignard et al. (2013) quality control: drop cells with no detected gene and cells with Ubc or
   Polr2a undetected (Ct > 27); 597 cells remain.
2. CT = Ct - mean(Ct of Ubc and Polr2a) per cell (Ct > 27 set to 28 first), undetected set to 15
   (Moignard 2013 Methods); log expression = 20 - CT (supp. 2.3.2). 18 transcription factors.
3. Correlations of supp. Fig. 29; <d>(sigma) of supp. Fig. 32A; diffusion map with sigma = 10^0.9
   (supp. Table 10 prints "100.9"; supp. Fig. 32A puts the maximum of <d> at log10 sigma = 0.9).
4. GENIE3 (threshold 0.08) and correlation signs (p < 0.01): Fig. 7C.
5. Branch clustering without labels (supp. 2.3.1) with Nn = 15.
6. Pseudo time series on the GMP and CLP pathways (Wanderlust k = 15, l = 5, three replicates),
   outlier removal and imputation (supp. 2.3.2), and the models of supp. Tables 8 and 9.
"""
import argparse
import json
import os
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import emulate as em  # noqa: E402
import geometry as geo  # noqa: E402
import grn  # noqa: E402

P = json.loads((HERE / "params" / "analysis.json").read_text())["haem"]
TFS = ["Erg", "Eto2", "Fli1", "Gata1", "Gata2", "Gfi1", "Gfi1b", "hHex", "Ldb1", "Lmo2", "Lyl1",
       "Meis1", "Mitf", "Nfe2", "PU.1", "Runx1", "SCL", "Tel"]
UPPER = {g: g.upper() for g in TFS}
UPPER["hHex"] = "HHEX"
PATHWAYS = {"CLP": ["HSC", "LMPP", "CLP"], "GMP": ["HSC", "LMPP", "GMP"], "PreMegE": ["HSC", "PreMegE"]}

# supp. Tables 8 and 9; signs from supp. Fig. 29 (right)
SIGN = {"GATA2": {"GFI1": "-", "NFE2": "+", "SCL": "+"},
        "GFI1": {"GATA2": "-", "GFI1B": "-"},
        "GFI1B": {"GATA2": "+", "GFI1": "-"}}
TABLE8 = ["GFI1", "NFE2", "SCL", "and(GFI1,NFE2)", "or(and(GFI1,NFE2),SCL)", "and(GFI1,SCL)",
          "or(and(GFI1,SCL),NFE2)", "and(GFI1,NFE2,SCL)", "and(NFE2,SCL)", "or(and(NFE2,SCL),GFI1)",
          "or(GFI1,NFE2)", "and(or(GFI1,NFE2),SCL)", "or(GFI1,SCL)", "and(or(GFI1,SCL),NFE2)",
          "or(GFI1,NFE2,SCL)", "or(NFE2,SCL)", "and(or(NFE2,SCL),GFI1)"]
TABLE9_GFI1 = ["and(GATA2,GFI1B)", "or(GATA2,GFI1B)", "GATA2", "GFI1B"]
TABLE9_GFI1B = ["and(GATA2,GFI1)", "or(GATA2,GFI1)", "GATA2", "GFI1"]
TARGETS = {"GATA2": ("CLP", TABLE8), "GFI1": ("GMP", TABLE9_GFI1), "GFI1B": ("GMP", TABLE9_GFI1B)}


def signed(spec, target):
    import re
    return re.sub(r"([A-Z0-9.]+)(?=[,)]|$)", lambda m: m.group(1) + SIGN[target][m.group(1)], spec)


def load(xlsx):
    df = pd.read_excel(xlsx)
    df["type"] = df["Cell"].str.extract(r"^([A-Za-z]+)")[0]
    genes = [c for c in df.columns if c not in ("Cell", "type")]
    ct = df[genes].astype(float)
    und = ct > 27
    keep = ~und.all(1) & ~und["Ubc"] & ~und["Polr2a"]
    qc = {"cells_in": int(len(df)), "no_gene": int(und.all(1).sum()),
          "ubc_undetected": int((und["Ubc"] & ~und.all(1)).sum()),
          "polr2a_undetected": int((und["Polr2a"] & ~und.all(1)).sum()),
          "cells_kept": int(keep.sum())}
    df, ct, und = df[keep].reset_index(drop=True), ct[keep].reset_index(drop=True), und[keep].reset_index(drop=True)
    ct = ct.clip(upper=28)
    hk = ct[["Ubc", "Polr2a"]].mean(1)
    d = ct.sub(hk, axis=0)
    d[und] = 15.0
    CT = d[TFS].to_numpy()
    qc["per_type"] = df["type"].value_counts().to_dict()
    return df["Cell"].tolist(), df["type"].to_numpy(), CT, qc


def tips(Y, n=4, k=10, dense_q=0.9):
    """Label-free end points of the embedding: farthest-point sampling from the centroid among
    cells in dense regions (distance to the k-th neighbour below its dense_q quantile), so that
    isolated outlier cells are not taken for branch ends."""
    from scipy.spatial.distance import cdist
    D = cdist(Y, Y)
    kd = np.sort(D, 1)[:, k]
    ok = kd <= np.quantile(kd, dense_q)
    c = Y[ok].mean(0)
    dc = ((Y - c) ** 2).sum(1)
    dc[~ok] = -1
    t = [int(np.argmax(dc))]
    while len(t) < n:
        d = np.min([D[i] for i in t], axis=0)
        d[~ok] = -1
        t.append(int(np.argmax(d)))
    return t


def branch_errors(Y, types, E):
    """supp. 2.3.1: start at the tip where GATA2 is expressed and GATA1 is not; a branch to each other
    tip; the error is the share of clustered cells outside the pathway the branch ends in."""
    t = tips(Y, n=P["tips"], dense_q=P["tips_dense_q"])
    g2, g1 = TFS.index("Gata2"), TFS.index("Gata1")
    score = []
    for i in t:
        nb = np.argsort(((Y - Y[i]) ** 2).sum(1))[:20]
        score.append(E[nb, g2].mean() - E[nb, g1].mean())
    start = t[int(np.argmax(score))]
    out = {"start": start, "tips": t, "branches": {}}
    for end in t:
        if end == start:
            continue
        cells, path = geo.branch_cluster(Y, start, end, P["Nn"], k_graph=P["branch_k_graph"])
        nb = np.argsort(((Y - Y[end]) ** 2).sum(1))[:20]
        vc = pd.Series(types[nb]).value_counts()
        last, purity = vc.index[0], int(vc.iloc[0])
        if last not in ("PreMegE", "GMP", "CLP"):
            continue  # an end in the HSC or LMPP region is not a branch end
        pw = last
        if pw in out["branches"] and out["branches"][pw]["purity"] >= purity:
            continue  # keep the purest end of each pathway
        wrong = ~np.isin(types[cells], PATHWAYS[pw])
        out["branches"][pw] = {"end": end, "n": int(len(cells)), "purity": purity,
                               "error_pct": float(100 * wrong.mean())}
    return out


def pseudotime(E, types, Y, start_cell, pathway, seed):
    cells = np.where(np.isin(types, PATHWAYS[pathway]))[0]
    sub = E[cells]
    # replicate start cells: the pathway's cell nearest the start tip and its 2 nearest neighbours
    d = ((Y[cells] - Y[start_cell]) ** 2).sum(1)
    starts = np.argsort(d)[:3]
    reps = []
    for r, s in enumerate(starts):
        traj, _ = geo.wanderlust(sub, int(s), l=P["wanderlust_l"], k=P["wanderlust_l"] // 3,
                                 num_graphs=P["num_graphs"], num_landmarks=P["num_landmarks"],
                                 seed=seed + r)
        reps.append(traj)
    return cells, np.array(reps)


def preprocess(ct, rng, n_ref=120):
    """supp. 2.3.2 for one gene in pseudo time order. Returns kept mask and log expression."""
    n = len(ct)
    det = ct < 15
    chosen = None
    for L in range(22, 29):
        w = max(3, int(round(L * n / n_ref)))
        frac = np.convolve(np.pad(det.astype(float), w // 2, mode="edge"), np.ones(w) / w, "valid")[:n]
        high = frac > 0.5
        changes = int((np.diff(high.astype(int)) != 0).sum())
        if changes == 1:
            chosen = (L, high)
            break
    if chosen is None:
        # no window splits the series into two areas: no outlier removal, only imputation
        L = None
        keep = np.ones(n, bool)
    else:
        L, high = chosen
        keep = det == high
    out = ct.astype(float).copy()
    sd = ct[keep & det].std() if (keep & det).sum() > 2 else 1.0  # spread of detected CT
    low = keep & ~det
    out[low] = rng.normal(15.0, sd, low.sum())
    return keep, 20.0 - out, {"window": L, "removed": int((~keep).sum()), "imputed": int(low.sum())}


def make_series(target, inputs, pdata, rep_ids):
    ser = []
    for r in rep_ids:
        d = pdata[r]
        emus = {g: em.linear_emulator(d[g]["t"], d[g]["y"], window=P["emulator_window"]) for g in inputs}
        ty, yy = np.array(d[target]["t"]), np.array(d[target]["y"])
        f = em.linear_emulator(ty, yy, window=P["emulator_window"])
        sigma = float(np.std(yy - f(ty)))
        ser.append(grn.Series(ty, yy, emus, float(f(np.array([0.0]))[0]), sigma, dt=P["dt"],
                              t1=P["time_scale"]))
    return ser


def collapsed(model, theta, ser):
    """A leaf collapses when its Hill function hardly varies along the emulated input."""
    out = []
    T = model.n_terms
    for l, (name, sg) in enumerate(model.leaves):
        k, h = theta[T + 1 + 2 * l], theta[T + 2 + 2 * l]
        vals = []
        for s in ser:
            x = np.maximum(s.emus[name](np.linspace(0, s.t1, 200)), 1e-12)
            f = 1 / (1 + (k / x) ** h)
            vals.append(f)
        v = np.concatenate(vals)
        out.append(bool(v.max() - v.min() < P["collapse_range"]))
    return out


def _fit(args):
    target, spec, seed, pdata = args
    m = grn.Model(signed(spec, target))
    ser = make_series(target, m.inputs, pdata, range(3))
    pr = grn.Problem(m, ser)
    mc = grn.run_mcmc(pr, seed, n_sample=P["n_sample"], thin=P["thin"])
    th, ll = grn.map_estimate(pr, mc)
    aic, bic = grn.info_criteria(ll, m.n_params, pr.n_obs)
    med = np.median(np.exp(mc["logtheta"]), 0)
    col = collapsed(m, med, ser)
    eff = [f"{n}{'+' if s > 0 else '-'}" for (n, s), c in zip(m.leaves, col) if not c]
    return {"target": target, "model": spec, "signed": m.spec, "names": m.names, "map": th.tolist(),
            "median": med.tolist(), "loglik": ll, "aic": aic, "bic": bic, "n_obs": pr.n_obs,
            "collapsed": col, "effective": sorted(set(eff)), "accept": mc["accept"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("xlsx")
    ap.add_argument("outdir")
    ap.add_argument("--mcmc-from")
    ap.add_argument("--cpus", type=int, default=int(os.environ.get("SLURM_CPUS_PER_TASK", 4)))
    a = ap.parse_args()
    out = Path(a.outdir)
    out.mkdir(parents=True, exist_ok=True)

    cells, types, CT, qc = load(a.xlsx)
    E = 20.0 - CT
    res = {"qc": qc}
    up = [UPPER[g] for g in TFS]
    ix = {g: i for i, g in enumerate(up)}
    R = np.corrcoef(E.T)
    res["fig29_r"] = {f"{a_},{b_}": float(R[ix[a_], ix[b_]]) for a_, b_ in
                      [("GATA1", "GATA2"), ("SCL", "GATA2"), ("NFE2", "GATA2"), ("GFI1", "GATA2"),
                       ("GFI1B", "GATA2"), ("GFI1", "GFI1B")]}

    ls = np.round(np.arange(0.0, 2.0001, 0.01), 2)
    dim = geo.intrinsic_dimension(E, ls)
    lm = geo.local_maxima(ls, dim)
    res["dimension_curve"] = {"log10_sigma": ls.tolist(), "d": dim.tolist(),
                              "local_maxima": lm, "argmax": lm[0][0] if lm else None}
    emb = {}
    for name, sg in P["sigmas"].items():
        Y, ev = geo.diffusion_map(E, sg)
        emb[name] = Y
        res.setdefault("eigenvalues", {})[name] = ev.tolist()
    Y = emb["main"]
    # separation of cell types in the embedding: 10-NN label agreement
    from scipy.spatial.distance import cdist
    for name, Yk in emb.items():
        D = cdist(Yk, Yk)
        nn = np.argsort(D, 1)[:, 1:11]
        res.setdefault("knn_type_agreement", {})[name] = float((types[nn] == types[:, None]).mean())

    W = geo.genie3(E, ntrees=P["genie3_trees"], seed=P["seed"], tree_method=P["genie3_method"])
    edges = geo.correlation_signs(E, W, P["genie3_threshold"], p_thr=0.01)
    res["genie3"] = {"weights": {f"{up[i]}->{up[j]}": float(W[i, j]) for i in range(18) for j in range(18) if i != j},
                     "edges": [{"from": up[i], "to": up[j], "w": w, "r": r, "p": p, "sign": s}
                               for i, j, w, r, p, s in edges]}
    pub = json.loads((HERE / "params" / "published_networks.json").read_text())["fig7c_edges"]
    pub_set = {tuple(e) for e in pub}
    ours = {(e["from"], e["to"]) for e in res["genie3"]["edges"]}
    und = lambda s: {tuple(sorted(e)) for e in s}
    res["fig7c_missing"] = sorted(map(list, pub_set - ours))
    res["fig7c_extra"] = sorted(map(list, ours - pub_set))
    res["fig7c_compare"] = {
        "published_edges": len(pub_set), "our_edges": len(ours), "shared_directed": len(ours & pub_set),
        "shared_undirected": len(und(ours) & und(pub_set)),
        "published_undirected": len(und(pub_set)), "our_undirected": len(und(ours)),
        "jaccard_directed": len(ours & pub_set) / len(ours | pub_set),
    }
    # control: random graphs with as many edges
    rng = np.random.default_rng(P["seed"])
    allp = [(a_, b_) for a_ in up for b_ in up if a_ != b_]
    jr = []
    for _ in range(1000):
        pick = {allp[i] for i in rng.choice(len(allp), len(ours), replace=False)}
        jr.append(len(pick & pub_set) / len(pick | pub_set))
    res["fig7c_compare"]["jaccard_random_q99"] = float(np.quantile(jr, 0.99))
    res["fig7c_compare"]["jaccard_random_mean"] = float(np.mean(jr))

    res["branch_clustering"] = branch_errors(Y, types, E)
    start = res["branch_clustering"]["start"]

    pdata = {}
    series_out = {}
    rng = np.random.default_rng(P["seed"] + 1)
    for pw_i, pw in enumerate(["CLP", "GMP", "PreMegE"]):
        cidx, reps = pseudotime(E, types, Y, start, pw, P["seed"] + 10 * pw_i)
        pdata[pw] = []
        series_out[pw] = {"cells": cidx.tolist(), "replicates": []}
        for r, traj in enumerate(reps):
            order = np.argsort(traj, kind="stable")
            rank = np.empty(len(order))
            rank[order] = np.arange(len(order))
            pt = rank * P["time_scale"] / (len(order) - 1)
            rep = {}
            for g in ["GATA2", "GFI1", "GFI1B", "SCL", "NFE2", "GATA1"]:
                ctg = CT[cidx, ix[g]][order]
                keep, ly, info = preprocess(ctg, rng)
                rep[g] = {"t": pt[order][keep].tolist(), "y": ly[keep].tolist(), "info": info,
                          "raw_t": pt[order].tolist(), "raw_ct": ctg.tolist()}
            pdata[pw].append(rep)
            series_out[pw]["replicates"].append({"traj": traj.tolist(),
                                                 "types": types[cidx][order].tolist()})
        # pseudo time agrees with the order of cell types (HSC first)
        tr = reps.mean(0)
        res.setdefault("pathway_order", {})[pw] = {t: float(np.mean(tr[types[cidx] == t])) for t in PATHWAYS[pw]}
    (out / "haem_series.json").write_text(json.dumps({"pdata": pdata, "series": series_out,
                                                       "types": types.tolist(), "Y": Y.tolist(),
                                                       "Y_controls": {k: v.tolist() for k, v in emb.items()}}))

    if a.mcmc_from:
        fits = json.loads((Path(a.mcmc_from) / "haem_fits.json").read_text())
        if (Path(a.mcmc_from) / "haem_fits.json").resolve() != (out / "haem_fits.json").resolve():
            (out / "haem_fits.json").write_text((Path(a.mcmc_from) / "haem_fits.json").read_text())
    else:
        jobs = []
        for ti, (target, (pw, models)) in enumerate(TARGETS.items()):
            for mi, spec in enumerate(models):
                jobs.append((target, spec, P["seed"] + 1000 + 100 * ti + mi, pdata[pw]))
        with Pool(a.cpus) as pool:
            fits = pool.map(_fit, jobs)
        (out / "haem_fits.json").write_text(json.dumps(fits))
    sel = {}
    for target in TARGETS:
        fs = [f for f in fits if f["target"] == target]
        best = max(fs, key=lambda f: f["aic"])
        sel[target] = {"best_aic": best["model"], "best_effective": best["effective"],
                       "best_bic": max(fs, key=lambda f: f["bic"])["model"],
                       "table": [{k: f[k] for k in ("model", "aic", "bic", "effective", "map")} for f in fs]}
    res["model_selection"] = sel
    (out / "haem.json").write_text(json.dumps(res, indent=1))
    print(json.dumps({k: res[k] for k in ("qc", "fig29_r", "fig7c_compare", "knn_type_agreement")}, indent=1))
    print(json.dumps(res["dimension_curve"]["argmax"]), json.dumps(res["branch_clustering"]["branches"]))
    for t, s in sel.items():
        print(t, s["best_aic"], s["best_effective"], [(r["model"], round(r["aic"], 1), r["effective"]) for r in s["table"]])


if __name__ == "__main__":
    main()
