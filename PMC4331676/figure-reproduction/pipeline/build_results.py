"""Merge the run's numbers with the hand-written notes into results.json, then compute verdicts.

Usage: build_results.py RUN_DIR FIGURES_DIR SENSITIVITY.json REMOVED.tsv PACKAGE.json NOTES.json OUT.json

NOTES.json holds what a person writes: the paper block, the inputs, and per item its label, kind,
source, the paper's printed values (expected), assumptions and cause. Everything observed is read
here from the run's outputs; check_results.py --write then sets every verdict and the summary.
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def j(path):
    return json.loads(Path(path).read_text())


def yes(b):
    return "yes" if b else "no"


def pct(v):
    return round(float(v), 2)


def main(run, figs, sens_path, removed_path, pkg_path, notes_path, out):
    run, figs = Path(run), Path(figs)
    notes = j(notes_path)
    bench = j(run / "benchmark.json")["encodings"]
    lg = j(run / "lg_sweep.json")
    ind = j(run / "independent.json")
    w = j(run / "weights.json")
    lou = j(run / "lou.json")["rows"]
    akh = j(run / "akh.json")
    ds = j(run / "datasets.json")
    defn = j(run / "definition_check.json")
    scores = j(figs / "scores.json")
    pkg = j(pkg_path)
    jk = {e: bench[e]["jackknife"] for e in bench}
    obs = {}

    # ---- data
    obs["data.datasets"] = [
        {"name": "benchmark DNA-binding chains", "observed": ds["benchmark"]["positives"]},
        {"name": "benchmark non-binding chains", "observed": ds["benchmark"]["negatives"]},
        {"name": "PDB186 DNA-binding chains", "observed": ds["pdb186"]["positives"]},
        {"name": "PDB186 non-binding chains", "observed": ds["pdb186"]["negatives"]},
    ]
    # ---- Fig. 1
    f1 = []
    for r in lg:
        f1.append({"name": f"ACC at LG {r['LG']}", "observed": r["ACC"]})
        f1.append({"name": f"MCC at LG {r['LG']}", "observed": r["MCC"]})
    obs["fig1"] = f1
    best_acc = max(lg, key=lambda r: r["ACC"])["LG"]
    best_mcc = max(lg, key=lambda r: r["MCC"])["LG"]
    obs["text.lg_best"] = [{"name": "LG with the highest ACC", "observed": str(best_acc)},
                           {"name": "LG with the highest MCC", "observed": str(best_mcc)}]
    # ---- Tables 1 to 3
    for item, rows in (("table1", ["PSSM-DDT", "PSSM-SDT", "PSSM-DT"]),
                       ("table2", ["AvePscore-20", "AvePscore-400", "Pscore-100", "ACC", "PSSM-DT"])):
        obs[item] = [{"name": f"{r} {k}", "observed": (round(jk[r][k], 3) if k == "MCC" else pct(jk[r][k]))}
                     for r in rows for k in ("ACC", "MCC", "SN", "SP", "AUC")]
    obs["table3.dnabinder"] = [{"name": f"{lab} {k}", "observed": (round(jk[r][k], 3) if k == "MCC" else pct(jk[r][k]))}
                               for lab, r in (("DNAbinder(dimension 21)", "AvePscore-20"),
                                              ("DNAbinder(dimension 400)", "AvePscore-400"))
                               for k in ("ACC", "MCC", "SN", "SP", "AUC")]
    # ---- Table 4
    t4 = []
    for name, lab in (("iDNA-Prot", "iDNA-Prot"), ("DNA-Prot", "DNA-Prot"), ("DNAbinder", "DNAbinder"),
                      ("DNABIND", "DNABIND"), ("DBD-Threader", "DNA-Threader"), ("DBPPred", "DBPPred")):
        for k in ("ACC", "MCC", "SN", "SP", "AUC"):
            if k in lou[name]:
                t4.append({"name": f"{lab} {k}", "observed": round(lou[name][k], 4) if k == "MCC" else round(lou[name][k], 4)})
    obs["table4.comparators"] = t4
    p186 = ind["pdb186"]
    obs["table4.pssm-dt"] = [{"name": f"PSSM-DT {k}", "observed": (round(p186[k], 3) if k == "MCC" else pct(p186[k]))}
                             for k in ("ACC", "MCC", "SN", "SP", "AUC")]
    # ---- claims
    four = ["AvePscore-20", "AvePscore-400", "Pscore-100", "ACC"]
    obs["text.encodings_beaten"] = [
        {"name": f"PSSM-DT {k} above all four other encodings", "observed": yes(all(jk["PSSM-DT"][k] > jk[e][k] for e in four))}
        for k in ("ACC", "MCC", "AUC")] + [
        {"name": "ACC gain over the best other encoding (points)", "observed": pct(jk["PSSM-DT"]["ACC"] - max(jk[e]["ACC"] for e in four))},
        {"name": "AUC gain over the best other encoding (points)", "observed": pct(jk["PSSM-DT"]["AUC"] - max(jk[e]["AUC"] for e in four))},
        {"name": "PSSM-DT ACC above PSSM-DDT and PSSM-SDT", "observed": yes(jk["PSSM-DT"]["ACC"] > max(jk["PSSM-DDT"]["ACC"], jk["PSSM-SDT"]["ACC"]))},
    ]
    others = {n: lou[n] for n in ("iDNA-Prot", "DNA-Prot", "DNAbinder", "DNABIND", "DBD-Threader", "DBPPred")}
    obs["text.pdb186_best"] = [
        {"name": "PSSM-DT ACC above the six other predictors", "observed": yes(all(p186["ACC"] > r["ACC"] for r in others.values()))},
        {"name": "PSSM-DT MCC above the six other predictors", "observed": yes(all(p186["MCC"] > r["MCC"] for r in others.values()))},
        {"name": "PSSM-DT AUC above DBPPred, DNAbinder and DNABIND", "observed": yes(all(p186["AUC"] > r["AUC"] for r in others.values() if "AUC" in r))},
        {"name": "ACC gain over DBPPred (points)", "observed": round(p186["ACC"] - lou["DBPPred"]["ACC"], 3)},
        {"name": "MCC gain over DBPPred", "observed": round(p186["MCC"] - lou["DBPPred"]["MCC"], 3)},
        {"name": "AUC gain over DBPPred (points)", "observed": pct(p186["AUC"] - lou["DBPPred"]["AUC"])},
    ]
    # ---- Fig. 2
    top4 = {a + b for a, b, _ in w["top_pairs"][:4]}
    obs["fig2.a"] = [{"name": f"({p[0]},{p[1]}) among the four pairs with the largest weight", "observed": yes(p in top4)}
                     for p in ("RR", "RP", "PR", "AR")]
    pw = w["paper_top4_by_lg"]
    def peak(p):  # the paper counts only positive descriptor weights
        if max(pw[p]) <= 0:
            return "none (no positive weight)"
        return str(1 + max(range(5), key=lambda l: pw[p][l]))
    obs["fig2.b"] = [{"name": "lg with the largest (R,R) weight", "observed": peak("RR")},
                     {"name": "lg with the largest (A,R) weight", "observed": peak("AR")}]
    occ = akh["occurrences"]
    obs["fig2.c"] = [
        {"name": "occurrences of the four pairs (lg 1 to 5) on 1AKH chain A", "observed": str(len(occ))},
        {"name": "occurrences listed (pair and lg)", "observed": ", ".join(sorted(akh["descriptors"]))},
        {"name": "occurrences in the DNA-binding region (residues within 4.5 A of DNA, our definition)", "observed": str(akh["in_binding_region"])},
        {"name": "occurrences outside it", "observed": str(akh["outside_binding_region"])},
    ]

    items = []
    for it in notes["items"]:
        it = json.loads(json.dumps(it))
        iid = it["id"]
        if it.get("method") == "values":
            exp = {f["name"]: f for f in it["values"]["fields"]}
            got = {f["name"]: f["observed"] for f in obs[iid]}
            missing = set(exp) - set(got)
            assert not missing, (iid, missing)
            for f in it["values"]["fields"]:
                f["observed"] = got[f["name"]]
        elif it.get("method") == "pixels":
            fig, curve = it["pixels_from"]
            s = scores[fig][curve]
            it["pixels"] = {"tolerance_px": s["tolerance_px"],
                            "published_near_ours": s["published_near_ours"],
                            "ours_near_published": s["ours_near_published"],
                            "threshold": s["threshold"], "controls": s["controls"]}
            del it["pixels_from"]
        elif iid == "text.arithmetic":
            ar = j(run / "arithmetic.json")
            slips = [c["claim"] for c in ar["claims"] if not c["comes_back"]]
            it["check"] = {"passed": bool(ar["passed"]),
                           "detail": f"{ar['came_back']} of {ar['total']} claims recomputed from the paper's own tables come back; "
                                     f"the other {len(slips)} do not follow from the printed numbers (run/arithmetic.json)"}
        elif iid == "code.definition":
            it["check"] = {"passed": bool(defn["passed"]),
                           "detail": f"pssmdt.pssm_dt equals the transliterated BioSeq-Analysis2.0 loops on {defn['pssms']} PSSMs "
                                     f"(largest relative difference {defn['max_relative_difference']:.1e})"}
        elif iid == "package":
            it["check"] = {"passed": bool(pkg.get("passed")), "detail": pkg.get("detail", "")}
        items.append(it)

    res = {"schema": "paper2repro/results/v1", "paper": notes["paper"], "run": notes["run"],
           "session": {"ledger": "session/ledger.json"}, "items": items}
    Path(out).write_text(json.dumps(res, indent=1, ensure_ascii=False) + "\n")
    r = subprocess.run([sys.executable, str(HERE / "check_results.py"), out, "--write", "--skip-files"],
                       capture_output=True, text=True)
    print(r.stdout + r.stderr)
    sys.exit(r.returncode)


if __name__ == "__main__":
    main(*sys.argv[1:8])
