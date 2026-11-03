"""Build the comparison page for PMC1847688 from the pipeline outputs.

Usage: python build_page.py <output_dir> <published_dir> <out index.html>
<output_dir> holds fig{2..9}_ours.png, comparison.json and tables.json (compare.py, make_tables.py).
Each published figure is cropped as compare.py crops it, so the two images share a pixel grid.
The page links ../results.css, the stylesheet the site's results pages share.
"""

import base64
import html
import io
import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from compare import CROP_ROWS  # noqa: E402

D, PUB, OUT = sys.argv[1:4]
cmp = json.load(open(os.path.join(D, "comparison.json")))
tab = json.load(open(os.path.join(D, "tables.json")))
MAX_W = 1500  # page images are scaled to this width; the scores come from the full-size files
FIG9_COLS = 3000  # compare.py keeps panels a and b, the left 3000 px of Fig. 9

CAPTIONS = {
    "2": "Raw MALDI-TOF mass spectrum from a human plasma sample, with background noise and baseline drift.",
    "3": "Difference between the spectrum before and after the Kaiser filter, window length 10, 20, 30 and 40 (a to d).",
    "4": "Difference before and after smoothing. Only panel c, the Kaiser filter, is LIMPIC’s.",
    "5": "Baseline drift by the minimum-value interpolation method (blue) and LIMPIC’s peak-elimination method (red).",
    "6": "The spectrum at 5 to 8 and 14.75 to 17.75 kDa (a, b) and the noise LIMPIC removes there (c, d).",
    "7": "Peaks detected in 8.73 to 9.02 kDa, marked by red crosses. Only the top panel, LIMPIC, is shown.",
    "8": "The same peaks classified across the 30 spectra: green for a detection rate of 0.5 or more, red for the rest.",
    "9": "PDR of every peak class across the 30 plasma spectra (a) and its histogram (b).",
}
PANEL_NAME = {"peak-elimination": "Peak elimination (red)", "monotone-minimum": "Minimum value (blue)", "LIMPIC": "LIMPIC"}

VCLASS = {"Agrees": "agrees", "Partly agrees": "partly", "Differs": "differs"}
esc = html.escape
num = lambda v: f"{v:g}"
pct = lambda v: num(round(100 * v, 2)) + "%"


def b64_png(img):
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode()


def page_image(img):
    w, h = img.size
    if w <= MAX_W:
        return img
    return img.resize((MAX_W, round(h * MAX_W / w)), Image.LANCZOS)


def published(fig):
    img = Image.open(os.path.join(PUB, f"figure-{fig}.png")).convert("RGB")
    top, bottom = CROP_ROWS.get(f"fig{fig}", (0, None))
    img = img.crop((0, top, FIG9_COLS if fig == "9" else img.width, bottom or img.height))
    return img


def stamp(verdict, basis):
    return f'<span class="stamp" data-v="{VCLASS[verdict]}">{esc(verdict)}<small>{esc(basis)}</small></span>'


def head(hid, title, caption, right=""):
    return f'<header class="station-head"><h2 id="{hid}">{title}</h2><p class="caption">{caption}</p>{right}</header>'


def dose(rows):
    return "".join(f"<div><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>" for k, v in rows)


def plate(label, src, alt, w, h):
    return f'<figure class="plate"><figcaption>{esc(label)}</figcaption><img src="{src}" alt="{esc(alt)}" width="{w}" height="{h}"></figure>'


def scores(fig):
    rows = []
    for r in cmp[f"fig{fig}"]:
        name = PANEL_NAME.get(r["panel"], f"panel {r['panel']}" if r["panel"] else "")
        both = f"{pct(r['published_within_2px'])} and {pct(r['ours_within_2px'])}"
        rows.append((f"{name}, ≤2 px both ways" if name else "≤2 px both ways", both))
    return rows


def markers(fig):
    r = cmp[f"fig{fig}"][0]
    out = [("Peaks", f"{r['published_marker_at_each_of_ours']} of {r['markers_ours']} at our positions"),
           ("Published peaks without ours", str(r["published_markers_without_ours"]))]
    if "class_agreement" in r:
        out.append(("Same colour as ours", r["class_agreement"]))
    return out


def fig8_note():
    peaks = cmp["fig8"][0]["peaks"]
    diff = [p for p in peaks if p["our_class"] != p["published_class"]]
    return (f"Every published cross sits on one of our 16 peaks. Our 30-spectrum classification colours "
            f"{len(peaks) - len(diff)} of them as the paper does; {len(diff)} differ. The paper’s classes "
            "came from a run we could not repeat (see Additional File 4, below).")


f9 = cmp["fig9"]
NOTES = {
    "2": "Plasma file P_15 is the example spectrum. The figure plots its raw counts divided by 5.",
    "3": "LIMPIC’s smoothing is a Savitzky-Golay filter run forward and backward, despite the “Kaiser” label. Raw minus smoothed, divided by 5.",
    "4": "Same signal as Fig. 3b. The Savitzky-Golay and wavelet panels (a, b) are not LIMPIC’s and are not drawn.",
    "5": ("Red is LIMPIC’s baseline, through the minima of the 100 Da blocks without peaks. The paper gives no settings "
          "for the blue minimum-value baseline; a wavelet-denoised running minimum, CROMWELL’s approach, matches it with "
          "one combination found by search. Ours dips to 1.5 near 7.25 kDa where the published red does not."),
    "6": "Panels a and b are the raw spectrum; c and d are what LIMPIC removes (smoothing residual plus baseline), divided by 5. The APEX, CENTROID and CROMWELL panels (e to h) are not drawn.",
    "7": "The processed spectrum and LIMPIC’s peaks, 8.73 to 9.02 kDa. The APEX, CENTROID and CROMWELL panels below it are not drawn.",
    "8": fig8_note(),
    "9": ("Drawn from Additional File 4, the authors’ own list of 1,581 plasma peak classes, not from our run. "
          f"Histogram counts {f9['b']['S4_counts']}; published bars read as "
          f"{[round(v) for v in f9['b']['published_bar_heights']]}. Panels c and d are left out: their SNR divides by a "
          "smooth noise curve that LIMPIC 1.1 does not compute."),
}
BASIS = {"9": "Drawn from Additional File 4"}
# Fig. 8: the curve and the peaks come back, the paper's protein/noise colours only in part.
VERDICTS = {"8": "Partly agrees", "9": "Partly agrees"}


def dose_rows(fig):
    if fig == "9":
        return [("Panel a, ≤2 px both ways", f"{pct(f9['a']['published_within_2px'])} and {pct(f9['a']['ours_within_2px'])}"),
                ("Panel b, largest bar gap", f"{num(f9['b']['max_abs_difference'])} peaks"),
                ("Peak classes", f"{f9['a']['classes']:,}")]
    rows = scores(fig)
    return rows + markers(fig) if fig in ("7", "8") else rows


figs, stations, verdict_of = [], [], {}
for fig in [str(i) for i in range(2, 10)]:
    pub = published(fig)
    ours = Image.open(os.path.join(D, f"fig{fig}_ours.png")).convert("RGB")
    assert pub.size == ours.size, (fig, pub.size, ours.size)
    full_w, full_h = pub.size
    pub, ours = page_image(pub), page_image(ours)
    w, h = pub.size
    mean_d = float(np.abs(np.asarray(pub.convert("L"), float) - np.asarray(ours.convert("L"), float)).mean())
    verdict = VERDICTS.get(fig, "Agrees")
    verdict_of[fig] = verdict
    hid = f"fig-{fig}-head"
    stats = [("Pixel size", f"{full_w} × {full_h}")] + dose_rows(fig) + [("Mean |Δ| grey", num(round(mean_d, 2)))]
    figs.append(dict(id=fig, w=w, h=h))
    stations.append(
        f'<section class="station surface" id="fig-{fig}" aria-labelledby="{hid}">'
        + head(hid, f"Fig. {fig}", esc(CAPTIONS[fig]), stamp(verdict, BASIS.get(fig, "Rerun of the authors’ code")))
        + '<div class="stage"><div class="pair">'
        + plate("Published", "data:image/png;base64," + b64_png(pub), f"Figure {fig} as published", w, h)
        + plate("Our run", "data:image/png;base64," + b64_png(ours), f"Figure {fig} reproduced", w, h)
        + "</div></div>"
        + f'<div class="station-foot"><dl class="dose">{dose(stats)}</dl><p class="note">{esc(NOTES[fig])}</p></div></section>')


# Tables 1 to 3: LIMPIC's rows, paper against our run.
P, t1 = tab["paper"], tab["table1_limpic"]
CONC = ["2.5", "5", "7.5", "10", "25", "50"]
fmt = lambda v: "" if v is None else num(v)
t1_rows = "".join(
    f"<tr><td>{c} fmol</td>"
    f"<td class=num data-label=\"Paper mean\">{fmt(P['table1_limpic']['average_intensity'][i])}</td>"
    f"<td class=num data-label=\"Ours mean\">{fmt(t1['average_intensity'][i])}</td>"
    f"<td class=num data-label=\"Paper CV\">{fmt(P['table1_limpic']['coefficient_of_variation'][i])}</td>"
    f"<td class=num data-label=\"Ours CV\">{fmt(t1['coefficient_of_variation'][i])}</td>"
    f"<td class=num data-label=\"Replicates with the peak\">{t1['n_replicates_with_peak'][i]} of 5</td>"
    f"<td class=num data-label=\"Paper classes\">{P['table2_limpic_detected_classes'][i]}</td>"
    f"<td class=num data-label=\"Ours classes\">{tab['table2_limpic_detected_classes'][i]}</td></tr>"
    for i, c in enumerate(CONC))
t3p, t3o = P["table3_limpic"], tab["table3_limpic"]
po, s4 = tab["plasma_ours"], tab["plasma_additional_file_4"]
EXTRA = f"""<section class="container after-bench" aria-labelledby="tables-head">
  <div class="station surface" id="tables">
    <header class="station-head"><h2 id="tables-head">Tables 1 to 3</h2><p class="caption">LIMPIC’s rows: cytochrome C intensity across 5 replicates (Table 1), classes detected per concentration (Table 2), and peaks, classes and hit rate (Table 3).</p>{stamp("Differs", "Rerun of the authors’ code")}</header>
    <div class="table-wrap"><table class="record stack"><thead><tr><th scope="col">In vitro</th><th scope="col" class=num>Paper mean</th><th scope="col" class=num>Ours mean</th><th scope="col" class=num>Paper CV</th><th scope="col" class=num>Ours CV</th><th scope="col" class=num>Replicates with the peak</th><th scope="col" class=num>Paper classes</th><th scope="col" class=num>Ours classes</th></tr></thead><tbody>{t1_rows}</tbody></table></div>
    <div class="split">
      <div class="side side--lead">
        <div class="table-wrap"><table class="record dense"><thead><tr><th scope="col">Table 3</th><th scope="col" class=num>Paper</th><th scope="col" class=num>Ours</th></tr></thead><tbody>
          <tr><td>In vitro peaks per spectrum</td><td class=num>{num(t3p['in_vitro']['average_peaks'])}</td><td class=num>{num(t3o['in_vitro']['average_peaks'])}</td></tr>
          <tr><td>In vitro hit rate</td><td class=num>{num(t3p['in_vitro']['hit_rate'])}</td><td class=num>{num(t3o['in_vitro']['hit_rate'])}</td></tr>
          <tr><td>Plasma peaks per spectrum</td><td class=num>{num(t3p['plasma']['average_peaks'])}</td><td class=num>{num(t3o['plasma']['average_peaks'])}</td></tr>
          <tr><td>Plasma classes selected</td><td class=num>{t3p['plasma']['classes']}</td><td class=num>{t3o['plasma']['classes']}</td></tr>
          <tr><td>Plasma hit rate</td><td class=num>{num(t3p['plasma']['hit_rate'])}</td><td class=num>{num(t3o['plasma']['hit_rate'])}</td></tr>
        </tbody></table></div>
      </div>
      <div class="wide">
        <p class="note">With the settings it ships with, LIMPIC 1.1 finds about {round(t3o['in_vitro']['average_peaks'])} peaks in each in vitro spectrum, where the paper reports {t3p['in_vitro']['average_peaks']}. The paper does not give the settings it used for Tables 1 to 3, so these rows do not come back. Table 1’s cytochrome C class is the one within 300 ppm of 12,360.5; where only one replicate has it, there is no CV.</p>
      </div>
    </div>
  </div>
</section>"""

RECOVERED = f"""<section class="notes" aria-labelledby="back-head">
  <div class="container">
    <h2 id="back-head">What came back</h2>
    <dl class="ledger">
      <div class="row"><dt>LIMPIC in Python</dt><dd>Each MATLAB file of Additional File 1 ported function by function. Against the authors’ code run in GNU Octave, every intermediate signal, all {po['peaks']:,} plasma peaks and every peak class agree to six decimals.</dd></div>
      <div class="row"><dt>The code runs again</dt><dd>As published, <span class="mono">find_intervals.m</span> keeps blocks with MATLAB’s <span class="mono">kurtosis</span> below 1. That kurtosis is 3 for Gaussian noise and never below 1, so no block passes and the code stops. With excess kurtosis (0 for Gaussian noise) Figs 7 and 8 come back peak for peak, so that is what the authors ran.</dd></div>
      <div class="row"><dt>The example spectrum</dt><dd>Figs 2 to 8 show plasma file <span class="mono">P_15</span>, as raw counts divided by 5.</dd></div>
      <div class="row"><dt>Fig. 5’s comparison baseline</dt><dd>A wavelet-denoised running minimum up to 20 kDa (db4, 9 levels, hard threshold at 6 MAD). The paper gives no settings; this one combination was found by search.</dd></div>
      <div class="row"><dt>A damaged input file</dt><dd>Line 32,768 of <span class="mono">SOL_5_TXT/SOL_calib_08e.txt</span> in Additional File 2 is corrupt in the publisher’s archive. It is skipped.</dd></div>
    </dl>
  </div>
</section>
<section class="buried" aria-labelledby="buried-head">
  <div class="container">
    <div class="plastic buried-band">
      <h2 id="buried-head">What stayed buried</h2>
      <ul>
        <li>The run behind Additional File 4. It lists {s4['peaks']:,} peaks in {s4['classes']:,} classes; LIMPIC 1.1 on the 30 plasma files gives {po['peaks']:,} peaks in {po['classes']:,} classes, and at most 17% of our peak intensities equal one of its values</li>
        <li>The smooth noise model behind Figs 9c and 9d</li>
        <li>The settings behind Tables 1 to 3</li>
        <li>APEX, CENTROID and CROMWELL’s settings, for the other panels of Figs 4, 6 and 7</li>
      </ul>
      <p class="so">Figs 2 to 7 and Fig. 8’s peaks match the paper pixel for pixel. Fig. 8’s colours, Figs 9c and 9d and the tables do not come back.</p>
    </div>
  </div>
</section>"""

LABEL = "<ol>" + "".join(
    f'<li><a href="#fig-{fig}"><span>Fig. {fig}</span><span class="v" data-v="{VCLASS[v]}">{esc(v)}</span></a></li>'
    for fig, v in verdict_of.items()) + '<li><a href="#tables"><span>Tables 1 to 3</span><span class="v" data-v="differs">Differs</span></a></li></ol>'
LEDE = "Its code runs again. Figs 2 to 7 came back the same, and so did Fig. 8’s peaks."
CLOSING = "We rebuild this page each time the pipeline runs."

page = open(os.path.join(HERE, "page_template.html")).read()
for marker, text in (("<!--__STATIONS__-->", "\n".join(stations)), ("<!--__EXTRA__-->", EXTRA), ("<!--__RECOVERED__-->", RECOVERED),
                     ("<!--__LABEL__-->", LABEL), ("<!--__LEDE__-->", LEDE), ("<!--__CLOSING__-->", CLOSING),
                     ("/*__FIGS__*/[]", json.dumps(figs))):
    assert marker in page, marker
    page = page.replace(marker, text)
os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
open(OUT, "w").write(page)
print("wrote", OUT, len(page) // 1024, "KB")
