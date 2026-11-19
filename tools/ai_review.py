"""Plain-language AI review of the results.json items a pull request changes.

For each item of <paper>/results.json (schema paper2repro/results/v1) that the PR adds or changes,
Claude explains in simple words why the item matched the paper or not, using only what the
repository says: the paper's value and ours, the tolerance, the verdict, the cause and its tested
hypotheses, the assumptions and any reviewer note. It flags a verdict the evidence seems to
contradict. It changes no file; a normal approval of the PR is the final conclusion.

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
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "paper2repro"))
import check_results as p2r  # noqa: E402

MODEL = "claude-opus-5-5"
MATCHED = {"exact", "agrees"}
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
- Use only the evidence in the item: values, tolerances, the precomputed measure, assumptions, \
cause, hypotheses and their results, reviewer note, and the previous version when given. Never \
add a reason, fact or number that is not there. When the evidence does not say why, say so.
- Quote one or two concrete numbers (ours against the paper's, and the allowed band) when there \
are values. Say whether a cause is explained or still open.
- When the item changed, say in a short clause what changed (e.g. "verdict was partly").
- Set flag to true only when the evidence in the item itself points against its verdict: for \
example a "differs" whose own cause says the gap is within chance, a matched verdict that rests \
on a setting the item says was tuned to the paper, a reviewer verdict whose note contradicts the \
numbers, or a cause marked explained whose hypotheses were all rejected. Give the reason in \
flag_reason. Otherwise flag is false and flag_reason is "".
- one_line: at most 20 words. explanation: at most 90 words, no headings, no bullet lists.
- overview (only when asked for it): two or three sentences on which main claims hold and what \
mostly does not match; otherwise "".
- Return exactly one entry per item id given, in the same order."""

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
                },
                "required": ["id", "one_line", "explanation", "flag", "flag_reason"],
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
        out["fields_within_band"] = sum(p2r.field_matches(f, v.get("tolerance")) for f in fields)
        out["fields_outside_band"] = [f.get("name") for f in fields if not p2r.field_matches(f, v.get("tolerance"))]
    return out


def build_prompt(paper, head, pairs, new_paper):
    title = head.get("paper", {}).get("citation") or head.get("paper", {}).get("title", "")
    blocks = []
    for item, before in pairs:
        entry = {"item": item, "facts": facts(item)}
        if before is not None:  # only the keys this PR changes
            entry["previous_version"] = {k: before.get(k) for k in sorted(set(before) | set(item)) if before.get(k) != item.get(k)}
        blocks.append(f'<item id="{item["id"]}">\n{json.dumps(entry, indent=1, ensure_ascii=False)}\n</item>')
    ask = ("This pull request adds the reproduction, so every item is new. Also write the overview."
           if new_paper else
           f"This pull request changes these {len(pairs)} items. Leave overview empty.")
    return f"Paper {paper}: {title}\n\n{ask}\n\n" + "\n\n".join(blocks)


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


def verdict_cell(item):
    v = item.get("verdict", "?").replace("_", " ")
    r = item.get("review")
    return f"**{v}** (reviewer; computed {r['computed'].replace('_', ' ')})" if r else f"**{v}**"


def cell(s):
    return str(s).replace("|", "\\|").replace("\n", " ")


def render(paper, head, pairs, removed, answer, new_paper):
    entries = validate(answer, pairs)
    items = {i["id"]: i for i, _ in pairs}
    n_flag = sum(e["flag"] for e in entries)
    out = []
    if new_paper:
        s = head.get("summary", {})
        counts = ", ".join(f"{s[k]} {k.replace('_', ' ')}" for k in p2r.VERDICTS if s.get(k))
        out += [f"#### 🤖 AI review of {paper} (new: {len(pairs)} items)", "", f"**{counts}.**" if counts else ""]
        if answer.get("overview"):
            out += ["", answer["overview"]]
    else:
        out.append(f"#### 🤖 AI review of the {len(pairs)} item{'s' if len(pairs) != 1 else ''} this PR changes")
    out += ["", "| Item | Verdict | In one line | |", "| --- | --- | --- | --- |"]
    for e in entries:
        it = items[e["id"]]
        out.append(f"| {cell(it.get('label', e['id']))} | {verdict_cell(it)} | {cell(e['one_line'])} | {MARK_FLAG if e['flag'] else MARK_OK} |")
    if removed:
        out += ["", "Removed in this PR: " + ", ".join(f"`{r}`" for r in removed) + "."]
    out.append("")
    for e in entries:
        it = items[e["id"]]
        matched = it.get("verdict") in MATCHED
        if new_paper and matched and not e["flag"]:
            continue  # a new paper's matched items are table rows only
        why = "why it matched" if matched else ("why it wasn't scored" if it.get("verdict") == "not_attempted" else "why it did not fully match")
        head_ = f"{'⚠️ ' if e['flag'] else ''}<b>{cell(it.get('label', e['id']))}: {it.get('verdict', '?').replace('_', ' ')}</b>, {why}"
        body = e["explanation"]
        if e["flag"]:
            body += f"\n\n**Worth a look:** {e['flag_reason']}"
        if it.get("review", {}).get("url"):
            body += f"\n\nReview by {it['review'].get('by', '?')}: {it['review']['url']}"
        out += [f"<details><summary>{head_}</summary>", "", body, "</details>", ""]
    out.append("**Final conclusion:** approve this PR if you accept the verdicts above"
               + (f". Before approving, check the {n_flag} ⚠️ item{'s' if n_flag != 1 else ''}." if n_flag else "; nothing was flagged."))
    out.append("")
    out.append(f"<sub>Written by {MODEL} from this PR's results.json only; it changes no file. Check the numbers before relying on it.</sub>")
    return "\n".join(out)


def failure(reason):
    return "\n".join(["#### 🤖 AI review: ❌ not run", "", reason, "",
                      "The **AI review** step of this check failed. Re-run the job once the cause is fixed."])


def main():
    ap = argparse.ArgumentParser(description="Plain-language AI review of the results.json items a PR changes.")
    ap.add_argument("paper")
    ap.add_argument("--base", required=True, help="the PR's base branch")
    ap.add_argument("--out", default="results-check", help="folder for ai-review.md and ai-review.json")
    ap.add_argument("--dry-run", action="store_true", help="print the prompt; call nothing")
    ap.add_argument("--response", help="render this saved answer (JSON) instead of calling the API")
    args = ap.parse_args()

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

    prompt = build_prompt(args.paper, head, pairs, new_paper)
    if args.dry_run:
        print(SYSTEM, "\n\n---\n", prompt)
        return 0
    try:
        if args.response:
            with open(args.response) as f:
                answer = json.load(f)
        else:
            answer = call_claude(prompt)
        body = render(args.paper, head, pairs, removed, answer, new_paper)
        with open(json_path, "w") as f:
            json.dump({"paper": args.paper, "model": MODEL, "answer": answer}, f, indent=1, ensure_ascii=False)
        status = 0
    except (ReviewError, json.JSONDecodeError) as e:
        body, status = failure(f"Reason: {e}"), 1
    open(md_path, "w").write(body + "\n")
    print(body)
    return status


if __name__ == "__main__":
    sys.exit(main())
