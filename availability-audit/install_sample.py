"""Try to obtain and install the software of each paper in install_sample.csv, as of today.

install_sample.csv records, for each sampled paper (see sample_candidates.py), the paper's primary
software artifact and an alternate (usually a PMC supplementary file with the code):
  kind      github | bitbucket | gitlab | sourceforge | googlecode | bioconductor | cran | pypi |
            download | supplement | webserver | unavailable | request | none
  artifact  repository URL, package name, direct download URL, or S3 key of the supplementary file
If the primary artifact cannot be obtained or installed, the alternate is tried and the row says so.

"Installs" means: the source can be obtained, and the build or install step a user would run
(R CMD INSTALL / BiocManager / pip / configure+make / cmake / make / ant / mvn) exits 0 within
20 minutes on Ubuntu 24.04 with current R 4.6, Bioconductor 3.23, Python 3.13, GCC 13, and
OpenJDK. For a prebuilt Java jar we check that its main class loads; for scripts without a build
system (Python, Perl) we check that every file compiles. We do not run the paper's analyses.

Writes install_results.csv and logs to cache/install/<pmcid>/{primary,alternate}/log.txt.
"""
import csv
import os
import re
import shutil
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path
from urllib.parse import urlsplit

import requests

WORK = Path("cache/install").resolve()
UA = "fossil-link-audit/0.1 (+https://github.com/jeonglab-bcm/fossil)"
TIMEOUT = 1200
S3 = "https://pmc-oa-opendata.s3.amazonaws.com/"
FIELDS = ["pmcid", "kind", "artifact", "obtained", "build_system", "installed", "failure", "detail", "via"]
NO_INSTALL = ("webserver", "none", "request", "unavailable", "")


def run(cmd, cwd, log, timeout=TIMEOUT, env=None):
    with open(log, "a") as f:
        f.write(f"\n$ {cmd if isinstance(cmd, str) else ' '.join(cmd)}  (cwd={cwd})\n")
        f.flush()
        try:
            p = subprocess.run(cmd, cwd=cwd, shell=isinstance(cmd, str), stdout=f, stderr=subprocess.STDOUT,
                               timeout=timeout, env={**os.environ, **(env or {})})
            f.write(f"[exit {p.returncode}]\n")
            return p.returncode
        except subprocess.TimeoutExpired:
            f.write("[timeout]\n")
            return "timeout"


def download(url, dest):
    with requests.get(url, headers={"User-Agent": UA}, stream=True, timeout=120, allow_redirects=True) as r:
        if r.status_code != 200:
            return r.status_code
        name = Path(urlsplit(r.url).path).name or "download"
        out = dest / name
        with open(out, "wb") as f:
            for c in r.iter_content(1 << 20):
                f.write(c)
    return out


def unpack(path, dest, nested=True):
    """Extract a zip or tar archive into dest; archives inside it are extracted once more, in place."""
    try:
        if zipfile.is_zipfile(path):
            with zipfile.ZipFile(path) as z:
                z.extractall(dest)
        elif tarfile.is_tarfile(path):
            with tarfile.open(path) as t:
                t.extractall(dest, filter="data")
        else:
            return False
    except (zipfile.BadZipFile, tarfile.TarError, OSError):
        return False
    if nested:
        for inner in [p for p in Path(dest).rglob("*") if p.is_file() and
                      p.name.lower().endswith((".zip", ".tar", ".tar.gz", ".tgz", ".tar.bz2"))]:
            if unpack(inner, inner.parent / (inner.name + "_unpacked"), nested=False):
                inner.unlink()
    return True


def project_root(src):
    """Descend through single-directory wrappers."""
    while True:
        kids = [k for k in src.iterdir() if not k.name.startswith((".", "__MACOSX"))]
        if len(kids) == 1 and kids[0].is_dir():
            src = kids[0]
        else:
            return src


def r_install(target, log, bioc=False):
    expr = (f'BiocManager::install("{target}", ask=FALSE, update=FALSE)' if bioc else
            f'install.packages("{target}")')
    code = run(["Rscript", "-e", f'{expr}; if (!requireNamespace("{target}", quietly=TRUE)) quit(status=1)'],
               WORK, log)
    return code


def build(src, log):
    """Detect the build system under src and run it. Returns (build_system, ok, detail)."""
    root = project_root(src)
    files = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}
    top = {f for f in files if "/" not in f}
    low = {f.lower() for f in top}
    desc = next((root / f for f in files if f.endswith("DESCRIPTION") and f.count("/") <= 1
                 and (root / f).read_text(errors="ignore").startswith("Package:")), None)
    if desc:
        pkg = desc.parent
        code = run(["Rscript", "-e",
                    f'remotes::install_local("{pkg}", dependencies=TRUE, upgrade="never", '
                    f'repos=BiocManager::repositories(), force=TRUE)'], WORK, log)
        name = re.search(r"^Package:\s*(\S+)", desc.read_text(errors="ignore"), re.M).group(1)
        ok = code == 0 and run(["Rscript", "-e", f'library({name})'], WORK, log) == 0
        return "R package", ok, ""
    if "setup.py" in low or "pyproject.toml" in low:
        venv = root / ".venv"
        run([sys.executable, "-m", "venv", str(venv)], root, log)
        code = run([str(venv / "bin/pip"), "install", "--no-input", "."], root, log)
        return "Python package", code == 0, ""
    if "configure" in low:
        c1 = run("chmod +x configure && ./configure", root, log)
        return "autotools", c1 == 0 and run("make -j4", root, log) == 0, ""
    if "cmakelists.txt" in low:
        b = root / "_build"
        b.mkdir(exist_ok=True)
        return "CMake", run("cmake .. && make -j4", b, log) == 0, ""
    if "makefile" in low or "gnumakefile" in low:
        return "make", run("make -j4", root, log) == 0, ""
    if "build.xml" in low:
        return "ant", run("ant", root, log) == 0, ""
    if "pom.xml" in low:
        return "maven", run("mvn -q -B package -DskipTests", root, log) == 0, ""
    jars = [f for f in files if f.endswith(".jar")]
    if jars:
        jar = root / sorted(jars, key=lambda j: (j.count("/"), len(j)))[0]
        with zipfile.ZipFile(jar) as z:
            man = z.read("META-INF/MANIFEST.MF").decode(errors="ignore") if "META-INF/MANIFEST.MF" in z.namelist() else ""
        main = re.search(r"Main-Class:\s*(\S+)", man)
        if not main:
            return "jar (library)", True, "no Main-Class; jar opens"
        code = run(["java", "-Djava.awt.headless=true", "-cp", str(jar), main.group(1), "--help"], root, log, 60)
        text = Path(log).read_text(errors="ignore")[-4000:]
        loads = "ClassNotFoundException" not in text and "UnsupportedClassVersion" not in text and \
            "NoClassDefFoundError" not in text
        return "jar", loads, "main class loads" if loads else "main class fails to load"
    py = [f for f in files if f.endswith(".py")]
    if py:
        code = run([sys.executable, "-m", "compileall", "-q", "."], root, log)
        return "Python scripts", code == 0, "py_compile under Python 3.13"
    pl = [f for f in files if f.endswith((".pl", ".pm"))]
    if pl:
        bad = 0
        for f in pl[:30]:
            bad += run(["perl", "-c", f], root, log, 60) != 0
        return "Perl scripts", bad == 0, f"{bad} of {min(len(pl), 30)} fail perl -c"
    if any(f.endswith(".m") for f in files):
        return "MATLAB", False, "requires MATLAB"
    if any(f.lower().endswith((".exe", ".msi", ".dll")) for f in files):
        return "Windows binary", False, "Windows-only"
    if any(f.endswith((".c", ".cpp", ".cc")) for f in files):
        srcs = " ".join(f for f in files if f.endswith((".c", ".cpp", ".cc")))
        return "C/C++ without build files", run(f"g++ -w -o _a.out {srcs} -lm", root, log) == 0, "compiled all sources"
    if any(f.endswith(".java") for f in files):
        return "Java sources", run("mkdir -p _cls && javac -nowarn -d _cls $(find . -name '*.java')", root,
                                   log) == 0, "javac all sources"
    if any(f.endswith((".R", ".r")) for f in files):
        bad = sum(run(["Rscript", "-e", f'invisible(parse("{f}"))'], root, log, 60) != 0
                  for f in files if f.endswith((".R", ".r")))
        return "R scripts", bad == 0, f"{bad} R files fail to parse"
    return "unknown", False, "no recognised build system or sources"


def obtain(kind, artifact, dest, log):
    """Fetch the source into dest. Returns (ok, detail)."""
    git_env = {"GIT_TERMINAL_PROMPT": "0"}
    if kind in ("github", "bitbucket", "gitlab"):
        p = urlsplit(artifact)
        parts = [x for x in p.path.split("/") if x][:2]
        repo = f"{p.scheme}://{p.hostname}/{parts[0]}/{parts[1].removesuffix('.git')}"
        code = run(["git", "clone", "--depth", "1", repo, str(dest / "src")], WORK, log, 600, git_env)
        return code == 0, "" if code == 0 else "clone failed (repository gone or private)"
    if kind == "googlecode":
        name = re.search(r"code\.google\.com/(?:archive/)?p/([^/#?]+)", artifact) or \
            re.search(r"([a-z0-9-]+)\.googlecode\.com", artifact)
        url = f"https://storage.googleapis.com/google-code-archive-source/v2/code.google.com/{name.group(1)}/source-archive.zip"
        out = download(url, dest)
        if isinstance(out, int):
            return False, f"Google Code archive HTTP {out}"
        (dest / "src").mkdir()
        return unpack(out, dest / "src"), "Google Code archive source-archive.zip"
    if kind == "sourceforge":
        proj = (re.search(r"sourceforge\.net/(?:projects|p)/([^/#?]+)", artifact) or
                re.search(r"([a-z0-9-]+)\.(?:sourceforge|sf)\.net", artifact)).group(1)
        # The project's file feed lists files newest first; take the newest source archive, else
        # the newest jar, else the newest file of any kind.
        rss = requests.get(f"https://sourceforge.net/projects/{proj}/rss?path=/", headers={"User-Agent": UA},
                           timeout=60)
        paths = re.findall(rf"<link>https://sourceforge\.net/projects/{re.escape(proj)}/files/(.+?)/download</link>",
                           rss.text) if rss.status_code == 200 else []
        if not paths:
            return False, f"SourceForge project has no files (feed HTTP {rss.status_code})"
        rank = lambda f: (0 if re.search(r"\.(tar\.gz|tgz|tar\.bz2?|tar\.xz|zip)$", f, re.I) else  # noqa: E731
                          1 if f.lower().endswith(".jar") else 2)
        pick = min(paths, key=lambda f: (rank(f), paths.index(f)))
        out = download(f"https://downloads.sourceforge.net/project/{proj}/{pick}", dest)
        if isinstance(out, int):
            return False, f"SourceForge download HTTP {out}"
        (dest / "src").mkdir()
        if not unpack(out, dest / "src"):
            shutil.move(str(out), dest / "src" / out.name)
        return True, f"SourceForge file {pick}"
    if kind in ("download", "supplement"):
        url = artifact if kind == "download" else S3 + artifact
        try:
            out = download(url, dest)
        except requests.RequestException as e:
            return False, f"download failed: {type(e).__name__}"
        if isinstance(out, int):
            return False, f"download HTTP {out}"
        (dest / "src").mkdir()
        if not unpack(out, dest / "src"):
            shutil.move(str(out), dest / "src" / out.name)
        return True, out.name
    return False, f"unknown kind {kind}"


def attempt(row, sub="primary"):
    pmcid, kind, artifact = row["pmcid"], row["kind"].strip(), row["artifact"].strip()
    dest = WORK / pmcid / sub
    shutil.rmtree(dest, ignore_errors=True)
    dest.mkdir(parents=True)
    log = dest / "log.txt"
    res = {"pmcid": pmcid, "kind": kind, "artifact": artifact}
    if kind in NO_INSTALL:
        return {**res, "obtained": "no" if kind == "unavailable" else "n/a", "installed": "n/a", "failure": kind}
    if kind in ("bioconductor", "cran", "pypi"):
        if kind == "pypi":
            run([sys.executable, "-m", "venv", str(dest / ".venv")], dest, log)
            code = run([str(dest / ".venv/bin/pip"), "install", "--no-input", artifact], dest, log)
        else:
            code = r_install(artifact, log, bioc=kind == "bioconductor")
        text = log.read_text(errors="ignore")
        unavailable = re.search(r"(?i)(is not available|No matching distribution|not available for this version)", text)
        return {**res, "obtained": "no" if unavailable else "yes", "build_system": kind,
                "installed": "yes" if code == 0 else "no",
                "failure": "" if code == 0 else "not in current repository" if unavailable else "install error"}
    ok, detail = obtain(kind, artifact, dest, log)
    if not ok:
        return {**res, "obtained": "no", "installed": "no", "failure": "source unavailable", "detail": detail}
    system, built, bdetail = build(dest / "src", log)
    return {**res, "obtained": "yes", "build_system": system, "installed": "yes" if built else "no",
            "failure": "" if built else "build/install error", "detail": "; ".join(x for x in (detail, bdetail) if x)}


def main(only=None):
    with open("install_sample.csv") as f:
        rows = [r for r in csv.DictReader(l for l in f if not l.startswith("#"))]
    if only:
        rows = [r for r in rows if r["pmcid"] in only.split(",")]
    out = Path("install_results.csv")
    prev = {}
    if out.exists():
        with open(out) as f:
            prev = {r["pmcid"]: r for r in csv.DictReader(f)}
    for r in rows:
        print(r["pmcid"], r["kind"], r["artifact"][:70], file=sys.stderr, flush=True)
        res = {**attempt(r), "via": "primary"}
        if res["installed"] != "yes" and r.get("alt_kind", "").strip() not in NO_INSTALL:
            alt = attempt({"pmcid": r["pmcid"], "kind": r["alt_kind"], "artifact": r["alt_artifact"]}, "alternate")
            if alt["installed"] == "yes" or res["obtained"] != "yes":
                res = {**alt, "via": "alternate", "detail": f"primary {r['kind']}: {res.get('failure', '')}; "
                       + (alt.get("detail") or "")}
        prev[r["pmcid"]] = res
        print("   ->", prev[r["pmcid"]]["installed"], prev[r["pmcid"]].get("failure", ""), file=sys.stderr, flush=True)
        with open(out, "w", newline="") as f:
            w = csv.DictWriter(f, FIELDS)
            w.writeheader()
            w.writerows(prev.values())


if __name__ == "__main__":
    main(*sys.argv[1:])
