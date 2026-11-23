"""Build the results page from results.json.

Usage: build_page.py RESULTS_JSON RUN_OUTPUT_DIR OUT_DIR   (writes OUT_DIR/index.html)

Every verdict and number on the page is read from results.json (verdicts computed there by check_results.py)
or, for the facts in the prose, from the run (build_results.facts_of); the prose that is not a number comes
from results_notes.json ("page"). The paper has no figures: each of Tables 3-8 is a station with every printed
cell, the paper's value above ours, shaded where ours is outside the Monte Carlo tolerance. The page links
../results.css like the site's other results pages.
"""
import html
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from check_results import field_matches  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
from session_page import with_session  # noqa: E402  the session card and session.html

esc = html.escape
STAMP = {"exact": ("agrees", "Exact"), "agrees": ("agrees", "Agrees"), "partly": ("partly", "Partly agrees"),
         "inconclusive": ("partly", "Inconclusive"), "differs": ("differs", "Differs")}
GROUPS = [("% bias", "bias", "0"), ("% bias", "bias", "0.5"), ("% coverage", "coverage", "0"), ("% coverage", "coverage", "0.5"),
          ("% power", "power", "0"), ("% power", "power", "0.5"), ("I2 (%)", "i2", "0.5")]
QL = {"bias": "% bias", "coverage": "% coverage", "power": "% power", "i2": "I2 (%)"}
STYLE = """<style>
table.cells { border-collapse: collapse; font-family: var(--font-outlier); font-size: var(--text-xs); }
table.cells th, table.cells td { padding: 2px 5px; text-align: right; border-top: var(--rule-hair) solid var(--color-rule); white-space: nowrap; }
table.cells th { font-weight: 500; color: var(--color-muted); }
table.cells th[scope=row] { text-align: left; }
table.cells th.grp { text-align: center; border-left: var(--rule-hair) solid var(--color-rule); }
table.cells td.first { border-left: var(--rule-hair) solid var(--color-rule); }
table.cells td.off { background: var(--color-paper-3); font-weight: 500; }
table.cells td small { color: var(--color-muted); }
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
    v = it["values"]
    exc = {e["field"] for e in v.get("exceptions", []) if e.get("category") == "paper_error"}
    counted = [x for x in v["fields"] if x["name"] not in exc]
    return sum(field_matches(x, v.get("tolerance")) for x in counted), len(counted), len(exc)


def measure(it):
    if it["method"] == "values":
        h, n, e = hits(it)
        return f"{h} of {n} values within tolerance" + (f" ({e} paper slip{'s' if e > 1 else ''} left out)" if e else "")
    if it["method"] == "check":
        return it["check"]["detail"]
    return ""


def fmt(v):
    if isinstance(v, str):
        return v
    s = f"{v:.1f}" if abs(v) < 1000 else f"{v:.0f}"
    return "0.0" if s == "-0.0" else s


def cell_grid(it, rows):
    """Rows: the 18 settings (effect, n, k); columns: the 21 printed cells in the paper's order."""
    fields = {f["name"]: f for f in it["values"]["fields"]}
    head1 = '<th scope="col" rowspan="2">Setting</th>' + "".join(
        f'<th scope="colgroup" colspan="3" class="grp">{esc(q)}, tau {esc(t)}</th>' for q, _, t in GROUPS)
    head2 = "".join(f'<th scope="col">{m}</th>' for _ in GROUPS for m in ("MD", "SMD", "RoM"))
    body = []
    for r in rows:
        tds = []
        for _, q, t in GROUPS:
            for j, m in enumerate(("MD", "SMD", "RoM")):
                name = f"SMD {r['effect']:g}, {r['n']}, k {r['k']}: {QL[q]}, tau {t}, {m}"
                f = fields[name]
                ok = field_matches(f, it["values"].get("tolerance"))
                cls = " ".join(c for c in ("first" if j == 0 else "", "" if ok else "off") if c)
                tds.append(f'<td class="{cls}">{esc(f["expected"])}<br><small>{esc(fmt(f["observed"]))}</small></td>')
        body.append(f'<tr><th scope="row">SMD {r["effect"]:g}, {esc(r["n"])}, k {r["k"]}</th>{"".join(tds)}</tr>')
    return (f'<div class="table-wrap"><table class="cells" aria-label="{esc(it["label"])}"><thead><tr>{head1}</tr><tr>{head2}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>')


def main_verdict(R):
    v = next(i["verdict"] for i in R["items"] if i["id"] == "text.main_claim")
    return {"exact": "holds", "agrees": "holds", "partly": "holds in part"}.get(v, "does not hold")


def main(results, run, out):
    R = json.loads(Path(results).read_text())
    from build_results import facts_of, fill
    pub = json.load(open(Path(run) / "published_values.json"))
    sm = R["summary"]
    facts = {**facts_of(Path(run)), **sm, "attempted": sm["items"] - sm["not_attempted"],
             "agree_total": sm.get("exact", 0) + sm.get("agrees", 0), "main_verdict": main_verdict(R), "reviewed": sm.get("reviewed", 0)}
    N = fill(json.loads((HERE.parent / "results_notes.json").read_text())["page"], facts)
    items = R["items"]
    by = {i["id"]: i for i in items}

    def label_row(anchor, name, ids):
        v = worst([by[i]["verdict"] for i in ids])
        cls, word = STAMP.get(v, ("running", "Not attempted"))
        return f'<li><a href="#{anchor}"><span>{esc(name)}</span><span class="v" data-v="{cls}">{esc(word)}</span></a></li>'
    label = "<ol>" + "".join(label_row(a, k, ids) for a, k, ids in N["label_rows"]) + "</ol>"

    stations = []
    for n in ("3", "4", "5", "6", "7", "8"):
        it = by[f"table{n}"]
        h, k, _ = hits(it)
        note = (it.get("cause") or {}).get("summary", "")
        stations.append(
            f'<section class="station surface" id="table-{n}" aria-labelledby="table-{n}-head"><header class="station-head">'
            f'<h2 id="table-{n}-head">Table {n}</h2><p class="caption">{esc(N["captions"][n])} {h} of {k} cells within tolerance.</p>'
            f'{stamp(it["verdict"])}</header>{cell_grid(it, pub["tables"][n]["rows"])}'
            f'<div class="station-foot"><p class="note">{esc(note or N["no_miss_note"])}</p></div></section>')

    rows = []
    for i in items:
        fields = ""
        if i["method"] == "values" and len(i["values"]["fields"]) <= 16:
            exc = {e["field"] for e in i["values"].get("exceptions", [])}
            fields = "<ul class=fields>" + "".join(
                f"<li>{esc(f['name'])}: paper {esc(str(f['expected']))}, ours <strong>{esc(fmt(f['observed']) if not isinstance(f['observed'], str) else f['observed'])}</strong>"
                + (" (a slip in the paper, left out)" if f["name"] in exc else "") + "</li>"
                for f in i["values"]["fields"]) + "</ul>"
        cause = (i.get("cause") or {}).get("summary", "")
        rows.append(f"<tr><td>{esc(i['label'])}</td><td>{stamp(i['verdict'])}</td><td>{esc(measure(i))}{fields}</td><td>{esc(cause)}</td></tr>")
    extra = (f'<section class="container after-bench" aria-labelledby="items-head"><div class="station surface" id="items">'
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
    outp = Path(out) / "index.html"
    outp.parent.mkdir(parents=True, exist_ok=True)
    page = with_install_block(page)
    page = with_session(page, Path(__file__).resolve().parents[2], outp)
    outp.write_text(page)
    print(f"wrote {outp} ({len(page) // 1024} KB)", file=sys.stderr)


if __name__ == "__main__":
    main(*sys.argv[1:4])
