"""Run the paper's two analyses on the aligned data and write every number we compare.

Usage: analyze.py ALNDIR OUTDIR [--boot 500] [--seed 0] [--muscle-label v3.6-source]

Writes OUTDIR/analysis.json (series, fits, bootstrap, selection, sensitivity variants) and
OUTDIR/bootstrap.npy.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

from hivrecomb.align import read_fasta
from hivrecomb.recombination import (
    as_array,
    bootstrap_rho,
    bin_events,
    concat_events,
    estimate_rho,
    mean_MpApB,
    pair_events,
    saturation,
)
from hivrecomb.selection import concat_rates, frequency_changes, ks, linked_mask, share_above

#: Generations per month: "generation time 2 days", "6 month ~ 100 generations".
GEN_PER_MONTH = 365.25 / 12 / 2
#: Figure 2A bin edges: 7 equal bins to 536 bp, read from the published panel's point positions.
FIG2A_EDGES = np.linspace(0.0, 536.0, 8)
#: Figure 2B bin width in bp x generations, read from the published panel's point positions.
FIG2B_WIDTH = 8000.0
#: Hitch-hiking filter (Methods): synonymous sites within 100 bp of a non-synonymous one
#: changing faster than 0.002 per generation.
FAST = 0.002
WINDOW = 100.0


def load_patients(alndir):
    out = {}
    for p in range(1, 12):
        path = Path(alndir) / f"p{p}.fasta"
        aln = read_fasta(path)
        names = list(aln)
        X = as_array([aln[n] for n in names])
        t = np.array([float(n.split("|")[1]) for n in names]) * GEN_PER_MONTH
        out[p] = (X, t)
    return out


def series(binned):
    return {
        "centers": binned.centers.tolist(),
        "p": np.where(np.isfinite(binned.p), binned.p, None).tolist(),
        "err": np.where(np.isfinite(binned.err), binned.err, None).tolist(),
        "pairs": binned.pairs.tolist(),
        "counts": binned.counts.tolist(),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("alndir")
    ap.add_argument("outdir")
    ap.add_argument("--boot", type=int, default=500)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--muscle-label", default="v3.6 built from source")
    a = ap.parse_args(argv)
    out = Path(a.outdir)
    out.mkdir(parents=True, exist_ok=True)

    data = load_patients(a.alndir)
    per = [pair_events(X, t, patient=p, min_count=3) for p, (X, t) in data.items()]
    ev = concat_events(per)

    rec2a = bin_events(ev["d"], ev["found"], FIG2A_EDGES)
    oth2a = bin_events(ev["d"], ev["other"], FIG2A_EDGES)
    fit = estimate_rho(ev, bin_width=FIG2B_WIDTH, weights="relative")
    boot = np.sort(bootstrap_rho(per, n=a.boot, seed=a.seed, bin_width=FIG2B_WIDTH,
                                 weights="relative"))
    np.save(out / "bootstrap.npy", boot)

    # slope of the "other haplotypes" curve against distance (the paper: no distance dependence)
    ok = oth2a.counts > 0
    slope, intercept = np.polyfit(oth2a.centers[ok], oth2a.p[ok], 1)

    rates_per = [frequency_changes(X, t, patient=p) for p, (X, t) in data.items()]
    rates = concat_rates(rates_per)
    syn = rates["synonymous"].astype(bool)
    hh = linked_mask(rates, fast=FAST, window=WINDOW)
    r_ns, r_syn, r_nohh = rates["rate"][~syn], rates["rate"][syn], rates["rate"][syn & ~hh]
    D_syn, p_syn = ks(r_ns, r_syn)
    D_nohh, p_nohh = ks(r_ns, r_nohh)

    digest_file = Path(a.alndir) / "input_digest.txt"
    res = {
        "input_digest": digest_file.read_text().strip() if digest_file.exists() else None,
        "generations_per_month": GEN_PER_MONTH,
        "muscle": a.muscle_label,
        "alignment": {str(p): {"sequences": int(X.shape[0]), "columns": int(X.shape[1])}
                      for p, (X, t) in data.items()},
        "recombination": {
            "pairs": int(len(ev["d"])),
            "fig2a_edges": FIG2A_EDGES.tolist(),
            "fig2a_recombinant": series(rec2a),
            "fig2a_other": series(oth2a),
            "fig2a_other_weighted_mean": float(np.mean(ev["other"])),
            "fig2a_other_slope_per_bp": float(slope),
            "fig2b_width": FIG2B_WIDTH,
            "fig2b": series(fit.binned),
            "fit": {"c0": fit.c0, "c1": fit.c1, "c2": fit.c2},
            "MpApB": fit.MpApB,
            "rho": fit.rho,
            "bootstrap": {"n": int(a.boot), "seed": a.seed, "mean": float(np.mean(boot)),
                          "median": float(np.median(boot)), "std": float(np.std(boot))},
        },
        "selection": {
            "counts": {"nonsynonymous": int((~syn).sum()), "synonymous": int(syn.sum()),
                       "synonymous_no_hitchhiking": int(len(r_nohh))},
            "share_above_0.002": {"nonsynonymous": share_above(r_ns, FAST),
                                  "synonymous": share_above(r_syn, FAST),
                                  "synonymous_no_hitchhiking": share_above(r_nohh, FAST)},
            "max_rate": {"nonsynonymous": float(r_ns.max()), "synonymous": float(r_syn.max()),
                         "synonymous_no_hitchhiking": float(r_nohh.max())},
            "ks": {"vs_synonymous": {"D": D_syn, "p": p_syn},
                   "vs_synonymous_no_hitchhiking": {"D": D_nohh, "p": p_nohh}},
            "quantile_0.85_nonsynonymous": float(np.quantile(r_ns, 0.85)),
        },
        "sensitivity": {},
    }

    # sensitivity: allele-count cutoff (Methods: "repeated with this cutoff at two or four alleles"),
    # the convention behind <M pA pB>, and the Figure 2 bin widths.
    for mc in (2, 4):
        per_mc = [pair_events(X, t, patient=p, min_count=mc) for p, (X, t) in data.items()]
        f = estimate_rho(concat_events(per_mc), bin_width=FIG2B_WIDTH, weights="relative")
        res["sensitivity"][f"min_count_{mc}"] = {"c0": f.c0, "c1": f.c1, "c2": f.c2,
                                                 "MpApB": f.MpApB, "rho": f.rho}
    for M in ("M0", "M1"):
        for alleles in ("minor", "missing"):
            m = mean_MpApB(ev, M, alleles)
            res["sensitivity"][f"MpApB_{M}_{alleles}"] = {
                "MpApB": m, "rho": fit.c1 * fit.c2 / (m - fit.c0)}
    mmin = float(np.mean(np.minimum(ev["M0"], ev["M1"]) * ev["qA"] * ev["qB"]))
    res["sensitivity"]["MpApB_min_minor"] = {"MpApB": mmin,
                                             "rho": fit.c1 * fit.c2 / (mmin - fit.c0)}
    res["sensitivity"]["MpApB_paper_0.93"] = {"MpApB": 0.93,
                                              "rho": fit.c1 * fit.c2 / (0.93 - fit.c0)}
    for bw in (6000.0, 10000.0):
        f = estimate_rho(ev, bin_width=bw, weights="relative")
        res["sensitivity"][f"bin_width_{int(bw)}"] = {"c0": f.c0, "c1": f.c1, "c2": f.c2, "rho": f.rho}
    f = estimate_rho(ev, bin_width=FIG2B_WIDTH, weights="error")
    res["sensitivity"]["weights_error_bar"] = {"c0": f.c0, "c1": f.c1, "c2": f.c2, "rho": f.rho}

    # curves for the figures
    xs = np.linspace(0.0, float(fit.binned.edges[-1]), 400)
    res["recombination"]["fit_curve"] = {"x": xs.tolist(),
                                         "y": saturation(xs, fit.c0, fit.c1, fit.c2).tolist()}
    grid = np.linspace(0.0, 0.01, 501)
    res["selection"]["cumulative"] = {
        "x": grid.tolist(),
        "nonsynonymous": (np.searchsorted(np.sort(r_ns), grid, "right") / len(r_ns)).tolist(),
        "synonymous": (np.searchsorted(np.sort(r_syn), grid, "right") / len(r_syn)).tolist(),
        "synonymous_no_hitchhiking":
            (np.searchsorted(np.sort(r_nohh), grid, "right") / len(r_nohh)).tolist(),
    }
    for name, arr in (("nonsynonymous", r_ns), ("synonymous", r_syn),
                      ("synonymous_no_hitchhiking", r_nohh)):
        np.save(out / f"rates_{name}.npy", np.sort(arr))

    with open(out / "analysis.json", "w") as f:
        json.dump(res, f, indent=1, sort_keys=True)
    print(f"pairs {res['recombination']['pairs']}, rho {fit.rho:.3g}, "
          f"observations ns/syn {(~syn).sum()}/{syn.sum()}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
