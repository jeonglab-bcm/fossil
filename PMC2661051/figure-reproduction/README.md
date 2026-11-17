# PMC2661051 figure reproduction

Ackermann and Strimmer (2009), every table and figure with computed results: Tables 2 to 7 and Figs 2
to 4, from the R package `gseamod` ([`../package`](../package)), which rebuilds the paper's modules from
its text. The paper is CC BY 2.0; `published/` holds its Figs 2 to 4 for comparison (see
[`../README.md`](../README.md)).

## Results

<!-- full table from ../results.json (check_results.py --markdown); do not edit by hand -->
<!--RESULTS-TABLE-->
19 exact, 7 agrees, 9 partly, 6 differs, 5 not attempted; 11 open causes.

| Item | Verdict | Measure | Why |
| --- | --- | --- | --- |
| Table 1, methods in the literature | not attempted | not attempted | A list of published methods and their references; nothing to compute. |
| Fig. 1, the five modules | not attempted | not attempted | A diagram of the framework; it is the structure of the package gseamod. |
| Text: 3 x 5 x 6 x 3 - 9 = 261 variants | exact | 1 of 1 fields as printed |  |
| Table 2, gene-level statistic x transformation (mean, resampling) | agrees | 135 of 135 fields as printed | Assumed: The binary transformation calls a gene at two-sided p <= 0.05 (t distribution for t and mod.t, Fisher's z for correlations) |
| Table 3, gene set statistics (squared mod.t, resampling) | partly | 51 of 54 fields as printed | 51 of 54 rates agree. Cond. FDR misses sets 8 and 9 (0.53 and 0.84 against 0.84 and 0.99) and ES misses set 8 (0.44 against 0.65): the paper does not define its cond. FDR statistic or its ES ordering on squared scores. |
| Table 4, significance assessment (mean of squared mod.t) | exact | 36 of 36 fields as printed |  |
| Table 5, globaltest | partly | 35 of 36 fields as printed | 35 of 36 rates agree. The parametric false positive rate of set 3 is 0.13 in our 100 data sets against 0.02; on 400 more data sets it is 0.050, so the 0.13 is chance in our sample (the same data sets also give 0.12 by permutation). |
| Table 6, Hotelling T2 with a shrinkage correlation | partly | 25 of 27 fields as printed | 25 of 27 rates agree. Set 1 is found more often than in the paper (0.25 against 0.09 by resampling and 0.25 against 0.08 by restandardization): the paper does not say how its shrinkage correlation was estimated. |
| Text check: Tables 2, 3 and 4 print the same squared mod.t / mean / resampling cell | exact | 9 of 9 fields as printed |  |
| Text: untransformed statistics miss sets 6 to 9 | exact | 1 of 1 fields as printed |  |
| Text: squaring finds sets 6 to 9 | exact | 1 of 1 fields as printed |  |
| Text: squaring lowers sets 1, 2, 4 and 5 slightly | exact | 1 of 1 fields as printed |  |
| Text: rank squared performs best overall | agrees | 1 of 1 fields as printed | Assumed: The binary transformation calls a gene at two-sided p <= 0.05 (t distribution for t and mod.t, Fisher's z for correlations) |
| Text: (rank) squared beats binary and local fdr | agrees | 1 of 1 fields as printed | Assumed: The binary transformation calls a gene at two-sided p <= 0.05 (t distribution for t and mod.t, Fisher's z for correlations) |
| Text: median and Wilcoxon beat the mean on correlated sets | exact | 1 of 1 fields as printed |  |
| Text: with permutation that advantage vanishes (data not shown) | exact | 1 of 1 fields as printed |  |
| Text: ES is weaker than the mean | exact | 1 of 1 fields as printed |  |
| Text: the parametric null gives the best rates | exact | 1 of 1 fields as printed |  |
| Text: restandardization performs like resampling | exact | 1 of 1 fields as printed |  |
| Text: permutation detects uncorrelated sets more easily | exact | 1 of 1 fields as printed |  |
| Text: globaltest is very close to the mean of squared statistics | differs | 0 of 1 fields as printed | Our largest difference is 0.06 (set 9, restandardization: 0.86 against 0.92), against the 0.05 we took as close; the paper's own tables differ by at most 0.04. Both are within Monte Carlo error of two shares of 100. |
| Text: Hotelling hardly detects the correlated sets | exact | 1 of 1 fields as printed |  |
| Text: Hotelling improves with permutation | exact | 1 of 1 fields as printed |  |
| Text: p53 data, 50 cell lines, 8,768 genes, 290 sets of 15 to 321 genes | agrees | 8 of 8 fields as printed | Assumed: p53 genes from GSEA's collapsed-symbol file (10,100 genes), kept when the maximum is at least 5 on the log2 scale and the max/min ratio is at least 2 (both criteria), then log2 |
| Fig. 2 left, significant p53 sets against the cutoff | not attempted | not attempted | Drawn and overlaid, not scored: sixteen curves with letter markers overlap, so their values cannot be read off the figure. The cutoff 0.01 is scored through the right panel, and the ranking claims are scored as text. |
| Fig. 2 right, p53 sets with p <= 0.01 | partly | 9 of 16 fields as printed | 9 of 16 bars within one set: Hotelling (32 and 35 against 33 and 35), globaltest, ES and maxmean come back. Cond. FDR finds 10 and 7 sets against 38 and 35 (our cond. FDR is not the paper's, as in Table 3); Wilcoxon and median differ by 3 to 5 sets. |
| Text: p53, Hotelling and cond. FDR find the most sets (resampling) | differs | 0 of 1 fields as printed | Hotelling finds the most sets as in the paper, but our cond. FDR finds few (see Fig. 2 right). |
| Text: p53, Hotelling and cond. FDR find the most sets (permutation) | differs | 0 of 1 fields as printed | Hotelling finds the most sets as in the paper, but our cond. FDR finds few (see Fig. 2 right). |
| Text: p53, ES, median and Wilcoxon find the fewest sets (resampling) | differs | 0 of 1 fields as printed | Our cond. FDR (10 sets) falls among the three lowest; without it median, Wilcoxon and ES are the three lowest as in the paper. |
| Text: p53, ES, median and Wilcoxon find the fewest sets (permutation) | differs | 0 of 1 fields as printed | Our cond. FDR (7 sets) falls among the three lowest; without it median, Wilcoxon and ES are the three lowest as in the paper. |
| Fig. 3 top, mean pairwise correlation of the 290 p53 sets | partly | 8 of 31 fields as printed | 8 of 31 bins equal: our correlations are lower (median 0.022 against about 0.03 in the paper, 6 sets below -0.01 where the paper has none). The paper does not say on which data the correlations were computed. |
| Fig. 3 bottom, mean absolute pairwise correlation | partly | 11 of 40 fields as printed | 11 of 40 bins equal; our histogram sits about 0.005 lower (median 0.160 against about 0.166). |
| Text: correlations within p53 sets are comparatively weak | agrees | 1 of 1 fields as printed | Assumed: p53 genes from GSEA's collapsed-symbol file (10,100 genes), kept when the maximum is at least 5 on the log2 scale and the max/min ratio is at least 2 (both criteria), then log2 |
| Text: Hedenfalk data, 7 BRCA1 and 8 BRCA2, 2,200 mapped genes, 89 sets | partly | 3 of 5 fields as printed | Samples and array size agree; we map 2,233 genes (2,200 in the paper) and keep 84 sets (89). The paper's UniGene build and set selection are not given. |
| Fig. 4 left, significant Hedenfalk sets against the cutoff | not attempted | not attempted | Drawn and overlaid, not scored, as Fig. 2 left: the overlapping letter markers cannot be read. |
| Fig. 4 right, Hedenfalk sets with p <= 0.01 | partly | 1 of 16 fields as printed | 1 of 16 bars equal. The pattern comes back (resampling finds few sets, permutation many; Hotelling, mean, maxmean and globaltest highest; cond. FDR none by permutation), but our counts are higher: mean 56 against 41 by permutation, 8 against 0 by resampling. Our gene mapping and set catalogue differ from the paper's (84 sets, not 89). |
| Text: Hedenfalk, resampling finds very few sets | differs | 0 of 1 fields as printed | Our resampling finds 2 to 9 sets per statistic at 0.01 against 0 or 1 in the paper; few compared with permutation, but more than 2. |
| Text: Hedenfalk, Hotelling, mean, maxmean and globaltest find the most sets | exact | 1 of 1 fields as printed |  |
| Text: Hedenfalk, cond. FDR is conservative | exact | 1 of 1 fields as printed |  |
| Table 7, Hedenfalk sets with p <= 0.01 (mean, permutation) | partly | 27 of 42 fields as printed | 27 of the 41 sets come back at the printed p within Monte Carlo error, breast_cancer_estrogen_signalling first at 0.000 as in the paper; 5 of the paper's sets are not in our 84, and we find 56 sets at p <= 0.01 against 41. |
| Text: breast_cancer_estrogen_signalling first by the mean, outside the ES top 20 | exact | 2 of 2 fields as printed |  |
| Table 8, contingency table notation (Appendix) | not attempted | not attempted | Notation for the 2 x 2 table of overrepresentation analysis. |
| Main claim: the mean of squared mod.t beats GSEA's ES | exact | 1 of 1 fields as printed |  |
| Main claim: the mean of squared mod.t beats Hotelling | exact | 1 of 1 fields as printed |  |
| Claims recomputed from the paper's own tables | agrees | 22 of 22 claims come back from the paper's own tables and figure bars |  |
| R package gseamod and its tutorial | agrees | R package gseamod: R CMD check OK; tests 10 passed, 0 failed, 0 skipped; tutorial rendering equals the committed TUTORIAL.md |  |
<!--/RESULTS-TABLE-->

The main claims hold: the mean of squared moderated t beats ES and Hotelling, and the simulation tables
come back. The claims that do not match come from our cond. FDR, which is not the paper's, and from the
Hedenfalk gene mapping.

## What the code does, against the paper

| Paper | Here |
| --- | --- |
| 600 genes, 20 samples, nine sets (Methods) | `gseamod::simulate_ackermann()`: shared factor for the correlated blocks, shift in class 1, background genes of the mixed sets drawn per set |
| Moderated t | limma's `squeezeVar`, equal to `eBayes` (tested) |
| Transformations: none, squared, rank squared, binary, local fdr | as named; binary calls a gene at two-sided p <= 0.05 (not given); local fdr from fdrtool, used as 1 - lfdr |
| Mean, median, maxmean, ES (weighted), Wilcoxon | as defined in the paper's Appendix |
| Cond. FDR, "linear logistic regression of the probability of gene set membership" | mean over the set of 1 - fdr_S, Efron's conditional fdr from that regression (the statistic is not given; see Table 3) |
| Resampling, permutation, restandardization, 1000 each | as described; one-sided, p = share of null statistics at or above the observed |
| Parametric (mean and Wilcoxon only) | m x mean of squared statistics against chi-squared with m degrees of freedom; normal approximation of the rank sum |
| globaltest | its statistic in closed form (equal to `globaltest::gt` up to a constant, tested); `gt`'s asymptotic p-value for the parametric column |
| Hotelling T2 with a shrinkage correlation | t' R^-1 t with corpcor's `cor.shrink` of the data centred within each class |
| p53: filter max < 5 on log2 and < 2-fold, 8,768 genes, 290 sets | GSEA's collapsed-symbol file, both criteria: exactly 8,768 genes and 290 sets of 15 to 321 |
| Hedenfalk: 2,200 genes mapped to UniGene symbols, 89 sets | UniGene build 236 (2013): 2,233 genes and 84 sets of 15 to 500 genes |

## Layout

| Path | Content |
| --- | --- |
| `main.nf`, `nextflow.config` | The pipeline. |
| `requirements.txt`, `pipeline/install_r.sh` | Pinned Python packages; R 4.3.3 and the R packages at fixed Ubuntu 24.04 versions, globaltest 5.56.0 from its Bioconductor tarball. |
| `results_notes.json` | Labels, sources, assumptions and causes, written by hand; merged with the computed numbers into `../results.json`. |
| `inputs/hedenfalk_image2unigene.tsv` | IMAGE clone to UniGene cluster and symbol for the Hedenfalk clones, cut from UniGene build 236 (NCBI, public domain); `fetch_inputs.sh --unigene` rebuilds it from the 156 MB source and checks it. |
| `pipeline/fetch_inputs.sh` | Downloads with SHA-256 checks: GSEA's p53 files and C2 sets (two GitHub mirrors), strimmerlab's `hedenfalk.rda.gz`. |
| `pipeline/simulate_tables.R` | One simulated data set per replicate, every combination of Tables 2 to 6 and the variants; `output/sim/rep_*.csv`. |
| `pipeline/prepare_data.R`, `pipeline/real_data.R` | p53 and Hedenfalk preprocessing; p-values of every set for eight statistics, resampling and permutation; `output/real/*.csv`. |
| `pipeline/figures.R`, `pipeline/overlay.py` | Figs 2 to 4 drawn on the published pixel grid (placed from the published tick marks), and the overlays. |
| `pipeline/read_published.py` | Bar heights of Figs 2 and 4 and histogram counts of Fig. 3, read off the published files through their tick marks. |
| `pipeline/variants.R` | The variants that test causes; `output/variants.json`. |
| `pipeline/compare.py`, `pipeline/paper_values.json` | Our values against the paper's (typed from Tables 2 to 7); the text's claims, also on the paper's own tables. |
| `pipeline/build_results.py`, `pipeline/check_results.py` | `../results.json` and its verdicts. |
| `pipeline/check_r_package.sh` | `R CMD build`, `R CMD check`, tutorial render compared with the committed `TUTORIAL.md`. |
| `pipeline/build_page.py`, `pipeline/page_template.html` | The results page (`site/PMC2661051/index.html`). |
| `pipeline/check_rerun.py`, `pipeline/check_reproduction.py`, `pipeline/compare_runs.py` | The checks against the committed outputs. |
| `pipeline/update_readmes.py` | The generated parts of the READMEs and the front-page verdict. |
| `output/` | Everything the pipeline writes, committed. |

## Run

From the repository root, on Ubuntu 24.04 with Java 21 and Nextflow 26.04.3:

```bash
bash PMC2661051/figure-reproduction/pipeline/install_r.sh
```

```bash
pip install -r PMC2661051/figure-reproduction/requirements.txt
```

```bash
nextflow run PMC2661051/figure-reproduction/main.nf --outdir results
```

The default run (the CI run of `.github/workflows/reproduce-pmc2661051.yml`) reruns replicates 1 to 3
of the simulation and six gene sets of each data set from scratch, checks that they equal the committed
p-values, and builds everything else from the committed p-values. `--full` reruns all 100 replicates,
every gene set and the variants (about 6 CPU hours) and builds everything from the fresh run; the
workflow does that when started by hand with `full`.

## Pipeline steps

1. `FETCH`: download the inputs and check their SHA-256.
2. `INSTALL`: install `gseamod` from `../package` into the run's own library.
3. `PREPARE`: p53 filter and gene sets; Hedenfalk mapping and gene sets; `datasets.json`.
4. `SIMULATE`, `REAL`: the reruns (or everything with `--full`).
5. `RERUN_CHECK`: the reruns must equal the committed p-values.
6. `VARIANTS`: rerun with `--full`, else the committed `variants.json`.
7. `FIGURES`, `READ_PUBLISHED`, `COMPARE`: renders, overlays, published values, comparison.
8. `PACKAGE`: the R package checks.
9. `RESULTS`, `PAGE`: `results.json` with computed verdicts; the results page and `report.md`.
10. `CHECK`: `check_results.py`, the verdicts against the committed `../results.json`, and
    `compare_runs.py` against the committed `output/`.

## Limits

- **Monte Carlo.** The paper gives no seeds, so simulated rates are compared within a 99% band for two
  shares of 100. With some 300 rates compared, a few misses are expected by chance alone.
- **Shared data.** We analyse every combination on the same 100 data sets; the paper simulated data per
  combination. Our maxmean column therefore repeats the mean column (they are equal on squared scores).
- **Cond. FDR.** The paper names a logistic regression of set membership on the score but not the
  statistic built from it. Neither the slope (which ranks random sets exactly as the mean does) nor the
  mean of Efron's conditional fdr gives the paper's numbers.
- **Hotelling.** Our shrinkage correlation finds the correlated set 1 more often than the paper's
  (0.25 against 0.09); three alternatives were tested, none fits every set.
- **Hedenfalk.** The paper's UniGene mapping and its 89 sets are not given; ours (2,233 genes, 84 sets)
  finds more significant sets, with the same pattern across statistics.
- **Fig. 3.** Our within-set correlations run lower than the paper's (median 0.022 against about 0.03);
  the data behind the figure are not described.
- **Figs 2 and 4, left panels.** Drawn and overlaid but not scored: the curves' letter markers overlap.
