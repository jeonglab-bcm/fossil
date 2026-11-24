"""Build the results page from results.json, the renders and the published figures.

Usage: build_page.py RESULTS_JSON FIG_DIR PUBLISHED_DIR OUT_DIR   (writes OUT_DIR/index.html)

Every verdict and number on the page is read from results.json (verdicts computed there by
check_results.py); the prose that is not a number comes from results_notes.json ("page"). Images are
embedded, so the page works offline; it links ../results.css like the site's other results pages.
"""
import base64
import html
import io
import json
import re
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from check_results import field_matches  # noqa: E402


def with_install_block(page):
    """The repository's "Install" block (tools/site_install.py, from package/README.md), placed as that
    tool places it, so the page the pipeline writes equals the committed one (as PMC2430201 and PMC3196500 do)."""
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

esc = html.escape
STAMP = {"exact": ("agrees", "Exact"), "agrees": ("agrees", "Agrees"), "partly": ("partly", "Partly agrees"),
         "inconclusive": ("partly", "Inconclusive"), "differs": ("differs", "Differs")}
CAPTIONS = {
    "1": "Fig. 1. Expected length given coverage of the three 95% CIs and the empirical CI, Scenario 1 (P(E) .05, P(D|not E) .02), N1 = N2 = 5,000.",
    "2": "Fig. 2. The same for Scenario 2 (P(E) .05, P(D|not E) .09).",
    "3": "Fig. 3. The same for Scenario 3 (P(E) .20, P(D|not E) .02).",
    "4": "Fig. 4. The same for Scenario 4 (P(E) .20, P(D|not E) .09). No ESR_S bar at RR 5.0: its coverage is 0.",
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


def b64(path):
    buf = io.BytesIO()
    im = Image.open(path).convert("RGB")
    im.save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode(), im.size


def stamp(v, small=""):
    if v == "not_attempted":
        return '<span class="stamp" data-v="running">Not attempted</span>'
    cls, word = STAMP[v]
    return f'<span class="stamp" data-v="{cls}">{esc(word)}' + (f"<small>{esc(small)}</small>" if small else "") + "</span>"


def reviewed(its):
    """'on review' when a reviewer set the verdict of any of these items (their review block), as in PMC522806."""
    return "on review" if any((i.get("review") or {}).get("verdict") == i.get("verdict") for i in its) else ""


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
        return f"{h} of {n} values" + (f" ({e} paper slip{'s' if e > 1 else ''} left out)" if e else "")
    if it["method"] == "pixels":
        p = it["pixels"]
        s = min(p["published_near_ours"], p["ours_near_published"])
        best = max(c["score"] for c in p["controls"])
        return f"{100 * s:.1f}% of bar tops within {p['tolerance_px']} px (pass {100 * p['threshold']:.0f}%, best control {100 * best:.1f}%)"
    if it["method"] == "check":
        return it["check"]["detail"]
    return ""


def fmt(v, like=None):
    """A number at the printed precision of `like` (the paper's value), else 4 significant digits."""
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


def cell_grid(it):
    """Scenario x N1/N2 rows, RR columns: the paper's value over ours; misses shaded."""
    rows, rrs = {}, []
    for f in it["values"]["fields"]:
        m = re.match(r"Scenario (\d), ([\d/]+), RR ([\d.]+)$", f["name"])
        if not m:
            return ""
        s, size, rr = m.groups()
        rows.setdefault((s, size), {})[rr] = f
        if rr not in rrs:
            rrs.append(rr)
    head = "".join(f'<th scope="col">RR {esc(r)}</th>' for r in rrs)
    body = []
    for (s, size), cs in rows.items():
        tds = []
        for r in rrs:
            f = cs.get(r)
            if not f:
                tds.append("<td></td>")
                continue
            ok = field_matches(f, it["values"].get("tolerance"))
            tds.append(f'<td class="{"" if ok else "off"}">{esc(str(f["expected"]))}<br><small>{esc(fmt(f["observed"], f["expected"]))}</small></td>')
        body.append(f'<tr><th scope="row">Scenario {s}, {esc(size)}</th>{"".join(tds)}</tr>')
    return (f'<div class="table-wrap"><table class="cells" aria-label="{esc(it["label"])}"><thead><tr><th scope="col">Setting</th>{head}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>')


def main(results, figs, pub, out):
    R = json.loads(Path(results).read_text())
    from build_results import facts_of, fill
    sm = R["summary"]
    facts = {**facts_of(Path(figs)), **sm, "attempted": sm["items"] - sm["not_attempted"],
             "differs_verb": "differs" if sm["differs"] == 1 else "differ", "reviewed": sm.get("reviewed", 0)}
    N = fill(json.loads((HERE.parent / "results_notes.json").read_text())["page"], facts)
    items = R["items"]
    by = {i["id"]: i for i in items}
    lede = N["lede"]
    def label_row(anchor, name, ids):
        v = worst([by[i]["verdict"] for i in ids])
        cls, word = STAMP.get(v, ("running", "Not attempted"))
        return f'<li><a href="#{anchor}"><span>{esc(name)}</span><span class="v" data-v="{cls}">{esc(word)}</span></a></li>'
    label = "<ol>" + "".join(label_row(a, k, ids) for a, k, ids in N["label_rows"]) + "</ol>"

    stations, figjs = [], []
    for n in ("1", "2", "3", "4"):
        its = [by[f"fig{n}"], by[f"fig{n}.bars"]]
        v = worst([i["verdict"] for i in its])
        psrc, (w, h) = b64(Path(pub) / f"figure-{n}.jpg")
        osrc, _ = b64(Path(figs) / f"fig{n}_ours.png")
        asrc, _ = b64(Path(figs) / f"fig{n}_ours_eq10_no_first_term.png")
        stats = "".join(f"<div><dt>{esc(i['label'])}</dt><dd>{esc(measure(i))}, {esc(STAMP[i['verdict']][1])}</dd></div>" for i in its)
        note = (its[0].get("cause") or {}).get("summary", "")
        hyp = its[0]["pixels"].get("hypotheses", {}).get("eq10_no_first_term")
        alt_stats = (f"<div><dt>Hypothesis, not our result</dt><dd>eq. 10 without its first term: "
                     f"{100 * hyp:.1f}% of bar tops within {its[0]['pixels']['tolerance_px']} px</dd></div>") if hyp is not None else ""
        stations.append(
            f'<section class="station surface" id="fig-{n}" aria-labelledby="fig-{n}-head">'
            f'<header class="station-head"><h2 id="fig-{n}-head">Fig. {n}</h2><p class="caption">{esc(CAPTIONS[n])}</p>{stamp(v, reviewed(its))}</header>'
            f'<div class="stage"><div class="pair">'
            f'<figure class="plate"><figcaption>Published</figcaption><img src="{psrc}" alt="Figure {n} as published" width="{w}" height="{h}"></figure>'
            f'<figure class="plate"><figcaption>Our run</figcaption><img src="{osrc}" alt="Figure {n} drawn from our run" width="{w}" height="{h}"></figure>'
            f'</div></div><div class="station-foot"><dl class="dose">{stats}</dl><p class="note">{esc(note)}</p></div></section>')
        figjs.append({"id": n, "w": w, "h": h, "variants": [
            {"label": "Our run (eq. 10 as printed)", "ours": osrc, "note": note, "stats": stats},
            {"label": "Hypothesis: eq. 10 without its first term", "ours": asrc,
             "note": "A test of the cause, not our result: the same samples with the first term of eq. 10 left out.", "stats": alt_stats}]})

    grids = []
    for tid in ("tableS1", "tableS2", "tableS3", "tableS4", "tableS5", "tableS6", "tableS7", "table4"):
        it = by[tid]
        h, n_, _ = hits(it)
        grids.append(f'<section class="station surface" id="{tid}" aria-labelledby="{tid}-head"><header class="station-head">'
                     f'<h2 id="{tid}-head">{esc(it["label"])}</h2><p class="caption">Paper above, ours below; shaded where ours is outside the tolerance. '
                     f'{h} of {n_} cells within.</p>{stamp(it["verdict"], reviewed([it]))}</header>{cell_grid(it)}'
                     f'<div class="station-foot"><p class="note">{esc((it.get("cause") or {}).get("summary", ""))}</p></div></section>')
    tables = (f'<section class="container after-bench" aria-labelledby="tables-head" id="tables"><h2 id="tables-head">The tables</h2>'
              f'<p class="caption">{esc(N["tables_caption"])}</p><div class="cellgrid">{"".join(grids)}</div></section>')

    rows = []
    for i in items:
        fields = ""
        if i["method"] == "values" and len(i["values"]["fields"]) <= 16:
            fields = "<ul class=fields>" + "".join(
                f"<li>{esc(f['name'])}: paper {esc(fmt(f['expected']))}, ours <strong>{esc(fmt(f['observed'], f['expected']))}</strong></li>"
                for f in i["values"]["fields"]) + "</ul>"
        cause = (i.get("cause") or {}).get("summary", "")
        rows.append(f"<tr><td>{esc(i['label'])}</td><td>{stamp(i['verdict'], reviewed([i]))}</td><td>{esc(measure(i))}{fields}</td><td>{esc(cause)}</td></tr>")
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
    for k, v in {"LEDE": esc(lede), "LABEL": label, "STATIONS": "".join(stations), "EXTRA": extra,
                 "RECOVERED": recovered, "MATCHED_INTRO": esc(N["matched_intro"]), "MATCHED": matched,
                 "CLOSING": esc(N["closing"])}.items():
        page = page.replace(f"<!--__{k}__-->", v)
    page = page.replace("/*__FIGS__*/[]", json.dumps(figjs))
    page = with_install_block(page)
    outp = Path(out) / "index.html"
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(page)
    print(f"wrote {outp} ({len(page) // 1024} KB)", file=sys.stderr)


if __name__ == "__main__":
    main(*sys.argv[1:5])
