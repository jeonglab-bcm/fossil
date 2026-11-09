"""Merge the run's outputs and the hand-written notes into results.json, then let
check_results.py compute every verdict.

Usage: make_results.py RUN_DIR NOTES.json INPUTS.json OUT.json
RUN_DIR holds network_counts.json, yeast.json, human.json, validate.json, arithmetic.json,
figures.json, port_check.json, package.json and fig2_label_hypotheses.json.
"""
import json
import subprocess
import sys
from datetime import date
from pathlib import Path
from statistics import median

HERE = Path(__file__).resolve().parent
PRINTED = {"printed": True}


def load(d, name):
    p = Path(d) / name
    return json.load(open(p)) if p.exists() else None


def field(name, expected, observed):
    return {"name": name, "expected": expected, "observed": observed}


def yesno(b):
    return "yes" if b else "no"


def pct(x):
    return round(100 * x, 1)


def main(run, notes_path, inputs_path, out):
    N = json.load(open(notes_path))
    nc = load(run, "network_counts.json")
    Y = load(run, "yeast.json")
    H = load(run, "human.json")
    V = load(run, "validate.json")
    A = load(run, "arithmetic.json")
    F = load(run, "figures.json")
    PC = load(run, "port_check.json")
    PK = load(run, "package.json")
    items = []

    def add(iid, **kw):
        n = N["items"][iid]
        it = {"id": iid, "label": n["label"], "kind": kw.pop("kind"), "source": n["source"]}
        it.update(kw)
        if n.get("assumptions"):
            it["assumptions"] = [N["assumptions"][a] for a in n["assumptions"]]
        if n.get("cause"):
            it["cause"] = n["cause"]
        items.append(it)

    def pixels(iid):
        f = F[iid]
        stem = "fig1" if iid.startswith("fig1") else iid
        add(iid, kind="figure", method="pixels",
            pixels={"tolerance_px": f["tolerance_px"], "dpi": 300,
                    "published_near_ours": round(f["published_near_ours"], 4),
                    "ours_near_published": round(f["ours_near_published"], 4),
                    "threshold": f["threshold"],
                    "controls": [{"name": c["name"], "kind": c["kind"], "score": round(c["score"], 4)}
                                 for c in f["controls"]]},
            outputs=[f"figure-reproduction/output/{stem}_ours.png", f"figure-reproduction/output/{stem}_overlay.png"])

    # ---- figures
    pixels("fig1.a")
    pixels("fig1.b")
    pixels("fig2")
    add("fig2.labels", kind="figure", method="values",
        values={"tolerance": PRINTED, "fields": [
            x for lab in Y["fig2_labels"] for x in (
                field(f"TP at epsilon {lab['eps']}", str(lab["paper_tp"]), lab["tp"]),
                field(f"FP at epsilon {lab['eps']}", str(lab["paper_fp"]), lab["fp"]))]})
    pixels("fig3")
    pixels("fig4")
    pixels("fig5")
    for s in ("figS1", "figS2", "figS3"):
        pixels(s)

    # ---- tables
    add("table1", kind="table", method="none")
    t1 = H["table_s1"]
    m = H["main"]
    add("tableS1", kind="table", method="values", values={"tolerance": PRINTED, "fields": [
        field("new pairs with CS >= 0.975", "251", m["high_new"]),
        field("published pairs among ours", "251", t1["overlap"])]})
    o = V["ours"]
    add("tableS2", kind="table", method="values", values={"tolerance": PRINTED, "fields": [
        field("predictions in HPRD", "12", o["hprd"]),
        field("predictions in BioGRID 2.0.50", "5", o["biogrid_2.0.50"]),
        field("of those, also in HPRD", "4", o["biogrid_2.0.50_and_hprd"]),
        field("validated in either", "13", o["validated_any"])]})
    add("tableS3", kind="table", method="values", values={"tolerance": PRINTED, "fields": [
        field("pairs with both proteins annotated (BP or CC)", "159", o["go_BP|CC"]["annotated"]),
        field("pairs sharing a BP or CC term", "105", o["go_BP|CC"]["sharing"])]})
    add("tableS4", kind="table", method="values", values={"tolerance": PRINTED, "fields": [
        field("pairs with both proteins annotated (BP)", "129", o["go_BP"]["annotated"]),
        field("pairs sharing a BP term", "55", o["go_BP"]["sharing"])]})
    add("tableS5", kind="table", method="values", values={"tolerance": PRINTED, "fields": [
        field("pairs with both proteins in a KEGG pathway", "26", o["kegg"]["both_in_a_pathway"]),
        field("pairs in the same pathway", "12", o["kegg"]["same_pathway"])]})
    fpv = V["false_positives"]
    add("tableS6", kind="table", method="values", values={"tolerance": PRINTED, "fields": [
        field("predicted false positives", "1455", fpv["table_s6_ours"])]})
    add("tableS7", kind="table", method="none")

    # ---- claims in the text
    add("text.networks", kind="value", method="values", values={"tolerance": PRINTED, "fields": [
        field("HumanBG proteins", "7930", nc["humanbg_full"]["proteins"]),
        field("HumanBG interactions", "23543", nc["humanbg_full"]["interactions"]),
        field("HumanBG largest component, proteins", "7513", nc["humanbg"]["proteins"]),
        field("HumanBG largest component, interactions", "23372", nc["humanbg"]["interactions"]),
        field("Collins high-confidence interactions", "9074", nc["collins_high_full"]["interactions"]),
        field("Collins high-confidence proteins", "1622", nc["collins_high_full"]["proteins"]),
        field("Yhigh proteins", "1004", nc["yhigh"]["proteins"]),
        field("Yhigh interactions", "8323", nc["yhigh"]["interactions"])]})
    d7 = Y["dims"]["7"]
    add("text.yeast_performance", kind="value", method="values", values={"tolerance": PRINTED, "fields": [
        field("AUC, dimension 7", "0.9", round(d7["auc"], 3)),
        field("sensitivity at 85% specificity, dimension 7 (%)", "90", pct(d7["sens_at_spec_0.85"])),
        field("precision at recall 0.35, dimension 7", "0.15", round(d7["precision_at_recall_0.35"], 3))]})
    aucs = {k: v["auc"] for k, v in Y["dims"].items()}
    hi = [aucs[k] for k in ("4", "5", "6", "7")]
    add("text.dimensions", kind="value", method="values", values={"tolerance": PRINTED, "fields": [
        field("dimension 2 has the lowest AUC", "yes", yesno(min(aucs, key=aucs.get) == "2")),
        field("AUCs of dimensions 4 to 7 within 0.01 of each other", "yes", yesno(max(hi) - min(hi) <= 0.01))]})
    conv = [c for c in Y["fig4"]["converged"] if all(isinstance(h, int) for h in c["new_per_iteration"])]
    its = median(c["iterations"] for c in conv)
    one = {round(p["eps"], 2): p for p in Y["fig4"]["one_iteration"]}
    worse = sum(c["sens"] <= one[round(c["eps"], 2)]["sens"] + 1e-9 or c["fpr"] >= one[round(c["eps"], 2)]["fpr"]
                for c in conv) == len(conv)
    add("text.iteration", kind="value", method="values", values={"tolerance": PRINTED, "fields": [
        field("iterations to converge (median over epsilon)", "10", round(its)),
        field("iterating is no better than one iteration at any epsilon", "yes", yesno(worse))]})
    add("text.false_positives", kind="value", method="values", values={"tolerance": PRINTED, "fields": [
        field("edges further apart than 0.4", "2838", H["edges_beyond_delta"]),
        field("share of all edges (%)", "12", round(100 * H["edges_beyond_delta_fraction"])),
        field("edges sharing a CC term (%)", "72", round(100 * fpv["edges_sharing_cc_fraction"])),
        field("candidates sharing a CC term (%)", "66", round(100 * fpv["candidates_sharing_cc_fraction"]))]})
    add("text.high_confidence", kind="value", method="values", values={"tolerance": PRINTED, "fields": [
        field("pairs with CS >= 0.975", "1685", m["high"]),
        field("of them edges", "1434", m["high_edges"]),
        field("of them new", "251", m["high_new"])]})
    bg = V["background"]
    add("text.go_background", kind="value", method="values", values={"tolerance": PRINTED, "fields": [
        field("HumanBG proteins with a BP or CC term", "6278", bg["BP|CC"]["annotated_proteins"]),
        field("pairs of them sharing a term (K)", "7400424", bg["BP|CC"]["K"]),
        field("HumanBG proteins with a BP term", "5864", bg["BP"]["annotated_proteins"]),
        field("pairs of them sharing a BP term (K)", "1354495", bg["BP"]["K"])]})
    p = V["published_table_s1"]
    add("validation.published_pairs", kind="value", method="values", values={"tolerance": PRINTED, "fields": [
        field("in BioGRID 2.0.50", "5", p["biogrid_2.0.50"]),
        field("in HPRD", "12", p["hprd"]),
        field("annotated (BP or CC)", "159", p["go_BP|CC"]["annotated"]),
        field("sharing a BP or CC term", "105", p["go_BP|CC"]["sharing"]),
        field("annotated (BP)", "129", p["go_BP"]["annotated"]),
        field("sharing a BP term", "55", p["go_BP"]["sharing"]),
        field("both proteins in a KEGG pathway", "26", p["kegg"]["both_in_a_pathway"]),
        field("in the same KEGG pathway", "12", p["kegg"]["same_pathway"])]})
    exc = N["arithmetic_exceptions"]
    add("text.arithmetic", kind="value", method="values", values={
        "tolerance": PRINTED,
        "fields": [field(r["claim"], r["printed"], r["recomputed"]) for r in A["checks"]],
        "exceptions": [{"field": k, "category": "paper_error", "evidence": v} for k, v in exc.items()]})
    add("text.citexplorer", kind="value", method="none")

    # ---- code checks
    if PC:
        d = PC["dims"]
        worst = max(v["max_abs_distance_difference"] for v in d.values())
        tp = max(v["max_relative_tp_difference"] for v in d.values())
        add("port", kind="code_check", method="check", check={"passed": PC["passed"], "detail":
            f"embed_novi.m under GNU Octave against geodenoise.embed on Yhigh, dimensions 2-7: distances "
            f"differ by at most {worst:.3f} (the authors' iteration stops at a change of 1e-3), TP counts at "
            f"the epsilon grid by at most {100 * tp:.1f}% (output/port_check.json)"})
    if PK:
        add("package", kind="code_check", method="check",
            check={"passed": PK["passed"], "detail": PK["detail"]},
            outputs=["package/tutorial/TUTORIAL.md"])

    inputs = json.load(open(inputs_path))
    res = {"schema": "paper2repro/results/v1", "paper": N["paper"],
           "run": {"date": str(date.today()), "pipeline": "PMC2711306/figure-reproduction/main.nf",
                   "command": "nextflow run PMC2711306/figure-reproduction/main.nf --outdir results",
                   "inputs": inputs["inputs"], "environment": inputs["environment"]},
           "session": {"ledger": "session/ledger.json"}, "items": items}
    json.dump(res, open(out, "w"), indent=1, ensure_ascii=False)
    r = subprocess.run([sys.executable, str(HERE / "check_results.py"), out, "--write", "--skip-files"],
                       capture_output=True, text=True)
    print(r.stdout + r.stderr)
    return r.returncode


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:5]))
