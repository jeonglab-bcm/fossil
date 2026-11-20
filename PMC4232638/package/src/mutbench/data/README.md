# Example data

| File | What it is |
| --- | --- |
| `oncogene_snvs.csv` | Example input: the 176 SNVs in the six oncogenes of the paper (BRAF, EGFR, ERBB2, KIT, KRAS, PIK3CA) whose effect was tested (169 non-neutral, 7 neutral). Columns `gene`, `mutation`, `label`, then the category each of the 15 predictors gave (empty: no call). |
| `oncogene_expected.csv` | Expected output: the point values the paper prints for these SNVs in Additional file 16 (accuracy, sensitivity, specificity, PPV and NPV in percent, composite score 0 to 4). |

## Where it comes from

- Input: Additional file 2 of Martelotto et al. (2014), the rows with `SNV` in column K, `Oncogene` in column A and a functional classification of `non-neutral` or `neutral`. The data of the article are released under the Creative Commons Public Domain Dedication (CC0 1.0); the article itself is CC BY 4.0.
- Expected output: Additional file 16, "ONCOGENES (n=176)", as printed, read from the supplement PDF by the reproduction's pipeline (`figure-reproduction/output/published_values.json`). It comes from the paper, not from this package.
- Both files are written by `scripts/make_example_data.py`.

Compare at the printed precision: half a unit in the last printed digit (82.39 means 82.385 to 82.395).

Citation: Martelotto LG, Ng CKY, De Filippo MR, et al. Benchmarking mutation effect prediction algorithms using functionally validated cancer-related missense mutations. Genome Biology 15:484 (2014). doi:10.1186/s13059-014-0484-1
