"""Draw the install-test sample and list each paper's candidate software artifacts.

Stratified random sample: 50 papers from each of 2004-2007, 2008-2011, 2012-2015 (seed 2026).
For each paper, lists URLs from the abstract or availability-type sections, code-host URLs anywhere
in the body, and supplementary files that hold source code. We then read these and record each
paper's primary software artifact by hand in install_sample.csv.
"""
import csv
import random
import re

CODE_HOST = re.compile(r"(?i)github\.com|sourceforge\.net|code\.google\.com|bitbucket\.org|bioconductor\.org|"
                       r"cran\.r-project\.org|pypi\.(python\.)?org|cpan\.org|gitlab\.com|launchpad\.net|"
                       r"savannah|codeplex|googlecode")
with open("papers.csv") as f:
    papers = list(csv.DictReader(l for l in f if not l.startswith("#")))
for p in papers:
    p["pmcid"] = "PMC" + p["pmcid"].removeprefix("PMC")
    y = int(p["year"])
    p["band"] = "2004-2007" if y <= 2007 else "2008-2011" if y <= 2011 else "2012-2015"
rng = random.Random(2026)
sample = []
for band in ("2004-2007", "2008-2011", "2012-2015"):
    pool = sorted((p for p in papers if p["band"] == band), key=lambda p: p["pmcid"])
    sample += rng.sample(pool, 50)
urls = {}
with open("urls.csv") as f:
    for r in csv.DictReader(f):
        urls.setdefault(r["pmcid"], []).append(r)
code_supp = {}
with open("supplements.csv") as f:
    supp = {(r["pmcid"], r["href"]): r for r in csv.DictReader(f)}
try:
    with open("supplement_status.csv") as f:
        for r in csv.DictReader(f):
            if r.get("has_code") == "True":
                code_supp.setdefault(r["pmcid"], []).append(r["href"])
except FileNotFoundError:
    pass
with open("cache/install_candidates.csv", "w", newline="") as f:
    w = csv.DictWriter(f, ["pmcid", "year", "band", "journal", "title", "avail_urls", "code_host_urls",
                           "supp_code"])
    w.writeheader()
    for p in sample:
        us = urls.get(p["pmcid"], [])
        avail = [u["url"] for u in us if u["availability_section"] == "True"]
        code = [u["url"] for u in us if CODE_HOST.search(u["url"]) and u["url"] not in avail]
        w.writerow({"pmcid": p["pmcid"], "year": p["year"], "band": p["band"], "journal": p["journal"],
                    "title": p["title"][:120], "avail_urls": " | ".join(avail[:6]),
                    "code_host_urls": " | ".join(code[:4]), "supp_code": " | ".join(code_supp.get(p["pmcid"], [])[:3])})
print(len(sample))
