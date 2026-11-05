"""Table 1 and the Section 3.1 numbers: hypergeometric P of the empirical mean, per GO term.

Usage: python table1.py PUBLISHED_TABLE1.csv S1_TERMS.tsv NULL39.tsv OUT_DIR

The paper: N = 15,733 genes with a biological-process term, n = 10,057 targets of the 39 Sokolov
miRNAs; for each term of size K, P = Pr(X >= m) for X ~ Hypergeometric(N, K, n), m = the empirical
mean number of term genes targeted by 39 random miRNAs. Supplementary Table S1's 9,462 P-values are
reproduced with m = floor(mean), not the rounded mean the caption names.

Writes OUT_DIR/table1.csv (published top 10: paper, recomputed from S1, ours) and
OUT_DIR/s1_check.json (S1 agreement counts, our null against S1's empirical means, ion transport).
"""
import csv
import json
import math
import os
import sys

import numpy as np
from scipy.stats import hypergeom, pearsonr

N, n = 15733, 10057


def hp(K, mean, rule=math.floor):
    return float(hypergeom.sf(rule(mean) - 1, N, K, n))


def sig3(x):
    return float(f"{x:.2e}")


def main(published, s1_path, null_path, out):
    os.makedirs(out, exist_ok=True)
    s1 = {r["go_id"]: r for r in csv.DictReader(open(s1_path), delimiter="\t")}
    ours = {r["go_id"]: r for r in csv.DictReader(open(null_path), delimiter="\t")}
    rules = {"floor": math.floor, "round": round, "ceil": math.ceil}
    agree = {}
    for name, rule in rules.items():
        agree[name] = sum(
            1 for r in s1.values()
            if math.isclose(hp(int(r["term_size"]), float(r["empirical_mean"]), rule),
                            float(r["hyper_p"]), rel_tol=1e-9, abs_tol=0))
    ours_p = {g: hp(int(r["term_size"]), float(r["mean_k"])) for g, r in ours.items()}
    s1_rank = sorted(s1, key=lambda g: float(s1[g]["hyper_p"]))
    our_rank = sorted(ours_p, key=lambda g: ours_p[g])
    pub = list(csv.DictReader(open(published)))
    with open(os.path.join(out, "table1.csv"), "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["rank", "go_id", "go_name", "term_size", "paper_p", "s1_mean", "s1_p_floor",
                    "s1_match", "our_mean", "our_p", "our_rank"])
        for r in pub:
            g = r["go_id"]
            K = int(s1[g]["term_size"])
            p_s1 = hp(K, float(s1[g]["empirical_mean"]))
            om = float(ours[g]["mean_k"]) if g in ours else float("nan")
            w.writerow([r["rank"], g, r["go_name"], K, r["p_value"], s1[g]["empirical_mean"],
                        f"{p_s1:.6e}", int(sig3(p_s1) == float(r["p_value"])), f"{om:.4f}",
                        f"{ours_p.get(g, float('nan')):.6e}", our_rank.index(g) + 1 if g in ours else ""])
    common = sorted(set(s1) & set(ours))
    a = np.array([float(s1[g]["empirical_mean"]) for g in common])
    b = np.array([float(ours[g]["mean_k"]) for g in common])
    big = a >= 10
    lp_s1 = np.array([math.log10(max(float(s1[g]["hyper_p"]), 1e-300)) for g in common])
    lp_ours = np.array([math.log10(max(ours_p[g], 1e-300)) for g in common])
    ion = "GO:0006811"
    rep = {
        "s1_terms": len(s1),
        "s1_p_agree_rel_1e-9": agree,
        "table1_rows_equal_at_3_digits_from_s1": sum(
            1 for r in pub if sig3(hp(int(s1[r["go_id"]]["term_size"]), float(s1[r["go_id"]]["empirical_mean"]))) == float(r["p_value"])),
        "table1_terms_in_our_top10": len({r["go_id"] for r in pub} & set(our_rank[:10])),
        "table1_terms_in_our_top20": len({r["go_id"] for r in pub} & set(our_rank[:20])),
        "terms_compared": len(common),
        "mean_targets_pearson_r": round(float(pearsonr(a, b)[0]), 5),
        "mean_targets_median_rel_diff_terms_ge10": round(float(np.median((b[big] - a[big]) / a[big])), 5),
        "log10p_pearson_r": round(float(pearsonr(lp_s1, lp_ours)[0]), 5),
        "ion_transport": {"paper_mean": float(s1[ion]["empirical_mean"]), "our_mean": float(ours[ion]["mean_k"]),
                          "paper_p": float(s1[ion]["hyper_p"]), "our_p": ours_p[ion],
                          "paper_text_p": 5.97e-7},
        "our_mean_targets_39": float(next(iter(ours.values()))["mean_n"]),
    }
    json.dump(rep, open(os.path.join(out, "s1_check.json"), "w"), indent=1)
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:5])
