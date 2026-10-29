"""Tables 1 and 2 and Supplementary Table 1 (Supporting Information S1) from the authors' saved
optima and from our refit, compared with the printed values.

Each row gives the maximum log-likelihood l(theta*), BIC = -2 l + log(n) * n_par, the rank by
BIC, Delta_BIC = BIC - BIC_min and the decision (optimal / not rejected / rejected if
Delta_BIC > 10), printed at the paper's precision.
"""

import argparse
import csv
import json
import os

import numpy as np

from saved import LABELS, load_model, model_list, to_D
from odemm import bic


def printed(v):
    return float(v.replace("−", "-"))


def rows_for(sources, study, refit_dir=None):
    out = []
    for label, model in zip(LABELS["cr" if study.startswith("cr") else "ngf"], model_list(study)):
        _, m = load_model(sources, study, model)
        p = m["parameters"]
        r = {"model": label, "fit": model, "n_par": int(p.number),
             "saved_logL": float(p.MS.MAP.logPost), "saved_BIC": float(p.MS.MAP.BIC)}
        if refit_dir and os.path.exists(os.path.join(refit_dir, f"{study}__{model}.json")):
            j = json.load(open(os.path.join(refit_dir, f"{study}__{model}.json")))
            r["refit_logL"] = j["best_logL"]
            r["refit_BIC"] = float(bic(j["best_logL"], int(p.number), to_D(m["D"])))
            r["refit_starts"] = j["n_starts"]
            r["refit_at_best"] = j.get("n_at_best", j.get("n_within_0.1_of_best"))
        out.append(r)
    for kind in ("saved", "refit"):
        if not all(f"{kind}_BIC" in r for r in out):
            continue
        b = np.array([r[f"{kind}_BIC"] for r in out])
        order = np.argsort(b)
        for rank, i in enumerate(order, start=1):
            d = b[i] - b.min()
            out[i][f"{kind}_rank"] = rank
            out[i][f"{kind}_dBIC"] = float(d)
            out[i][f"{kind}_decision"] = "optimal" if d == 0 else ("rejected" if d > 10 else "not rejected")
    return out


def compare(rows, published, scale, digits):
    """Published rows (same order) vs ours, each formatted at the printed precision."""
    res = []
    for r, pub in zip(rows, published):
        c = {"model": r["model"]}
        for kind in ("saved", "refit"):
            if f"{kind}_BIC" not in r:
                continue
            ll = f"{r[f'{kind}_logL'] / scale:.{digits}f}"
            bb = f"{r[f'{kind}_BIC'] / scale:.{digits}f}"
            d = r[f"{kind}_dBIC"]
            dd = ">10" if d > 10 else f"{d:.3f}".rstrip("0").rstrip(".") if d else "0"
            c[kind] = {"logL": ll, "BIC": bb, "rank": r[f"{kind}_rank"], "dBIC": dd,
                       "decision": r[f"{kind}_decision"]}
            pd_ = pub["dBIC"].replace(" ", "")
            pdv = pd_ if pd_.startswith(">") else f"{float(pd_):.3f}".rstrip("0").rstrip(".") if float(pd_) else "0"
            c[kind]["matches"] = {
                "logL": abs(float(ll) - printed(pub["logL"])) < 0.5 * 10 ** -digits + 1e-12,
                "BIC": abs(float(bb) - printed(pub["BIC"])) < 0.5 * 10 ** -digits + 1e-12,
                "rank": c[kind]["rank"] == int(pub["rank"]),
                "dBIC": dd == pdv or (not pd_.startswith(">") and abs(d - float(pd_)) < 6e-3),
                "decision": c[kind]["decision"] == pub["decision"]}
        c["published"] = pub
        res.append(c)
    return res


def read_published(path, block_col=None, block=None):
    rows = list(csv.reader(open(path, encoding="utf-8")))
    head, body = rows[0], rows[1:]
    il = next(i for i, h in enumerate(head) if h.startswith("ℓ"))
    ib = next(i for i, h in enumerate(head) if h.startswith("BIC"))
    out = []
    for r in body:
        if block_col is not None and not r[block_col].startswith(block):
            continue
        out.append({"logL": r[il], "BIC": r[ib], "rank": r[il + 2], "dBIC": r[il + 3],
                    "decision": r[il + 4]})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources", required=True)
    ap.add_argument("--published", required=True)
    ap.add_argument("--refit-dir")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    P = a.published
    result = {}
    for study, block, scale, digits in [("cr1", "Scenario 1", 1e4, 4), ("cr2", "Scenario 2", 1e3, 3)]:
        rows = rows_for(a.sources, study, a.refit_dir)
        result[f"table1_{study}"] = {"rows": rows, "comparison": compare(
            rows, read_published(os.path.join(P, "table-1.csv"), 0, block), scale, digits)}
    rows = rows_for(a.sources, "ngfA", a.refit_dir)
    result["table2"] = {"rows": rows, "comparison": compare(
        rows, read_published(os.path.join(P, "table-2.csv")), 1e4, 4)}
    for study, block in [("ngfA", "Pathway model A"), ("ngfB", "Pathway model B"),
                         ("ngfC", "Pathway model C")]:
        rows = rows_for(a.sources, study, a.refit_dir)
        result[f"supp_table1_{study}"] = {"rows": rows, "comparison": compare(
            rows, read_published(os.path.join(P, "supplementary-table-1.csv"), 0, block), 1e4, 4)}
    json.dump(result, open(a.out, "w"), indent=1, ensure_ascii=False)
    for k, v in result.items():
        for kind in ("saved", "refit"):
            if kind not in v["comparison"][0]:
                continue
            ok = {f: sum(c[kind]["matches"][f] for c in v["comparison"]) for f in
                  ("logL", "BIC", "rank", "dBIC", "decision")}
            print(f"{k:18s} {kind:5s} of {len(v['comparison'])}: {ok}")


if __name__ == "__main__":
    main()
