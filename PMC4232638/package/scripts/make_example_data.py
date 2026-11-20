"""Write the bundled example data from the paper's Additional file 2 and Additional file 16.

Usage (from the repository root, after the pipeline has run once so that the inputs exist):
  python3 PMC4232638/package/scripts/make_example_data.py ADDITIONAL_FILE_2.xlsx \
      PMC4232638/figure-reproduction/output/published_values.json PMC4232638/package/src/mutbench/data

oncogene_snvs.csv       the 176 functionally labelled SNVs in the six oncogenes (BRAF, EGFR, ERBB2, KIT,
                        KRAS, PIK3CA): gene, mutation, label, and the category each of the 15 predictors gave
oncogene_expected.csv   Additional file 16's printed point values for the oncogenes (percent, composite
                        0 to 4), read from the paper's supplement PDF by the pipeline: the expected output
                        comes from the paper, not from this package.
"""
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "figure-reproduction" / "pipeline"))
from data import PRED, load  # noqa: E402

xlsx, published, out = sys.argv[1:4]
out = Path(out)
rows = [r for r in load(xlsx) if r["snv"] and r["type"] == "Oncogene" and r["label"] in ("neutral", "non-neutral")]
with open(out / "oncogene_snvs.csv", "w", newline="") as f:
    w = csv.writer(f, lineterminator="\n")
    w.writerow(["gene", "mutation", "label"] + PRED)
    for r in rows:
        w.writerow([r["gene"], r["aa"], r["label"]] + [r["cat"][p] or "" for p in PRED])
pub = json.load(open(published))["af16"]["oncogenes"]
STATS = ["accuracy", "sensitivity", "specificity", "ppv", "npv", "composite"]
with open(out / "oncogene_expected.csv", "w", newline="") as f:
    w = csv.writer(f, lineterminator="\n")
    w.writerow(["predictor"] + STATS)
    for p in PRED:
        w.writerow([p] + [pub[p][k][0].rstrip("%") for k in STATS])
print(f"{len(rows)} SNVs", file=sys.stderr)
