"""Rerun the first replicates of every cell from scratch and check them against the committed records.

Usage: sim_check.py RECORDS_DIR OUT.json [--reps N] [--jobs J]

Each replicate has its own random stream, so replicate r of a cell is the same data set and the same fit whether
it runs alone or in the full study. For the first N replicates (default 3) of every cell of the main grid, the
prevalence study and the robustness study, the fresh fit must have the committed status and convergence, and
every estimate and standard error must be within 1e-5 (absolute plus relative) of the committed one (the
records keep 8 significant digits; a fit that creeps to a variance of zero can stop a few iterations apart on
another processor). Exit 1 otherwise.
"""
import json
import math
import multiprocessing as mp
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from simulate import COLUMNS, _job  # noqa: E402
from summarize import read  # noqa: E402

from mlagq import simulation as sim  # noqa: E402

NUMS = [c for c in COLUMNS if c[0] in "gv" or c.endswith("_se") or c in ("prevalence", "z_mean", "z_sd", "x_mean", "x_sd")]
TOL = 1e-5


def main():
    rec_dir, out = Path(sys.argv[1]), sys.argv[2]
    reps = int(sys.argv[sys.argv.index("--reps") + 1]) if "--reps" in sys.argv else 3
    jobs = int(sys.argv[sys.argv.index("--jobs") + 1]) if "--jobs" in sys.argv else 1
    kw = {"cov": True, "qpick": "second", "absxconv": 1e-8}
    report = {"replicates_per_cell": reps, "studies": {}}
    ok_all = True
    for study, f in (("main", "main.csv.gz"), ("prevalence", "prevalence.csv.gz"), ("robustness", "robustness.csv.gz")):
        committed = {(r["cell"], int(r["rep"])): r for r in read(rec_dir / f) if r["rep"] < reps}
        tasks = [(study, c, r, 19554471, kw) for c in sim.cells(study) for r in range(reps)]
        if jobs > 1:
            with mp.Pool(jobs) as pool:
                fresh = pool.map(_job, tasks, chunksize=1)
        else:
            fresh = [_job(t) for t in tasks]
        bad, worst = [], 0.0
        for row in fresh:
            d = dict(zip(COLUMNS, row))
            c = committed.get((d["cell"], int(d["rep"])))
            if c is None:
                bad.append(f"{d['cell']} rep {d['rep']}: not in the committed records")
                continue
            if d["status"] != c["status"] or (d["converged"] == "1") != c["converged"]:
                bad.append(f"{d['cell']} rep {d['rep']}: status {d['status']} against {c['status']}")
                continue
            for k in NUMS:
                a, b = float(d[k]), c[k]
                if math.isnan(a) and math.isnan(b):
                    continue
                gap = abs(a - b) / (1 + abs(b)) if not (math.isnan(a) or math.isnan(b)) else math.inf
                worst = max(worst, gap)
                if gap > TOL:
                    bad.append(f"{d['cell']} rep {d['rep']}: {k} {a} against {b}")
        report["studies"][study] = {"replicates": len(fresh), "mismatches": bad, "largest_difference": worst}
        ok_all &= not bad
    report["passed"] = ok_all
    n = sum(v["replicates"] for v in report["studies"].values())
    report["detail"] = (f"{n} replicates ({reps} of every cell of Tables 1-5) rerun from scratch: "
                        + (f"every one has the committed status and estimates within {TOL:g}" if ok_all else
                           f"{sum(len(v['mismatches']) for v in report['studies'].values())} differ from the committed records"))
    Path(out).write_text(json.dumps(report, indent=1) + "\n")
    print(report["detail"], file=sys.stderr)
    sys.exit(0 if ok_all else 1)


if __name__ == "__main__":
    main()
