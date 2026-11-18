# PMC2430201 figure reproduction

Friedrich JO, Adhikari NKJ, Beyene J. The ratio of means method as an alternative to mean differences for
analyzing continuous outcome variables in meta-analysis: a simulation study. *BMC Medical Research Methodology*
8:32 (2008). [doi:10.1186/1471-2288-8-32](https://doi.org/10.1186/1471-2288-8-32). CC BY 2.0.

The paper has no figures; its results are Tables 3-8 (the simulation study) and the claims of its text. Nothing of
the paper is in this folder: `output/published_values.json` holds the printed numbers of Tables 1-8, read from the
article XML by `pipeline/extract_published.py` (rerun with `--extract`, which downloads the XML and checks its
SHA-256).

## Results

<!-- full table from results.json (check_results.py --markdown); regenerate with pipeline/update_readmes.py -->

<!--RESULTS-TABLE-->
2 exact, 14 agrees, 3 partly, 3 not attempted; 0 open causes.

| Item | Verdict | Measure | Why |
| --- | --- | --- | --- |
| Table 1, low-dose dopamine meta-analysis: pooled MD, SMD and RoM with CIs, p and I2 | not attempted | not attempted | Table 1 reprints pooled results of the authors' 2005 dopamine meta-analysis (Ann Intern Med 142:510). This paper does not print the trials' means, SDs and sizes, and the 2005 paper and its appendix are not open access. Its printed numbers are checked against each other (table1.consistency). |
| Table 1: each estimate at the midpoint of its CI, and each p-value from its CI | exact | 13 of 13 fields as printed, 1 paper errors |  |
| Table 2, the parameter values of the simulated data sets | not attempted | not attempted | The design of the simulation (SD, number of trials, patients per arm, effect size, heterogeneity); used as input, nothing to compare. |
| Table 3, normal data, SD 40% of the control mean, equal arms (18 rows x 21 cells) | partly | 377 of 378 fields as printed | One cell of 378 is outside the tolerance: SMD 0.2, 100/100, k 5: % power, tau 0.5, RoM, 21 in the paper against 23.34 (tolerance 2.26). It is Monte Carlo error. Our second run, with other seeds, gives 22.29, within tolerance, and MD and SMD of the same row sit as far from the paper's 21 as RoM does: one draw of 10,000 meta-analyses moves all three. The table's RMS z is 0.97. |
| Table 4, normal data, SD 10% of the control mean, equal arms (18 rows x 21 cells) | agrees | 378 of 378 fields as printed | Assumed: % bias of RoM is 100 x (mean of the 10,000 back-transformed pooled RoMs - true RoM) / true RoM, the same definition as for MD and SMD. The paper says only 'a percentage of the true parameter value'; I2 (%) is 100 x (1 - 1/m), with m the mean of Q/(k - 1) over the 10,000 replicates (the Table legends speak of 'the ratio of Q/(k-1)'). The paper does not say how I2 was summarized over replicates |
| Table 5, normal data, SD 70% of the control mean, equal arms (18 rows x 21 cells) | agrees | 378 of 378 fields as printed | Assumed: % bias of RoM is 100 x (mean of the 10,000 back-transformed pooled RoMs - true RoM) / true RoM, the same definition as for MD and SMD. The paper says only 'a percentage of the true parameter value'; I2 (%) is 100 x (1 - 1/m), with m the mean of Q/(k - 1) over the 10,000 replicates (the Table legends speak of 'the ratio of Q/(k-1)'). The paper does not say how I2 was summarized over replicates |
| Table 6, skewed data, SD 40% of the control mean, equal arms (18 rows x 21 cells) | partly | 377 of 378 fields as printed | One cell of 378 is outside the tolerance: SMD 0.8, 100/100, k 30: I2 (%), tau 0.5, SMD, 91 in the paper against 91.60 (tolerance 0.59, a Monte Carlo SE of only 0.02). The paper prints 92 for the same column at k 5 and 10, where ours is also 91.6: the cell sits on the rounding boundary. Our second run gives 91.54, within tolerance; so does the mixture rescaled to SD 40 exactly. |
| Table 7, normal data, SD 40%, 2:1 experimental to control (14/6 and 134/66; 18 rows x 21 cells) | agrees | 378 of 378 fields as printed | Assumed: % bias of RoM is 100 x (mean of the 10,000 back-transformed pooled RoMs - true RoM) / true RoM, the same definition as for MD and SMD. The paper says only 'a percentage of the true parameter value'; I2 (%) is 100 x (1 - 1/m), with m the mean of Q/(k - 1) over the 10,000 replicates (the Table legends speak of 'the ratio of Q/(k-1)'). The paper does not say how I2 was summarized over replicates |
| Table 8, normal data, SD 40%, 1:2 experimental to control (6/14 and 66/134; 18 rows x 21 cells) | agrees | 378 of 378 fields as printed | Assumed: % bias of RoM is 100 x (mean of the 10,000 back-transformed pooled RoMs - true RoM) / true RoM, the same definition as for MD and SMD. The paper says only 'a percentage of the true parameter value'; I2 (%) is 100 x (1 - 1/m), with m the mean of Q/(k - 1) over the 10,000 replicates (the Table legends speak of 'the ratio of Q/(k-1)'). The paper does not say how I2 was summarized over replicates |
| SMD bias towards no effect: about 5% with 10 patients per arm (Abstract), -4 to -6% in Table 3, smaller with 100 (Results) | agrees | 4 of 4 fields as printed | Assumed: % bias of RoM is 100 x (mean of the 10,000 back-transformed pooled RoMs - true RoM) / true RoM, the same definition as for MD and SMD. The paper says only 'a percentage of the true parameter value'; I2 (%) is 100 x (1 - 1/m), with m the mean of Q/(k - 1) over the 10,000 replicates (the Table legends speak of 'the ratio of Q/(k-1)'). The paper does not say how I2 was summarized over replicates |
| RoM bias -4% to 2% with SD 70% and effects 0.5-0.8 (Abstract); up to 2-3% towards unity at n 10 and 1-2% away from it with heterogeneity at n 100; its sign with unequal arms (Results) | agrees | 7 of 7 fields as printed | Assumed: % bias of RoM is 100 x (mean of the 10,000 back-transformed pooled RoMs - true RoM) / true RoM, the same definition as for MD and SMD. The paper says only 'a percentage of the true parameter value'; I2 (%) is 100 x (1 - 1/m), with m the mean of Q/(k - 1) over the 10,000 replicates (the Table legends speak of 'the ratio of Q/(k-1)'). The paper does not say how I2 was summarized over replicates |
| Where RoM bias towards no effect exceeds 1.5%, RoM covers 89-92% and MD 92-94% (Abstract) | agrees | 3 of 3 fields as printed, 1 paper errors | Assumed: % bias of RoM is 100 x (mean of the 10,000 back-transformed pooled RoMs - true RoM) / true RoM, the same definition as for MD and SMD. The paper says only 'a percentage of the true parameter value'; I2 (%) is 100 x (1 - 1/m), with m the mean of Q/(k - 1) over the 10,000 replicates (the Table legends speak of 'the ratio of Q/(k-1)'). The paper does not say how I2 was summarized over replicates |
| Lowest coverage 87-88%, for all three methods, with 5 trials of 100 patients per arm and heterogeneity (I2 92-93%) (Results) | agrees | 5 of 5 fields as printed, 1 paper errors | Assumed: % bias of RoM is 100 x (mean of the 10,000 back-transformed pooled RoMs - true RoM) / true RoM, the same definition as for MD and SMD. The paper says only 'a percentage of the true parameter value'; I2 (%) is 100 x (1 - 1/m), with m the mean of Q/(k - 1) over the 10,000 replicates (the Table legends speak of 'the ratio of Q/(k-1)'). The paper does not say how I2 was summarized over replicates |
| 1,000 patients per arm: coverage still 87-88% and I2 99% (Results, 'results not shown') | agrees | 4 of 4 fields as printed | Assumed: % bias of RoM is 100 x (mean of the 10,000 back-transformed pooled RoMs - true RoM) / true RoM, the same definition as for MD and SMD. The paper says only 'a percentage of the true parameter value'; I2 (%) is 100 x (1 - 1/m), with m the mean of Q/(k - 1) over the 10,000 replicates (the Table legends speak of 'the ratio of Q/(k-1)'). The paper does not say how I2 was summarized over replicates |
| I2 around 55-60% with 10 patients per arm and above 90% with 100; lower for SMD and RoM where they are biased (Results) | partly | 3 of 4 fields as printed | Two Table 6 cells cross the 61% line: our MD I2 at 10/10, k 30 is 61.55, 61.70, 61.39 (effects 0.2, 0.5, 0.8), against 61 printed; each is within its cell's tolerance. The second run gives 61.49, 61.54, 61.72. With the mixture rescaled to SD 40 exactly (an unstated setting of the skewed data) they are 61.28, 61.43, 61.12, and the statement holds. Every other MD I2 at 10 patients per arm is within 54 to 61%. |
| Power within 5 percentage points across the methods in almost all scenarios; lower with unequal arms (Results) | agrees | 3 of 3 fields as printed | Assumed: % bias of RoM is 100 x (mean of the 10,000 back-transformed pooled RoMs - true RoM) / true RoM, the same definition as for MD and SMD. The paper says only 'a percentage of the true parameter value'; I2 (%) is 100 x (1 - 1/m), with m the mean of Q/(k - 1) over the 10,000 replicates (the Table legends speak of 'the ratio of Q/(k-1)'). The paper does not say how I2 was summarized over replicates |
| Methods: expected I2 56% (n 10) and 93% (n 100); second-order delta terms below 2.5%; the skewed mixture's mean, SD and skewness 0.88 | exact | 6 of 6 fields as printed |  |
| Main claim: MD bias-free, SMD biased towards no effect in small trials, RoM bias within -4 to 2%, similar power (Abstract and Conclusion) | agrees | 4 of 4 fields as printed | Assumed: % bias of RoM is 100 x (mean of the 10,000 back-transformed pooled RoMs - true RoM) / true RoM, the same definition as for MD and SMD. The paper says only 'a percentage of the true parameter value'; I2 (%) is 100 x (1 - 1/m), with m the mean of Q/(k - 1) over the 10,000 replicates (the Table legends speak of 'the ratio of Q/(k-1)'). The paper does not say how I2 was summarized over replicates |
| Claims recomputed from the paper's own tables | agrees | 34 of 38 statements follow from the paper's own tables. Not: text_coverage: k 5, 100/100, tau 0.5 (Tables 3-6): lowest I2 (%) [Results: I2 = 92-93%] (92 against 91.0); text_biased_rom_coverage: Scenarios with RoM bias towards no effect over 1.5% (Tables 3-8): highest RoM coverage (%) [Abstract: 89-92%] (92 against 95.0); text_biased_rom_coverage: Scenarios with RoM bias towards no effect over 1.5% (Tables 3-8): lowest MD coverage (%) [Abstract: 92-94%] (92 against 90.0); text_biased_rom_coverage: Scenarios with RoM bias towards no effect over 1.5% (Tables 3-8): highest MD coverage (%) [Abstract: 92-94%] (94 against 95.0). |  |
| rommeta's effect sizes and pooling against R's metafor (an independent implementation) | agrees | rommeta.pool against metafor 4.4.0 rma (DL) on 900 simulated meta-analyses (100 each of 3 scenarios x MD, SMD, RoM): pooled estimate, SE, tau2, Q and I2 agree to a relative 5.2e-14; both leave out the same 2 RoM studies with a non-positive mean |  |
| The authors' SAS 8.2 programs | not attempted | not attempted | The simulations were programmed in SAS 8.2 and no code was released or found (issue #73 lists the search). The method was rebuilt from the text as rommeta and checked against the paper's tables, and its pooling against R's metafor. |
| Python package rommeta and its tutorial | agrees | rommeta 0.1.0: wheel installed in a fresh environment and imported from it; tests 11 passed; tutorial 6 cells compared, 0 skipped (nondeterministic); TUTORIAL.md in sync |  |
<!--/RESULTS-TABLE-->

<!--CLAIMS-LINE-->
The main claim holds. The one claim that misses on our run sits on a rounding line in Table 6 (a setting of the skewed data the paper does not state); three statements of the text do not match the paper's own tables.
<!--/CLAIMS-LINE-->

## What the code does, against the paper

| Paper | Here |
| --- | --- |
| RoM = mean_exp/mean_contr; Var[ln RoM] = (1/n_exp)(sd_exp/mean_exp)² + (1/n_contr)(sd_contr/mean_contr)² (Methods, first-order delta method) | `rommeta.effect_sizes(..., "RoM")`: as printed. A study with a non-positive mean has no ln RoM and is left out of its meta-analysis (only Table 5 has any; the paper does not say). |
| MD and its variance (Appendix) | As printed. |
| SMD = (mean_exp - mean_contr)/sd_pool x [1 - 3/(4N - 9)], Var = N/(n_exp n_contr) + SMD²/(2(N - 3.94)) (Appendix) | As printed, with the standard pooled SD; the Appendix's formula has a stray "- 1" under the root, which changes no cell of Table 4 (`sd_pool_literal` in `output/comparison.json`). |
| Inverse-variance random effects; Q; DerSimonian-Laird tau² (Appendix); 95% CI = estimate ± 1.96 SE, on ln RoM for RoM (Methods) | `rommeta.pool`: as printed, vectorized over the 10,000 replicates. Checked against R's metafor 4.4.0 `rma(method = "DL")` on 900 simulated meta-analyses (`CROSSCHECK`). |
| k trials, each arm's mean and SD from n values of a normal distribution with mean 100 (control) or 100 + effect x SD (experimental), SD 10, 40 or 70 | `rommeta.draw_trials`: each arm's mean and SD drawn from their sampling distributions (normal mean, scaled chi-squared variance), the same in distribution; drawing every patient (`draw_values`) gives the same tables. |
| Heterogeneity: "an additional study-specific SD equal to 0.5/√2 SD units to both the experimental and the control groups" | Independent normal shifts of each arm's mean, SD 0.5/√2 x SD. |
| Skewed data: three normals, SD 0.24, centred at 0.84, 1.42, 1.92, weighted 77%, 17%, 6% | The mixture times 100; the experimental arm shifted by effect x 40. |
| Bias "as a percentage of the true parameter value"; coverage; power "by excluding zero for MD and SMD or one for RoM"; I2 | Bias: (mean of the 10,000 pooled estimates - true)/true, RoM on the ratio scale. Coverage and power from the 95% CIs. I2: 100 x (1 - 1/mean(Q/(k - 1))). |
| 10,000 replicates per scenario; SAS 8.2, seeds not given | 10,000 replicates; NumPy 2.2.6 PCG64, one stream per scenario (seed [20080521, table, row, tau]), so a scenario gives the same numbers whatever else runs. A second run (base 20080522) measures how far two runs of one design stray. |
| 1,000 patients per arm: coverage 87-88%, I2 99% ("results not shown") | SD 40, k 5, tau 0.5, effects 0.2, 0.5, 0.8 at 1000/1000 (`extra` in `output/simulation.json`). |
| Table 1: pooled results of the 2005 dopamine meta-analysis | Not recomputed (the trial data are not in this paper). Each estimate against the centre of its CI, and each p against its CI. |

## Comparing Monte Carlo tables

No printed cell can come back exactly: the paper's seeds and random-number generator are not given. Each cell is
compared at a tolerance fixed before the comparison: half a unit of the last printed digit plus 3 x √2 standard
errors of one 10,000-replicate estimate (ours stands in for the paper's): the SD of the pooled estimates over √10,000
for bias (as a percentage of the true value), √(p(1 - p)/10,000) for coverage and power with p the mean of ours and
the paper's, and the delta-method error of 100(1 - 1/mean(Q/(k - 1))) for I2. A claim of the text that cites one
cell (a range end) is compared at that cell's tolerance.

How good is that test? Our second run, printed as the paper would, falls within the tolerance of our main run in
every cell (`replicate` in `output/comparison.json`). Our run of a wrong design (another SD, the arms swapped,
normal data for skewed) leaves a much smaller share of a table's RoM cells within tolerance than the right design
does (`controls`). MD and SMD do not depend on the SD at all, which is why Tables 3, 4 and 5 print the same MD and
SMD columns: those columns confirm the pooling, the design and the definitions of coverage, power and I2, while the
RoM columns tell the designs apart. The RMS z-score of each table (`rms_z`), with the rounding of the printed value
in the error, is near 1 for every table.

The unstated settings were found by scoring alternatives on the same seeds (`hypotheses` in `output/comparison.json`):
the scale of RoM bias, the summary of I2 over replicates, the heterogeneity model, the scaling of the skewed data,
the handling of non-positive means, the pooled SD and the SMD's small-sample factor. Each is an assumption of
`results.json` with its sensitivity.

## Layout

| Path | Content |
| --- | --- |
| `main.nf`, `nextflow.config` | The pipeline. |
| `requirements.txt` | Pinned Python packages; the package `rommeta` is installed from `../package`. |
| `results_notes.json` | Labels, assumptions, causes and the page's prose, written by hand; merged with the run into `../results.json`. Numbers in the prose are filled from the run. |
| `results.json` | The repository's results check (`tools/check_results.py`): our value for every compared cell and claim. |
| `reference/metafor_replicates.csv` | R metafor 4.4.0's pooled results for the 900 simulated meta-analyses of `CROSSCHECK` (`--metafor` reruns R and checks it gives this file). |
| `pipeline/` | `fetch_inputs.sh`, `extract_published.py`, `simulate.py`, `compare.py`, `claims.py`, `crosscheck.py` with `metafor_replicates.R`, `build_results.py`, `make_results_check.py`, `build_page.py` with `page_template.html`, `check_reproduction.py`, `update_readmes.py`, `env_versions.py`; copies of the skill's `check_results.py`, `compare_runs.py` and `check_package.py`. |
| `output/published_values.json` | Every printed number of Tables 1-8. |
| `output/simulation.json` | Every scenario's measures: the main run, a second run, the hypothesis variants and the 1,000-per-arm scenarios. |
| `output/comparison.json`, `output/tables.csv` | Every printed cell against ours, with tolerances, the second run, the controls and the hypotheses; the same cells as one CSV. |
| `output/claims.json`, `output/crosscheck.json`, `output/package.json` | Every claim of the text against the paper's own tables and our run; the check against metafor; the package check. |

## Run

```bash
pip install -r PMC2430201/figure-reproduction/requirements.txt ./PMC2430201/package
nextflow run PMC2430201/figure-reproduction/main.nf --outdir results
nextflow run PMC2430201/figure-reproduction/main.nf --outdir results --extract              # also reread the printed tables from the XML
nextflow run PMC2430201/figure-reproduction/main.nf --outdir results --metafor --rscript Rscript   # also rerun R's metafor
```

The whole run takes about 3 minutes on 4 cores here, the simulation study (about 2 minutes) and the package check
(about 10 seconds, a fresh environment) included. `.github/workflows/reproduce-pmc2430201.yml` runs it on every pull
request that touches this paper.

## Pipeline steps

1. `FETCH`: the article XML from PMC's open-access bucket (Europe PMC as a fallback), SHA-256 checked.
2. `PUBLISHED_VALUES`: the committed printed values, or with `--extract` read again from the XML and checked against them.
3. `SIMULATE`: the 216 scenarios x 10,000 meta-analyses, a second run, the hypothesis variants, the 1,000-per-arm scenarios.
4. `COMPARE`: every printed cell against ours, the controls and the hypotheses.
5. `CLAIMS`: every claim of the text against the paper's own tables and our run; Table 1 against itself.
6. `CROSSCHECK`: rommeta's pooling against metafor's committed results (with `--metafor`, metafor rerun).
7. `PACKAGE`: `check_package.py` on `../package` (wheel, fresh install, tests, tutorial rerun).
8. `RESULTS`: `results.json` (verdicts by `check_results.py`), the repository's results check, the results page, and `check_reproduction.py` against the committed outputs (`report.md`); `CHECK` fails the run if anything differs.

## Limits

- **The SAS code is lost.** The method is rebuilt from the paper's text and checked against its tables and text only (`port` is not attempted); the pooling is checked against R's metafor, an independent implementation.
- **Two definitions were found from the tables**, not read from the paper: the scale of RoM bias and how I2 is summarized over replicates (`found_by_search` in `results.json`). Every simulated item carries them, so none can be "exact".
- **Skewed data.** Our reading and the mixture rescaled to SD 40 exactly cannot be told apart; they move Table 6's I2 by about 0.3 points, which decides one line of the text.
- **Monte Carlo error.** Every simulated cell carries it; our run has one chance miss in each of Tables 3 and 6, and the second run puts each back.
- **Table 1** cannot be recomputed: the trial data of the 2005 meta-analysis are not in this paper and not open access.
