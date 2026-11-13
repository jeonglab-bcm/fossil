"""Build the 13 in silico datasets of Table 1 as genes x conditions TSVs with their gold standards.

D1-D8 (DREAM3 networks): simulated with gnw_sim.py (the GNW port) from GNW's network files, DREAM4
time-series protocol, 5 series for size 10 and 10 series for size 50, seed = 1000 + dataset number.
D9-D13 (DREAM4): the challenge's released time series (Bioconductor DREAM4 package, raw files).

Usage: dream_data.py DOWNLOADS OUTDIR [--only D1,D2] [--from-committed DIR]
"""
import json, os, shutil, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gnw_sim

TABLE1 = [
    ("D1", "dream3", "InSilicoSize10-Ecoli1", 10), ("D2", "dream3", "InSilicoSize10-Ecoli2", 10),
    ("D3", "dream3", "InSilicoSize50-Ecoli1", 50), ("D4", "dream3", "InSilicoSize50-Ecoli2", 50),
    ("D5", "dream3", "InSilicoSize10-Yeast1", 10), ("D6", "dream3", "InSilicoSize10-Yeast2", 10),
    ("D7", "dream3", "InSilicoSize50-Yeast1", 50), ("D8", "dream3", "InSilicoSize50-Yeast2", 50),
    ("D9", "dream4", "insilico_size10_1", 10), ("D10", "dream4", "insilico_size10_2", 10),
    ("D11", "dream4", "insilico_size10_3", 10), ("D12", "dream4", "insilico_size100_1", 100),
    ("D13", "dream4", "insilico_size100_2", 100),
]


def write_tsv(path, names, X):
    with open(path, "w") as f:
        f.write("gene\t" + "\t".join(f"t{i + 1}" for i in range(X.shape[1])) + "\n")
        for n, row in zip(names, X):
            f.write(n + "\t" + "\t".join(f"{v:.6g}" for v in row) + "\n")


def dream4(downloads, net):
    d = os.path.join(downloads, "dream4_raw", net)
    with open(os.path.join(d, "timeseries.tsv")) as f:
        header = [h.strip('"') for h in f.readline().split()]
        rows = [l.split() for l in f if l.strip()]
    vals = np.array([[float(v) for v in r] for r in rows])
    t = vals[:, 0]
    X = vals[:, 1:].T  # genes x samples
    names = header[1:]
    starts = np.nonzero(t == 0)[0]
    seg = list(np.diff(np.r_[starts, len(t)]))
    idx = {g: i for i, g in enumerate(names)}
    G = np.zeros((len(names), len(names)), dtype=int)
    for line in open(os.path.join(d, "goldStandard.tsv")):
        a, b, c = line.split()
        if c == "1":
            G[idx[a], idx[b]] = 1
    return names, X, seg, G


def main():
    downloads, out = sys.argv[1], sys.argv[2]
    only = None
    if "--only" in sys.argv:
        only = set(sys.argv[sys.argv.index("--only") + 1].split(","))
    os.makedirs(out, exist_ok=True)
    meta = {}
    for ds, kind, net, size in TABLE1:
        if only and ds not in only:
            continue
        if kind == "dream3":
            nser = 5 if size == 10 else 10
            seed = 1000 + int(ds[1:])
            names, X, seg, G, _ = gnw_sim.simulate_dream4(os.path.join(downloads, "dream3net", net + ".xml"), nser, seed)
            src = f"simulated with gnw_sim.py, {nser} series x 21 points, seed {seed}"
        else:
            names, X, seg, G = dream4(downloads, net)
            src = "DREAM4 released time series"
        write_tsv(os.path.join(out, f"{ds}.tsv"), names, X)
        np.savetxt(os.path.join(out, f"{ds}_gold.tsv"), G, fmt="%d", delimiter="\t")
        meta[ds] = {"network": net, "challenge": kind, "size": size, "genes": len(names), "conditions": int(X.shape[1]),
                    "segments": [int(s) for s in seg], "gold_edges_directed": int(G.sum()),
                    "gold_pairs_undirected": int(((G + G.T) > 0).sum() // 2), "source": src}
        print(ds, meta[ds]["genes"], meta[ds]["conditions"], src, flush=True)
    with open(os.path.join(out, "datasets.json"), "w") as f:
        json.dump(meta, f, indent=1)


if __name__ == "__main__":
    main()
