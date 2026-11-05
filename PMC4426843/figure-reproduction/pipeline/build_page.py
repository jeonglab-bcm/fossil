#!/usr/bin/env python3
"""Build the comparison page for PMC4426843 from the pipeline outputs.

Usage: build_page.py RUN_DIR FIGS_DIR COMPARE_DIR PUBLISHED_DIR OUT.html
RUN_DIR holds results_table.csv, table1.csv, table2.csv, targets_vs_s3.csv, s1_check.json,
go_universe.json and axonogenesis.json. FIGS_DIR holds ours-figure-1.png and
published-values-figure-1.png; COMPARE_DIR holds figure-1-{ours,published-values}/report.json.
The page links ../results.css, the stylesheet the site's results pages share; images are embedded.
"""

from __future__ import annotations

import base64
import csv
import html
import io
import json
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
RUN, FIGS, CMP, PUB, OUT = map(Path, sys.argv[1:6])
esc = html.escape


def read(p):
    with open(p) as fh:
        return list(csv.DictReader(fh))


def js(name):
    return json.loads((RUN / name).read_text())


t1 = read(RUN / "table1.csv")
t2 = read(RUN / "table2.csv")
tg = read(RUN / "targets_vs_s3.csv")
s1 = js("s1_check.json")
go = js("go_universe.json")
ax = js("axonogenesis.json")
# Table 2's multi-hit column under several readings (run_multihit_readings.sh, issue #33): a
# committed side analysis, not a pipeline output, so it is read from output/.
mh_path = RUN / "multihit_readings.csv"
mh = read(mh_path if mh_path.exists() else HERE.parent / "output" / "multihit_readings.csv")


def b64(path: Path) -> str:
    buf = io.BytesIO()
    Image.open(path).convert("RGB").save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


VCLASS = {"Agrees": "agrees", "Partly agrees": "partly", "Differs": "differs"}


def stamp(verdict, basis):
    return f'<span class="stamp" data-v="{VCLASS[verdict]}">{esc(verdict)}<small>{esc(basis)}</small></span>'


def dose(items):
    return "".join(f"<div><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>" for k, v in items)


def plate(label, src, alt, w, h):
    return (f'<figure class="plate"><figcaption>{esc(label)}</figcaption>'
            f'<img src="{src}" alt="{esc(alt)}" width="{w}" height="{h}"></figure>')


def fig_stats(kind):
    rep = json.loads((CMP / f"figure-1-{kind}" / "report.json").read_text())
    w, h = rep["size_px"]
    return rep, [("Pixel size", f"{w} × {h}"),
                 ("Mean |Δ| grey", f"{rep['mean_abs_grey_difference']:g}"),
                 ("Pixels within ±24", f"{rep['pixels_within_24_pct']:g}%"),
                 ("Ink distance (chamfer)", f"{rep['chamfer_all_px']:g} px"),
                 ("Best global shift", f"{rep['global_shift']['dx']}, {rep['global_shift']['dy']} px")]


def n(x):
    return f"{int(x):,}"


ion = s1["ion_transport"]
s3_total = sum(int(r["s3_targets"]) for r in tg)
s3_both = sum(int(r["both"]) for r in tg)
s3_extra = sum(int(r["only_ours"]) for r in tg)
identical = [r["study"] for r in tg if r["only_s3"] == "0" and r["only_ours"] == "0"]
sok = next(r for r in tg if r["study"] == "Sokolov")


def any_sig(sp, col):
    return sum(1 for r in t2 if r["species"] == sp and int(r[col]) > 0)


hum_p, hum_o = any_sig("Human", "paper_basic"), any_sig("Human", "ours_basic")
mou_p, mou_o = any_sig("Mouse", "paper_basic"), any_sig("Mouse", "ours_basic")
calls_b = sum(1 for r in t2 if (int(r["paper_basic"]) > 0) == (int(r["ours_basic"]) > 0))
calls_m = sum(1 for r in t2 if (int(r["paper_multi_hit"]) > 0) == (int(r["ours_multi_hit"]) > 0))
big = [r for r in t2 if int(r["paper_basic"]) > 0]
big_dev = max(abs(int(r["ours_basic"]) - int(r["paper_basic"])) / int(r["paper_basic"]) for r in big)
t1_top10 = s1["table1_terms_in_our_top10"]
t1_same_p = sum(1 for r in t1 if f"{float(r['our_p']):.2e}" == f"{float(r['paper_p']):.2e}")

LEDE = (f"A test that called random miRNA lists enriched, and a fix that called almost nothing enriched. "
        f"We regenerated the paper’s miRanda predictions and rebuilt its empirical test. "
        f"{s3_both / s3_total:.2%} of the paper’s published target lists come back, Figure 1 lands on the published bars, "
        f"and after correction {hum_o} of 22 human and {mou_o} of 7 mouse lists have an enriched term "
        f"(paper: {hum_p} and {mou_p}).")

LABEL = "".join(
    f'<a class="label-row" href="#{a}"><span>{esc(k)}</span><span>{esc(v)}</span></a>'
    for a, k, v in [
        ("fig-1", "Fig. 1", "Same setup"),
        ("tables", "Table 1", f"S1 exact; ours {t1_top10} of 10"),
        ("tables", "Table 2, basic", f"{calls_b} of 29 calls"),
        ("tables", "Table 2, multi-hit", f"{calls_m} of 29 calls"),
        ("targets", "S3 targets", f"{s3_both / s3_total:.2%}"),
        ("targets", "S5 control", f"{ax['significant_in_both']} of {ax['s5_significant']}"),
    ])

pub_path = PUB / "figure-1.jpg"
w, h = Image.open(pub_path).size
rep_o, st_o = fig_stats("ours")
rep_p, st_p = fig_stats("published-values")
ours_src = b64(FIGS / "ours-figure-1.png")
pv_src = b64(FIGS / "published-values-figure-1.png")
NOTE = (f"Our null: 999,999 draws of 39 random human miRNAs from our miRanda predictions. The empirical mean "
        f"is {ion['our_mean']:.2f} ion-transport genes against the paper’s {ion['paper_mean']:.2f}, and its "
        f"hypergeometric P is {ion['our_p']:.2e} (paper: 5.97e-07). The blue bars are the exact hypergeometric "
        f"distribution with the paper’s N = 15,733, K = 327, n = 10,057.")
VNOTE = ("Paper’s values: the empirical bar heights read off the published figure, drawn by the same code. "
         "What is left here is drawing, not data.")
FIGS_JS = [{"id": "1", "w": w, "h": h, "variants": [
    {"label": "Our run", "ours": ours_src, "note": NOTE, "stats": dose(st_o)},
    {"label": "Paper’s values", "ours": pv_src, "note": VNOTE, "stats": dose(st_p)}]}]
STATIONS = (
    '<section class="station surface" id="fig-1" aria-labelledby="fig-1-head">'
    '<header class="station-head"><h2 id="fig-1-head">Fig. 1</h2><p class="caption">Expected (hypergeometric, blue) and '
    'empirical (red) number of predicted targets in ‘ion transport’ (GO:0006811) for 39 random miRNAs, per 5-gene bin.</p>'
    f'{stamp("Agrees", "Same setup, regenerated predictions")}</header>'
    '<div class="stage"><div class="pair">'
    + plate("Published", b64(pub_path), "Figure 1 as published", w, h)
    + plate("Our run", ours_src, "Figure 1 reproduced", w, h)
    + "</div></div>"
    f'<div class="station-foot"><dl class="dose">{dose(st_o)}</dl><p class="note">{esc(NOTE)}</p></div></section>')

t1_body = "".join(
    f"<tr><td>{esc(r['go_id'])} {esc(r['go_name'])}</td><td class=num>{esc(r['paper_p'])}</td>"
    f"<td class=num>{float(r['s1_p_floor']):.2e}</td><td class=num><strong>{float(r['our_p']):.2e}</strong></td>"
    f"<td class=num>{r['our_rank']}</td></tr>" for r in t1)


def t2cell(p, o):
    cls = "num" if p == o else "num off"
    return f'<td class="{cls}">{n(p)} / <strong>{n(o)}</strong>{"" if p == o else " ≠"}</td>'


t2_body = "".join(
    f"<tr><td>{esc(r['reference'])}</td><td>{esc(r['species'])}</td><td class=num>{r['mirnas']}</td>"
    + t2cell(r["paper_basic"], r["ours_basic"]) + t2cell(r["paper_multi_hit"], r["ours_multi_hit"]) + "</tr>"
    for r in t2)
tg_body = "".join(
    f"<tr><td>{esc(r['study'])}</td><td>{esc(r['species'])}</td><td class=num>{r['mirnas']}</td>"
    f"<td class=num>{n(r['s3_targets'])}</td><td class=num><strong>{n(r['our_targets'])}</strong></td>"
    f"<td class=num>{r['only_s3']}</td><td class=num>{r['only_ours']}</td></tr>" for r in tg)

EXTRA = f"""<section class="container after-bench" aria-labelledby="tables-head">
  <div class="station surface" id="tables">
    <header class="station-head"><h2 id="tables-head">Tables 1 and 2</h2><p class="caption">Table 1: hypergeometric P of the mean of the empirical distribution, for the ten most biased terms. Table 2: GO terms significant after Benjamini–Hochberg correction (FDR &lt; 0.05), published / ours.</p>{stamp("Partly agrees", f"Basic {calls_b} of 29, multi-hit {calls_m} of 29 calls")}</header>
    <div class="table-wrap"><table class="record dense"><caption>Table 1 (paper; recomputed from the paper’s S1 means; ours from our null; our rank)</caption><thead><tr><th scope="col">GO term</th><th scope="col" class=num>Paper</th><th scope="col" class=num>From S1</th><th scope="col" class=num>Ours</th><th scope="col" class=num>Our rank</th></tr></thead><tbody>{t1_body}</tbody></table></div>
    <p class="note">All {s1['s1_terms']:,} P-values of Supplementary Table S1 come back to 1e-9 when the mean is truncated, not rounded as the caption says ({s1['s1_p_agree_rel_1e-9']['round']:,} with rounding). Our own null puts the paper’s ten terms at ranks 1 to 10; {t1_same_p} of the ten P-values are identical because the truncated means agree.</p>
    <div class="table-wrap"><table class="record dense"><caption>Table 2. Significant GO terms (published / ours)</caption><thead><tr><th scope="col">Study</th><th scope="col">Species</th><th scope="col" class=num>miRNAs</th><th scope="col" class=num>Basic</th><th scope="col" class=num>Multi-hit</th></tr></thead><tbody>{t2_body}</tbody></table></div>
    <p class="note">Basic algorithm: the five large lists come back within {big_dev:.1%} of the paper’s counts, and {calls_b} of 29 lists get the same zero or non-zero call. Lists with any significant term: {hum_o} of 22 human (paper {hum_p}) and {mou_o} of 7 mouse (paper {mou_p}). The multi-hit algorithm agrees on {calls_m} of 29 calls; its counts are not reproducible from the Methods (see the next section).</p>
  </div>
  <div class="station surface" id="targets">
    <header class="station-head"><h2>Supplementary Tables S3 and S5</h2><p class="caption">S3: the miRanda target genes of each published list (genes with a biological-process term). S5: the positive control, eight miRNAs tested together.</p>{stamp("Agrees", f"{s3_both / s3_total:.2%} of S3’s targets; no extra gene")}</header>
    <div class="table-wrap"><table class="record dense"><caption>Target genes per list (S3 / ours; genes only in S3; only in ours)</caption><thead><tr><th scope="col">Study</th><th scope="col">Species</th><th scope="col" class=num>miRNAs</th><th scope="col" class=num>S3</th><th scope="col" class=num>Ours</th><th scope="col" class=num>Only S3</th><th scope="col" class=num>Only ours</th></tr></thead><tbody>{tg_body}</tbody></table></div>
    <p class="note">{len(identical)} lists come back gene for gene ({", ".join(identical)}). Over all 29, {n(s3_both)} of S3’s {n(s3_total)} study–gene pairs are ours and {s3_extra} of ours are not in S3. S5: our eight miRNAs target {ax['our_target_genes']:,} genes (S5: {ax['s5_target_genes']:,}); {ax['our_significant']:,} terms are significant against S5’s {ax['s5_significant']:,}, {ax['significant_in_both']:,} in both, and ‘regulation of axonogenesis’ is among them.</p>
  </div>
</section>"""

MH_COLS = [("max", "Reference"), ("seed2", "Other seed"), ("longest", "Longest UTR"), ("sum", "Sum, UTRs"),
           ("sum_tx", "Sum, transcripts"), ("univ", "GO-gene denominator"), ("allpairs", "All pairs")]
mh_rows = [r for r in mh if any(int(r[c] or 0) for c in ["paper_multi_hit"] + [c for c, _ in MH_COLS])]
mh_rows.sort(key=lambda r: (r["species"] != "Human", -int(r["mirnas"])))
mh_body = "".join(
    f"<tr><td>{esc(r['study'])}{'' if r['species'] == 'Human' else ' (mouse)'}</td><td class=num>{r['mirnas']}</td>"
    f"<td class=num>{n(r['paper_multi_hit'])}</td>"
    + "".join(f"<td class=num><strong>{n(r[c])}</strong></td>" if c == "max" else f"<td class=num>{n(r[c])}</td>"
              for c, _ in MH_COLS)
    + f"<td class=num>{n(r['max_fdr0.025'])}–{n(r['max_fdr0.1'])}</td>"
    f"<td class=num>{esc(r['max_fdr_at_paper_count'])}</td></tr>" for r in mh_rows)
mh_head = "".join(f'<th scope="col" class=num>{esc(h)}</th>' for _, h in MH_COLS)
fdr_paper = [float(r["max_fdr_at_paper_count"]) for r in mh if r["max_fdr_at_paper_count"]]
chart = next(r for r in mh if r["study"] == "Chartoumpekis")

MULTI = f"""<section class="container after-bench" aria-labelledby="multi-head">
  <div class="station surface" id="multi-hit">
    <header class="station-head"><h2 id="multi-head">The multi-hit test</h2><p class="caption">Table 2’s second column. Significant GO terms (BH FDR &lt; 0.05) under readings of the method that each change one thing against ours.</p>{stamp("Differs", "Counts not reproducible from the Methods")}</header>
    <p class="note"><strong>What it is.</strong> The basic test counts each target gene once: a gene hit by one site of one miRNA weighs as much as a gene hit by ten miRNAs. The multi-hit test (Section 3.4) scores each gene by its predicted binding sites summed over the list’s miRNAs, and a term by the summed scores of its genes over the total. Both compare the list with 999,999 random lists, so both correct the targeting bias; the multi-hit version puts back convergence, several miRNAs hitting the same genes, to show the corrected test can still find biology.</p>
    <p class="note"><strong>How much rests on it.</strong> Little. The main claim (5 of 22 human and 0 of 7 mouse lists enriched after correction), Figure 1 and Table 1 stand on the basic test. From the multi-hit test the paper takes only a pattern, which our run shows too: lists enriched under the basic test stay enriched with fewer terms, and five of the paper’s six lists that gain terms gain them here (Liu does not).</p>
    <div class="table-wrap"><table class="record dense"><caption>Significant multi-hit terms per list: paper, then our readings; our reference at FDR 0.025–0.1; the FDR at which our ranking gives the paper’s count</caption><thead><tr><th scope="col">List</th><th scope="col" class=num>miRNAs</th><th scope="col" class=num>Paper</th>{mh_head}<th scope="col" class=num>FDR 0.025–0.1</th><th scope="col" class=num>FDR at paper’s count</th></tr></thead><tbody>{mh_body}</tbody></table></div>
    <p class="note"><strong>Why the counts differ.</strong> The paper does not say how sites are counted on a gene with several transcripts, or whether sites on pairs failing the score and energy cut count, and no supplementary table records site counts. The targets feeding both columns agree with S3 to 99.8%, so the gap lies in the site counts. No reading reproduces the paper, and the errors point both ways: seven lists come out too high, three too low. The paper’s counts are not ours at another threshold either: the FDR that would give them runs from {min(fdr_paper):.2g} to {max(fdr_paper):.2g}. Many multi-hit P-values sit near the cut, so the counts are fragile; under another seed Chartoumpekis goes from {chart['max']} to {chart['seed2']}, so its exact match is chance.</p>
    <p class="note"><strong>Comparing counts.</strong> <code>table2.csv</code> gives ours − paper and (ours − paper) / paper. The paper publishes no multi-hit term lists, so the term sets cannot be compared; the readings, the FDR range and the FDR at the paper’s count show how far a count can move.</p>
  </div>
</section>"""

RECOVERED = f"""<section class="notes" aria-labelledby="back-head">
  <div class="container">
    <h2 id="back-head">What came back</h2>
    <dl class="ledger">
      <div class="row"><dt>The GO universe</dt><dd>Ensembl 75’s BioMart tables survive as MySQL dumps. By gene name, direct annotations, all evidence codes, they give the paper’s {go['human_genes']:,} human genes and all {go['s1_term_sizes_equal']:,} of S1’s term sizes.</dd></div>
      <div class="row"><dt>The miRanda thresholds</dt><dd>“Score &gt; 155, energy &lt; −20” is applied to miRanda’s per-UTR totals, inclusive (score ≥ 155, energy ≤ −20), on a run with miRanda’s defaults. Per-site filtering finds a third of S3’s genes; a strict &gt; 155 misses about 3%.</dd></div>
      <div class="row"><dt>The 3′ UTRs</dt><dd>Cut from the Ensembl 75 GTF and genome; they equal BioMart’s 3′ UTRs for all 104,763 coding transcripts. Haplotype and patch sequences need their shared regions copied from the parent chromosome.</dd></div>
      <div class="row"><dt>The empirical P-value</dt><dd>S5’s P-values are counts over 999,999 draws with no pseudo-count, the overlap divides by all target genes (S5’s 1,064 include genes without a GO term), and BH runs over all 9,462 terms.</dd></div>
      <div class="row"><dt>S5’s eight miRNAs</dt><dd>Not the eight with the most targets in the term, as the text says: S5 rules out every miRNA that hits a term it reports as empty, and exactly eight survive.</dd></div>
      <div class="row"><dt>A spreadsheet in the way</dt><dd>S3 lists MARCH1, MARCH5, SEPT7 and SEP15 as dates (36951.0 is 1 March 2001).</dd></div>
    </dl>
  </div>
</section>
<section class="buried" aria-labelledby="buried-head">
  <div class="container">
    <div class="plastic buried-band">
      <h2 id="buried-head">What stayed buried</h2>
      <ul>
        <li>The authors’ Python script (sgjlab.org/empirical-go no longer resolves)</li>
        <li>Table 3 (rice): psRNATarget’s 2011 server and the agriGO tables it used</li>
        <li>The robustness runs of Section 3.3: PITA v6, DIANA-microT-v4, starBase v2 CLIP sets and DAVID’s 2014 BP_FAT</li>
        <li>The multi-hit counts of Table 2: how sites are counted per gene is not stated, and six readings do not reproduce them</li>
        <li>Why {s3_total - s3_both} of S3’s {s3_total:,} study–gene pairs are not in ours: the genes have short 3′ UTRs here, and no Ensembl 75 table we found gives them longer ones</li>
      </ul>
      <p class="so">The bias the paper reports comes back: with regenerated predictions, the mean ion-transport count of 39 random miRNAs is {ion['our_mean']:.1f}, and the hypergeometric test calls it significant at {ion['our_p']:.2e}. Corrected, almost nothing is enriched.</p>
    </div>
  </div>
</section>"""

MATCHED = "".join(f'<div class="row"><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>' for k, v in [
    ("Our run", "miRanda 3.3a (bioconda build) on all 2,578 human and 1,908 mouse miRBase 20 mature miRNAs against every Ensembl 75 3′ UTR; the empirical null rebuilt from the Methods and checked against S1, S3 and S5."),
    ("Axes", "One linear map per axis from the tick marks (x = 150 to 300, y = 0 to 0.20), R’s 4% axis extension, and half a pixel for the pixel centre."),
    ("Fitted, not data", "Raster resolution 118 dpi at R’s default 12 pt, Liberation Sans for Helvetica, the y-title centre and the legend position, and the two fill colours (sampled from the JPEG)."),
    ("Two renders", "“Our run” draws our null. “Paper’s values” draws the bar heights read off the published figure with the same code."),
    ("Reading the views", "Overlay: ink is the paper only, light green is the reproduction only, dark green is both. Difference: darker means a larger grey-level difference (×2)."),
])

CLOSING = ("The paper’s main claim holds on regenerated predictions: the standard hypergeometric test flags terms "
           "that random miRNAs hit just as often, and the empirical test leaves most published lists with nothing.")

page = (HERE / "page_template.html").read_text()
for k, v in {"LEDE": esc(LEDE), "LABEL": LABEL, "STATIONS": STATIONS, "EXTRA": EXTRA + MULTI,
             "RECOVERED": RECOVERED, "MATCHED": MATCHED, "CLOSING": esc(CLOSING)}.items():
    page = page.replace(f"<!--__{k}__-->", v)
page = page.replace("/*__FIGS__*/[]", json.dumps(FIGS_JS))
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(page)
print(f"wrote {OUT} ({len(page) // 1024} KB)")
