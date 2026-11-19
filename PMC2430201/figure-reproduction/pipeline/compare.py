"""Compare every printed cell of Tables 3-8 with our run, and score the controls and the hypotheses.

Usage: compare.py PUBLISHED_VALUES_JSON SIMULATION_JSON OUT_JSON [--csv TABLES_CSV]

--csv also writes every cell as one row (table, setting, column, paper, ours, tolerance, within, second run).

Tolerance of a cell, fixed before the comparison: half a printed unit plus 3 x sqrt(2) Monte Carlo standard
errors of one 10,000-replicate estimate (ours stands in for the paper's):
  bias      sd of the 10,000 pooled estimates / sqrt(10,000), as a percentage of the true value
  coverage, power   sqrt(p (1 - p)/10,000), p the mean of ours and the paper's
  I2        the delta-method error of 100 (1 - 1/mean(Q/(k - 1)))
A cell "rounds to the printed value" when ours, rounded half away from zero, is the printed integer.

replicate: our second run (other seeds), rounded as if printed, against our main run at the same tolerance:
how often two runs of one design disagree. controls: the paper's table against our run of a different
design (a wrong input). hypotheses: the paper's table against our variants (simulation.json) and against
the other definitions of RoM bias and I2 computed from the main run.
"""
import json
import math
import sys

QLABEL = {"bias": "% bias", "coverage": "% coverage", "power": "% power", "i2": "I2 (%)"}
CONTROLS = {  # paper's table -> our run of another design
    "3": [("5", "SD 70 instead of 40"), ("7", "2:1 arms instead of 1:1")],
    "4": [("5", "SD 70 instead of 10"), ("3", "SD 40 instead of 10")],
    "5": [("3", "SD 40 instead of 70"), ("4", "SD 10 instead of 70")],
    "6": [("3", "normal instead of skewed"), ("5", "normal, SD 70")],
    "7": [("8", "1:2 arms instead of 2:1"), ("3", "1:1 arms instead of 2:1")],
    "8": [("7", "2:1 arms instead of 1:2"), ("3", "1:1 arms instead of 1:2")],
}
TAUKEY = {"0": "tau0", "0.5": "tau0.5"}


def half_up(x):
    return math.floor(abs(x) + 0.5) * (1 if x >= 0 else -1)


def se_of(q, s, observed, printed):
    if q in ("coverage", "power"):
        p = (observed + printed) / 200
        return 100 * math.sqrt(max(p * (1 - p), 0) / 10_000)
    return s[f"{q}_se"]


def cell_name(row, col):
    q, tau, m = col.split("|")
    return f"SMD {row['effect']:g}, {row['n']}, k {row['k']}: {QLABEL[q]}, tau {tau}, {m}"


def value(srow, col, bias_key="bias", i2_key="i2"):
    q, tau, m = col.split("|")
    s = srow.get(TAUKEY[tau])
    if s is None:
        return None, None
    s = s[m]
    key = bias_key if (q == "bias" and m == "RoM") else (i2_key if q == "i2" else q)
    return s[key], s


def score(pub_rows, sim_rows, cols=None, **kw):
    """Within-tolerance count of the paper's cells against one of our runs."""
    within = total = 0
    zs = []
    for prow, srow in zip(pub_rows, sim_rows):
        for col, printed in prow["cells"].items():
            q = col.split("|")[0]
            if cols and q not in cols:
                continue
            o, s = value(srow, col, **kw)
            if o is None:
                continue
            p = float(printed)
            tol = 0.5 + 3 * math.sqrt(2) * se_of(q, s, o, p)
            total += 1
            within += abs(o - p) <= tol
            se = math.sqrt(2) * se_of(q, s, o, p)
            if se > 0:
                zs.append((o - p) / math.hypot(se, 1 / math.sqrt(12)))
    rms = math.sqrt(sum(z * z for z in zs) / len(zs)) if zs else None
    return {"within": within, "fields": total, "rms_z": None if rms is None else round(rms, 3)}


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
    main_run, second = sim["runs"]["main"], sim["runs"]["second"]
    doc = {"about": "Every printed cell of Tables 3-8 against our run (fields), with the tolerance; the second run, "
                    "the wrong-input controls and the hypotheses scored the same way.",
           "tolerance": "0.5 + 3 x sqrt(2) x Monte Carlo SE of one 10,000-replicate estimate",
           "tables": {}, "replicate": {}, "controls": {}, "hypotheses": {}}
    own_within = own_cells = 0
    for n, t in pub["tables"].items():
        fields, by_q = [], {}
        rows = main_run[n]
        for prow, srow, srow2 in zip(t["rows"], rows, second[n]):
            for col, printed in prow["cells"].items():
                q = col.split("|")[0]
                o, s = value(srow, col)
                p = float(printed)
                tol = 0.5 + 3 * math.sqrt(2) * se_of(q, s, o, p)
                o2, _ = value(srow2, col)
                ok = abs(o - p) <= tol
                fields.append({"name": cell_name(prow, col), "expected": printed, "observed": round(o, 3),
                               "tolerance": {"abs": round(tol, 3)}, "second_run": round(o2, 3),
                               "rounds_to_printed": half_up(o) == int(printed)})
                b = by_q.setdefault(q, {"within": 0, "fields": 0, "rounds": 0})
                b["within"] += ok
                b["fields"] += 1
                b["rounds"] += half_up(o) == int(printed)
                # the second run, printed, against the main run: two runs of one design
                tol_own = 0.5 + 3 * math.sqrt(2) * se_of(q, s, o, half_up(o2))
                own_cells += 1
                own_within += abs(o - half_up(o2)) <= tol_own
        within = sum(abs(f["observed"] - float(f["expected"])) <= f["tolerance"]["abs"] for f in fields)
        doc["tables"][n] = {"fields": fields, "by_quantity": by_q,
                            "summary": {"fields": len(fields), "within": within,
                                        "rounds_to_printed": sum(f["rounds_to_printed"] for f in fields),
                                        "rms_z": score(t["rows"], rows)["rms_z"]}}
        doc["replicate"][n] = score(t["rows"], second[n])
        doc["controls"][n] = {f"our Table {c} ({why})": {**score(t["rows"], main_run[c]),
                                                         "rom_columns": _rom_only(t["rows"], main_run[c])}
                              for c, why in CONTROLS[n]}
        doc["controls"][n]["our Table " + n + " (the right design)"] = {**score(t["rows"], rows),
                                                                      "rom_columns": _rom_only(t["rows"], rows)}
    doc["replicate"]["own_runs_within"] = {"within": own_within, "cells": own_cells}
    hyp = doc["hypotheses"]
    for n, t in pub["tables"].items():
        rows = main_run[n]
        hyp.setdefault("rom_bias_ln", {})[n] = _rom_bias(t["rows"], rows, "bias_ln")
        hyp.setdefault("rom_bias_rm1", {})[n] = _rom_bias(t["rows"], rows, "bias_rm1")
        hyp.setdefault("rom_bias_ratio", {})[n] = _rom_bias(t["rows"], rows, "bias")
        hyp.setdefault("i2_mean_of_replicates", {})[n] = score(t["rows"], rows, cols=["i2"], i2_key="i2_mean")
        hyp.setdefault("i2_median_of_replicates", {})[n] = score(t["rows"], rows, cols=["i2"], i2_key="i2_median")
        hyp.setdefault("i2_from_mean_q", {})[n] = score(t["rows"], rows, cols=["i2"])
    for name, v in sim["variants"].items():
        for n in v["tables"]:
            prows = pub["tables"][n]["rows"]
            same = _tau05(prows, main_run[n]) if name.startswith("het_") else score(prows, main_run[n])
            hyp.setdefault(name, {})[n] = {**score(prows, v["runs"][n]), "main_run": same}
    json.dump(doc, open(out, "w"), indent=1)
    open(out, "a").write("\n")
    if csv_out:
        import csv
        with open(csv_out, "w", newline="") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(["table", "effect", "n", "k", "quantity", "tau", "measure", "paper", "ours", "tolerance", "within",
                        "rounds_to_printed", "second_run"])
            for n, t in doc["tables"].items():
                for prow, block in zip(pub["tables"][n]["rows"], [t["fields"][i:i + 21] for i in range(0, len(t["fields"]), 21)]):
                    for col, fl in zip(prow["cells"], block):
                        q, tau, m = col.split("|")
                        w.writerow([n, prow["effect"], prow["n"], prow["k"], q, tau, m, fl["expected"], fl["observed"],
                                    fl["tolerance"]["abs"], abs(fl["observed"] - float(fl["expected"])) <= fl["tolerance"]["abs"],
                                    fl["rounds_to_printed"], fl["second_run"]])
    tot = sum(d["summary"]["within"] for d in doc["tables"].values())
    print(f"{out}: {tot} of {sum(d['summary']['fields'] for d in doc['tables'].values())} cells within tolerance", file=sys.stderr)


def _rom_only(pub_rows, sim_rows):
    return _filter_score(pub_rows, sim_rows, lambda col: col.endswith("|RoM"))


def _rom_bias(pub_rows, sim_rows, key):
    return _filter_score(pub_rows, sim_rows, lambda col: col.startswith("bias|") and col.endswith("|RoM"), bias_key=key)


def _tau05(pub_rows, sim_rows):
    return _filter_score(pub_rows, sim_rows, lambda col: col.split("|")[1] == "0.5")


def _filter_score(pub_rows, sim_rows, keep, **kw):
    pr = [{**r, "cells": {c: v for c, v in r["cells"].items() if keep(c)}} for r in pub_rows]
    return score(pr, sim_rows, **kw)


if __name__ == "__main__":
    main()
