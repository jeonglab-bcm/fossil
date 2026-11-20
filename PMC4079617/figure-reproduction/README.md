# PMC4079617 figure reproduction

The simulation study of Chen, Shi, Qian and Azen (2014) rebuilt and rerun: all 24 scenarios at 0%, 2% and 5%
contamination, 1,000 data sets each at n = 1500 and n = 500, both models; every printed cell of Tables 1-3 and
A1-A3, Fig. 1 on the published picture, and the statements of the text. The method is the package
[`robustrr`](../package/), implemented from the paper's text.

```bash
nextflow run PMC4079617/figure-reproduction/main.nf --outdir results
```

Results page: <https://jeonglab-bcm.github.io/fossil/PMC4079617/>

## Results

<!--RESULTS-TABLE-->
1 exact, 21 agrees, 3 partly, 1 inconclusive, 2 not attempted; 1 open causes.

| Item | Verdict | Measure | Why |
| --- | --- | --- | --- |
| Additional file 1, the 24 scenarios: exposure 50% and outcome 10, 25 or 40% | exact | 48 of 48 fields as printed |  |
| Table 1, relative bias (%) of the log RR, n = 1500 (18 rows x 8 cells) | agrees | 144 of 144 fields as printed | Assumed: Contamination flips the outcome of the records whose true p_y lies beyond the population's rate/2 and 1 - rate/2 quantiles of p_y (computed exactly for each scenario), so the number flipped varies between data sets (74.9 on average at 5% and n = 1500, SD 8.5). The paper says only 'p_y at bottom or top 1%' (2.5% for 5%) |
| Fig. 1A, relative bias, linear Z, moderate association (n = 1500) | agrees | 95.79% within 2.0 px (pass 95.0%, best control 73.6%) | Ours scores 0.958 against a pass mark of 0.95; the best wrong input scores 0.175 and the best near miss 0.736. At 2 px a pixel score cannot resolve Monte Carlo noise: one point of relative bias is 4.62 px, and the Monte Carlo SE of a 1,000-replicate relative bias is 0.3 to 1.3 points. Two runs of our own simulation with different seeds score only 0.741 against each other in this panel, while the paper's own Table 1 drawn with the same code scores 0.983, so the drawing and the frame are right. The values behind the panel are Table 1: its 36 values for this panel are each within tolerance and sit at an RMS z of 0.43 from the paper's, where our two runs sit at 0.84 from each other. |
| Fig. 1B, relative bias, linear Z, strong association (n = 1500) | partly | 68.37% within 2.0 px (pass 95.0%, best control 56.8%) | Ours scores 0.684 against a pass mark of 0.95; the best wrong input scores 0.156 and the best near miss 0.568. At 2 px a pixel score cannot resolve Monte Carlo noise: one point of relative bias is 4.62 px, and the Monte Carlo SE of a 1,000-replicate relative bias is 0.3 to 1.3 points. Two runs of our own simulation with different seeds score only 0.736 against each other in this panel, while the paper's own Table 1 drawn with the same code scores 0.970, so the drawing and the frame are right. The values behind the panel are Table 1: its 36 values for this panel are each within tolerance and sit at an RMS z of 1.05 from the paper's, where our two runs sit at 1.22 from each other. |
| Fig. 1C, relative bias, non-linear Z, moderate association (n = 1500) | inconclusive | 41.30% within 2.0 px (pass 95.0%, best control 51.3%) | Ours scores 0.413 against a pass mark of 0.95; the best wrong input scores 0.148 and the best near miss 0.513. At 2 px a pixel score cannot resolve Monte Carlo noise: one point of relative bias is 4.62 px, and the Monte Carlo SE of a 1,000-replicate relative bias is 0.3 to 1.3 points. Two runs of our own simulation with different seeds score only 0.674 against each other in this panel, while the paper's own Table 1 drawn with the same code scores 0.954, so the drawing and the frame are right. The values behind the panel are Table 1: its 36 values for this panel are each within tolerance and sit at an RMS z of 1.36 from the paper's, where our two runs sit at 1.12 from each other. |
| Fig. 1D, relative bias, non-linear Z, strong association (n = 1500) | partly | 88.57% within 2.0 px (pass 95.0%, best control 83.8%) | Ours scores 0.886 against a pass mark of 0.95; the best wrong input scores 0.092 and the best near miss 0.838. At 2 px a pixel score cannot resolve Monte Carlo noise: one point of relative bias is 4.62 px, and the Monte Carlo SE of a 1,000-replicate relative bias is 0.3 to 1.3 points. Two runs of our own simulation with different seeds score only 0.714 against each other in this panel, while the paper's own Table 1 drawn with the same code scores 0.956, so the drawing and the frame are right. The values behind the panel are Table 1: its 36 values for this panel are each within tolerance and sit at an RMS z of 0.55 from the paper's, where our two runs sit at 0.70 from each other. |
| Fig. 1 draws Table 1 (the published vertices read back) | agrees | 121 of the 123 vertices of Fig. 1 that can be read (of 144) lie within 1 point of Table 1 as printed; largest difference 1.09 points |  |
| Table 2, empirical SE of the log RR, n = 1500 (18 rows x 8 cells) | agrees | 144 of 144 fields as printed | Assumed: Contamination flips the outcome of the records whose true p_y lies beyond the population's rate/2 and 1 - rate/2 quantiles of p_y (computed exactly for each scenario), so the number flipped varies between data sets (74.9 on average at 5% and n = 1500, SD 8.5). The paper says only 'p_y at bottom or top 1%' (2.5% for 5%) |
| Table 3, MSE of the log RR, n = 1500 (18 rows x 8 cells) | agrees | 143 of 143 fields as printed, 1 paper errors | Assumed: Contamination flips the outcome of the records whose true p_y lies beyond the population's rate/2 and 1 - rate/2 quantiles of p_y (computed exactly for each scenario), so the number flipped varies between data sets (74.9 on average at 5% and n = 1500, SD 8.5). The paper says only 'p_y at bottom or top 1%' (2.5% for 5%) |
| Additional file 2, Table A1, relative bias (%), n = 500 | agrees | 144 of 144 fields as printed | Assumed: Contamination flips the outcome of the records whose true p_y lies beyond the population's rate/2 and 1 - rate/2 quantiles of p_y (computed exactly for each scenario), so the number flipped varies between data sets (74.9 on average at 5% and n = 1500, SD 8.5). The paper says only 'p_y at bottom or top 1%' (2.5% for 5%) |
| Additional file 2, Table A2, empirical SE, n = 500 | agrees | 144 of 144 fields as printed | Assumed: Contamination flips the outcome of the records whose true p_y lies beyond the population's rate/2 and 1 - rate/2 quantiles of p_y (computed exactly for each scenario), so the number flipped varies between data sets (74.9 on average at 5% and n = 1500, SD 8.5). The paper says only 'p_y at bottom or top 1%' (2.5% for 5%) |
| Additional file 2, Table A3, MSE, n = 500 | agrees | 144 of 144 fields as printed | Assumed: Contamination flips the outcome of the records whose true p_y lies beyond the population's rate/2 and 1 - rate/2 quantiles of p_y (computed exactly for each scenario), so the number flipped varies between data sets (74.9 on average at 5% and n = 1500, SD 8.5). The paper says only 'p_y at bottom or top 1%' (2.5% for 5%) |
| Results: with contamination every relative bias is negative | agrees | 1 of 1 fields as printed | Assumed: Contamination flips the outcome of the records whose true p_y lies beyond the population's rate/2 and 1 - rate/2 quantiles of p_y (computed exactly for each scenario), so the number flipped varies between data sets (74.9 on average at 5% and n = 1500, SD 8.5). The paper says only 'p_y at bottom or top 1%' (2.5% for 5%) |
| Results: lower outcome rates go with larger biases | agrees | 2 of 2 fields as printed | Assumed: Contamination flips the outcome of the records whose true p_y lies beyond the population's rate/2 and 1 - rate/2 quantiles of p_y (computed exactly for each scenario), so the number flipped varies between data sets (74.9 on average at 5% and n = 1500, SD 8.5). The paper says only 'p_y at bottom or top 1%' (2.5% for 5%) |
| Results: linear Z, log-binomial 3.5% to 6.7% more biased at outcome 10% and 5% contamination | agrees | 3 of 3 fields as printed | Assumed: Contamination flips the outcome of the records whose true p_y lies beyond the population's rate/2 and 1 - rate/2 quantiles of p_y (computed exactly for each scenario), so the number flipped varies between data sets (74.9 on average at 5% and n = 1500, SD 8.5). The paper says only 'p_y at bottom or top 1%' (2.5% for 5%) |
| Results: non-linear Z, robust Poisson less biased from 2% contamination on | agrees | 3 of 3 fields as printed | Assumed: Contamination flips the outcome of the records whose true p_y lies beyond the population's rate/2 and 1 - rate/2 quantiles of p_y (computed exactly for each scenario), so the number flipped varies between data sets (74.9 on average at 5% and n = 1500, SD 8.5). The paper says only 'p_y at bottom or top 1%' (2.5% for 5%) |
| Results: without contamination the two SEs are identical at the 2nd decimal | agrees | 1 of 1 fields as printed, 1 paper errors | Assumed: Contamination flips the outcome of the records whose true p_y lies beyond the population's rate/2 and 1 - rate/2 quantiles of p_y (computed exactly for each scenario), so the number flipped varies between data sets (74.9 on average at 5% and n = 1500, SD 8.5). The paper says only 'p_y at bottom or top 1%' (2.5% for 5%) |
| Results: with contamination, comparable SEs at outcome 25% and 40%, log-binomial higher at 10% | agrees | 2 of 2 fields as printed | Assumed: Contamination flips the outcome of the records whose true p_y lies beyond the population's rate/2 and 1 - rate/2 quantiles of p_y (computed exactly for each scenario), so the number flipped varies between data sets (74.9 on average at 5% and n = 1500, SD 8.5). The paper says only 'p_y at bottom or top 1%' (2.5% for 5%) |
| Results: the MSEs follow the biases | agrees | 2 of 2 fields as printed | Assumed: Contamination flips the outcome of the records whose true p_y lies beyond the population's rate/2 and 1 - rate/2 quantiles of p_y (computed exactly for each scenario), so the number flipped varies between data sets (74.9 on average at 5% and n = 1500, SD 8.5). The paper says only 'p_y at bottom or top 1%' (2.5% for 5%) |
| Results: the same pattern at n = 500, with larger SEs | agrees | 2 of 2 fields as printed | Assumed: Contamination flips the outcome of the records whose true p_y lies beyond the population's rate/2 and 1 - rate/2 quantiles of p_y (computed exactly for each scenario), so the number flipped varies between data sets (74.9 on average at 5% and n = 1500, SD 8.5). The paper says only 'p_y at bottom or top 1%' (2.5% for 5%) |
| Discussion: no difference between the models without outliers | agrees | 1 of 1 fields as printed | Assumed: Contamination flips the outcome of the records whose true p_y lies beyond the population's rate/2 and 1 - rate/2 quantiles of p_y (computed exactly for each scenario), so the number flipped varies between data sets (74.9 on average at 5% and n = 1500, SD 8.5). The paper says only 'p_y at bottom or top 1%' (2.5% for 5%) |
| Discussion: COPY converged in all fits of 48 of 48 linear and 30 of 48 non-linear scenarios | partly | 1 of 2 fields as printed | Every log-binomial fit of ours converges, plain or COPY, so ours counts 48 of 48 non-linear scenarios against the paper's 30. The paper's failures are failures of SAS GENMOD's optimizer on the COPY data, which we cannot run. The boundary that COPY handles is common in our non-linear runs: COPY is needed in some fit of 47 of 48 non-linear scenarios (up to 863 of 1,000 fits, median 172) and of 5 of 48 linear ones (at most 2 fits), which agrees with the paper's split between the forms but cannot say which 18 failed. |
| Main claim: comparable models with a linear Z; robust Poisson less biased with a quadratic Z from 2% contamination on | agrees | 2 of 2 fields as printed | Assumed: Contamination flips the outcome of the records whose true p_y lies beyond the population's rate/2 and 1 - rate/2 quantiles of p_y (computed exactly for each scenario), so the number flipped varies between data sets (74.9 on average at 5% and n = 1500, SD 8.5). The paper says only 'p_y at bottom or top 1%' (2.5% for 5%) |
| Discussion: results cited from Petersen and Deddens (three decimals with 10,000 copies; 70% to 100% convergence) | not attempted | not attempted | Results of another paper, quoted in the Discussion; this paper does not compute them. |
| Each statement of the text recomputed from the paper's own tables | agrees | 18 of 19 statements follow from the paper's own tables. Not: text.se_uncontaminated: Table 2, 0% rows: LB and RP SEs equal at the 2nd decimal in all 24 pairs (yes against no). |  |
| robustrr's fits against statsmodels and an independent maximizer | agrees | 60 contaminated data sets (8 COPY fits): robust Poisson coefficients equal statsmodels' to 1.2e-12 and the sandwich SE its HC0 SE to a relative 3.1e-12; log-binomial coefficients equal an independent maximizer's to 1.0e-06, with a likelihood at least as high (to 1.1e-13) and a score of at most 4.0e-06 |  |
| The authors' SAS 9.2 program and COPY macro | not attempted | not attempted | The simulation program was never released, and the revised COPY macro of Petersen and Deddens is not online (its NIOSH page answers 403). Both are SAS, which no free runtime runs. The method is implemented from the paper's text and checked against its printed tables. |
| Python package robustrr and its tutorial | agrees | robustrr 0.1.0: wheel installed in a fresh environment and imported from it; tests 8 passed; tutorial 6 cells compared, 0 skipped (nondeterministic); TUTORIAL.md in sync |  |
<!--/RESULTS-TABLE-->

<!--CLAIMS-LINE-->
The main claim holds. Every statement about bias, SE and MSE holds on our run but one, which the paper's own Table 2 breaks as well: without contamination the two SEs differ by less than 0.0009, yet can round to different second decimals. The one table cell that misses is a misprint in Table 3 (0.013 where the paper's own bias and SE give 0.0351), and the convergence count of the Discussion belongs to SAS's optimizer, which we cannot run.
<!--/CLAIMS-LINE-->

## What the code does, against the paper

| Paper | Here |
| --- | --- |
| Z ~ Beta(6, 2); logit(p_x) = alpha0 + alpha1 Z; log(p_y) = beta0 + beta1 X + beta2 Z (+ 0.5 beta2 Z² for a quadratic confounder); beta1 = log RR; alpha1 = beta2 = log 2 or log 4 (Methods) | `robustrr.generate`: as printed. |
| alpha0 and beta0 of the 24 scenarios (Additional file 1), "searched iteratively" to give 50% exposure and 10, 25 or 40% outcome | The printed values. Quadrature over Z confirms the rates (`design` in `results.json`); the largest p_y of any scenario is below 1, so the paper needs no rule for p_y > 1. |
| Contamination: flip Y for "records with p_y at bottom or top 1%" (2%), "bottom or top 2.5%" (5%) | Records whose true p_y is beyond the population's 1% and 99% (2.5% and 97.5%) quantiles are flipped (`robustrr.population_cutoffs`, exact by quadrature), so how many are flipped varies between data sets. Found from the SEs: see below. |
| Robust Poisson: Poisson GLM with the sandwich variance (PROC GENMOD, REPEATED) | `robustrr.poisson_coef` / `robust_poisson`: Newton's method; HC0 sandwich. The tables use only the point estimates, so the working correlation does not matter. |
| Log-binomial with the COPY method: the plain fit if it converges, else weights C = 1,000,000 on the data and 1 on the data with Y reversed (Petersen and Deddens' revised macro) | `robustrr.log_binomial_coef`: Newton's method with a line search inside the parameter space; when the maximum is on the boundary (a fitted probability reaches 1), the COPY fit. Checked against statsmodels and an independent maximizer (`CROSSCHECK`). statsmodels' own log-binomial GLM is not the reference: on these data its IRLS stops at lower likelihoods than ours. |
| Fitted model: X and Z, and the higher-order term of Z "added into the model" with a quadratic confounder (Discussion) | Z² is fitted for the quadratic confounder. |
| Relative bias = (mean of the 1,000 log RR - log RR)/log RR; SE = their empirical SD; MSE = squared bias + variance | `robustrr.summarize`: as printed, with the divisor 999. |
| 1,000 replicates; SAS 9.2, seeds not given | 1,000 replicates; NumPy 2.2.6 PCG64, one stream per scenario and sample size, the same data sets contaminated at each rate. A second run with other seeds measures how far two runs of one design stray. |
| n = 500: "the same process was repeated" | The same alpha0 and beta0. |

## Finding the contamination rule

The Methods do not say whether "p_y at bottom or top 1%" means a fixed share of each data set or fixed cut-offs of
p_y. A first run flipped exactly ceil(n x rate/2) records per tail in every data set. Its relative biases matched
Table 1, but at outcome 10% and 5% contamination its SEs were too small, at both sample sizes, by more than Monte Carlo
error allows. Flipping the records beyond fixed cut-offs gives the same means and the larger spread the paper prints. Each
reading was scored on the same seeds (`hypotheses` in `output/comparison.json`); counts are of the cells each
variant changes, within tolerance:

<!--HYPOTHESES-->
| Variant | Table | Variant within | Compared with | That reading within | RMS z, variant / that reading |
| --- | --- | --- | --- | --- | --- |
| a fixed ceil(n rate/2) records per tail in every data set | table1 | 96 of 96 | the main reading | 96 of 96 | 0.97 / 0.90 |
| a fixed ceil(n rate/2) records per tail in every data set | table2 | 89 of 96 | the main reading | 96 of 96 | 1.69 / 0.92 |
| a fixed ceil(n rate/2) records per tail in every data set | table3 | 95 of 96 | the main reading | 95 of 96 | 1.99 / 1.81 |
| the same at n = 500 | tableA1 | 92 of 96 | the main reading | 96 of 96 | 1.53 / 1.15 |
| the same at n = 500 | tableA2 | 87 of 96 | the main reading | 96 of 96 | 2.19 / 1.28 |
| the same at n = 500 | tableA3 | 95 of 96 | the main reading | 96 of 96 | 1.34 / 1.27 |
| a fixed floor(n rate/2) per tail (against the fixed ceil) | table1 | 48 of 48 | the fixed ceil reading | 48 of 48 | 0.96 / 1.03 |
| a fixed floor(n rate/2) per tail (against the fixed ceil) | table2 | 42 of 48 | the fixed ceil reading | 42 of 48 | 1.97 / 2.02 |
| a fixed floor(n rate/2) per tail (against the fixed ceil) | table3 | 47 of 48 | the fixed ceil reading | 47 of 48 | 2.65 / 2.56 |
| the whole rate at the bottom of p_y | table1 | 3 of 96 | the main reading | 96 of 96 | 49.14 / 0.90 |
| the whole rate at the bottom of p_y | table2 | 94 of 96 | the main reading | 96 of 96 | 1.50 / 0.92 |
| the whole rate at the bottom of p_y | table3 | 7 of 96 | the main reading | 95 of 96 | 31.94 / 1.81 |
| the whole rate at the top of p_y | table1 | 0 of 96 | the main reading | 96 of 96 | 49.75 / 0.90 |
| the whole rate at the top of p_y | table2 | 85 of 96 | the main reading | 96 of 96 | 2.12 / 0.92 |
| the whole rate at the top of p_y | table3 | 19 of 96 | the main reading | 95 of 96 | 19.00 / 1.81 |
| a fixed number ranked by fitted p_y | table1 | 85 of 96 | the main reading | 96 of 96 | 2.22 / 0.90 |
| a fixed number ranked by fitted p_y | table2 | 85 of 96 | the main reading | 96 of 96 | 2.07 / 0.92 |
| a fixed number ranked by fitted p_y | table3 | 79 of 96 | the main reading | 95 of 96 | 3.15 / 1.81 |
| Z^2 left out of the fitted models (non-linear columns) | table1 | 50 of 72 | the main reading | 72 of 72 | 3.89 / 1.04 |
| Z^2 left out of the fitted models (non-linear columns) | table2 | 71 of 72 | the main reading | 72 of 72 | 1.20 / 0.94 |
| Z^2 left out of the fitted models (non-linear columns) | table3 | 56 of 72 | the main reading | 72 of 72 | 3.95 / 0.94 |
<!--/HYPOTHESES-->

## Comparing Monte Carlo tables

No printed cell can come back exactly: the seeds and generator are not given. Each cell is compared at a tolerance
fixed before the comparison: half a unit of the last printed digit plus 3 x √2 Monte Carlo standard errors of one
1,000-replicate estimate (ours stands in for the paper's): the SD of the log RR estimates over √1,000 (relative to
log RR) for the relative bias, SD/√(2 x 999) for the SE, and the SD of the squared errors over √1,000 for the MSE.
The text's statements are recomputed first from the paper's own tables (`arithmetic` in `output/claims.json`),
then from our run.

How good is that test? Our second run, as if it were the paper, and our run of a wrong design (the other sample
size, the linear and non-linear columns swapped, the RR rows swapped) are scored the same way (`replicate` and
`controls`):

<!--CONTROLS-->
Cells of 144 within tolerance:

| Table | Our run of the other sample size | Linear and non-linear columns swapped | RR rows swapped | Our run (the right design) | Our second run |
| --- | --- | --- | --- | --- | --- |
| Table 1 | 144 | 67 | 97 | 144 | 144 |
| Table 2 | 0 | 139 | 144 | 144 | 144 |
| Table 3 | 0 | 83 | 54 | 143 | 143 |
| Table A1 | 140 | 101 | 114 | 144 | 144 |
| Table A2 | 0 | 142 | 142 | 144 | 144 |
| Table A3 | 0 | 105 | 77 | 144 | 144 |
<!--/CONTROLS-->

The relative bias barely depends on n, so Tables 1 and A1 tell the designs apart only by their columns and rows; the
SEs depend mostly on n and the outcome rate, so Tables 2 and A2 tell the sample sizes apart and little else. The MSE
tables separate every wrong design.

Table 3 prints 0.013 for RR 2.0, outcome 25%, 5%, linear strong, log-binomial. The paper's own bias and SE for that
cell (Tables 1 and 2) give 0.035, and the robust Poisson cell next to it prints 0.035; it is a misprint, left out
as a `paper_error`. A few more MSEs of the paper, in Tables 3 and A3, disagree with its own bias and SE at the printed precision
(`consistency` in `output/comparison.json`); ours is within tolerance of the printed value in each.

## Fig. 1

Fig. 1 plots Table 1. Reading its vertices back from the published picture confirms that (`fig1.consistency`).
Our Table 1 is drawn on a copy of the published picture with the published lines removed, at the measured stroke
width, colours and dash pattern (`output/fig1_ours.png`; overlay in green, `output/fig1_overlay.png`; the whole figure,
as the paper prints it). Each panel is scored both ways at 2 px with wrong-input and near-miss controls. A 2 px test cannot resolve
Monte Carlo noise here: two of our own runs score only about 0.7 against each other, while the paper's Table 1 drawn
with the same code scores 0.95 or more. Panel A passes; B and D fall short, and C scores below a near miss, so
it is inconclusive. Their verdicts rest on the pixels, and their numbers on Table 1, where every value is within
tolerance.

## Layout

| Path | Content |
| --- | --- |
| `main.nf`, `nextflow.config` | The pipeline. The config pins NumPy and OpenBLAS to their AVX2 code paths so that runs on different x86-64 machines agree bit for bit. |
| `requirements.txt` | Pinned Python packages; the package `robustrr` is installed from `../package`. |
| `results_notes.json` | Labels, assumptions, causes and the page's prose, written by hand; merged with the run into `../results.json`. Numbers in the prose are filled from the run. |
| `results.json` | The repository's results check (`tools/check_results.py`): our value for every compared cell, claim and figure score. |
| `published/fig1.png` | Fig. 1 as published (CC BY 4.0, Chen et al. 2014), extracted from the article PDF. |
| `pipeline/` | `fetch_inputs.sh`, `extract_published.py`, `published_figure.py`, `simulate.py`, `compare.py`, `claims.py`, `figure.py`, `crosscheck.py`, `build_results.py`, `make_results_check.py`, `build_page.py` with `page_template.html`, `check_reproduction.py`, `update_readmes.py`, `env_versions.py`; copies of the skill's `check_results.py`, `compare_runs.py` and `check_package.py`. |
| `output/published_values.json` | Every printed number of Tables 1-3, A1-A3 and Additional file 1. |
| `output/simulation.json` | Every scenario's summaries: the main run, the second run and the hypothesis variants. |
| `output/comparison.json`, `output/tables.csv` | Every printed cell against ours, with tolerances, the second run, the controls, the hypotheses and the paper's own consistency; the same cells as one CSV. |
| `output/figure.json`, `output/fig1_*.png` | Fig. 1: calibration, scores, controls, the vertices read back; our drawing and the overlay of the whole figure. |
| `output/claims.json`, `output/crosscheck.json`, `output/package.json` | The statements of the text against the paper's own tables and our run, and the design check; the fits against statsmodels and an independent maximizer; the package check. |

## Run

```bash
sudo apt-get install poppler-utils      # pdftotext and pdfimages
pip install -r PMC4079617/figure-reproduction/requirements.txt ./PMC4079617/package
nextflow run PMC4079617/figure-reproduction/main.nf --outdir results
```

The whole run takes about 8 minutes on 4 cores, nearly all of it the simulation study; `--jobs N` sets the number
of processes. `.github/workflows/reproduce-pmc4079617.yml` runs it on
every pull request that touches this paper.

## Pipeline steps

1. `FETCH`: the article XML and PDF and Additional files 1 and 2 from PMC's open-access bucket (Europe PMC as a fallback), SHA-256 checked.
2. `PUBLISHED_VALUES`: every printed value read from the XML and the supplements, checked against the committed copy.
3. `PUBLISHED_FIGURE`: Fig. 1 extracted from the PDF, checked pixel for pixel against `published/fig1.png`.
4. `SIMULATE`: the main run at n = 1500 and n = 500, the second run, the hypothesis variants.
5. `COMPARE`: every printed cell against ours, the controls, the hypotheses and the paper's own consistency.
6. `CLAIMS`: every statement of the text against the paper's own tables and our run; the design check.
7. `FIGURE`: Fig. 1 calibrated, drawn on the published picture, scored with controls; its vertices read back.
8. `CROSSCHECK`: the fits against statsmodels and an independent maximizer.
9. `PACKAGE`: `check_package.py` on `../package` (wheel, fresh install, tests, tutorial rerun).
10. `RESULTS`: `results.json` (verdicts by `check_results.py`), the repository's results check, the results page, and `check_reproduction.py` against the committed outputs (`report.md`); `CHECK` fails the run if anything differs.

## Limits

- **The SAS code and the COPY macro are lost.** The method is rebuilt from the paper's text and checked against its tables (`port` is not attempted); the fits are checked against statsmodels and an independent maximizer.
- **The contamination rule was found from the tables**, not read from the paper (`found_by_search`), so no simulated item can be "exact".
- **Convergence.** Every fit of ours converges; the paper's count of SAS failures (18 non-linear scenarios) belongs to GENMOD's optimizer and is left open.
- **Fig. 1 at 2 px.** The pixel test cannot tell Monte Carlo noise from a wrong curve; the verdicts of panels B, C and D reflect that limit. Their values are Table 1's, each within tolerance.
- **Monte Carlo error.** Every simulated cell carries it; the tolerance allows for it.
