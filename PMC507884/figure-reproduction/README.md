# PMC507884 figure reproduction

Szabo A, Perou CM, Karaca M, Perreard L, Palais R, Quackenbush JF, Bernard PS. Statistical modeling
for selecting housekeeper genes. *Genome Biology* 5:R59 (2004).
[doi:10.1186/gb-2004-5-8-r59](https://doi.org/10.1186/gb-2004-5-8-r59). Licence and what is kept
local: see [`../README.md`](../README.md).

## Results

<!-- full table from ../results.json (check_results.py --markdown); do not edit by hand -->
<!--RESULTS-TABLE-->
5 exact, 12 agrees, 5 partly, 4 differs, 2 not attempted; 6 open causes.

| Item | Verdict | Measure | Why |
| --- | --- | --- | --- |
| Fig. 1a, raw expression of six genes in 80 breast tumours | agrees | 97.36% within 2 px (pass 90.0%, best control 79.7%) |  |
| Fig. 1b, the same on a log scale | agrees | 95.87% within 2 px (pass 90.0%, best control 71.5%) |  |
| Table 1, Model 1a standard deviations | exact | 6 of 6 fields as printed |  |
| Table 1, 95% confidence intervals | partly | 6 of 12 fields as printed | The printed bounds are nlme's approximate intervals, whose numerical Hessian moves them in the third decimal with the order of the rows and the contrasts; across 24 such parameterizations nlme 3.1-164 reaches all 12 printed bounds. Ours, from an accurate Hessian, are within 0.002 of every printed bound. |
| Text: Model 1a has the best BIC of Models 1a, 1b and 1c | agrees | BIC (REML) Model 1a 988.3, 1b 1012.4, 1c 990.6 (rho 0.31); Model 1a lowest |  |
| Text: microarray-selected genes against GAPD and ACTB, p = 0.0014 | agrees | 1 of 1 fields as printed | Assumed: The test: a likelihood ratio test of Model 1a against the model in which the four microarray-selected genes share one variance and GAPD and ACTB another (REML, 4 degrees of freedom) |
| Table 2, best gene set of each size and the SD of its log geometric mean | partly | 10 of 11 fields as printed, 1 paper errors | Every set and five of the six SDs come back as printed; the six-gene SD is 0.151354, printed 0.1513, 0.000004 above the rounding boundary. Optimizer settings, the rounded SDs of Table 1 and truncation do not explain it. |
| Methods: the printed variance of a set's log geometric mean (divided by the set size) | differs | the printed formula (divided by the set size) gives 1 of 6 Table 2 values; divided by its square, 5 of 6 | The formula divides by the set size where Table 2 divides by its square: on the paper's own Table 1 the best pair gives 0.1716 with the square (printed 0.1718) and 0.2426 with the size. |
| Text: the four-gene set is lowest, three genes barely worse, two far worse | agrees | the four-gene set is lowest (0.1490); three genes 0.1494, 0.0004 more; two genes 0.1718, 0.0224 more than three |  |
| Text: the SDs of Table 2 are about the coefficients of variation on the original scale | agrees | the coefficient of variation sqrt(exp(SD^2) - 1) of each Table 2 normaliser is within 1.2% of its SD |  |
| Text: geNorm M-values give the same ranking except PUM1 and PSMC4, with MRPL19 and PSMC4 an unordered best pair | exact | 5 of 5 fields as printed |  |
| Methods: the printed bounds on the M-value under Model 1 | differs | under Model 1a's SDs (R = 2.38) the printed bounds sigma_j^2 sqrt(1 + 1/R^2) <= M_j <= sigma_j^2 sqrt(1 + R^2) fail; with sigma_j in place of sigma_j^2 they hold | The bounds print sigma_j^2 where sigma_j belongs (M is a mean of SDs): with sigma_j they hold for Model 1a's SDs, with sigma_j^2 they fail. |
| Methods: the four candidate genes chosen from microarrays | not attempted | not attempted | A SAS selection of genes with 'a small range of expression' and 'the least variance' on 62 arrays (Perou et al. 2000 and cell lines), with no thresholds; it cannot be rerun as described, and its result (the four genes) is the paper's input, not one of its results. |
| Fig. 2, Vandesompele et al.'s data by tissue type | agrees | 93.37% within 2 px (pass 90.0%, best control 85.7%) |  |
| Table 3, Model 2 gene SDs | differs | 0 of 10 fields as printed | Every gene SD comes out below the printed one, by 2.1 to 5.2% (ACTB the most), in the same order. Table 3's figures are not a rounding of ours, and none of the variant fits below reaches them; Fig. 3 draws the printed values, so the authors' fit, or their copy of the data, differed from ours. |
| Table 3, Model 2 tissue multipliers | differs | 0 of 4 fields as printed | The same gap as the gene SDs (table3.sigma): our multipliers are 2.7 to 3.2% higher, so outside bone marrow the SDs varsigma_k sigma_j come within 2.7% of the printed products (bone marrow, where the multiplier is 1, carries the gene SDs' 2.1 to 5.2%). |
| Table 3, the order of the genes (GAPD lowest, then UBC, HPRT1, YWHAZ) | exact | 9 of 9 fields as printed |  |
| Methods: Model 2 has the best BIC of six variance structures | agrees | BIC (REML) Model 2 2241.0; common 2367.4, gene 2276.2, tissue 2334.6, unstructured 2370.8, exchangeable 2245.4 |  |
| Text: the top five genes by mean geNorm rank over tissue types are Table 3's top five, in order | exact | 5 of 5 fields as printed |  |
| Table 4, minimax-MSE gene sets | partly | 15 of 20 fields as printed | Every set comes back; 5 of 10 MSEs are 0.001 off. They follow from Model 2's SDs (table3.sigma, open): with Table 3's printed SDs in place of ours, a sensitivity variant, 9 of 10 MSEs are as printed and the tenth (0.543 against 0.544) within Table 3's rounding. |
| Fig. 3, signed MSE of each gene by tissue type | agrees | 99.66% within 2 px (pass 98.0%, best control 95.9%) |  |
| Fig. 3, squared biases (bar heights in the publisher's R graphics file) | agrees | 50 of 50 fields as printed | Assumed: Published heights read from the R PostScript of Fig. 3 (MOESM5.eps) at 0.01 pt, with the scale of the 0 and 8 tick labels (11.1175 pt per unit) |
| Fig. 3, variances (bar heights in the publisher's R graphics file) | partly | 10 of 50 fields as printed | The variances are (varsigma_k sigma_j)^2 of Table 3, whose gap is open (table3.sigma): ours are 3 to 10% lower in bone marrow and within 5.2% elsewhere. |
| Text: ACTB plus TBP in pooled tissues, MSE 0.35 against individual MSEs above 6 | partly | 3 of 4 fields as printed | Ours is 0.337, printed 0.35: the variance of the pair comes from Model 2's SDs (table3.sigma, open), and ours is 0.320 against 0.331 from Table 3's printed SDs, 3.3% low (ACTB's 5% low, TBP's on the mark). The paper's own Table 3 and Fig. 3 give 0.349. The individual MSEs (6.41 and 6.70) and the opposite signs come back. |
| Text: 80 tumours and 6 genes; 10 genes in 5 tissue types | exact | 4 of 4 fields as printed |  |
| The claims recomputed from the paper's own tables and Fig. 3 | agrees | 8 of 8 claims hold on the paper's own numbers: Table 2's best pair from Table 1, divided by the squared set size (holds, 0.1716 against 0.1718 (the set size gives 0.2426)); the four-gene set lowest in Table 2 (holds, 0.1490); three genes barely worse than four, two far worse (holds, 0.0004 and 0.0224); GAPD lowest in Table 3, then UBC, HPRT1, YWHAZ (holds); ACTB plus TBP in pooled tissues 0.35 (bias of the set summed) (holds, 0.349 (the mean of the biases gives 0.335)); ACTB and TBP individual MSEs in pooled tissues above 6 (holds, 6.45 and 6.70); Table 4's ten-gene MSE from Table 3 (no bias) (holds, 0.0490); Table 4's single gene RPL13A from Table 3 and Fig. 3, within Table 3's rounding (holds, 0.5435 against 0.544) |  |
| Table 5, primers | not attempted | not attempted | Primer sequences, lengths, GC content and melting temperatures: laboratory reagents, nothing computed. |
| R package hkselect and its tutorial | agrees | R package hkselect: R CMD check OK; tests 23 passed, 0 failed, 0 skipped; tutorial rendering equals the committed TUTORIAL.md (figures by name) |  |
<!--/RESULTS-TABLE-->

## What the code does, against the paper

| Paper | Here |
| --- | --- |
| Model 1a, "fitted using the gls routine of the nlme library for R" | `hkselect::fit_model1()`: `nlme::gls(log y ~ sample + gene, weights = varIdent(~ 1 \| gene))`, by REML (nlme's default; the paper does not say). ML does not converge on these data (nlme: false convergence). |
| Table 1's 95% intervals, method not given | Wald intervals on the log SDs from an accurate numerical Hessian of the REML likelihood (`gene_sd_ci()`). nlme's own `intervals()` moves in the third decimal with the order of the rows and the contrasts; `analysis.R` runs it under 24 equivalent parameterizations and their range covers every printed bound. |
| Variance of a set's log geometric mean, printed as sum sigma_j^2 / \|S\| | sum sigma_j^2 / \|S\|^2 (`set_sd()`), the variance of a mean, which gives Table 2; the printed divisor is kept as `divisor = "size"` and shown next to Table 2 on the results page. |
| p = 0.0014, test not named | A likelihood ratio test of Model 1a against one variance for the four microarray-selected genes and one for GAPD and ACTB (`variance_group_test()`, 4 df). Three other readings tried are in `output/analysis.json` (`group_test.alternatives`). |
| Models 1b, 1c and the BIC | `fit_model1(variance = "common")` and `"exchangeable"` (one correlation between the genes of a sample). |
| Vandesompele et al.'s M-value | geNorm's stepwise elimination on natural logs (`genorm()`); for several tissue types, ranks per tissue type averaged with the best pair at 1.5 (`genorm_mean_rank()`). |
| Model 2 and its competitors | `fit_model2()`: fixed sample effects (which absorb C_k), tissue-by-gene effects with sum-to-zero contrasts, `varComb(varIdent(~ 1 \| gene), varIdent(~ 1 \| tissue))`; competitors with one variance, per gene, per tissue type, per gene and tissue type, and Model 2's variance with an exchangeable correlation. |
| MSE of a gene set, described in words | Squared bias plus the variance of the log-average, maximised over tissue types (`set_mse()`), with the bias of a set the **sum** of its genes' (CG)_kj. That reading gives every set of Table 4 and the paper's ACTB plus TBP example (0.349 on the paper's own numbers); the mean of the biases gives 2 of 10 sets, and 0.335 on the paper's numbers (0.324 on ours). |
| Table 4, "maximum number of members" | The best set with at most k genes (`minimax_sets(nested = TRUE)`), an exhaustive search over all 1,023 sets. |
| Fig. 3 | Bias (CG)_kj and variance (varsigma_k sigma_j)^2 of each gene in each tissue type (`gene_mse()`). The publisher keeps two versions: the published one, signed by the bias (MOESM4, drawn over in Illustrator), and R's own unsigned PostScript (MOESM5), whose bar heights `read_published.py` reads at 0.01 pt. |

## Layout

| Path | Content |
| --- | --- |
| `main.nf`, `nextflow.config` | The pipeline. |
| `requirements.txt` | Pinned Python packages (Pillow, NumPy); R is pinned by `pipeline/install_r.sh`. |
| `results_notes.json` | Labels, sources, assumptions and causes of every item, written by hand; the numbers come from the run. |
| `pipeline/fetch_inputs.sh` | Downloads the three inputs and checks their SHA-256 (`--published` also checks `published/` against the publisher's EPS files). |
| `pipeline/prepare_data.R` | The two supplements as tidy CSV files. |
| `pipeline/analysis.R` | Every model, table and claim, with `hkselect`. |
| `pipeline/hypotheses.R` | Variant fits of Model 2 that test why Table 3 differs (rerun with `--full`). |
| `pipeline/read_published.py` | Fig. 3's bar heights from the publisher's R PostScript. |
| `pipeline/figures.py` | Figs 1 to 3 drawn on the published pixel grid, overlays, scores and negative controls. |
| `pipeline/compare.py`, `paper_values.json` | Our values against the printed ones (typed from the paper), and the claims recomputed on the paper's own numbers. |
| `pipeline/build_results.py`, `check_results.py` | `../results.json` and its verdicts. |
| `pipeline/build_page.py`, `page_template.html` | The results page, `site/PMC507884/index.html`. |
| `pipeline/check_r_package.sh` | Builds and checks `../package` and renders its tutorial. |
| `pipeline/check_reproduction.py`, `compare_runs.py` | The fresh run against the committed one. |
| `pipeline/update_readmes.py`, `make_results_check.py` | The README tables, the front-page verdict and the results-check file `results.json` in this folder. |
| `published/` | Figs 1 to 3: the publisher's EPS files (MOESM2 to MOESM4) rendered at 300 dpi with Ghostscript 10.02. |
| `output/` | The committed run: `analysis.json`, `hypotheses.json`, `published_fig3.json`, `figures.json`, `fig3_bars.csv`, `comparison.json`, `tables.json`, `fig*_ours.png`, `fig*_overlay.png`. |

## Run

From the repository root, with R 4.3.3 and the packages of `pipeline/install_r.sh`, Python with
`requirements.txt`, Java 21 and Nextflow 26.04.3:

```bash
nextflow run PMC507884/figure-reproduction/main.nf --outdir results
```

About 5 minutes on 4 cores; most of it is Model 2's competitors and the 24 refits behind Table 1's
intervals. `--full` also reruns the variant fits behind Table 3's cause (about 100 fits, 6 more
minutes on 4 cores); without it they are read from `output/hypotheses.json`. `--sources DIR` copies
inputs from a local folder. CI: `.github/workflows/reproduce-pmc507884.yml` runs the default on every
pull request that touches this paper, and `--full` when started by hand with `full`.

## Pipeline steps

1. **FETCH**: the breast cancer data (`gb-2004-5-8-r59-s1.xls`), Vandesompele et al.'s data
   (`gb-2002-3-7-research0034-s1.TXT`) and the R file of Fig. 3 (`MOESM5.eps`), from Springer's
   static-content server with PMC's open access copy on AWS as the fallback; SHA-256 checked.
2. **INSTALL**: `hkselect` from `../package` into a fresh library.
3. **PREPARE**, **ANALYSIS**: the data as CSV; Models 1a, 1b, 1c and 2 and its competitors, Tables 1
   to 4, the claims, the nlme interval spread and the checks on Table 2's last row.
4. **HYPOTHESES**: the variant fits of Model 2 (`--full`), or the committed results.
5. **READ_PUBLISHED**, **FIGURES**: Fig. 3's printed bar heights; Figs 1 to 3 drawn and scored.
6. **COMPARE**: every value against the paper.
7. **PACKAGE**: `R CMD build`, `R CMD check --no-manual`, and the tutorial rendered and compared with
   `../package/tutorial/TUTORIAL.md`.
8. **RESULTS**: `results.json` from the notes and the comparison; `check_results.py --write`.
9. **PAGE**: the results page and `report.md`.
10. **CHECK**: `check_results.py` on the fresh `results.json`, every verdict equal to the committed one,
    and `compare_runs.py` of the fresh outputs against `output/` (numbers within 1e-9, images by
    decoded pixels). Any difference fails the run.

## Limits

- Model 2's SDs (Table 3) come out 2 to 5% below the printed ones. Neither maximum likelihood, random
  sample effects, dropping the tissue-by-gene term, log10, nor leaving out any one of the 85 samples
  reaches Table 3 (`output/hypotheses.json`). The authors' copy of the pooled tissues may have differed:
  their caption lists small intestine where the file has liver. The Table 4
  MSEs, Fig. 3's variances and the ACTB plus TBP value follow from these SDs.
- Table 2's six-gene SD is 0.151354, printed 0.1513; no optimizer setting moves it across 0.15135.
- The test behind p = 0.0014 and the set MSE rule were found by matching the paper's numbers; each is
  an assumption in `../results.json` with the alternatives tried.
- The figure scores measure where our points and bars sit on the published grid; they top out at
  `agrees`. The residual is marker placement (the down triangles sit about 2 px off) and the order of
  overlapping markers, not the data.
- The microarray pre-selection of the four candidate genes is not rerun: its SAS criteria have no
  thresholds. Table 5 lists primers.
