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


def check_python(paths):
    """Parse each file with Python 3.13's ast. Returns (failures, python2_markers, first error)."""
    code = ("import ast, sys\nbad = py2 = 0\nfirst = ''\nfor f in sys.argv[1:]:\n    try:\n"
            "        ast.parse(open(f, 'rb').read(), f)\n    except (SyntaxError, ValueError) as e:\n"
            "        bad += 1\n        m = str(e)\n"
            "        py2 += any(k in m for k in ('Missing parentheses', 'multiple exception types', 'leading zeros', "
            "'inconsistent use of tabs'))\n"
            "        first = first or m[:100]\nprint(bad, py2, first, sep='\\t')")
    out = subprocess.run([sys.executable, "-I", "-c", code, *paths], capture_output=True, text=True,
                         errors="replace", timeout=600).stdout.strip().split("\t")
    return int(out[0] or 0), int(out[1] or 0), (out[2] if len(out) > 2 else "")


def check_r(paths):
    """Parse each file with R's parse() (no evaluation). Returns (failures, first error)."""
    if not paths:
        return 0, ""
    expr = ('bad <- 0; first <- ""; for (f in commandArgs(TRUE)) { e <- try(parse(f, encoding="latin1"), silent=TRUE); '
            'if (inherits(e, "try-error")) { bad <- bad + 1; if (first == "") first <- conditionMessage(attr(e, "condition")) } }; '
            'cat(bad, gsub("[\\t\\n]", " ", substr(first, 1, 100)), sep="\\t")')
    out = subprocess.run(["Rscript", "-e", expr, *paths], capture_output=True, text=True, errors="replace",
                         timeout=600).stdout.strip().split("\t")
    return int(out[0] or 0), (out[1] if len(out) > 1 else "")


KNOWN_BREAK = re.compile(
    r"[‘'](u?int(8|16|32|64)_t|u?intptr_t|INT_MIN|INT_MAX|UINT_MAX|LONG_MAX|CHAR_BIT|SIZE_MAX|strlen|strcpy|strncpy|strcmp|"
    r"strcat|memcpy|memset|memmove|exit|malloc|calloc|realloc|free|abs|atoi|atof|qsort|rand|srand|printf|sprintf|"
    r"fprintf|fopen|fclose|std::\w+)[’'] (was not declared|does not name a type|is not a member of)"
    r"|conflicting types for [‘'](getline|getdelim|strdup|strndup|basename)[’']"
    r"|must use [‘']\.\*[’'] or [‘']->\*[’'] to call pointer-to-member function")


def check_c(root, files, csrc):
    incs = sorted({str(p.parent) for p in files if p.suffix in (".h", ".hpp", ".hh")})
    bad, lang, first = 0, 0, ""
    for p in csrc[:60]:
        comp = "gcc" if p.suffix == ".c" else "g++"
        cmd = [comp, "-fsyntax-only", "-w", *[f"-I{i}" for i in incs[:40]], str(p)]
        r = subprocess.run(cmd, capture_output=True, text=True, errors="replace", timeout=120)
        if r.returncode:
            bad += 1
            errs = [l for l in r.stderr.splitlines() if "error" in l]
            # Only errors caused by documented toolchain changes count as breakage: standard names no
            # longer pulled in by other headers (GCC 13 porting notes), glibc's POSIX getline, and old
            # pointer-to-member call syntax. Anything else may just be this file compiled outside its
            # build (missing defines, generated or external headers), so it stays inconclusive.
            if any(KNOWN_BREAK.search(e) for e in errs):
                lang += 1
            err = next((e for e in errs if "No such file" not in e), errs[0] if errs else "")
            first = first or re.sub(r"^.*?(fatal error|error): ", r"\1: ", err)[:110]
    return bad, lang, first


def java_targets(jars, classes):
    majors = set()
    for j in jars[:5]:
        try:
            with zipfile.ZipFile(j) as z:
                for n in [n for n in z.namelist() if n.endswith(".class")][:20]:
                    head = z.read(n)[:8]
                    if head[:4] == b"\xca\xfe\xba\xbe":
                        majors.add(struct.unpack(">H", head[6:8])[0])
        except (zipfile.BadZipFile, OSError, KeyError):
            pass
    for c in classes[:20]:
        head = c.read_bytes()[:8]
        if head[:4] == b"\xca\xfe\xba\xbe":
            majors.add(struct.unpack(">H", head[6:8])[0])
    return sorted(majors)


def static(src):
    """Identify the build system, then check every language present. Returns (system, check, detail)."""
    root = project_root(src)
    files = [p for p in root.rglob("*") if p.is_file() and "__MACOSX" not in p.parts and ".git" not in p.parts]
    names = {p.relative_to(root).as_posix().lower() for p in files}
    top = {n.split("/")[-1] for n in names if n.count("/") <= 1}
    desc = [p for p in files if p.name == "DESCRIPTION" and p.read_text(errors="ignore").startswith("Package:")]
    py = [str(p) for p in files if p.suffix == ".py"]
    rf = [str(p) for p in files if p.suffix in (".R", ".r")]
    csrc = [p for p in files if p.suffix in (".c", ".cc", ".cpp", ".cxx")]
    jars = [p for p in files if p.suffix == ".jar"]
    classes = [p for p in files if p.suffix == ".class"]
    system = ("R package" if desc else "autotools" if {"configure", "configure.ac", "configure.in"} & top
              else "CMake" if "cmakelists.txt" in top else "Python package" if {"setup.py", "pyproject.toml"} & top
              else "maven" if "pom.xml" in top else "ant" if "build.xml" in top
              else "make" if {"makefile", "gnumakefile"} & top else "")
    results, details = [], []
    if desc:
        text = desc[0].read_text(errors="ignore")
        deps = set()
        for field in ("Depends", "Imports", "LinkingTo"):
            m = re.search(rf"^{field}:(.*?)(?=^\S|\Z)", text, re.M | re.S)
            if m:
                deps |= {re.sub(r"\(.*?\)", "", d).strip() for d in m.group(1).split(",")}
        deps -= {"", "R"}
        missing = sorted(d for d in deps if d not in r_available())
        results.append(("R package", 10 ** 6, "fail" if missing else "pass"))
        details.append(f"R deps {len(deps)}, missing from today's CRAN/Bioconductor: {', '.join(missing) or 'none'}")
    if rf:
        bad, first = check_r(rf)
        results.append(("R", len(rf), "fail" if bad else "pass"))
        details.append(f"R: {bad} of {len(rf)} files fail to parse" + (f" ({first})" if first else ""))
    if py:
        bad, py2, first = check_python(py)
        results.append(("Python", len(py), "fail" if py2 else "inconclusive" if bad else "pass"))
        details.append(f"Python: {bad} of {len(py)} files do not parse as Python 3"
                       + (f", {py2} with Python 2 print/exec syntax" if py2 else "") + (f" ({first})" if first else ""))
    if csrc:
        bad, lang, first = check_c(root, files, csrc)
        results.append(("C/C++", len(csrc), "pass" if bad == 0 else "fail" if lang else "inconclusive"))
        details.append(f"C/C++: {bad} of {min(len(csrc), 60)} sources fail gcc -fsyntax-only, {lang} from a known "
                       f"compiler/libc change" + (f" ({first})" if first else ""))
    if jars or classes:
        majors = java_targets(jars, classes)
        results.append(("Java", len(jars) + len(classes), "pass" if majors else "inconclusive"))
        details.append("Java: targets " + ", ".join(JAVA.get(m, str(m)) for m in majors) if majors
                       else "Java: no readable class files")
    if not results:
        if any(p.suffix == ".m" for p in files):
            return "MATLAB", "n/a", "needs MATLAB"
        if any(p.suffix in (".pl", ".pm") for p in files):
            return system or "Perl scripts", "n/a", "Perl not checked (perl -c runs BEGIN blocks)"
        if any(p.suffix.lower() in (".exe", ".msi", ".dll") for p in files):
            return "Windows binary", "fail", "Windows-only"
        elf = [p for p in files if p.read_bytes()[:4] == b"\x7fELF"]
        if elf:
            bits = {"32-bit" if p.read_bytes()[4] == 1 else "64-bit" for p in elf}
            return "Linux binary", "n/a", f"prebuilt {'/'.join(sorted(bits))} ELF executable(s) only, no source"
        if any(p.suffix.lower() in (".rpm", ".deb") for p in files):
            return "Linux package", "n/a", "binary RPM/DEB package only"
        if any(p.suffix in (".gms", ".gams") or p.suffix.upper() == ".GMS" for p in files):
            return "GAMS model", "n/a", "needs GAMS"
        return system or "unknown", "n/a", f"{len(files)} files, no recognised sources"
    if not system:
        langs = [("R scripts", rf), ("Python scripts", py), ("C/C++ without build files", csrc),
                 ("Java", jars or classes)]
        system = next(n for n, v in langs if v)
    # The verdict follows the dominant language (most files; an R package's DESCRIPTION wins).
    check = max(results, key=lambda r: r[1])[2]
    return system, check, "; ".join(details)


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
