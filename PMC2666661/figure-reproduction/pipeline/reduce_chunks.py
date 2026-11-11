"""Collect the per-replicate JSONs of the simulation chunks (main.nf --full, or the Slurm arrays of
run_tasks.sbatch) into the committed per-replicate statistics.

  reduce_chunks.py CHUNK_ROOT [CHUNK_ROOT ...] OUTDIR

Writes OUTDIR/snp.json (H4M4, incremental LD models), OUTDIR/snp_independent.json (H4M4, each LD
model on its own data), OUTDIR/other/<model>.json and OUTDIR/hap.json (both frequency rules).
"""
import json
import os
import sys
from pathlib import Path

from summarize import reduce_hap_rep, reduce_snp_rep

roots, outdir = [Path(a) for a in sys.argv[1:-1]], Path(sys.argv[-1])
snp, indep, other, hap = {}, {}, {}, {}
for p in sorted(q for root in roots for q in root.rglob("*.json")):
    if p.name.endswith(".tmp") or not p.stem.isdigit():
        continue
    d = json.load(open(p))
    if "kinds" in d:
        r = reduce_snp_rep(d)
        if d.get("model", "H4M4") != "H4M4":
            other.setdefault(d["model"], {}).setdefault(d["ld_model"], {})[d["rep"]] = r
        elif d.get("ld_data", "independent") == "incremental":
            snp.setdefault(d["ld_model"], {})[d["rep"]] = r
        else:
            indep.setdefault(d["ld_model"], {})[d["rep"]] = r
    elif "HAP" in d:
        hap.setdefault(d["rule"], {}).setdefault(f"{d['r2']:.1f}", {})[d["rep"]] = reduce_hap_rep(d)

ORDER = ["n0", "n1", "n2", "n3", "n4", "r1", "r2", "r3", "r4", "r1n1", "r2n2", "r3n3", "r4n4"]


def lists(d):
    return {ld: [d[ld][k] for k in sorted(d[ld])] for ld in ORDER if ld in d}


os.makedirs(outdir / "other", exist_ok=True)
json.dump(lists(snp), open(outdir / "snp.json", "w"), separators=(",", ":"))
json.dump(lists(indep), open(outdir / "snp_independent.json", "w"), separators=(",", ":"))
for m, d in other.items():
    json.dump(lists(d), open(outdir / "other" / f"{m}.json", "w"), separators=(",", ":"))
json.dump({rule: {r2: [lv[r2][k] for k in sorted(lv[r2])] for r2 in sorted(lv)} for rule, lv in hap.items()},
          open(outdir / "hap.json", "w"), separators=(",", ":"))
print({"snp": {k: len(v) for k, v in snp.items()}, "independent": len(indep), "other": list(other),
       "hap": {r: {k: len(v) for k, v in lv.items()} for r, lv in hap.items()}}, file=sys.stderr)
