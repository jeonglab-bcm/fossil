"""Merge the run's numbers with the hand-written notes into results.json.

Usage: build_results.py NOTES ANALYSIS PUBLISHED_VALUES COMPARISON PACKAGE_JSON OUT

The notes file holds what a person writes (labels, sources, assumptions, causes, controls' names)
and the skill block; everything numeric comes from this run.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

GEN = 365.25 / 12 / 2


def field(name, expected, observed, tol=None):
    f = {"name": name, "expected": expected, "observed": observed}
    if tol is not None:
        f["tolerance"] = tol
    return f


def fmt(v, digits=3):
    return None if v is None else float(f"%.{digits}g" % v)


def pixel_block(cmp_entry):
    controls = [{"name": k, "kind": v["kind"], "score": fmt(v["score"], 4)}
                for k, v in sorted(cmp_entry.get("controls", {}).items())]
    best = max((c["score"] for c in controls), default=0.0)
    return {
        "tolerance_px": 2,
        "dpi": 399,
        "published_near_ours": fmt(cmp_entry["published_near_ours"], 4),
        "ours_near_published": fmt(cmp_entry["ours_near_published"], 4),
        "threshold": round(min(0.99, best + 0.05), 4),
        "controls": controls,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    for n in ("notes", "analysis", "published_values", "comparison", "package", "out"):
        ap.add_argument(n)
    a = ap.parse_args(argv)
    notes = json.load(open(a.notes))
    an = json.load(open(a.analysis))
    pub = json.load(open(a.published_values))
    cmp_ = json.load(open(a.comparison))
    pkg = json.load(open(a.package)) if Path(a.package).exists() else None

    rec = an["recombination"]
    sel = an["selection"]
    items = {i["id"]: i for i in notes["items"]}

    def put(iid, **kw):
        items[iid].update(kw)

    # --- Figure 2A: the two series, point by point, in data units -------------------------------
    fields = []
    for key, label in (("fig2a_recombinant", "recombinant"), ("fig2a_other", "other")):
        ours = an["recombination"][key]
        for k, p in enumerate(pub["series"][key]):
            o = ours["p"][k]
            oe = ours["err"][k]
            if o is None or oe is None:
                continue
            tol = {"abs": round(p["err"] + oe, 4)}
            fields.append(field(f"{label} {p['x']:.0f} bp", round(p["y"], 3), round(o, 3), tol))
    put("fig2.a", values={"fields": fields, "tolerance": {"abs": 0.02}})
    items["fig2.a"]["pixels"] = pixel_block(cmp_["panels"]["fig2a"])

    # --- Figure 2B ------------------------------------------------------------------------------
    fields = []
    ours = rec["fig2b"]
    for k, p in enumerate(pub["series"]["fig2b"]):
        if k >= len(ours["p"]) or ours["p"][k] is None:
            continue
        tol = {"abs": round(p["err"] + (ours["err"][k] or 0.0), 4)}
        fields.append(field(f"{p['x']:.0f} bp x gen", round(p["y"], 3), round(ours["p"][k], 3), tol))
    put("fig2.b", values={"fields": fields, "tolerance": {"abs": 0.02}})
    items["fig2.b"]["pixels"] = pixel_block(cmp_["panels"]["fig2b"])

    # --- the fit and the recombination rate -----------------------------------------------------
    # The legend of Fig. 2B prints the fit, not a measured value: each constant is compared with
    # the spread of the same fit over the 500 resamples of the patients, the uncertainty the paper
    # itself quotes for rho.
    sd = rec["fit_bootstrap_sd"]
    put("text.fit", values={"fields": [
        field("c0", "0.10", fmt(rec["fit"]["c0"], 3), {"abs": fmt(sd["c0"], 3)}),
        field("c1", "0.26", fmt(rec["fit"]["c1"], 3), {"abs": fmt(sd["c1"], 3)}),
        field("c2", "4.39e-05", fmt(rec["fit"]["c2"], 3), {"abs": fmt(sd["c2"], 3)}),
    ], "tolerance": {"printed": True}})

    # <M pA pB> is measured from the data, not fitted, and is compared at printed precision.
    put("text.mpapb", values={"fields": [
        field("<M pA pB>", "0.93", fmt(rec["MpApB"], 3)),
    ], "tolerance": {"printed": True}})

    boot = rec["bootstrap"]
    put("text.rho", values={"fields": [
        # the paper prints the rate with its own one standard deviation, which is the tolerance
        # it gives the number; the deviation itself is the bootstrap item below
        field("rho (per site and generation)", "1.4e-05", fmt(rec["rho"], 3), {"abs": 0.6e-5}),
    ], "tolerance": {"printed": True}})

    put("text.bootstrap", values={"fields": [
        field("mean", "1.51e-05", fmt(boot["mean"], 3)),
        field("median", "1.38e-05", fmt(boot["median"], 3)),
        field("standard deviation", "0.55e-05", fmt(boot["std"], 3)),
    ], "tolerance": {"printed": True}})

    items["fig3"]["pixels"] = pixel_block(cmp_["panels"]["fig3"])

    # --- Figure 4: the three cumulative curves, read in data units -------------------------------
    cur = sel["cumulative"]
    x = np.asarray(cur["x"])
    n = {k: sel["counts"][k] for k in sel["counts"]}
    key_count = {"nonsynonymous": "nonsynonymous", "synonymous": "synonymous",
                 "synonymous_no_hitchhiking": "synonymous_no_hitchhiking"}
    fields = []
    for name, ys in pub["fig4"]["curves"].items():
        for xv, yv in zip(pub["fig4"]["x"], ys):
            if yv is None:
                continue
            o = float(np.interp(xv, x, cur[name]))
            m = n[key_count[name]]
            sigma = math.sqrt(max(yv * (1 - yv), 1e-6) / m)
            fields.append(field(f"{name} at {xv}", round(yv, 3), round(o, 3),
                                {"abs": round(2 * sigma, 4)}))
    put("fig4.curves", values={"fields": fields, "tolerance": {"abs": 0.02}})
    items["fig4.curves"]["pixels"] = pixel_block(cmp_["panels"]["fig4"])

    # the inset: the observation counts behind the curves, bin by bin. A class hidden under a
    # taller one drawn later cannot be read off the published panel and is left out. The tolerance
    # is two Poisson standard deviations of the published count plus 5 percent for reading it.
    ins_pub = pub["fig4_inset"]["counts"]
    ins_ours = sel["inset_counts"]
    fields = []
    for name, vals in ins_pub.items():
        for k, pv in enumerate(vals):
            if pv is None:
                continue
            ov = ins_ours[name][k]
            tol = 2 * math.sqrt(max(pv, 1.0)) + 0.05 * pv
            fields.append(field(f"{name}, bin {k}", round(pv, 1), ov, {"abs": round(tol, 1)}))
    fields.append(field("observations, non-synonymous", "2400", sel["counts"]["nonsynonymous"],
                        {"abs": 600}))
    put("fig4.inset", values={"fields": fields, "tolerance": {"abs": 1.0}})

    # --- the selection claims --------------------------------------------------------------------
    share = sel["share_above_0.002"]
    n = sel["counts"]
    above3 = sel["share_above_0.003"]
    put("text.selection", values={
        "fields": [
            field("non-synonymous faster than 0.002 per generation", "0.15",
                  fmt(share["nonsynonymous"], 3)),
            field("more fast non-synonymous than fast synonymous polymorphisms", "yes",
                  "yes" if share["nonsynonymous"] > share["synonymous"] else "no"),
            # read off Figure 4 (the published synonymous curve reaches 0.895 at 0.002 per
            # generation); the tolerance is two standard errors of a share on our sample
            field("share of synonymous faster than 0.002 per generation", "0.105",
                  fmt(share["synonymous"], 2),
                  {"abs": round(2 * math.sqrt(0.105 * 0.895 / max(n["synonymous"], 1)), 4)}),
            field("fastest non-synonymous change", "0.01", fmt(sel["max_rate"]["nonsynonymous"], 2)),
            field("share of synonymous without hitch-hiking beyond 0.003 per generation", "0.00",
                  fmt(above3["synonymous_no_hitchhiking"], 2)),
            field("selection coefficient of the top 15% (s >= 4 dp/dt)", "0.008",
                  fmt(4 * sel["quantile_0.85_nonsynonymous"], 2)),
        ],
        "tolerance": {"printed": True},
        "exceptions": [{
            "field": "non-synonymous faster than 0.002 per generation",
            "category": "paper_error",
            "evidence": [
                "The text says about 15 percent; the paper's own Figure 4 puts the "
                "non-synonymous curve at 0.828 at 0.002 per generation, which is 17.2 percent. "
                "Ours, 15.9 percent, lies between the two.",
                "PMC2813257/figure-reproduction/output/published_values.json"],
        }]})

    ks = sel["ks"]
    put("text.ks", values={"fields": [
        field("p, non-synonymous vs synonymous (< 1e-13)", "yes",
              "yes" if ks["vs_synonymous"]["p"] < 1e-13 else "no"),
        field("p, non-synonymous vs synonymous without hitch-hiking (< 1e-25)", "yes",
              "yes" if ks["vs_synonymous_no_hitchhiking"]["p"] < 1e-25 else "no"),
        field("Kolmogorov-Smirnov D, vs synonymous", "0.14", fmt(ks["vs_synonymous"]["D"], 2)),
    ], "tolerance": {"printed": True}})

    # --- the "other haplotypes" curve has no distance dependence ----------------------------------
    sl = rec["fig2a_other_slope_per_bp"]
    se = rec["fig2a_other_slope_se_per_bp"]
    rise_rec = (rec["fig2a_recombinant"]["p"][-1] - rec["fig2a_recombinant"]["p"][0])
    put("text.other_haplotypes", values={"fields": [
        # no distance dependence: the rise over the plotted range against two standard errors of
        # the slope of the same least squares fit
        field("rise of the other-haplotype curve over 500 bp", "0.0", fmt(sl * 500, 2),
              {"abs": round(2 * se * 500, 4)}),
        field("flatter than the recombinant curve", "yes", "yes" if abs(sl * 500) < rise_rec / 2 else "no"),
    ], "tolerance": {"printed": True}})

    # --- the Discussion's derived numbers -------------------------------------------------------
    # Our formulas applied to the paper's own rho = 1.4e-5 (the arithmetic check), and then to ours.
    def derived(r):
        return {"factor": 3e-4 / r,
                "coinfection": 2 * r / 3e-4,      # the heterozygote factor is 1/2
                "sweep_bp": 0.01 / (r * math.log(1e4 * 0.01)),
                "spacing_bp": 1 / 0.03 / 0.5 / 0.15}

    paper_vals = derived(1.4e-5)
    checks = [("factor below template switching", 20, paper_vals["factor"], 5.0),
              ("probability of coinfection", 0.1, paper_vals["coinfection"], 0.03),
              ("sweep region [bp]", 200, paper_vals["sweep_bp"], 60.0),
              ("distance between sweeping loci [bp]", 400, paper_vals["spacing_bp"], 100.0)]
    hits = sum(abs(e - g) <= t for _, e, g, t in checks)
    put("text.arithmetic", check={
        "passed": hits == len(checks),
        "detail": f"{hits} of {len(checks)} Discussion numbers come back from the paper's own "
                  f"rho = 1.4e-5: " + ", ".join(f"{n} {g:.3g} (paper {e})" for n, e, g, _ in checks)})

    rho = rec["rho"]
    ours = derived(rho)
    put("text.derived", values={"fields": [
        # the Discussion prints these to one significant digit ("about a factor of 20")
        field("template switching / rho", "2e1", fmt(ours["factor"], 2)),
        field("probability of coinfection", "1e-1", fmt(ours["coinfection"], 2)),
        field("sweep region [bp]", "2e2", fmt(ours["sweep_bp"], 2)),
        field("distance between sweeping loci [bp]", "4e2", fmt(ours["spacing_bp"], 2)),
    ], "tolerance": {"printed": True}})

    # --- the allele-count cutoff ------------------------------------------------------------------
    # "The analysis was repeated with this cutoff at two or four alleles, yielding similar
    # results": one claim about both cutoffs, so one field.
    s2 = an["sensitivity"]["min_count_2"]["rho"]
    s4 = an["sensitivity"]["min_count_4"]["rho"]
    similar = all(0.5 <= v / rho <= 2 for v in (s2, s4))
    put("text.cutoff", values={"fields": [
        field("the cutoff at two and at four alleles gives a similar rate", "yes",
              "yes" if similar else "no"),
    ], "tolerance": {"printed": True}})

    if pkg is not None:
        put("package", check={"passed": bool(pkg.get("passed")), "detail": pkg.get("detail", "")})

    # the GenBank download has no stable checksum (see prepare_data.py); the digest of the
    # parsed records takes its place
    run = dict(notes["run"])
    run["inputs"] = [dict(i, sha256=(an.get("input_digest") if i["sha256"] is None else i["sha256"]))
                     for i in run["inputs"]]
    out = {
        "schema": "paper2repro/results/v1",
        "paper": notes["paper"],
        "run": run,
        "session": notes["session"],
        "skill": notes["skill"],
        "items": [items[i["id"]] for i in notes["items"]],
    }
    with open(a.out, "w") as f:
        json.dump(out, f, indent=1)
    print(f"wrote {a.out} with {len(out['items'])} items")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
