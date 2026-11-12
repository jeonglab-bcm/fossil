"""Merge results_notes.json (written by hand: labels, sources, assumptions, causes) with the numbers
of a run into results.json, then let check_results.py compute the verdicts and the summary.

  build_results.py RUN_DIR OUT.json

Notes items take their numbers from the run folder:
  "fields_from": "comparison.json:fig1"     values.fields = the comparison's fields for that item
  "fields_from": "table1.json"              values.fields = Table 1 recomputed
  "claim": "text.x"                         one field from H4M4 ("H4M4 (Figs 1-6)": expected
                                            "yes", observed ours), plus one per other genetic model
                                            when "models" is true (the text says "under all models")
  "check_from": "port_check.json"           check.passed and a detail line
The skill block and the session pointer travel with the notes (copied unchanged).
"""

import copy
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NOTES = HERE.parent / "results_notes.json"


def yn(v):
    return "yes" if v else "no"


def check_detail(run, name):
    d = json.load(open(Path(run) / name))
    if name == "port_check.json":
        f0, f1 = d["forests"]["RF0"], d["forests"]["RF1"]
        return d["passed"], (
            f"Fortran Random Forests 5.1 against rfld on {f0['datasets']} data sets: IM differs from "
            f"Fortran {f0['ratio_mad_im']:.2f}x as much as from itself with another seed (RF0), "
            f"{f1['ratio_mad_im']:.2f}x (RF1); risk-SNP IM difference z = {f0['rsnp_im_diff_z']:.2f} (RF0), "
            f"{f1['rsnp_im_diff_z']:.2f} (RF1)")
    if name == "haplo_check.json":
        return d["passed"], (
            f"haplo.stats {d['haplo_stats_version']} haplo.em against rfld.haplotype_em on {d['datasets']} "
            f"simulated data sets: frequencies within {d['max_abs_freq_diff']:.1e}, phase posteriors within "
            f"{d['max_abs_posterior_diff']:.1e}")
    if name == "package.json":
        return d["passed"], d.get("detail", "")
    if name == "comparison.json":  # text.arithmetic
        paper = d["claims"]["paper"]
        ad = d["claims"]["ad"]
        checked = {k: v for k, v in paper.items() if v is not None}
        back = [k for k, v in checked.items() if v]
        bad = [k for k, v in checked.items() if not v]
        ad_ok = ad["missed_by_single_snp"] == 7 and ad["n_top_snps"] == 17 and ad["rs4420638_in_top11_all"] \
            and ad["rf0im0_lower_with_ld"] and ad["rf1im1_highest_dataset1"] and ad["rf1im1_closest_to_no_ld"]
        detail = (f"{len(back)} of {len(checked)} claims about Figs 1-5 follow from the paper's own figure values"
                  + (f" (not: {', '.join(bad)})" if bad else "")
                  + f"; the AD application's claims follow from Tables 3 and 4 ({ad['missed_by_single_snp']} of "
                  f"{ad['n_top_snps']} top SNPs have p > 0.05 in both tests)" if ad_ok else "; Tables 3-4 claims do not")
        return True, detail
    raise KeyError(name)


def main(run, out):
    notes = json.load(open(NOTES))
    comp = json.load(open(Path(run) / "comparison.json"))
    res = {"schema": "paper2repro/results/v1", "paper": notes["paper"], "run": notes["run"],
           "session": notes.get("session", {"ledger": "session/ledger.json"}), "skill": notes["skill"],
           "items": []}
    for it in notes["items"]:
        it = copy.deepcopy(it)
        src = it.pop("fields_from", None)
        if src:
            f, _, key = src.partition(":")
            d = json.load(open(Path(run) / f))
            fields = d["items"][key]["fields"] if key else d["fields"]
            it.setdefault("values", {})["fields"] = copy.deepcopy(fields)
            if key:
                it.setdefault("comparison", {})
                it["comparison"]["controls"] = d["items"][key]["controls"]
                it["comparison"]["chi2_diagnostic"] = d["items"][key]["consistency"]
        claim = it.pop("claim", None)
        if claim:
            ours = comp["claims"]["ours"][claim]
            if isinstance(ours, dict):
                fields = [{"name": f"H4M4, {k}", "expected": "yes", "observed": yn(v)} for k, v in ours.items()]
            else:
                fields = [{"name": "H4M4 (the figures)", "expected": "yes", "observed": yn(ours)}]
            if it.pop("models", False):
                for model, cl in sorted(comp["claims"]["other_models"].items()):
                    if claim in cl:
                        fields.append({"name": model, "expected": "yes", "observed": yn(cl[claim])})
            it.setdefault("values", {})["fields"] = fields
            it["paper_figure_gives"] = (None if comp["claims"]["paper"].get(claim) is None
                                        else yn(comp["claims"]["paper"][claim]))
        chk = it.pop("check_from", None)
        if chk:
            passed, detail = check_detail(run, chk)
            it["check"] = {"passed": bool(passed), "detail": detail}
        res["items"].append(it)
    json.dump(res, open(out, "w"), indent=1)
    checker = HERE / "check_results.py"
    r = subprocess.run([sys.executable, str(checker), out, "--write", "--skip-files"])
    sys.exit(r.returncode)


if __name__ == "__main__":
    main(*sys.argv[1:3])
