# PMC1955447: A simulation study of sample size for multilevel logistic regression models (Moineddin et al. 2007)

Moineddin R, Matheson FI, Glazier RH. A simulation study of sample size for multilevel logistic regression models.
*BMC Medical Research Methodology* 7:34 (2007). [doi:10.1186/1471-2288-7-34](https://doi.org/10.1186/1471-2288-7-34) ·
[PMC1955447](https://pmc.ncbi.nlm.nih.gov/articles/PMC1955447/) · issue #86

The paper is © 2007 Moineddin et al., licensee BioMed Central, under
[CC BY 2.0](https://creativecommons.org/licenses/by/2.0/). This folder does not contain the paper or its full
text. The paper has no figures and no supplement. The printed numbers of Tables 1-5 are in
`figure-reproduction/output/published_values.json`, read from the article XML by `extract_published.py`.

The paper asks how many groups, and how many people per group, a two-level logistic regression with a random
intercept and a random slope needs. It simulated 27 designs (30, 50 or 100 groups of 5, 30 or 50, at three
intra-class correlations), 1,000 data sets each, fitted each by maximum likelihood with SAS PROC NLMIXED, and
reported convergence, bias and the coverage of Wald intervals (Tables 1-3), the same at three prevalences
(Table 4), and with non-normal covariates and random effects (Table 5). It released no code. We rebuilt the
data generator and an NLMIXED-like fit (adaptive Gauss-Hermite quadrature, NLMIXED's rule for the number of
points, quasi-Newton from the true values) as the Python package [`package/`](package/) (`mlagq`), reran every
design and compared every printed cell and every quantitative claim of the text.

| Folder | Content |
| --- | --- |
| [`figure-reproduction/`](figure-reproduction/) | The Nextflow pipeline: the simulation, the per-replicate records, the comparison with every printed cell, the claims, the check against numerical integration, the checks. |
| [`package/`](package/) | `mlagq`, the method as an installable Python package, with example data, tests and an [executed tutorial](package/tutorial/TUTORIAL.md). |
| [`results.json`](results.json) | Every table and claim of the paper, with our values and computed verdicts. |
| [`session/`](session/) | The ledger of the session that made this reproduction. |

Results page: <https://jeonglab-bcm.github.io/fossil/PMC1955447/>

## Results

<!-- summary from results.json (check_results.py); the full table, with the causes: figure-reproduction/README.md -->

<!--RESULTS-SUMMARY-->
1 exact, 5 agrees, 21 partly, 1 not attempted; 19 open causes.

| Item | Verdict | Measure |
| --- | --- | --- |
| Methods: variances 0.13, 0.67, 2.0 give ICC 0.04, 0.17, 0.38 and σ0 0.36, 0.82, 1.42 | exact | 5 of 5 fields as printed, 1 paper errors |
| Methods and Table 4: prevalence close to 30% in the main grid; 0.10, 0.34, 0.45 with Table 4's coefficients | partly | 1 of 4 fields as printed |
| Table 1, % converged in each of the 27 cells | partly | 24 of 27 fields as printed |
| Table 1, % relative bias in the 19 cells that converged in 98-100% of data sets (114 values) | agrees | 114 of 114 fields as printed |
| Table 1, % relative bias in the 8 cells that converged in 56-94% of data sets (48 values) | partly | 45 of 48 fields as printed |
| Table 2, non-coverage pooled by number of groups, group size and ICC (54 values) | partly | 51 of 54 fields as printed |
| Table 2, the 18 p-values for the effect of each factor on non-coverage, as significant or not at 0.05 | partly | 12 of 18 fields as printed |
| Table 3, non-coverage in the 19 cells that converged in 98-100% of data sets (114 values) | agrees | 114 of 114 fields as printed |
| Table 3, non-coverage in the 8 cells that converged in 56-94% of data sets (48 values) | partly | 43 of 48 fields as printed |
| Table 4, % bias, non-coverage and % converged at prevalence 0.10, 0.34 and 0.45 (54 values) | partly | 33 of 54 fields as printed |
| Table 5, % converged of the eight non-normal models in 9 cells each (72 values) | partly | 71 of 72 fields as printed |
| Table 5, % relative bias (432 values) | partly | 396 of 432 fields as printed |
| Table 5, % non-coverage (432 values) | partly | 403 of 432 fields as printed |
| Convergence: 56% to 100% by cell; 80.4/99.3/99.9% by group size, 87.7/93.8/98.1% by number of groups, 89.2/94.5/95.9% by ICC; no negative variances | partly | 8 of 13 fields as printed |
| Converged against non-converged data sets: prevalence 30.4% vs 30.0%; z mean and SD 0.01 and 1.01 vs 0.02 and 1.00; x 0.00 and 1.00 vs 0.00 and 1.00 | partly | 5 of 10 fields as printed |
| Non-converged data sets of 30 groups x 5 refitted with a random intercept only and a random slope only: both significant in 2.4% (168 data sets) | partly | 1 of 2 fields as printed |
| Shapiro-Wilk tests of the fixed-effect estimates: most non-normal with groups of 5 even with 100 groups, a few non-normal with groups of 30 and 50 groups, all normal with 100 groups of 50 | partly | 1 of 3 fields as printed |
| Overall fixed-effect bias 0.6%, 2.6%, 1.4% and 3.7% for γ00, γ01, γ10, γ11 ('data not shown'); γ11 the largest | partly | 3 of 5 fields as printed |
| Largest fixed-effect biases 8.8%, 11.1%, 15.8%, 13.3% at 30 groups x 5, ICC 0.04; below 6% at 30 x 30, below 4% at 50 x 30, 1% or less at 100 x 30 | partly | 7 of 8 fields as printed, 3 paper errors |
| Variance components: overall bias 6.9% (σ0) and 5.0% (σ1); σ0 21.2% at σ0 0.36 (21%, 0.5%, 0.1% by ICC); σ1 4-6% by ICC; below 4% at 100 x 50; positive at group size 5, negative at 30 and 50 | partly | 10 of 11 fields as printed |
| Non-coverage: fixed effects 5-6% by number of groups (4-6% in Table 2, 3-7% by cell); variance components 7-11% (11% and 10% at 30 groups, 9% and 7% at 100; 7-17% by cell); σ1 rises with group size, σ0 falls with ICC | partly | 14 of 15 fields as printed, 1 paper errors |
| Prevalence: 10% gives the largest bias and the lowest convergence; non-coverage 5-6% (fixed) and 8-11% (random); largest bias 12% and 50% with groups of 5, 9% and 15% with 30 groups ('data not shown') | partly | 7 of 11 fields as printed |
| Non-normal models against model 1 (Discussion): convergence with groups of 5 higher for models 3, 6, 7, 8 and lower for 4, 5; no difference in fixed effects; variances underestimated for models 6-8; random-effect coverage lower for models 6 and 7 | partly | 18 of 19 fields as printed, 1 paper errors |
| Main claim (Abstract, Conclusion): fixed effects unbiased with 100 groups of 50, variance components slightly biased there, severe bias with groups of 5, fixed-effect SEs right and variance-component SEs too small, low prevalence needs larger samples | partly | 4 of 9 fields as printed |
| Claims and pooled values recomputed from the paper's own tables (Table 2 from Tables 1 and 3; the text from Tables 1-5) | agrees | 123 of 139 statements and pooled values follow from the paper's own tables. Not: methods_design: sigma0 = sqrt(2.0) (1.42 against 1.4142); text_convergence: % converged, size 5 (80.4 against 81.1111); text_fixed_bias_cells: g01: the largest bias of the 27 cells is at 30 groups x 5, ICC 0.04 (yes against no); text_fixed_bias_cells: g11: the largest bias of the 27 cells is at 30 groups x 5, ICC 0.04 (yes against no); text_fixed_bias_cells: every fixed-effect bias 1% or less at 100 groups x 30 (yes against no); text_random_bias: overall % bias σ0 (6.9 against 7.5363); text_random_bias: overall % bias σ1 (5.0 against 5.2064); text_random_bias: % bias σ0 at σ0 = 0.36 (ICC 0.04) (21.2 against 22.7106); text_random_bias: % bias σ0, ICC 0.04 (21 against 22.7106); text_random_bias: % bias σ0, ICC 0.17 (0.5 against 0.6467); text_random_bias: % bias σ0, ICC 0.38 (0.1 against 0.1746); text_random_bias: lowest % bias σ1 over the ICCs (4 against 4.6512); text_noncoverage: lowest variance-component non-coverage of a cell (%) (7 against 3.0); text_robustness: model 7 against model 1, convergence with groups of 5 (p < 0.01) (more likely against no difference); text_robustness: model 8 against model 1, convergence with groups of 5 (p < 0.01) (more likely against no difference); text_robustness: no model differs from model 1 in convergence with groups of 30 or 50 (yes against no). |
| mlagq's likelihood and maxima against direct numerical integration | agrees | mlagq's adaptive quadrature log-likelihood against a dense-grid integral on 9 data sets of 30 groups x 5 and x 30 (all ICCs): every relative difference below 1e-4; at 9 interior maxima no step of 1e-4 in any parameter raises the dense-grid log-likelihood by 1e-5 or more |
| The authors' SAS 9.1 PROC NLMIXED programs | not attempted | not attempted |
| Python package mlagq and its tutorial | agrees | mlagq 0.1.0: wheel installed in a fresh environment and imported from it; tests 6 passed; tutorial 7 cells compared, 0 skipped (nondeterministic); TUTORIAL.md in sync |
<!--/RESULTS-SUMMARY-->

<!--SUMMARY-PROSE-->
Every simulated cell is compared at a tolerance fixed before the comparison: half a printed unit plus three
combined Monte Carlo standard errors ([figure-reproduction/README.md](figure-reproduction/README.md#comparing-monte-carlo-tables)).
No simulated item can be "exact": the paper gives no seeds, and three of its unstated settings were found by testing
against its tables.

**What came back.** 1,294 of the 1,395 printed values of Tables 1-5 (all but Table 2's p-values) came back within Monte Carlo error.
In the 19 designs where 98-100% of fits converged, every bias and non-coverage cell of Tables 1 and 3 came back
(114 of 114 and 114 of 114), and so did 33 of Table 4's 36 biases and non-coverage rates. The
pattern of convergence came back: fits fail with few small groups and a small random intercept.

**What did not.** Which fits count as converged is NLMIXED's verdict. Our NLMIXED-like optimizer converges in
55, 77, 82% of data sets of 30 groups of 5 (paper 56, 68, 76), so the group-size-5 rows of Tables 1 and 3, Table 4's
convergence and the t3 models of Table 5 differ where they depend on which fits are kept. σ0's interval covers more
often than the paper's where the random intercept is small. Each gap has its tested hypotheses in `results.json`.

**Settings the paper does not state**, each tested against its tables (`output/comparison.json`, `hypotheses`):

- σ0 and σ1 are the variances as fitted, not standard deviations: the biases at group size 5 only come back on the
  variance scale, and so do the intervals (38 of 38 high-convergence σ cells of Table 3,
  against 31 on the SD scale).
- The model estimates σ01, although the data have none. Without it nearly every data set of groups of 5 converges.
- A fit also stops when no parameter moves by more than 1e-8 (the paper's "absolute parameter convergence
  criterion", NLMIXED's ABSXCONV); fits creeping towards a zero variance stop this way and count as converged.
- Table 5's non-coverage counts a data set that did not converge as not covered: 403 of 432
  cells come back, against 354 over converged fits only.

**Slips in the paper**, found by recomputing its text from its own tables (`text.arithmetic`): the Methods give
σ0 = 1.42 for a variance of 2.0 (√2 = 1.41); the text puts the largest γ01 and γ11 biases at 30 x 5, ICC 0.04,
where Table 1 has them at ICC 0.38 and 0.17; "1% or less" at 100 x 30, where Table 1 prints 1.04 and 1.07;
variance-component non-coverage of "7% to 17%" by cell, where Table 3 goes down to 0.030; the convergence of groups
of 5 (80.4%) is not the mean of Table 1's (81.1%); and "no significant difference between the rates of convergence"
with groups larger than 5, where Table 5 has model 4 at 76% against model 1's 100%. Table 2's σ0 row by ICC repeats
its row by number of groups but is what Table 3 gives: not a copy error.
<!--/SUMMARY-PROSE-->

<!--CLAIMS-LINE-->
The main claim holds in part: on our run fixed effects are unbiased with 100 groups of 50, biases are severe with groups of 5, convergence fails where samples are small, and the variances' intervals stay too narrow even with 100 groups of 50. Our run does not make the 10% prevalence the most biased, and with groups of 5 some of our fixed-effect intervals cover more often than the paper's (non-coverage down to 0.9% against its lowest 2.8%); both depend on which fits NLMIXED kept.
<!--/CLAIMS-LINE-->

Kept local and gitignored: `sources/` (the paper's XML, text and PDF as downloaded), `work/` (scratch runs and
the full records of the second run and the hypothesis variants), `.venv/`.
