"""Build the results page from results.json, the renders and the published figures.

usage: build_page.py RESULTS_JSON FIG_DIR PUBLISHED_DIR OUT_DIR [TABLES_JSON]
(renders fig*_ours.png in FIG_DIR; writes OUT_DIR/index.html; TABLES_JSON from compare.py adds
Tables 2 and 3 in the paper's layout, published next to ours)

Every verdict on the page is read from results.json (computed there by check_results.py); prose
that is not a number comes from results_notes.json ("page"). Images are embedded, so the page
works offline; it links ../results.css like the site's other results pages.
"""
import base64
import html
import io
import json
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
esc = html.escape
STAMP = {"exact": ("agrees", "Exact"), "agrees": ("agrees", "Agrees"), "partly": ("partly", "Partly agrees"),
         "inconclusive": ("partly", "Inconclusive"), "differs": ("differs", "Differs")}
FIGS = {"3": "fig3", "4": "fig4"}
CAPTIONS = {
    "3": "Fig. 3. Test-set accuracy on ALL-AML, lung and prostate: Tan and Gilbert's bagged decision trees and the best cited method (quoted, kept as published) and the paper's method (redrawn from our run).",
    "4": "Fig. 4. Accuracy without test sets: the best cited method (kept as published) and the paper's method (redrawn from our run): DLBCL on Cho and Won's 22/25 split, ovarian by 10-fold CV, colon by LOOCV.",
}
NAMES = {"allaml": "ALL-AML", "lung": "Lung", "prostate": "Prostate", "dlbcl": "DLBCL", "ovarian": "Ovarian",
         "colon": "Colon", "mll": "MLL"}


def tables_section(T):
    """Tables 2 and 3 in the paper's layout: published, ours (correct of total), and the spread."""
    def cell(c):
        o = c["ours"]
        return (f"<td>{esc(c['published'])}%</td><td><strong>{esc(o['percent'])}%</strong> "
                f"<small>{o['correct']}/{o['total']}</small></td>")
    def spread(runs):
        return ", ".join(f"{r['correct']}/{r['total']}" for r in runs)
    t2 = T["table2"]
    head2 = "".join(f'<th scope="col" colspan="2">{NAMES[d]}</th>' for d in t2["test"])
    sub = "".join('<th scope="col">Paper</th><th scope="col">Ours</th>' for _ in t2["test"])
    rows2 = "".join(f'<tr><th scope="row">{esc(lab)}</th>' + "".join(
        f'<td colspan="2">{esc(v)}% <small>quoted</small></td>' for v in T["table2_cited"][key].values()) + "</tr>"
        for key, lab in (("bagged", "Bagged decision trees"), ("best", "The best methods")))
    rows2 += "".join(f'<tr><th scope="row">{esc(lab)}</th>' + "".join(cell(t2[r][d]) for d in t2[r]) + "</tr>"
                     for r, lab in (("test", "Our methods (test set)"), ("loocv", "LOOCV on training samples")))
    t3 = T["table3"]
    head3 = "".join(f'<th scope="col" colspan="2">{NAMES[d]}</th>' for d in t3["loocv"])
    rows3 = "".join(f'<tr><th scope="row">{esc(lab)}</th>' + "".join(cell(t3[r][d]) for d in t3[r]) + "</tr>"
                    for r, lab in (("loocv", "LOOCV, our method"), ("cv10", "10-fold CV, our method")))
    seeds = "".join(f"<li>{NAMES[d]} test set, seeds 0 to 4: {esc(spread(r))}</li>" for d, r in T["seeds"].items())
    folds = "".join(f"<li>{NAMES[d]} 10-fold CV, three fold assignments: {esc(spread(r))}</li>" for d, r in T["folds"].items())
    c = T["cho"]
    cho = (f"<li>DLBCL, {c['splits']} random 22/25 splits (11 + 11 training samples): mean {c['mean_percent']}%; "
           f"correct per split {esc(', '.join(map(str, c['correct_per_split'])))} of 25</li>")
    return (f'<section class="container after-bench" aria-labelledby="tables-head"><div class="station surface" id="tables">'
            f'<header class="station-head"><h2 id="tables-head">Tables 2 and 3</h2><p class="caption">The paper\'s accuracies next to our run '
            f'(seed 0, first fold assignment), with the correct count. The quoted rows come from other papers and are not rerun.</p></header>'
            f'<div class="table-wrap"><table class="record dense"><thead><tr><th scope="col">Table 2</th>{head2}</tr>'
            f'<tr><th></th>{sub}</tr></thead><tbody>{rows2}</tbody></table></div>'
            f'<div class="table-wrap"><table class="record dense"><thead><tr><th scope="col">Table 3</th>{head3}</tr>'
            f'<tr><th></th>{sub}</tr></thead><tbody>{rows3}</tbody></table></div>'
            f'<p class="note">How much a rerun moves:</p><ul class="fields">{seeds}{folds}{cho}</ul></div></section>')


def b64(path):
    buf = io.BytesIO()
    im = Image.open(path).convert("RGB")
    if im.width > 2000:
        im = im.resize((2000, round(im.height * 2000 / im.width)), Image.LANCZOS)
    im.save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode(), im.size


def stamp(v, small=""):
    if v == "not_attempted":
        return '<span class="stamp" data-v="running">Not attempted</span>'
    cls, word = STAMP[v]
    return f'<span class="stamp" data-v="{cls}">{esc(word)}' + (f"<small>{esc(small)}</small>" if small else "") + "</span>"


def worst(vs):
    order = ["differs", "inconclusive", "partly", "agrees", "exact"]
    vs = [v for v in vs if v in order]
    return min(vs, key=order.index) if vs else "not_attempted"


def measure(it):
    if it["method"] == "values":
        f = it["values"]["fields"]
        from check_results import field_matches
        hits = sum(field_matches(x, it["values"].get("tolerance")) for x in f)
        return f"{hits} of {len(f)} values"
    if it["method"] == "pixels":
        p = it["pixels"]
        s = min(p["published_near_ours"], p["ours_near_published"])
        return f"{100 * s:.1f}% within {p['tolerance_px']} px"
    return ""


def fmt(v):
    if isinstance(v, float):
        return f"{v:g}"
    return str(v)


def main(results, figs, pub, out, tables=None):
    sys.path.insert(0, str(HERE))
    R = json.loads(Path(results).read_text())
    N = json.loads((HERE.parent / "results_notes.json").read_text())["page"]
    items = R["items"]
    by = {i["id"]: i for i in items}
    sm = R["summary"]

    lede = N["lede"].format(**sm, attempted=sm["items"] - sm["not_attempted"])
    label = "".join(
        f'<a class="label-row" href="#{a}"><span>{esc(k)}</span><span>{esc(STAMP.get(worst([by[i]["verdict"] for i in ids]), ("", "Not attempted"))[1])}</span></a>'
        for a, k, ids in N["label_rows"])

    stations, figjs = [], []
    for n, prefix in FIGS.items():
        its = [i for i in items if (i["id"] == prefix or (i["id"].startswith(prefix) and not i["id"][len(prefix)].isdigit()))
               and i["method"] in ("pixels", "values")]
        if not its:
            continue
        v = worst([i["verdict"] for i in its])
        pf = Path(pub) / f"figure-{n}.png"
        psrc, (w, h) = b64(pf if pf.exists() else Path(pub) / f"figure-{n}.jpg")
        osrc, _ = b64(Path(figs) / f"fig{n}_ours.png")
        stats = "".join(f"<div><dt>{esc(i['label'])}</dt><dd>{esc(measure(i))} · {esc(STAMP[i['verdict']][1] if i['verdict'] in STAMP else '')}</dd></div>"
                        .replace(" · ", ", ") for i in its)
        causes = []
        for i in its:
            c = (i.get("cause") or {}).get("summary")
            if c and c not in causes:
                causes.append(c)
        note = " ".join(causes)
        stations.append(
            f'<section class="station surface" id="fig-{n}" aria-labelledby="fig-{n}-head">'
            f'<header class="station-head"><h2 id="fig-{n}-head">Fig. {n}</h2><p class="caption">{esc(CAPTIONS[n])}</p>{stamp(v)}</header>'
            f'<div class="stage"><div class="pair">'
            f'<figure class="plate"><figcaption>Published</figcaption><img src="{psrc}" alt="Figure {n} as published" width="{w}" height="{h}"></figure>'
            f'<figure class="plate"><figcaption>Our run</figcaption><img src="{osrc}" alt="Figure {n} redrawn from our run" width="{w}" height="{h}"></figure>'
            f'</div></div><div class="station-foot"><dl class="dose">{stats}</dl><p class="note">{esc(note)}</p></div></section>')
        figjs.append({"id": n, "w": w, "h": h})

    rows = []
    for i in items:
        fields = ""
        if i["method"] == "values":
            fields = "<ul class=fields>" + "".join(
                f"<li>{esc(f['name'])}: paper {esc(fmt(f['expected']))}, ours <strong>{esc(fmt(f['observed']))}</strong></li>"
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
    tables_html = tables_section(json.loads(Path(tables).read_text())) if tables else ""
    for k, v in {"LEDE": esc(lede), "LABEL": label, "STATIONS": "".join(stations), "EXTRA": extra, "TABLES": tables_html,
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
