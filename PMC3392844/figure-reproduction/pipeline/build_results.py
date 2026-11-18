"""Merge results_notes.json (written by hand: labels, sources, assumptions, causes) with the numbers of a
run into results.json, then let check_results.py compute every verdict and the summary.

Usage: build_results.py RUN_DIR OUT.json [--environment ENV.json]

Notes items take their numbers from the run folder:
  "fields_from": "comparison.json:tables/table2_all"   values.fields from that file and key path
  "pixels_from": "figures.json:figures/fig2"            pixels block (scores and controls), with "threshold"
  "check_from":  "package.json"                         check.passed and detail from check_package.py's report
                 "claims.json"                          text.arithmetic: the claims recomputed from the paper's tables
                 "identity"                             the recovered data against the paper's own counts
  "cause_from":  "<key>"                                a shared cause of the notes
A cause is attached only when the item falls short (a field missed, a score under its pass mark, or not
attempted); a cause on an item that comes back in full fails the build, so a stale cause cannot reach a page.
Every "{fact}" in the notes' text is filled from the run (facts_of), so the prose cannot drift from it.
The skill block and the session pointer travel with the notes, unchanged.
"""
import copy
import json
import math
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NOTES = HERE.parent / "results_notes.json"
sys.path.insert(0, str(HERE))
from check_results import field_matches  # noqa: E402

FIELD_KEYS = ("name", "expected", "observed", "tolerance", "arithmetic")


def get(run, ref):
    f, _, key = ref.partition(":")
    d = json.load(open(Path(run) / f))
    for k in key.split("/") if key else []:
        d = d[k]
    return d


def hits(fields):
    return sum(field_matches(f, {"printed": True}) for f in fields)


def f4(x):
    return f"{x:.4f}"


def facts_of(run):
    run = Path(run)
    M = json.load(open(run / "metrics.json"))
    C = json.load(open(run / "comparison.json"))
    F = json.load(open(run / "figures.json"))["figures"]
    S = json.load(open(run / "seed_spread.json"))
    H = json.load(open(run / "hypotheses.json"))
    T4 = json.load(open(run / "table4.json"))
    t2 = C["tables"]["table2"]["fields"]
    t2a = [f for f in t2 if "|all|" in f["name"]]
    t25 = [f for f in t2 if "|50+|" in f["name"]]
    auc_diff = max(abs(float(f["expected"]) - f["observed"]) for f in t2 if f["name"].endswith("auc"))
    pr_diff = max(abs(float(f["expected"]) - f["observed"]) for f in t2 if f["name"].endswith(("precision", "recall")))
    sc = {c["name"]: c for c in S["cells"]}
    auc_cells = [c for c in S["cells"] if c["name"].endswith("auc")]
    t3 = {f["name"]: f for f in C["tables"]["table3"]["fields"]}
    fx = {}
    for alg in ("lr", "nb", "knn", "rf", "svm"):
        rows = [f for n, f in t3.items() if n.startswith(alg + "|")]
        fx[f"t3_{alg}_hits"] = hits(rows)
        fx[f"t3_{alg}_all_auc"] = f4(t3[f"{alg}|all|auc"]["observed"])
        fx[f"t3_{alg}_50_auc"] = f4(t3[f"{alg}|50+|auc"]["observed"])
    for name, v in H.items():
        if name.startswith("_"):
            continue
        key = name.replace(".", "")
        fx[f"h_{key}_all"] = f4(v["all"]["auc"])
        fx[f"h_{key}_50"] = f4(v["50+"]["auc"])
        fx[f"h_{key}_acc"] = f4(v["all"]["acc"])
        fx[f"h_{key}_50acc"] = f4(v["50+"]["acc"])
    s1 = {f["name"]: f["observed"] for f in C["tables"]["tableS1"]["fields"]}
    rf_w = M["rf:chem+bio+pheno:paper"]["all"]["auc"]
    t4 = T4["fields"]
    miss4 = [f["name"].replace("|", ", ") for f in t4 if f["expected"] != f["observed"]]
    fig5 = {f["name"]: f for f in C["tables"]["fig5"]["fields"]}
    fx.update({
        "t2_all_hits": hits(t2a), "t2_50_hits": hits(t25), "t2_auc_maxdiff": f4(auc_diff), "t2_pr_maxdiff": f"{pr_diff:.3f}",
        "seed_n": S["summary"]["seeds"], "seed_inside": S["summary"]["paper_inside"], "seed_cells": S["summary"]["cells"],
        "seed_auc_range": f4(S["summary"]["max_range"]["auc"]), "seed_pr_range": f"{max(S['summary']['max_range']['precision'], S['summary']['max_range']['recall']):.3f}",
        "seed_auc_inside": sum(c["paper_inside"] for c in auc_cells), "seed_auc_cells": len(auc_cells),
        "seed_chem_all_auc_min": f4(sc["chem|all|auc"]["min"]), "seed_chem_all_auc_max": f4(sc["chem|all|auc"]["max"]),
        "svm_decision_auc": f4(H["svm_decision"]["all"]["auc"]),
        "fig3_chem_pub_auc": f4(F["fig3"]["curve_auc_published"]["chem"]), "fig3_chem_ours_auc": f4(M["svm:chem"]["50+"]["auc"]),
        "fig3_chem_score": f"{100 * min(F['fig3']['per_curve']['chem'].values()):.1f}",
        "fig3_other_min": f"{100 * min(min(v.values()) for k, v in F['fig3']['per_curve'].items() if k != 'chem'):.1f}",
        "fig4_nb_score": f"{100 * min(F['fig4']['per_curve']['nb'].values()):.1f}", "fig4_lr_score": f"{100 * min(F['fig4']['per_curve']['lr'].values()):.1f}",
        "fig4_other_min": f"{100 * min(min(F['fig4']['per_curve'][k].values()) for k in ('svm', 'rf', 'knn')):.1f}",
        "fig4_nb_pub_auc": f4(F["fig4"]["curve_auc_published"]["nb"]), "fig4_lr_pub_auc": f4(F["fig4"]["curve_auc_published"]["lr"]),
        "s1_chem": f"{s1['chem']:.1f}", "s1_ade": f"{s1['ade']:.1f}", "s1_target": f"{s1['target']:.1f}", "s1_indication": f"{s1['indication']:.1f}",
        "rf_weighted_auc": f4(rf_w), "rf_auc": f4(M["rf:chem+bio+pheno"]["all"]["auc"]),
        "svm_weighted_auc": f4(M["svm:chem+bio+pheno:paper"]["all"]["auc"]),
        "t4_hits": sum(f["expected"] == f["observed"] for f in t4), "t4_fields": len(t4), "t4_misses": "; ".join(miss4),
        "t4_decision_hits": T4["hypotheses"]["decision_rule_matches"],
        "fig5_hits": hits(list(fig5.values())), "fig5_maxrel": f"{100 * max(abs(f['observed'] - int(f['expected'])) / int(f['expected']) for f in fig5.values()):.0f}",
        "chem_ind_auc": f4(M["svm:chem+indication"]["all"]["auc"]),
        "positives": C["counts"]["positives"], "adrs_lt5": C["counts"]["adrs_fewer_than_5"], "adrs_1to4": C["counts"]["adrs_1_to_4"],
        "nausea_headache": C["counts"]["nausea_headache_drugs"], "pairs400": C["counts"]["pairs_over_400"], "pairs400ge": C["counts"]["pairs_at_least_400"],
        "ks1": f"{C['ks']['ks_chem_vs_chembio']['bonferroni3']:.2e}", "ks2": f"{C['ks']['ks_chem_vs_chembiopheno']['bonferroni3']:.1e}",
        "ks3": f"{C['ks']['ks_pheno_vs_chembiopheno']['bonferroni3']:.3f}", "ks1raw": f"{C['ks']['ks_chem_vs_chembio']['raw']:.2e}",
        "ks3raw": f"{C['ks']['ks_pheno_vs_chembiopheno']['raw']:.3f}",
        "adr50_ge_chem": f4(C["hypotheses"]["adr50_at_least"]["chem"]),
        "s1_yates_chem": f"{C['hypotheses']['tableS1_yates']['chem']:.1f}", "s1_yates_ade": f"{C['hypotheses']['tableS1_yates']['ade']:.1f}",
        "op_youden_prec": f4(C["hypotheses"]["operating_points_chem"]["youden"]["precision"]),
        "op_youden_rec": f4(C["hypotheses"]["operating_points_chem"]["youden"]["recall"]),
        "op_half_prec": f4(C["hypotheses"]["operating_points_chem"]["threshold_0.5"]["precision"]),
        "op_half_rec": f4(C["hypotheses"]["operating_points_chem"]["threshold_0.5"]["recall"]),
        "chem_prec": f4(M["svm:chem"]["all"]["precision"]), "chem_rec": f4(M["svm:chem"]["all"]["recall"]),
        "ks2_1": f"{C['hypotheses']['ks_two_sided_bonferroni3']['ks_chem_vs_chembio']:.2e}",
        "ks2_3": f"{C['hypotheses']['ks_two_sided_bonferroni3']['ks_pheno_vs_chembiopheno']:.3f}",
        "s1_feat_chem": f"{C['hypotheses']['tableS1_per_feature']['chem']:.1f}", "s1_feat_ade": f"{C['hypotheses']['tableS1_per_feature']['ade']:.1f}",
        "s1_feat_target": f"{C['hypotheses']['tableS1_per_feature']['target']:.1f}",
        "t4_cer_chem": sum(1 for f in t4 if f["name"].startswith("Cerivastatin") and f["name"].endswith("|chem") and f["observed"] == "Yes" and "Group" not in f["name"]),
        "single_pairs": H["_counts"]["pairs_in_single_class_folds"], "first_pairs": H["_counts"]["pairs_in_first_label_positive_folds"],
    })
    return fx


def fill(obj, facts):
    if isinstance(obj, str):
        def rep(m):
            if m.group(1) not in facts:
                raise KeyError(f"results_notes.json cites an unknown fact {{{m.group(1)}}}")
            return str(facts[m.group(1)])
        return re.sub(r"\{([a-z0-9_]+)\}", rep, obj)
    if isinstance(obj, list):
        return [fill(x, facts) for x in obj]
    if isinstance(obj, dict):
        return {k: fill(v, facts) for k, v in obj.items()}
    return obj


def arithmetic(claims):
    """text.arithmetic: each claim's statement recomputed from the paper's own tables (our formula, the
    paper's numbers). A statement that does not come back would mean our formula is not the paper's."""
    back, missed = [], []
    for cid, c in claims.items():
        if cid.startswith("_"):
            continue
        for f in c["fields"]:
            if "arithmetic" not in f:
                continue
            g = {"expected": f["expected"], "observed": f["arithmetic"], "tolerance": f.get("tolerance", {"printed": True})}
            (back if field_matches(g, None) else missed).append(f"{c['label'][:40]}...: {f['name']} ({f['expected']} against {f['arithmetic']})")
    detail = f"{len(back)} of {len(back) + len(missed)} statements follow from the paper's own tables and figures"
    detail += ("; not: " + "; ".join(missed)) if missed else "."
    return not missed, detail


def identity(claims):
    """The recovered training file against the paper: Fig. 5's true-positive totals divided by Table 2's
    recalls give the number of positive (drug, ADR) pairs the paper had; the file has its own count."""
    d = claims["_data_identity"]
    ok = all(abs(v - d["positives"]) / d["positives"] < 0.001 for v in d["implied_by_fig5_and_table2"].values())
    imp = ", ".join(f"{k} {v:,.0f}" for k, v in d["implied_by_fig5_and_table2"].items())
    return ok, (f"The recovered file has {d['positives']:,} positive (drug, ADR) pairs; Fig. 5's true positives over "
                f"Table 2's recalls imply {imp}, all within 0.1%.")


def short(item, run):
    """True when the item falls short of a full match: a missed field, a score under its pass mark."""
    if item.get("method") == "none":
        return True
    if "values" in item:
        v = item["values"]
        return not all(field_matches(f, v.get("tolerance")) for f in v["fields"])
    if "pixels" in item:
        p = item["pixels"]
        return min(p["published_near_ours"], p["ours_near_published"]) < p["threshold"]
    if "check" in item:
        return not item["check"]["passed"]
    return False


def main():
    args = sys.argv[1:]
    env = None
    if "--environment" in args:
        i = args.index("--environment")
        env = json.load(open(args[i + 1]))
        del args[i:i + 2]
    run, out = args
    notes = json.load(open(NOTES))
    facts = facts_of(run)
    notes = {k: (fill(v, facts) if k in ("items", "causes", "assumption_sets") else v) for k, v in notes.items()}
    claims = json.load(open(Path(run) / "claims.json"))
    run_block = copy.deepcopy(notes["run"])
    if env:
        run_block["environment"] = env
    res = {"schema": "paper2repro/results/v1", "paper": notes["paper"], "run": run_block,
           "session": notes["session"], "skill": notes["skill"], "items": []}
    stale = []
    for it in notes["items"]:
        it = copy.deepcopy(it)
        sets = it.pop("assumptions_from", [])
        if sets:
            it["assumptions"] = [a for s_ in sets for a in notes["assumption_sets"][s_]] + it.get("assumptions", [])
        cause = it.pop("cause_from", None)
        src = it.pop("fields_from", None)
        if src:
            fields = [{k: f[k] for k in f if k in FIELD_KEYS} for f in get(run, src)]
            it["values"] = {"fields": fields, "tolerance": {"printed": True}}
        pix = it.pop("pixels_from", None)
        if pix:
            d = get(run, pix)
            tol = json.load(open(Path(run) / pix.split(":")[0]))["tolerance_px"]
            it["pixels"] = {"tolerance_px": tol, "dpi": 600, "published_near_ours": d["published_near_ours"],
                            "ours_near_published": d["ours_near_published"], "threshold": it.pop("threshold"),
                            "controls": d["controls"], "per_curve": d["per_curve"]}
        chk = it.pop("check_from", None)
        if chk == "package.json":
            p = Path(run) / chk
            d = json.load(open(p)) if p.exists() else {"passed": False, "detail": "package check not run"}
            it["check"] = {"passed": bool(d["passed"]), "detail": d.get("detail", "")}
        elif chk == "claims.json":
            ok, detail = arithmetic(claims)
            it["check"] = {"passed": ok, "detail": detail}
        elif chk == "identity":
            ok, detail = identity(claims)
            it["check"] = {"passed": ok, "detail": detail}
        if cause:
            if short(it, run):
                it["cause"] = copy.deepcopy(notes["causes"][cause])
            else:
                stale.append(f"{it['id']} comes back in full, but the notes give it cause {cause!r}")
        elif short(it, run) and "cause" not in it:
            stale.append(f"{it['id']} falls short and the notes give it no cause")
        res["items"].append(it)
    if stale:
        print("results_notes.json no longer matches the run:\n  " + "\n  ".join(stale), file=sys.stderr)
        sys.exit(1)
    with open(out, "w") as f:
        json.dump(res, f, indent=1)
        f.write("\n")
    r = subprocess.run([sys.executable, str(HERE / "check_results.py"), out, "--write", "--skip-files"])
    sys.exit(r.returncode)


if __name__ == "__main__":
    main()
