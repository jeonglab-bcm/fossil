# rctconf

Confidence that a MEDLINE citation reports a randomized controlled trial (RCT): binary feature sets from the citation (title and abstract n-grams, journal, authors, author count) and optionally from MEDLINE indexing (MeSH terms, substances), a linear SVM trained with LIBLINEAR, forward selection of whole feature sets by cross-validation, and a sigmoid fitted to the SVM margin.

The method comes from:

> Cohen AM, Smalheiser NR, McDonagh MS, Yu C, Adams CE, Davis JM, Yu PS. Automated confidence ranked classification of randomized controlled trial articles: an aid to evidence-based medicine. *J Am Med Inform Assoc* 22(3):707–717 (2015). [doi:10.1093/jamia/ocu025](https://doi.org/10.1093/jamia/ocu025)

The authors released the method only as the RCT Tagger web service, which no longer answers; no code or model was published. This package is rebuilt from the paper's text. Details the paper leaves to its supplement, which we could not obtain, are our choices and are listed below. The reproduction (pipeline, results and comparison with Tables 1–3) is in [`PMC4457112/`](../).

**Language:** Python. The paper's tools were LIBLINEAR (C, with an official Python interface) and the authors' own Python feature code (described in their 2018 paper, PMC6146117); nothing in the method depends on R.

## Install

```bash
pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC4457112/package"
```

Or with uv:

```bash
uv pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC4457112/package"
```

Python 3.10 or later, with NumPy, SciPy and `liblinear-official`.

## Use

```python
import rctconf

train = rctconf.read_citations(rctconf.example_path("citations_train.csv.gz"))
model = rctconf.train(train, [r["rct"] for r in train], rctconf.EXAMPLE_SETS)
test = rctconf.read_citations(rctconf.example_path("citations_test.csv.gz"))
for r, c in zip(test[:5], model.confidence(test[:5])):
    print(r["pmid"], round(float(c), 3))
```

From the command line:

```bash
rctconf train "$(rctconf --example-path)" -o model.npz --sets title_unigrams title_bigrams journal author_count mesh_terms
rctconf score model.npz "$(rctconf --example-path citations_test.csv.gz)" -o scores.csv
```

The [tutorial](tutorial/TUTORIAL.md) installs the package, trains on the bundled example, compares the predictions with MEDLINE's RCT publication type, and explains the input and output formats.

## What is the paper's and what is ours

| Part | Source |
| --- | --- |
| Binary features; title n-grams of length 1–3; abstract, journal, author, author-count and MeSH features; publication types never a feature | the paper |
| Author count split into ranges by Fayyad and Irani's MDL method, each a binary feature | the paper |
| LIBLINEAR linear SVM; forward selection of whole feature sets by 5×2 cross-validation on AUC and F1 | the paper |
| Tokens split on whitespace and punctuation, lower case, stop words of McCallum's Bag-Of-Words library (the SMART list), no stemming | the same group's 2018 paper (PMC6146117) |
| Feature-set list (`ALL_SETS`), keywords and substances as sets | ours |
| Solver `-s 1` (L2-loss SVM, dual), C = 1, bias term, no row scaling | ours (LIBLINEAR's defaults) |
| Forward selection: largest AUC gain at four decimals, F1 breaks ties, stop when neither improves | ours, after PMC6146117 |
| Confidence: Platt's sigmoid fitted to 2-fold out-of-fold margins, in place of the paper's "extension to the method of Rüping" | ours; the extension is described only in the supplement |
| Features as 64-bit BLAKE2b hashes of set and value | ours (exact up to hash collisions, which are negligible at 2⁶⁴) |

## Licence

MIT. See [LICENSE](LICENSE). The stop-word list `src/rctconf/data/stoplist_smart_libbow.txt` is the SMART list as built into McCallum's Bag-Of-Words library (libbow 2002-02-13, LGPL-2). The example data are described in [data/README.md](src/rctconf/data/README.md).
