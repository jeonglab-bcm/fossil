# PMC4232638: Benchmarking mutation effect prediction algorithms (Martelotto et al. 2014)

Martelotto LG, Ng CKY, De Filippo MR, Zhang Y, Piscuoglio S, Lim RS, Shen R, Norton L, Reis-Filho JS,
Weigelt B. Benchmarking mutation effect prediction algorithms using functionally validated cancer-related
missense mutations. *Genome Biology* 15:484 (2014).
[doi:10.1186/s13059-014-0484-1](https://doi.org/10.1186/s13059-014-0484-1),
[PMC4232638](https://pmc.ncbi.nlm.nih.gov/articles/PMC4232638/), fossil issue
[#97](https://github.com/jeonglab-bcm/fossil/issues/97)

The paper is © 2014 Martelotto et al., licensee BioMed Central, under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); its data are released under the
[CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) waiver. This folder does not contain the paper,
its full text or its supplement. `figure-reproduction/published/` holds renders of Figs 1 to 4 and of
Additional files 4, 10, 12, 15, 20, 23, 24, 26 and 29, made from the PMC PDFs, for comparison; they are
redistributed under CC BY 4.0 with the attribution above. The package's example data are a subset of
Additional file 2 (CC0). The printed numbers of Tables 1 to 4 and of 20 supplement tables are in
`figure-reproduction/output/published_values.json`, read from the article XML and the supplement PDFs by
`extract_published.py`; the values drawn in the vector figures are in `figure-reproduction/output/figure_values.json`.

The paper scores 15 mutation effect predictors (CHASM breast, lung and melanoma; FATHMM cancer and missense;
Mutation Assessor; MutationTaster; PolyPhen-2; PROVEAN; SIFT; VEST; CanDrA breast, lung and melanoma; Condel)
on 3,591 cancer SNVs, 989 of them with a known effect (849 non-neutral, 140 neutral): accuracy, sensitivity,
specificity, PPV, NPV and a composite score with bootstrap intervals, Cohen's kappa between predictors, a
clustering of their calls, a low-confidence category, and 11,253 "at least p of n" combinations of the 11
single predictors scored over 1,000 random two-thirds / one-third splits. The predictors' calls are frozen
in Additional file 2; the statistics code was never released. We rebuilt every analysis from the text as
the Python package [`package/`](package/) (`mutbench`), reran it on Additional file 2 and compared every
table, figure and supplement file with the published one.

| Folder | Content |
| --- | --- |
| [`figure-reproduction/`](figure-reproduction/) | The Nextflow pipeline: the downloads, the published values, the analysis, the comparison, the figures drawn on the published frames, the checks. |
| [`package/`](package/) | `mutbench`, the method as an installable Python package, with example data, tests and an [executed tutorial](package/tutorial/TUTORIAL.md). |
| [`results.json`](results.json) | Every figure, table and claim of the paper and its supplement, with our values and computed verdicts. |
| [`session/`](session/) | The ledger of the session that made this reproduction. |

Results page: <https://jeonglab-bcm.github.io/fossil/PMC4232638/>

## Results

<!-- summary from results.json (check_results.py); the full table, with the causes: figure-reproduction/README.md -->

<!--RESULTS-SUMMARY-->
9 exact, 40 agrees, 23 partly, 1 differs, 2 not attempted; 3 open causes.

| Item | Verdict | Measure |
| --- | --- | --- |
| Table 1, SNVs by gene and functional category | exact | 64 of 64 fields as printed |
| Table 2, calls of the 15 predictors by functional category | exact | 160 of 160 fields as printed |
| Table 3, performance on the 989 labelled SNVs (point values) | agrees | 90 of 90 fields as printed |
| Table 3, bootstrap 95% intervals | agrees | 180 of 180 fields as printed |
| Table 4, performance on the 297 labelled non-COSMIC SNVs (point values) | agrees | 90 of 90 fields as printed |
| Table 4, bootstrap 95% intervals | partly | 179 of 180 fields as printed |
| Fig. 1A, clustering of the calls of all 3,591 SNVs (clades, join heights, row shares) | agrees | 71 of 71 fields as printed |
| Fig. 1B, kappa of each pair of predictors, all SNVs (cell colours) | agrees | 225 of 225 fields as printed |
| Fig. 1C, clustering of the calls of the 1,699 non-COSMIC SNVs | agrees | 71 of 71 fields as printed |
| Fig. 1D, kappa of each pair of predictors, non-COSMIC SNVs (cell colours) | agrees | 225 of 225 fields as printed |
| Fig. 2A, performance on the 989 labelled SNVs (bars) | agrees | 90 of 90 fields as printed |
| Fig. 2A, error bars | agrees | 176 of 176 fields as printed |
| Fig. 2B, performance on the 297 non-COSMIC SNVs (bars) | agrees | 90 of 90 fields as printed |
| Fig. 2B, error bars | agrees | 176 of 176 fields as printed |
| Fig. 3A, top five combinations by composite score, all SNVs, subset 1 (names, bars, error bars, significance marks) | agrees | 151 of 151 fields as printed |
| Fig. 3B, top five combinations by composite score, all SNVs, subset 2 (names, bars, error bars, significance marks) | partly | 147 of 151 fields as printed |
| Fig. 3C, top five combinations by composite score, non-COSMIC SNVs, subset 1 (names, bars, error bars, significance marks) | partly | 144 of 151 fields as printed |
| Fig. 3D, top five combinations by composite score, non-COSMIC SNVs, subset 2 (names, bars, error bars, significance marks) | partly | 144 of 151 fields as printed |
| Fig. 4A, how often each predictor is in the top 10, 20, 50 and 100 combinations, all SNVs | partly | 74 of 88 fields as printed |
| Fig. 4B, the same for the non-COSMIC SNVs | partly | 43 of 88 fields as printed |
| Additional file 3, kappa and its interval for every pair of predictors (all and non-COSMIC SNVs) | agrees | 720 of 720 fields as printed |
| Additional file 5, kappa for the 989 labelled and the 297 labelled non-COSMIC SNVs | agrees | 720 of 720 fields as printed |
| Additional file 8, three-category calls (with low confidence) by functional category | agrees | 379 of 379 fields as printed, 5 paper errors |
| Additional file 9, SNVs by number of low-confidence calls, and those with eight or more | agrees | 67 of 67 fields as printed, 1 paper errors |
| Additional file 11, kappa with the low-confidence category (all and non-COSMIC SNVs) | agrees | 720 of 720 fields as printed |
| Additional file 13, kappa with the low-confidence category (989 and 297 labelled SNVs) | agrees | 720 of 720 fields as printed |
| Additional file 16, performance in oncogenes (176 SNVs) and tumour suppressor genes (783) | agrees | 180 of 180 fields as printed |
| Additional file 16, bootstrap 95% intervals | partly | 352 of 360 fields as printed |
| Additional file 17, all 11,253 combinations on the 989 labelled SNVs (means and intervals in both subsets) | agrees | 135,036 of 135,036 means (11,253 combinations x 6 statistics x 2 subsets) within the printed precision plus three Monte Carlo standard deviations; 268,491 of 270,072 interval ends within three times the run-to-run spread. Control: our run on the other data set puts 10,831 of 135,036 means within. |
| Additional file 18, all 11,253 combinations on the 297 labelled non-COSMIC SNVs | agrees | 135,036 of 135,036 means (11,253 combinations x 6 statistics x 2 subsets) within the printed precision plus three Monte Carlo standard deviations; 268,138 of 270,072 interval ends within three times the run-to-run spread. Control: our run on the other data set puts 10,530 of 135,036 means within. |
| Additional file 19, combinations that beat the best single and meta-predictor | partly | 52 of 144 fields as printed |
| Additional file 21, top five combinations by accuracy and by composite score, 989 SNVs | partly | 385 of 388 fields as printed |
| Additional file 22, top five combinations, 297 non-COSMIC SNVs | partly | 370 of 388 fields as printed |
| Additional file 25, optimal p for each n and n for each p, 989 SNVs | partly | 41 of 42 fields as printed |
| Additional file 27, optimal p and n, 297 non-COSMIC SNVs | partly | 37 of 42 fields as printed |
| Additional file 28, training-set SNVs left among the labelled SNVs | exact | 12 of 12 fields as printed |
| Additional file 4, kappa heat maps for the 989 and the 297 labelled SNVs (cell colours; the call heat maps and dendrograms are not compared) | agrees | 450 of 450 fields as printed |
| Additional file 6, the 1,699 non-COSMIC SNVs by gene and functional category | exact | 64 of 64 fields as printed |
| Additional file 7, calls of the 15 predictors on the 1,699 non-COSMIC SNVs | exact | 158 of 158 fields as printed, 2 paper errors |
| Additional file 10, kappa heat maps with the low-confidence category, all and non-COSMIC SNVs (cell colours) | agrees | 450 of 450 fields as printed |
| Additional file 12, kappa heat maps with the low-confidence category, 989 and 297 labelled SNVs (cell colours) | agrees | 450 of 450 fields as printed |
| Additional file 14, calls on the 989 labelled SNVs by gene class | exact | 240 of 240 fields as printed |
| Additional file 15A, performance in oncogenes (bars) | agrees | 90 of 90 fields as printed |
| Additional file 15A, error bars | partly | 167 of 172 fields as printed |
| Additional file 15B, performance in tumour suppressor genes (bars) | agrees | 90 of 90 fields as printed |
| Additional file 15B, error bars | agrees | 174 of 174 fields as printed |
| Additional file 20A, top five combinations by accuracy, all SNVs, subset 1 | partly | 150 of 151 fields as printed |
| Additional file 20B, top five combinations by accuracy, all SNVs, subset 2 | partly | 150 of 151 fields as printed |
| Additional file 20C, top five combinations by accuracy, non-COSMIC SNVs, subset 1 | partly | 149 of 151 fields as printed |
| Additional file 20D, top five combinations by accuracy, non-COSMIC SNVs, subset 2 | partly | 143 of 151 fields as printed |
| Additional file 23A, how often each predictor is in the top combinations by accuracy, all SNVs | partly | 63 of 88 fields as printed |
| Additional file 23B, the same for the non-COSMIC SNVs | partly | 45 of 88 fields as printed |
| Additional file 24, box plots of the combinations' accuracy by n and p, 989 SNVs (hinges and medians) | partly | 382 of 390 fields as printed |
| Additional file 26, the same box plots for the 297 non-COSMIC SNVs | agrees | 390 of 390 fields as printed |
| Additional file 29, performance of six predictors on all, non-COSMIC and non-training-set SNVs (bars) | agrees | 108 of 108 fields as printed |
| Additional file 29, error bars | agrees | 216 of 216 fields as printed |
| Dataset sizes and SNVs per gene class (Results) | exact | 14 of 14 fields as printed |
| Calls of VEST and PROVEAN (Results) | exact | 4 of 4 fields as printed |
| Kappa within and between the two clusters, all SNVs (Results) | agrees | 10 of 10 fields as printed |
| Cluster 1 median kappa without COSMIC SNVs (Results) | agrees | 1 of 1 fields as printed |
| SNVs not in COSMIC v68 (Results) | exact | 5 of 5 fields as printed |
| Cluster structure of Fig. 1A, 1C and Additional file 4 (Results) | agrees | 5 of 5 fields as printed |
| Low-confidence calls (Results) | agrees | 6 of 6 fields as printed, 1 paper errors |
| Medians, ranges and significance calls of Table 3 (Results) | partly | 26 of 27 fields as printed |
| Table 4 and the loss of accuracy without COSMIC SNVs (Results) | partly | 10 of 12 fields as printed |
| Oncogenes against tumour suppressor genes (Results) | agrees | 14 of 14 fields as printed |
| The combinations against FATHMM (cancer) and CHASM (lung), and the best combination (Results) | partly | 16 of 19 fields as printed |
| The best combination's NPV gain in every subset (Results, Discussion) | agrees | 4 of 4 fields as printed |
| MutationTaster and CHASM (breast, lung) lead the top combinations (Results, Fig. 4) | agrees | 16 of 16 fields as printed |
| Removing COSMIC or training-set SNVs never raises accuracy significantly (Discussion) | agrees | 12 of 12 fields as printed |
| Optimal n and p (Results) | differs | 0 of 0 fields as printed, 2 paper errors |
| The text's statements recomputed from the paper's own tables (arithmetic check) | agrees | 133 of 135 statements recomputed from the paper's own tables come back. Not: text.optimal: for n = 1 to 4, the best p is about 2n (printed yes, from the tables no); text.optimal: for p = 3 to 11, the best n is about p/2 (printed yes, from the tables no). Fig. 4 recomputed from the means printed in Additional files 17 and 18: 173 of 176 points. |
| Additional file 1, overview of the predictors | not attempted | not attempted |
| The authors' statistical code | not attempted | not attempted |
| Python package mutbench and its tutorial | agrees | mutbench 0.1.0: wheel installed in a fresh environment and imported from it; tests 9 passed; tutorial 7 cells compared, 0 skipped (nondeterministic); TUTORIAL.md in sync |
<!--/RESULTS-SUMMARY-->

"Exact" means every value as printed. "Agrees" means every value matches, with a setting the paper does not
state found by trying the alternatives (how a missing call enters the statistics, the bootstrap, the
low-confidence end points), or with values read from a figure, or within the Monte Carlo spread of our own
repeat runs for results that come from random resampling (fixed before the comparison: three standard
deviations of the run-to-run difference, plus half a printed unit).

## What came back

- **The data and the counts.** Tables 1 and 2 and Additional files 6 and 14 count by count, from the paper's
  spreadsheet, and Additional file 7 apart from its own slip (below).
- **Each predictor.** Every point value of Tables 3 and 4 and of Additional file 16 (oncogenes and tumour
  suppressor genes), once a call the predictor did not make is left out of its counts. The bootstrap
  intervals are percentile intervals of unstratified resamples: all 180 interval ends of Table 3 and 179 of 180
  of Table 4 come back within the spread of our own repeats. In the oncogenes (7 neutral SNVs) 8 of 360 ends of
  Additional file 16 miss, three of them in a way no seed of ours reproduces (an open cause).
- **Agreement between predictors.** All 2,880 kappa values and interval ends of Additional files 3, 5, 11 and 13,
  to the fourth significant digit, once a missing call is kept as a third category and the interval is
  kappa +/- 1.96 standard errors under no agreement. The dendrograms of Fig. 1 have our clades and our
  join heights, and every cell of the kappa heat maps of Fig. 1 and Additional files 4, 10 and 12 has our colour.
- **Low confidence.** Every count of Additional file 9 and the 27 SNVs with eight or more low-confidence calls, and
  Additional file 8 apart from its own slip (below), with the interval end points included and a missing call
  counted as low confidence.
- **The combinations.** Every one of the 11,253 x 6 x 2 means of Additional files 17 and 18 within the Monte
  Carlo spread, and the best combination, at least 1 of CHASM (breast) and MutationTaster, first by accuracy and
  by composite score in both subsets, with an NPV significantly above the best single and meta-predictor in every
  subset.

## What does not match, and why

- **Random splits.** The combinations were scored over 1,000 random splits whose seeds are unknown. Means come
  back; rankings of combinations whose means differ by less than the Monte Carlo error do not always (Figs 3
  and 4, Additional files 20 to 25 and 27), nor do counts of combinations near a cutoff (Additional file 19).
  Our second run, with another seed, differs from our first about as much as from the paper. Recomputed from
  the means the paper itself prints in Additional files 17 and 18, Fig. 4 comes back for 173 of 176 points.
- **Two sentences on the optimal n and p** swap n and p: the paper's own Additional file 25 gives a best n of about
  2p, as our run does, where the text says p is about 2n and n about p/2.
- **Four slips in the supplement.** Additional file 7's PolyPhen-2 rows add up to 1,698 of 1,699 SNVs; Additional
  file 8 leaves out Mutation Assessor's N/A calls (7, and 2 without COSMIC), which Additional file 9 counts as low
  confidence; Additional file 9 lists PIK3CA G451V under ERBB2; Additional file 2 swaps the headers of FATHMM's two
  training-set columns, which we read by their content.
- **One significance call.** Without COSMIC SNVs, the paper finds the accuracy of 13 predictors significantly lower;
  from its own intervals that comes back, but our run finds 12 (CanDrA (melanoma) not), and only 2 of our 20 repeat
  bootstraps find 13. Open.

The main finding holds: no single predictor is accurate enough, the cancer-specific predictors agree more with
each other than the others do, and combining CHASM (breast) with MutationTaster ranks first by accuracy and
composite score in both subsets, with an NPV significantly above the best single and meta-predictor. Most
claims that do not match move with the random splits or resamples; one significance call does not come back
for a reason we have not found; two sentences are the paper's own slip.

## Run

```bash
pip install -r PMC4232638/figure-reproduction/requirements.txt ./PMC4232638/package
nextflow run PMC4232638/figure-reproduction/main.nf --outdir results
```

It needs Python 3.12, poppler-utils (`pdftotext`), Java 21 and Nextflow, and takes about 90 seconds on four
cores. See [`figure-reproduction/README.md`](figure-reproduction/README.md).
