import base64, io, json, os, sys
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
    "2": ("identical", "Same data as the paper. ψ = seq(1e-11, 1e-10, length.out = 300); Eq. (6) evaluated as R's lgammafn with x86 (no-FMA) arithmetic and 80-bit sum(). The curve covers 100% of the paper's curve pixels and vice versa."),
    "4": ("identical", "The aod,dirmult curve is the Fig. 2 series, identical to the paper. The mesh values come from the authors' compiled library (lldmn); their error is below 1e-15, so the line is flat at this scale, as in the paper."),
    "5": ("partial", "Shown on the paper's y-axis (−2395 to 2401 × 10⁻¹⁴, gridlines every 1000), so the frame and tick labels coincide; none of our points fall outside it. Same n grid (200…10000, step 200), with errors counted in whole ulps as in the paper. The ulp-level noise depends on the exact 2013 build: our VGAM R code reproduces 26 of the 50 published marks, and the authors' mesh library run here under Rosetta gives 1–3-ulp errors where the paper shows 0."),
    "6": ("remeasured", "Shown on the paper's own axis (0.27–510 µs; breaks 1, 10, 100). Timings were measured on this Mac, then each method was divided by one constant fitted to the paper's box medians (least squares in log10): mesh ÷13.2, VGAM ÷27.3. Mesh runs 13.2–13.3× slower than the paper's at every n, so after that one constant its growth with n matches the paper exactly. For VGAM the ratio climbs from 4.3× (n = 100) to 77× (n = 10⁴): our R code for Eq. (7) grows linearly with n, while the paper's VGAM barely changes between n = 100 and 1000 (2.1 → 2.5 µs). One VGAM outlier at 10⁵ falls above the axis and is clipped."),
}

VERDICTS = {"2": "Agrees", "4": "Agrees", "5": "Partly agrees", "6": "Partly agrees"}


def b64(path_or_img, fmt="PNG"):
    if isinstance(path_or_img, str):
        return base64.b64encode(open(path_or_img, "rb").read()).decode()
    buf = io.BytesIO(); path_or_img.save(buf, fmt, optimize=True); return base64.b64encode(buf.getvalue()).decode()


MEASURED6 = "Raw timings on this Mac, not the paper's 2013 Xeon. Mesh: native C port of the algorithm, checked against the authors' library to ≤1 ulp. VGAM: Eq. (7) as R code (as the paper describes), timed with microbenchmark, 100 evaluations each. The y-axis follows these timings."


def stats(P, png):
    O = np.asarray(Image.open(png).convert("L")).astype(float); d = np.abs(P - O)
    return round(float(d.mean()), 2), round(float((d <= 24).mean() * 100), 1)


figs = []
for fig in ("2", "4", "5", "6"):
    f = final[fig]
    P = np.asarray(Image.open(f"{PAPER}/figure-{fig}.jpg").convert("L")).astype(float)
    O = np.asarray(Image.open(f"{OUTDIR}/fig{fig}_ours.png").convert("L")).astype(float)
    d = np.abs(P - O)
    figs.append(dict(
        id=fig, caption=CAPTIONS[fig], data_status=DATA[fig][0], data_note=DATA[fig][1], verdict=VERDICTS[fig],
        w=P.shape[1], h=P.shape[0],
        paper="data:image/jpeg;base64," + b64(f"{PAPER}/figure-{fig}.jpg"),
        ours="data:image/png;base64," + b64(Image.open(f"{OUTDIR}/fig{fig}_ours.png").convert("L")),
        W=round(f["W"], 2), H=round(f["H"], 2), dpix=f["dpi"], dpiy=f["dpiy"],
        mad=round(float(d.mean()), 2), within=round(float((d <= 24).mean() * 100), 1),
        panel=f["panel"], strip=f.get("strip"), ytitle=f["p"].get("ytitle_size", 12),
    ))
    if fig == "5":
        m = json.load(open(f"{OUTDIR}/fig5_own.json"))
        mad2, within2 = stats(P, f"{OUTDIR}/fig5_own_ours.png")
        figs[-1]["variants"] = [
            dict(label="On the paper's axis", ours=figs[-1]["ours"], note=figs[-1]["data_note"], W=figs[-1]["W"], H=figs[-1]["H"], dpix=f["dpi"], dpiy=f["dpiy"], mad=figs[-1]["mad"], within=figs[-1]["within"]),
            dict(label="Own axis range", ours="data:image/png;base64," + b64(Image.open(f"{OUTDIR}/fig5_own_ours.png").convert("L")),
                 note="Same data on ggplot's automatic y-range, which follows our values (−1091 to 2183 × 10⁻¹⁴). The tick positions therefore differ from the paper's.", W=round(m["W"], 2), H=round(m["H"], 2), dpix=m["dpi"], dpiy=m.get("dpiy", m["dpi"]), mad=mad2, within=within2),
        ]
    if fig == "6":
        m = json.load(open(f"{OUTDIR}/fig6_measured.json"))
        mad2, within2 = stats(P, f"{OUTDIR}/fig6_measured_ours.png")
        figs[-1]["variants"] = [
            dict(label="On the paper's axis", ours=figs[-1]["ours"], note=figs[-1]["data_note"], W=figs[-1]["W"], H=figs[-1]["H"], dpix=f["dpi"], dpiy=f["dpiy"], mad=figs[-1]["mad"], within=figs[-1]["within"]),
            dict(label="Measured µs", ours="data:image/png;base64," + b64(Image.open(f"{OUTDIR}/fig6_measured_ours.png").convert("L")),
                 note=MEASURED6, W=round(m["W"], 2), H=round(m["H"], 2), dpix=m["dpi"], dpiy=m.get("dpiy", m["dpi"]), mad=mad2, within=within2),
        ]

t1 = json.load(open(os.path.join(T1DIR, "table1_result.json")))
NAMES = {"saliva": "Saliva", "throat": "Throat", "tongue": "Tongue", "tonsils": "Tonsils"}
def jtable(label, col):
    rows = "".join(f"<tr><td>{NAMES[k]}</td><td class=num>{col(v)}</td></tr>" for k, v in t1.items())
    return f'<div class="jt"><span class="label">{label}</span><table><thead><tr><th>Body site</th><th class=num><i>ψ</i></th></tr></thead><tbody>{rows}</tbody></table></div>'
detail = "".join(
    f"<tr><td>{NAMES[k]}</td><td class=num>{v['samples']}</td><td class=num>{v['reads']:,}</td><td class=num>{v['psi']:.6f}</td><td class=num>{v['paper']:.5f}</td>"
    f"<td class=num>{'✓' if round(v['psi'], 5) == v['paper'] else '✗'}</td></tr>" for k, v in t1.items())
TABLE1 = f"""<section class="card" aria-label="Table 1">
  <div class="card-head"><h2>Table 1</h2><span class="pill agrees"><span aria-hidden="true">✓</span>Agrees</span><span class="badge identical">All four match to 5 decimals</span>
  <p>The MLE of the dispersion parameters of the 16S rRNA pyrosequencing data from all four body sites.</p></div>
  <div class="t1pair">{jtable("Published", lambda v: f"{v['paper']:.5f}")}{jtable("Reproduced", lambda v: f"{round(v['psi'], 5):.5f}")}</div>
  <div class="stage"><table class="detail"><thead><tr><th>Body site</th><th class=num>Samples</th><th class=num>Reads</th><th class=num>MLE <i>ψ</i> (6 d.p.)</th><th class=num>Paper</th><th class=num>Match</th></tr></thead><tbody>{detail}</tbody></table></div>
  <p class="note">Data: the HMP saliva, throat, tongue and tonsils count matrices (21 taxa) from the archived CRAN package HMP 2.0.1 (Apache-2.0). Maximum likelihood over all 21 Dirichlet parameters, with the log-likelihood from the mesh algorithm and exact digamma gradients (L-BFGS-B, four starting values of ψ, each fit in about 0.1 s). Checks: the plain lgamma formula agrees with mesh at the optimum to within 5e-10, and a ψ scan peaks at the fitted value. A separate pure-Python fit with finite-difference gradients (about 20 min per site) gives the same ψ to six decimals.</p>
</section>"""
page = open(f"{HERE}/page_template.html").read().replace("<!--__TABLE1__-->", TABLE1)
page = page.replace("/*__FIGS__*/[]", json.dumps(figs))
page = page.replace('<span class="eyebrow">', '<a class="back" href="../">← fossil</a>\n    <span class="eyebrow">', 1)
HEAD = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
        '<style>:root{padding:env(safe-area-inset-top,0) 0 env(safe-area-inset-bottom,0)}body{margin:0}img{max-width:100%}[hidden]{display:none!important}'
        '.back{font-size:13px;color:var(--accent);text-decoration:none}.back:hover{text-decoration:underline}</style>\n</head>\n<body>\n')
i = page.index("</style>") + len("</style>")
page = HEAD.replace("</head>\n<body>\n", "") + page[:i] + "\n</head>\n<body>\n" + page[i:] + "\n</body>\n</html>\n"
os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
assert "__TABLE1__" not in page
open(OUT, "w").write(page)
print("wrote", OUT, len(page) // 1024, "KB")
