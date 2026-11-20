"""Build the results page from results.json, the renders and the published figure.

Usage: build_page.py RESULTS_JSON FIG_DIR PUBLISHED_DIR OUT_DIR   (writes OUT_DIR/index.html)

Every verdict and number on the page is read from results.json (verdicts computed there by
check_results.py); the prose that is not a number comes from results_notes.json ("page"), with its numbers
filled from results.json. Images are embedded, so the page works offline; it links ../results.css like the
site's other results pages.
"""
import base64
import html
import io
import json
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from check_results import field_matches  # noqa: E402

esc = html.escape
STAMP = {"exact": ("agrees", "Exact"), "agrees": ("agrees", "Agrees"), "partly": ("partly", "Partly agrees"),
         "inconclusive": ("partly", "Inconclusive"), "differs": ("differs", "Differs")}
PANELS = {"a": (0, 390), "b": (390, 776)}  # rows of Fig. 1's two panels in the published picture
CAPTIONS = {
    "a": "Fig. 1A. Net relative risk reduction against the 5-year control event rate, when treatment halves the risk but adds 3 complications per 1,000 treated per year.",
    "b": "Fig. 1B. Power (AUROC) of one RF and of a score of four RFs (OR 2, prevalence 25%) at four average control event rates. Ours is written into the cells; in the overlay it is in green under the paper's.",
}
STYLE = """<style>
table.cells { border-collapse: collapse; font-family: var(--font-outlier); font-size: var(--text-xs); }
table.cells th, table.cells td { padding: 2px 6px; text-align: right; border-top: var(--rule-hair) solid var(--color-rule); }
table.cells th { font-weight: 500; color: var(--color-muted); text-align: left; }
table.cells td.off { background: var(--color-paper-3); font-weight: 500; }
table.cells td small { color: var(--color-muted); }
.cellgrid { display: grid; gap: var(--space-lg); }
</style>"""


def b64(im):
    buf = io.BytesIO()
    im.convert("RGB").save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode(), im.size


def crop(path, panel):
    y0, y1 = PANELS[panel]
    im = Image.open(path).convert("RGB")
    return im.crop((0, y0, im.size[0], y1))


def stamp(v):
    if v == "not_attempted":
        return '<span class="stamp" data-v="running">Not attempted</span>'
    cls, word = STAMP[v]
    return f'<span class="stamp" data-v="{cls}">{esc(word)}</span>'


def worst(vs):
    order = ["differs", "inconclusive", "partly", "agrees", "exact"]
    vs = [v for v in vs if v in order]
    return min(vs, key=order.index) if vs else "not_attempted"


def ok(it, f):
    return field_matches(f, it["values"].get("tolerance"))


def hits(it):
    f = it["values"]["fields"]
    return sum(ok(it, x) for x in f), len(f)


def fmt(v, like=None):
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        if isinstance(like, str):
            try:
                float(like)
                dec = len(like.split(".")[1]) if "." in like else 0
                return f"{v:.{max(dec, 2) if dec else 1}f}"
            except ValueError:
                pass
        return f"{v:.4g}"
    return str(v)


def measure(it):
    if it["method"] == "values":
        h, n = hits(it)
        return f"{h} of {n} values within tolerance"
    if it["method"] == "pixels":
        p = it["pixels"]
        s = min(p["published_near_ours"], p["ours_near_published"])
        best = max(c["score"] for c in p["controls"])
        return f"{100 * s:.1f}% of the curve within {p['tolerance_px']} px both ways (pass {100 * p['threshold']:.0f}%, best control {100 * best:.1f}%)"
    if it["method"] == "check":
        return it["check"]["detail"]
    return ""


def cell_table(it):
    rows = []
    for f in it["values"]["fields"]:
        cls = "" if ok(it, f) else "off"
        tol = f.get("tolerance", {}).get("abs")
        rows.append(f'<tr><th scope="row">{esc(f["name"])}</th><td>{esc(str(f["expected"]))}</td>'
                    f'<td class="{cls}">{esc(fmt(f["observed"], f["expected"]))}</td>'
                    f'<td><small>{"±" + fmt(tol, f["expected"]) if tol else "printed"}</small></td></tr>')
    return ('<div class="table-wrap"><table class="cells" aria-label="' + esc(it["label"]) + '"><thead><tr><th scope="col">Value</th>'
            '<th scope="col">Paper</th><th scope="col">Ours</th><th scope="col">Tolerance</th></tr></thead><tbody>'
            + "".join(rows) + "</tbody></table></div>")


def main(results, figs, pub, out):
    R = json.loads(Path(results).read_text())
    sm = R["summary"]
    by = {i["id"]: i for i in R["items"]}
    attempted = sm["items"] - sm["not_attempted"]
    facts = {"attempted": attempted, "exact_agrees": sm["exact"] + sm["agrees"], "partly": sm["partly"],
             "differs": sm["differs"], "differs_verb": "differs" if sm["differs"] == 1 else "differ"}
    notes = json.loads((HERE.parent / "results_notes.json").read_text())["page"]
    lede = notes["lede"].format(**facts)
    claims_line = notes["claims_line"]

    def label_row(anchor, name, ids):
        v = worst([by[i]["verdict"] for i in ids])
        cls, word = STAMP.get(v, ("running", "Not attempted"))
        return f'<li><a href="#{anchor}"><span>{esc(name)}</span><span class="v" data-v="{cls}">{esc(word)}</span></a></li>'

    label = "<ol>" + "".join(label_row(*r) for r in [
        ("fig-a", "Fig. 1A", ["fig1a"]), ("fig-b", "Fig. 1B", ["fig1b"]),
        ("tables", "Tables 1 to 5", ["table1.true", "table1.power", "table2", "table3", "table4", "table5"]),
        ("items", "Main claim", ["text.main_claim"])]) + "</ol>"

    stations, figjs = [], []
    for panel, iid in (("a", "fig1a"), ("b", "fig1b")):
        it = by[iid]
        psrc, (w, h) = b64(crop(Path(pub) / "figure-1.jpg", panel))
        osrc, _ = b64(crop(Path(figs) / f"fig1{panel}_ours.png", panel))
        stats = f"<div><dt>{esc(it['label'])}</dt><dd>{esc(measure(it))}, {esc(STAMP[it['verdict']][1])}</dd></div>"
        note = (it.get("cause") or {}).get("summary", "")
        stations.append(
            f'<section class="station surface" id="fig-{panel}" aria-labelledby="fig-{panel}-head">'
            f'<header class="station-head"><h2 id="fig-{panel}-head">Fig. 1{panel.upper()}</h2><p class="caption">{esc(CAPTIONS[panel])}</p>{stamp(it["verdict"])}</header>'
            f'<div class="stage"><div class="pair">'
            f'<figure class="plate"><figcaption>Published</figcaption><img src="{psrc}" alt="Figure 1{panel.upper()} as published" width="{w}" height="{h}"></figure>'
            f'<figure class="plate"><figcaption>Our run</figcaption><img src="{osrc}" alt="Figure 1{panel.upper()} from our run" width="{w}" height="{h}"></figure>'
            f'</div></div><div class="station-foot"><dl class="dose">{stats}</dl><p class="note">{esc(note)}</p></div></section>')
        figjs.append({"id": panel, "w": w, "h": h})

    grids = []
    for tid in ("table1.true", "table1.power", "table2", "table3", "table4", "table5", "fig1b"):
        it = by[tid]
        h, n = hits(it)
        anchor = tid.replace(".", "-")
        grids.append(f'<section class="station surface" id="{anchor}" aria-labelledby="{anchor}-head"><header class="station-head">'
                     f'<h2 id="{anchor}-head">{esc(it["label"])}</h2><p class="caption">The paper, ours, and the tolerance; shaded where ours is outside it. '
                     f'{h} of {n} within.</p>{stamp(it["verdict"])}</header>{cell_table(it)}'
                     f'<div class="station-foot"><p class="note">{esc((it.get("cause") or {}).get("summary", ""))}</p></div></section>')
    tables = (f'<section class="container after-bench" aria-labelledby="tables-head" id="tables"><h2 id="tables-head">The tables</h2>'
              f'<p class="caption">Each power is compared at half a printed unit plus three combined Monte Carlo standard errors (the paper ran 2,000 trials, we ran 20,000). Shares, rates and AUROCs at their printed precision.</p>'
              f'<div class="cellgrid">{"".join(grids)}</div></section>')

    rows = []
    for i in R["items"]:
        fields = ""
        if i["method"] == "values" and len(i["values"]["fields"]) <= 4:
            fields = "<ul class=fields>" + "".join(
                f"<li>{esc(f['name'])}: paper {esc(str(f['expected']))}, ours <strong>{esc(fmt(f['observed'], f['expected']))}</strong></li>"
                for f in i["values"]["fields"]) + "</ul>"
        cause = (i.get("cause") or {}).get("summary", "")
        rows.append(f"<tr><td>{esc(i['label'])}</td><td>{stamp(i['verdict'])}</td><td>{esc(measure(i))}{fields}</td><td>{esc(cause)}</td></tr>")
    extra = (tables + f'<section class="container after-bench" aria-labelledby="items-head"><div class="station surface" id="items">'
             f'<header class="station-head"><h2 id="items-head">Every result</h2><p class="caption">Every figure panel, table and claim of the paper, with the verdict computed from the numbers.</p></header>'
             f'<div class="table-wrap"><table class="record dense"><thead><tr><th scope="col">Result</th><th scope="col">Verdict</th>'
             f'<th scope="col">Measure</th><th scope="col">Why</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>'
             f'<p class="note">{esc(claims_line)}</p></div></section>')

    t1, t2, t3, t5 = by["table1.power"], by["table2"], by["table3"], by["table5"]
    came_back = [
        ("Fig. 1A", f"The curve came back on the published axes: {measure(by['fig1a'])}."),
        ("The base case", f"Table 1's three powers and the score's AUROC came back ({hits(t1)[0]} of {hits(t1)[1]})."),
        ("The main claim", "In every setting a score of several RFs has far more power than one RF analysed alone, as the paper says."),
        ("The method", "stratpower, a Python package with the interaction test, the power simulation and a tutorial."),
    ]
    buried = [
        "The code. The paper names no software and released nothing; no copy was found.",
        f"Some powers. Where the heterogeneity is large most of our powers are higher than the paper's: Table 2 {hits(t2)[0]} of {hits(t2)[1]}, Table 3 {hits(t3)[0]} of {hits(t3)[1]}, Table 5 {hits(t5)[0]} of {hits(t5)[1]} within tolerance. No tested reading of the paper closes the gap.",
        "Table 1's rates. Its CER, RRR and NNT columns follow from no population of the stated risk factors, nor from each other.",
    ]
    recovered = ('<section class="notes" aria-labelledby="back-head"><div class="container"><h2 id="back-head">What came back</h2><dl class="ledger">'
                 + "".join(f'<div class="row"><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>' for k, v in came_back)
                 + '</dl></div></section><section class="buried" aria-labelledby="buried-head"><div class="container"><div class="plastic buried-band">'
                 '<h2 id="buried-head">What stayed buried</h2><ul>' + "".join(f"<li>{esc(x)}</li>" for x in buried)
                 + f'</ul><p class="so">{esc(claims_line)}</p></div></div></section>')
    seen, matched = set(), []
    for i in R["items"]:
        for a in i.get("assumptions", []):
            if a["what"] not in seen:
                seen.add(a["what"])
                matched.append(f'<div class="row"><dt>{esc(a["source"].replace("_", " "))}</dt><dd>{esc(a["what"])} {esc(a["sensitivity"])}</dd></div>')

    page = (HERE / "page_template.html").read_text()
    page = page.replace('<link rel="stylesheet" href="../results.css">', '<link rel="stylesheet" href="../results.css">\n' + STYLE)
    for k, v in {"LEDE": esc(lede), "LABEL": label, "STATIONS": "".join(stations), "EXTRA": extra,
                 "RECOVERED": recovered, "MATCHED_INTRO": "What the paper does not say, and what we chose.",
                 "MATCHED": "".join(matched),
                 "CLOSING": "We rebuilt a lost power simulation from its paper and ran every setting again."}.items():
        page = page.replace(f"<!--__{k}__-->", v)
    page = page.replace("/*__FIGS__*/[]", json.dumps(figjs))
    outp = Path(out) / "index.html"
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(page)
    print(f"wrote {outp} ({len(page) // 1024} KB)", file=sys.stderr)


if __name__ == "__main__":
    main(*sys.argv[1:5])
