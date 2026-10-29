"""Check the reproduction against required matches and write report.md (exit 1 on failure).

Pixel checks: per panel, the share of published pixels within 4 px of ours and of ours within
4 px of the published ones, for the colour classes named below. Number checks: the port, the
tables, Fig. 5C weights and Fig. 6 statistics at the paper's printed precision.
"""

import argparse
import json
import os
import re
import sys

# (figure, panel regex, colour key, min published share, min our share)
PIXEL_RULES = [
    ("fig2", r"^B$", "all_traces", 0.95, 0.95),
    ("fig2", r"^E$", "all_traces", 0.95, 0.85),   # dashed means: 500 random cells in the original
    ("fig2", r"^[BE]$", "(0.0, 0.0, 0.0)", 0.95, 0.95),
    ("fig2", r"^[CF]:", "all_traces", 0.95, 0.95),
    ("fig2", r"^[CF]:", "(0.7, 0.7, 0.7)", 0.9, 0.95),
    ("fig2", r"^[DG]:k\d_density", "all_traces", 0.95, 0.95),
    ("fig2", r"^[DG]:w1_density", "(0.0, 0.0, 0.0)", 0.95, 0.95),
    ("fig2", r"^[DG]:.*_estimate", "(0.0, 0.0, 0.0)", 0.95, 0.9),
    ("fig3", r"^B:", "all_traces", 0.95, 0.95),
    ("fig4", r"^B:", "all_traces", 0.8, 0.95),    # coloured "w = ..%" labels partly inside
    ("fig[34]", r"^B:", "(0.0, 0.0, 0.0)", 0.95, 0.95),
    ("fig[34]", r"^C:", "all_traces", 0.85, 0.95),
    ("fig[34]", r"^C:", "(0.7, 0.7, 0.7)", 0.8, 0.95),
    ("fig[34]", r"^D:", "(0.0, 0.0, 0.0)", 0.9, 0.9),
    ("fig5", r"^B$", "all_traces", 0.95, 0.95),
    ("fig5", r"^B$", "(0.0, 0.0, 0.0)", 0.95, 0.95),
    ("fig6", r":scatter$", "(0.0, 0.0, 0.0)", 0.95, 0.95),
    ("fig6", r"^B:scatter$", "all_traces", 0.95, 0.95),
    ("fig6", r"^A:.*_hist$", "(0.7, 0.7, 0.7)", 0.95, 0.95),
    ("fig6", r"^B:.*_hist$", "all_traces", 0.95, 0.95),
]

# Printed table values that disagree with the authors' own saved results (paper errors).
TABLE_EXCEPTIONS = {("table1_cr1", "H3,1", "logL"),     # 0.99105 printed 0.9911
                    ("table1_cr2", "H1,1", "rank"),     # ranks 12/10/11 contradict the
                    ("table1_cr2", "H1,2", "rank"),     # printed BICs, which give 10/11/12
                    ("table1_cr2", "H1,3", "rank")}


def pixel_checks(comp, label):
    rows, ok = [], True
    for fig, panels in comp.items():
        for name, v in panels.items():
            if not isinstance(v, dict) or "colours" not in v:
                continue
            if label == "refit" and name.endswith("_estimate"):
                continue   # no profile likelihoods for the refit: only the optimum is drawn
            for f_re, p_re, key, a, b in PIXEL_RULES:
                if not re.fullmatch(f_re, fig) or not re.search(p_re, name):
                    continue
                m = v["colours"].get(key)
                if m is None or m.get("published_matched") is None:
                    good, pm, om = False, None, None
                else:
                    pm, om = m["published_matched"], m["ours_matched"]
                    good = pm >= a and om >= b
                ok &= good
                rows.append((label, fig, name, key, pm, om, a, b, good))
    return rows, ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True, help="folder with the json outputs")
    a = ap.parse_args()
    D = a.dir
    lines = ["# PMC4081021 reproduction check", ""]
    ok_all = True

    port = json.load(open(os.path.join(D, "port_check.json")))
    good = port["max_abs_diff_logL"] < 1e-2
    ok_all &= good
    lines += ["## Likelihood port", "",
              f"Python log-likelihood at the authors' 51 saved optima: max |difference| "
              f"{port['max_abs_diff_logL']:.1e} (required < 1e-2): {'PASS' if good else 'FAIL'}", ""]

    tables = json.load(open(os.path.join(D, "tables.json")))
    lines += ["## Tables", "", "| Table | Fit | Rows | Fields matching | Exceptions (paper errors) |",
              "| --- | --- | --- | --- | --- |"]
    for k, v in tables.items():
        for kind in ("saved", "refit"):
            if kind not in v["comparison"][0]:
                continue
            n, bad, exc = 0, [], []
            for c in v["comparison"]:
                for f, m in c[kind]["matches"].items():
                    n += 1
                    if not m:
                        (exc if (k, c["model"], f) in TABLE_EXCEPTIONS else bad).append(f"{c['model']} {f}")
            ok_all &= not bad
            lines.append(f"| {k} | {kind} | {len(v['comparison'])} | {n - len(bad) - len(exc)}/{n}"
                         f"{' FAIL: ' + ', '.join(bad) if bad else ''} | {', '.join(exc) or '-'} |")
    lines.append("")

    comp = json.load(open(os.path.join(D, "comparison.json")))
    rows, ok = pixel_checks(comp, "saved")
    if os.path.exists(os.path.join(D, "comparison_refit.json")):
        r2, ok2 = pixel_checks(json.load(open(os.path.join(D, "comparison_refit.json"))), "refit")
        rows += r2
        ok &= ok2
    ok_all &= ok
    lines += ["## Figures (pixels within 4 px)", "",
              "| Fit | Figure | Panel | Colour | Published matched | Ours matched | Required | |",
              "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for lab, fig, name, key, pm, om, a_, b_, good in rows:
        fmt = lambda x: "-" if x is None else f"{x:.3f}"   # noqa: E731
        lines.append(f"| {lab} | {fig} | {name} | {key} | {fmt(pm)} | {fmt(om)} | {a_} / {b_} | "
                     f"{'PASS' if good else 'FAIL'} |")
    lines.append("")

    f5 = comp["fig5"]
    f6 = comp["fig6"]
    w = f5["C_w1_percent"]
    good5 = w[0] == 68.8 and w[2] == 70.0
    good6 = (f"{f6['rho_control']:.3f}" == "0.895" and f"{f6['rho_stimulated']:.3f}" == "0.696"
             and [round(x, 1) for x in f6["w_percent"]] == [68.0, 32.0])
    ok_all &= good5 and good6
    lines += ["## Numbers", "",
              f"- Fig. 5C, w1 of M_H3,3 (A, B, C): {w} % against published [68.8, 71.5, 70.0] %. "
              f"A and C must match: {'PASS' if good5 else 'FAIL'}. B does not match any saved fit "
              "of pathway model B (M_H3,3 gives 69.8 %).",
              f"- Fig. 6: rho {f6['rho_control']:.3f} and {f6['rho_stimulated']:.3f}, mixture weights "
              f"{f6['w_percent']} % (published 0.895, 0.696, 68.0 / 32.0 %): {'PASS' if good6 else 'FAIL'}", ""]

    if os.path.exists(os.path.join(D, "optima_check.json")):
        oc = json.load(open(os.path.join(D, "optima_check.json")))
        fin = [r for r in oc if r["local_gain"] != float("inf")]
        lines += ["## Saved optima", "",
                  f"{len(fin)} of {len(oc)} saved optima checked with exact gradients; the largest "
                  f"gain of a local L-BFGS-B run started at a saved optimum is "
                  f"{max(r['local_gain'] for r in fin):.1e} in log-likelihood.", ""]

    lines.append(f"**Overall: {'PASS' if ok_all else 'FAIL'}**")
    print("\n".join(lines))
    sys.exit(0 if ok_all else 1)


if __name__ == "__main__":
    main()
