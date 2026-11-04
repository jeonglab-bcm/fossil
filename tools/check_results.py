"""Check a reproduction's results.json against a fresh run of its pipeline.

results.json lists the results a reproduction stands on. Each entry says where a run writes the
value (a file under the run's output directory, and a path into it), the value expected, and how far
a rerun may stray from it. This script reads every value from the run and compares.

Where a value comes from (fields of an entry):
  file                 path under the run's output directory
  path                 for JSON: keys joined by dots; a number picks a list item, and key=value
                       picks the list item whose key equals value (fig3.panel=a.published_within_2px)
  column, where, agg   for CSV: the column, the rows whose columns equal the given values, and how
                       to reduce them when more than one row matches (count, sum, mean, min, max, list)
  digest: "sha256"     the file's SHA-256, for files that must come back byte for byte

How close it must come: tolerance {"abs": a, "rel": r} passes |observed - expected| <=
max(a, r * |expected|), element by element for lists. Without a tolerance a value must be equal.

Writes a Markdown table to stdout (CI adds it to the job summary) and, with --report DIR,
DIR/results-check.json and DIR/index.html, a page that draws each expected value against the
observed one. Exits 1 if a value is missing or outside its tolerance.

With --committed the values are read from the files committed beside results.json instead of a
run, after the prefix rewrites in results.json's "committed_paths" (for a reproduction whose
committed layout differs from its pipeline's output layout). Nothing is rerun.

Usage:
  python3 tools/check_results.py <results.json> --committed [--report DIR]
  python3 tools/check_results.py <results.json> <run output dir> [--report DIR]
  python3 tools/check_results.py <results.json> <run output dir> --update
      (writes the run's values into results.json as the new expected values)
"""
import argparse
import csv
import hashlib
import html
import json
import math
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


class Missing(Exception):
    pass


def pick(obj, path):
    for part in path.split(".") if path else []:
        if isinstance(obj, list):
            if "=" in part:
                k, v = part.split("=", 1)
                hits = [x for x in obj if isinstance(x, dict) and str(x.get(k)) == v]
                if not hits:
                    raise Missing(f"no item with {k} = {v}")
                obj = hits[0]
            else:
                try:
                    obj = obj[int(part)]
                except (ValueError, IndexError):
                    raise Missing(f"no item {part}")
        elif isinstance(obj, dict):
            if part not in obj:
                raise Missing(f"no key {part}")
            obj = obj[part]
        else:
            raise Missing(f"cannot go into {part}")
    return obj


def number(s):
    try:
        v = float(s)
    except ValueError:
        return s
    return int(v) if v.is_integer() and "." not in s and "e" not in s.lower() else v


def observe(entry, run, rewrites=None):
    rel = entry["file"]
    for old, new in (rewrites or {}).items():
        if rel.startswith(old):
            rel = new + rel[len(old):]
            break
    path = os.path.join(run, rel)
    if not os.path.exists(path):
        raise Missing(f"{entry['file']} not written by the run")
    if entry.get("digest") == "sha256":
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    if entry["file"].endswith(".csv"):
        with open(path, newline="") as f:
            rows = [r for r in csv.DictReader(f) if all(r.get(k) == str(v) for k, v in entry.get("where", {}).items())]
        col = entry["column"]
        if not rows or col not in rows[0]:
            raise Missing(f"no rows or no column {col}")
        vals = [number(r[col]) for r in rows]
        agg = entry.get("agg")
        if agg is None:
            if len(vals) != 1:
                raise Missing(f"{len(vals)} rows match; give an agg")
            return vals[0]
        if agg == "count":
            return len(vals)
        if agg == "list":
            return vals
        nums = [float(v) for v in vals]
        return {"sum": math.fsum, "mean": statistics.fmean, "min": min, "max": max}[agg](nums)
    with open(path) as f:
        return pick(json.load(f), entry.get("path", ""))


def compare(expected, observed, tol):
    """(passes, gap): gap is observed - expected for numbers, the largest such gap for lists."""
    a, r = (tol or {}).get("abs", 0), (tol or {}).get("rel", 0)

    def num_ok(e, o):
        return abs(o - e) <= max(a, r * abs(e)) + 1e-15 * abs(e)

    isnum = lambda v: isinstance(v, (int, float)) and not isinstance(v, bool)
    gap = lambda e, o: 0 if abs(o - e) <= 1e-12 * max(abs(e), abs(o)) else o - e  # rounding noise is no gap
    if isnum(expected) and isnum(observed):
        return num_ok(expected, observed), gap(expected, observed)
    if isinstance(expected, list) and isinstance(observed, list):
        if len(expected) != len(observed):
            return False, None
        if all(isnum(e) and isnum(o) for e, o in zip(expected, observed)):
            gaps = [gap(e, o) for e, o in zip(expected, observed)]
            return all(num_ok(e, o) for e, o in zip(expected, observed)), max(gaps, key=abs) if gaps else 0
        return expected == observed, None
    return expected == observed, None


def fmt(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, float):
        return f"{v:.6g}"
    if isinstance(v, list):
        return "[" + ", ".join(fmt(x) for x in v[:12]) + (", …" if len(v) > 12 else "") + "]"
    if isinstance(v, str) and len(v) == 64 and all(c in "0123456789abcdef" for c in v):
        return v[:12] + "…"
    return str(v)


def fmt_tol(t):
    if not t:
        return "equal"
    parts = []
    if t.get("abs"):
        parts.append(f"±{t['abs']:.3g}")
    if t.get("rel"):
        parts.append(f"±{t['rel'] * 100:.3g}%")
    return " or ".join(parts)


def main():
    ap = argparse.ArgumentParser(description="Check a reproduction's results.json against a fresh run of its pipeline.")
    ap.add_argument("results_json")
    ap.add_argument("run_dir", nargs="?", help="a run's output directory (omit with --committed)")
    ap.add_argument("--committed", action="store_true", help="read the files committed beside results.json")
    ap.add_argument("--report", help="directory for results-check.json and index.html")
    ap.add_argument("--update", action="store_true", help="write the run's values into results.json")
    args = ap.parse_args()

    with open(args.results_json) as f:
        spec = json.load(f)
    if args.committed:
        run_dir, rewrites, source = os.path.dirname(os.path.abspath(args.results_json)), spec.get("committed_paths", {}), "the committed files"
    elif args.run_dir:
        run_dir, rewrites, source = args.run_dir, {}, "this run"
    else:
        ap.error("give a run output directory or --committed")
    checked = []
    for e in spec["results"]:
        row = {k: e.get(k) for k in ("id", "label", "file", "expected", "tolerance")}
        try:
            row["observed"] = observe(e, run_dir, rewrites)
            ok, gap = compare(e["expected"], row["observed"], e.get("tolerance"))
            row.update(status="pass" if ok else "fail", gap=gap)
        except (Missing, KeyError, ValueError) as err:
            row.update(observed=None, status="missing", gap=None, why=str(err))
        checked.append(row)

    if args.update:
        for e, row in zip(spec["results"], checked):
            if row["status"] != "missing":
                e["expected"] = row["observed"]
        with open(args.results_json, "w") as f:
            json.dump(spec, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"Updated {sum(r['status'] != 'missing' for r in checked)} expected values in {args.results_json}")
        return
    observed_word = "Committed" if args.committed else "Observed"

    n_pass = sum(r["status"] == "pass" for r in checked)
    summary = f"{n_pass} of {len(checked)} results came back within tolerance."
    lines = [f"## {spec['paper']}: results.json against {source}", "", summary, "",
             f"| Result | Expected | {observed_word} | Gap | Allowed | Status |", "| --- | --- | --- | --- | --- | --- |"]
    for r in checked:
        status = {"pass": "within", "fail": "**outside**", "missing": f"**missing** ({r.get('why')})"}[r["status"]]
        gap = f"{r['gap']:+.3g}" if isinstance(r["gap"], (int, float)) else ""
        cells = [r["label"], fmt(r["expected"]), fmt(r["observed"]) if r["status"] != "missing" else "", gap, fmt_tol(r["tolerance"]), status]
        lines.append("| " + " | ".join(str(c).replace("|", "\\|") for c in cells) + " |")
    print("\n".join(lines))

    if args.report:
        os.makedirs(args.report, exist_ok=True)
        meta = {"paper": spec["paper"], "title": spec.get("title", ""), "summary": summary, "source": source,
                "commit": os.environ.get("GITHUB_SHA", "")[:12], "run": os.environ.get("GITHUB_RUN_ID", "")}
        with open(os.path.join(args.report, "results-check.json"), "w") as f:
            json.dump({"meta": meta, "results": checked}, f, indent=2, ensure_ascii=False)
        with open(os.path.join(HERE, "results-report.html")) as f:
            page = f.read()
        rows = []
        for i, r in enumerate(checked):
            obs = html.escape(fmt(r["observed"])) if r["status"] != "missing" else "none"
            gap = f"{r['gap']:+.3g}" if isinstance(r["gap"], (int, float)) else ""
            word = {"pass": "Within", "fail": "Outside", "missing": "Missing"}[r["status"]]
            rows.append(
                f'<tr data-status="{r["status"]}"><td>{html.escape(r["label"])}<span class="src">{html.escape(r["file"])}</span></td>'
                f'<td class="num">{html.escape(fmt(r["expected"]))}</td><td class="num">{obs}</td><td class="num">{gap}</td>'
                f'<td class="num">{html.escape(fmt_tol(r["tolerance"]))}</td><td class="strip" data-i="{i}"></td>'
                f'<td><span class="state" data-status="{r["status"]}">{word}</span></td></tr>')
        data = json.dumps({"meta": meta, "results": checked}, ensure_ascii=False).replace("</", "<\\/")
        page = (page.replace("__PAPER__", html.escape(spec["paper"]))
                    .replace("__OBSERVED__", observed_word)
                    .replace("__TITLE__", html.escape(spec.get("title", "")))
                    .replace("__SUMMARY__", html.escape(summary))
                    .replace("__ROWS__", "\n".join(rows))
                    .replace("__DATA__", data))
        with open(os.path.join(args.report, "index.html"), "w") as f:
            f.write(page)

    sys.exit(0 if n_pass == len(checked) else 1)


if __name__ == "__main__":
    main()
