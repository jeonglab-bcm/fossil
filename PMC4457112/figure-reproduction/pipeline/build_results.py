#!/usr/bin/env python3
"""Merge results_notes.json (written by hand: labels, assumptions, causes) with the numbers of a run
into results.json, then let check_results.py compute every verdict and the summary.

Usage: build_results.py RUN_OUTPUT_DIR OUT.json [--environment ENV.json]

Notes items take their numbers from the run:
  "fields_from": "tables/table1" or "claims/text.mesh_better"   values.fields from comparison.json
  "check_from": "package.json"      check.passed and detail from check_package.py's report
  "check_from": "arithmetic"        text.arithmetic: every claim recomputed from the paper's own numbers
  "assumptions_from": [...]         shared assumption sets of the notes
  "cause_from": "<name>"            a shared cause of the notes (used when any field misses)
Strings in items, causes and assumptions may cite run facts as {name}; see facts_of().
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


def facts_of(run):
    """Numbers the notes cite, read from the run so the prose cannot drift from it."""
    run = Path(run)
    c = json.load(open(run / "comparison.json"))
    m = json.load(open(run / "models.json"))
    ds = json.load(open(run / "dataset.json"))
    dis = json.load(open(run / "disagreements.json"))
    sel = json.load(open(run / "selection.json"))
    var = json.load(open(run / "variants.json")) if (run / "variants.json").exists() else {}
    M, C = m["models"]["citation_plus_mesh"]["forward_selection"], m["models"]["citation_only"]["forward_selection"]
    MM, CC = m["models"]["citation_plus_mesh"], m["models"]["citation_only"]
    t = c["tables"]
    facts = {
        "dataset": f"{ds['dataset']:,}", "dataset_rct": f"{ds['dataset_rct']:,}",
        "humans": f"{ds['humans_1987_2012']:,}", "train_years": f"{ds['train_years']:,}",
        "train_sample": f"{ds['train_sample']:,}", "train_sample_rct": f"{ds['train_sample_rct']:,}",
        "test2011": f"{ds['test2011']:,}", "test2012": f"{ds['test2012']:,}",
        "test2011_rct": f"{ds['test2011_rct']:,}", "test2012_rct": f"{ds['test2012_rct']:,}",
        "rct_pt": f"{dis['rct_pt']:,}",
        "m_auc11": f"{M['2011']['auc']:.3f}", "c_auc11": f"{C['2011']['auc']:.3f}",
        "m_f1_11": f"{M['2011']['f1']:.3f}", "c_f1_11": f"{C['2011']['f1']:.3f}",
        "m_ap11": f"{M['2011']['average_precision']:.3f}", "c_ap11": f"{C['2011']['average_precision']:.3f}",
        "m_mse11": f"{M['2011']['mse']:.3f}", "m_mses11": f"{M['2011']['mse_sigmoid']:.3f}",
        "sets_c": ", ".join(sel["citation_only"]["chosen"]), "sets_m": ", ".join(sel["citation_plus_mesh"]["chosen"]),
        "n_sets_c": len(sel["citation_only"]["chosen"]), "n_sets_m": len(sel["citation_plus_mesh"]["chosen"]),
        "n_feat_c": f"{C['n_features']:,}", "n_feat_m": f"{M['n_features']:,}",
        "n_chisq_c": f"{CC['chisq']['n_features']:,}", "n_chisq_m": f"{MM['chisq']['n_features']:,}",
    }
    for k, v in t.items():
        facts[f"{k}_printed"] = v["summary"]["printed"]
        facts[f"{k}_within"] = v["summary"]["within_0.01"]
        facts[f"{k}_fields"] = v["summary"]["fields"]
    def meas(r):
        return (f"AUC {r['auc']:.3f}, AP {r['average_precision']:.3f}, F1 {r['f1']:.3f}"
                + (f", sigmoid MSE {r['mse_sigmoid']:.3f}" if "mse_sigmoid" in r else ""))

    for k in ("sel3_c", "sel3_m", "chisq_c_kept", "chisq_m_kept", "chisq_c_bonf", "chisq_m_bonf", "chisq_c_bonf_chisq",
              "chisq_m_bonf_chisq", "chisq_c_bonf_posthoc", "chisq_m_bonf_posthoc"):
        facts[k] = "not run"
    for kind, short in (("citation_plus_mesh", "m"), ("citation_only", "c")):
        v = var.get(kind, {})
        facts[f"var_{short}"] = "; ".join(f"{name}: {meas(r)}" for name, r in v.items()) or "not run"
        ch = var.get("chisq", {}).get(kind)
        if ch:
            facts[f"chisq_{short}_kept"] = ", ".join(f"p < {a}: {n:,}" if a != "Bonferroni" else f"Bonferroni: {n:,}"
                                                     for a, n in ch["kept"].items())
            facts[f"chisq_{short}_bonf"] = f"{ch['kept']['Bonferroni']:,}"
            facts[f"chisq_{short}_bonf_chisq"] = meas(ch["bonferroni_chisq_2011"])
            facts[f"chisq_{short}_bonf_posthoc"] = meas(ch["bonferroni_posthoc_2011"])
        s3 = var.get("selection_3_decimals", {}).get(kind)
        if s3:
            facts[f"sel3_{short}"] = f"{s3['n_sets']} sets ({', '.join(s3['chosen'])})"
    sf = json.load(open(run / "single_feature.json")) if (run / "single_feature.json").exists() else None
    if sf:
        facts["rand_f1"] = f"{sf['randomized']['title_or_abstract']['f1']:.2f}"
        for k, v in sf.get("hypotheses", {}).items():
            facts[f"rand_{k}"] = f"{v['f1']:.2f}"
    for k in ("conf_ge_0.95_without_rct_pt", "conf_ge_0.50_without_rct_pt", "conf_le_0.05_with_rct_pt"):
        facts["dis_" + k.replace(".", "")] = f"{dis[k]:,}"
    for k, v in dis.get("sigmoid_baseline", {}).items():
        facts["dis_sig_" + k.replace(".", "")] = f"{v:,}"
    tp = json.load(open(run / "topic.json")) if (run / "topic.json").exists() else None
    if tp:
        facts.update({f"topic_{k.replace('.', '')}": f"{v:,}" for k, v in tp.items()})
    return facts


def fill(obj, facts):
    if isinstance(obj, str):
        def rep(mm):
            if mm.group(1) not in facts:
                raise KeyError(f"results_notes.json cites an unknown fact {{{mm.group(1)}}}")
            return str(facts[mm.group(1)])
        return re.sub(r"\{([a-z0-9_.]+)\}", rep, obj)
    if isinstance(obj, list):
        return [fill(x, facts) for x in obj]
    if isinstance(obj, dict):
        return {k: fill(v, facts) for k, v in obj.items()}
    return obj


def get(d, path):
    for k in path.split("/"):
        d = d[k]
    return d


def arithmetic(claims, excepted):
    """Each claim recomputed from the paper's own numbers; misses must be recorded paper errors."""
    back, missed, unexplained = [], [], []
    for key, cl in claims.items():
        if key.startswith("_"):
            continue
        cid = key.replace("_", ".", 1)  # comparison.json keys text_<name>; items are text.<name>
        for f in cl["fields"]:
            if "arithmetic" not in f:
                continue
            g = {"expected": f["expected"], "observed": f["arithmetic"], "tolerance": {"printed": True}}
            if field_matches(g, None):
                back.append(cid)
            else:
                a = f["arithmetic"]
                a = f"{a:.4g}" if isinstance(a, float) else a
                missed.append(f"{cid}: {f['name']} ({f['expected']} against {a})")
                if (cid, f["name"]) not in excepted:
                    unexplained.append(missed[-1])
    mids = claims.get("_interval_midpoints", [])
    sym = sum(m["midpoint"] == float(m["auc"]) for m in mids)
    detail = (f"{len(back)} of {len(back) + len(missed)} statements follow from the paper's own numbers. "
              + ("Not: " + "; ".join(missed) + ". " if missed else "")
              + f"The four Hanley-McNeil intervals are centred on their AUC in {sym} of {len(mids)} cases.")
    return not unexplained, detail


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
    comp = json.load(open(Path(run) / "comparison.json"))
    run_block = copy.deepcopy(notes["run"])
    if env:
        run_block["environment"] = env
    res = {"schema": "paper2repro/results/v1", "paper": notes["paper"], "run": run_block,
           "session": notes["session"], "skill": notes["skill"], "items": []}
    excepted = {(it["id"], e["field"]) for it in notes["items"] for e in it.get("exceptions", [])
                if e.get("category") == "paper_error"}
    for it in notes["items"]:
        it = copy.deepcopy(it)
        sets = it.pop("assumptions_from", [])
        if sets:
            it["assumptions"] = [a for s in sets for a in notes["assumption_sets"][s]] + it.get("assumptions", [])
        cause = it.pop("cause_from", None)
        src = it.pop("fields_from", None)
        if src:
            fields = [{k: f[k] for k in ("name", "expected", "observed", "arithmetic", "within_0.01") if k in f}
                      for f in get(comp, src)["fields"]]
            it["values"] = {"fields": fields, "tolerance": {"printed": True}}
            if "exceptions" in it:
                it["values"]["exceptions"] = it.pop("exceptions")
            exc = {e["field"] for e in it["values"].get("exceptions", [])}
            misses = [f for f in fields if f["name"] not in exc and not field_matches(f, {"printed": True})]
            if misses and cause and "cause" not in it:
                it["cause"] = copy.deepcopy(notes["causes"][cause])
        if not src:
            it.pop("exceptions", None)  # kept in the notes for the arithmetic check only
        chk = it.pop("check_from", None)
        if chk == "package.json":
            p = Path(run) / chk
            d = json.load(open(p)) if p.exists() else {"passed": False, "detail": "package check not run"}
            it["check"] = {"passed": bool(d["passed"]), "detail": d.get("detail", "")}
        elif chk == "arithmetic":
            passed, detail = arithmetic(comp["claims"], excepted)
            it["check"] = {"passed": passed, "detail": detail}
        res["items"].append(it)
    with open(out, "w") as f:
        json.dump(res, f, indent=1)
        f.write("\n")
    r = subprocess.run([sys.executable, str(HERE / "check_results.py"), out, "--write", "--skip-files"])
    sys.exit(r.returncode)


if __name__ == "__main__":
    main()
