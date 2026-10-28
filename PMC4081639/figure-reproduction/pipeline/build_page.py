"""Build the comparison page for PMC4081639 from the pipeline outputs.

Usage: python3 build_page.py [out index.html]
Inputs come from FOSSIL_PUBLISHED, FOSSIL_OUTPUT and FOSSIL_DATA (defaults: ../published, ../output, here).
The page links ../results.css, the stylesheet the site's results pages share.
"""
import base64, html, io, json, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
PAPER = os.environ.get("FOSSIL_PUBLISHED", os.path.join(HERE, "..", "published"))
OUTDIR = os.environ.get("FOSSIL_OUTPUT", os.path.join(HERE, "..", "output"))
T1DIR = os.environ.get("FOSSIL_DATA", HERE)
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "..", "..", "site", "PMC4081639", "index.html")

final = {f: json.load(open(f"{OUTDIR}/fig{f}.json")) for f in "2456"}

CAPTIONS = {
    "2": "The function implementing (6) is unstable when ψ approaches 0. x = (2, 3, 1), p = (.2, .3, .5).",
    "4": "Mesh vs aod(dirmult) when ψ varies near 0. x = (2, 3, 1), p = (.2, .3, .5).",
    "5": "Error of mesh vs the method in VGAM. x = n(1, 1, 1, 1), ψ = 1/200, p = (.1, .2, .3, .4).",
    "6": "Runtime of mesh vs VGAM, 100 evaluations per box. x = n(1, 2, 3), p = (1/6, 1/3, 1/2), ψ = 1/60.",
}
DATA = {
    "2": ("identical", "Same data as the paper. ψ = seq(1e-11, 1e-10, length.out = 300); Eq. (6) evaluated as R’s lgammafn with x86 (no-FMA) arithmetic and 80-bit sum(). The curve covers 100% of the paper’s curve pixels and vice versa."),
    "4": ("identical", "The aod,dirmult curve is the Fig. 2 series, identical to the paper. The mesh values come from the authors’ compiled library (lldmn); their error is below 1e-15, so the line is flat at this scale, as in the paper."),
    "5": ("partial", "Shown on the paper’s y-axis (−2395 to 2401 × 10⁻¹⁴, gridlines every 1000), so the frame and tick labels coincide; none of our points fall outside it. Same n grid (200…10000, step 200), with errors counted in whole ulps as in the paper. The ulp-level noise depends on the exact 2013 build: our VGAM R code reproduces 26 of the 50 published marks, and the authors’ mesh library run here under Rosetta gives 1 to 3 ulp errors where the paper shows 0."),
    "6": ("remeasured", "Shown on the paper’s own axis (0.27 to 510 µs; breaks 1, 10, 100). Timings were measured on this Mac, then each method was divided by one constant fitted to the paper’s box medians (least squares in log10): mesh ÷13.2, VGAM ÷27.3. Mesh runs 13.2 to 13.3× slower than the paper’s at every n, so after that one constant its growth with n matches the paper exactly. For VGAM the ratio climbs from 4.3× (n = 100) to 77× (n = 10⁴): our R code for Eq. (7) grows linearly with n, while the paper’s VGAM barely changes between n = 100 and 1000 (2.1 to 2.5 µs). One VGAM outlier at 10⁵ falls above the axis and is clipped."),
}

VERDICTS = {"2": "Agrees", "4": "Agrees", "5": "Partly agrees", "6": "Partly agrees"}

# What each reproduction is drawn from, printed under its verdict.
BASIS = {"identical": "Identical data", "partial": "Same setup, ulp noise differs", "remeasured": "Re-timed, scaled to the paper’s axis"}
VCLASS = {"Agrees": "agrees", "Partly agrees": "partly", "Differs": "differs", "Running": "running"}
esc = html.escape
num = lambda v: f"{v:g}"  # prints a number the way the page's script would (100.0 as 100)


def b64(path_or_img, fmt="PNG"):
    if isinstance(path_or_img, str):
        return base64.b64encode(open(path_or_img, "rb").read()).decode()
    buf = io.BytesIO(); path_or_img.save(buf, fmt, optimize=True); return base64.b64encode(buf.getvalue()).decode()


MEASURED6 = "Raw timings on this Mac, not the paper’s 2013 Xeon. Mesh: native C port of the algorithm, checked against the authors’ library to ≤1 ulp. VGAM: Eq. (7) as R code (as the paper describes), timed with microbenchmark, 100 evaluations each. The y-axis follows these timings."


def stats(P, png):
    O = np.asarray(Image.open(png).convert("L")).astype(float); d = np.abs(P - O)
    return round(float(d.mean()), 2), round(float((d <= 24).mean() * 100), 1)


def dose(W, H, dpix, dpiy, panel, mad, within, w, h):
    rows = [("Pixel size", f"{w} × {h}"), ("Drawn at", f"{num(W)} × {num(H)} in"),
            ("Rasterised", f"{num(dpix)} dpi" if dpix == dpiy else f"{num(dpix)} × {num(dpiy)} dpi"),
            ("Panel fill", panel), ("Mean |Δ| grey", num(mad)), ("Pixels within ±24", num(within) + "%")]
    return "".join(f"<div><dt>{esc(k)}</dt><dd>{esc(str(v))}</dd></div>" for k, v in rows)


def stamp(verdict, basis):
    return f'<span class="stamp" data-v="{VCLASS[verdict]}">{esc(verdict)}<small>{esc(basis)}</small></span>'


def head(hid, title, caption, right):
    return f'<header class="station-head"><h2 id="{hid}">{title}</h2><p class="caption">{caption}</p>{right}</header>'


def plate(label, src, alt, w, h):
    return f'<figure class="plate"><figcaption>{esc(label)}</figcaption><img src="{src}" alt="{esc(alt)}" width="{w}" height="{h}"></figure>'


figs, stations = [], []
for fig in ("2", "4", "5", "6"):
    f = final[fig]
    P = np.asarray(Image.open(f"{PAPER}/figure-{fig}.jpg").convert("L")).astype(float)
    O = np.asarray(Image.open(f"{OUTDIR}/fig{fig}_ours.png").convert("L")).astype(float)
    d = np.abs(P - O)
    w, h = P.shape[1], P.shape[0]
    W, H, mad, within = round(f["W"], 2), round(f["H"], 2), round(float(d.mean()), 2), round(float((d <= 24).mean() * 100), 1)
    base = dose(W, H, f["dpi"], f["dpiy"], f["panel"], mad, within, w, h)
    entry = dict(id=fig, w=w, h=h)
    if fig == "5":
        m = json.load(open(f"{OUTDIR}/fig5_own.json"))
        mad2, within2 = stats(P, f"{OUTDIR}/fig5_own_ours.png")
        entry["variants"] = [
            dict(label="On the paper’s axis", ours=None, note=DATA[fig][1], stats=base),
            dict(label="Own axis range", ours="data:image/png;base64," + b64(Image.open(f"{OUTDIR}/fig5_own_ours.png").convert("L")),
                 note="Same data on ggplot’s automatic y-range, which follows our values (−1091 to 2183 × 10⁻¹⁴). The tick positions therefore differ from the paper’s.",
                 stats=dose(round(m["W"], 2), round(m["H"], 2), m["dpi"], m.get("dpiy", m["dpi"]), f["panel"], mad2, within2, w, h)),
        ]
    if fig == "6":
        m = json.load(open(f"{OUTDIR}/fig6_measured.json"))
        mad2, within2 = stats(P, f"{OUTDIR}/fig6_measured_ours.png")
        entry["variants"] = [
            dict(label="On the paper’s axis", ours=None, note=DATA[fig][1], stats=base),
            dict(label="Measured µs", ours="data:image/png;base64," + b64(Image.open(f"{OUTDIR}/fig6_measured_ours.png").convert("L")),
                 note=MEASURED6, stats=dose(round(m["W"], 2), round(m["H"], 2), m["dpi"], m.get("dpiy", m["dpi"]), f["panel"], mad2, within2, w, h)),
        ]
    figs.append(entry)
    hid = f"fig-{fig}-head"
    stations.append(
        f'<section class="station surface" id="fig-{fig}" aria-labelledby="{hid}">'
        + head(hid, f"Fig. {fig}", esc(CAPTIONS[fig]), stamp(VERDICTS[fig], BASIS[DATA[fig][0]]))
        + '<div class="stage"><div class="pair">'
        + plate("Published", "data:image/jpeg;base64," + b64(f"{PAPER}/figure-{fig}.jpg"), f"Figure {fig} as published", w, h)
        + plate("Reproduction in ggplot2 and tikzDevice", "data:image/png;base64," + b64(Image.open(f"{OUTDIR}/fig{fig}_ours.png").convert("L")), f"Figure {fig} reproduced", w, h)
        + '</div></div>'
        + f'<div class="station-foot"><dl class="dose">{base}</dl><p class="note">{esc(DATA[fig][1])}</p></div></section>')

t1 = json.load(open(os.path.join(T1DIR, "table1_result.json")))
NAMES = {"saliva": "Saliva", "throat": "Throat", "tongue": "Tongue", "tonsils": "Tonsils"}
def jtable(label, col):
    rows = "".join(f"<tr><td>{NAMES[k]}</td><td class=num>{col(v)}</td></tr>" for k, v in t1.items())
    return f'<figure class="jt"><figcaption>{label}</figcaption><table><thead><tr><th scope="col">Body site</th><th scope="col" class=num><i>ψ</i></th></tr></thead><tbody>{rows}</tbody></table></figure>'
detail = "".join(
    f"<tr><td>{NAMES[k]}</td><td class=num data-label=\"Samples\">{v['samples']}</td><td class=num data-label=\"Reads\">{v['reads']:,}</td><td class=num data-label=\"MLE ψ (6 d.p.)\">{v['psi']:.6f}</td><td class=num data-label=\"Paper\">{v['paper']:.5f}</td>"
    f"<td class=num data-label=\"Match\">{'✓' if round(v['psi'], 5) == v['paper'] else '✗'}</td></tr>" for k, v in t1.items())
TABLE1 = f"""<section class="container after-bench" aria-labelledby="table-1-head">
  <div class="station surface" id="table-1">
    {head("table-1-head", "Table 1", "The MLE of the dispersion parameters of the 16S rRNA pyrosequencing data from all four body sites.", stamp("Agrees", "All four match to 5 decimals"))}
    <div class="split">
      <div class="side side--lead"><div class="jt-pair">{jtable("Published", lambda v: f"{v['paper']:.5f}")}{jtable("Reproduced", lambda v: f"{round(v['psi'], 5):.5f}")}</div></div>
      <div class="wide">
        <div class="table-wrap"><table class="record stack"><thead><tr><th scope="col">Body site</th><th scope="col" class=num>Samples</th><th scope="col" class=num>Reads</th><th scope="col" class=num>MLE <i>ψ</i> (6 d.p.)</th><th scope="col" class=num>Paper</th><th scope="col" class=num>Match</th></tr></thead><tbody>{detail}</tbody></table></div>
        <p class="note">Data: the HMP saliva, throat, tongue and tonsils count matrices (21 taxa) from the archived CRAN package HMP 2.0.1 (Apache-2.0). Maximum likelihood over all 21 Dirichlet parameters, with the log-likelihood from the mesh algorithm and exact digamma gradients (L-BFGS-B, four starting values of ψ, each fit in about 0.1 s). Checks: the plain lgamma formula agrees with mesh at the optimum to within 5e-10, and a ψ scan peaks at the fitted value. A separate pure-Python fit with finite-difference gradients (about 20 min per site) gives the same ψ to six decimals.</p>
      </div>
    </div>
  </div>
</section>"""

# The hero's label lists every figure and Table 1 with its verdict; the lede counts what came back.
items = [(f"fig-{k}", f"Fig. {k}", v) for k, v in VERDICTS.items()] + [("table-1", "Table 1", "Agrees")]
LABEL = "<ol>" + "".join(
    f'<li><a href="#{a}"><span>{n}</span><span class="v" data-v="{VCLASS[v]}">{esc(v)}</span></a></li>' for a, n, v in items) + "</ol>"
COUNT = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six"}
LEDE = f"Its data, its algorithm, {COUNT.get(len(figs), len(figs))} figures and Table 1 are back."

page = open(f"{HERE}/page_template.html").read()
for marker, text in (("<!--__STATIONS__-->", "\n".join(stations)), ("<!--__TABLE1__-->", TABLE1),
                     ("<!--__LABEL__-->", LABEL), ("<!--__LEDE__-->", LEDE), ("/*__FIGS__*/[]", json.dumps(figs))):
    assert marker in page, marker
    page = page.replace(marker, text)
os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
assert "__TABLE1__" not in page
open(OUT, "w").write(page)
print("wrote", OUT, len(page) // 1024, "KB")
