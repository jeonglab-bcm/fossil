# PMC2648748: A random forest approach to the detection of epistatic interactions (Jiang et al. 2009)

Jiang R, Tang W, Wu X, Fu W. A random forest approach to the detection of epistatic interactions in case-control
studies. *BMC Bioinformatics* 10(Suppl 1):S65 (2009).
[doi:10.1186/1471-2105-10-S1-S65](https://doi.org/10.1186/1471-2105-10-S1-S65) ·
[PMC2648748](https://pmc.ncbi.nlm.nih.gov/articles/PMC2648748/) · issue #60

The paper is © 2009 Jiang et al., licensee BioMed Central, under
[CC BY 2.0](https://creativecommons.org/licenses/by/2.0/). This folder does not contain the paper or its full
text; `figure-reproduction/published/` holds its Figs 2 and 3 (the images embedded in the paper's PDF) for
comparison, redistributed under CC BY 2.0 with the attribution above.

The authors' program, epiForest, was never released. We rebuilt it from the paper as the R package
[`package/`](package/) (`epiforest`): a random forest (R randomForest, the package the paper used) ranks the SNPs
by gini importance, the sliding window sequential forward feature selection (SWSFS) keeps the top candidates, and
hierarchical B-statistic tests report one-, two- and three-way associations. With it, and the paper's two
comparators, we reran the simulation study of Figs 2 and 3: three disease models, four MAFs and two r² values,
100 data sets of 1000 markers, 1000 cases and 1000 controls each (2,400 data sets).

| Folder | Content |
| --- | --- |
| [`figure-reproduction/`](figure-reproduction/) | Figs 2 and 3 read off the published images and compared with our study; the Nextflow pipeline, the per-data-set records, the hypothesis tests for every gap. |
| [`package/`](package/) | `epiforest`, the method as an installable R package with the paper's simulation design and comparators, example data, tests and an [executed tutorial](package/tutorial/TUTORIAL.md). |
| [`results.json`](results.json) | Every figure, table and claim of the paper, with our values and computed verdicts. |
| [`session/`](session/) | The ledger of the session that made this reproduction. It was not a fresh kickoff: its first prompt installed the skill, and a container restart midway stopped the simulation study, which resumed from its records. |

Results page: <https://jeonglab-bcm.github.io/fossil/PMC2648748/>

## Results

<!-- summary from results.json (check_results.py); the full table: python3 figure-reproduction/pipeline/check_results.py results.json --markdown -->

27 results: 2 exact, 3 agree, 5 partly agree, 2 inconclusive, 2 differ, 13 not attempted; 8 open causes.

| Result | Verdict | Ours against the paper |
| --- | --- | --- |
| Fig. 2, chi-squared | partly | 20 of 24 bars within Monte Carlo error; the four misses are model 3 at small MAF, where ours is higher (26 against 0 at r² = 0.7, MAF 0.05) |
| Fig. 2, stepwise logistic regression | partly | 17 of 24, with the stage-2 test chosen by its match to these bars (interaction terms, adjusted by all tests; 4 of 24 with Marchini et al.'s two-stage strategy as published) |
| Fig. 2, epiForest | partly | 15 of 24; above the paper where the signal is weak (r² = 0.7), below it where the paper's epiForest is far ahead of chi-squared (model 2, r² = 1, MAF 0.05: 2 against 16) |
| Fig. 2, the drawing | inconclusive | The pixel score cannot tell our bars from our bars shifted by 5 points; the values carry the comparison |
| Fig. 2, BEAM | not attempted | BEAM's program is gone |
| Fig. 3, SNPs selected by SWSFS | differs | 0 of 24 medians: ours 4 to 37 (median 32), the paper's 45 to 48 in every setting |
| Main claim: epiForest comparable to, sometimes better than, the other methods | partly | Never below chi-squared and above it in 5 settings; above logistic regression in 2, below it in 4 (small MAF) where the paper has it level or ahead |
| Other claims of the text | 2 exact, 1 partly, 1 differs | Model 1 alike (holds); SWSFS keeps fewer than 100 (holds); "epiForest best at small MAF" (partly); "about 45 SNPs" (32) |
| Claims against the paper's own figures | agrees | 14 of 14 statements follow from the published bars, Table 1 and text |
| The B statistic on null data | agrees | Our shift of the chi-squared gives the right mean and 5% tail for one- and two-way tests; three-way tests are conservative (2.8%) |
| Package | agrees | `R CMD check` OK; the tutorial rendered from the vignette is the committed one |
| AMD study (Figs 4 to 6, Table 1, 6 statements) | not attempted | The genotypes were never deposited |
| Fig. 1 | not attempted | A diagram of the method |

The main claim holds in part. epiForest is never below chi-squared, beats it where interactions matter (model 2),
and keeps far fewer candidates than stepwise logistic regression; in our run it falls below logistic regression in
4 of 24 settings at small MAF, where the paper has it level or ahead. The gaps trace to settings the paper does not
give: how it ran its forests (our first forest ranks a model-2 disease marker near 800 of 1000 at MAF 0.05; with
mtry = 100 the markers rank higher at MAF 0.1), how it simulated model 3 (our exact chi-squared power is above
its bars at small MAF; the documented readings of the disease tables cannot move model 3's marginal power, and
reading 0.7 as r overshoots the other way) and which stage-2 test its logistic regression used. Fig.
3's flat medians (45 to 48, median 46) are not reproduced by any of five tested readings of SWSFS. All of these are open, with
the tested candidates in `results.json`.

Kept local and gitignored: `sources/` (the paper's PDF and XML, its figures, epiMODE's Text S1), `work/` (the
study's chunks and logs, the hypothesis-test runs, Nextflow work folders) and `.venv/`.
