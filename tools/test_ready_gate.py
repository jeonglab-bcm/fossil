#!/usr/bin/env python3
"""Tests of the ready gate's own logic (tools/ready_gate.py); no network.

Usage: python3 tools/test_ready_gate.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ready_gate as g  # noqa: E402

failures = []


def expect(name, got, want):
    if got != want:
        failures.append(f"{name}: got {got!r}, want {want!r}")


def run(name, status="completed", conclusion="success", run_id=None):
    url = f"https://github.com/o/r/actions/runs/{run_id}/job/1" if run_id else ""
    return {"name": name, "status": status, "conclusion": conclusion, "details_url": url}


# CI: green only when every other check finished well; the gate's own check is not waited for.
expect("all green", g.ci_state([run("reproduce"), run("check", conclusion="skipped")], []), (True, [], []))
expect("own check ignored", g.ci_state([run("ready gate", status="in_progress")], []), (True, [], []))
expect("pending", g.ci_state([run("reproduce", status="queued")], [])[1], ["reproduce"])
expect("failed", g.ci_state([run("reproduce", conclusion="failure")], [])[2], ["reproduce (failure)"])
expect("status failed", g.ci_state([], [{"context": "lint", "state": "error"}])[2], ["lint (error)"])
expect("workflow names", g.ci_state([run("reproduce", conclusion="failure", run_id=7)], [], {"7": "Reproduce PMC1"})[2],
       ["Reproduce PMC1: reproduce (failure)"])

# The PR body holds the rows of check_results.py --markdown, whatever else it holds.
table = "| Item | Verdict | Measure | Why |\n| --- | --- | --- | --- |\n| Fig. 2 | agrees | 98% within 2 px | |\n| Table 1 | partly | 6 of 8 |  a cause |"
expect("rows", g.table_rows(table), {("Fig. 2", "agrees", "98% within 2 px"), ("Table 1", "partly", "6 of 8")})
body = "## Title\n\n### What came back\n| Item | Verdict | Measure |\n|---|---|---|\n|  Fig. 2 | agrees |  98% within 2 px |\n| Table 1 | partly | 6 of 8 |"
expect("body holds the rows", g.table_rows(table) - g.table_rows(body), set())
stale = body.replace("6 of 8", "5 of 8")
expect("stale body misses a row", g.table_rows(table) - g.table_rows(stale), {("Table 1", "partly", "6 of 8")})

# Reviews: a new or changed review needs reason {kind, text}; an unchanged one on main only warns.
old = {"verdict": "agrees", "by": "r", "note": "n"}
reason = {"kind": "noise", "text": "within the spread of our runs"}
head = {"items": [
    {"id": "a", "review": old},                                  # unchanged from main, no reason: warn
    {"id": "b", "review": {**old, "verdict": "partly"}},         # changed, no reason: error
    {"id": "c", "review": {**old, "reason": reason}},            # changed, with a reason: fine
    {"id": "d", "review": {**old, "reason": {"kind": "noise", "text": " "}}},  # empty text: error
    {"id": "e"},                                                 # no review
]}
base = {"items": [{"id": i, "review": old} for i in "abcd"]}
expect("reviews", g.review_problems(head, base), (["b", "d"], ["a"]))
expect("new paper: every review is new", g.review_problems(head, None)[0], ["a", "b", "d"])

# AI review flags in a results-check comment.
comment = ("<details><summary>⚠️ <b>Fig. 3: partly</b>, why it did not fully match</summary>\n</details>\n"
           "<details><summary><b>Fig. 4: agrees</b>, why it matched</summary>\n</details>\n"
           "**Final conclusion:** approve this PR if you accept the verdicts above. First check the 1 item marked ⚠️.")
expect("flags", g.ai_flags(comment), ["Fig. 3: partly"])
expect("no flags", g.ai_flags(comment.replace("⚠️ <b>", "<b>")), [])

for f in failures:
    print("FAIL", f)
print("all tests passed" if not failures else f"{len(failures)} failed")
sys.exit(1 if failures else 0)
