"""Plain-language AI review of the results.json items a pull request changes.

For each item of <paper>/results.json (schema paper2repro/results/v1) that the PR adds or changes,
Claude explains in simple words why the item matched the paper or not, using only what the
repository says: the paper's value and ours, the tolerance, the verdict, the cause and its tested
hypotheses, the assumptions and any reviewer note. It flags a verdict the evidence seems to
contradict. For a partly or inconclusive item it may suggest the verdict a named reviewer (default
hyunhwan-bcm) would likely give, citing one of that reviewer's past review blocks on the base branch. It changes no file; a normal approval of the PR is the final conclusion.

The prompt asks for plain text in the style of the STE80 Humanizer skill (80% of ASD-STE100), and
tools/ste80/ste_check.py checks the answer; its notes go to the log and ai-review.json only.

Writes <out>/ai-review.md (the section tools/pr_comment.py adds to the PR comment) and
<out>/ai-review.json. Exits 1 when the review could not be made (no API key, API error, an answer
that does not cover every changed item), after writing a section that says why.

Usage:
  python3 tools/ai_review.py <paper> --base main --out results-check      # in CI, ANTHROPIC_API_KEY set
  python3 tools/ai_review.py <paper> --base main --dry-run                # print the prompt only
  python3 tools/ai_review.py <paper> --base main --response answer.json   # render a saved answer
"""
import argparse
import json
import os
import re
import subprocess
import sys
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "paper2repro"))
sys.path.insert(0, os.path.join(HERE, "ste80"))
import check_results as p2r  # noqa: E402
import ste_check  # noqa: E402

MODEL = "claude-opus-5-5"
MATCHED = {"exact", "agrees"}
# Items can hold thousands of compared values. Above MAX_FIELDS the prompt carries a sample: up to
# SHOW_OUTSIDE values outside their band and SHOW_INSIDE inside it. The counts in "facts" stay exact.
MAX_FIELDS, SHOW_OUTSIDE, SHOW_INSIDE = 40, 25, 10
# The reviewer whose past review blocks teach the "likely reviewer verdict" (--reviewer to change).
REVIEWER = "hyunhwan-bcm"
# The Paper2Repro review page: ?r=owner/repo/pull/N shows a PR's figures, tables and numbers with
# decision buttons; #i-<item id> scrolls to one item.
REVIEW_PAGE = "https://jeonglab-bcm.github.io/Paper2Repro/"
SUGGEST_FOR = {"partly", "inconclusive"}  # the computed verdicts this reviewer has changed before
MARK_OK, MARK_FLAG = "✅", "⚠️ worth a look"

SYSTEM = """You review a scientific paper reproduction for the people approving a pull request. \
Many of them are biologists, not programmers. For each item you are given, explain in plain, \
short sentences why it matched the paper or why it did not.

What the verdicts mean (computed by a script from the numbers, never typed by hand):
- exact: every compared value is within its allowed band and no setting was fitted to the paper.
- agrees: every value is within its band, but a setting was read from a figure or found by \
search; or a pass/fail check passed; or a figure overlay scored above its threshold.
- partly: some values are within their band, some are not.
- differs: no value is within its band, or the check failed.
- inconclusive: a figure overlay scored no better than a deliberately near-miss control.
- not_attempted: nothing was compared; the cause says why.
A "review" block means a named person overruled the computed verdict ("computed" is what the \
numbers gave); the item's verdict is then the reviewer's.

Rules:
- Use only the evidence in the item: values, tolerances, the precomputed facts, assumptions, \
cause, hypotheses and their results, reviewer note, and the previous version when given. Never \
add a reason, fact or number that is not there. When the evidence does not say why, say so. \
When the values are a sample (values.note says so), take counts from facts, not from the sample.
- Quote one or two concrete numbers (ours against the paper's, and the allowed band) when there \
are values. Say whether a cause is explained or still open.
- When the item changed, say in a short clause what changed (e.g. "verdict was partly").
- Set flag to true only when the evidence in the item itself points against its verdict: for \
example a "differs" whose own cause says the gap is within chance, a matched verdict that rests \
on a setting the item says was tuned to the paper, a reviewer verdict whose note contradicts the \
numbers, or a cause marked explained whose hypotheses were all rejected. Give the reason in \
flag_reason. Otherwise flag is false and flag_reason is "".
- one_line: at most 20 words. explanation: at most 90 words, no headings, no bullet lists.

How to write (adapted from the STE80 Humanizer skill, MIT, github.com/Dodaios/ste80-humanizer: 80% of the way to ASD-STE100, Simplified Technical English):
- Start with the answer. No run-up ("Here's the thing"), no closing line that repeats the point.
- One idea per sentence. Two linked facts may share a sentence with "and" or "because". Keep sentences under about 25 words, and vary their length a little.
- Active voice. Name who acts: "our run gives", "the reviewer set", "the paper prints".
- Simple tenses. Put the action in the verb ("we chose", not "a choice was made").
- Plain words: use, show, help, check. Not utilize, leverage, robust, crucial, ensure, highlight, underscore, additionally.
- One term per thing. Say "allowed band" every time; do not swap in synonyms for variety.
- No "not X but Y" framing, no lists of three for rhythm, no dashes, no semicolons, no bold, no trailing "-ing" phrase such as ", highlighting the gap".
- Keep certainty as the item gives it: "likely" stays "likely", "open" stays open.
- Keep numbers, names and identifiers exactly as written.
- overview (only when asked for it): two or three sentences on which main claims hold and what \
mostly does not match; otherwise "".
- Return exactly one entry per item id given, in the same order.

Likely reviewer verdict:
- You get the past decisions of one reviewer as <precedent> entries: the item, what the numbers \
gave, what the reviewer set, the cause and the reviewer's note.
- For an item whose verdict is partly or inconclusive and that has no review block, compare it \
with the precedents. When one precedent has the same kind of gap (for example Monte Carlo noise, \
a gap of a few samples with no seeds given, figure resolution, or a setting the paper does not \
give), set likely_verdict to what that reviewer set, precedent to that precedent's key exactly, \
and likely_reason to one plain sentence that names the shared kind of gap.
- Be strict about "same kind of gap". A larger gap, a different cause, or a gap the precedent's \
note does not cover is not a match. When nothing matches, leave all three fields "".
- For every other item, leave all three fields "".
- The suggestion is advice for the reviewer. It never changes the verdict you explain."""

SCHEMA = {
    "type": "object",
    "properties": {
        "overview": {"type": "string"},
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "one_line": {"type": "string"},
                    "explanation": {"type": "string"},
                    "flag": {"type": "boolean"},
                    "flag_reason": {"type": "string"},
                    "likely_verdict": {"type": "string", "enum": ["", "agrees", "partly", "differs"]},
                    "precedent": {"type": "string"},
                    "likely_reason": {"type": "string"},
                },
                "required": ["id", "one_line", "explanation", "flag", "flag_reason",
                             "likely_verdict", "precedent", "likely_reason"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["overview", "items"],
    "additionalProperties": False,
}


class ReviewError(Exception):
    pass


def load_base(paper, base):
    r = subprocess.run(["git", "show", f"origin/{base}:{paper}/results.json"], capture_output=True, text=True)
    return json.loads(r.stdout) if r.returncode == 0 else None


def load_precedents(base, reviewer):
    """The reviewer's past review blocks in every <paper>/results.json on the base branch."""
    r = subprocess.run(["git", "ls-tree", "-d", "--name-only", f"origin/{base}"], capture_output=True, text=True)
    out = {}
    for paper in sorted(d for d in r.stdout.split() if d.startswith("PMC")):
        spec = load_base(paper, base)
        for it in (spec or {}).get("items", []):
            rv = it.get("review") or {}
            if rv.get("by") != reviewer:
                continue
            cause = it.get("cause") or {}
            out[f"{paper}/{it['id']}"] = {
                "label": it.get("label", ""), "numbers_gave": rv.get("computed"), "reviewer_set": rv.get("verdict"),
                "measure": facts(it).get("measure", ""), "cause": f"{cause.get('category')} ({cause.get('status')}): "
                + str(cause.get("summary", ""))[:400], "note": str(rv.get("note", ""))[:400], "url": rv.get("url", ""),
            }
    return out


def changed_items(head, base):
    """(items to review, removed item ids); every item when the PR adds results.json."""
    old = {i["id"]: i for i in (base or {}).get("items", [])}
    new = [i for i in head.get("items", []) if old.get(i["id"]) != i]
    removed = [i for i in old if i not in {x["id"] for x in head.get("items", [])}]
    return [(i, old.get(i["id"])) for i in new], removed


def facts(item):
    """Deterministic facts the model should not have to work out: the measure and each field's fit."""
    errors = []
    computed, measure = p2r.verdict_of(item, errors)
    out = {"computed_verdict": computed, "measure": measure}
    v = item.get("values") or {}
    fields = v.get("fields") or []
    if fields:
        outside = [f.get("name") for f in fields if not p2r.field_matches(f, v.get("tolerance"))]
        out["fields_total"] = len(fields)
        out["fields_within_band"] = len(fields) - len(outside)
        out["fields_outside_band"] = outside[:50] + ([f"... and {len(outside) - 50} more"] if len(outside) > 50 else [])
    return out


def sampled(item):
    """The item with its values cut to a sample when it holds more than MAX_FIELDS of them."""
    v = item.get("values") or {}
    fields = v.get("fields") or []
    if len(fields) <= MAX_FIELDS:
        return item
    tol = v.get("tolerance")
    outside = [f for f in fields if not p2r.field_matches(f, tol)][:SHOW_OUTSIDE]
    inside = [f for f in fields if p2r.field_matches(f, tol)][:SHOW_INSIDE]
    keep = {id(f) for f in outside + inside}
    item = dict(item)
    item["values"] = dict(v, fields=[f for f in fields if id(f) in keep],
                          note=f"a sample of {len(keep)} of the {len(fields)} values; the counts in facts cover all of them")
    return item


def build_prompt(paper, head, pairs, new_paper, precedents=None):
    title = head.get("paper", {}).get("citation") or head.get("paper", {}).get("title", "")
    blocks = []
    for item, before in pairs:
        entry = {"item": sampled(item), "facts": facts(item)}
        if before is not None:  # only the keys this PR changes
            prev = {k: before.get(k) for k in sorted(set(before) | set(item)) if before.get(k) != item.get(k)}
            if "values" in prev and len((before.get("values") or {}).get("fields") or []) > MAX_FIELDS:
                prev["values"] = {"note": "changed; too many values to list", "facts_before": facts(before)}
            entry["previous_version"] = prev
        blocks.append(f'<item id="{item["id"]}">\n{json.dumps(entry, indent=1, ensure_ascii=False)}\n</item>')
    ask = ("This pull request adds the reproduction, so every item is new. Also write the overview."
           if new_paper else
           f"This pull request changes these {len(pairs)} items. Leave overview empty.")
    prec = ""
    if precedents:
        prec = (f"Past decisions of reviewer {REVIEWER} ({len(precedents)}):\n\n" + "\n".join(
            f'<precedent key="{k}">{json.dumps({x: y for x, y in v.items() if x != "url"}, ensure_ascii=False)}</precedent>'
            for k, v in precedents.items()) + "\n\n")
    return f"{prec}Paper {paper}: {title}\n\n{ask}\n\n" + "\n\n".join(blocks)


def call_claude(prompt):
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise ReviewError("`ANTHROPIC_API_KEY` is not available to this run (a pull request from a fork gets no repository secrets).")
    import anthropic
    client = anthropic.Anthropic(max_retries=4)
    try:
        # Streaming: a new paper's review can be long. Server-side fallbacks re-run the request on
        # another model if a safety classifier declines it.
        with client.beta.messages.stream(
            model=MODEL,
            max_tokens=64000,
            system=SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            output_config={"effort": "high", "format": {"type": "json_schema", "schema": SCHEMA}},
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        ) as stream:
            msg = stream.get_final_message()
    except anthropic.APIStatusError as e:
        raise ReviewError(f"Claude API error {e.status_code}: {e.message}")
    except anthropic.APIConnectionError as e:
        raise ReviewError(f"could not reach the Claude API: {e}")
    if msg.stop_reason == "refusal":
        raise ReviewError("the model declined the request")
    if msg.stop_reason == "max_tokens":
        raise ReviewError("the answer was cut off at max_tokens")
    text = next((b.text for b in msg.content if b.type == "text"), None)
    if text is None:
        raise ReviewError("the answer has no text")
    return json.loads(text)


def validate(answer, pairs):
    want = [i["id"] for i, _ in pairs]
    got = [e.get("id") for e in answer.get("items", [])]
    if sorted(got) != sorted(want):
        missing, extra = sorted(set(want) - set(got)), sorted(set(got) - set(want))
        raise ReviewError(f"the answer does not cover the changed items exactly (missing {missing}, extra {extra})")
    by_id = {e["id"]: e for e in answer["items"]}
    return [by_id[i] for i in want]


def check_suggestions(entries, items, precedents):
    """Keep a likely verdict only for an unreviewed partly/inconclusive item that cites a real precedent."""
    dropped = []
    for e in entries:
        if not e.get("likely_verdict"):
            e["likely_verdict"] = e["precedent"] = e["likely_reason"] = ""
            continue
        it = items[e["id"]]
        ok = (it.get("verdict") in SUGGEST_FOR and not it.get("review") and e.get("precedent") in precedents
              and e["likely_verdict"] != it.get("verdict"))
        if not ok:
            dropped.append(f"{e['id']} ({e.get('likely_verdict')}, cites {e.get('precedent')!r})")
            e["likely_verdict"] = e["precedent"] = e["likely_reason"] = ""
    return dropped


def verdict_cell(item):
    v = item.get("verdict", "?").replace("_", " ")
    r = item.get("review")
    if not r:
        return f"**{v}**"
    return f"**{v}**<br><sub>set by {r.get('by', 'a reviewer')}; the numbers alone say {r['computed'].replace('_', ' ')}</sub>"


def style_notes(answer):
    """STE80 checker notes on each text the model wrote (a heuristic, for the log only)."""
    notes = []
    texts = [("overview", answer.get("overview", ""))]
    for e in answer.get("items", []):
        texts += [(f"{e['id']}.{k}", e.get(k, "")) for k in ("one_line", "explanation", "flag_reason", "likely_reason")]
    for where, text in texts:
        for f in ste_check.check(text, strict=False) if text else []:
            notes.append({"where": where, "rule": f.rule, "message": f.message, "excerpt": f.excerpt})
    return notes


def review_link(repo, pr, item_id=None):
    """The review page for a pull request, at one item when item_id is given; "" without repo and pr."""
    if not (repo and pr):
        return ""
    url = f"{REVIEW_PAGE}?r={repo}/pull/{pr}"
    return url + (f"#i-{urllib.parse.quote(str(item_id), safe='.-_')}" if item_id else "")


def precedent_review_link(p, key):
    """The review page at the precedent's item, from the pull request its review url names."""
    m = re.match(r"https://github\.com/([^/]+/[^/]+)/pull/(\d+)", p.get("url") or "")
    return review_link(m.group(1), m.group(2), key.split("/", 1)[1]) if m else ""


def cell(s):
    return str(s).replace("|", "\\|").replace("\n", " ")


def render(paper, head, pairs, removed, answer, new_paper, precedents=None, repo="", pr=""):
    precedents = precedents or {}
    entries = validate(answer, pairs)
    items = {i["id"]: i for i, _ in pairs}
    dropped = check_suggestions(entries, items, precedents)
    if dropped:
        print("dropped likely verdicts that cite no real precedent: " + "; ".join(dropped), file=sys.stderr)
    n_flag = sum(e["flag"] for e in entries)
    n_likely = sum(bool(e["likely_verdict"]) for e in entries)
    out = []
    if new_paper:
        s = head.get("summary", {})
        counts = ", ".join(f"{s[k]} {k.replace('_', ' ')}" for k in p2r.VERDICTS if s.get(k))
        out += [f"#### 🤖 AI review of {paper} (new: {len(pairs)} items)", "", f"**{counts}.**" if counts else ""]
        if answer.get("overview"):
            out += ["", answer["overview"]]
    else:
        out.append(f"#### 🤖 AI review of the {len(pairs)} item{'s' if len(pairs) != 1 else ''} this PR changes")
    page = review_link(repo, pr)
    if page:
        out += ["", f"To look closer, open this PR in the [review page]({page}). It shows each figure and table with its "
                "numbers, and lets you record a decision. Each item name below links to that item there."]
    out += ["", "| Item | Verdict | In one line | |", "| --- | --- | --- | --- |"]
    for e in entries:
        it = items[e["id"]]
        mark = MARK_FLAG if e["flag"] else MARK_OK
        if e["likely_verdict"]:
            mark += f"<br><sub>{REVIEWER} would likely say {e['likely_verdict']}</sub>"
        name = cell(it.get("label", e["id"]))
        if page:
            name = f"[{name}]({review_link(repo, pr, e['id'])})"
        out.append(f"| {name} | {verdict_cell(it)} | {cell(e['one_line'])} | {mark} |")
    if removed:
        out += ["", "Removed in this PR: " + ", ".join(f"`{r}`" for r in removed) + "."]
    out.append("")
    for e in entries:
        it = items[e["id"]]
        matched = it.get("verdict") in MATCHED
        if new_paper and matched and not e["flag"] and not e["likely_verdict"]:
            continue  # a new paper's matched items are table rows only
        why = "why it matched" if matched else ("why we did not score it" if it.get("verdict") == "not_attempted" else "why it did not fully match")
        head_ = f"{'⚠️ ' if e['flag'] else ''}<b>{cell(it.get('label', e['id']))}: {it.get('verdict', '?').replace('_', ' ')}</b>, {why}"
        body = e["explanation"]
        if e["flag"]:
            body += f"\n\n**Worth a look:** {e['flag_reason']}"
        if e["likely_verdict"]:
            p = precedents[e["precedent"]]
            ref = f"[{e['precedent']}]({p['url']})" if p.get("url") else e["precedent"]
            body += (f"\n\n**Likely reviewer verdict: {e['likely_verdict']}.** {e['likely_reason']} "
                     f"{REVIEWER} set {p['reviewer_set']} on {ref}, where the numbers gave {p['numbers_gave']}.")
            then = precedent_review_link(p, e["precedent"])
            if then and page:
                body += f" Compare the two in the review page: [this item]({review_link(repo, pr, e['id'])}), [the past one]({then})."
        if page:
            body += f"\n\n[See this item in the review page]({review_link(repo, pr, e['id'])})"
        if it.get("review", {}).get("url"):
            body += f"\n\n[Review by {it['review'].get('by', 'the reviewer')}]({it['review']['url']})"
        out += [f"<details><summary>{head_}</summary>", "", body, "</details>", ""]
    out.append("**Final conclusion:** approve this PR if you accept the verdicts above."
               + (f" First check the {n_flag} item{'s' if n_flag != 1 else ''} marked ⚠️." if n_flag else " The AI flagged nothing.")
               + (f" {n_likely} item{'s look like gaps' if n_likely != 1 else ' looks like a gap'} {REVIEWER} accepted before."
                  " To change a verdict, add a review block." if n_likely else ""))
    out.append("")
    out.append(f"<sub>{MODEL} wrote this from the PR's results.json only. It changes no file. Check the numbers before you rely on it.</sub>")
    return "\n".join(out)


def failure(reason):
    return "\n".join(["#### 🤖 AI review: ❌ not run", "", reason, "",
                      "The AI review step failed, so this check failed. Fix the cause, then run the job again."])


def main():
    ap = argparse.ArgumentParser(description="Plain-language AI review of the results.json items a PR changes.")
    ap.add_argument("paper")
    ap.add_argument("--base", required=True, help="the PR's base branch")
    ap.add_argument("--out", default="results-check", help="folder for ai-review.md and ai-review.json")
    ap.add_argument("--dry-run", action="store_true", help="print the prompt; call nothing")
    ap.add_argument("--response", help="render this saved answer (JSON) instead of calling the API")
    ap.add_argument("--reviewer", default=REVIEWER, help="GitHub login whose past review blocks guide the likely verdict")
    ap.add_argument("--repo", default="", help="owner/repo, for links to the review page")
    ap.add_argument("--pr", default="", help="the PR number, for links to the review page")
    args = ap.parse_args()
    globals()["REVIEWER"] = args.reviewer

    os.makedirs(args.out, exist_ok=True)
    md_path, json_path = os.path.join(args.out, "ai-review.md"), os.path.join(args.out, "ai-review.json")

    path = os.path.join(args.paper, "results.json")
    if not os.path.exists(path):
        body = f"#### 🤖 AI review\n{args.paper} has no paper-level results.json yet, so there are no verdicts to review."
        open(md_path, "w").write(body + "\n")
        print(body)
        return 0
    with open(path) as f:
        head = json.load(f)
    base = load_base(args.paper, args.base)
    new_paper = base is None
    pairs, removed = changed_items(head, base)

    if not pairs:
        body = "#### 🤖 AI review\nNo item's verdict, values, cause or review changes in this PR. There is nothing to review."
        if removed:
            body += "\n\nRemoved in this PR: " + ", ".join(f"`{r}`" for r in removed) + "."
        open(md_path, "w").write(body + "\n")
        print(body)
        return 0

    precedents = load_precedents(args.base, args.reviewer)
    print(f"{len(precedents)} past decisions by {args.reviewer} loaded", file=sys.stderr)
    prompt = build_prompt(args.paper, head, pairs, new_paper, precedents)
    if args.dry_run:
        print(SYSTEM, "\n\n---\n", prompt)
        return 0
    try:
        if args.response:
            with open(args.response) as f:
                answer = json.load(f)
        else:
            answer = call_claude(prompt)
        body = render(args.paper, head, pairs, removed, answer, new_paper, precedents, args.repo, args.pr)
        notes = style_notes(answer)
        with open(json_path, "w") as f:
            json.dump({"paper": args.paper, "model": MODEL, "answer": answer, "style_notes": notes}, f, indent=1, ensure_ascii=False)
        print(f"STE80 style check: {len(notes)} note(s) (a heuristic; not shown on the PR)", file=sys.stderr)
        for n in notes:
            print(f"  {n['where']}: {n['rule']}: {n['message']}", file=sys.stderr)
        status = 0
    except (ReviewError, json.JSONDecodeError) as e:
        body, status = failure(f"Reason: {e}"), 1
    open(md_path, "w").write(body + "\n")
    print(body)
    return status


if __name__ == "__main__":
    sys.exit(main())
