# PMC507884: Statistical modeling for selecting housekeeper genes (Szabo et al. 2004)

Szabo A, Perou CM, Karaca M, Perreard L, Palais R, Quackenbush JF, Bernard PS. Statistical modeling
for selecting housekeeper genes. *Genome Biology* 5:R59 (2004).
[doi:10.1186/gb-2004-5-8-r59](https://doi.org/10.1186/gb-2004-5-8-r59),
[PMC507884](https://pmc.ncbi.nlm.nih.gov/articles/PMC507884/); correction (author list only)
*Genome Biology* 9:405 (2008), [PMC2575510](https://pmc.ncbi.nlm.nih.gov/articles/PMC2575510/).
Issue [jeonglab-bcm/fossil#96](https://github.com/jeonglab-bcm/fossil/issues/96).

The paper is "Copyright © 2004 Szabo et al.; licensee BioMed Central Ltd. This is an Open Access
article: verbatim copying and redistribution of this article are permitted in all media for any
purpose, provided this notice is preserved along with the article's original URL"
(<http://genomebiology.com/2004/5/8/R59>). This folder does not contain the paper or its full text.
`figure-reproduction/published/` holds Figs 1 to 3 for comparison: the publisher's vector EPS files
of the figures rendered at 300 dpi, unchanged otherwise, under that notice. The package's example data
include the paper's Additional data file 1 (the breast cancer data) under the same notice. The data of
Vandesompele et al. (2002), which Model 2 uses, carry a copyright line without a redistribution grant,
so the pipeline downloads them and the data file is not committed (our Fig. 2 plots them, as the paper's does).

The paper chooses housekeeper genes for normalizing quantitative RT-PCR. Within one tissue type it fits
log expression with sample and gene effects and one error variance per gene (Model 1a), ranks single
genes by that variance (Table 1) and gene sets by the variance of their log geometric mean (Table 2),
on 80 breast tumours. Across tissue types it adds a tissue-specific gene bias and an error SD that is a
gene factor times a tissue factor (Model 2, Table 3), and picks universal gene sets by their largest
mean squared error over tissue types (Table 4, Fig. 3), on Vandesompele et al.'s data. The models were
fitted with R's nlme; no code was released. We rebuilt both models from the paper's text as the R
package [`package/`](package/) (`hkselect`) and reran every table, figure and claim.

| Folder | Content |
| --- | --- |
| [`figure-reproduction/`](figure-reproduction/) | The Nextflow pipeline: inputs, Models 1 and 2, Tables 1 to 4, Figs 1 to 3, the text's claims, the tests of the open causes, and the check against the committed outputs. |
| [`package/`](package/) | `hkselect`, the method as an installable R package, with example data, tests and a [tutorial](package/tutorial/TUTORIAL.md). |
| [`results.json`](results.json) | Every figure, table and claim of the paper, with our values and computed verdicts. |
| [`session/`](session/) | The ledger of the session that made this reproduction. |

Kept local and git-ignored: `sources/` (the paper's XML and text, its supplementary files and figure
files as downloaded, Vandesompele et al.'s supplement).

Results page: <https://jeonglab-bcm.github.io/fossil/PMC507884/>

Install the package: `remotes::install_github("jeonglab-bcm/fossil/PMC507884/package")`.

## Results

<!-- summary and table from results.json (check_results.py --markdown); do not edit by hand -->
<!--RESULTS-SUMMARY-->
5 exact, 12 agrees, 5 partly, 4 differs, 2 not attempted; 6 open causes.

| Item | Verdict | Measure |
| --- | --- | --- |
| Fig. 1a, raw expression of six genes in 80 breast tumours | agrees | 97.36% within 2 px (pass 90.0%, best control 79.7%) |
| Fig. 1b, the same on a log scale | agrees | 95.87% within 2 px (pass 90.0%, best control 71.5%) |
| Table 1, Model 1a standard deviations | exact | 6 of 6 fields as printed |
| Table 1, 95% confidence intervals | partly | 6 of 12 fields as printed |
| Text: Model 1a has the best BIC of Models 1a, 1b and 1c | agrees | BIC (REML) Model 1a 988.3, 1b 1012.4, 1c 990.6 (rho 0.31); Model 1a lowest |
| Text: microarray-selected genes against GAPD and ACTB, p = 0.0014 | agrees | 1 of 1 fields as printed |
| Table 2, best gene set of each size and the SD of its log geometric mean | partly | 10 of 11 fields as printed, 1 paper errors |
| Methods: the printed variance of a set's log geometric mean (divide by | S | ) |
| Text: the four-gene set is lowest, three genes barely worse, two far worse | agrees | the four-gene set is lowest (0.1490); three genes 0.1494, 0.0004 more; two genes 0.1718, 0.0224 more than three |
| Text: the SDs of Table 2 are about the coefficients of variation on the original scale | agrees | the coefficient of variation sqrt(exp(SD^2) - 1) of each Table 2 normaliser is within 1.2% of its SD |
| Text: geNorm M-values give the same ranking except PUM1 and PSMC4, with MRPL19 and PSMC4 an unordered best pair | exact | 5 of 5 fields as printed |
| Methods: the printed bounds on the M-value under Model 1 | differs | under Model 1a's SDs (R = 2.38) the printed bounds sigma_j^2 sqrt(1 + 1/R^2) <= M_j <= sigma_j^2 sqrt(1 + R^2) fail; with sigma_j in place of sigma_j^2 they hold |
| Methods: the four candidate genes chosen from microarrays | not attempted | not attempted |
| Fig. 2, Vandesompele et al.'s data by tissue type | agrees | 93.37% within 2 px (pass 90.0%, best control 85.7%) |
| Table 3, Model 2 gene SDs | differs | 0 of 10 fields as printed |
| Table 3, Model 2 tissue multipliers | differs | 0 of 4 fields as printed |
| Table 3, the order of the genes (GAPD lowest, then UBC, HPRT1, YWHAZ) | exact | 9 of 9 fields as printed |
| Methods: Model 2 has the best BIC of six variance structures | agrees | BIC (REML) Model 2 2241.0; common 2367.4, gene 2276.2, tissue 2334.6, unstructured 2370.8, exchangeable 2245.4 |
| Text: the top five genes by mean geNorm rank over tissue types are Table 3's top five, in order | exact | 5 of 5 fields as printed |
| Table 4, minimax-MSE gene sets | partly | 15 of 20 fields as printed |
| Fig. 3, signed MSE of each gene by tissue type | agrees | 99.66% within 2 px (pass 98.0%, best control 95.9%) |
| Fig. 3, squared biases (bar heights in the publisher's R graphics file) | agrees | 50 of 50 fields as printed |
| Fig. 3, variances (bar heights in the publisher's R graphics file) | partly | 10 of 50 fields as printed |
| Text: ACTB plus TBP in pooled tissues, MSE 0.35 against individual MSEs above 6 | partly | 3 of 4 fields as printed |
| Text: 80 tumours and 6 genes; 10 genes in 5 tissue types | exact | 4 of 4 fields as printed |
| The claims recomputed from the paper's own tables and Fig. 3 | agrees | 8 of 8 claims hold on the paper's own numbers: Table 2's best pair from Table 1 with |
| Table 5, primers | not attempted | not attempted |
| R package hkselect and its tutorial | agrees | R package hkselect: R CMD check OK; tests 23 passed, 0 failed, 0 skipped; tutorial rendering equals the committed TUTORIAL.md (figures by name) |
<!--/RESULTS-SUMMARY-->

## Claims

- **Breast cancer (Model 1a).** Model 1a has the best BIC; MRPL19 is the most stable single gene,
  and every SD of Table 1 comes back as printed. Every best gene set of Table 2 comes back, and
  five of its six SDs; the paper's choice, MRPL19, PUM1 and PSMC4, holds. p = 0.0014 comes back
  from a likelihood ratio test the paper does not name. geNorm's ranking differs from Model 1a's
  only by PUM1 and PSMC4, as the paper says.
- **Across tissue types (Model 2).** Model 2 has the best BIC of the six variance structures the
  paper names, and its gene order is the paper's (GAPD, UBC, HPRT1, YWHAZ, SDHA first, also by
  geNorm averaged over tissue types). Its SDs stay 2 to 5% below Table 3's. Every gene set of
  Table 4 comes back, with half of the maximal MSEs 0.001 off; all 50 squared biases of Fig. 3
  come back within the resolution of the publisher's R file.
- **Formulas.** The printed variance of a set's log geometric mean divides by |S| where Table 2
  uses |S|^2, and the printed M-value bounds use sigma_j^2 where sigma_j belongs. The MSE of a gene
  set is given in words only: Table 4 and the ACTB plus TBP example both need the bias of a set to
  be the sum of its genes' biases, not their mean.

The main claims hold: the best single genes and gene sets come back in both settings; the claims that
do not match are two formula slips, Table 2's last digit, and Model 2's SDs (Table 3, open), from
which the Table 4 and ACTB plus TBP differences follow.
