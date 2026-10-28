"""Static check of each sampled paper's software: can the source still be obtained, and does it
look buildable today? Runs none of the downloaded code.

For each row of install_sample.csv (see install_sample.py for the kinds):
  - package repositories (Bioconductor, CRAN, PyPI): is the package in today's release?
    (R's available.packages() with BiocManager's repositories; the PyPI JSON API)
  - everything else: obtain the source (git clone, Google Code archive, SourceForge latest file,
    direct download, or the PMC supplement), unpack it, identify the build system, and run checks
    that only read the code:
      Python   every .py file parses with Python 3.13's ast (Python 2-only syntax fails)
      R        every .R file parses with R 4.6's parse(); for a package, which Depends/Imports are
               missing from today's CRAN and Bioconductor
      Java     class-file major version inside jars (which Java release they target)
      C/C++    each source file passes `gcc/g++ -fsyntax-only` (no linking, no Makefile run)
Building and installing (install_sample.py) executes third-party code and is a separate step.

Writes inspect_results.csv; downloads go to cache/install/<pmcid>/ (not committed).
"""
import csv
import re
import shutil
import struct
import subprocess
import sys
import zipfile
from pathlib import Path

import requests

from install_sample import NO_INSTALL, WORK, obtain, project_root

FIELDS = ["pmcid", "kind", "artifact", "via", "obtained", "build_system", "static_check", "detail"]
PY_AST = ("import ast, sys\nbad = []\nfor f in sys.argv[1:]:\n    try:\n        ast.parse(open(f, 'rb').read(), f)\n"
          "    except (SyntaxError, ValueError) as e:\n        bad.append(f)\nprint(len(bad))")
JAVA = {45: "1.1", 46: "1.2", 47: "1.3", 48: "1.4", 49: "5", 50: "6", 51: "7", 52: "8", 53: "9", 54: "10", 55: "11",
        56: "12", 57: "13", 58: "14", 59: "15", 60: "16", 61: "17", 62: "18", 63: "19", 64: "20", 65: "21"}
_avail = {}


def r_available():
    if "pkgs" not in _avail:
        out = subprocess.run(["Rscript", "-e", 'p <- rownames(available.packages(repos=BiocManager::repositories())); '
                              'cat(p, sep="\\n")'], capture_output=True, text=True, timeout=600)
        base = subprocess.run(["Rscript", "-e", 'cat(rownames(installed.packages(priority="base")), sep="\\n")'],
                              capture_output=True, text=True, timeout=120)
        _avail["pkgs"] = set(out.stdout.split()) | set(base.stdout.split())
    return _avail["pkgs"]


def pypi(name):
    r = requests.get(f"https://pypi.org/pypi/{name}/json", timeout=60)
    if r.status_code != 200:
        return False, f"not on PyPI (HTTP {r.status_code})"
    info = r.json()["info"]
    return True, f"latest {info.get('version')}, requires_python={info.get('requires_python') or 'unspecified'}"


def static(src):
    root = project_root(src)
    files = [p for p in root.rglob("*") if p.is_file() and "__MACOSX" not in p.parts]
    rel = {p.relative_to(root).as_posix().lower() for p in files}
    top = {r for r in rel if "/" not in r}
    desc = [p for p in files if p.name == "DESCRIPTION" and p.read_text(errors="ignore").startswith("Package:")]
    if desc:
        text = desc[0].read_text(errors="ignore")
        deps = set()
        for field in ("Depends", "Imports", "LinkingTo"):
            m = re.search(rf"^{field}:(.*?)(?=^\S|\Z)", text, re.M | re.S)
            if m:
                deps |= {re.sub(r"\(.*?\)", "", d).strip() for d in m.group(1).split(",")}
        deps -= {"", "R"}
        missing = sorted(d for d in deps if d not in r_available())
        rfiles = [str(p) for p in files if p.suffix in (".R", ".r")]
        bad = parse_r(rfiles)
        ok = not missing and not bad
        return "R package", "pass" if ok else "fail", \
            f"{len(deps)} deps, missing today: {', '.join(missing) or 'none'}; {bad} of {len(rfiles)} R files fail to parse"
    py = [str(p) for p in files if p.suffix == ".py"]
    if py:
        bad = int(subprocess.run([sys.executable, "-I", "-c", PY_AST, *py], capture_output=True, text=True,
                                 timeout=300).stdout.strip() or 0)
        system = "Python package" if {"setup.py", "pyproject.toml"} & top else "Python scripts"
        return system, "pass" if bad == 0 else "fail", f"{bad} of {len(py)} .py files do not parse as Python 3"
    jars = [p for p in files if p.suffix == ".jar"]
    classes = [p for p in files if p.suffix == ".class"]
    if jars or classes:
        majors = set()
        for j in jars[:5]:
            try:
                with zipfile.ZipFile(j) as z:
                    for n in [n for n in z.namelist() if n.endswith(".class")][:20]:
                        head = z.read(n)[:8]
                        if head[:4] == b"\xca\xfe\xba\xbe":
                            majors.add(struct.unpack(">H", head[6:8])[0])
            except (zipfile.BadZipFile, OSError):
                pass
        for c in classes[:20]:
            head = c.read_bytes()[:8]
            if head[:4] == b"\xca\xfe\xba\xbe":
                majors.add(struct.unpack(">H", head[6:8])[0])
        if not majors:
            return "Java", "fail", "no readable class files"
        return "Java", "pass", "targets Java " + ", ".join(JAVA.get(m, str(m)) for m in sorted(majors))
    csrc = [p for p in files if p.suffix in (".c", ".cc", ".cpp", ".cxx")]
    if csrc:
        system = ("autotools" if "configure" in top or "configure.ac" in top else "CMake" if "cmakelists.txt" in top
                  else "make" if "makefile" in top else "C/C++ without build files")
        incs = sorted({str(p.parent) for p in files if p.suffix in (".h", ".hpp", ".hh")})
        bad, lang, first = 0, 0, ""
        for p in csrc[:60]:
            comp = "gcc" if p.suffix == ".c" else "g++"
            cmd = [comp, "-fsyntax-only", "-w", *[f"-I{i}" for i in incs[:40]], str(p)]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if r.returncode:
                bad += 1
                errs = [l for l in r.stderr.splitlines() if "error" in l]
                # A missing header (external library, or one the build generates) is inconclusive;
                # any other error means today's compiler rejects the code.
                if not errs or not all("No such file" in e for e in errs):
                    lang += 1
                err = next((e for e in errs if "No such file" not in e), errs[0] if errs else "")
                first = first or re.sub(r"^.*?(fatal error|error): ", r"\1: ", err)[:110]
        check = "pass" if bad == 0 else "fail" if lang else "inconclusive"
        return system, check, f"{bad} of {min(len(csrc), 60)} sources fail gcc -fsyntax-only, {lang} with a " \
            f"compiler error other than a missing header" + (f" (first: {first})" if first else "")
    rfiles = [str(p) for p in files if p.suffix in (".R", ".r")]
    if rfiles:
        bad = parse_r(rfiles)
        return "R scripts", "pass" if bad == 0 else "fail", f"{bad} of {len(rfiles)} R files fail to parse"
    if any(p.suffix == ".m" for p in files):
        return "MATLAB", "n/a", "needs MATLAB"
    if any(p.suffix in (".pl", ".pm") for p in files):
        return "Perl scripts", "n/a", "not checked (perl -c runs BEGIN blocks)"
    if any(p.suffix.lower() in (".exe", ".msi", ".dll") for p in files):
        return "Windows binary", "fail", "Windows-only"
    if any(p.suffix in (".gms", ".gams") for p in files):
        return "GAMS model", "n/a", "needs GAMS"
    return "unknown", "n/a", f"{len(files)} files, no recognised sources"


def parse_r(rfiles):
    if not rfiles:
        return 0
    expr = ('bad <- 0; for (f in commandArgs(TRUE)) { e <- try(parse(f), silent=TRUE); '
            'if (inherits(e, "try-error")) { bad <- bad + 1; message(f, ": ", conditionMessage(attr(e, "condition"))) } }; '
            'cat(bad)')
    out = subprocess.run(["Rscript", "-e", expr, "--args", *rfiles], capture_output=True, text=True, timeout=300)
    return int(out.stdout.strip() or 0)


def inspect(pmcid, kind, artifact, sub):
    res = {"pmcid": pmcid, "kind": kind, "artifact": artifact, "via": sub}
    if kind in NO_INSTALL:
        return {**res, "obtained": "no" if kind == "unavailable" else "n/a", "static_check": "n/a"}
    if kind in ("bioconductor", "cran"):
        ok = artifact in r_available()
        return {**res, "obtained": "yes" if ok else "no", "build_system": kind, "static_check": "n/a",
                "detail": "in today's release" if ok else "not in today's CRAN/Bioconductor"}
    if kind == "pypi":
        ok, detail = pypi(artifact)
        return {**res, "obtained": "yes" if ok else "no", "build_system": "pypi", "static_check": "n/a",
                "detail": detail}
    dest = WORK / pmcid / sub
    shutil.rmtree(dest, ignore_errors=True)
    dest.mkdir(parents=True)
    try:
        ok, detail = obtain(kind, artifact, dest, dest / "log.txt")
    except Exception as e:  # noqa: BLE001
        ok, detail = False, f"{type(e).__name__}: {str(e)[:120]}"
    if not ok:
        return {**res, "obtained": "no", "static_check": "n/a", "detail": detail}
    try:
        system, check, sdetail = static(dest / "src")
    except Exception as e:  # noqa: BLE001
        system, check, sdetail = "unknown", "n/a", f"{type(e).__name__}: {str(e)[:120]}"
    return {**res, "obtained": "yes", "build_system": system, "static_check": check,
            "detail": "; ".join(x for x in (detail, sdetail) if x)}


def main(only=None):
    with open("install_sample.csv") as f:
        rows = list(csv.DictReader(l for l in f if not l.startswith("#")))
    if only:
        rows = [r for r in rows if r["pmcid"] in only.split(",")]
    out = Path("inspect_results.csv")
    prev = {}
    if out.exists():
        with open(out) as f:
            prev = {r["pmcid"]: r for r in csv.DictReader(f)}
    for r in rows:
        kind, alt = r["kind"].strip(), (r.get("alt_kind") or "").strip()
        res = inspect(r["pmcid"], kind, (r["artifact"] or "").strip(), "primary")
        if res["obtained"] != "yes" and alt and alt not in NO_INSTALL:
            a = inspect(r["pmcid"], alt, (r["alt_artifact"] or "").strip(), "alternate")
            if a["obtained"] == "yes":
                res = {**a, "detail": f"primary {kind} not obtained; " + (a.get("detail") or "")}
        prev[r["pmcid"]] = res
        print(r["pmcid"], res["kind"], res["obtained"], res.get("build_system", ""), res["static_check"],
              (res.get("detail") or "")[:90], file=sys.stderr, flush=True)
        with open(out, "w", newline="") as f:
            w = csv.DictWriter(f, FIELDS, extrasaction="ignore")
            w.writeheader()
            w.writerows(prev.values())


if __name__ == "__main__":
    main(*sys.argv[1:])
