"""Build the comparison page for PMC4247685 from the pipeline outputs.

Usage: python3 build_page.py <dir with outputs and published figures> <out index.html>
The directory holds fig{2,3,4,5}_ours.png and .json, figure-2.jpg, figure-{3,4,5}.png,
fig5_tests.json, fig34_summary.json, fig2_boxes.csv and fig2_tests.json.
The page links ../results.css, the stylesheet the site's results pages share.
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
        out += (f" On block data, Algorithm 2’s offset b ~ N(0, 1) is negative in {40 - by['n_positive']} of 40 "
                f"datasets, where the implanted block is lower than the rest of its rows and the block model "
                f"cannot see it: GABi.block’s median F is {by['b_negative']:.2f} there and {by['b_positive']:.2f} "
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
        f"{t34['control_samples']} control tumours found by GABi 0.1 with S1’s dysregulation-vs-outcome "
        f"model on the Table S3 probes; {t34['features']:,} CpG sites selected. Paper: 21 and 21 tumours, "
        f"14,382 sites. Mode of the pair-wise correlations: {t34['pair_cor_mode']['bicluster']:.2f} "
        f"(bicluster), {t34['pair_cor_mode']['control']:.2f} (control).")),
    "4": lambda: ("partial", "R base graphics", (
        f"Same reconstruction. Logrank p = {fmt_p(t34['pfs_logrank_p'])} (paper 1 × 10⁻⁵). Median "
        f"progression-free interval {'not reached' if pm['bicluster'] is None else format(pm['bicluster'], '.1f')} vs "
        f"{pm['control']:.1f} months (paper 85.4 vs 32). "
        + ("Our bicluster progresses sooner than its control set, the reverse of the paper. "
           if pm['bicluster'] is not None and pm['bicluster'] < pm['control'] else "")
        + "Progression-free interval from the TCGA Pan-Cancer clinical resource, not the 2013 portal "
        "data the paper used.")),
    "5": lambda: ("identical", "R base graphics", (
        f"Same data as the paper: the clinical rows of Table S3 (20 + 20 patients, PFS in the file’s "
        f"units). Logrank p = {fmt_p(t5['pfs']['p'])} for progression-free survival and "
        f"{fmt_p(t5['os']['p'])} for overall survival; the paper reports 0.15 and 0.1.")),
    }[fig]()


# Verdict per figure. Fig. 3: the bicluster's sites co-vary more than the control set's, as in the paper,
# but the two peaks sit closer. Fig. 4: the survival difference runs the other way from the paper's.
VERDICTS = {"2": "Partly agrees", "3": "Partly agrees", "4": "Differs", "5": "Agrees"}

PENDING = {
    "2": "The synthetic benchmark (40 datasets × 3 structures × 7 methods) is still running.",
    "3": "GABi is still searching the TCGA data for the dysregulation bicluster.",
    "4": "GABi is still searching the TCGA data for the dysregulation bicluster.",
}

# What each reproduction is drawn from, printed under its verdict.
BASIS = {"identical": "Identical data", "partial": "Reconstructed from public data", "remeasured": "Rerun on random data"}
VCLASS = {"Agrees": "agrees", "Partly agrees": "partly", "Differs": "differs", "Running": "running"}


def b64_file(path):
    return base64.b64encode(open(path, "rb").read()).decode()


def b64_img(img):
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode()


esc = html.escape
num = lambda v: f"{v:g}"  # prints a number the way the page's script would (100.0 as 100)


def stamp(verdict, basis=None):
    if not verdict:
        return f'<p class="basis">{esc(basis)}</p>' if basis else ""
    small = f"<small>{esc(basis)}</small>" if basis else ""
    return f'<span class="stamp" data-v="{VCLASS[verdict]}">{esc(verdict)}{small}</span>'


def head(hid, title, caption, right=""):
    return f'<header class="station-head"><h2 id="{hid}">{title}</h2><p class="caption">{caption}</p>{right}</header>'


def dose(rows):
    return "".join(f"<div><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>" for k, v in rows)


def plate(label, src, alt, w, h):
    return f'<figure class="plate"><figcaption>{esc(label)}</figcaption><img src="{src}" alt="{esc(alt)}" width="{w}" height="{h}"></figure>'


def figs_phrase(ids):
    ids = sorted(ids, key=int)
    if len(ids) == 1:
        return f"Fig. {ids[0]}"
    run = [int(i) for i in ids] == list(range(int(ids[0]), int(ids[-1]) + 1))
    return f"Figs {ids[0]} to {ids[-1]}" if run and len(ids) > 2 else f"Figs {', '.join(ids[:-1])} and {ids[-1]}"


figs, pending, stations, verdict_of = [], [], {}, {}
for fig in ("2", "3", "4", "5"):
    pub_path = p("figure-2.jpg" if fig == "2" else f"figure-{fig}.png")
    mime = "jpeg" if pub_path.endswith(".jpg") else "png"
    hid = f"fig-{fig}-head"
    if not os.path.exists(p(f"fig{fig}_ours.png")):
        pw, ph = Image.open(pub_path).size
        pending.append(fig)
        verdict_of[fig] = "Running"
        stations[int(fig) * 10] = (
            f'<section class="station surface" id="fig-{fig}" aria-labelledby="{hid}">'
            + head(hid, f"Fig. {fig}", esc(CAPTIONS[fig]), stamp("Running"))
            + '<div class="pending">'
            + plate("Published", f"data:image/{mime};base64," + b64_file(pub_path), f"Figure {fig} as published", pw, ph)
            + f'<p class="note">{esc(PENDING[fig])} This page is rebuilt when it finishes.</p></div></section>')
        continue
    m = j(f"fig{fig}.json")
    P = np.asarray(Image.open(pub_path).convert("L")).astype(float)
    ours = Image.open(p(f"fig{fig}_ours.png")).convert("RGB" if fig == "2" else "L")
    O = np.asarray(ours.convert("L")).astype(float)
    status, tool, note = notes(fig)
    w, h = P.shape[1], P.shape[0]
    verdict_of[fig] = VERDICTS.get(fig)
    stats = [
        ("Pixel size", f"{w} × {h}"),
        ("Drawn at", "ggplot2, 1946×1355 px at 300 dpi" if fig == "2" else "png() 480×480 px, 72 dpi"),
        ("Frame scale", f"{m['scale'][0]:.3f} × {m['scale'][1]:.3f}"),
        ("Paper ink ≤2 px from ours", num(round(100 * m["published_ink_within_2px_of_ours"], 1)) + "%"),
        ("Our ink ≤2 px from paper", num(round(100 * m["our_ink_within_2px_of_published"], 1)) + "%"),
        ("Mean |Δ| grey", num(round(float(np.abs(P - O).mean()), 2))),
    ]
    figs.append(dict(id=fig, w=w, h=h))
    stations[int(fig) * 10] = (
        f'<section class="station surface" id="fig-{fig}" aria-labelledby="{hid}">'
        + head(hid, f"Fig. {fig}", esc(CAPTIONS[fig]), stamp(VERDICTS.get(fig), BASIS[status]))
        + '<div class="stage"><div class="pair">'
        + plate("Published", f"data:image/{mime};base64," + b64_file(pub_path), f"Figure {fig} as published", w, h)
        + plate(f"Reproduction in {tool}", "data:image/png;base64," + b64_img(ours), f"Figure {fig} reproduced", w, h)
        + '</div></div>'
        + f'<div class="station-foot"><dl class="dose">{dose(stats)}</dl><p class="note">{esc(note)}</p></div></section>')


def fig2_section():
    rows = "".join(
        f"<tr><td>{esc(b['structure'])}</td><td>{esc(b['method'])}</td>"
        f"<td class=num>{float(b['published_median']):.2f}</td><td class=num>{float(b['published_q1']):.2f} to {float(b['published_q3']):.2f}</td>"
        f"<td class=num>{float(b['ours_median']):.2f}</td><td class=num>{float(b['ours_q1']):.2f} to {float(b['ours_q3']):.2f}</td></tr>"
        for b in boxes)
    best = "; ".join(f"{s}: paper {v['published']}, ours {v['ours']}" for s, v in t2["highest_median"].items())
    tests = "".join(
        f"<tr><td>{esc(t['structure'])}</td><td>{esc(t['matched'])} &gt; {esc(t['versus'])}</td>"
        f"<td class=num>{fmt_p(t['p_greater'])}</td></tr>" for t in t2["wilcoxon"])
    intro = ("Median and interquartile range per method. Published values are read from the figure’s box "
             f"positions (fig2_measure.py, ±0.002 F.score). Highest median per structure: {esc(best)}.")
    return f"""<section class="station surface" id="fig-2-numbers" aria-labelledby="fig-2-numbers-head">
      {head("fig-2-numbers-head", "Fig. 2 in numbers", intro, '<p class="basis">Read from the published pixels</p>')}
      <div class="split">
        <div class="wide table-wrap"><table class="record dense"><thead><tr><th scope="col">Structure</th><th scope="col">Method</th><th scope="col" class=num>Paper median</th><th scope="col" class=num>Paper IQR</th><th scope="col" class=num>Ours median</th><th scope="col" class=num>Ours IQR</th></tr></thead><tbody>{rows}</tbody></table></div>
        <div class="side">
          <p class="note">The paper (p. 11) reports that the matched GABi model beat every other method at p &lt; 0.01 (Wilcoxon signed rank), except Bimax on block structure (p = 0.1). Our one-sided paired tests on the rerun:</p>
          <div class="table-wrap"><table class="record dense"><thead><tr><th scope="col">Structure</th><th scope="col">Comparison</th><th scope="col" class=num>p</th></tr></thead><tbody>{tests}</tbody></table></div>
        </div>
      </div>
    </section>"""


if t2 is not None and boxes is not None:
    stations[25] = fig2_section()
STATIONS = "\n".join(stations[k] for k in sorted(stations))

r, sd = s23["tcga_mean_abs_r"], s23["tcga_median_sd"]
EXTRA = f"""<section class="container after-bench" aria-labelledby="s2s3-head">
  <div class="station surface">
    <header class="station-head"><h2 id="s2s3-head">Tables S2 and S3 list different CpG sites</h2><p class="basis">Our finding</p></header>
    <div class="split">
      <div class="side side--lead"><p class="caption">Both are described as the {s23['s2']:,} CpG sites of the dysregulation bicluster. They share {s23['shared']:,}. Both lists are sorted, and they agree row for row up to row {s23['rows_equal_until']}. After that they drift apart by up to {s23['row_offset_range'][1]} positions, which looks like an indexing slip in one of them.</p></div>
      <div class="wide">
        <div class="table-wrap"><table class="record stack"><thead><tr><th scope="col">Probes (TCGA OV HM27, {s23['tcga_primary_tumours']} primary tumours)</th><th scope="col" class=num>Mean |r| between probes</th><th scope="col" class=num>Median SD of β</th></tr></thead><tbody>
  <tr><td>In both lists ({s23['shared']:,})</td><td class=num data-label="Mean |r| between probes">{r['shared']:.3f}</td><td class=num data-label="Median SD of β">{sd['shared']:.3f}</td></tr>
  <tr><td>Only in Table S3 ({s23['s3_only']:,})</td><td class=num data-label="Mean |r| between probes">{r['s3_only']:.3f}</td><td class=num data-label="Median SD of β">{sd['s3_only']:.3f}</td></tr>
  <tr><td>Only in Table S2 ({s23['s2_only']:,})</td><td class=num data-label="Mean |r| between probes">{r['s2_only']:.3f}</td><td class=num data-label="Median SD of β">{sd['s2_only']:.3f}</td></tr>
  <tr><td>Random probes in neither list (3,000)</td><td class=num data-label="Mean |r| between probes">{r['random']:.3f}</td><td class=num data-label="Median SD of β">{sd['random']:.3f}</td></tr></tbody></table></div>
        <p class="note">The probes only in Table S3 behave like the shared ones: tightly co-varying, with low variance across tumours. The probes only in Table S2 behave like random probes. Table S3’s row labels also match its values (mean β per row against the TCGA mean of the labelled probe: r = {s23['s3_labels_vs_tcga_mean_r']:.3f}; against the S2 probe at the same row: r = {s23['s2_labels_at_same_row_vs_tcga_mean_r']:.3f}). We take Table S3’s list as the bicluster’s CpG sites.</p>
      </div>
    </div>
  </div>
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
RECOVERED = f"""<section class="notes" aria-labelledby="back-head">
  <div class="container">
    <h2 id="back-head">What came back</h2>
    <dl class="ledger">
      <div class="row"><dt>Fig. 5 data</dt><dd>Table S3 is the validation cohort of Fig. 5, not the TCGA set: its 40 columns are the
        20 tumours most (Group1, solid) and 20 least (Group2, dashed) correlated with the bicluster profile, and its
        times span the figure’s unlabelled 0 to 1700 axis. Kaplan-Meier curves from it match the published curves
        pixel for pixel. Logrank p = {fmt_p(t5['pfs']['p'])} (progression-free) and {fmt_p(t5['os']['p'])}
        (overall); the paper prints 0.15 and 0.1.</dd></div>
      <div class="row"><dt>How Figs 3 to 5 were drawn</dt><dd>R base graphics on the default <span class="mono">png()</span> device
        (480×480&nbsp;px, 72&nbsp;dpi, pointsize 12, default margins), cropped to the plot frame and enlarged 2.00×,
        2.01× and 2.14×. The survival curves use <span class="mono">xaxs = "S"</span>, the survival 2.x default.</dd></div>
      <div class="row"><dt>How Fig. 2 was drawn</dt><dd>ggplot2 with 0.9.3 theme sizes at a base of 8.6&nbsp;pt, the default hue
        palette in method order, one facet per structure. Its box statistics are read back from the pixels (Fig. 2 in
        numbers, above).</dd></div>
      <div class="row"><dt>The bicluster’s CpG sites</dt><dd>Table S3’s {s23['s3']:,} row labels. Table S2 claims the same sites,
        but only {s23['shared']:,} agree; from row {s23['rows_equal_until'] + 1} on it is shifted by up to
        {s23['row_offset_range'][1]} positions, and its extra probes behave like random probes.</dd></div>
      <div class="row"><dt>What the code computes</dt><dd>As published, S1’s dysregulation fitness cannot score a 21-sample
        bicluster in current R. Spearman’s test returns p&nbsp;=&nbsp;0 for the seed row against itself and for
        |ρ| between 0.836 and 0.865, and GABi turns the resulting infinite score into 0. We add the 2e-16 floor that
        S1’s own selection function uses. Details, and 77 checks of GABi&nbsp;0.1 and S1 against the paper, are on
        the implementation page.</dd></div>
      <div class="row"><dt>Fig. 2 result</dt>{fig2_recovered()}</div>
      <div class="row"><dt>TCGA bicluster (Figs 3 and 4)</dt>{tcga}</div>
    </dl>
  </div>
</section>
<section class="buried" aria-labelledby="buried-head">
  <div class="container">
    <div class="plastic buried-band">
      <h2 id="buried-head">What stayed buried</h2>
      <ul>
        <li>GABi’s thresholds (consistency, ρ, α), the comparison methods’ settings and the synthetic datasets of Fig. 2</li>
        <li>The identities of the 21 + 21 TCGA tumours</li>
        <li>The 2013 TCGA clinical data</li>
      </ul>
      <p class="so">Figs 2 to 4 can therefore match the paper only in distribution, not pixel for pixel.</p>
    </div>
  </div>
</section>"""

# The hero's label lists every figure with its verdict; the lede and the closing line follow what has run.
LABEL = "<ol>" + "".join(
    f'<li><a href="#fig-{fig}"><span>Fig. {fig}</span>'
    f'<span class="v" data-v="{VCLASS.get(v, "none")}">{esc(v or "No verdict yet")}</span></a></li>'
    for fig, v in verdict_of.items()) + "</ol>"
done = [f["id"] for f in figs]
LEDE = (f"So far its data, code and {figs_phrase(done)} are back." if pending and done else
        "So far its data and its code are back." if pending else
        f"Its data, its code and {figs_phrase(done)} are back.")
CLOSING = (f"We rebuild this page when {figs_phrase(pending)} {'comes' if len(pending) == 1 else 'come'} back."
           if pending else "We rebuild this page each time the pipeline runs.")

page = open(os.path.join(HERE, "page_template.html")).read()
for marker, text in (("<!--__STATIONS__-->", STATIONS), ("<!--__EXTRA__-->", EXTRA), ("<!--__RECOVERED__-->", RECOVERED),
                     ("<!--__LABEL__-->", LABEL), ("<!--__LEDE__-->", LEDE), ("<!--__CLOSING__-->", CLOSING),
                     ("/*__FIGS__*/[]", json.dumps(figs))):
    assert marker in page, marker
    page = page.replace(marker, text)
assert "__EXTRA__" not in page
os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
open(OUT, "w").write(page)
print("wrote", OUT, len(page) // 1024, "KB")
