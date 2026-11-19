"""Table 3 counts from the public files, and the normalisation test of GeCON on Yeast KY.

Usage: real_data.py DOWNLOADS OUTDIR   -> OUTDIR/table3.json, OUTDIR/normalisation.json
"""
import gzip, json, os, sys
import numpy as np
import gecon


def kayee(path):
    rows = [l.rstrip("\n").split("\t") for l in open(path)]
    head, body = rows[0], [r for r in rows[1:] if len(r) > 3]
    conds = [h for h in head if h.startswith("c") and h[1:].isdigit()]
    return len(body), len(conds), body


def gds_samples(path):
    with gzip.open(path, "rt", encoding="latin-1") as f:
        for line in f:
            if line.startswith("!dataset_sample_count"):
                return int(line.split("=")[1])


def main():
    dl, out = sys.argv[1:3]
    ky_n, ky_c, _ = kayee(os.path.join(dl, "logcho_237_4class.txt"))
    cc_n, cc_c, _ = kayee(os.path.join(dl, "log_cellcycle_384_17.txt"))
    t3 = {"Yeast KY": {"genes": ky_n, "samples": ky_c}, "Yeast cell cycle": {"genes": cc_n, "samples": cc_c},
          "GDS825": {"samples": gds_samples(os.path.join(dl, "GDS825.soft.gz"))},
          "GDS958 (Subset)": {"samples": gds_samples(os.path.join(dl, "GDS958.soft.gz"))},
          "GDS3702 (Subset)": {"samples": gds_samples(os.path.join(dl, "GDS3702.soft.gz"))}}
    json.dump(t3, open(os.path.join(out, "table3.json"), "w"), indent=1)
    res = {}
    for name, f in (("log", "logcho_237_4class.txt"), ("normalised", "normcho_237_4class.txt")):
        _, _, body = kayee(os.path.join(dl, f))
        X = np.array([[float(v) for v in r[2:19]] for r in body])
        s = gecon.supports(X, tau=20)
        res[name] = {"pairs": int(X.shape[0] * (X.shape[0] - 1) // 2),
                     **{f"edges_theta_{t:g}": int(np.triu(gecon.network(s, t) != 0, 1).sum()) for t in (0.5, 0.6, 0.7, 0.8)},
                     "mean_total_support": round(float(s.total[np.triu_indices(X.shape[0], 1)].mean()), 4)}
    r, a = gecon.edge_patterns(np.array([[float(v) for v in r[2:19]] for r in kayee(os.path.join(dl, "logcho_237_4class.txt"))[2]]))
    res["log_angles_share_within_5_degrees_of_45_or_135"] = round(float(((np.abs(a - 45) < 5) | (np.abs(a - 135) < 5)).mean()), 4)
    json.dump(res, open(os.path.join(out, "normalisation.json"), "w"), indent=1)
    print(t3, res)


if __name__ == "__main__":
    main()
