# Example data

Synthetic, written by `scripts/make_example_data.py` (seed 20040318). Public domain (no third-party data).

| File | Content |
| --- | --- |
| `expression.tsv` | 500 genes x 60 experiments, log2 expression ratios; blank = missing (10 values) |
| `binding_ratio.tsv` | 500 genes x 8 TFs, ChIP enrichment ratios (not logged); blank = missing (5 values) |
| `binding_p.tsv` | 500 genes x 8 TFs, ChIP P-values |
| `expected.json` | what the generating formula planted: the active TFs, their functional targets and non-functional bound genes, and their true activities |

Each TF binds 40 genes. TF1, TF2 and TF3 are active, and 25 of the 40 genes each binds follow its
activity: `E = sum_f a_ft * B_fg * [functional] + noise (sd 0.3)`. The other bound genes, and all genes
bound by TF4 to TF8, do not respond.

**Expected output** (from the formula, not from the package): backward selection keeps exactly
TF1, TF2 and TF3; at least 72 of the 75 functional targets are B+/C+ (a gene with a missing ChIP
ratio is unclassified); none of the 45 non-functional bound genes is B+/C+; each activity profile
correlates with the planted one above 0.95.
