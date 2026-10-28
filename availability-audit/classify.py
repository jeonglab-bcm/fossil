"""Turn raw check_urls.py outcomes into availability categories.

alive          answers with content (2xx after redirects), or the GitHub repository still exists
moved          answers with a "this has moved / new home" notice
gone           404/410, soft 404, parked or expired domain, "retired" notice, redirect to a site's home
               page or to a catch-all page, domain no longer in DNS, GitHub repository deleted
unreachable    host resolves but does not answer properly: connection refused/reset, timeout, 5xx,
               redirect loop, invalid TLS certificate (expired, wrong host, self-signed); http:// links
               count only if HTTPS fails too
indeterminate  the site answered but refused this client (401/403/429, bot check), the TLS chain is
               incomplete (most browsers repair this), other 4xx, or a transient DNS/git error
untestable     ftp://, non-standard ports, GitHub user/org pages: this environment cannot reach them
"""
from collections import defaultdict
from urllib.parse import urlsplit

CATEGORIES = ["alive", "moved", "gone", "unreachable", "indeterminate", "untestable"]


def catch_all_finals(rows, min_sources=3):
    """Final URLs that many different deep links redirect to: a site's generic landing page."""
    sources = defaultdict(set)
    for r in rows:
        if r["outcome"] == "http" and r["final_url"] and r["n_redirects"] not in ("0", 0, ""):
            o = urlsplit(r["url"])
            if o.path.strip("/"):
                sources[r["final_url"]].add((o.hostname, o.path.rstrip("/")))
    return {f for f, s in sources.items()
            if len(s) >= min_sources and urlsplit(f).path.strip("/").count("/") <= 1}


def classify(r, catch_all=frozenset()):
    o = r["outcome"]
    if o == "git_ok":
        return "alive", "GitHub repository exists"
    if o == "git_not_found":
        return "gone", "GitHub repository not found"
    if o in ("git_error", "git_timeout", "dns_error", "proxy_403", "tls_chain_incomplete"):
        return "indeterminate", o
    if o in ("untestable_ftp", "untestable_port", "untestable_github", "bad_url"):
        return "untestable", o
    if o == "dns_fail":
        return "gone", "domain not in DNS"
    if o in ("connect_fail", "proxy_502", "gateway_503", "timeout", "redirect_loop", "other_error"):
        return "unreachable", o
    if o.startswith("tls_"):
        return "unreachable", o
    if o != "http":
        return "indeterminate", o
    s = int(r["status"] or 0)
    flag = r.get("flag", "")
    if s in (404, 410):
        return "gone", f"HTTP {s}"
    if s in (401, 403, 407, 429, 451) or flag == "bot_check":
        return "indeterminate", f"HTTP {s}" + (" bot check" if flag == "bot_check" else "")
    if s >= 500:
        return "unreachable", f"HTTP {s}"
    if s >= 400:
        return "indeterminate", f"HTTP {s}"
    if flag in ("soft404", "parked", "retired_notice"):
        return "gone", flag
    if r.get("to_root") in (True, "True"):
        return "gone", "redirected to home page"
    if r["final_url"] in catch_all:
        return "gone", "redirected to catch-all page"
    if flag == "moved_notice":
        return "moved", flag
    return "alive", "cross-host redirect" if r.get("cross_host") in (True, "True") else "ok"
