#!/usr/bin/env python3
"""Feature-set forward selection and the eight models of Tables 1-3, all with rctconf.

Models (citation-only and citation-plus-MeSH variants of each):
  FORWARD SELECTION   the sets chosen by forward selection (Tables 1 and 2, Table 3 column 1)
  CHISQ               every feature of every candidate set that is individually significant by a
                      chi-squared test on the training sample (Table 3 column 2)
  POSTHOC             the FORWARD SELECTION model's N features of largest |weight|, N = CHISQ's
                      feature count, retrained (Table 3 column 3)
  PLUS PUBTYPES       FORWARD SELECTION sets plus the publication types other than RCT (column 4)

Each model is trained on the 7.5% training sample; its confidence sigmoid is fitted to 2-fold
out-of-fold margins; it is evaluated on all 2011 and all 2012 citations. The FORWARD SELECTION models
are also cross-validated 5x2 on the training sample (Tables 1 and 2, first column).

Usage: models.py DATA_DIR OUT_DIR [--selection-repeats 1] [--workers 3] [--alpha 0.05]
        [--candidates-citation ...] [--candidates-mesh ...] [--cv-repeats 5]
Writes OUT_DIR/selection.json, OUT_DIR/models.json, and DATA_DIR/model_citation_plus_mesh.npz.
"""
import argparse
import gc
import json
import os
import sys
import time

import numpy as np
import scipy.sparse as sp
from scipy.stats import chi2 as chi2_dist

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from featurize import load_hashed  # noqa: E402

import rctconf  # noqa: E402
from rctconf.model import FeatureSpace, RCTModel, fit_sigmoid, platt, train_svm, zero_sigmoid  # noqa: E402
from rctconf.selection import _block_margins, cross_validate, forward_select  # noqa: E402

ROW_CHUNK = 100_000


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def yates_chi2_p(n11, n1_, n_1, n):
    """p-values of the 2x2 chi-squared test with Yates' correction, vectorized.

    n11: documents with the feature and the label; n1_: with the feature; n_1: with the label; n: all.
    """
    n11 = n11.astype(float)
    n1_ = n1_.astype(float)
    n12 = n1_ - n11
    n21 = n_1 - n11
    n22 = n - n1_ - n21
    num = n * np.maximum(np.abs(n11 * n22 - n12 * n21) - n / 2.0, 0) ** 2
    den = n1_ * (n - n1_) * n_1 * (n - n_1)
    with np.errstate(divide="ignore", invalid="ignore"):
        stat = np.where(den > 0, num / den, 0.0)
    return chi2_dist.sf(stat, 1)


class Model:
    """A model on a subset of the columns of per-set blocks."""

    def __init__(self, name, sets, masks=None):
        self.name, self.sets, self.masks = name, list(sets), masks or {}

    def blocks(self, blocks):
        out = []
        for s in self.sets:
            b = blocks[s]
            out.append(b[:, self.masks[s]] if s in self.masks else b)
        return out

    def n_features(self, blocks):
        return int(sum(b.shape[1] for b in self.blocks(blocks)))


def oof_margins(blocks_list, y, seed=0):
    f = np.empty(len(y))
    rng = np.random.default_rng(seed)
    fold = rng.permutation(len(y)) % 2
    for k in range(2):
        tr, te = np.nonzero(fold != k)[0], np.nonzero(fold == k)[0]
        Xtr = sp.hstack([b[tr] for b in blocks_list], format="csr")
        w, b = train_svm(Xtr, y[tr])
        del Xtr
        f[te] = _block_margins(blocks_list, te, w, b)
    return f


def test_margins(model, spaces, w, b, hashed_test):
    """Margins on a test year, in row chunks, with the training vocabulary."""
    n = len(next(iter(hashed_test.values()))[0]) - 1
    out = np.empty(n)
    for start in range(0, n, ROW_CHUNK):
        stop = min(start + ROW_CHUNK, n)
        blocks = []
        for s in model.sets:
            ptr, h = hashed_test[s]
            sub = (ptr[start : stop + 1] - ptr[start], h[ptr[start] : ptr[stop]])
            m = spaces[s].matrix({s: sub})
            blocks.append(m[:, model.masks[s]] if s in model.masks else m)
        out[start:stop] = _block_margins(blocks, np.arange(stop - start), w, b)
    return out


def metrics(y, f, A, B):
    return rctconf.evaluate(y, f, platt(f, A, B), zero_sigmoid(f))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data_dir")
    ap.add_argument("out_dir")
    ap.add_argument("--selection-repeats", type=int, default=1)
    ap.add_argument("--cv-repeats", type=int, default=5)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--candidates-citation", nargs="+", default=list(rctconf.CITATION_SETS))
    ap.add_argument("--candidates-mesh", nargs="+", default=list(rctconf.MESH_SETS))
    ap.add_argument("--test-years", type=int, nargs="+", default=[2011, 2012])
    ap.add_argument("--selection", help="reuse a selection.json instead of running forward selection")
    a = ap.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)

    hashed, y, _ = load_hashed(os.path.join(a.data_dir, "train_sample.features.npz"))
    with open(os.path.join(a.data_dir, "author_bins.json")) as fh:
        bins = json.load(fh)["cut_points"]
    cand_cit = list(a.candidates_citation)
    cand_mesh = cand_cit + list(a.candidates_mesh)
    all_sets = cand_mesh + ["pubtypes"]
    spaces = {s: FeatureSpace.fit(hashed, [s]) for s in all_sets}
    blocks = {s: spaces[s].matrix(hashed) for s in all_sets}
    del hashed
    gc.collect()
    log("training sample", len(y), "citations,", int(y.sum()), "RCT;",
        {s: blocks[s].shape[1] for s in all_sets})

    # forward selection
    if a.selection:
        with open(a.selection) as fh:
            selection = json.load(fh)
    else:
        # each step is checkpointed in OUT_DIR/selection_partial.json; a rerun continues from it
        part_path = os.path.join(a.out_dir, "selection_partial.json")
        selection = {"repeats": a.selection_repeats, "seed": 0}
        if os.path.exists(part_path):
            selection = json.load(open(part_path))
        for name, cands in (("citation_only", cand_cit), ("citation_plus_mesh", cand_mesh)):
            log("forward selection", name, "over", len(cands), "sets")

            def save(partial, name=name):
                selection[name] = partial
                json.dump(selection, open(part_path, "w"), indent=1)
            r = forward_select(blocks, y, cands, repeats=a.selection_repeats, seed=0, workers=a.workers, log=log,
                               resume=selection.get(name), checkpoint=save)
            selection[name] = r
            save(r)
        with open(os.path.join(a.out_dir, "selection.json"), "w") as fh:
            json.dump(selection, fh, indent=1)
        os.remove(part_path)

    results = {"training_sample": int(len(y)), "training_sample_rct": int(y.sum()), "alpha": a.alpha,
               "candidate_features": {s: int(blocks[s].shape[1]) for s in all_sets}, "models": {}}
    tests = {}
    for yr in a.test_years:
        h, yt, _ = load_hashed(os.path.join(a.data_dir, f"test{yr}.features.npz"))
        tests[yr] = (h, yt)

    for kind, cands in (("citation_only", cand_cit), ("citation_plus_mesh", cand_mesh)):
        fs_sets = selection[kind]["chosen"]
        models = [Model("forward_selection", fs_sets)]
        # CHISQ: significant features of every candidate set
        n = len(y)
        masks = {}
        for s in cands:
            Xb = blocks[s]
            n1_ = np.asarray(Xb.sum(axis=0)).ravel()
            n11 = np.asarray(Xb[y].sum(axis=0)).ravel()
            masks[s] = yates_chi2_p(n11, n1_, int(y.sum()), n) < a.alpha
        chisq = Model("chisq", cands, masks)
        n_chisq = chisq.n_features(blocks)
        models.append(chisq)
        models.append(Model("plus_pubtypes", fs_sets + ["pubtypes"]))
        posthoc_pending = True

        fitted = {}
        queue = list(models)
        while queue:
            m = queue.pop(0)
            bl = m.blocks(blocks)
            log(kind, m.name, "features", m.n_features(blocks))
            X = sp.hstack(bl, format="csr")
            w, b = train_svm(X, y)
            del X
            gc.collect()
            A, B = fit_sigmoid(oof_margins(bl, y), y)
            entry = {"sets": m.sets, "n_features": m.n_features(blocks), "nonzero_weights": int((w != 0).sum()),
                     "sigmoid": [A, B]}
            for yr, (h, yt) in tests.items():
                f = test_margins(m, spaces, w, b, h)
                entry[str(yr)] = metrics(yt, f, A, B)
                log(kind, m.name, yr, {k: round(v, 4) for k, v in entry[str(yr)].items() if isinstance(v, float)})
            if m.name == "forward_selection":
                cv = cross_validate(bl, y, repeats=a.cv_repeats, seed=1, keep_margins=True)
                fm = cv.pop("fold_margins")
                per = []
                for te, f in fm:
                    per.append(rctconf.evaluate(y[te], f, None, zero_sigmoid(f)))
                entry["cv"] = {k: float(np.mean([p[k] for p in per])) for k in
                               ("auc", "average_precision", "f1", "accuracy", "mse_sigmoid")}
                entry["cv"]["folds"] = len(per)
                log(kind, "cv", {k: round(v, 4) for k, v in entry["cv"].items()})
                if kind == "citation_plus_mesh":
                    space = FeatureSpace({s: spaces[s].vocab[s] for s in m.sets})
                    RCTModel(space, w, b, (A, B), bins, {"sets_kind": kind}).save(
                        os.path.join(a.data_dir, "model_citation_plus_mesh.npz"))
                if posthoc_pending:
                    # POSTHOC: top n_chisq |w| of the forward selection model, retrained
                    absw = np.abs(w)
                    keep = np.zeros(len(w), dtype=bool)
                    keep[np.argsort(-absw, kind="stable")[:n_chisq]] = True
                    pm, off = {}, 0
                    for s in m.sets:
                        k = blocks[s].shape[1]
                        pm[s] = keep[off : off + k]
                        off += k
                    queue.insert(0, Model("posthoc", m.sets, pm))
                    posthoc_pending = False
            fitted[m.name] = entry
            gc.collect()
        results["models"][kind] = fitted
        with open(os.path.join(a.out_dir, "models.json"), "w") as fh:
            json.dump(results, fh, indent=1)
    log("done")


if __name__ == "__main__":
    main()
