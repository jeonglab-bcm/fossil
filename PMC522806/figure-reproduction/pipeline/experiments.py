"""Run every classification of the reproduction with the cfsenn package.

  experiments.py DATA_DIR OUT_DIR [--jobs N] [--reuse COMMITTED_RUNS_DIR] [--only PREFIX ...]

DATA_DIR holds the .dbc files from fetch_inputs.sh. For each experiment, OUT_DIR/runs/<id>.json
gets the prediction of every held-out sample and the accuracy; OUT_DIR/accuracy.json gathers the
accuracies.

An experiment is a list of units (one fit each: the test split, one LOOCV sample, one CV fold, one
random split). Units are independent and seeded by (experiment seed, unit index), so they run in
parallel in any order and give the same answer.

--reuse DIR: for the slow experiments (ovarian and prostate-training LOOCV and the LOOCV hypothesis
tests, about 3.5 of the 4.5 CPU-hours), rerun every SLOW_STRIDE-th unit and take the rest from DIR
(the committed output/runs). The rerun units must equal the committed ones; check_reproduction.py fails
otherwise. Without --reuse every unit is run.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

import cfsenn

DATASETS = {  # key: (train file, test file or None)
    "allaml": ("AMLALL_Train", "AMLALL_Test"),
    "lung": ("lungCancer_Train", "lungCancer_Test"),
    "prostate": ("prostate_TumorVSNormal_Train", "prostate_TumorVSNormal_Test"),
    "mll": ("MLL_Train", "MLL_Test"),
    "dlbcl": ("DLBCL-Stanford", None),
    "ovarian": ("ovarian_61902", None),
    "colon": ("colonTumor", None),
}
TEST_SETS = ("allaml", "lung", "prostate", "mll")
SEEDS = range(5)
FOLD_SEEDS = range(3)
CHO_SPLITS = range(20)
SLOW_STRIDE = 25


def slow(eid):
    """Experiments that --reuse samples: the two slowest LOOCVs and the LOOCV hypothesis tests."""
    return eid in ("loocv.ovarian", "loocv.prostate") or (eid.startswith("hyp.") and ".loocv." in eid)


def experiments():
    """Every experiment: id -> spec. ``settings`` go to cfsenn.Ensemble."""
    E = {}
    for d in TEST_SETS:
        for s in SEEDS:
            E[f"test.{d}.s{s}"] = {"data": d, "scheme": "test", "seed": s, "settings": {}}
    for d in ("allaml", "lung", "prostate", "dlbcl", "ovarian", "colon"):
        E[f"loocv.{d}"] = {"data": d, "scheme": "loocv", "seed": 0, "settings": {}}
    for d in ("dlbcl", "ovarian", "colon"):
        for f in FOLD_SEEDS:
            E[f"cv10.{d}.f{f}"] = {"data": d, "scheme": "cv10", "seed": 0, "fold_seed": f, "settings": {}}
    for r in CHO_SPLITS:
        E[f"cho.dlbcl.r{r}"] = {"data": "dlbcl", "scheme": "split", "seed": 0, "split_seed": r, "settings": {}}
    # The Discussion's controls: random genes, one network on all 75 features, AdaBoost.
    controls = {
        "random": {"feature_sets": ["random", "random", "random"]},
        "single": {"feature_sets": ["combined"], "resample": "none"},
        "adaboost": {"resample": "adaboost"},
    }
    for name, st in controls.items():
        for d in ("allaml", "lung", "prostate"):
            E[f"ctl.{name}.test.{d}"] = {"data": d, "scheme": "test", "seed": 0, "settings": st}
        for d in ("dlbcl", "colon"):
            E[f"ctl.{name}.loocv.{d}"] = {"data": d, "scheme": "loocv", "seed": 0, "settings": st}
    # Hypothesis tests for the items that do not match (sensitivity variants, never agreement).
    hyps = {
        "once": {"select_per_bag": False},
        "hard": {"vote": "hard"},
        "alpha1e-3": {"alpha": 1e-3},
        "alpha1e-1": {"alpha": 1e-1},
        "iter50": {"maxiter": 50},
        "iter1000": {"maxiter": 1000},
        "prefilter2000": {"n_prefilter": 2000},
    }
    for name, st in hyps.items():
        for d in ("allaml", "prostate"):
            E[f"hyp.{name}.test.{d}"] = {"data": d, "scheme": "test", "seed": 0, "settings": st}
        E[f"hyp.{name}.loocv.colon"] = {"data": "colon", "scheme": "loocv", "seed": 0, "settings": st}
    for s in SEEDS:
        E[f"hyp.scaled.test.prostate.s{s}"] = {"data": "prostate", "scheme": "test", "seed": s, "settings": {},
                                               "transform": "scale"}
    # Array scaling on the other train/test sets and on prostate LOOCV; log2 for colon; weight decay
    # 0.1 (which moves prostate's test set) on prostate LOOCV.
    E["hyp.scaled.test.allaml"] = {"data": "allaml", "scheme": "test", "seed": 0, "settings": {}, "transform": "scale"}
    for d in ("allaml", "prostate"):
        E[f"hyp.scaled.loocv.{d}"] = {"data": d, "scheme": "loocv", "seed": 0, "settings": {}, "transform": "scale"}
    E["hyp.alpha1e-1.loocv.prostate"] = {"data": "prostate", "scheme": "loocv", "seed": 0, "settings": {"alpha": 1e-1}}
    E["hyp.log2.loocv.colon"] = {"data": "colon", "scheme": "loocv", "seed": 0, "settings": {}, "transform": "log2"}
    E["hyp.zerofill.loocv.dlbcl"] = {"data": "dlbcl", "scheme": "loocv", "seed": 0, "settings": {},
                                     "transform": "zerofill"}
    return E


# ---------------------------------------------------------------------------------------------

_CACHE: dict = {}


def load(data_dir, key, transform=None):
    """(Xtrain, ytrain, Xtest, ytest, classes) for a dataset; test is None for CV-only sets."""
    ck = (key, transform)
    if ck in _CACHE:
        return _CACHE[ck]
    tr, te = DATASETS[key]
    npz = Path(data_dir) / "npz"
    def read(name):
        f = npz / f"{name}.npz"
        d = np.load(f, allow_pickle=False)
        return d["X"], d["y"], [str(c) for c in d["classes"]]
    Xtr, ytr, classes = read(tr)
    Xte = yte = None
    if te:
        Xte, yte, c2 = read(te)
        assert c2 == classes
    if transform == "scale":
        # Each array scaled to the same mean intensity (global scaling, as MAS5 does): a test of
        # the 10-fold intensity difference between the prostate training and test experiments.
        Xtr = Xtr / Xtr.mean(axis=1, keepdims=True) * 1000.0
        if Xte is not None:
            Xte = Xte / Xte.mean(axis=1, keepdims=True) * 1000.0
    if transform == "log2":
        # log2 of the intensities, floored at 10 (the colon values are positive intensities).
        Xtr = np.log2(np.maximum(Xtr, 10.0))
    if transform == "zerofill":
        Xtr = np.where(np.isnan(Xtr), 0.0, Xtr)
    _CACHE[ck] = (Xtr, ytr, Xte, yte, classes)
    return _CACHE[ck]


def prepare(data_dir):
    """Parse each .dbc once into DATA_DIR/npz (the workers load these)."""
    npz = Path(data_dir) / "npz"
    npz.mkdir(exist_ok=True)
    counts = {}
    for key, (tr, te) in DATASETS.items():
        for name in (tr, te):
            if not name:
                continue
            X, y, genes, classes = cfsenn.read_dbc(Path(data_dir) / f"{name}.dbc")
            np.savez(npz / f"{name}.npz", X=X, y=y, classes=np.array(classes))
            counts[name] = {"samples": int(len(y)), "genes": int(X.shape[1]),
                            "per_class": {c: int((y == i).sum()) for i, c in enumerate(classes)},
                            "missing": int(np.isnan(X).sum())}
    return counts


def units(spec, data_dir):
    """The held-out index sets of an experiment, in unit order. Each: (train idx, test idx, on)."""
    Xtr, ytr, Xte, yte, _ = load(data_dir, spec["data"], spec.get("transform"))
    n = len(ytr)
    if spec["scheme"] == "test":
        return [(np.arange(n), np.arange(len(yte)), "test")]
    if spec["scheme"] == "loocv":
        return [(np.delete(np.arange(n), i), np.array([i]), "train") for i in range(n)]
    if spec["scheme"] == "cv10":
        fold = cfsenn.stratified_folds(ytr, 10, seed=spec["fold_seed"])
        return [(np.flatnonzero(fold != f), np.flatnonzero(fold == f), "train") for f in range(10)]
    if spec["scheme"] == "split":
        # Cho and Won's DLBCL split: 22 training samples (11 of each class), 25 test samples.
        rng = np.random.default_rng(1000 + spec["split_seed"])
        train = np.sort(np.concatenate([rng.choice(np.flatnonzero(ytr == c), 11, replace=False) for c in (0, 1)]))
        return [(train, np.setdiff1d(np.arange(n), train), "train")]
    raise ValueError(spec["scheme"])


def run_unit(args):
    eid, spec, u, data_dir = args
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    Xtr, ytr, Xte, yte, classes = load(data_dir, spec["data"], spec.get("transform"))
    tr, te, on = units(spec, data_dir)[u]
    seed = spec["seed"] * 100003 + u
    t0 = time.time()
    model = cfsenn.Ensemble(seed=seed, **spec["settings"]).fit(Xtr[tr], ytr[tr])
    Xq = Xte if on == "test" else Xtr
    P = model.predict_proba(Xq[te])
    return eid, u, {"unit": u, "held_out": [int(i) for i in te], "predicted": [int(i) for i in P.argmax(axis=1)],
                    "confidence": [round(float(p), 6) for p in P.max(axis=1)]}, time.time() - t0


def cost(spec):
    n = {"ovarian": 37, "prostate": 13, "mll": 9, "lung": 5, "colon": 4, "allaml": 4, "dlbcl": 3}[spec["data"]]
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data_dir")
    ap.add_argument("out_dir")
    ap.add_argument("--jobs", type=int, default=os.cpu_count() or 1)
    ap.add_argument("--reuse")
    ap.add_argument("--only", nargs="*", default=None, help="run only experiments whose id starts with one of these")
    a = ap.parse_args()
    out = Path(a.out_dir)
    (out / "runs").mkdir(parents=True, exist_ok=True)
    counts = prepare(a.data_dir)
    (out / "datasets.json").write_text(json.dumps(counts, indent=1) + "\n")

    E = experiments()
    if a.only:
        E = {k: v for k, v in E.items() if any(k.startswith(p) for p in a.only)}
    todo, reused = [], {}
    for eid, spec in E.items():
        n = len(units(spec, a.data_dir))
        idx = list(range(n))
        if a.reuse and slow(eid):
            old = json.loads((Path(a.reuse) / f"{eid}.json").read_text())
            reused[eid] = {u["unit"]: u for u in old["units"]}
            idx = [i for i in idx if i % SLOW_STRIDE == 0]
        todo += [(eid, E[eid], i, a.data_dir) for i in idx]
    todo.sort(key=lambda t: -cost(t[1]))
    print(f"{len(E)} experiments, {len(todo)} fits on {a.jobs} workers", flush=True)

    results: dict = {eid: {} for eid in E}
    seconds: dict = {eid: 0.0 for eid in E}
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=a.jobs) as ex:
        for k, (eid, u, rec, dt) in enumerate(ex.map(run_unit, todo, chunksize=1)):
            results[eid][u] = rec
            seconds[eid] += dt
            if (k + 1) % 50 == 0:
                print(f"  {k + 1}/{len(todo)} fits, {time.time() - t0:.0f} s", flush=True)

    summary, reran = {}, {}
    for eid, spec in E.items():
        Xtr, ytr, Xte, yte, classes = load(a.data_dir, spec["data"], spec.get("transform"))
        n = len(units(spec, a.data_dir))
        rerun = sorted(results[eid])
        recs = [results[eid].get(i) or reused[eid][i] for i in range(n)]
        truth = yte if spec["scheme"] == "test" else ytr
        held = [i for r in recs for i in r["held_out"]]
        pred = [p for r in recs for p in r["predicted"]]
        acc = cfsenn.accuracy(truth[held], np.array(pred))
        wrong = sorted(int(i) for i, p in zip(held, pred) if truth[i] != p)
        doc = {"id": eid, "data": spec["data"], "scheme": spec["scheme"],
               "settings": dict(cfsenn.DEFAULTS, **spec["settings"], seed=spec["seed"]),
               "transform": spec.get("transform"), "classes": classes, "accuracy": acc,
               "misclassified": wrong, "units": recs}
        doc["settings"]["feature_sets"] = list(doc["settings"]["feature_sets"])
        for k in ("fold_seed", "split_seed"):
            if k in spec:
                doc[k] = spec[k]
        (out / "runs" / f"{eid}.json").write_text(json.dumps(doc, indent=0) + "\n")
        summary[eid] = dict(acc, misclassified=wrong)
        reran[eid] = "all" if len(rerun) == n else rerun
    if a.only and (out / "accuracy.json").exists():  # a partial run adds to the earlier summary
        old = json.loads((out / "accuracy.json").read_text())
        summary = {**old, **summary}
        summary = {k: summary[k] for k in experiments() if k in summary}
    (out / "accuracy.json").write_text(json.dumps(summary, indent=1) + "\n")
    # Which units this run computed (the rest came from --reuse); not compared between runs.
    (out / "reran.json").write_text(json.dumps(reran, indent=1) + "\n")
    print(f"done in {time.time() - t0:.0f} s", flush=True)


if __name__ == "__main__":
    sys.exit(main())
