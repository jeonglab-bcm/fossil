# PMC3392844: Large-scale prediction of adverse drug reactions (Liu et al. 2012)

Liu M, Wu Y, Chen Y, Sun J, Zhao Z, Chen XW, Matheny ME, Xu H. Large-scale prediction of adverse drug
reactions using chemical, biological, and phenotypic properties of drugs. *Journal of the American
Medical Informatics Association* 19(e1):e28-e35 (2012).
[doi:10.1136/amiajnl-2011-000699](https://doi.org/10.1136/amiajnl-2011-000699) ·
[PMC3392844](https://pmc.ncbi.nlm.nih.gov/articles/PMC3392844/) · issue #93

The paper is an open-access article under
[CC BY-NC 2.0](https://creativecommons.org/licenses/by-nc/2.0/). This folder does not contain the paper, its
full text or its supplement. `figure-reproduction/published/` holds crops of its Figs 2-5, rendered from the
PMC PDF at 600 dpi for comparison, redistributed for non-commercial use with the attribution above.
`figure-reproduction/output/published_values.json` holds the printed numbers of Tables 1-4 and S1 and of the
text, and `published_curves.json` the ROC curves of Figs 2-4 read from the PDF's vector paths, both made by
`extract_published.py`.

The paper predicts each of 1,385 adverse drug reactions (ADRs) of 832 drugs with one classifier per ADR,
from 881 chemical substructures, 1,142 biological features (targets, transporters, enzymes, pathways) and
2,253 phenotypic features (indications and the drug's other ADRs), and compares feature sets (Table 2,
Figs 2 and 3) and five algorithms (Table 3, Fig. 4) by micro-averaged ROC over fivefold cross-validation.
Its pipeline was never released. The authors' training file, with every feature bit and the fold of each
drug for each ADR, survives in the supplement of Zhang et al. 2015
([PMC4634905](https://pmc.ncbi.nlm.nih.gov/articles/PMC4634905/), CC BY 4.0), who received it from the
authors. We rebuilt the method from the paper's text as the Python package [`package/`](package/)
(`adrfusion`) and reran every model on that file.

| Folder | Content |
| --- | --- |
| [`figure-reproduction/`](figure-reproduction/) | The Nextflow pipeline: the downloads, every model on every ADR and fold, the tables, the figures redrawn on the published frames, the claims, the checks. |
| [`package/`](package/) | `adrfusion`, the method as an installable Python package, with example data, tests and an [executed tutorial](package/tutorial/TUTORIAL.md). |
| [`results.json`](results.json) | Every figure, table and claim of the paper, with our values and computed verdicts. |
| [`session/`](session/) | The ledger of the session that made this reproduction. |

Results page: <https://jeonglab-bcm.github.io/fossil/PMC3392844/>

## Results

<!-- summary from results.json (check_results.py); the full table, with the causes: figure-reproduction/README.md -->

<!--RESULTS-SUMMARY-->
<!--/RESULTS-SUMMARY-->

Verdicts compare our value with the paper's at its printed precision (four decimals for Tables 2 and 3).

**What came back.** Table 1's dimensions and the text's dataset counts, exactly. The SVM's micro-averaged
AUCs of Table 2, to the third decimal, and with them Fig. 2, whose six curves overlay ours. Fig. 3, but for
its chem curve. The SVM, random forest and KNN curves of Fig. 4 and rows of Table 3. 36 of 39 calls of
Table 4. Every claim recomputed from the paper's own tables, and the identity of the training file:
Fig. 5's true positives divided by Table 2's recalls give the file's 59,205 positive pairs.

**Settings the paper does not state**, found by testing them against its tables: the SVM's scores are
LIBSVM's probability estimates (decision values give chem an AUC near 0.79, not 0.9054); ACC is read at the
maximum-accuracy point of the global ROC, precision and recall at the maximum-F1 point; KNN scores the share
of positive neighbours, ties included.

**What did not, and why.** Fourth decimals of Table 2: the SVM's probability fit draws a random internal
split, and its seed moves AUCs by a few 1e-4 and precision and recall by one or two points. The LR and NB rows of
Table 3 and their curves in Fig. 4: no LIBLINEAR setting we tried gives the paper's LR, and CLOP, the
package of its naive Bayes, is gone. Fig. 3's chem curve is not Table 2's chem row: its area is 0.7558,
Table 2 prints 0.7659, and ours is 0.7658. Fig. 5's counts, Table S1 and some numbers of the Discussion
differ by a few percent. Each cause, with the hypotheses tested, is in `results.json`.

<!--CLAIMS-LINE--><!--/CLAIMS-LINE-->

Kept local and gitignored: `sources/` (the paper, its PDF, XML and supplement, the figure JPEGs, Zhang et
al.'s supplement), `work/` (exploration runs) and `.venv/`.
