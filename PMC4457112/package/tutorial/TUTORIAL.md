<!-- Generated from tutorial.ipynb by check_package.py --write. Do not edit by hand. -->

# rctconf tutorial

`rctconf` gives each MEDLINE citation a confidence that it reports a randomized controlled trial (RCT). It turns the citation into binary feature sets (title and abstract n-grams, journal, authors, author count, and optionally MeSH terms and substances), trains a linear SVM with LIBLINEAR, and maps the SVM margin to a confidence with a fitted sigmoid.

It is a rebuild, from the paper's text, of the method of Cohen AM, Smalheiser NR, McDonagh MS, Yu C, Adams CE, Davis JM, Yu PS. Automated confidence ranked classification of randomized controlled trial articles: an aid to evidence-based medicine. *J Am Med Inform Assoc* 22(3):707-717 (2015). doi:10.1093/jamia/ocu025. The authors' RCT Tagger was never released as code, and its web service is gone.

## 1. Install

```bash
pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC4457112/package"
```

Or with uv:

```bash
uv pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC4457112/package"
```

It needs Python 3.10 or later, NumPy, SciPy and LIBLINEAR's official Python package (`liblinear-official`).

```python
import rctconf

print("rctconf", rctconf.__version__)
```

```text
rctconf 0.1.0
```

## 2. The example input

The package ships 1,500 training citations from 2010 and 500 test citations from 2011, taken from the PubMed 2026 baseline: human-related, in English, with an abstract. RCTs are over-sampled to 20%. Only the title, journal, author count, MeSH descriptors and substances are bundled (no abstracts), so the example uses those feature sets. `data/README.md` says how the files were made.

```python
train = rctconf.read_citations(rctconf.example_path("citations_train.csv.gz"))
test = rctconf.read_citations(rctconf.example_path("citations_test.csv.gz"))
print(len(train), "training citations,", sum(r["rct"] for r in train), "with the RCT publication type")
print(len(test), "test citations; columns:", ", ".join(test[0]))
for r in train[:3]:
    print(r["pmid"], r["rct"], r["journal"], "|", r["title"][:70])
```

```text
1500 training citations, 300 with the RCT publication type
500 test citations; columns: pmid, title, journal, n_authors, mesh, chemicals
20129750 0 Magn Reson Imaging | Off-resonance frequency filtered magnetic resonance imaging.
20130132 0 J Gen Virol | A mutation in H5 haemagglutinin that conferred human receptor recognit
20130894 0 Arch Dermatol Res | Clearance of experimental cutaneous Staphylococcus aureus infections i
```

## 3. Train and score

`rctconf.train` builds the feature sets, fits the author-count ranges (Fayyad and Irani's MDL method), trains LIBLINEAR and fits the confidence sigmoid to out-of-fold margins. `model.margins` and `model.confidence` score new citations.

```python
model = rctconf.train(train, [r["rct"] for r in train], rctconf.EXAMPLE_SETS)
print(model.n_features, "features in", len(model.sets), "sets:", ", ".join(model.sets))

margins = model.margins(test)
confidence = model.confidence_from_margins(margins)
ranked = sorted(zip(confidence, test), key=lambda x: -x[0])
print("highest confidence:")
for c, r in ranked[:5]:
    print(f"  {c:.3f}  {r['pmid']}  {r['title'][:70]}")
print("lowest confidence:")
for c, r in ranked[-3:]:
    print(f"  {c:.3f}  {r['pmid']}  {r['title'][:70]}")
```

```text
29147 features in 7 sets: title_unigrams, title_bigrams, journal, author_count, mesh_terms, mesh_major, chemicals
highest confidence:
  1.000  21591581  Lack of beneficial effects of granulocyte colony-stimulating factor in
  1.000  21741092  Immunologic effects and tolerability profile of in-season initiation o
  1.000  20851499  Early treatment of cold sores with topical ME-609 decreases the freque
  1.000  21519733  Safety of oral glutamine in the abbreviation of preoperative fasting:
  1.000  21285525  Effectiveness of myofascial trigger point manual therapy combined with
lowest confidence:
  0.002  21481115  Parental perceptions of end-of-life care on paediatric intensive care
  0.001  21673090  Truncated ErbB2 expressed in tumor cell nuclei contributes to acquired
  0.001  21371186  Application of UKHCDO 2004 guidelines in type 1 von Willebrand Disease
```

## 4. Compare with the expected output

The expected output is MEDLINE's own RCT publication type for the 500 test citations, assigned by NLM indexers, not by this package. The paper's full models reach an AUC of about 0.97 on all 2011 citations; this small example, without abstracts, should still rank most RCTs first.

```python
import csv

with open(rctconf.example_path("citations_test_expected.csv"), newline="") as fh:
    expected = {r["pmid"]: int(r["rct"]) for r in csv.DictReader(fh)}
y = [expected[r["pmid"]] for r in test]
m = rctconf.evaluate(y, margins, confidence, rctconf.zero_sigmoid(margins))
agree = sum((f > 0) == (label == 1) for f, label in zip(margins, y))
print(f"{agree} of {len(y)} test citations agree with MEDLINE's RCT publication type")
print(f"AUC {m['auc']:.3f} (95% CI {m['auc_ci_low']:.3f} to {m['auc_ci_high']:.3f}), "
      f"average precision {m['average_precision']:.3f}, F1 {m['f1']:.3f}")
print(f"MSE of the confidence {m['mse']:.3f}; of a zero-centred sigmoid of the margin {m['mse_sigmoid']:.3f}")
assert m["auc"] >= 0.90 and agree >= 0.85 * len(y)
```

```text
450 of 500 test citations agree with MEDLINE's RCT publication type
AUC 0.921 (95% CI 0.884 to 0.958), average precision 0.837, F1 0.713
MSE of the confidence 0.073; of a zero-centred sigmoid of the margin 0.121
```

## 5. From the command line

The same steps run as `rctconf train` and `rctconf score`. Without `-o`, `score` writes the CSV to standard output.

```python
train_path = rctconf.example_path("citations_train.csv.gz")
test_path = rctconf.example_path("citations_test.csv.gz")
!rctconf train "{train_path}" -o example_model.npz --sets title_unigrams title_bigrams journal author_count mesh_terms mesh_major chemicals
!rctconf score example_model.npz "{test_path}" -o example_scores.csv
!head -4 example_scores.csv
```

```text
example_model.npz: 29147 features, 1500 citations
pmid,margin,confidence
20187071,-0.655943,0.099612
20202787,-0.518927,0.167992
20204548,0.068835,0.727276
```

## 6. Your own data

- **Input:** a CSV (optionally gzipped) with a header row and a `pmid` column. The other columns are optional: `title`, `abstract`, `journal`, `authors` (`|`-joined "Last Initials"), `n_authors`, `mesh` (`|`-joined MeSH descriptor UIs, `*` before a major topic), `mesh_qual` (`D.../Q...` pairs), `chemicals` (substance UIs), `keywords`, `pubtypes` (publication type UIs) and, for training, `rct` (1 or 0).
- **Feature sets:** `rctconf.CITATION_SETS` need only the citation, so they work before MEDLINE indexing; `rctconf.MESH_SETS` add the MeSH indexing. The paper chose its sets by forward selection (`rctconf.forward_select`). Train on tens of thousands of citations or more: the paper used 7.5% of 1987-2010, about 390,000.
- **Output:** `margin` is the SVM's signed distance (RCT when above 0) and `confidence` the fitted probability that the citation reports an RCT. Rank by either.
- **Measures:** `rctconf.evaluate(labels, margins, confidence)` gives the paper's AUC with its Hanley-McNeil interval, average precision, F1, accuracy and MSE.

## 7. The reproduction

The full reproduction retrains both of the paper's models on 6.3 million citations of the PubMed 2026 baseline and compares them with Tables 1-3: [results page](https://jeonglab-bcm.github.io/fossil/PMC4457112/), [pipeline](https://github.com/jeonglab-bcm/fossil/tree/main/PMC4457112/figure-reproduction).
