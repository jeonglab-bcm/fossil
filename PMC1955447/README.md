# PMC1955447: A simulation study of sample size for multilevel logistic regression models (Moineddin et al. 2007)

Moineddin R, Matheson FI, Glazier RH. A simulation study of sample size for multilevel logistic regression models.
*BMC Medical Research Methodology* 7:34 (2007). [doi:10.1186/1471-2288-7-34](https://doi.org/10.1186/1471-2288-7-34) ·
[PMC1955447](https://pmc.ncbi.nlm.nih.gov/articles/PMC1955447/) · issue #86

The paper is © 2007 Moineddin et al., licensee BioMed Central, under
[CC BY 2.0](https://creativecommons.org/licenses/by/2.0/). This folder does not contain the paper or its full
text. The paper has no figures and no supplement. The printed numbers of Tables 1-5 are in
`figure-reproduction/output/published_values.json`, read from the article XML by `extract_published.py`.

The paper asks how many groups, and how many people per group, a two-level logistic regression with a random
intercept and a random slope needs. It simulated 27 designs (30, 50 or 100 groups of 5, 30 or 50, at three
intra-class correlations), 1,000 data sets each, fitted each by maximum likelihood with SAS PROC NLMIXED, and
reported convergence, bias and the coverage of Wald intervals (Tables 1-3), the same at three prevalences
(Table 4), and with non-normal covariates and random effects (Table 5). It released no code. We rebuilt the
data generator and an NLMIXED-like fit (adaptive Gauss-Hermite quadrature, NLMIXED's rule for the number of
points, quasi-Newton from the true values) as the Python package [`package/`](package/) (`mlagq`), reran every
design and compared every printed cell and every quantitative claim of the text.

| Folder | Content |
| --- | --- |
| [`figure-reproduction/`](figure-reproduction/) | The Nextflow pipeline: the simulation, the per-replicate records, the comparison with every printed cell, the claims, the check against numerical integration, the checks. |
| [`package/`](package/) | `mlagq`, the method as an installable Python package, with example data, tests and an [executed tutorial](package/tutorial/TUTORIAL.md). |
| [`results.json`](results.json) | Every table and claim of the paper, with our values and computed verdicts. |
| [`session/`](session/) | The ledger of the session that made this reproduction. |

Results page: <https://jeonglab-bcm.github.io/fossil/PMC1955447/>

## Results

<!-- summary from results.json (check_results.py); the full table, with the causes: figure-reproduction/README.md -->

<!--RESULTS-SUMMARY-->
<!--/RESULTS-SUMMARY-->

<!--SUMMARY-PROSE-->
<!--/SUMMARY-PROSE-->

<!--CLAIMS-LINE-->
<!--/CLAIMS-LINE-->

Kept local and gitignored: `sources/` (the paper's XML, text and PDF as downloaded), `work/` (scratch runs and
the full records of the second run and the hypothesis variants), `.venv/`.
