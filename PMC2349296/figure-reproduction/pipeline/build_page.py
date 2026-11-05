#!/usr/bin/env python3
"""Build the comparison page for PMC2349296 from the pipeline outputs.

Usage: build_page.py RESULTS_TABLE.csv CLAIMS.csv CLAIMS_VERDICTS.csv CLAIMS_BY_CORPUS.csv FIGS_DIR COMPARE_DIR CORPUS_COUNTS.csv PUBLISHED_DIR OUT.html
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
TABLE, CLAIMS, VERDICTS, BY_CORPUS, FIGS, CMP, COUNTS, PUB, OUT = map(Path, sys.argv[1:10])
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


verdicts = read(VERDICTS)
by_corpus = read(BY_CORPUS)
tally = {v: sum(r["verdict"] == v for r in verdicts) for v in ("holds", "close", "differs")}
CLAIMS_BASIS = f"{tally['holds']} of {len(verdicts)} hold, {tally['close']} close, {tally['differs']} differ"


def minus(t):
    return t.replace("-", "−")


claim_body = "".join(
    f"<tr><td>{esc(r['claim'])}</td><td class=num>{esc(r['paper'])}</td>"
    f"<td class=num><strong>{esc(minus(r['ours']))}</strong></td><td>{esc(r['verdict'])}</td>"
    f"<td class=num>{esc(minus(r['published_tables']))}</td><td class=num>{esc(minus(r['ours_with_published_BioInfer']))}</td></tr>"
    for r in verdicts)


def pct(x):
    return minus(f"{float(x):.1f}%")


def lowest(col):
    return min(by_corpus, key=lambda r: float(r[col]))


lo_ours, lo_hyb = lowest("error_reduction_pct_ours"), lowest("error_reduction_pct_with_published_BioInfer")
corpus_body = "".join(
    f"<tr><td>{r['corpus']}</td><td>{esc(r['corpus_version']).replace('&#x27;', '’')}</td>"
    f"<td class=num>{pct(r['error_reduction_pct_published'])}</td>"
    f"<td class=num><strong>{pct(r['error_reduction_pct_ours'])}</strong></td>"
    f"<td class=num>{float(r['relex_F_published']):.2f}</td><td class=num><strong>{float(r['relex_F_ours']):.2f}</strong></td></tr>"
    for r in by_corpus)
iepa = next(r for r in by_corpus if r["corpus"] == lo_hyb["corpus"])
V = {r["claim_id"]: r for r in verdicts}

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
    <p class="note">Co-occurrence and the corpus statistics are arithmetic on the annotation, so where the corpus is the paper’s they come back exactly. AIMed’s surviving copy lacks 12 sentences and its self-interactions (about 5% of AIMed’s interactions in the paper), so its co-occurrence recall is 1.00, not 0.95. RelEx was never released; ours is rebuilt from the two papers’ descriptions. Its F is within {100 * max_gap('T2', 'relex_F', MATCHING):.0f} points of the paper’s on the three matching corpora, but it matches {agree('T2', 'relex', MATCHING)} of their RelEx cells.</p>
  </div>
  <div class="station surface" id="claims">
    <header class="station-head"><h2>The claims in the text</h2><p class="caption">The paper’s summary numbers. <b>Ours</b> is our run: it is the reproduction, and the verdict reads only that column. <b>Paper’s tables</b> runs the same code on the paper’s own Tables 2 and 4; it returns the paper’s text, which shows we compute each number the way the paper did, not that our run agrees. <b>Paper’s BioInfer row</b> is our run with BioInfer’s numbers replaced by the paper’s: it shows how much BioInfer matters, and moves toward the paper by construction.</p>{stamp("Partly agrees", CLAIMS_BASIS)}</header>
    <div class="table-wrap"><table class="record dense"><thead><tr><th scope="col">Claim</th><th scope="col" class=num>Paper</th><th scope="col" class=num>Ours</th><th scope="col">Verdict</th><th scope="col" class=num>Paper’s tables</th><th scope="col" class=num>Paper’s BioInfer row</th></tr></thead><tbody>{claim_body}</tbody></table></div>
    <p class="note">A yes/no claim holds if it is true in our run, and “not significant” holds if p ≥ 0.05. A number holds if it rounds to the paper’s value, is close if within 10% of it, and differs otherwise.</p>
    <div class="table-wrap"><table class="record dense"><caption>Per corpus: relative cut in F error from co-occurrence to RelEx, and RelEx F</caption><thead><tr><th scope="col">Corpus</th><th scope="col">Our copy of the corpus</th><th scope="col" class=num>Error cut, paper’s tables</th><th scope="col" class=num>Ours</th><th scope="col" class=num>RelEx F, paper</th><th scope="col" class=num>Ours</th></tr></thead><tbody>{corpus_body}</tbody></table></div>
    <p class="note">The main claim holds: in our run RelEx’s F varies by {cnum('relex_pairwise_pts', 'ours')} points between corpora, more than the {cnum('method_gap_pts', 'ours')}-point gap between the methods. The numbers that differ have two causes. BioInfer’s surviving copy is a later conversion, and it sets our smallest error cut ({pct(lo_ours['error_reduction_pct_ours'])}, {lo_ours['corpus']}). Our rebuild of RelEx is the other cause: on HPRD50, IEPA and LLL, whose corpora are the paper’s, it matches {agree('T2', 'relex', MATCHING)} of the paper’s RelEx cells in Table 2. On {iepa['corpus']}, co-occurrence F is the paper’s {float(iepa['cooc_F_published']):.2f}, but RelEx F is {float(iepa['relex_F_ours']):.2f} against {float(iepa['relex_F_published']):.2f}. So even with the paper’s BioInfer row the smallest error cut is {pct(lo_hyb['error_reduction_pct_with_published_BioInfer'])} ({lo_hyb['corpus']}) against 21%, and the gap between the methods is {cnum('method_gap_pts', 'ours_with_published_BioInfer')} points against 13. With the paper’s BioInfer row, the filtered difference ({V['relex_pairwise_filtered_pts']['ours_with_published_BioInfer']}) and the Kendall p ({V['kendall_IEP_p']['ours_with_published_BioInfer']}) come near the paper’s, but that column takes one corpus from the paper; our run gives {V['relex_pairwise_filtered_pts']['ours']} and {V['kendall_IEP_p']['ours']}.</p>
    <p class="note"><strong>Result:</strong> the main finding of the paper holds. Some summary values do not agree. Two causes explain these differences: the only surviving copy of BioInfer is a later conversion, and RelEx, which the authors did not release, had to be rebuilt.</p>
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
      <p class="so">Co-occurrence and the corpus statistics come back exactly where the corpus survives. RelEx, rebuilt, comes back up to {100 * max_gap('T2', 'relex_F', MATCHING):.0f} F points from the paper’s. The main claim holds; {tally['differs']} of the {len(verdicts)} claims in the text differ in our run.</p>
    </div>
  </div>
</section>"""

items = [("fig-1", "Fig. 1", "Partly agrees"), ("fig-2", "Fig. 2", "Partly agrees"),
         ("tables", "Tables 2 to 4", "Partly agrees"), ("claims", "Claims", "Partly agrees")]
LABEL = "<ol>" + "".join(
    f'<li><a href="#{a}"><span>{esc(n)}</span><span class="v" data-v="{VCLASS[v]}">{esc(v)}</span></a></li>'
    for a, n, v in items) + "</ol>"
LEDE = (f"Co-occurrence and the corpus statistics came back exactly where the corpora survive. "
        f"A rebuilt RelEx lands up to {100 * max_gap('T2', 'relex_F', MATCHING):.0f} F points from the paper’s, and the main claim holds.")
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
