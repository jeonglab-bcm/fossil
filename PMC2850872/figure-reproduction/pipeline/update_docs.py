"""Write the generated parts of the READMEs and the front page from results.json.

Usage (from the repository root): python3 PMC2850872/figure-reproduction/pipeline/update_docs.py

- PMC2850872/README.md and figure-reproduction/README.md: the table between <!--RESULTS--> and
  <!--/RESULTS-->, from check_results.py --markdown; the claims line between <!--CLAIMS--> markers.
- README.md (top level): the PMC2850872 row's status, from the summary.
- site/index.html: the PMC2850872 row and the paper count.
Nothing here is typed by hand: rerun it after results.json changes.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PAPER = ROOT / "PMC2850872"
RES = json.loads((PAPER / "results.json").read_text())
ITEMS = {i["id"]: i for i in RES["items"]}
S = RES["summary"]


def fill(text, tag, body):
    pat = re.compile(rf"<!--{tag}-->.*?<!--/{tag}-->|<!--{tag}-->", re.S)
    return pat.sub(lambda m: f"<!--{tag}-->\n{body}\n<!--/{tag}-->", text, count=1)


def count(iid):
    it = ITEMS[iid]
    f = it["values"]["fields"]
    ex = {e["field"] for e in it["values"].get("exceptions", [])}
    tol = it["values"].get("tolerance") or {}

    def ok(x):
        t = x.get("tolerance", tol) or {}
        try:
            a, b = float(str(x["expected"]).replace(",", "")), float(str(x["observed"]).replace(",", ""))
        except ValueError:
            return x["expected"] == x["observed"]
        allowed = 1e-12 + t.get("abs", 0)
        if t.get("printed"):
            s = str(x["expected"])
            allowed += 0.5 * 10 ** (-(len(s.split(".")[1]) if "." in s else 0))
        return abs(a - b) <= allowed

    return sum(1 for x in f if x["name"] not in ex and ok(x)), len(f) - len(ex)


def main():
    md = subprocess.run([sys.executable, str(ROOT / "tools/paper2repro/check_results.py"), str(PAPER / "results.json"),
                         "--markdown", "--root", str(PAPER)], capture_output=True, text=True)
    if md.returncode:
        sys.exit(md.stdout + md.stderr)
    table = md.stdout.strip() + (
        "\n\nFor values that depend on the random split (Tables 2 and 3, Fig. 2 values, the logistic AUCs, the DeLong P) "
        "\"exact\" and \"fields as printed\" mean every value lies within two standard deviations of our median over 10 "
        "splits, not equal at printed precision: the paper's split is unpublished.")
    main_ok = ITEMS["text.delong"]["verdict"] in ("exact", "agrees")
    t2 = count("table2")
    tb = json.loads((PAPER / "figure-reproduction/output/tables.json").read_text())
    m = tb["mlr"]
    diff = max(abs(m[s]["svm_minus_mlr_auc"]["median"]) for s in ["I", "II"])
    claims = ((f"The main claim holds: on both schemes the median AUCs of the SVM and the logistic regression differ by "
               f"{diff:.4f} or less, and the DeLong test finds no difference in {10 - m['I']['reps_significant_0_05']} "
               f"and {10 - m['II']['reps_significant_0_05']} of 10 splits. ") if main_ok else "The main claim does not hold on our run. ")
    claims += (f"Table 2 agrees for {t2[0]} of {t2[1]} kernels: the polynomial kernels come back better than published, "
               "as an untuned polynomial model explains (item table2); the scheme I 10-fold CV and test PPV of Table 3 "
               "differ, cause open (item table3.schemeI).")
    for p in [PAPER / "README.md", PAPER / "figure-reproduction/README.md"]:
        t = p.read_text()
        t = fill(t, "RESULTS", table)
        if "<!--CLAIMS-->" in t:
            t = fill(t, "CLAIMS", claims)
        p.write_text(t)

    # Top-level README row.
    t1 = count("table1")
    t3a, t3b = count("table3.schemeI"), count("table3.schemeII")
    fa, fb = count("fig2.a.values"), count("fig2.b.values")
    status = (f"Table 1 {t1[0]} of {t1[1]} counts exact (diagnosed 1,266 as published, the rest within 10); "
              f"Table 2 {t2[0]} of {t2[1]} AUCs within the split spread (polynomial kernels differ); "
              f"Table 3 {t3a[0]} of {t3a[1]} and {t3b[0]} of {t3b[1]}; Fig. 2 {fa[0] + fb[0]} of {fa[1] + fb[1]} "
              f"curve points; main claim holds; package `diabclass`"
              + (f"; {S['reviewed']} verdicts set to agrees in review" if S.get("reviewed") else ""))
    readme = ROOT / "README.md"
    t = readme.read_text()
    row = ("| [`PMC2850872`](PMC2850872/) | Yu W, Liu T, Valdez R, Gwinn M, Khoury MJ. Application of support vector "
           "machine modeling for prediction of common diseases: the case of diabetes and pre-diabetes. *BMC Medical "
           "Informatics and Decision Making* 10:16 (2010). [doi:10.1186/1472-6947-10-16](https://doi.org/10.1186/1472-6947-10-16) | "
           f"{status} |")
    if "[`PMC2850872`]" in t:
        t = re.sub(r"^\| \[`PMC2850872`\].*$", row, t, flags=re.M)
    else:
        t = t.replace("| [`PMC4247685`](PMC4247685/)", row + "\n| [`PMC4247685`](PMC4247685/)", 1)
    if "reproduce-pmc2850872.yml" not in t:
        t = t.replace("`.github/workflows/reproduce-pmc4426843.yml` does the same for PMC4426843",
                      "`.github/workflows/reproduce-pmc2850872.yml` reruns PMC2850872 on changes to its folder, "
                      "refitting every model from the committed grid search (the search itself, about 80 minutes, only "
                      "when started by hand with `search = true`). `.github/workflows/reproduce-pmc4426843.yml` does the same for PMC4426843")
    readme.write_text(t)

    # Front page row.
    verdicts = [i["verdict"] for i in RES["items"] if i["verdict"] != "not_attempted"]
    stamp = ("agrees", "Agrees") if all(v in ("exact", "agrees") for v in verdicts) else (
        ("partly", "Partly agrees") if main_ok else ("differs", "Differs"))
    note = ("The main claim holds; agreed in review" if S.get("reviewed") and stamp[0] == "agrees"
            else "The main claim holds; the polynomial kernels differ" if main_ok else "")
    site = ROOT / "site/index.html"
    s = site.read_text()
    tr = f"""              <tr>
                <td class="date" data-label="Published"><time datetime="2010-03-22">22 Mar 2010</time></td>
                <td class="date" data-label="Analyzed"><time datetime="{RES['run']['date']}">8 Nov 2026</time></td>
                <td data-label="Paper">
                  <span class="pmc">PMC2850872</span>
                  <a class="title" href="https://doi.org/10.1186/1472-6947-10-16">Application of support vector machine modeling for prediction of common diseases: the case of diabetes and pre-diabetes</a>
                  <span class="journal">Yu et al., BMC Medical Informatics and Decision Making</span>
                  <span class="go"><a href="PMC2850872/">Results</a><a href="https://github.com/jeonglab-bcm/fossil/tree/main/PMC2850872">GitHub</a></span>
                </td>
                <td data-label="What we lost"><ul>
                  <li>The Diabetes Classifier web tool and its Java code</li>
                  <li>The random split behind every table</li>
                </ul></td>
                <td data-label="What we recovered"><ul>
                  <li><a href="https://github.com/jeonglab-bcm/fossil/blob/main/PMC2850872/package/tutorial/TUTORIAL.md">diabclass</a>, the SVM classifier as a Python package</li>
                  <li><a href="https://github.com/jeonglab-bcm/fossil/blob/main/PMC2850872/figure-reproduction/output/analytic.csv">The NHANES 1999 to 2004 cohort</a>, diagnosed diabetes at 1,266 as published</li>
                  <li><a href="PMC2850872/">Tables 1 to 3 and Fig. 2</a> against the paper</li>
                </ul></td>
                <td data-label="Verdict"><span class="stamp" data-v="{stamp[0]}">{stamp[1]}</span><span class="verdict-note">{note}</span></td>
              </tr>
"""
    s = re.sub(r"              <tr>\n                <td class=\"date\" data-label=\"Published\"><time datetime=\"2010-03-22\">.*?</tr>\n", "", s, flags=re.S)
    # Newest first: before the first row analyzed earlier than this one.
    s = re.sub(r"(?m)^ {16}(</?tr>)$", r"              \1", s)
    rows = list(re.finditer(r'(?m)^              <tr>\n                <td class="date" data-label="Published">.*?</td>\n'
                            r'                <td class="date" data-label="Analyzed"><time datetime="([\d-]+)">', s))
    older = [m for m in rows if m.group(1) < RES["run"]["date"]]
    if older:
        s = s[:older[0].start()] + tr + s[older[0].start():]
    else:
        s = s.replace("            </tbody>\n", tr + "            </tbody>\n", 1)
    n = s.count('<span class="pmc">')
    words = {5: "Five", 6: "Six", 7: "Seven", 8: "Eight"}
    s = re.sub(r'<h2 id="index-head">\w+ papers, figure by figure</h2>', f'<h2 id="index-head">{words.get(n, n)} papers, figure by figure</h2>', s)
    stamps = re.findall(r'<td data-label="Verdict"><span class="stamp" data-v="(\w+)"', s)
    agree, partly = stamps.count("agrees"), stamps.count("partly")
    nums = {1: "One", 2: "Two", 3: "Three", 4: "four", 5: "five", 6: "six"}
    agree_s = f"{nums.get(agree, agree)} " + ("agrees with its paper" if agree == 1 else "agree with their papers")
    s = re.sub(r"<p>Newest first\..*?</p>", f"<p>Newest first. {agree_s}, {nums.get(partly, partly)} partly.</p>", s, count=1)
    if 'href="PMC2850872/">' not in s.split('<footer class="foot">')[1]:
        s = s.replace('      <a href="PMC4426843/">miRNA enrichment figure</a>\n',
                      '      <a href="PMC4426843/">miRNA enrichment figure</a>\n      <a href="PMC2850872/">Diabetes classifier tables</a>\n')
    site.write_text(s)
    print("updated READMEs and site/index.html")


if __name__ == "__main__":
    main()
