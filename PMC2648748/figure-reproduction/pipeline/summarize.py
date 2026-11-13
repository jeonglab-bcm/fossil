"""Reduce the simulation records to per-setting files and the figure summary.

usage:
  summarize.py reduce CHUNK_DIR SIM_DIR      JSON lines of sim_study.R -> SIM_DIR/m<model>_maf<maf>_r<r2>.json
  summarize.py aggregate SIM_DIR SUMMARY     per-setting files -> summary.json (power, selected SNPs)

Power is the share of the 100 data sets in which every disease marker is identified at
alpha = 0.05 after the Bonferroni correction (the paper's definition). The primary rule for each
method, and the variants used to test hypotheses about unstated settings:

* epiForest: a disease marker is identified when it is in any reported one-, two- or three-way
  test (Bonferroni over all L = 1000 markers). Variants: both markers in one reported test
  (`joint`); both reported in one-way tests (`one_way`); Bonferroni over the candidates only
  (`bonf_candidates`).
* Stepwise logistic regression: single-locus tests adjusted by L, stage-2 tests by the number of
  stage-2 tests of each order (Marchini et al.). Variants: stage 2 adjusted by L(L-1)/2 and
  L(L-1)(L-2)/6 (`bonf_all`); single-locus tests only (`single_only`).
* Chi-squared: both disease markers significant after adjustment by L.
"""
import glob
import json
import math
import os
import sys

MODELS = (1, 2, 3)
MAFS = (0.05, 0.1, 0.2, 0.5)
R2S = (0.7, 1.0)
L = 1000
ALPHA = 0.05
REPS = 100


def key(model, maf, r2):
    return f"m{model}_maf{maf:g}_r{r2:g}"


def reduce(chunk_dir, sim_dir):
    rows = {}
    for f in sorted(glob.glob(os.path.join(chunk_dir, "**", "*.jsonl"), recursive=True)):
        for line in open(f):
            if not line.strip():
                continue
            r = json.loads(line)
            rows.setdefault(key(r["model"], r["maf"], r["r2"]), {})[r["rep"]] = r
    os.makedirs(sim_dir, exist_ok=True)
    for k, reps in sorted(rows.items()):
        recs = [reps[i] for i in sorted(reps)]
        with open(os.path.join(sim_dir, k + ".json"), "w") as fh:
            fh.write("[\n" + ",\n".join(json.dumps(r, separators=(",", ":")) for r in recs) + "\n]\n")
    print(f"reduced {sum(len(v) for v in rows.values())} data sets into {len(rows)} settings")


def num(v):
    """A p-value from the records; R's NA (written as "NA" or null) means the test was not run."""
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def lr_found_all(r):
    """Stepwise LR with stage 2 adjusted by all L(L-1)/2 and L(L-1)(L-2)/6 tests."""
    lr = r["lr"]
    out = []
    for i in range(2):
        p1 = num(lr["p1"][i])
        f = p1 is not None and p1 * L < ALPHA
        for p, m in ((num(lr["p2min"][i]), math.comb(L, 2)), (num(lr["p3min"][i]), math.comb(L, 3))):
            if p is not None and p * m < ALPHA:
                f = True
        out.append(f)
    return out


def median(v):
    s = sorted(v)
    n = len(s)
    return (s[n // 2] + s[(n - 1) // 2]) / 2


def share(rows, fn):
    return round(100 * sum(1 for r in rows if fn(r)) / len(rows), 6)


def aggregate(sim_dir, out):
    settings = []
    for model in MODELS:
        for r2 in R2S:
            for maf in MAFS:
                path = os.path.join(sim_dir, key(model, maf, r2) + ".json")
                if not os.path.exists(path):
                    continue
                rows = json.load(open(path))
                s = {"model": model, "maf": maf, "r2": r2, "n": len(rows), "complete": len(rows) == REPS}
                s["power"] = {
                    "epiforest": share(rows, lambda r: all(r["ef"]["found"])),
                    "lr": share(rows, lambda r: all(r["lr"]["found"])),
                    "chisq": share(rows, lambda r: all(r["chisq"]["found"])),
                }
                s["variants"] = {
                    "epiforest_joint": share(rows, lambda r: r["ef"]["found_joint"]),
                    "epiforest_one_way": share(rows, lambda r: all(r["ef"]["found_one_way"])),
                    "epiforest_bonf_candidates": share(rows, lambda r: all(r["ef"]["found_bonf_candidates"])),
                    "epiforest_in_candidates": share(rows, lambda r: all(r["ef"]["in_candidates"])),
                    "lr_bonf_all": share(rows, lambda r: all(lr_found_all(r))),
                    "lr_single_only": share(rows, lambda r: all(num(p) is not None and p * L < ALPHA
                                                                for p in r["lr"]["p1"])),
                }
                ks = [r["ef"]["k"] for r in rows]
                s["selected"] = ks
                s["selected_median"] = median(ks)
                s["selected_max"] = max(ks)
                s["selected_min"] = min(ks)
                s["forests_mean"] = round(sum(r["ef"]["forests"] for r in rows) / len(rows), 3)
                s["false_identified_mean"] = round(sum(r["ef"]["n_false"] for r in rows) / len(rows), 4)
                settings.append(s)
    # the figures' panels: r2 = 0.7 models 1-3, then r2 = 1.0 models 1-3; methods in the
    # published order (epiForest, BEAM, logistic regression, chi-squared); BEAM was not run
    panels = []
    for r2 in R2S:
        for model in MODELS:
            ss = {s["maf"]: s for s in settings if s["model"] == model and s["r2"] == r2}
            power = [[ss[m]["power"][meth] if (m in ss and meth) else None for m in MAFS]
                     for meth in ("epiforest", None, "lr", "chisq")] if ss else None
            panels.append({"model": model, "r2": r2,
                           "power": power,
                           "selected": [ss[m]["selected"] if m in ss else [] for m in MAFS]})
    all_k = [k for s in settings for k in s["selected"]]
    res = {"settings": settings, "panels": panels,
           "pooled": {"datasets": len(all_k), "selected_median": median(all_k) if all_k else None,
                      "selected_max": max(all_k) if all_k else None}}
    with open(out, "w") as fh:
        json.dump(res, fh, indent=1)
    print(f"summary of {len(settings)} settings, {len(all_k)} data sets -> {out}")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "reduce":
        reduce(sys.argv[2], sys.argv[3])
    elif cmd == "aggregate":
        aggregate(sys.argv[2], sys.argv[3])
    else:
        raise SystemExit(__doc__)
