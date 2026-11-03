"""For each URL that is not alive, ask the Internet Archive's Wayback Machine for a capture.

Source: the Wayback Availability API (https://archive.org/wayback/available), which returns the
capture closest to a given time. We ask for the capture closest to 1 July of the year the earliest
citing paper was published, so "archived" means the archive has some copy, and the timestamp shows
how close to publication it is. Three requests in flight at most, each worker pausing 1 s, backing
off on 429. Links from the abstract or availability-type sections (the papers' own resources) go
first; the rest follow in a fixed random order, so a run cut short still leaves a random sample.

Writes wayback.csv: url, archived, snapshot_timestamp, snapshot_status, snapshot_url.
"""
import csv
import random
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

from classify import catch_all_finals, classify

API = "https://archive.org/wayback/available"
OUT = Path("wayback.csv")
FIELDS = ["url", "archived", "snapshot_timestamp", "snapshot_status", "snapshot_url"]
S = requests.Session()
S.headers["User-Agent"] = "fossil-link-audit/0.1 (+https://github.com/jeonglab-bcm/fossil)"


def lookup(url, year):
    for attempt in range(5):
        try:
            r = S.get(API, params={"url": url, "timestamp": f"{year}0701"}, timeout=60)
            if r.status_code == 200:
                snap = r.json().get("archived_snapshots", {}).get("closest") or {}
                return {"url": url, "archived": bool(snap.get("available")),
                        "snapshot_timestamp": snap.get("timestamp", ""), "snapshot_status": snap.get("status", ""),
                        "snapshot_url": snap.get("url", "")}
            if r.status_code == 429:
                time.sleep(int(r.headers.get("Retry-After", 0) or 0) or 60)
                continue
        except (requests.RequestException, ValueError):
            pass
        time.sleep(2 ** attempt)
    return {"url": url, "archived": "", "snapshot_timestamp": "", "snapshot_status": "error", "snapshot_url": ""}


def main():
    with open("papers.csv") as f:
        year = {f"PMC{r['pmcid'].removeprefix('PMC')}": r["year"]
                for r in csv.DictReader(l for l in f if not l.startswith("#"))}
    first_year, own = {}, set()
    with open("urls.csv") as f:
        for r in csv.DictReader(f):
            first_year[r["url"]] = min(first_year.get(r["url"], "9999"), year[r["pmcid"]])
            if r["availability_section"] == "True":
                own.add(r["url"])
    with open("url_status.csv") as f:
        rows = list(csv.DictReader(f))
    ca = catch_all_finals(rows)
    todo = [r["url"] for r in rows if classify(r, ca)[0] not in ("alive", "moved")]
    done = set()
    if OUT.exists():
        with open(OUT) as f:
            done = {r["url"] for r in csv.DictReader(f) if r["snapshot_status"] != "error"}
    todo = [u for u in todo if u not in done]
    random.Random(2026).shuffle(todo)
    todo.sort(key=lambda u: u not in own)
    print(len(todo), "URLs to look up", file=sys.stderr)
    new = not OUT.exists()
    lock = threading.Lock()

    def one(u):
        res = lookup(u, first_year.get(u, "2010"))
        time.sleep(1.0)
        return res

    with open(OUT, "a", newline="") as f, ThreadPoolExecutor(3) as ex:
        w = csv.DictWriter(f, FIELDS)
        if new:
            w.writeheader()
        for i, res in enumerate(ex.map(one, todo)):
            with lock:
                w.writerow(res)
            if i % 20 == 0:
                f.flush()
                print(i, file=sys.stderr, flush=True)


if __name__ == "__main__":
    main()
