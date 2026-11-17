# PMC3022898: Evaluation of exposure-specific risks from two independent samples (Reichmann et al. 2011)

Reichmann WM, Gagnon D, Horsburgh CR, Losina E. Evaluation of exposure-specific risks from two independent
samples: a simulation study. *BMC Medical Research Methodology* 11:1 (2011).
[doi:10.1186/1471-2288-11-1](https://doi.org/10.1186/1471-2288-11-1) ·
[PMC3022898](https://pmc.ncbi.nlm.nih.gov/articles/PMC3022898/) · issue #68

The paper is © 2011 Reichmann et al., licensee BioMed Central, under
[CC BY 2.0](https://creativecommons.org/licenses/by/2.0/). This folder does not contain the paper, its full
text or its supplement (Additional file 1, Tables S1-S7); `figure-reproduction/published/` holds its four
figures (the JPEGs PMC serves) for comparison, redistributed under CC BY 2.0 with the attribution above. The
printed numbers of Tables 2-5 and S1-S7 are in `figure-reproduction/output/published_values.json`, read from
the article and the supplement by `extract_published.py`.

The paper compares two estimators of an exposure-specific risk (ESR) from two independent samples: the
simple product-based ESR_S = P1(D) x RR2, and the authors' revised ESR_R, which first divides the exposed share
out of the overall risk. It ran a simulation in SAS 9.2 (4 scenarios x 7 RRs x 4 pairs of sample sizes, plus
250/250 in one scenario; 1,000 pairs of samples from populations of 10 million) and released no code. We
rebuilt both estimators, their three 95% CIs and the simulation from the text as the Python package
[`package/`](package/) (`esrisk`), reran all 119 settings, and compared every printed cell of Tables 2-4 and
S1-S7 and every bar of Figs 1-4.

| Folder | Content |
| --- | --- |
| [`figure-reproduction/`](figure-reproduction/) | The Nextflow pipeline: the simulation, the comparison with every printed cell and bar, the figures redrawn on the published frames, Table 5, the claims, the checks. |
| [`package/`](package/) | `esrisk`, the method as an installable Python package, with example data, tests and an [executed tutorial](package/tutorial/TUTORIAL.md). |
| [`results.json`](results.json) | Every figure, table and claim of the paper, with our values and computed verdicts. |
| [`session/`](session/) | The ledger of the session that made this reproduction. |

Results page: <https://jeonglab-bcm.github.io/fossil/PMC3022898/>

## Results

<!-- summary from results.json (check_results.py); the full table, with the causes: figure-reproduction/README.md -->

<!--RESULTS-SUMMARY-->
10 agrees, 22 partly, 1 differs, 2 not attempted; 0 open causes.

| Item | Verdict | Measure |
| --- | --- | --- |
| Table 1, the parameter grid | not attempted | not attempted |
| Table 2, relative bias of ESR_S and ESR_R (1000/1000 and 5000/5000) | partly | 78 of 80 fields as printed |
| Table 3, coverage of the log CIs of ESR_S and ESR_R (1000/1000 and 5000/5000) | partly | 77 of 80 fields as printed |
| Table 4, coverage of the binomial CI of ESR_R (four N1/N2, seven RRs) | partly | 111 of 112 fields as printed |
| Table S1, relative bias of ESR_S | partly | 111 of 112 fields as printed |
| Table S2, relative bias of ESR_R | partly | 111 of 112 fields as printed |
| Table S3, absolute bias of ESR_S | agrees | 112 of 112 fields as printed |
| Table S4, absolute bias of ESR_R | partly | 111 of 112 fields as printed |
| Table S5, coverage of the log CI of ESR_S | partly | 111 of 112 fields as printed |
| Table S6, coverage of the log CI of ESR_R | partly | 82 of 112 fields as printed |
| Table S7, coverage of the binomial CI of ESR_R | partly | 111 of 112 fields as printed |
| Fig. 1, expected length given coverage, Scenario 1 (drawn) | partly | 75.00% within 2 px (pass 90.0%, best control 58.3%) |
| Fig. 2, expected length given coverage, Scenario 2 (drawn) | partly | 75.00% within 2 px (pass 90.0%, best control 50.0%) |
| Fig. 3, expected length given coverage, Scenario 3 (drawn) | partly | 66.67% within 2 px (pass 90.0%, best control 58.3%) |
| Fig. 4, expected length given coverage, Scenario 4 (drawn) | partly | 54.55% within 2 px (pass 90.0%, best control 45.5%) |
| Fig. 1, the 12 bar heights | partly | 10 of 12 fields as printed |
| Fig. 2, the 12 bar heights | partly | 9 of 12 fields as printed |
| Fig. 3, the 12 bar heights | partly | 9 of 12 fields as printed |
| Fig. 4, the 11 bar heights (no ESR_S bar at RR 5.0: coverage 0) | partly | 8 of 11 fields as printed |
| Table 5, ESR_S and ESR_R of the case study from the printed inputs | partly | 2 of 6 fields as printed |
| Table 5, log CI of ESR_R predicted from the other two CIs | partly | 5 of 6 fields as printed |
| Abstract: largest relative bias 4.0% for ESR_R and 93.9% for ESR_S | agrees | 2 of 2 fields as printed |
| Main claim: ESR_R has little bias, ESR_S a large one, and the log CI of ESR_R covers better in most settings | agrees | 3 of 3 fields as printed |
| Scenario 1: the CI of ESR_S covers at least 95% when RR is 2.0 or less | differs | 0 of 1 fields as printed |
| Scenarios 1-3: the log CI of ESR_R reaches 95% except at N1/N2 1000/5000, where it never does | partly | 3 of 6 fields as printed |
| The binomial CI of ESR_R reaches 95% only at 1000/5000 (Scenario 1, smallest 98.9%), and is above 99% there in Scenarios 2 and 3 | agrees | 3 of 3 fields as printed, 1 paper errors |
| Relative bias of ESR_S over 20% at RR 5.0 (Scenario 2) and over 10%, 20%, 80% at RR 1.5, 2.0, 5.0 (Scenario 3) | agrees | 4 of 4 fields as printed |
| Scenario 3: the largest relative bias of ESR_R is -1.8% | agrees | 1 of 1 fields as printed |
| Numbers of the Results and Discussion that restate a table cell | agrees | 8 of 8 fields as printed |
| Scenario 4 at N1/N2 250/250 (given only in the text) | agrees | 12 of 12 fields as printed |
| Figs 1-3 as the text reads them | partly | 5 of 6 fields as printed |
| Case study: ESR_R 0.57% to 2.11%, ESR_S higher, largest over-estimation 0.71% at ages 70-79 | partly | 4 of 5 fields as printed |
| Claims recomputed from the paper's own tables and figures | agrees | 40 of 46 statements follow from the paper's own tables and figures. Not: text_binomial_ci_1000_5000: Scenario 3: above 99% for every RR at 1000/5000 (yes against no); text_discussion_self: case study overall risk ranges from (0.0087 against 0.0040); text_discussion_self: case study overall risk ranges to (0.0132 against 0.0147); text_discussion_self: the scenario with exposure .20 and disease in the unexposed .02 (scenario two against Scenario 3); text_discussion_self: equation of the log-based variance of ESR_R (11 against 10); text_discussion_self: equation of the binomial variance of ESR_R (12 against 11). Tables 2-4 restate Tables S1, S2, S5-S7 in every cell but 2: table2 S4 |
| The authors' SAS 9.2 programs | not attempted | not attempted |
| Python package esrisk and its tutorial | agrees | esrisk 0.1.0: wheel installed in a fresh environment and imported from it; tests 8 passed; tutorial 7 cells compared, 0 skipped (nondeterministic); TUTORIAL.md in sync |
<!--/RESULTS-SUMMARY-->

"Agrees" for a simulated table means every cell is within Monte Carlo error of the paper's: half a printed
unit plus three combined standard errors of two 1,000-pair estimates, a tolerance fixed before the comparison
([figure-reproduction/README.md](figure-reproduction/README.md#comparing-monte-carlo-tables)). Two runs of our
own design, with different seeds, differ by more than it in about one cell in a hundred; one such chance miss
is enough to make a 112-cell table "partly".

**What came back.** The bias of both estimators (Tables 2, S1-S4), the log CI of ESR_S (Table S5), the
binomial CI of ESR_R (Tables 4 and S7), every bar of Figs 1-4 for those intervals and the empirical CI, the
numbers given only in the text for Scenario 4 at 250/250, and the case study (Table 5) to its last digit once
the rounding of its printed inputs is allowed for.

**What did not, and why.** The log CI of ESR_R (eq. 10): our intervals, computed as printed, cover more often
than the paper's Table S6 says, most of all at N1/N2 1000/5000 (96.1% to 99.9% against the paper's 85.6% to 94.7%). The
same samples with the first term of eq. 10 left out (the variance of ln P1(D|not E)) give back every cell of
Table S6 and every ESR_R bar of Figs 1-4; so does that term computed as p(1-p)/n1, the variance of the
proportion instead of its log. Using n2 for n1, or P1(D) for P1(D|not E), does not. The case study used eq. 10
as printed: with the sample sizes solved from Table 5's other two intervals, eq. 10 predicts its ESR_R
intervals to the last digit and the shortened variance does not. The SAS code is lost, so this is read from
the results; it makes the paper's simulation understate the coverage of the interval it recommends for
1000/1000 and 5000/5000 by under a point, and overstate its failure at 1000/5000.

**Settings the paper does not state**, each tested against its tables: the true ESR is RR x P(D|not E)
unrounded (the rounded table labels, such as .14 for 0.135, miss many cells); a log interval whose sample 2 has
no cases among the exposed or the unexposed is (0, infinity), covering, with no finite length; populations by
Bernoulli draws, samples without replacement (exact proportions change nothing).

**Slips in the paper**, found by recomputing its text from its own tables (`text.arithmetic`):

- Table 2 prints -0.8% for ESR_S, Scenario 4, RR 1.0, 1000/1000; Table S1 prints 0.8% (ours is within tolerance of both).
- Table 3 prints 96.1 for ESR_R, Scenario 2, RR 4.0, 1000/1000; Table S6 prints 96.9.
- Scenario 3 Results: "greater than 99% when ... 1,000 and ... 5,000", but Tables 4 and S7 give 98.0-99.7; the sentence repeats Scenario 2's.
- Discussion: the case study's overall risk "ranged from 0.0087 to 0.0132"; Table 5 prints 0.0040 to 0.0147.
- Discussion: the case study "most closely resemble[s] scenario two ... exposure probability of 0.20 and ... .02"; that is Scenario 3.
- Discussion: "equation 11" and "equation 12" for the log and binomial variances of ESR_R; they are equations 10 and 11.

The main claim holds: ESR_R removes the bias of ESR_S (largest relative bias 2.9% against 94.2% in our run;
4.0% and 93.9% in the paper), and the binomial CI of ESR_R and the log CI of ESR_S behave as the paper reports.
The claims that do not match come from eq. 10's first term, from cells near the 95% line, or from the rounding
of the case study's inputs.

Kept local and gitignored: `sources/` (the paper, its XML and text, Additional file 1, the figure JPEGs as
downloaded, the LibreOffice conversion), `work/` and `.venv/`.
