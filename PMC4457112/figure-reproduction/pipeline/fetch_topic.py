#!/usr/bin/env python3
"""PMIDs of the acute cholecystitis topic search, from PubMed E-utilities.

The paper's query (its Supplementary Table S2) is lost with the supplement. This rebuilds it from what
the paper says: the topic terms of the Cochrane review CD005440 (early versus delayed laparoscopic
cholecystectomy for acute cholecystitis) combined with the highly sensitive search strategy of
Robinson and Dickersin (2002; the paper's ref. 21), restricted to 1987-2012. The topic terms are our
choice. The result is written once and committed, because PubMed changes.

Usage: fetch_topic.py OUT.txt
"""
import re
import subprocess
import sys
import time
import urllib.parse

TOPIC = '(cholecystitis[mh] OR cholecystitis[tiab]) AND acute[tiab]'
ANIMALS = '(animals[mh] NOT humans[mh])'
P1 = ('(randomized controlled trial[pt] OR controlled clinical trial[pt] OR randomized controlled trials[mh] '
      'OR random allocation[mh] OR double-blind method[mh] OR single-blind method[mh])')
P2 = ('(clinical trial[pt] OR clinical trials as topic[mh] OR (clinic*[tw] AND trial*[tw]) OR '
      '((singl*[tw] OR doubl*[tw] OR trebl*[tw] OR tripl*[tw]) AND (mask*[tw] OR blind*[tw])) OR '
      'placebos[mh] OR placebo*[tw] OR random*[tw] OR research design[mh:noexp])')
P3 = ('(comparative study[pt] OR evaluation studies[pt] OR follow-up studies[mh] OR prospective studies[mh] '
      'OR control*[tw] OR prospectiv*[tw] OR volunteer*[tw])')
HSSS = f'(({P1} OR {P2} OR {P3}) NOT {ANIMALS})'
QUERY = f'({TOPIC}) AND {HSSS}'
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"


def esearch(term, retmax=10000):
    url = EUTILS + "?" + urllib.parse.urlencode({"db": "pubmed", "term": term, "retmax": retmax})
    for attempt in range(5):
        r = subprocess.run(["curl", "-sS", "--retry", "3", url], capture_output=True, text=True)
        if r.returncode == 0 and "<Count>" in r.stdout:
            count = int(re.search(r"<Count>(\d+)</Count>", r.stdout).group(1))
            return count, [int(x) for x in re.findall(r"<Id>(\d+)</Id>", r.stdout)]
        time.sleep(3 * (attempt + 1))
    raise RuntimeError("esearch failed")


def main():
    out = sys.argv[1]
    pmids = set()
    for year in range(1987, 2013):
        count, ids = esearch(f"{QUERY} AND {year}[dp]")
        if count > len(ids):
            raise RuntimeError(f"{year}: {count} results, more than one page")
        pmids.update(ids)
        time.sleep(0.4)
    with open(out, "w") as fh:
        fh.write(f"# query: {QUERY} AND <year>[dp], year 1987-2012\n")
        fh.write(f"# retrieved {time.strftime('%Y-%m-%d')} from PubMed E-utilities; {len(pmids)} PMIDs\n")
        for p in sorted(pmids):
            fh.write(f"{p}\n")
    print(out, len(pmids), "PMIDs")


if __name__ == "__main__":
    main()
