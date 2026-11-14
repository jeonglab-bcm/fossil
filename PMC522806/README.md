# PMC522806: A combinational feature selection and ensemble neural network method for classification of gene expression data (Liu et al. 2004)

Liu B, Cui Q, Jiang T, Ma S. A combinational feature selection and ensemble neural network method for
classification of gene expression data. *BMC Bioinformatics* 5:136 (2004).
[doi:10.1186/1471-2105-5-136](https://doi.org/10.1186/1471-2105-5-136),
[PMC522806](https://pmc.ncbi.nlm.nih.gov/articles/PMC522806/), issue
[jeonglab-bcm/fossil#63](https://github.com/jeonglab-bcm/fossil/issues/63).

The paper is © 2004 Liu et al; licensee BioMed Central Ltd, open access under the Creative Commons
Attribution License 2.0 (<https://creativecommons.org/licenses/by/2.0>). This folder does not contain
the paper or its full text; `figure-reproduction/published/` holds its four figures, unchanged, with
that notice.

The method classifies expression samples with an ensemble: on each of 100 bootstrap resamples it
picks three feature sets (30 genes by rank-sum test, 15 principal components, 30 genes from 50 gene
clusters by t-test), trains a ten-hidden-unit network on each, averages their confidences, and
combines the 100 answers by soft voting. The authors wrote it in Matlab and released no code; the
paper's only link, the Kent Ridge data repository, is gone. We rebuilt the method from the paper as
the Python package [`package/`](package/) (`cfsenn`) and ran it on the seven Kent Ridge datasets from
the University of Granada mirror, whose sample and gene counts all equal Table 1's.

| Folder | Content |
| --- | --- |
| [`figure-reproduction/`](figure-reproduction/) | The Nextflow pipeline: the datasets, every classification of Tables 2 and 3 and the text, the Discussion's controls, Figs 3 and 4 redrawn on the published images, and the check against the committed outputs. |
| [`package/`](package/) | `cfsenn`, the method as an installable Python package, with example data, tests and an [executed tutorial](package/tutorial/TUTORIAL.md). |
| [`results.json`](results.json) | Every figure, table and claim of the paper, with our values and computed verdicts. |
| [`session/`](session/) | The ledger of the session that made this reproduction. |

Results page: <https://jeonglab-bcm.github.io/fossil/PMC522806/>

## Results

<!-- summary and table from results.json (check_results.py --markdown); do not edit by hand -->
<!--RESULTS-SUMMARY-->
8 exact, 2 agrees, 6 partly, 3 differs, 4 not attempted; 8 open causes.

| Item | Verdict | Measure |
| --- | --- | --- |
| Table 1, the seven datasets (genes, training and test samples per class) | exact | 32 of 32 fields as printed |
| Fig. 1 (flow chart) | not attempted | not attempted |
| Fig. 2 (the three networks) | not attempted | not attempted |
| Table 2, our methods: test-set accuracy (ALL-AML, lung, prostate) | partly | 1 of 3 fields as printed |
| Table 2, LOOCV on the training samples | partly | 1 of 3 fields as printed |
| Table 2, bagged decision trees and the best methods (quoted) | not attempted | not attempted |
| Fig. 3, 'Our method' bars (test sets) | partly | 1 of 3 fields as printed |
| Table 3, LOOCV (DLBCL, ovarian, colon) | partly | 1 of 3 fields as printed |
| Table 3, 10-fold CV (DLBCL, ovarian, colon) | partly | 1 of 3 fields as printed |
| Table 3, other methods (quoted) | not attempted | not attempted |
| Fig. 4, 'OurMethod' bars (DLBCL 22/25 split, ovarian 10-fold, colon LOOCV) | differs | 0 of 3 fields as printed |
| Text: MLL, 15 of 15 test samples correct | exact | 1 of 1 fields as printed |
| Text: 75 features in all | exact | 1 of 1 fields as printed |
| Claims recomputed from the paper's own tables | agrees | 7 of 7 claims come back from the paper's own tables. 11 of 12 printed accuracies are whole counts of samples; not a whole count: Ovarian 98.82% of 253. Fig. 4's 98% on 25 test samples is not a whole count either (24/25 = 96, 25/25 = 100). |
| Text and Fig. 3: better than bagged decision trees on all three test sets | exact | 3 of 3 fields as printed |
| Text: better than the best cited method on all three test sets | partly | 2 of 3 fields as printed |
| Text: prostate LOOCV a little lower than its test accuracy | differs | 0 of 1 fields as printed |
| Text: colon LOOCV better than Dettling and Buhlmann's boosting (85.48%) | exact | 1 of 1 fields as printed |
| Text: DLBCL on the 22/25 split better than Cho and Won's 96% | differs | 0 of 1 fields as printed |
| Discussion: random genes in place of the selected features classify worse | exact | 1 of 1 fields as printed |
| Discussion: a single network on all the same features classifies worse | exact | 1 of 1 fields as printed |
| Discussion and Methods: AdaBoost in place of bagging classifies worse | exact | 1 of 1 fields as printed |
| Python package cfsenn and its tutorial | agrees | cfsenn 0.1.0: wheel installed in a fresh environment and imported from it; tests 8 passed; tutorial 5 cells compared, 0 skipped (nondeterministic); TUTORIAL.md in sync |
<!--/RESULTS-SUMMARY-->

<!--CLAIMS-LINE-->
The main claim holds in part: our ensemble beats the bagged trees on all three test sets and each Discussion control classifies worse, but it only ties the best cited method on ALL-AML, its prostate LOOCV is not below its test accuracy, and it falls short of Cho and Won's DLBCL split; the causes are one ALL-AML test sample that every seed and hypothesis test misses, the unscaled prostate test arrays and the unlisted 22/25 split.
<!--/CLAIMS-LINE-->

## Kept local, not in the repository

`PMC522806/sources/` (git-ignored) holds the paper's full text (Europe PMC XML), its figure files and
the seven downloaded datasets. `figure-reproduction/pipeline/fetch_inputs.sh` downloads the datasets
again and checks their SHA-256. The Kent Ridge repository gave no licence for redistributing the
data, so none of it is committed; the package's example data are synthetic.

## Session

The session that made this reproduction began with a request to install the Paper2Agent skills, in
the same conversation, before the kickoff prompt; its ledger (`session/`) therefore counts that turn
as well.
