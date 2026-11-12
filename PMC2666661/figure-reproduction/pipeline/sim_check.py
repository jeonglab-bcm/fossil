"""Rerun a few replicates of the simulation studies from scratch and check that they give the
committed per-replicate statistics exactly (integers equal, means within 1e-9).

  sim_check.py COMMITTED_SIM_DIR OUT.json [--snp n0:0 r4:0 ...] [--hap 0.5:0 ...] [--other H8M4:r2:0 ...]

The committed statistics (output/sim) come from the full runs (main.nf --full, or the Slurm arrays
of run_tasks.sbatch); every replicate has its own seeds, so any replicate reruns alone.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hap_study  # noqa: E402
import snp_study  # noqa: E402
from summarize import reduce_hap_rep, reduce_snp_rep  # noqa: E402


def same(a, b, path=""):
    bad = []
    if isinstance(a, dict):
        for k in a:
            if k not in b:
                bad.append(f"{path}.{k} missing")
            else:
                bad += same(a[k], b[k], f"{path}.{k}")
    elif isinstance(a, float) or isinstance(b, float):
        if abs(a - b) > 1e-9:
            bad.append(f"{path}: {a} != {b}")
    elif a != b:
        bad.append(f"{path}: {a} != {b}")
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("committed")
    ap.add_argument("out")
    ap.add_argument("--snp", nargs="*", default=["n0:0", "r4:0"])
    ap.add_argument("--hap", nargs="*", default=["0.5:0"])
    ap.add_argument("--other", nargs="*", default=["H8M4:r2:0"])
    a = ap.parse_args()
    res = {"replicates": [], "passed": True}
    snp = json.load(open(os.path.join(a.committed, "snp.json")))
    for spec in a.snp:
        ld, rep = spec.split(":")
        fresh = reduce_snp_rep(snp_study.run_one(ld, int(rep), [0.5, 0.02], 5000, 35))
        com = next(r for r in snp[ld] if r["rep"] == int(rep))
        bad = same(com, fresh)
        res["replicates"].append({"study": "SNP H4M4", "ld_model": ld, "rep": int(rep), "differences": bad})
    hap = json.load(open(os.path.join(a.committed, "hap.json")))
    for spec in a.hap:
        r2, rep = spec.split(":")
        fresh = reduce_hap_rep(hap_study.run_one(float(r2), int(rep), "empirical_ratio", 5000, 1000, 100, 35))
        com = next(r for r in hap["empirical_ratio"][f"{float(r2):.1f}"] if r["rep"] == int(rep))
        bad = same(com, fresh)
        res["replicates"].append({"study": "haplotypes", "r2": r2, "rep": int(rep), "differences": bad})
    for spec in a.other:
        model, ld, rep = spec.split(":")
        other = json.load(open(os.path.join(a.committed, "other", f"{model}.json")))
        fresh = reduce_snp_rep(snp_study.run_one(ld, int(rep), [0.5], 5000, 35, model))
        com = next(r for r in other[ld] if r["rep"] == int(rep))
        bad = same(com, fresh)
        res["replicates"].append({"study": f"SNP {model}", "ld_model": ld, "rep": int(rep), "differences": bad})
    res["passed"] = all(not r["differences"] for r in res["replicates"])
    json.dump(res, open(a.out, "w"), indent=1)
    print(json.dumps(res, indent=1))
    sys.exit(0 if res["passed"] else 1)


if __name__ == "__main__":
    main()
