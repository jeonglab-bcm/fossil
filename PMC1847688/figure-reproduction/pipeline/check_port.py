"""Compare the Python port's outputs with the authors' MATLAB code run in GNU Octave.

Usage: python check_port.py <python_outdir> <octave_outdir> <report.json>

Peak lists and classes must agree exactly (same m/z, same count); intensities and
intermediate signals to within 1e-6 relative (both sides are written with 6 decimals).
Exits 1 if anything differs.
"""

import glob
import json
import os
import sys

import numpy as np
import pandas as pd


def compare_numeric(a, b, rtol=1e-6, atol=2e-6):
    if a.shape != b.shape:
        return {"same_shape": False, "python": list(a.shape), "octave": list(b.shape)}
    diff = np.abs(a - b)
    tol = atol + rtol * np.abs(b)
    return {"same_shape": True, "max_abs_diff": float(np.nanmax(diff)), "within_tolerance": bool(np.all(diff <= tol))}


def main(py, oc, out):
    report = {}
    for name in ["p15_raw.csv", "p15_processed.csv", "p15_blocks.csv", "p15_smooth.csv", "p15_norm.csv"]:
        a = np.loadtxt(os.path.join(py, name), delimiter=",", ndmin=2)
        b = np.loadtxt(os.path.join(oc, name), delimiter=",", ndmin=2)
        report[name] = compare_numeric(a, b)

    for name in ["plasma_peaks.csv", "invitro_peaks.csv"]:
        a = pd.read_csv(os.path.join(py, name))
        b = pd.read_csv(os.path.join(oc, name))
        keys = [c for c in a.columns if c in ("spectrum", "conc", "replicate", "mz")]
        r = {"rows_python": len(a), "rows_octave": len(b)}
        r["same_peaks"] = len(a) == len(b) and bool((a[keys].values == b[keys].values).all())
        if r["same_peaks"]:
            num = [c for c in a.columns if c not in keys and c != "file"]
            r.update(compare_numeric(a[num].values, b[num].values))
        report[name] = r

    for path in sorted(glob.glob(os.path.join(oc, "*_classes.csv"))):
        name = os.path.basename(path)
        a = pd.read_csv(os.path.join(py, name)).values
        b = pd.read_csv(path).values
        report[name] = compare_numeric(a, b)

    ok = all(
        r.get("within_tolerance", False) and r.get("same_peaks", True)
        for r in report.values()
    )
    report["all_agree"] = ok
    with open(out, "w") as f:
        json.dump(report, f, indent=2)
    print(json.dumps(report, indent=2))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main(*sys.argv[1:4])
