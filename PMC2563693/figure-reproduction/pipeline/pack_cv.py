"""Pack per-repeat CV files (cv.py) into one gzip JSON per experiment, or check repeats against packs.

  pack_cv.py pack CVDIR OUTDIR        OUTDIR/<within|cross>/<name>.json.gz: {"repeats": [...]}
  pack_cv.py check CVDIR PACKDIR OUT.json
      every repeat file in CVDIR must equal the same repeat in PACKDIR (scores to 1e-9 relative,
      marker lists exactly); writes a report and exits 1 on any difference.
"""

from __future__ import annotations

import gzip
import json
import math
import sys
from pathlib import Path


def pack(cv: Path, out: Path):
    for kind in ("within", "cross"):
        for d in sorted((cv / kind).glob("*")):
            reps = [json.loads(p.read_text()) for p in sorted(d.glob("rep*.json"))]
            if not reps:
                continue
            (out / kind).mkdir(parents=True, exist_ok=True)
            with gzip.GzipFile(out / kind / f"{d.name}.json.gz", "wb", mtime=0) as f:
                f.write(json.dumps({"repeats": reps}, sort_keys=True).encode())


def load_pack(path: Path):
    with gzip.open(path, "rt") as f:
        return {r["repeat"]: r for r in json.load(f)["repeats"]}


def same(a, b, path=""):
    if isinstance(a, dict):
        if set(a) != set(b):
            return [f"{path}: keys differ"]
        return [m for k in a for m in same(a[k], b[k], f"{path}/{k}")]
    if isinstance(a, list):
        if len(a) != len(b):
            return [f"{path}: lengths differ"]
        return [m for i, (x, y) in enumerate(zip(a, b)) for m in same(x, y, f"{path}[{i}]")]
    if isinstance(a, float) or isinstance(b, float):
        if not (math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-12) or (math.isnan(a) and math.isnan(b))):
            return [f"{path}: {a} != {b}"]
        return []
    return [] if a == b else [f"{path}: {a!r} != {b!r}"]


def check(cv: Path, packs: Path, out: Path):
    report = {"checked": [], "differences": []}
    for kind in ("within", "cross"):
        for d in sorted((cv / kind).glob("*")):
            ref = load_pack(packs / kind / f"{d.name}.json.gz")
            for p in sorted(d.glob("rep*.json")):
                r = json.loads(p.read_text())
                diffs = same(r, ref[r["repeat"]])
                report["checked"].append(f"{kind}/{d.name}/{r['repeat']}")
                report["differences"] += [f"{kind}/{d.name}/{r['repeat']}{m}" for m in diffs[:5]]
    report["passed"] = bool(report["checked"]) and not report["differences"]
    out.write_text(json.dumps(report, indent=1))
    print(f"{len(report['checked'])} repeats rerun, {len(report['differences'])} differences")
    return report["passed"]


if __name__ == "__main__":
    if sys.argv[1] == "pack":
        pack(Path(sys.argv[2]), Path(sys.argv[3]))
    elif sys.argv[1] == "check":
        sys.exit(0 if check(Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4])) else 1)
