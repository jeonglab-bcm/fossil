"""Compare every printed cell of Tables 1-3 (n = 1500) and A1-A3 (n = 500) with our run; score the second run,
the controls and the hypothesis variants the same way; check the paper's MSEs against its own biases and SEs.

Usage: compare.py PUBLISHED_VALUES_JSON SIMULATION_JSON OUT_JSON [--csv TABLES_CSV]

Tolerance of a cell, fixed before the comparison: half a printed unit plus 3 x sqrt(2) Monte Carlo standard
errors of one 1,000-replicate estimate (ours stands in for the paper's; sqrt(2) because both are estimates):
  relative bias   100 x SD of the 1,000 log RR estimates / sqrt(1,000) / |log RR|
  SE              SD / sqrt(2 x 999)
  MSE             SD of the 1,000 squared errors / sqrt(1,000)
A cell "rounds to the printed value" when ours, rounded half away from zero at the printed precision, is the
printed value.

second_run: our second run (other seeds) at the same tolerance, as if it were the paper.
controls (wrong inputs): the paper's table against our run of another design: the other sample size, the other
  confounder form (linear and non-linear columns swapped), the other RR (rows of RR 1.5 and 2.0 swapped).
hypotheses: the paper's Tables 1-3 against each variant of the contamination rule and the fitted model,
  counted on the cells the variant changes (the contaminated cells; for noquad, the non-linear columns).
consistency: each printed MSE against (relative bias x log RR / 100)^2 + SE^2 from the paper's own Tables 1 and 2
  (A1 and A2), with the range the printed precision of the bias and SE allows.
"""
import csv
import json
import math
import sys
from decimal import ROUND_HALF_UP, Decimal

TABLES = {"table1": ("1500", "relbias"), "table2": ("1500", "se"), "table3": ("1500", "mse"),
          "tableA1": ("500", "relbias"), "tableA2": ("500", "se"), "tableA3": ("500", "mse")}
LABEL = {"table1": "Table 1", "table2": "Table 2", "table3": "Table 3",
         "tableA1": "Table A1", "tableA2": "Table A2", "tableA3": "Table A3"}
FORM = {"linear": "linear", "nonlinear": "non-linear"}
MCSE = {"relbias": "relbias_mcse", "se": "se_mcse", "mse": "mse_mcse"}


def decimals(s):
    return len(s.split(".")[1]) if "." in s else 0


def rounds_to(x, printed):
    q = Decimal(1).scaleb(-decimals(printed))
    r = Decimal(repr(x)).quantize(q, rounding=ROUND_HALF_UP)
    return r == Decimal(printed) or (r == 0 and Decimal(printed) == 0)


def cell_name(row, col):
    form, lev, m = col.split("|")
    return f"RR {row['rr']}, {row['py']}, {row['contamination']}: {FORM[form]} {lev}, {m}"


def ours(sim_cells, row, col, q):
    form, lev, m = col.split("|")
    c = sim_cells[f"{row['rr']}|{row['py']}|{form}|{lev}"][row["contamination"]][m]
    return c[q], c[MCSE[q]]


def tol(printed, mcse):
    return 0.5 * 10 ** -decimals(printed) + 3 * math.sqrt(2) * mcse


def score(rows, sim_cells, q, keep=lambda row, col: True, remap=lambda row, col: (row, col)):
    """Within-tolerance count of the paper's cells against one of our runs."""
    within = total = 0
    zs = []
    for row in rows:
        for col, printed in row["cells"].items():
            if not keep(row, col):
                continue
            r2, c2 = remap(row, col)
            try:
                o, se = ours(sim_cells, r2, c2, q)
            except KeyError:
                continue
            p = float(printed)
            total += 1
            within += abs(o - p) <= tol(printed, se)
            s = math.hypot(math.sqrt(2) * se, 10 ** -decimals(printed) / math.sqrt(12))
            zs.append((o - p) / s)
    rms = math.sqrt(sum(z * z for z in zs) / len(zs)) if zs else None
    return {"within": within, "fields": total, "rms_z": None if rms is None else round(rms, 3)}


def swap_form(row, col):
    form, lev, m = col.split("|")
    return row, f"{'nonlinear' if form == 'linear' else 'linear'}|{lev}|{m}"


def swap_rr(row, col):
    return {**row, "rr": "2.0" if row["rr"] == "1.5" else "1.5"}, col


def consistency(pub, t_bias, t_se, t_mse):
    """Printed MSE against the MSE implied by the printed bias and SE, with their rounding ranges."""
    out = []
    for rb, rs, rm in zip(pub["tables"][t_bias]["rows"], pub["tables"][t_se]["rows"], pub["tables"][t_mse]["rows"]):
        b1 = math.log(float(rb["rr"]))
        for col in rb["cells"]:
            b, s, m = rb["cells"][col], rs["cells"][col], rm["cells"][col]
            hb, hs, hm = 0.5 * 10 ** -decimals(b), 0.5 * 10 ** -decimals(s), 0.5 * 10 ** -decimals(m)
            bias = [abs(float(b)) - hb, abs(float(b)) + hb]
            bias = [max(bias[0], 0) * b1 / 100, bias[1] * b1 / 100]
            lo = bias[0] ** 2 + (float(s) - hs) ** 2
            hi = bias[1] ** 2 + (float(s) + hs) ** 2
            implied = (float(b) * b1 / 100) ** 2 + float(s) ** 2
            ok = lo - hm <= float(m) <= hi + hm
            out.append({"name": cell_name(rb, col), "printed_mse": m, "implied": round(implied, 4),
                        "range": [round(lo, 4), round(hi, 4)], "consistent": ok})
    return out


def main():
    args = sys.argv[1:]
    csv_out = None
    if "--csv" in args:
        i = args.index("--csv"); csv_out = args[i + 1]; del args[i:i + 2]
    pub_path, sim_path, out = args
    pub = json.load(open(pub_path))
    sim = json.load(open(sim_path))
    R = sim["runs"]
    doc = {"about": "Every printed cell of Tables 1-3 and A1-A3 against our run (fields), with the tolerance; the "
                    "second run, the wrong-input controls and the hypotheses scored the same way.",
           "tolerance": "half a printed unit + 3 x sqrt(2) x Monte Carlo SE of one 1,000-replicate estimate",
           "tables": {}, "replicate": {}, "controls": {}, "hypotheses": {}, "consistency": {}}
    for t, (n, q) in TABLES.items():
        rows = pub["tables"][t]["rows"]
        cells, cells2 = R["main"][f"n{n}"], R["second"][f"n{n}"]
        fields = []
        by_model = {"LB": [0, 0], "RP": [0, 0]}
        for row in rows:
            for col, printed in row["cells"].items():
                o, se = ours(cells, row, col, q)
                o2, _ = ours(cells2, row, col, q)
                tl = tol(printed, se)
                fields.append({"name": cell_name(row, col), "expected": printed, "observed": round(o, 4),
                               "tolerance": {"abs": round(tl, 4)}, "second_run": round(o2, 4),
                               "rounds_to_printed": rounds_to(o, printed)})
                m = col.split("|")[2]
                by_model[m][0] += abs(o - float(printed)) <= tl
                by_model[m][1] += 1
        within = sum(abs(f["observed"] - float(f["expected"])) <= f["tolerance"]["abs"] for f in fields)
        doc["tables"][t] = {"label": LABEL[t], "n": int(n), "quantity": q, "fields": fields,
                            "summary": {"fields": len(fields), "within": within,
                                        "rounds_to_printed": sum(f["rounds_to_printed"] for f in fields),
                                        "rms_z": score(rows, cells, q)["rms_z"],
                                        "by_model": {k: {"within": v[0], "fields": v[1]} for k, v in by_model.items()}}}
        doc["replicate"][t] = score(rows, cells2, q)
        other = R["main"]["n500" if n == "1500" else "n1500"]
        doc["controls"][t] = {
            f"our n = {'500' if n == '1500' else '1500'} run (the other sample size)": score(rows, other, q),
            "our run with the linear and non-linear columns swapped": score(rows, cells, q, remap=swap_form),
            "our run with the RR 1.5 and 2.0 rows swapped": score(rows, cells, q, remap=swap_rr),
            "our run (the right design)": score(rows, cells, q)}
    contaminated = lambda row, col: row["contamination"] != "0%"  # noqa: E731
    for name in sim["variants"]:
        n = "500" if "n500" in R[name] else "1500"
        for t in (("tableA1", "tableA2", "tableA3") if n == "500" else ("table1", "table2", "table3")):
            q = TABLES[t][1]
            rows = pub["tables"][t]["rows"]
            if name == "noquad":
                keep = lambda row, col: col.startswith("nonlinear")  # noqa: E731
            elif name == "floor":
                keep = lambda row, col: row["contamination"] == "5%"  # noqa: E731
            else:
                keep = contaminated
            doc["hypotheses"].setdefault(name, {})[t] = {**score(rows, R[name][f"n{n}"], q, keep),
                                                        "main_run": score(rows, R["main"][f"n{n}"], q, keep)}
            if name == "floor":
                doc["hypotheses"][name][t]["sample_run"] = score(rows, R["sample"]["n1500"], q, keep)
    for tb, ts, tm in (("table1", "table2", "table3"), ("tableA1", "tableA2", "tableA3")):
        c = consistency(pub, tb, ts, tm)
        doc["consistency"][tm] = {"cells": len(c), "consistent": sum(x["consistent"] for x in c),
                                  "inconsistent": [x for x in c if not x["consistent"]]}
    json.dump(doc, open(out, "w"), indent=1)
    open(out, "a").write("\n")
    if csv_out:
        with open(csv_out, "w", newline="") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(["table", "n", "quantity", "rr", "outcome", "contamination", "confounder", "association", "model",
                        "paper", "ours", "tolerance", "within", "rounds_to_printed", "second_run"])
            for t, d in doc["tables"].items():
                for row, chunk in zip(pub["tables"][t]["rows"], [d["fields"][i:i + 8] for i in range(0, 144, 8)]):
                    for col, fl in zip(row["cells"], chunk):
                        form, lev, m = col.split("|")
                        w.writerow([t, d["n"], d["quantity"], row["rr"], row["py"], row["contamination"], form, lev, m,
                                    fl["expected"], fl["observed"], fl["tolerance"]["abs"],
                                    abs(fl["observed"] - float(fl["expected"])) <= fl["tolerance"]["abs"],
                                    fl["rounds_to_printed"], fl["second_run"]])
    for t, d in doc["tables"].items():
        s = d["summary"]
        print(f"{t}: {s['within']} of {s['fields']} within tolerance, {s['rounds_to_printed']} as printed, RMS z {s['rms_z']}; "
              f"second run {doc['replicate'][t]['within']}; controls {[v['within'] for v in doc['controls'][t].values()]}",
              file=sys.stderr)


if __name__ == "__main__":
    main()
