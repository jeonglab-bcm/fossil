"""Write package/inst/extdata/fig1_published.csv: the published Fig. 1 densities (read from the
authors' original vector figure, BMC ESM 2) at p = 0.05, 0.10, ..., 0.95, for the curves the
package reproduces (both null curves... all three; the alternative's no-filter and fold-change
curves). Usage: python make_example_published.py published_values.json out.csv"""
import csv
import json
import sys

import numpy as np

pub = json.load(open(sys.argv[1]))["fig1"]["panels"]
rows = []
for panel, curves in (("null", ("none", "foldchange", "variance")), ("alternative", ("none", "foldchange"))):
    for c in curves:
        pts = np.array(pub[panel]["series"][c])
        for u in np.round(np.arange(0.05, 0.951, 0.05), 2):
            rows.append([panel, c, f"{u:.2f}", f"{float(np.interp(u, pts[:, 0], pts[:, 1])):.4f}"])
with open(sys.argv[2], "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["hypothesis", "filter", "p", "density"])
    w.writerows(rows)
print(len(rows), "rows")
