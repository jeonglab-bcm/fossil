"""Fill the generated parts of PMC4331676/README.md from results.json.

Usage: readme_tables.py RESULTS_JSON README_MD NOTES_JSON

Replaces everything between each marker comment and the next blank line or heading: the results
table (check_results.py --markdown), the claims table (the text.* items, paper against our run)
and the closing line on the claims (results_notes.json, page.claims_line).
"""
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def fmt(v):
    return f"{v:g}" if isinstance(v, float) else str(v)


def main(results, readme, notes):
    R = json.loads(Path(results).read_text())
    N = json.loads(Path(notes).read_text())["page"]
    table = subprocess.run([sys.executable, str(HERE / "check_results.py"), results, "--markdown", "--skip-files"],
                           capture_output=True, text=True, check=True).stdout.strip()
    claims = []
    for it in R["items"]:
        if it["id"].startswith("text.") and it["method"] == "values":
            exc = {e["field"] for e in it["values"].get("exceptions", [])}
            for f in it["values"]["fields"]:
                note = " (paper error: does not follow from its own Table 4)" if f["name"] in exc else ""
                claims.append(f"| {f['name']} | {fmt(f['expected'])}{note} | {fmt(f['observed'])} | ours |")
        if it["id"] == "text.arithmetic":
            claims.append(f"| Claims recomputed from the paper's own tables | | {it['check']['detail']} | arithmetic check |")
    text = Path(readme).read_text()
    text = re.sub(r"<!-- RESULTS TABLE -->\n(?:.*\n)*?(?=\n## )", "<!-- RESULTS TABLE -->\n" + table + "\n", text)
    text = re.sub(r"<!-- CLAIMS TABLE -->\n(?:\|.*\n)*", "<!-- CLAIMS TABLE -->\n" + "\n".join(claims) + "\n", text)
    text = re.sub(r"<!-- CLAIMS LINE -->\n(?:.+\n)*", "<!-- CLAIMS LINE -->\n" + N["claims_line"] + "\n", text)
    Path(readme).write_text(text)
    print(f"README tables written ({len(claims)} claim rows)")


if __name__ == "__main__":
    main(*sys.argv[1:4])
