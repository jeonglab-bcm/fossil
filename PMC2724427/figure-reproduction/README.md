# PMC2724427 figure reproduction

The simulation study of Nemes, Jonasson, Genell and Steineck (2009) run again in full, and Table 1,
Figs 1 to 3 and every claim in the text compared with the paper. The study is the package
[`../package`](../package) (`logitbias`); the pipeline calls it and holds no second copy.

## Results

<!-- table from results.json (check_results.py --markdown); do not edit by hand -->
<!--RESULTS-TABLE-->
5 exact, 2 agrees, 3 partly, 1 inconclusive, 7 differs, 1 not attempted; 8 open causes.

| Item | Verdict | Measure | Why |
| --- | --- | --- | --- |
| Table 1, continuous variable (intercept and n⁻¹: estimate, SE, t, p) | partly | 2 of 8 fields as printed | The intercept is the population draw: 2.011 lies inside our 20 populations (1.962 to 2.023; ours 1.966). The n⁻¹ slope and both SEs do not: b1 is 26.7 to 30.0 over 20 populations against 23.9, and the SEs are about 1.5 times the paper's, because our per-size means scatter more. The analytic first-order bias of our population is 23.8, close to the paper's 23.9. A population with x of SD 1 comes closer (b1 25.2, SE 0.307, intercept SE 0.00080) but does not close the gap. |
| Table 1, discrete variable (intercept and n⁻¹: estimate, SE, t, p) | partly | 1 of 8 fields as printed | The intercept is the population draw: -0.898 lies inside our 20 populations (-0.956 to -0.866; ours -0.855 is the far end of that spread). The slope does not come back: -1.9 here and -2.4 to -5.7 over 20 populations against -9.524, with SEs 2 to 3 times the paper's. Leaving out separated samples pulls the small-n means of the discrete coefficient toward zero; keeping the fits R does not warn about pushes them far away (b1 -67). The paper's rule is not stated. A population with x of SD 1 gives -8.1. |
| Text: R² of the OLS fit, 0.963 (continuous) and 0.836 (discrete) | differs | 0 of 2 fields as printed | Ours 0.940 and 0.034 against 0.963 and 0.836; over 20 populations 0.926 to 0.955 and 0.04 to 0.22. The R squared of the fit to all estimates is near 0.02, so the paper fitted the means. Our per-size means scatter more around the curve than the paper's, most for the discrete coefficient. A population with x of SD 1 gives 0.960 and 0.566. Follows table1. |
| Claims recomputed from the paper's own numbers (SE = estimate / t in Table 1; P(x>2.5) of Additional file 1) | differs | 4 of 5 come back from the paper's own numbers; not back: Table 1, discrete Intercept: SE = estimate / t (paper 0.00065, recomputed 0.00066) | In Table 1 the discrete intercept's printed estimate and t (-0.898, -1369.34) imply an SE of 0.000656, printed as 0.00065 (cut, not rounded). The other three SEs and P(x>2.5) come back. |
| The paper against itself: Fig. 2's headings and Table 1's curve 2.011 + 23.9/n | differs | 1 of 6 Fig. 2 headings lie within 0.02 of Table 1's curve 2.011 + 23.9/n; n=100 2.262 against 2.250, n=150 2.129 against 2.170, n=300 2.051 against 2.091, n=500 2.019 against 2.059, n=750 2.011 against 2.043, n=1000 2.003 against 2.035 | Fig. 2's headings are means at six sizes; Table 1's curve 2.011 + 23.9/n gives the means it implies. Five of six headings lie 0.02 to 0.04 below the curve (2.003 at n = 1000 against 2.035), and Fig. 3's medians sit higher still (about 2.07 at n = 1000). Figs 2 and 3 cannot come from the run behind Table 1 and Fig. 1. |
| Additional file 1: P(x>2.5) = 0.2375 | exact | 1 of 1 fields as printed |  |
| Abstract and Results: estimates biased away from zero, odds ratios away from one | exact | 3 of 3 fields as printed |  |
| Results: the fit is better for the continuous than for the discrete variable | exact | 1 of 1 fields as printed |  |
| Results and Fig. 2: the sampling distribution is skewed at small n and grows symmetric | exact | 2 of 2 fields as printed |  |
| Results and Fig. 3: extreme estimates become rarer as n grows | exact | 2 of 2 fields as printed |  |
| Methods: kernel regression derivatives confirm the convergence rate | partly | 2 of 4 fields as printed | The continuous coefficient's kernel derivative has the sign of -b1/n² everywhere and falls as n to the power -2.07. The discrete check fails because our discrete means have almost no 1/n trend (b1 -1.9, R² 0.03, see table1.discrete), which depends on the unstated handling of separated samples. |
| Discussion: maximum likelihood is risky under n = 100 and adequate above 500 (Long 1997) | not attempted | not attempted | A citation of Long (1997), not a result of the paper. |
| Fig. 1, continuous variable | inconclusive | 11.77% within 2 px (pass 16.8%, best control 16.3%) | Drawn on the published axes, 162 of our 281 means fall below them: our population sits lower (intercept 1.966 against 2.011) and our means scatter more. Moving our series by the difference of the intercepts raises the score from 12% to 54%; a population with x of SD 1 reaches 72%. Neither reaches the published points. |
| Fig. 1, discrete variable | differs | 0.38% within 2 px (pass 3.5%, best control 3.0%) | 267 of our 281 means fall outside the published axes: our population's discrete coefficient is -0.840 (Table 1 -0.898) and our means have almost no 1/n trend (see table1.discrete). Moving our series by the difference of the intercepts gives 19%; a population with x of SD 1 gives 1%. |
| Fig. 2, densities at n = 100, 150, 300, 500, 750 and 1000 | differs | 13.11% within 2 px (pass 17.7%, best control 17.2%) | Our densities are wider and lower: the sampling SD at n = 1000 is 0.25 to 0.27 over 21 populations, while the published curve's peak of about 2.35 implies about 0.17. A kernel bandwidth 0.8 or 1.25 times ours does not help. A population with x of SD 1 (SD 0.20) raises the score from 13% to 54%. |
| Fig. 2, the mean in each panel heading | differs | 0 of 6 fields as printed | Each heading is a mean of 1,000 random estimates and is printed to three decimals, so it cannot come back exactly. Over 20 populations our means at five of the six sizes span the paper's heading; at n = 150 the paper's 2.129 is 0.006 below our lowest (2.135). Figs 2 and 3 also disagree with Table 1 (text.figures_vs_table1). |
| Fig. 3, box plots at the same six sizes | differs | 41.87% within 2 px (pass 50.0%, best control 49.5%) | Our boxes are taller (our sampling spread is about 1.5 times the paper's) and our medians lower; the published medians stay near 2.07 to 2.2 at every size, above Fig. 2's means. The control shifted up by 1% of the axis scores better than ours, so a shift is part of the gap. A population with x of SD 1 raises the score from 42% to 60%. |
| simulate_population() against the R lines of Additional file 1 | agrees | simulate_population(seed = 2724427) is identical to the R lines of Additional file 1 run on the same seed (100,000 rows: x, z and y all equal) |  |
| R package logitbias and its tutorial | agrees | logitbias 0.1.0: R CMD check Status: OK; tests 23 passed, 0 failed, 0 warnings, 0 skipped; tutorial rendered, TUTORIAL.md unchanged, 1 figures |  |
<!--/RESULTS-TABLE-->

The study draws its own population, and the paper gives no seed. One run is compared; how far
another population moves each value (20 more populations, seeds 1 to 20) is in
`output/tables.json` and on the results page. The sensitivity and hypothesis runs (the rule for
separated samples, a population with x of SD 1) change one setting each. They test a cause and are
never counted as agreement.

<!--CLAIMS-LINE-->
The main claim holds: in our run logistic regression pushes both coefficients away from zero, more at small n, and the sampling distribution is skewed at small n and grows symmetric. Table 1's slopes, SEs and R squared values and the figures' spreads do not come back; the causes are open (the paper's per-size means scatter less than any population of Additional file 1's design gives), and the intercepts move with the population draw.
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
population differs from its committed copy. About 5 minutes on 4 cores, downloads included. CI
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
