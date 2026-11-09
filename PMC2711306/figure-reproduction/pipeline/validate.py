"""Validation of the human predictions (Tables S2-S6 and the counts in the text).

Each test runs twice: on the paper's own Table S1 (a check of our validation code against the
paper's counts; it says nothing about our predictions) and on our predictions.

- BioGRID 2.0.50: a predicted pair is validated if it is an interaction (any system) in the human
  BioGRID 2.0.50 file, by upper-cased official symbol.
- HPRD: the release behind the paper (34,119 interactions) is not available; HPRD release 9
  (April 2010) as redistributed by Pathway Commons 2 (v3) stands in for it.
- GO: GOA human release 70 (February 2009), direct annotations by symbol, NOT annotations
  excluded, root terms excluded; BP or CC terms, and BP terms only.
- KEGG: the March 2009 release is not available; the current KEGG REST lists stand in for it.
- Candidate false positives (Table S6): edges further apart than 0.4 that share no CC term or have
  an endpoint without a CC term.

Usage: validate.py HUMANBG.tsv PREDICTIONS.tsv FP_CANDIDATES.tsv SUPPLEMENT.json DOWNLOADS OUT.json
"""
import gzip
import json
import sys
from pathlib import Path

import numpy as np
import scipy.sparse as sp
from scipy.stats import hypergeom

import geodenoise as gd

ROOT = {"GO:0008150", "GO:0005575", "GO:0003674"}
GOA = "gene_association.goa_human.70.gz"


def read_pairs(path):
    out = []
    with open(path) as f:
        next(f)
        for line in f:
            p = line.rstrip("\n").split("\t")
            out.append((p[0], p[1]))
    return out


def biogrid_pairs(path):
    pairs, started = set(), False
    with open(path, encoding="latin-1") as f:
        for line in f:
            if line.startswith("INTERACTOR_A"):
                started = True
                continue
            if started and line.strip():
                r = line.split("\t")
                a = (r[2] if r[2] not in ("N/A", "") else r[0]).upper()
                b = (r[3] if r[3] not in ("N/A", "") else r[1]).upper()
                if a != b:
                    pairs.add(frozenset((a, b)))
    return pairs


def hprd_pairs(path, uniprot_to_symbol):
    """HPRD interactions from the Pathway Commons extended SIF (participants are UniProt URIs)."""
    pairs = set()
    with gzip.open(path, "rt") as f:
        next(f)
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) < 4 or not p[0] or p[3] != "HPRD":
                continue
            if p[0] and not p[0][0].isspace():
                pass
            a = uniprot_to_symbol.get(p[0].rsplit("/", 1)[-1])
            b = uniprot_to_symbol.get(p[2].rsplit("/", 1)[-1])
            if a and b and a != b:
                pairs.add(frozenset((a, b)))
    return pairs


def goa(path, nodes):
    ann = {"P": {}, "C": {}}
    acc = {}
    with gzip.open(path, "rt", errors="replace") as f:
        for line in f:
            if line.startswith("!"):
                continue
            p = line.rstrip("\n").split("\t")
            if len(p) < 9:
                continue
            sym = p[2].upper()
            acc.setdefault(p[1].split("-")[0], sym)
            if "NOT" in p[3] or p[8] not in ann or p[4] in ROOT or sym not in nodes:
                continue
            ann[p[8]].setdefault(sym, set()).add(p[4])
    both = {}
    for k in ("P", "C"):
        for g, t in ann[k].items():
            both.setdefault(g, set()).update(t)
    return {"BP|CC": both, "BP": ann["P"], "CC": ann["C"]}, acc


def sharing_pairs(gs):
    genes = sorted(gs)
    terms = sorted({t for g in genes for t in gs[g]})
    ti = {t: k for k, t in enumerate(terms)}
    r, c = [], []
    for i, g in enumerate(genes):
        for t in gs[g]:
            r.append(i)
            c.append(ti[t])
    A = sp.csr_matrix((np.ones(len(r), np.float32), (r, c)), shape=(len(genes), len(terms)))
    S = (A @ A.T).toarray() > 0
    return len(genes), int(np.triu(S, 1).sum())


def kegg(d):
    sym = {}
    for line in open(d / "list_hsa.tsv"):
        p = line.rstrip("\n").split("\t")
        if len(p) >= 4 and p[1] == "CDS":
            sym[p[0]] = [s.strip().upper() for s in p[3].split(";")[0].split(",")]
    path = {}
    for line in open(d / "link_pathway_hsa.tsv"):
        g, pw = line.rstrip("\n").split("\t")
        for s in sym.get(g, []):
            path.setdefault(s, set()).add(pw.split(":")[1])
    return path


def test_set(pairs, refs, go_sets, kegg_paths):
    pairs = [frozenset(p) for p in pairs]
    out = {"pairs": len(pairs)}
    found = {}
    for name, ref in refs.items():
        hit = [p for p in pairs if p in ref]
        out[name] = len(hit)
        found[name] = set(hit)
    out["validated_any"] = len(set().union(*found.values()))
    out["biogrid_2.0.50_and_hprd"] = len(found["biogrid_2.0.50"] & found["hprd"])
    out["biogrid_2.0.50_not_hprd"] = len(found["biogrid_2.0.50"] - found["hprd"])
    for key in ("BP|CC", "BP"):
        gs = go_sets[key]
        ann = [p for p in pairs if all(v in gs for v in p)]
        share = [p for p in ann if set.intersection(*(gs[v] for v in p))]
        out[f"go_{key}"] = {"annotated": len(ann), "sharing": len(share)}
    inkegg = [p for p in pairs if all(v in kegg_paths for v in p)]
    same = [p for p in inkegg if set.intersection(*(kegg_paths[v] for v in p))]
    out["kegg"] = {"both_in_a_pathway": len(inkegg), "same_pathway": len(same)}
    return out


def main(humanbg, predictions, fp_file, supplement, downloads, out):
    d = Path(downloads)
    net = gd.read_network(humanbg)
    nodes = set(net.nodes)
    supp = json.load(open(supplement))
    go_sets, acc = goa(d / GOA, nodes)
    refs = {
        "biogrid_2.0.50": biogrid_pairs(d / "BIOGRID-ORGANISM-Homo_sapiens-2.0.50.tab.txt"),
        "hprd": hprd_pairs(d / "pc2_v3_hsa_extended_sif.tsv.gz", acc),
    }
    kp = kegg(d)
    res = {"sources": {"goa": GOA, "hprd": "HPRD release 9 via Pathway Commons 2 v3",
                       "hprd_interactions_mapped": len(refs["hprd"]),
                       "kegg": "KEGG REST, current", "kegg_genes_in_pathways": len(kp)}}
    # background counts of the paper's Text S1
    res["background"] = {}
    for key in ("BP|CC", "BP"):
        n, k = sharing_pairs(go_sets[key])
        res["background"][key] = {"annotated_proteins": n, "M": n * (n - 1) // 2, "K": k}
    res["published_table_s1"] = test_set(supp["S1"]["pairs"], refs, go_sets, kp)
    ours = read_pairs(predictions)
    res["ours"] = test_set(ours, refs, go_sets, kp)
    # hypergeometric tests of Text S1, on our counts
    M = net.n * (net.n - 1) // 2
    o = res["ours"]
    res["ours"]["p_hprd"] = float(hypergeom.sf(o["hprd"] - 1, M, len(refs["hprd"]), o["pairs"]))
    for key in ("BP|CC", "BP"):
        b = res["background"][key]
        g = o[f"go_{key}"]
        res["ours"][f"p_go_{key}"] = float(hypergeom.sf(g["sharing"] - 1, b["M"], b["K"], g["annotated"]))
    # candidate false positives
    fp = read_pairs(fp_file)
    cc = go_sets["CC"]
    share_all = [p for p in ((net.nodes[i], net.nodes[j]) for i, j in net.edges)
                 if all(v in cc for v in p) and cc[p[0]] & cc[p[1]]]
    share_fp = [p for p in fp if all(v in cc for v in p) and cc[p[0]] & cc[p[1]]]
    table = [p for p in fp if not (all(v in cc for v in p) and cc[p[0]] & cc[p[1]])]
    s6 = {frozenset(p) for p in supp["S6"]["pairs"]}
    ann_all = [p for p in ((net.nodes[i], net.nodes[j]) for i, j in net.edges) if all(v in cc for v in p)]
    ann_fp = [p for p in fp if all(v in cc for v in p)]
    res["false_positives"] = {
        "edges_sharing_cc_fraction_of_annotated": len(share_all) / len(ann_all),
        "candidates_sharing_cc_fraction_of_annotated": len(share_fp) / len(ann_fp),
        "candidates": len(fp),
        "edges_sharing_cc_fraction": len(share_all) / net.m,
        "candidates_sharing_cc_fraction": len(share_fp) / len(fp),
        "table_s6_ours": len(table),
        "table_s6_published": len(s6),
        "table_s6_overlap": len({frozenset(p) for p in table} & s6),
    }
    json.dump(res, open(out, "w"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:7])
