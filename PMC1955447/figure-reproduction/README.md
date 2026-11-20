# PMC1955447 figure reproduction

Moineddin R, Matheson FI, Glazier RH. A simulation study of sample size for multilevel logistic regression models.
*BMC Medical Research Methodology* 7:34 (2007). [doi:10.1186/1471-2288-7-34](https://doi.org/10.1186/1471-2288-7-34). CC BY 2.0.

The paper has no figures; its results are Tables 1-5 (the simulation study) and the claims of its text. Nothing of
the paper is in this folder: `output/published_values.json` holds the printed numbers of Tables 1-5, read from the
article XML by `pipeline/extract_published.py` (rerun with `--extract`, which downloads the XML and checks its
SHA-256).

## Results

<!-- full table from results.json (check_results.py --markdown); regenerate with pipeline/update_readmes.py -->

<!--RESULTS-TABLE-->
1 exact, 5 agrees, 21 partly, 1 not attempted; 19 open causes.

| Item | Verdict | Measure | Why |
| --- | --- | --- | --- |
| Methods: variances 0.13, 0.67, 2.0 give ICC 0.04, 0.17, 0.38 and σ0 0.36, 0.82, 1.42 | exact | 5 of 5 fields as printed, 1 paper errors |  |
| Methods and Table 4: prevalence close to 30% in the main grid; 0.10, 0.34, 0.45 with Table 4's coefficients | partly | 1 of 4 fields as printed | The stated design gives a prevalence of 32.1% over the main grid (30.5, 31.8 and 34.0% at the three ICCs, by numerical integration), which the paper calls 'close to 30 percent'; Table 4's middle column, labelled 0.34, has an expected prevalence of 0.324 (0.095, 0.324, 0.446 in our data sets). |
| Table 1, % converged in each of the 27 cells | partly | 24 of 27 fields as printed | Which fits count as converged is NLMIXED's verdict, and NLMIXED cannot be run here. Our NLMIXED-like optimizer gives 55, 77, 82% at 30 groups x 5 (paper 56, 68, 76); the bias and coverage of the group-size-5 cells move with which fits are kept. No variant of the optimizer settings moves 30 groups x 5 to the paper's rates (replicates 0-199: without σ01 96, 98, 98%, without ABSXCONV 38, 62, 78%, 2,000 function calls 68, 76, 86%, fewer quadrature points 60, 80, 86%, 3 points 62, 74, 88%). On 200 data sets per design, whose tolerance is wider, three variants score all 27 convergence cells, as our own reading does. |
| Table 1, % relative bias in the 19 cells that converged in 98-100% of data sets (114 values) | agrees | 114 of 114 fields as printed | Assumed: The fitted model estimates the covariance σ01 of the random intercept and slope (the model of equation 1), started at 0, although the data are drawn with σ01 = 0. The paper reports no σ01 and does not say whether it was fitted.; σ0 and σ1 in Tables 1-5 are the variances as fitted (NLMIXED's random statement takes variances): % bias of the variance estimate, Wald interval on the variance. The tables label them σ0 and σ1. |
| Table 1, % relative bias in the 8 cells that converged in 56-94% of data sets (48 values) | partly | 45 of 48 fields as printed | The 3 misses are σ1's bias at 30 groups x 5, ICC 0.04 σ1; 30 groups x 5, ICC 0.17 σ1; 50 groups x 5, ICC 0.04 σ1. At 30 groups x 5 our σ1 biases are 28.6, 31.2, 43.2% against the paper's 55.49, 54.55, 54.02 (second run 24.6, 36.2, 35.7). These designs keep 55-82% of fits, and the mean of the kept variance estimates depends on which fits NLMIXED declared converged; NLMIXED cannot be run here. |
| Table 2, non-coverage pooled by number of groups, group size and ICC (54 values) | partly | 51 of 54 fields as printed | The misses are σ0's pooled non-coverage at 100 groups, group size 5 and ICC 0.04, the levels that hold the low-ICC and group-size-5 designs where σ0's interval covers more often than the paper's (Table 3). There NLMIXED's verdict on the fit and its standard error at a near-zero variance decide the interval; our boundary fits have no positive definite Hessian and no interval. Elsewhere the variance-scale interval matches (38 of 38 σ cells of the 98-100% designs). |
| Table 2, the 18 p-values for the effect of each factor on non-coverage, as significant or not at 0.05 | partly | 12 of 18 fields as printed | Table 2's p-values pool about 24,000 fits, so a difference of half a point of non-coverage between levels is significant; whether the paper's small differences cross 0.05 depends on Monte Carlo error and on which fits enter. σ0's group-size test follows σ0's coverage gap at group size 5 (Table 3). 4 of 18 calls change between our two runs. |
| Table 3, non-coverage in the 19 cells that converged in 98-100% of data sets (114 values) | agrees | 114 of 114 fields as printed | Assumed: The fitted model estimates the covariance σ01 of the random intercept and slope (the model of equation 1), started at 0, although the data are drawn with σ01 = 0. The paper reports no σ01 and does not say whether it was fitted.; σ0 and σ1 in Tables 1-5 are the variances as fitted (NLMIXED's random statement takes variances): % bias of the variance estimate, Wald interval on the variance. The tables label them σ0 and σ1. |
| Table 3, non-coverage in the 8 cells that converged in 56-94% of data sets (48 values) | partly | 43 of 48 fields as printed | σ0's interval covers more often than the paper's where the random intercept is small and fits often stop near a zero variance (ICC 0.04, and groups of 5): non-coverage 0.064 at 30 groups x 5, ICC 0.04 (paper 0.142) and 0.072 at 100 x 5 (paper 0.172). There NLMIXED's verdict on the fit and its standard error at a near-zero variance decide the interval; our boundary fits have no positive definite Hessian and no interval. Elsewhere the variance-scale interval matches (38 of 38 σ cells of the 98-100% designs). |
| Table 4, % bias, non-coverage and % converged at prevalence 0.10, 0.34 and 0.45 (54 values) | partly | 33 of 54 fields as printed | 33 of the 36 biases and non-coverage rates come back; % converged does not: pooled over the nine groups x size designs our fit converges in 89, 97, 98% of data sets at the three prevalences, against the paper's 77, 86, 87. The paper does not say which designs Table 4 ran, and its own Table 1 has about 95% converged at a random-intercept variance near 1. The misses in bias (σ1 at 0.10, γ11 at 0.45) and σ0's non-coverage at 0.10 sit in the designs whose fits depend on convergence. |
| Table 5, % converged of the eight non-normal models in 9 cells each (72 values) | partly | 71 of 72 fields as printed | Model 7 at 50 groups x 5: the paper prints 80% converged, below model 1's 88%, while its text says model 7 converged more often than model 1 with groups of 5 (p < 0.01). Our 100% agrees with the text. |
| Table 5, % relative bias (432 values) | partly | 396 of 432 fields as printed | 61 of the 65 missed Table 5 bias and coverage cells are in models 6 and 7, nearly all of them σ0 and σ1; their random effects are t with 3 degrees of freedom, and our variance estimates fall further below the t3 variance than the paper's (0 misses in models 1 to 5). The paper does not say how the t variates were drawn or which true variance the bias refers to. |
| Table 5, % non-coverage (432 values) | partly | 403 of 432 fields as printed | Most misses are σ0 and σ1 of models 6 and 7 (t3 random effects), whose variance estimates and intervals fall further from the t3 variance than the paper's; see the Table 5 bias row. |
| Convergence: 56% to 100% by cell; 80.4/99.3/99.9% by group size, 87.7/93.8/98.1% by number of groups, 89.2/94.5/95.9% by ICC; no negative variances | partly | 8 of 13 fields as printed | The text's convergence rates are the means of Table 1's, so they carry Table 1's convergence gap: by number of groups ours are 89.4, 93.9, 97.0% (paper 87.7, 93.8, 98.1) and by ICC 87.2, 96.0, 97.2% (89.2, 94.5, 95.9). The pattern (rising with groups and group size) came back. |
| Converged against non-converged data sets: prevalence 30.4% vs 30.0%; z mean and SD 0.01 and 1.01 vs 0.02 and 1.00; x 0.00 and 1.00 vs 0.00 and 1.00 | partly | 5 of 10 fields as printed | The stated design gives a prevalence of 32.1% over the main grid, so ours is 32.1% in converged and 30.8% in non-converged data sets against the paper's 30.4 and 30.0. Our SD of z is the mean over data sets of each one's sample SD (below 1 by the small-sample bias of an SD); the paper's 1.01 is not stated as either. Means of z and x come back. |
| Non-converged data sets of 30 groups x 5 refitted with a random intercept only and a random slope only: both significant in 2.4% (168 data sets) | partly | 1 of 2 fields as printed | The paper examined 168 non-converged data sets of 30 groups x 5; we have 867 (453, 229, 185 at the three ICCs), and the paper does not say which 168 it took. With likelihood-ratio tests both random effects are significant in 1.3% of ours (paper 2.4%, within Monte Carlo error of 168 data sets); with NLMIXED's Wald t tests on the variances in 0.0%. |
| Shapiro-Wilk tests of the fixed-effect estimates: most non-normal with groups of 5 even with 100 groups, a few non-normal with groups of 30 and 50 groups, all normal with 100 groups of 50 | partly | 1 of 3 fields as printed | With 100 groups of 50, 1 of 12 Shapiro-Wilk tests is significant at 0.05 (twelve tests at 0.05 give at least one in about half of all runs); with 100 groups of 5, 6 of 12 are, not the majority. With 50 groups of 30, 2 of 12, as the paper says. The paper does not give its counts. |
| Overall fixed-effect bias 0.6%, 2.6%, 1.4% and 3.7% for γ00, γ01, γ10, γ11 ('data not shown'); γ11 the largest | partly | 3 of 5 fields as printed | The text's overall biases are Table 1 averaged over all converged fits (the arithmetic gives 0.60, 2.58, 1.37, 3.75); they are dominated by the groups-of-5 designs, whose kept fits depend on NLMIXED's convergence. Ours are 1.20, 2.84, 0.75, 1.92%; γ11's falls short because our γ11 bias at 30 groups x 5 is lower (Table 1). |
| Largest fixed-effect biases 8.8%, 11.1%, 15.8%, 13.3% at 30 groups x 5, ICC 0.04; below 6% at 30 x 30, below 4% at 50 x 30, 1% or less at 100 x 30 | partly | 7 of 8 fields as printed, 3 paper errors | One threshold misses: at 50 groups x 30 our largest fixed-effect bias is γ01's 5.0% at ICC 0.38 (Monte Carlo SE 2.4), against the text's 'below 4%'. Three statements are left out because the paper's own Table 1 contradicts them. |
| Variance components: overall bias 6.9% (σ0) and 5.0% (σ1); σ0 21.2% at σ0 0.36 (21%, 0.5%, 0.1% by ICC); σ1 4-6% by ICC; below 4% at 100 x 50; positive at group size 5, negative at 30 and 50 | partly | 10 of 11 fields as printed | σ1's overall bias at ICC 0.04 is 1.42% (paper: 4 to 6% at every ICC) because our σ1 bias at 30 groups x 5, ICC 0.04, is about half the paper's (Table 1), a design that keeps 55% of fits. At 100 groups x 50 our σ0 bias at ICC 0.04 is -5.1% (Monte Carlo SE 0.9), against the text's 'below 4%'. σ0's overall and by-ICC biases come back. |
| Non-coverage: fixed effects 5-6% by number of groups (4-6% in Table 2, 3-7% by cell); variance components 7-11% (11% and 10% at 30 groups, 9% and 7% at 100; 7-17% by cell); σ1 rises with group size, σ0 falls with ICC | partly | 14 of 15 fields as printed, 1 paper errors | The misses follow σ0's coverage gap in the low-ICC designs (Table 3): our σ0 non-coverage rises with ICC instead of falling, and at 30 and 100 groups it is below the paper's. There NLMIXED's verdict on the fit and its standard error at a near-zero variance decide the interval; our boundary fits have no positive definite Hessian and no interval. Elsewhere the variance-scale interval matches (38 of 38 σ cells of the 98-100% designs). |
| Prevalence: 10% gives the largest bias and the lowest convergence; non-coverage 5-6% (fixed) and 8-11% (random); largest bias 12% and 50% with groups of 5, 9% and 15% with 30 groups ('data not shown') | partly | 7 of 11 fields as printed | These statements rest on Table 4, whose designs the paper does not state and whose convergence we do not reproduce (89, 97, 98% against 77, 86, 87). Keeping more fits at 10% prevalence, our biases there are smaller: the 10% prevalence does not have the largest bias, and the largest variance-component bias with groups of 5 is 28.9% (paper 50%, 'data not shown'). |
| Non-normal models against model 1 (Discussion): convergence with groups of 5 higher for models 3, 6, 7, 8 and lower for 4, 5; no difference in fixed effects; variances underestimated for models 6-8; random-effect coverage lower for models 6 and 7 | partly | 18 of 19 fields as printed, 1 paper errors | With groups of 5, model 2 converges in 96% of our data sets against model 1's 90% (p 0.003); the paper finds no difference. Every other test came back but the statement that no model differs with groups of 30 or more: ours differ (models 4 and 5), and so does the paper's own Table 5, so it is set aside as a slip in the text. |
| Main claim (Abstract, Conclusion): fixed effects unbiased with 100 groups of 50, variance components slightly biased there, severe bias with groups of 5, fixed-effect SEs right and variance-component SEs too small, low prevalence needs larger samples | partly | 4 of 9 fields as printed | 4 of 9 parts hold on our run: fixed effects are unbiased with 100 groups of 50, biases are severe with groups of 5, convergence fails where samples are small, and the variance intervals stay too narrow at 100 x 50. The misses: at 100 x 50 our largest variance bias is σ0's -5.1% (Monte Carlo SE 0.9) against the text's 'below 4%'; with groups of 5 our fixed-effect intervals over-cover (non-coverage down to 0.9%) and σ0's under ICC 0.04 also covers more than the paper's (Table 3); and our Table 4 does not make the 10% prevalence the most biased (Table 4's convergence). |
| Claims and pooled values recomputed from the paper's own tables (Table 2 from Tables 1 and 3; the text from Tables 1-5) | agrees | 123 of 139 statements and pooled values follow from the paper's own tables. Not: methods_design: sigma0 = sqrt(2.0) (1.42 against 1.4142); text_convergence: % converged, size 5 (80.4 against 81.1111); text_fixed_bias_cells: g01: the largest bias of the 27 cells is at 30 groups x 5, ICC 0.04 (yes against no); text_fixed_bias_cells: g11: the largest bias of the 27 cells is at 30 groups x 5, ICC 0.04 (yes against no); text_fixed_bias_cells: every fixed-effect bias 1% or less at 100 groups x 30 (yes against no); text_random_bias: overall % bias σ0 (6.9 against 7.5363); text_random_bias: overall % bias σ1 (5.0 against 5.2064); text_random_bias: % bias σ0 at σ0 = 0.36 (ICC 0.04) (21.2 against 22.7106); text_random_bias: % bias σ0, ICC 0.04 (21 against 22.7106); text_random_bias: % bias σ0, ICC 0.17 (0.5 against 0.6467); text_random_bias: % bias σ0, ICC 0.38 (0.1 against 0.1746); text_random_bias: lowest % bias σ1 over the ICCs (4 against 4.6512); text_noncoverage: lowest variance-component non-coverage of a cell (%) (7 against 3.0); text_robustness: model 7 against model 1, convergence with groups of 5 (p < 0.01) (more likely against no difference); text_robustness: model 8 against model 1, convergence with groups of 5 (p < 0.01) (more likely against no difference); text_robustness: no model differs from model 1 in convergence with groups of 30 or 50 (yes against no). |  |
| mlagq's likelihood and maxima against direct numerical integration | agrees | mlagq's adaptive quadrature log-likelihood against a dense-grid integral on 9 data sets of 30 groups x 5 and x 30 (all ICCs): every relative difference below 1e-4; at 9 interior maxima no step of 1e-4 in any parameter raises the dense-grid log-likelihood by 1e-5 or more |  |
| The authors' SAS 9.1 PROC NLMIXED programs | not attempted | not attempted | The simulations ran in SAS 9.1 with PROC NLMIXED and no code was released or found (issue #86 lists the search). SAS is proprietary and not available here, so the rebuilt method (mlagq) is checked against the paper's tables and against direct numerical integration, not against NLMIXED. |
| Python package mlagq and its tutorial | agrees | mlagq 0.1.0: wheel installed in a fresh environment and imported from it; tests 6 passed; tutorial 7 cells compared, 0 skipped (nondeterministic); TUTORIAL.md in sync |  |
<!--/RESULTS-TABLE-->

<!--CLAIMS-LINE-->
The main claim holds in part: on our run fixed effects are unbiased with 100 groups of 50, biases are severe with groups of 5, convergence fails where samples are small, and the variances' intervals stay too narrow even with 100 groups of 50. Our run does not make the 10% prevalence the most biased, and with groups of 5 some of our fixed-effect intervals cover more often than the paper's (non-coverage down to 0.9% against its lowest 2.8%); both depend on which fits NLMIXED kept.
<!--/CLAIMS-LINE-->

<!--DETAILS-->
## Comparing Monte Carlo tables

No printed cell can come back exactly: the paper's seeds and random-number generator are not given. Each cell is
compared at a tolerance fixed before the comparison: half a unit of the last printed digit plus 3 x √2 Monte Carlo
standard errors of one estimate (ours stands in for the paper's): the SD of the converged fits' estimates over √n
for % bias, √(p(1 - p)/n) for non-coverage and % converged. Table 2's p-values are compared as significant or not at
0.05.

How good is that test? Our second run (other seeds) falls within the tolerance of our main run in
114 of 114, 48 of 48 and 27 of 27 Table 1 cells, and
114 of 114 and 48 of 48 Table 3 cells. Against the paper, the right designs
give 114 of 114 high-convergence bias cells; the neighbouring design of a wrong input gives at most
111 (a neighbouring ICC barely moves the fixed effects, so only the σ columns and the other factors
tell designs apart), and 17 of 27 convergence cells against our 24. For Table 5
the next model scores 377 bias and 359 non-coverage cells against our
396 and 403.

The settings the paper does not state were found by scoring alternatives on the same data sets
(`hypotheses` in `output/comparison.json`): σ01 estimated, the variance scale of σ0 and σ1, the paper's ABSXCONV,
the number of quadrature points, the interval for the variances, Table 4's designs and Table 5's non-coverage.
Each is an assumption of `results.json` with its sensitivity. The variants refit replicates 0-199 of every cell of
the main grid; their records are not kept (about 4 MB), their summaries are (`output/records/extra.json`).

## Layout

| Path | Content |
| --- | --- |
| `main.nf`, `nextflow.config` | The pipeline. |
| `requirements.txt` | Pinned Python packages; the package `mlagq` is installed from `../package`. |
| `results_notes.json` | Labels, assumptions, causes and the page's prose, written by hand; merged with the run into `../results.json`. Numbers in the prose are filled from the run. |
| `results.json` | The repository's results check (`tools/check_results.py`): our value for every compared cell and claim. |
| `pipeline/` | `fetch_inputs.sh`, `extract_published.py`, `simulate.py`, `sim_check.py`, `summarize.py`, `record_tests.py`, `compare.py`, `claims.py`, `crosscheck.py`, `build_results.py`, `make_results_check.py`, `build_page.py` with `page_template.html`, `check_reproduction.py`, `update_readmes.py`, `env_versions.py`; copies of the skill's `check_results.py`, `compare_runs.py` and `check_package.py`. |
| `output/published_values.json` | Every printed number of Tables 1-5. |
| `output/records/` | One record per data set (status, estimates, standard errors) of the main grid (27,000), the prevalence study (27,000) and Table 5 (7,200), gzipped CSV with 8 significant digits; `extra.json`, the summaries of the second run and the variants. |
| `output/simulation.json` | Every summary the comparison uses. |
| `output/comparison.json`, `output/tables.csv` | Every printed cell against ours, with tolerances, the second run, the controls and the hypotheses; the same cells as one CSV. |
| `output/claims.json`, `output/record_tests.json` | Every claim of the text against the paper's own tables and our two runs; the tests the claims need from the records (the non-converged follow-up, Shapiro-Wilk, the Table 5 tests). |
| `output/crosscheck.json`, `output/sim_check.json`, `output/package.json` | The likelihood against direct integration; the first replicates rerun from scratch; the package check. |

## Run

```bash
pip install -r PMC1955447/figure-reproduction/requirements.txt ./PMC1955447/package
nextflow run PMC1955447/figure-reproduction/main.nf --outdir results
nextflow run PMC1955447/figure-reproduction/main.nf --outdir results --full       # rerun the whole study
nextflow run PMC1955447/figure-reproduction/main.nf --outdir results --extract    # reread the printed tables from the XML
```

The default run takes about 10 minutes on 4 cores: 378 data sets (the first 3 of every cell) simulated and fitted
again from scratch and checked against the committed records, the summaries, comparisons and claims recomputed
from the records, the cross-check (about 2 minutes) and the package check (about 1 minute). `--full` reruns all
61,200 data sets of Tables 1-5, the second run of Tables 1-3 (27,000) and the six variants (32,400), about 6 CPU
hours. `.github/workflows/reproduce-pmc1955447.yml` runs the default on every pull request that touches this paper,
and `--full` when started by hand.

## Pipeline steps

1. `FETCH`: the article XML from PMC's open-access bucket (Europe PMC as a fallback), SHA-256 checked.
2. `PUBLISHED_VALUES`: the committed printed values, or with `--extract` read again from the XML and checked against them.
3. `RECORDS_COMMITTED` and `SIM_CHECK` (default), or `SIMULATE` (`--full`): the per-replicate records.
4. `SUMMARIZE`: every printed quantity from the records.
5. `RECORD_TESTS`: the non-converged follow-up (refits), Shapiro-Wilk tests and the Table 5 tests.
6. `COMPARE` and `CLAIMS`: every printed cell and claim against ours, the controls and the hypotheses.
7. `CROSSCHECK`: mlagq's likelihood against a dense-grid integral, and its maxima against the exact likelihood's.
8. `PACKAGE`: `check_package.py` on `../package` (wheel, fresh install, tests, tutorial rerun).
9. `RESULTS`: `results.json` (verdicts by `check_results.py`), the repository's results check, the results page, and `check_reproduction.py` against the committed outputs (`report.md`); `CHECK` fails the run if anything differs.

## Limits

- **The SAS code is lost and SAS is not available.** The fit is rebuilt from the paper's description of PROC NLMIXED and checked against direct numerical integration and the paper's tables, not against NLMIXED (`port` is not attempted).
- **Convergence is NLMIXED's.** Which fits count as converged decides the group-size-5 rows of Tables 1 and 3, Table 4's convergence and the low-convergence models of Table 5. Our optimizer follows NLMIXED's documented defaults; its line search and update are not public. Every summary depends on this through the fits it keeps.
- **Three readings were found from the tables**, not read from the paper: σ01 estimated, σ0 and σ1 as variances, and Table 5's non-coverage over all data sets (`found_by_search` in `results.json`). The follow-up's likelihood-ratio tests are a fourth.
- **Table 4's designs are not stated.** We pool the nine designs of the main grid; no combination of numbers of groups and group sizes we tried (49) gives the paper's convergence (the closest is 2.8 points off on average).
- **Monte Carlo error.** Every cell carries it, Table 5 most (100 data sets per cell).
<!--/DETAILS-->

## What the code does, against the paper

| Paper | Here |
| --- | --- |
| logit p_ij = γ00 + γ10 x_ij + γ01 z_j + γ11 x_ij z_j + u0j + u1j x_ij (equation 2) | `mlagq.simulation.generate`: as printed; fixed effects 1, z, x, x z; random intercept and slope on x. |
| x_ij, z_j standard normal; u0j, u1j independent normal; σ1 = 1; random-intercept variance 0.13, 0.67, 2.0 (ICC 0.04, 0.17, 0.38); γ = (-1.0, 0.3, 0.3, 0.3); 30, 50, 100 groups of 5, 30, 50; 1,000 data sets per cell | As printed. The variances are used as given (σ0 = 0.361, 0.819, 1.414; the paper prints 0.36, 0.82 and 1.42). |
| SAS 9.1 PROC NLMIXED, default options: full maximum likelihood, normal random effects, adaptive Gaussian quadrature with the points selected automatically | `mlagq.fit`: the marginal likelihood by adaptive Gauss-Hermite quadrature centred and scaled at each group's posterior mode, re-adapted at every iteration; the number of points per dimension chosen at the starting values by NLMIXED's rule (1, 3, 5, 7, 9, 11, 21, 31 until two successive log-likelihoods differ by less than 1e-4, the larger kept). Checked against a dense-grid integral (`CROSSCHECK`). |
| Dual quasi-Newton; starting values at the true values; "absolute value for parameter convergence criterion" 1e-8; at most 200 iterations | BFGS with a backtracking line search from the true values (σ01 started at 0); converged on NLMIXED's default gradient criteria (ABSGCONV 1e-5, GCONV 1e-8) or when no parameter moves by more than 1e-8 in an iteration (ABSXCONV, our reading of the paper's criterion); at most 200 iterations and 500 function calls (NLMIXED's MAXFUNC). |
| The model with σ01 (equation 1); data drawn with σ01 = 0 | σ01 estimated; the variances and the covariance unconstrained, so a trial point with a covariance matrix that is not positive definite has no likelihood. |
| "If convergence was not achieved the estimated parameters were not included" | Summaries over converged fits only. |
| % relative bias of σ0 and σ1; non-coverage of the 95% Wald interval "from the asymptotic standard normal distribution" | On the variance scale, the parameters as fitted (the SD scale is a tested hypothesis); Wald intervals from the observed information. |
| Table 2: non-coverage by factor, with p-values from logistic regression | All converged fits of a level pooled; p from a likelihood-ratio test of the 3-level factor; compared as significant or not at 0.05. |
| Table 4: prevalence 0.10, 0.34, 0.45 with γ = (-3, .3, .3, .3), (-1, .3, .3, .3), (-.3, -.3, -.3, -.3), both variances 1 | The nine groups x size cells of the main grid, 1,000 data sets each, pooled per prevalence (the cells and the pooling are not stated). |
| Table 5: eight models for the distributions of (z, u0, u1, x), 100 replications | All 72 cells x 100; the true variance of a random effect is its distribution's variance (t3: 3, t5: 5/3, U(-2, 2): 4/3). |
| SAS's random-number generator, seeds not given | NumPy 2.2.6 PCG64, one stream per data set (seed [19554471, study, cell, replicate]); a second run of the main grid uses base 19554472. |
