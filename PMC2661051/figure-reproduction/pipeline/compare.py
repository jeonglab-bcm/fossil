#!/usr/bin/env python3
"""Compare our run with the paper: Tables 2-7, the bars of Figs 2 and 4, the histograms of Fig. 3,
the data counts of the text and the text's claims. Writes comparison.json (items with values for
results.json) and tables.json (our detection rates and counts, for the page).

Detection rates (Tables 2-6) are shares of 100 simulated data sets; each field's tolerance is the
Monte Carlo band of gseamod::rate_tolerance (99% two-proportion band plus half a printed unit),
fixed before the comparison. Table 7 p-values come from 1000 permutations and get the same band for
shares of 1000. Bar heights and histogram counts read off the published figures are integers;
they match when our count equals the value read.

Usage: compare.py SIMDIR REALDIR PUBLISHED_VALUES PAPER_VALUES OUTDIR
  SIMDIR: rep_*.csv from simulate_tables.R; REALDIR: p53.csv, hedenfalk.csv, datasets.json,
  figures.json, fig3_variants.json, variants.json
"""
import csv
import json
import math
import sys
from pathlib import Path

SETS = [f"set{i}" for i in range(1, 10)]
NONNULL = [s for s in SETS if s != "set3"]
CORRELATED = ["set1", "set4", "set6", "set8"]
UNCORRELATED = ["set2", "set5", "set7", "set9"]
STATS8 = ["mean", "median", "maxmean", "es", "wilcoxon", "condfdr", "globaltest", "hotelling"]


def qnorm995():
    return 2.5758293035489004


def rate_tol(p1, p2, n=100):
    """gseamod::rate_tolerance: 99% two-proportion band plus half a printed unit."""
    p1, p2 = float(p1), float(p2)
    pbar = (n * p1 + n * p2 + 1) / (2 * n + 2)
    return qnorm995() * math.sqrt(2 * pbar * (1 - pbar) / n) + 0.005


def fmt2(x):
    return f"{x:.2f}"


def load_sim(simdir):
    rows = []
    for f in sorted(Path(simdir).glob("rep_*.csv")):
        rows += list(csv.DictReader(open(f)))
    reps = sorted({r["replicate"] for r in rows}, key=int)
    cols = [c for c in rows[0] if c not in ("replicate", "set")]
    rates = {c: {s: sum(float(r[c]) <= 0.05 for r in rows if r["set"] == s) / len(reps) for s in SETS} for c in cols}
    return rates, len(reps)


def our_tables(rates):
    t = {"table2": {}, "table3": {}, "table4": {}, "table5": {}, "table6": {}, "variants": {}}
    for g in ("t", "modt", "corr"):
        for tr in ("none", "square", "ranksq", "binary", "lfdr"):
            t["table2"][f"{g}.{tr}"] = rates[f"T2.{g}.{tr}"]
    t["table3"]["mean"] = rates["T2.modt.square"]
    for st in ("maxmean", "median", "es", "condfdr", "wilcoxon"):
        t["table3"][st] = rates[f"T3.{st}"]
    t["table4"]["resampling"] = rates["T2.modt.square"]
    for me in ("parametric", "permutation", "restandardization"):
        t["table4"][me] = rates[f"T4.{me}"]
    for me in ("parametric", "resampling", "permutation", "restandardization"):
        t["table5"][me] = rates[f"T5.{me}"]
    for me in ("resampling", "permutation", "restandardization"):
        t["table6"][me] = rates[f"T6.{me}"]
    for c, v in rates.items():
        if c.startswith("V."):
            t["variants"][c[2:]] = v
    return t


def paper_tables(pv):
    return {k: {c: {s: float(x) for s, x in col.items()} for c, col in pv[k].items()}
            for k in ("table2", "table3", "table4", "table5", "table6")}


def table_item(name, ours, paper, n):
    fields = []
    for col, byset in paper.items():
        for s in SETS:
            exp = byset[s]
            obs = ours[col][s]
            fields.append({"name": f"{s}, {col}", "expected": exp, "observed": fmt2(obs),
                           "tolerance": {"abs": round(rate_tol(exp, obs, n) - 0.005, 4), "printed": True}})
    return {"method": "values", "values": {"fields": fields}}


def mean_over(col, sets):
    return sum(col[s] for s in sets) / len(sets)


# Claims of the text, as functions of the tables (ours or the paper's). Each returns "yes" or "no".
def claims_sim(T):
    t2, t3, t4, t5, t6 = (T[k] for k in ("table2", "table3", "table4", "table5", "table6"))
    g3 = ("t", "modt", "corr")
    c = {}
    c["untransformed_miss_6_9"] = all(t2[f"{g}.none"][s] <= 0.05 for g in g3 for s in ("set6", "set7", "set8", "set9"))
    c["squared_finds_6_9"] = all(t2[f"{g}.square"][s] >= 0.5 for g in g3 for s in ("set6", "set7", "set8", "set9"))
    c["squared_lower_1_2_4_5"] = all(t2[f"{g}.square"][s] <= t2[f"{g}.none"][s] for g in g3 for s in ("set1", "set2", "set4", "set5"))
    avg = {tr: sum(mean_over(t2[f"{g}.{tr}"], NONNULL) for g in g3) / 3 for tr in ("none", "square", "ranksq", "binary", "lfdr")}
    c["rank_squared_best"] = max(avg, key=avg.get) == "ranksq"
    c["quadratic_beat_binary_lfdr"] = min(avg["square"], avg["ranksq"]) > max(avg["binary"], avg["lfdr"])
    c["median_wilcoxon_beat_mean_on_correlated"] = all(t3[st][s] > t3["mean"][s] for st in ("median", "wilcoxon") for s in CORRELATED)
    c["es_weaker_than_mean"] = mean_over(t3["es"], NONNULL) < mean_over(t3["mean"], NONNULL)
    c["parametric_highest"] = mean_over(t4["parametric"], NONNULL) > max(mean_over(t4[m], NONNULL) for m in ("resampling", "permutation", "restandardization"))
    c["restandardization_like_resampling"] = round(max(abs(t4["restandardization"][s] - t4["resampling"][s]) for s in SETS), 9) <= 0.05
    c["permutation_easier_uncorrelated"] = all(t4["permutation"][s] >= t4["resampling"][s] for s in UNCORRELATED)
    c["globaltest_close_to_mean"] = round(max(abs(t5[m][s] - t4[m][s]) for m in ("resampling", "permutation", "restandardization") for s in SETS), 9) <= 0.05
    c["hotelling_misses_correlated"] = max(t6["resampling"][s] for s in CORRELATED) < min(t6["resampling"][s] for s in UNCORRELATED)
    c["hotelling_better_with_permutation"] = all(t6["permutation"][s] >= t6["resampling"][s] for s in SETS)
    c["main_mean_beats_es"] = mean_over(t3["mean"], NONNULL) > mean_over(t3["es"], NONNULL)
    c["main_mean_beats_hotelling"] = mean_over(t4["permutation"], NONNULL) > mean_over(t6["permutation"], NONNULL)
    return {k: "yes" if v else "no" for k, v in c.items()}


def claims_real(fig2, fig4):
    """fig2/fig4: {method: {stat: count at 0.01}}."""
    c = {}
    for me in ("resampling", "permutation"):
        top2 = sorted(STATS8, key=lambda s: -fig2[me][s])[:2]
        c[f"p53_hotelling_condfdr_top_{me}"] = set(top2) == {"hotelling", "condfdr"}
        low3 = sorted(STATS8, key=lambda s: fig2[me][s])[:3]
        c[f"p53_es_median_wilcoxon_lowest_{me}"] = set(low3) == {"es", "median", "wilcoxon"}
    c["hedenfalk_resampling_few"] = max(fig4["resampling"].values()) <= 2
    top4 = sorted(STATS8, key=lambda s: -fig4["permutation"][s])[:4]
    c["hedenfalk_top4_permutation"] = set(top4) == {"hotelling", "mean", "maxmean", "globaltest"}
    c["hedenfalk_condfdr_conservative"] = fig4["permutation"]["condfdr"] <= sorted(fig4["permutation"].values())[3]
    return {k: "yes" if v else "no" for k, v in c.items()}


CLAIM_TEXT = {
    "untransformed_miss_6_9": "Untransformed statistics miss sets 6 to 9 (every rate <= 0.05)",
    "squared_finds_6_9": "Squared statistics find sets 6 to 9 (every rate >= 0.5)",
    "squared_lower_1_2_4_5": "Squaring lowers the rates of sets 1, 2, 4 and 5 (or keeps them)",
    "rank_squared_best": "Rank squared has the highest mean rate over the eight non-null sets",
    "quadratic_beat_binary_lfdr": "Squared and rank squared beat binary and local fdr (mean rate)",
    "median_wilcoxon_beat_mean_on_correlated": "Median and Wilcoxon beat the mean on every correlated set (1, 4, 6, 8)",
    "es_weaker_than_mean": "ES has a lower mean rate than the mean statistic",
    "parametric_highest": "The parametric null gives the highest mean rate over the non-null sets",
    "restandardization_like_resampling": "Restandardization is within 0.05 of resampling on every set",
    "permutation_easier_uncorrelated": "Permutation detects the uncorrelated sets at least as often as resampling",
    "globaltest_close_to_mean": "globaltest is within 0.05 of the mean of squared moderated t (resampling, permutation, restandardization)",
    "hotelling_misses_correlated": "Hotelling (resampling) detects every correlated set less often than every uncorrelated set",
    "hotelling_better_with_permutation": "Hotelling detects every set at least as often with permutation as with resampling",
    "main_mean_beats_es": "Main claim: the mean of squared moderated t beats the ES score",
    "main_mean_beats_hotelling": "Main claim: the mean of squared moderated t (permutation) beats Hotelling (permutation)",
    "p53_hotelling_condfdr_top_resampling": "p53, resampling: Hotelling and cond. FDR find the most sets",
    "p53_hotelling_condfdr_top_permutation": "p53, permutation: Hotelling and cond. FDR find the most sets",
    "p53_es_median_wilcoxon_lowest_resampling": "p53, resampling: ES, median and Wilcoxon find the fewest sets",
    "p53_es_median_wilcoxon_lowest_permutation": "p53, permutation: ES, median and Wilcoxon find the fewest sets",
    "hedenfalk_resampling_few": "Hedenfalk: resampling finds very few sets (at most 2) with every statistic",
    "hedenfalk_top4_permutation": "Hedenfalk, permutation: Hotelling, mean, maxmean and globaltest find the most sets",
    "hedenfalk_condfdr_conservative": "Hedenfalk, permutation: cond. FDR is among the four statistics that find the fewest sets",
}
CLAIM_PERM_ONLY = {"perm_median_wilcoxon_lose": "With permutation, median and Wilcoxon lose their edge over the mean on the correlated sets (data not shown in the paper)"}


def main():
    simdir, realdir, pubf, paperf, outdir = sys.argv[1:6]
    realdir, outdir = Path(realdir), Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    pv = json.load(open(paperf))
    pub = json.load(open(pubf))
    rates, nrep = load_sim(simdir)
    T = our_tables(rates)
    P = paper_tables(pv)
    items = {}
    for k in ("table2", "table3", "table4", "table5", "table6"):
        items[k] = table_item(k, T[k], pv[k], nrep)

    # the paper's own consistency check: the shared cell of Tables 2, 3 and 4
    items["text.shared_cell"] = {"method": "values", "values": {"fields": [
        {"name": f"{s}: Table 2 squared mod.t = Table 3 mean = Table 4 resampling",
         "expected": "yes",
         "observed": "yes" if pv["table2"]["modt.square"][s] == pv["table3"]["mean"][s] == pv["table4"]["resampling"][s] else "no"}
        for s in SETS]}}
    items["text.variants"] = {"method": "values", "values": {"fields": [
        {"name": "3 gene-level statistics x 5 transformations x 6 gene set statistics x 3 significance assessments - 9 (ES with binary)",
         "expected": pv["text"]["variants"], "observed": str(3 * 5 * 6 * 3 - 9)}]}}

    # data counts
    ds = json.load(open(realdir / "datasets.json"))
    p, h = ds["p53"], ds["hedenfalk"]
    items["text.p53_data"] = {"method": "values", "values": {"fields": [
        {"name": "cell lines", "expected": "50", "observed": str(p["samples"])},
        {"name": "wild type", "expected": "17", "observed": str(p["wild_type"])},
        {"name": "mutant", "expected": "33", "observed": str(p["mutant"])},
        {"name": "probe sets on the HG-U95Av2 file", "expected": "12625", "observed": str(p["probe_sets"])},
        {"name": "genes after filtering", "expected": "8768", "observed": str(p["genes_after_filter"])},
        {"name": "gene sets of 15 to 500 genes", "expected": "290", "observed": str(p["gene_sets"])},
        {"name": "smallest set", "expected": "15", "observed": str(p["min_set_size"])},
        {"name": "largest set", "expected": "321", "observed": str(p["max_set_size"])}]}}
    items["text.hedenfalk_data"] = {"method": "values", "values": {"fields": [
        {"name": "BRCA1 patients", "expected": "7", "observed": str(h["brca1"])},
        {"name": "BRCA2 patients", "expected": "8", "observed": str(h["brca2"])},
        {"name": "genes on the array", "expected": "3226", "observed": str(h["clones"])},
        {"name": "genes mapped uniquely to a UniGene symbol", "expected": "2200", "observed": str(h["genes_mapped"])},
        {"name": "gene sets", "expected": "89", "observed": str(h["gene_sets"])}]}}

    # Figs 2 and 4: bars at cutoff 0.01
    fj = json.load(open(realdir / "figures.json"))
    bars = {}
    for fig in ("fig2", "fig4"):
        ours = {me: {st: int(fj[fig][me][st]["0.01"]) for st in STATS8} for me in ("resampling", "permutation")}
        bars[fig] = ours
        fields = []
        for st in STATS8:
            for me in ("resampling", "permutation"):
                rd = pub[fig]["bars"][f"{st}.{me}"]
                f = {"name": f"{st}, {me}", "expected": str(rd["read"]), "observed": str(ours[me][st])}
                if fig == "fig2":  # one pixel is 0.62 sets: a bar read off Fig. 2 can be one set off
                    f["tolerance"] = {"abs": 1}
                fields.append(f)
        items[f"{fig}.b"] = {"method": "values", "values": {"fields": fields},
                      "outputs": [f"figure-reproduction/output/{fig}_ours.png", f"figure-reproduction/output/{fig}_overlay.png"]}

    # Fig. 3 histograms
    for key, sub, label in (("mean_correlation", "fig3.a", "mean pairwise correlation"),
                            ("mean_abs_correlation", "fig3.b", "mean pairwise absolute correlation")):
        ours = fj["fig3"][key]["counts"]
        fields = [{"name": f"{label} in [{b['bin'][0]:.3f}, {b['bin'][1]:.3f})", "expected": str(b["read"]), "observed": str(o)}
                  for b, o in zip(pub["fig3"][key], ours)]
        items[sub] = {"method": "values", "values": {"fields": fields},
                      "outputs": ["figure-reproduction/output/fig3_ours.png", "figure-reproduction/output/fig3_overlay.png"]}
    items["text.fig3_weak"] = {"method": "values", "values": {"fields": [
        {"name": "median over the 290 sets of the mean pairwise correlation below 0.1 (\"comparatively weak\")",
         "expected": "yes", "observed": "yes" if fj["fig3"]["median_mean"] < 0.1 else "no"}]}}

    # Table 7 and the ES claim
    hp = list(csv.DictReader(open(realdir / "hedenfalk.csv")))
    pm = {r["set"]: float(r["mean.permutation"]) for r in hp}
    pes = {r["set"]: float(r["es.permutation"]) for r in hp}
    sig = sorted([s for s in pm if pm[s] <= 0.01], key=lambda s: pm[s])
    fields = [{"name": "sets with p <= 0.01", "expected": pv["text"]["table7_count"], "observed": str(len(sig))}]
    for row in pv["table7"]:
        s = row["set"]
        if s in pm:
            fields.append({"name": f"{row['rank']}. {s}", "expected": row["p"], "observed": f"{pm[s]:.3f}",
                           "tolerance": {"abs": round(rate_tol(row["p"], pm[s], 1000) - 0.005, 4), "printed": True}})
        else:
            fields.append({"name": f"{row['rank']}. {s} (not among our {len(pm)} sets)", "expected": row["p"], "observed": None})
    items["table7"] = {"method": "values", "values": {"fields": fields}}
    rank_mean = 1 + sum(1 for s in pm if pm[s] < pm.get("breast_cancer_estrogen_signalling", 1))
    rank_es = 1 + sum(1 for s in pes if pes[s] < pes.get("breast_cancer_estrogen_signalling", 1))
    items["text.es_estrogen"] = {"method": "values", "values": {"fields": [
        {"name": "breast_cancer_estrogen_signalling: rank by the mean (1 + sets with a smaller p)", "expected": "1", "observed": str(rank_mean)},
        {"name": "breast_cancer_estrogen_signalling: outside the top 20 by ES", "expected": "yes", "observed": "yes" if rank_es > 20 else "no"}]}}

    # claims
    cs_ours, cs_paper = claims_sim(T), claims_sim(P)
    pubbars = {fig: {me: {st: pub[fig]["bars"][f"{st}.{me}"]["read"] for st in STATS8} for me in ("resampling", "permutation")}
               for fig in ("fig2", "fig4")}
    cr_ours, cr_paper = claims_real(bars["fig2"], bars["fig4"]), claims_real(pubbars["fig2"], pubbars["fig4"])
    perm = T["variants"]
    perm_lose = sum(perm[f"perm.{st}"][s] for st in ("median", "wilcoxon") for s in CORRELATED) / 8 <= \
        sum(T["table4"]["permutation"][s] for s in CORRELATED) / 4
    claims = {**cs_ours, **cr_ours, "perm_median_wilcoxon_lose": "yes" if perm_lose else "no"}
    paper_claims = {**cs_paper, **cr_paper}
    for k, v in claims.items():
        text = CLAIM_TEXT.get(k) or CLAIM_PERM_ONLY[k]
        items[f"text.{k}"] = {"method": "values", "values": {"fields": [{"name": text, "expected": "yes", "observed": v}]}}
    ar = [{"claim": k, "paper_tables": v} for k, v in paper_claims.items()]
    failed = [a["claim"] for a in ar if a["paper_tables"] != "yes"]
    items["text.arithmetic"] = {"method": "check", "check": {
        "passed": not failed,
        "detail": f"{len(ar) - len(failed)} of {len(ar)} claims come back from the paper's own tables and figure bars"
                  + (f"; not: {', '.join(failed)}" if failed else ""),
        "claims": ar}}

    tables = {"replicates": nrep, "ours": T, "paper": pv, "bars": bars, "published_bars": pubbars,
              "fig3": fj["fig3"], "fig3_variants": json.load(open(realdir / "fig3_variants.json")),
              "fig3_published": {k: [b["read"] for b in pub["fig3"][k]] for k in ("mean_correlation", "mean_abs_correlation")},
              "table7_ours": [{"set": s, "p": pm[s]} for s in sig], "hedenfalk_sets": len(pm),
              "datasets": ds, "claims_ours": claims, "claims_paper": paper_claims,
              "variants": json.load(open(realdir / "variants.json"))}
    # item_list: the same items as a list keyed by id (dots as underscores), for tools/check_results.py paths
    item_list = [{"key": k.replace(".", "_"), **v} for k, v in items.items()]
    Path(outdir / "comparison.json").write_text(json.dumps({"items": items, "item_list": item_list}, indent=1) + "\n")
    Path(outdir / "tables.json").write_text(json.dumps(tables, indent=1) + "\n")
    print(f"{len(items)} items; {nrep} replicates")


if __name__ == "__main__":
    main()
