"""Merge the hand-written notes with the pipeline's numbers into results.json.

build_results.py NOTES OUTDIR RESULTS [--package package.json] [--inputs fetch_inputs.sh] [--env env.json]
                 [--date YYYY-MM-DD] [--uniprot DIR]

Every observed value is computed here from the pipeline's outputs (prepare.json, fig2.json, clm.json and
the package report); the notes give labels, the paper's values, sources, assumptions and causes.
check_results.py --write then sets the verdicts.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def yn(x: bool) -> str:
    return "yes" if x else "no"


def observed(out: Path, package: dict | None) -> dict[str, dict[str, object]]:
    prep = json.load(open(out / "prepare.json"))
    f2 = json.load(open(out / "fig2.json"))
    cl = json.load(open(out / "clm.json"))
    o: dict[str, dict[str, object]] = {}

    b = prep["table1b"]
    o["table1b"] = {"proteins": b["proteins"], "locations": b["locations"], **b["per_location"]}
    c = prep["table1c"]
    o["table1c"] = {"interactions": c["interactions"], "proteins": c["proteins"]}
    o["table1d"] = dict(prep["table1d"]["per_condition"])

    a = f2["fig2a"]
    o["fig2a"] = {"PPI positive minus negative": round(a["ppi_pos_minus_neg"], 3),
                  "positive against negative, P < 0.001": yn(a["ppi_pos_minus_neg_p"] < 0.001),
                  "linked pairs share more than all pairs": yn(min(a["ppi"]["positive"], a["ppi"]["none"],
                                                                   a["ppi"]["negative"]) > a["all_pairs"]["positive"]),
                  "all pairs near random": yn(abs(a["all_pairs"]["none"] - a["random"]) < 0.05)}
    bb = f2["fig2b"]
    o["fig2b"] = {"single + physical + correlated": round(bb["single+physical+correlated"]["mean_auc"], 3),
                  "physical + correlated": round(bb["physical+correlated"]["mean_auc"], 3),
                  "physical": round(bb["physical"]["mean_auc"], 3),
                  "correlated": round(bb["correlated"]["mean_auc"], 3)}
    order = sorted(bb, key=lambda k: -bb[k]["mean_auc"])
    o["fig2b"]["same order as the paper"] = yn(order == ["single+physical+correlated", "physical+correlated",
                                                         "physical", "correlated"])
    cc = f2["fig2c"]
    i1k, i10k = cc["x"].index(1000), cc["x"].index(10000)
    o["fig2c"] = {"top 1,000 pairs enriched for links in every condition":
                  yn(all(cc[k][i1k] > 10 * cc["random"] for k in ("normal", "low", "high"))),
                  "common pairs enriched more than any one condition (top 10,000)":
                  yn(cc["common"][i10k] > max(cc[k][i10k] for k in ("normal", "low", "high")))}
    d = f2["fig2d"]
    o["fig2d"] = {k: round(d[k], 3) for k in ("S", "N1", "N2", "L1", "L2", "TR")}
    e = f2["fig2e"]
    kind_mean = {k: d[k] for k in ("S", "N1", "N2", "L1", "L2")}
    o["fig2e"] = {"N1 sets the most useful kind": yn(max(kind_mean, key=kind_mean.get) == "N1"),
                  "single-protein sets also selected": yn(e["selected_by_kind"]["S"] > 0)}

    h = cl["high_confidence"]
    o["text.high_confidence"] = {"locations": h["locations"], "proteins": h["proteins"],
                                 "locations without a GO location": h["locations_unknown"],
                                 "proteins without a GO location": h["proteins_unknown"]}
    panel = {"fig3a": "NKX2-2", "fig3e": "CPB1", "fig4a": "KIF13A", "fig5b": "RNF138", "fig5c": "TLX3",
             "fig6a": "GFRA4", "fig6b": "PSPN", "fig6c": "RET", "text.smad4": "SMAD4"}
    for iid, sym in panel.items():
        ours = cl["named"][sym]["ours"] or ["none"] * 3
        o[iid] = {f"{sym} {cond}": ours[k] for k, cond in enumerate(("normal", "low", "high"))}
    m = cl["fig3i"]["counts"]
    o["fig3j"] = {"TP": m.get("TP", 0), "FN": m.get("FN", 0), "FP": m.get("FP", 0), "TN": m.get("TN", 0),
                  "correct of 100": cl["fig3i"]["correct"]}
    o["text.mislocations"] = {"mislocated proteins": cl["mislocations"]["count"]}
    o["fig5a"] = {k: round(v, 2) for k, v in cl["fig5a"]["ours"].items()}
    links = cl["kif13a_links"]

    def higher_in_normal(sym):
        v = links.get(sym)
        return "no link" if v is None else yn(v["normal"] > max(v["low"], v["high"]))

    def higher_in_glioma(sym):
        v = links.get(sym)
        return "no link" if v is None else yn(min(v["low"], v["high"]) > v["normal"])

    o["fig4eg"] = {"AP1G1 more coherent in normal brain": higher_in_normal("AP1G1"),
                   "COG2 more coherent in normal brain": higher_in_normal("COG2"),
                   "ATF7IP more coherent in both gliomas": higher_in_glioma("ATF7IP")}
    bl = cl["blinded"]
    o["text.blinded"] = {s: v["ours"] for part in ("mislocating", "stable") for s, v in bl[part].items()}
    o["text.validated"] = {s: v["ours"] for s, v in cl["validated"].items()}
    o["_package"] = package or {}
    return o


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("notes")
    ap.add_argument("outdir")
    ap.add_argument("results")
    ap.add_argument("--package")
    ap.add_argument("--inputs")
    ap.add_argument("--env")
    ap.add_argument("--date")
    ap.add_argument("--uniprot", help="the downloaded uniprot folder (human_sprot.tsv.gz and RELEASE)")
    args = ap.parse_args()
    notes = json.load(open(args.notes))
    pkg = json.load(open(args.package)) if args.package else None
    obs = observed(Path(args.outdir), pkg)
    items = []
    for it in notes["items"]:
        it = json.loads(json.dumps(it))
        if it.get("method") == "values":
            got = obs[it["id"]]
            for f in it["values"]["fields"]:
                f["observed"] = got[f["name"]]
        if it["id"] == "package":
            it["check"] = {"passed": bool(pkg and pkg.get("passed")),
                           "detail": (pkg or {}).get("detail", "package check did not run")}
        items.append(it)
    inputs = []
    if args.inputs:
        text = Path(args.inputs).read_text()
        for dest, sha, url in re.findall(r"^fetch (\S+) ([0-9a-f]{64}) (\S+)", text, re.M):
            url = url.replace("$GEO", "https://ftp.ncbi.nlm.nih.gov/geo").replace(
                "$GOS3", "https://s3.amazonaws.com/go-data-product-release/2007-01-01").replace(
                "$PC1", "https://download.baderlab.org/PathwayCommons/PC1/last_release-2011/tab_delim_network/by_source").replace(
                "$PMC", "https://pmc-oa-opendata.s3.amazonaws.com")
            inputs.append({"name": dest, "url": url, "sha256": sha})
        if args.uniprot:
            import hashlib
            u = Path(args.uniprot)
            inputs.append({"name": "uniprot/human_sprot.tsv.gz",
                           "url": "https://rest.uniprot.org/uniprotkb/stream (organism_id:9606 AND reviewed:true)",
                           "sha256": hashlib.sha256((u / "human_sprot.tsv.gz").read_bytes()).hexdigest(),
                           "release": (u / "RELEASE").read_text().strip()})
    run = dict(notes["run"])
    run["inputs"] = inputs
    if args.date:
        run["date"] = args.date
    if args.env:
        run["environment"] = json.load(open(args.env))
    res = {"schema": "paper2repro/results/v1", "paper": notes["paper"], "run": run, "session": notes["session"],
           "skill": notes["skill"], "items": items}
    Path(args.results).write_text(json.dumps(res, indent=1, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
