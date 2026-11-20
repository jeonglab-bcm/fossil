"""Build the results page from results.json.

Usage: build_page.py RESULTS_JSON RUN_OUTPUT_DIR OUT_DIR   (writes OUT_DIR/index.html)

Every verdict and number on the page is read from results.json (verdicts computed there by check_results.py)
or, for the facts in the prose, from the run (build_results.facts_of); the prose that is not a number comes
from results_notes.json ("page"). The paper has no figures: each of Tables 1-5 is a station with every printed
cell, the paper's value above ours, shaded where ours is outside the Monte Carlo tolerance. The page links
../results.css like the site's other results pages.
"""
import html
import os
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from check_results import field_matches  # noqa: E402

esc = html.escape
STAMP = {"exact": ("agrees", "Exact"), "agrees": ("agrees", "Agrees"), "partly": ("partly", "Partly agrees"),
         "inconclusive": ("partly", "Inconclusive"), "differs": ("differs", "Differs")}
PL = ["γ00", "γ01", "γ10", "γ11", "σ0", "σ1"]
STYLE = """<style>
table.cells { border-collapse: collapse; font-family: var(--font-outlier); font-size: var(--text-xs); }
table.cells th, table.cells td { padding: 2px 6px; text-align: right; border-top: var(--rule-hair) solid var(--color-rule); white-space: nowrap; }
table.cells th { font-weight: 500; color: var(--color-muted); }
table.cells th[scope=row] { text-align: left; }
table.cells td.first { border-left: var(--rule-hair) solid var(--color-rule); }
table.cells td.off { background: var(--color-paper-3); font-weight: 500; }
table.cells td small { color: var(--color-muted); }
ul.fields { margin: var(--space-xs) 0 0; padding-left: 1.1em; font-size: var(--text-xs); }
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
    if v is None:
        return "n/a"
    s = f"{v:.2f}" if abs(v) < 10 else (f"{v:.1f}" if abs(v) < 1000 else f"{v:.0f}")
    return s.replace("-0.00", "0.00")


def fmt3(v):
    return "n/a" if v is None else f"{v:.3f}"


def td(f, tol, first=False, f3=False):
    ok = field_matches(f, tol)
    cls = " ".join(c for c in ("first" if first else "", "" if ok else "off") if c)
    o = f["observed"]
    shown = fmt3(o) if (f3 and not isinstance(o, str)) else fmt(o)
    return f'<td class="{cls}">{esc(str(f["expected"]))}<br><small>{esc(shown)}</small></td>'


def grid(head, rows, label):
    return (f'<div class="table-wrap"><table class="cells" aria-label="{esc(label)}"><thead><tr>{head}</tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div>')


def t1_t3(by, pub):
    """Table 1 (convergence and bias) and Table 3 (non-coverage): one row per cell."""
    f1 = {f["name"]: (f, by[k]) for k in ("table1_converged", "table1_stable", "table1_lowconv") for f in by[k]["values"]["fields"]}
    f3 = {f["name"]: (f, by[k]) for k in ("table3_stable", "table3_lowconv") for f in by[k]["values"]["fields"]}
    rows1, rows3 = [], []
    for r in pub["table1"]:
        n0 = f"{r['groups']} groups x {r['size']}, ICC {r['icc']}"
        f, it = f1[f"{n0}: % converged"]
        c = [td(f, it["values"]["tolerance"])]
        for i, p in enumerate(PL):
            f, it = f1[f"{n0}: % bias {p}"]
            c.append(td(f, it["values"]["tolerance"], first=i == 0))
        rows1.append(f'<tr><th scope="row">{r["groups"]} x {r["size"]}, {r["icc"]}</th>{"".join(c)}</tr>')
        c = []
        for i, p in enumerate(PL):
            f, it = f3[f"{n0}: non-coverage {p}"]
            c.append(td(f, it["values"]["tolerance"], first=i == 0, f3=True))
        rows3.append(f'<tr><th scope="row">{r["groups"]} x {r["size"]}, {r["icc"]}</th>{"".join(c)}</tr>')
    h1 = '<th scope="col">Groups x size, ICC</th><th scope="col">% conv.</th>' + "".join(f'<th scope="col">{p}</th>' for p in PL)
    h3 = '<th scope="col">Groups x size, ICC</th>' + "".join(f'<th scope="col">{p}</th>' for p in PL)
    return grid(h1, rows1, "Table 1"), grid(h3, rows3, "Table 3")


def t2(by):
    fr = {f["name"]: f for f in by["table2_rates"]["values"]["fields"]}
    fp = {f["name"].split(" (p ")[0]: f for f in by["table2_pvalues"]["values"]["fields"]}
    tol = by["table2_rates"]["values"]["tolerance"]
    rows = []
    for p in PL:
        c = []
        for fac, lab, levels in (("groups", "groups", ("30", "50", "100")), ("size", "group size", ("5", "30", "50")),
                                 ("icc", "ICC", ("0.04", "0.17", "0.38"))):
            for i, lev in enumerate(levels):
                c.append(td(fr[f"{p}, {lab} {lev}: non-coverage"], tol, first=i == 0, f3=True))
            f = fp[f"{p}, effect of {lab} on non-coverage"]
            ok = f["expected"] == f["observed"]
            c.append(f'<td class="{"" if ok else "off"}">{esc("p < 0.05" if f["expected"] == "significant" else "n.s.")}'
                     f'<br><small>{esc("p < 0.05" if f["observed"] == "significant" else "n.s.")}</small></td>')
        rows.append(f'<tr><th scope="row">{p}</th>{"".join(c)}</tr>')
    head = ('<th scope="col">Parameter</th>' + "".join(f'<th scope="col">{x}</th>' for x in
            ("30 gr.", "50 gr.", "100 gr.", "effect", "size 5", "size 30", "size 50", "effect", "ICC 0.04", "ICC 0.17", "ICC 0.38", "effect")))
    return grid(head, rows, "Table 2")


def t4(by):
    fs = {f["name"]: f for f in by["table4"]["values"]["fields"]}
    tol = by["table4"]["values"]["tolerance"]
    rows = []
    for p in PL:
        c = []
        for q, lab in (("bias", "% bias"), ("nc", "non-coverage"), ("conv", "% converged")):
            for i, prev in enumerate(("0.10", "0.34", "0.45")):
                f = fs[f"{p}, prevalence {prev}: {lab}"]
                c.append(td(f, tol, first=i == 0, f3=q == "nc"))
        rows.append(f'<tr><th scope="row">{p}</th>{"".join(c)}</tr>')
    head = ('<th scope="col">Parameter</th>' + "".join(f'<th scope="col">{q} {x}</th>' for q in ("bias", "non-cov.", "% conv.")
                                                       for x in ("0.10", "0.34", "0.45")))
    return grid(head, rows, "Table 4")


def t5(by, pub):
    fc = {f["name"]: f for f in by["table5_converged"]["values"]["fields"]}
    fb = {f["name"]: f for f in by["table5_bias"]["values"]["fields"]}
    fn = {f["name"]: f for f in by["table5_noncoverage"]["values"]["fields"]}
    tol = by["table5_bias"]["values"]["tolerance"]
    rows = []
    for r in pub["table5"]:
        n0 = f"Model {r['model']}, {r['groups']} groups x {r['size']}"
        c = [td(fc[f"{n0}: % converged"], tol)]
        for i, p in enumerate(PL):
            c.append(td(fb[f"{n0}: % bias {p}"], tol, first=i == 0))
        for i, p in enumerate(PL):
            c.append(td(fn[f"{n0}: % non-coverage {p}"], tol, first=i == 0))
        rows.append(f'<tr><th scope="row">M{r["model"]}, {r["groups"]} x {r["size"]}</th>{"".join(c)}</tr>')
    head = ('<th scope="col">Model, groups x size</th><th scope="col">% conv.</th>'
            + "".join(f'<th scope="col">bias {p}</th>' for p in PL) + "".join(f'<th scope="col">non-cov. {p}</th>' for p in PL))
    return grid(head, rows, "Table 5")


def main_verdict(R):
    v = next(i["verdict"] for i in R["items"] if i["id"] == "text.main_claim")
    return {"exact": "holds", "agrees": "holds", "partly": "holds in part"}.get(v, "does not hold")


def main(results, run, out):
    R = json.loads(Path(results).read_text())
    from build_results import facts_of, fill
    pub = json.load(open(Path(run) / "published_values.json"))
    sm = R["summary"]
    facts = {**facts_of(Path(run)), **sm, "attempted": sm["items"] - sm["not_attempted"],
             "agree_total": sm.get("exact", 0) + sm.get("agrees", 0), "main_verdict": main_verdict(R)}
    N = fill(json.loads(Path(os.environ.get("RESULTS_NOTES", HERE.parent / "results_notes.json")).read_text())["page"], facts)
    items = R["items"]
    by = {i["id"].replace(".", "_"): i for i in items}
    by.update({i["id"]: i for i in items})

    def label_row(anchor, name, ids):
        v = worst([by[i]["verdict"] for i in ids])
        cls, word = STAMP.get(v, ("running", "Not attempted"))
        return f'<li><a href="#{anchor}"><span>{esc(name)}</span><span class="v" data-v="{cls}">{esc(word)}</span></a></li>'
    label = "<ol>" + "".join(label_row(a, k, ids) for a, k, ids in N["label_rows"]) + "</ol>"

    g1, g3 = t1_t3(by, pub)
    grids = {"1": g1, "2": t2(by), "3": g3, "4": t4(by), "5": t5(by, pub)}
    stations = []
    for n, ids in (("1", ["table1.converged", "table1.stable", "table1.lowconv"]), ("2", ["table2.rates", "table2.pvalues"]),
                   ("3", ["table3.stable", "table3.lowconv"]), ("4", ["table4"]),
                   ("5", ["table5.converged", "table5.bias", "table5.noncoverage"])):
        its = [by[i] for i in ids]
        counts = "; ".join(f"{esc(it['label'])}: {hits(it)[0]} of {hits(it)[1]}" for it in its)
        notes = "".join(f'<p class="note">{esc(it["cause"]["summary"])}</p>' for it in its if it.get("cause"))
        stations.append(
            f'<section class="station surface" id="table-{n}" aria-labelledby="table-{n}-head"><header class="station-head">'
            f'<h2 id="table-{n}-head">Table {n}</h2><p class="caption">{esc(N["captions"][n])} Within tolerance: {counts}.</p>'
            f'{stamp(worst([it["verdict"] for it in its]))}</header>{grids[n]}'
            f'<div class="station-foot">{notes or "<p class=note>" + esc(N["no_miss_note"]) + "</p>"}</div></section>')

    rows = []
    for i in items:
        fields = ""
        if i["method"] == "values" and len(i["values"]["fields"]) <= 30:
            exc = {e["field"] for e in i["values"].get("exceptions", [])}
            fields = "<ul class=fields>" + "".join(
                f"<li>{esc(f['name'])}: paper {esc(str(f['expected']))}, ours <strong>{esc(fmt(f['observed']))}</strong>"
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
    outp.write_text(page)
    print(f"wrote {outp} ({len(page) // 1024} KB)", file=sys.stderr)


if __name__ == "__main__":
    main(*sys.argv[1:4])
