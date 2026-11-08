"""Write the bundled example input from the reproduction's analytic data set.

Usage: python scripts/make_example_data.py ANALYTIC.csv src/diabclass/data/nhanes_example.csv

ANALYTIC.csv is written by PMC2850872/figure-reproduction/pipeline/cohort.py from the NHANES
1999-2004 public-use files (public domain, US National Center for Health Statistics).

The example is scheme I (diabetes, diagnosed or not, against everyone else): a balanced training
set of 100 cases and 100 non-cases, and a test set of 60 cases and 180 non-cases, drawn at random
(seed 2010). The training set is already balanced so that the package's undersampling keeps
every row and an independent implementation (R, scripts/expected_from_r.R) trains on the same rows.
"""

import sys

import numpy as np
import pandas as pd

COLS = ["family_history", "age", "race", "weight", "height", "waist", "bmi", "hypertension",
        "weight_mec6"]


def main(src, dst):
    d = pd.read_csv(src)
    rng = np.random.default_rng(2010)
    cases = d[d.scheme_I_case == 1]
    non = d[d.scheme_I_case == 0]
    ci = rng.permutation(cases.index.values)
    ni = rng.permutation(non.index.values)
    parts = [
        d.loc[ci[:100]].assign(set="train"), d.loc[ni[:100]].assign(set="train"),
        d.loc[ci[100:160]].assign(set="test"), d.loc[ni[100:280]].assign(set="test"),
    ]
    e = pd.concat(parts)
    e = e.assign(case=e.scheme_I_case.astype(int))
    e = e[["set", "case"] + COLS].reset_index(drop=True)
    e.insert(0, "id", np.arange(1, len(e) + 1))
    e["weight_mec6"] = e.weight_mec6.round(1)
    e.to_csv(dst, index=False)
    print(f"{len(e)} rows -> {dst}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
