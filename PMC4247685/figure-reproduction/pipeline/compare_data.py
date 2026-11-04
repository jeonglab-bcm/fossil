"""Bundle what the expected-and-observed page draws into one script, compare-data.js.

Expected is the paper: Fig. 2's boxes read from its pixels, the curves of Figs 3 to 5 traced from
the published figures. Observed is ours: the rerun's scores, our
densities, and the patients behind our survival curves. The page computes quartiles, Kaplan-Meier
curves, medians and gaps from these in the browser.

Usage: python3 compare_data.py <data dir> <paper_traced.json> <out compare-data.js>
"""
import csv
import json
import sys


def read_csv(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def num(v, nd=4):
    return None if v in ("", "NA") else round(float(v), nd)


def main():
    data_dir, traced_path, out_path = sys.argv[1:4]
    with open(traced_path) as f:
        traced = json.load(f)
    with open(f"{data_dir}/fig2_published_boxes.json") as f:
        boxes = json.load(f)["boxes"]

    methods = ["GABi.block", "GABi.cor", "GABi.highvar", "ISA", "CC", "Plaid", "Bimax"]
    structures = ["block", "cor", "highvar"]
    scores = {s: {m: [] for m in methods} for s in structures}
    for r in read_csv(f"{data_dir}/fig2_scores.csv"):
        v = num(r["F.score"])
        if v is not None:
            scores[r["structure"]][r["method"]].append(v)
    fig2 = {
        "structures": structures,
        "methods": methods,
        "expected": {s: {m: {k: boxes[s][m][k] for k in ("lower", "q1", "median", "q3", "upper")}
                         for m in methods} for s in structures},
        "observed": scores,
    }

    dens = read_csv(f"{data_dir}/fig3_density.csv")
    fig3 = {
        "expected": {"bicluster": traced["paper"]["fig3"]["solid"], "control": traced["paper"]["fig3"]["dashed"]},
        "observed": {g: [[num(r["x"]), num(r["y"])] for r in dens if r["set"] == g] for g in ("bicluster", "control")},
    }

    g4 = read_csv(f"{data_dir}/fig4_groups.csv")
    fig4 = {
        "expected": {"bicluster": traced["paper"]["fig4"]["solid"], "control": traced["paper"]["fig4"]["dashed"]},
        "observed": {g: [[num(r["PFI.months"], 3), int(r["PFI"])] for r in g4 if r["group"] == g and r["PFI.months"] not in ("", "NA")]
                     for g in ("bicluster", "control")},
    }

    c5 = read_csv(f"{data_dir}/fig5_clinical.csv")
    fig5 = {
        "expected": {"Group1": traced["paper"]["fig5"]["solid"], "Group2": traced["paper"]["fig5"]["dashed"]},
        "observed": {g: [[num(r["PFS"], 1), int(r["progression"])] for r in c5 if r["group"] == g and r["PFS"] not in ("", "NA")]
                     for g in ("Group1", "Group2")},
    }

    bundle = {"fig2": fig2, "fig3": fig3, "fig4": fig4, "fig5": fig5,
              "tracer_check": traced["check"]}
    with open(out_path, "w") as f:
        f.write("// Written by PMC4247685/figure-reproduction/pipeline/compare_data.py. Do not edit.\n")
        f.write("window.FOSSIL_COMPARE = ")
        json.dump(bundle, f, separators=(",", ":"))
        f.write(";\n")


if __name__ == "__main__":
    main()
