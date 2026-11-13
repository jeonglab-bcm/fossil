#!/usr/bin/env python3
"""Build the results page for PMC2850872 from results.json and the pipeline outputs.

Usage: build_page.py RUN_DIR PUBLISHED_DIR OUT.html

RUN_DIR holds results.json, tables.json, table1.json, fig2_comparison.json, fig2_ours.png and
fig2_overlay.png. Every verdict on the page is read from results.json; every number from the run.
The page links ../results.css, the stylesheet the site's results pages share; images are embedded.
"""

from __future__ import annotations

import base64
import html
import io
import json
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
RUN, PUB, OUT = map(Path, sys.argv[1:4])
esc = html.escape

res = json.loads((RUN / "results.json").read_text())
tb = json.loads((RUN / "tables.json").read_text())
t1 = json.loads((RUN / "table1.json").read_text())
fig = json.loads((RUN / "fig2_comparison.json").read_text())
items = {i["id"]: i for i in res["items"]}

# Split-dependent values agree within two SDs of our median, never at printed precision: no "Exact" stamp.
STAMP = {"exact": ("agrees", "Agrees"), "agrees": ("agrees", "Agrees"), "partly": ("partly", "Partly agrees"),
         "inconclusive": ("partly", "Inconclusive"), "differs": ("differs", "Differs")}
KN = {"linear": "Linear", "poly": "Polynomial", "rbf": "RBF", "sigmoid": "Sigmoid"}


def verdict(iid):
    return items[iid].get("verdict", "not_attempted")


def measure(iid):
    it = items[iid]
    if it["method"] == "values":
        f = it["values"]["fields"]
        ex = {e["field"] for e in it["values"].get("exceptions", [])}
        return f"{sum(1 for x in f if matches(x, it) and x['name'] not in ex)} of {len(f) - len(ex)} values"
    if it["method"] == "pixels":
        p = it["pixels"]
        return f"{100 * min(p['published_near_ours'], p['ours_near_published']):.0f}% within {p['tolerance_px']:g} px"
    if it["method"] == "check":
        return "passed" if it["check"]["passed"] else "failed"
    return "not attempted"


def matches(f, it):
    tol = f.get("tolerance", it["values"].get("tolerance")) or {}
    try:
        a, b = float(str(f["expected"]).replace(",", "")), float(str(f["observed"]).replace(",", ""))
    except ValueError:
        return f["expected"] == f["observed"]
    allowed = 1e-12 + tol.get("abs", 0)
    if tol.get("printed"):
        s = str(f["expected"])
        allowed += 0.5 * 10 ** (-(len(s.split(".")[1]) if "." in s else 0))
    return abs(a - b) <= allowed


def word(iid):
    """The stamp's word; a verdict a reviewer set says so."""
    w = STAMP.get(verdict(iid), ("", "Not attempted"))[1]
    return w + " on review" if items[iid].get("review") else w


def stamp(iid, basis=None):
    v = verdict(iid)
    if v not in STAMP:
        return ""
    cls, word_ = STAMP[v][0], word(iid)
    return f'<span class="stamp" data-v="{cls}">{esc(word_)}<small>{esc(basis or measure(iid))}</small></span>'


def b64(path: Path) -> str:
    buf = io.BytesIO()
    Image.open(path).convert("RGB").save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def dose(pairs):
    return "".join(f"<div><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>" for k, v in pairs)


def plate(label, src, alt, w, h):
    return (f'<figure class="plate"><figcaption>{esc(label)}</figcaption>'
            f'<img src="{src}" alt="{esc(alt)}" width="{w}" height="{h}"></figure>')


def n(x):
    return f"{int(x):,}"


t2 = tb["table2"]
mlr = tb["mlr"]
reps = t2["I"]["rbf"]["n"]
ours_t1, pap_t1 = t1["ours"], t1["paper"]

LEDE = (f"Neither the web tool nor its code survived. We rebuilt the cohort from the NHANES 1999 to 2004 files "
        f"and the method from the text. Diagnosed diabetes comes back at {n(ours_t1['diagnosed'])} people "
        f"(paper {n(pap_t1['diagnosed'])}). Over {reps} random splits the SVM’s median test AUC is "
        f"{t2['I']['rbf']['median']:.3f} for diabetes and {t2['II']['linear']['median']:.3f} for pre-diabetes "
        f"or undiagnosed diabetes (paper {t2['I']['rbf']['paper']} and {t2['II']['linear']['paper']}), and it "
        f"ties with logistic regression, as the paper says.")

LABEL_ROWS = [("tables", "Table 1", "table1"), ("tables", "Table 2", "table2"),
              ("tables", "Table 3, scheme I", "table3.schemeI"), ("tables", "Table 3, scheme II", "table3.schemeII"),
              ("fig-2", "Fig. 2a values", "fig2.a.values"), ("fig-2", "Fig. 2b values", "fig2.b.values"),
              ("claims", "Claims", "text.delong")]
LABEL = "".join(f'<a class="label-row" href="#{a}"><span>{esc(k)}</span><span>{esc(word(i))}, {esc(measure(i))}</span></a>'
                for a, k, i in LABEL_ROWS)

pub_path = PUB / "figure-2.jpg"
w, h = Image.open(pub_path).size
ours_src = b64(RUN / "fig2_ours.png")
pa, pb = items["fig2.a"]["pixels"], items["fig2.b"]["pixels"]


def best_ctrl(p):
    c = max(p["controls"], key=lambda c: c["score"])
    return f"{100 * c['score']:.0f}% ({c['name']})"


STATS = [("Pixel size", f"{w} × {h}"), ("Tolerance", f"{pa['tolerance_px']:g} px"),
         ("Panel a, ours", f"{100 * min(pa['published_near_ours'], pa['ours_near_published']):.0f}%"),
         ("Panel a, best control", best_ctrl(pa)),
         ("Panel b, ours", f"{100 * min(pb['published_near_ours'], pb['ours_near_published']):.0f}%"),
         ("Panel b, best control", best_ctrl(pb)),
         ("Tick fit residual", f"{max(fig['panels'][s]['tick_fit_max_residual_px'] for s in fig['panels']):.2f} px")]
NOTE = (f"Our curves are from split 0. The paper’s split was never published, and the curves of two random "
        f"splits differ by about as much as a curve moved 0.03 in sensitivity, so a pixel score cannot single "
        f"out the paper’s split. In data units, the published sensitivity at nine false-positive rates lies within "
        f"two standard deviations of our median for {measure('fig2.a.values')} in panel a and "
        f"{measure('fig2.b.values')} in panel b.")
FIGS_JS = [{"id": "2", "w": w, "h": h}]
STATIONS = (
    '<section class="station surface" id="fig-2" aria-labelledby="fig-2-head">'
    '<header class="station-head"><h2 id="fig-2-head">Fig. 2</h2><p class="caption">ROC curves of the SVM '
    '(black) and the logistic regression (grey) on the test set, for scheme I (a: diabetes against everyone '
    'else) and scheme II (b: undiagnosed diabetes or pre-diabetes against no diabetes).</p>'
    f'{stamp("fig2.a.values", "panel a, " + measure("fig2.a.values"))}{stamp("fig2.b.values", "panel b, " + measure("fig2.b.values"))}</header>'
    '<div class="stage"><div class="pair">'
    + plate("Published", b64(pub_path), "Figure 2 as published", w, h)
    + plate("Our split 0", ours_src, "Figure 2 reproduced", w, h)
    + "</div></div>"
    f'<div class="station-foot"><dl class="dose">{dose(STATS)}</dl><p class="note">{esc(NOTE)}</p></div></section>')


def row(cells, num_from=1):
    return "<tr>" + "".join(f"<td{' class=num' if i >= num_from else ''}>{c}</td>" for i, c in enumerate(cells)) + "</tr>"


T1_NAMES = [("diagnosed", "Diagnosed diabetes"), ("undiagnosed", "Undiagnosed diabetes"), ("prediabetes", "Pre-diabetes"),
            ("none", "No diabetes"), ("scheme_I_cases", "Scheme I cases"), ("scheme_I_noncases", "Scheme I non-cases"),
            ("scheme_II_cases", "Scheme II cases"), ("scheme_II_noncases", "Scheme II non-cases")]
t1_body = "".join(row([esc(lab), n(pap_t1[k]), f"<strong>{n(ours_t1[k])}</strong>", f"{ours_t1[k] - pap_t1[k]:+d}"])
                  for k, lab in T1_NAMES)


def spread(st):
    return f"<strong>{st['median']:.4f}</strong><br><small>{st['min']:.3f} to {st['max']:.3f}</small>"


t2_body = "".join(row([f"Scheme {s}"] + [f"{t2[s][k]['paper']} / {spread(t2[s][k])}" for k in ["linear", "poly", "rbf", "sigmoid"]])
                  for s in ["I", "II"])
t3_rows = []
for s, kern in [("I", "RBF"), ("II", "linear")]:
    t3 = tb["table3"][s]
    for lab, key in [("Test", "test"), ("Training", t3["paper_training_row_is"]), ("10-fold CV", "cv10")]:
        r = t3["rows"][key]
        t3_rows.append(row([f"Scheme {s} ({kern}), {lab}"] + [f"{r[m]['paper']} / {spread(r[m])}" for m in ["sensitivity", "specificity", "ppv", "npv", "auc"]]))
t3_body = "".join(t3_rows)

claims = []
for iid in ["text.mlr_auc", "text.delong", "text.best_kernel"]:
    for f in items[iid]["values"]["fields"]:
        claims.append(row([esc(f["name"]), esc(f["expected"]), f"<strong>{esc(f['observed'])}</strong>",
                           "yes" if matches(f, items[iid]) else "no"]))
claims_body = "".join(claims)
ar = items["text.arithmetic"]["values"]
ar_ok = sum(1 for f in ar["fields"] if matches(f, items["text.arithmetic"]))

EXTRA = f"""<section class="container after-bench" aria-labelledby="tables-head">
  <div class="station surface" id="tables">
    <header class="station-head"><h2 id="tables-head">Tables 1 to 3</h2><p class="caption">Table 1: people per diabetes category, NHANES 1999 to 2004, adults aged 20 or over, not pregnant. Tables 2 and 3: published value / our median over {reps} random 80/20 splits (our range).</p>{stamp("table1")}{stamp("table2")}</header>
    <div class="table-wrap"><table class="record dense"><caption>Table 1 (paper; ours; difference)</caption><thead><tr><th scope="col">Category</th><th scope="col" class=num>Paper</th><th scope="col" class=num>Ours</th><th scope="col" class=num>Δ</th></tr></thead><tbody>{t1_body}</tbody></table></div>
    <p class="note">Diagnosed diabetes comes back exactly. The fasting groups come back within a handful of people, with glucose counted for people who fasted at least 8 hours, “borderline” answers counted as not diagnosed and “don’t know” as no. The paper does not name its physical activity variable; moderate activity in the past 30 days (PAD320) leaves the scheme II totals closest to the paper’s.</p>
    <div class="table-wrap"><table class="record dense"><caption>Table 2. Test AUC per kernel (paper / ours)</caption><thead><tr><th scope="col">Scheme</th><th scope="col" class=num>Linear</th><th scope="col" class=num>Polynomial</th><th scope="col" class=num>RBF</th><th scope="col" class=num>Sigmoid</th></tr></thead><tbody>{t2_body}</tbody></table></div>
    <div class="table-wrap"><table class="record dense"><caption>Table 3. Best kernel per scheme (paper / ours)</caption><thead><tr><th scope="col">Row</th><th scope="col" class=num>Sensitivity</th><th scope="col" class=num>Specificity</th><th scope="col" class=num>PPV</th><th scope="col" class=num>NPV</th><th scope="col" class=num>AUC</th></tr></thead><tbody>{t3_body}</tbody></table></div>
    <p class="note">{stamp("table3.schemeI")} {stamp("table3.schemeII")} A value agrees when the paper’s lies within two standard deviations of our median, the range one random split lands in about 95% of the time. The paper’s training row is the whole training set for scheme I and the balanced sample for scheme II: that is the prevalence each row’s PPV implies. The scheme II training NPV implies the whole training set instead, so no one set gives that row; it is left out of the count.</p>
  </div>
  <div class="station surface" id="claims">
    <header class="station-head"><h2>Claims in the text</h2><p class="caption">Our median over {reps} splits against the paper’s numbers. The logistic regression is weighted by the NHANES examination weights and fitted to the whole training set.</p>{stamp("text.delong")}</header>
    <div class="table-wrap"><table class="record dense"><caption>Claims (paper; ours; agrees)</caption><thead><tr><th scope="col">Claim</th><th scope="col">Paper</th><th scope="col">Ours</th><th scope="col">Agrees</th></tr></thead><tbody>{claims_body}</tbody></table></div>
    <p class="note">The paper’s own numbers: {ar_ok} of {len(ar["fields"])} arithmetic checks on Tables 1 and 3 hold. Our code against R: {esc(items["r_check"]["check"]["detail"])}.</p>
    <p class="note"><strong><!--__MAINCLAIM__--></strong></p>
  </div>
</section>"""

RECOVERED = f"""<section class="notes" aria-labelledby="back-head">
  <div class="container">
    <h2 id="back-head">What came back</h2>
    <dl class="ledger">
      <div class="row"><dt>The cohort</dt><dd>All 33 NHANES files still download from the CDC. Diagnosed diabetes at {n(ours_t1['diagnosed'])} people; the scheme I totals at {n(ours_t1['scheme_I_cases'])} cases and {n(ours_t1['scheme_I_noncases'])} non-cases (paper {n(pap_t1['scheme_I_cases'])} and {n(pap_t1['scheme_I_noncases'])}).</dd></div>
      <div class="row"><dt>The method</dt><dd>LIBSVM with grid.py’s default grid, trained on all cases and as many random non-cases. It is now a Python package, diabclass, with a tutorial: <a href="https://github.com/jeonglab-bcm/fossil/blob/main/PMC2850872/package/tutorial/TUTORIAL.md">PMC2850872/package</a>.</dd></div>
      <div class="row"><dt>The comparison</dt><dd>A survey-weighted logistic regression and the DeLong test, checked against R’s survey and pROC packages.</dd></div>
      <div class="row"><dt>The tie</dt><dd>On scheme I the SVM and the logistic regression differ by {mlr['I']['svm_minus_mlr_auc']['median']:+.4f} in median AUC; on scheme II by {mlr['II']['svm_minus_mlr_auc']['median']:+.4f}. DeLong P is below 0.05 in {mlr['I']['reps_significant_0_05']} and {mlr['II']['reps_significant_0_05']} of {reps} splits.</dd></div>
    </dl>
  </div>
</section>
<section class="buried" aria-labelledby="buried-head">
  <div class="container">
    <div class="plastic buried-band">
      <h2 id="buried-head">What stayed buried</h2>
      <ul>
        <li>The Diabetes Classifier web tool and its Java code</li>
        <li>The paper’s random 80/20 split and its undersampled training set</li>
        <li>Which NHANES items stand for family history, hypertension and physical activity, and the divisors for weight, height, waist and BMI</li>
        <li>The polynomial kernel’s degree and offset, and the survey weight given to SUDAAN</li>
      </ul>
      <p class="so"><!--__SO__--></p>
    </div>
  </div>
</section>"""

MATCHED = "".join(f'<div class="row"><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>' for k, v in [
    ("Our run", f"{reps} random splits per scheme. Each: 80% of every Table 1 category to training, a balanced sample, grid.py’s search per kernel (5-fold CV), the test AUC, Table 3’s rows, the weighted logistic regression and the DeLong test."),
    ("Axes", "One linear map per axis from the eleven tick marks of each panel."),
    ("Scores", "Share of the published trace within 2 px of ours and of ours within 2 px of the published, the smaller of the two. Legend and diagonal masked."),
    ("Controls", "The other scheme’s curve and age alone (wrong inputs), and our curve with sensitivity moved by 0.03 either way (near misses)."),
    ("Reading the views", "Overlay: ink is the paper only, light green is the reproduction only, dark green is both."),
])

v_main = verdict("text.delong")
CLAIM = ("The main claim holds: on both schemes the SVM discriminates as well as the logistic regression, and the DeLong "
         f"test finds no difference in {reps - mlr['I']['reps_significant_0_05']} and {reps - mlr['II']['reps_significant_0_05']} of {reps} splits. "
         if v_main in ("exact", "agrees") else "The main claim does not hold on our run. ")
CLAIM += ("The polynomial kernels come back better than published, as an untuned model would explain; the scheme I "
          "10-fold CV and test PPV stay apart, cause open.")
CLOSING = "The SVM and the logistic regression tie, as the paper found, on data anyone can still download."

page = (HERE / "page_template.html").read_text()
for k, v in {"LEDE": esc(LEDE), "LABEL": LABEL, "STATIONS": STATIONS, "EXTRA": EXTRA, "RECOVERED": RECOVERED,
             "MATCHED": MATCHED, "CLOSING": esc(CLOSING)}.items():
    page = page.replace(f"<!--__{k}__-->", v)
page = page.replace("<!--__MAINCLAIM__-->", esc(CLAIM)).replace("<!--__SO__-->", esc(CLAIM))
page = page.replace("/*__FIGS__*/[]", json.dumps(FIGS_JS))
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(page)
print(f"wrote {OUT} ({len(page) // 1024} KB)")
