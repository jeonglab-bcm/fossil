#!/usr/bin/env python3
"""Compare the run with the paper and with the committed results; write report.md.

Usage: check_reproduction.py RUN_DIR COMMITTED_DIR OUT_DIR

RUN_DIR holds this run's go_universe.json, targets_vs_s3.csv, table1.csv, s1_check.json,
table2.csv, axonogenesis.json and compare/figure-1-*/report.json. COMMITTED_DIR is
figure-reproduction/output.

Exit status 1 when a claim that must hold fails:
  * the GO universe equals the paper's: 15,733 human genes, S1's 9,462 terms with equal sizes;
  * S1's 9,462 hypergeometric P-values are reproduced (floor of the empirical mean), and so are
    Table 1's ten values at the printed precision;
  * our miRanda target sets agree with S3: no gene outside S3, and at least 99.8% of S3's
    study-gene pairs;
  * the run equals the committed results (target counts, Table 1, Table 2, S5 check).
Everything else is reported.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


def read(path: Path) -> list[dict]:
    with open(path) as fh:
        return list(csv.DictReader(fh))


def main():
    run, committed, out = map(Path, sys.argv[1:4])
    out.mkdir(parents=True, exist_ok=True)
    fails, lines, rows = [], [], []

    def must(ok, what):
        if not ok:
            fails.append(what)
        return ok

    def row(item, quantity, paper, ours, match, note=""):
        rows.append({"item": item, "quantity": quantity, "paper": paper, "ours": ours,
                     "match": int(bool(match)), "note": note})

    go = json.loads((run / "go_universe.json").read_text())
    must(go["human_genes"] == 15733, "human universe is not 15,733 genes")
    must(go["s1_term_sizes_equal"] == go["s1_terms"] == 9462, "S1 term sizes differ")
    row("GO universe", "human genes", 15733, go["human_genes"], go["human_genes"] == 15733)
    row("GO universe", "S1 terms with equal size", 9462, go["s1_term_sizes_equal"], go["s1_term_sizes_equal"] == 9462)
    row("GO universe", "ion transport (GO:0006811) size", 327, go["ion_transport_size"], go["ion_transport_size"] == 327)

    s1 = json.loads((run / "s1_check.json").read_text())
    must(s1["s1_p_agree_rel_1e-9"]["floor"] == 9462, "S1 P-values not reproduced")
    must(s1["table1_rows_equal_at_3_digits_from_s1"] == 10, "Table 1 not reproduced from S1")
    row("S1", "P-values equal (floor of mean)", 9462, s1["s1_p_agree_rel_1e-9"]["floor"], s1["s1_p_agree_rel_1e-9"]["floor"] == 9462)
    row("S1", "P-values equal (rounded mean)", "", s1["s1_p_agree_rel_1e-9"]["round"], False, "the caption's rule")
    row("Table 1", "rows equal at 3 digits, from S1 means", 10, s1["table1_rows_equal_at_3_digits_from_s1"],
        s1["table1_rows_equal_at_3_digits_from_s1"] == 10)
    row("Table 1", "paper's top 10 in our top 10 (our null)", 10, s1["table1_terms_in_our_top10"],
        s1["table1_terms_in_our_top10"] == 10)
    row("Table 1", "paper's top 10 in our top 20 (our null)", 10, s1["table1_terms_in_our_top20"],
        s1["table1_terms_in_our_top20"] == 10)
    ion = s1["ion_transport"]
    row("Fig. 1", "ion transport mean targets, 39 random miRNAs", round(ion["paper_mean"], 2), round(ion["our_mean"], 2),
        abs(ion["our_mean"] - ion["paper_mean"]) < 2.5, "Section 3.1 text: 250")
    row("Fig. 1", "hypergeometric P of the mean", f"{ion['paper_p']:.2e}", f"{ion['our_p']:.2e}",
        f"{ion['paper_p']:.2e}" == f"{ion['our_p']:.2e}", "text: 5.97e-07")
    row("S1", "Pearson r of empirical means, ours vs S1", 1, s1["mean_targets_pearson_r"], s1["mean_targets_pearson_r"] > 0.999)

    tg = read(run / "targets_vs_s3.csv")
    s3 = sum(int(r["s3_targets"]) for r in tg)
    both = sum(int(r["both"]) for r in tg)
    extra = sum(int(r["only_ours"]) for r in tg)
    must(extra == 0, "target genes outside S3")
    must(both >= 0.998 * s3, "fewer than 99.8% of S3's study-gene pairs")
    row("S3", "study-gene target pairs found", s3, both, both >= 0.998 * s3, f"{both / s3:.4%}")
    row("S3", "target genes not in S3", 0, extra, extra == 0)
    exact = sum(1 for r in tg if r["only_s3"] == "0" and r["only_ours"] == "0")
    row("S3", "lists with identical target sets", 29, exact, exact == 29)
    sok = next(r for r in tg if r["study"] == "Sokolov")
    row("S3", "Sokolov targets (n of Section 3.1)", 10057, sok["our_targets"], sok["our_targets"] == "10057")

    t2 = read(run / "table2.csv")
    for alg, pcol, ocol in (("basic", "paper_basic", "ours_basic"), ("multi-hit", "paper_multi_hit", "ours_multi_hit")):
        for sp, n in (("Human", 22), ("Mouse", 7)):
            sub = [r for r in t2 if r["species"] == sp]
            p_any = sum(1 for r in sub if int(r[pcol]) > 0)
            o_any = sum(1 for r in sub if int(r[ocol]) > 0)
            row("Table 2", f"{sp} lists with any significant term, {alg}", f"{p_any} of {n}", f"{o_any} of {n}", p_any == o_any)
        same_zero = sum(1 for r in t2 if (int(r[pcol]) > 0) == (int(r[ocol]) > 0))
        row("Table 2", f"lists with the same zero/non-zero call, {alg}", 29, same_zero, same_zero == 29)
        for r in t2:
            if int(r[pcol]) > 0 or int(r[ocol]) > 0:
                p, o = int(r[pcol]), int(r[ocol])
                row("Table 2", f"{r['study']} ({r['mirnas']} miRNAs), {alg}", p, o, p == o,
                    f"{(o - p) / p:+.1%}" if p else "")

    ax = json.loads((run / "axonogenesis.json").read_text())
    row("S5", "target genes of the 8 miRNAs", ax["s5_target_genes"], ax["our_target_genes"],
        ax["s5_target_genes"] == ax["our_target_genes"])
    row("S5", "significant terms (BH 0.05)", ax["s5_significant"], ax["our_significant"],
        ax["s5_significant"] == ax["our_significant"])
    row("S5", "significant in both", ax["s5_significant"], ax["significant_in_both"], False)
    row("S5", "regulation of axonogenesis significant", ax["axonogenesis_significant_s5"],
        ax["axonogenesis_significant_ours"], ax["axonogenesis_significant_s5"] == ax["axonogenesis_significant_ours"])

    for k in ("published-values", "ours"):
        rep = json.loads((run / "compare" / f"figure-1-{k}" / "report.json").read_text())
        row("Fig. 1 drawing", f"chamfer distance, all ink (px), {k}", 0, rep["chamfer_all_px"], rep["chamfer_all_px"] < 1)
        row("Fig. 1 drawing", f"pixels within 24 grey levels (%), {k}", 100, rep["pixels_within_24_pct"], rep["pixels_within_24_pct"] > 95)

    # The run against the committed results.
    cmp_files = ["targets_vs_s3.csv", "table1.csv", "table2.csv", "axonogenesis.json"]
    for f in cmp_files:
        c = committed / f
        if c.exists():
            must(c.read_text() == (run / f).read_text(), f"{f} differs from the committed run")
        else:
            lines.append(f"- No committed {f} to compare with.")

    with open(out / "results_table.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["item", "quantity", "paper", "ours", "match", "note"], lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    md = ["# PMC4426843 reproduction check", "",
          "| Item | Quantity | Paper | Ours | Match | Note |", "| --- | --- | --- | --- | --- | --- |"]
    md += [f"| {r['item']} | {r['quantity']} | {r['paper']} | {r['ours']} | {'yes' if r['match'] else 'no'} | {r['note']} |"
           for r in rows]
    md += ["", "## Claims that must hold", ""]
    md += [f"- FAIL: {f}" for f in fails] or ["- All hold."]
    md += lines
    (out / "report.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
