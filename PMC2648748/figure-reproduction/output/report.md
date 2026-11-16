# PMC2648748 reproduction check

## results.json

| Item | Verdict | Measure | Why |
| --- | --- | --- | --- |
| Fig. 1, the two stages of epiForest | not attempted | not attempted | A diagram of the method; it holds no data. The method it shows is the package epiforest. |
| Fig. 2, power of epiForest (24 bars) | partly | 15 of 24 fields as printed | 15 of 24 bars within Monte Carlo error. Where the signal is weak (r2 = 0.7, models 2 and 3, MAF 0.05 to 0.2) ours is higher, as our chi-squared is in model 3; where the paper's epiForest is far ahead of chi-squared (models 2 and 3, r2 = 1, MAF 0.05 and 0.1) ours is lower: 2 against 16, 38 against 57, 87 against 97, 72 against 89. There our first forest ranks a disease marker low (model 2, MAF 0.05: the lower one at rank 800 in median), so neither SWSFS nor the B tests see it. The paper's forest settings are not given; mtry = 100 ranks the markers higher at MAF 0.1 but not at MAF 0.05. |
| Fig. 2, power of BEAM (24 bars) | not attempted | not attempted | BEAM 1.0 (Zhang and Liu 2007) was distributed only as a binary from the authors' Harvard page, which now answers 403; the Pasteur mirror keeps only its README, and the Wayback Machine could not be reached from this session. BEAM3 and StrBEAM are other methods. Rebuilding BEAM's MCMC was out of scope. |
| Fig. 2, power of stepwise logistic regression (24 bars) | partly | 17 of 24 fields as printed | With the reading that fits best (interaction terms in stage 2, adjusted by all tests; found by search) 17 of 24 bars within Monte Carlo error. Four misses are model 3 at small MAF, where our chi-squared is above the paper's as well; the other three are model 2 (22 against 10 at r2 = 0.7, MAF 0.2; 26 against 8 and 56 against 32 at r2 = 1, MAF 0.05 and 0.1). The paper does not say which models stage 2 compares or how it is adjusted. |
| Fig. 2, power of the chi-squared test (24 bars) | partly | 20 of 24 fields as printed | 20 of 24 bars within Monte Carlo error; all four misses are model 3 at small MAF, where our chi-squared power is higher than the paper's (r2 = 0.7: 26, 72, 99 against 0, 11, 79 at MAF 0.05, 0.1, 0.2; r2 = 1: 64 against 48 at MAF 0.05). The exact power of our model (no simulation) gives the same values, so the gap is in how the paper simulated model 3 or the LD, which it does not state; the documented table, scale and prevalence readings leave model 3's marginal power unchanged, and reading 0.7 as r overshoots in the other direction. |
| Fig. 2, the figure (pixels, BEAM bars masked) | inconclusive | 68.58% within 2 px (pass 85.8%, best control 71.5%) | The pixel score (68.6% of our ink near the paper's) is no better than our own bars shifted by 5 power points (71.5%), a shift within Monte Carlo error, so the drawing cannot settle the comparison; the bar values do (fig2.epiforest, fig2.lr, fig2.chisq). Both wrong-input controls score lower (22.6%, 49.1%). |
| Fig. 3, median number of SNPs SWSFS selects (24 boxes) | differs | 0 of 24 fields as printed | None of the 24 medians within error: ours run from 4 to 37 (median 32) and fall where the signal is strong, the paper's are flat at 45 to 48 in every setting. Returning the top i instead of the top i - w (i = k + 20, the number of forests built, which is how the AMD text's 84 SNPs and 104 forests relate) brings 16 of 24 within error but not the strong-signal settings (25.5 and 24 against 45 and 46). Which count the paper plotted, and with what forests, is not stated. |
| Fig. 3, the figure (pixels) | inconclusive | 16.39% within 2 px (pass 58.9%, best control 17.8%) | The pixel score (16.4%) is no better than our boxes shifted by 2 SNPs (17.8%); the boxes sit about 14 SNPs below the paper's and are not flat across settings (fig3.medians). |
| Text: all methods perform alike in model 1 | exact | 1 of 1 fields as printed |  |
| Text: in models 2 and 3 epiForest beats logistic regression and chi-squared at small MAF, where chi-squared does poorly | partly | 2 of 4 fields as printed | Chi-squared is the lowest of the three at small MAF, as in the paper; epiForest is not above logistic regression there (model 2, r2 = 1: 2 and 38 against 26 and 56; model 3: 72 and 99 against 100 and 100), because our epiForest is below the paper's in these settings (fig2.epiforest). |
| Main claim: epiForest's power is comparable to, sometimes higher than, the other methods' | partly | 3 of 4 fields as printed | epiForest is never below chi-squared and is above it beyond Monte Carlo error in 5 settings, as the paper says, and above logistic regression in 2 (model 2, MAF 0.2: 44 against 22 at r2 = 0.7, 87 against 62 at r2 = 1). It is below logistic regression beyond Monte Carlo error in 4 of 24 settings (models 2 and 3 at MAF 0.05 or 0.1), where the paper has it level or above: in each of them our epiForest is below the paper's or our logistic regression above it (fig2.epiforest, fig2.lr). |
| Text: SWSFS selects about 45 SNPs in every setting, generally fewer than 80 | differs | 0 of 2 fields as printed | Our SWSFS selects a median of about 32 SNPs, not 45 (fig3.medians), and 17 of 24 settings have every selection below 80, not all 24. The claim that SWSFS keeps far fewer SNPs than the 100 of stepwise logistic regression holds (text.swsfs_below_eps). |
| Text: SWSFS keeps fewer candidates than the 100 (10%) of stepwise logistic regression | exact | 1 of 1 fields as printed |  |
| Text: BEAM beats logistic regression and chi-squared; epiForest and BEAM alike | not attempted | not attempted | Needs BEAM's power, which we could not compute (fig2.beam). On the paper's own figure the claim holds (text.arithmetic). |
| Claims about Figs 2 and 3 against the paper's own figure values | agrees | 14 of 14 statements about Fig. 2 and the AMD study follow from the paper's own bars, Table 1 and text; Fig. 3's published medians run from 44.94 to 48.02 (about 45: yes) and 24 of 24 maxima are below 80; epiForest is at or above logistic regression in 21 of 24 settings | Assumed: Published bar heights and box medians read off the figures (read_published.py) |
| Text: AMD data, 116,204 SNPs, 96 cases, 50 controls; 95,986 SNPs after filtering | not attempted | not attempted | The AMD genotypes (Klein et al. 2005, Affymetrix 100K, 96 cases and 50 controls) came from J. Hoh and were never deposited; the AREDS scan in dbGaP (phs000001) has controlled access, and whether it holds the same 146 people is unverified. |
| Fig. 4, gini importance of the AMD SNPs | not attempted | not attempted | The AMD genotypes (Klein et al. 2005, Affymetrix 100K, 96 cases and 50 controls) came from J. Hoh and were never deposited; the AREDS scan in dbGaP (phs000001) has controlled access, and whether it holds the same 146 people is unverified. |
| Text: largest gini importance rs380390 (2.73) and rs1329428 (2.44) | not attempted | not attempted | The AMD genotypes (Klein et al. 2005, Affymetrix 100K, 96 cases and 50 controls) came from J. Hoh and were never deposited; the AREDS scan in dbGaP (phs000001) has controlled access, and whether it holds the same 146 people is unverified. |
| Text: Bonferroni-corrected chi-squared p 0.0043 (rs380390) and 0.14 (rs1329428) | not attempted | not attempted | The AMD genotypes (Klein et al. 2005, Affymetrix 100K, 96 cases and 50 controls) came from J. Hoh and were never deposited; the AREDS scan in dbGaP (phs000001) has controlled access, and whether it holds the same 146 people is unverified. |
| Fig. 5, gini importance against the B-statistic p-value (AMD) | not attempted | not attempted | The AMD genotypes (Klein et al. 2005, Affymetrix 100K, 96 cases and 50 controls) came from J. Hoh and were never deposited; the AREDS scan in dbGaP (phs000001) has controlled access, and whether it holds the same 146 people is unverified. |
| Text: Pearson correlation of gini importance and p-value -0.59, p < 2.2e-16 | not attempted | not attempted | The AMD genotypes (Klein et al. 2005, Affymetrix 100K, 96 cases and 50 controls) came from J. Hoh and were never deposited; the AREDS scan in dbGaP (phs000001) has controlled access, and whether it holds the same 146 people is unverified. |
| Fig. 6, out-of-bag error against the number of top SNPs (AMD) | not attempted | not attempted | The AMD genotypes (Klein et al. 2005, Affymetrix 100K, 96 cases and 50 controls) came from J. Hoh and were never deposited; the AREDS scan in dbGaP (phs000001) has controlled access, and whether it holds the same 146 people is unverified. |
| Text: minimum OOB error 8.5% at the top 84 SNPs; SWSFS builds 104 forests | not attempted | not attempted | The AMD genotypes (Klein et al. 2005, Affymetrix 100K, 96 cases and 50 controls) came from J. Hoh and were never deposited; the AREDS scan in dbGaP (phs000001) has controlled access, and whether it holds the same 146 people is unverified. |
| Table 1, top five two-way and three-way interactions in AMD | not attempted | not attempted | The AMD genotypes (Klein et al. 2005, Affymetrix 100K, 96 cases and 50 controls) came from J. Hoh and were never deposited; the AREDS scan in dbGaP (phs000001) has controlled access, and whether it holds the same 146 people is unverified. |
| Text: no interaction significant after Bonferroni; 9 and 14 SNPs more significant than rs6104678 and rs7863587 | not attempted | not attempted | The AMD genotypes (Klein et al. 2005, Affymetrix 100K, 96 cases and 50 controls) came from J. Hoh and were never deposited; the AREDS scan in dbGaP (phs000001) has controlled access, and whether it holds the same 146 people is unverified. |
| Check: the B statistic's null distribution (our shift of the chi-squared) | agrees | one-way: mean 2.01 (df 2), p<0.05 in 4.9%; two-way: mean 7.85 (df 8), p<0.05 in 4.8%; two-way given 1: mean 5.84 (df 6), p<0.05 in 4.7%; three-way: mean 22.89 (df 26), p<0.05 in 2.8%; three-way given 1: mean 20.83 (df 24), p<0.05 in 2.8%; three-way given 2: mean 15.01 (df 18), p<0.05 in 2.6% (200 null data sets) |  |
| R package epiforest and its tutorial | agrees | R CMD check: Status: OK; 9 testthat blocks; vignette rebuilt; TUTORIAL.md rendered from it is the committed one |  |

2 exact, 3 agrees, 5 partly, 2 inconclusive, 2 differs, 13 not attempted; 8 open causes.
OK results.json: {"items": 27, "exact": 2, "agrees": 3, "partly": 5, "inconclusive": 2, "differs": 2, "not_attempted": 13, "open_causes": 8}

## Data sets rerun from scratch

| Setting | Data set | SNPs selected | Same as committed |
| --- | --- | --- | --- |
| model 1, MAF 0.05, r2 0.7 | 1 | 18 | yes |
| model 3, MAF 0.2, r2 1.0 | 1 | 51 | yes |
| model 2, MAF 0.1, r2 1.0 | 7 | 58 | yes |

## Inputs

The paper's PDF: downloaded; Figs 2 and 3 from it are the committed copies: yes

## Package

R CMD check: Status: OK; 9 testthat blocks; vignette rebuilt; TUTORIAL.md rendered from it is the committed one

## Fresh run against the committed outputs

| File | Fresh vs committed | Detail |
| --- | --- | --- |
| comparison.json | same |  |
| published_values.json | same |  |
| summary.json | same |  |
| checks/bstat_null.json | same |  |
| checks/error_variants.json | same |  |
| checks/model_variants.json | same |  |
| checks/rank_variants.json | same |  |

7 of 7 files agree.

Renders and controls, inside the scored frames (text outside them depends on the font rasterizer):

| File | Inside the scored frames | Pixels compared |
| --- | --- | --- |
| fig2_ours.png | same | 974274 |
| fig2_overlay.png | same | 974274 |
| fig3_ours.png | same | 1370334 |
| fig3_overlay.png | same | 1370334 |
| controls/fig2_minus5.png | same | 974274 |
| controls/fig2_plus5.png | same | 974274 |
| controls/fig2_wrong_model.png | same | 974274 |
| controls/fig2_wrong_r2.png | same | 974274 |
| controls/fig3_minus2.png | same | 1370334 |
| controls/fig3_plus2.png | same | 1370334 |
| controls/fig3_wrong_model.png | same | 1370334 |

**PASS**
