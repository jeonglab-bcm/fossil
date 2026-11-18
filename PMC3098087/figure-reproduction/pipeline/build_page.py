"""Build the results page from results.json, the renders and the published figures.

Usage: build_page.py RESULTS_JSON OUTPUT_DIR PUBLISHED_DIR OUT_DIR   (writes OUT_DIR/index.html)

Every verdict and number on the page is read from results.json (verdicts computed there by
check_results.py); the prose that is not a number comes from results_notes.json ("page"), with
{name} replaced by numbers from results.json. Images are embedded (downscaled to at most 800 px
wide), so the page works offline; it links ../results.css like the site's other results pages.
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
MAXW = 800
STAMP = {"exact": ("agrees", "Exact"), "agrees": ("agrees", "Agrees"), "partly": ("partly", "Partly agrees"),
         "inconclusive": ("partly", "Inconclusive"), "differs": ("differs", "Differs")}
STATIONS = [
    ("fig1", ["fig1"], "Fig. 1. Null case, p = 40, no selection: PA (filled), PA1 and PA2 (open) against k1train; test set as imbalanced as the training set."),
    ("fig2", ["fig2"], "Fig. 2. Null case with selection of 40 variables: PA1 for p = 40, 1000 and 10000; balanced test set."),
    ("fig3", ["fig3"], "Fig. 3. Alternative case, mu2 = 1: PA1 with 20 (left) or all (right) variables differing."),
    ("fig4", ["fig4"], "Fig. 4. Overall PA against the difference mu2, k1train 0.5 to 0.9; samples (left) or variables (right) centred."),
    ("fig5", ["fig5"], "Fig. 5. No correction, over-sampling, down-sizing and MultDS, p = 1000."),
    ("fig6", ["fig6", "fig6.pi"], "Fig. 6. ER status on the Sotiriou data: class-specific PA (%) and 95% prediction intervals; black no correction, red MultDS."),
    ("af4", ["af4"], "Additional file 4. Fig. 3 left for all nine classifiers."),
    ("af5", ["af5"], "Additional file 5. Fig. 3 right for all nine classifiers."),
    ("af6", ["af6"], "Additional file 6. No variable selection (all 1000 variables), Fig. 5 first column, all nine classifiers."),
    ("af7", ["af7"], "Additional file 7. Fig. 4 for all nine classifiers."),
    ("af8", ["af8"], "Additional file 8. Fig. 5 for all nine classifiers (MultDS run for six)."),
    ("af9", ["af9"], "Additional file 9. Over-sampling, then centred variables; balanced test set (odd columns) or as imbalanced as training."),
    ("af10", ["af10"], "Additional file 10. 95% prediction intervals of the overall PA."),
    ("af11", ["af11"], "Additional file 11. RF-THR and PLR-THR."),
    ("af12", ["af12"], "Additional file 12. Fig. 6 for all nine classifiers (intervals compared)."),
]
STYLE = """<style>
table.cells { border-collapse: collapse; font-family: var(--font-outlier); font-size: var(--text-xs); }
table.cells th, table.cells td { padding: 2px 6px; text-align: right; border-top: var(--rule-hair) solid var(--color-rule); white-space: nowrap; }
table.cells th { font-weight: 500; color: var(--color-muted); }
table.cells th[scope=row] { text-align: left; }
table.cells td.off { background: var(--color-paper-3); font-weight: 500; }
table.cells td.slip { background: var(--color-paper-2); }
table.cells td small { color: var(--color-muted); }
.cellgrid { display: grid; gap: var(--space-lg); }
</style>"""


def b64(path):
    im = Image.open(path).convert("RGB")
    if im.width > MAXW:
        im = im.resize((MAXW, round(im.height * MAXW / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
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


def hits(it):
    f = it["values"]["fields"]
    exc = {e["field"] for e in it["values"].get("exceptions", []) if e.get("category") == "paper_error"}
    counted = [x for x in f if x["name"] not in exc]
    return sum(field_matches(x, it["values"].get("tolerance")) for x in counted), len(counted), len(exc)


def measure(it):
    if it["method"] == "values":
        h, n, e = hits(it)
        return f"{h} of {n} values within tolerance" + (f" ({e} paper slip{'s' if e > 1 else ''} left out)" if e else "")
    if it["method"] == "check":
        return it["check"]["detail"]
    return ""


def fmt(v, like=None):
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        if isinstance(like, str):
            try:
                float(like)
                dec = len(like.split(".")[1]) if "." in like else 0
                return f"{v:.{max(dec, 2)}f}"
            except ValueError:
                pass
        return f"{v:.3g}"
    return str(v)


def facts(R):
    sm = R["summary"]
    by = {i["id"]: i for i in R["items"]}
    out = dict(sm)
    out["attempted"] = sm["items"] - sm["not_attempted"]
    for i in R["items"]:
        if i["method"] == "values":
            h, n, e = hits(i)
            key = i["id"].replace(".", "_")
            out[f"{key}_hits"], out[f"{key}_n"], out[f"{key}_slips"] = h, n, e
    return out, by


def fill(obj, F):
    if isinstance(obj, str):
        return re.sub(r"\{([a-z0-9_]+)\}", lambda m: str(F[m.group(1)]), obj)
    if isinstance(obj, list):
        return [fill(x, F) for x in obj]
    if isinstance(obj, dict):
        return {k: fill(v, F) for k, v in obj.items()}
    return obj


def table_grid(it, rowkey, cols):
    """Rows (classifier and setting) by measures: the paper's value over ours; misses shaded."""
    exc = {e["field"] for e in it["values"].get("exceptions", [])}
    rows = {}
    for f in it["values"]["fields"]:
        parts = f["name"].split(" ")
        row, metric = " ".join(parts[:-1]), parts[-1]
        rows.setdefault(row, {})[metric] = f
    head = "".join(f'<th scope="col">{esc(c)}</th>' for c in cols)
    body = []
    for row, cs in rows.items():
        tds = []
        for c in cols:
            f = cs.get(c)
            if not f:
                tds.append("<td></td>")
                continue
            ok = field_matches(f, it["values"].get("tolerance"))
            cls = "" if ok else ("slip" if f["name"] in exc else "off")
            tds.append(f'<td class="{cls}">{esc(str(f["expected"]))}<br><small>{esc(fmt(f["observed"], f["expected"]))}</small></td>')
        body.append(f'<tr><th scope="row">{esc(rowkey(row))}</th>{"".join(tds)}</tr>')
    return (f'<div class="table-wrap"><table class="cells" aria-label="{esc(it["label"])}"><thead><tr><th scope="col">Setting</th>{head}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>')


def main(results, outdir, pubdir, out):
    R = json.loads(Path(results).read_text())
    F, by = facts(R)
    N = fill(json.loads((HERE.parent / "results_notes.json").read_text())["page"], F)
    label = "<ol>" + "".join(
        f'<li><a href="#{a}"><span>{esc(name)}</span><span class="v" data-v="{STAMP.get(worst([by[i]["verdict"] for i in ids]), ("running", ""))[0]}">'
        f'{esc(STAMP.get(worst([by[i]["verdict"] for i in ids]), ("running", "Not attempted"))[1])}</span></a></li>'
        for a, name, ids in N["label_rows"]) + "</ol>"
    stations, figjs = [], []
    for fid, ids, cap in STATIONS:
        its = [by[i] for i in ids if i in by]
        if not its or not (Path(outdir) / f"{fid}_ours.png").exists():
            continue
        v = worst([i["verdict"] for i in its])
        psrc, (w, h) = b64(Path(pubdir) / f"{fid}.png")
        osrc, _ = b64(Path(outdir) / f"{fid}_ours.png")
        stats = "".join(f"<div><dt>{esc(i['label'])}</dt><dd>{esc(measure(i))}, {esc(STAMP[i['verdict']][1])}</dd></div>" for i in its)
        note = " ".join((i.get("cause") or {}).get("summary", "") for i in its).strip()
        stations.append(
            f'<section class="station surface" id="fig-{fid}" aria-labelledby="fig-{fid}-head">'
            f'<header class="station-head"><h2 id="fig-{fid}-head">{esc(cap.split(".")[0] + ("." + cap.split(".")[1] if cap.startswith("Fig") else ""))}</h2><p class="caption">{esc(cap)}</p>{stamp(v)}</header>'
            f'<div class="stage"><div class="pair">'
            f'<figure class="plate"><figcaption>Published</figcaption><img src="{psrc}" alt="{esc(cap.split(".")[0])} as published" width="{w}" height="{h}"></figure>'
            f'<figure class="plate"><figcaption>Our run</figcaption><img src="{osrc}" alt="{esc(cap.split(".")[0])} drawn from our run" width="{w}" height="{h}"></figure>'
            f'</div></div><div class="station-foot"><dl class="dose">{stats}</dl><p class="note">{esc(note)}</p></div></section>')
        figjs.append({"id": fid, "w": w, "h": h})
    grids = []
    cols_sim = ["PA", "PA1", "PA2", "PV1", "PV2", "AUC"]
    cols_er = ["PA", "PA_ER+", "PA_ER-", "PV_ER+", "PV_ER-", "AUC"]
    for tid, cols, rk in (("af1", cols_sim, lambda r: re.sub(r"^(\S+) (\S+) (\S+)$", r"\1, k1 \2, ntest \3", r)),
                          ("af3", cols_sim, lambda r: re.sub(r"^(\S+) (\S+) (\S+)$", r"\1, k1 \2, ntest \3", r)),
                          ("af13", cols_er, lambda r: re.sub(r"^(\S+) (\S+) (\S+)$", r"\1, \2 ER+ / \3 ER-", r)),
                          ("af14", cols_er, lambda r: re.sub(r"^(\S+) (\S+) (\S+)$", r"\1, \2 ER+ / \3 ER-", r))):
        it = by[tid]
        h, n_, e = hits(it)
        grids.append(f'<section class="station surface" id="{tid}" aria-labelledby="{tid}-head"><header class="station-head">'
                     f'<h2 id="{tid}-head">{esc(it["label"].split(":")[0])}</h2><p class="caption">{esc(it["label"])}. Paper above, ours below; '
                     f'dark shading where ours is outside the tolerance, light where the paper printed another classifier\'s value. {h} of {n_} cells within.</p>{stamp(it["verdict"])}</header>'
                     f'{table_grid(it, rk, cols)}<div class="station-foot"><p class="note">{esc((it.get("cause") or {}).get("summary", ""))}</p></div></section>')
    tables = (f'<section class="container after-bench" aria-labelledby="tables-head" id="tables"><h2 id="tables-head">The tables</h2>'
              f'<p class="caption">{esc(N["tables_caption"])}</p><div class="cellgrid">{"".join(grids)}</div></section>')
    rows = []
    for i in R["items"]:
        fields = ""
        if i["method"] == "values" and len(i["values"]["fields"]) <= 20:
            fields = "<ul class=fields>" + "".join(
                f"<li>{esc(f['name'])}: paper {esc(fmt(f['expected']))}"
                + (f", the paper's own values {esc(fmt(f['arithmetic'], f['expected']))}" if f.get("arithmetic") is not None else "")
                + f", ours <strong>{esc(fmt(f['observed'], f['expected']))}</strong></li>"
                for f in i["values"]["fields"]) + "</ul>"
        cause = (i.get("cause") or {}).get("summary", "")
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
    outp.write_text(page)
    print(f"wrote {outp} ({len(page) // 1024} KB)", file=sys.stderr)


if __name__ == "__main__":
    main(*sys.argv[1:5])
