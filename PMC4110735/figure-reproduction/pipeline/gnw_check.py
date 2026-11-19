"""Check the GNW port (gnw_sim.py) against the DREAM4 challenge release, which GNW itself made.

For each of the 10 DREAM4 networks: the gold standard read from the network file must equal the released
goldStandard.tsv, and the port's wild-type steady state must track the released wildtype.tsv (which carries
microarray noise and an unknown normalisation): log-scale correlation of at least 0.95.

Usage: gnw_check.py DOWNLOADS OUT.json
"""
import json, os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gnw_sim


def main():
    dl, out = sys.argv[1:3]
    rows = {}
    for size in (10, 100):
        for k in range(1, 6):
            net = f"insilico_size{size}_{k}"
            names, genes = gnw_sim.read_sbml(os.path.join(dl, "dream4net", f"{net}.xml"))
            wt = gnw_sim.Model(genes).steady_state()[: len(names)]
            d = os.path.join(dl, "dream4_raw", net)
            hdr = [h.strip('"') for h in open(os.path.join(d, "wildtype.tsv")).readline().split()]
            rel = np.loadtxt(os.path.join(d, "wildtype.tsv"), skiprows=1)
            assert hdr == names
            G = gnw_sim.gold_standard(genes, names)
            idx = {g: i for i, g in enumerate(names)}
            released = {(idx[a], idx[b]) for a, b, c in (l.split() for l in open(os.path.join(d, "goldStandard.tsv"))) if c == "1"}
            ours = {tuple(map(int, x)) for x in np.argwhere(G == 1)}
            rows[net] = {"gold_standard_equal": released == ours, "edges": len(released),
                         "wildtype_log_corr": round(float(np.corrcoef(np.log(wt), np.log(rel))[0, 1]), 4)}
            print(net, rows[net], flush=True)
    passed = all(r["gold_standard_equal"] and r["wildtype_log_corr"] >= 0.95 for r in rows.values())
    corr = [r["wildtype_log_corr"] for r in rows.values()]
    json.dump({"passed": passed, "networks": rows, "min_corr": min(corr), "max_corr": max(corr)}, open(out, "w"), indent=1)


if __name__ == "__main__":
    main()
