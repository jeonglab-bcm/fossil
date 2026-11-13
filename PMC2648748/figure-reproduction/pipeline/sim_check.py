"""Rerun a few simulated data sets from scratch and compare them with the committed records.

usage: sim_check.py SIM_DIR OUT_JSON [--rscript RSCRIPT]

The full study (2,400 data sets, about 28 CPU hours) runs only with main.nf --full; a rerun in CI
redraws these data sets from their seeds with sim_study.R and requires every recorded value
(selected SNPs, out-of-bag error curve, ranks, gini, p-values, what each method found) to equal
the committed record, apart from the run time.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATASETS = [(1, 0.05, 0.7, 1), (3, 0.2, 1.0, 1), (2, 0.1, 1.0, 7)]


def same(a, b, path=""):
    diffs = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k == "seconds":
                continue
            diffs += same(a.get(k), b.get(k), f"{path}.{k}")
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for i, (x, y) in enumerate(zip(a, b)):
            diffs += same(x, y, f"{path}[{i}]")
    elif isinstance(a, float) or isinstance(b, float):
        try:
            if abs(float(a) - float(b)) > 1e-9 * max(1.0, abs(float(a))):
                diffs.append(f"{path}: {a} vs {b}")
        except (TypeError, ValueError):
            diffs.append(f"{path}: {a} vs {b}")
    elif a != b:
        diffs.append(f"{path}: {a} vs {b}")
    return diffs


def main():
    sim_dir, out = sys.argv[1:3]
    rscript = sys.argv[sys.argv.index("--rscript") + 1] if "--rscript" in sys.argv else "Rscript"
    rows = []
    for model, maf, r2, rep in DATASETS:
        path = Path(sim_dir) / f"m{model}_maf{maf:g}_r{r2:g}.json"
        rec = next((r for r in json.loads(path.read_text()) if r["rep"] == rep), None) if path.exists() else None
        if rec is None:
            rows.append({"model": model, "maf": maf, "r2": r2, "rep": rep, "seconds": None, "k": None,
                         "differences": ["no committed record"]})
            continue
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "one.jsonl"
            subprocess.run([rscript, str(HERE / "sim_study.R"), str(model), f"{maf:g}", f"{r2:g}", str(rep), str(rep), str(f)],
                           check=True)
            fresh = json.loads(f.read_text().splitlines()[0])
        d = same(rec, fresh)
        rows.append({"model": model, "maf": maf, "r2": r2, "rep": rep, "seconds": fresh["ef"]["seconds"],
                     "k": fresh["ef"]["k"], "differences": d[:10]})
        print(f"model {model} MAF {maf} r2 {r2} rep {rep}: {'same' if not d else str(len(d)) + ' differences'}")
    res = {"passed": all(not r["differences"] for r in rows), "datasets": rows}
    Path(out).write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
