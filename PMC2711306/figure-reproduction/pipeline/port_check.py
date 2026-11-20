"""Compare the authors' Matlab embedding (run under Octave) with geodenoise on Yhigh.

Usage: port_check.py YHIGH.tsv LOW.tsv OCTAVE_PREFIX OUT.json DIMS...
The Octave run numbers nodes in the order of yhigh.tsv's first appearance (export with
--export EDGES.txt first). Reports, per dimension, the largest difference between the two
distance matrices and the ROC counts of both at the paper's epsilon grid.
"""
import json
import sys

import numpy as np

import geodenoise as gd

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from yeast import EPS_GRID, grid_points, labels, nonedge_universe  # noqa: E402


def main():
    if sys.argv[1] == "--export":
        net = gd.read_network(sys.argv[2])
        np.savetxt(sys.argv[3], net.edges + 1, fmt="%d")
        return
    yhigh, low, prefix, out, *dims = sys.argv[1:]
    net = gd.read_network(yhigh)
    lw = gd.read_network(low)
    ni, nj = nonedge_universe(net)
    pos = labels(net, ni, nj, [(lw.nodes[i], lw.nodes[j]) for i, j in lw.edges])
    P, N = int(pos.sum()), int((~pos).sum())
    res = {"dims": {}}
    for dim in dims:
        Xo = np.loadtxt(f"{prefix}_dim{dim}.txt", delimiter=",", ndmin=2)
        Do = gd.pairwise_distances(Xo)
        D = gd.pairwise_distances(gd.embed(net, int(dim)))
        go = grid_points(Do[ni, nj], pos, P, N, EPS_GRID[:14])
        gp = grid_points(D[ni, nj], pos, P, N, EPS_GRID[:14])
        rel = max(abs(a["tp"] - b["tp"]) / max(b["tp"], 1) for a, b in zip(go, gp) if b["tp"] >= 100)
        res["dims"][dim] = {"max_abs_distance_difference": float(np.abs(Do - D).max()),
                            "mean_abs_distance_difference": float(np.abs(Do - D).mean()),
                            "max_relative_tp_difference": rel,
                            "authors_grid": go, "ours_grid": gp}
        print(dim, res["dims"][dim]["max_abs_distance_difference"], rel, flush=True)
    res["passed"] = all(v["max_relative_tp_difference"] <= 0.02 for v in res["dims"].values())
    json.dump(res, open(out, "w"), indent=1)


if __name__ == "__main__":
    main()
