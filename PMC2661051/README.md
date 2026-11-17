# PMC2661051: A general modular framework for gene set enrichment analysis (Ackermann and Strimmer 2009)

Ackermann M, Strimmer K. A general modular framework for gene set enrichment analysis.
*BMC Bioinformatics* 10:47 (2009). [doi:10.1186/1471-2105-10-47](https://doi.org/10.1186/1471-2105-10-47),
[PMC2661051](https://pmc.ncbi.nlm.nih.gov/articles/PMC2661051/), issue
[jeonglab-bcm/fossil#64](https://github.com/jeonglab-bcm/fossil/issues/64).

The paper is © 2009 Ackermann and Strimmer; licensee BioMed Central Ltd, published under the
[Creative Commons Attribution License 2.0](https://creativecommons.org/licenses/by/2.0/). This folder
does not contain the paper or its full text; `figure-reproduction/published/` holds Figs 2 to 4 (the
Springer original files, converted to PNG, unchanged) for comparison, under that licence and with this
attribution.

The paper splits gene set enrichment into modules (a gene-level statistic, a transformation, a gene set
statistic and a significance assessment, plus globaltest and Hotelling's T-squared), compares 261
combinations by simulation (Tables 2 to 6) and analyses the p53 (Figs 2 and 3) and Hedenfalk (Fig. 4,
Table 7) data. All of it was done in R, and none of the code was released. We rebuilt every module from
the paper's text as the R package [`package/`](package/) (`gseamod`), reran the simulation study (100
data sets, 1000 random sets and permutations each) and redid both data analyses from public copies of
the data.

| Folder | Content |
| --- | --- |
| [`figure-reproduction/`](figure-reproduction/) | The Nextflow pipeline: inputs, the simulation study, the p53 and Hedenfalk analyses, Tables 2 to 7, Figs 2 to 4, the text's claims, and the check against the committed outputs. |
| [`package/`](package/) | `gseamod`, the method as an installable R package, with example data, tests and a [tutorial](package/tutorial/TUTORIAL.md). |
| [`results.json`](results.json) | Every figure, table and claim of the paper, with our values and computed verdicts. |
| [`session/`](session/) | The ledger of the session that made this reproduction. |

Results page: <https://jeonglab-bcm.github.io/fossil/PMC2661051/>

Install the package: `remotes::install_github("jeonglab-bcm/fossil/PMC2661051/package")`.

## Results

<!-- summary and table from results.json (check_results.py --markdown); do not edit by hand -->
<!--RESULTS-SUMMARY-->
19 exact, 7 agrees, 9 partly, 6 differs, 5 not attempted; 11 open causes.

| Item | Verdict | Measure |
| --- | --- | --- |
| Table 1, methods in the literature | not attempted | not attempted |
| Fig. 1, the five modules | not attempted | not attempted |
| Text: 3 x 5 x 6 x 3 - 9 = 261 variants | exact | 1 of 1 fields as printed |
| Table 2, gene-level statistic x transformation (mean, resampling) | agrees | 135 of 135 fields as printed |
| Table 3, gene set statistics (squared mod.t, resampling) | partly | 51 of 54 fields as printed |
| Table 4, significance assessment (mean of squared mod.t) | exact | 36 of 36 fields as printed |
| Table 5, globaltest | partly | 35 of 36 fields as printed |
| Table 6, Hotelling T2 with a shrinkage correlation | partly | 25 of 27 fields as printed |
| Text check: Tables 2, 3 and 4 print the same squared mod.t / mean / resampling cell | exact | 9 of 9 fields as printed |
| Text: untransformed statistics miss sets 6 to 9 | exact | 1 of 1 fields as printed |
| Text: squaring finds sets 6 to 9 | exact | 1 of 1 fields as printed |
| Text: squaring lowers sets 1, 2, 4 and 5 slightly | exact | 1 of 1 fields as printed |
| Text: rank squared performs best overall | agrees | 1 of 1 fields as printed |
| Text: (rank) squared beats binary and local fdr | agrees | 1 of 1 fields as printed |
| Text: median and Wilcoxon beat the mean on correlated sets | exact | 1 of 1 fields as printed |
| Text: with permutation that advantage vanishes (data not shown) | exact | 1 of 1 fields as printed |
| Text: ES is weaker than the mean | exact | 1 of 1 fields as printed |
| Text: the parametric null gives the best rates | exact | 1 of 1 fields as printed |
| Text: restandardization performs like resampling | exact | 1 of 1 fields as printed |
| Text: permutation detects uncorrelated sets more easily | exact | 1 of 1 fields as printed |
| Text: globaltest is very close to the mean of squared statistics | differs | 0 of 1 fields as printed |
| Text: Hotelling hardly detects the correlated sets | exact | 1 of 1 fields as printed |
| Text: Hotelling improves with permutation | exact | 1 of 1 fields as printed |
| Text: p53 data, 50 cell lines, 8,768 genes, 290 sets of 15 to 321 genes | agrees | 8 of 8 fields as printed |
| Fig. 2 left, significant p53 sets against the cutoff | not attempted | not attempted |
| Fig. 2 right, p53 sets with p <= 0.01 | partly | 9 of 16 fields as printed |
| Text: p53, Hotelling and cond. FDR find the most sets (resampling) | differs | 0 of 1 fields as printed |
| Text: p53, Hotelling and cond. FDR find the most sets (permutation) | differs | 0 of 1 fields as printed |
| Text: p53, ES, median and Wilcoxon find the fewest sets (resampling) | differs | 0 of 1 fields as printed |
| Text: p53, ES, median and Wilcoxon find the fewest sets (permutation) | differs | 0 of 1 fields as printed |
| Fig. 3 top, mean pairwise correlation of the 290 p53 sets | partly | 8 of 31 fields as printed |
| Fig. 3 bottom, mean absolute pairwise correlation | partly | 11 of 40 fields as printed |
| Text: correlations within p53 sets are comparatively weak | agrees | 1 of 1 fields as printed |
| Text: Hedenfalk data, 7 BRCA1 and 8 BRCA2, 2,200 mapped genes, 89 sets | partly | 3 of 5 fields as printed |
| Fig. 4 left, significant Hedenfalk sets against the cutoff | not attempted | not attempted |
| Fig. 4 right, Hedenfalk sets with p <= 0.01 | partly | 1 of 16 fields as printed |
| Text: Hedenfalk, resampling finds very few sets | differs | 0 of 1 fields as printed |
| Text: Hedenfalk, Hotelling, mean, maxmean and globaltest find the most sets | exact | 1 of 1 fields as printed |
| Text: Hedenfalk, cond. FDR is conservative | exact | 1 of 1 fields as printed |
| Table 7, Hedenfalk sets with p <= 0.01 (mean, permutation) | partly | 27 of 42 fields as printed |
| Text: breast_cancer_estrogen_signalling first by the mean, outside the ES top 20 | exact | 2 of 2 fields as printed |
| Table 8, contingency table notation (Appendix) | not attempted | not attempted |
| Main claim: the mean of squared mod.t beats GSEA's ES | exact | 1 of 1 fields as printed |
| Main claim: the mean of squared mod.t beats Hotelling | exact | 1 of 1 fields as printed |
| Claims recomputed from the paper's own tables | agrees | 22 of 22 claims come back from the paper's own tables and figure bars |
| R package gseamod and its tutorial | agrees | R package gseamod: R CMD check OK; tests 11 passed, 0 failed, 0 skipped; tutorial rendering equals the committed TUTORIAL.md |
<!--/RESULTS-SUMMARY-->

For a simulated detection rate, "exact" means within its Monte Carlo band: a 99% band for two shares
of 100 data sets, fixed before the comparison. Neither the seeds nor the code survive, so no rate can
come back to the digit.

The main claims hold: the mean of squared moderated t beats ES and Hotelling; Tables 2, 4 and 5 come back and Tables 3 and 6 partly. Of the claims that do not match, four come from our cond. FDR, which is not the paper's, one from the Hedenfalk gene mapping and one from Monte Carlo error (globaltest against the mean).

## Kept local, not in the repository

`sources/` (the paper, its text and figure files, the downloaded data) and `work/` (scratch runs) are
git-ignored. The data are downloaded by `figure-reproduction/pipeline/fetch_inputs.sh`.
