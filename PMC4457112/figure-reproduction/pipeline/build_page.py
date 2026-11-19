#!/usr/bin/env python3
"""Build the results page from results.json.

Usage: build_page.py RESULTS_JSON RUN_OUTPUT_DIR OUT_DIR   (writes OUT_DIR/index.html)

Every verdict and number on the page is read from results.json (verdicts computed there by
check_results.py); the prose that is not a number comes from results_notes.json ("page"), with run
facts filled in by build_results.facts_of. The paper has no computed figure: Fig. 1 needs manual labels
that were never released, so the page shows the tables.
"""
import html
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build_results import facts_of, fill  # noqa: E402
from check_results import field_matches  # noqa: E402

esc = html.escape
STAMP = {"exact": ("agrees", "Exact"), "agrees": ("agrees", "Agrees"), "partly": ("partly", "Partly agrees"),
         "inconclusive": ("partly", "Inconclusive"), "differs": ("differs", "Differs")}
STYLE = """<style>
table.cells { border-collapse: collapse; font-family: var(--font-outlier); font-size: var(--text-xs); }
table.cells th, table.cells td { padding: 2px 6px; text-align: right; border-top: var(--rule-hair) solid var(--color-rule); white-space: nowrap; }
table.cells th { font-weight: 500; color: var(--color-muted); }
table.cells th[scope=row] { text-align: left; }
table.cells td.off { background: var(--color-paper-3); font-weight: 500; }
table.cells td small { color: var(--color-muted); }
.cellgrid { display: grid; gap: var(--space-lg); }
</style>"""


def stamp(v):
    if v == "not_attempted":
        return '<span class="stamp" data-v="running">Not attempted</span>'
    cls, word = STAMP[v]
    return f'<span class="stamp" data-v="{cls}">{esc(word)}</span>'


def worst(vs):
    order = ["differs", "inconclusive", "partly", "agrees", "exact"]
    vs = [v for v in vs if v in order]
    return min(vs, key=order.index) if vs else "not_attempted"


def counted(it):
    exc = {e["field"] for e in it["values"].get("exceptions", []) if e.get("category") == "paper_error"}
    return [x for x in it["values"]["fields"] if x["name"] not in exc], len(exc)


def measure(it):
    if it["method"] == "values":
        fs, e = counted(it)
        h = sum(field_matches(x, it["values"].get("tolerance")) for x in fs)
        near = sum(bool(x.get("within_0.01")) for x in fs)
        extra = f"; {near} within 0.01" if any("within_0.01" in x for x in fs) else ""
        return f"{h} of {len(fs)} values at printed precision{extra}" + (f" ({e} paper slip{'s' if e > 1 else ''} left out)" if e else "")
    if it["method"] == "check":
        return it["check"]["detail"]
    return ""


def fmt(v, like=None):
    if isinstance(v, bool):
        return "yes" if v else "no"
    if isinstance(v, (int, float)):
        if isinstance(like, str):
            try:
                float(like)
                dec = len(like.split(".")[1]) if "." in like else 0
                if isinstance(v, int) or dec == 0:
                    return f"{v:,.0f}" if abs(v) >= 1000 else f"{v:.0f}"
                return f"{v:.{dec}f}"
            except ValueError:
                pass
        return f"{v:,}" if isinstance(v, int) else f"{v:.4g}"
    return str(v)


def grid(it, cols, rows):
    """Measures as rows, columns as given; each cell the paper's value over ours, shaded on a miss."""
    by = {f["name"]: f for f in it["values"]["fields"]}
    head = "".join(f'<th scope="col">{esc(c)}</th>' for c, _ in cols)
    body = []
    for rlabel, rkey in rows:
        tds = []
        for _, ckey in cols:
            f = by.get(rkey(ckey))
            if not f:
                tds.append("<td></td>")
                continue
            ok = field_matches(f, it["values"].get("tolerance"))
            tds.append(f'<td class="{"" if ok else "off"}">{esc(str(f["expected"]))}<br><small>{esc(fmt(f["observed"], f["expected"]))}</small></td>')
        body.append(f'<tr><th scope="row">{esc(rlabel)}</th>{"".join(tds)}</tr>')
    return (f'<div class="table-wrap"><table class="cells" aria-label="{esc(it["label"])}"><thead><tr><th scope="col">Measure</th>{head}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>')


MEAS12 = [("AUC", "auc"), ("AUC 95% CI low", "auc ci low"), ("AUC 95% CI high", "auc ci high"),
          ("Average precision", "average precision"), ("F1", "f1"), ("Accuracy", "accuracy"),
          ("MSE, calibrated", "mse"), ("MSE, zero-centred sigmoid", "mse sigmoid")]
COLS12 = [("1987-2010 cross-validation", "1987-2010 cross-validation"), ("2011", "2011"), ("2012", "2012")]
COLS3 = [("Forward selection", "forward selection"), ("CHISQ", "chisq"), ("Post hoc drop", "posthoc"),
         ("Plus pubtypes", "plus pubtypes")]
MEAS3 = [("AUC", "auc"), ("Average precision", "average precision"), ("F1", "f1"), ("MSE", "mse"),
         ("Features", "n features")]


def main(results, run_out, out):
    R = json.loads(Path(results).read_text())
    sm = R["summary"]
    facts = {**facts_of(Path(run_out)), **sm, "attempted": sm["items"] - sm["not_attempted"]}
    N = fill(json.loads((HERE.parent / "results_notes.json").read_text())["page"], facts)
    items = R["items"]
    by = {i["id"]: i for i in items}

    def label_row(anchor, name, ids):
        v = worst([by[i]["verdict"] for i in ids])
        cls, word = STAMP.get(v, ("running", "Not attempted"))
        return f'<li><a href="#{anchor}"><span>{esc(name)}</span><span class="v" data-v="{cls}">{esc(word)}</span></a></li>'
    label = "<ol>" + "".join(label_row(a, k, ids) for a, k, ids in N["label_rows"]) + "</ol>"

    grids = []
    for tid in ("table1", "table2"):
        it = by[tid]
        g = grid(it, COLS12, [(lab, (lambda c, k=key: f"{c}, {k}")) for lab, key in MEAS12])
        grids.append(f'<section class="station surface" id="{tid}" aria-labelledby="{tid}-head"><header class="station-head">'
                     f'<h2 id="{tid}-head">{esc(it["label"])}</h2><p class="caption">{esc(measure(it))}.</p>{stamp(it["verdict"])}</header>{g}'
                     f'<div class="station-foot"><p class="note">{esc((it.get("cause") or {}).get("summary", ""))}</p></div></section>')
    it = by["table3"]
    for model, mlabel in (("citation only", "CITATION_ONLY"), ("citation plus mesh", "CITATION_PLUS_MESH")):
        g = grid(it, COLS3, [(lab, (lambda c, k=key, m=model: f"{m}, {c}, {k}")) for lab, key in MEAS3])
        grids.append(f'<section class="station surface" id="table3-{model.replace(" ", "-")}" aria-labelledby="t3{model[-4:]}-head"><header class="station-head">'
                     f'<h2 id="t3{model[-4:]}-head">Table 3, {mlabel}, 2011</h2><p class="caption">{esc(measure(it))} (both models).</p>{stamp(it["verdict"])}</header>{g}'
                     f'<div class="station-foot"><p class="note">{esc((it.get("cause") or {}).get("summary", ""))}</p></div></section>')
    tables = (f'<section class="container after-bench" aria-labelledby="tables-head" id="tables"><h2 id="tables-head">The tables</h2>'
              f'<p class="caption">{esc(N["tables_caption"])}</p><div class="cellgrid">{"".join(grids)}</div></section>')

    rows = []
    for i in items:
        fields = ""
        if i["method"] == "values" and len(i["values"]["fields"]) <= 8:
            fields = "<ul class=fields>" + "".join(
                f"<li>{esc(f['name'])}: paper {esc(str(f['expected']))}, ours <strong>{esc(fmt(f['observed'], f['expected']))}</strong></li>"
                for f in i["values"]["fields"]) + "</ul>"
        cause = (i.get("cause") or {}).get("summary", "")
        rows.append(f'<tr id="item-{esc(i["id"])}"><td>{esc(i["label"])}</td><td>{stamp(i["verdict"])}</td><td>{esc(measure(i))}{fields}</td><td>{esc(cause)}</td></tr>')
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
    for k, v in {"LEDE": esc(N["lede"]), "LABEL": label, "EXTRA": extra, "RECOVERED": recovered,
                 "MATCHED_INTRO": esc(N["matched_intro"]), "MATCHED": matched, "CLOSING": esc(N["closing"])}.items():
        page = page.replace(f"<!--__{k}__-->", v)
    outp = Path(out) / "index.html"
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(page)
    print(f"wrote {outp} ({len(page) // 1024} KB)", file=sys.stderr)


if __name__ == "__main__":
    main(*sys.argv[1:4])
