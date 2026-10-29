"""Build the comparison page for PMC4081021 from the pipeline outputs.

Usage: python build_page.py <output_dir> <published_dir> <out index.html>
<output_dir> holds fig{2..6}_redrawn.png and comparison.json (compare.py), tables.json
(make_tables.py) and port_check.json (check_port.py); after a --refit run also optima_check.json,
and tables.json then carries the refit of Table 1.
Each published figure is halved as compare.py halves its images, so the two share a pixel grid.
The page links ../results.css, the stylesheet the site's results pages share.
"""

import base64
import html
import io
import json
import os
import sys
from collections import defaultdict

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from check_reproduction import TABLE_EXCEPTIONS, pixel_checks  # noqa: E402

D, PUB, OUT = sys.argv[1:4]
load = lambda f: json.load(open(os.path.join(D, f)))  # noqa: E731
cmp, tab, port = load("comparison.json"), load("tables.json"), load("port_check.json")
optima = load("optima_check.json") if os.path.exists(os.path.join(D, "optima_check.json")) else None
MAX_W = 1500  # page images are scaled to this width; the scores come from the full-size files
CROP_ROWS = {"5": (1530, 2935)}  # Fig. 5: panel B only (published pixel rows), not the schematics or the pies

CAPTIONS = {
    "2": "A conversion process fitted by ODE constrained mixture modelling: homogeneous, non-overlapping subpopulations (B to D) and heterogeneous, highly overlapping ones (E to G).",
    "3": "NGF-induced Erk1/2 signalling without subpopulations: mean pErk against the data (B), histograms (C) and parameter estimates (D).",
    "4": "The same pathway with two subpopulations that differ in TrkA level: mean pErk (B), histograms (C) and parameter estimates (D).",
    "5": "Three pathway models compared by BIC across the nine hypotheses (B), and the subpopulation weights of their best model, M_H3,3 (C).",
    "6": "Joint distribution of pErk and total Erk in control cells (A) and after 1 nM NGF for 30 min (B), with a two-component normal mixture.",
}
VCLASS = {"Agrees": "agrees", "Partly agrees": "partly", "Differs": "differs"}
esc = html.escape
num = lambda v: f"{v:g}"  # noqa: E731
pct = lambda v: num(round(100 * v, 1)) + "%"  # noqa: E731
SUP = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")
word = lambda n: ["no", "one", "two", "three", "four", "five"][n] if n < 6 else str(n)  # noqa: E731


def sci(v):
    """0.00088 -> '9 × 10⁻⁴'"""
    m, e = f"{v:.0e}".split("e")
    return f"{m} × 10{str(int(e)).translate(SUP)}"


def model(m):
    return f"M<sub>{esc(m)}</sub>"


def b64_png(img):
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode()


def page_image(img):
    w, h = img.size
    if w <= MAX_W:
        return img
    return img.resize((MAX_W, round(h * MAX_W / w)), Image.LANCZOS)


def shared_palette(a, b, exact=64):
    """Both images in one 256-colour palette: the `exact` commonest colours as they are (the flat
    fills keep their hue), the rest by maximum coverage. Each colour goes to its nearest entry,
    without dithering, so equal pixels stay equal."""
    w = a.width
    both = Image.new("RGB", (w, a.height + b.height))
    both.paste(a, (0, 0))
    both.paste(b, (0, a.height))
    rgb = np.asarray(both).reshape(-1, 3).astype(np.int32)
    u, inv, n = np.unique(rgb[:, 0] << 16 | rgb[:, 1] << 8 | rgb[:, 2], return_inverse=True, return_counts=True)
    cols = np.stack([u >> 16, u >> 8 & 255, u & 255], 1)
    rest = both.quantize(256 - exact, method=Image.Quantize.MAXCOVERAGE).getpalette()[:3 * (256 - exact)]
    pal = np.vstack([cols[np.argsort(-n, kind="stable")[:exact]], np.reshape(rest, (-1, 3))])
    near = np.concatenate([((cols[i:i + 4096, None] - pal[None]) ** 2).sum(2).argmin(1) for i in range(0, len(cols), 4096)])
    q = Image.fromarray(near[inv].reshape(both.height, w).astype(np.uint8), "P")
    q.putpalette(pal.astype(np.uint8).flatten().tolist())
    return q.crop((0, 0, w, a.height)), q.crop((0, a.height, w, a.height + b.height))


def stamp(verdict, basis):
    return f'<span class="stamp" data-v="{VCLASS[verdict]}">{esc(verdict)}<small>{esc(basis)}</small></span>'


def head(hid, title, caption, right=""):
    return f'<header class="station-head"><h2 id="{hid}">{title}</h2><p class="caption">{caption}</p>{right}</header>'


def dose(rows):
    return "".join(f"<div><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>" for k, v in rows)


def plate(label, src, alt, w, h):
    return f'<figure class="plate"><figcaption>{esc(label)}</figcaption><img src="{src}" alt="{esc(alt)}" width="{w}" height="{h}"></figure>'


# The pipeline's own pixel checks; per panel letter, the lowest share each way.
lowest = defaultdict(lambda: [1.0, 1.0])
for _, fig, name, _, pm, om, _, _, _ in pixel_checks(cmp, "saved")[0]:
    lo = lowest[fig[3:], name.split(":")[0]]
    lo[0], lo[1] = min(lo[0], pm), min(lo[1], om)


def scores(fig):
    return [(f"{fig}{p}, ≤4 px both ways", f"{pct(a)} and {pct(b)}")
            for (f, p), (a, b) in sorted(lowest.items()) if f == fig]


f4, f5, f6 = cmp["fig4"], cmp["fig5"], cmp["fig6"]
supp = [c for k, v in tab.items() if k.startswith("supp_table1") for c in v["comparison"]]
bic_same = sum(c["saved"]["matches"]["BIC"] for c in supp)
w4 = [pct(w[0]) for w in f4["weights"]]
w5, w5p = f5["C_w1_percent"], f5["C_published_percent"]
rho = [f"{f6['rho_control']:.3f}", f"{f6['rho_stimulated']:.3f}"]
w6 = " / ".join(f"{w:.1f}" for w in f6["w_percent"]) + "%"
EXTRA_STATS = {
    "4": [("4B, w₁ (red, blue)", f"{w4[0]} and {w4[1]}")],
    "5": [("5B, BIC as in S1 Table 1", f"{bic_same} of {len(supp)}"),
          ("5C, w₁ ours (A, B, C)", ", ".join(f"{w:.1f}" for w in w5) + "%"),
          ("5C, w₁ published", ", ".join(f"{w:.1f}" for w in w5p) + "%")],
    "6": [("ρ, control and stimulated", " and ".join(rho)), ("Mixture weights", w6)],
}
# Notes are HTML.
NOTES = {
    "2": ("Both scenarios, drawn from the authors’ saved fits. The thin sample trajectories in B and E are 20 seeded "
          "draws of ours and are not scored. The dashed means in E averaged 500 random cells in the original; we draw "
          "their exact expectation. The interval bars in D and G come from the profile likelihoods the authors saved."),
    "3": (f"Pathway model A, {model('H1,2')} (red) and {model('H1,3')} (blue). The dose-response curves in B are the state at 60 min, not "
          "30: the data and the fit are at 30 min, but the plotting script reuses the kinetic panel’s time vector "
          "(0 to 60 min) and takes its last point. pErk has nearly settled by 30 min, so the curves barely move; we "
          "draw them as the script does."),
    "4": (f"{model('H3,2')} (red) and {model('H3,3')} (blue). The saved fits give the weights printed in B, {w4[0]} and {w4[1]}; the "
          "coloured “w = …%” labels are left out of the scores. As in Fig. 3, the dose-response curves are drawn at "
          "60 min."),
    "5": (f"Panel B only; A and C are cut from the images. All {len(supp)} BIC values equal S1 Table 1 at the printed "
          f"four digits. In C, w₁ of {model('H3,3')} is {w5[0]:.1f}% for pathway model A and {w5[2]:.1f}% for C, as published. "
          f"For model B the saved fit gives {w5[1]:.1f}%, where the pie reads {w5p[1]:.1f}%; no saved fit of model B "
          "gives that."),
    "6": (f"Correlations {rho[0]} and {rho[1]}, mixture weights {w6}, as published. MATLAB’s gmdistribution.fit stops "
          "EM when the log-likelihood changes by less than 10⁻⁶ of its value, and we stop it the same way; run to "
          "convergence, EM gives 68.1 / 31.9%. Panel B plots the control and stimulated cells together, as the "
          "script does."),
}
BASIS = {"6": "Python port of the script"}
VERDICTS = {"5": "Agrees" if w5 == w5p else "Partly agrees"}


figs, stations, verdict_of = [], [], {}
for fig in [str(i) for i in range(2, 7)]:
    pub = Image.open(os.path.join(PUB, f"figure-{fig}.png")).convert("RGB")
    full_w, full_h = pub.size
    pub = pub.resize((full_w // 2, full_h // 2), Image.LANCZOS)  # as compare.py saves its images
    ours = Image.open(os.path.join(D, f"fig{fig}_redrawn.png")).convert("RGB")
    assert pub.size == ours.size, (fig, pub.size, ours.size)
    if fig in CROP_ROWS:
        top, bottom = CROP_ROWS[fig]
        pub, ours = (im.crop((0, top // 2, im.width, bottom // 2)) for im in (pub, ours))
        full_h = bottom - top
    pub, ours = page_image(pub), page_image(ours)
    w, h = pub.size
    mean_d = float(np.abs(np.asarray(pub.convert("L"), float) - np.asarray(ours.convert("L"), float)).mean())
    pub, ours = shared_palette(pub, ours)
    verdict = VERDICTS.get(fig, "Agrees")
    verdict_of[fig] = verdict
    hid = f"fig-{fig}-head"
    stats = ([("Pixel size", f"{full_w} × {full_h}")] + scores(fig) + EXTRA_STATS.get(fig, [])
             + [("Mean |Δ| grey", num(round(mean_d, 2)))])
    figs.append(dict(id=fig, w=w, h=h))
    caption = esc(CAPTIONS[fig]).replace("M_H3,3", model("H3,3"))
    stations.append(
        f'<section class="station surface" id="fig-{fig}" aria-labelledby="{hid}">'
        + head(hid, f"Fig. {fig}", caption, stamp(verdict, BASIS.get(fig, "Python port, saved fits")))
        + '<div class="stage"><div class="pair">'
        + plate("Published", "data:image/png;base64," + b64_png(pub), f"Figure {fig} as published", w, h)
        + plate("Our run", "data:image/png;base64," + b64_png(ours), f"Figure {fig} redrawn from our run", w, h)
        + "</div></div>"
        + f'<div class="station-foot"><dl class="dose">{dose(stats)}</dl><p class="note">{NOTES[fig]}</p></div></section>')


# Tables 1 and 2: each field as printed against ours at the printed precision.
def minus(v):
    return str(v).replace("-", "−")


def table_rows(comparison):
    out = []
    for c in comparison:
        p, o, m = c["published"], c["saved"], c["saved"]["matches"]

        def pair(f):
            mark = (lambda s: s) if m[f] else (lambda s: f"<strong>{s}</strong>")
            return f"<td class=num>{mark(esc(minus(p[f])))}</td><td class=num>{mark(esc(minus(o[f])))}</td>"

        def once(f):
            return esc(minus(p[f])) if m[f] else f"<strong>{esc(minus(p[f]))}</strong> (ours {esc(minus(o[f]))})"

        out.append(f"<tr><td>{model(c['model'])}</td>{pair('logL')}{pair('BIC')}{pair('rank')}"
                   f"<td class=num>{once('dBIC')}</td><td>{once('decision').replace(' ', '&nbsp;')}</td></tr>")
    return "".join(out)


THEAD = ('<thead><tr><th scope="col">Model</th><th scope="col" class=num>ℓ(θ*) paper</th><th scope="col" class=num>ℓ(θ*) ours</th>'
         '<th scope="col" class=num>BIC paper</th><th scope="col" class=num>BIC ours</th><th scope="col" class=num>Rank paper</th>'
         '<th scope="col" class=num>Rank ours</th><th scope="col" class=num>ΔBIC</th><th scope="col">Decision</th></tr></thead>')


def table(caption, key):
    # the caption sits outside the sideways scroll, so it wraps on a phone
    return (f'<figure class="table-fig"><figcaption>{caption}</figcaption><div class="table-wrap"><table class="record dense">'
            f'{THEAD}<tbody>{table_rows(tab[key]["comparison"])}</tbody></table></div></figure>')


def fields(keys, kind="saved"):
    n = same = 0
    for k in keys:
        for c in tab[k]["comparison"]:
            if kind in c:
                n += len(c[kind]["matches"])
                same += sum(c[kind]["matches"].values())
    return same, n


T1 = ("table1_cr1", "table1_cr2")
SUPP = tuple(k for k in tab if k.startswith("supp_table1"))
refit = all("refit" in c for k in T1 for c in tab[k]["comparison"])
slips = [(k, c["model"], f, c["published"][f], c["saved"][f]) for k in T1 for c in tab[k]["comparison"]
         for f, ok in c["saved"]["matches"].items() if not ok]
assert {(k, m, f) for k, m, f, _, _ in slips} == TABLE_EXCEPTIONS, slips
h31 = next(r for r in tab["table1_cr1"]["rows"] if r["model"] == "H3,1")
c31 = next(c for c in tab["table1_cr1"]["comparison"] if c["model"] == "H3,1")
h1 = [c for c in tab["table1_cr2"]["comparison"] if c["model"].startswith("H1,")]
and_ = lambda xs: ", ".join(xs[:-1]) + " and " + xs[-1]  # noqa: E731
t1_same, t1_n = fields(T1)
rest_n = fields(("table2",) + SUPP)[1]
count_rows = [("Table 1, saved fits", fields(T1)), ("Table 2", fields(("table2",))), ("S1 Table 1", fields(SUPP))]
if refit:
    count_rows.insert(1, ("Table 1, our refit", fields(T1, "refit")))
counts = "".join(f"<tr><td>{name}</td><td class=num>{s} of {n}</td></tr>" for name, (s, n) in count_rows)
refit_note = (" Refitted from scratch, the 24 models give the same table, slips and all."
              if refit and fields(T1, "refit") == fields(T1) else "")
EXTRA = f"""<section class="container after-bench" aria-labelledby="tables-head">
  <div class="station surface" id="tables">
    <header class="station-head"><h2 id="tables-head">Tables 1 and 2</h2><p class="caption">Model selection for the conversion process in both scenarios (Table 1) and for NGF-induced Erk1/2 signalling, pathway model A (Table 2): log-likelihood at the optimum, BIC, rank, ΔBIC and decision.</p>{stamp("Agrees", "Python port, saved fits")}</header>
    {table("Table 1, scenario 1: homogeneous, non-overlapping subpopulations. ℓ and BIC in 10⁴; bold where the printed value differs from ours.", "table1_cr1")}
    {table("Table 1, scenario 2: heterogeneous, highly overlapping subpopulations. ℓ and BIC in 10³.", "table1_cr2")}
    {table("Table 2, pathway model A. ℓ and BIC in 10⁴.", "table2")}
    <div class="split">
      <div class="side side--lead">
        <div class="table-wrap"><table class="record dense"><thead><tr><th scope="col">Fields as printed</th><th scope="col" class=num>Ours</th></tr></thead><tbody>{counts}</tbody></table></div>
      </div>
      <div class="wide">
        <p class="note">{t1_same} of Table 1’s {t1_n} fields come back as printed, and all {rest_n} of Table 2 and S1 Table 1, which adds pathway models B and C. The {word(len(slips))} others are slips in the paper. Scenario 1’s {model("H3,1")} has ℓ = {h31["saved_logL"]:,.2f}, which rounds to {c31["saved"]["logL"]} × 10⁴, not the printed {c31["published"]["logL"]}. In scenario 2 the paper ranks {and_([model(c["model"]) for c in h1])} {and_([c["published"]["rank"] for c in h1])}, but its own BICs for them, {and_([minus(c["published"]["BIC"]) for c in h1])}, put them {and_([str(c["saved"]["rank"]) for c in h1])}.{refit_note}</p>
      </div>
    </div>
  </div>
</section>"""


refit_row = ""
if refit:
    rows = [r for k in T1 for r in tab[k]["rows"]]
    at_best = [r["refit_at_best"] for r in rows]
    gap = max(abs(r["refit_logL"] - r["saved_logL"]) for r in rows)
    refit_row = (f'<div class="row"><dt>Table 1, refitted</dt><dd>All {len(rows)} conversion-reaction models, fitted again from scratch: '
                 f'{rows[0]["refit_starts"]:,} Latin hypercube starts each inside the authors’ bounds, L-BFGS-B with exact gradients '
                 f'from JAX. Every one reaches the saved optimum (within {sci(gap)} in ℓ); the best value is found by '
                 f'{min(at_best)} to {max(at_best):,} of the starts.</dd></div>')
optima_row = ""
if optima:
    fin = [r for r in optima if r["local_gain"] != float("inf")]
    failed = [r for r in optima if r["local_gain"] == float("inf")]
    optima_row = (f'<div class="row"><dt>The saved optima hold</dt><dd>For {len(fin)} of the {len(optima)} saved optima the exact '
                  f'gradient was computed, and a local L-BFGS-B run started there gains at most {sci(max(r["local_gain"] for r in fin))} '
                  f'in ℓ.' + (f' The JAX solver fails at the other {word(len(failed))}; the numpy port reproduces their ℓ.' if failed else "")
                  + '</dd></div>')
RECOVERED = f"""<section class="notes" aria-labelledby="back-head">
  <div class="container">
    <h2 id="back-head">What came back</h2>
    <dl class="ledger">
      <div class="row"><dt>The likelihood in Python</dt><dd><span class="mono">odemm.py</span> reads each model (rates, mean or median constraint, noise parameters, weights) from the authors’ fitting script and evaluates <span class="mono">logLikelihood.m</span>. At the {len(port["models"])} saved optima it gives the saved log-likelihood to within {sci(port["max_abs_diff_logL"])}. The conversion reaction is solved in closed form, where the authors used CVODES.</dd></div>
      <div class="row"><dt>Every panel, as the scripts plot it</dt><dd>MATLAB’s <span class="mono">hist</span> with bin centres, the staircase fills, <span class="mono">pchip</span> interpolation of the noise parameters and intervals from <span class="mono">getConfidenceIntervals.m</span>, all from the optima, Hessians and profile likelihoods the authors saved in Code S1.</dd></div>
      {refit_row}{optima_row}
      <div class="row"><dt>Fig. 6’s early stop</dt><dd>From a random start, EM stopped by MATLAB’s rule ends at 68.0 / 32.0% in 289 of 300 starts. Run to convergence it gives 68.1 / 31.9%, so the published weights carry MATLAB’s stopping rule.</dd></div>
      <div class="row"><dt>A mislabelled time point</dt><dd>The kinetic data file labels its second time point “10 min”. The scripts and the paper use 5 min, and so do we.</dd></div>
    </dl>
  </div>
</section>
<section class="buried" aria-labelledby="buried-head">
  <div class="container">
    <div class="plastic buried-band">
      <h2 id="buried-head">What stayed buried</h2>
      <ul>
        <li>The fit behind Fig. 5C’s {w5p[1]:.1f}% for pathway model B. Its saved {model("H3,3")} gives {w5[1]:.1f}%</li>
        <li>The 500 random cells behind the dashed means of Fig. 2E, and the sample trajectories drawn in Figs 2B and 2E</li>
        <li>A blind refit of the NGF models. At the authors’ start counts, L-BFGS-B does not reach the saved optima of pathway model A (ℓ = −43,278 against −40,348 for {model("H2,1")}): about half the starts fail in the ODE solve at the extreme rates the bounds allow</li>
      </ul>
      <p class="so">Figs 2 to 6 and the three tables come back from the authors’ saved fits. One pie in Fig. 5C does not.</p>
    </div>
  </div>
</section>"""

LABEL = "<ol>" + "".join(
    f'<li><a href="#fig-{fig}"><span>Fig. {fig}</span><span class="v" data-v="{VCLASS[v]}">{esc(v)}</span></a></li>'
    for fig, v in verdict_of.items()) + '<li><a href="#tables"><span>Tables 1 and 2</span><span class="v" data-v="agrees">Agrees</span></a></li></ol>'
LEDE = "Its likelihood runs again, in Python. Figs 2 to 6 and the tables came back from the authors’ saved fits; one pie in Fig. 5C did not."
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
