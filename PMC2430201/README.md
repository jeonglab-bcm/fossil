# PMC2430201: The ratio of means method for meta-analysis of continuous outcomes (Friedrich et al. 2008)

Friedrich JO, Adhikari NKJ, Beyene J. The ratio of means method as an alternative to mean differences for
analyzing continuous outcome variables in meta-analysis: a simulation study. *BMC Medical Research Methodology*
8:32 (2008). [doi:10.1186/1471-2288-8-32](https://doi.org/10.1186/1471-2288-8-32) ·
[PMC2430201](https://pmc.ncbi.nlm.nih.gov/articles/PMC2430201/) · issue #73

The paper is © 2008 Friedrich et al., licensee BioMed Central, under
[CC BY 2.0](https://creativecommons.org/licenses/by/2.0/). This folder does not contain the paper or its full
text. The paper has no figures and no supplement. The printed numbers of Tables 1-8 are in
`figure-reproduction/output/published_values.json`, read from the article XML by `extract_published.py`.

The paper proposes the ratio of means (RoM) for meta-analysis of continuous outcomes: the experimental mean over
the control mean, pooled on the log scale with a first-order delta-method variance. It compares RoM with the mean
difference (MD) and the standardized mean difference (SMD) in a simulation study run in SAS 8.2 (216 scenarios of
SD, effect size, trial size, number of trials and heterogeneity, 10,000 meta-analyses each; Tables 3-8), and
released no code. We rebuilt the three measures, DerSimonian-Laird pooling and the simulation from the text as the
Python package [`package/`](package/) (`rommeta`), checked its pooling against R's metafor, reran every scenario
and compared every printed cell of Tables 3-8 and every quantitative claim of the text.

| Folder | Content |
| --- | --- |
| [`figure-reproduction/`](figure-reproduction/) | The Nextflow pipeline: the simulation, the comparison with every printed cell, the claims, the check against metafor, the checks. |
| [`package/`](package/) | `rommeta`, the method as an installable Python package, with example data, tests and an [executed tutorial](package/tutorial/TUTORIAL.md). |
| [`results.json`](results.json) | Every table and claim of the paper, with our values and computed verdicts. |
| [`session/`](session/) | The ledger of the session that made this reproduction. |

Results page: <https://jeonglab-bcm.github.io/fossil/PMC2430201/>

## Results

<!-- summary from results.json (check_results.py); the full table, with the causes: figure-reproduction/README.md -->

<!--RESULTS-SUMMARY-->
2 exact, 14 agrees, 3 partly, 3 not attempted; 0 open causes.

| Item | Verdict | Measure |
| --- | --- | --- |
| Table 1, low-dose dopamine meta-analysis: pooled MD, SMD and RoM with CIs, p and I2 | not attempted | not attempted |
| Table 1: each estimate at the midpoint of its CI, and each p-value from its CI | exact | 13 of 13 fields as printed, 1 paper errors |
| Table 2, the parameter values of the simulated data sets | not attempted | not attempted |
| Table 3, normal data, SD 40% of the control mean, equal arms (18 rows x 21 cells) | partly | 377 of 378 fields as printed |
| Table 4, normal data, SD 10% of the control mean, equal arms (18 rows x 21 cells) | agrees | 378 of 378 fields as printed |
| Table 5, normal data, SD 70% of the control mean, equal arms (18 rows x 21 cells) | agrees | 378 of 378 fields as printed |
| Table 6, skewed data, SD 40% of the control mean, equal arms (18 rows x 21 cells) | partly | 377 of 378 fields as printed |
| Table 7, normal data, SD 40%, 2:1 experimental to control (14/6 and 134/66; 18 rows x 21 cells) | agrees | 378 of 378 fields as printed |
| Table 8, normal data, SD 40%, 1:2 experimental to control (6/14 and 66/134; 18 rows x 21 cells) | agrees | 378 of 378 fields as printed |
| SMD bias towards no effect: about 5% with 10 patients per arm (Abstract), -4 to -6% in Table 3, smaller with 100 (Results) | agrees | 4 of 4 fields as printed |
| RoM bias -4% to 2% with SD 70% and effects 0.5-0.8 (Abstract); up to 2-3% towards unity at n 10 and 1-2% away from it with heterogeneity at n 100; its sign with unequal arms (Results) | agrees | 7 of 7 fields as printed |
| Where RoM bias towards no effect exceeds 1.5%, RoM covers 89-92% and MD 92-94% (Abstract) | agrees | 3 of 3 fields as printed, 1 paper errors |
| Lowest coverage 87-88%, for all three methods, with 5 trials of 100 patients per arm and heterogeneity (I2 92-93%) (Results) | agrees | 5 of 5 fields as printed, 1 paper errors |
| 1,000 patients per arm: coverage still 87-88% and I2 99% (Results, 'results not shown') | agrees | 4 of 4 fields as printed |
| I2 around 55-60% with 10 patients per arm and above 90% with 100; lower for SMD and RoM where they are biased (Results) | partly | 3 of 4 fields as printed |
| Power within 5 percentage points across the methods in almost all scenarios; lower with unequal arms (Results) | agrees | 3 of 3 fields as printed |
| Methods: expected I2 56% (n 10) and 93% (n 100); second-order delta terms below 2.5%; the skewed mixture's mean, SD and skewness 0.88 | exact | 6 of 6 fields as printed |
| Main claim: MD bias-free, SMD biased towards no effect in small trials, RoM bias within -4 to 2%, similar power (Abstract and Conclusion) | agrees | 4 of 4 fields as printed |
| Claims recomputed from the paper's own tables | agrees | 34 of 38 statements follow from the paper's own tables. Not: text_coverage: k 5, 100/100, tau 0.5 (Tables 3-6): lowest I2 (%) [Results: I2 = 92-93%] (92 against 91.0); text_biased_rom_coverage: Scenarios with RoM bias towards no effect over 1.5% (Tables 3-8): highest RoM coverage (%) [Abstract: 89-92%] (92 against 95.0); text_biased_rom_coverage: Scenarios with RoM bias towards no effect over 1.5% (Tables 3-8): lowest MD coverage (%) [Abstract: 92-94%] (92 against 90.0); text_biased_rom_coverage: Scenarios with RoM bias towards no effect over 1.5% (Tables 3-8): highest MD coverage (%) [Abstract: 92-94%] (94 against 95.0). |
| rommeta's effect sizes and pooling against R's metafor (an independent implementation) | agrees | rommeta.pool against metafor 4.4.0 rma (DL) on 900 simulated meta-analyses (100 each of 3 scenarios x MD, SMD, RoM): pooled estimate, SE, tau2, Q and I2 agree to a relative 5.2e-14; both leave out the same 2 RoM studies with a non-positive mean |
| The authors' SAS 8.2 programs | not attempted | not attempted |
| Python package rommeta and its tutorial | agrees | rommeta 0.1.0: wheel installed in a fresh environment and imported from it; tests 11 passed; tutorial 6 cells compared, 0 skipped (nondeterministic); TUTORIAL.md in sync |
<!--/RESULTS-SUMMARY-->

"Agrees" for a simulated table means every cell is within Monte Carlo error of the paper's: half a printed unit
plus three combined standard errors of two 10,000-replicate estimates, a tolerance fixed before the comparison
([figure-reproduction/README.md](figure-reproduction/README.md#comparing-monte-carlo-tables)). No simulated item can
be "exact": the paper gives no seeds, and two of its unstated definitions were found by testing against its tables.

**What came back.** The whole simulation study: bias, coverage and power of MD, SMD and RoM with and without
heterogeneity, and I2, in all six tables, cell by cell, with two chance misses that our second run puts back. The
claims of the text came back on our run, including the case of 1,000 patients per arm that the paper describes but
does not show. The Methods' analytic statements (expected I2, the size of the second-order delta terms, the moments
of the skewed mixture) follow from their formulas.

**Settings the paper does not state**, each tested against its tables (`output/comparison.json`, `hypotheses`):

- % bias of RoM is taken on the ratio scale, (mean pooled RoM - true RoM)/true RoM. On ln RoM, or as a share of
  RoM - 1, many RoM bias cells miss.
- I2 is 100 x (1 - 1/m), m the mean of Q/(k - 1) over the 10,000 replicates, as the tables' legends hint ("the
  ratio of Q/(k-1)"). The mean or the median of each replicate's I2 is lower, the mean far lower at small k.
- Heterogeneity: the paper gives the per-arm SD, 0.5/√2 SD; independence and normality of the shifts are ours. A
  shift of one arm only, or one shift shared by both, misses.
- Skewed data (Table 6): the mixture times 100, the experimental arm shifted by the effect. Scaling the experimental
  arm instead misses; rescaling the mixture to SD 40 exactly before the shift fits as well, and the tables cannot
  tell the two apart.

**Slips in the paper**, found by recomputing its text from its own tables (`text.arithmetic`) and Table 1 from itself:

- Abstract: where RoM bias towards no effect exceeds 1.5%, "RoM ... 89-92% vs. [MD] 92-94%" coverage. The paper's
  tables give RoM 89-95% and MD 90-95% for those scenarios (Table 5, SMD 0.5, 10/10, k 10, tau 0 prints RoM bias -2
  and coverage 95 for both RoM and MD).
- Results: the lowest coverage occurs with "I2 = 92-93%"; Table 5 prints a RoM I2 of 91 there.
- Table 1: the serum creatinine MD, -3.51, is not the centre of its own CI (-6.71 to -0.23, centred on -3.47).

<!--CLAIMS-LINE-->
The main claim holds. The one claim that misses on our run sits on a rounding line in Table 6 (a setting of the skewed data the paper does not state); three statements of the text do not match the paper's own tables.
<!--/CLAIMS-LINE-->

Kept local and gitignored: `sources/` (the paper's XML, text and PDF as downloaded), `work/` (scratch runs),
`.venv/` and `.rlib/`.
