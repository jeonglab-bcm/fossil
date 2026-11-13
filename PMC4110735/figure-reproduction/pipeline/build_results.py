"""Merge results_notes.json (labels, sources, assumptions, causes: written by hand) with the numbers of a
run into results.json; check_results.py then computes every verdict and the summary.

Usage: build_results.py RUN_DIR NOTES.json PAPER_VALUES.json OUT.json [--inputs INPUTS.json]
RUN_DIR holds the pipeline's outputs: dream.json, datasets.json, fig4.json, fig5.json, profiles.json,
enrich.json, claims.json, table3.json, normalisation.json, port_check.json, package.json and figures/.
"""
import copy, datetime, json, os, platform, sys

M = ["gecon", "aracne", "clr", "mrnet"]
NAMES = {"gecon": "GeCON", "aracne": "ARACNE", "clr": "CLR", "mrnet": "MRNET"}
KEY = {"aupr": "aupr", "auroc": "auroc", "f": "f_max"}
DS = [f"D{i}" for i in range(1, 14)]


def load(run, name):
    return json.load(open(os.path.join(run, name)))


def yn(b):
    return "yes" if b else "no"


def main():
    run, notes_p, paper_p, out = sys.argv[1:5]
    notes = json.load(open(notes_p))
    pv = json.load(open(paper_p))
    t2 = pv["table2"]
    dream, prof, fig4, fig5 = load(run, "dream.json"), load(run, "profiles.json"), load(run, "fig4.json"), load(run, "fig5.json")
    enr, claims, t3, norm = load(run, "enrich.json"), load(run, "claims.json"), load(run, "table3.json"), load(run, "normalisation.json")
    port, pkg, meta = load(run, "port_check.json"), load(run, "package.json"), load(run, "datasets.json")
    D = dream["datasets"]
    items = []
    for iid, n in notes["items"].items():
        it = {"id": iid}
        for k in ("label", "kind", "source", "method", "assumptions", "outputs"):
            if k in n:
                it[k] = copy.deepcopy(n[k])
        if "cause" in n:
            it["cause"] = copy.deepcopy(n["cause"])
        if "cause_ref" in n:
            it["cause"] = copy.deepcopy(notes["causes"][n["cause_ref"]])
        fields = None
        if iid in ("fig2", "fig3", "fig7"):
            p = prof[iid]
            it["pixels"] = {"tolerance_px": p["tolerance_px"], "dpi": "1200 px wide (publisher original)",
                            "published_near_ours": p["combined"]["published_near_ours"], "ours_near_published": p["combined"]["ours_near_published"],
                            "threshold": n["threshold"], "controls": p["controls"], "axes": p["mapping"]}
            it["outputs"] = [f"figure-reproduction/output/figures/{iid}_ours.png", f"figure-reproduction/output/figures/{iid}_overlay.png"]
        elif iid.startswith("fig4."):
            key = iid.split(".")[1]
            fields = [{"name": f["name"], "expected": f["expected"], "observed": f["observed"]} for f in fig4[key]["fields"] if f["observed"] is not None]
            it["outputs"] = ["figure-reproduction/output/figures/fig4_ours.png", "figure-reproduction/output/figures/fig4_overlay.png",
                             "figure-reproduction/output/figures/fig4_run.png"]
            it["note"] = "D11's GeCON bar is hidden by the legend and has no field."
        elif iid == "fig5":
            fields = [{"name": f"faster at {s} genes", "expected": "yes", "observed": yn(v)} for s, v in fig5["faster"].items()]
            it["outputs"] = ["figure-reproduction/output/figures/fig5_ours.png", "figure-reproduction/output/figures/fig5_overlay.png"]
            it["measured"] = {"ours_seconds": fig5["ours"], "published_read": fig5["published"], "scale_to_paper": fig5["scale"]}
        elif iid == "fig7.values":
            fv = prof["fig7_values"]
            fields = [{"name": "angle, edge 1", "expected": "138", "observed": f"{fv['angles'][0]:.4f}"},
                      {"name": "angle, edge 2", "expected": "52", "observed": f"{fv['angles'][1]:.4f}"},
                      {"name": "regulation, edge 1", "expected": "-1", "observed": str(fv["regulation"][0])},
                      {"name": "regulation, edge 2", "expected": "1", "observed": str(fv["regulation"][1])}]
        elif iid == "table1":
            fields = [{"name": f"{d} {net} size", "expected": str(size), "observed": str(meta[d]["genes"])} for d, ch, net, size in pv["table1"]]
        elif iid.startswith("table2."):
            key = iid.split(".")[1]
            fields = [{"name": f"{d} {NAMES[m]}", "expected": t2[key][d][m], "observed": round(D[d][m][KEY[key]], 4)} for d in DS for m in M]
        elif iid == "table3":
            fields = []
            for name, genes, samples in pv["table3"]:
                ours = t3.get(name) or t3.get(name.replace(" (Subset)", ""))
                if not ours:
                    continue
                if "genes" in ours:
                    fields.append({"name": f"{name} genes", "expected": genes, "observed": str(ours["genes"])})
                fields.append({"name": f"{name} samples", "expected": samples, "observed": str(ours["samples"])})
        elif iid in ("table4", "table5"):
            fields = [{"name": f"{r['dataset']} module {r['module']}: {r['term']}", "expected": "yes", "observed": r["found"],
                       **({"our_q": r["our_q"]} if r.get("our_q") is not None else {})}
                      for r in enr[iid] if r["found"] is not None]
            skipped = sorted({r["dataset"] for r in enr[iid] if r["found"] is None})
            it["cause"] = {"category": "data_unavailable" if iid == "table4" else "data_differs",
                           "summary": (f"Terms not found in our modules: GeneMANIA's and FuncAssociate's 2014 annotations and the authors' modules are gone, and our module cut and filters are guesses. "
                                       f"Rows of {', '.join(skipped)} are left out: " +
                                       ("the sporulation file failed TLS verification from our runner and no archive was reachable, and the 517 x 13 Arabidopsis matrix was not located." if iid == "table4"
                                        else "GEO's GDS825 has 4 samples, not the paper's 8, and the sporulation file could not be fetched.")),
                           "evidence": ["figure-reproduction/output/enrich.json"],
                           "hypotheses": [
                               {"hypothesis": "theta: modules cut at another threshold", "test": "theta 0.7, 0.8 and 0.9 (enrich.json theta_sensitivity_found)", "result": "rejected"},
                               {"hypothesis": "GeCON on unstandardised values", "test": "On log values every pair is connected and there is one module (normalisation.json)", "result": "rejected"}],
                           "status": "open"}
        elif iid == "text.arithmetic":
            a = claims["arithmetic"]

            def close(f, unit):
                return abs(float(f["expected"]) - float(f["observed"])) <= unit + 1e-9

            def unit(s):
                return 10 ** -(len(s.split(".")[1]) if "." in s else 0)

            av = a["average"]
            av_exact = sum(f["expected"] == f["observed"] for f in av)
            av_close = sum(close(f, unit(f["expected"])) for f in av)
            im = a["improvement_from_rows"]
            im_exact = sum(f["expected"] == f["observed"] for f in im)
            im_close = sum(close(f, unit(f["expected"])) for f in im)
            not_best = sum(len(v) for v in a["gecon_best"].values())
            passed = av_close == len(av) and im_close == len(im)
            it["check"] = {"passed": passed, "detail": (
                f"Average row: {av_exact} of {len(av)} exact, {av_close} within one unit in the last digit; improvements from the row means: "
                f"{im_exact} of {len(im)} exact, {im_close} within one unit (from the printed averages {sum(f['expected'] == f['observed'] for f in a['improvement_from_printed_averages'])} of 9). "
                f"The table itself has GeCON best in {39 - not_best} of 39 dataset-score cells (not: " +
                ", ".join(f"{d} {k.upper()}" for k, v in a["gecon_best"].items() for d in v) +
                f"), against \"in all cases\". \"More than 200 times better\" in AUPR is {a['aupr_times']['aracne']} times (269.72%).")}
            it["arithmetic"] = a
        elif iid == "text.outperforms":
            o = claims["ours"]["gecon_best"]
            fields = [{"name": f"GeCON best on every dataset, {k.upper()}", "expected": "yes", "observed": yn(len(o[k]) == 13)} for k in ("aupr", "auroc", "f")]
            it["ours"] = {f"datasets where GeCON is best, {k}": o[k] for k in o}
        elif iid == "text.improvement":
            imp = claims["ours"]["improvement"]
            fields = [{"name": f"{k.upper()} over {NAMES[m]} (%)", "expected": t2["improvement_percent"][k][m], "observed": imp[k][m]} for k in ("aupr", "auroc", "f") for m in M[1:]]
        elif iid == "text.d6":
            d6 = claims["ours"]["d6"]
            fields = [{"name": "AUPR", "expected": ".84", "observed": d6["aupr"]}, {"name": "AUROC", "expected": ".78", "observed": d6["auroc"]},
                      {"name": "F0.5", "expected": ".86", "observed": d6["f"]}]
        elif iid == "text.fig2_negative":
            fields = [{"name": "GeCON gives the pair sign -1 (theta 0.5, tau 20)", "expected": "yes", "observed": yn(claims["ours"]["fig2_negative"])}]
        elif iid == "text.fig3_mixed":
            fields = [{"name": "YBL002W and YBL003C positive", "expected": "yes", "observed": yn(claims["ours"]["fig3_002_003_positive"])},
                      {"name": "YBL006W negative to both", "expected": "yes", "observed": yn(claims["ours"]["fig3_006_inverted"])}]
        elif iid == "text.faster":
            fields = [{"name": "GeCON faster than ARACNE at every size", "expected": "yes", "observed": yn(all(fig5["faster"].values()))}]
            it["ours"] = {"aracne_over_gecon_at_3000": claims["ours"]["ratio_3000"]}
        elif iid == "text.normalisation":
            fields = [{"name": "same network on log and normalised Yeast KY (theta 0.6)", "expected": "yes",
                       "observed": yn(norm["log"]["edges_theta_0.6"] == norm["normalised"]["edges_theta_0.6"])}]
        elif iid == "text.modules":
            me = claims["ours"]["modules_enriched"]
            mt = claims["ours"]["modules_total"]
            fields = [{"name": f"{d}: a module with a GO term at Q < 0.05", "expected": "yes", "observed": yn(me[d] > 0)} for d in me]
            it["ours"] = {d: f"{me[d]} of {mt[d]} modules enriched" for d in me}
        elif iid == "port.gnw":
            it["check"] = {"passed": port["passed"], "detail": (
                f"All 10 DREAM4 networks: gold standards from the network files equal the released ones; the port's wild-type "
                f"steady state tracks the released wild type with log correlation {port['min_corr']:.2f} to {port['max_corr']:.2f}")}
        elif iid == "package":
            it["check"] = {"passed": pkg["passed"], "detail": pkg.get("detail", "")}
        if fields is not None:
            v = {"fields": fields}
            if "tolerance" in n:
                v["tolerance"] = n["tolerance"]
            exc = n.get("exceptions", []) + it.pop("values_exceptions", [])
            if exc:
                v["exceptions"] = exc
            it["values"] = v
        items.append(it)
    res = {"schema": "paper2repro/results/v1", "paper": notes["paper"],
           "run": {**notes["run"],
                   "inputs": json.load(open(sys.argv[sys.argv.index("--inputs") + 1])) if "--inputs" in sys.argv else []},
           "session": notes["session"], "skill": notes["skill"], "items": items}
    json.dump(res, open(out, "w"), indent=1)


if __name__ == "__main__":
    main()
