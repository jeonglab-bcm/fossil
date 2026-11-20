"""Run the paper's analyses on Additional file 2 with the package mutbench.

Usage: analyze.py XLSX OUT.json OUT_COMBINATIONS.npz

OUT.json (committed as output/analysis.json) holds every number the comparison uses: the counts of
Tables 1 and 2, the performance of Tables 3 and 4 and Additional file 16 with bootstrap intervals and the
Monte Carlo spread of those intervals, the kappa matrices, the clustering, the low-confidence counts, the
training-set counts and the summaries of the combination analysis (counts against the best predictors,
top-five lists, recurrence, optimal p and n) for a main run and a second run with another seed.
OUT_COMBINATIONS.npz (not committed) holds the mean and interval of every combination for the comparison
with Additional files 17 and 18.

Seeds are fixed, so a rerun gives the same numbers.
"""
import json
import math
import sys

import numpy as np

import mutbench as mb
from data import META, PRED, SINGLE, TRAINING, load, snvs

N_BOOT = 1000
N_SPLITS = 1000
BOOT_REPLICATES = 20  # extra bootstrap runs to measure the Monte Carlo spread of each interval end
SEED_BOOT = 20141028
SEED_SPLITS = (1, 2)  # main run, second run
TOPS = (10, 20, 50, 100)

# Table 2's class names for each predictor's categories (lower case).
CLASS_NAMES = {
    "driver": "Driver", "passenger": "Passenger", "cancer": "CANCER", "passenger/other": "PASSENGER/OTHER",
    "damaging": "Damaging", "tolerated": "Tolerated", "no weights": "No weights", "high": "High",
    "medium": "Medium", "low": "Low", "neutral": "Neutral", "disease_causing": "Disease_causing",
    "disease_causing_automatic": "Disease_causing_automatic", "polymorphism": "Polymorphism",
    "polymorphism_automatic": "Polymorphism_automatic", "probably damaging": "Probably damaging",
    "possibly damaging": "Possibly damaging", "benign": "Benign", "deleterious": "Deleterious",
    "functional": "Functional", "no-call": "No-call", "d": "Deleterious", "n": "Neutral",
}


def labels_of(rows):
    return mb.label_vector(r["label"] for r in rows)


def calls_of(rows):
    return {p: mb.binary_calls(r["cat"][p] for r in rows) for p in PRED}


def perf_block(rows, seed, only=None):
    """Point values, bootstrap intervals and the spread of the interval ends, per predictor."""
    y, calls = labels_of(rows), calls_of(rows)
    out = {}
    for i, p in enumerate(PRED):
        if only and p not in only:
            continue
        perf = mb.performance(y, calls[p])
        ci = mb.bootstrap_ci(y, calls[p], N_BOOT, seed + 1000 * i)
        reps = [mb.bootstrap_ci(y, calls[p], N_BOOT, seed + 1000 * i + 1 + r) for r in range(BOOT_REPLICATES)]
        sd = {k: [float(np.nanstd([rr[k][j] for rr in reps], ddof=1)) for j in (0, 1)] for k in mb.STATS}
        out[p] = {"n": perf["n"], "counts": {k: perf[k] for k in ("tp", "tn", "fp", "fn")},
                  **{k: {"value": perf[k], "low": ci[k][0], "high": ci[k][1], "mc_sd": sd[k],
                         "repeats": [[rr[k][0], rr[k][1]] for rr in reps]} for k in mb.STATS}}
    return out


def kappa_block(rows, three_category=False):
    out = {}
    if three_category:
        low = {p: mb.low_confidence(p, [r["cat"][p] for r in rows], [r["score"][p] for r in rows]) for p in PRED}
        for a in PRED:
            out[a] = {b: list(mb.kappa_categorical(low[a], low[b])) for b in PRED}
    else:
        calls = calls_of(rows)
        for a in PRED:
            out[a] = {b: list(mb.cohen_kappa(calls[a], calls[b])) for b in PRED}
    return out


def cluster_block(rows):
    calls = calls_of(rows)
    D = mb.hamming_matrix([calls[p] for p in PRED])
    merge, height = mb.hclust_complete(D)
    return {"merge": merge.tolist(), "height": height.tolist(),
            "clades": [sorted(PRED[i] for i in c) for c in mb.clades(merge)],
            "leaf_order": [PRED[i] for i in mb.leaf_order(merge)],
            "row_shares": {p: {"non-neutral": float(np.mean(calls[p] == 1)), "neutral": float(np.mean(calls[p] == 0)),
                               "no call": float(np.mean(np.isnan(calls[p])))} for p in PRED}}


def low_table(rows):
    """Additional file 8: three-category calls by functional category ([neutral, non-neutral,
    uncertain, total]); a low-confidence call is counted under 'Low confidence', the others under the
    predictor's own class."""
    out = {}
    for p in PRED:
        low = mb.low_confidence(p, [r["cat"][p] for r in rows], [r["score"][p] for r in rows])
        tab = out.setdefault(p, {})
        for r, l in zip(rows, low):
            cls = "Low confidence" if l == "low" else CLASS_NAMES[r["cat"][p].lower()]
            v = tab.setdefault(cls, [0, 0, 0, 0])
            v[["neutral", "non-neutral", "uncertain"].index(r["label"])] += 1
            v[3] += 1
    return out


def low_block(rows_sets):
    out = {}
    for name, rows in rows_sets.items():
        low = {p: np.array(mb.low_confidence(p, [r["cat"][p] for r in rows], [r["score"][p] for r in rows])) == "low"
               for p in PRED}
        per = {p: int(v.sum()) for p, v in low.items()}
        tot = np.sum([low[p] for p in PRED], axis=0)
        hist = np.bincount(tot, minlength=16)[:16].tolist()
        majority = {}
        for r, t in zip(rows, tot):
            if t >= 8:
                majority.setdefault(r["gene"], []).append(r["aa"])
        out[name] = {"per_predictor": per, "by_count": hist, "majority": {g: sorted(v) for g, v in sorted(majority.items())}}
    return out


def fisher_two_sided(a, b, c, d):
    """Fisher's exact test of the 2 x 2 table [[a, b], [c, d]], two-sided (sum of tables no more likely
    than the observed one)."""
    n1, n2, k = a + b, c + d, a + c
    lo, hi = max(0, k - n2), min(k, n1)
    def p(x):
        return math.comb(n1, x) * math.comb(n2, k - x) / math.comb(n1 + n2, k)
    p0 = p(a)
    return min(1.0, sum(p(x) for x in range(lo, hi + 1) if p(x) <= p0 * (1 + 1e-7)))


def combination_block(rows, seeds):
    y = labels_of(rows)
    calls = {p: v for p, v in calls_of(rows).items() if p in SINGLE}
    combos = mb.combinations(SINGLE)
    names = [mb.combination_name(m, p) for m, p in combos]
    members = [list(m) for m, _ in combos]
    cc = mb.combination_calls(calls, combos)
    runs, arrays = [], {}
    for seed in seeds:
        S = mb.random_splits(len(y), N_SPLITS, seed=seed)
        r = mb.split_sample(y, cc, S)
        runs.append(r)
    # Best single and meta-predictor of each statistic (point values over all labelled mutations), with
    # their bootstrap intervals: the reference of Additional file 19.
    return names, members, runs


def summarize_combinations(names, members, run, perf):
    out = {}
    best = {}
    for grp, preds in (("single", SINGLE), ("meta", META)):
        for k in mb.STATS:
            b = max(preds, key=lambda p: (perf[p][k]["value"], -preds.index(p)))
            best[(grp, k)] = b
    counts = {}
    for grp in ("single", "meta"):
        counts[grp] = {}
        for k in mb.STATS:
            ref = perf[best[(grp, k)]][k]
            res = {}
            for kind in ("mean", "significant"):
                if kind == "mean":
                    a = run["subset1"][k]["mean"] > ref["value"]
                    b = run["subset2"][k]["mean"] > ref["value"]
                else:
                    a = run["subset1"][k]["low"] >= ref["high"]
                    b = run["subset2"][k]["low"] >= ref["high"]
                res[kind] = [int(a.sum()), int(b.sum()), int((a & b).sum())]
            counts[grp][k] = {"reference": best[(grp, k)], **res}
    tops, recur, optimal = {}, {}, {}
    for sub in ("subset1", "subset2"):
        for by in ("accuracy", "composite"):
            order = mb.rank(run[sub][by]["mean"])
            tops[f"{sub}/{by}"] = [{"name": names[i], **{k: [float(run[sub][k][part][i]) for part in ("mean", "low", "high")]
                                                         for k in mb.STATS}} for i in order[:5]]
            ranked = [members[i] for i in order]
            recur[f"{sub}/{by}"] = {str(t): mb.recurrence(ranked, SINGLE, t) for t in TOPS}
    acc = run["subset1"]["accuracy"]["mean"]
    pn = [(int(n.split(" of ")[0].split()[-1]), len(m)) for n, m in zip(names, members)]
    by_p, by_n = [], []
    for p in range(1, 12):
        idx = [i for i, (pp, nn) in enumerate(pn) if pp == p]
        i = idx[int(mb.rank(acc[idx])[0])]
        by_p.append({"p": p, "n": pn[i][1], "name": names[i], "accuracy": float(acc[i])})
    for n in range(2, 12):
        idx = [i for i, (pp, nn) in enumerate(pn) if nn == n]
        i = idx[int(mb.rank(acc[idx])[0])]
        by_n.append({"p": pn[i][0], "n": n, "name": names[i], "accuracy": float(acc[i])})
    named = {}
    for nm in ("At least 1 of CHASM (breast), MutationTaster",):
        i = names.index(nm)
        named[nm] = {sub: {k: [float(run[sub][k][part][i]) for part in ("mean", "low", "high")] for k in mb.STATS}
                     for sub in ("subset1", "subset2")}
        named[nm]["rank"] = {f"{sub}/{by}": int(np.where(mb.rank(run[sub][by]["mean"]) == i)[0][0]) + 1
                             for sub in ("subset1", "subset2") for by in ("accuracy", "composite")}
    return {"n_combinations": len(names), "counts": counts, "top5": tops, "recurrence": recur,
            "optimal": {"by_p": by_p, "by_n": by_n}, "named": named}


def main():
    xlsx, out, out_npz = sys.argv[1:4]
    rows = load(xlsx)
    s = snvs(rows)
    lab = [r for r in s if r["label"] in ("non-neutral", "neutral")]
    nc = [r for r in s if r["cosmic"] is None]
    labnc = [r for r in lab if r["cosmic"] is None]
    res = {"counts": {"mutations": len(rows), "snvs": len(s), "labelled": len(lab), "non_cosmic": len(nc),
                      "labelled_non_cosmic": len(labnc),
                      "labelled_non_cosmic_by_label": {k: sum(r["label"] == k for r in labnc) for k in ("non-neutral", "neutral")}}}
    genes = sorted({r["gene"] for r in s})
    res["table1"] = {g: [sum(r["gene"] == g for r in s)] + [sum(r["gene"] == g and r["label"] == k for r in s)
                                                            for k in ("neutral", "non-neutral", "uncertain")] for g in genes}
    res["table1"]["Total"] = [len(s)] + [sum(r["label"] == k for r in s) for k in ("neutral", "non-neutral", "uncertain")]
    t2 = {}
    for p in PRED:
        t2[p] = {}
        for r in s:
            cls = CLASS_NAMES[r["cat"][p].lower()] if r["cat"][p] else "N/A"
            v = t2[p].setdefault(cls, [0, 0, 0, 0])
            v[["neutral", "non-neutral", "uncertain"].index(r["label"])] += 1
            v[3] += 1
    res["table2"] = t2
    def class_table(rows_, cols):
        t = {}
        for p in PRED:
            t[p] = {}
            for r in rows_:
                cls = CLASS_NAMES[r["cat"][p].lower()] if r["cat"][p] else "N/A"
                v = t[p].setdefault(cls, [0] * (len(cols) + 1))
                v[cols.index(r["label"])] += 1
                v[-1] += 1
        return t
    res["table2_non_cosmic"] = class_table(nc, ["neutral", "non-neutral", "uncertain"])
    res["table2_by_class"] = {k: class_table([r for r in lab if r["type"] == t], ["neutral", "non-neutral"])
                              for k, t in (("oncogenes", "Oncogene"), ("tsg", "Tumor suppressor"), ("new", "New cancer gene"))}
    res["table1_non_cosmic"] = {g: [sum(r["gene"] == g for r in nc)] + [sum(r["gene"] == g and r["label"] == k for r in nc)
                                                                      for k in ("neutral", "non-neutral", "uncertain")] for g in genes}
    res["table1_non_cosmic"]["Total"] = [len(nc)] + [sum(r["label"] == k for r in nc) for k in ("neutral", "non-neutral", "uncertain")]
    res["table3"] = perf_block(lab, SEED_BOOT)
    res["table4"] = perf_block(labnc, SEED_BOOT + 100000)
    onc = [r for r in lab if r["type"] == "Oncogene"]
    tsg = [r for r in lab if r["type"] == "Tumor suppressor"]
    new = [r for r in lab if r["type"] == "New cancer gene"]
    res["gene_classes"] = {"n": {"oncogenes": len(onc), "tsg": len(tsg), "new": len(new)},
                           "neutral": {"oncogenes": sum(r["label"] == "neutral" for r in onc), "tsg": sum(r["label"] == "neutral" for r in tsg),
                                       "new": sum(r["label"] == "neutral" for r in new)},
                           "oncogenes": perf_block(onc, SEED_BOOT + 200000), "tsg": perf_block(tsg, SEED_BOOT + 300000)}
    gc = res["gene_classes"]
    res["gene_classes"]["fisher_p"] = fisher_two_sided(gc["neutral"]["oncogenes"], gc["n"]["oncogenes"] - gc["neutral"]["oncogenes"],
                                                       gc["neutral"]["tsg"], gc["n"]["tsg"] - gc["neutral"]["tsg"])
    res["kappa"] = {"all": kappa_block(s), "non_cosmic": kappa_block(nc), "labelled": kappa_block(lab),
                    "labelled_non_cosmic": kappa_block(labnc)}
    res["kappa_low_confidence"] = {"all": kappa_block(s, True), "non_cosmic": kappa_block(nc, True),
                                   "labelled": kappa_block(lab, True), "labelled_non_cosmic": kappa_block(labnc, True)}
    res["clustering"] = {"all": cluster_block(s), "non_cosmic": cluster_block(nc), "labelled": cluster_block(lab),
                         "labelled_non_cosmic": cluster_block(labnc)}
    res["low_confidence"] = low_block({"all": s, "non_cosmic": nc, "labelled": lab, "labelled_non_cosmic": labnc})
    low_lab = {p: np.array(mb.low_confidence(p, [r["cat"][p] for r in lab], [r["score"][p] for r in lab])) == "low" for p in PRED}
    n_low = np.sum([low_lab[p] for p in PRED], axis=0)
    res["low_confidence_only"] = {p: int(np.sum(low_lab[p] & (n_low == 1))) for p in PRED}
    # Additional file 29: each training-set predictor on the labelled SNVs outside its own training set.
    res["training_excluded"] = {}
    for i, p in enumerate(TRAINING):
        rows_p = [r for r in lab if not r["training"][p]]
        res["training_excluded"][p] = perf_block(rows_p, SEED_BOOT + 400000 + 10000 * i, only=[p])[p]
    res["low_confidence_table"] = {"all": low_table(s), "non_cosmic": low_table(nc)}
    res["training_sets"] = {p: [sum(r["training"][p] for r in lab), sum(r["training"][p] for r in labnc)] for p in TRAINING}
    res["combinations"] = {}
    arrays = {}
    for key, rows_, perf in (("all", lab, res["table3"]), ("non_cosmic", labnc, res["table4"])):
        names, members, runs = combination_block(rows_, SEED_SPLITS)
        res["combinations"][key] = {f"run{j + 1}": summarize_combinations(names, members, r, perf) for j, r in enumerate(runs)}
        res["combinations"][key]["seeds"] = list(SEED_SPLITS)
        for j, r in enumerate(runs):
            for sub in ("subset1", "subset2"):
                for k in mb.STATS:
                    for part in ("mean", "sd", "n", "low", "high"):
                        arrays[f"{key}|run{j + 1}|{sub}|{k}|{part}"] = r[sub][k][part]
        arrays[f"{key}|names"] = np.array(names)
    res["settings"] = {"n_boot": N_BOOT, "boot_replicates": BOOT_REPLICATES, "seed_boot": SEED_BOOT, "n_splits": N_SPLITS,
                       "split_seeds": list(SEED_SPLITS), "subset1_share": "2/3", "package": f"mutbench {mb.__version__}"}
    with open(out, "w") as f:
        json.dump(res, f, indent=1, sort_keys=False, default=float)
        f.write("\n")
    np.savez_compressed(out_npz, **arrays)


if __name__ == "__main__":
    main()
