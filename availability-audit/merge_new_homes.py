"""Combine the registry pass (new_homes.csv) with the web search (cache/newhome/web_result_*.csv).

The web search was done by reading search results for each paper not settled by the registry pass;
its rows are kept in new_homes_web_search.csv. A paper's software counts as moved when a verified
home is reachable now. Papers the web search did not reach (its shared limit of searches ran out)
are marked "search pending". Writes software_new_homes.csv: one row per paper with RCR >= 1 whose cited
software link is dead (tiers D and E).
"""
import csv
import glob

KIND = [("github.com", "github"), ("gitlab", "gitlab"), ("bitbucket.org", "bitbucket"), ("sourceforge", "sourceforge"),
        ("bioconductor.org", "bioconductor"), ("cran.r-project.org", "cran"), ("pypi.org", "pypi")]


# Software that the automated supplement scan missed (RAR archive, binary, RData, scripts without
# code file extensions) but that the supplement caption and an inspection of the file show is there.
CODE_IN_SUPPLEMENT = {
    "PMC2206061": ("1471-2105-8-341-S5.rar", 'caption: "application and source code of miRFinder"'),
    "PMC3123239": ("1471-2105-12-202-S1.ZIP", 'caption: "Binary code with manual and examples" (Linux64 binary)'),
    "PMC2599889": ("pcbi.1000257.s001.zip", 'caption: "RData archive containing the complete collection of programs"'),
    "PMC3038154": ("1471-2105-12-28-S1.ZIP", 'caption: "FASIMU 2.2.1 release archive"'),
}


def kind_of(url):
    return next((k for host, k in KIND if host in url), "lab-site")


def main():
    reg = {r["pmcid"]: r for r in csv.DictReader(open("new_homes.csv"))}
    web = {}
    for path in sorted(glob.glob("cache/newhome/web_result_*.csv")):
        for r in csv.DictReader(open(path)):
            web[r["pmcid"]] = r
    if web:
        with open("new_homes_web_search.csv", "w", newline="") as f:
            w = csv.DictWriter(f, ["pmcid", "found", "new_home", "kind", "same_tool_evidence", "reachable", "note"])
            w.writeheader()
            w.writerows(web[k] for k in sorted(web))
    # Use the current tiers: a paper whose cited link was later found to work leaves the list.
    tier = {r["pmcid"]: r["tier"] for r in csv.DictReader(open("paper_audit.csv"))}
    out = []
    for pmcid, r in reg.items():
        if tier.get(pmcid) not in ("D", "E"):
            continue
        row = {"pmcid": pmcid, "year": r["year"], "rcr": r["rcr"], "title": r["title"], "dead_links": r["dead_links"]}
        live_reg = r["found"] == "True" and r["home_status"] in ("alive", "indeterminate")
        w = web.get(pmcid)
        if pmcid in CODE_IN_SUPPLEMENT:
            f, ev = CODE_IN_SUPPLEMENT[pmcid]
            row.update(outcome="moved, code is in the PMC supplement", new_home=f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/",
                       kind="pmc-supplement", source="supplement inspection", evidence=f"{f}; {ev}", note="")
        elif live_reg:
            row.update(outcome="moved, live home found", new_home=r["new_home"], kind=kind_of(r["new_home"]),
                       source=r["where"], evidence=r["evidence"], note=r["registry"])
        elif w and w["found"] == "yes" and w["reachable"] == "yes":
            row.update(outcome="moved, live home found", new_home=w["new_home"], kind=w["kind"], source="web search",
                       evidence=w["same_tool_evidence"], note=w["note"])
        elif w and "not web-searched" in w["note"].lower():
            row.update(outcome="search pending", new_home=w["new_home"] if w["found"] != "no" else "", kind=w["kind"],
                       source="web search (incomplete)", evidence=w["same_tool_evidence"], note=w["note"])
        elif w and w["found"] in ("yes", "unsure"):
            row.update(outcome="possible home, not confirmed", new_home=w["new_home"], kind=w["kind"],
                       source="web search", evidence=w["same_tool_evidence"], note=f"reachable: {w['reachable']}; {w['note']}")
        elif r["found"] == "True":
            row.update(outcome="registry entry only, its home is dead", new_home=r["new_home"], kind=kind_of(r["new_home"]),
                       source=r["where"], evidence=r["evidence"], note=(w or {}).get("note", ""))
        else:
            row.update(outcome="not found", new_home="", kind="", source="web search" if w else "",
                       evidence="", note=(w or {}).get("note", ""))
        out.append(row)
    with open("software_new_homes.csv", "w", newline="") as f:
        w = csv.DictWriter(f, ["pmcid", "year", "rcr", "title", "outcome", "new_home", "kind", "source", "evidence",
                               "note", "dead_links"])
        w.writeheader()
        w.writerows(sorted(out, key=lambda x: -float(x["rcr"])))
    from collections import Counter
    print(Counter(o["outcome"] for o in out))
    print(Counter(o["kind"] for o in out if o["outcome"].startswith("moved")))


if __name__ == "__main__":
    main()
