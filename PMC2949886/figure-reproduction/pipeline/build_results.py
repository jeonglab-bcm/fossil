"""Merge results_notes.json (written by hand: labels, sources, assumptions, causes) with the numbers
of a run into results.json, then let check_results.py compute the verdicts and the summary.

  build_results.py RUN_DIR OUT.json

Notes items take their numbers from the run folder:
  "pixels_from": "fig4:BH"        pixels = the comparison's two-way scores, pass mark and controls
                                  for that panel; outputs = its render and overlay; "data_units" =
                                  differences from the published values (not used for the verdict)
  "claims_from": "text.fig4"      values.fields = the claim's fields from claims.json (ours), and
                                  "paper_figure_gives" = the same rule on the published figure values
  "check_from": "package.json"    check.passed and its detail line
  "check_from": "arithmetic"      text.arithmetic: the claims recomputed from the paper's own figures
The skill block and the session pointer travel with the notes (copied unchanged). claims.py runs
first and writes claims.json into the run folder.
"""
import copy
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NOTES = HERE.parent / "results_notes.json"
FIGDIR = "figure-reproduction/output/figures"


def arithmetic(claims):
    """text.arithmetic: each claim's rule applied to the paper's own figure values."""
    rows = [(k, f) for k, v in claims.items() if isinstance(v, list) for f in v if "paper_figure_gives" in f]
    checked = [(k, f) for k, f in rows if f["paper_figure_gives"] is not None]
    back = [f for _, f in checked if f["paper_figure_gives"] == f["expected"]]
    notback = [f"{k}: {f['name']}" for k, f in checked if f["paper_figure_gives"] != f["expected"]]
    ar = claims["text.arithmetic"]
    nums = [f"{v['name']} = {v['observed']} (paper {v['expected']})" for v in ar.values() if v["observed"] != v["expected"]]
    detail = (f"{len(back)} of {len(checked)} claims hold on the values read from the paper's own figures"
              + (f"; not on the paper's figures: {'; '.join(notback)}" if notback else "")
              + f". {len(rows) - len(checked)} claims need the Fig. S4 test labels, which are not text in the PDF. "
              + "The paper's own numbers: " + "; ".join(nums) + ".")
    return detail


def main(run, out):
    run = Path(run)
    notes = json.loads(NOTES.read_text())
    comp = json.loads((run / "comparison.json").read_text())
    subprocess.run([sys.executable, str(HERE / "claims.py"), str(run), str(run / "claims.json")], check=True,
                   capture_output=True)
    claims = json.loads((run / "claims.json").read_text())
    res = {"schema": "paper2repro/results/v1", "paper": notes["paper"], "run": notes["run"],
           "session": notes.get("session", {"ledger": "session/ledger.json"}), "skill": notes["skill"],
           "items": []}
    for it in notes["items"]:
        it = copy.deepcopy(it)
        src = it.pop("pixels_from", None)
        if src:
            fig, panel = src.split(":")
            p = comp["figures"][fig]["panels"][panel]
            it["pixels"] = {"tolerance_px": comp["tolerance_px"], "dpi": comp["dpi"] if not fig.startswith("figS") else comp["dpi"],
                            "published_near_ours": p["published_near_ours"], "ours_near_published": p["ours_near_published"],
                            "threshold": p["threshold"], "controls": p["controls"]}
            if p.get("values"):
                it["data_units"] = p["values"]
            it["outputs"] = [f"{FIGDIR}/{fig}_ours.png", f"{FIGDIR}/{fig}_overlay.png"]
        src = it.pop("claims_from", None)
        if src:
            fields = claims[src]
            it.setdefault("values", {})["fields"] = [{"name": f["name"], "expected": f["expected"], "observed": f["observed"]}
                                                     for f in fields]
            if any("paper_figure_gives" in f for f in fields):
                it["paper_figure_gives"] = {f["name"]: f["paper_figure_gives"] for f in fields}
        src = it.pop("arithmetic_from", None)
        if src:
            it.setdefault("values", {})["fields"] = list(claims["text.arithmetic"].values())
        chk = it.pop("check_from", None)
        if chk == "package.json":
            d = json.loads((run / "package.json").read_text())
            it["check"] = {"passed": bool(d["passed"]), "detail": d["detail"]}
        elif chk == "arithmetic":
            it["check"] = {"passed": True, "detail": arithmetic(claims)}
        res["items"].append(it)
    Path(out).write_text(json.dumps(res, indent=1))
    r = subprocess.run([sys.executable, str(HERE / "check_results.py"), out, "--write", "--skip-files"])
    sys.exit(r.returncode)


if __name__ == "__main__":
    main(*sys.argv[1:3])
