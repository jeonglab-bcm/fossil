"""Build the results page from results.json, the renders and the published figures.

Usage: build_page.py RESULTS_JSON RUN_OUTPUT_DIR PUBLISHED_DIR OUT_DIR   (writes OUT_DIR/index.html)

Every verdict and number on the page is read from results.json (verdicts computed there by
check_results.py) or from the run's outputs. Images are embedded, so the page works offline; it links
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
from check_results import field_matches, verdict_of  # noqa: E402

esc = html.escape
STAMP = {"exact": ("agrees", "Exact"), "agrees": ("agrees", "Agrees"), "partly": ("partly", "Partly agrees"),
         "inconclusive": ("partly", "Inconclusive"), "differs": ("differs", "Differs")}
CAPTIONS = {
    "2": "Fig. 2. ROC curves in fivefold cross-validation of the SVM on six feature sets, all 1,385 ADRs.",
    "3": "Fig. 3. The same over the common ADRs (ADR_50+).",
    "4": "Fig. 4. ROC curves of five algorithms on the full feature set, all ADRs.",
}
STYLE = """<style>
table.cells { border-collapse: collapse; font-family: var(--font-outlier); font-size: var(--text-xs); }
table.cells th, table.cells td { padding: 2px 6px; text-align: right; border-top: var(--rule-hair) solid var(--color-rule); white-space: nowrap; }
table.cells th { font-weight: 500; color: var(--color-muted); }
table.cells th[scope=row] { text-align: left; }
table.cells td.off { background: var(--color-paper-3); font-weight: 500; }
table.cells td small { color: var(--color-muted); }
.cellgrid { display: grid; gap: var(--space-lg); }
.plate.solo img { max-width: 100%; height: auto; }
</style>"""


def b64(path, scale=1):
    buf = io.BytesIO()
    im = Image.open(path).convert("RGB")
    if scale != 1:
        im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
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


def ok(it, f):
    return field_matches(f, it["values"].get("tolerance"))


def measure(it):
    """The measure check_results.py computes with the verdict."""
    return verdict_of(it, [])[1]


def fmt(v, like=None):
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        if isinstance(like, str):
            try:
                float(like)
                dec = len(like.split(".")[1]) if "." in like else 0
                return f"{v:.{dec}f}"
            except ValueError:
                pass
        return f"{v:.4g}" if isinstance(v, float) else str(v)
    return str(v)


def grid(its, row_of, col_of, cols, aria):
    """Rows x columns of 'paper over ours' cells from one or more values items; misses shaded."""
    rows = {}
    for it in its:
        for f in it["values"]["fields"]:
            rows.setdefault(row_of(f), {})[col_of(f)] = (it, f)
    head = "".join(f'<th scope="col">{esc(c)}</th>' for c in cols)
    body = []
    for r, cs in rows.items():
        tds = []
        for c in cols:
            if c not in cs:
                tds.append("<td></td>")
                continue
            it, f = cs[c]
            tds.append(f'<td class="{"" if ok(it, f) else "off"}">{esc(str(f["expected"]))}<br><small>{esc(fmt(f["observed"], f["expected"]))}</small></td>')
        body.append(f'<tr><th scope="row">{esc(r)}</th>{"".join(tds)}</tr>')
    return (f'<div class="table-wrap"><table class="cells" aria-label="{esc(aria)}"><thead><tr><th scope="col"></th>{head}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>')


def table_station(sid, title, its, table_html, caption):
    v = worst([i["verdict"] for i in its])
    h = sum(ok(i, f) for i in its for f in i["values"]["fields"])
    n = sum(len(i["values"]["fields"]) for i in its)
    notes = " ".join(dict.fromkeys((i.get("cause") or {}).get("summary", "") for i in its if i.get("cause")))
    return (f'<section class="station surface" id="{sid}" aria-labelledby="{sid}-head"><header class="station-head">'
            f'<h2 id="{sid}-head">{esc(title)}</h2><p class="caption">{esc(caption)} Paper above, ours below; shaded where ours '
            f'differs at the printed precision. {h} of {n} cells.</p>{stamp(v)}</header>{table_html}'
            f'<div class="station-foot"><p class="note">{esc(notes)}</p></div></section>')


CAUSE_WORDS = {
    "text.headline": "the seed of the SVM's probability fit and the unstated cut-off rule",
    "text.feature_gains": "the seed of the SVM's probability fit and the unstated cut-off rule",
    "text.indication": "the seed of the SVM's probability fit and the unstated cut-off rule",
    "text.ks": "the unstated variant of the KS test",
    "text.methods": "the LR and NB settings",
    "text.class_weights": "the class weighting of RF (our AUC falls)",
    "text.data_facts": "small differences in three counts of the recovered file",
    "text.clinical": "the unstated threshold of Table 4",
    "text.fig5": "the precision and recall points behind Fig. 5",
}


def main_claim_line(M, R):
    """The verdict on the main claim and the causes of the claims that do not match, from our metrics and
    the verdicts of results.json."""
    a, b = M["svm:chem"]["all"], M["svm:chem+bio+pheno"]["all"]
    up = b["auc"] > a["auc"] and b["precision"] > a["precision"] and b["recall"] > a["recall"]
    head = next(i for i in R["items"] if i["id"] == "text.headline")
    exact = head["verdict"] in ("exact", "agrees")
    miss = [i["id"] for i in R["items"] if i["id"].startswith("text.") and i["verdict"] in ("partly", "differs", "inconclusive")]
    causes = list(dict.fromkeys(CAUSE_WORDS[i] for i in miss if i in CAUSE_WORDS))
    verdict = ("holds" if exact else "holds in direction, not in the printed digits") if up else "does not hold"
    line = (f"The main claim {verdict}: in our run adding biological and phenotypic features to chemical structures raises AUC "
            f"from {a['auc']:.4f} to {b['auc']:.4f}, precision from {100 * a['precision']:.2f}% to {100 * b['precision']:.2f}% and recall "
            f"from {100 * a['recall']:.2f}% to {100 * b['recall']:.2f}% (paper 0.9054 to 0.9524, 43.37% to 66.17%, 49.25% to 63.06%).")
    if causes:
        line += " The claims that do not match come from " + (", ".join(causes[:-1]) + " and " + causes[-1] if len(causes) > 1 else causes[0]) + "."
    return line


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


def main(results, run, pub, out):
    R = json.loads(Path(results).read_text())
    run, pub = Path(run), Path(pub)
    sm = R["summary"]
    items = R["items"]
    by = {i["id"]: i for i in items}
    M = json.loads((run / "metrics.json").read_text())

    # ---- hero and label
    lede = (f"The authors' pipeline was never released. We rebuilt it from the paper and reran it on their own training "
            f"file: 832 drugs, 1,385 ADRs and their folds. Of {sm['items']} results, {sm['exact']} came back exact, "
            f"{sm['agrees']} agree, {sm['partly']} partly, {sm['differs']} differ and {sm['not_attempted']} were not attempted.")
    rows = [("fig-2", "Fig. 2", ["fig2", "fig2.values"]), ("fig-3", "Fig. 3", ["fig3", "fig3.values"]),
            ("fig-4", "Fig. 4", ["fig4", "fig4.values"]), ("table1", "Table 1", ["table1"]),
            ("table2", "Table 2", ["table2.all", "table2.50"]), ("table3", "Table 3", [i for i in by if i.startswith("table3.")]),
            ("table4", "Table 4", ["table4"]), ("fig5", "Fig. 5", ["fig5"]), ("tableS1", "Table S1", ["tableS1"])]

    def label_row(anchor, name, ids):
        cls, word = STAMP.get(worst([by[i]["verdict"] for i in ids]), ("running", "Not attempted"))
        return f'<li><a href="#{anchor}"><span>{esc(name)}</span><span class="v" data-v="{cls}">{esc(word)}</span></a></li>'
    label = "<ol>" + "".join(label_row(*r) for r in rows) + "</ol>"

    # ---- figure stations
    stations, figjs = [], []
    for n in ("2", "3", "4"):
        its = [by[f"fig{n}"], by[f"fig{n}.values"]]
        v = worst([i["verdict"] for i in its])
        psrc, (w, h) = b64(pub / f"fig{n}.png", 0.5)
        osrc, _ = b64(run / f"fig{n}_ours.png", 0.5)
        stats = "".join(f"<div><dt>{esc(i['label'])}</dt><dd>{esc(measure(i))}, {esc(STAMP[i['verdict']][1])}</dd></div>" for i in its)
        note = (its[0].get("cause") or {}).get("summary", "") or "Every curve overlays the published one."
        stations.append(
            f'<section class="station surface" id="fig-{n}" aria-labelledby="fig-{n}-head">'
            f'<header class="station-head"><h2 id="fig-{n}-head">Fig. {n}</h2><p class="caption">{esc(CAPTIONS[n])}</p>{stamp(v)}</header>'
            f'<div class="stage"><div class="pair">'
            f'<figure class="plate"><figcaption>Published</figcaption><img src="{psrc}" alt="Figure {n} as published" width="{w}" height="{h}"></figure>'
            f'<figure class="plate"><figcaption>Our run</figcaption><img src="{osrc}" alt="Figure {n} drawn from our run" width="{w}" height="{h}"></figure>'
            f'</div></div><div class="station-foot"><dl class="dose">{stats}</dl><p class="note">{esc(note)}</p></div></section>')
        figjs.append({"id": n, "w": w, "h": h, "paper": psrc, "ours": osrc})

    # ---- tables
    metric_cols = [f"{p} {m}" for p in ("All", "50+") for m in ("AUC", "ACC", "Prec.", "Recall")]
    mname = {"auc": "AUC", "acc": "ACC", "precision": "Prec.", "recall": "Recall"}
    pname = {"all": "All", "50+": "50+"}
    rowf = lambda f: f["name"].split("|")[0]  # noqa: E731
    colf = lambda f: f"{pname[f['name'].split('|')[1]]} {mname[f['name'].split('|')[2]]}"  # noqa: E731
    t3 = [by[i] for i in ("table3.lr", "table3.nb", "table3.knn", "table3.rf", "table3.svm")]
    t4 = by["table4"]
    t4cols = ["chem", "chem+bio", "chem+bio+pheno"]
    grids = [
        table_station("table1", by["table1"]["label"], [by["table1"]],
                      grid([by["table1"]], lambda f: f["name"], lambda f: "Dimension", ["Dimension"], "Table 1"), "Feature dimensions of the recovered training file."),
        table_station("table2", "Table 2, the SVM by feature set", [by["table2.all"], by["table2.50"]],
                      grid([by["table2.all"], by["table2.50"]], rowf, colf, metric_cols, "Table 2"),
                      "Micro-averaged over all ADRs and over ADR_50+."),
        table_station("table3", "Table 3, five algorithms on the full feature set", t3, grid(t3, rowf, colf, metric_cols, "Table 3"),
                      "Micro-averaged over all ADRs and over ADR_50+."),
        table_station("table4", t4["label"], [t4],
                      grid([t4], lambda f: " ".join(f["name"].split("|")[:2]), lambda f: f["name"].split("|")[2], t4cols, "Table 4"),
                      "Yes or No: is the withdrawn drug predicted to have the ADR, with every other drug as the training set."),
        table_station("fig5", by["fig5"]["label"], [by["fig5"]],
                      grid([by["fig5"]], lambda f: f["name"], lambda f: "True positives", ["True positives"], "Fig. 5"),
                      "Regions of the Venn diagram of Fig. 5."),
        table_station("tableS1", by["tableS1"]["label"], [by["tableS1"]],
                      grid([by["tableS1"]], lambda f: f["name"], lambda f: "%", ["%"], "Table S1"),
                      "Share of all informative (feature, ADR) pairs, by feature block."),
    ]
    tables = (f'<section class="container after-bench" aria-labelledby="tables-head" id="tables"><h2 id="tables-head">The tables</h2>'
              f'<div class="cellgrid">{"".join(grids)}</div></section>')

    trs = []
    for i in items:
        fields = ""
        if i["method"] == "values" and len(i["values"]["fields"]) <= 8:
            fields = "<ul class=fields>" + "".join(
                f"<li>{esc(f['name'])}: paper {esc(fmt(f['expected']))}, ours <strong>{esc(fmt(f['observed'], f['expected']))}</strong></li>"
                for f in i["values"]["fields"]) + "</ul>"
        trs.append(f"<tr><td>{esc(i['label'])}</td><td>{stamp(i['verdict'])}</td><td>{esc(measure(i))}{fields}</td>"
                   f"<td>{esc((i.get('cause') or {}).get('summary', ''))}</td></tr>")

    claims_line = main_claim_line(M, R)
    extra = (tables + f'<section class="container after-bench" aria-labelledby="items-head"><div class="station surface" id="items">'
             f'<header class="station-head"><h2 id="items-head">Every result</h2><p class="caption">Each figure, table and claim of the paper, '
             f'with the verdict results.json computes from the numbers.</p></header>'
             f'<div class="table-wrap"><table class="record dense"><thead><tr><th scope="col">Result</th><th scope="col">Verdict</th>'
             f'<th scope="col">Measure</th><th scope="col">Why</th></tr></thead><tbody>{"".join(trs)}</tbody></table></div>'
             f'<p class="note">{esc(claims_line)}</p></div></section>')

    good = [i for i in items if i["verdict"] in ("exact", "agrees")]
    bad = [i for i in items if i["verdict"] in ("partly", "differs", "inconclusive")]
    recovered = ('<section class="notes" aria-labelledby="back-head"><div class="container"><h2 id="back-head">What came back</h2><dl class="ledger">'
                 + "".join(f'<div class="row"><dt>{esc(i["label"])}</dt><dd>{esc(measure(i))}</dd></div>' for i in good)
                 + '</dl></div></section><section class="buried" aria-labelledby="buried-head"><div class="container"><div class="plastic buried-band">'
                 '<h2 id="buried-head">What stayed buried</h2><ul>'
                 + "".join(f"<li>{esc(i['label'])}: {esc(measure(i))}.</li>" for i in bad)
                 + f'</ul><p class="so">{esc(claims_line)}</p></div></div></section>')
    matched = "".join(f'<div class="row"><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>' for k, v in (
        ("Data", "The authors' training file, from Zhang et al. 2015's supplement (CC BY 4.0): 832 drugs, every feature bit and the fold of each drug for each ADR."),
        ("Method", "adrfusion, rebuilt from the paper's Methods: one classifier per ADR, LIBSVM's RBF kernel with g 0.008 and C 2, micro-averaged ROC."),
        ("Figures", "The published ROC curves read from the PDF's vector paths, our curves drawn on the published frames at 600 dpi."),
    ))

    page = (HERE / "page_template.html").read_text()
    page = page.replace('<link rel="stylesheet" href="../results.css">', '<link rel="stylesheet" href="../results.css">\n' + STYLE)
    for k, v in {"LEDE": esc(lede), "LABEL": label, "STATIONS": "".join(stations), "EXTRA": extra,
                 "RECOVERED": recovered, "MATCHED_INTRO": esc("What the reproduction stands on."), "MATCHED": matched,
                 "CLOSING": esc("Fig. 2 came back the same.")}.items():
        page = page.replace(f"<!--__{k}__-->", v)
    page = page.replace("/*__FIGS__*/[]", json.dumps(figjs))
    page = with_install_block(page)
    outp = Path(out) / "index.html"
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(page)
    print(f"wrote {outp} ({len(page) // 1024} KB)", file=sys.stderr)


if __name__ == "__main__":
    main(*sys.argv[1:5])
