#!/usr/bin/env python3
"""Check that each reproduction names the Paper2Repro release it was made with.

Usage:
  check_skill.py --base origin/main   papers this branch adds, or whose results.json it changes
  check_skill.py --all                every paper folder
  add --offline to skip looking the tags up in the Paper2Repro repository

A paper's "skill" block is read from <paper>/results.json (written by Paper2Repro 0.2.0 and later)
or, for papers made before that file existed, from <paper>/figure-reproduction/results.json:

  "skill": {"name": "paper2repro", "version": "0.5.0", "tag": "paper2repro-v0.5.0",
            "commit": "<sha>" or null, "modified": false, true or null,
            "source": ..., "note": ...}

Sessions write it with the skill's scripts/skill_version.py, which leaves out "source". Blocks
added afterwards say how the version was found:
  transcript  the skill text loaded in the session's transcript matches this release
  inferred    deduced from when and how the session installed the skill; "note" says how
  none        no Paper2Repro skill was used (version null); "note" says why
  unknown     not known yet (version null); allowed only for papers already on the base branch

Every version must be a paper2repro-v<version> tag in jeonglab-bcm/Paper2Repro.
"""
import argparse
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = "https://github.com/jeonglab-bcm/Paper2Repro"
SOURCES = {"skill_version.py", "transcript", "inferred", "none", "unknown"}
NEEDS_NOTE = {"inferred", "none", "unknown"}


def git(*args):
    return subprocess.run(["git", "-C", ROOT, *args], check=True, capture_output=True, text=True).stdout


def papers_to_check(base):
    if base is None:
        return sorted(d for d in os.listdir(ROOT) if re.fullmatch(r"PMC\d+", d) and os.path.isdir(os.path.join(ROOT, d)))
    on_base = {p.split("/")[0] for p in git("ls-tree", "--name-only", base).split()}
    changed = git("diff", "--name-only", f"{base}...HEAD", "--", "PMC*").split()
    papers = set()
    for path in changed:
        paper = path.split("/")[0]
        if not os.path.isdir(os.path.join(ROOT, paper)):
            continue  # the branch deletes it
        if paper not in on_base or path in (f"{paper}/results.json", f"{paper}/figure-reproduction/results.json"):
            papers.add(paper)
    return sorted(papers), on_base


def skill_block(paper):
    for rel in ("results.json", "figure-reproduction/results.json"):
        path = os.path.join(ROOT, paper, rel)
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                return f"{paper}/{rel}", json.load(f).get("skill")
    return None, None


def published_tags():
    out = subprocess.run(["git", "ls-remote", "--tags", REPO, "paper2repro-v*"], check=True,
                         capture_output=True, text=True).stdout
    return {line.split("refs/tags/")[1] for line in out.splitlines() if "refs/tags/" in line and not line.endswith("^{}")}


def check(paper, on_base, tags):
    where, s = skill_block(paper)
    if where is None:
        return [f"{paper}: no results.json to hold the skill block"], None
    if not isinstance(s, dict):
        return [f"{where}: no \"skill\" block; run the installed skill's scripts/skill_version.py on it "
                "(or on the notes file the pipeline builds it from)"], None
    errors = []
    source = s.get("source", "skill_version.py")
    version = s.get("version")
    if s.get("name") != "paper2repro":
        errors.append(f"skill.name is {s.get('name')!r}, not 'paper2repro'")
    if source not in SOURCES:
        errors.append(f"skill.source {source!r} is not one of {', '.join(sorted(SOURCES))}")
    if source in NEEDS_NOTE and not s.get("note"):
        errors.append(f"skill.source {source!r} needs a note saying how it was found")
    if source == "unknown" and on_base is not None and paper not in on_base:
        errors.append("skill.source 'unknown' is only for papers made before versions were recorded; "
                      "a new paper records its version with scripts/skill_version.py")
    if source in ("none", "unknown"):
        if version is not None:
            errors.append(f"skill.source {source!r} must have version null")
    elif not re.fullmatch(r"\d+\.\d+\.\d+", str(version)):
        errors.append(f"skill.version {version!r} is not MAJOR.MINOR.PATCH")
    else:
        tag = f"paper2repro-v{version}"
        if s.get("tag") != tag:
            errors.append(f"skill.tag is {s.get('tag')!r}, expected {tag!r}")
        elif tags is not None and tag not in tags:
            errors.append(f"{tag} is not a tag in {REPO}")
    label = "none" if source == "none" else ("unknown" if version is None else f"v{version}")
    return [f"{where}: {e}" for e in errors], f"{paper}: {label} ({source})"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    which = ap.add_mutually_exclusive_group(required=True)
    which.add_argument("--base")
    which.add_argument("--all", action="store_true")
    ap.add_argument("--offline", action="store_true")
    args = ap.parse_args()

    if args.all:
        papers, on_base = papers_to_check(None), None
    else:
        papers, on_base = papers_to_check(args.base)
    if not papers:
        print("no paper added and no results.json changed")
        return 0
    tags = None if args.offline else published_tags()
    errors = []
    for paper in papers:
        errs, ok = check(paper, on_base, tags)
        errors += errs
        if ok and not errs:
            print(ok)
    for e in errors:
        print(f"ERROR {e}", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
