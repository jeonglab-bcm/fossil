#!/usr/bin/env python3
"""Build the comparison page for PMC2349296 from the pipeline outputs.

Usage: build_page.py RESULTS_TABLE.csv CLAIMS.csv FIGS_DIR COMPARE_DIR CORPUS_COUNTS.csv PUBLISHED_DIR OUT.html
FIGS_DIR holds ours-figure-{1,2}.png and published-values-figure-{1,2}.png (figures.R);
COMPARE_DIR holds figure-{1,2}-{ours,published-values}/report.json (compare_figures.py).
The page links ../results.css, the stylesheet the site's results pages share; images are embedded.
"""

from __future__ import annotations

import base64
import csv
import html
import json
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
TABLE, CLAIMS, FIGS, CMP, COUNTS, PUB, OUT = map(Path, sys.argv[1:8])
CORPORA = ["AIMed", "BioInfer", "HPRD50", "IEPA", "LLL"]
MATCHING = ["HPRD50", "IEPA", "LLL"]
esc = html.escape
VCLASS = {"Agrees": "agrees", "Partly agrees": "partly", "Differs": "differs"}


def read(p):
    with open(p) as fh:
        return list(csv.DictReader(fh))


rows = read(TABLE)
R = {(r["table"], r["corpus"], r["quantity"]): r for r in rows}
claims = {r["statistic"]: r for r in read(CLAIMS)}
counts = {r["corpus"]: r for r in read(COUNTS)}


def b64(path: Path) -> str:
    img = Image.open(path).convert("RGB")
    import io
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def stamp(verdict, basis):
    return f'<span class="stamp" data-v="{VCLASS[verdict]}">{esc(verdict)}<small>{esc(basis)}</small></span>'


def dose(items):
    return "".join(f"<div><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>" for k, v in items)


def plate(label, src, alt, w, h):
    return (f'<figure class="plate"><figcaption>{esc(label)}</figcaption>'
            f'<img src="{src}" alt="{esc(alt)}" width="{w}" height="{h}"></figure>')


def fig_stats(i, kind):
    rep = json.loads((CMP / f"figure-{i}-{kind}" / "report.json").read_text())
    w, h = rep["size_px"]
    return rep, [("Pixel size", f"{w} × {h}"),
                 ("Mean |Δ| grey", f"{rep['mean_abs_grey_difference']:g}"),
                 ("Pixels within ±24", f"{rep['pixels_within_24_pct']:g}%"),
                 ("Ink distance (chamfer)", f"{rep['chamfer_all_px']:g} px"),
                 ("Best global shift", f"{rep['global_shift']['dx']}, {rep['global_shift']['dy']} px")]


def max_gap(table, quantity, corpora):
    return max(abs(float(R[(table, c, quantity)]["ours"]) - float(R[(table, c, quantity)]["published"]))
               for c in corpora)


CAPTIONS = {
    1: "RelEx and co-occurrence F-scores for the five corpora.",
    2: "RelEx and co-occurrence F-scores on the filtered corpora (only entities that take part in an "
       "interaction kept); the unfiltered results of Fig. 1 in grey.",
}
NOTES = {
    1: ("Co-occurrence matches on AIMed, HPRD50, IEPA and LLL. RelEx, rebuilt, is within "
        f"{100 * max_gap('T2', 'relex_F', ['AIMed', 'HPRD50', 'IEPA', 'LLL']):.0f} F points on those four. "
        "BioInfer’s co-occurrence point sits at 41, not 23: the only surviving copy of BioInfer is a later "
        "conversion with 1.8 times the interactions."),
    2: ("The filtered co-occurrence curve matches on HPRD50, IEPA and LLL and is within 2 points on AIMed. "
        "Filtered RelEx is "
        f"{100 * max_gap('T4', 'relex_F', ['AIMed', 'HPRD50', 'IEPA', 'LLL']):.0f} points or less below the paper on "
        "four corpora; BioInfer differs for the same reason as in Fig. 1."),
}
VARIANT_NOTE = ("Paper’s values: the published Table 2 and 4 F-scores drawn by the same code. "
                "What is left here is drawing, not data.")

figs, stations = [], []
for i in (1, 2):
    pub_path = PUB / f"figure-{i}.jpg"
    pub = Image.open(pub_path)
    w, h = pub.size
    rep_o, st_o = fig_stats(i, "ours")
    rep_p, st_p = fig_stats(i, "published-values")
    ours_src = b64(FIGS / f"ours-figure-{i}.png")
    pv_src = b64(FIGS / f"published-values-figure-{i}.png")
    figs.append({"id": str(i), "w": w, "h": h, "variants": [
        {"label": "Our run", "ours": ours_src, "note": NOTES[i], "stats": dose(st_o)},
        {"label": "Paper’s values", "ours": pv_src, "note": VARIANT_NOTE, "stats": dose(st_p)}]})
    hid = f"fig-{i}-head"
    stations.append(
        f'<section class="station surface" id="fig-{i}" aria-labelledby="{hid}">'
        f'<header class="station-head"><h2 id="{hid}">Fig. {i}</h2><p class="caption">{esc(CAPTIONS[i])}</p>'
        f'{stamp("Partly agrees", "Rerun with a rebuilt RelEx")}</header>'
        '<div class="stage"><div class="pair">'
        + plate("Published", b64(pub_path), f"Figure {i} as published", w, h)
        + plate("Our run", ours_src, f"Figure {i} reproduced", w, h)
        + "</div></div>"
        f'<div class="station-foot"><dl class="dose">{dose(st_o)}</dl><p class="note">{esc(NOTES[i])}</p></div></section>')


def cell(t, c, q, label):
    r = R[(t, c, q)]
    cls = "num" if r["match"] == "1" else "num off"
    mark = "" if r["match"] == "1" else " ≠"
    return (f'<td class="{cls}" data-label="{esc(label)}">{esc(r["published"])} / '
            f'<strong>{esc(r["ours_rounded"])}</strong>{mark}</td>')


def table(t, qs, labels, caption):
    head = "".join(f'<th scope="col" class=num>{esc(l)}</th>' for l in labels)
    body = "".join(
        f"<tr><td>{c}</td>" + "".join(cell(t, c, q, l) for q, l in zip(qs, labels)) + "</tr>" for c in CORPORA)
    return (f'<div class="table-wrap"><table class="record stack"><caption>{esc(caption)}</caption>'
            f'<thead><tr><th scope="col">Corpus</th>{head}</tr></thead><tbody>{body}</tbody></table></div>')


def agree(t, method=None, corpora=CORPORA):
    sel = [r for r in rows if r["table"] == t and r["corpus"] in corpora
           and (method is None or r["quantity"].startswith(method))]
    return f"{sum(r['match'] == '1' for r in sel)} of {len(sel)}"


t2 = table("T2", ["cooc_P", "cooc_R", "cooc_F", "relex_P", "relex_R", "relex_F"],
           ["Co-occ. P", "Co-occ. R", "Co-occ. F", "RelEx P", "RelEx R", "RelEx F"],
           "Table 2. PPI extraction performance (published / ours)")
t3 = table("T3", ["tokens", "entities", "entity_pairs", "interactions", "no_entities", "no_interactions"],
           ["Tokens", "Entities", "Entity pairs", "Interactions", "No entities", "No interactions"],
           "Table 3. Per-sentence averages and fractions of sentences (published / ours)")
t4 = table("T4", ["cooc_P", "cooc_F", "relex_P", "relex_F"], ["Co-occ. P", "Co-occ. F", "RelEx P", "RelEx F"],
           "Table 4. Performance on the filtered corpora (published / ours)")


def cnum(k, col, d=1):
    return f"{float(claims[k][col]):.{d}f}"


CLAIM_ROWS = [
    ("Average F gap between the two methods", "13 points", "method_gap_pts", 1),
    ("Average pairwise RelEx F difference between corpora", "19 points", "relex_pairwise_pts", 1),
    ("… after filtering", "11 points", "relex_pairwise_filtered_pts", 1),
    ("Smallest relative reduction in F error, co-occurrence to RelEx", "21%", "error_reduction_min_pct", 1),
    ("Largest relative reduction in F error", "32%", "error_reduction_max_pct", 1),
    ("Kendall p, I/EP against RelEx F", "≈ 0.08", "kendall_IEP_p", 3),
    ("Kendall p, sentences without interactions against RelEx F", "not significant", "kendall_noint_p", 3),
]
claim_body = "".join(
    f"<tr><td>{esc(lab)}</td><td class=num>{esc(paper)}</td><td class=num>{cnum(k, 'published_tables', d)}</td>"
    f"<td class=num><strong>{cnum(k, 'ours', d)}</strong></td><td class=num>{cnum(k, 'ours_with_published_BioInfer', d)}</td></tr>"
    for lab, paper, k, d in CLAIM_ROWS)
beats = "yes" if claims["cooc_beats_relex_filtered_all_but_LLL"]["ours"].startswith("1") else "no"
claim_body += (f"<tr><td>Co-occurrence beats RelEx on every filtered corpus except LLL</td><td class=num>yes</td>"
               f"<td class=num>yes</td><td class=num><strong>{beats}</strong></td><td class=num>yes</td></tr>")

EXTRA = f"""<section class="container after-bench" aria-labelledby="tables-head">
  <div class="station surface" id="tables">
    <header class="station-head"><h2 id="tables-head">Tables 2 to 4</h2><p class="caption">Each cell is published / ours, rounded as printed; ≠ marks a difference at that precision. HPRD50, IEPA and LLL are the corpora whose surviving copies match the paper’s.</p>{stamp("Partly agrees", "Rerun on the surviving corpora")}</header>
    {t2}
    {t3}
    {t4}
    <div class="table-wrap"><table class="record dense"><thead><tr><th scope="col">Agreement at the printed precision</th><th scope="col" class=num>All five corpora</th><th scope="col" class=num>HPRD50, IEPA, LLL</th></tr></thead><tbody>
      <tr><td>Table 2, co-occurrence</td><td class=num>{agree('T2', 'cooc')}</td><td class=num>{agree('T2', 'cooc', MATCHING)}</td></tr>
      <tr><td>Table 2, RelEx</td><td class=num>{agree('T2', 'relex')}</td><td class=num>{agree('T2', 'relex', MATCHING)}</td></tr>
      <tr><td>Table 3</td><td class=num>{agree('T3')}</td><td class=num>{agree('T3', None, MATCHING)}</td></tr>
      <tr><td>Table 4, co-occurrence</td><td class=num>{agree('T4', 'cooc')}</td><td class=num>{agree('T4', 'cooc', MATCHING)}</td></tr>
      <tr><td>Table 4, RelEx</td><td class=num>{agree('T4', 'relex')}</td><td class=num>{agree('T4', 'relex', MATCHING)}</td></tr>
    </tbody></table></div>
    <p class="note">Co-occurrence and the corpus statistics are arithmetic on the annotation, so where the corpus is the paper’s they come back exactly. AIMed’s surviving copy lacks 12 sentences and its self-interactions (about 5% of AIMed’s interactions in the paper), so its co-occurrence recall is 1.00, not 0.95. RelEx was never released; ours is rebuilt from the two papers’ descriptions and agrees within a few points.</p>
  </div>
  <div class="station surface" id="claims">
    <header class="station-head"><h2>The claims in the text</h2><p class="caption">The paper’s summary numbers, computed by the same code from the published tables, from our run, and from our run with the paper’s BioInfer row in place of ours.</p>{stamp("Partly agrees", "Rerun on the surviving corpora")}</header>
    <div class="table-wrap"><table class="record dense"><thead><tr><th scope="col">Statistic</th><th scope="col" class=num>Paper</th><th scope="col" class=num>From the published tables</th><th scope="col" class=num>Ours</th><th scope="col" class=num>Ours, paper’s BioInfer row</th></tr></thead><tbody>{claim_body}</tbody></table></div>
    <p class="note">The main claim holds: RelEx’s F-score varies by {cnum('relex_pairwise_pts', 'ours')} points on average between corpora in our run, more than the gap between the methods. The other numbers move with BioInfer, whose surviving copy is not the paper’s. With the paper’s BioInfer row, filtering cuts the between-corpus difference from {cnum('relex_pairwise_pts', 'ours_with_published_BioInfer')} to {cnum('relex_pairwise_filtered_pts', 'ours_with_published_BioInfer')} points (paper: 19 to 11) and the Kendall p is {cnum('kendall_IEP_p', 'ours_with_published_BioInfer', 3)}, as in the paper.</p>
  </div>
</section>"""

RECOVERED = f"""<section class="notes" aria-labelledby="back-head">
  <div class="container">
    <h2 id="back-head">What came back</h2>
    <dl class="ledger">
      <div class="row"><dt>The corpora</dt><dd>The unified XML of all five corpora survives only in a third-party GitHub copy (metalrt/ppi-dataset, commit dd49ea3). HPRD50, IEPA and LLL match the paper; AIMed has {counts['AIMed']['sentences']} of 1,955 sentences; BioInfer is the later, improved binarization with {int(counts['BioInfer']['interactions']):,} interactions.</dd></div>
      <div class="row"><dt>The tokenizer</dt><dd>MedPost’s tokens give Table 3’s token counts exactly on all five corpora, so the paper counted MedPost tokens.</dd></div>
      <div class="row"><dt>Stanford Parser 1.5.1</dt><dd>The 2006 release the paper names is still on Stanford’s download server and runs on Java 11. Every sentence parses.</dd></div>
      <div class="row"><dt>RelEx’s relation terms</dt><dd>Fundel et al.’s supplementary list, recovered from a 2014 Wayback capture of their page: 175 stems, which expand to the 1,048 terms their paper reports.</dd></div>
      <div class="row"><dt>RelEx</dt><dd>Rules 1 to 3, enumeration expansion, the negation filter and the term filter, rebuilt in Python on the 1.5.1 dependencies. Developed on HPRD50 only, then run once on all corpora.</dd></div>
      <div class="row"><dt>MedPost on 64-bit</dt><dd>The 2008 source counts its abbreviation table in bytes, not entries, and crashes on x86_64. One line fixes it.</dd></div>
    </dl>
  </div>
</section>
<section class="buried" aria-labelledby="buried-head">
  <div class="container">
    <div class="plastic buried-band">
      <h2 id="buried-head">What stayed buried</h2>
      <ul>
        <li>The paper’s BioInfer conversion (Causal-Change interactions only). The archived download page still links it, but the file itself was never archived</li>
        <li>The conversion programs at mars.cs.utu.fi/PPICorpora</li>
        <li>The authors’ RelEx code, and the details of its chunking and negation list</li>
        <li>The 250 interactions behind Fig. 3 and Table 5, and their manual labels. Fig. 4 is an illustration</li>
      </ul>
      <p class="so">Co-occurrence and the corpus statistics come back exactly where the corpus survives. RelEx comes back within a few points, and so does the main claim.</p>
    </div>
  </div>
</section>"""

items = [("fig-1", "Fig. 1", "Partly agrees"), ("fig-2", "Fig. 2", "Partly agrees"),
         ("tables", "Tables 2 to 4", "Partly agrees"), ("claims", "Claims", "Partly agrees")]
LABEL = "<ol>" + "".join(
    f'<li><a href="#{a}"><span>{esc(n)}</span><span class="v" data-v="{VCLASS[v]}">{esc(v)}</span></a></li>'
    for a, n, v in items) + "</ol>"
LEDE = ("Co-occurrence and the corpus statistics came back exactly where the corpora survive. "
        "A rebuilt RelEx lands within a few points, and the main claim holds.")
CLOSING = "We rebuild this page each time the pipeline runs."

page = (HERE / "page_template.html").read_text()
for marker, text in (("<!--__STATIONS__-->", "\n".join(stations)), ("<!--__EXTRA__-->", EXTRA),
                     ("<!--__RECOVERED__-->", RECOVERED), ("<!--__LABEL__-->", LABEL),
                     ("<!--__LEDE__-->", LEDE), ("<!--__CLOSING__-->", CLOSING),
                     ("/*__FIGS__*/[]", json.dumps(figs))):
    assert marker in page, marker
    page = page.replace(marker, text)
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(page)
print("wrote", OUT, len(page) // 1024, "KB")
