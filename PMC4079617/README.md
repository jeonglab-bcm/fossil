# PMC4079617: Robust Poisson against log-binomial models when outliers are present (Chen et al. 2014)

Chen W, Shi J, Qian L, Azen SP. Comparison of robustness to outliers between robust poisson models and log-binomial
models when estimating relative risks for common binary outcomes: a simulation study. *BMC Medical Research
Methodology* 14:82 (2014). [doi:10.1186/1471-2288-14-82](https://doi.org/10.1186/1471-2288-14-82) ·
[PMC4079617](https://pmc.ncbi.nlm.nih.gov/articles/PMC4079617/) · issue [#74](https://github.com/jeonglab-bcm/fossil/issues/74)

The paper is © 2014 Chen et al., licensee BioMed Central, under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). This folder does not contain the paper, its full text or
its supplements. It holds Fig. 1 as published (`figure-reproduction/published/fig1.png`, the 300 dpi image embedded
in the article PDF) for comparison, with this attribution, as the licence allows. The printed numbers of Tables 1-3,
of Tables A1-A3 (Additional file 2) and the design of Additional file 1 are in
`figure-reproduction/output/published_values.json`, read from the article XML and the supplement PDFs by
`extract_published.py`.

The paper compares two ways of estimating a relative risk for a common binary outcome, robust (modified) Poisson
regression and log-binomial regression (with the COPY method when the log-binomial fit does not converge), in a
SAS 9.2 simulation: 24 scenarios of RR, outcome rate, association and a linear or quadratic confounder, each at
0%, 2% and 5% contamination (outcomes flipped at the extremes of the outcome probability), 1,000 data sets of
n = 1500 (Tables 1-3, Fig. 1) and n = 500 (Additional file 2). It released no code, and the COPY macro is no longer
online. We rebuilt both fits, the design and the contamination from the text as the Python package
[`package/`](package/) (`robustrr`), reran every scenario and compared every printed cell, Fig. 1 and every
quantitative statement of the text.

| Folder | Content |
| --- | --- |
| [`figure-reproduction/`](figure-reproduction/) | The Nextflow pipeline: the simulation, the comparison with every printed cell, Fig. 1, the claims, the cross-check of the fits, the checks. |
| [`package/`](package/) | `robustrr`, the method as an installable Python package, with example data, tests and an [executed tutorial](package/tutorial/TUTORIAL.md). |
| [`results.json`](results.json) | Every table, figure panel and claim of the paper, with our values and computed verdicts. |
| [`session/`](session/) | The ledger of the session that made this reproduction. |

Results page: <https://jeonglab-bcm.github.io/fossil/PMC4079617/>

## Results

<!-- summary from results.json (check_results.py); the full table, with the causes: figure-reproduction/README.md -->

<!--RESULTS-SUMMARY-->
1 exact, 21 agrees, 3 partly, 1 inconclusive, 2 not attempted; 1 open causes.

| Item | Verdict | Measure |
| --- | --- | --- |
| Additional file 1, the 24 scenarios: exposure 50% and outcome 10, 25 or 40% | exact | 48 of 48 fields as printed |
| Table 1, relative bias (%) of the log RR, n = 1500 (18 rows x 8 cells) | agrees | 144 of 144 fields as printed |
| Fig. 1A, relative bias, linear Z, moderate association (n = 1500) | agrees | 95.79% within 2.0 px (pass 95.0%, best control 73.6%) |
| Fig. 1B, relative bias, linear Z, strong association (n = 1500) | partly | 68.37% within 2.0 px (pass 95.0%, best control 56.8%) |
| Fig. 1C, relative bias, non-linear Z, moderate association (n = 1500) | inconclusive | 41.30% within 2.0 px (pass 95.0%, best control 51.3%) |
| Fig. 1D, relative bias, non-linear Z, strong association (n = 1500) | partly | 88.57% within 2.0 px (pass 95.0%, best control 83.8%) |
| Fig. 1 draws Table 1 (the published vertices read back) | agrees | 121 of the 123 vertices of Fig. 1 that can be read (of 144) lie within 1 point of Table 1 as printed; largest difference 1.09 points |
| Table 2, empirical SE of the log RR, n = 1500 (18 rows x 8 cells) | agrees | 144 of 144 fields as printed |
| Table 3, MSE of the log RR, n = 1500 (18 rows x 8 cells) | agrees | 143 of 143 fields as printed, 1 paper errors |
| Additional file 2, Table A1, relative bias (%), n = 500 | agrees | 144 of 144 fields as printed |
| Additional file 2, Table A2, empirical SE, n = 500 | agrees | 144 of 144 fields as printed |
| Additional file 2, Table A3, MSE, n = 500 | agrees | 144 of 144 fields as printed |
| Results: with contamination every relative bias is negative | agrees | 1 of 1 fields as printed |
| Results: lower outcome rates go with larger biases | agrees | 2 of 2 fields as printed |
| Results: linear Z, log-binomial 3.5% to 6.7% more biased at outcome 10% and 5% contamination | agrees | 3 of 3 fields as printed |
| Results: non-linear Z, robust Poisson less biased from 2% contamination on | agrees | 3 of 3 fields as printed |
| Results: without contamination the two SEs are identical at the 2nd decimal | agrees | 1 of 1 fields as printed, 1 paper errors |
| Results: with contamination, comparable SEs at outcome 25% and 40%, log-binomial higher at 10% | agrees | 2 of 2 fields as printed |
| Results: the MSEs follow the biases | agrees | 2 of 2 fields as printed |
| Results: the same pattern at n = 500, with larger SEs | agrees | 2 of 2 fields as printed |
| Discussion: no difference between the models without outliers | agrees | 1 of 1 fields as printed |
| Discussion: COPY converged in all fits of 48 of 48 linear and 30 of 48 non-linear scenarios | partly | 1 of 2 fields as printed |
| Main claim: comparable models with a linear Z; robust Poisson less biased with a quadratic Z from 2% contamination on | agrees | 2 of 2 fields as printed |
| Discussion: results cited from Petersen and Deddens (three decimals with 10,000 copies; 70% to 100% convergence) | not attempted | not attempted |
| Each statement of the text recomputed from the paper's own tables | agrees | 18 of 19 statements follow from the paper's own tables. Not: text.se_uncontaminated: Table 2, 0% rows: LB and RP SEs equal at the 2nd decimal in all 24 pairs (yes against no). |
| robustrr's fits against statsmodels and an independent maximizer | agrees | 60 contaminated data sets (8 COPY fits): robust Poisson coefficients equal statsmodels' to 1e-12 and the sandwich SE its HC0 SE to a relative 3e-12; log-binomial coefficients equal an independent maximizer's to 1e-06, with a likelihood at least as high (to 1e-13) and a score of at most 4e-06 |
| The authors' SAS 9.2 program and COPY macro | not attempted | not attempted |
| Python package robustrr and its tutorial | agrees | robustrr 0.1.0: wheel installed in a fresh environment and imported from it; tests 8 passed; tutorial 6 cells compared, 0 skipped (nondeterministic); TUTORIAL.md in sync |
<!--/RESULTS-SUMMARY-->

<!--CLAIMS-LINE-->
The main claim holds. Every claim about bias, SE and MSE holds on our run. The one table cell that misses is a misprint in Table 3 (0.013 where the paper's own bias and SE give 0.0351), and the convergence count of the Discussion belongs to SAS's optimizer, which we cannot run.
<!--/CLAIMS-LINE-->

## What is kept local

Git-ignored: `sources/` (the article XML, text and PDF, the supplements and figure as downloaded), `work/`
(scratch runs) and `.venv/`. `figure-reproduction/pipeline/fetch_inputs.sh` downloads every input again and checks
its SHA-256.
