"""Static model and Fig. 2: leave-two-out DC-kNN on the gold standard.

train.py RUN OUTDIR

Writes OUTDIR/fig2.json (Figs 2A to 2E numbers), OUTDIR/model.json (feature sets chosen for each
location on the whole gold standard) and RUN/static_sets.npz is not kept (recomputed where needed).
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import dump, load_proteome, load_studies  # noqa: E402
from settings import K, LOCATIONS, RHO, SEED  # noqa: E402

from condloc import dcknn, features, network  # noqa: E402
from condloc.model import knn_counts, leave_two_out, network_sets, train  # noqa: E402

S_NAMES = list(features.S_SETS)


def kinds(names):
    out = {"S": [], "N1": [], "N2": [], "L1": [], "L2": []}
    for m in names:
        if m.startswith("N1_"):
            out["N1"].append(m)
        elif m.startswith("N2_"):
            out["N2"].append(m)
        elif m in ("L1", "L2"):
            out[m].append(m)
        else:
            out["S"].append(m)
    return out


def correlation_matrix(studies, genes, min_samples=10):
    """Pearson r of every gene pair, averaged over studies (weighted by samples) where both genes are measured;
    NaN where those studies hold fewer than min_samples samples together."""
    idx = {g: i for i, g in enumerate(genes)}
    n = len(genes)
    tot = np.zeros((n, n), dtype=np.float32)
    wt = np.zeros((n, n), dtype=np.float32)
    for g, x, _ in studies:
        rows = np.array([idx[a] for a in g if a in idx])
        sub = np.array([i for i, a in enumerate(g) if a in idx])
        z = x[sub] - x[sub].mean(axis=1, keepdims=True)
        sd = np.sqrt((z * z).sum(axis=1))
        sd[sd == 0] = np.inf
        z = (z / sd[:, None]).astype(np.float32)
        r = z @ z.T
        w = np.float32(x.shape[1])
        tot[np.ix_(rows, rows)] += r * w
        wt[np.ix_(rows, rows)] += w
    with np.errstate(invalid="ignore", divide="ignore"):
        out = tot / wt
    out[wt < min_samples] = np.nan
    np.fill_diagonal(out, np.nan)
    return out


def fig2a(p, studies_normal, seed):
    """Share of protein pairs sharing a location: all pairs and links split by the sign of their expression
    correlation in normal brain (Fisher z test at P < 0.05), and random link sets (1000)."""
    known = np.flatnonzero(p.known)
    genes = [p.accessions[i] for i in known]
    r = correlation_matrix(studies_normal, genes)
    n_eff = sum(x.shape[1] for _, x, _ in studies_normal) / len(studies_normal)
    crit = np.tanh(1.959964 / np.sqrt(max(n_eff - 3, 1)))
    lab = p.labels[known].astype(np.float32)
    share = (lab @ lab.T) > 0
    iu = np.triu_indices(len(known), 1)
    rv, sv = r[iu], share[iu]
    ok = ~np.isnan(rv)
    out = {"threshold_r": crit}

    def split(rr, ss):
        return {"positive": float(ss[rr > crit].mean()), "none": float(ss[np.abs(rr) <= crit].mean()),
                "negative": float(ss[rr < -crit].mean()),
                "n": {"positive": int((rr > crit).sum()), "none": int((np.abs(rr) <= crit).sum()),
                      "negative": int((rr < -crit).sum())}}

    out["all_pairs"] = split(rv[ok], sv[ok])
    pos = {a: i for i, a in enumerate(known)}
    e = np.array([(pos[i], pos[j]) for i, j in p.edges if i in pos and j in pos])
    er = r[e[:, 0], e[:, 1]]
    es = share[e[:, 0], e[:, 1]]
    k = ~np.isnan(er)
    out["ppi"] = split(er[k], es[k])
    out["ppi_all"] = float(es.mean())
    # test of positive against negative links: two-proportion z test
    a, b = out["ppi"]["positive"], out["ppi"]["negative"]
    na, nb = out["ppi"]["n"]["positive"], out["ppi"]["n"]["negative"]
    pool = (a * na + b * nb) / (na + nb)
    z = (a - b) / np.sqrt(pool * (1 - pool) * (1 / na + 1 / nb))
    from scipy.stats import norm
    out["ppi_pos_minus_neg"] = a - b
    out["ppi_pos_minus_neg_p"] = float(2 * norm.sf(abs(z)))
    rng = np.random.default_rng(seed)
    m = len(e)
    rand = []
    for _ in range(1000):
        u = rng.integers(0, len(known), m)
        v = rng.integers(0, len(known), m)
        keep = u != v
        rand.append(float(share[u[keep], v[keep]].mean()))
    out["random"] = float(np.mean(rand))
    out["random_sd"] = float(np.std(rand))
    return out


def fig2c(p, studies, edges_set, xs):
    """Share of known links among the top-k most correlated protein pairs of each condition, and among the
    pairs common to the top-k lists of all three conditions. A pair's correlation is averaged over the studies
    of the condition that measure both genes, when they hold at least 10 samples together."""
    net = sorted({i for e in p.edges for i in e})
    out = {"x": xs}
    tops = {}
    for cond, st in studies.items():
        genes_all = set.union(*[set(g) for g, _, _ in st])
        idx = [i for i in net if p.accessions[i] in genes_all]
        r = correlation_matrix(st, [p.accessions[i] for i in idx])
        iu = np.triu_indices(len(idx), 1)
        rv = np.nan_to_num(r[iu], nan=-2.0)
        order = np.argsort(-rv, kind="stable")[: max(xs)]
        ia, ib = np.array(idx)[iu[0][order]], np.array(idx)[iu[1][order]]
        key = np.minimum(ia, ib).astype(np.int64) * 100000 + np.maximum(ia, ib)
        hit = np.isin(key, edges_set)
        cum = np.cumsum(hit)
        out[cond] = [float(cum[x - 1] / x) for x in xs]
        out[f"{cond}_genes"] = len(idx)
        out[f"{cond}_random"] = float(len([1 for i, j in p.edges if i in set(idx) and j in set(idx)]) /
                                      (len(idx) * (len(idx) - 1) / 2))
        tops[cond] = key
        del r
    common = []
    for x in xs:
        s = set(tops["normal"][:x]) & set(tops["low"][:x]) & set(tops["high"][:x])
        arr = np.fromiter(s, dtype=np.int64)
        common.append(float(np.isin(arr, edges_set).mean()) if len(arr) else float("nan"))
    out["common"] = common
    out["random"] = float(np.mean([out[f"{c}_random"] for c in studies]))
    return out


def correlated_adjacency(p, studies_normal, m):
    """The m most positively correlated pairs of network proteins in normal brain, as a network."""
    net = sorted({i for e in p.edges for i in e})
    genes_all = set.union(*[set(g) for g, _, _ in studies_normal])
    idx = np.array([i for i in net if p.accessions[i] in genes_all])
    r = correlation_matrix(studies_normal, [p.accessions[i] for i in idx])
    iu = np.triu_indices(len(idx), 1)
    rv = np.nan_to_num(r[iu], nan=-2.0)
    top = np.argpartition(-rv, m)[:m]
    e = np.stack([idx[iu[0][top]], idx[iu[1][top]]], axis=1)
    return network.adjacency(len(p.accessions), e)


def evaluate(counts, labels, names, seed):
    res = leave_two_out(counts, labels, names, seed, K)
    fpr = np.linspace(0, 1, 101)
    tprs = []
    for loc in range(labels.shape[1]):
        f, t = dcknn.roc_curve(res["confidence"][:, loc], labels[:, loc])
        tprs.append(np.interp(fpr, f, t))
    return {"auc": res["auc"], "mean_auc": float(np.mean(res["auc"])), "roc_fpr": fpr,
            "roc_tpr": np.mean(tprs, axis=0)}


def main(run: Path, out: Path) -> None:
    t0 = time.time()
    out.mkdir(parents=True, exist_ok=True)
    p, symbol = load_proteome(run)
    print(f"proteome {len(p.accessions)} proteins, {int(p.known.sum())} known, {len(p.edges)} links "
          f"({time.time() - t0:.0f} s)", flush=True)
    sets = dict(p.s)
    sets.update(network_sets(p, rho=RHO))
    names = S_NAMES + [f"N1_{x}" for x in S_NAMES] + [f"N2_{x}" for x in S_NAMES] + ["L1", "L2"]
    gold = np.flatnonzero(p.known)
    labels = p.labels[gold]
    counts = knn_counts({m: sets[m] for m in names}, p, query=gold, train=gold)
    print(f"29 feature sets and kNN ({time.time() - t0:.0f} s)", flush=True)

    # Fig. 2D: single-set AUC averaged over locations and over the sets of each kind; TR = selected models (LTOCV)
    single = {m: [dcknn.auc(counts[m][:, loc], labels[:, loc]) for loc in range(len(LOCATIONS))] for m in names}
    kd = kinds(names)
    fig2d = {kind: float(np.mean([np.mean(single[m]) for m in ms])) for kind, ms in kd.items()}
    ltocv = evaluate(counts, labels, names, SEED)
    fig2d["TR"] = ltocv["mean_auc"]
    print(f"Fig 2D {fig2d} ({time.time() - t0:.0f} s)", flush=True)

    # final models on the whole gold standard; Fig. 2E
    model, paths = train(counts, labels, np.arange(len(gold)), names, K)
    fig2e = {"sets": names, "locations": LOCATIONS,
             "selected": {LOCATIONS[loc]: s for loc, s in model.selected.items()},
             "first": {LOCATIONS[loc]: s[0] for loc, s in model.selected.items()},
             "single_auc": single, "location_auc": dict(zip(LOCATIONS, ltocv["auc"])),
             "set_mean_auc": {m: float(np.mean(v)) for m, v in single.items()},
             "selection_path": {LOCATIONS[loc]: v for loc, v in paths.items()}}
    sel_kind = {kind: sum(1 for s in model.selected.values() for m in s if m in ms) for kind, ms in kd.items()}
    fig2e["selected_by_kind"] = sel_kind

    # Fig. 2B: physical links, correlated pairs (as many as the physical links), and single-protein sets
    studies = load_studies(run)
    corr = correlated_adjacency(p, studies["normal"], len(p.edges))
    csets = network_sets(p, adj=corr, rho=RHO, prefix="C", plcp_adj=corr)
    cnames = list(csets)
    ccounts = knn_counts(csets, p, query=gold, train=gold)
    allc = {**counts, **ccounts}
    pnames = [m for m in names if m not in S_NAMES]
    configs = {"single+physical+correlated": names + cnames, "physical+correlated": pnames + cnames,
               "physical": pnames, "correlated": cnames}
    fig2b = {}
    for key, cand in configs.items():
        fig2b[key] = evaluate(allc, labels, cand, SEED)
        print(f"Fig 2B {key} {fig2b[key]['mean_auc']:.3f} ({time.time() - t0:.0f} s)", flush=True)

    fig2a_res = fig2a(p, studies["normal"], SEED)
    print(f"Fig 2A {fig2a_res['ppi']} ({time.time() - t0:.0f} s)", flush=True)
    edge_keys = np.sort(p.edges[:, 0].astype(np.int64) * 100000 + p.edges[:, 1])
    xs = [100, 300, 1000, 3000, 10000, 30000, 100000, 300000, 1000000]
    fig2c_res = fig2c(p, studies, edge_keys, xs)
    print(f"Fig 2C done ({time.time() - t0:.0f} s)", flush=True)

    dump({"fig2a": fig2a_res, "fig2b": fig2b, "fig2c": fig2c_res, "fig2d": fig2d, "fig2e": fig2e,
          "gold_proteins": len(gold), "network_links": len(p.edges)}, out / "fig2.json")
    dump({"selected": fig2e["selected"], "weights": {LOCATIONS[loc]: {m: model.weights[loc][m] for m in s}
                                                    for loc, s in model.selected.items()}}, out / "model.json")
    print(f"done ({time.time() - t0:.0f} s)")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
