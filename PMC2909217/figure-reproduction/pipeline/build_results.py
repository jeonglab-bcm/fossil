"""Merge results_notes.json (written by hand: labels, sources, assumptions, causes) with the numbers
of a run into results.json, then let check_results.py compute the verdicts and the summary.

    python build_results.py RUN_DIR NOTES.json OUT.json

Notes items take their numbers from the run folder:
  "fields_from": "claims.json:KEY"        values.fields = the claim's fields
  "pixels_from": "comparison.json:KEY"    pixels = the figure's scores, controls and pass mark
  "check_from": "package.json"            check.passed and its detail line
  "check_from": "claims.json:text.arithmetic"
Text anywhere in an item may hold {{path}} placeholders, filled from the run's JSON files
(hypotheses.json, roc.json, claims.json, comparison.json, table1.json, counts.json, network.json):
"{{hypotheses.ppi_all.ssl.auc}}" or "{{roc.curves.unlabelled50/ssl/weighted.auc_mean:.3f}}".
The supplementary figures S1-S32 are generated from the "supplement" block. The skill block and the
session pointer travel with the notes unchanged.
"""

from __future__ import annotations

import copy
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCES = ["hypotheses", "roc", "claims", "comparison", "table1", "counts", "network", "package"]  # + verdict, summary for the page


def lookup(ctx, path):
    head, _, rest = path.partition(".")
    node = ctx[head]
    while rest:
        # keys may contain dots or slashes: take the longest key that matches
        keys = sorted((k for k in node if rest == k or rest.startswith(k + ".")), key=len, reverse=True) \
            if isinstance(node, dict) else []
        if keys:
            k = keys[0]
            node = node[k]
            rest = rest[len(k) + 1:]
        else:
            k, _, rest = rest.partition(".")
            node = node[int(k)] if isinstance(node, list) else node[k]
    return node


def fill(obj, ctx):
    if isinstance(obj, str):
        def rep(m):
            path, _, spec = m.group(1).partition(":")
            v = lookup(ctx, path.strip())
            return format(v, spec) if spec else str(v)
        return re.sub(r"\{\{(.+?)\}\}", rep, obj)
    if isinstance(obj, list):
        return [fill(x, ctx) for x in obj]
    if isinstance(obj, dict):
        return {k: fill(v, ctx) for k, v in obj.items()}
    return obj


def arithmetic_detail(a):
    n = a["implied_effective_n_median"]
    return (f"From the paper's own Table 1: P below 0.05 in {16 - len(a['p_not_below_0.05'])} of 16 cells "
            f"(not: {', '.join(a['p_not_below_0.05'])}); the weighted-network P below the binary one in "
            f"{a['weighted_p_smaller_rows']} of 8 rows (not: {', '.join(a['weighted_p_not_smaller'])}). "
            f"The printed D and P imply about {n['binary']:,.0f} (binary) and {n['weighted']:,.0f} (weighted) "
            f"effective pairs per test; at that size D = 0.0364 gives P = {a['avg_degree_binary_p_at_median_n']:.1e}, "
            f"not 0.9. Binary absolute-difference degree and closeness rows are identical. "
            f"Fig. 6 labels equal Table 1 except panel c's P (1.1590e-008 against 1.56E-08).")


def main(run, notes_path, out):
    run = Path(run)
    notes = json.loads(Path(notes_path).read_text())
    ctx = {k: json.loads((run / f"{k}.json").read_text()) for k in SOURCES if (run / f"{k}.json").exists()}
    res = {"schema": "paper2repro/results/v1", "paper": notes["paper"], "run": notes["run"],
           "session": notes.get("session", {"ledger": "session/ledger.json"}), "skill": notes["skill"],
           "items": []}
    items = []
    for it in notes["items"]:
        if it.get("id") == "supplement":
            for k in range(1, 33):
                s = copy.deepcopy(it["template"])
                part = s["density"] if k <= 16 else s["ecdf"]
                s.update({"id": f"figS{k}", "label": f"Additional file 1, Fig. S{k}"})
                s["cause"] = copy.deepcopy(part["cause"])
                s.pop("density"), s.pop("ecdf")
                items.append(s)
            continue
        items.append(it)
    for it in items:
        it = copy.deepcopy(it)
        src = it.pop("fields_from", None)
        if src:
            f, _, key = src.partition(":")
            d = json.loads((run / f).read_text())[key]
            it.setdefault("values", {})["fields"] = copy.deepcopy(d["fields"])
            if "detail" in d:
                it["detail"] = d["detail"]
        px = it.pop("pixels_from", None)
        if px:
            f, _, key = px.partition(":")
            d = json.loads((run / f).read_text())[key]
            it["pixels"] = {"tolerance_px": d["tolerance_px"], "dpi": "PMC web JPEG",
                            "published_near_ours": d["published_near_ours"],
                            "ours_near_published": d["ours_near_published"],
                            "threshold": d["threshold"], "controls": d["controls"]}
        chk = it.pop("check_from", None)
        if chk:
            f, _, key = chk.partition(":")
            d = json.loads((run / f).read_text())
            if key == "text.arithmetic":
                a = d[key]
                it["check"] = {"passed": True, "detail": arithmetic_detail(a)}
            else:
                it["check"] = {"passed": bool(d.get("passed")), "detail": d.get("detail", "")}
        res["items"].append(fill(it, ctx))
    Path(out).write_text(json.dumps(res, indent=1) + "\n")
    r = subprocess.run([sys.executable, str(HERE / "check_results.py"), out, "--write", "--skip-files"])
    if "page" in notes:
        done = json.loads(Path(out).read_text())
        ctx["verdict"] = {i["id"]: str(i.get("verdict", "")).replace("_", " ") for i in done["items"]}
        ctx["summary"] = done.get("summary", {})
        (run / "page.json").write_text(json.dumps(fill(notes["page"], ctx), indent=1) + "\n")
    sys.exit(r.returncode)


if __name__ == "__main__":
    main(*sys.argv[1:4])
