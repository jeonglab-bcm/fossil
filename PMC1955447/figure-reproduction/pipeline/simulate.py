"""Run replicates of the simulation study with the package mlagq and write one record per replicate.

Usage: simulate.py STUDY OUT.csv.gz [--reps A:B] [--base SEED] [--jobs N] [--nocov] [--qpick first]
                   [--maxfunc N] [--qpoints Q] [--absxconv X|none] [--cells ID,ID,...]

STUDY is main (Tables 1-3), prevalence (Table 4) or robustness (Table 5). Each replicate is drawn from its own
stream (base seed, study, cell, replicate), so any subset of replicates gives the same records as the full run.
The output is a gzipped CSV (written with mtime 0, so the same records give the same bytes).
"""
import argparse
import csv
import gzip
import io
import math
import multiprocessing as mp
import sys
import time

from mlagq import simulation as sim

COLUMNS = ["study", "cell", "rep", "status", "converged", "iterations", "qpoints", "hessian_pd", "loglik",
           "prevalence", "z_mean", "z_sd", "x_mean", "x_sd",
           "g00", "g01", "g10", "g11", "var0", "cov01", "var1",
           "g00_se", "g01_se", "g10_se", "g11_se", "var0_se", "cov01_se", "var1_se"]


def fmt(v):
    if isinstance(v, bool):
        return "1" if v else "0"
    if isinstance(v, float):
        return "nan" if math.isnan(v) else repr(float(f"{v:.8g}"))
    return str(v)


def _job(args):
    study, cell, rep, base, kw = args
    rec, _ = sim.run_replicate(study, cell, rep, base, **kw)
    rec.update(study=study, cell=cell["id"], rep=rep)
    return [fmt(rec.get(c, float("nan"))) for c in COLUMNS]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("study", choices=["main", "prevalence", "robustness"])
    ap.add_argument("out")
    ap.add_argument("--reps", default=None, help="A:B, replicates A to B-1 (default 0:1000, 0:100 for robustness)")
    ap.add_argument("--base", type=int, default=19554471)
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--nocov", action="store_true", help="hypothesis: sigma01 not estimated")
    ap.add_argument("--qpick", default="second", choices=["first", "second"])
    ap.add_argument("--maxfunc", type=int, default=None)
    ap.add_argument("--qpoints", type=int, default=None, help="hypothesis: a fixed number of quadrature points")
    ap.add_argument("--absxconv", default="1e-8")
    ap.add_argument("--cells", default=None)
    a = ap.parse_args()
    reps = a.reps or ("0:100" if a.study == "robustness" else "0:1000")
    r0, r1 = map(int, reps.split(":"))
    kw = {"cov": not a.nocov, "qpick": a.qpick,
          "absxconv": None if a.absxconv == "none" else float(a.absxconv)}
    if a.maxfunc:
        kw["maxfunc"] = a.maxfunc
    if a.qpoints:
        kw["qpoints"] = a.qpoints
    cells = sim.cells(a.study)
    if a.cells:
        keep = set(a.cells.split(","))
        cells = [c for c in cells if c["id"] in keep]
    tasks = [(a.study, c, r, a.base, kw) for c in cells for r in range(r0, r1)]
    t0 = time.time()
    if a.jobs > 1:
        with mp.Pool(a.jobs) as pool:
            rows = pool.map(_job, tasks, chunksize=2)
    else:
        rows = [_job(t) for t in tasks]
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(COLUMNS)
    w.writerows(rows)
    with open(a.out, "wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=0, filename="") as gz:
        gz.write(buf.getvalue().encode())
    print(f"{a.study}: {len(rows)} replicates in {time.time() - t0:.0f} s -> {a.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
