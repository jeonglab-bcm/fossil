"""Turn the downloaded SGD files into the inputs of the reproduction.

    python prepare_inputs.py DOWNLOADS OUT_DIR

Writes to OUT_DIR:
  genes.txt             systematic names, one per line (the order of every index below)
  ppi_edges.tsv         protein interaction edges (gene index pairs)
  complex_edges.tsv     complex co-membership edges (Gavin 2002 and Ho 2002 purifications as cliques)
  expression.npy        genes x 54 conditions, missing values replaced by the condition mean
  expression_columns.txt
  sgi_pairs.tsv         Tong et al. 2004 synthetic lethal / sick pairs (gene index pairs)
  tested.json           Tong 2004 query genes and the deletion-array genes (non-essential ORFs)
  counts.json           the data counts compared with the paper's Methods
"""

from __future__ import annotations

import collections
import gzip
import itertools
import json
import sys
from pathlib import Path

import numpy as np

TONG = "14764870"
GAVIN = "11805826"
HO = "11805837"
# Protein interactions: our filter (the paper gives only "BioGrid"). Two-hybrid and Affinity
# Capture-Western give 13,007 interactions, the paper 12,990. See results_notes.json.
PPI_TYPES = ("Two-hybrid", "Affinity Capture-Western")

EXPRESSION = [
    # (file inside DOWNLOADS, label, columns used)
    ("Cho_1998_PMID_9702192/2010.Cho98.filter.flt.knn.avg.div.log.pcl", "cho", None),
    ("Chu_1998_PMID_9784122/2010.Chu98.flt.knn.avg.pcl", "chu_sporulation", None),
    ("Spellman_1998_PMID_9843569/2010.Spellman98_alphaFactor.flt.knn.avg.pcl", "spellman_alpha", None),
    ("Spellman_1998_PMID_9843569/2010.Spellman98_elutriation.flt.knn.avg.pcl", "spellman_elutriation", None),
]


def pmid(ref: str) -> str:
    for x in ref.split("|"):
        if x.startswith("PMID:"):
            return x[5:]
    return ""


def read_pcl(path: Path):
    lines = path.read_text(encoding="latin-1").splitlines()
    head = lines[0].split("\t")
    cols = head[3:]
    data = {}
    for line in lines[1:]:
        f = line.split("\t")
        if not f[0] or f[0] in ("EWEIGHT",):
            continue
        vals = [float(x) if x.strip() not in ("",) else np.nan for x in f[3:3 + len(cols)]]
        vals += [np.nan] * (len(cols) - len(vals))
        data[f[0].upper()] = vals
    return cols, data


def main(downloads: str, out: str) -> None:
    dl, od = Path(downloads), Path(out)
    od.mkdir(parents=True, exist_ok=True)
    rows = [l.rstrip("\n").split("\t") for l in gzip.open(dl / "interaction_data.tab.20091219.gz", "rt", encoding="latin-1")]

    # Gold standard: Tong 2004 genetic interactions (all are Synthetic Lethality in this release)
    tong = [r for r in rows if pmid(r[10]) == TONG and r[5].startswith("genetic")]
    queries = sorted({r[0] for r in tong})
    sgi = {tuple(sorted((r[0], r[2]))) for r in tong if r[0] != r[2]}

    # Protein interactions and complexes
    ppi = {tuple(sorted((r[0], r[2]))) for r in rows
           if r[5].startswith("physical") and r[4] in PPI_TYPES and r[0] != r[2]}
    ppi_all = {tuple(sorted((r[0], r[2]))) for r in rows
               if r[5].startswith("physical") and pmid(r[10]) not in (GAVIN, HO) and r[0] != r[2]}
    groups = collections.defaultdict(set)
    for r in rows:
        if pmid(r[10]) in (GAVIN, HO) and r[4] == "Affinity Capture-MS":
            groups[(pmid(r[10]), r[0])].update((r[0], r[2]))
    cpx = set()
    for g in groups.values():
        cpx.update(itertools.combinations(sorted(g), 2))

    # Deletion array: Verified and Uncharacterized ORFs whose systematic deletion is viable
    feats = [l.rstrip("\n").split("\t") for l in gzip.open(dl / "SGD_features.tab.20091205.gz", "rt", encoding="latin-1")]
    orfs = {f[3] for f in feats if len(f) > 3 and f[1] == "ORF" and f[2] in ("Verified", "Uncharacterized")}
    phen = [l.rstrip("\n").split("\t") for l in gzip.open(dl / "phenotype_data.tab.20091205.gz", "rt", encoding="latin-1")]
    essential = {p[0] for p in phen if len(p) > 9 and p[5] == "systematic mutation set" and p[6] == "null" and p[9] == "inviable"}
    array = sorted(orfs - essential)

    # Expression
    blocks, labels, all_genes = [], [], set()
    for rel, name, _ in EXPRESSION:
        cols, data = read_pcl(dl / rel)
        blocks.append((cols, data))
        labels += [f"{name}:{c}" for c in cols]
        all_genes |= set(data)

    net_genes = {g for e in ppi | cpx | ppi_all for g in e}
    genes = sorted(all_genes | net_genes)
    index = {g: i for i, g in enumerate(genes)}
    X = np.full((len(genes), len(labels)), np.nan)
    c0 = 0
    for cols, data in blocks:
        for g, v in data.items():
            X[index[g], c0:c0 + len(cols)] = v
        c0 += len(cols)
    missing = int(np.isnan(X).sum())
    means = np.nanmean(X, axis=0)
    idx = np.where(np.isnan(X))
    X[idx] = means[idx[1]]

    (od / "genes.txt").write_text("\n".join(genes) + "\n")
    (od / "expression_columns.txt").write_text("\n".join(labels) + "\n")
    np.save(od / "expression.npy", X)

    def write_edges(name, edges):
        arr = np.array(sorted((index[a], index[b]) for a, b in edges if a in index and b in index), dtype=np.int64)
        np.savetxt(od / name, arr, fmt="%d", delimiter="\t")
        return arr

    write_edges("ppi_edges.tsv", ppi)
    write_edges("complex_edges.tsv", cpx)
    write_edges("ppi_edges_all.tsv", ppi_all)
    # SGI pairs keep genes outside the network too; the sampling step keeps pairs inside it.
    sg = sorted(sgi)
    with open(od / "sgi_pairs.tsv", "w") as f:
        for a, b in sg:
            f.write(f"{a}\t{b}\n")
    (od / "tested.json").write_text(json.dumps({"queries": queries, "array": array}, indent=0))

    union = ppi | cpx
    counts = {
        "tong_rows": len(tong),
        "tong_queries": len(queries),
        "sgi_pairs": len(sgi),
        "array_genes": len(array),
        "essential_genes": len(essential),
        "tested_pairs": len({tuple(sorted((q, a))) for q in queries for a in array if q != a}),
        "ppi_interactions": len(ppi),
        "ppi_proteins": len({g for e in ppi for g in e}),
        "gavin_ho_purifications": len(groups),
        "complex_interactions": len(cpx),
        "complex_new_interactions": len(cpx - ppi),
        "network_interactions": len(union),
        "network_genes": len({g for e in union for g in e}),
        "ppi_all_interactions": len(ppi_all),
        "expression_genes": len(all_genes),
        "expression_conditions": len(labels),
        "expression_missing_values": missing,
        "network_genes_without_expression": len({g for e in union for g in e} - all_genes),
    }
    (od / "counts.json").write_text(json.dumps(counts, indent=1) + "\n")
    print(json.dumps(counts, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:3])
