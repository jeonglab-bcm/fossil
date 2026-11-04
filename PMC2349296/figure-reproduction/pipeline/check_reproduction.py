#!/usr/bin/env python3
"""Compare the run with the paper and with the committed results; write report.md.

Usage: check_reproduction.py RUN_DIR COMMITTED_DIR PUBLISHED_TABLES.csv OUT_DIR

RUN_DIR holds this run's cooccurrence.csv, table3.csv, tokens_medpost.csv, relex.csv,
claims.csv, claims_verdicts.csv, claims_by_corpus.csv, corpus_counts.csv and
compare/figure-N/report.json. COMMITTED_DIR holds the same
files from the committed run (figure-reproduction/output).

Exit status 1 when a claim that must hold fails:
  * co-occurrence P/R/F (Tables 2, 4) and the Table 3 statistics equal the paper at the printed
    precision on HPRD50, IEPA and LLL, whose unified versions match the paper's;
  * MedPost token counts equal Table 3 on all five corpora;
  * the summary statistics computed from the published tables equal the paper's text, and every
    claim holds on the published tables;
  * the run equals the committed results (RelEx counts, co-occurrence counts, claims, the claim
    verdicts of our run).
Everything else is reported.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

CORPORA = ["AIMed", "BioInfer", "HPRD50", "IEPA", "LLL"]
MATCHING = {"HPRD50", "IEPA", "LLL"}


def read(path: Path) -> list[dict]:
    with open(path) as fh:
        return list(csv.DictReader(fh))


def ours_values(run: Path) -> dict[tuple[str, str, str], float]:
    v = {}
    for r in read(run / "cooccurrence.csv"):
        t = "T2" if r["variant"] == "unfiltered" else "T4"
        for q in ("P", "R", "F"):
            v[(t, r["corpus"], f"cooc_{q}")] = float(r[q])
    for r in read(run / "relex.csv"):
        t = "T2" if r["variant"] == "unfiltered" else "T4"
        for q in ("P", "R", "F"):
            v[(t, r["corpus"], f"relex_{q}")] = float(r[q])
    tok = {r["corpus"]: float(r["tokens_medpost"]) for r in read(run / "tokens_medpost.csv")}
    for r in read(run / "table3.csv"):
        c = r["corpus"]
        v[("T3", c, "tokens")] = tok[c]
        for q in ("entities", "entity_pairs", "interactions", "no_entities", "no_interactions"):
            v[("T3", c, q)] = float(r[q])
    return v


def fmt(x: float, d: int) -> str:
    return f"{x:.{d}f}"


def main():
    run, committed, pub_path, out = map(Path, sys.argv[1:5])
    out.mkdir(parents=True, exist_ok=True)
    pub = read(pub_path)
    ours = ours_values(run)
    failures, rows = [], []
    for p in pub:
        key = (p["table"], p["corpus"], p["quantity"])
        d = int(p["digits"])
        val = ours[key]
        same = fmt(val, d) == fmt(float(p["value"]), d)
        rows.append({"table": key[0], "corpus": key[1], "quantity": key[2], "published": p["value"],
                     "ours": round(val, 4), "ours_rounded": fmt(val, d), "match": int(same)})
        method = key[2].split("_")[0]
        must = key[1] in MATCHING and (key[0] == "T3" or method == "cooc")
        must |= key[0] == "T3" and key[2] == "tokens"
        if must and not same:
            failures.append(f"{key}: published {p['value']}, ours {fmt(val, d)}")
    with open(out / "results_table.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    claims = {r["statistic"]: r for r in read(run / "claims.csv")}
    exp = {"method_gap_pts": (13, 0), "relex_pairwise_pts": (19, 0), "relex_pairwise_filtered_pts": (11, 0),
           "error_reduction_min_pct": (21, 0), "error_reduction_max_pct": (32, 0), "kendall_IEP_p": (0.08, 2)}
    for k, (v, d) in exp.items():
        got = float(claims[k]["published_tables"])
        if fmt(got, d) != fmt(v, d):
            failures.append(f"claim {k} from the published tables: {got:.4f}, paper {v}")

    verdicts = read(run / "claims_verdicts.csv")
    for r in verdicts:
        if r["verdict_published_tables"] != "holds":
            failures.append(f"claim {r['claim_id']} does not hold on the published tables")

    # regression against the committed run
    for name, keys in (("relex.csv", ("corpus", "variant", "tp", "fp", "fn")),
                       ("cooccurrence.csv", ("corpus", "variant", "tp", "fp", "fn", "EP")),
                       ("corpus_counts.csv", None), ("tokens_medpost.csv", None)):
        a, b = read(run / name), read(committed / name)
        if keys:
            a = [{k: r[k] for k in keys} for r in a]
            b = [{k: r[k] for k in keys} for r in b]
        if a != b:
            failures.append(f"{name} differs from the committed results")
    a = {r["statistic"]: round(float(r["ours"]), 6) for r in read(run / "claims.csv")}
    b = {r["statistic"]: round(float(r["ours"]), 6) for r in read(committed / "claims.csv")}
    if a != b:
        failures.append("claims.csv differs from the committed results")
    a = {r["claim_id"]: r["verdict"] for r in verdicts}
    b = {r["claim_id"]: r["verdict"] for r in read(committed / "claims_verdicts.csv")}
    if a != b:
        failures.append("claim verdicts differ from the committed results: "
                        + ", ".join(f"{k} {b.get(k)} -> {a.get(k)}" for k in sorted(set(a) | set(b)) if a.get(k) != b.get(k)))

    # report
    def count(table, method=None, corpora=CORPORA):
        sel = [r for r in rows if r["table"] == table and r["corpus"] in corpora
               and (method is None or r["quantity"].startswith(method))]
        return f"{sum(r['match'] for r in sel)} of {len(sel)}"

    lines = ["# PMC2349296 reproduction check", ""]
    lines += ["**Result: " + ("all must-hold checks pass**" if not failures else
                              f"{len(failures)} must-hold checks fail**"), ""]
    for f in failures:
        lines.append(f"- FAIL: {f}")
    lines += ["", "## Agreement at the published precision", "",
              "| Item | All five corpora | HPRD50, IEPA, LLL |", "| --- | --- | --- |"]
    for label, t, m in (("Table 2, co-occurrence", "T2", "cooc"), ("Table 2, RelEx", "T2", "relex"),
                        ("Table 3", "T3", None), ("Table 4, co-occurrence", "T4", "cooc"),
                        ("Table 4, RelEx", "T4", "relex")):
        lines.append(f"| {label} | {count(t, m)} | {count(t, m, MATCHING)} |")
    lines += ["", "## Tables (published / ours)", ""]
    for t, title in (("T2", "Table 2"), ("T3", "Table 3"), ("T4", "Table 4")):
        qs = list(dict.fromkeys(r["quantity"] for r in rows if r["table"] == t))
        lines += [f"### {title}", "", "| Corpus | " + " | ".join(qs) + " |", "| --- |" + " --- |" * len(qs)]
        for c in CORPORA:
            cells = []
            for q in qs:
                r = next(r for r in rows if r["table"] == t and r["corpus"] == c and r["quantity"] == q)
                mark = "" if r["match"] else " ≠"
                cells.append(f"{r['published']} / {r['ours_rounded']}{mark}")
            lines.append(f"| {c} | " + " | ".join(cells) + " |")
        lines.append("")
    tally = {v: sum(r["verdict"] == v for r in verdicts) for v in ("holds", "close", "differs")}
    lines += ["## Claims in the text", "",
              f"Our run is the reproduction; the verdict reads only that column: {tally['holds']} of {len(verdicts)} "
              f"claims hold, {tally['close']} close, {tally['differs']} differ. *Paper's tables* runs the same code on "
              "the paper's own Tables 2 and 4: it checks that we compute each number the way the paper did, not that "
              "our run agrees. *Paper's BioInfer row* is our run with BioInfer's numbers replaced by the paper's: a "
              "sensitivity check that moves toward the paper by construction.", "",
              "| Claim | Paper | Ours | Verdict | Paper's tables | Paper's BioInfer row |",
              "| --- | --- | --- | --- | --- | --- |"]
    for r in verdicts:
        lines.append(f"| {r['claim']} | {r['paper']} | {r['ours']} | {r['verdict']} | {r['published_tables']} | "
                     f"{r['ours_with_published_BioInfer']} |")
    lines += ["", "Rule: a yes/no claim holds if true; \"not significant\" holds if p >= 0.05; a number holds if it "
              "rounds to the paper's value, is close if within 10% of it, and differs otherwise.", "",
              "### Per corpus", "",
              "| Corpus | Our copy of the corpus | Error cut, paper's tables | Ours | RelEx F, paper | Ours |",
              "| --- | --- | --- | --- | --- | --- |"]
    for r in read(run / "claims_by_corpus.csv"):
        lines.append(f"| {r['corpus']} | {r['corpus_version']} | {float(r['error_reduction_pct_published']):.1f}% | "
                     f"{float(r['error_reduction_pct_ours']):.1f}% | {float(r['relex_F_published']):.2f} | "
                     f"{float(r['relex_F_ours']):.2f} |")
    lines += ["", "### All statistics", "",
              "| Statistic | Paper text | From published tables | Ours | Ours with the paper's BioInfer row |",
              "| --- | --- | --- | --- | --- |"]
    for k, r in claims.items():
        lines.append(f"| {k} | {r['paper_text'] or ''} | {float(r['published_tables']):.3g} | "
                     f"{float(r['ours']):.3g} | {float(r['ours_with_published_BioInfer']):.3g} |")
    lines += ["", "## Figures", "", "| Figure | Render | Mean abs. grey diff. | Pixels within ±24 | Chamfer (px) | Global shift |",
              "| --- | --- | --- | --- | --- | --- |"]
    for i in (1, 2):
        for kind in ("ours", "published-values"):
            p = run / "compare" / f"figure-{i}-{kind}" / "report.json"
            if p.exists():
                rep = json.loads(p.read_text())
                gs = rep["global_shift"]
                lines.append(f"| {i} | {kind} | {rep['mean_abs_grey_difference']} | {rep['pixels_within_24_pct']}% | "
                             f"{rep['chamfer_all_px']} | {gs['dx']}, {gs['dy']} |")
    (out / "report.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
