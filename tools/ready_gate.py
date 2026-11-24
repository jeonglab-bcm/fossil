#!/usr/bin/env python3
"""The ready gate: a reproduction pull request is ready for review only when its checks are done.

Usage (in CI, with GH_TOKEN set and the PR's head checked out with full history):
  ready_gate.py --pr N [--repo owner/name] [--wait MINUTES] [--dry-run]
  ready_gate.py --draft-open [--repo owner/name] [--dry-run]

A pull request stays a draft while the agent keeps working on it. It is ready for review only when
all of these hold (issue #130):

  ci         every other check on the head commit finished, none failed, and the branch is up to date
             with main and has no conflicts, so CI ran on the current main
  results    the results check finds results.json for each paper whose results.json the PR adds or changes
  install    a paper with a package (PMC…/package/README.md) shows the Install block that
             tools/site_install.py writes on its results page
  ai review  the paper's results-check comment is for the head commit and has no item marked ⚠️
  body       the PR body holds every row (item, verdict, measure) of check_results.py --markdown, so it
             was regenerated from results.json after the last change (audit finding A7)
  reviews    every review block the PR adds or changes has a reason {kind, text} (#125); one already
             on main without a reason only warns until it is backfilled (#135)

A PR that changes no PMC…/results.json is not a reproduction PR: only the ci conditions apply.

The gate keeps one comment on the PR (marker <!-- fossil-ready-gate -->) listing each condition. When
one fails and the PR is not a draft, it converts the PR back to a draft. It never marks a PR ready;
the agent or the author does that, and the gate runs again. Exit 0 when ready, 1 when not.

--draft-open converts every open, non-draft reproduction PR to a draft with a comment that explains
the gate, so each comes back through it. --dry-run prints what would be done and changes nothing.
"""
import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

MARKER = "<!-- fossil-ready-gate -->"
RESULTS_MARK = "<!-- fossil-results-check: {} -->"
GATE_CHECK = "ready gate"  # this workflow's job name; its own check run is not waited for
OK_CONCLUSIONS = {"success", "neutral", "skipped"}
PAPER = re.compile(r"^(PMC\d+)/")


# --- GitHub, through the gh CLI (on every runner, and authenticated by GH_TOKEN) ---------------------

def gh(*args, data=None):
    cmd = ["gh", "api", *args]
    if data is not None:
        cmd += ["--input", "-"]
    p = subprocess.run(cmd, input=json.dumps(data) if data is not None else None, capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError(f"gh api {' '.join(args)}: {p.stderr.strip() or p.stdout.strip()}")
    return json.loads(p.stdout) if p.stdout.strip() else None


def gh_pages(path):
    """Every item of a paginated list endpoint (check-runs come wrapped in an object)."""
    out, page = [], 1
    while True:
        sep = "&" if "?" in path else "?"
        got = gh(f"{path}{sep}per_page=100&page={page}")
        items = got.get("check_runs", []) if isinstance(got, dict) else got
        out += items
        if len(items) < 100:
            return out
        page += 1


def pull(repo, n):
    """The PR, asking again while GitHub is still computing whether it merges."""
    for _ in range(6):
        pr = gh(f"repos/{repo}/pulls/{n}")
        if pr.get("mergeable") is not None:
            return pr
        time.sleep(5)
    return pr


def to_draft(repo, pr):
    gh("graphql", "-f", "query=mutation($id: ID!) { convertPullRequestToDraft(input: {pullRequestId: $id}) "
       "{ pullRequest { isDraft } } }", "-f", f"id={pr['node_id']}")


def upsert_comment(repo, n, body):
    for c in gh_pages(f"repos/{repo}/issues/{n}/comments"):
        if MARKER in (c.get("body") or ""):
            if c["body"] != body:
                gh(f"repos/{repo}/issues/comments/{c['id']}", "-X", "PATCH", data={"body": body})
            return
    gh(f"repos/{repo}/issues/{n}/comments", "-X", "POST", data={"body": body})


# --- The conditions: each returns (ok, lines) where lines say why ------------------------------------

def ci_state(runs, statuses, workflows=None):
    """(finished and green, pending names, failed names) from check runs and commit statuses.

    workflows maps an Actions run id to its workflow's name, so that the many jobs called "reproduce"
    are told apart ("Reproduce PMC2430201: reproduce")."""
    pending, failed = [], []
    for r in runs:
        if r["name"].lower() == GATE_CHECK:
            continue
        m = re.search(r"/actions/runs/(\d+)/", r.get("details_url") or "")
        name = f"{(workflows or {})[m.group(1)]}: {r['name']}" if m and m.group(1) in (workflows or {}) else r["name"]
        if r["status"] != "completed":
            pending.append(name)
        elif r.get("conclusion") not in OK_CONCLUSIONS:
            failed.append(f"{name} ({r.get('conclusion')})")
    for s in statuses:
        if s["state"] == "pending":
            pending.append(s["context"])
        elif s["state"] != "success":
            failed.append(f"{s['context']} ({s['state']})")
    return not pending and not failed, sorted(set(pending)), sorted(set(failed))


def check_ci(repo, pr, wait_minutes):
    lines, ok = [], True
    if pr.get("mergeable") is False or pr.get("mergeable_state") == "dirty":
        ok = False
        lines.append(f"conflicts with `{pr['base']['ref']}`: merge `{pr['base']['ref']}` into the branch and resolve them")
    cmp = gh(f"repos/{repo}/compare/{pr['base']['ref']}...{pr['head']['sha']}")
    if cmp.get("behind_by"):
        ok = False
        lines.append(f"{cmp['behind_by']} commit(s) behind `{pr['base']['ref']}`: merge it so CI runs on the current "
                     f"`{pr['base']['ref']}`")
    sha = pr["head"]["sha"]
    deadline = time.time() + 60 * wait_minutes
    while True:
        workflows = {str(w["id"]): w["name"] for w in gh(f"repos/{repo}/actions/runs?head_sha={sha}&per_page=100")["workflow_runs"]}
        green, pending, failed = ci_state(gh_pages(f"repos/{repo}/commits/{sha}/check-runs"),
                                          gh(f"repos/{repo}/commits/{sha}/status").get("statuses", []), workflows)
        if not pending or time.time() >= deadline:
            break
        time.sleep(30)
    if failed:
        ok = False
        lines.append("failed: " + ", ".join(failed))
    if pending:
        ok = False
        lines.append("still running: " + ", ".join(pending))
    if ok:
        lines.append(f"CI green on {sha[:7]}, up to date with `{pr['base']['ref']}`, no conflicts")
    return ok, lines


def results_path(paper):
    for p in (ROOT / paper / "results.json", ROOT / paper / "figure-reproduction" / "results.json"):
        if p.is_file():
            return p
    return None


def check_install(paper):
    import site_install
    want = site_install.block(paper)
    if not want:
        return True, ["no package: no Install block needed"]
    page = ROOT / "site" / paper / "index.html"
    if not page.is_file():
        return False, [f"site/{paper}/index.html does not exist"]
    if want.strip() not in page.read_text(encoding="utf-8"):
        return False, [f"site/{paper}/index.html has no Install block matching package/README.md: "
                       "run `python3 tools/site_install.py --write`"]
    return True, ["Install block matches package/README.md"]


def ai_flags(comment):
    """Labels of the items the AI review marks ⚠️ in a results-check comment."""
    return re.findall(r"⚠️\s*<b>(.*?)</b>", comment)


def check_ai(paper, comments, sha):
    mark = RESULTS_MARK.format(paper)
    found = [c["body"] for c in comments if mark in (c.get("body") or "")]
    if not found:
        return False, ["no results-check comment yet: the Results check workflow has not commented on this paper"]
    body = found[-1]
    if f"For {sha[:7]}." not in body:
        return False, [f"the results-check comment is not for the head commit {sha[:7]}: wait for the Results check to rerun"]
    if "AI review: ❌ not run" in body:
        return False, ["the AI review did not run (see the results-check comment); fix its cause and rerun the job"]
    flags = ai_flags(body)
    if flags:
        return False, [f"{len(flags)} item(s) marked ⚠️ in the AI review: " + "; ".join(flags[:5])
                       + (" …" if len(flags) > 5 else "") + ". Fix the item, or add a review block with its reason"]
    return True, ["the AI review marks no item ⚠️"]


def table_rows(markdown):
    """(item, verdict, measure) of every row of a markdown table, whitespace collapsed."""
    rows = set()
    for line in markdown.splitlines():
        line = line.strip()
        if not line.startswith("|") or re.fullmatch(r"\|[\s|:-]+\|", line):
            continue
        cells = [re.sub(r"\s+", " ", c).strip() for c in line.strip("|").split("|")]
        if len(cells) >= 3 and cells[:2] != ["Item", "Verdict"]:
            rows.add(tuple(cells[:3]))
    return rows


def check_body(paper, body):
    path = results_path(paper)
    p = subprocess.run([sys.executable, str(ROOT / "tools" / "paper2repro" / "check_results.py"), str(path), "--markdown"],
                       capture_output=True, text=True)
    want = table_rows(p.stdout)
    if p.returncode or not want:
        return False, [f"`check_results.py {path.relative_to(ROOT)} --markdown` fails: {(p.stderr or p.stdout).strip()[-300:]}"]
    missing = want - table_rows(body or "")
    if missing:
        first = sorted(missing)[0]
        return False, [f"{len(missing)} of {len(want)} rows of `check_results.py --markdown` are not in the PR body "
                       f"(first: {first[0]!r}, {first[1]}): regenerate the body's results table from results.json"]
    return True, [f"the PR body holds all {len(want)} rows of `check_results.py --markdown`"]


def review_problems(head, base):
    """(errors, warnings) for review blocks: a new or changed one needs reason {kind, text}."""
    old = {i.get("id"): i.get("review") for i in (base or {}).get("items", [])}
    errors, warnings = [], []
    for i in head.get("items", []):
        r = i.get("review")
        if not isinstance(r, dict):
            continue
        reason = r.get("reason")
        has = isinstance(reason, dict) and str(reason.get("kind", "")).strip() and str(reason.get("text", "")).strip()
        if has:
            continue
        if old.get(i.get("id")) == r:
            warnings.append(i.get("id"))
        else:
            errors.append(i.get("id"))
    return errors, warnings


def check_reviews(paper, base_ref):
    path = results_path(paper)
    head = json.loads(path.read_text(encoding="utf-8"))
    rel = path.relative_to(ROOT).as_posix()
    p = subprocess.run(["git", "-C", str(ROOT), "show", f"origin/{base_ref}:{rel}"], capture_output=True, text=True)
    base = json.loads(p.stdout) if p.returncode == 0 else None
    errors, warnings = review_problems(head, base)
    lines = []
    if errors:
        lines.append(f"{len(errors)} review block(s) this PR adds or changes have no reason {{kind, text}}: "
                     + ", ".join(errors[:8]) + (" …" if len(errors) > 8 else ""))
    if warnings:
        lines.append(f"note: {len(warnings)} review block(s) already on `{base_ref}` have no reason yet (#135); not blocking")
    if not errors and not warnings:
        lines.append("every review block has a reason" if any("review" in i for i in head.get("items", []))
                     else "no review blocks")
    return not errors, lines


# --- The gate ------------------------------------------------------------------------------------------

def papers_changed(repo, n):
    """(papers whose results.json the PR adds or changes, every paper folder it touches)."""
    files = [f["filename"] for f in gh_pages(f"repos/{repo}/pulls/{n}/files") if f.get("status") != "removed"]
    touched = sorted({m.group(1) for f in files if (m := PAPER.match(f))})
    results = sorted({f.split("/")[0] for f in files
                      if re.fullmatch(r"PMC\d+/(figure-reproduction/)?results\.json", f)})
    return results, touched


def render(n, sha, sections, ready, draft):
    head = ("✅ **Ready for review.**" + (" Mark it ready for review when the work is done." if draft else "")) if ready else (
        "❌ **Not ready for review.** " + ("This PR was moved back to a draft. " if not draft else "")
        + "Fix what is marked ❌ and push; the gate runs again on every push and when the PR is marked ready.")
    out = [MARKER, "### Ready gate", "", head, ""]
    for title, ok, lines in sections:
        out.append(f"- {'✅' if ok else '❌'} **{title}**: " + lines[0])
        out += [f"  - {line}" for line in lines[1:]]
    out += ["", f"<sub>For {sha[:7]}. The conditions are in `tools/ready_gate.py` (#130).</sub>"]
    return "\n".join(out)


def gate(args):
    pr = pull(args.repo, args.pr)
    if pr["state"] != "open":
        print(f"PR #{args.pr} is {pr['state']}: nothing to do")
        return 0
    sha, base_ref = pr["head"]["sha"], pr["base"]["ref"]
    here = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    if here != sha:
        print(f"WARNING the working tree is at {here[:7]}, the PR head is {sha[:7]}: file checks read the working tree",
              file=sys.stderr)
    sections = [("CI on the current " + base_ref, *check_ci(args.repo, pr, args.wait))]
    results, touched = papers_changed(args.repo, args.pr)
    if not results:
        names = ", ".join(touched[:4]) + (f" and {len(touched) - 4} more" if len(touched) > 4 else "")
        what = f"touches {names} but " if touched else ""
        sections.append(("Reproduction", True, [f"this PR {what}changes no PMC…/results.json: only the CI conditions apply"]))
    comments = gh_pages(f"repos/{args.repo}/issues/{args.pr}/comments") if results else []
    for paper in results:
        if not results_path(paper):
            sections.append((f"{paper}: results check", False, ["the PR removes or moves results.json; the results check finds none"]))
            continue
        sections.append((f"{paper}: results check", True, [f"finds {results_path(paper).relative_to(ROOT).as_posix()}"]))
        sections.append((f"{paper}: Install block", *check_install(paper)))
        sections.append((f"{paper}: AI review", *check_ai(paper, comments, sha)))
        sections.append((f"{paper}: PR body", *check_body(paper, pr.get("body"))))
        sections.append((f"{paper}: review reasons", *check_reviews(paper, base_ref)))
    ready = all(ok for _, ok, _ in sections)
    draft = pr["draft"]
    if not ready and not draft and not args.dry_run:
        to_draft(args.repo, pr)
    body = render(args.pr, sha, sections, ready, draft or not ready)
    if args.dry_run:
        print(body)
        if not ready and not draft:
            print(f"\n(dry run: PR #{args.pr} would be converted to a draft)")
    else:
        upsert_comment(args.repo, args.pr, body)
        print(body)
    return 0 if ready else 1


DRAFT_NOTE = (MARKER + "\n### Ready gate\n\nThis reproduction PR was moved to a draft, as every open reproduction PR was "
              "when the ready gate (#130) was added. It comes back for review through the gate: CI green on the "
              "current `main` with no conflicts, the Install block, no ⚠️ items in the AI review, the PR body "
              "regenerated from `results.json`, and a reason on every review block. Push, or mark it ready for "
              "review, and the gate posts what is missing here.")


def draft_open(args):
    moved = 0
    for pr in gh_pages(f"repos/{args.repo}/pulls?state=open"):
        if pr["draft"]:
            continue
        results, _ = papers_changed(args.repo, pr["number"])
        if not results:
            continue
        moved += 1
        print(f"#{pr['number']} {pr['title']} ({', '.join(results)})" + (": would move to draft" if args.dry_run else ": moved to draft"))
        if not args.dry_run:
            to_draft(args.repo, pr)
            upsert_comment(args.repo, pr["number"], DRAFT_NOTE)
    print(f"{moved} reproduction PR(s) {'would be ' if args.dry_run else ''}moved to draft")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default="jeonglab-bcm/fossil")
    ap.add_argument("--pr", type=int)
    ap.add_argument("--wait", type=float, default=0, help="minutes to wait for other checks to finish")
    ap.add_argument("--draft-open", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if args.draft_open == bool(args.pr):
        ap.error("give --pr N or --draft-open")
    return draft_open(args) if args.draft_open else gate(args)


if __name__ == "__main__":
    sys.exit(main())
