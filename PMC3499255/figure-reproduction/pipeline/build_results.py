"""Assemble the normalized PMC3499255/results.json from the run outputs and the
hand-written results_notes.json, then compute verdicts with the skill's
check_results.py.

    build_results.py RUNDIR NOTES OUT [--check-results PATH]

RUNDIR holds the run outputs: y2007.json, y2001.json, test.json, series.json,
textclaims.json, package.json, pseudolik_check.json, arithmetic_check.json.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

import numpy as np


def load(rundir, name):
    path = os.path.join(rundir, name)
    if os.path.exists(path):
        return json.load(open(path))
    return None


def jpath(obj, path):
    cur = obj
    for key in path.split("."):
        if isinstance(cur, list):
            cur = cur[int(key)]
        else:
            cur = cur[key]
    return cur


def resolve_obs(spec, runs):
    """Resolve an 'obs' mini-spec to an observed value string."""
    # file:path form
    if spec.startswith("bool:"):
        # bool:test:truth.mean_latency in test:lo,test:hi
        body = spec[len("bool:"):]
        val_spec, rng = body.split(" in ")
        f, p = val_spec.split(":", 1)
        v = jpath(runs[f], p)
        (lof, lop), (hif, hip) = [x.split(":", 1) for x in rng.split(",")]
        lo = jpath(runs[lof], lop); hi = jpath(runs[hif], hip)
        return "yes" if lo <= v <= hi else "no"
    if spec.startswith("tree_correct:"):
        f = spec.split(":", 1)[1]
        p = runs[f]
        bt = p["best_tree"]; tr = p["truth"]["J"]; I = len(bt)
        tp = np.array(p["trans_prob"])
        return str(sum(1 for i in range(I)
                       if int(np.argmax(tp[i])) == (I if tr[i] == -1 else tr[i])))
    if spec.startswith("ip5_phase1_prob:"):
        f = spec.split(":", 1)[1]
        p = runs[f]
        nm = p["names"]; tp = np.array(p["trans_prob"]); i5 = nm.index("IP5")
        phase1 = [nm.index(x) for x in ("IP1b", "IP2b") if x in nm]
        return f"{sum(tp[i5, j] for j in phase1):.2f}"
    if spec.startswith("k_is_hub:"):
        f = spec.split(":", 1)[1]
        p = runs[f]
        nm = p["names"]; bt = p["best_tree"]
        from collections import Counter
        c = Counter(s for s in bt if s is not None and s != -1)
        if not c:
            return "no"
        hub = max(c, key=c.get)
        return "yes" if nm[hub] == "K" else "no"
    if spec.startswith("text:"):
        key = spec.split(":", 1)[1]
        v = runs["text"][key]
        return f"{v}"
    # plain file:path
    f, p = spec.split(":", 1)
    v = jpath(runs[f], p)
    if isinstance(v, float):
        return f"{v:.4f}"
    return f"{v}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rundir")
    ap.add_argument("notes")
    ap.add_argument("out")
    ap.add_argument("--check-results", default=None, help="path to check_results.py")
    ap.add_argument("--root", default=None, help="root dir for check_results --root")
    args = ap.parse_args()

    notes = json.load(open(args.notes))
    runs = {
        "y2007": load(args.rundir, "y2007.json"),
        "y2001": load(args.rundir, "y2001.json"),
        "test": load(args.rundir, "test.json"),
        "series": load(args.rundir, "series.json"),
        "text": load(args.rundir, "textclaims.json"),
        "package": load(args.rundir, "package.json"),
        "pseudolik": load(args.rundir, "pseudolik_check.json"),
        "arith": load(args.rundir, "arithmetic_check.json"),
    }

    assumptions_lib = {"mc": notes["mc_assumption"]}

    def build_value_item(iid, note):
        fields = []
        for f in note["fields"]:
            obs = resolve_obs(f["obs"], runs)
            field = {"name": f["name"], "expected": f["expected"], "observed": obs}
            if "tolerance" in f:
                field["tolerance"] = f["tolerance"]
            fields.append(field)
        item = {"id": iid, "label": note["label"], "kind": note["kind"],
                "source": note["source"], "method": note["method"],
                "values": {"fields": fields}}
        if "assumptions" in note:
            item["assumptions"] = [assumptions_lib[a] for a in note["assumptions"]]
        if "outputs" in note and note["outputs"]:
            item["outputs"] = note["outputs"]
        if "cause" in note:
            item["cause"] = note["cause"]
        return item

    items = []
    for iid, note in notes["item_notes"].items():
        method = note["method"]
        if method == "none":
            item = {"id": iid, "label": note["label"], "kind": note["kind"],
                    "source": note["source"], "method": "none", "cause": note["cause"]}
        elif method == "values":
            item = build_value_item(iid, note)
        elif method == "check":
            if iid == "package":
                rep = runs["package"] or {"passed": False, "detail": "package report missing"}
                chk = {"passed": bool(rep.get("passed")), "detail": rep.get("detail", "")}
            elif iid == "pseudolik_check":
                rep = runs["pseudolik"] or {"passed": False, "detail": "missing"}
                chk = {"passed": bool(rep.get("passed")), "detail": rep.get("detail", "")}
            elif iid == "text.arithmetic":
                rep = runs["arith"] or {"passed": False, "detail": "missing"}
                chk = {"passed": bool(rep.get("passed")), "detail": rep.get("detail", "")}
            else:
                chk = {"passed": False, "detail": "unknown check"}
            item = {"id": iid, "label": note["label"], "kind": note["kind"],
                    "source": note["source"], "method": "check", "check": chk}
            if note.get("outputs"):
                item["outputs"] = note["outputs"]
            if note.get("cause"):
                item["cause"] = note["cause"]
        else:
            continue
        items.append(item)

    import datetime
    env = {"python": sys.version.split()[0], "numpy": np.__version__}
    out = {
        "schema": "paper2repro/results/v1",
        "paper": notes["paper"],
        "run": {**notes["run"], "date": datetime.date.today().isoformat(),
                "environment": env},
        "session": {"ledger": "session/ledger.json"},
        "skill": notes["skill"],
        "items": items,
    }
    # run metadata: iteration counts actually used
    cfg = {}
    for k in ("y2007", "y2001", "test"):
        if runs.get(k) and "config" in runs[k]:
            cfg[k] = runs[k]["config"]
    out["run"]["mcmc"] = cfg
    with open(args.out, "w") as fh:
        json.dump(out, fh, indent=2)

    if args.check_results:
        cmd = [sys.executable, args.check_results, args.out, "--write"]
        if args.root:
            cmd += ["--root", args.root]
        subprocess.run(cmd, check=True)
    print("wrote", args.out)


if __name__ == "__main__":
    main()
