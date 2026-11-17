"""Build the analytic data set of Yu et al. (2010) from NHANES 1999-2004, and Table 1.

Usage: cohort.py DOWNLOADS OUTDIR

Writes OUTDIR/analytic.csv (one row per person in Table 1, with the model variables in plain
units, the design variables and weights) and OUTDIR/table1.json (our counts, the paper's, and
the definition variants we tried).

Definitions (paper, Methods and Table 1): non-pregnant adults aged 20 or over; diagnosed
diabetes = "yes" to DIQ010; otherwise fasting plasma glucose (LBXGLU) >= 126 undiagnosed,
100-125 pre-diabetes, < 100 no diabetes. What the paper does not say, and we chose (each is an
assumption in results_notes.json): glucose only for people fasting at least 8 hours (PHAFSTHR,
the NHANES fasting-weight rule); "borderline" (DIQ010 = 3) counted as not diagnosed; people
with a missing model variable dropped (Table 1 counts are complete cases on the scheme I
variables); family history and hypertension "don't know" counted as no.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

CYCLES = {"1999": ("", "LAB10AM"), "2001": ("_B", "L10AM_B"), "2003": ("_C", "L10AM_C")}
PAPER = {"diagnosed": 1266, "undiagnosed": 195, "prediabetes": 1576, "none": 3277,
         "scheme_I_cases": 1461, "scheme_I_noncases": 4853,
         "scheme_II_cases": 1709, "scheme_II_noncases": 3206}
RACE = {3: "nh_white", 4: "nh_black", 1: "mexican_american", 5: "other", 2: "other_hispanic"}
# Physical activity: PAD320, "moderate activity over the past 30 days" (1 yes, 2 no; 3 unable,
# 7 refused, 9 don't know are missing). Chosen among the NHANES 1999-2004 activity items as the
# one whose missing values best match the drop from Table 1's category sums to the scheme II
# totals; see the "pa_variants" record in table1.json.
PA_VAR = "PAD320"


def read(path):
    return pd.read_sas(path, format="xport")


def load(downloads: Path) -> pd.DataFrame:
    parts = []
    for year, (s, lab) in CYCLES.items():
        m = read(downloads / f"DEMO{s}.xpt")
        m["cycle"] = year
        for f in ["DIQ", "BMX", "BPQ", "MCQ", "PAQ", "PH"]:
            t = read(downloads / f"{f}{s}.xpt")
            m = m.merge(t[[c for c in t.columns if c == "SEQN" or c not in m.columns]],
                        on="SEQN", how="left")
        g = read(downloads / f"{lab}.xpt")[["SEQN", "LBXGLU"]]
        parts.append(m.merge(g, on="SEQN", how="left"))
    return pd.concat(parts, ignore_index=True)


def categorize(a: pd.DataFrame, fasting_hours=8.0, borderline="not_diagnosed",
               dont_know="no", require_body=True) -> pd.Series:
    """Diabetes category of each row, or NaN when the person is not in Table 1."""
    ok = pd.Series(True, index=a.index)
    keep = [1, 2, 7, 9] if dont_know == "no" else [1, 2]
    ok &= a.MCQ250A.isin(keep) & a.BPQ020.isin(keep)
    if require_body:
        for c in ["BMXWT", "BMXHT", "BMXWAIST", "BMXBMI"]:
            ok &= a[c].notna()
    diag = a.DIQ010 == 1
    notdiag = a.DIQ010.isin([2, 3] if borderline == "not_diagnosed" else [2])
    if borderline == "diagnosed":
        diag |= a.DIQ010 == 3
    g = a.LBXGLU
    fasted = g.notna()
    if fasting_hours is not None:
        fasted &= a.PHAFSTHR >= fasting_hours
    cat = pd.Series(np.nan, index=a.index, dtype=object)
    cat[ok & diag] = "diagnosed"
    nd = ok & notdiag & fasted
    cat[nd & (g >= 126)] = "undiagnosed"
    cat[nd & (g >= 100) & (g < 126)] = "prediabetes"
    cat[nd & (g < 100)] = "none"
    return cat


def counts(cat: pd.Series) -> dict:
    vc = cat.value_counts()
    return {k: int(vc.get(k, 0)) for k in ["diagnosed", "undiagnosed", "prediabetes", "none"]}


def main(downloads, outdir):
    downloads, outdir = Path(downloads), Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    df = load(downloads)
    a = df[(df.RIDAGEYR >= 20) & (df.RIDEXPRG != 1)].copy()

    # Definition variants, for the record (Table 1 cause in results_notes.json).
    variants = []
    for fh in [8.0, None]:
        for bl in ["not_diagnosed", "excluded", "diagnosed"]:
            for dk in ["no", "missing"]:
                c = counts(categorize(a, fh, bl, dk))
                dist = sum(abs(c[k] - PAPER[k]) for k in c)
                variants.append({"fasting_hours_min": fh, "borderline": bl, "dont_know": dk,
                                 **c, "abs_diff_from_paper": dist})
    for fh in [6.0, 7.0, 9.0]:
        c = counts(categorize(a, fh))
        variants.append({"fasting_hours_min": fh, "borderline": "not_diagnosed", "dont_know": "no",
                         **c, "abs_diff_from_paper": sum(abs(c[k] - PAPER[k]) for k in c)})
    variants.sort(key=lambda v: v["abs_diff_from_paper"])

    a["category"] = categorize(a)
    t = a[a.category.notna()].copy()

    # Physical activity variants (scheme II complete cases).
    s2 = t[t.category != "diagnosed"]
    pa_variants = []
    for v in ["PAD020", "PAQ100", "PAD200", "PAD320", "PAQ180"]:
        okv = s2[v].isin([1, 2]) if v != "PAQ180" else s2[v].isin([1, 2, 3, 4])
        cases = int((okv & s2.category.isin(["undiagnosed", "prediabetes"])).sum())
        non = int((okv & (s2.category == "none")).sum())
        pa_variants.append({"variable": v, "scheme_II_cases": cases, "scheme_II_noncases": non,
                            "abs_diff_from_paper": abs(cases - PAPER["scheme_II_cases"])
                            + abs(non - PAPER["scheme_II_noncases"])})

    out = pd.DataFrame({
        "seqn": t.SEQN.astype(int),
        "cycle": t.cycle,
        "category": t.category,
        "family_history": (t.MCQ250A == 1).astype(int),
        "age": t.RIDAGEYR,
        "race": t.RIDRETH1.astype(int).map(RACE),
        "weight": t.BMXWT,
        "height": t.BMXHT,
        "waist": t.BMXWAIST,
        "bmi": t.BMXBMI,
        "hypertension": (t.BPQ020 == 1).astype(int),
        "sex": t.RIAGENDR.map({1.0: "male", 2.0: "female"}),
        "physical_activity": t[PA_VAR].map({1.0: 1, 2.0: 0}),
        "glucose": t.LBXGLU,
        "sdmvstra": t.SDMVSTRA.astype(int),
        "sdmvpsu": t.SDMVPSU.astype(int),
        # Six-year MEC weights, as NCHS advises for combining 1999-2002 and 2003-2004.
        "weight_mec6": np.where(t.cycle == "2003", t.WTMEC2YR / 3, t.WTMEC4YR * 2 / 3),
    })
    out["scheme_I_case"] = out.category.isin(["diagnosed", "undiagnosed"]).astype(int)
    s2case = out.category.isin(["undiagnosed", "prediabetes"]).astype(float)
    s2case[(out.category == "diagnosed") | out.physical_activity.isna()] = np.nan
    out["scheme_II_case"] = s2case
    out = out.sort_values("seqn").reset_index(drop=True)
    out.to_csv(outdir / "analytic.csv", index=False, float_format="%.6g")

    ours = counts(out.category)
    ours["scheme_I_cases"] = int(out.scheme_I_case.sum())
    ours["scheme_I_noncases"] = int((out.scheme_I_case == 0).sum())
    ours["scheme_II_cases"] = int((out.scheme_II_case == 1).sum())
    ours["scheme_II_noncases"] = int((out.scheme_II_case == 0).sum())
    rec = {"paper": PAPER, "ours": ours, "adults_20_plus_not_pregnant": int(len(a)),
           "physical_activity_variable": PA_VAR,
           "definition_variants": variants, "pa_variants": pa_variants}
    (outdir / "table1.json").write_text(json.dumps(rec, indent=2) + "\n")
    print(json.dumps(ours))


if __name__ == "__main__":
    main(*sys.argv[1:3])
