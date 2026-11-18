"""rommeta's pooling against R's metafor on simulated meta-analyses of the paper's design.

Usage: crosscheck.py COMMITTED_METAFOR_CSV OUT_JSON [--metafor] [--rscript Rscript]

Simulates 100 meta-analyses in each of three scenarios (Table 5, SD 70, SMD 0.8, 10/10, k 30, tau 0.5; Table 7,
14/6, k 5, tau 0.5; Table 6, skewed, 100/100, k 10, tau 0) with rommeta.draw_trials, pools each with
rommeta.pool, and compares the pooled estimate, SE, tau2, Q and I2 with metafor's (rma, method = "DL").
metafor's values are committed (output/metafor_replicates.csv), so CI needs no R. --metafor reruns
metafor_replicates.R and checks that it gives the committed file.
"""
import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

import rommeta
from rommeta import Scenario

HERE = Path(__file__).resolve().parent
SCENARIOS = {
    "table5": Scenario(sd=70, effect=0.8, n_exp=10, n_contr=10, k=30, tau=0.5),
    "table7": Scenario(sd=40, effect=0.5, n_exp=14, n_contr=6, k=5, tau=0.5),
    "table6": Scenario(sd=40, effect=0.2, n_exp=100, n_contr=100, k=10, distribution="skewed"),
}
REPS = 100
KEYS = ("estimate", "se", "tau2", "q", "i2")


def trials():
    rows = []
    for i, (name, sc) in enumerate(SCENARIOS.items()):
        me, se, mc, sdc = draw_rounded(sc, i)
        for r in range(REPS):
            for s in range(sc.k):
                rows.append({"scenario": name, "replicate": r + 1, "study": s + 1, "mean_exp": me[r, s], "sd_exp": se[r, s],
                             "n_exp": sc.n_exp, "mean_contr": mc[r, s], "sd_contr": sdc[r, s], "n_contr": sc.n_contr})
    return rows


def draw_rounded(sc, i):
    # written to CSV with repr (17 significant digits), so R reads the same doubles
    return rommeta.draw_trials(sc, REPS, seed=[20080521, 99, i])


def ours():
    out = {}
    for i, (name, sc) in enumerate(SCENARIOS.items()):
        arms = draw_rounded(sc, i)
        for m in rommeta.MEASURES:
            y, v = rommeta.effect_sizes(arms[0], arms[1], sc.n_exp, arms[2], arms[3], sc.n_contr, m)
            p = rommeta.pool(y, v)
            for r in range(REPS):
                out[(name, r + 1, m)] = {"k": int(p["k"][r]), "estimate": p["estimate"][r], "se": p["se"][r], "tau2": p["tau2"][r],
                                         "q": p["q"][r], "i2": 100 * p["i2"][r]}
    return out


def read(path):
    with open(path, newline="") as f:
        return {(r["scenario"], int(r["replicate"]), r["measure"]): {"k": int(r["k"]), **{k: float(r[k]) for k in KEYS}}
                for r in csv.DictReader(f)}


def main():
    args = sys.argv[1:]
    rerun = "--metafor" in args
    rscript = "Rscript"
    if "--rscript" in args:
        rscript = args[args.index("--rscript") + 1]
    committed, out = [a for a in args if not a.startswith("--") and a != rscript][:2]
    report = {}
    if rerun:
        with tempfile.TemporaryDirectory() as d:
            tcsv, mcsv = Path(d) / "trials.csv", Path(d) / "metafor.csv"
            rows = trials()
            with open(tcsv, "w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=list(rows[0]))
                w.writeheader()
                for r in rows:
                    w.writerow({k: (repr(float(v)) if isinstance(v, (float, np.floating)) else v) for k, v in r.items()})
            subprocess.run([rscript, str(HERE / "metafor_replicates.R"), str(tcsv), str(mcsv)], check=True)
            fresh = read(mcsv)
        old = read(committed)
        same = fresh.keys() == old.keys() and all(
            fresh[k]["k"] == old[k]["k"] and all(np.isclose(fresh[k][x], old[k][x], rtol=1e-9, atol=1e-12) for x in KEYS) for k in old)
        report["metafor_rerun"] = {"passed": bool(same), "detail": "a fresh metafor run gives the committed file" if same else "metafor rerun DIFFERS from the committed file"}
    ref, mine = read(committed), ours()
    worst, kdiff = 0.0, 0
    for key, e in ref.items():
        o = mine[key]
        kdiff += o["k"] != e["k"]
        for x in KEYS:
            worst = max(worst, abs(o[x] - e[x]) / max(abs(e[x]), 1e-8))
    left_out = sum(SCENARIOS[s].k - ref[(s, r, m)]["k"] for s, r, m in ref if m == "RoM")
    ok = kdiff == 0 and worst < 1e-8 and len(ref) == len(mine)
    report["pooling"] = {"passed": ok, "fits": len(ref), "max_relative_difference": float(f"{worst:.3g}"),
                         "rom_studies_left_out": left_out,
                         "detail": f"rommeta.pool against metafor 4.4.0 rma (DL) on {len(ref)} simulated meta-analyses "
                                   f"({REPS} each of {len(SCENARIOS)} scenarios x MD, SMD, RoM): pooled estimate, SE, tau2, Q and I2 "
                                   f"agree to a relative {worst:.1e}; both leave out the same {left_out} RoM studies with a non-positive mean"}
    report["passed"] = all(v["passed"] for v in report.values() if isinstance(v, dict))
    Path(out).write_text(json.dumps(report, indent=1) + "\n")
    print(report["pooling"]["detail"], file=sys.stderr)
    sys.exit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
