# Example data

| File | What |
| --- | --- |
| `citations_train.csv.gz` | 1,500 citations of 2010 (300 with the MEDLINE publication type Randomized Controlled Trial, 1,200 without), with that label in `rct` |
| `citations_test.csv.gz` | 500 citations of 2011 (100 RCT, 400 not), without the label |
| `citations_test_expected.csv` | the expected output: the test citations' RCT publication type in MEDLINE (`pmid`, `rct`) |
| `stoplist_smart_libbow.txt` | the 523 distinct stop words built into McCallum's Bag-Of-Words library (`stopwords.c` of bow-20020213, from the SMART system), LGPL-2 |

**Where the citations come from.** The PubMed 2026 baseline (`https://ftp.ncbi.nlm.nih.gov/pubmed/baseline/`, files `pubmed26n0650` to `pubmed26n0700`), extracted by the reproduction's `extract_medline.py` and sampled by `scripts/make_example_data.py` with fixed seeds: human-related citations (MeSH Humans), in English, with an abstract. The columns are `pmid`, `title`, `journal` (MedlineTA), `n_authors`, `mesh` (descriptor UIs, `*` before a major topic) and `chemicals` (substance UIs). Abstracts and author names are left out. NLM provides PubMed data free of charge under its [terms and conditions](https://www.nlm.nih.gov/databases/download/terms_and_conditions.html); abstracts may be copyrighted by their publishers, which is why they are not bundled.

**Why the expected output is evidence.** The labels are NLM's indexing, made by NLM's indexers, not by this package. The tests and the tutorial check that the model trained on the training file ranks the test RCTs first (AUC at least 0.90) and agrees with NLM on at least 85% of the test citations. The paper's own models reach an AUC of about 0.97 on all 2011 citations.
