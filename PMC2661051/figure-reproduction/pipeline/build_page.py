#!/usr/bin/env python3
"""Build the results page from results.json, tables.json, the renders and the published figures.

usage: build_page.py RESULTS_JSON TABLES_JSON FIG_DIR PUBLISHED_DIR OUT_DIR

Every verdict and every number on the page is read from results.json (verdicts computed there by
check_results.py) or tables.json (written by compare.py); prose that is not a number comes from
results_notes.json ("page"). Images are embedded, so the page works offline; it links
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
FIGS = {"2": "fig2", "3": "fig3", "4": "fig4"}
CAPTIONS = {
    "2": "Fig. 2. p53 data, squared moderated t. Left: number of significant gene sets against the p-value cutoff for eight gene set statistics, resampling (black) and permutation (blue). Right: the counts at cutoff 0.01.",
    "3": "Fig. 3. The 290 p53 gene sets. Top: histogram of the mean pairwise correlation in each set. Bottom: of the mean absolute correlation.",
    "4": "Fig. 4. Hedenfalk data, as Fig. 2.",
}
TABLES = [
    ("table2", "Table 2", "Detection rates (share of 100 data sets with p <= 0.05): gene-level statistic and transformation; mean, resampling.",
     [("t.none", "none t"), ("modt.none", "none mod.t"), ("corr.none", "none corr"), ("t.square", "sq t"), ("modt.square", "sq mod.t"),
      ("corr.square", "sq corr"), ("t.ranksq", "rank sq t"), ("modt.ranksq", "rank sq mod.t"), ("corr.ranksq", "rank sq corr"),
      ("t.binary", "binary t"), ("modt.binary", "binary mod.t"), ("corr.binary", "binary corr"), ("t.lfdr", "lfdr t"),
      ("modt.lfdr", "lfdr mod.t"), ("corr.lfdr", "lfdr corr")]),
    ("table3", "Table 3", "Gene set statistics; squared moderated t, resampling.",
     [("mean", "mean"), ("maxmean", "maxmean"), ("median", "median"), ("es", "ES"), ("condfdr", "cond. FDR"), ("wilcoxon", "Wilcoxon")]),
    ("table4", "Table 4", "Significance assessment; mean of squared moderated t.",
     [("parametric", "parametric"), ("resampling", "resampling"), ("permutation", "permutation"), ("restandardization", "restand.")]),
    ("table5", "Table 5", "globaltest.",
     [("parametric", "parametric"), ("resampling", "resampling"), ("permutation", "permutation"), ("restandardization", "restand.")]),
    ("table6", "Table 6", "Hotelling T2 with a shrinkage correlation.",
     [("resampling", "resampling"), ("permutation", "permutation"), ("restandardization", "restand.")]),
]


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


def measure(it):
    if it["method"] == "values":
        f = it["values"]["fields"]
        hits = sum(field_matches(x, it["values"].get("tolerance")) for x in f)
        return f"{hits} of {len(f)} values"
    if it["method"] == "check":
        return it["check"].get("detail", "")
    return ""


def fmt(v):
    return "none" if v is None else str(v)


def journal_table(item, title, caption, cols):
    fields = {f["name"]: f for f in item["values"]["fields"]}
    head = "".join(f'<th class="num" scope="col">{esc(lab)}</th>' for _, lab in cols)
    rows = []
    for i in range(1, 10):
        s = f"set{i}"
        cells = []
        for key, _ in cols:
            f = fields[f"{s}, {key}"]
            ok = field_matches(f, item["values"].get("tolerance"))
            cells.append(f'<td class="num">{esc(f["expected"])} / {esc(f["observed"])}{"" if ok else " *"}</td>')
        rows.append(f"<tr><td>set {i}</td>{''.join(cells)}</tr>")
    return (f'<figure class="jt" id="{item["id"]}"><figcaption>{esc(title)}. {esc(caption)} Paper / ours; '
            f'* outside the Monte Carlo band. {esc(measure(item))} within the band.</figcaption>'
            f'<div class="table-wrap"><table><thead><tr><th scope="col">set</th>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table></div></figure>')


def main(results, tables, figs, pub, out):
    R = json.loads(Path(results).read_text())
    T = json.loads(Path(tables).read_text())
    N = json.loads((HERE.parent / "results_notes.json").read_text())["page"]
    items = R["items"]
    by = {i["id"]: i for i in items}
    sm = R["summary"]

    lede = N["lede"].format(**sm, attempted=sm["items"] - sm["not_attempted"], replicates=T["replicates"])
    label = "".join(
        f'<a class="label-row" href="#{a}"><span>{esc(k)}</span><span>{esc(STAMP.get(worst([by[i]["verdict"] for i in ids]), ("", "Not attempted"))[1])}</span></a>'
        for a, k, ids in N["label_rows"])

    # The simulation tables, as the journal printed them, paper and ours in each cell.
    tabs = "".join(journal_table(by[k], t, c, cols) for k, t, c, cols in TABLES)
    t7 = by["table7"]
    t7rows = "".join(f'<tr><td>{esc(f["name"])}</td><td class="num">{esc(f["expected"])}</td><td class="num">{esc(fmt(f["observed"]))}</td></tr>'
                     for f in t7["values"]["fields"])
    tabs += (f'<figure class="jt" id="table7"><figcaption>Table 7. Hedenfalk sets with p <= 0.01 (mean of squared moderated t, '
             f'permutation). {esc(measure(t7))} as printed or within the Monte Carlo band of 1000 permutations.</figcaption>'
             f'<div class="table-wrap"><table><thead><tr><th scope="col">Set</th><th class="num" scope="col">paper</th>'
             f'<th class="num" scope="col">ours</th></tr></thead><tbody>{t7rows}</tbody></table></div></figure>')
    sim_v = worst([by[k]["verdict"] for k, *_ in TABLES])
    sim_station = (f'<section class="station surface" id="tables" aria-labelledby="tables-head">'
                   f'<header class="station-head"><h2 id="tables-head">Tables 2 to 7</h2><p class="caption">{esc(N["tables_caption"])}</p>{stamp(sim_v, reviewed([by[k] for k, *_ in TABLES]))}</header>'
                   f'<div class="stack">{tabs}</div><div class="station-foot"><p class="note">{esc(N["tables_note"])}</p></div></section>')

    stations, figjs = [sim_station], []
    for n, prefix in FIGS.items():
        its = [i for i in items if i["id"].startswith(prefix + ".") and i["method"] in ("pixels", "values")]
        if not its:
            continue
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
            f'<header class="station-head"><h2 id="fig-{n}-head">Fig. {n}</h2><p class="caption">{esc(CAPTIONS[n])}</p>{stamp(v, reviewed(its))}</header>'
            f'<div class="stage"><div class="pair">'
            f'<figure class="plate"><figcaption>Published</figcaption><img src="{psrc}" alt="Figure {n} as published" width="{w}" height="{h}"></figure>'
            f'<figure class="plate"><figcaption>Our run</figcaption><img src="{osrc}" alt="Figure {n} redrawn from our run" width="{w}" height="{h}"></figure>'
            f'</div></div><div class="station-foot"><dl class="dose">{stats}</dl><p class="note">{esc(" ".join(causes))}</p></div></section>')
        figjs.append({"id": n, "w": w, "h": h})

    rows = []
    for i in items:
        fields = ""
        if i["method"] == "values" and len(i["values"]["fields"]) <= 20:
            fields = "<ul class=fields>" + "".join(
                f"<li>{esc(f['name'])}: paper {esc(fmt(f['expected']))}, ours <strong>{esc(fmt(f['observed']))}</strong></li>"
                for f in i["values"]["fields"]) + "</ul>"
        cause = (i.get("cause") or {}).get("summary", "")
        if i["verdict"] == "not_attempted" and not cause:
            cause = "Not attempted."
        rows.append(f"<tr><td>{esc(i['label'])}</td><td>{stamp(i['verdict'], reviewed([i]))}</td><td>{esc(measure(i))}{fields}</td><td>{esc(cause)}</td></tr>")
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
