"""Application to the human network HumanBG (Fig. 1B, Figs S1-S3, Table S1, the false-positive
candidates behind Table S6, and the counts in the text).

Algorithm 2 with the authors' settings: 5 dimensions, P(edge) = 0.001, delta = 0.4, three
Gaussians, 18,000 training distances, EM stopping at a log-likelihood change below 0.01. The
training distances and the EM start are random (the authors' Matlab used rand without a fixed
state), so the run is repeated over SEEDS and the main run uses MAIN_SEED.

Usage: human.py HUMANBG.tsv SUPPLEMENT.json OUT_DIR [--seeds N]
"""
import argparse
import json
from pathlib import Path

import numpy as np

import geodenoise as gd

MAIN_SEED = 2009
CS_CUT = 0.975


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("humanbg")
    ap.add_argument("supplement")
    ap.add_argument("out")
    ap.add_argument("--seeds", type=int, default=20)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    supp = json.load(open(a.supplement))
    net = gd.read_network(a.humanbg)
    X = gd.embed(net, 5)
    D = gd.pairwise_distances(X)
    ed = D[net.edges[:, 0], net.edges[:, 1]]
    res = {"network": {"proteins": net.n, "interactions": net.m},
           "max_distance": float(D.max()),
           "edges_beyond_delta": int((ed > gd.DELTA).sum()),
           "edges_beyond_delta_fraction": float((ed > gd.DELTA).mean())}

    runs = []
    main_run = None
    for seed in [MAIN_SEED] + list(range(1, a.seeds)):
        f_edge, f_non = gd.learn_densities(net, D, rng=seed)
        sc = gd.confidence_scores(net, D, f_edge, f_non)
        hi = sc[sc["score"] >= CS_CUT]
        r = {"seed": seed, "pairs_within_delta": int(sc.size), "high": int(hi.size),
             "high_edges": int(hi["is_edge"].sum()), "high_new": int((~hi["is_edge"]).sum()),
             "edge": f_edge.to_dict(), "nonedge": f_non.to_dict()}
        runs.append(r)
        if seed == MAIN_SEED:
            main_run = (f_edge, f_non, sc, hi)
        print(f"seed {seed}: {r['high']} pairs with CS >= {CS_CUT}, {r['high_edges']} edges, "
              f"{r['high_new']} new", flush=True)
    res["runs"] = runs
    hs = np.array([r["high"] for r in runs])
    hn = np.array([r["high_new"] for r in runs])
    res["seed_spread"] = {"high": [int(hs.min()), int(np.median(hs)), int(hs.max())],
                          "high_new": [int(hn.min()), int(np.median(hn)), int(hn.max())],
                          "seeds": len(runs),
                          "paper_high_within_range": bool(hs.min() <= 1685 <= hs.max()),
                          "paper_new_within_range": bool(hn.min() <= 251 <= hn.max())}

    f_edge, f_non, sc, hi = main_run
    res["main"] = next(r for r in runs if r["seed"] == MAIN_SEED)
    new = hi[~hi["is_edge"]]
    with open(out / "predictions.tsv", "w") as f:
        f.write("protein_a\tprotein_b\tdistance\tscore\n")
        # sorted by the score as written, then by name: ties must not depend on rounding noise
        rows = sorted(((-round(float(r["score"]), 6), net.nodes[r["i"]], net.nodes[r["j"]], float(r["distance"]))
                       for r in new))
        for negs, a, b, dist in rows:
            f.write(f"{a}\t{b}\t{dist:.6f}\t{-negs:.6f}\n")
    fp = gd.candidate_false_positives(net, D)
    with open(out / "false_positive_candidates.tsv", "w") as f:
        f.write("protein_a\tprotein_b\tdistance\n")
        for i, j in fp:
            f.write(f"{net.nodes[i]}\t{net.nodes[j]}\t{D[i, j]:.6f}\n")

    # Table S1 against our predictions, and where the published pairs fall in our scores
    idx = {v: k for k, v in enumerate(net.nodes)}
    ours = {frozenset((net.nodes[r["i"]], net.nodes[r["j"]])) for r in new}
    s1 = [frozenset(p) for p in supp["S1"]["pairs"]]
    in_net = [p for p in s1 if all(v in idx for v in p)]
    score_of = {}
    for p in in_net:
        i, j = sorted(idx[v] for v in p)
        score_of[p] = float(D[i, j])
    post = {}
    if in_net:
        dd = np.array([score_of[p] for p in in_net])
        pe = f_edge.pdf(dd) * gd.PRIOR_EDGE
        pn = f_non.pdf(dd) * (1 - gd.PRIOR_EDGE)
        cs = (pe / (pe + pn)) / sc["posterior"].max()
        post = dict(zip(in_net, cs))
    res["table_s1"] = {
        "published": len(s1),
        "published_both_in_humanbg": len(in_net),
        "ours": len(ours),
        "overlap": len(ours & set(s1)),
        "jaccard": len(ours & set(s1)) / len(ours | set(s1)),
        "published_with_our_cs_ge_cut": int(sum(v >= CS_CUT for v in post.values())),
        "published_distance_quartiles": np.percentile(list(score_of.values()), [25, 50, 75]).tolist(),
    }

    # Fig. 1B and Figs S1-S3 (the authors plotted one point per pair with distance <= 0.4)
    xs = np.linspace(0, 1.4, 1401)
    res["fig1b"] = {"x": xs.round(4).tolist(), "p_edge": f_edge.pdf(xs).round(6).tolist(),
                    "p_nonedge": f_non.pdf(xs).round(6).tolist()}
    rng = np.random.default_rng(0)
    d = sc["distance"]
    near = np.flatnonzero(d < 0.005)
    pick = np.unique(np.r_[near[:: max(1, near.size // 4000)], rng.choice(d.size, 6000, replace=False)])
    dp = np.sort(d[pick])
    pe = f_edge.pdf(dp) * gd.PRIOR_EDGE
    pn = f_non.pdf(dp) * (1 - gd.PRIOR_EDGE)
    res["figS"] = {"distance": dp.round(6).tolist(), "s1_p_edge": pe.round(8).tolist(),
                   "s2_p_nonedge": pn.round(6).tolist(),
                   "s3_score": ((pe / (pe + pn)) / sc["posterior"].max()).round(6).tolist(),
                   "s3_posterior": (pe / (pe + pn)).round(6).tolist()}
    json.dump(res, open(out / "human.json", "w"), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k in ("network", "edges_beyond_delta",
                                                           "seed_spread", "table_s1")}, indent=1))


if __name__ == "__main__":
    main()
