# Example data

| File | What it is | Source |
| --- | --- | --- |
| `szabo2004_breast.csv` | Relative copy numbers of six candidate housekeeper genes (MRPL19, PSMC4, SF3A1, PUM1, GAPD, ACTB) in 80 primary breast tumours (T1-T80), measured by real-time quantitative RT-PCR on the LightCycler. | Additional data file 1 of Szabo et al. (2004), `gb-2004-5-8-r59-s1.xls`, sheet "Relative copy numbers". Values unchanged; the column `PUM` is named `PUM1`, as in the paper, and samples 1-80 are named T1-T80. |
| `synthetic_tissues.csv` | Synthetic data for Model 2: five genes (G1-G5) in three tissue types (A, B, C) of 60 samples each, drawn from Model 2 with known parameters (seed 20041). | Written by `scripts/make_example_data.R` (in the package source). |
| `synthetic_truth.csv` | The parameters the synthetic data were drawn from: sigma_j, varsigma_k and the biases (CG)_kj. This is the expected output for the Model 2 example; the estimates should come within sampling error (the tutorial allows 15% for sigma and varsigma and 0.25 for the biases, about three standard errors of the noisiest bias). | Set by hand in `scripts/make_example_data.R`, not computed by this package. |
| `szabo2004_expected.csv` | The expected output: Tables 1 and 2 of Szabo et al. (2004) as printed (gene, gene set and value; the sets in the paper's order, separated by `;`). Table 2's row 4 prints "SP3A1", a slip for SF3A1, written here as SF3A1. | Typed from the paper, not computed by this package. |

`scripts/make_example_data.R` (in the package source) writes `szabo2004_breast.csv` from the
downloaded supplement and draws the synthetic data.

## Comparing with the expected output

Compare gene sets as sets and values at the printed precision: half a unit in the last printed digit
(0.0005 for Table 1, 0.00005 for Table 2). On these data the package gives all six Table 1 standard
deviations, every Table 2 gene set and five of the six Table 2 values as printed. The six-gene value
comes out 0.1514 (printed 0.1513), one unit in the last digit away; the tutorial allows that one
unit for Table 2. Tables 3 and 4 need the data of Vandesompele et al. (2002), which are not bundled;
the reproduction, `PMC507884/README.md` in the fossil repository, downloads them.

## Licence

`szabo2004_breast.csv` is part of an open access article published by BioMed Central:

- Szabo A, Perou CM, Karaca M, Perreard L, Palais R, Quackenbush JF, Bernard PS. Statistical
  modeling for selecting housekeeper genes. *Genome Biology* 5:R59 (2004).
  <https://doi.org/10.1186/gb-2004-5-8-r59>. "Copyright © 2004 Szabo et al.; licensee BioMed
  Central Ltd. This is an Open Access article: verbatim copying and redistribution of this article
  are permitted in all media for any purpose, provided this notice is preserved along with the
  article's original URL." Original URL: <http://genomebiology.com/2004/5/8/R59>.

The data of Vandesompele et al. (2002), used for the paper's Model 2, are not bundled: their article
carries a copyright line without a redistribution grant.
