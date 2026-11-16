# PMC2724427 figure reproduction

The simulation study of Nemes, Jonasson, Genell and Steineck (2009) run again in full, and Table 1,
Figs 1 to 3 and every claim in the text compared with the paper. The study is the package
[`../package`](../package) (`logitbias`); the pipeline calls it and holds no second copy.

## Results

<!-- table from results.json (check_results.py --markdown); do not edit by hand -->
<!--RESULTS-TABLE-->
<!--/RESULTS-TABLE-->

The study draws its own population, and the paper gives no seed. One run is compared; how far
another population moves each value (20 more populations, seeds 1 to 20) is in
`output/tables.json` and on the results page. The sensitivity and hypothesis runs (the rule for
separated samples, a population with x of SD 1) change one setting each. They test a cause and are
never counted as agreement.

<!--CLAIMS-LINE-->
<!--/CLAIMS-LINE-->

## What the code does, against the paper

| Paper | Here |
| --- | --- |
| Population of 100,000: x ~ N(2, 0.7); z ~ Bernoulli(0.6) if x > 2.5, else Bernoulli(0.4); θ = 0.1 + 2x − 0.9z; y = 1 if a uniform draw is below plogis(θ) (Additional file 1, its R lines) | the same lines, unchanged, in `logitbias::simulate_population()`; one population, seed 2724427. Checked identical to the lines run as printed (`port`). The supplement's prose reverses its own code for y; we follow the code, which gives the positive coefficient for x |
| Samples drawn by row index without replacement (`simdata[sample(100000, 500),]`) | the same; one seed per sample size, so the result does not depend on the number of cores (`bias_simulation()`) |
| n from 100 to 1500 by 5, 1,000 samples each | the same: 281 sizes, 281,000 fits |
| A logistic regression of y on x and z in each sample (function not named; Additional file 1 points to Harrell's Design library) | `glm.fit`, binomial family, R's default control |
| Separated samples (no finite estimate) not mentioned | left out and counted: a fitted probability within 1e-8 of 0 or 1, or no convergence. All are at n ≤ 370 in our run. The two other rules (only the fits R warns about; every fit) are sensitivity runs |
| OLS of the coefficient on 1/n (Equation 2); Table 1 | on the 281 per-size means (`fit_bias_curve()`); the fit on all individual estimates is reported beside it |
| Kernel regression with derivatives, "automatically adapted local plug-in bandwidth"; no numbers | `lokern::lokerns` on the per-size means; its derivative against −b1/n² (sign, and log-log slope) |
| Figs 1 to 3 | base R graphics, drawn on the published axes (fitted to the published tick marks) at the published pixel size |
| (not in the paper) | the analytic first-order bias of the estimator (Cordeiro and McCullagh 1991; Firth 1993) for the same population, as an independent value of b1 (`analytic_bias()`) |

## Layout

```text
figure-reproduction/
├── main.nf, nextflow.config, requirements.txt
├── results_notes.json        labels, assumptions, causes and page text (written by hand)
├── results.json              the repository's results-check file (tools/check_results.py)
├── status_note.txt           the words after the counts in the top-level README's status cell
├── pipeline/
│   ├── fetch_inputs.sh       Additional file 1 and the three figures, SHA-256 checked
│   ├── simulate.R            the study with logitbias (main run, seed spread, hypothesis run)
│   ├── checks.R              the port check and the kernel-derivative check
│   ├── calibrate.py          the published axes, fitted to their tick marks
│   ├── figures.R             Figs 1 to 3 on the published pixel grid, the controls, the hypothesis renders
│   ├── compare.py            Table 1, the claims, the figure scores; tables.json for the page
│   ├── check_package_r.sh    R CMD build, R CMD check, the tutorial rerendered
│   ├── build_results.py      results_notes.json + comparison.json -> ../results.json
│   ├── build_page.py, page_template.html   the results page
│   ├── check_reproduction.py the check step
│   ├── make_results_check.py results.json for tools/check_results.py
│   ├── update_readmes.py     the results tables of the READMEs, from ../results.json
│   ├── env_versions.py       runtime versions into results.json
│   └── check_results.py, compare_runs.py   copied from Paper2Repro v0.5.0
├── published/                the paper's figures (CC BY 2.0) and axes.json, with the licence note
└── output/                   the committed outputs of a full run
    ├── run/                  per_n.csv (every size and coefficient), samples_fig.csv (every estimate
    │                         at the six sizes of Figs 2 and 3), fit.json (Table 1 three ways), checks.json
    ├── seeds/                seed_1.json to seed_20.json (the spread); xsd1/ (the hypothesis run)
    ├── figs/                 fig1_ours.png, fig2_ours.png, fig3_ours.png
    └── cmp/                  comparison.json, tables.json, fig*_overlay.png
```

## Run

From the repository root, with R 4.3.3 (Ubuntu 24.04's `r-base-core`, `r-cran-knitr`,
`r-cran-rmarkdown`, `r-cran-testthat`, `pandoc` and `fonts-liberation`), lokern 1.1-12, the
package installed (`R CMD INSTALL PMC2724427/package`), Python 3.13 with `requirements.txt`, Java 21
and Nextflow 26.04.3:

```bash
nextflow run PMC2724427/figure-reproduction/main.nf --outdir results
```

This reruns the whole study and one population of the spread (seed 1), and takes the other 19
populations and the hypothesis run from `output/seeds`; the check step fails if the rerun
population differs from its committed copy. About 8 minutes on 4 cores, downloads included. CI
runs the same command (`.github/workflows/reproduce-pmc2724427.yml`) on every change to the
paper's folder. To rerun all 21 extra studies (about 50 minutes on 4 cores; the workflow's `full`
input):

```bash
nextflow run PMC2724427/figure-reproduction/main.nf --outdir results --full
```

## Pipeline steps

1. `FETCH`: Additional file 1 and the three figure files, SHA-256 checked; the figures must equal `published/`.
2. `SIMULATE`: `simulate.R`, 281,000 logistic fits on 4 cores; then `checks.R` (port check, kernel derivatives).
3. `SEEDS`: the seed spread and the hypothesis run (only seed 1 without `--full`).
4. `FIGURES`: `calibrate.py` fits the published axes; `figures.R` draws ours, the negative controls and the hypothesis renders.
5. `COMPARE`: every field, claim and figure score; overlays; `tables.json`.
6. `PACKAGE`: `check_package_r.sh` on `../package`.
7. `RESULTS`: `../results.json`, verdicts computed by `check_results.py`.
8. `PAGE`: the results page and `report.md`.
9. `CHECK`: `check_results.py` passes, no verdict changed against the committed `../results.json`, and `compare_runs.py` finds the fresh outputs equal to `output/`.

## Limits

- The authors' simulation code is lost. Only the population lines survive. The fitting function, the handling of separated samples, the input of the OLS fit (means or every estimate), the seed and the kernel software are not stated. Our choices are in the table above and in `../results.json`; none was tuned to the paper's numbers.
- One population is compared. The paper's population was never deposited, so its intercepts cannot come back exactly; the spread over 20 populations shows how far they move.
- The figures are compared on the published axes. Points of ours that fall outside them are clipped and counted in `output/cmp/comparison.json`.
- We could not run Harrell's Design library of 2009 (`lrm`), which Additional file 1 mentions: it no longer builds with current R, and its handling of separated samples was not emulated.
