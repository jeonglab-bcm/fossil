# PMC2850872 — SVM prediction of diabetes and pre-diabetes (Yu et al. 2010)

Yu W, Liu T, Valdez R, Gwinn M, Khoury MJ. Application of support vector machine modeling for prediction
of common diseases: the case of diabetes and pre-diabetes. *BMC Medical Informatics and Decision Making*
10:16 (2010). [doi:10.1186/1472-6947-10-16](https://doi.org/10.1186/1472-6947-10-16) ·
[PMC2850872](https://pmc.ncbi.nlm.nih.gov/articles/PMC2850872/)

The paper is © 2010 Yu et al., licensee BioMed Central Ltd., published under
[CC BY 2.0](https://creativecommons.org/licenses/by/2.0/). In keeping with the rest of this repository,
this folder does not contain the paper or its full text. `figure-reproduction/published/figure-2.jpg` is
the paper's Figure 2, redistributed under CC BY 2.0 with the attribution above.

The NHANES 1999–2004 public-use files (US National Center for Health Statistics, public domain) are
downloaded by the pipeline and checked against SHA-256 sums. `figure-reproduction/output/analytic.csv` is
the analytic data set built from them.

**What was lost:** the "Diabetes Classifier" web tool (hugenavigator.net, gone, no Wayback capture) and
its Java code, which was never released; the paper's random split.

| Folder | Content |
| --- | --- |
| [`figure-reproduction/`](figure-reproduction/) | Table 1 from NHANES; Tables 2 and 3, Figure 2 and the claims in the text over 10 random splits. Nextflow pipeline. |
| [`package/`](package/) | `diabclass`, the method as a Python package, with an executed [tutorial](package/tutorial/TUTORIAL.md): `pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC2850872/package"`. |
| [`results.json`](results.json) | Every figure, table and claim of the paper, with its computed verdict. |
| [`session/`](session/) | The ledger of the session that made this reproduction. |

Results page: <https://jeonglab-bcm.github.io/fossil/PMC2850872/>

## Results

<!--RESULTS-->

## Claims

<!--CLAIMS-->

Kept local and gitignored: `sources/` (the paper's text, PDF and figures; the NHANES downloads), `work/`
(scratch runs) and `.rlib/` (the local R library).
