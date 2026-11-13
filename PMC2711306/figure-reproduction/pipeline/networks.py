"""Build the paper's networks from BioGRID 2.0.35 and write them as edge lists.

HumanBG: human physical interactions (Table S7 systems), both directions merged, self-loops
dropped, proteins named by their official symbol in upper case (the BioGRID ID where BioGRID gives
no symbol), any partner organism; largest connected component.
Yhigh: Collins et al.'s (2007) combined PE scores, pairs with PE >= 3.19 (their high-confidence
set), proteins by systematic name; largest connected component. The test positives (yhigh_low.tsv)
are the pairs between Yhigh proteins with 1.85 <= PE < 3.19: Collins et al. clustered pairs down
to PE 1.85 (a scaled score of 0.2), and the (TP, FP) labels of Fig. 2 imply about 5,300 positives.
The BioGRID copy of the high-confidence set (PubMed 17200106) is written for comparison.

Usage: networks.py BIOGRID_DIR COLLINS_COMBINED_SCORES PHYSICAL_SYSTEMS OUT_DIR
       networks.py BIOGRID_DIR INPUTS_DIR PHYSICAL_SYSTEMS OUT_DIR
With INPUTS_DIR (the committed pipeline/inputs) in place of the Collins scores, the Yhigh files and
their counts are copied from it (the pull-request run; the Collins scores come from the Wayback
Machine, which is too unreliable for CI).
"""
import json
import sys
from pathlib import Path

import geodenoise as gd


def read_biogrid(path):
    rows, started = [], False
    with open(path, encoding="latin-1") as f:
        for line in f:
            if line.startswith("INTERACTOR_A"):
                started = True
                continue
            if started and line.strip():
                rows.append(line.rstrip("\n").split("\t"))
    return rows


def name(row, k):
    sym = row[2 + k]
    return (sym if sym not in ("N/A", "") else row[k]).upper()


def human_pairs(rows, systems):
    return [(name(r, 0), name(r, 1)) for r in rows if r[6] in systems]


def write(net, path):
    with open(path, "w") as f:
        f.write("protein_a\tprotein_b\n")
        for i, j in net.edges:
            f.write(f"{net.nodes[i]}\t{net.nodes[j]}\n")


HIGH, LOW = 3.19, 1.85


def collins(path):
    rows = []
    with open(path) as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            p = line.rstrip("\n").split("\t")
            rows.append((p[0].upper(), p[2].upper(), float(p[4])))
    return rows


def main(biogrid_dir, collins_scores, systems_file, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    systems = {l.strip() for l in open(systems_file) if l.strip() and not l.startswith("#")}
    d = Path(biogrid_dir)
    human = read_biogrid(d / "BIOGRID-ORGANISM-Homo_sapiens-2.0.35.tab.txt")
    yeast = read_biogrid(d / "BIOGRID-ORGANISM-Saccharomyces_cerevisiae-2.0.35.tab.txt")
    full_h = gd.network_from_edges(human_pairs(human, systems))
    hbg = gd.largest_component(full_h)
    write(hbg, out / "humanbg.tsv")
    committed = Path(collins_scores).is_dir()
    if committed:
        import shutil
        for f in ("yhigh.tsv", "yhigh_low.tsv"):
            shutil.copy(Path(collins_scores) / f, out / f)
        yhigh = gd.read_network(out / "yhigh.tsv")
        low = gd.read_network(out / "yhigh_low.tsv")
        old = json.load(open(Path(collins_scores) / "network_counts.json"))
    else:
        pe = collins(collins_scores)
        full_y = gd.network_from_edges([(a, b) for a, b, s in pe if s >= HIGH])
        yhigh = gd.largest_component(full_y)
        write(yhigh, out / "yhigh.tsv")
        yn = set(yhigh.nodes)
        low = gd.network_from_edges([(a, b) for a, b, s in pe
                                     if LOW <= s < HIGH and a in yn and b in yn])
        write(low, out / "yhigh_low.tsv")
    nodes = set(yhigh.nodes)
    coll = [(r[0].upper(), r[1].upper()) for r in yeast if "17200106" in r[8].split(";")]
    bg_y = gd.network_from_edges(coll)
    bg_yhigh = gd.largest_component(bg_y)
    write(bg_yhigh, out / "yhigh_biogrid.tsv")
    # Gavin et al. 2006 and Krogan et al. 2006, the two screens Collins et al. rescored
    gk = {frozenset((r[0].upper(), r[1].upper())) for r in yeast
          if r[0].upper() != r[1].upper() and set(r[8].split(";")) & {"16429126", "16554755"}}
    cset = {frozenset(e) for e in coll if e[0] != e[1]}
    # negative control for Figs 2-3: the Gavin/Krogan pairs Collins et al. discarded, between
    # Yhigh proteins and not Yhigh edges (a wrong truth set for the same universe)
    yset = {frozenset((yhigh.nodes[i], yhigh.nodes[j])) for i, j in yhigh.edges}
    wrong = gd.network_from_edges(sorted(tuple(sorted(e)) for e in gk - cset if e <= nodes and e not in yset))
    write(wrong, out / "yhigh_wrong_truth.tsv")
    counts = {
        "humanbg_full": {"proteins": full_h.n, "interactions": full_h.m},
        "humanbg": {"proteins": hbg.n, "interactions": hbg.m},
        "collins_pairs_scored": old["collins_pairs_scored"] if committed else len(pe),
        "collins_high_full": old["collins_high_full"] if committed else
        {"proteins": full_y.n, "interactions": full_y.m},
        "yhigh": {"proteins": yhigh.n, "interactions": yhigh.m},
        "yhigh_low_confidence_pairs": low.m,
        "yhigh_wrong_truth_pairs": wrong.m,
        "biogrid_collins_full": {"proteins": bg_y.n, "interactions": bg_y.m},
        "biogrid_yhigh": {"proteins": bg_yhigh.n, "interactions": bg_yhigh.m},
        "gavin_krogan": {"interactions": len(gk), "kept_by_collins": len(gk & cset),
                         "discarded_by_collins": len(gk - cset)},
    }
    json.dump(counts, open(out / "network_counts.json", "w"), indent=1)
    print(json.dumps(counts, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:5])
