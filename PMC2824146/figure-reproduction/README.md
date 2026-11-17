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
<!--/RESULTS-TABLE-->

<!--RESULTS-PROSE-->
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

The figures are drawn on the published axes (`fig*_ours.png`) and laid over the published vector
figure rasterised at 144 dpi (`fig*_overlay.png`, ours in magenta). The published JPEGs in
`published/` are the PMC figure files, kept for reference.

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
<!--/LIMITS-->
