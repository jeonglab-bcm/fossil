"""Merge results_notes.json (written by hand: labels, sources, assumptions, causes) with the numbers of
a run into results.json, then let check_results.py compute the verdicts and the summary.

  build_results.py RUN_DIR OUT.json

RUN_DIR holds analysis.json (reproduce.py), figures.json (figures.py), package.json
(check_package.py) and checks/weka_versions.json. Notes items take their numbers from it:
  "fields_from": "<key>"      values.fields = analysis.json items[<key>]
  "pixels_from": "fig3.a"     the pixel scores and controls of figures.json fig3/a
  "check_from": "<name>"      check.passed and a detail line: port, weka_versions, package,
                              arithmetic, normalisation
The skill block and the session pointer travel with the notes (copied unchanged).
"""

import copy
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NOTES = HERE.parent / "results_notes.json"


def figure_claims(analysis, figures, pub):
    """Claims checked against the published figures read back to numbers (digitised: within 1.5
    points for Fig. 4 and 0.015 for an AUC)."""
    out = []
    t3 = pub["table3"]
    for panel, s in (("a", "training"), ("b", "hgmd"), ("c", "oligogenic")):
        auc = figures["fig3"][panel]["digitised_auc"]
        out.append({"claim": f"Fig. 3{panel} points read back: AUC {auc:.3f} against Table 3's {t3[s]['auc']}",
                    "expected": t3[s]["auc"], "observed": round(auc, 3), "follows": abs(auc - float(t3[s]["auc"])) <= 0.015})
    curves = figures["fig4"]["curves"]
    A = pub["artificial_loci"]
    name = {"hgmd": "hgmd", "omim": "omim", "pocus": "oligogenic"}
    for s in ("hgmd", "omim", "pocus"):
        for k, v in A[s].items():
            if not k.startswith("top"):
                continue
            top = int(k[3:])
            read = curves[name[s]].get(str(top))
            out.append({"claim": f"Fig. 4 {s} at top {top}%: {read} against the text's {v[1]}%", "expected": v[1],
                        "observed": read, "follows": read is not None and abs(read - float(v[1])) <= 1.5})
    read = curves["omim"].get("30")
    out.append({"claim": f"Fig. 4 caption: training set at top 30% 'around 56%': {read}", "expected": "56",
                "observed": read, "follows": read is not None and abs(read - 56) <= 1.5})
    E = figures["fig4"]["enrichment"]
    for fold, pct in pub["enrichment"]["abstract"].items():
        m = E[fold]["mean"]
        out.append({"claim": f"abstract: {fold}-fold enrichment {pct}% of the time; Fig. 4 mean of the three sets at the top "
                             f"{E[fold]['top_pct']}%: {m}", "expected": pct, "observed": m,
                    "follows": m is not None and abs(m - float(pct)) <= 1.5})
    m = E["25"]["mean"]
    out.append({"claim": f"conclusion: 25-fold enrichment ~11% of the time; Fig. 4 mean at the top 4%: {m}", "expected": "11",
                "observed": m, "follows": m is not None and abs(m - 11) <= 1.5})
    return out


def check_detail(run, name, analysis, figures, pub):
    if name == "port":
        pcs = analysis["port_check"]
        ok = all(p["passed"] for p in pcs)
        return ok, "; ".join(
            f"{p['label']}: tree text {'identical' if p['tree_identical'] else 'different'}, scores within "
            f"{p['max_abs_score_diff']:.1e}, 10-fold CV folds {'identical' if p['cv_folds_identical'] else 'different'}, "
            f"Weka's statistics {'identical' if p['statistics_identical'] else 'different'}" for p in pcs) + \
            " (prospectr_adtree against Weka 3.4.3 on the archived sets)"
    if name == "weka_versions":
        d = json.load(open(Path(run) / "checks" / "weka_versions.json"))
        return d["passed"], d["detail"]
    if name == "package":
        d = json.load(open(Path(run) / "package.json"))
        return d["passed"], d.get("detail", "")
    if name == "normalisation":
        g = analysis["genome"]
        ok = g["normalisation_max_err_e"] < 1e-6 and g["af1_raw_scores_on_3dp_grid_max_err"] < 1e-9
        return ok, (f"dump.tab's 22,240 normalised scores are 1/(1+e^raw) of its raw scores within "
                    f"{g['normalisation_max_err_e']:.1e} (with the Euler-Mascheroni constant in place of e they are off by up to "
                    f"{g['normalisation_max_err_euler_mascheroni']:.2f}); each of Additional File 1's 61 scores is 1/(1+e^a) of a raw "
                    f"score a with three decimals (within {g['af1_raw_scores_on_3dp_grid_max_err']:.0e}), as the printed tree's values give")
    if name == "arithmetic":
        claims = analysis["arithmetic"] + figure_claims(analysis, figures, pub)
        back = [c for c in claims if c["follows"]]
        bad = [c["claim"] for c in claims if not c["follows"]]
        detail = (f"{len(back)} of {len(claims)} claims follow from the paper's own numbers (text, tables, and Figs 3 and 4 "
                  f"read back); not: " + "; ".join(bad)) if bad else f"all {len(claims)} claims follow"
        return True, detail
    raise KeyError(name)


def main(run, out):
    run = Path(run)
    notes = json.load(open(NOTES))
    analysis = json.load(open(run / "analysis.json"))
    figures = json.load(open(run / "figures.json"))
    pub = json.load(open(HERE.parent / "published" / "published_values.json"))
    res = {"schema": "paper2repro/results/v1", "paper": notes["paper"], "run": notes["run"],
           "session": notes.get("session", {"ledger": "session/ledger.json"}), "skill": notes["skill"], "items": []}
    for it in notes["items"]:
        it = copy.deepcopy(it)
        key = it.pop("fields_from", None)
        if key:
            it.setdefault("values", {})["fields"] = copy.deepcopy(analysis["items"][key])
        px = it.pop("pixels_from", None)
        if px:
            fig, panel = px.split(".")
            f = figures[fig][panel]
            it["pixels"] = {"tolerance_px": figures["tolerance_px"], "dpi": None,
                            "published_near_ours": round(f["published_near_ours"], 6),
                            "ours_near_published": round(f["ours_near_published"], 6),
                            "threshold": figures["fig3_pass"],
                            "controls": [{k: (round(v, 6) if isinstance(v, float) else v) for k, v in c.items()} for c in f["controls"]]}
        chk = it.pop("check_from", None)
        if chk:
            passed, detail = check_detail(run, chk, analysis, figures, pub)
            it["check"] = {"passed": bool(passed), "detail": detail}
        res["items"].append(it)
    json.dump(res, open(out, "w"), indent=1)
    r = subprocess.run([sys.executable, str(HERE / "check_results.py"), out, "--write", "--skip-files"])
    sys.exit(r.returncode)


if __name__ == "__main__":
    main(*sys.argv[1:3])
