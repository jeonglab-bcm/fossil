# PMC2824146 reproduction check

## results.json

| Item | Verdict | Measure | Why |
| --- | --- | --- | --- |
| Table 1, means and SDs after transformation | exact | 16 of 16 fields as printed |  |
| Skewness of X2, X3, X4, X8 (Methods text) | agrees | 4 of 4 fields as printed | Assumed: Skewness b1 = m3 / s^3 with the n - 1 SD, on the raw scale (the paper does not define it) |
| Correlations quoted in the Methods text | agrees | 4 of 4 fields as printed | Assumed: Pearson correlations on the raw (untransformed) scale |
| Fig. 1, histograms of the covariates (a) and the transformed covariates (b) | agrees | 82 of 82 fields as printed | Assumed: Published values are read from the article PDF's vector figures: each plotted point is a vertex of the series' line, each axis is mapped from its tick marks and printed labels; the PDF writer's coordinate grid is 0.405 pt |
| Linear predictor, full Cox model on the breast cancer data (Methods equation) | exact | 9 of 9 fields as printed |  |
| About 35% censored (Methods text) | differs | 0 of 1 fields as printed | The text's 'approximately 35%' is a rounded figure: the stated hazards (0.0002 for censoring against 0.00027 exp(LP) for events) give 36.4 to 36.6% censored with every variant of our generator. |
| Missingness design: incomplete cases, shares and overlaps (Methods text) | partly | 22 of 40 fields as printed | Each covariate is missing in exactly its share of all cases (X3 at 25%: 67.98% of 25.75% incomplete cases is 17.50% of all cases, the design's 0.70 x 25%), but the overall share of incomplete cases runs 0.3 to 0.8 points above the target because only three pairs of indicators are tied (X5 and X3 or X8 and X2 can be missing together by chance). The shares of incomplete cases then fall slightly below the stated ones. The paper's numbers are design targets ('approximately'), and how it tied the other pairs is not stated. |
| Table 2, specification of the missingness mechanisms | not attempted | not attempted | A design input, used as given (the blank X3 cell of the combined mechanism read as MCAR). |
| Table 3, odds ratios between missingness indicators | agrees | 15 of 15 fields as printed | Assumed: The shares become whole cases of 1000, rounded half up, before the odds ratio is taken |
| Table 4, the missing data methods | not attempted | not attempted | A list of methods and settings, implemented as given in the package. |
| Figs 2 and 3, reference lines: true values and empirical SEs (20,000 complete-data cohorts) | partly | 10 of 18 fields as printed | Our generator's empirical SEs are 14% smaller for X1 and X6 and 14% larger for X4 than the paper's, and its true values 1 to 3% larger in magnitude for X2, X3, X5 and X7. Keeping the binaries' observed correlations takes the X1 and X6 SEs past the paper's (0.0064 and 0.132 against 0.0060 and 0.119, ours 0.0051 and 0.104); the unrounded coefficients move X2's true value from 0.0517 to 0.0513 (paper 0.0507); the X4 SE and the larger magnitudes stay open. |
| Fig. 2, coefficient estimates under MAR | partly | 301 of 333 fields as printed | Most points fall within Monte Carlo error; the misses are MI estimates of X2, X3, X4 and X5 at 50 and 75%, where our MIX without truncating, MICE-PMM and SI are further from or nearer the truth than the paper's. The offset of the true values does not explain them; the 2004 to 2005 package versions could not be tested. |
| Claims about Fig. 2 (bias, 0.5 SE, 10% bias) | partly | 11 of 18 fields as printed, 5 paper errors | Each claim is computed from our figure values with the paper's thresholds (0.5 SE, 10% bias, 90% coverage, p = 0.05). Where the text disagrees with the paper's own figures and our run agrees with the figures, the field is a paper error and is not counted; the claims that still differ follow the gaps of the figure they rest on. |
| Fig. 3, average SEs under MAR | partly | 164 of 333 fields as printed | Every point of X1, X4 and X6 misses by a constant factor across methods and levels (ours 0.84, 1.15 and 0.85 times the paper's), the same factor as their empirical SEs with no missing data: the generated covariates differ (see the reference lines). Keeping the binaries' correlations moves the X1 and X6 SEs past the paper's. The other misses (X2, X5) are MI SEs at 50 and 75%. |
| Claims about Fig. 3 (SEs) | exact | 6 of 6 fields as printed, 3 paper errors | Each claim is computed from our figure values with the paper's thresholds (0.5 SE, 10% bias, 90% coverage, p = 0.05). Where the text disagrees with the paper's own figures and our run agrees with the figures, the field is a paper error and is not counted; the claims that still differ follow the gaps of the figure they rest on. |
| Fig. 4, coverage under MAR | partly | 322 of 333 fields as printed | Nearly all points fall within binomial error; the misses are X3 coverage of the MI methods at 50 and 75%, where our MICE-PMM and MIX without truncating cover the true value more often than the paper's, as their X3 estimates in Fig. 2 are less biased. |
| Claims about Fig. 4 (coverage) | partly | 14 of 18 fields as printed, 1 paper errors | Each claim is computed from our figure values with the paper's thresholds (0.5 SE, 10% bias, 90% coverage, p = 0.05). Where the text disagrees with the paper's own figures and our run agrees with the figures, the field is a paper error and is not counted; the claims that still differ follow the gaps of the figure they rest on. |
| Fig. 5, mean p-values under MAR | partly | 295 of 333 fields as printed | Most misses are X6, whose mean p-value is lower in our run at every level and method, as its SE is 15% smaller (Fig. 3); the rest are scattered MI points for X2 to X5. |
| Claims about Fig. 5 (significance) | partly | 1 of 2 fields as printed, 2 paper errors | Each claim is computed from our figure values with the paper's thresholds (0.5 SE, 10% bias, 90% coverage, p = 0.05). Where the text disagrees with the paper's own figures and our run agrees with the figures, the field is a paper error and is not counted; the claims that still differ follow the gaps of the figure they rest on. |
| Fig. 6, model performance under MAR (LR p, R2, D, 2-year survival) | partly | 125 of 148 fields as printed | Two gaps. The pooled likelihood ratio p-values after MI are 10^-6 or smaller in our run against up to 0.0046 in the paper; no pooling rule we tried gives the paper's values. Complete-case R2, D and 2-year survival rise with missingness in our run (2-year survival 0.805 at 75% against 0.760): reversing X5's time term brings survival to 0.771 but leaves R2 and D high. |
| Claims about Fig. 6 (model performance) | partly | 5 of 7 fields as printed | Each claim is computed from our figure values with the paper's thresholds (0.5 SE, 10% bias, 90% coverage, p = 0.05). Where the text disagrees with the paper's own figures and our run agrees with the figures, the field is a paper error and is not counted; the claims that still differ follow the gaps of the figure they rest on. |
| Fig. 7, coefficients of X2 to X5 under MAR and MNAR | partly | 119 of 140 fields as printed | The MAR series match as in Fig. 2. Under MNAR our MI estimates of X3 and X4 are further from the truth than the paper's at 50 and 75% (X4 with MICE-PMM at 75%: -0.00049 against -0.00036), so the MNAR gap the paper reports is larger in our run. The scale of X3's own term does not explain it. |
| Fig. 8, coverage of X2 to X4 under MAR and MNAR | partly | 94 of 105 fields as printed | The misses are X3 coverage at 50 and 75%, following the X3 estimates of Fig. 7: under MNAR our MICE covers the true value in 12% of replicates at 75% against the paper's 33%; under MAR our MICE-PMM covers it more often (64% against 49%). |
| Claims about Figs 7 and 8 (MNAR against MAR) | partly | 7 of 10 fields as printed, 1 paper errors | Under MNAR X3 and X4 are more than 0.5 SE from the truth from 25% with every MI, as the paper says, and MICE-PMM without transformation reaches 0.5 SE under MAR only at 50%, as it says. The direction claims at 75% differ in places: our X3 is not further from the truth under MNAR for every method, X5 is not closer, and X2 coverage is not lower for every method; the paper's own Fig. 8 has X3 coverage higher under MNAR for two of three methods (a paper error). |
| MCAR and combined like MAR; NORM and MIX like MICE (Results text, not plotted) | partly | 1 of 4 fields as printed | The text judges 'no apparent differences' and 'indistinguishable' by eye; we set 0.25 SE (mechanisms) and 0.1 SE (methods). MIX is within 0.1 SE of MICE everywhere and NORM in 44 of 45 points (X5 at 75%: 0.17 SE). MCAR differs from MAR by more than 0.25 SE in 10% of the points, all of them X3 (up to 1.2 SE with MIX without truncating at 75%), with a median difference of 0.09 SE. |
| Main claim (Abstract and Conclusions): MICE-PMM least biased, fails from 50% and under MNAR | exact | 6 of 6 fields as printed |  |
| Claims recomputed from the paper's own figure values | agrees | 59 of 77 claim fields come back when computed from the paper's own figure values; not: text.fig2: SI more than 0.5 SE away for X2, X3 and X4 from 25% (figures give no); text.fig2: Most MI more than 0.5 SE away for X2, X3 and X4 from 25% (figures give no); text.fig2: X2 MICE: first level with bias over 10% (figures give 50); text.fig2: X2 MICE-PMM: first level with bias over 10% (figures give 50); text.fig2: X2 MICE-PMM no transformation: first level with bias over 10% (figures give 75); text.fig2: X2 aregImpute: first level with bias over 10% (figures give 50); text.fig2: X2 MIX no truncating: first level with bias over 10% (figures give 50); text.fig2: X3 MICE-PMM no transformation: first level with bias over 10% (figures give 75); text.fig2: X3 aregImpute: first level with bias over 10% (figures give 50); text.fig2: X5 bias over 10% at 50% with every MI (figures give no); text.fig2: X4: MICE-PMM no transformation least biased MI at 75% (figures give no); text.fig3: X2: every MI SE between SI and CC at 25 to 75% (figures give no); text.fig3: X3: every MI SE between SI and CC at 25 to 75% (figures give no); text.fig3: X4: CC SE rises by over 10% at 75%, SI and MI within 10% of full data (figures give no); text.fig4: X3 MICE-PMM no transformation: first level with coverage below 90% (figures give 75); text.fig5: CC X5: first level with p over 0.05 (figures give 75); text.fig5: CC X7: first level with p over 0.05 (figures give 75); text.mnar: X3 coverage lower under MNAR than MAR at 75%, every MI (figures give no) |  |
| Replicates rerun from scratch equal the committed results | agrees | 3 of 3 reruns from scratch equal the committed results: MAR replicate 1 (46 rows); MNAR replicate 1 (31 rows); true values replicate 1-200 (200 rows) |  |
| R package misscox and its tutorial | agrees | R CMD build ok; R CMD check: OK; testthat [ FAIL 0 | WARN 0 | SKIP 0 | PASS 19 ]; TUTORIAL.md same as the vignette rendered now |  |

4 exact, 7 agrees, 15 partly, 1 differs, 2 not attempted; 15 open causes.
OK results.json: {"items": 29, "exact": 4, "agrees": 7, "partly": 15, "inconclusive": 0, "differs": 1, "not_attempted": 2, "open_causes": 15}

## Replicates rerun from scratch

| Study | Replicate | Rows | Same as committed |
| --- | --- | --- | --- |
| MAR | 1 | 46 | yes |
| MNAR | 1 | 31 | yes |
| true values | 1-200 | 200 | yes |

## Package

R CMD build ok; R CMD check: OK; testthat [ FAIL 0 | WARN 0 | SKIP 0 | PASS 19 ]; TUTORIAL.md same as the vignette rendered now

## Fresh run against the committed outputs

| File | Fresh vs committed | Detail |
| --- | --- | --- |

0 of 0 files agree.

**FAIL**
