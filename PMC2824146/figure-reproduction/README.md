# PMC2824146 figure reproduction

Marshall A, Altman DG, Royston P, Holder RL. Comparison of techniques for handling missing covariate
data within prognostic modelling studies: a simulation study. *BMC Medical Research Methodology* 10:7
(2010). [doi:10.1186/1471-2288-10-7](https://doi.org/10.1186/1471-2288-10-7)

The authors released no simulation code. This pipeline rebuilds the study from the paper's text with
the R package [`../package`](../package) (`misscox`), reruns it, and compares every table, every
plotted point of Figures 1 to 8 and every claim in the text with the paper.

## Results

<!-- the table is check_results.py --markdown on ../results.json; do not edit by hand -->
<!--RESULTS-TABLE-->
4 exact, 13 agrees, 9 partly, 1 differs, 2 not attempted; 15 open causes; 7 verdicts set by a reviewer.

| Item | Verdict | Measure | Why |
| --- | --- | --- | --- |
| Table 1, means and SDs after transformation | exact | 16 of 16 fields as printed |  |
| Skewness of X2, X3, X4, X8 (Methods text) | agrees | 4 of 4 fields as printed | Assumed: Skewness b1 = m3 / s^3 with the n - 1 SD, on the raw scale (the paper does not define it) |
| Correlations quoted in the Methods text | agrees | 4 of 4 fields as printed | Assumed: Pearson correlations on the raw (untransformed) scale |
| Fig. 1, histograms of the covariates (a) and the transformed covariates (b) | agrees | 82 of 82 fields as printed | Assumed: Published values are read from the article PDF's vector figures: each plotted point is a vertex of the series' line, each axis is mapped from its tick marks and printed labels; the PDF writer's coordinate grid is 0.405 pt |
| Linear predictor, full Cox model on the breast cancer data (Methods equation) | exact | 9 of 9 fields as printed |  |
| About 35% censored (Methods text) | differs | 0 of 1 fields as printed | The text's 'approximately 35%' is a rounded figure: the stated hazards (0.0002 for censoring against 0.00027 exp(LP) for events) give 36.4% censored in our run and 36.6% with every variant of our generator. |
| Missingness design: incomplete cases, shares and overlaps (Methods text) | partly | 22 of 40 fields as printed | Each covariate is missing in exactly its share of all cases (X3 at 25%: 67.98% of 25.75% incomplete cases is 17.50% of all cases, the design's 0.70 x 25%), but the overall share of incomplete cases runs 0.3 to 0.8 points above the target because only three pairs of indicators are tied (X5 and X3 or X8 and X2 can be missing together by chance). The shares of incomplete cases then fall slightly below the stated ones. The paper's numbers are design targets ('approximately'), and how it tied the other pairs is not stated. |
| Table 2, specification of the missingness mechanisms | not attempted | not attempted | A design input, used as given (the blank X3 cell of the combined mechanism read as MCAR). |
| Table 3, odds ratios between missingness indicators | agrees | 15 of 15 fields as printed | Assumed: The shares become whole cases of 1000, rounded half up, before the odds ratio is taken |
| Table 4, the missing data methods | not attempted | not attempted | A list of methods and settings, implemented as given in the package. |
| Figs 2 and 3, reference lines: true values and empirical SEs (20,000 complete-data cohorts) | partly | 10 of 18 fields as printed | Our generator's empirical SEs are 14% smaller for X1 and X6 and 14% larger for X4 than the paper's, and its true values 1 to 5% larger in magnitude for X2, X3, X4 and X5 (X7 0.8%). Keeping the binaries' observed correlations takes the X1 and X6 SEs past the paper's (0.0064 and 0.132 against 0.0060 and 0.119, ours 0.0051 and 0.104); the unrounded coefficients move X2's true value from 0.0517 to 0.0513 (paper 0.0507); the X4 SE and the larger magnitudes stay open. |
| Fig. 2, coefficient estimates under MAR | agrees | 301 of 333 fields as printed; computed partly, reviewer agrees | Most points fall within Monte Carlo error. Most of the 32 misses are estimates of X2, X3, X4 and X5 at 50 and 75% (five at 25%), mostly MI and SI, where our MIX without truncating, MICE-PMM and SI are further from or nearer the truth than the paper's. The offset of the true values does not explain them; the 2004 to 2005 package versions could not be tested. |
| Claims about Fig. 2 (bias, 0.5 SE, 10% bias) | partly | 11 of 18 fields as printed, 5 paper errors | Each claim is computed from our figure values with the paper's thresholds (0.5 SE, 10% bias, 90% coverage, p = 0.05). Where the text disagrees with the paper's own figures and our run agrees with the figures, the field is a paper error and is not counted; the claims that still differ follow the gaps of the figure they rest on. |
| Fig. 3, average SEs under MAR | partly | 164 of 333 fields as printed; computed partly, reviewer partly | Every point of X1, X4 and X6 misses by a near-constant factor across methods and levels (ours 0.83 to 0.91, 1.12 to 1.29 and 0.83 to 0.87 times the paper's, medians 0.86, 1.14 and 0.86), close to the ratio of their empirical SEs with no missing data (0.86, 1.14, 0.87): the generated covariates differ (see the reference lines). Keeping the binaries' correlations moves the X1 and X6 SEs past the paper's. The other misses (X2, X5) are MI SEs at 50 and 75%. |
| Claims about Fig. 3 (SEs) | exact | 6 of 6 fields as printed, 3 paper errors | Each claim is computed from our figure values with the paper's thresholds (0.5 SE, 10% bias, 90% coverage, p = 0.05). Where the text disagrees with the paper's own figures and our run agrees with the figures, the field is a paper error and is not counted; the claims that still differ follow the gaps of the figure they rest on. |
| Fig. 4, coverage under MAR | agrees | 322 of 333 fields as printed; computed partly, reviewer agrees | Nearly all points fall within binomial error; the misses are X3 coverage of the MI methods at 50 and 75%, where our MICE-PMM and MIX without truncating cover the true value more often than the paper's, as their X3 estimates in Fig. 2 are less biased. |
| Claims about Fig. 4 (coverage) | partly | 14 of 18 fields as printed, 1 paper errors | Each claim is computed from our figure values with the paper's thresholds (0.5 SE, 10% bias, 90% coverage, p = 0.05). Where the text disagrees with the paper's own figures and our run agrees with the figures, the field is a paper error and is not counted; the claims that still differ follow the gaps of the figure they rest on. |
| Fig. 5, mean p-values under MAR | agrees | 295 of 333 fields as printed; computed partly, reviewer agrees | Most misses are X6, whose mean p-value is lower in our run at every level and method, as its SE is about 14% smaller (Fig. 3); the rest are scattered MI points for X2 to X5. |
| Claims about Fig. 5 (significance) | partly | 1 of 2 fields as printed, 2 paper errors | Each claim is computed from our figure values with the paper's thresholds (0.5 SE, 10% bias, 90% coverage, p = 0.05). Where the text disagrees with the paper's own figures and our run agrees with the figures, the field is a paper error and is not counted; the claims that still differ follow the gaps of the figure they rest on. |
| Fig. 6, model performance under MAR (LR p, R2, D, 2-year survival) | agrees | 125 of 148 fields as printed; computed partly, reviewer agrees | Two gaps. The pooled likelihood ratio p-values after MI are below 3 x 10^-6 in our run against up to 0.0046 in the paper; no pooling rule we tried gives the paper's values. Complete-case R2, D and 2-year survival rise with missingness in our run (2-year survival 0.805 at 75% against 0.760): reversing X5's time term brings survival to 0.771 but leaves R2 and D high. |
| Claims about Fig. 6 (model performance) | partly | 5 of 7 fields as printed | Each claim is computed from our figure values with the paper's thresholds (0.5 SE, 10% bias, 90% coverage, p = 0.05). Where the text disagrees with the paper's own figures and our run agrees with the figures, the field is a paper error and is not counted; the claims that still differ follow the gaps of the figure they rest on. |
| Fig. 7, coefficients of X2 to X5 under MAR and MNAR | agrees | 119 of 140 fields as printed; computed partly, reviewer agrees | The MAR series match as in Fig. 2. Under MNAR our X4 estimates (every MI method shown) and X3 with MICE are further from the truth than the paper's at 50 and 75% (X4 with MICE-PMM at 75%: -0.00049 against -0.00036); X3 with MICE-PMM is nearer. The scale of X3's own term does not explain it. |
| Fig. 8, coverage of X2 to X4 under MAR and MNAR | agrees | 94 of 105 fields as printed; computed partly, reviewer agrees | The misses are X3 coverage at 50 and 75%, following the X3 estimates of Fig. 7: under MNAR our MICE covers the true value in 12% of replicates at 75% against the paper's 33%; under MAR our MICE-PMM covers it more often (64% against 49%). |
| Claims about Figs 7 and 8 (MNAR against MAR) | partly | 7 of 10 fields as printed, 1 paper errors | Under MNAR X3 and X4 are more than 0.5 SE from the truth from 25% with every MI, as the paper says, and MICE-PMM without transformation reaches 0.5 SE under MAR only at 50%, as it says. The direction claims at 75% differ in places: our X3 is not further from the truth under MNAR for every method, X5 is not closer, and X2 coverage is not lower for every method; the paper's own Fig. 8 has X3 coverage higher under MNAR for two of three methods (a paper error). |
| MCAR and combined like MAR; NORM and MIX like MICE (Results text, not plotted) | partly | 1 of 4 fields as printed | The text judges 'no apparent differences' and 'indistinguishable' by eye; we set 0.25 SE (mechanisms) and 0.1 SE (methods). MIX is within 0.1 SE of MICE everywhere and NORM in 44 of 45 points (X5 at 75%: 0.17 SE). MCAR differs from MAR by more than 0.25 SE in 10% of the points, all of them X3 (up to 1.2 SE with MIX without truncating at 75%), with a median difference of 0.09 SE. |
| Main claim (Abstract and Conclusions): MICE-PMM least biased, fails from 50% and under MNAR | exact | 6 of 6 fields as printed |  |
| Claims recomputed from the paper's own figure values | agrees | 59 of 77 claim fields come back when computed from the paper's own figure values; the 18 that do not are where the text contradicts its own figures (listed in comparison.json, arithmetic.not_back) |  |
| Replicates rerun from scratch equal the committed results | agrees | 3 of 3 reruns from scratch equal the committed results: MAR replicate 1 (46 rows); MNAR replicate 1 (31 rows); true values replicate 1-200 (200 rows) |  |
| R package misscox and its tutorial | agrees | R CMD build ok; R CMD check: OK; testthat [ FAIL 0, WARN 0, SKIP 0, PASS 19 ]; TUTORIAL.md same as the vignette rendered now |  |
<!--/RESULTS-TABLE-->

<!--RESULTS-PROSE-->
The main claim holds: MICE-PMM without transformation is the least biased MI method for the skewed
covariates and stays within 10% bias at 25% (both under MAR), and is more than 0.5 SE from the truth at
50% under MAR, MCAR and the combined mechanism, and every MI method is more than 0.5 SE off for X3 under MNAR from 25%.
The text contradicts its own figures in 18 claim fields; the 12 where our run agrees with the figures
are counted as paper errors. The claims that differ follow the generated covariates and the newer
imputation packages (open).

Controls. A point matches when it is within three combined Monte Carlo SEs and one grid step. Many
curves are flat, so the controls also match many points of Figs 2 and 4 to 8 (fewer of Fig. 3); on
the points where the published curve moves by more than the tolerance between neighbouring levels,
ours match 43 of 66 (Fig. 2), 83 of 196 (Fig. 3), 32 of 39 (Fig. 4), 37 of 51 (Fig. 5), 45 of 63
(Fig. 6), 59 of 76 (Fig. 7) and 33 of 43 (Fig. 8), and our values at the neighbouring level match
17, 22, 11, 10, 16, 14 and 11 of them (`comparison.json`,
`controls`).
<!--/RESULTS-PROSE-->

## What the code does, against the paper

| Step | The paper | Our code |
| --- | --- | --- |
| Motivating data | German Breast Cancer Study Group data (Sauerbrei et al. 1999), eight covariates, recurrence-free survival; size not stated | `TH.data::GBSG2` (686 patients, 299 events); Table 1, the skewness and correlation values and the Cox coefficients come back from it |
| Covariates | Multivariate normal with the means and covariance of the transformed data; back-transformed; binaries cut at 0.5; X8 grouped at 20 and 30 mm; truncated at the upper observed limits | The same (`generation_parameters()`, `simulate_cohort()`); back-transformed X3 and X4 below 0 set to 0 (not stated) |
| Survival | Exponential event times with hazard 0.00027 exp(LP), censoring hazard 0.0002, about 35% censored, n = 1000 | The same, per day, with the printed coefficients |
| True values | Mean coefficient and empirical SE over 20,000 cohorts without missing data | The same (20,000 cohorts) |
| Missingness | Logistic models per covariate (Tables 2 and 3); X3, X2, X5, X8 missing in about 70, 55, 20, 10% of incomplete cases; overlaps 35, 10, 5% | The shares as whole cases of 1000, rounded half up (this gives Table 3 exactly); intercepts solved at the mean of each mechanism's term (`impose_missing()`) |
| Replications | 1000 for every mechanism | 200 for MAR and MNAR, 100 for MCAR and combined (the same cohorts across mechanisms and levels, new deletion seeds, as in the paper) |
| Methods | CC; SI (PMM); NORM, MIX, MIX without truncating, MICE, MICE-PMM, MICE-PMM without transformation, aregImpute; m = 20; iterations of Table 4 | The same with current CRAN versions (mice 3.16.0, Hmisc 5.1-1, norm 1.0-11.1, mix 1.0-13) instead of the 2002 to 2005 ones; MIX on a restricted general location model; settings the paper omits at the packages' defaults (`handle_missing()`) |
| Analysis | Full Cox model; Rubin's rules; Li et al. (1991) for the LR test; median R2 of the m fits; D (Royston and Sauerbrei 2004); 2-year survival after a complementary log-log transformation | The same (`analyse_complete()`, `pool_fits()`); survival predicted at the means of all covariates |
| Summaries | Mean estimate, bias, % bias, mean SE, coverage, mean p-value, model measures | The same (`summarise_replicates()`); the figures plot mean p-values, not medians (the full-data points agree with means only) |

## Comparing the figures

The article's PDF holds Figures 1 to 8 as vector drawings. `pipeline/extract_published.py` reads
every plotted point from them: each series is a chain of line segments whose vertices are the
points, each axis is mapped from its tick marks and its printed tick labels, and series that share
a colour are told apart by their markers, matched against the legend. The PDF writer stores
coordinates on a 0.405 pt grid, which is about 0.3% of a panel's height; one grid step is added to
every tolerance. Two things in the published figures are not what their legends say: in Fig. 6b the
SI line is drawn in MICE-PMM's blue (with SI's red markers) and carries exactly MICE-PMM's values,
and in several panels the PDF writer merged collinear segments, so a few points lie on a merged
segment and are interpolated (`collinear_points` in `published_values.json`).

Our value for each point is the mean over our replicates. A point matches when it lies within three
combined Monte Carlo SEs (ours from 200 or 100 replicates, the paper's for 1000 from the same SD)
plus one grid step. Two controls are scored at the same tolerance: the other mechanism's values
(MAR for MNAR and the reverse) and our values at the neighbouring missingness level.

Our figures (`fig*_ours.png`) are the paper's own vector pages with the plotted data taken out
(series lines and markers, dashed reference lines, histogram bars) and ours drawn in their place, in
the published colours, markers, line width and dash pattern, so the axes, labels, panel titles and
key are the paper's and only the data are ours. They line up with the published figures rasterised
from the same pages at 144 dpi (`fig*_published.png`); `fig*_overlay.png` lays ours in magenta over
the published figure in grey. The published JPEGs in `published/` are the PMC figure files, kept
for reference.

## Layout

```text
figure-reproduction/
├── main.nf, nextflow.config     the pipeline
├── requirements.txt             pinned Python packages (PyMuPDF, Pillow, NumPy)
├── results_notes.json           labels, sources, assumptions and causes (written by hand)
├── results.json                 the repository's results-check file (tools/check_results.py)
├── published/                   the paper's eight figures (CC BY 2.0), for reference
├── pipeline/
│   ├── fetch_inputs.sh          the article PDF and figures from PMC's open-access bucket, SHA-256 checked
│   ├── extract_published.py     every plotted value from the vector figures
│   ├── gbsg_targets.R           Table 1, skewness, correlations, Cox model, Fig. 1 histograms, Table 3
│   ├── run_sim.R                one chunk of the simulation (or of the true-value cohorts)
│   ├── sim_check.R              replicates rerun from scratch against the committed ones
│   ├── summarise_sim.R          the figure quantities from the per-replicate results
│   ├── truth_variants.R         the true values under variants of the data generation
│   ├── compare.py               tables, figure points and claims against the paper
│   ├── render.py                our figures and the overlays
│   ├── check_package_r.sh       R CMD build, R CMD check and the tutorial
│   ├── build_results.py, check_results.py, check_reproduction.py, compare_runs.py
│   ├── build_page.py, page_template.html, update_readmes.py, make_results_check.py
└── output/
    ├── sim/                     per-replicate results (MAR, MNAR, MCAR, COMBINED) and true-value fits
    ├── published_values.json, targets.json, summary.json, truth_variants.json, comparison.json
    ├── figures/                 fig<N>_ours.png, fig<N>_overlay.png, fig<N>_published.png
    └── report.md
```

## Run

```bash
pip install -r PMC2824146/figure-reproduction/requirements.txt
R CMD INSTALL PMC2824146/package
nextflow run PMC2824146/figure-reproduction/main.nf --outdir results          # about 15 minutes
nextflow run PMC2824146/figure-reproduction/main.nf --outdir results --full   # every replicate again
```

It needs R 4.3 with survival, mice, Hmisc, TH.data, norm, mix, jsonlite, rmarkdown, knitr and
testthat, pandoc, Python 3.11 or later, Java 21 and Nextflow. The workflow
`.github/workflows/reproduce-pmc2824146.yml` installs exactly the versions used here in an
`ubuntu:24.04` container.

The default run downloads the inputs, reads the published figures, recomputes the data-derived
results, reruns replicate 1 of the MAR study (all nine methods) and of the MNAR study, and the first
200 true-value cohorts, from scratch and checks them against `output/sim`, summarises `output/sim`,
reruns the true-value variants, compares and draws everything, checks the package, and compares the
run with the committed `output/`. The full simulation (64 chunks: 20 MAR, 20 MNAR, 10 MCAR,
10 combined, 4 of true values) took about 24 CPU hours, run on 4 cores; `--full` runs it through
Nextflow, one task per chunk. It does not run in CI.

## Pipeline steps

| Process | Does |
| --- | --- |
| `FETCH` | `fetch_inputs.sh`: the article PDF and the eight figure JPEGs, SHA-256 checked |
| `EXTRACT` | `extract_published.py`: every bar and every plotted point of Figures 1 to 8, the reference lines, the legends |
| `TARGETS` | `gbsg_targets.R`: Table 1, skewness, correlations, the Cox model (Efron and Breslow ties), the Figure 1 histograms, Table 3 |
| `SIM_COMMITTED` or `SIM_CHUNK` + `GATHER` | the per-replicate results: committed, or simulated again with `--full` |
| `SIM_CHECK` | `sim_check.R`: replicate 1 (MAR, MNAR) and true-value cohorts 1 to 200 from scratch, against the committed rows |
| `SUMMARY` | `summarise_sim.R`: mean estimate, bias, SE, coverage, p-values, model measures per mechanism, level and method |
| `TRUTH_VARIANTS` | `truth_variants.R`: true values and empirical SEs under variants of the generation (hypothesis tests) |
| `COMPARE` | `compare.py` and `render.py`: every comparison, the claims (on the paper's figure values and on ours), the figures |
| `PACKAGE` | `check_package_r.sh`: R CMD build, R CMD check, the tutorial against `package/tutorial/TUTORIAL.md` |
| `RESULTS` | `build_results.py` (results.json and its verdicts), `check_reproduction.py` (report.md; fails on any difference), `build_page.py` (the results page) |

## Limits

<!--LIMITS-->
- 200 replicates for MAR and MNAR and 100 for MCAR and combined, not 1000: the tolerances carry the
  extra Monte Carlo error, and a point can match only because our error is larger.
- The imputation packages are today's (mice 3.16.0, Hmisc 5.1-1, norm 1.0-11.1, mix 1.0-13). mice
  1.13.1 is not in the CRAN archive, and the 2002 to 2005 versions do not build on R 4.3.
- Settings the paper does not give are ours: X3 and X4 floored at 0 after back-transformation, the
  missingness intercepts at the mean of each term, the time unit (days), survival predicted at the
  means of all covariates, MIX on a restricted general location model (the unrestricted one fails on
  empty cells), aregImpute with one burn-in iteration, imputed X2 and X3 clipped to the observed range.
- The published values are read from the vector figures to 0.405 pt; a handful of points lie on
  collinear segments merged by the PDF writer and are interpolated (`collinear_points`).
- The combined mechanism leaves X3 blank in Table 2; we read it as MCAR.
- `--full` reruns the 24 CPU hours of simulation; CI reruns only replicate 1 of MAR and MNAR and 200
  true-value cohorts from scratch.
<!--/LIMITS-->
