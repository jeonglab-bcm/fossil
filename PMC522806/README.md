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
<!--/RESULTS-SUMMARY-->

<!--CLAIMS-LINE-->

## Kept local, not in the repository

`PMC522806/sources/` (git-ignored) holds the paper's full text (Europe PMC XML), its figure files and
the seven downloaded datasets. `figure-reproduction/pipeline/fetch_inputs.sh` downloads the datasets
again and checks their SHA-256. The Kent Ridge repository gave no licence for redistributing the
data, so none of it is committed; the package's example data are synthetic.

## Session

The session that made this reproduction began with a request to install the Paper2Agent skills, in
the same conversation, before the kickoff prompt; its ledger (`session/`) therefore counts that turn
as well.
