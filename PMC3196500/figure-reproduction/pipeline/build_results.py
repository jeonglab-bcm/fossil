"""Merge results_notes.json (written by hand) with the numbers of a run into results.json, then let
check_results.py compute every verdict and the summary.

Usage: build_results.py RUN_DIR OUT.json [--environment ENV.json]

RUN_DIR holds the run's tables.json, figures.json, claims.json, simulation.json and package.json.
The notes give the paper, the run block, the skill block, the labels, assumptions and the causes of the
tables; every figure panel's item is generated here from figures.json (one item per panel), with its pass
mark, controls, assumptions and cause computed from the panel's own numbers. Strings in the notes may
cite run facts as {name}; an unknown name fails the build, so prose cannot drift from the numbers.
"""
import copy
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NOTES = HERE.parent / "results_notes.json"
PANEL_LETTERS = "abcdef"
FIG_LABEL = {"fig2": "Fig. 2"} | {f"figS{k}": f"Fig. S{k}" for k in range(1, 13)}
DUPLICATE_OF = {"figS5": "figS1", "figS6": "figS2", "figS7": "figS3"}


def load(run, name):
    return json.load(open(Path(run) / name))


def facts_of(run):
    t = load(run, "tables.json")
    f = load(run, "figures.json")
    sim = load(run, "simulation.json")
    tb = t["tables"]
    facts = {}
    for k in ("table1", "tableS3", "tableS4"):
        s = tb[k]["summary"]
        for kk, v in s.items():
            facts[f"{k}_{kk}"] = v
    for kk, v in tb["table2"]["summary"].items():
        facts[f"table2_{kk}"] = v
    for k in ("table3_ois", "table4_ois"):
        for kk, v in tb[k]["summary"].items():
            facts[f"{k}_{kk}"] = v
    s34 = tb["table34_sim"]
    facts.update({"t34_cells": s34["cells"], "t34_rules": s34["rules_tried"], "t34_best": s34["best_rule_cells"],
                  "t34_any": s34["cells_any_rule"], "t34_def_max": max(s34["methods_definition_cells"].values())})
    for v, d in t["hypotheses"].items():
        facts[f"h_{v}_table1_exact"] = d["table1"]["exact"]
        facts[f"h_{v}_table1_within_one_bin"] = d["table1"]["within_one_bin"]
    srch = {(g["bin_rule"], g["read_rule"]): g["exact"] for g in t["search"]}
    facts.update({f"search_{a}_{b}": v for (a, b), v in srch.items()})
    ch = t["chosen"]
    facts.update({"chosen_bin_rule": ch["bin_rule"], "chosen_read_rule": ch["read_rule"],
                  "s3_patient_width": ch["widths"]["tableS3"]["patients"]})
    rs = f["rule_search"]
    facts.update({"fig_rule_patients": f["rules"]["patients"], "fig_rule_events": f["rules"]["events"],
                  "fig_pat_nearest": rs["patients"]["mean_score"]["nearest"], "fig_pat_interval": rs["patients"]["mean_score"]["interval"],
                  "fig_ev_nearest": rs["events"]["mean_score"]["nearest"], "fig_ev_interval": rs["events"]["mean_score"]["interval"]})
    m = sim["runs"]["main"]
    facts["no_estimate_max"] = f"{100 * max(r['no_estimate_share'] for r in m.values()):.2f}"
    return facts


def fill(obj, facts):
    if isinstance(obj, str):
        def rep(mm):
            if mm.group(1) not in facts:
                raise KeyError(f"results_notes.json cites an unknown fact {{{mm.group(1)}}}")
            return str(facts[mm.group(1)])
        return re.sub(r"\{([A-Za-z0-9_]+)\}", rep, obj)
    if isinstance(obj, list):
        return [fill(x, facts) for x in obj]
    if isinstance(obj, dict):
        return {k: fill(v, facts) for k, v in obj.items()}
    return obj


def pct(x):
    return f"{100 * x:.1f}%"


def panel_items(run, notes):
    figs = load(run, "figures.json")
    tol = figs["tolerance_px"]
    items = []
    for fig, fr in figs["figures"].items():
        for i, p in enumerate(fr["panels"]):
            sizes, pc, tau, rrr = p["scenario"].split("_")
            sc = (f"{'Cochrane' if sizes == 'cochrane' else 'common'} trial sizes, PC {pc[2:]}%, tau2 {tau[3:]}, "
                  f"true RRR {rrr[3:]}%, cumulative {p['axis']}")
            pid = f"{fig}.{p['axis']}" if fig == "fig2" else f"{fig}.{PANEL_LETTERS[i]}"
            label = (f"{FIG_LABEL[fig]}, {'upper' if p['axis'] == 'patients' else 'lower'} panel ({sc})" if fig == "fig2"
                     else f"{FIG_LABEL[fig]}, {'top' if i < 3 else 'bottom'} {['left', 'middle', 'right'][i % 3]} ({sc})")
            s = min(p["published_near_ours"], p["ours_near_published"])
            best = max(c["score"] for c in p["controls"])
            ceiling = p["chance_ceiling"]
            # Pass mark: above every control, and at least 90% of the chance ceiling (how close our two
            # runs with other seeds are to each other on the same grid).
            thr = round(max(best + 0.01, 0.9 * ceiling), 4)
            it = {"id": pid, "label": label, "kind": "figure", "source": "reconstructed", "method": "pixels",
                  "pixels": {"tolerance_px": tol, "dpi": None, "published_near_ours": p["published_near_ours"],
                             "ours_near_published": p["ours_near_published"], "threshold": min(thr, 0.9999),
                             "controls": p["controls"], "chance_ceiling": ceiling,
                             "hypotheses": {k: min(v.values()) for k, v in p["hypotheses"].items()}},
                  "assumptions": copy.deepcopy(notes["assumption_sets"]["simulation"] + notes["assumption_sets"]["figures"]),
                  "outputs": [f"figure-reproduction/output/{fig}_ours.png", f"figure-reproduction/output/{fig}_overlay.png"]}
            alt_name, alt = next((k, v) for k, v in it["pixels"]["hypotheses"].items() if k.startswith("rule_"))
            near = {c["name"]: c["score"] for c in p["controls"] if c["kind"] == "near_miss"}
            if fig in DUPLICATE_OF:
                coch = it["pixels"]["hypotheses"]["cochrane_sizes"]
                same_file = fr["sha256"] == figs["figures"][DUPLICATE_OF[fig]]["sha256"]
                it["cause"] = {
                    "category": "paper_error",
                    "summary": (f"{FIG_LABEL[fig]} is a byte copy of {FIG_LABEL[DUPLICATE_OF[fig]]} (the same TIFF file, SHA-256 "
                                f"identical): it shows the Cochrane-size scenario, not the 'common' one its caption names. Our "
                                f"Cochrane-size curves score {pct(coch)} on this panel, our 'common'-size curves {pct(s)}."),
                    "evidence": ["figure-reproduction/output/figures.json"],
                    "hypotheses": [{"hypothesis": "The panel shows the Cochrane trial-size scenario (the file is a copy of "
                                                  f"{FIG_LABEL[DUPLICATE_OF[fig]]})",
                                    "test": f"SHA-256 of the two supplement files ({'identical' if same_file else 'different'}); "
                                            f"our Cochrane-size curves score {pct(coch)} on the panel",
                                    "result": "supported" if same_file else "rejected"},
                                   {"hypothesis": "The panel shows the 'common'-size scenario its caption names",
                                    "test": f"our 'common'-size curves score {pct(s)}",
                                    "result": "rejected" if same_file else "inconclusive"}],
                    "status": "explained" if same_file else "open"}
            else:
                hyps = [
                    {"hypothesis": "Chance: a run with other seeds lands this far from ours",
                     "test": f"score our second run against our first on the same grid: {pct(ceiling)}; ours against the paper: {pct(s)}",
                     "result": "supported" if s >= 0.9 * ceiling else "rejected"},
                    {"hypothesis": f"The other binning rule ({alt_name[5:]})",
                     "test": f"score the curves binned by {alt_name[5:]}: {pct(alt)}",
                     "result": "rejected" if alt <= s else "inconclusive"},
                    {"hypothesis": "An amplitude difference of about 5%",
                     "test": f"score ours x1.05 ({pct(near['ours x1.05'])}) and x0.95 ({pct(near['ours x0.95'])})",
                     "result": "inconclusive" if max(near["ours x1.05"], near["ours x0.95"]) > s else "rejected"},
                    {"hypothesis": "A shift of one point along x",
                     "test": f"score ours shifted one point right: {pct(near['ours one point right'])}",
                     "result": "inconclusive" if near["ours one point right"] > s else "rejected"},
                ]
                chance = hyps[0]["result"] == "supported"
                it["cause"] = {
                    "category": "nondeterminism" if chance else "unknown",
                    "summary": (f"Our curves score {pct(s)} within {tol} px (pass mark {pct(min(thr, 0.9999))}); our two runs score "
                                f"{pct(ceiling)} against each other. " + notes["panel_cause_note"]),
                    "evidence": ["figure-reproduction/output/figures.json", f"figure-reproduction/output/{fig}_overlay.png"],
                    "hypotheses": hyps, "status": "explained" if chance else "open"}
            if pid in notes.get("panel_reviews", {}):
                it["review"] = copy.deepcopy(notes["panel_reviews"][pid])
            items.append(it)
    return items


def table_items(run, notes):
    t = load(run, "tables.json")
    out = []
    for it in notes["items"]:
        it = copy.deepcopy(it)
        sets = it.pop("assumptions_from", [])
        if sets:
            it["assumptions"] = [a for s in sets for a in notes["assumption_sets"][s]] + it.get("assumptions", [])
        src = it.pop("fields_from", None)
        if src:
            fields = [{k: f[k] for k in ("name", "expected", "observed")} for f in t["tables"][src]["fields"]]
            it["values"] = {"fields": fields, "tolerance": {"printed": True}}
            if "exceptions" in it:
                it["values"]["exceptions"] = it.pop("exceptions")
        if it.pop("claims_from", None):
            c = next(c for c in load(run, "claims.json")["claims"] if c["id"] == it["id"])
            it["values"] = {"fields": [{k: f[k] for k in ("name", "expected", "observed")} for f in c["fields"]],
                            "tolerance": {"printed": True}}
        chk = it.pop("check_from", None)
        if chk == "package.json":
            p = Path(run) / chk
            d = json.load(open(p)) if p.exists() else {"passed": False, "detail": "package check not run"}
            it["check"] = {"passed": bool(d["passed"]), "detail": d.get("detail", "")}
        elif chk == "claims.json":
            c = load(run, "claims.json")
            back, total, notes_ = 0, 0, []
            for cl in c["claims"]:
                cid = cl["id"]
                for f in cl["fields"]:
                    if "arithmetic" in f:
                        total += 1
                        ok = f["arithmetic"] == f["expected"]
                        back += ok
                        notes_.append(f"{cid} ({f['name']}): {f['arithmetic']}, {100 * f['arithmetic_share']:.0f}% of cases")
            it["check"] = {"passed": back == total,
                           "detail": f"{back} of {total} statements follow from the paper's own Tables 1, S3, S4 and 2: " + "; ".join(notes_)
                                     + ". The claim about early probabilities above 25% rests on the figures only."}
        out.append(it)
    return out


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
    notes = {k: (fill(v, facts) if k in ("items", "assumption_sets", "panel_cause_note") else v) for k, v in notes.items()}
    run_block = copy.deepcopy(notes["run"])
    if env:
        run_block["environment"] = env
    items = table_items(run, notes)
    # figure panels go after Fig. 1 in the paper's order: Fig. 2, then the supplement's
    figs = panel_items(run, notes)
    pos = next(i for i, it in enumerate(items) if it["id"] == "fig1") + 1
    items = items[:pos] + figs + items[pos:]
    res = {"schema": "paper2repro/results/v1", "paper": notes["paper"], "run": run_block,
           "session": notes["session"], "skill": notes["skill"], "items": items}
    with open(out, "w") as f:
        json.dump(res, f, indent=1, ensure_ascii=False)
        f.write("\n")
    r = subprocess.run([sys.executable, str(HERE / "check_results.py"), out, "--write", "--skip-files"])
    sys.exit(r.returncode)


if __name__ == "__main__":
    main()
