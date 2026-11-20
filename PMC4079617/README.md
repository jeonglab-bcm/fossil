# PMC4079617: Robust Poisson against log-binomial models when outliers are present (Chen et al. 2014)

Chen W, Shi J, Qian L, Azen SP. Comparison of robustness to outliers between robust poisson models and log-binomial
models when estimating relative risks for common binary outcomes: a simulation study. *BMC Medical Research
Methodology* 14:82 (2014). [doi:10.1186/1471-2288-14-82](https://doi.org/10.1186/1471-2288-14-82) ·
[PMC4079617](https://pmc.ncbi.nlm.nih.gov/articles/PMC4079617/) · issue [#74](https://github.com/jeonglab-bcm/fossil/issues/74)

The paper is © 2014 Chen et al., licensee BioMed Central, under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). This folder does not contain the paper, its full text or
its supplements. It holds Fig. 1 as published (`figure-reproduction/published/fig1.png`, the 300 dpi image embedded
in the article PDF) for comparison, with this attribution, as the licence allows. The printed numbers of Tables 1-3,
of Tables A1-A3 (Additional file 2) and the design of Additional file 1 are in
`figure-reproduction/output/published_values.json`, read from the article XML and the supplement PDFs by
`extract_published.py`.

The paper compares two ways of estimating a relative risk for a common binary outcome, robust (modified) Poisson
regression and log-binomial regression (with the COPY method when the log-binomial fit does not converge), in a
SAS 9.2 simulation: 24 scenarios of RR, outcome rate, association and a linear or quadratic confounder, each at
0%, 2% and 5% contamination (outcomes flipped at the extremes of the outcome probability), 1,000 data sets of
n = 1500 (Tables 1-3, Fig. 1) and n = 500 (Additional file 2). It released no code, and the COPY macro is no longer
online. We rebuilt both fits, the design and the contamination from the text as the Python package
[`package/`](package/) (`robustrr`), reran every scenario and compared every printed cell, Fig. 1 and every
quantitative statement of the text.

| Folder | Content |
| --- | --- |
| [`figure-reproduction/`](figure-reproduction/) | The Nextflow pipeline: the simulation, the comparison with every printed cell, Fig. 1, the claims, the cross-check of the fits, the checks. |
| [`package/`](package/) | `robustrr`, the method as an installable Python package, with example data, tests and an [executed tutorial](package/tutorial/TUTORIAL.md). |
| [`results.json`](results.json) | Every table, figure panel and claim of the paper, with our values and computed verdicts. |
| [`session/`](session/) | The ledger of the session that made this reproduction. |

Results page: <https://jeonglab-bcm.github.io/fossil/PMC4079617/>

## Results

<!-- summary from results.json (check_results.py); the full table, with the causes: figure-reproduction/README.md -->

<!--RESULTS-SUMMARY-->
<!--/RESULTS-SUMMARY-->

<!--CLAIMS-LINE--><!--/CLAIMS-LINE-->

## What is kept local

Git-ignored: `sources/` (the article XML, text and PDF, the supplements and figure as downloaded), `work/`
(scratch runs) and `.venv/`. `figure-reproduction/pipeline/fetch_inputs.sh` downloads every input again and checks
its SHA-256.
