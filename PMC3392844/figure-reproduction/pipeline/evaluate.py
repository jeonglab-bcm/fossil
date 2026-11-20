"""Every number of the reproduction from the score matrices: Tables 1-3, Table S1, Fig. 5's counts, the
per-ADR AUCs and KS tests, the dataset counts of the text, and the ROC curves the figures draw.

Usage: evaluate.py DATA_DIR SCORES_DIR PUBLISHED_VALUES.json OUT_DIR

Writes OUT_DIR/metrics.json (micro-averaged AUC, ACC, precision and recall of every model, over all ADRs
and over ADR_50+), OUT_DIR/rocs.json (each model's global ROC on a grid of 2,001 FPR values) and
OUT_DIR/comparison.json (our value next to the paper's for every printed number, with the hypotheses that
bear on them).
"""
import json
import sys
from pathlib import Path

import numpy as np

import adrfusion as A

GRID = np.linspace(0.0, 1.0, 2001)
SETS = ["chem", "bio", "pheno", "chem+bio", "chem+pheno", "chem+bio+pheno"]
ALGS = ["lr", "nb", "knn", "rf", "svm"]
FULL = "chem+bio+pheno"
METRICS = ["auc", "acc", "precision", "recall"]


def r(x, n=10):
    return None if x is None else float(round(float(x), n))


def load(data_dir):
    d = Path(data_dir)
    cuis = [l.split("|")[0] for l in (d / "ade_feature_list").read_text().splitlines() if l]
    return A.read_dataset(d / "random_group_cv_data.indication", cuis)


def model_name(alg, fs, weighted=False):
    return f"{alg}:{fs}" + (":paper" if weighted else "")


def fields(expected: dict, observed: dict, prefix=""):
    return [{"name": f"{prefix}{k}", "expected": expected[k], "observed": r(observed[k])} for k in expected]


def roc_on_grid(y, s):
    fpr, tpr, _ = A.roc(y, s)
    # Highest TPR reached at each FPR (the curve's upper envelope at a vertical step), then on the grid.
    return np.interp(GRID, fpr, tpr)


def feature_level_shares(data, alpha=0.05):
    """Share of each block among the features informative (chi-square p < alpha) for at least one ADR."""
    from scipy.stats import chi2

    Y = data.Y.astype(np.float64)
    n, a1 = data.n_drugs, Y.sum(0)
    blocks = dict(data.blocks)
    blocks["ade"] = data.Y
    cnt = {}
    for k, X in blocks.items():
        X = X.astype(np.float64)
        f1 = X.sum(0)
        a = X.T @ Y
        b, c = f1[:, None] - a, a1[None, :] - a
        d = n - f1[:, None] - a1[None, :] + a
        den = (a + b) * (c + d) * (a + c) * (b + d)
        with np.errstate(divide="ignore", invalid="ignore"):
            st = np.where(den > 0, (a * d - b * c) ** 2 * n / den, np.nan)
        sig = np.nan_to_num(chi2.sf(st, 1), nan=1.0) < alpha
        if k == "ade":
            np.fill_diagonal(sig, False)
        cnt[k] = int(sig.any(1).sum())
    tot = sum(cnt.values())
    return {k: v / tot for k, v in cnt.items()}


def main():
    data_dir, scores_dir, pubf, out = sys.argv[1:5]
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    pub = json.load(open(pubf))
    data = load(data_dir)
    Y = data.Y
    npos = Y.sum(0)
    sub50 = npos > 50  # Methods: "more than 50 of the 832 drugs"
    sub50_ge = npos >= 50  # Table 2's footnote: "at least 50 drugs"

    S = {p.stem: np.load(p) for p in Path(scores_dir).glob("*.npy")}

    # ---- micro-averaged metrics and ROC curves
    metrics, rocs, per_adr = {}, {}, {}
    for name, M in sorted(S.items()):
        metrics[name] = {"all": {k: r(v) for k, v in A.micro_metrics(Y, M).as_dict().items()},
                         "50+": {k: r(v) for k, v in A.micro_metrics(Y[:, sub50], M[:, sub50]).as_dict().items()},
                         "50+_at_least": {k: r(v) for k, v in A.micro_metrics(Y[:, sub50_ge], M[:, sub50_ge]).as_dict().items()}}
        rocs[name] = {"all": [r(v, 6) for v in roc_on_grid(Y, M)], "50+": [r(v, 6) for v in roc_on_grid(Y[:, sub50], M[:, sub50])]}
        per_adr[name] = A.per_adr_auc(Y, M)

    comp = {"tables": {}, "text": {}, "hypotheses": {}}

    # ---- Table 1: feature dimensions
    dims = data.dimensions()
    t1map = {"Substructures": "chem", "Targets": "target", "Transporters": "transporter", "Enzymes": "enzyme",
             "Pathways": "pathway", "Treatment indications": "indication", "Other side effects": "ade"}
    comp["tables"]["table1"] = {"fields": [{"name": k, "expected": v, "observed": dims[t1map[k]]} for k, v in pub["table1"].items()]}

    # ---- Table 2 (SVM, six feature sets) and Table 3 (five algorithms, full feature set)
    for tab, rows in (("table2", {fs: model_name("svm", fs) for fs in SETS}),
                      ("table3", {a: model_name(a, FULL) for a in ALGS})):
        fl = []
        for row, mname in rows.items():
            if mname not in metrics:
                continue
            for part in ("all", "50+"):
                exp = pub[tab][row][part]
                fl += fields(exp, metrics[mname][part], prefix=f"{row}|{part}|")
        comp["tables"][tab] = {"fields": fl}
    # The items results.json reports: Table 2 by ADR set, Table 3 by algorithm.
    t2 = comp["tables"]["table2"]["fields"]
    comp["tables"]["table2_all"] = {"fields": [f for f in t2 if "|all|" in f["name"]]}
    comp["tables"]["table2_50"] = {"fields": [f for f in t2 if "|50+|" in f["name"]]}
    for a in ALGS:
        comp["tables"][f"table3_{a}"] = {"fields": [f for f in comp["tables"]["table3"]["fields"] if f["name"].startswith(a + "|")]}

    # ---- Table S1: informative features (chi-square p < 0.05), share of all informative (feature, ADR) pairs
    inf = A.informative_features(data)
    inf_y = A.informative_features(data, correction=True)
    comp["tables"]["tableS1"] = {"fields": [{"name": k, "expected": v, "observed": r(100 * inf[k]["share"])}
                                            for k, v in pub["tableS1"].items()],
                                 "counts": {k: v["informative"] for k, v in inf.items()}}
    comp["hypotheses"]["tableS1_yates"] = {k: r(100 * v["share"]) for k, v in inf_y.items()}

    # ---- Fig. 5: overlap of the true positives of chem, bio and pheno at their precision/recall points
    tp = {}
    for fs in ("chem", "bio", "pheno"):
        M = S[model_name("svm", fs)]
        tp[fs] = A.true_positives(Y, M, metrics[model_name("svm", fs)]["all"]["f1_threshold"])
    c, b, p = tp["chem"], tp["bio"], tp["pheno"]
    venn = {"chem": c & ~b & ~p, "chem&bio": c & b & ~p, "bio": b & ~c & ~p, "chem&bio&pheno": c & b & p,
            "chem&pheno": c & p & ~b, "bio&pheno": b & p & ~c, "pheno": p & ~c & ~b}
    vc = {k: int(v.sum()) for k, v in venn.items()}
    comp["tables"]["fig5"] = {"fields": [{"name": k, "expected": v, "observed": vc[k]} for k, v in pub["fig5"].items()]}

    # ---- KS tests over per-ADR AUCs (one-sided, Bonferroni over the paper's three reported comparisons)
    a = per_adr
    ks = {}
    for key, lo, hi in (("ks_chem_vs_chembio", "svm:chem", "svm:chem+bio"),
                        ("ks_chem_vs_chembiopheno", "svm:chem", "svm:chem+bio+pheno"),
                        ("ks_pheno_vs_chembiopheno", "svm:chem+bio+pheno", "svm:pheno")):
        ks[key] = {"raw": A.ks_larger(a[lo], a[hi]), "bonferroni3": A.ks_larger(a[lo], a[hi], 3),
                   "bonferroni15": A.ks_larger(a[lo], a[hi], 15)}
    comp["ks"] = ks

    # ---- dataset counts of the text
    sider = [l.split("\t") for l in (Path(data_dir) / "sider1_costart_adverse_effects.tsv").read_text().splitlines() if l]
    sdrugs = {x[0] for x in sider}
    sterms = {x[1] for x in sider}
    co = (Y.T.astype(np.int64) @ Y.astype(np.int64))
    iu = np.triu_indices(Y.shape[1], 1)
    cuis = data.adrs
    names = [l.split("|")[1] for l in (Path(data_dir) / "ade_feature_list").read_text().splitlines() if l]
    nausea, headache = names.index("nausea"), names.index("headache")
    comp["counts"] = {
        "sider_drugs": len(sdrugs), "sider_terms": len(sterms), "sider_associations": len(sider),
        "sider_mean_per_drug": len(sider) / len(sdrugs), "drugs": data.n_drugs, "adrs": data.n_adrs,
        "positives": int(Y.sum()), "adrs_more_than_50": int(sub50.sum()), "adrs_at_least_50": int(sub50_ge.sum()),
        "adrs_fewer_than_5": int((npos < 5).sum()), "adrs_1_to_4": int(((npos >= 1) & (npos < 5)).sum()),
        "adrs_no_drug": int((npos == 0).sum()),
        "nausea_headache_drugs": int(co[nausea, headache]),
        "pairs_over_400": int((co[iu] > 400).sum()), "pairs_at_least_400": int((co[iu] >= 400).sum()),
        "feature_dimension": sum(dims.values()), "bio_dimension": sum(dims[k] for k in ("target", "transporter", "enzyme", "pathway")),
        "pheno_dimension": dims["indication"] + dims["ade"], "nausea_cui": cuis[nausea], "headache_cui": cuis[headache],
    }

    # ---- hypotheses on the metrics
    # Other operating-point rules for chem (all ADRs): Youden's J and a probability threshold of 0.5.
    fpr, tpr, th = A.roc(Y, S["svm:chem"])
    P, N = int(Y.sum()), Y.size - int(Y.sum())
    tp, fp = tpr * P, fpr * N
    op = {}
    for nm, i in (("youden", int(np.argmax(tpr - fpr))), ("threshold_0.5", int(np.searchsorted(-th, -0.5, side="right") - 1))):
        op[nm] = {"acc": r((tp[i] + N - fp[i]) / Y.size), "precision": r(tp[i] / (tp[i] + fp[i])), "recall": r(tpr[i])}
    comp["hypotheses"]["operating_points_chem"] = op
    from scipy.stats import ks_2samp
    comp["hypotheses"]["ks_two_sided_bonferroni3"] = {
        k: r(min(1.0, 3 * ks_2samp(*[x[~np.isnan(x)] for x in (per_adr[lo], per_adr[hi])]).pvalue), 12)
        for k, lo, hi in (("ks_chem_vs_chembio", "svm:chem", "svm:chem+bio"), ("ks_pheno_vs_chembiopheno", "svm:chem+bio+pheno", "svm:pheno"))}
    # Table S1 counted per feature (informative for at least one ADR) instead of per (feature, ADR) pair.
    comp["hypotheses"]["tableS1_per_feature"] = {k: r(100 * v, 6) for k, v in feature_level_shares(data).items()}
    comp["hypotheses"]["adr50_at_least"] = {fs: metrics[model_name("svm", fs)]["50+_at_least"]["auc"] for fs in SETS}

    (out / "metrics.json").write_text(json.dumps(metrics, indent=1) + "\n")
    (out / "rocs.json").write_text(json.dumps({"grid": [r(v, 6) for v in GRID], "curves": rocs}) + "\n")
    (out / "per_adr_auc.json").write_text(json.dumps({k: [None if np.isnan(v) else r(v) for v in x] for k, x in per_adr.items()}) + "\n")
    (out / "comparison.json").write_text(json.dumps(comp, indent=1) + "\n")
    print(f"evaluated {len(S)} models", file=sys.stderr)


if __name__ == "__main__":
    main()
