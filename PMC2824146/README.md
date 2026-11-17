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
<!--/RESULTS-SUMMARY-->

<!--RESULTS-PROSE-->
<!--/RESULTS-PROSE-->

## Kept local

Git-ignored: `sources/` (the paper's PDF, text and XML, and the figure files as downloaded). The
pipeline downloads its inputs itself (`figure-reproduction/pipeline/fetch_inputs.sh`); the breast
cancer data come from the CRAN package TH.data (GPL-3), which is not copied here.

Made with Paper2Repro v0.5.0 (the installed copy of the skill had no git metadata, so `results.json`
records `commit: null`).
