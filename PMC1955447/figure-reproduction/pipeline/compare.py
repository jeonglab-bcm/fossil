"""Compare every printed cell of Tables 1-5 with our run; score the second run, the controls and the hypotheses.

Usage: compare.py PUBLISHED_VALUES_JSON SIMULATION_JSON OUT_JSON [--csv TABLES_CSV]

Tolerance of a cell, fixed before the comparison: half a unit of the last printed digit plus 3 x sqrt(2)
Monte Carlo standard errors of one estimate (ours stands in for the paper's, which has the same design):
  % bias          the SD of the estimates over the converged fits / sqrt(their number), as % of the true value
  non-coverage    sqrt(p (1 - p) / n), p the mean of ours and the paper's, n our number of intervals
  % converged     100 sqrt(p (1 - p) / n), n the number of data sets
Table 5's non-coverage is taken over all 100 data sets of a cell, a non-converged one counting as not covered;
Tables 3 and 4 take it over the converged fits (each reading tested against the tables: hypotheses).
Table 1 and 3 cells are split by the paper's own convergence: the 19 cells that converged in 98-100% of data
sets (the fit is a well-defined maximum likelihood fit whatever the software) and the 8 that did not (which
fits enter the summaries depends on which fits NLMIXED declared converged).

second_run: our second run (other seeds) against the paper at the same tolerance, and against our main run
(replicate: how often two runs of one design disagree). controls: the paper's cells against a wrong cell of
our run (another ICC, number of groups or group size; another prevalence; another model). hypotheses: the
paper's Table 1 and 3 cells against our variants on replicates 0-199 (simulation.json, variants), with the
baseline (the main run's replicates 0-199) scored the same way.
"""
import csv
import json
import math
import sys

PARAMS = ["g00", "g01", "g10", "g11", "sigma0", "sigma1"]
PLABEL = {"g00": "γ00", "g01": "γ01", "g10": "γ10", "g11": "γ11", "sigma0": "σ0", "sigma1": "σ1"}
K = 3 * math.sqrt(2)


def unit(printed):
    s = printed.strip().lstrip("-")
    return 10.0 ** -(len(s.split(".")[1])) if "." in s else 1.0


def tol_bias(printed, mcse):
    return 0.5 * unit(printed) + K * (mcse or 0.0)


def tol_prop(printed, ours, n, scale=1.0):
    """Proportion printed on `scale` (1 for a rate, 100 for a percentage)."""
    if ours is None:
        ours = float(printed)
    p = (float(printed) / scale + ours / scale) / 2
    return 0.5 * unit(printed) + K * scale * math.sqrt(max(p * (1 - p), 0.0) / max(n, 1))


def cell_id(g, n, icc):
    return f"J{g}_n{n}_icc{float(icc):.2f}"


def field(name, printed, observed, tol, second=None, extra=None):
    f = {"name": name, "expected": printed, "observed": None if observed is None else round(observed, 4),
         "tolerance": {"abs": round(tol, 4)}}
    if second is not None:
        f["second_run"] = round(second, 4)
    if extra:
        f.update(extra)
    f["within"] = observed is not None and abs(observed - float(printed)) <= tol + 1e-12
    return f


def t1_fields(rows, cells, cells2, which, stable):
    out = []
    for r in rows:
        if (float(r["converged"]) >= 98) != stable and which != "converged":
            continue
        cid = cell_id(r["groups"], r["size"], r["icc"])
        s, s2 = cells[cid], (cells2 or {}).get(cid)
        name0 = f"{r['groups']} groups x {r['size']}, ICC {r['icc']}"
        if which == "converged":
            o = s["converged_pct"]
            out.append(field(f"{name0}: % converged", r["converged"], o, tol_prop(r["converged"], o, s["n"], 100),
                             s2 and s2["converged_pct"]))
        else:
            for p in PARAMS:
                o = s[p]["bias_pct"]
                out.append(field(f"{name0}: % bias {PLABEL[p]}", r[p], o, tol_bias(r[p], s[p]["bias_mcse"]),
                                 s2 and s2[p]["bias_pct"]))
    return out


def t3_fields(rows, conv_rows, cells, cells2, stable):
    out = []
    for r, rc in zip(rows, conv_rows):
        if (float(rc["converged"]) >= 98) != stable:
            continue
        cid = cell_id(r["groups"], r["size"], r["icc"])
        s, s2 = cells[cid], (cells2 or {}).get(cid)
        for p in PARAMS:
            o = s[p]["noncoverage"]
            out.append(field(f"{r['groups']} groups x {r['size']}, ICC {r['icc']}: non-coverage {PLABEL[p]}", r[p], o,
                             tol_prop(r[p], o, s[p]["n_ci"]), s2 and s2[p]["noncoverage"]))
    return out


def t2_fields(t2, run, run2):
    rates, pvals = [], []
    for p in PARAMS:
        for fac, lab in (("groups", "groups"), ("size", "group size"), ("icc", "ICC")):
            m, m2 = run["marginals"][p][fac], run2["marginals"][p][fac]
            for lev, printed in t2[p][fac].items():
                if lev == "p":
                    continue
                o = m[lev]
                rates.append(field(f"{PLABEL[p]}, {lab} {lev}: non-coverage", printed, o,
                                   tol_prop(printed, o, m["n"] / 3), m2[lev]))
            pp = float(t2[p][fac]["p"])
            exp = "significant" if pp < 0.05 else "not significant"
            obs = "significant" if m["p"] < 0.05 else "not significant"
            f = {"name": f"{PLABEL[p]}, effect of {lab} on non-coverage (p {t2[p][fac]['p']} printed)",
                 "expected": exp, "observed": obs, "p_ours": float(f"{m['p']:.4g}"),
                 "second_run": "significant" if m2["p"] < 0.05 else "not significant",
                 "p_second": float(f"{m2['p']:.4g}")}
            f["within"] = exp == obs
            pvals.append(f)
    return rates, pvals


def t4_fields(t4, pooled):
    out = []
    for p in PARAMS:
        for q, lab in (("bias", "% bias"), ("noncoverage", "non-coverage"), ("converged", "% converged")):
            for prev, printed in t4[p][q].items():
                s = pooled[prev]
                if q == "bias":
                    # pooled over the cells: the SE of the mean of the per-fit relative errors
                    o = s[p]["bias_pct"]
                    tol = tol_bias(printed, s[p].get("bias_mcse"))
                elif q == "noncoverage":
                    o = s[p]["noncoverage"]
                    tol = tol_prop(printed, o, s[p]["n_ci"])
                else:
                    o = s["converged_pct"]
                    tol = tol_prop(printed, o, s["n"], 100)
                out.append(field(f"{PLABEL[p]}, prevalence {prev}: {lab}", printed, o, tol))
    return out


def t5_fields(t5, cells, nc_over_all=False):
    conv, bias, nc = [], [], []
    for r in t5:
        cid = f"m{r['model']}_J{r['groups']}_n{r['size']}"
        s = cells[cid]
        name0 = f"Model {r['model']}, {r['groups']} groups x {r['size']}"
        o = s["converged_pct"]
        conv.append(field(f"{name0}: % converged", r["converged"], o, tol_prop(r["converged"], o, s["n"], 100)))
        for p in PARAMS:
            b, n = r[p]["bias"], r[p]["noncoverage"]
            ob = s[p]["bias_pct"]
            bias.append(field(f"{name0}: % bias {PLABEL[p]}", b, ob, tol_bias(b, s[p]["bias_mcse"])))
            on = None if s[p]["noncoverage"] is None else 100 * s[p]["noncoverage"]
            n_for_se = max(s[p]["n_ci"], 1)
            if nc_over_all:
                # hypothesis: a data set that did not converge counts as not covered (share of all data sets)
                cv = s["converged_pct"] / 100
                on = 100 * ((1 - cv) + cv * (s[p]["noncoverage"] or 0.0))
                n_for_se = s["n"]
            nc.append(field(f"{name0}: % non-coverage {PLABEL[p]}", n, on,
                            tol_prop(n, on if on is not None else float(n), n_for_se, 100)))
    return conv, bias, nc


def score(fields):
    return {"within": sum(f["within"] for f in fields), "fields": len(fields)}


def rms_z(fields):
    zs = []
    for f in fields:
        if not isinstance(f["observed"], float) or "tolerance" not in f:
            continue
        se = (f["tolerance"]["abs"] - 0.5 * unit(f["expected"])) / K
        sd = math.hypot(se, unit(f["expected"]) / math.sqrt(12))
        if sd > 0:
            zs.append((f["observed"] - float(f["expected"])) / sd)
    return round(math.sqrt(sum(z * z for z in zs) / len(zs)), 3) if zs else None


def summary(fields):
    s = score(fields)
    s["rms_z"] = rms_z(fields)
    if fields and "second_run" in fields[0]:
        s["second_within"] = sum(abs(f["second_run"] - float(f["expected"])) <= f["tolerance"]["abs"] + 1e-12
                                 for f in fields if isinstance(f.get("second_run"), float))
    return s


def shifted(cells, how):
    """A wrong cell for each cell: the same design with one factor moved to its neighbouring level."""
    out = {}
    for cid in cells:
        g, n, icc = cid.split("_")
        G, N, I = ["J30", "J50", "J100"], ["n5", "n30", "n50"], ["icc0.04", "icc0.17", "icc0.38"]
        if how == "icc":
            icc = I[(I.index(icc) + 1) % 3]
        elif how == "groups":
            g = G[(G.index(g) + 1) % 3]
        elif how == "size":
            n = N[(N.index(n) + 1) % 3]
        out[cid] = cells[f"{g}_{n}_{icc}"]
    return out


def main():
    args = sys.argv[1:]
    csv_out = None
    if "--csv" in args:
        i = args.index("--csv")
        csv_out = args[i + 1]
        del args[i:i + 2]
    pub_path, sim_path, out = args
    pub = json.load(open(pub_path))
    sim = json.load(open(sim_path))
    R1, R2 = sim["runs"]["main"], sim["runs"]["second"]
    T = {}
    T["table1_converged"] = t1_fields(pub["table1"], R1["cells"], R2["cells"], "converged", True)
    T["table1_stable"] = t1_fields(pub["table1"], R1["cells"], R2["cells"], "bias", True)
    T["table1_lowconv"] = t1_fields(pub["table1"], R1["cells"], R2["cells"], "bias", False)
    T["table3_stable"] = t3_fields(pub["table3"], pub["table1"], R1["cells"], R2["cells"], True)
    T["table3_lowconv"] = t3_fields(pub["table3"], pub["table1"], R1["cells"], R2["cells"], False)
    T["table2_rates"], T["table2_pvalues"] = t2_fields(pub["table2"], R1, R2)
    T["table4"] = t4_fields(pub["table4"], sim["prevalence"]["pooled"]["all_cells"])
    # Table 5's non-coverage is a share of all 100 data sets, a non-converged one counted as not covered (found by
    # testing: hypotheses, table5_noncoverage_converged_only)
    T["table5_converged"], T["table5_bias"], T["table5_noncoverage"] = t5_fields(pub["table5"], sim["robustness"]["cells"], nc_over_all=True)
    doc = {"about": "Every printed cell of Tables 1-5 against our run, with its tolerance; the second run, the controls "
                    "and the hypotheses scored the same way (compare.py).",
           "tolerance": "half a printed unit + 3 x sqrt(2) x the Monte Carlo SE of one estimate",
           "tables": {k: {"summary": summary(v), "fields": v} for k, v in T.items()}}

    # replicate: our second run, printed as the paper would, against the main run
    rep = {}
    for k in ("table1_converged", "table1_stable", "table1_lowconv", "table3_stable", "table3_lowconv", "table2_rates"):
        n = sum(1 for f in T[k] if isinstance(f.get("second_run"), float)
                and abs(f["second_run"] - f["observed"]) <= f["tolerance"]["abs"] + 1e-12)
        rep[k] = {"within": n, "fields": len(T[k])}
    doc["replicate"] = rep

    # controls: a wrong cell of our run against the paper's cell
    ctrl = {}
    for how in ("icc", "groups", "size"):
        c1 = shifted(R1["cells"], how)
        ctrl[f"neighbouring {how}"] = {
            "table1_stable": score(t1_fields(pub["table1"], c1, None, "bias", True)),
            "table1_converged": score(t1_fields(pub["table1"], c1, None, "converged", True)),
            "table3_stable": score(t3_fields(pub["table3"], pub["table1"], c1, None, True)),
            "table3_lowconv": score(t3_fields(pub["table3"], pub["table1"], c1, None, False)),
            "table1_lowconv": score(t1_fields(pub["table1"], c1, None, "bias", False))}
    P = sim["prevalence"]["pooled"]["all_cells"]
    rot = {"0.10": P["0.34"], "0.34": P["0.45"], "0.45": P["0.10"]}
    ctrl["table4: another prevalence"] = {"table4": score(t4_fields(pub["table4"], rot))}
    rc = sim["robustness"]["cells"]
    wrong = {cid: rc[f"m{int(cid.split('_')[0][1:]) % 8 + 1}_" + "_".join(cid.split("_")[1:])] for cid in rc}
    c_conv, c_bias, c_nc = t5_fields(pub["table5"], wrong, nc_over_all=True)
    ctrl["table5: the next model"] = {"table5_converged": score(c_conv), "table5_bias": score(c_bias),
                                      "table5_noncoverage": score(c_nc)}
    doc["controls"] = ctrl

    # hypotheses on replicates 0-199
    hyp = {}
    V = sim["variants"]
    for name, cells in V.items():
        hyp[name] = {"table1_converged": score(t1_fields(pub["table1"], cells, None, "converged", True)),
                     "table1_stable": score(t1_fields(pub["table1"], cells, None, "bias", True)),
                     "table1_lowconv": score(t1_fields(pub["table1"], cells, None, "bias", False)),
                     "table3_stable": score(t3_fields(pub["table3"], pub["table1"], cells, None, True)),
                     "table3_lowconv": score(t3_fields(pub["table3"], pub["table1"], cells, None, False)),
                     "mean_abs_converged_gap": round(sum(abs(cells[cell_id(r["groups"], r["size"], r["icc"])]["converged_pct"] - float(r["converged"]))
                                                         for r in pub["table1"]) / 27, 2)}
    # scale and convergence-rule hypotheses on the full main run
    for name, key in (("sd_scale", "sd_scale"), ("interior_only", "interior"), ("hessian_pd_required", "hessian")):
        cells = {cid: dict(R1["cells"][cid], **R1[key][cid]) for cid in R1["cells"]}
        hyp[name] = {"table1_converged": score(t1_fields(pub["table1"], cells, None, "converged", True)),
                     "table1_stable": score(t1_fields(pub["table1"], cells, None, "bias", True)),
                     "table1_lowconv": score(t1_fields(pub["table1"], cells, None, "bias", False)),
                     "table3_stable": score(t3_fields(pub["table3"], pub["table1"], cells, None, True)),
                     "table3_lowconv": score(t3_fields(pub["table3"], pub["table1"], cells, None, False)),
                     "mean_abs_converged_gap": round(sum(abs(cells[cell_id(r["groups"], r["size"], r["icc"])]["converged_pct"] - float(r["converged"]))
                                                         for r in pub["table1"]) / 27, 2)}
    for v in ("sd_scale", "log_scale", "boundary_as_miss"):
        cells = {cid: {**R1["cells"][cid], **{p: {**R1["cells"][cid][p], "noncoverage": R1["ci_variants"][cid][p][v]}
                                                for p in ("sigma0", "sigma1")}} for cid in R1["cells"]}
        sel = lambda fs: [f for f in fs if "σ" in f["name"]]  # noqa: E731
        hyp[f"table3_interval_{v}"] = {"table3_stable_sigma": score(sel(t3_fields(pub["table3"], pub["table1"], cells, None, True))),
                                       "table3_lowconv_sigma": score(sel(t3_fields(pub["table3"], pub["table1"], cells, None, False))),
                                       "cell_30x5_icc0.04_sigma0": round(R1["ci_variants"]["J30_n5_icc0.04"]["sigma0"][v], 4)}
    sel = lambda fs: [f for f in fs if "σ" in f["name"]]  # noqa: E731
    hyp["table3_interval_variance"] = {"table3_stable_sigma": score(sel(T["table3_stable"])),
                                       "table3_lowconv_sigma": score(sel(T["table3_lowconv"])),
                                       "cell_30x5_icc0.04_sigma0": round(R1["cells"]["J30_n5_icc0.04"]["sigma0"]["noncoverage"], 4)}
    tr = []
    for p in PARAMS:
        for fac in ("groups", "size", "icc"):
            pp = float(pub["table2"][p][fac]["p"])
            tr.append(((pp < 0.05) == (R1["marginals"][p][fac]["p_trend"] < 0.05)))
    hyp["table2_pvalues_trend_1df"] = {"table2_pvalues": {"within": sum(tr), "fields": len(tr)}}
    hyp["main_run"] = {k: doc["tables"][k]["summary"] for k in ("table1_converged", "table1_stable", "table1_lowconv", "table3_stable", "table3_lowconv")}
    hyp["main_run"]["mean_abs_converged_gap"] = round(sum(abs(f["observed"] - float(f["expected"])) for f in T["table1_converged"]) / 27, 2)
    for alt in ("size5", "groups30"):
        hyp[f"table4_{alt}_cells"] = {"table4": score(t4_fields(pub["table4"], sim["prevalence"]["pooled"][alt]))}
    rsd = {cid: dict(rc[cid], **sim["robustness"]["sd_scale"][cid]) for cid in rc}
    _, b_sd, _ = t5_fields(pub["table5"], rsd)
    _, b_var, _ = t5_fields(pub["table5"], rc)
    _, _, nc_conv = t5_fields(pub["table5"], rc, nc_over_all=False)
    hyp["table5_noncoverage_converged_only"] = {"table5_noncoverage": score(nc_conv),
                                                "group_size_5": score([f for f in nc_conv if "x 5:" in f["name"]]),
                                                "main_run_group_size_5": score([f for f in T["table5_noncoverage"] if "x 5:" in f["name"]])}
    hyp["table5_sd_scale"] = {
        "table5_bias_sigma": score([f for f in b_sd if "σ" in f["name"]]),
        "main_run_table5_bias_sigma": score([f for f in b_var if "σ" in f["name"]]),
        "by_model": {m: {"sd_scale": score([f for f in b_sd if "σ" in f["name"] and f["name"].startswith(f"Model {m},")]),
                         "variance_scale": score([f for f in b_var if "σ" in f["name"] and f["name"].startswith(f"Model {m},")])}
                     for m in range(1, 9)}}
    doc["hypotheses"] = hyp
    with open(out, "w") as f:
        json.dump(doc, f, indent=1, ensure_ascii=False)
        f.write("\n")
    if csv_out:
        with open(csv_out, "w", newline="") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(["item", "cell", "paper", "ours", "tolerance", "within", "second_run"])
            for k, v in T.items():
                for fl in v:
                    w.writerow([k, fl["name"], fl["expected"], fl["observed"], fl.get("tolerance", {}).get("abs", ""),
                                int(fl["within"]), fl.get("second_run", "")])


if __name__ == "__main__":
    main()
