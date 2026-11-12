"""Summary statistics of the simulation studies, as the paper defines them (Methods, "Simulation
Analysis for SNPs" and "for Haplotypes").

  summarize.py reduce-snp MERGED.json OUT.json     per-replicate statistics of a SNP study
  summarize.py reduce-hap MERGED.json OUT.json     per-replicate statistics of the haplotype study
  summarize.py aggregate SNP.json HAP.json OTHER_DIR SNP_INDEP.json OUT.json

Per replicate (reduce), for each forest/importance combination (RF0, RF1 at R = 0.5 and at 0.02;
IM0, IM1) of the SNP study:
  m   mean IM of the rSNPs (Fig. 1)
  a   1 if every rSNP and LD.rSNP has a higher IM than every noise SNP (nSNPs and LD.nSNPs) (Fig. 2)
  b   the smallest X such that each rSNP or one of its LD.rSNPs ranks in the top X (Fig. 3,
      "rSNPs/LD.rSNPs")
  w   the smallest X such that every rSNP ranks in the top X ("rSNPs with LD.rSNPs")
and for each coding (SNP, HAP, PRED) of the haplotype study: m (mean IM of the risk variables,
Fig. 4), a (Fig. 5), w (all risk variables in the top X, Fig. 6), and for SNP also b (at least one
SNP of each risk haplotype in the top X, "BEST.SNP").
Ranks: 1 = highest IM; tied IMs share the largest rank (a tie never helps a risk variable).
The aggregate is the mean over replicates (with the SE of m) and, for X = 1..N, the share of
replicates with b <= X or w <= X.
"""

import json
import os
import sys

import numpy as np
from scipy.stats import rankdata

COMBOS = {"RF0:IM0": ("RF0", "im0"), "RF0:IM1": ("RF0", "im1"),
          "RF1:IM0": ("RF1_R0.5", "im0"), "RF1:IM1": ("RF1_R0.5", "im1"),
          "RF1(R=0.02):IM0": ("RF1_R0.02", "im0"), "RF1(R=0.02):IM1": ("RF1_R0.02", "im1")}


def ranks(im):
    return rankdata(-np.asarray(im), method="max")


def reduce_snp_rep(rep):
    kinds = np.array(rep["kinds"])
    partner = np.array(rep["partner"])
    r_idx = np.where(kinds == "rSNP")[0]
    ldr_idx = np.where(kinds == "LD.rSNP")[0]
    noise_idx = np.where((kinds == "nSNP") | (kinds == "LD.nSNP"))[0]
    groups = [[r] + list(ldr_idx[partner[ldr_idx] == r]) for r in r_idx]
    risk = np.r_[r_idx, ldr_idx]
    out = {"rep": rep["rep"], "N": len(kinds), "max_noise_r2": round(rep["max_offdiag_r2_noise"], 6)}
    for name, (forest, imk) in COMBOS.items():
        if forest not in rep["forests"]:
            continue
        im = np.asarray(rep["forests"][forest][imk])
        rk = ranks(im)
        out[name] = {"m": round(float(im[r_idx].mean()), 10),
                     "a": int(im[risk].min() > im[noise_idx].max()),
                     "b": int(max(min(rk[g]) for g in groups)), "w": int(rk[r_idx].max())}
    return out


def reduce_hap_rep(rep):
    k = rep["n_risk_haps"]
    out = {"rep": rep["rep"]}
    for coding in ("SNP", "HAP", "PRED"):
        nrisk = 2 * k if coding == "SNP" else k
        im = np.asarray(rep[coding])
        rk = ranks(im)
        d = {"N": len(im), "m": round(float(im[:nrisk].mean()), 10),
             "a": int(im[:nrisk].min() > im[nrisk:].max()), "w": int(rk[:nrisk].max())}
        if coding == "SNP":
            d["b"] = int(max(min(rk[2 * j], rk[2 * j + 1]) for j in range(k)))
        out[coding] = d
    return out


def agg(rows, key_m="m"):
    m = np.array([r[key_m] for r in rows])
    out = {"n": len(rows), "mean_im": float(m.mean()), "se_im": float(m.std(ddof=1) / np.sqrt(len(m))),
           "sd_im": float(m.std(ddof=1)), "above_noise": float(np.mean([r["a"] for r in rows]))}
    return out


def curve(vals, N):
    v = np.asarray(vals)
    return [float(np.mean(v <= x)) for x in range(1, N + 1)]


def aggregate_snp(red):
    out = {}
    for ld, reps in red.items():
        N = reps[0]["N"]
        out[ld] = {}
        for combo in COMBOS:
            if combo not in reps[0]:
                continue
            rows = [r[combo] for r in reps]
            d = agg(rows)
            d["top_any"] = curve([r["b"] for r in rows], N)
            d["top_r"] = curve([r["w"] for r in rows], N)
            out[ld][combo] = d
    return out


def aggregate_hap(red):
    out = {}
    for rule, levels in red.items():
        out[rule] = {}
        for r2, reps in levels.items():
            if not reps:
                continue
            d = {}
            for coding in ("SNP", "HAP", "PRED"):
                rows = [r[coding] for r in reps]
                d[coding] = agg(rows)
                d[coding]["top"] = curve([r["w"] for r in rows], rows[0]["N"])
            d["BEST.SNP"] = {"n": len(reps), "top": curve([r["SNP"]["b"] for r in reps], reps[0]["SNP"]["N"])}
            out[rule][r2] = d
    return out


def main():
    cmd = sys.argv[1]
    if cmd == "reduce-snp":
        merged = json.load(open(sys.argv[2]))
        red = {ld: [reduce_snp_rep(r) for r in reps] for ld, reps in merged.items()}
        json.dump(red, open(sys.argv[3], "w"), separators=(",", ":"))
    elif cmd == "reduce-hap":
        merged = json.load(open(sys.argv[2]))
        red = {rule: {r2: [reduce_hap_rep(r) for r in reps] for r2, reps in lv.items()} for rule, lv in merged.items()}
        json.dump(red, open(sys.argv[3], "w"), separators=(",", ":"))
    elif cmd == "aggregate":
        snp, hap, other_dir, indep, outp = sys.argv[2:7]
        res = {"snp": aggregate_snp(json.load(open(snp))), "hap": aggregate_hap(json.load(open(hap))),
               "snp_independent": aggregate_snp(json.load(open(indep))) if os.path.exists(indep) else {},
               "other_models": {}}
        if os.path.isdir(other_dir):
            for f in sorted(os.listdir(other_dir)):
                if f.endswith(".json"):
                    res["other_models"][f[:-5]] = aggregate_snp(json.load(open(os.path.join(other_dir, f))))
        json.dump(res, open(outp, "w"))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
