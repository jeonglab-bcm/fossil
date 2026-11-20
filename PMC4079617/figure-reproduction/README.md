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
<!--/RESULTS-TABLE-->

<!--CLAIMS-LINE--><!--/CLAIMS-LINE-->

## What the code does, against the paper

| Paper | Here |
| --- | --- |
| Z ~ Beta(6, 2); logit(p_x) = alpha0 + alpha1 Z; log(p_y) = beta0 + beta1 X + beta2 Z (+ 0.5 beta2 Z² for a quadratic confounder); beta1 = log RR; alpha1 = beta2 = log 2 or log 4 (Methods) | `robustrr.generate`: as printed. The main text writes "beta2 = alpha1" where the design means a1 = beta2. |
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
Table 1, but at outcome 10% and 5% contamination its SEs were too small, in both runs, by more than Monte Carlo error
allows. Flipping the records beyond fixed cut-offs gives the same means and the larger spread the paper prints. Each
reading was scored on the same seeds (`hypotheses` in `output/comparison.json`); counts are of the cells each
variant changes, within tolerance:

<!--HYPOTHESES-->
<!--/HYPOTHESES-->

## Comparing Monte Carlo tables

No printed cell can come back exactly: the seeds and generator are not given. Each cell is compared at a tolerance
fixed before the comparison: half a unit of the last printed digit plus 3 x √2 Monte Carlo standard errors of one
1,000-replicate estimate (ours stands in for the paper's): the SD of the log RR estimates over √1,000 (relative to
log RR) for the relative bias, SD/√(2 x 999) for the SE, and the SD of the squared errors over √1,000 for the MSE.
The text's statements are recomputed first from the paper's own tables (`arithmetic` in `output/claims.json`),
then from our run.

How good is that test? Our second run, as if it were the paper, passes in nearly every cell (`replicate`). Our run
of a wrong design (the other sample size, the linear and non-linear columns swapped, the RR rows swapped) passes far
fewer (`controls`); the relative bias barely depends on n, so for Tables 1 and A1 only the swapped designs tell the
designs apart, while the SEs and MSEs separate the sample sizes completely.

Table 3 prints 0.013 for RR 2.0, outcome 25%, 5%, linear strong, log-binomial. The paper's own bias and SE for that
cell (Tables 1 and 2) give 0.035, and the robust Poisson cell next to it prints 0.035; it is a misprint, left out
as a `paper_error`. Three more MSEs of the paper disagree with its own bias and SE at the printed precision
(`consistency` in `output/comparison.json`); ours matches the printed value in each.

## Fig. 1

Fig. 1 plots Table 1. Reading its vertices back from the published picture confirms that (`fig1.consistency`).
Our Table 1 is drawn on a copy of the published picture with the published lines removed, at the measured stroke
width, colours and dash pattern (`output/fig1_ours.png`; overlay in green, `output/fig1_overlay.png`; one crop per
panel). Each panel is scored both ways at 2 px with wrong-input and near-miss controls. A 2 px test cannot resolve
Monte Carlo noise here: two of our own runs score only about 0.7 against each other, while the paper's Table 1 drawn
with the same code scores 0.95 or more. So Fig. 1's verdicts rest on the pixels, and its numbers on Table 1.

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
| `output/figure.json`, `output/fig1_*.png` | Fig. 1: calibration, scores, controls, the vertices read back; our drawing and the overlay, whole and per panel. |
| `output/claims.json`, `output/crosscheck.json`, `output/package.json` | The statements of the text against the paper's own tables and our run, and the design check; the fits against statsmodels and an independent maximizer; the package check. |

## Run

```bash
sudo apt-get install poppler-utils      # pdftotext and pdfimages
pip install -r PMC4079617/figure-reproduction/requirements.txt ./PMC4079617/package
nextflow run PMC4079617/figure-reproduction/main.nf --outdir results
```

The whole run takes about 8 minutes on 4 cores, nearly all of it the simulation study (204 scenario runs plus
the variants); `--jobs N` sets the number of processes. `.github/workflows/reproduce-pmc4079617.yml` runs it on
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
- **Fig. 1 at 2 px.** The pixel test cannot tell Monte Carlo noise from a wrong curve; panel B, C and D verdicts reflect that limit, not a gap in the numbers.
- **Monte Carlo error.** Every simulated cell carries it; the tolerance allows for it.
