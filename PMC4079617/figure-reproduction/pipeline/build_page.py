"""Build the results page from results.json, the renders and the published figure.

Usage: build_page.py RESULTS_JSON RUN_OUTPUT_DIR PUBLISHED_FIG1_PNG OUT_DIR   (writes OUT_DIR/index.html)

Every verdict and number on the page is read from results.json (verdicts computed there by check_results.py)
or, for the facts in the prose, from the run (build_results.facts_of); the prose that is not a number comes from
results_notes.json ("page"). Fig. 1 is one station, as the paper prints it: the published figure (panels A to
D) next to ours drawn on it, with swipe, blink, overlay and difference views, and the score of each panel. Tables 1-3 and A1-A3 are grids of every printed cell, the paper's value above ours, shaded where
ours is outside the Monte Carlo tolerance. Images are embedded, so the page works offline; it links
../results.css like the site's other results pages.
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
PANEL = {"a": "linear Z, moderate association", "b": "linear Z, strong association",
         "c": "non-linear Z, moderate association", "d": "non-linear Z, strong association"}
COLS = [("linear", "moderate"), ("linear", "strong"), ("nonlinear", "moderate"), ("nonlinear", "strong")]
STYLE = """<style>
table.cells { border-collapse: collapse; font-family: var(--font-outlier); font-size: var(--text-xs); }
table.cells th, table.cells td { padding: 2px 6px; text-align: right; border-top: var(--rule-hair) solid var(--color-rule); white-space: nowrap; }
table.cells th { font-weight: 500; color: var(--color-muted); }
table.cells th[scope=row] { text-align: left; }
table.cells th.grp { text-align: center; border-left: var(--rule-hair) solid var(--color-rule); }
table.cells td.first { border-left: var(--rule-hair) solid var(--color-rule); }
table.cells td.off { background: var(--color-paper-3); font-weight: 500; }
table.cells td.slip { background: var(--color-paper-2); font-style: italic; }
table.cells td small { color: var(--color-muted); }
.cellgrid { display: grid; gap: var(--space-lg); }
ul.fields { margin: var(--space-xs) 0 0; padding-left: 1.1em; font-size: var(--text-xs); }
</style>"""


def with_install_block(page):
    """The repository's "Install" block (tools/site_install.py, from package/README.md), placed as that
    tool places it, so the page the pipeline writes equals the committed one."""
    tools = HERE.parents[2] / "tools"
    if not (tools / "site_install.py").is_file():
        return page
    sys.path.insert(0, str(tools))
    import site_install

    want = site_install.block(HERE.parents[1].name)
    page = site_install.BLOCK.sub("", page)
    if want and site_install.ANCHOR in page:
        page = page.replace(site_install.ANCHOR, site_install.ANCHOR + "    " + want, 1)
    return page


def b64(im):
    buf = io.BytesIO()
    im.convert("RGB").save(buf, "PNG", optimize=True)
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
        return f"{h} of {n} values within tolerance" + (f" ({e} slip{'s' if e > 1 else ''} of the paper left out)" if e else "")
    if it["method"] == "pixels":
        p = it["pixels"]
        s = min(p["published_near_ours"], p["ours_near_published"])
        best = max(c["score"] for c in p["controls"])
        m = f"{100 * s:.1f}% of the lines within {p['tolerance_px']:g} px (pass {100 * p['threshold']:.0f}%, best control {100 * best:.1f}%)"
        r = it.get("review")
        return m + (f"; computed {r['computed']}, set to {r['verdict']} in review by {r['by']}" if r else "")
    if it["method"] == "check":
        return it["check"]["detail"]
    return ""


def fmt(v, like=None):
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        if isinstance(like, str):
            try:
                float(like)
                dec = len(like.split(".")[1]) if "." in like else 0
                s = f"{v:.{dec}f}"
                return "0." + "0" * dec if s.startswith("-") and float(s) == 0 and dec else s
            except ValueError:
                pass
        return f"{v:.4g}"
    return str(v)


def cell_grid(it, rows):
    """The 18 rows (RR, outcome, contamination) x 8 cells, the paper's value over ours."""
    fields = {f["name"]: f for f in it["values"]["fields"]}
    slips = {e["field"] for e in it["values"].get("exceptions", [])}
    head1 = '<th scope="col" rowspan="2">RR, P(Y = 1), contamination</th>' + "".join(
        f'<th scope="colgroup" colspan="2" class="grp">{"Non-linear" if f == "nonlinear" else "Linear"}, {l}</th>' for f, l in COLS)
    head2 = "".join('<th scope="col">LB</th><th scope="col">RP</th>' for _ in COLS)
    body = []
    for r in rows:
        tds = []
        for f, l in COLS:
            for j, m in enumerate(("LB", "RP")):
                name = f"RR {r['rr']}, {r['py']}, {r['contamination']}: {'non-linear' if f == 'nonlinear' else 'linear'} {l}, {m}"
                fl = fields[name]
                ok = field_matches(fl, it["values"].get("tolerance"))
                cls = " ".join(x for x in ("first" if j == 0 else "", "slip" if name in slips else ("" if ok else "off")) if x)
                tds.append(f'<td class="{cls}">{esc(fl["expected"])}<br><small>{esc(fmt(fl["observed"], fl["expected"]))}</small></td>')
        body.append(f'<tr><th scope="row">{esc(r["rr"])}, {esc(r["py"])}, {esc(r["contamination"])}</th>{"".join(tds)}</tr>')
    return (f'<div class="table-wrap"><table class="cells" aria-label="{esc(it["label"])}"><thead><tr>{head1}</tr><tr>{head2}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>')


def main_verdict(R):
    v = next(i["verdict"] for i in R["items"] if i["id"] == "text.main_claim")
    return {"exact": "holds", "agrees": "holds", "partly": "holds in part"}.get(v, "does not hold")


def main(results, run, pub_png, out):
    R = json.loads(Path(results).read_text())
    from build_results import facts_of, fill
    run = Path(run)
    sm = R["summary"]
    facts = {**facts_of(run), **{k: v for k, v in sm.items()}, "attempted": sm["items"] - sm["not_attempted"],
             "agree_total": sm.get("exact", 0) + sm.get("agrees", 0), "main_verdict": main_verdict(R)}
    N = fill(json.loads((HERE.parent / "results_notes.json").read_text())["page"], facts)
    items = R["items"]
    by = {i["id"]: i for i in items}
    pub = json.load(open(run / "published_values.json"))
    fig = json.load(open(run / "figure.json"))
    published = Image.open(pub_png)

    def label_row(anchor, name, ids):
        v = worst([by[i]["verdict"] for i in ids])
        cls, word = STAMP.get(v, ("running", "Not attempted"))
        return f'<li><a href="#{anchor}"><span>{esc(name)}</span><span class="v" data-v="{cls}">{esc(word)}</span></a></li>'
    label = "<ol>" + "".join(label_row(a, k, ids) for a, k, ids in N["label_rows"]) + "</ol>"

    # Fig. 1 as the paper prints it: one picture with panels A to D, published next to ours
    its = [by[f"fig1.{p}"] for p in ("a", "b", "c", "d")]
    psrc, (w, h) = b64(published)
    osrc, _ = b64(Image.open(run / "fig1_ours.png"))
    stats = "".join(f"<div><dt>{esc(it['label'])}</dt><dd>{esc(measure(it))}, {esc(STAMP[it['verdict']][1])}</dd></div>" for it in its)
    stations = [
        f'<section class="station surface" id="fig-1" aria-labelledby="fig-1-head">'
        f'<header class="station-head"><h2 id="fig-1-head">Fig. 1</h2><p class="caption">{esc(N["fig_caption"])}</p>'
        f'{stamp(worst([it["verdict"] for it in its]))}</header>'
        f'<div class="stage"><div class="pair">'
        f'<figure class="plate"><figcaption>Published</figcaption><img src="{psrc}" alt="Fig. 1 as published" width="{w}" height="{h}"></figure>'
        f'<figure class="plate"><figcaption>Our run, drawn on the published frame</figcaption><img src="{osrc}" alt="Fig. 1 drawn from our run" width="{w}" height="{h}"></figure>'
        f'</div></div><div class="station-foot"><dl class="dose">{stats}</dl><p class="note">{esc(N["fig_note"])}</p></div></section>']
    figjs = [{"id": "1", "w": w, "h": h}]

    grids = []
    for tid in ("table1", "table2", "table3", "tableA1", "tableA2", "tableA3"):
        it = by[tid]
        h_, n_, e_ = hits(it)
        slip = (" " + N["slip_note"]) if e_ else ""
        grids.append(f'<section class="station surface" id="{tid}" aria-labelledby="{tid}-head"><header class="station-head">'
                     f'<h2 id="{tid}-head">{esc(it["label"])}</h2><p class="caption">{esc(N["grid_caption"])} {h_} of {n_} cells within.{esc(slip)}</p>'
                     f'{stamp(it["verdict"])}</header>{cell_grid(it, pub["tables"][tid]["rows"])}</section>')
    tables = (f'<section class="container after-bench" aria-labelledby="tables-head" id="tables"><h2 id="tables-head">The tables</h2>'
              f'<p class="caption">{esc(N["tables_caption"])}</p><div class="cellgrid">{"".join(grids)}</div></section>')

    rows = []
    for i in items:
        fields = ""
        if i["method"] == "values" and len(i["values"]["fields"]) <= 8:
            exc = {e["field"] for e in i["values"].get("exceptions", [])}
            fields = "<ul class=fields>" + "".join(
                f"<li>{esc(f['name'])}: paper {esc(str(f['expected']))}, ours <strong>{esc(fmt(f['observed'], f['expected']))}</strong>"
                + (" (the paper's own table breaks it; left out)" if f["name"] in exc else "") + "</li>"
                for f in i["values"]["fields"]) + "</ul>"
        cause = (i.get("cause") or {}).get("summary", "")
        rows.append(f"<tr><td>{esc(i['label'])}</td><td>{stamp(i['verdict'])}</td><td>{esc(measure(i))}{fields}</td><td>{esc(cause)}</td></tr>")
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
    outp.write_text(with_install_block(page))
    print(f"wrote {outp} ({len(page) // 1024} KB)", file=sys.stderr)


if __name__ == "__main__":
    main(*sys.argv[1:5])
