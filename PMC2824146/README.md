# PMC2824146: Comparison of techniques for handling missing covariate data within prognostic modelling studies (Marshall et al. 2010)

Marshall A, Altman DG, Royston P, Holder RL. Comparison of techniques for handling missing covariate
data within prognostic modelling studies: a simulation study. *BMC Medical Research Methodology* 10:7
(2010). [doi:10.1186/1471-2288-10-7](https://doi.org/10.1186/1471-2288-10-7),
[PMC2824146](https://pmc.ncbi.nlm.nih.gov/articles/PMC2824146/), issue
[jeonglab-bcm/fossil#66](https://github.com/jeonglab-bcm/fossil/issues/66).

The paper is © 2010 Marshall et al; licensee BioMed Central Ltd, an Open Access article under the
Creative Commons Attribution License 2.0 (<https://creativecommons.org/licenses/by/2.0/>). This
folder does not contain the paper or its full text; `figure-reproduction/published/` holds its eight
figures, unchanged, with that attribution, and the figures under `figure-reproduction/output/figures/`
include renderings of them (`fig*_published.png`, `fig*_overlay.png`).

The paper simulated prognostic cohorts like the German Breast Cancer Study Group 2 data, deleted
values of four covariates under four mechanisms at five levels, handled the missing data by complete
case analysis, single imputation and seven multiple imputation methods in R, and compared the Cox
model estimates. The simulation code was never released. We rebuilt it from the paper's text as the R
package [`package/`](package/) (`misscox`), ran it (200 replicates for MAR and MNAR, 100 for MCAR and
the combined mechanism, 20,000 true-value cohorts), and compared every plotted point of Figures 2 to 8,
read from the article's vector figures, within Monte Carlo error.

| Folder | Content |
| --- | --- |
| [`figure-reproduction/`](figure-reproduction/) | The Nextflow pipeline: inputs, the published values, the data-derived results, the simulation results, every comparison, the figures, the check against the committed outputs. |
| [`package/`](package/) | `misscox`, the simulation and the nine methods as an R package, with example data, tests and a [tutorial](package/tutorial/TUTORIAL.md). |
| [`results.json`](results.json) | Every figure, table and claim of the paper, with our values and computed verdicts. |
| [`session/`](session/) | The ledger of the session that made this reproduction. |

Results page: <https://jeonglab-bcm.github.io/fossil/PMC2824146/>

## Results

<!-- summary and table from results.json (check_results.py --markdown); do not edit by hand -->
<!--RESULTS-SUMMARY-->
4 exact, 7 agrees, 15 partly, 1 differs, 2 not attempted; 15 open causes.

| Item | Verdict | Measure |
| --- | --- | --- |
| Table 1, means and SDs after transformation | exact | 16 of 16 fields as printed |
| Skewness of X2, X3, X4, X8 (Methods text) | agrees | 4 of 4 fields as printed |
| Correlations quoted in the Methods text | agrees | 4 of 4 fields as printed |
| Fig. 1, histograms of the covariates (a) and the transformed covariates (b) | agrees | 82 of 82 fields as printed |
| Linear predictor, full Cox model on the breast cancer data (Methods equation) | exact | 9 of 9 fields as printed |
| About 35% censored (Methods text) | differs | 0 of 1 fields as printed |
| Missingness design: incomplete cases, shares and overlaps (Methods text) | partly | 22 of 40 fields as printed |
| Table 2, specification of the missingness mechanisms | not attempted | not attempted |
| Table 3, odds ratios between missingness indicators | agrees | 15 of 15 fields as printed |
| Table 4, the missing data methods | not attempted | not attempted |
| Figs 2 and 3, reference lines: true values and empirical SEs (20,000 complete-data cohorts) | partly | 10 of 18 fields as printed |
| Fig. 2, coefficient estimates under MAR | partly | 301 of 333 fields as printed |
| Claims about Fig. 2 (bias, 0.5 SE, 10% bias) | partly | 11 of 18 fields as printed, 5 paper errors |
| Fig. 3, average SEs under MAR | partly | 164 of 333 fields as printed |
| Claims about Fig. 3 (SEs) | exact | 6 of 6 fields as printed, 3 paper errors |
| Fig. 4, coverage under MAR | partly | 322 of 333 fields as printed |
| Claims about Fig. 4 (coverage) | partly | 14 of 18 fields as printed, 1 paper errors |
| Fig. 5, mean p-values under MAR | partly | 295 of 333 fields as printed |
| Claims about Fig. 5 (significance) | partly | 1 of 2 fields as printed, 2 paper errors |
| Fig. 6, model performance under MAR (LR p, R2, D, 2-year survival) | partly | 125 of 148 fields as printed |
| Claims about Fig. 6 (model performance) | partly | 5 of 7 fields as printed |
| Fig. 7, coefficients of X2 to X5 under MAR and MNAR | partly | 119 of 140 fields as printed |
| Fig. 8, coverage of X2 to X4 under MAR and MNAR | partly | 94 of 105 fields as printed |
| Claims about Figs 7 and 8 (MNAR against MAR) | partly | 7 of 10 fields as printed, 1 paper errors |
| MCAR and combined like MAR; NORM and MIX like MICE (Results text, not plotted) | partly | 1 of 4 fields as printed |
| Main claim (Abstract and Conclusions): MICE-PMM least biased, fails from 50% and under MNAR | exact | 6 of 6 fields as printed |
| Claims recomputed from the paper's own figure values | agrees | 59 of 77 claim fields come back when computed from the paper's own figure values; not: text.fig2: SI more than 0.5 SE away for X2, X3 and X4 from 25% (figures give no); text.fig2: Most MI more than 0.5 SE away for X2, X3 and X4 from 25% (figures give no); text.fig2: X2 MICE: first level with bias over 10% (figures give 50); text.fig2: X2 MICE-PMM: first level with bias over 10% (figures give 50); text.fig2: X2 MICE-PMM no transformation: first level with bias over 10% (figures give 75); text.fig2: X2 aregImpute: first level with bias over 10% (figures give 50); text.fig2: X2 MIX no truncating: first level with bias over 10% (figures give 50); text.fig2: X3 MICE-PMM no transformation: first level with bias over 10% (figures give 75); text.fig2: X3 aregImpute: first level with bias over 10% (figures give 50); text.fig2: X5 bias over 10% at 50% with every MI (figures give no); text.fig2: X4: MICE-PMM no transformation least biased MI at 75% (figures give no); text.fig3: X2: every MI SE between SI and CC at 25 to 75% (figures give no); text.fig3: X3: every MI SE between SI and CC at 25 to 75% (figures give no); text.fig3: X4: CC SE rises by over 10% at 75%, SI and MI within 10% of full data (figures give no); text.fig4: X3 MICE-PMM no transformation: first level with coverage below 90% (figures give 75); text.fig5: CC X5: first level with p over 0.05 (figures give 75); text.fig5: CC X7: first level with p over 0.05 (figures give 75); text.mnar: X3 coverage lower under MNAR than MAR at 75%, every MI (figures give no) |
| Replicates rerun from scratch equal the committed results | agrees | 3 of 3 reruns from scratch equal the committed results: MAR replicate 1 (46 rows); MNAR replicate 1 (31 rows); true values replicate 1-200 (200 rows) |
| R package misscox and its tutorial | agrees | R CMD build ok; R CMD check: OK; testthat [ FAIL 0 |
<!--/RESULTS-SUMMARY-->

<!--RESULTS-PROSE-->
The data side comes back exactly. Table 1, the skewness and correlations quoted in the Methods,
and the linear predictor's nine coefficients come back from GBSG2 at the printed digit; every bar of
Figure 1 matches; all 15 odds ratios of Table 3 come back once the design's shares are counted as whole
cases of 1000, rounded half up.

The simulation comes back in shape and mostly in value. Of the points plotted in Figures 2 to 8, read
from the article's vector figures, 301 of 333 (Fig. 2), 322 of 333 (Fig. 4), 295 of 333 (Fig. 5),
119 of 140 (Fig. 7) and 94 of 105 (Fig. 8) lie within Monte Carlo error of ours; Fig. 3 (164 of 333)
and Fig. 6 (125 of 148) less so. The main claim holds (6 of 6 fields): MICE-PMM without transformation
is the least biased MI method for the skewed covariates, stays within 10% bias at 25%, and is more than
0.5 SE from the truth at 50% under MAR, MCAR and the combined mechanism; under MNAR every MI method is
more than 0.5 SE off for X3 from 25%.

Three gaps stay open. Our generated covariates differ from the paper's: the binaries, cut at 0.5 as
the text says, lose part of their correlation, so the SEs of X1 and X6 come out 15% smaller (Fig. 3)
and X6's p-values lower (Fig. 5); keeping the correlations overshoots the paper's SEs. The paper's
pooled likelihood ratio p-values after MI (up to 0.0046) do not come back under any pooling rule we
tried (ours stay below 3 x 10^-6). Under MNAR our X3 and X4 estimates are further from the truth
than the paper's. The 2004 to 2005 imputation packages could not be run to test their part.

The text contradicts its own figures in 18 of 77 claim fields: for example, by Fig. 2 MICE-PMM
without transformation passes 10% bias for X2 and X3 at 75%, not at 50% as the text says, and by
Fig. 5 the complete-case p-values of X5 and X7 cross 0.05 at 75%, not 50%. In Fig. 6b the SI line is
drawn in MICE-PMM's colour with MICE-PMM's values. These are counted as paper errors where our run
agrees with the figures.
<!--/RESULTS-PROSE-->

## Kept local

Git-ignored: `sources/` (the paper's PDF, text and XML, and the figure files as downloaded). The
pipeline downloads its inputs itself (`figure-reproduction/pipeline/fetch_inputs.sh`); the breast
cancer data come from the CRAN package TH.data (GPL-3), which is not copied here.

Made with Paper2Repro v0.5.0 (the installed copy of the skill had no git metadata, so `results.json`
records `commit: null`).
