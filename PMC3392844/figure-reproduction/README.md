# PMC3392844 figure reproduction

Liu M, Wu Y, Chen Y, Sun J, Zhao Z, Chen XW, Matheny ME, Xu H. Large-scale prediction of adverse drug
reactions using chemical, biological, and phenotypic properties of drugs. *J Am Med Inform Assoc*
19(e1):e28-e35 (2012). [doi:10.1136/amiajnl-2011-000699](https://doi.org/10.1136/amiajnl-2011-000699).
CC BY-NC 2.0.

`published/fig2.png` to `fig5.png` are the paper's figures (CC BY-NC 2.0, attribution above), cropped from
the PMC PDF at 600 dpi. Nothing else of the paper is in this folder. The training data are downloaded by
`pipeline/fetch_inputs.sh` from Zhang et al. 2015's Additional file 1 (PMC4634905, CC BY 4.0) and checked by
SHA-256; they are not committed.

## Results

<!-- full table from results.json (check_results.py --markdown); regenerate with pipeline/update_readmes.py -->

<!--RESULTS-TABLE-->
<!--/RESULTS-TABLE-->

<!--CLAIMS-LINE--><!--/CLAIMS-LINE-->

## What the code does, against the paper

| Paper | Here |
| --- | --- |
| 832 drugs, 1,385 ADRs, 4,276 binary features; for ADR j the "other side effects" are the other 1,384 ADRs | The authors' file `random_group_cv_data.indication`; the other ADRs of j are the label columns but j |
| Fivefold cross-validation per ADR | The authors' folds, the last field of their file (a fold for every drug and ADR) |
| LIBSVM, RBF kernel, g = 0.008, C = 2 | scikit-learn's libsvm on a precomputed RBF kernel built from per-block Hamming distances (the same kernel; the package tests it against the official LIBSVM) |
| Scores merged into one global ROC (not stated which) | Platt probabilities (LIBSVM `-b 1`) |
| ACC, precision and recall at the "best cut-off points" | ACC at the maximum-accuracy point, precision and recall at the maximum-F1 point |
| LIBLINEAR LR, C = 10, epsilon = 1 | scikit-learn's liblinear, no bias term |
| CLOP naive Bayes (settings not stated) | Bernoulli naive Bayes, smoothing 1 |
| WEKA KNN, k = 55; WEKA RF, 100 trees | share of positives among the 55 nearest (ties included); scikit-learn RF, 13 features per split |
| KS test on per-ADR AUCs, Bonferroni-corrected | One-sided two-sample KS, times 3 (the comparisons the paper reports) |
| Clinical validation: train on the other drugs, predict cerivastatin and rofecoxib | The same, Yes when the probability is above 0.5 |
| Chi-square test of each feature against each ADR, p < 0.05 (Table S1) | The same, shares of informative (feature, ADR) pairs |

## Layout

```text
figure-reproduction/
├── main.nf, nextflow.config, requirements.txt
├── results_notes.json          labels, assumptions and causes of results.json (written by hand)
├── pipeline/
│   ├── fetch_inputs.sh         downloads and SHA-256 checks
│   ├── extract_published.py    the paper's printed values, vector curves and figure crops (--extract)
│   ├── run_models.py           every model on every ADR and fold, through adrfusion
│   ├── evaluate.py             metrics, ROC curves, Tables 1-3, S1, Fig. 5 counts, KS tests
│   ├── table4.py, claims.py    Table 4 and the claims of the text
│   ├── figures.py              our curves on the published frames, pixel scores and controls
│   ├── seed_spread.py          Table 2 over SVM seeds 0-3 (--full)
│   ├── hypotheses.py           the variants behind the causes (--full)
│   ├── build_results.py        results.json from the notes and the run
│   ├── build_page.py           the results page
│   ├── check_reproduction.py   fresh run against the committed outputs
│   └── check_results.py, compare_runs.py, check_package.py   from Paper2Repro
├── published/                  the paper's Figs 2-5 at 600 dpi
└── output/                     every number and render of the run
```

## Run

From the repository root (Python 3.12, Java 21, Nextflow 26.04.3):

```bash
pip install -r PMC3392844/figure-reproduction/requirements.txt ./PMC3392844/package
```

```bash
nextflow run PMC3392844/figure-reproduction/main.nf --outdir results
```

`--full` also reruns SVM seeds 1-3 and the hypothesis variants (about 25 minutes more; otherwise the
committed `seed_spread.json` and `hypotheses.json` are used). `--extract` downloads the paper again and
checks that its values, curves and figure crops equal the committed ones (needs `poppler-utils`).

## Pipeline steps

1. `FETCH`: Zhang et al. 2015's Additional file 1, SHA-256 checked; the authors' training file from inside it.
2. `PUBLISHED`: the committed published values and curves (or extracted again with `--extract`).
3. `RUN_SVM`, `RUN_METHODS`: every model of Tables 2 and 3, the indication-only set and the class-weighted SVM and RF.
4. `EVALUATE`, `TABLE4`, `FIGURES`, `CLAIMS`: every compared number, the renders and overlays.
5. `SEEDS`, `HYPOTHESES`: committed, or rerun with `--full`.
6. `PACKAGE`: `check_package.py` on `adrfusion`.
7. `RESULTS`: `results.json`, the results page, `figure-reproduction/results.json`, and the check against the committed outputs.
8. `CHECK`: fails the run when any check fails.

## Limits

- The authors' code is lost, so the method is rebuilt from the text and checked against the paper only.
- `output/offline_checks.json` records two one-off checks that are not part of the pipeline: the official
  LIBSVM C library with a fresh `rand()` seed per model, and RF with another seed.
- The LR and NB rows are not reproduced; the settings behind them are not stated, and CLOP is no longer available.
- The precision, recall and Table 4 calls depend on cut-off rules the paper does not state.
