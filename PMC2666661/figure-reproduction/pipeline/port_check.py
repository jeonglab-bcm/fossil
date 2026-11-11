"""Check the port (rfld.forest) against Breiman and Cutler's Fortran Random Forests 5.1 (prog.f),
built with gfortran, on simulated data sets of the SNP study.

  port_check.py PROG_F OUT.json [--per-model 5] [--workdir DIR]

Forests are random and the two programs use different random number streams, so the check
compares distributions on the same data: for each data set, the importances (IM0) and tree counts
(T_v) of every variable from the Fortran program and from rfld (seed 1) are compared, and the same
comparison is made between rfld with seed 1 and rfld with seed 2. A port that grows the same
forests in distribution differs from the Fortran program by no more than it differs from itself.
RF0 is the unmodified prog.f; RF1 is prog.f with our reconstruction of the revised tree builder
(patch_prog.py --rf1), so its comparison checks our two implementations of the paper's rule
against each other, not against the authors' lost program.

Pass: for RF0 and RF1, the mean absolute Fortran-rfld difference in IM0 and in T_v is at most 1.15
times the rfld-rfld difference, and the mean signed Fortran-rfld difference in the risk SNPs' IM0
is within 3 standard errors of zero.
"""

import argparse
import json
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from rfld.forest import grow_forest, r2_matrix  # noqa: E402
from rfld.simulate import MODELS, snp_dataset  # noqa: E402

LD_MODELS = ["n0", "r1", "r4", "r4n4"]
R = 0.5


def build(prog, workdir, mdim, seed, rf1):
    name = f"rf{'1' if rf1 else '0'}_{mdim}_{seed}"
    src = os.path.join(workdir, name + ".f")
    exe = os.path.join(workdir, name)
    cmd = [sys.executable, os.path.join(HERE, "patch_prog.py"), prog, src, "--mdim", str(mdim), "--seed", str(seed)]
    if rf1:
        cmd.append("--rf1")
    subprocess.run(cmd, check=True)
    subprocess.run(["gfortran", "-O2", "-std=legacy", "-ffixed-line-length-none", "-fno-range-check",
                    "-o", exe, src], check=True, capture_output=True)
    return exe


def run_fortran(exe, X, y, ld, d):
    os.makedirs(d, exist_ok=True)
    np.savetxt(os.path.join(d, "data.train"), np.c_[X + 1, y + 1], fmt="%d")
    np.savetxt(os.path.join(d, "data.ld"), ld.astype(int), fmt="%d")
    out = os.path.join(d, "imp-all")
    if os.path.exists(out):
        os.remove(out)
    subprocess.run([exe], cwd=d, check=True, stdout=subprocess.DEVNULL)
    a = np.loadtxt(out)
    return a[:, 1], a[:, 2]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prog")
    ap.add_argument("out")
    ap.add_argument("--per-model", type=int, default=5)
    ap.add_argument("--workdir", default="port_check_work")
    a = ap.parse_args()
    a.workdir = os.path.abspath(a.workdir)
    os.makedirs(a.workdir, exist_ok=True)
    rows = []
    for li, ld_model in enumerate(LD_MODELS):
        for rep in range(a.per_model):
            rng = np.random.default_rng([2666661, 31, li, rep])
            X, y, kinds = snp_dataset(rng, MODELS["H4M4"], ld_model)
            r2 = r2_matrix(X)
            ld = r2 > R
            for rf1 in (False, True):
                fseed = 1000 + 10 * li + rep
                exe = build(a.prog, a.workdir, X.shape[1], fseed, rf1)
                f_im, f_tv = run_fortran(exe, X, y, ld, os.path.join(a.workdir, f"d_{ld_model}_{rep}_{int(rf1)}"))
                p1 = grow_forest(X, y, seed=1, revised_tree=rf1, ld_threshold=R, r2=r2)
                p2 = grow_forest(X, y, seed=2, revised_tree=rf1, ld_threshold=R, r2=r2)
                rows.append({
                    "ld_model": ld_model, "rep": rep, "forest": "RF1" if rf1 else "RF0", "fortran_seed": fseed,
                    "mad_im_fortran_port": float(np.abs(f_im - p1["im0"]).mean()),
                    "mad_im_port_port": float(np.abs(p1["im0"] - p2["im0"]).mean()),
                    "mad_tv_fortran_port": float(np.abs(f_tv - p1["trees"]).mean()),
                    "mad_tv_port_port": float(np.abs(p1["trees"] - p2["trees"]).mean()),
                    "corr_im_fortran_port": float(np.corrcoef(f_im, p1["im0"])[0, 1]),
                    "corr_im_port_port": float(np.corrcoef(p1["im0"], p2["im0"])[0, 1]),
                    "rsnp_im_fortran": float(f_im[:4].mean()), "rsnp_im_port": float(p1["im0"][:4].mean()),
                    "rsnp_im_port_seed2": float(p2["im0"][:4].mean()),
                })
                print(rows[-1], flush=True)
    summary = {"R": R, "datasets_per_ld_model": a.per_model, "ld_models": LD_MODELS, "forests": {}}
    ok = True
    for forest in ("RF0", "RF1"):
        rs = [r for r in rows if r["forest"] == forest]
        ratio_im = np.mean([r["mad_im_fortran_port"] for r in rs]) / np.mean([r["mad_im_port_port"] for r in rs])
        ratio_tv = np.mean([r["mad_tv_fortran_port"] for r in rs]) / np.mean([r["mad_tv_port_port"] for r in rs])
        d = np.array([r["rsnp_im_fortran"] - r["rsnp_im_port"] for r in rs])
        z = float(d.mean() / (d.std(ddof=1) / np.sqrt(len(d))))
        passed = bool(ratio_im <= 1.15 and ratio_tv <= 1.15 and abs(z) <= 3)
        ok &= passed
        summary["forests"][forest] = {
            "datasets": len(rs), "ratio_mad_im": float(ratio_im), "ratio_mad_tv": float(ratio_tv),
            "mean_corr_im_fortran_port": float(np.mean([r["corr_im_fortran_port"] for r in rs])),
            "mean_corr_im_port_port": float(np.mean([r["corr_im_port_port"] for r in rs])),
            "rsnp_im_mean_diff": float(d.mean()), "rsnp_im_diff_z": z, "passed": passed}
    summary["passed"] = ok
    summary["rows"] = rows
    json.dump(summary, open(a.out, "w"), indent=1)
    print(json.dumps({k: v for k, v in summary.items() if k != "rows"}, indent=1))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
