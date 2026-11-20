"""Build the results page from results.json, the renders and the published figures.

Usage: build_page.py RESULTS_JSON FIG_DIR PUBLISHED_DIR OUT_DIR   (writes OUT_DIR/index.html)

Every verdict and number on the page is read from results.json (verdicts computed there by
check_results.py) or from the run's outputs; the prose that is not a number comes from
results_notes.json ("page"), with the run's numbers filled in. Images are embedded, so the page works
offline; it links ../results.css like the site's other results pages.
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
FIGS = {
    "1": (["fig1a", "fig1b", "fig1c", "fig1d"],
          "Fig. 1. Clustering of the calls of the 15 predictors (A, C) and kappa of each pair (B, D), for all 3,591 SNVs and the 1,699 not in COSMIC. Ours: our calls, kappa colours and dendrograms; the SNVs of our heat map are sorted by their calls, not clustered."),
    "2": (["fig2a", "fig2a.ci", "fig2b", "fig2b.ci"],
          "Fig. 2. Accuracy, sensitivity, specificity, PPV, NPV and composite score of each predictor, on the 989 labelled SNVs (A) and the 297 not in COSMIC (B), with bootstrap 95% intervals."),
    "3": (["fig3a", "fig3b", "fig3c", "fig3d"],
          "Fig. 3. The top five combinations by composite score in subset 1 and subset 2, against the best single and meta-predictor; stars and triangles mark significant gains in composite score and NPV. Ours: our top five, named in the legend."),
    "4": (["fig4a", "fig4b"],
          "Fig. 4. How often each predictor is in the top 10, 20, 50 and 100 combinations by composite score, in each subset."),
}
STYLE = """<style>
table.cells { border-collapse: collapse; font-family: var(--font-outlier); font-size: var(--text-xs); }
table.cells th, table.cells td { padding: 2px 6px; text-align: right; border-top: var(--rule-hair) solid var(--color-rule); white-space: nowrap; }
table.cells th { font-weight: 500; color: var(--color-muted); }
table.cells th[scope=row] { text-align: left; }
table.cells td.off { background: var(--color-paper-3); font-weight: 500; }
table.cells td small { color: var(--color-muted); }
.cellgrid { display: grid; gap: var(--space-lg); }
</style>"""
STATS = [("acc", "Accuracy"), ("sens", "Sensitivity"), ("spec", "Specificity"), ("PPV", "PPV"), ("NPV", "NPV"), ("comp", "Composite")]


def b64(path):
    """The picture at half its 300 dpi size (150 dpi), embedded as PNG."""
    buf = io.BytesIO()
    im = Image.open(path).convert("RGB")
    im = im.resize((im.width // 2, im.height // 2), Image.Resampling.BOX)
    im.save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode(), im.size


def stamp(v):
    if v == "not_attempted":
        return '<span class="stamp" data-v="running">Not attempted</span>'
    cls, word = STAMP[v]
    return f'<span class="stamp" data-v="{cls}">{esc(word)}</span>'


def worst(vs):
    order = ["differs", "inconclusive", "partly", "agrees", "exact"]
    vs = [v for v in vs if v in order]
    return min(vs, key=order.index) if vs else "not_attempted"


def hits(it):
    f = it["values"]["fields"]
    exc = {e["field"] for e in it["values"].get("exceptions", []) if e.get("category") == "paper_error"}
    counted = [x for x in f if x["name"] not in exc]
    return sum(field_matches(x, it["values"].get("tolerance")) for x in counted), len(counted), len(exc)


def measure(it):
    if it["method"] == "values":
        h, n, e = hits(it)
        return f"{h:,} of {n:,} values" + (f" ({e} paper slip{'s' if e > 1 else ''} left out)" if e else "")
    if it["method"] == "check":
        return it["check"]["detail"]
    return ""


def fmt(v, like=None):
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        if isinstance(like, str):
            try:
                float(like)
                dec = len(like.split(".")[1]) if "." in like else 0
                return f"{v:.{dec}f}"
            except ValueError:
                pass
        return f"{v:.4g}"
    return str(v)


def perf_grid(points, cis):
    """Predictor rows, statistic columns: the paper's value and interval over ours; shaded where ours is
    outside the tolerance."""
    by = {f["name"]: f for f in points["values"]["fields"]}
    byc = {f["name"]: f for f in cis["values"]["fields"]}
    preds = []
    for f in points["values"]["fields"]:
        p = f["name"].rsplit(" ", 1)[0]
        if p not in preds:
            preds.append(p)
    head = "".join(f'<th scope="col">{esc(lab)}</th>' for _, lab in STATS)
    body = []
    for p in preds:
        tds = []
        for k, _ in STATS:
            f, lo, hi = by[f"{p} {k}"], byc[f"{p} {k} low"], byc[f"{p} {k} high"]
            ok = all(field_matches(x, {"printed": True}) for x in (f, lo, hi))
            tds.append(f'<td class="{"" if ok else "off"}">{esc(f["expected"])} ({esc(lo["expected"])}-{esc(hi["expected"])})<br>'
                       f'<small>{esc(fmt(f["observed"], f["expected"]))} ({esc(fmt(lo["observed"], lo["expected"]))}-{esc(fmt(hi["observed"], hi["expected"]))})</small></td>')
        body.append(f'<tr><th scope="row">{esc(p)}</th>{"".join(tds)}</tr>')
    return (f'<div class="table-wrap"><table class="cells" aria-label="{esc(points["label"])}"><thead><tr><th scope="col">Predictor</th>{head}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>')


def main(results, figs, pub, out):
    R = json.loads(Path(results).read_text())
    from build_results import facts_of, fill
    sm = R["summary"]
    facts = {**facts_of(Path(figs)), **sm, "attempted": sm["items"] - sm["not_attempted"]}
    N = fill(json.loads((HERE.parent / "results_notes.json").read_text())["page"], facts)
    items = R["items"]
    by = {i["id"]: i for i in items}

    def label_row(anchor, name, ids):
        v = worst([by[i]["verdict"] for i in ids])
        cls, word = STAMP.get(v, ("running", "Not attempted"))
        return f'<li><a href="#{anchor}"><span>{esc(name)}</span><span class="v" data-v="{cls}">{esc(word)}</span></a></li>'
    label = "<ol>" + "".join(label_row(a, k, ids) for a, k, ids in N["label_rows"]) + "</ol>"

    stations, figjs = [], []
    for n, (ids, caption) in FIGS.items():
        its = [by[i] for i in ids]
        v = worst([i["verdict"] for i in its])
        psrc, (w, h) = b64(Path(pub) / f"figure-{n}.png")
        osrc, _ = b64(Path(figs) / f"fig{n}_ours.png")
        stats = "".join(f"<div><dt>{esc(i['label'])}</dt><dd>{esc(measure(i))}, {esc(STAMP[i['verdict']][1])}</dd></div>" for i in its)
        notes = []
        for i in its:
            s = (i.get("cause") or {}).get("summary", "")
            if s and s not in notes:
                notes.append(s)
        note = " ".join(notes)
        stations.append(
            f'<section class="station surface" id="fig-{n}" aria-labelledby="fig-{n}-head">'
            f'<header class="station-head"><h2 id="fig-{n}-head">Fig. {n}</h2><p class="caption">{esc(caption)}</p>{stamp(v)}</header>'
            f'<div class="stage"><div class="pair">'
            f'<figure class="plate"><figcaption>Published</figcaption><img src="{psrc}" alt="Figure {n} as published" width="{w}" height="{h}"></figure>'
            f'<figure class="plate"><figcaption>Our run</figcaption><img src="{osrc}" alt="Figure {n} drawn from our run" width="{w}" height="{h}"></figure>'
            f'</div></div><div class="station-foot"><dl class="dose">{stats}</dl><p class="note">{esc(note)}</p></div></section>')
        figjs.append({"id": n, "w": w, "h": h})

    grids = []
    for tid, cid in (("table3", "table3.ci"), ("table4", "table4.ci")):
        it, ci = by[tid], by[cid]
        h1, n1, _ = hits(it)
        h2, n2, _ = hits(ci)
        grids.append(f'<section class="station surface" id="{tid}" aria-labelledby="{tid}-head"><header class="station-head">'
                     f'<h2 id="{tid}-head">{esc(it["label"].split(" (")[0])}</h2><p class="caption">Paper above, ours below, in percent (composite 0 to 4); '
                     f'shaded where a value of ours is outside its tolerance. Point values {h1} of {n1}, interval ends {h2} of {n2}.</p>'
                     f'{stamp(worst([it["verdict"], ci["verdict"]]))}</header>{perf_grid(it, ci)}'
                     f'<div class="station-foot"><p class="note">{esc((ci.get("cause") or {}).get("summary", ""))}</p></div></section>')
    tables = (f'<section class="container after-bench" aria-labelledby="tables-head" id="tables"><h2 id="tables-head">Tables 3 and 4</h2>'
              f'<p class="caption">{esc(N["tables_caption"])}</p><div class="cellgrid">{"".join(grids)}</div></section>')

    rows = []
    for i in items:
        fields = ""
        if i["method"] == "values" and len(i["values"]["fields"]) <= 20:
            fields = "<ul class=fields>" + "".join(
                f"<li>{esc(f['name'])}: paper {esc(fmt(f['expected']))}, ours <strong>{esc(fmt(f['observed'], f['expected']))}</strong></li>"
                for f in i["values"]["fields"]) + "</ul>"
        cause = (i.get("cause") or {}).get("summary", "")
        exc = "; ".join(e["evidence"] for e in (i.get("values") or {}).get("exceptions", []))
        why = " ".join(x for x in (cause, exc) if x)
        rows.append(f"<tr><td>{esc(i['label'])}</td><td>{stamp(i['verdict'])}</td><td>{esc(measure(i))}{fields}</td><td>{esc(why)}</td></tr>")
    extra = (tables + f'<section class="container after-bench" aria-labelledby="items-head"><div class="station surface" id="items">'
             f'<header class="station-head"><h2 id="items-head">Every result</h2><p class="caption">{esc(N["items_caption"])}</p></header>'
             f'<div class="table-wrap"><table class="record dense"><thead><tr><th scope="col">Result</th><th scope="col">Verdict</th>'
             f'<th scope="col">Measure</th><th scope="col">Why</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>'
             f'<p class="note">{esc(N["claims_line"])}</p></div></section>')

    recovered = ('<section class="notes" aria-labelledby="back-head"><div class="container"><h2 id="back-head">What came back</h2><dl class="ledger">'
                 + "".join(f'<div class="row"><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>' for k, v in N["came_back"])
                 + '</dl></div></section><section class="buried" aria-labelledby="buried-head"><div class="container"><div class="plastic buried-band">'
                 '<h2 id="buried-head">What stayed buried</h2><ul>' + "".join(f"<li>{esc(x)}</li>" for x in N["buried"])
                 + f'</ul><p class="so">{esc(N["claims_line"])}</p></div></div></section>')
    matched = "".join(f'<div class="row"><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>' for k, v in N["matched"])

    page = (HERE / "page_template.html").read_text()
    page = page.replace('<link rel="stylesheet" href="../results.css">', '<link rel="stylesheet" href="../results.css">\n' + STYLE)
    for k, v in {"LEDE": esc(N["lede"]), "LABEL": label, "STATIONS": "".join(stations), "EXTRA": extra,
                 "RECOVERED": recovered, "MATCHED_INTRO": esc(N["matched_intro"]), "MATCHED": matched,
                 "CLOSING": esc(N["closing"])}.items():
        page = page.replace(f"<!--__{k}__-->", v)
    page = page.replace("/*__FIGS__*/[]", json.dumps(figjs))
    outp = Path(out) / "index.html"
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(page)
    print(f"wrote {outp} ({len(page) // 1024} KB)", file=sys.stderr)


if __name__ == "__main__":
    main(*sys.argv[1:5])
