"""Build the weighted FGN and the binary network, and the 18 features of every gene pair we use.

    python features.py INPUTS OUT_DIR

INPUTS is the folder prepare_inputs.py wrote. Writes OUT_DIR/features.npz with, for the weighted
and the binary network, the features of every Tong 2004 SGI pair and every tested non-SGI pair
(query x deletion array, no reported interaction) whose two genes are both in the network; and
OUT_DIR/network.json with the network sizes and the cluster count.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from fgnssl import fgn, network as N


def main(inputs: str, out: str) -> None:
    ind, od = Path(inputs), Path(out)
    od.mkdir(parents=True, exist_ok=True)
    genes = ind.joinpath("genes.txt").read_text().split()
    index = {g: i for i, g in enumerate(genes)}
    X = np.load(ind / "expression.npy")
    E = np.vstack([np.loadtxt(ind / "ppi_edges.tsv", dtype=np.int64, ndmin=2),
                   np.loadtxt(ind / "complex_edges.tsv", dtype=np.int64, ndmin=2)])
    E = np.unique(np.sort(E, axis=1), axis=0)
    labels = fgn.dcca(X)
    w = fgn.edge_weights(X, labels, E)
    n = len(genes)
    in_net = np.zeros(n, dtype=bool)
    in_net[E.ravel()] = True

    tested = json.loads(ind.joinpath("tested.json").read_text())
    queries = [q for q in tested["queries"] if q in index and in_net[index[q]]]
    array = [a for a in tested["array"] if a in index and in_net[index[a]]]
    sgi = set()
    for line in ind.joinpath("sgi_pairs.tsv").read_text().splitlines():
        a, b = line.split("\t")
        if a in index and b in index and in_net[index[a]] and in_net[index[b]]:
            sgi.add(frozenset((a, b)))
    qset = set(tested["queries"])

    def orient(p):
        a, b = sorted(p)
        return (a, b) if a in qset or b not in qset else (b, a)  # the query gene first

    pos = sorted(orient(p) for p in sgi)
    neg = sorted({orient((q, a)) for q in queries for a in array if q != a and frozenset((q, a)) not in sgi})
    pairs = np.array([(index[a], index[b]) for a, b in pos + neg], dtype=np.int64)
    y = np.r_[np.ones(len(pos), dtype=np.int8), np.zeros(len(neg), dtype=np.int8)]

    result = {"pairs": pairs, "y": y}
    sizes = {}
    for name, weights in (("weighted", w), ("binary", None)):
        g = N.make_graph(n, E, weights)
        props = N.node_properties(g, weighted=weights is not None)
        result[f"X_{name}"] = N.pair_features(g, props, pairs, weighted=weights is not None)
        for p, v in props.items():
            result[f"node_{name}_{p}"] = v
    result["genes"] = np.array(genes)
    result["edge_weights"] = w
    result["clusters"] = labels
    np.savez_compressed(od / "features.npz", **result)
    sizes = {
        "network_genes": int(in_net.sum()), "network_interactions": int(len(E)), "clusters": int(labels.max() + 1),
        "edge_weight_median": float(np.median(w)), "sgi_pairs_in_network": len(pos),
        "nonsgi_pairs_in_network": len(neg), "queries_in_network": len(queries), "array_in_network": len(array),
        "feature_names": list(N.FEATURE_NAMES),
    }
    (od / "network.json").write_text(json.dumps(sizes, indent=1) + "\n")
    print(json.dumps(sizes, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:3])
