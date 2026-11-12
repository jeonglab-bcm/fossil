"""Every number of the reproduction, from the paper's data and our rerun of the methods.

    analysis.py DATA_DIR MCL_DIR analysis.json [--consensus weka_predictions.csv]

DATA_DIR holds HPRD.net, OPHID.net and the unpacked DiseaseNetPreds.zip (preds/); MCL_DIR holds
the MCL clusterings written by run_mcl.sh. Two kinds of scores are used and kept apart:

- the authors' scores: the per-pair scores in the prediction files of the paper's web site;
- our scores: the methods rerun with the package diseasenet (Neighborhood, Oti, RW, Prop) and
  MCL 14-137, from the networks and the known associations alone.

Our rerun equals the authors' scores on every candidate pair (the `rerun` block). The graph
summarization (GS1-3, GS-All) and VI-Cut scores cannot be rerun (the GS code is lost), so those
methods use the authors' scores throughout.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np

import diseasenet as dn

METHODS = ["Neighborhood", "Oti1", "Oti2", "Oti3", "GS1", "GS2", "GS3", "GS-All", "MCL", "VI-CutL", "VI-CutS", "Prop", "RW"]
CLUSTERING = ["GS1", "GS2", "GS3", "GS-All", "MCL", "VI-CutL", "VI-CutS"]
FIVE = ["Neighborhood", "VI-CutL", "GS-All", "Prop", "RW"]
SELF_LOOPS = {"OPHID"}
# The prediction files call the larger-cluster VI-Cut variant "VI-CutH" (cut high in the tree) and
# the smaller-cluster one "VI-CutL" (cut low); the paper calls them VI-CutL and VI-CutS.
FILE_NAME = {"VI-CutL": "VI-CutH", "VI-CutS": "VI-CutL"}

# Threshold grids. The paper gives only their ranges (Sec. 2.3 and the supplement): 5-90% for
# neighbourhood and cluster scores, 0.01-9% for RW, 1-90% for Prop. These grids reproduce every
# point of Supplementary Fig. S1 and Fig. 2a (see README): found by search.
GRID_FRACTION = [round(0.05 * i, 2) for i in range(1, 20)]
GRID_RW = [0.0001, 0.0005, 0.001, 0.002, 0.0035, 0.005] + [round(0.01 + 0.005 * i, 3) for i in range(17)]
GRID_PROP = [0.01, 0.02, 0.03, 0.04, 0.05] + [round(0.1 + 0.05 * i, 2) for i in range(17)]


def grid(method):
    if method == "RW":
        return GRID_RW
    if method == "Prop":
        return GRID_PROP
    if method.startswith("Oti"):
        return [None]
    return GRID_FRACTION


# ------------------------------------------------------------------------------------- data
def load_authors(data: Path, net: str, kind: str = "LOC"):
    """Candidates and the authors' score arrays aligned to them."""
    preds = data / "preds"
    cands = dn.read_candidates(preds / f"locus_disease_preds-{net}-{kind}") if kind == "LOC" else None
    files = ["neighborhood", "oti", "gs", "mcl", "vicut", "prop", "rw"]
    raw = {}
    for f in files:
        raw.update(dn.read_scores(preds / f"{f}_preds-{net}-{kind}"))
    if cands is None:
        return raw
    keys = list(zip(cands.genes, cands.diseases))
    arr = {m: np.array([s[k] for k in keys]) for m, s in raw.items()}
    return cands, arr


def predicted(method, scores, theta):
    """Predictions of a method at theta from a dict of score arrays (file method names)."""
    if method == "GS-All":
        return (scores["GS1"] > theta) | (scores["GS2"] > theta) | (scores["GS3"] > theta)
    if method.startswith("Oti"):
        return scores["Oti"] >= int(method[3])
    return scores[FILE_NAME.get(method, method)] > theta


def curves(scores, known, n_known=None):
    out = {}
    for m in METHODS:
        pts = []
        for t in grid(m):
            p, r, n = dn.precision_recall(predicted(m, scores, t), known, n_known)
            pts.append({"theta": t, "precision": p, "recall": r, "n": n})
        out[m] = pts
    return out


def r1(x):
    """Round to 0.1 as R does (IEC 60559, ties to even on the binary value): 81.25 gives 81.2."""
    return None if x is None or (isinstance(x, float) and math.isnan(x)) else round(x, 1)


def plotted(points, dedup):
    """Points as the figures plot them: rounded to 0.1%, recall below 1% removed and, in Fig. 2,
    consecutive repeats removed (Supplementary Fig. S1 keeps them)."""
    out = []
    for p in points:
        rr, pp = r1(p["recall"]), r1(p["precision"])
        if pp is None or rr < 1.0:
            continue
        if dedup and out and out[-1] == [rr, pp]:
            continue
        out.append([rr, pp])
    return out


# ------------------------------------------------------------------------------------- rerun
def rerun(data: Path, mcl_dir: Path, net_name: str, cands, author_scores):
    """Our scores for Neighborhood, Oti, RW, Prop and MCL, and their agreement with the files."""
    net = dn.read_network(data / f"{net_name}.net")
    # OPHID: the authors' RW and Prop scores come back only with a self-interaction on every
    # protein (HPRD: only HPRD's own 1,839 self-interactions). Found by search (README).
    walk_net = dn.read_network(data / f"{net_name}.net", self_loops=(net_name in SELF_LOOPS))
    ann = cands.annotations()
    clusters = read_clusters(mcl_dir / f"mcl_{net_name}_I2.0.txt")
    ours = {
        "Neighborhood": dn.neighborhood_scores(net, ann, cands),
        "Oti": dn.oti_scores(net, ann, cands),
        "RW": dn.rw_scores(walk_net, ann, cands),
        "Prop": dn.prop_scores(walk_net, ann, cands),
        "MCL": dn.cluster_scores(clusters, ann, cands),
    }
    agree = {}
    for m, s in ours.items():
        t = author_scores[m]
        # the files print 12 significant digits
        rel = np.abs(s - t) / np.maximum(np.abs(t), 1e-300)
        same = (np.abs(s - t) <= 5e-12 * np.maximum(1.0, np.abs(t))) | (rel <= 1e-9)
        agree[m] = {
            "pairs": int(len(t)),
            "equal": int(same.sum()),
            "max_relative_difference": float(rel[np.isfinite(rel)].max()) if len(rel) else 0.0,
        }
    return net, ours, agree, clusters


def read_clusters(path: Path):
    with open(path, encoding="utf-8") as f:
        return [line.rstrip("\n").split("\t") for line in f if line.strip()]


# ------------------------------------------------------------------------------- per disease
def disease_stats(cands, preds_by_method):
    """{method: {disease: per-disease precision, recall, F1}}."""
    return {m: dn.per_disease(p, cands) for m, p in preds_by_method.items()}


def closest_to_10(scores, known, m):
    best = None
    for t in grid(m):
        _, r, _ = dn.precision_recall(predicted(m, scores, t), known)
        if best is None or abs(r - 10) < best[0]:
            best = (abs(r - 10), t, r)
    return best[1], best[2]


def bin10(v):
    """Ten bins of width 0.1 for a fraction in [0, 1]: [0, 0.1), ..., [0.9, 1.0]."""
    return min(int(v * 10 + 1e-9), 9)


def figure3(stats, diseases, recall_closed="left"):
    maxp, maxr = {}, {}
    for d in diseases:
        ps = [stats[m][d]["precision"] for m in METHODS if stats[m][d]["precision"] is not None]
        if not ps:
            continue
        maxp[d] = max(ps)
        maxr[d] = max(stats[m][d]["recall"] for m in METHODS)
    mat = np.zeros((10, 10), dtype=int)  # [precision bin][recall bin]
    for d in maxp:
        rb = bin10(maxr[d]) if recall_closed == "left" else max(0, min(math.ceil(maxr[d] * 10 - 1e-9) - 1, 9))
        mat[bin10(maxp[d]), rb] += 1
    return maxp, maxr, mat


def homophily(net, cands, ann):
    """Both homophily measures for each disease, as the paper's figures compute them.

    Neighbourhood homophily: for each gene of the disease, the fraction of its *annotated*
    neighbours (neighbours associated with any disease) that are associated with this disease,
    averaged over the disease's genes. Dividing by all neighbours, as the text reads, does not
    give the published bar counts; dividing by annotated neighbours gives all ten (README).
    Average pairwise distance: mean shortest path over connected pairs of the disease's genes.
    """
    annotated = {net.index[g] for gs in ann.values() for g in gs if g in net.index}
    nh, nh_text, apd = {}, {}, {}
    for d, gs in ann.items():
        s = {net.index[g] for g in gs if g in net.index}
        vals = []
        for i in s:
            na = net.neighbours(i) & annotated
            if na:
                vals.append(len(na & (s - {i})) / len(na))
        nh[d] = float(np.mean(vals)) if vals else 0.0
        t = dn.neighborhood_homophily(net, gs)
        nh_text[d] = 0.0 if t is None else t
        apd[d] = dn.average_pairwise_distance(net, gs)
    return nh, nh_text, apd


def apd_bin(v):
    return min(max(int(v) - 1, 0), 4)


def homophily_figure(stats, measure, binner, nbins, diseases, methods=FIVE):
    """Bars: mean F1 over the (method, disease) pairs of the bin where the method predicted
    something for the disease; error bars: variance over the five methods of their mean F1;
    lines: least squares of F1 on the measure over the same pairs, with Pearson's r."""
    bins = defaultdict(list)
    for d in diseases:
        if measure.get(d) is not None:
            bins[binner(measure[d])].append(d)
    counts = [len(bins[b]) for b in range(nbins)]
    bars, var, sd = [], [], []
    spreads: dict[str, list] = {}
    for b in range(nbins):
        vals = [stats[m][d]["f1"] for m in methods for d in bins[b] if stats[m][d]["predicted"] > 0]
        bars.append(float(np.mean(vals)) if vals else None)
        means = [np.mean([stats[m][d]["f1"] for d in bins[b] if stats[m][d]["predicted"] > 0]) for m in methods
                 if any(stats[m][d]["predicted"] > 0 for d in bins[b])]
        var.append(float(np.var(means)) if means else None)
        sd.append(float(np.std(means)) if means else None)
        spreads.setdefault("sd_means_ddof1", []).append(float(np.std(means, ddof=1)) if len(means) > 1 else None)
        spreads.setdefault("var_values", []).append(float(np.var(vals)) if vals else None)
        spreads.setdefault("sd_values", []).append(float(np.std(vals)) if vals else None)
        spreads.setdefault("sem_values", []).append(float(np.std(vals) / np.sqrt(len(vals))) if vals else None)
        spreads.setdefault("var_means_ddof1", []).append(float(np.var(means, ddof=1)) if len(means) > 1 else None)
    fits = {}
    for m in methods:
        pts = [(measure[d], stats[m][d]["f1"]) for d in diseases if measure.get(d) is not None and stats[m][d]["predicted"] > 0]
        x = np.array([p[0] for p in pts])
        y = np.array([p[1] for p in pts])
        pts_all = [(measure[d], stats[m][d]["f1"]) for d in diseases if measure.get(d) is not None]
        xa = np.array([p[0] for p in pts_all])
        ya = np.array([p[1] for p in pts_all])
        slope, icpt = np.polyfit(x, y, 1)
        fits[m] = {
            "n": int(len(x)),
            "slope": float(slope),
            "intercept": float(icpt),
            "r": float(np.corrcoef(x, y)[0, 1]),
            "r_all_diseases": float(np.corrcoef(xa, ya)[0, 1]),
        }
    return {"counts": counts, "bars": bars, "variance": var, "sd": sd, "spreads": spreads, "fits": fits}


def homophily_pr(stats, measure, binner, nbins, diseases, key, methods=FIVE):
    """Supplementary Fig. S2: mean precision or recall per bin, as the bars of Fig. 4."""
    bins = defaultdict(list)
    for d in diseases:
        if measure.get(d) is not None:
            bins[binner(measure[d])].append(d)
    out = []
    for b in range(nbins):
        vals = [stats[m][d][key] for m in methods for d in bins[b] if stats[m][d]["predicted"] > 0]
        out.append(float(np.mean(vals)) if vals else None)
    return out


def homophily_pr_r(stats, measure, diseases, key, methods=FIVE):
    """Pearson r of per-disease precision or recall on the measure (diseases the method predicts for)."""
    r = {}
    for m in methods:
        pts = [(measure[d], stats[m][d][key]) for d in diseases if measure.get(d) is not None and stats[m][d]["predicted"] > 0]
        x = np.array([p[0] for p in pts])
        y = np.array([p[1] for p in pts], dtype=float)
        r[m] = float(np.corrcoef(x, y)[0, 1])
    return r


# ------------------------------------------------------------------------------------ NOLOC
def noloc(net, cands, ann, clusters):
    """Every network gene against every disease, without linkage intervals (Sec. 3.2)."""
    diseases = sorted(ann)
    genes = list(net.nodes)
    all_c = dn.Candidates(
        [g for d in diseases for g in genes],
        [d for d in diseases for g in genes],
        np.array([g in ann[d] for d in diseases for g in genes], dtype=bool),
    )
    s = {
        "Neighborhood": dn.neighborhood_scores(net, ann, all_c),
        "Oti": dn.oti_scores(net, ann, all_c),
        "RW": dn.rw_scores(net, ann, all_c),
        "Prop": dn.prop_scores(net, ann, all_c),
        "MCL": dn.cluster_scores(clusters, ann, all_c),
    }
    return all_c, s


# ------------------------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data", type=Path)
    ap.add_argument("mcl", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--consensus", type=Path, help="consensus Random Forest predictions (consensus.py)")
    ap.add_argument("--skip-noloc", action="store_true")
    args = ap.parse_args()
    data = args.data
    res: dict = {"grids": {"fraction": GRID_FRACTION, "RW": GRID_RW, "Prop": GRID_PROP}}

    # ---- authors' scores, both networks
    nets = {}
    for net_name in ("HPRD", "OPHID"):
        cands, arr = load_authors(data, net_name)
        nets[net_name] = (cands, arr)

    cands, arr = nets["HPRD"]
    ann = cands.annotations()
    known = cands.known

    # ---- Sec. 2.1 counts
    hprd = dn.read_network(data / "HPRD.net")
    ophid = dn.read_network(data / "OPHID.net")
    genes_ann = {g for gs in ann.values() for g in gs}
    n_known = int(known.sum())
    res["counts"] = {
        "hprd_proteins": len(hprd),
        "hprd_interactions": hprd.n_interactions,
        "hprd_self_interactions": int(hprd.adjacency.diagonal().sum()),
        "ophid_proteins": len(ophid),
        "ophid_interactions": ophid.n_interactions,
        "diseases": len(ann),
        "annotated_genes": len(genes_ann),
        "known_associations": n_known,
        "genes_with_locus": len(set(cands.genes)),
        "genes_per_disease": n_known / len(ann),
        "diseases_per_gene": n_known / len(genes_ann),
        "candidate_pairs": len(cands),
        "genes_per_disease_intervals": len(cands) / len(ann),
        "unannotated_genes": len(hprd) - len(genes_ann),
    }

    # ---- rerun of the methods and agreement with the authors' scores
    res["rerun"] = {}
    ours_by_net = {}
    for net_name in ("HPRD", "OPHID"):
        c, a = nets[net_name]
        net, ours, agree, clusters = rerun(data, args.mcl, net_name, c, a)
        res["rerun"][net_name] = agree
        ours_by_net[net_name] = (net, ours, clusters)

    # Scores used from here on: ours where the rerun exists, the authors' for GS and VI-Cut.
    def combined(net_name):
        c, a = nets[net_name]
        s = dict(a)
        s.update(ours_by_net[net_name][1])
        return c, s

    # ---- Fig. 2 and Supp. Fig. S1 curves
    res["curves"] = {}
    for net_name in ("HPRD", "OPHID"):
        c, s = combined(net_name)
        res["curves"][net_name] = curves(s, c.known)
    res["fig2a"] = {m: plotted(res["curves"]["HPRD"][m], True) for m in METHODS}
    res["figS1"] = {m: plotted(res["curves"]["OPHID"][m], False) for m in METHODS}

    # ---- consensus (Fig. 2a)
    if args.consensus and args.consensus.exists():
        cons = json.loads(args.consensus.read_text())
        res["consensus"] = cons
        res["fig2a"]["Consensus"] = [[r1(p["recall"]), r1(p["precision"])] for p in cons["points"]]
        singles = [(p["recall"], p["precision"]) for m in METHODS for p in res["curves"]["HPRD"][m]
                   if not math.isnan(p["precision"]) and p["recall"] >= 1.0]
        res["consensus"]["pareto_optimal"] = [
            not any(r >= p["recall"] and q >= p["precision"] and (r > p["recall"] or q > p["precision"]) for r, q in singles)
            for p in cons["points"]
        ]

    # ---- Sec. 3.1 ranges over all methods (HPRD, plotted points)
    c, s = combined("HPRD")
    allpts = [(r, p) for m in METHODS for r, p in res["fig2a"][m]]
    clus = [(r, p) for m in CLUSTERING for r, p in res["fig2a"][m]]
    neigh = res["fig2a"]["Neighborhood"]
    vs = res["fig2a"]["VI-CutS"]
    res["sec31"] = {
        "precision_min": min(p for _, p in allpts),
        "precision_max": max(p for _, p in allpts),
        "recall_min": min(r for r, _ in allpts),
        "recall_max": max(r for r, _ in allpts),
        "rw_precision_max": max(p for _, p in res["fig2a"]["RW"]),
        "rw_best_single": max(allpts, key=lambda x: x[1]) in [tuple(x) for x in res["fig2a"]["RW"]] or
        max(p for _, p in allpts) == max(p for _, p in res["fig2a"]["RW"]),
        "rw_high_precision_end": res["fig2a"]["RW"][-1],
        "rw_high_recall_end": res["fig2a"]["RW"][0],
        "clustering_precision_min": min(p for _, p in clus),
        "clustering_precision_max": max(p for _, p in clus),
        "clustering_recall_min": min(r for r, _ in clus),
        "clustering_recall_max": max(r for r, _ in clus),
        "vicuts_mean_precision": float(np.mean([p for _, p in vs])),
        "vicuts_mean_recall": float(np.mean([r for r, _ in vs])),
        "neighborhood_precision_min": min(p for _, p in neigh),
        "neighborhood_precision_max": max(p for _, p in neigh),
        "neighborhood_recall_min": min(r for r, _ in neigh),
        "neighborhood_recall_max": max(r for r, _ in neigh),
        "oti1": res["fig2a"]["Oti1"][0],
        "oti2": res["fig2a"]["Oti2"][0],
        "oti3": res["fig2a"]["Oti3"][0],
        "oti4": [r1(x) for x in dn.precision_recall(s["Oti"] >= 4, c.known)[1::-1]],
    }

    vcs = [p for p in res["curves"]["HPRD"]["VI-CutS"] if not math.isnan(p["precision"])]
    res["sec31_vicuts"] = {
        "mean_precision_grid": float(np.mean([p["precision"] for p in vcs])),
        "mean_recall_grid": float(np.mean([p["recall"] for p in vcs])),
        "mean_precision_plotted": float(np.mean([p for _, p in vs])),
        "mean_recall_plotted": float(np.mean([r for r, _ in vs])),
        "mean_precision_grid_rounded": float(np.mean([r1(p["precision"]) for p in vcs])),
        "mean_precision_half_grid": float(np.mean([p["precision"] for p in vcs if p["theta"] >= 0.5])),
    }

    # ---- Sec. 3.2 baselines (HPRD)
    rng = np.random.default_rng(2010)
    by_d = defaultdict(list)
    for k, d in enumerate(c.diseases):
        by_d[d].append(k)
    reps = 1000
    pr_rand = []
    for _ in range(reps):
        pred = np.zeros(len(c), dtype=bool)
        for d, ks in by_d.items():
            x = len(ann[d])
            pred[rng.choice(ks, size=min(x, len(ks)), replace=False)] = True
        p, r, _ = dn.precision_recall(pred, c.known)
        pr_rand.append((p, r))
    p_all, r_all, _ = dn.precision_recall(np.ones(len(c), dtype=bool), c.known)
    res["sec32_baselines"] = {
        "random_precision": float(np.mean([p for p, _ in pr_rand])),
        "random_recall": float(np.mean([r for _, r in pr_rand])),
        "random_precision_sd": float(np.std([p for p, _ in pr_rand])),
        "random_reps": reps,
        "random_seed": 2010,
        "all_precision": p_all,
        "all_recall": r_all,
    }

    # ---- Sec. 3.2 without linkage intervals
    if not args.skip_noloc:
        net, _, clusters = ours_by_net["HPRD"]
        all_c, ns = noloc(net, c, ann, clusters)
        authors_nl = load_authors(data, "HPRD", "NOLOC")
        # agreement with the thresholded NOLOC files
        idx = {(g, d): k for k, (g, d) in enumerate(zip(all_c.genes, all_c.diseases))}
        nl_agree = {}
        for m, fname in (("Neighborhood", "Neighborhood"), ("Oti", "Oti"), ("RW", "RW"), ("Prop", "Prop"), ("MCL", "MCL")):
            pairs = authors_nl.get(fname, {})
            eq = 0
            for (g, d), v in pairs.items():
                k = idx.get((g, d))
                if k is not None and abs(ns[m][k] - v) <= 1e-9 * max(1.0, abs(v)):
                    eq += 1
            nl_agree[m] = {"pairs_in_file": len(pairs), "equal": eq, "file_minimum": min(pairs.values()) if pairs else None}
        nl_scores = dict(ns)
        nl_curves = {}
        for m in ["Neighborhood", "Oti1", "Oti2", "Oti3", "MCL", "Prop", "RW"]:
            nl_curves[m] = [
                {"theta": t, **dict(zip(("precision", "recall", "n"), dn.precision_recall(predicted(m, nl_scores, t), all_c.known)))}
                for t in grid(m)
            ]
        # GS and VI-Cut: only the thresholded files (scores >= 1/3); recall over all known pairs
        known_set = {(g, d) for d, gs in ann.items() for g in gs}
        for m in ["GS1", "GS2", "GS3", "GS-All", "VI-CutL", "VI-CutS"]:
            pts = []
            for t in GRID_FRACTION:
                if m == "GS-All":
                    pr_set = {k for f in ("GS1", "GS2", "GS3") for k, v in authors_nl.get(f, {}).items() if v > t}
                else:
                    pr_set = {k for k, v in authors_nl.get(FILE_NAME.get(m, m), {}).items() if v > t}
                tp = len(pr_set & known_set)
                complete = t >= 1 / 3 - 1e-9
                pts.append({"theta": t, "precision": 100 * tp / len(pr_set) if pr_set else float("nan"),
                            "recall": 100 * tp / n_known, "n": len(pr_set), "complete": complete})
            nl_curves[m] = pts
        res["noloc"] = {"agreement": nl_agree, "curves": nl_curves, "pairs": len(all_c)}

        def rng_of(ms, key, complete_only=True):
            vals = [p[key] for m in ms for p in nl_curves[m]
                    if not math.isnan(p["precision"]) and p["recall"] >= 1.0 and (p.get("complete", True) or not complete_only)]
            return (min(vals), max(vals)) if vals else (None, None)

        def argext(ms, key, fn):
            best = None
            for m in ms:
                for p in nl_curves[m]:
                    if math.isnan(p["precision"]) or p["recall"] < 1.0 or not p.get("complete", True):
                        continue
                    if best is None or fn(p[key], best[0]):
                        best = (p[key], m)
            return best

        res["sec32_noloc"] = {
            "rw_precision": rng_of(["RW", "Prop"], "precision"),
            "rw_recall": rng_of(["RW", "Prop"], "recall"),
            "clustering_precision_min": argext(CLUSTERING, "precision", lambda a, b: a < b),
            "clustering_precision_max": argext(CLUSTERING, "precision", lambda a, b: a > b),
            "clustering_recall_min": argext(CLUSTERING, "recall", lambda a, b: a < b),
            "clustering_recall_max": argext(CLUSTERING, "recall", lambda a, b: a > b),
        }
        # Supplementary Table 1: scores of the literature-backed pairs (our NOLOC rerun)
        table = [("PRMT2", "Myocardial"), ("PSMA5", "Myocardial"), ("BCAS2", "Myocardial"), ("ALOX5", "Myocardial"),
                 ("MYC", "Cleft"), ("MDM2", "Melanoma"), ("ATM", "Pancreatic")]
        t1 = {}
        for g, d in table:
            k = idx.get((g, d))
            row = {}
            if k is not None:
                for m in ("Neighborhood", "Oti", "MCL", "Prop", "RW"):
                    row[m] = float(ns[m][k])
            for f in ("GS1", "GS2", "GS3", "VI-CutH", "VI-CutL"):
                v = authors_nl.get(f, {}).get((g, d))
                if v is not None:
                    row[{"VI-CutH": "VI-CutL", "VI-CutL": "VI-CutS"}.get(f, f) + " (authors' file)"] = v
            t1[f"{g}|{d}"] = row
        res["suppT1"] = t1

    # ---- per disease at about 10% recall (Fig. 3, Sec. 3.3, Fig. 4, Sec. 3.5, Supp. Fig. S2)
    thr = {}
    preds = {}
    for m in METHODS:
        t, r = closest_to_10(s, c.known, m)
        thr[m] = {"theta": t, "recall": r}
        preds[m] = predicted(m, s, t)
    res["thresholds_10pct"] = thr
    stats = disease_stats(c, preds)
    diseases = sorted(ann)
    maxp, maxr, mat = figure3(stats, diseases)
    _, _, mat_right = figure3(stats, diseases, recall_closed="right")
    n_methods_over90 = {d: sum(1 for m in METHODS if (stats[m][d]["precision"] or 0) > 0.9) for d in diseases}
    predicted_by = {d: [m for m in METHODS if stats[m][d]["predicted"] > 0] for d in diseases}
    supp4 = [d for d in diseases if len(predicted_by[d]) >= 7 and min(stats[m][d]["precision"] for m in predicted_by[d]) >= 0.9]
    res["fig3"] = {
        "matrix": mat.tolist(),
        "matrix_recall_right_closed": mat_right.tolist(),
        "rows_top_down": mat.sum(axis=1)[::-1].tolist(),
        "columns": mat.sum(axis=0).tolist(),
        "columns_recall_right_closed": mat_right.sum(axis=0).tolist(),
        "diseases": len(maxp),
    }
    both = sorted(d for d in maxp if maxp[d] > 0.9 and maxr[d] > 0.9 and len(ann[d]) >= 3)
    res["sec33"] = {
        "max_precision_over_90": sum(1 for d in maxp if maxp[d] > 0.9),
        "max_precision_under_10": sum(1 for d in maxp if maxp[d] < 0.1),
        "half_methods_over_90": sum(1 for d in diseases if n_methods_over90[d] >= 7),
        "supp4_rule_count": len(supp4),
        "supp4_rule_diseases": supp4,
        "both_over_90_three_genes": both,
        "fanconi": [maxp.get("Fanconi"), maxr.get("Fanconi")],
    }

    net = ours_by_net["HPRD"][0]
    nh, nh_text, apd = homophily(net, c, ann)
    res["fig4a"] = homophily_figure(stats, nh, bin10, 10, diseases)
    res["fig4a_text_definition"] = {"counts": homophily_figure(stats, nh_text, bin10, 10, diseases)["counts"]}
    res["fig4b"] = homophily_figure(stats, apd, apd_bin, 5, diseases)
    res["figS2"] = {
        "a_precision": homophily_pr(stats, nh, bin10, 10, diseases, "precision"),
        "a_recall": homophily_pr(stats, nh, bin10, 10, diseases, "recall"),
        "b_precision": homophily_pr(stats, apd, apd_bin, 5, diseases, "precision"),
        "b_recall": homophily_pr(stats, apd, apd_bin, 5, diseases, "recall"),
        "r": {
            "a_precision": homophily_pr_r(stats, nh, diseases, "precision"),
            "a_recall": homophily_pr_r(stats, nh, diseases, "recall"),
            "b_precision": homophily_pr_r(stats, apd, diseases, "precision"),
            "b_recall": homophily_pr_r(stats, apd, diseases, "recall"),
        },
    }
    # Sec. 3.5
    correct = {m: preds[m] & c.known for m in FIVE}
    uniq = {}
    for m in FIVE:
        others = np.zeros(len(c), dtype=bool)
        for o in FIVE:
            if o != m:
                others |= correct[o]
        uniq[m] = 100.0 * int((correct[m] & ~others).sum()) / int(correct[m].sum())
    union = np.zeros(len(c), dtype=bool)
    inter = np.ones(len(c), dtype=bool)
    for m in FIVE:
        union |= preds[m]
        inter &= preds[m]
    res["sec35"] = {
        "uniqueness": uniq,
        "predictions": int(union.sum()),
        "wrong_by_all_five": int((inter & ~c.known).sum()),
        "wrong_by_all_five_pct": 100.0 * int((inter & ~c.known).sum()) / int(union.sum()),
    }
    args.out.write_text(json.dumps(res, indent=1, default=float))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
