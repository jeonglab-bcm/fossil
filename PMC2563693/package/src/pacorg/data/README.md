# Example data

| File | What it is |
| --- | --- |
| `example.gct` | Example expression matrix (GCT 1.2): 120 genes G001 to G120, 40 samples S01 to S40, on a log2-like scale. |
| `example.cls` | Class labels (CLS): S01 to S20 `case`, S21 to S40 `control`. |
| `example.gmt` | Four gene sets (GMT): SET_UP (12 genes), SET_DOWN (10), SET_MIXED (15), SET_NULL (8). |
| `example_expected.csv` | Expected output: for each set, its CORGs, Tian's score and S(G), the t statistic of the CORG activity. |

## Where it comes from

- Input: synthetic, written by `scripts/make_example_data.py` (seed 2008). Each value is 8 + 0.5 × (standard normal noise + shift); the shifts are planted in the case samples: G001, G002, G003 up by 1.6, 1.2 and 0.9 noise SDs (SET_UP), G021 and G022 down by 1.4 and 1.0 (SET_DOWN), G041 up and G042 down by 1.3 (SET_MIXED); SET_NULL has none. Values are rounded to three decimals.
- Expected output: computed in the same script with `scipy.stats.ttest_ind` and plain loops written for it, not with this package (z-score each gene, rank members by t, add genes while |t| of the combined z-score rises). Labels sort as `case`, `control`, so `control` is the case class of every t statistic, as in the package.
- The paper's own data are not bundled: the lung datasets are distributed by the Broad Institute's GSEA site without a stated licence. The tutorial shows how to run the package on them and get the CORGs of the paper's Table 1.
- Licence: synthetic data, released with the package under its MIT licence.

Compare the CORG lists exactly and the scores with a relative tolerance of 1e-9.
