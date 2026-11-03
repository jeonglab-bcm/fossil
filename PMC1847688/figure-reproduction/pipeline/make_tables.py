"""LIMPIC's rows of Tables 1 to 3, and the plasma totals, from our run beside the paper's.

Usage: python make_tables.py <data_dir> <S4_csv> <out_json>

Only LIMPIC's rows can be recomputed: APEX and CENTROID are Bruker FlexAnalysis
(proprietary), and the paper gives neither CROMWELL's settings nor the manual peak lists
that define missed and incorrect classes in Table 2.
"""

import json
import os
import sys

import numpy as np
import pandas as pd

CONCENTRATIONS = ["2.5", "5", "7.5", "10", "25", "50"]
CYTC_MZ = 12360.5  # [M+H]+ of equine cytochrome C, the class every replicate shares at 50 fmol

PAPER = {
    "table1_limpic": {
        "average_intensity": [1.17, 4.65, 5.32, 17.07, 94.03, 277.37],
        "standard_deviation": [0.10, 0.39, 0.61, 2.70, 14.01, 42.48],
        "coefficient_of_variation": [0.09, 0.08, 0.12, 0.16, 0.15, 0.15],
    },
    "table2_limpic_detected_classes": [8, 7, 10, 8, 10, 11],
    "table3_limpic": {
        "in_vitro": {"average_peaks": 16, "classes": 11, "hit_rate": 0.69},
        "plasma": {"average_peaks": 146, "classes": 62, "hit_rate": 0.42},
    },
    "plasma_text": {"peaks": 4382, "classes": 1581, "selected_pdr_0.5": 62},
}


def classes(data, name):
    return pd.read_csv(os.path.join(data, name))


def main(data, s4, out):
    res = {"paper": PAPER}

    # Table 1: the cytochrome C class (within 300 ppm of 12360.5) in the 5 replicates.
    t1 = {"n_replicates_with_peak": [], "average_intensity": [], "standard_deviation": [], "coefficient_of_variation": [], "replicates": []}
    for c in CONCENTRATIONS:
        k = classes(data, f"invitro_{c}_classes.csv")
        near = k[np.abs(k.mz - CYTC_MZ) <= CYTC_MZ * 300e-6]
        row = near.loc[near.n.idxmax()] if len(near) else None
        amps = np.array([row[f"s{i}"] for i in range(1, 6)]) if row is not None else np.zeros(5)
        v = amps[amps > 0]
        t1["n_replicates_with_peak"].append(int(len(v)))
        t1["replicates"].append([round(float(a), 2) for a in amps])
        mean = float(v.mean()) if len(v) else 0.0
        sd = float(v.std(ddof=1)) if len(v) > 1 else None
        t1["average_intensity"].append(round(mean, 2))
        t1["standard_deviation"].append(round(sd, 2) if sd is not None else None)
        t1["coefficient_of_variation"].append(round(sd / mean, 2) if sd is not None and mean else None)
    res["table1_limpic"] = t1

    # Tables 2 and 3: classes with PDR above 0.5 (multiple_spectra.m: n > 0.5 * spectra).
    peaks = pd.read_csv(os.path.join(data, "invitro_peaks.csv"))
    detected = []
    for c in CONCENTRATIONS:
        k = classes(data, f"invitro_{c}_classes.csv")
        detected.append(int((k.n > 2.5).sum()))
    res["table2_limpic_detected_classes"] = detected

    per_spectrum = peaks.groupby(["conc", "replicate"]).size()
    iv_peaks = float(per_spectrum.mean())
    iv_classes = float(np.mean(detected))
    pl = classes(data, "plasma_classes.csv")
    pl_peaks = int(pl.n.sum())
    res["table3_limpic"] = {
        "in_vitro": {"average_peaks": round(iv_peaks, 1), "classes": round(iv_classes, 1), "hit_rate": round(iv_classes / iv_peaks, 2)},
        "plasma": {"average_peaks": round(pl_peaks / 30, 1), "classes": int((pl.n > 15).sum()), "hit_rate": round((pl.n > 15).sum() / (pl_peaks / 30), 2)},
    }
    res["plasma_ours"] = {
        "peaks": pl_peaks,
        "classes": int(len(pl)),
        "selected_pdr_gt_0.5": int((pl.n > 15).sum()),
        "selected_pdr_ge_0.5": int((pl.n >= 15).sum()),
    }
    d = pd.read_csv(s4)
    n = d[" num_elem"]
    res["plasma_additional_file_4"] = {
        "peaks": int(n.sum()),
        "classes": int(len(d)),
        "selected_pdr_gt_0.5": int((n > 15).sum()),
        "selected_pdr_ge_0.5": int((n >= 15).sum()),
    }
    with open(out, "w") as f:
        json.dump(res, f, indent=2)
    print(json.dumps({k: v for k, v in res.items() if k != "paper"}, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:4])
