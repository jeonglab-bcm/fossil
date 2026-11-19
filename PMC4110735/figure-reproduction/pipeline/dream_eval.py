"""Table 2 and Fig. 4: GeCON, ARACNE, CLR and MRNET on the 13 datasets of Table 1.

GeCON comes from the gecon package; ARACNE, CLR and MRNET from minet (minet_run.R). Every method is scored
by gecon.score_network on undirected pairs: AUPR and AUROC of the ranked scores, and the largest F0.5
over thresholds. GeCON's ranked score is its total support Pos_support + Neg_support; the F0.5 of its
thresholded network (theta) is reported too.

Usage: dream_eval.py DATADIR OUT.json [--rscript Rscript]
"""
import json, os, subprocess, sys, tempfile
import numpy as np
import gecon

TAU, THETA = 20.0, 0.5
TAUS = [15.0, 20.0, 25.0]
THETAS = [0.3, 0.4, 0.5, 0.6, 0.7]


def read(datadir, ds):
    names, _, X = gecon.read_matrix(os.path.join(datadir, f"{ds}.tsv"))
    G = np.loadtxt(os.path.join(datadir, f"{ds}_gold.tsv"), dtype=int, ndmin=2)
    return names, X, G


def minet_scores(path, rscript):
    with tempfile.TemporaryDirectory() as tmp:
        pre = os.path.join(tmp, "net")
        subprocess.run([rscript, os.path.join(os.path.dirname(os.path.abspath(__file__)), "minet_run.R"), path, pre],
                       check=True, capture_output=True, text=True)
        out = {}
        for m in ("aracne", "clr", "mrnet"):
            _, _, M = gecon.read_matrix(pre + f"_{m}.tsv")
            out[m] = M
        return out


def r(x):
    return float(round(x, 6))


def main():
    datadir, out = sys.argv[1], sys.argv[2]
    rscript = sys.argv[sys.argv.index("--rscript") + 1] if "--rscript" in sys.argv else "Rscript"
    meta = json.load(open(os.path.join(datadir, "datasets.json")))
    res = {"settings": {"tau": TAU, "theta": THETA, "score": "undirected pairs; AUPR and AUROC trapezoidal; F0.5 maximum over thresholds",
                        "minet": "minet(estimator='spearman', disc='none')"}, "datasets": {}}
    for ds in meta:
        names, X, G = read(datadir, ds)
        seg = meta[ds]["segments"]
        A, sup = gecon.gecon(X, theta=THETA, tau=TAU, segments=seg)
        row = {"gecon": {k: r(v) for k, v in gecon.score_network(G, sup.total, binary=A).items() if k not in ("n_true", "n_pairs")}}
        y_true = gecon.score_network(G, sup.total)
        row["n_true"], row["n_pairs"] = y_true["n_true"], y_true["n_pairs"]
        row["gecon"]["edges"] = int(np.triu(A != 0, 1).sum())
        # binary adjacency scored as a ranking (one threshold)
        b = gecon.score_network(G, np.abs(A).astype(float))
        row["gecon_binary"] = {k: r(b[k]) for k in ("aupr", "auroc", "f_max")}
        # variants: tau grid (ranked scores), theta grid (thresholded F0.5), printed Eq. 7, no segments
        row["variants"] = {}
        for t in TAUS:
            s = gecon.supports(X, tau=t, segments=seg)
            sc = gecon.score_network(G, s.total)
            row["variants"][f"tau={t:g}"] = {"aupr": r(sc["aupr"]), "auroc": r(sc["auroc"]), "f_max": r(sc["f_max"]),
                                             "f_theta": {f"{th:g}": r(gecon.score_network(G, s.total, binary=gecon.network(s, th))["f_binary"]) for th in THETAS}}
        s = gecon.supports(X, tau=TAU, segments=seg, neg_rule="printed")
        sc = gecon.score_network(G, s.total)
        row["variants"]["eq7_printed"] = {k: r(sc[k]) for k in ("aupr", "auroc", "f_max")}
        s = gecon.supports(X, tau=TAU)
        sc = gecon.score_network(G, s.total)
        row["variants"]["no_segments"] = {k: r(sc[k]) for k in ("aupr", "auroc", "f_max")}
        # log2 inputs ("the logarithm of the relative abundance", Terminologies used), at smaller tau too
        L = np.log2(np.maximum(X, 1e-6))
        for t in (5.0, 10.0, 20.0):
            s = gecon.supports(L, tau=t, segments=seg)
            sc = gecon.score_network(G, s.total)
            row["variants"][f"log2 tau={t:g}"] = {k: r(sc[k]) for k in ("aupr", "auroc", "f_max")}
            row["variants"][f"log2 tau={t:g}"]["edges_theta_0.5"] = int(np.triu(gecon.network(s, THETA) != 0, 1).sum())
        # random-score control: expected AUPR is the share of true pairs
        row["random_aupr"] = r(row["n_true"] / row["n_pairs"])
        ms = minet_scores(os.path.join(datadir, f"{ds}.tsv"), rscript)
        for m, M in ms.items():
            sc = gecon.score_network(G, M)
            row[m] = {k: r(sc[k]) for k in ("aupr", "auroc", "f_max")}
            # directed scoring: every ordered pair (i, j), i != j, the score symmetric, the gold standard directed
            off = ~np.eye(len(names), dtype=bool)
            yd = (G != 0)[off].astype(int)
            sd = np.maximum(M, M.T)[off]
            row[m]["directed"] = {"aupr": r(gecon.aupr(yd, sd)), "auroc": r(gecon.auroc(yd, sd))}
        off = ~np.eye(len(names), dtype=bool)
        row["gecon"]["directed"] = {"aupr": r(gecon.aupr((G != 0)[off].astype(int), sup.total[off])), "auroc": r(gecon.auroc((G != 0)[off].astype(int), sup.total[off]))}
        row["random_aupr_directed"] = r(float((G != 0)[off].mean()))
        res["datasets"][ds] = row
        print(ds, {m: (row[m]["aupr"], row[m]["auroc"], row[m]["f_max"]) for m in ("gecon", "aracne", "clr", "mrnet")}, flush=True)
    json.dump(res, open(out, "w"), indent=1)


if __name__ == "__main__":
    main()
