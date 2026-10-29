"""Evaluate the Python likelihood at the authors' saved optimum of every model and compare it
with the saved log-likelihood (parameters.MS.MAP.logPost) and BIC."""

import argparse
import json

import numpy as np

from odemm import bic, log_likelihood
from saved import STUDIES, load_model, model_list, to_D


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    rows = []
    for study in STUDIES:
        for model in model_list(study):
            spec, m = load_model(args.sources, study, model)
            p = m["parameters"]
            xi = np.asarray(p.MS.MAP.par, float)
            D = to_D(m["D"])
            ll = log_likelihood(spec, xi, D)
            b = bic(ll, int(p.number), D)
            rows.append({"study": study, "model": model, "n_par": int(p.number),
                         "logL_saved": float(p.MS.MAP.logPost), "logL_python": ll,
                         "BIC_saved": float(p.MS.MAP.BIC), "BIC_python": float(b),
                         "abs_diff_logL": abs(ll - float(p.MS.MAP.logPost))})
            print(f"{study:5s} {model:20s} saved {rows[-1]['logL_saved']:14.6f} "
                  f"python {ll:14.6f} diff {rows[-1]['abs_diff_logL']:.2e}", flush=True)
    worst = max(r["abs_diff_logL"] for r in rows)
    json.dump({"max_abs_diff_logL": worst, "models": rows}, open(args.out, "w"), indent=1)
    print("max |difference|:", worst)


if __name__ == "__main__":
    main()
