# PMC3022898 figure reproduction

Reichmann WM, Gagnon D, Horsburgh CR, Losina E. Evaluation of exposure-specific risks from two independent
samples: a simulation study. *BMC Medical Research Methodology* 11:1 (2011).
[doi:10.1186/1471-2288-11-1](https://doi.org/10.1186/1471-2288-11-1). CC BY 2.0.

The published figures in `published/` are the paper's (CC BY 2.0, attribution above), the JPEGs PMC serves.
Nothing else of the paper is in this folder: the pipeline downloads the figures, the article XML and
Additional file 1 and checks their SHA-256. `output/published_values.json` holds the printed numbers of
Tables 2-5 and S1-S7, read from those files by `pipeline/extract_published.py`.

## Results

<!-- full table from results.json (check_results.py --markdown); regenerate with pipeline/update_readmes.py -->

<!--RESULTS-TABLE-->
11 agrees, 22 partly, 1 differs, 2 not attempted; 0 open causes.

| Item | Verdict | Measure | Why |
| --- | --- | --- | --- |
| Table 1, the parameter grid | not attempted | not attempted | The design of the simulation (P(E), P(D|not E), RR, N1/N2); used as input, nothing to compare. |
| Table 2, relative bias of ESR_S and ESR_R (1000/1000 and 5000/5000) | partly | 78 of 80 fields as printed | Monte Carlo error: the paper's seeds are not given, and two runs of our own design differ by more than the tolerance in 8 of 784 cells (1.0%). Our second run, with another seed, puts each of these cells within tolerance. |
| Table 3, coverage of the log CIs of ESR_S and ESR_R (1000/1000 and 5000/5000) | partly | 77 of 80 fields as printed | The paper's log CI of ESR_R behaves as if the first term of eq. 10, the variance of ln P1(D|not E), had been left out of the simulation (or computed as p(1-p)/n1, the variance of the proportion rather than of its log, which is close to 0). With eq. 10 as printed, our intervals cover more often, most of all at N1/N2 1000/5000 where that term is largest; without it, 112 of 112 cells of Table S6 (against 82 with it) and 47 of 47 bars of Figs 1-4 come back. The case study (Table 5) used eq. 10 as printed. The SAS code is lost, so this is read from the results. |
| Table 4, coverage of the binomial CI of ESR_R (four N1/N2, seven RRs) | partly | 111 of 112 fields as printed | Monte Carlo error: the paper's seeds are not given, and two runs of our own design differ by more than the tolerance in 8 of 784 cells (1.0%). Our second run, with another seed, puts each of these cells within tolerance. |
| Table S1, relative bias of ESR_S | partly | 111 of 112 fields as printed | Monte Carlo error: the paper's seeds are not given, and two runs of our own design differ by more than the tolerance in 8 of 784 cells (1.0%). Our second run, with another seed, puts each of these cells within tolerance. |
| Table S2, relative bias of ESR_R | partly | 111 of 112 fields as printed | Monte Carlo error: the paper's seeds are not given, and two runs of our own design differ by more than the tolerance in 8 of 784 cells (1.0%). Our second run, with another seed, puts each of these cells within tolerance. |
| Table S3, absolute bias of ESR_S | agrees | 112 of 112 fields as printed | Assumed: The 'assumed population ESR' is RR x P(D|not E) unrounded (0.135 for the label .14), not the rounded label of the tables; When sample 2 has no cases among its exposed (or its unexposed), the log interval is (0, infinity): it covers, and it has no finite length, so it is left out of the expected length. The paper does not say. |
| Table S4, absolute bias of ESR_R | partly | 111 of 112 fields as printed | Monte Carlo error: the paper's seeds are not given, and two runs of our own design differ by more than the tolerance in 8 of 784 cells (1.0%). Our second run, with another seed, puts each of these cells within tolerance. |
| Table S5, coverage of the log CI of ESR_S | partly | 111 of 112 fields as printed | Monte Carlo error: the paper's seeds are not given, and two runs of our own design differ by more than the tolerance in 8 of 784 cells (1.0%). Our second run, with another seed, puts each of these cells within tolerance. |
| Table S6, coverage of the log CI of ESR_R | partly | 82 of 112 fields as printed | The paper's log CI of ESR_R behaves as if the first term of eq. 10, the variance of ln P1(D|not E), had been left out of the simulation (or computed as p(1-p)/n1, the variance of the proportion rather than of its log, which is close to 0). With eq. 10 as printed, our intervals cover more often, most of all at N1/N2 1000/5000 where that term is largest; without it, 112 of 112 cells of Table S6 (against 82 with it) and 47 of 47 bars of Figs 1-4 come back. The case study (Table 5) used eq. 10 as printed. The SAS code is lost, so this is read from the results. |
| Table S7, coverage of the binomial CI of ESR_R | partly | 111 of 112 fields as printed | Monte Carlo error: the paper's seeds are not given, and two runs of our own design differ by more than the tolerance in 8 of 784 cells (1.0%). Our second run, with another seed, puts each of these cells within tolerance. |
| Fig. 1, expected length given coverage, Scenario 1 (drawn) | partly | 75.00% within 2 px (pass 90.0%, best control 58.3%) | The paper's log CI of ESR_R behaves as if the first term of eq. 10, the variance of ln P1(D|not E), had been left out of the simulation (or computed as p(1-p)/n1, the variance of the proportion rather than of its log, which is close to 0). With eq. 10 as printed, our intervals cover more often, most of all at N1/N2 1000/5000 where that term is largest; without it, 112 of 112 cells of Table S6 (against 82 with it) and 47 of 47 bars of Figs 1-4 come back. The case study (Table 5) used eq. 10 as printed. The SAS code is lost, so this is read from the results. |
| Fig. 2, expected length given coverage, Scenario 2 (drawn) | partly | 75.00% within 2 px (pass 90.0%, best control 50.0%) | The paper's log CI of ESR_R behaves as if the first term of eq. 10, the variance of ln P1(D|not E), had been left out of the simulation (or computed as p(1-p)/n1, the variance of the proportion rather than of its log, which is close to 0). With eq. 10 as printed, our intervals cover more often, most of all at N1/N2 1000/5000 where that term is largest; without it, 112 of 112 cells of Table S6 (against 82 with it) and 47 of 47 bars of Figs 1-4 come back. The case study (Table 5) used eq. 10 as printed. The SAS code is lost, so this is read from the results. |
| Fig. 3, expected length given coverage, Scenario 3 (drawn) | partly | 66.67% within 2 px (pass 90.0%, best control 58.3%) | The paper's log CI of ESR_R behaves as if the first term of eq. 10, the variance of ln P1(D|not E), had been left out of the simulation (or computed as p(1-p)/n1, the variance of the proportion rather than of its log, which is close to 0). With eq. 10 as printed, our intervals cover more often, most of all at N1/N2 1000/5000 where that term is largest; without it, 112 of 112 cells of Table S6 (against 82 with it) and 47 of 47 bars of Figs 1-4 come back. The case study (Table 5) used eq. 10 as printed. The SAS code is lost, so this is read from the results. |
| Fig. 4, expected length given coverage, Scenario 4 (drawn) | partly | 54.55% within 2 px (pass 90.0%, best control 45.5%) | The paper's log CI of ESR_R behaves as if the first term of eq. 10, the variance of ln P1(D|not E), had been left out of the simulation (or computed as p(1-p)/n1, the variance of the proportion rather than of its log, which is close to 0). With eq. 10 as printed, our intervals cover more often, most of all at N1/N2 1000/5000 where that term is largest; without it, 112 of 112 cells of Table S6 (against 82 with it) and 47 of 47 bars of Figs 1-4 come back. The case study (Table 5) used eq. 10 as printed. The SAS code is lost, so this is read from the results. |
| Fig. 1, the 12 bar heights | partly | 10 of 12 fields as printed | The paper's log CI of ESR_R behaves as if the first term of eq. 10, the variance of ln P1(D|not E), had been left out of the simulation (or computed as p(1-p)/n1, the variance of the proportion rather than of its log, which is close to 0). With eq. 10 as printed, our intervals cover more often, most of all at N1/N2 1000/5000 where that term is largest; without it, 112 of 112 cells of Table S6 (against 82 with it) and 47 of 47 bars of Figs 1-4 come back. The case study (Table 5) used eq. 10 as printed. The SAS code is lost, so this is read from the results. |
| Fig. 2, the 12 bar heights | partly | 9 of 12 fields as printed | The paper's log CI of ESR_R behaves as if the first term of eq. 10, the variance of ln P1(D|not E), had been left out of the simulation (or computed as p(1-p)/n1, the variance of the proportion rather than of its log, which is close to 0). With eq. 10 as printed, our intervals cover more often, most of all at N1/N2 1000/5000 where that term is largest; without it, 112 of 112 cells of Table S6 (against 82 with it) and 47 of 47 bars of Figs 1-4 come back. The case study (Table 5) used eq. 10 as printed. The SAS code is lost, so this is read from the results. |
| Fig. 3, the 12 bar heights | partly | 9 of 12 fields as printed | The paper's log CI of ESR_R behaves as if the first term of eq. 10, the variance of ln P1(D|not E), had been left out of the simulation (or computed as p(1-p)/n1, the variance of the proportion rather than of its log, which is close to 0). With eq. 10 as printed, our intervals cover more often, most of all at N1/N2 1000/5000 where that term is largest; without it, 112 of 112 cells of Table S6 (against 82 with it) and 47 of 47 bars of Figs 1-4 come back. The case study (Table 5) used eq. 10 as printed. The SAS code is lost, so this is read from the results. |
| Fig. 4, the 11 bar heights (no ESR_S bar at RR 5.0: coverage 0) | partly | 8 of 11 fields as printed | The paper's log CI of ESR_R behaves as if the first term of eq. 10, the variance of ln P1(D|not E), had been left out of the simulation (or computed as p(1-p)/n1, the variance of the proportion rather than of its log, which is close to 0). With eq. 10 as printed, our intervals cover more often, most of all at N1/N2 1000/5000 where that term is largest; without it, 112 of 112 cells of Table S6 (against 82 with it) and 47 of 47 bars of Figs 1-4 come back. The case study (Table 5) used eq. 10 as printed. The SAS code is lost, so this is read from the results. |
| Table 5, ESR_S and ESR_R of the case study from the printed inputs | partly | 2 of 6 fields as printed | The case study's inputs are printed rounded (overall risk to 4 decimals, RR 1.91). From the printed inputs, ESR_S and ESR_R at ages 60-69 and 70-79 come out one unit low in the last digit (0.0166 against 0.0167, 0.0124 against 0.0125, 0.0281 against 0.0282, 0.0210 against 0.0211). An overall risk in [0.008719, 0.008750) and [0.014742, 0.014750), both of which round to the printed 0.0087 and 0.0147, gives every printed value. |
| Table 5, log CI of ESR_R predicted from the other two CIs | partly | 5 of 6 fields as printed | 5 of 6 bounds come back as printed; the 70-79 upper bound is 0.0290 against 0.0289. Rounding of the printed inputs and CIs alone spans 0.0289 to 0.0291 for it. |
| Abstract: largest relative bias 4.0% for ESR_R and 93.9% for ESR_S | agrees | 2 of 2 fields as printed | Assumed: The 'assumed population ESR' is RR x P(D|not E) unrounded (0.135 for the label .14), not the rounded label of the tables; When sample 2 has no cases among its exposed (or its unexposed), the log interval is (0, infinity): it covers, and it has no finite length, so it is left out of the expected length. The paper does not say. |
| Main claim: ESR_R has little bias, ESR_S a large one, and the log CI of ESR_R covers better in most settings | agrees | 3 of 3 fields as printed | Assumed: The 'assumed population ESR' is RR x P(D|not E) unrounded (0.135 for the label .14), not the rounded label of the tables; When sample 2 has no cases among its exposed (or its unexposed), the log interval is (0, infinity): it covers, and it has no finite length, so it is left out of the expected length. The paper does not say. |
| Scenario 1: the CI of ESR_S covers at least 95% when RR is 2.0 or less | differs | 0 of 1 fields as printed | One of the 12 cells of our run is at 94.4% (1000/5000, RR 2.0; the paper 96.0%). The paper's 12 cells are 95.4% to 97.5%, each within a point or two of the line; our second run has all 12 at 95% or more. |
| Scenarios 1-3: the log CI of ESR_R reaches 95% except at N1/N2 1000/5000, where it never does | partly | 3 of 6 fields as printed | The paper's log CI of ESR_R behaves as if the first term of eq. 10, the variance of ln P1(D|not E), had been left out of the simulation (or computed as p(1-p)/n1, the variance of the proportion rather than of its log, which is close to 0). With eq. 10 as printed, our intervals cover more often, most of all at N1/N2 1000/5000 where that term is largest; without it, 112 of 112 cells of Table S6 (against 82 with it) and 47 of 47 bars of Figs 1-4 come back. The case study (Table 5) used eq. 10 as printed. The SAS code is lost, so this is read from the results. |
| The binomial CI of ESR_R reaches 95% only at 1000/5000 (Scenario 1, smallest 98.9%), and is above 99% there in Scenarios 2 and 3 | agrees | 3 of 3 fields as printed, 1 paper errors | Assumed: The 'assumed population ESR' is RR x P(D|not E) unrounded (0.135 for the label .14), not the rounded label of the tables; When sample 2 has no cases among its exposed (or its unexposed), the log interval is (0, infinity): it covers, and it has no finite length, so it is left out of the expected length. The paper does not say. |
| Relative bias of ESR_S over 20% at RR 5.0 (Scenario 2) and over 10%, 20%, 80% at RR 1.5, 2.0, 5.0 (Scenario 3) | agrees | 4 of 4 fields as printed | Assumed: The 'assumed population ESR' is RR x P(D|not E) unrounded (0.135 for the label .14), not the rounded label of the tables; When sample 2 has no cases among its exposed (or its unexposed), the log interval is (0, infinity): it covers, and it has no finite length, so it is left out of the expected length. The paper does not say. |
| Scenario 3: the largest relative bias of ESR_R is -1.8% | agrees | 1 of 1 fields as printed | Assumed: The 'assumed population ESR' is RR x P(D|not E) unrounded (0.135 for the label .14), not the rounded label of the tables; When sample 2 has no cases among its exposed (or its unexposed), the log interval is (0, infinity): it covers, and it has no finite length, so it is left out of the expected length. The paper does not say. |
| Scenario 2: the CI of ESR_S is below 95% in most cases; with equal N1 and N2 the binomial CI of ESR_R covers 87% to 95% in most cases | agrees | 2 of 2 fields as printed | Assumed: The 'assumed population ESR' is RR x P(D|not E) unrounded (0.135 for the label .14), not the rounded label of the tables; When sample 2 has no cases among its exposed (or its unexposed), the log interval is (0, infinity): it covers, and it has no finite length, so it is left out of the expected length. The paper does not say. |
| Numbers of the Results and Discussion that restate a table cell | agrees | 8 of 8 fields as printed | Assumed: The 'assumed population ESR' is RR x P(D|not E) unrounded (0.135 for the label .14), not the rounded label of the tables; When sample 2 has no cases among its exposed (or its unexposed), the log interval is (0, infinity): it covers, and it has no finite length, so it is left out of the expected length. The paper does not say. |
| Scenario 4 at N1/N2 250/250 (given only in the text) | agrees | 12 of 12 fields as printed | Assumed: The 'assumed population ESR' is RR x P(D|not E) unrounded (0.135 for the label .14), not the rounded label of the tables; When sample 2 has no cases among its exposed (or its unexposed), the log interval is (0, infinity): it covers, and it has no finite length, so it is left out of the expected length. The paper does not say. |
| Figs 1-3 as the text reads them | partly | 5 of 6 fields as printed | With eq. 10 as printed, our log CI of ESR_R at RR 1.0 in Fig. 1 is as long as the CI of ESR_S (0.0413 against 0.0412); the paper's is shorter (0.0399 against 0.0416). Without eq. 10's first term the statement holds, and so it does on our second run (a near tie at RR 1.0). |
| Case study: ESR_R 0.57% to 2.11%, ESR_S higher, largest over-estimation 0.71% at ages 70-79 | partly | 4 of 5 fields as printed | The case study's inputs are printed rounded (overall risk to 4 decimals, RR 1.91). From the printed inputs, ESR_S and ESR_R at ages 60-69 and 70-79 come out one unit low in the last digit (0.0166 against 0.0167, 0.0124 against 0.0125, 0.0281 against 0.0282, 0.0210 against 0.0211). An overall risk in [0.008719, 0.008750) and [0.014742, 0.014750), both of which round to the printed 0.0087 and 0.0147, gives every printed value. |
| Claims recomputed from the paper's own tables and figures | agrees | 42 of 48 statements follow from the paper's own tables and figures. Not: text_binomial_ci_1000_5000: Scenario 3: above 99% for every RR at 1000/5000 (yes against no); text_discussion_self: case study overall risk ranges from (0.0087 against 0.0040); text_discussion_self: case study overall risk ranges to (0.0132 against 0.0147); text_discussion_self: the scenario with exposure .20 and disease in the unexposed .02 (scenario two against Scenario 3); text_discussion_self: equation of the log-based variance of ESR_R (11 against 10); text_discussion_self: equation of the binomial variance of ESR_R (12 against 11). Tables 2-4 restate Tables S1, S2, S5-S7 in every cell but 2: table2 S4|1000/1000|1.0|S -0.8 against S1 0.8; table3 S2|1000/1000|4.0|R 96.1 against S6 96.9 |  |
| The authors' SAS 9.2 programs | not attempted | not attempted | The paper ran in SAS 9.2 and released no code; none was found (issue #68 lists the search). The method was rebuilt from the text as esrisk and checked against the paper's tables and figures only. |
| Python package esrisk and its tutorial | agrees | esrisk 0.1.0: wheel installed in a fresh environment and imported from it; tests 8 passed; tutorial 7 cells compared, 0 skipped (nondeterministic); TUTORIAL.md in sync |  |
<!--/RESULTS-TABLE-->

The main claim holds: ESR_R removes the bias of ESR_S, and the binomial CI of ESR_R and the log CI of ESR_S
behave as reported. The claims that do not match come from eq. 10's first term (left out of the paper's
simulation), from cells near the 95% line (chance), or from the rounding of the case study's inputs.

## What the code does, against the paper

| Paper | Here |
| --- | --- |
| ESR_S = P1(D) x RR2 (eq. 2); log variance (eqs 3-5), CI exp(ln ESR_S ± 1.96 √Var) (eq. 6) | `esrisk.estimate`: as printed; z = 1.959964. |
| P1(D\|not E) = P1(D) / ((RR2 - 1) P2(E) + 1) (eq. 8); ESR_R = P1(D\|not E) x RR2 (eq. 9) | As printed; P2(E) is sample 2's exposed share. |
| Log variance of ESR_R (eq. 10): (1 - P1(D\|not E)) / (n1 P1(D\|not E)) + the two RR terms | As printed. The paper's simulation behaves as if the first term were left out (Table S6, Figs 1-4); its case study uses it as printed. Both are in `output/` (`eq10_*` variants). |
| Binomial variance of ESR_R (eq. 11): ESR_R (1 - ESR_R) / (n1 P2(E)); CI ESR_R ± 1.96 √Var (eq. 12) | As printed; no truncation at 0 (the paper does not say). Truncation cannot change a coverage (the true ESR is above 0) and moves Fig. 1's binomial bar at RR 1.0, where a third of the lower bounds are below 0, by 0.0003 (0.4 px): the figures cannot tell. |
| "Populations of size 10 million were generated based on" P(E), P(D\|not E) and RR | `esrisk.make_population`: one population per setting, exposure and disease by Bernoulli draws. Exact proportions instead give the same tables (`exact_population` in `output/comparison.json`). |
| "One thousand pairs of samples were drawn from the population" | `esrisk.draw_samples`: two independent samples of N1 and N2 per pair, each without replacement (multivariate hypergeometric on the population's four cells). |
| Observed relative bias against "the assumed population ESR" | (mean of the 1,000 estimates - RR x P(D\|not E)) / RR x P(D\|not E), unrounded. The rounded labels of the tables (.14 for 0.135, .23 for 0.225) miss many cells. |
| Coverage: "the number of times the interval covered divided by 1,000" | Intervals that cover the true ESR over the defined intervals. When sample 2 has no cases among the exposed (or the unexposed) the log variances are undefined; the interval is then (0, infinity) and covers. Up to 39% of pairs have this in Scenario 1 at N2 = 1,000. Leaving those pairs out, counting them as misses, or adding 0.5 to the cells all fit worse (`hypotheses` in `output/comparison.json`). |
| Expected length given coverage; empirical CI from the 2.5th and 97.5th percentiles "of the direct estimator" | Mean upper - lower over the covering intervals with a finite length; the empirical CI of ESR_R (that of ESR_S is 2 to 189 px longer than the published bars, and misses 9 of 12). Percentiles by NumPy's default (linear) rule. |
| SAS 9.2, seeds not given | NumPy 2.2.6 PCG64; one random stream per setting (seed 20110105, scenario, N1, N2, 10 x RR), so a setting gives the same numbers whatever else runs. A second run (seed 20110106) measures how often two runs of one design disagree. |
| Case study (Table 5): P1(D) by age from Oliveria et al. 1995, RR 1.91 and P(obese) 0.371 from Niu et al. 2009 | Point estimates from the printed inputs. The CIs need n1 by age and Var(ln RR2), which the paper does not print: n1 is solved from the binomial CI of ESR_R (14,632, 14,171 and 11,817), Var(ln RR2) from the log CI of ESR_S (0.0191; an RR CI of 1.46 to 2.50), and the log CI of ESR_R is then predicted, not fitted. |

## Comparing Monte Carlo tables

No printed cell can come back exactly: the paper's seeds and random-number generator are not given. Each cell
is compared at a tolerance fixed before the comparison: half a unit of the last printed digit plus 3 x √2
standard errors of one 1,000-pair estimate (ours stands in for the paper's): sd/√1000 of the estimates for
bias, √(p(1-p)/n) for coverage with p the mean of ours and the paper's, the sd of the covering lengths over
√(their number) for expected lengths, and a bootstrap standard error for the empirical CI length. Figure bars
also get one pixel of the published figure (0.00075).

How good is that test? Two runs of our own design differ by more than the tolerance in about one cell in a
hundred (`replicate` in `output/comparison.json`). Wrong inputs, our values for the neighbouring scenario or with
N1 and N2 swapped, fall outside it in 21% to 81% of the cells of Tables S1, S3, S5, S6 and S7 (`controls`). In
Tables S2 and S4, the bias of ESR_R, the true value is 0 in every setting and a wrong input does almost as
well as the right one: those tables confirm that ESR_R is unbiased, not that our simulation is the paper's.
The RMS z-score of each table (`rms_z`), near 1 for every table but S6, is reported as a diagnostic.

The figures are scored twice. `fig*.bars`: each bar's height, read off the JPEG through the y tick labels,
against ours at the tolerance above. `fig*`: our bars drawn into the published frame (the published bars
removed, ours drawn with the published columns, fills and border), and the share of bar-top pixels within
2 px, both ways, against wrong inputs (the neighbouring scenario, N1/N2 1000/1000) and near misses (every bar
x 1.05 and x 0.95; the empirical CI of ESR_S), with a pass mark of 90%, above every control. The renders without
eq. 10's first term (`fig*_ours_eq10_no_first_term.png`) are a hypothesis test, not our result.

## Layout

| Path | Content |
| --- | --- |
| `main.nf`, `nextflow.config` | The pipeline. |
| `requirements.txt` | Pinned Python packages; the package `esrisk` is installed from `../package`. |
| `results_notes.json` | Labels, assumptions, causes and the page's prose, written by hand; merged with the run into `../results.json`. Numbers in the prose are filled from the run. |
| `results.json` | The repository's results check (`tools/check_results.py`): our value for every compared cell, bar, score and claim (1,175 entries). |
| `pipeline/` | `fetch_inputs.sh`, `extract_published.py`, `read_published.py`, `simulate.py`, `compare.py`, `figures.py`, `table5.py`, `claims.py`, `build_results.py`, `make_results_check.py`, `build_page.py` with `page_template.html`, `check_reproduction.py`, `update_readmes.py`, `env_versions.py`; copies of the skill's `check_results.py`, `compare_runs.py` and `check_package.py`. |
| `published/` | The paper's four figures (CC BY 2.0). |
| `output/published_values.json` | Every printed number of Tables 2-5 and S1-S7. |
| `output/figure_values.json` | The 47 bar heights read off Figs 1-4, with the axis calibration. |
| `output/simulation.json` | Every setting's measures: the main run, the hypothesis variants on the same samples, a second run and an exact-population run. |
| `output/comparison.json` | Every cell and bar against the paper, with tolerances, z-scores, controls and hypotheses. |
| `output/fig*_ours.png`, `fig*_overlay.png`, `figures.json` | Our bars in the published frames; overlays (red channel the paper, green and blue ours: black is both, cyan the paper only, red ours only); scores and controls. |
| `output/table5.json`, `claims.json`, `package.json` | The case study; every claim of the text against the paper's own tables and our run; the package check. |

## Run

```bash
pip install -r PMC3022898/figure-reproduction/requirements.txt ./PMC3022898/package
nextflow run PMC3022898/figure-reproduction/main.nf --outdir results
nextflow run PMC3022898/figure-reproduction/main.nf --outdir results --extract    # also reread the printed tables (LibreOffice)
```

The whole run takes about 15 seconds here, the simulation (2 seconds) and the package check (about 8 seconds,
a fresh environment) included. `.github/workflows/reproduce-pmc3022898.yml` runs it on every pull request that touches this paper.

## Pipeline steps

1. `FETCH`: the four figure JPEGs, the article XML and Additional file 1 from PMC's open-access bucket (Europe PMC as a fallback), SHA-256 checked.
2. `PUBLISHED_VALUES`: the committed printed values, or with `--extract` read again from the XML and the DOC.
3. `READ_FIGURES`: the 47 bar heights of Figs 1-4.
4. `SIMULATE`: the 119 settings x 1,000 pairs of samples, the hypothesis variants on the same samples, a second run, an exact-population run.
5. `COMPARE`: every printed cell and bar against ours, the controls and the hypotheses.
6. `FIGURES`: our bars in the published frames, overlays, pixel scores and controls.
7. `TABLE5`, `CLAIMS`: the case study, and every claim against the paper's own tables and our run.
8. `PACKAGE`: `check_package.py` on `../package` (wheel, fresh install, tests, tutorial rerun).
9. `RESULTS`: `results.json` (verdicts by `check_results.py`), the repository's results check, the results page, and `check_reproduction.py` against the committed outputs (`report.md`); `CHECK` fails the run if anything differs.

## Limits

- **The SAS code is lost.** The method is rebuilt from the paper's text and checked against its tables and figures only (`port` is not attempted).
- **Eq. 10.** The reading that the simulation left out its first term rests on Table S6 and the figures; the two variants that fit (term left out, or the variance of the proportion in place of that of its log) cannot be told apart, as both make the term about 0.
- **Monte Carlo error.** Every simulated cell carries it; the tolerance lets two runs of the same design disagree in about one cell in a hundred, and our run has one such miss in each of Tables 2, 4, S1, S2, S4, S5 and S7 (one setting, Scenario 2 at 1000/1000 and RR 3.0, accounts for four of them). The second run puts each back within tolerance.
- **Zero cells and the true ESR** are settings we chose by comparing with the paper's tables (`found_by_search` in `results.json`); every simulated item carries them as assumptions, so none can be "exact".
- **Figures.** The JPEGs are 600 x 464 px; one pixel is 0.00075 on the y axis. The empirical CI is a difference of two percentiles of 1,000 values, and its bars move by a few pixels between runs.
- **Table 5's CIs** rest on sample sizes solved from the paper's own intervals; only the log CI of ESR_R is a prediction.
