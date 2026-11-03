"""Check that each supplementary file named in a paper's XML is in the PMC dataset, intact, and opens.

Downloads each file from the PMC Article Datasets on AWS (s3://pmc-oa-opendata over HTTPS) to a
temporary file, compares its MD5 with the one PMC publishes in the article's JSON metadata and
with the object's own ETag (when only the JSON value differs, the file is intact and the metadata
is stale), checks the format by its magic bytes
or by opening it (zip, gzip, bzip2, tar, PDF, Office, images, text), and lists archive members (and members of
archives nested one level inside) to see whether the supplement carries source code. Files are deleted after checking.

Writes supplement_status.csv: one row per supplementary file.
"""
import bz2
import csv
import gzip
import hashlib
import io
import re
import sys
import tarfile
import tempfile
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

S3 = "https://pmc-oa-opendata.s3.amazonaws.com/"
OUT = Path("supplement_status.csv")
FIELDS = ["pmcid", "href", "ext", "bytes", "status", "detail", "has_code", "code_files", "build_files"]
CODE_EXT = {"r", "py", "pl", "pm", "m", "c", "cpp", "cc", "cxx", "h", "hpp", "java", "sh", "rb", "php", "js",
            "f", "f90", "f77", "for", "scala", "go", "rs", "jl", "ipynb", "rmd", "sas", "do", "awk", "tcl",
            "lua", "cs", "vb", "bas", "pro", "nb", "mat", "ml", "hs", "lisp", "el", "clj", "groovy", "kt",
            "swift", "jar", "class", "cu", "bat", "ps1", "mak", "cmake", "ijm", "sci", "sce", "wl", "q"}
BUILD = re.compile(r"(?i)(^|/)(makefile|cmakelists\.txt|setup\.py|pyproject\.toml|description|namespace|"
                   r"configure(\.ac|\.in)?|pom\.xml|build\.xml|build\.gradle|cargo\.toml|install|readme[^/]*)$")
TEXT_EXT = {"txt", "csv", "tsv", "tab", "html", "htm", "xml", "json", "fasta", "fa", "fas", "faa", "fna",
            "gff", "gtf", "bed", "vcf", "sam", "obo", "owl", "rdf", "nex", "nwk", "newick", "tre", "phy",
            "aln", "sdf", "mol2", "pdb", "sbml", "cys", "dat", "out", "log", "md", "tex", "bib", "sql", "yaml",
            "yml", "ini", "cfg", "conf", "svg", "rtf"} | (CODE_EXT - {"jar", "class", "mat", "nb"})
MAGIC = {
    "pdf": [b"%PDF"], "png": [b"\x89PNG"], "jpg": [b"\xff\xd8"], "jpeg": [b"\xff\xd8"], "gif": [b"GIF8"],
    "tif": [b"II*\x00", b"MM\x00*"], "tiff": [b"II*\x00", b"MM\x00*"], "bmp": [b"BM"],
    "eps": [b"%!PS", b"\xc5\xd0\xd3\xc6"], "ps": [b"%!PS"], "rar": [b"Rar!"], "7z": [b"7z\xbc\xaf"],
    "doc": [b"\xd0\xcf\x11\xe0"], "xls": [b"\xd0\xcf\x11\xe0"], "ppt": [b"\xd0\xcf\x11\xe0"],
    "avi": [b"RIFF"], "wav": [b"RIFF"], "mp3": [b"ID3", b"\xff\xfb", b"\xff\xf3"],
}
session = requests.Session()


def ext_of(name):
    n = name.lower()
    for multi in ("tar.gz", "tar.bz2"):
        if n.endswith("." + multi):
            return multi
    return n.rsplit(".", 1)[-1] if "." in n else ""


def code_in(names):
    code = [n for n in names if ext_of(n) in CODE_EXT and not n.startswith("__MACOSX")]
    build = [n for n in names if BUILD.search(n.rstrip("/"))]
    return code, build


def looks_text(head):
    if not head:
        return False
    if head.count(b"\x00") > len(head) // 100:
        return False
    try:
        head.decode("utf-8")
        return True
    except UnicodeDecodeError:
        return sum(32 <= b < 127 or b in (9, 10, 13) for b in head) > 0.85 * len(head)


def validate(path, ext):
    """Return (status, detail, member names) for the file at path."""
    size = path.stat().st_size
    if size == 0:
        return "empty", "", []
    with open(path, "rb") as f:
        head = f.read(8192)
        f.seek(max(0, size - 32768))
        tail = f.read()
    try:
        if zipfile.is_zipfile(path):
            with zipfile.ZipFile(path) as z:
                bad = z.testzip()
                names = z.namelist()
            return ("corrupt", f"bad member {bad}", names) if bad else ("ok", "zip", names)
        if ext in ("zip", "docx", "xlsx", "pptx", "jar", "odt", "ods"):
            if ext in ("xlsx", "docx") and head[:4] == b"\xd0\xcf\x11\xe0":
                return "ok", "OLE2 under a newer-format name", []
            return ("ok", "text under zip name", []) if looks_text(head) else ("corrupt", "not a zip", [])
        if head[:2] == b"\x1f\x8b":
            with gzip.open(path) as g:
                data = g.read(200_000_000)
            names = []
            try:
                with tarfile.open(fileobj=io.BytesIO(data)) as t:
                    names = t.getnames()
            except tarfile.TarError:
                pass
            return "ok", "gzip" + ("+tar" if names else ""), names
        if head[:3] == b"BZh":
            data = bz2.decompress(path.read_bytes())
            names = []
            try:
                with tarfile.open(fileobj=io.BytesIO(data)) as t:
                    names = t.getnames()
            except tarfile.TarError:
                pass
            return "ok", "bzip2" + ("+tar" if names else ""), names
        if ext in ("gz", "tgz", "tar.gz", "bz2", "tar.bz2"):
            return "corrupt", "compressed name but no gzip/bzip2 header", []
        if tarfile.is_tarfile(path):
            with tarfile.open(path) as t:
                return "ok", "tar", t.getnames()
        if ext == "pdf":
            if not head.startswith(b"%PDF"):
                return "corrupt", "no %PDF header", []
            return ("ok", "pdf", []) if b"%%EOF" in tail else ("corrupt", "pdf without %%EOF (truncated?)", [])
        if ext in ("mp4", "mov", "m4v", "3gp"):
            return ("ok", "iso media", []) if head[4:8] in (b"ftyp", b"moov", b"mdat", b"wide", b"free", b"skip") \
                else ("corrupt", "no ftyp/moov box", [])
        if ext in MAGIC:
            if any(head.startswith(m) for m in MAGIC[ext]):
                return "ok", ext, []
            if ext in ("xls", "doc") and looks_text(head):
                return "ok", "text/HTML under an Office name", []
            return "corrupt", f"magic mismatch for .{ext}", []
        if ext in TEXT_EXT:
            return ("ok", "text", []) if looks_text(head) else ("ok_binary", "binary under a text name", [])
        return "ok_unchecked", "unknown format", []
    except (zipfile.BadZipFile, OSError, EOFError, tarfile.TarError, ValueError, NotImplementedError,
            RuntimeError) as e:
        return "corrupt", f"{type(e).__name__}: {str(e)[:120]}", []


ARCHIVE = (".zip", ".tar", ".tar.gz", ".tgz", ".tar.bz2", ".tbz2", ".gz")


def nested_names(path, names, limit=200_000_000):
    """Member names of archives inside an archive (one level), prefixed with the outer member."""
    inner = [n for n in names if n.lower().endswith(ARCHIVE) and not n.startswith("__MACOSX")]
    out = []
    if not inner:
        return out
    try:
        if zipfile.is_zipfile(path):
            z = zipfile.ZipFile(path)
            read = lambda n: z.read(n) if z.getinfo(n).file_size < limit else b""  # noqa: E731
        else:
            t = tarfile.open(path)
            read = lambda n: (t.extractfile(n).read(limit) if t.extractfile(n) else b"")  # noqa: E731
        for n in inner[:20]:
            data = read(n)
            buf = io.BytesIO(data)
            try:
                if zipfile.is_zipfile(buf):
                    out += [f"{n}/{m}" for m in zipfile.ZipFile(buf).namelist()]
                else:
                    buf.seek(0)
                    with tarfile.open(fileobj=buf) as tt:
                        out += [f"{n}/{m}" for m in tt.getnames()]
            except (tarfile.TarError, zipfile.BadZipFile, OSError, EOFError):
                pass
    except (tarfile.TarError, zipfile.BadZipFile, OSError, EOFError, KeyError):
        pass
    return out


def check(row):
    name = row["href"].split("/")[-1]
    ext = ext_of(name)
    base = {"pmcid": row["pmcid"], "href": row["href"], "ext": ext}
    if row["in_dataset"] != "True":
        return {**base, "status": "not_in_dataset"}
    url = row["s3_url"].replace("s3://pmc-oa-opendata/", S3)
    with tempfile.NamedTemporaryFile(dir="cache", delete=True) as tmp:
        md5 = hashlib.md5()
        n = 0
        etag = ""
        for attempt in range(4):
            try:
                with session.get(url, stream=True, timeout=120) as r:
                    etag = r.headers.get("ETag", "").strip('"')
                    if r.status_code == 404:
                        return {**base, "status": "missing_in_bucket"}
                    r.raise_for_status()
                    tmp.seek(0)
                    tmp.truncate()
                    md5, n = hashlib.md5(), 0
                    for chunk in r.raw.stream(1 << 20, decode_content=False):
                        tmp.write(chunk)
                        md5.update(chunk)
                        n += len(chunk)
                break
            except requests.RequestException:
                if attempt == 3:
                    return {**base, "status": "download_error"}
        tmp.flush()
        stale = bool(row["md5"]) and md5.hexdigest() != row["md5"]
        if stale and md5.hexdigest() != etag:
            return {**base, "bytes": n, "status": "md5_mismatch"}
        status, detail, names = validate(Path(tmp.name), ext)
        if names:
            names += nested_names(Path(tmp.name), names)
        if stale:
            detail = (detail + "; " if detail else "") + "metadata MD5 stale, matches object ETag"
    code, build = code_in(names) if names else ([name] if ext in CODE_EXT else [], [])
    return {**base, "bytes": n, "status": status, "detail": detail, "has_code": bool(code),
            "code_files": len(code), "build_files": ";".join(build[:5])}


def main():
    Path("cache").mkdir(exist_ok=True)
    with open("supplements.csv") as f:
        rows = list(csv.DictReader(f))
    done = set()
    if OUT.exists():
        with open(OUT) as f:
            done = {(r["pmcid"], r["href"]) for r in csv.DictReader(f)}
    todo = [r for r in rows if (r["pmcid"], r["href"]) not in done]
    print(len(rows), "files;", len(todo), "to check", file=sys.stderr)
    new = not OUT.exists()
    with open(OUT, "a", newline="") as f, ThreadPoolExecutor(8) as ex:
        w = csv.DictWriter(f, FIELDS)
        if new:
            w.writeheader()
        for i, res in enumerate(ex.map(check, todo)):
            w.writerow(res)
            if i % 500 == 0:
                f.flush()
                print(i, file=sys.stderr, flush=True)


if __name__ == "__main__":
    main()
