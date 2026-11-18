"""Merge results_notes.json (written by hand: labels, sources, assumptions, causes) with the numbers
of a run into results.json, then let check_results.py compute every verdict and the summary.

Usage: build_results.py RUN_DIR OUT.json [--environment ENV.json]

Each notes item names where its numbers come from:
  "from": "comparison:<key>"   values.fields from output/comparison.json
  "from": "claims:<id>"        values.fields from output/claims.json (with the arithmetic check kept)
  "from": "arithmetic"         the text.arithmetic check: every claim recomputed from the paper's values
  "from": "port"               check from output/port_check.json
  "from": "package"            check from output/package.json
Rules the build applies, so a stale note cannot reach the page:
  - an item with misses and no cause fails the build; a cause given for an item without misses is dropped
    unless the note marks it "always";
  - "exceptions": "af1_plr_columns" lists as paper errors the missed Additional file 1 cells that
    the table prints identically for all nine classifiers (they are PLR's, see the cause);
  - "exceptions": "arithmetic" lists as paper errors the missed claim fields whose statement the
    paper's own figures and tables do not support either (the arithmetic value misses too).
The skill block and the session pointer travel with the notes, unchanged.
"""
import copy
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NOTES = HERE.parent / "results_notes.json"
sys.path.insert(0, str(HERE))
from check_results import field_matches  # noqa: E402

KEEP = ("name", "expected", "observed", "tolerance", "z", "arithmetic", "mean_available", "replicates_na")


def matches(f):
    return field_matches(f, {"printed": True} if "tolerance" not in f else None)


def facts_of(run):
    """Numbers the hand-written causes cite, taken from the run so the prose cannot drift from it."""
    run = Path(run)
    h = json.load(open(run / "hypotheses.json"))
    c = json.load(open(run / "comparison.json"))
    S = {}
    import csv
    with open(run / "summary.csv") as f:
        for r in csv.DictReader(f):
            S[(r["setting"], r["test"], r["method"], r["metric"])] = r
    def grid(case, cost, w, i):
        for k, v in h[case]["grid"].items():
            if abs(float(k) - cost) < 1e-12:
                return v[w][i]
        raise KeyError((case, cost))
    dq = h["dqda_auc"]
    return {
        "svm_af3_ours": f"{float(S[('alt20_p1000_k0.10', 'bal20', 'SVM', 'PA1')]['mean']):.2f}",
        "svm_c01_af3": f"{grid('af3_k0.1', 0.1, 'proportion', 0):.2f}",
        "svm_c003_af3": f"{grid('af3_k0.1', 0.03, 'proportion', 0):.2f}",
        "svm_c01_null": f"{grid('null_k0.2', 0.1, 'proportion', 0):.3f}",
        "svm_inv_er": f"{grid('er_20_5', 0.1, 'inverse', 1):.2f}",
        "svm_prop_er": f"{grid('er_20_5', 1, 'proportion', 1):.2f}",
        "dqda_auc_ours": f"{float(S[('alt20_p1000_k0.10', 'bal20', 'DQDA', 'AUC')]['mean']):.2f}",
        "dqda_ratio": ", ".join(f"{v['by_score']['ratio of the discriminants']:.2f}" for v in dq.values()),
        "dlda_ratio": f"{dq['k1train 0.1']['by_score']['DLDA: ratio']:.2f}",
        "af10_hits": c["af10"]["matched"], "af10_n": c["af10"]["n_fields"],
        **more_facts(h, c, run),
        "af10_500_hits": c["af10.ntest500"]["matched"], "af10_500_n": c["af10.ntest500"]["n_fields"],
    }


def claim_facts(run, h):
    cl = json.load(open(Path(run) / "claims.json"))
    sh = [f["observed_share"] for f in cl["text.fig4_selection"]["fields"]]
    rt = h["rf_thr_null"]
    g = lambda k: f"{rt['k1train_0.1'][k]:.2f} and {rt['k1train_0.9'][k]:.2f}"  # noqa: E731
    ge_flat = abs(rt["k1train_0.9"]["class weights, >= at the cutoff"] - rt["k1train_0.1"]["class weights, >= at the cutoff"]) <= 0.05
    return {"sel_shares": ", ".join(f"{v:.2f}" for v in sh), "sel_pooled": f"{sum(sh) / len(sh):.2f}",
            "rf_thr_ours": g("class weights (ours)"), "rf_thr_nocw": g("no class weights"), "rf_thr_ge": g("class weights, >= at the cutoff"),
            "rf_thr_ge_result": "rejected" if ge_flat else "supported"}


def more_facts(h, c, run_dir="."):
    """Facts of the PAM, SVM, over-sampling, centring and interval hypotheses."""
    R = lambda case, key, m: h[case]["res"][key][m]  # noqa: E731
    paper = {f["name"]: f["expected"] for f in c["af8"]["fields"]}
    z = {"matched": 0, "n": 0}
    nc = {k: {"centred": c[f"{k}.hyp_nocenter"].get("centred", z), "not centred": c[f"{k}.hyp_nocenter"].get("not centred", z)}
          for k in ("fig3", "af4", "af5")}
    ot = {k: c[f"{k}.hyp_over_test"] for k in ("fig5", "af8")}
    f2 = lambda v: f"{v:.2f}"  # noqa: E731
    pv = lambda v, k, i=0: v[k] if isinstance(v, dict) else v[i] if isinstance(v, list) else v  # noqa: E731  (R vectors lose their names)
    return {
        "svm_over_w": f"Additional file 8, k1train 0.1: PA1 {f2(R('over_k0.10', 'SVM weights from the over-sampled set', 'PA1'))} and "
                      f"{f2(R('over_k0.10', 'SVM weights from the original set', 'PA1'))}",
        "nc_fig3_c": nc["fig3"]["centred"]["matched"], "nc_fig3_cn": nc["fig3"]["centred"]["n"],
        "nc_fig3": nc["fig3"]["not centred"]["matched"], "nc_fig3_n": nc["fig3"]["not centred"]["n"],
        "nc_af4_c": nc["af4"]["centred"]["matched"], "nc_af5_c": nc["af5"]["centred"]["matched"],
        "nc_af4": nc["af4"]["not centred"]["matched"], "nc_af4_n": nc["af4"]["not centred"]["n"],
        "nc_af5": nc["af5"]["not centred"]["matched"], "nc_af5_n": nc["af5"]["not centred"]["n"],
        "ot_fig5_i": ot["fig5"]["as_imbalanced_as_training"]["matched"], "ot_fig5_b": ot["fig5"]["balanced"]["matched"], "ot_fig5_n": ot["fig5"]["balanced"]["n"],
        "ot_af8_i": ot["af8"]["as_imbalanced_as_training"]["matched"], "ot_af8_b": ot["af8"]["balanced"]["matched"], "ot_af8_n": ot["af8"]["balanced"]["n"],
        "ord_dlda_a": f2(R("over_k0.20", "DLDA selection after over-sampling (ours)", "PA")),
        "ord_dlda_b": f2(R("over_k0.20", "DLDA selection before over-sampling", "PA")),
        "ord_dqda_a": f2(R("over_k0.20", "DQDA selection after over-sampling (ours)", "PA")),
        "ord_dqda_b": f2(R("over_k0.20", "DQDA selection before over-sampling", "PA")),
        "ord_3nn_a": f2(R("over_k0.20", "3-NN selection after over-sampling (ours)", "PA")),
        "ord_3nn_b": f2(R("over_k0.20", "3-NN selection before over-sampling", "PA")),
        "ord_dlda_p": f2(float(paper["DLDA over PA, x = 0.2"])), "ord_dqda_p": f2(float(paper["DQDA over PA, x = 0.2"])),
        "pp_af8_p": f2(pv(h["over_k0.10"]["paper_af8"], "PAM_PA")), "pp_af8_a": f2(R("over_k0.10", "PAM: ours", "PA")),
        "pp_af8_b": f2(R("over_k0.10", "PAM: original prior", "PA")),
        "pp_af9_p": f2(pv(h["af9_k0.05"]["paper_af9"], "PAM_PA1", 0)), "pp_af9_a": f2(R("af9_k0.05", "PAM: ours", "PA1")),
        "pp_af9_b": f2(R("af9_k0.05", "PAM: original prior", "PA1")),
        "pt_null_a": f2(R("pam_null_k0.45", "PAM: ours", "PA1")), "pt_null_s": f2(R("pam_null_k0.45", "PAM: smallest threshold", "PA1")),
        "pt_null_cv": f2(R("pam_null_k0.45", "PAM: 10-fold CV", "PA1")), "pt_null_e": f2(R("pam_null_k0.45", "PAM: equal priors", "PA1")),
        "pt_er_a": f2(R("pam_er_45_5", "PAM: ours", "PA2")), "pt_er_s": f2(R("pam_er_45_5", "PAM: smallest threshold", "PA2")),
        "pt_er_cv": f2(R("pam_er_45_5", "PAM: 10-fold CV", "PA2")), "pt_er_e": f2(R("pam_er_45_5", "PAM: equal priors", "PA2")),
        **claim_facts(run_dir, h),
        **{f"pt_af6_{w}": f2(float(v)) for w, v in zip("pa", next((f["expected"], f["observed"]) for f in c["af6"]["fields"] if f["name"] == "PAM none PA, x = 0.2"))},
        "pi_fig6": c["fig6.pi"]["matched"], "pi_fig6_n": c["fig6.pi"]["n_fields"],
        "pi_af12": c["af12"]["matched"], "pi_af12_n": c["af12"]["n_fields"],
        "pi_fig6_norm": c["fig6.pi.normal"]["matched"], "pi_af12_norm": c["af12.normal"]["matched"],
        "pi_fig6_q90": c["fig6.pi.q90"]["matched"], "pi_af12_q90": c["af12.q90"]["matched"],
    }


def fill(obj, F):
    if isinstance(obj, str):
        def rep(m):
            if m.group(1) not in F:
                raise KeyError(f"results_notes.json cites an unknown fact {{{m.group(1)}}}")
            return str(F[m.group(1)])
        return re.sub(r"\{([a-z0-9_]+)\}", rep, obj)
    if isinstance(obj, list):
        return [fill(x, F) for x in obj]
    if isinstance(obj, dict):
        return {k: fill(v, F) for k, v in obj.items()}
    return obj


def af1_identical(fields):
    """Cells of Additional file 1 whose printed value is the same for all nine classifiers."""
    by = {}
    for f in fields:
        cl, k1, nt, m = f["name"].split(" ")
        by.setdefault((k1, nt, m), set()).add(f["expected"])
    return {key for key, vals in by.items() if len(vals) == 1}


def fields_of(run, src):
    kind, _, key = src.partition(":")
    if kind == "comparison":
        d = json.load(open(Path(run) / "comparison.json"))[key]
        return [{k: f[k] for k in KEEP if k in f} for f in d["fields"]], d
    if kind == "claims":
        d = json.load(open(Path(run) / "claims.json"))[key]
        out = []
        for f in d["fields"]:
            g = {k: f[k] for k in KEEP if k in f}
            if "tolerance" not in g:
                g["tolerance"] = {"printed": True}
            if g.get("observed") is None:
                g["observed"] = "not computed"
            out.append(g)
        return out, d
    raise KeyError(src)


def arithmetic(run):
    claims = json.load(open(Path(run) / "claims.json"))
    back, missed = [], []
    for cid, c in claims.items():
        for f in c["fields"]:
            a = f.get("arithmetic")
            if a is None:
                continue
            g = {"expected": f["expected"], "observed": a, "tolerance": f.get("tolerance", {"printed": True})}
            (back if field_matches(g, None) else missed).append(f"{cid}: {f['name']} (paper says {f['expected']}, its own values give {a})")
    detail = (f"{len(back)} of {len(back) + len(missed)} statements follow from the paper's own figures and tables"
              + (". Not: " + "; ".join(missed) + "." if missed else "."))
    return {"passed": True, "detail": detail, "back": len(back), "checked": len(back) + len(missed), "missed": missed}


def main():
    args = sys.argv[1:]
    env = None
    if "--environment" in args:
        i = args.index("--environment")
        env = json.load(open(args[i + 1]))
        del args[i:i + 2]
    run, out = args
    notes = json.load(open(NOTES))
    notes["causes"] = fill(notes["causes"], facts_of(run))
    res = {"schema": "paper2repro/results/v1", "paper": notes["paper"], "run": copy.deepcopy(notes["run"]),
           "session": notes["session"], "skill": notes["skill"], "items": []}
    if env:
        res["run"]["environment"] = env
    problems = []
    for it in notes["items"]:
        it = copy.deepcopy(it)
        sets = it.pop("assumptions_from", [])
        if sets:
            it["assumptions"] = [a for s in sets for a in notes["assumption_sets"][s]] + it.get("assumptions", [])
        cause_key = it.pop("cause_from", None)
        always = it.pop("cause_always", False)
        rule = it.pop("exceptions_rule", None)
        src = it.pop("from", None)
        if cause_key and cause_key in notes["causes"]:
            it["cause"] = copy.deepcopy(notes["causes"][cause_key])
        elif cause_key:
            problems.append(f"{it['id']}: the notes name a cause '{cause_key}' they do not define")
        if src == "arithmetic":
            it["check"] = {k: v for k, v in arithmetic(run).items() if k in ("passed", "detail")}
        elif src == "port":
            d = json.load(open(Path(run) / "port_check.json"))
            it["check"] = {"passed": bool(d["passed"]),
                           "detail": (f"DLDA {d['dlda_agree']} and DQDA {d['dqda_agree']} of {d['test_samples']} test-sample predictions "
                                      f"identical to sma::stat.diag.da (sma {d['sma_version']}) on {d['datasets']} simulated training sets; "
                                      f"AUC equal to Hmisc::somers2 in {d['auc_comparisons']} tries (largest difference {d['auc_max_abs_diff']:.1g}); "
                                      f"t statistics equal to t.test (largest difference {d['t_max_abs_diff']:.1g})")}
        elif src == "package":
            p = Path(run) / "package.json"
            d = json.load(open(p)) if p.exists() else {"passed": False, "detail": "package check not run"}
            it["check"] = {"passed": bool(d["passed"]), "detail": d.get("detail", "")}
        elif src:
            fields, _ = fields_of(run, src)
            it["values"] = {"fields": fields}
            missed = [f for f in fields if not matches(f)]
            exc = []
            if rule == "af1_plr_columns":
                same = af1_identical(fields)
                for f in missed:
                    cl, k1, nt, m = f["name"].split(" ")
                    if cl != "PLR" and m != "AUC" and (k1, nt, m) in same:
                        exc.append({"field": f["name"], "category": "paper_error",
                                    "evidence": "Additional file 1 prints this cell identically for all nine classifiers; the values are PLR's "
                                                "(they match the PLR curve of the paper's own Fig. 1 and Fig. 2), while Figs 1 and 2 show other values for this classifier."})
            elif rule == "arithmetic":
                for f in missed:
                    a = f.get("arithmetic")
                    if a is not None and not field_matches({"expected": f["expected"], "observed": a,
                                                            "tolerance": f.get("tolerance", {"printed": True})}, None):
                        exc.append({"field": f["name"], "category": "paper_error",
                                    "evidence": f"The paper's own figures and tables give {a} here, not {f['expected']} (output/claims.json, 'arithmetic')."})
            if exc:
                it["values"]["exceptions"] = exc
            counted_missed = [f for f in missed if f["name"] not in {e["field"] for e in exc}]
            if counted_missed and "cause" not in it:
                problems.append(f"{it['id']}: {len(counted_missed)} fields miss and the notes give no cause, e.g. {counted_missed[0]['name']}")
            if not counted_missed and not always and "cause" in it:
                del it["cause"]
        res["items"].append(it)
    if problems:
        print("results_notes.json does not explain the run:\n  " + "\n  ".join(problems), file=sys.stderr)
    with open(out, "w") as f:
        json.dump(res, f, indent=1)
        f.write("\n")
    r = subprocess.run([sys.executable, str(HERE / "check_results.py"), out, "--write", "--skip-files"])
    sys.exit(1 if problems else r.returncode)


if __name__ == "__main__":
    main()
