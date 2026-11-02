"""Candidate tool names for papers whose software link is dead (tiers D and E, iCite RCR >= 1).

Sources, in order: the title before a colon (three words at most), name-like title tokens (two or
more capitals, a digit, or lower-then-upper like miTarget), the last path segment and host label of
each dead own-resource link, and name-like words that appear at least twice in the abstract.
Common abbreviations (DNA, SVM, KEGG...) are skipped. Used by find_new_homes.py.
"""
import csv
import re
from collections import Counter
from urllib.parse import urlsplit

from lxml import etree


COMMON = set("""DNA RNA SVM PPI GO MRI EST SNP SNPS QTL EQTL ROC AUC KEGG PDB NCBI EBI HMM PCA MCMC ICA LDA CNV GWAS ChIP
SAGE SOM NMR GPU CPU API XML HTML URL HTTP PHP CGI JAVA PERL R C MS MS/MS LC NGS PCR qPCR mRNA miRNA miRNAs siRNA ncRNA
TF TFBS HIV HCV GPCR GPCRs ORF ORFs UTR BLAST PSI PSSM ANN KNN RF CRF NB GA EM ML MAP MAQC TCGA ENCODE OMIM UMLS NLP
CT PET EEG ECG ICU EHR EMR FDA NIH US UK EU PLoS BMC IEEE ACM SQL MySQL PubMed MEDLINE MeSH WWW II III IV DE FDR GSEA""".split())
NAME = re.compile(r"\b([A-Za-z][A-Za-z0-9\-\+]{2,24})\b")
def looks_like_name(t):
    if t.upper() in {c.upper() for c in COMMON} or t.isdigit():
        return False
    caps = sum(ch.isupper() for ch in t)
    return caps >= 2 or any(ch.isdigit() for ch in t) or (t[0].islower() and caps >= 1)


def candidates(min_rcr=1.0, tiers=("D", "E")):
    cat = {r["pmcid"]: r for r in csv.DictReader(open("paper_catalog.csv"))}
    pool = [r for r in cat.values() if r["icite_rcr"] and float(r["icite_rcr"]) >= min_rcr and r["tier"] in tiers]
    own = {}
    for u in csv.DictReader(open("url_audit.csv")):
        if u["availability_section"] == "True" and u["category"] in ("gone", "unreachable"):
            own.setdefault(u["pmcid"], []).append(u["url"])
    out = []
    for r in pool:
        p = r['pmcid']; cands = []
        title = r['title']
        if ':' in title:
            head = title.split(':')[0].strip()
            if len(head.split()) <= 3:
                cands.append(('title-colon', head))
        for t in NAME.findall(title):
            if looks_like_name(t):
                cands.append(('title-token', t))
        for u in own.get(p, []):
            s = urlsplit(u)
            segs = [x for x in s.path.split('/') if x and not re.search(r'\.(html?|php|cgi|asp|jsp)$', x, re.I)
                    and x.lower() not in ('software', 'tools', 'tool', 'download', 'downloads', 'research', 'projects', 'people',
                                          'lab', 'labs', 'pub', 'public', 'supplement', 'supplementary', 'data', 'home', 'index',
                                          'bioinformatics', 'services', 'cgi-bin', 'web', 'www', 'users', 'staff', 'group', 'groups')
                    and not x.startswith('~')]
            if segs:
                cands.append(('url-path', segs[-1]))
            lab = s.hostname.split('.')[0] if s.hostname else ''
            if lab and lab not in ('www', 'bioinformatics', 'bioinfo', 'compbio', 'cbio', 'genome', 'web', 'sites'):
                cands.append(('url-host', lab))
        root = etree.parse(f'cache/articles/{p}.xml', etree.XMLParser(resolve_entities=False, no_network=True, huge_tree=True)).getroot()
        ab = ' '.join(' '.join(''.join(x.itertext()).split()) for x in root.findall('front/article-meta/abstract'))
        cnt = Counter(t for t in NAME.findall(ab) if looks_like_name(t))
        for t, n in cnt.most_common(3):
            if n >= 2:
                cands.append(('abstract', t))
        seen, uniq = set(), []
        for src, t in cands:
            k = t.lower().strip('-+')
            if k and k not in seen and len(k) >= 3:
                seen.add(k); uniq.append((src, t.strip('-+')))
        out.append({'pmcid': p, 'pmid': r['pmid'], 'doi': r['doi'], 'year': r['year'], 'rcr': r['icite_rcr'],
                    'title': title, 'dead_links': own.get(p, []), 'names': uniq})
    return out
