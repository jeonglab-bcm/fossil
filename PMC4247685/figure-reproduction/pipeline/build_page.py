"""Build the comparison page for PMC4247685 from the pipeline outputs.

Usage: python3 build_page.py <dir with outputs and published figures> <out index.html>
The directory holds fig{2,3,4,5}_ours.png and .json, figure-2.jpg, figure-{3,4,5}.png,
fig5_tests.json, fig34_summary.json, fig2_boxes.csv and fig2_tests.json.
"""
import base64
import csv
import html
import io
import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
D, OUT = sys.argv[1], sys.argv[2]
j = lambda f: json.load(open(os.path.join(D, f)))
p = lambda f: os.path.join(D, f)

opt = lambda f: j(f) if os.path.exists(p(f)) else None

# A figure whose reproduction has not been run yet is shown as published, marked as pending.
t5, t34, t2, s23 = j("fig5_tests.json"), opt("fig34_summary.json"), opt("fig2_tests.json"), j("s2_s3_check.json")
boxes = list(csv.DictReader(open(p("fig2_boxes.csv")))) if os.path.exists(p("fig2_boxes.csv")) else None


def fmt_p(v):
    return f"{v:.2g}" if v >= 1e-3 else f"{v:.1e}"


CAPTIONS = {
    "2": "Structure-dependent biclustering algorithm recovery scores: best overlap per dataset, 40 synthetic datasets per structure.",
    "3": "Pair-wise correlation of CpG methylation levels: bicluster samples (solid) and control set (dashed).",
    "4": "Progression-free survival of the bicluster samples (solid) and the control set (dashed), TCGA.",
    "5": "Progression-free survival of the validation cohort: most (solid) and least (dashed) correlated tumours.",
}
def fig2_result():
    hm = t2["highest_median"]
    won = [s for s, v in hm.items() if v["ours"] == {"block": "GABi.block", "cor": "GABi.cor", "highvar": "GABi.highvar"}[s]]
    lost = [f"{s} ({hm[s]['ours']} highest)" for s in hm if s not in won]
    out = (f"The matched GABi model has the highest median for {', '.join(won) or 'no structure'}"
           + (f", but not for {', '.join(lost)}." if lost else "."))
    bc = opt("fig2_block_check.json")
    if bc is not None:
        by, runs = bc["benchmark_by_sign"], {r["consistency"]: r for r in bc["consistency_runs"]}
        out += (f" On block data, Algorithm 2's offset b ~ N(0, 1) is negative in {40 - by['n_positive']} of 40 "
                f"datasets, where the implanted block is lower than the rest of its rows and the block model "
                f"cannot see it: GABi.block's median F is {by['b_negative']:.2f} there and {by['b_positive']:.2f} "
                f"where b > 0. With consistency 0.6 instead of 0.8 the median rises to {runs[0.6]['median']:.2f}.")
    return out


def notes(fig):
    if fig in ("3", "4"):
        pm = t34["pfs_median_months"]
    return {
    "2": lambda: ("remeasured", "ggplot2", (
        "Rerun of the benchmark: 40 new datasets per structure from Algorithm 2 (n = 100, m = 20, "
        "p ~ U{1..100}, q ~ U{2..18}, ζ ~ U(0,1)). GABi 0.1 is run with the S1 fitness functions and "
        "its defaults; the paper does not report consistency, ρ or α, so we use 0.8, 0.5 and 0.05. "
        "ISA (isa2), CC, Plaid and Bimax (biclust 2.0.3.1) run with package defaults, also unreported "
        "in the paper. The datasets are random, so boxes are compared by their statistics below, not "
        "by pixels. " + fig2_result())),
    "3": lambda: ("partial", "R base graphics", (
        f"TCGA OV HumanMethylation27 (UCSC Xena), {t34['bicluster_samples']} bicluster and "
        f"{t34['control_samples']} control tumours found by GABi 0.1 with S1's dysregulation-vs-outcome "
        f"model on the Table S3 probes; {t34['features']:,} CpG sites selected. Paper: 21 and 21 tumours, "
        f"14,382 sites. Mode of the pair-wise correlations: {t34['pair_cor_mode']['bicluster']:.2f} "
        f"(bicluster), {t34['pair_cor_mode']['control']:.2f} (control).")),
    "4": lambda: ("partial", "R base graphics", (
        f"Same reconstruction. Logrank p = {fmt_p(t34['pfs_logrank_p'])} (paper 1 × 10⁻⁵). Median "
        f"progression-free interval {pm['bicluster'] if pm['bicluster'] is not None else 'not reached'} vs "
        f"{pm['control']:.1f} months (paper 85.4 vs 32). Progression-free interval from the TCGA "
        "Pan-Cancer clinical resource, not the 2013 portal data the paper used.")),
    "5": lambda: ("identical", "R base graphics", (
        f"Same data as the paper: the clinical rows of Table S3 (20 + 20 patients, PFS in the file's "
        f"units). Logrank p = {fmt_p(t5['pfs']['p'])} for progression-free survival and "
        f"{fmt_p(t5['os']['p'])} for overall survival; the paper reports 0.15 and 0.1.")),
    }[fig]()


# Verdict per figure. Figs 3-4 get theirs from the TCGA reconstruction once it has run.
VERDICTS = {"2": "Partly agrees", "5": "Agrees"}

PENDING = {
    "2": "The synthetic benchmark (40 datasets × 3 structures × 7 methods) is still running.",
    "3": "GABi is still searching the TCGA data for the dysregulation bicluster.",
    "4": "GABi is still searching the TCGA data for the dysregulation bicluster.",
}


def b64_file(path):
    return base64.b64encode(open(path, "rb").read()).decode()


def b64_img(img):
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode()


figs, pending = [], []
for fig in ("2", "3", "4", "5"):
    pub_path = p("figure-2.jpg" if fig == "2" else f"figure-{fig}.png")
    mime = "jpeg" if pub_path.endswith(".jpg") else "png"
    if not os.path.exists(p(f"fig{fig}_ours.png")):
        pending.append((fig, f"data:image/{mime};base64," + b64_file(pub_path)))
        continue
    m = j(f"fig{fig}.json")
    P = np.asarray(Image.open(pub_path).convert("L")).astype(float)
    ours = Image.open(p(f"fig{fig}_ours.png")).convert("RGB" if fig == "2" else "L")
    O = np.asarray(ours.convert("L")).astype(float)
    status, tool, note = notes(fig)
    figs.append(dict(
        id=fig, caption=CAPTIONS[fig], data_status=status, data_note=note, tool=tool, verdict=VERDICTS.get(fig),
        w=P.shape[1], h=P.shape[0],
        paper=f"data:image/{mime};base64," + b64_file(pub_path),
        ours="data:image/png;base64," + b64_img(ours),
        device=("ggplot2, 1946×1355 px at 300 dpi" if fig == "2" else "png() 480×480 px, 72 dpi"),
        scale=f"{m['scale'][0]:.3f} × {m['scale'][1]:.3f}",
        cover_pub=round(100 * m["published_ink_within_2px_of_ours"], 1),
        cover_ours=round(100 * m["our_ink_within_2px_of_published"], 1),
        mad=round(float(np.abs(P - O).mean()), 2),
    ))

esc = html.escape


def fig2_section():
    rows = "".join(
        f"<tr><td>{esc(b['structure'])}</td><td>{esc(b['method'])}</td>"
        f"<td class=num>{float(b['published_median']):.2f}</td><td class=num>{float(b['published_q1']):.2f}–{float(b['published_q3']):.2f}</td>"
        f"<td class=num>{float(b['ours_median']):.2f}</td><td class=num>{float(b['ours_q1']):.2f}–{float(b['ours_q3']):.2f}</td></tr>"
        for b in boxes)
    best = "; ".join(f"{s}: paper {v['published']}, ours {v['ours']}" for s, v in t2["highest_median"].items())
    tests = "".join(
        f"<tr><td>{esc(t['structure'])}</td><td>{esc(t['matched'])} &gt; {esc(t['versus'])}</td>"
        f"<td class=num>{fmt_p(t['p_greater'])}</td></tr>" for t in t2["wilcoxon"])
    return f"""<section class="card" aria-label="Figure 2 box statistics">
      <div class="card-head"><h2>Figure 2 in numbers</h2><span class="badge remeasured">Read from the published pixels</span>
      <p>Median and interquartile range per method. Published values are read from the figure's box positions (fig2_measure.py, ±0.002 F.score). Highest median per structure: {esc(best)}.</p></div>
      <div class="stage"><table class="detail"><thead><tr><th>Structure</th><th>Method</th><th class=num>Paper median</th><th class=num>Paper IQR</th><th class=num>Ours median</th><th class=num>Ours IQR</th></tr></thead><tbody>{rows}</tbody></table></div>
      <p class="note">The paper (p. 11) reports that the matched GABi model beat every other method at p &lt; 0.01 (Wilcoxon signed rank), except Bimax on block structure (p = 0.1). Our one-sided paired tests on the rerun:</p>
      <div class="stage"><table class="detail"><thead><tr><th>Structure</th><th>Comparison</th><th class=num>p</th></tr></thead><tbody>{tests}</tbody></table></div>
    </section>"""


EXTRA = "".join(
    f"""<section class="card" aria-label="Figure {fig}">
  <div class="card-head"><h2>Figure {fig}</h2><span class="pill running"><span aria-hidden="true">⋯</span>Running</span>
  <p>{esc(CAPTIONS[fig])}</p></div>
  <div class="stage"><div class="plate single"><span class="label">Published</span><img src="{src}" alt="Figure {fig} as published"></div></div>
  <p class="note">{esc(PENDING[fig])} This page is rebuilt when it finishes.</p>
</section>""" for fig, src in pending)
if t2 is not None and boxes is not None:
    EXTRA += fig2_section()

r, sd = s23["tcga_mean_abs_r"], s23["tcga_median_sd"]
EXTRA += f"""<section class="card" aria-label="Table S2 and Table S3">
  <div class="card-head"><h2>Tables S2 and S3 list different CpG sites</h2><span class="badge partial">Finding</span>
  <p>Both are described as the {s23['s2']:,} CpG sites of the dysregulation bicluster. They share {s23['shared']:,}. Both lists are sorted, and they agree row for row up to row {s23['rows_equal_until']}. After that they drift apart by up to {s23['row_offset_range'][1]} positions, which looks like an indexing slip in one of them.</p></div>
  <div class="stage"><table class="detail"><thead><tr><th>Probes (TCGA OV HM27, {s23['tcga_primary_tumours']} primary tumours)</th><th class=num>Mean |r| between probes</th><th class=num>Median SD of β</th></tr></thead><tbody>
  <tr><td>In both lists ({s23['shared']:,})</td><td class=num>{r['shared']:.3f}</td><td class=num>{sd['shared']:.3f}</td></tr>
  <tr><td>Only in Table S3 ({s23['s3_only']:,})</td><td class=num>{r['s3_only']:.3f}</td><td class=num>{sd['s3_only']:.3f}</td></tr>
  <tr><td>Only in Table S2 ({s23['s2_only']:,})</td><td class=num>{r['s2_only']:.3f}</td><td class=num>{sd['s2_only']:.3f}</td></tr>
  <tr><td>Random probes in neither list (3,000)</td><td class=num>{r['random']:.3f}</td><td class=num>{sd['random']:.3f}</td></tr></tbody></table></div>
  <p class="note">The probes only in Table S3 behave like the shared ones: tightly co-varying, with low variance across tumours. The probes only in Table S2 behave like random probes. Table S3's row labels also match its values (mean β per row against the TCGA mean of the labelled probe: r = {s23['s3_labels_vs_tcga_mean_r']:.3f}; against the S2 probe at the same row: r = {s23['s2_labels_at_same_row_vs_tcga_mean_r']:.3f}). We take Table S3's list as the bicluster's CpG sites.</p>
</section>"""
def fig2_recovered():
    if t2 is None or boxes is None:
        return "<dd>Running: the synthetic benchmark is not finished.</dd>"
    med = {(b["structure"], b["method"]): (float(b["published_median"]), float(b["ours_median"])) for b in boxes}
    parts = []
    for s, m in (("block", "GABi.block"), ("cor", "GABi.cor"), ("highvar", "GABi.highvar")):
        ps = [t["p_greater"] for t in t2["wilcoxon"] if t["structure"] == s]
        beaten = sum(p < 0.01 for p in ps)
        pub, ours = med[(s, m)]
        parts.append(f"{s}: {m} median {ours:.2f} (paper {pub:.2f}), better than {beaten} of {len(ps)} other "
                     "methods at p &lt; 0.01")
    return ("<dd>" + "; ".join(parts) + ". The paper reports the matched model better than all six at "
            "p &lt; 0.01 except Bimax on block (p = 0.1).</dd>")


tcga = ("<dd>Running: GABi is searching the TCGA tumours for the dysregulation bicluster.</dd>" if t34 is None else
        f"<dd>{t34['bicluster_samples']} bicluster and {t34['control_samples']} control tumours with "
        f"{t34['features']:,} CpG sites (paper: 21, 21 and 14,382); progression-free logrank p = "
        f"{fmt_p(t34['pfs_logrank_p'])} (paper 1 × 10⁻⁵). The paper does not list the tumours, so they are "
        "found again by GABi on public TCGA data.</dd>")
RECOVERED = f"""<section class="method">
    <h2>What we recovered</h2>
    <dl>
      <dt>Fig. 5 data</dt><dd>Table S3 is the validation cohort of Fig. 5, not the TCGA set: its 40 columns are the
        20 tumours most (Group1, solid) and 20 least (Group2, dashed) correlated with the bicluster profile, and its
        times span the figure's unlabelled 0–1700 axis. Kaplan–Meier curves from it match the published curves
        pixel for pixel. Logrank p = {fmt_p(t5['pfs']['p'])} (progression-free) and {fmt_p(t5['os']['p'])}
        (overall); the paper prints 0.15 and 0.1.</dd>
      <dt>How Figs 3–5 were drawn</dt><dd>R base graphics on the default <span class="mono">png()</span> device
        (480×480&nbsp;px, 72&nbsp;dpi, pointsize 12, default margins), cropped to the plot frame and enlarged 2.00×,
        2.01× and 2.14×. The survival curves use <span class="mono">xaxs = "S"</span>, the survival 2.x default.</dd>
      <dt>How Fig. 2 was drawn</dt><dd>ggplot2 with 0.9.3 theme sizes at a base of 8.6&nbsp;pt, the default hue
        palette in method order, one facet per structure. Its box statistics are read back from the pixels (table
        below).</dd>
      <dt>The bicluster's CpG sites</dt><dd>Table S3's {s23['s3']:,} row labels. Table S2 claims the same sites,
        but only {s23['shared']:,} agree; from row {s23['rows_equal_until'] + 1} on it is shifted by up to
        {s23['row_offset_range'][1]} positions, and its extra probes behave like random probes.</dd>
      <dt>What the code computes</dt><dd>As published, S1's dysregulation fitness cannot score a 21-sample
        bicluster in current R. Spearman's test returns p&nbsp;=&nbsp;0 for the seed row against itself and for
        |ρ| between 0.836 and 0.865, and GABi turns the resulting infinite score into 0. We add the 2e-16 floor that
        S1's own selection function uses. Details, and 77 checks of GABi&nbsp;0.1 and S1 against the paper, are on
        the implementation page.</dd>
      <dt>Fig. 2 result</dt>{fig2_recovered()}
      <dt>TCGA bicluster (Figs 3–4)</dt>{tcga}
      <dt>Not recoverable</dt><dd>GABi's thresholds (consistency, ρ, α), the comparison methods' settings and
        the synthetic datasets of Fig. 2; the identities of the 21 + 21 TCGA tumours; the 2013 TCGA clinical data.
        Figs 2–4 can therefore match the paper only in distribution, not pixel for pixel.</dd>
    </dl>
  </section>"""

page = open(os.path.join(HERE, "page_template.html")).read().replace("<!--__EXTRA__-->", EXTRA)
page = page.replace("<!--__RECOVERED__-->", RECOVERED)
page = page.replace("/*__FIGS__*/[]", json.dumps(figs))
page = page.replace('<span class="eyebrow">', '<a class="back" href="../">← fossil</a>\n    <span class="eyebrow">', 1)
HEAD = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
        '<style>:root{padding:env(safe-area-inset-top,0) 0 env(safe-area-inset-bottom,0)}body{margin:0}img{max-width:100%}[hidden]{display:none!important}'
        '.back{font-size:13px;color:var(--accent);text-decoration:none}.back:hover{text-decoration:underline}</style>\n')
i = page.index("</style>") + len("</style>")
page = HEAD + page[:i] + "\n</head>\n<body>\n" + page[i:] + "\n</body>\n</html>\n"
assert "__EXTRA__" not in page
os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
open(OUT, "w").write(page)
print("wrote", OUT, len(page) // 1024, "KB")
