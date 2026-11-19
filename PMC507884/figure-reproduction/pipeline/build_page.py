#!/usr/bin/env python3
"""Build the results page from results.json, tables.json, the renders and the published figures.

usage: build_page.py RESULTS_JSON TABLES_JSON FIG_DIR PUBLISHED_DIR OUT_DIR

Every verdict and every number on the page is read from results.json (verdicts computed there by
check_results.py) or tables.json (written by compare.py); prose that is not a number comes from
results_notes.json ("page"), with {placeholders} filled from the results summary. Images are
embedded, so the page works offline; it links ../results.css like the site's other results pages.
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
from check_results import field_matches, verdict_of  # noqa: E402

esc = html.escape
STAMP = {"exact": ("agrees", "Exact"), "agrees": ("agrees", "Agrees"), "partly": ("partly", "Partly agrees"),
         "inconclusive": ("partly", "Inconclusive"), "differs": ("differs", "Differs")}
FIGS = {
    "1": (["fig1.a", "fig1.b"], "Fig. 1. Relative expression of six genes in 80 breast tumours, raw (a) and on a log scale (b); tumours ordered by the mean of their log values."),
    "2": (["fig2"], "Fig. 2. Vandesompele et al.'s data on a log scale: ten genes by sample and tissue type."),
    "3": (["fig3", "fig3.bias2", "fig3.sigma2"], "Fig. 3. Mean squared error of each gene in each tissue type, split into squared bias (red) and variance (white), signed by the bias."),
}


def b64(path):
    buf = io.BytesIO()
    im = Image.open(path).convert("RGB")
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


def measure(it):
    return verdict_of(it, [])[1]


def jtable(tid, caption, head, rows, verdict, note=""):
    th = "".join(f'<th scope="col"{" class=num" if n else ""}>{esc(h)}</th>' for h, n in head)
    body = "".join("<tr>" + "".join(f'<td{" class=num" if n else ""}>{c}</td>' for c, (_, n) in zip(r, head)) + "</tr>" for r in rows)
    return (f'<figure class="jt" id="{tid}"><figcaption>{caption} {stamp(verdict)}</figcaption>'
            f'<div class="table-wrap"><table><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table></div>'
            + (f'<p class="note">{esc(note)}</p>' if note else "") + "</figure>")


def mark(paper, ours, tol):
    """Ours, with * when it is not the printed value at its precision."""
    ok = field_matches({"expected": paper, "observed": ours}, tol)
    return esc(str(ours)) + ("" if ok else " *")


def main(results, tables, figs, pub, out):
    R = json.loads(Path(results).read_text())
    T = json.loads(Path(tables).read_text())
    N = json.loads((HERE.parent / "results_notes.json").read_text())["page"]
    items = R["items"]
    by = {i["id"]: i for i in items}
    sm = R["summary"]
    fill = {**sm, "attempted": sm["items"] - sm["not_attempted"]}

    lede = N["lede"].format(**fill)
    label = "".join(
        f'<a class="label-row" href="#{a}"><span>{esc(k)}</span><span>{esc(STAMP.get(worst([by[i]["verdict"] for i in ids]), ("", "Not attempted"))[1])}</span></a>'
        for a, k, ids in N["label_rows"])

    P = {"printed": True}
    t1 = jtable("table1", "Table 1. Model 1a standard deviations of log expression, with 95% intervals. Paper, then ours; * not as printed.",
                [("Gene", 0), ("Paper", 1), ("Ours", 1), ("nlme intervals() over 24 parameterizations", 0)],
                [[esc(r["gene"]), esc(r["paper"]), esc(r["ours"]), esc(r["nlme_range"])] for r in T["table1"]],
                worst([by["table1"]["verdict"], by["table1.ci"]["verdict"]]), by["table1.ci"].get("cause", {}).get("summary", ""))
    t2 = jtable("table2", "Table 2. Best gene set of each size and the SD of its log geometric mean. * not as printed.",
                [("Size", 1), ("Paper", 0), ("SD", 1), ("Ours", 0), ("SD", 1), ("Printed formula, SD", 1)],
                [[str(r["size"]), esc(r["paper_set"]), esc(r["paper_sd"]), esc(r["ours_set"]), mark(r["paper_sd"], r["ours_sd"], P),
                  esc(r["printed_formula_sd"])] for r in T["table2"]],
                by["table2"]["verdict"], by["table2"].get("cause", {}).get("summary", ""))
    rows3 = [[esc(r["gene"]), esc(r["paper"]), mark(r["paper"], r["ours"], P)] for r in T["table3"]["sigma"]]
    rows3 += [[esc(r["tissue"]), esc(r["paper"]), mark(r["paper"], r["ours"], P)] for r in T["table3"]["varsigma"]]
    t3 = jtable("table3", "Table 3. Model 2: gene SDs sigma_j, then tissue multipliers varsigma_k (bone marrow 1). * not as printed.",
                [("", 0), ("Paper", 1), ("Ours", 1)], rows3,
                worst([by["table3.sigma"]["verdict"], by["table3.varsigma"]["verdict"]]), by["table3.sigma"].get("cause", {}).get("summary", ""))
    t4 = jtable("table4", "Table 4. Minimax-MSE gene set with at most each number of members. * not as printed. Last two columns: the same search with the bias of a set taken as the mean of its genes' biases.",
                [("Size", 1), ("Paper", 0), ("MSE", 1), ("Ours", 0), ("MSE", 1), ("Mean bias", 0), ("MSE", 1)],
                [[str(r["size"]), esc(r["paper_set"]), esc(r["paper_mse"]), esc(r["ours_set"]), mark(r["paper_mse"], r["ours_mse"], P),
                  esc(r["mean_bias_set"]), esc(r["mean_bias_mse"])] for r in T["table4"]],
                by["table4"]["verdict"], by["table4"].get("cause", {}).get("summary", ""))
    tab_station = (f'<section class="station surface" id="tables" aria-labelledby="tables-head">'
                   f'<header class="station-head"><h2 id="tables-head">Tables 1 to 4</h2><p class="caption">{esc(N["tables_caption"])}</p>'
                   f'{stamp(worst([by[k]["verdict"] for k in ("table1", "table1.ci", "table2", "table3.sigma", "table3.varsigma", "table4")]))}</header>'
                   f'<div class="stack">{t1}{t2}{t3}{t4}</div></section>')

    stations, figjs = [], []
    for n, (ids, caption) in FIGS.items():
        its = [by[i] for i in ids]
        v = worst([i["verdict"] for i in its])
        psrc, (w, h) = b64(Path(pub) / f"Fig{n}.png")
        osrc, _ = b64(Path(figs) / f"fig{n}_ours.png")
        stats = "".join(f"<div><dt>{esc(i['label'])}</dt><dd>{esc(measure(i))}, {esc(STAMP[i['verdict']][1])}</dd></div>" for i in its)
        causes = []
        for i in its:
            c = (i.get("cause") or {}).get("summary")
            if c and c not in causes:
                causes.append(c)
        stations.append(
            f'<section class="station surface" id="fig-{n}" aria-labelledby="fig-{n}-head">'
            f'<header class="station-head"><h2 id="fig-{n}-head">Fig. {n}</h2><p class="caption">{esc(caption)}</p>{stamp(v)}</header>'
            f'<div class="stage"><div class="pair">'
            f'<figure class="plate"><figcaption>Published</figcaption><img src="{psrc}" alt="Figure {n} as published" width="{w}" height="{h}"></figure>'
            f'<figure class="plate"><figcaption>Our run</figcaption><img src="{osrc}" alt="Figure {n} redrawn from our run" width="{w}" height="{h}"></figure>'
            f'</div></div><div class="station-foot"><dl class="dose">{stats}</dl><p class="note">{esc(" ".join(causes))}</p></div></section>')
        figjs.append({"id": n, "w": w, "h": h})
    stations.insert(1, tab_station)

    rows = []
    for i in items:
        fields = ""
        if i["method"] == "values" and len(i["values"]["fields"]) <= 12:
            fields = "<ul class=fields>" + "".join(
                f"<li>{esc(f['name'])}: paper {esc(str(f['expected']))}, ours <strong>{esc(str(f['observed']))}</strong></li>"
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
    for k, v in {"LEDE": esc(lede), "LABEL": label, "STATIONS": "".join(stations), "EXTRA": extra,
                 "RECOVERED": recovered, "MATCHED_INTRO": esc(N["matched_intro"]), "MATCHED": matched,
                 "CLOSING": esc(N["closing"])}.items():
        page = page.replace(f"<!--__{k}__-->", v)
    page = page.replace("/*__FIGS__*/[]", json.dumps(figjs))
    out = Path(out) / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page)
    print(f"wrote {out} ({len(page) // 1024} KB)")


if __name__ == "__main__":
    main(*sys.argv[1:6])
