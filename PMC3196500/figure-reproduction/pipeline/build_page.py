"""Build the results page from results.json, the renders and the published figures.

Usage: build_page.py RESULTS_JSON RUN_OUTPUT_DIR PUBLISHED_DIR OUT_DIR   (writes OUT_DIR/index.html)

Every verdict and number on the page is read from results.json (verdicts computed there by
check_results.py); the prose that is not a number comes from results_notes.json ("page"), with run facts
filled in. Images are embedded, so the page works offline; it links ../results.css like the site's other
results pages.
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

esc = html.escape
STAMP = {"exact": ("agrees", "Exact"), "agrees": ("agrees", "Agrees"), "partly": ("partly", "Partly agrees"),
         "inconclusive": ("partly", "Inconclusive"), "differs": ("differs", "Differs"),
         "not_attempted": ("running", "Not attempted")}
FIGS = ["fig2"] + [f"figS{k}" for k in range(1, 13)]
STYLE = """<style>
table.cells { border-collapse: collapse; font-family: var(--font-outlier); font-size: var(--text-xs); }
table.cells th, table.cells td { padding: 2px 6px; text-align: right; border-top: var(--rule-hair) solid var(--color-rule); white-space: nowrap; }
table.cells th { font-weight: 500; color: var(--color-muted); }
table.cells th[scope=row] { text-align: left; }
table.cells td.off { background: var(--color-paper-3); font-weight: 500; }
table.cells td small { color: var(--color-muted); }
.cellgrid { display: grid; gap: var(--space-lg); }
ul.panels { margin: 0; padding-left: 1.2em; font-size: var(--text-xs); }
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


def b64(path):
    buf = io.BytesIO()
    im = Image.open(path).convert("RGB")
    im.save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode(), im.size


def stamp(v):
    cls, word = STAMP[v]
    return f'<span class="stamp" data-v="{cls}">{esc(word)}</span>'


def worst(vs):
    order = ["differs", "inconclusive", "partly", "agrees", "exact"]
    vs = [v for v in vs if v in order]
    return min(vs, key=order.index) if vs else "not_attempted"


def hits(it):
    f = it["values"]["fields"]
    return sum(field_matches(x, it["values"].get("tolerance")) for x in f), len(f)


def measure(it):
    if it["method"] == "values":
        h, n = hits(it)
        return f"{h} of {n} values as printed"
    if it["method"] == "pixels":
        p = it["pixels"]
        s = min(p["published_near_ours"], p["ours_near_published"])
        best = max(c["score"] for c in p["controls"])
        return (f"{100 * s:.1f}% within {p['tolerance_px']} px (pass {100 * p['threshold']:.1f}%, best control "
                f"{100 * best:.1f}%, our two runs {100 * p['chance_ceiling']:.1f}%)")
    if it["method"] == "check":
        return it["check"]["detail"]
    return "not attempted"


def grid(it):
    """The paper's value over ours, one row per scenario; misses shaded."""
    rows, cols = {}, []
    for f in it["values"]["fields"]:
        name = f["name"]
        m = re.match(r"(.*), (patients|events)( for (\d+)%)?$", name) or re.match(r"(.*), (beta \d+%), (patients|events)$", name)
        if not m:
            return ""
        if name.startswith("RRR") and " for " in name:
            row, col = m.group(1), f"{m.group(2)} {m.group(4)}%"
        else:
            row, col = name.rsplit(", ", 2)[0], ", ".join(name.rsplit(", ", 2)[1:])
        rows.setdefault(row, {})[col] = f
        if col not in cols:
            cols.append(col)
    head = "".join(f'<th scope="col">{esc(c)}</th>' for c in cols)
    body = []
    for r, cs in rows.items():
        tds = []
        for c in cols:
            f = cs.get(c)
            ok = f is not None and field_matches(f, it["values"].get("tolerance"))
            tds.append(f'<td class="{"" if ok else "off"}">{esc(str(f["expected"]))}<br><small>{esc(str(f["observed"]))}</small></td>'
                       if f else "<td></td>")
        body.append(f'<tr><th scope="row">{esc(r)}</th>{"".join(tds)}</tr>')
    return (f'<div class="table-wrap"><table class="cells" aria-label="{esc(it["label"])}"><thead><tr><th scope="col">Scenario</th>{head}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>')


def fill(obj, facts):
    if isinstance(obj, str):
        return re.sub(r"\{([A-Za-z0-9_]+)\}", lambda m: str(facts[m.group(1)]), obj)
    if isinstance(obj, list):
        return [fill(x, facts) for x in obj]
    if isinstance(obj, dict):
        return {k: fill(v, facts) for k, v in obj.items()}
    return obj


def main(results, run_out, pub, out):
    R = json.loads(Path(results).read_text())
    from build_results import facts_of
    sm = R["summary"]
    facts = {**facts_of(Path(run_out)), **sm, "attempted": sm["items"] - sm["not_attempted"]}
    by = {i["id"]: i for i in R["items"]}
    pix = [i for i in R["items"] if i["method"] == "pixels"]
    facts.update({f"panels_{v}": sum(i["verdict"] == v for i in pix) for v in STAMP},
                 panels=len(pix))
    N = fill(json.loads((HERE.parent / "results_notes.json").read_text())["page"], facts)

    def label_row(anchor, name, ids):
        v = worst([by[i]["verdict"] for i in ids])
        cls, word = STAMP[v]
        return f'<li><a href="#{anchor}"><span>{esc(name)}</span><span class="v" data-v="{cls}">{esc(word)}</span></a></li>'
    label = "<ol>" + "".join(label_row(a, k, ids) for a, k, ids in N["label_rows"]) + "</ol>"

    stations, figjs = [], []
    for fig in FIGS:
        its = [i for i in pix if i["id"].split(".")[0] == fig]
        v = worst([i["verdict"] for i in its])
        psrc, (w, h) = b64(Path(pub) / f"{fig}.png")
        osrc, _ = b64(Path(run_out) / f"{fig}_ours.png")
        name = "Fig. 2" if fig == "fig2" else f"Fig. S{fig[4:]}"
        stats = "".join(f"<div><dt>{esc(i['label'].split('(')[0].strip().split(', ', 1)[-1])}</dt>"
                        f"<dd>{esc(measure(i))}, {esc(STAMP[i['verdict']][1])}</dd></div>" for i in its)
        note = N["figure_notes"].get(fig, N["figure_note"])
        stations.append(
            f'<section class="station surface" id="fig-{fig}" aria-labelledby="fig-{fig}-head">'
            f'<header class="station-head"><h2 id="fig-{fig}-head">{esc(name)}</h2><p class="caption">{esc(N["captions"][fig])}</p>{stamp(v)}</header>'
            f'<div class="stage"><div class="pair">'
            f'<figure class="plate"><figcaption>Published</figcaption><img src="{psrc}" alt="{esc(name)} as published" width="{w}" height="{h}"></figure>'
            f'<figure class="plate"><figcaption>Our run</figcaption><img src="{osrc}" alt="{esc(name)} drawn from our run" width="{w}" height="{h}"></figure>'
            f'</div></div><div class="station-foot"><dl class="dose">{stats}</dl><p class="note">{esc(note)}</p></div></section>')
        figjs.append({"id": fig, "w": w, "h": h})

    grids = []
    for tid in ("table1", "tableS4", "tableS3", "table2", "table3.ois", "table4.ois"):
        it = by[tid]
        h, n_ = hits(it)
        grids.append(f'<section class="station surface" id="{tid.replace(".", "-")}" aria-labelledby="{tid.replace(".", "-")}-head"><header class="station-head">'
                     f'<h2 id="{tid.replace(".", "-")}-head">{esc(it["label"])}</h2><p class="caption">Paper above, ours below; shaded where ours is not the printed value. '
                     f'{h} of {n_} cells as printed.</p>{stamp(it["verdict"])}</header>{grid(it)}'
                     f'<div class="station-foot"><p class="note">{esc((it.get("cause") or {}).get("summary", ""))}</p></div></section>')
    tables = (f'<section class="container after-bench" aria-labelledby="tables-head" id="tables"><h2 id="tables-head">The tables</h2>'
              f'<p class="caption">{esc(N["tables_caption"])}</p><div class="cellgrid">{"".join(grids)}</div></section>')

    rows = []
    for i in R["items"]:
        fields = ""
        if i["method"] == "values" and len(i["values"]["fields"]) <= 4:
            fields = "<ul class=fields>" + "".join(
                f"<li>{esc(f['name'])}: paper {esc(str(f['expected']))}, ours <strong>{esc(str(f['observed']))}</strong></li>"
                for f in i["values"]["fields"]) + "</ul>"
        cause = (i.get("cause") or {}).get("summary", "")
        if i["method"] == "pixels":
            cause = cause.split(". Settings tested")[0] + "."
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
