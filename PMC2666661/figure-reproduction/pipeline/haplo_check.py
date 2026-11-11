"""Check rfld's two-SNP haplotype EM against haplo.stats::haplo.em (R) on simulated data.

  haplo_check.py RSCRIPT OUT.json [--reps 3]

For each r^2 level of the haplotype study and each frequency rule, simulate replicates of 250 cases
and 250 controls (rfld.simulate), and compare, for every risk haplotype, the four EM frequencies and
the phase posterior of a double heterozygote between rfld.haplo and haplo.em.
"""
import argparse
import csv
import json
import os
import subprocess
import tempfile

import numpy as np

from rfld.haplo import haplotype_em, phase_posterior
from rfld.simulate import MODELS, haplotype_dataset, haplotype_frequencies

HERE = os.path.dirname(os.path.abspath(__file__))
# rfld haplotype index -> (allele at SNP 1, allele at SNP 2)
IDX = {(0, 0): 0, (1, 1): 1, (0, 1): 2, (1, 0): 3}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rscript")
    ap.add_argument("out")
    ap.add_argument("--reps", type=int, default=3)
    a = ap.parse_args()
    rows = []
    version = None
    with tempfile.TemporaryDirectory() as tmp:
        for rule in ("empirical_ratio", "equal_snp_freq"):
            for i in range(11):
                r2 = round(0.1 * i, 1)
                for rep in range(a.reps):
                    rng = np.random.default_rng([2666661, 7, i, rep, len(rule)])
                    d = haplotype_dataset(rng, MODELS["H4M4"], haplotype_frequencies(r2, rule))
                    g1, g2 = d["snps"][:, 0], d["snps"][:, 1]
                    gin = os.path.join(tmp, "g.csv")
                    gout = os.path.join(tmp, "o.csv")
                    with open(gin, "w", newline="") as fh:
                        w = csv.writer(fh)
                        w.writerow(["g1", "g2"])
                        w.writerows(zip(g1.tolist(), g2.tolist()))
                    res = subprocess.run([a.rscript, os.path.join(HERE, "haplo_check.R"), gin, gout],
                                         check=True, capture_output=True, text=True)
                    version = res.stdout.strip()
                    r_f = np.zeros(4)
                    r_post = None
                    for row in csv.DictReader(open(gout)):
                        r_f[IDX[(int(row["a1"]), int(row["a2"]))]] = float(row["freq"])
                        if row["post_00_11"] not in ("NA", ""):
                            r_post = float(row["post_00_11"])
                    f, _ = haplotype_em(g1, g2)
                    ours_post = phase_posterior(f)
                    rows.append({"rule": rule, "r2": r2, "rep": rep,
                                 "ours": [round(float(x), 6) for x in f], "haplo_em": [round(float(x), 6) for x in r_f],
                                 "max_abs_freq_diff": float(np.max(np.abs(f - r_f))),
                                 "post_ours": ours_post, "post_haplo_em": r_post,
                                 "post_abs_diff": None if r_post is None else abs(ours_post - r_post)})
    worst_f = max(r["max_abs_freq_diff"] for r in rows)
    posts = [r["post_abs_diff"] for r in rows if r["post_abs_diff"] is not None]
    summary = {"haplo_stats_version": version, "datasets": len(rows), "max_abs_freq_diff": worst_f,
               "max_abs_posterior_diff": max(posts) if posts else None,
               "passed": bool(worst_f < 1e-3 and (not posts or max(posts) < 1e-3)), "rows": rows}
    json.dump(summary, open(a.out, "w"), indent=1)
    print({k: v for k, v in summary.items() if k != "rows"})


if __name__ == "__main__":
    main()
