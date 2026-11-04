"""Post (or update) one PR comment per reproduction: what the PR changes in results.json, whether
results.json agrees with the committed outputs, and an overlay of each published figure with the
render committed in the PR.

The overlays go to the ci-assets branch (pr-<number>/<paper>/<commit>/fig<N>.png) so the comment can
show them. Only figures whose render the PR changes are shown, or every figure when the PR adds
results.json. The comment carries a marker and is edited in place on later runs.

Usage (in CI, with GITHUB_TOKEN or GH_TOKEN set):
  python3 tools/pr_comment.py <paper> --check results-check/results-check.json --base main
      --pr 27 --repo owner/name --sha <commit> --run-url <url>
  python3 tools/pr_comment.py <paper> --check ... --base main --dry-run   # print the comment only
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import check_results  # noqa: E402
import overlay  # noqa: E402

ASSETS = "ci-assets"


def git(*args, cwd=None, check=True):
    return subprocess.run(["git", *args], cwd=cwd, check=check, capture_output=True, text=True)


def base_results(paper, base):
    r = git("show", f"origin/{base}:{paper}/figure-reproduction/results.json", check=False)
    return json.loads(r.stdout) if r.returncode == 0 else None


def changed_renders(paper, base):
    r = git("diff", "--name-only", f"origin/{base}...HEAD", "--", f"{paper}/figure-reproduction/output", check=False)
    return {os.path.basename(p).split("_")[0] for p in r.stdout.split() if p.endswith("_ours.png")}


def publish(src_dir, files, dest, message):
    """Commit files to the ci-assets branch under dest and push, retrying when another job pushed first."""
    tmp = tempfile.mkdtemp()
    for attempt in range(6):
        wt = os.path.join(tmp, f"wt{attempt}")
        if git("ls-remote", "--exit-code", "--heads", "origin", ASSETS, check=False).returncode == 0:
            git("fetch", "-q", "--depth", "1", "origin", ASSETS)
            git("worktree", "add", "-q", "--detach", wt, "FETCH_HEAD")
        else:
            git("worktree", "add", "-q", "--detach", wt)
            git("checkout", "-q", "--orphan", f"{ASSETS}-new", cwd=wt)
            git("rm", "-rqf", ".", cwd=wt)
        os.makedirs(os.path.join(wt, dest), exist_ok=True)
        for f in files:
            shutil.copy(os.path.join(src_dir, f), os.path.join(wt, dest, f))
        git("add", dest, cwd=wt)
        git("-c", "user.name=github-actions[bot]", "-c", "user.email=41898282+github-actions[bot]@users.noreply.github.com",
            "commit", "-qm", message, cwd=wt, check=False)
        if git("push", "-q", "origin", f"HEAD:refs/heads/{ASSETS}", cwd=wt, check=False).returncode == 0:
            git("worktree", "remove", "--force", wt, check=False)
            return
        git("worktree", "remove", "--force", wt, check=False)
        time.sleep(2 + 2 * attempt)
    raise SystemExit("could not push the overlays to the ci-assets branch")


def diff_block(lines):
    return "```diff\n" + "\n".join(lines) + "\n```"


def build(paper, check, base_spec, head_spec, figures, image_url, sha, run_url):
    fmt = check_results.fmt
    rows = check["results"]
    n_ok = sum(r["status"] == "pass" for r in rows)
    out = [f"<!-- fossil-results-check: {paper} -->", f"### {paper}: results.json against the committed outputs", ""]
    out.append(f"**{n_ok} of {len(rows)} results agree** with the files committed in this PR." if n_ok == len(rows)
               else f"**{len(rows) - n_ok} of {len(rows)} results {'does' if len(rows) - n_ok == 1 else 'do'} not agree** with the files committed in this PR.")
    out.append("")

    # What the PR changes in results.json.
    out.append("#### What this PR changes in results.json")
    if base_spec is None:
        out.append(f"This PR adds results.json, with {len(head_spec['results'])} results.")
    else:
        old = {e["id"]: e for e in base_spec["results"]}
        new = {e["id"]: e for e in head_spec["results"]}
        width = max([len(i) for i in list(old) + list(new)] + [4])
        lines = []
        for i, e in new.items():
            if i not in old:
                lines.append(f"+ {i:<{width}}  {fmt(e['expected'])}   (new)")
            elif old[i].get("expected") != e.get("expected") or old[i].get("tolerance") != e.get("tolerance"):
                lines.append(f"- {i:<{width}}  {fmt(old[i]['expected'])}   allowed {check_results.fmt_tol(old[i].get('tolerance'))}")
                lines.append(f"+ {i:<{width}}  {fmt(e['expected'])}   allowed {check_results.fmt_tol(e.get('tolerance'))}")
        for i, e in old.items():
            if i not in new:
                lines.append(f"- {i:<{width}}  {fmt(e['expected'])}   (removed)")
        out.append(diff_block(lines) if lines else "No expected value changes.")
    out.append("")

    bad = [r for r in rows if r["status"] != "pass"]
    if bad:
        out.append("#### Results that do not agree")
        width = max(len(r["id"]) for r in bad)
        lines = []
        for r in bad:
            lines.append(f"- expected   {r['id']:<{width}}  {fmt(r['expected'])}")
            lines.append(f"+ committed  {r['id']:<{width}}  " + (fmt(r["observed"]) if r["status"] != "missing" else f"missing: {r.get('why')}"))
        out.append(diff_block(lines))
        out.append("")

    out.append(f"<details><summary>All {len(rows)} results</summary>\n")
    out.append("| Result | Expected | Committed | Gap | Allowed | |\n| --- | --- | --- | --- | --- | --- |")
    for r in rows:
        gap = f"{r['gap']:+.3g}" if isinstance(r["gap"], (int, float)) else ""
        mark = {"pass": "agrees", "fail": "**differs**", "missing": "**missing**"}[r["status"]]
        cells = [r["label"], fmt(r["expected"]), fmt(r["observed"]) if r["status"] != "missing" else "", gap,
                 check_results.fmt_tol(r.get("tolerance")), mark]
        out.append("| " + " | ".join(str(c).replace("|", "\\|") for c in cells) + " |")
    out.append("\n</details>\n")

    out.append("#### The paper's figures against the renders in this PR")
    if not figures:
        out.append("No render changed in this PR.")
    else:
        out.append("Grey: the paper and our render agree within 2 px. Dark: only in the paper. Green: only in our render. "
                   "The whole figure is compared, axes and labels included.\n")
        cells = [f'<td align="center" width="50%"><img src="{image_url(f["file"])}" width="400" alt="{f["figure"]}, paper against our render"><br>'
                 f'<sub>{f["figure"]}: {f["paper_within_2px"]:.1%} of the paper\'s ink within 2 px of ours, '
                 f'{f["ours_within_2px"]:.1%} of ours within 2 px of the paper\'s</sub></td>' for f in figures]
        rows_html = ["<tr>" + "".join(cells[i:i + 2]) + "</tr>" for i in range(0, len(cells), 2)]
        out.append("<table>" + "".join(rows_html) + "</table>")
    out.append("")
    foot = f"For {sha[:7]}." if sha else ""
    if run_url:
        foot += f" [This run]({run_url}); its full report is the `{paper}-results-check` artifact."
    out.append(f"<sub>{foot.strip()}</sub>")
    return "\n".join(out)


def upsert(repo, pr, body, marker):
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        raise SystemExit("set GITHUB_TOKEN or GH_TOKEN to post the comment")

    def api(method, url, data=None):
        req = urllib.request.Request(f"https://api.github.com{url}", method=method,
                                     data=json.dumps(data).encode() if data is not None else None,
                                     headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
                                              "X-GitHub-Api-Version": "2022-11-28"})
        with urllib.request.urlopen(req) as r:
            return json.load(r)

    page = 1
    while True:
        comments = api("GET", f"/repos/{repo}/issues/{pr}/comments?per_page=100&page={page}")
        for c in comments:
            if c["body"].startswith(marker):
                api("PATCH", f"/repos/{repo}/issues/comments/{c['id']}", {"body": body})
                print(f"updated comment {c['html_url']}")
                return
        if len(comments) < 100:
            break
        page += 1
    c = api("POST", f"/repos/{repo}/issues/{pr}/comments", {"body": body})
    print(f"posted comment {c['html_url']}")


def main():
    ap = argparse.ArgumentParser(description="Post the results check and figure overlays as a PR comment.")
    ap.add_argument("paper")
    ap.add_argument("--check", required=True, help="results-check.json from check_results.py --report")
    ap.add_argument("--base", required=True, help="the PR's base branch")
    ap.add_argument("--pr")
    ap.add_argument("--repo")
    ap.add_argument("--sha", default="")
    ap.add_argument("--run-url", default="")
    ap.add_argument("--dry-run", action="store_true", help="print the comment; push and post nothing")
    args = ap.parse_args()

    folder = os.path.join(args.paper, "figure-reproduction")
    with open(args.check) as f:
        check = json.load(f)
    with open(os.path.join(folder, "results.json")) as f:
        head_spec = json.load(f)
    base_spec = base_results(args.paper, args.base)

    tmp = tempfile.mkdtemp()
    overlay.main(os.path.join(folder, "published"), os.path.join(folder, "output"), tmp)
    with open(os.path.join(tmp, "overlays.json")) as f:
        figures = json.load(f)
    if base_spec is not None:
        changed = changed_renders(args.paper, args.base)
        figures = [f for f in figures if f["file"][:-4] in changed]

    dest = f"pr-{args.pr}/{args.paper}/{args.sha[:7] or 'local'}"
    if args.dry_run:
        image_url = lambda name: os.path.join(tmp, name)
    else:
        if figures:
            publish(tmp, [f["file"] for f in figures], dest, f"Overlays for {args.paper}, PR #{args.pr} at {args.sha[:7]}")
        image_url = lambda name: f"https://raw.githubusercontent.com/{args.repo}/{ASSETS}/{dest}/{name}"

    body = build(args.paper, check, base_spec, head_spec, figures, image_url, args.sha, args.run_url)
    if args.dry_run:
        print(body)
        return
    upsert(args.repo, args.pr, body, body.split("\n", 1)[0])


if __name__ == "__main__":
    main()
