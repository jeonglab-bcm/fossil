# PMC2648748 figure reproduction

Jiang R, Tang W, Wu X, Fu W. A random forest approach to the detection of epistatic interactions in case-control
studies. *BMC Bioinformatics* 10(Suppl 1):S65 (2009).
[doi:10.1186/1471-2105-10-S1-S65](https://doi.org/10.1186/1471-2105-10-S1-S65). CC BY 2.0.

`published/` holds the paper's Figs 2 and 3 (CC BY 2.0, attribution above), the 2400 x 1200 images embedded in
the paper's PDF on PMC. Nothing else of the paper is in this folder.

## Results

<!--__RESULTS__-->

## What the code does, against the paper

| Paper | Here |
| --- | --- |
| Stage 1: R randomForest, SNPs as categorical features, gini importance from one forest with all SNPs; mtry the default (printed garbled); ntree not given for the simulations | `epiforest::gini_importance`: randomForest 4.7-1.1, every SNP a three-level factor, `MeanDecreaseGini`; mtry floor(sqrt(p)), ntree 500 (the package defaults). |
| SWSFS pseudocode: add SNPs by gini importance, forest on the top i, stop at the first i > w with i − w the argmin of Error over [i − w, i], w = 20; return the top i − w | `epiforest::swsfs`, line by line (ties: the first minimum, R's `which.min`); the loop's missing `i := i + 1` added. The out-of-bag error of the last tree count (`err.rate[ntree, "OOB"]`). |
| Stage 2: one-way B tests (Bonferroni L), two-way (skip if both reported, conditional B if one, L(L−1)/2), three-way (B or conditional B, L(L−1)(L−2)/6), alpha = 0.05 | `epiforest::hierarchical_tests`. A three-way test conditions on the SNPs of the triple already reported singly or in a reported pair, and is skipped when all three were. |
| B statistic: ln[P1/P1] with P1 = Pjoin(D)[Pind(U) + Pjoin(U)], P0 = Pind(D,U) + Pjoin(D,U), Dirichlet pseudo-counts 0.5; 2B "shifted" chi-squared with 3^k − 1 df; conditional B with 3^k − 3^t df, not written out | `epiforest::b_from_counts`: the printed formula with P0 in the denominator. The shift from Stirling's expansion of each Dirichlet-multinomial term (`b_shift`), checked on null data (`output/checks/bstat_null.json`). The conditional B compares cases' joint distribution with a null where the reported SNPs keep their association and the rest are unlinked; its df are the paper's. |
| Simulations: models 1-3 of Marchini et al. (2005), lambda 0.3, 0.5, 1.0, prevalence 0.1, MAF 0.05-0.5, r² 0.7 and 1.0, 100 data sets of 1000 markers x (1000 cases + 1000 controls), null MAF U(0, 0.5) | `epiforest::simulate_dataset` with `disease_model`: odds tables solved for the prevalence and lambda (the marginal odds ratio of heterozygote to wild type, minus 1); model 2 with the table of epiMODE (same group), chosen by the chi-squared powers (`output/checks/model_variants.json`); the marker of each locus at the locus's MAF with correlation sqrt(r²) per haplotype (epiMODE Text S1). One seed per data set. |
| Comparators: BEAM (priors 0.001), stepwise logistic regression (epsilon 10%, two- and three-way), chi-squared with up to 2 df | BEAM not run (the program is gone). `epiforest::stepwise_lr`: the full logistic model per observed genotype combination (likelihood-ratio test), 100 SNPs kept, stage 2 adjusted by its own number of tests. `epiforest::chisq_single`. |
| Power: share of the 100 data sets in which all disease loci are identified at 0.05 after Bonferroni | Both disease markers in some reported test. Variants in `output/summary.json`. |
| AMD application (116,204 SNPs, 96 cases, 50 controls) | Not attempted: the genotypes are not public (see Limits). The statements that follow from Table 1 itself are checked (`text.arithmetic`). |

## Comparing Monte Carlo figures

Every bar of Fig. 2 and every box of Fig. 3 summarizes 100 random data sets whose seeds the paper does not give, so
nothing can come back exactly. Each published bar and box median is read off the figure (`read_published.py`,
through the tick marks of each panel; the bars read within 0.2 points of an integer count) and compared with ours
at a tolerance fixed before the comparison: for a power, 1.96 standard errors of the difference of two independent
shares of 100 data sets, 1.96 sqrt(2 p (1 − p) / 100) with p = (paper + ours + 1) / 202; for a median, 1.96
sqrt(2) standard errors of a median of 100 values (from our interquartile range) plus half a SNP for reading.
Two runs of the same design miss about 1 value in 20.

The pixel scores compare the drawings inside the six frames (the BEAM bars and the legend masked): the share of the
paper's black ink within 2 px of ours, and of ours within 2 px of the paper's. A known-wrong drawing scores
against the same frames: each panel with another model's or the other r²'s values (wrong inputs), and our values
shifted by 5 power points or 2 SNPs (near misses). Shifts of that size are within Monte Carlo error, so the pixel
score cannot settle a single bar; the values carry the comparison.

## Layout

| Path | Content |
| --- | --- |
| `main.nf`, `nextflow.config` | The pipeline. |
| `requirements.txt` | Pinned Python packages (R 4.3.3 and randomForest 4.7-1.1 come from Ubuntu 24.04; see the workflow). |
| `results_notes.json` | Labels, assumptions and causes, written by hand; merged with the run into `../results.json`. |
| `results.json` | The repository's results check (`tools/check_results.py`): our value for every compared bar and median, and the pixel scores. |
| `pipeline/` | `fetch_inputs.sh`, `read_published.py`, `sim_study.R` (one chunk of the study), `summarize.py`, `sim_check.py`, `render.R`, `compare.py`, `build_results.py`, `check_reproduction.py`, `build_page.py` + `page_template.html`, `make_results_check.py`; the checks `model_variants.R`, `bstat_null.R`, `swsfs_variants.R` + `swsfs_summary.py`, `check_package.sh`; copies of the skill's `check_results.py` and `compare_runs.py`. |
| `published/` | The paper's Figs 2 and 3 (CC BY 2.0). |
| `output/sim/` | One record per simulated data set (2,400): seed, disease marker columns, the chi-squared and logistic regression p-values, and epiForest's ranks, out-of-bag error curve, candidates and what it found. |
| `output/checks/` | The disease-model variants, the B statistic's null distribution and the SWSFS variants. |
| `output/` | `fig2_ours.png`, `fig3_ours.png` (our run drawn as the paper drew it, on its pixel grid), `fig2_overlay.png`, `fig3_overlay.png` (paper in dark ink, ours in green), `controls/`, `published_values.json`, `summary.json`, `comparison.json`, `report.md`. |

## Run

```bash
pip install -r PMC2648748/figure-reproduction/requirements.txt
sudo apt-get install r-base-core r-cran-randomforest r-cran-jsonlite r-cran-testthat r-cran-knitr r-cran-rmarkdown pandoc poppler-utils fonts-liberation
nextflow run PMC2648748/figure-reproduction/main.nf --outdir results               # about 10 minutes
nextflow run PMC2648748/figure-reproduction/main.nf --outdir results --full        # every data set again: about 28 CPU hours
nextflow run PMC2648748/figure-reproduction/main.nf --outdir results --variants    # + the SWSFS hypothesis tests, about 2 CPU hours
```

The default run rereads the published figures, reruns three data sets from scratch (one of each model) and checks
them against `output/sim` value for value, recomputes every power and Fig. 3 from `output/sim`, redraws and scores
both figures with their controls, reruns the disease-model and B-statistic checks, checks the package, and
compares everything with the committed `output/`. `.github/workflows/reproduce-pmc2648748.yml` runs it on every
pull request that touches this paper; started by hand with `full` it reruns the whole study (it needs a runner
with more cores to fit in its time limit).

## Pipeline steps

1. `FETCH`: the paper's PDF from PMC's open-access bucket (SHA-256 checked); Figs 2 and 3 extracted and checked
   against `published/` pixel for pixel.
2. `READ_PUBLISHED`: every bar of Fig. 2 and every box median and maximum of Fig. 3.
3. `INSTALL_PACKAGE`: `../package` into a private R library.
4. `SIM_COMMITTED` or (`--full`) `SIM_CHUNK` x 96 and `REDUCE`: the per-data-set records.
5. `SIM_CHECK`: three data sets rerun from scratch against the committed records.
6. `SUMMARY`: power per method and setting, the selected-SNP counts; `render.R` draws Figs 2 and 3 and the
   controls; `compare.py` scores them and computes the claims.
7. `CHECKS`: `model_variants.R`, `bstat_null.R`; the committed SWSFS variants (or, with `--variants`, rerun).
8. `PACKAGE`: `R CMD build`, `R CMD check`, the tutorial rendered and compared with `../package/tutorial/TUTORIAL.md`.
9. `RESULTS`: `results.json` (`build_results.py`, verdicts by `check_results.py`), the check step (`report.md`)
   and the results page.

## Limits

<!--__LIMITS__-->
