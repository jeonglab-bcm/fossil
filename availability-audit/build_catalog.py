"""Build the paper catalog: one row per paper with the audit's tags and citation metrics.

Joins papers.csv, paper_audit.csv, url_audit.csv, data_candidates.csv, install_sample.csv,
inspect_results.csv and citations.csv. Writes paper_catalog.csv and paper_catalog.xlsx (Papers,
Columns and Data Sources tabs; filters and a frozen header on Papers; opens in Google Sheets).
"""
import csv
import sys
from collections import defaultdict
from pathlib import Path

from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

sys.path.insert(0, str(Path(__file__).parent))
from summarize import TIERS, sample_outcome  # noqa: E402

TIER_TAG = {"A": "code:in-supplement", "B": "code:repository-live", "C": "code:own-site-live",
            "D": "code:lost-archived", "E": "code:lost", "F": "code:unclear", "G": "code:no-link"}
LOW_RCR, HIGH_RCR = 0.25, 2.0  # median RCR in this set is 0.48; below 0.25 is about 30% of it
COLUMNS = [  # (name, description)
    ("pmcid", "PubMed Central ID; links to the article"),
    ("pmid", "PubMed ID"),
    ("doi", "DOI"),
    ("year", "Publication year (PubMed)"),
    ("journal", "Journal (NLM abbreviation)"),
    ("title", "Article title"),
    ("tier", "Reproduction readiness tier A-G (first match): see the tier table in README.md"),
    ("tier_meaning", "What the tier means"),
    ("tags", "Semicolon-separated tags for filtering; see the tag list below"),
    ("own_links", "Links in the abstract or availability-type sections (the paper's own resources)"),
    ("own_links_reachable", "Of those, reachable today (October 2026)"),
    ("own_links_dead", "Of those, gone or not answering"),
    ("dead_own_links_archived", "Of the dead own links, how many have a Wayback Machine capture"),
    ("code_in_supplement", "TRUE if a PMC supplementary file contains source code"),
    ("data_supplement_mb", "Size of data-type supplementary files in PMC (MB), when the code is unavailable"),
    ("input_data_captions", "Supplement captions describing input data (dataset, benchmark, training/test set)"),
    ("live_repository_accessions", "GEO/ArrayExpress/SRA accessions cited that still resolve"),
    ("accessions_not_resolving", "Cited accessions now obsolete or not found"),
    ("sample_outcome", "For the 150-paper software sample only: what happened to the paper's software"),
    ("icite_citations", "Citations (NIH iCite)"),
    ("icite_rcr", "Relative Citation Ratio (iCite): citations per year relative to papers in the same field; 1.0 = NIH-funded median"),
    ("icite_nih_percentile", "RCR percentile among NIH-funded papers (iCite)"),
    ("icite_citations_per_year", "Citations per year (iCite)"),
    ("icite_expected_per_year", "Expected citations per year for the paper's field (iCite)"),
    ("europepmc_cited_by", "Citations (Europe PMC)"),
    ("pmc_citing", "PMC articles citing the paper (NCBI elink pubmed_pmc_refs)"),
    ("oa_cited_by", "Citations (OpenAlex)"),
    ("oa_cited_by_last5y", "OpenAlex citations in the last five complete years"),
    ("oa_fwci", "Field-weighted citation impact (OpenAlex); 1.0 = world average for the field and year"),
    ("oa_citation_percentile", "Field- and year-normalized citation percentile (OpenAlex), 0-1"),
    ("oa_topic", "OpenAlex primary topic"),
    ("oa_subfield", "OpenAlex subfield of the primary topic"),
    ("oa_keywords", "OpenAlex keywords"),
    ("mesh_major", "MeSH major topics (PubMed), check tags removed"),
]
TAGS = [
    ("code:in-supplement ... code:no-link", "The readiness tier as a tag (A in-supplement, B repository-live, "
     "C own-site-live, D lost-archived, E lost, F unclear, G no-link)"),
    ("data:small-supplement", "Code unavailable, and data-type supplementary files total at most 20 MB"),
    ("data:input-described", "A supplement caption describes input data"),
    ("data:repository", "Cites a GEO, ArrayExpress or SRA accession that still resolves"),
    ("data:obsolete-accession", "Cites an accession that is now obsolete or not found"),
    ("link:hijacked", "A link in the paper now goes to a gambling, crypto or porn site"),
    ("cites:low", f"iCite RCR below {LOW_RCR} (about 30% of these papers; their median RCR is 0.48)"),
    ("cites:high", f"iCite RCR {HIGH_RCR} or more (about 13% of these papers)"),
    ("cites:none", "No citations in iCite"),
    ("sample:...", "In the 150-paper software sample; the outcome follows the colon"),
]


def read(name, comment=False):
    with open(name) as f:
        return list(csv.DictReader(l for l in f if not (comment and l.startswith("#"))))


def num(x):
    try:
        f = float(x)
        return int(f) if f.is_integer() and "." not in str(x) else f
    except (TypeError, ValueError):
        return x if x not in (None, "") else None


def main():
    papers = {("PMC" + p["pmcid"].removeprefix("PMC")): p for p in read("papers.csv", comment=True)}
    audit = {r["pmcid"]: r for r in read("paper_audit.csv")}
    cites = {r["pmcid"]: r for r in read("citations.csv", comment=True)}
    cand = {r["pmcid"]: r for r in read("data_candidates.csv")}
    smp = {r["pmcid"]: r for r in read("install_sample.csv", comment=True)}
    insp = {r["pmcid"]: r for r in read("inspect_results.csv")}
    archived, hijacked = defaultdict(int), set()
    for r in read("url_audit.csv"):
        if r["availability_section"] == "True" and r["category"] in ("gone", "unreachable") and r["wayback"] == "True":
            archived[r["pmcid"]] += 1
        if r["reason"].startswith("hijacked"):
            hijacked.add(r["pmcid"])
    tier_meaning = dict(TIERS)
    rows = []
    for pmcid, p in papers.items():
        a, c, d = audit[pmcid], cites.get(pmcid, {}), cand.get(pmcid, {})
        tags = [TIER_TAG[a["tier"]]]
        if d and float(d["data_mb"]) > 0 and int(d["data_files"]) > 0:
            tags.append("data:small-supplement")
        if d and int(d["input_data_captions"]) > 0:
            tags.append("data:input-described")
        if d and d["live_accessions"]:
            tags.append("data:repository")
        if int(a["accessions_not_resolving"]) > 0:
            tags.append("data:obsolete-accession")
        if pmcid in hijacked:
            tags.append("link:hijacked")
        rcr = num(c.get("icite_rcr"))
        if isinstance(rcr, (int, float)):
            tags += ["cites:low"] if rcr < LOW_RCR else ["cites:high"] if rcr >= HIGH_RCR else []
        if num(c.get("icite_citations")) == 0:
            tags.append("cites:none")
        outcome = sample_outcome(smp[pmcid], insp.get(pmcid, {})) if pmcid in smp else ""
        if outcome:
            tags.append("sample:" + outcome.lower().replace(": ", "-").replace(" ", "-"))
        rows.append({
            "pmcid": pmcid, "pmid": p["pmid"], "doi": p["doi"], "year": p["year"], "journal": p["journal"],
            "title": p["title"], "tier": a["tier"], "tier_meaning": tier_meaning[a["tier"]], "tags": "; ".join(tags),
            "own_links": a["own_urls"], "own_links_reachable": a["own_reachable"], "own_links_dead": a["own_dead"],
            "dead_own_links_archived": archived[pmcid] if int(a["own_dead"]) else "",
            "code_in_supplement": a["supplement_has_code"] == "True",
            "data_supplement_mb": d.get("data_mb", ""), "input_data_captions": d.get("input_data_captions", ""),
            "live_repository_accessions": len(d["live_accessions"].split()) if d.get("live_accessions") else "",
            "accessions_not_resolving": a["accessions_not_resolving"], "sample_outcome": outcome,
            **{k: c.get(k, "") for k, _ in COLUMNS if k.startswith(("icite_", "europepmc_", "pmc_citing", "oa_", "mesh_"))},
        })
    names = [k for k, _ in COLUMNS]
    with open("paper_catalog.csv", "w", newline="") as f:
        w = csv.DictWriter(f, names)
        w.writeheader()
        w.writerows(rows)
    write_xlsx(rows, names)
    print(len(rows), "papers")


def write_xlsx(rows, names):
    wb = Workbook()
    ws = wb.active
    ws.title = "Papers"
    base, bold = Font(name="Arial", size=10), Font(name="Arial", size=10, bold=True)
    head_fill = PatternFill("solid", fgColor="E8EEF6")
    ws.append(names)
    for r in rows:
        ws.append([num(r[k]) if k not in ("pmcid", "pmid", "doi", "title", "journal", "tags", "tier", "tier_meaning",
                                          "sample_outcome", "oa_topic", "oa_subfield", "oa_keywords", "mesh_major")
                   else r[k] for k in names])
    for cell in ws[1]:
        cell.font, cell.fill = bold, head_fill
        cell.alignment = Alignment(wrap_text=True, vertical="top")
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.font = base
    for i, row in enumerate(ws.iter_rows(min_row=2, max_col=1), start=2):
        cell = row[0]
        cell.hyperlink = f"https://pmc.ncbi.nlm.nih.gov/articles/{cell.value}/"
        cell.font = Font(name="Arial", size=10, color="1F5FA8", underline="single")
    ws["A1"].comment = Comment(
        "Source: availability-audit in jeonglab-bcm/fossil (paper_catalog.csv). Audit checks run 28 October 2026; "
        "citation metrics from NIH iCite, Europe PMC, NCBI E-utilities and OpenAlex (see the Data Sources tab).",
        "fossil")
    widths = {"title": 60, "tags": 48, "tier_meaning": 34, "journal": 18, "oa_topic": 30, "oa_keywords": 30,
              "mesh_major": 40, "sample_outcome": 26, "doi": 26}
    for i, n in enumerate(names, start=1):
        ws.column_dimensions[get_column_letter(i)].width = widths.get(n, 12)
    ws.freeze_panes = "B2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(names))}{len(rows) + 1}"

    cols = wb.create_sheet("Columns")
    cols.append(["Column", "Meaning"])
    for row in COLUMNS:
        cols.append(list(row))
    cols.append([])
    cols.append(["Tag", "Meaning"])
    for row in TAGS:
        cols.append(list(row))
    for row in cols.iter_rows():
        for cell in row:
            cell.font = base
            cell.alignment = Alignment(wrap_text=True, vertical="top")
    for cell in (cols["A1"], cols["B1"], cols.cell(len(COLUMNS) + 3, 1), cols.cell(len(COLUMNS) + 3, 2)):
        cell.font, cell.fill = bold, head_fill
    cols.column_dimensions["A"].width, cols.column_dimensions["B"].width = 34, 100

    src = wb.create_sheet("Data Sources")
    retrieved = Path("citations.csv").read_text().splitlines()[0].lstrip("# ")
    src.append(["Written to", "Source", "Object", "Obtained via", "Query or request", "Run at", "Row count", "Notes"])
    src.append(["Papers!A1:AH", "PubMed, PMC", "papers.csv, paper_audit.csv", "NCBI E-utilities; PMC Article Datasets on AWS; "
                "link, accession and supplement checks", "See availability-audit/README.md", "28 October 2026", len(rows),
                "Audit columns (tier, tags, links, data, sample outcome)"])
    src.append(["Papers (citation columns)", "NIH iCite; Europe PMC; NCBI E-utilities elink; OpenAlex; PubMed MeSH",
                "citations.csv", "fetch_citations.py, run by Claude", "Batch lookups by PMID", retrieved, len(rows),
                "OpenAlex columns stay empty until fetched with an API key"])
    for row in src.iter_rows():
        for cell in row:
            cell.font = base
            cell.alignment = Alignment(wrap_text=True, vertical="top")
    for cell in src[1]:
        cell.font, cell.fill = bold, head_fill
    for col, w in zip("ABCDEFGH", (22, 34, 26, 34, 28, 26, 10, 40)):
        src.column_dimensions[col].width = w
    wb.save("paper_catalog.xlsx")


if __name__ == "__main__":
    main()
