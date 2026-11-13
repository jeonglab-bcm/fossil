"""Write the Results and claims tables of the READMEs from results.json (never by hand).

Usage: readme_tables.py PMC2711306_DIR
Replaces the text between <!--RESULTS:start--> and <!--RESULTS:end--> (both READMEs) and between
<!--CLAIMS:start--> and <!--CLAIMS:end--> (the paper README).
"""
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CLAIMS = ["text.networks", "text.yeast_performance", "text.dimensions", "text.iteration",
          "text.false_positives", "text.high_confidence", "text.go_background",
          "validation.published_pairs", "text.arithmetic", "text.citexplorer"]
KIND = {"text.arithmetic": "arithmetic check (the paper's own numbers)",
        "validation.published_pairs": "our validation code on the paper's Table S1"}


def put(text, tag, body):
    pat = re.compile(rf"<!--{tag}:start-->.*?<!--{tag}:end-->", re.S)
    return pat.sub(f"<!--{tag}:start-->\n{body}\n<!--{tag}:end-->", text)


def main(d):
    d = Path(d)
    out = subprocess.run([sys.executable, str(HERE / "check_results.py"), str(d / "results.json"), "--markdown",
                          "--skip-files"], capture_output=True, text=True).stdout
    lines = out.strip().splitlines()
    table = "\n".join(l for l in lines if l.startswith("|"))
    summ = next(l for l in lines if l and not l.startswith("|") and not l.startswith("OK "))
    r = json.loads((d / "results.json").read_text())
    notes = json.loads((d / "figure-reproduction/results_notes.json").read_text())
    by = {i["id"]: i for i in r["items"]}
    rows = ["| Claim | Kind | Paper | Ours | Verdict |", "| --- | --- | --- | --- | --- |"]
    for cid in CLAIMS:
        it = by[cid]
        kind = KIND.get(cid, "ours")
        if it["method"] == "values":
            exc = {e["field"] for e in it["values"].get("exceptions", [])}
            for f in it["values"]["fields"]:
                v = "paper error" if f["name"] in exc else it["verdict"]
                rows.append(f"| {it['label']}: {f['name']} | {kind} | {f['expected']} | {f['observed']} | {v} |")
        else:
            rows.append(f"| {it['label']} | {kind} | | not attempted | {it['verdict']} |")
    claims = "\n".join(rows) + "\n\n" + notes["page"]["claims_line"]
    for name in ("README.md", "figure-reproduction/README.md"):
        p = d / name
        s = put(p.read_text(), "RESULTS", table + "\n\n" + summ)
        s = put(s, "CLAIMS", claims)
        p.write_text(s)


if __name__ == "__main__":
    main(sys.argv[1])
