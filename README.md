# fossil

Independent reproductions of published computational papers. Each folder is one paper, named by its
PubMed Central ID. Each folder holds our code, our data, and our results. We do not redistribute the
papers or their supplements.

The list of papers, with each one's status, results page and code, is the front page of the site:
<https://jeonglab-bcm.github.io/fossil/>. This README does not list them, and neither does any shared
file: each paper's row is its own `PMC…/index.json`, which `tools/build_index.py` turns into the front
page when the site deploys ([`site/index.html`](site/index.html) is the template). A pull request that
adds or updates a paper touches only its own folder and its own workflow.

```sh
python3 tools/build_index.py                          # check every PMC…/index.json
python3 tools/build_index.py --out _site/index.html   # build the front page to look at it
python3 tools/index_row_to_json.py --ref origin/BRANCH PMC…   # move a branch's hand-written row into PMC…/index.json
```

The fields of `index.json` are listed at the top of `tools/build_index.py`.

Other analyses:

- [`availability-audit`](availability-audit/): what still works in 7,080 open-access bioinformatics and
  biomedical-informatics methodology papers from 2004–2015 (links, Wayback captures, repository
  accessions, supplementary files, and the software of a 150-paper sample), with a per-paper
  readiness tier for choosing reproduction targets.
- [`publication-trends`](publication-trends/): PMC articles per year (2000–2026) mentioning
  code hosts, R and Python ecosystems, DOI archives, data repositories, and software environment tools,
  as a proxy for when code and data sharing took hold.

Figures for the papers are in [`figures/`](figures/).

Each paper's `.github/workflows/reproduce-pmc….yml` (`reproduce.yml` for PMC4081639) reruns its
reproduction and checks the run against its `results.json`. What it reruns, and when, is in the
comments at the top of the workflow file.

## Results check

Each reproduction lists the results it stands on in `PMC…/figure-reproduction/results.json`. Each
entry gives:

- where the pipeline writes the value (a file under its output directory and a path into it);
- the value expected;
- how far a rerun may stray from it.

When a pull request creates or changes a reproduction's `results.json`, `.github/workflows/results-check.yml`
compares it with the outputs committed in the same pull request. Nothing is rerun, so it takes seconds.
It keeps one comment per reproduction on the pull request, with:

- what the pull request changes in `results.json` (a diff of expected values);
- any result that does not agree with the committed outputs (expected against committed);
- the full table;
- an overlay of each published figure with the committed render. Grey is where they agree within
  2 px, dark is only in the paper, and green is only in the render. Only renders the pull request
  changes are shown, or all of them when it adds `results.json`. The images live on the `ci-assets`
  branch.

The job fails if a value is missing or outside its tolerance. A full rerun, started by hand, is
checked against `results.json` in the same way.

```sh
python3 tools/check_results.py PMC4247685/figure-reproduction/results.json --committed               # against the committed outputs
python3 tools/check_results.py PMC4247685/figure-reproduction/results.json results --report results-check   # against a run
python3 tools/check_results.py PMC4247685/figure-reproduction/results.json results --update            # after an intended change
```

Each reproduction also names the [Paper2Repro](https://github.com/jeonglab-bcm/Paper2Repro) release
it was made with, in a `skill` block in `PMC…/results.json`. Papers made before that file existed keep
it in `PMC…/figure-reproduction/results.json`. Sessions write it with the skill's
`scripts/skill_version.py`. Blocks added afterwards say how the version was found (`source`:
`transcript`, `inferred`, `none` or `unknown`, with a `note`). The `skill` job in the same workflow
fails when a pull request adds a paper, or changes a paper's `results.json`, without a block whose
version is a `paper2repro-v…` tag of Paper2Repro.

The same job checks that every paper's block gives the front page's Paper2Repro column, and that
the front page builds. The column is written by `tools/build_index.py` from the block, never by hand.

```sh
python3 tools/check_skill.py --all                 # every paper
python3 tools/check_skill.py --base origin/main    # what this branch adds or changes
```

Values come from JSON (`"path": "pfs.p"`, or `"fig3.panel=a.published_within_2px"` to pick a list
item by a field), from CSV (`"column"`, `"where"`, `"agg"`), or as a file's SHA-256
(`"digest": "sha256"`). Paths are those of the pipeline's output directory; `"committed_paths"`
maps them to the committed layout where the two differ. A tolerance is `{"abs": …}`, `{"rel": …}` or both. Without one, the value
must be equal. Timings and other values that depend on the machine are left out.

## Ready for review

A reproduction pull request (one that adds or changes a `PMC…/results.json`) is opened as a draft and
stays one while the work goes on. `.github/workflows/ready-gate.yml` runs `tools/ready_gate.py` on every
push and when the PR is marked ready for review. Once the other checks have finished, it keeps one comment
on the PR that lists each condition:

- CI is green on the head commit, and the branch is up to date with `main` and has no conflicts, so CI ran
  on the current `main`;
- the results check finds the paper's `results.json`;
- a paper with a package shows the Install block (`tools/site_install.py`) on its results page;
- the AI review in the results-check comment is for the head commit and marks no item ⚠️;
- the PR body holds every row (item, verdict, measure) of `check_results.py --markdown`, so it was
  regenerated from `results.json` after the last change;
- every `review` block the PR adds or changes has a `reason` with a `kind` and a `text`. One already on
  `main` without a reason only gets a note until it is backfilled.

When a condition fails and the PR is not a draft, the gate moves it back to a draft. The gate never marks
a PR ready. A PR that changes no `results.json` is held only to the CI conditions.

```sh
python3 tools/ready_gate.py --pr 118 --dry-run   # what the gate would say (needs gh, signed in)
python3 tools/test_ready_gate.py                 # the gate's own tests
```

Run workflow on the Ready gate workflow, with "move open PRs to draft" set, moves every open, non-draft
reproduction PR to a draft with a comment that explains the gate. It is a dry run unless "dry run" is
turned off.
