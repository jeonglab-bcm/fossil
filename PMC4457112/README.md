# PMC4457112: Automated confidence ranked classification of RCT articles (Cohen et al. 2015)

Cohen AM, Smalheiser NR, McDonagh MS, Yu C, Adams CE, Davis JM, Yu PS. Automated confidence ranked
classification of randomized controlled trial articles: an aid to evidence-based medicine. *J Am Med Inform
Assoc* 22(3):707–717 (2015). [doi:10.1093/jamia/ocu025](https://doi.org/10.1093/jamia/ocu025) ·
[PMC4457112](https://pmc.ncbi.nlm.nih.gov/articles/PMC4457112/) · issue #94

The paper is © The Author 2015, published by Oxford University Press on behalf of the American Medical
Informatics Association, under [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/). This folder
does not contain the paper, its full text or any part of its supplement. The paper has no computed figure
to compare (its only figure needs manual labels that were never released), so no published figure is
committed. The printed numbers of Tables 1–3 are in `figure-reproduction/output/published_values.json`, read
from the article's PMC XML by `extract_published.py`.

The paper built the RCT Tagger: linear SVMs (LIBLINEAR) that give each human-related MEDLINE citation a
confidence that it reports a randomized controlled trial, trained on the MEDLINE publication type as the
label, with feature sets chosen by forward selection. It released the models only as a web service at
arrowsmith.psych.uic.edu, which now answers HTTP 503; no code, model or scores were published, and the
methods supplement is not in PMC and could not be fetched. We rebuilt the method from the paper's text as
the Python package [`package/`](package/) (`rctconf`), retrained both of the paper's models on the PubMed
2026 baseline, and compared every cell of Tables 1–3 and every claim of the text.

| Folder | Content |
| --- | --- |
| [`figure-reproduction/`](figure-reproduction/) | The Nextflow pipeline: the baseline extraction, the dataset, forward selection, the eight models of Tables 1–3, scoring of 6.2 million citations, the comparison with the paper, the checks. |
| [`package/`](package/) | `rctconf`, the method as an installable Python package, with example data, tests and an [executed tutorial](package/tutorial/TUTORIAL.md). |
| [`results.json`](results.json) | Every table, figure and claim of the paper, with our values and computed verdicts. |
| [`session/`](session/) | The ledger of the session that made this reproduction. |

Results page: <https://jeonglab-bcm.github.io/fossil/PMC4457112/>

## Results

<!-- summary from results.json (check_results.py); the full table, with the causes: figure-reproduction/README.md -->

<!--RESULTS-SUMMARY-->
10 agrees, 7 partly, 4 differs, 5 not attempted; 10 open causes.

| Item | Verdict | Measure |
| --- | --- | --- |
| Table 1, CITATION_PLUS_MESH: 5x2 CV on 1987-2010, held-out 2011 and 2012 | partly | 6 of 21 fields as printed |
| Table 2, CITATION_ONLY: 5x2 CV on 1987-2010, held-out 2011 and 2012 | partly | 6 of 21 fields as printed |
| Table 3, four modelling approaches on 2011, both models | partly | 8 of 40 fields as printed |
| Results: for both years AUC >= 0.965, accuracy >= 0.984, F1 >= 0.807 | partly | 2 of 3 fields as printed |
| Results: test performance very nearly the same as cross-validation | agrees | 2 of 2 fields as printed |
| CITATION_PLUS_MESH slightly better than CITATION_ONLY across all measures | agrees | 1 of 1 fields as printed |
| The two models' AUC 95% intervals do not overlap (2011, 2012) | agrees | 2 of 2 fields as printed |
| Squared error of the confidence below 0.015 for both models | agrees | 1 of 1 fields as printed |
| The enhanced Ruping method more than 3 times as accurate as the zero-centred sigmoid | agrees | 1 of 1 fields as printed |
| Forward selection outperforms CHISQ filtering on every metric | agrees | 1 of 1 fields as printed |
| POSTHOC DROP LOW WEIGHTS almost identical to forward selection with 300-400 times fewer features | partly | 1 of 2 fields as printed, 1 paper errors |
| Adding publication types: AUC up a little, average precision down more, F1 and MSE worse | agrees | 4 of 4 fields as printed |
| Forward selection chose 7 feature sets for CITATION_ONLY and 10 for CITATION_PLUS_MESH | differs | 0 of 2 fields as printed |
| Approximately 45 million unique features | differs | 0 of 1 fields as printed |
| The 1987-2010 training set holds over 5 million articles | agrees | 1 of 1 fields as printed |
| Best single feature: the term "randomized", F1 about 0.72 | partly | 1 of 2 fields as printed |
| Performance basically flat between 5% and 10% of the training data (figure in the supplement) | differs | 0 of 1 fields as printed |
| Disagreements with RCT_PT over 1987-2012: 1811 at >= 0.95, 19 838 at >= 0.50, 277 789 tagged, 20 523 at <= 0.05 | partly | 1 of 5 fields as printed |
| Estimates from the disagreements and Fig. 1's rates: 1268, 7935 (3%), 19 497 (7%), 12 900 (5%), 20 000 | not attempted | not attempted |
| Discussion: the acute cholecystitis search, 3883 articles, 795 tagged, 2751 of 3088 at <= 0.10 | differs | 0 of 6 fields as printed, 1 paper errors |
| Every claim recomputed from the paper's own numbers | agrees | 25 of 29 statements follow from the paper's own numbers. Not: text.posthoc: forward selection features over POSTHOC features, CITATION_ONLY, between 300 and 400 (yes against no); text.estimates: possible RCT_PT errors, thousands (approximately 12 900, 5% of the tagged articles) (12.9 against 13.89); text.estimates: additional RCTs and possible errors combined, thousands (about 20 000) (20 against 20.8); text.cholecystitis: share of the unannotated articles skipped, % (85 against 89.09). The four Hanley-McNeil intervals are centred on their AUC in 4 of 4 cases. |
| Fig. 1, manual-review RCT prevalence by confidence bin, four Cochrane topics (STRICT 0.962, LOOSE 0.986) | not attempted | not attempted |
| The 50 RCT_PT articles of 2014: 14 disagreements; 11 below 0.50, 5 below 0.25, 3 below 0.01 | not attempted | not attempted |
| Cohen's kappa 0.72 between the manual review and RCT_PT | not attempted | not attempted |
| Supplementary material: feature-set lists, top-weighted features, confidence distributions of 2011, the training-fraction figure, Table S2 | not attempted | not attempted |
| Python package rctconf and its tutorial | agrees | rctconf 0.1.0: wheel installed in a fresh environment and imported from it; tests 7 passed; tutorial 5 cells compared, 0 skipped (nondeterministic); TUTORIAL.md in sync |
<!--/RESULTS-SUMMARY-->

Both models came back. Retrained on 6,164,168 human-related MEDLINE citations of 1987-2012 (278,869 tagged RCT
against the paper's 277,789), the CITATION_PLUS_MESH model scores AUC 0.9738 on 2011 and 0.9715 on 2012 (paper 0.973 and
0.972) and the CITATION_ONLY model 0.9681 and 0.9658 (paper 0.966 and 0.965). Every AUC, average precision, F1 and accuracy
of Tables 1 and 2 is within 0.008 of the paper's; at the printed three decimals 12 of 42 cells match exactly. Table 3's
pattern holds: forward selection beats CHISQ filtering, dropping all but the strongest weights costs almost nothing, and
adding publication types raises AUC a little while average precision, F1 and MSE get worse.

What does not come back depends on the lost supplement or on manual labels: the number of feature sets chosen (10 and 13
here, 7 and 10 in the paper; comparing AUC at three decimals gives 7 and 7), the size of the CHISQ models (the test's
threshold is not given), the zero-centred-sigmoid MSE, the disagreement counts at 0.95 and 0.05 (set by the lost
confidence method), the acute cholecystitis example (its search is lost), and Fig. 1, the 2014 sample and the kappa (the
reviewed articles were never released). The arithmetic check found four slips in the paper: 2751 of 3088 is 89%, not 85%;
5% of 277,789 is 13,889, not 12,900; 7,900 + 12,900 is about 21,000, not 20,000; and Table 3's feature counts give a
431-fold reduction for CITATION_ONLY, not 300-400.

**The main claim holds: both rebuilt models rank RCTs with AUC near 0.97, the MeSH model ahead, as in the paper. The
claims that do not match come from the lost supplement (feature sets, CHISQ test, confidence method) and from manual
labels that were never released.**

## Install the method

```bash
pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC4457112/package"
```

See the [tutorial](package/tutorial/TUTORIAL.md).

## Kept local

Not committed and git-ignored: `sources/` (the paper's PMC XML, the Bag-Of-Words toolkit the stop words come
from) and `work/` (the extracted baseline, about 3 GB; feature files, models and scores, about 6 GB). The
pipeline rebuilds them from NLM's baseline (`figure-reproduction/README.md`, Run).

This reproduction was made with Paper2Repro 0.5.0 (the `skill` block of `results.json`), installed as a copy
of the Paper2Repro repository at commit 2aa66c4 without its git folder, so `skill_version.py` could not
record the commit itself.
