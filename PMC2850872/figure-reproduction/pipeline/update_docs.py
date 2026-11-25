"""Write the generated parts of the READMEs and the front page from results.json.

Usage (from the repository root): python3 PMC2850872/figure-reproduction/pipeline/update_docs.py

- PMC2850872/README.md and figure-reproduction/README.md: the table between <!--RESULTS--> and
  <!--/RESULTS-->, from check_results.py --markdown; the claims line between <!--CLAIMS--> markers.
- PMC2850872/index.json: the front page's verdict and analysis date (tools/build_index.py builds the row).
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

    # Front page row.
    verdicts = [i["verdict"] for i in RES["items"] if i["verdict"] != "not_attempted"]
    stamp = "agrees" if all(v in ("exact", "agrees") for v in verdicts) else ("partly" if main_ok else "differs")
    note = ("The main claim holds; agreed in review" if S.get("reviewed") and stamp == "agrees"
            else "The main claim holds; the polynomial kernels differ" if main_ok else "")
    sys.path.insert(0, str(ROOT / "tools"))
    from build_index import set_fields
    set_fields("PMC2850872", analyzed=RES["run"]["date"], verdict={"v": stamp, "note": note} if note else {"v": stamp})
    print("updated READMEs and PMC2850872/index.json")


if __name__ == "__main__":
    main()
