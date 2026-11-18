#!/usr/bin/env python3
"""Build the results page from results.json, the renders and the published figures.

usage: build_page.py RESULTS_JSON FIG_DIR PUBLISHED_DIR OUT_DIR

Every verdict and number on the page is read from results.json (verdicts computed there by
check_results.py); prose that is not a number comes from results_notes.json ("page"). Images are
embedded, so the page works offline; it links ../results.css like the site's other results pages.
Pixel-scored panels (drawn on the published pixel grid) get the side-by-side, swipe, blink, overlay
and difference views; panels compared as values show the published panel next to our render.
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

# anchor id, title, items, published image, our image, pixel views
STATIONS = [
    ("1a", "Fig. 1a", ["fig1a", "text.mapping", "text.truncation"], "fig1a.png", "fig1a_overlay.png", False),
    ("2a", "Fig. 2a", ["fig2a", "text.fig2", "text.core_targets"], "fig2a.png", "fig2a_overlay.png", False),
    ("3a", "Fig. 3a", ["fig3a", "text.fig3"], "fig3a.png", "fig3a_overlay.png", False),
    ("3b", "Fig. 3b", ["fig3b"], "fig3b.png", "fig3b_overlay.png", False),
    ("5a", "Fig. 5a", ["fig5.a", "fig5.counts"], "fig5.png", "fig5a_ours.png", True),
    ("5b", "Fig. 5b", ["fig5.b", "fig5.counts"], "fig5.png", "fig5b_ours.png", True),
    ("6", "Fig. 6", ["fig6"], "fig6.png", "fig6_ours.png", True),
    ("7a", "Fig. 7a", ["fig7a", "figS5"], "fig7.png", "fig7a_ours.png", True),
    ("7b", "Fig. 7b", ["fig7b"], None, "fig7b_overlay.png", False),
    ("s2", "Fig. S2", ["figS2.a", "figS2.b"], None, "figS2_overlay.png", False),
    ("s4", "Fig. S4", ["figS4"], None, "figS4_overlay.png", False),
]
TABLES = [("table1", "Table 1"), ("tableS1", "Table S1"), ("tableS2", "Table S2"), ("tableS5", "Table S5"),
          ("tableS7", "Table S7"), ("tableS8", "Table S8")]


def b64(path, max_w=1400):
    buf = io.BytesIO()
    im = Image.open(path).convert("RGB")
    if im.width > max_w:
        im = im.resize((max_w, round(im.height * max_w / im.width)))
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


def fmt(v):
    if v is None:
        return "none"
    if isinstance(v, float):
        return f"{v:,.3f}".rstrip("0").rstrip(".") if abs(v) < 1000 else f"{v:,.0f}"
    if isinstance(v, int):
        return f"{v:,}"
    return str(v)


def values_table(item, title):
    v = item["values"]
    rows = []
    exc = {e["field"] for e in v.get("exceptions", [])}
    for f in v["fields"]:
        ok = field_matches(f, v.get("tolerance"))
        mark = "paper error" if f["name"] in exc else ("" if ok else "differs")
        rows.append(f'<tr><td>{esc(f["name"])}</td><td class="num">{esc(fmt(f["expected"]))}</td>'
                    f'<td class="num">{esc(fmt(f["observed"]))}</td><td>{esc(mark)}</td></tr>')
    return (f'<figure class="jt" id="{esc(item["id"])}"><figcaption>{esc(title)}. {esc(item["label"])}: '
            f'{esc(measure(item))}.</figcaption><div class="table-wrap"><table><thead><tr><th scope="col">Value</th>'
            f'<th class="num" scope="col">Paper</th><th class="num" scope="col">Ours</th><th scope="col"></th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div></figure>')


def main(results, figs, pub, out):
    R = json.loads(Path(results).read_text())
    N = json.loads((HERE.parent / "results_notes.json").read_text())["page"]
    items = R["items"]
    by = {i["id"]: i for i in items}
    sm = R["summary"]
    lede = N["lede"].format(**sm, attempted=sm["items"] - sm["not_attempted"])
    label = "".join(
        f'<a class="label-row" href="#{a}"><span>{esc(k)}</span><span>{esc(STAMP.get(worst([by[i]["verdict"] for i in ids if i in by]), ("", "Not attempted"))[1])}</span></a>'
        for a, k, ids in N["label_rows"])

    stations, figjs = [], []
    tabs = "".join(values_table(by[k], t) for k, t in TABLES if k in by and by[k]["method"] == "values")
    tv = worst([by[k]["verdict"] for k, _ in TABLES if k in by])
    stations.append(f'<section class="station surface" id="tables" aria-labelledby="tables-head">'
                    f'<header class="station-head"><h2 id="tables-head">Tables</h2><p class="caption">{esc(N["tables_caption"])}</p>{stamp(tv)}</header>'
                    f'<div class="stack">{tabs}</div><div class="station-foot"><p class="note">{esc(N["tables_note"])}</p></div></section>')
    for anchor, title, ids, pubfile, ourfile, pixel in STATIONS:
        its = [by[i] for i in ids if i in by]
        if not its or not (Path(figs) / ourfile).exists():
            continue
        v = worst([i["verdict"] for i in its])
        stats = "".join(f"<div><dt>{esc(i['label'])}</dt><dd>{esc(measure(i))}, {esc(STAMP.get(i['verdict'], ('', 'not attempted'))[1])}</dd></div>" for i in its)
        causes = []
        for i in its:
            c = (i.get("cause") or {}).get("summary")
            if c and c not in causes:
                causes.append(c)
        cap = N["captions"].get(anchor, "")
        osrc, (w, h) = b64(Path(figs) / ourfile)
        if pixel:
            psrc, _ = b64(Path(pub) / pubfile)
            pair = (f'<figure class="plate"><figcaption>Published</figcaption><img src="{psrc}" alt="{esc(title)} as published" width="{w}" height="{h}"></figure>'
                    f'<figure class="plate"><figcaption>Our run</figcaption><img src="{osrc}" alt="{esc(title)} redrawn from our run" width="{w}" height="{h}"></figure>')
            figjs.append({"id": anchor, "w": w, "h": h})
        else:
            pair = f'<figure class="plate"><figcaption>Published (left) and our run (right)</figcaption><img src="{osrc}" alt="{esc(title)}, published and ours" width="{w}" height="{h}"></figure>'
        tables = "".join(values_table(i, title) for i in its if i["method"] == "values")
        stations.append(
            f'<section class="station surface" id="fig-{anchor}" aria-labelledby="fig-{anchor}-head">'
            f'<header class="station-head"><h2 id="fig-{anchor}-head">{esc(title)}</h2><p class="caption">{esc(cap)}</p>{stamp(v)}</header>'
            f'<div class="stage"><div class="pair">{pair}</div></div>'
            f'<div class="station-foot"><dl class="dose">{stats}</dl><p class="note">{esc(" ".join(causes))}</p>'
            f'<details><summary>Every value</summary><div class="stack">{tables}</div></details></div></section>')

    rows = []
    for i in items:
        cause = (i.get("cause") or {}).get("summary", "")
        rows.append(f"<tr><td>{esc(i['label'])}</td><td>{stamp(i['verdict'])}</td><td>{esc(measure(i))}</td><td>{esc(cause)}</td></tr>")
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
    main(*sys.argv[1:5])
