"""Yeast test of the method (Figs 1A, 2, 3, 4 and 5) on Yhigh.

Yhigh is the largest connected component of Collins et al.'s high-confidence network (PE >= 3.19);
the test positives are Collins' low-confidence pairs (1.85 <= PE < 3.19) between Yhigh proteins,
and the universe is every pair of Yhigh proteins that is not an edge.

Usage: yeast.py YHIGH.tsv LOW.tsv OUT_DIR [--fig4-max-iter N] [--fig5-repeats N]
Writes OUT_DIR/yeast.json (curves at the paper's epsilon grid, dense ROC summaries, Fig. 1A
mixtures, Fig. 4 iterations, Fig. 5 deletions) and OUT_DIR/roc_dense.csv.
"""
import argparse
import json
import time
from pathlib import Path

import numpy as np
from scipy.sparse.linalg import ArpackError

import geodenoise as gd

# The epsilon grid behind the published markers (read from Fig. 2: dim 2 points at 0.2 ... 0.9
# fall on the markers, and the dim 7 labels sit at 0.2, 0.3, 0.4, 0.5).
EPS_GRID = [round(0.01 * k, 2) for k in range(1, 11)] + [round(0.1 * k, 1) for k in range(2, 15)]
FIG2_LABELS = {"0.2": (1776, 10725), "0.3": (3454, 26718), "0.4": (4312, 47227), "0.5": (4793, 73331)}
SEED = 2009


def nonedge_universe(net):
    A = net.adjacency().toarray().astype(bool)
    iu, ju = np.triu_indices(net.n, 1)
    keep = ~A[iu, ju]
    return iu[keep], ju[keep]


def labels(net, ni, nj, pairs):
    idx = {v: k for k, v in enumerate(net.nodes)}
    code = set()
    for a, b in pairs:
        if a in idx and b in idx:
            i, j = sorted((idx[a], idx[b]))
            code.add(i * net.n + j)
    return np.isin(ni * net.n + nj, np.fromiter(code, dtype=np.int64))


def grid_points(d, pos, P, N, grid):
    out = []
    for e in grid:
        s = d < e
        tp = int((s & pos).sum())
        fp = int((s & ~pos).sum())
        out.append({"eps": e, "tp": tp, "fp": fp, "sens": tp / P, "fpr": fp / N,
                    "precision": tp / (tp + fp) if tp + fp else None, "recall": tp / P})
    return out


def dense_summary(d, pos):
    thr, tp, fp, P, N = gd.roc_curve(d, pos)
    k = np.searchsorted(fp / N, 0.15, side="right") - 1
    rec = tp / P
    prec = tp / (tp + fp)
    j = np.searchsorted(rec, 0.35)
    return {
        "auc": gd.auc(tp, fp, P, N),
        "sens_at_spec_0.85": float(tp[k] / P),
        "precision_at_recall_0.35": float(prec[j]),
        "max_distance": float(d.max()),
    }, (thr, tp, fp, P, N)


# False-positive rates at which Fig. 5's deletions are averaged (vertical averaging of ROC curves):
# fine near 0, where the curves rise steeply
FIG5_FPR = ([round(0.0002 * i, 4) for i in range(100)] + [round(0.02 + 0.001 * i, 3) for i in range(80)]
            + [round(0.1 + 0.005 * i, 3) for i in range(181)])


def sens_at_fpr(d, pos, k, n_all, grid=FIG5_FPR):
    """One deletion's full ROC curve, every deleted edge a positive (k) and every non-edge of Yhigh a
    negative (n_all), read as sensitivity at each false-positive rate of grid (linear between the
    curve's points, and from its last point to (1, 1) when the embedding left pairs out)."""
    _, tp, fp, _, _ = gd.roc_curve(d, pos)
    last = np.r_[np.flatnonzero(np.diff(fp)), fp.size - 1]  # highest tp at each fp
    x = np.r_[0.0, fp[last] / n_all, 1.0]
    y = np.r_[0.0, tp[last] / k, 1.0]
    if x[1] == 0.0:
        x, y = x[1:], y[1:]
    if x[-2] == 1.0:
        x, y = x[:-1], y[:-1]
    return np.interp(grid, x, y)


def iterate(net, dim, eps, max_iter, ni, nj):
    """Algorithm 1 iterated: add the predictions and re-embed until no new pair is predicted."""
    edges = net.edges
    added = np.zeros(0, dtype=np.int64)
    history = []
    for it in range(1, max_iter + 1):
        cur = gd.Network(net.nodes, edges)
        try:
            D = gd.pairwise_distances(gd.embed(cur, dim))
        except (ValueError, ArpackError):
            # the graph has become so dense that the leading eigenvalues are not positive: the
            # embedding collapses and every remaining pair is within epsilon
            history.append("degenerate")
            return np.ones(ni.size, dtype=bool), it, history
        new = gd.predict(cur, D, eps)
        history.append(int(new.shape[0]))
        if new.shape[0] == 0:
            break
        edges = np.vstack([edges, new])
        added = np.r_[added, new[:, 0] * net.n + new[:, 1]]
    return np.isin(ni * net.n + nj, added), it, history


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("yhigh")
    ap.add_argument("low")
    ap.add_argument("out")
    ap.add_argument("--wrong-truth", help="edge list of a wrong truth set (negative control)")
    ap.add_argument("--fig4-max-iter", type=int, default=50)
    ap.add_argument("--fig5-repeats", type=int, default=10)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    net = gd.read_network(a.yhigh)
    low = gd.read_network(a.low)
    low_pairs = [(low.nodes[i], low.nodes[j]) for i, j in low.edges]
    ni, nj = nonedge_universe(net)
    pos = labels(net, ni, nj, low_pairs)
    P, N = int(pos.sum()), int((~pos).sum())
    res = {"network": {"proteins": net.n, "interactions": net.m}, "positives": P, "negatives": N,
           "eps_grid": EPS_GRID, "dims": {}}
    L = gd.path_lengths(net)
    dense_rows = []
    wpos = None
    if a.wrong_truth:
        w = gd.read_network(a.wrong_truth)
        wpos = labels(net, ni, nj, [(w.nodes[i], w.nodes[j]) for i, j in w.edges])
        res["wrong_truth"] = {"positives": int(wpos.sum()), "dims": {}}
    for dim in range(2, 8):
        X = gd.embed(net, dim, lengths=L)
        D = gd.pairwise_distances(X)
        d = D[ni, nj]
        summ, (thr, tp, fp, _, _) = dense_summary(d, pos)
        summ["grid"] = grid_points(d, pos, P, N, [e for e in EPS_GRID if e <= d.max() + 0.1])
        res["dims"][str(dim)] = summ
        if wpos is not None:
            wP, wN = int(wpos.sum()), int((~wpos).sum())
            ws, _ = dense_summary(d, wpos)
            ws["grid"] = grid_points(d, wpos, wP, wN, [e for e in EPS_GRID if e <= d.max() + 0.1])
            res["wrong_truth"]["dims"][str(dim)] = ws
        # counts at fixed distances (not at fixed indices, which shift with rounding noise)
        ds = np.sort(d)
        ps = np.cumsum(pos[np.argsort(d, kind="stable")])
        for t in np.round(np.linspace(0, 1.5, 1501), 3):
            k = int(np.searchsorted(ds, t, side="right"))
            ntp = int(ps[k - 1]) if k else 0
            dense_rows.append((dim, float(t), ntp, k - ntp))
        if dim == 5:  # Fig. 1A: densities after embedding in 5 dimensions
            f_edge, f_non = gd.learn_densities(net, D, size=net.m, rng=SEED)
            xs = np.linspace(0, 1.4, 1401)
            res["fig1a"] = {"edge": f_edge.to_dict(), "nonedge": f_non.to_dict(),
                            "learn_set_size": net.m, "seed": SEED,
                            "max_distance_all_pairs": float(D.max()),
                            "x": xs.round(4).tolist(),
                            "p_edge": f_edge.pdf(xs).round(6).tolist(),
                            "p_nonedge": f_non.pdf(xs).round(6).tolist()}
        print(f"dim {dim}: AUC {summ['auc']:.3f} ({time.time() - t0:.0f} s)", flush=True)
    g7 = {f"{p['eps']}": p for p in res["dims"]["7"]["grid"]}
    res["fig2_labels"] = [{"eps": e, "paper_tp": tp, "paper_fp": fp, "tp": g7[e]["tp"], "fp": g7[e]["fp"]}
                          for e, (tp, fp) in FIG2_LABELS.items()]

    # Fig. 4: dimension 4, one iteration against iterating to convergence, at each epsilon.
    fig4 = []
    for e in [e for e in EPS_GRID if e <= 1.3]:
        pred, its, hist = iterate(net, 4, e, a.fig4_max_iter, ni, nj)
        tp, fp = int((pred & pos).sum()), int((pred & ~pos).sum())
        fig4.append({"eps": e, "iterations": its, "new_per_iteration": hist, "tp": tp, "fp": fp,
                     "sens": tp / P, "fpr": fp / N})
        print(f"fig4 eps {e}: {its} iterations, sens {tp / P:.3f} fpr {fp / N:.3f} "
              f"({time.time() - t0:.0f} s)", flush=True)
    res["fig4"] = {"converged": fig4, "one_iteration": res["dims"]["4"]["grid"]}

    # Fig. 5: delete k random edges from Yhigh, embed what is left, recover the deleted edges.
    # Each deletion is embedded twice: the largest component only (the method's rule) and every
    # protein, including those the deletion cut off (embed_novi.m puts them at the unreachable
    # distance). Neither embedding draws random numbers, so the deletions are the same for both.
    # Each deletion's full ROC curve is kept as sensitivity at the false-positive rates of FIG5_FPR;
    # fig5_roc holds their mean (the curves of Fig. 5).
    rng = np.random.default_rng(SEED)
    n_all = net.n * (net.n - 1) // 2 - net.m
    fig5, fig5_roc = {}, {}
    for dim in (4, 5, 7):
        for k in (500, 1000, 2000, 3000):
            runs = []
            sens = {"lcc": [], "whole": []}
            for r in range(a.fig5_repeats):
                drop = rng.choice(net.m, size=k, replace=False)
                keep = np.ones(net.m, dtype=bool)
                keep[drop] = False
                cur = gd.Network(net.nodes, net.edges[keep])
                dropped = {frozenset((net.nodes[x], net.nodes[y])) for x, y in net.edges[drop]}
                lcc = gd.largest_component(cur)
                summ = None
                for name, g in (("lcc", lcc), ("whole", cur)):
                    D = gd.pairwise_distances(gd.embed(g, dim))
                    ci, cj = nonedge_universe(g)
                    cpos = labels(g, ci, cj, [tuple(e) for e in dropped])
                    cP, cN = int(cpos.sum()), int((~cpos).sum())
                    d = D[ci, cj]
                    s, _ = dense_summary(d, cpos)
                    s["grid"] = grid_points(d, cpos, cP, cN, [e for e in EPS_GRID if e <= d.max() + 0.1])
                    s["positives"] = cP
                    sens[name].append(sens_at_fpr(d, cpos, k, n_all))
                    if name == "lcc":
                        summ = s
                        summ["lcc_proteins"] = lcc.n
                    else:
                        summ["whole"] = {"auc": s["auc"], "grid": s["grid"], "positives": cP}
                runs.append(summ)
            fig5[f"{dim}:{k}"] = runs
            for name, v in sens.items():
                m = np.mean(v, axis=0)
                aucs = [float(np.trapezoid(t, FIG5_FPR)) for t in v]
                fig5_roc[f"{dim}:{k}:{name}"] = {
                    "sens": [round(float(t), 6) for t in m],
                    "auc": round(float(np.trapezoid(m, FIG5_FPR)), 6),
                    "auc_range_over_repeats": [round(min(aucs), 6), round(max(aucs), 6)]}
            print(f"fig5 dim {dim} k {k}: AUC {np.mean([r['auc'] for r in runs]):.3f} largest component, "
                  f"{np.mean([r['whole']['auc'] for r in runs]):.3f} every protein "
                  f"({time.time() - t0:.0f} s)", flush=True)
    res["fig5"] = fig5
    res["fig5_roc"] = {"fpr": FIG5_FPR, "negatives": n_all, "curves": fig5_roc}
    json.dump(res, open(out / "yeast.json", "w"), indent=1)
    with open(out / "roc_dense.csv", "w") as f:
        f.write("dim,threshold,tp,fp\n")
        for r in dense_rows:
            f.write(f"{r[0]},{r[1]:.3f},{r[2]},{r[3]}\n")


if __name__ == "__main__":
    main()
