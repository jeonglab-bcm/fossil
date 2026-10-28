"""Check whether each distinct URL from urls.csv still answers, and how.

One GET per URL (redirects followed, first 300 kB of HTML read), with a user agent that names this
project. No browser emulation: a site that refuses this client is recorded as refusing it, not as
dead. Per-host concurrency is capped at 2 with a short pause between requests.

github.com links are checked with `git ls-remote` instead: this session's proxy serves public
GitHub repositories to git but not github.com web pages. That tells whether the repository still
exists, not whether a deeper path in it does.

Two things a current browser does are done here too, and noted in the row:
- an http:// link whose server cannot be reached over HTTP is retried over HTTPS (Chrome and
  Firefox now upgrade http:// navigations to HTTPS first);
- when a server sends an incomplete certificate chain, the missing intermediate certificate is
  fetched from the URL in the server certificate's Authority Information Access field (AIA
  fetching) and the request is repeated with it. Verification stays on.
In this environment plain-HTTP requests pass through an egress gateway that answers 503
"upstream connect error" when it cannot reach the server; that is recorded as gateway_503, a
connection failure, not as the server's own 503.

Writes url_status.csv with the raw outcome; classify() in summarize.py turns it into categories.
Rerun with --retry to re-check transient failures (timeouts, connection errors, 5xx, 429); a
retry result replaces the earlier one only if it got further.
"""
import csv
import os
import re
import socket
import subprocess
import sys
import threading
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from urllib.parse import urljoin, urlsplit

import requests
import urllib3

urllib3.disable_warnings()  # only silences warnings; verification stays on
UA = "fossil-link-audit/0.1 (+https://github.com/jeonglab-bcm/fossil; checks links cited in published papers)"
HEADERS = {"User-Agent": UA, "Accept": "text/html,application/xhtml+xml,*/*;q=0.8"}
TIMEOUT = (15, 30)
MAX_BYTES = 300_000
OUT = Path("url_status.csv")
FIELDS = ["url", "outcome", "status", "final_url", "n_redirects", "cross_host", "to_root", "content_type",
          "bytes_read", "title", "flag", "meta_refresh", "error", "note", "checked_at"]
TRANSIENT = {"connect_fail", "timeout", "dns_error", "read_error", "proxy_502", "git_timeout", "git_error",
             "gateway_503", "tls_chain_incomplete"}
CONN_FAIL = {"connect_fail", "timeout", "proxy_502", "gateway_503"}
BASE_BUNDLE = os.environ.get("REQUESTS_CA_BUNDLE") or requests.certs.where()
PROXY = urlsplit(os.environ.get("HTTPS_PROXY", "")).netloc
AIA_DIR = Path("cache/aia")

TITLE_RE = re.compile(r"(?is)<title[^>]*>(.*?)</title>")
H1_RE = re.compile(r"(?is)<h[12][^>]*>(.*?)</h[12]>")
TAG_RE = re.compile(r"(?s)<script.*?</script>|<style.*?</style>|<[^>]+>")
REFRESH_RE = re.compile(r"""(?is)<meta[^>]+http-equiv=["']?refresh["']?[^>]*content=["']?\s*(\d+)\s*;\s*url=['"]?([^"'>\s]+)""")
SOFT404 = re.compile(r"(?i)\b(404|not found|cannot be found|could not be found|can't be found|does not exist|"
                     r"doesn't exist|error 404|file not found|object not found|page unavailable|no such page)\b")
PARKED = re.compile(r"(?i)(domain (name )?(is |may be )?for sale|buy this domain|this domain (has expired|is parked|"
                    r"may be for sale)|parked (free|domain)|sedoparking|hugedomains|domain parking|parkingcrew|"
                    r"bodis\.com|afternic|this web page is parked|is available for purchase|domain has expired)")
PARKING_HOSTS = ("hugedomains.com", "sedo.com", "dan.com", "afternic.com", "godaddy.com", "parkingcrew.net",
                 "bodis.com", "above.com", "namecheap.com", "domainmarket.com")
RETIRED = re.compile(r"(?i)(retired|discontinued|decommissioned|no longer (maintained|supported|available|in service|"
                     r"active|online)|has been (shut down|taken offline|removed|closed)|is (closed|offline))")
BOTCHECK = re.compile(r"(?i)(just a moment|attention required|checking your browser|recaptcha|"
                      r"pardon our interruption|are you a robot|access denied|ddos protection)")
MOVED = re.compile(r"(?i)(has moved|have moved|moved to|new home|new location|new address|relocated|"
                   r"now (located|hosted|available) at|please update your (bookmark|link))")

host_locks = defaultdict(lambda: threading.Semaphore(2))
git_lock = threading.Semaphore(4)
GITHUB_HOSTS = ("github.com", "www.github.com", "gist.github.com")
dns_cache = {}
local = threading.local()


def sess():
    if not hasattr(local, "s"):
        local.s = requests.Session()
        local.s.max_redirects = 15
    return local.s


def doh(host):
    """Second opinion from Google Public DNS over HTTPS: 'nxdomain', 'ok', or 'error'."""
    try:
        r = requests.get("https://dns.google/resolve", params={"name": host, "type": "A"}, headers=HEADERS,
                         timeout=20).json()
    except (requests.RequestException, ValueError):
        return "error"
    if r.get("Status") == 3:
        return "nxdomain"
    if r.get("Status") == 0 and r.get("Answer"):
        return "ok"
    return "nxdomain" if r.get("Status") == 0 else "error"  # NOERROR with no A record: nothing to reach


def dns(host):
    if host not in dns_cache:
        try:
            socket.getaddrinfo(host, None)
            dns_cache[host] = "ok"
        except socket.gaierror as e:
            local = "nxdomain" if e.errno in (socket.EAI_NONAME, -5) else "error"
            dns_cache[host] = doh(host) if local == "nxdomain" else local
        except UnicodeError:
            dns_cache[host] = "nxdomain"
    return dns_cache[host]


def text_of(html):
    return " ".join(unescape(TAG_RE.sub(" ", html)).split())


def analyse(html, final_url):
    title = text_of(TITLE_RE.search(html).group(1))[:150] if TITLE_RE.search(html) else ""
    heads = " ".join(text_of(h) for h in H1_RE.findall(html)[:3])[:300]
    body = text_of(html)[:4000]
    host = (urlsplit(final_url).hostname or "").lower()
    if BOTCHECK.search(title):
        flag = "bot_check"
    elif PARKED.search(body) or any(host.endswith(h) for h in PARKING_HOSTS):
        flag = "parked"
    elif SOFT404.search(title) or SOFT404.search(heads):
        flag = "soft404"
    elif RETIRED.search(title) or RETIRED.search(heads):
        flag = "retired_notice"
    elif MOVED.search(title) or MOVED.search(heads) or (len(body) < 1500 and MOVED.search(body)):
        flag = "moved_notice"
    else:
        flag = ""
    m = REFRESH_RE.search(html)
    refresh = urljoin(final_url, m.group(2)) if m and int(m.group(1)) <= 10 else ""
    return title, flag, refresh


def tls_kind(msg):
    m = msg.lower()
    if "expired" in m:
        return "tls_expired"
    if "hostname" in m or "doesn't match" in m or "not valid for" in m:
        return "tls_hostname"
    if "self-signed" in m or "self signed" in m:
        return "tls_self_signed"
    if "unable to get local issuer" in m:
        return "tls_chain_incomplete"
    return "tls_other"


def fetch(url, verify=True):
    """One GET; returns a dict of FIELDS (without url/checked_at)."""
    r0 = {"outcome": "", "status": "", "final_url": "", "n_redirects": 0, "cross_host": False, "to_root": False,
          "content_type": "", "bytes_read": 0, "title": "", "flag": "", "meta_refresh": "", "error": ""}
    try:
        r = sess().get(url, headers=HEADERS, timeout=TIMEOUT, stream=True, allow_redirects=True, verify=verify)
    except requests.exceptions.SSLError as e:
        return {**r0, "outcome": tls_kind(str(e)), "error": str(e)[-200:]}
    except requests.exceptions.ProxyError as e:
        kind = "proxy_403" if "403" in str(e) else "proxy_502" if "502" in str(e) else "connect_fail"
        return {**r0, "outcome": kind, "error": str(e)[-200:]}
    except requests.exceptions.TooManyRedirects as e:
        return {**r0, "outcome": "redirect_loop", "error": str(e)[-200:]}
    except requests.exceptions.ConnectTimeout as e:
        return {**r0, "outcome": "timeout", "error": str(e)[-200:]}
    except requests.exceptions.ReadTimeout as e:
        return {**r0, "outcome": "timeout", "error": str(e)[-200:]}
    except (requests.exceptions.InvalidURL, requests.exceptions.InvalidSchema, ValueError) as e:
        return {**r0, "outcome": "bad_url", "error": str(e)[-200:]}
    except requests.exceptions.ConnectionError as e:
        s = str(e)
        if "NameResolution" in s or "Name or service not known" in s:
            return {**r0, "outcome": "dns_fail", "error": s[-200:]}
        return {**r0, "outcome": "connect_fail", "error": s[-200:]}
    except Exception as e:  # noqa: BLE001
        return {**r0, "outcome": "other_error", "error": f"{type(e).__name__}: {str(e)[-180:]}"}
    if r.status_code == 503 and "server" not in r.headers and r.headers.get("content-type", "") == "text/plain":
        body = r.raw.read(200)
        r.close()
        if body.startswith(b"upstream connect error"):
            return {**r0, "outcome": "gateway_503", "final_url": r.url, "error": body.decode(errors="replace")}
        return {**r0, "outcome": "http", "status": 503, "final_url": r.url}
    out = dict(r0, outcome="http", status=r.status_code, final_url=r.url, n_redirects=len(r.history),
               content_type=r.headers.get("content-type", "")[:60])
    o, f = urlsplit(url), urlsplit(r.url)
    out["cross_host"] = (o.hostname or "").lower().removeprefix("www.") != (f.hostname or "").lower().removeprefix("www.")
    out["to_root"] = bool(r.history) and len(o.path.strip("/")) > 0 and f.path.strip("/") in (
        "", "index.html", "index.htm", "index.php", "home", "en")
    try:
        data = b""
        if "html" in out["content_type"].lower() or not out["content_type"]:
            for chunk in r.iter_content(16384):
                data += chunk
                if len(data) >= MAX_BYTES:
                    break
        else:
            data = next(r.iter_content(4096), b"")
        out["bytes_read"] = len(data)
        if data and ("html" in out["content_type"].lower() or data.lstrip()[:1] == b"<"):
            out["title"], out["flag"], out["meta_refresh"] = analyse(data.decode(r.encoding or "utf-8", "replace"), r.url)
    except Exception as e:  # noqa: BLE001
        out["error"] = f"read: {type(e).__name__}"
    finally:
        r.close()
    return out


def openssl(args, data=None, timeout=30):
    return subprocess.run(["openssl", *args], input=data, capture_output=True, timeout=timeout)


def aia_bundle(host):
    """Bundle of trusted roots plus intermediates fetched via AIA for host, or None."""
    AIA_DIR.mkdir(parents=True, exist_ok=True)
    out = AIA_DIR / f"{host}.pem"
    if out.exists():
        return str(out) if out.stat().st_size else None
    pems = []
    try:
        cmd = ["s_client", "-connect", f"{host}:443", "-servername", host, "-showcerts"]
        if PROXY:
            cmd[1:1] = ["-proxy", PROXY]
        chain = openssl(cmd, b"", 40).stdout.decode(errors="replace")
        leaf = re.search(r"-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----", chain, re.S)
        cert = leaf.group(0).encode() if leaf else b""
        for _ in range(3):
            text = openssl(["x509", "-noout", "-text"], cert).stdout.decode(errors="replace")
            m = re.search(r"CA Issuers - URI:(\S+)", text)
            if not m:
                break
            raw = requests.get(m.group(1), headers=HEADERS, timeout=30).content
            if b"-----BEGIN CERTIFICATE-----" in raw:
                pem = raw
            else:
                pem = openssl(["x509", "-inform", "DER", "-outform", "PEM"], raw).stdout or \
                    openssl(["pkcs7", "-inform", "DER", "-print_certs"], raw).stdout
            if not pem:
                break
            pems.append(pem.decode(errors="replace"))
            cert = pem
    except (subprocess.SubprocessError, requests.RequestException, OSError):
        pass
    if not pems:
        out.write_text("")
        return None
    out.write_text(Path(BASE_BUNDLE).read_text() + "\n" + "\n".join(pems))
    return str(out)


def git_check(url):
    p = urlsplit(url)
    parts = [x for x in p.path.split("/") if x]
    if (p.hostname or "").lower() == "gist.github.com":
        repo = f"https://gist.github.com/{parts[-1]}.git" if parts else ""
    else:
        repo = f"https://github.com/{parts[0]}/{parts[1].removesuffix('.git')}" if len(parts) >= 2 else ""
    if not repo:
        return {"outcome": "untestable_github", "final_url": ""}
    env = {"GIT_TERMINAL_PROMPT": "0", "PATH": "/usr/bin:/bin:/usr/local/bin", "HOME": str(Path.home())}
    with git_lock:
        try:
            r = subprocess.run(["git", "ls-remote", "--heads", repo], capture_output=True, text=True,
                               timeout=90, env=env)
        except subprocess.TimeoutExpired:
            return {"outcome": "git_timeout", "final_url": repo}
    if r.returncode == 0:
        return {"outcome": "git_ok", "final_url": repo, "bytes_read": len(r.stdout)}
    err = r.stderr.strip().splitlines()[-1] if r.stderr.strip() else ""
    gone = "could not read Username" in err or "not found" in err.lower()
    return {"outcome": "git_not_found" if gone else "git_error", "final_url": repo, "error": err[-200:]}


def check(url):
    p = urlsplit(url)
    host = (p.hostname or "").lower()
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    base = {"url": url, "checked_at": now}
    if p.scheme == "ftp":
        return {**base, "outcome": "untestable_ftp"}
    try:
        port = p.port
    except ValueError:
        return {**base, "outcome": "bad_url"}
    if port not in (None, 80, 443):
        return {**base, "outcome": "untestable_port"}
    if host in GITHUB_HOSTS:
        return {**base, **git_check(url)}
    d = dns(host)
    if d != "ok":
        return {**base, "outcome": "dns_fail" if d == "nxdomain" else "dns_error"}
    with host_locks[host]:
        res = fetch(url)
        time.sleep(0.3)
    if res["outcome"] == "tls_chain_incomplete":
        bad = re.search(r"host='([^']+)'", res["error"])
        bundle = aia_bundle(bad.group(1) if bad else host)
        if bundle:
            res2 = fetch(url, verify=bundle)
            if res2["outcome"] != "tls_chain_incomplete":
                res = {**res2, "note": "missing intermediate certificate fetched via AIA"}
    if res["outcome"] in CONN_FAIL and p.scheme == "http":
        res2 = fetch("https://" + url[len("http://"):])
        if res2["outcome"] == "http":
            res = {**res2, "note": f"reached over HTTPS after HTTP failed ({res['outcome']})"}
    # Follow one meta-refresh hop, as a browser would.
    if res.get("meta_refresh") and res["meta_refresh"] != url and res.get("status") == 200:
        nxt = fetch(res["meta_refresh"])
        if nxt["outcome"] == "http":
            nxt["n_redirects"] = res["n_redirects"] + 1 + nxt["n_redirects"]
            nxt["meta_refresh"] = res["meta_refresh"]
            o, f = urlsplit(url), urlsplit(nxt["final_url"])
            nxt["cross_host"] = (o.hostname or "").removeprefix("www.") != (f.hostname or "").removeprefix("www.")
            nxt["to_root"] = len(o.path.strip("/")) > 0 and f.path.strip("/") in ("", "index.html", "index.htm",
                                                                                  "index.php", "home", "en")
            res = nxt
    return {**base, **res}


def progress_rank(row):
    if row["outcome"] == "http":
        s = int(row["status"] or 0)
        return 4 if s < 400 else 3 if s in (404, 410) else 2
    return 1 if row["outcome"] in TRANSIENT else 2


def main(*args):
    retry = "--retry" in args
    with open("urls.csv") as f:
        urls = sorted({r["url"] for r in csv.DictReader(f)})
    done = {}
    if OUT.exists():
        with open(OUT) as f:
            done = {r["url"]: r for r in csv.DictReader(f)}
    if retry:
        todo = [u for u, r in done.items() if r["outcome"] in TRANSIENT | {"dns_fail"} or
                (r["outcome"] == "http" and (r["status"] in ("429", "408") or r["status"].startswith("5")))]
    else:
        todo = [u for u in urls if u not in done]
    print(len(urls), "urls;", len(todo), "to check", file=sys.stderr)
    # Interleave hosts so one big host does not hold all workers.
    by_host = defaultdict(list)
    for u in todo:
        by_host[urlsplit(u).hostname].append(u)
    order = [u for i in range(max(map(len, by_host.values()), default=0)) for h in by_host.values() if i < len(h)
             for u in [h[i]]]
    lock = threading.Lock()
    n = 0

    def run(u):
        nonlocal n
        row = check(u)
        with lock:
            n += 1
            old = done.get(u)
            if not retry or old is None or progress_rank(row) >= progress_rank(old):
                done[u] = row
            if n % 250 == 0:
                print(n, file=sys.stderr, flush=True)
                write(done)

    with ThreadPoolExecutor(32) as ex:
        list(ex.map(run, order))
    write(done)


def write(done):
    tmp = OUT.with_suffix(".tmp")
    with open(tmp, "w", newline="") as f:
        w = csv.DictWriter(f, FIELDS, extrasaction="ignore")
        w.writeheader()
        for u in sorted(done):
            w.writerow(done[u])
    tmp.replace(OUT)


if __name__ == "__main__":
    main(*sys.argv[1:])
