"""Haplotype simulation of Meng et al. (2009), Figures 4-6: H4M4 model with two-SNP risk haplotypes,
K4S4N100 design, r^2 between the two SNPs of a risk haplotype 0, 0.1, ..., 1, 100 replicates of 250
cases and 250 controls, original RF.

Three codings of each replicate:
  SNP   the 8 risk SNPs as genotypes (3 categories) + 92 noise SNPs; 5000 trees;
  HAP   the 4 true haplo-genotypes (10 categories) + 92 noise SNPs; 5000 trees;
  PRED  the 4 haplo-genotypes with the phase of double heterozygotes drawn from the EM posterior,
        100 draws, one forest of 1000 trees each; importances averaged over the 100 forests.

  hap_study.py run OUTDIR --r2 0.3 --reps 0-99 [--rule empirical_ratio] [--npred 100]
  hap_study.py merge OUTDIR MERGED.json
"""

import argparse
import json
import os
import sys
import time

import numpy as np

from rfld.forest import grow_forest
from rfld.haplo import haplotype_em, sample_haplotype_pairs
from rfld.simulate import MODELS, haplo_genotype_code, haplotype_dataset, haplotype_frequencies

STUDY = 2666661
R2_LEVELS = [round(0.1 * i, 1) for i in range(11)]
RULES = ["empirical_ratio", "equal_snp_freq"]


def seeds(r2, rep, rule):
    ss = np.random.SeedSequence([STUDY, 99, RULES.index(rule), R2_LEVELS.index(r2), rep])
    a, b, c = ss.generate_state(3)
    return int(a), int(b % (2**31 - 1)), int(c)


def run_one(r2, rep, rule, ntree, ntree_pred, npred, mtry):
    dseed, fseed, pseed = seeds(r2, rep, rule)
    rng = np.random.default_rng(dseed)
    freqs = haplotype_frequencies(r2, rule)
    d = haplotype_dataset(rng, MODELS["H4M4"], freqs)
    y, snps, noise, haps = d["y"], d["snps"], d["noise"], d["haps"]
    k = haps.shape[1]
    out = {"r2": r2, "rep": rep, "rule": rule, "freqs": [float(f) for f in freqs],
           "data_seed": dseed, "forest_seed": fseed, "pred_seed": pseed, "ntree": ntree,
           "ntree_pred": ntree_pred, "npred": npred, "mtry": mtry, "n_risk_haps": k,
           "n_noise": int(noise.shape[1])}
    Xs = np.c_[snps, noise]
    f = grow_forest(Xs, y, ntree=ntree, mtry=mtry, seed=fseed)
    out["SNP"] = [round(float(v), 10) for v in f["im0"]]
    hcode = haplo_genotype_code(haps)
    Xh = np.c_[hcode, noise]
    ncat = np.r_[np.full(k, 10), np.full(noise.shape[1], 3)]
    f = grow_forest(Xh, y, ntree=ntree, mtry=mtry, seed=fseed + 1, ncat=ncat)
    out["HAP"] = [round(float(v), 10) for v in f["im0"]]
    # predicted haplotypes
    prng = np.random.default_rng(pseed)
    em = [haplotype_em(snps[:, 2 * j], snps[:, 2 * j + 1])[0] for j in range(k)]
    out["em_freqs"] = [[float(x) for x in e] for e in em]
    draws = [sample_haplotype_pairs(prng, snps[:, 2 * j], snps[:, 2 * j + 1], em[j], npred) for j in range(k)]
    acc = np.zeros(Xh.shape[1])
    ambiguous = 0
    for s in range(npred):
        pcode = np.stack([haplo_genotype_code(draws[j][s]) for j in range(k)], axis=1)
        if s == 0:
            ambiguous = int((pcode != hcode).sum())
        Xp = np.c_[pcode, noise]
        f = grow_forest(Xp, y, ntree=ntree_pred, mtry=mtry, seed=fseed + 2 + s, ncat=ncat)
        acc += f["im0"]
    out["PRED"] = [round(float(v), 10) for v in acc / npred]
    out["pred_wrong_phase_first_draw"] = ambiguous
    return out


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("outdir")
    r.add_argument("--r2", type=float, required=True)
    r.add_argument("--reps", default="0-99")
    r.add_argument("--rule", default="empirical_ratio", choices=RULES)
    r.add_argument("--ntree", type=int, default=5000)
    r.add_argument("--ntree-pred", type=int, default=1000)
    r.add_argument("--npred", type=int, default=100)
    r.add_argument("--mtry", type=int, default=35)
    m = sub.add_parser("merge")
    m.add_argument("outdir")
    m.add_argument("merged")
    a = ap.parse_args()
    if a.cmd == "run":
        r2 = round(a.r2, 1)
        if r2 not in R2_LEVELS:
            sys.exit(f"r2 must be one of {R2_LEVELS}")
        d = os.path.join(a.outdir, a.rule, f"r2_{r2:.1f}")
        os.makedirs(d, exist_ok=True)
        lo, hi = (int(x) for x in a.reps.split("-")) if "-" in a.reps else (int(a.reps), int(a.reps))
        for rep in range(lo, hi + 1):
            path = os.path.join(d, f"{rep:03d}.json")
            if os.path.exists(path):
                continue
            t = time.time()
            res = run_one(r2, rep, a.rule, a.ntree, a.ntree_pred, a.npred, a.mtry)
            with open(path + ".tmp", "w") as fh:
                json.dump(res, fh)
            os.replace(path + ".tmp", path)
            print(f"{a.rule} r2={r2} rep={rep} {time.time() - t:.1f}s", flush=True)
    else:
        merged = {}
        for rule in RULES:
            for r2 in R2_LEVELS:
                d = os.path.join(a.outdir, rule, f"r2_{r2:.1f}")
                if not os.path.isdir(d):
                    continue
                files = sorted(f for f in os.listdir(d) if f.endswith(".json"))
                merged.setdefault(rule, {})[f"{r2:.1f}"] = [json.load(open(os.path.join(d, f))) for f in files]
        json.dump(merged, open(a.merged, "w"))
        print({r: {k: len(v) for k, v in d.items()} for r, d in merged.items()}, file=sys.stderr)


if __name__ == "__main__":
    main()
