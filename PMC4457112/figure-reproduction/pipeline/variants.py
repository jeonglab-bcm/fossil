#!/usr/bin/env python3
"""Hypothesis tests for the gaps in Tables 1-3: rerun the forward-selection models with one unstated
setting changed at a time and evaluate on 2011.

The paper does not state the LIBLINEAR solver, C, feature scaling or the 7.5% sample. Each variant
changes one of them; a variant that moves our numbers onto the paper's would explain a gap. Then the
CHISQ threshold: the features kept at several thresholds, and the CHISQ and POSTHOC models refitted at
the Bonferroni threshold. (selection_rule.py reruns forward selection with a coarser rule.) These are
tests, never results.

Usage: variants.py DATA_DIR OUT_DIR   (reads OUT_DIR/selection.json; writes OUT_DIR/variants.json)
(Logistic regression, -s 0, was left out: on 54 million features it ran for over 15 minutes per model.)
"""
import json
import os
import sys
import time

import numpy as np
import scipy.sparse as sp

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from featurize import load_hashed  # noqa: E402
from models import Model, test_margins, yates_chi2_p  # noqa: E402

import rctconf  # noqa: E402
from rctconf.model import FeatureSpace, train_svm  # noqa: E402


def row_normalize(X):
    n = np.sqrt(np.asarray(X.multiply(X).sum(axis=1)).ravel())
    n[n == 0] = 1
    return sp.diags(1 / n) @ X


def main():
    data_dir, out_dir = sys.argv[1:3]
    sel = json.load(open(os.path.join(out_dir, "selection.json")))
    hashed, y, _ = load_hashed(os.path.join(data_dir, "train_sample.features.npz"))
    h11, y11, _ = load_hashed(os.path.join(data_dir, "test2011.features.npz"))
    res = {}
    fs_weights = {}
    for kind in ("citation_plus_mesh", "citation_only"):
        sets = sel[kind]["chosen"]
        spaces = {s: FeatureSpace.fit(hashed, [s]) for s in sets}
        X = sp.hstack([spaces[s].matrix(hashed) for s in sets], format="csr")
        m = Model(kind, sets)
        n11 = len(y11)
        variants = {
            "default (-s 1 -c 1, binary)": ("-s 1 -c 1 -B 1 -q", False),
            "C = 0.1": ("-s 1 -c 0.1 -B 1 -q", False),
            "rows scaled to unit length": ("-s 1 -c 1 -B 1 -q", True),
        }
        res[kind] = {}
        for name, (opt, norm) in variants.items():
            t0 = time.time()
            Xt = row_normalize(X) if norm else X
            w, b = train_svm(Xt, y, opt)
            if norm:
                # margins of the scaled test rows: scale each row's margin by its norm
                f = []
                for start in range(0, n11, 100_000):
                    stop = min(start + 100_000, n11)
                    blocks = []
                    for s in sets:
                        ptr, hh = h11[s]
                        sub = (ptr[start:stop + 1] - ptr[start], hh[ptr[start]:ptr[stop]])
                        blocks.append(spaces[s].matrix({s: sub}))
                    Xb = row_normalize(sp.hstack(blocks, format="csr"))
                    f.append(np.asarray(Xb @ w).ravel() + b)
                f = np.concatenate(f)
            else:
                f = test_margins(m, spaces, w, b, h11)
            if name.startswith("default"):
                w_fs = w
            r = rctconf.evaluate(y11, f, None, rctconf.zero_sigmoid(f))
            res[kind][name] = {k: r[k] for k in ("auc", "average_precision", "f1", "accuracy", "mse_sigmoid")}
            print(kind, name, {k: round(v, 4) for k, v in res[kind][name].items()}, f"{time.time() - t0:.0f}s", flush=True)
        fs_weights[kind] = (sets, w_fs)
        del X, Xt

    # CHISQ: how many features each threshold keeps, and CHISQ and POSTHOC refitted at the Bonferroni
    # threshold (0.05 over the number of candidate features)
    cands = {"citation_only": list(rctconf.CITATION_SETS),
             "citation_plus_mesh": list(rctconf.CITATION_SETS) + list(rctconf.MESH_SETS)}
    spaces = {s: FeatureSpace.fit(hashed, [s]) for s in cands["citation_plus_mesh"]}
    blocks = {s: spaces[s].matrix(hashed) for s in cands["citation_plus_mesh"]}
    del hashed
    n, npos = len(y), int(y.sum())
    pvals = {}
    for s, Xb in blocks.items():
        n1_ = np.asarray(Xb.sum(axis=0)).ravel()
        n11 = np.asarray(Xb[y].sum(axis=0)).ravel()
        pvals[s] = yates_chi2_p(n11, n1_, npos, n)
    res["chisq"] = {}
    for kind, cs in cands.items():
        total = sum(len(pvals[s]) for s in cs)
        alphas = {"0.05": 0.05, "0.001": 0.001, "1e-6": 1e-6, "Bonferroni": 0.05 / total}
        entry = {"candidate_features": total,
                 "kept": {k: int(sum((pvals[s] < a).sum() for s in cs)) for k, a in alphas.items()}}
        masks = {s: pvals[s] < alphas["Bonferroni"] for s in cs}
        mdl = Model("chisq_bonferroni", cs, masks)
        Xc = sp.hstack(mdl.blocks(blocks), format="csr")
        w, b = train_svm(Xc, y)
        del Xc
        r = rctconf.evaluate(y11, test_margins(mdl, spaces, w, b, h11))
        entry["bonferroni_chisq_2011"] = {k: r[k] for k in ("auc", "average_precision", "f1", "accuracy")}
        n_keep = entry["kept"]["Bonferroni"]
        sets, w_fs = fs_weights[kind]
        keep = np.zeros(len(w_fs), dtype=bool)
        keep[np.argsort(-np.abs(w_fs), kind="stable")[:n_keep]] = True
        pm, off = {}, 0
        for s_ in sets:
            k = blocks[s_].shape[1]
            pm[s_] = keep[off:off + k]
            off += k
        mdl = Model("posthoc_bonferroni", sets, pm)
        Xp = sp.hstack(mdl.blocks(blocks), format="csr")
        w, b = train_svm(Xp, y)
        del Xp
        r = rctconf.evaluate(y11, test_margins(mdl, spaces, w, b, h11))
        entry["bonferroni_posthoc_2011"] = {k: r[k] for k in ("auc", "average_precision", "f1", "accuracy")}
        res["chisq"][kind] = entry
        print(kind, "chisq", json.dumps(entry), flush=True)
    del h11

    json.dump(res, open(os.path.join(out_dir, "variants.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
