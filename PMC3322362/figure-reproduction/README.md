# Figure reproduction (PMC3322362)

RPISeq encodes an RNA-protein pair as 599 numbers: 343 normalized 3-mer frequencies of the
protein over a 7-letter alphabet (conjoint triads) and 256 normalized 4-mer frequencies of the
RNA. It classifies the pair with a random forest (RPISeq-RF) or an SVM (RPISeq-SVM). The paper
ships no code and ran both classifiers in Weka 3.7.

This reproduction is built from the paper's text. Each step below implements what the Methods
say, in Python and scikit-learn 1.9.1, and where the paper is silent the choice is named. The
data are the authors' own: their lab later published the full RPI2241 dataset, positives and
negatives with sequences, in [Dobbs-Lab/RPIMotif](https://github.com/Dobbs-Lab/RPIMotif).

## Results

| Item | Status | Evidence |
| --- | --- | --- |
| Table 1, RPI2241, SVM | Agrees within run-to-run spread | 86.8%, precision 0.86, recall 0.87, F 0.87 against 87.1%, 0.87, 0.88, 0.87. Fold seeds 1 to 5 give 86.5% to 87.1%. |
| Table 1, RPI2241, RF | Agrees within run-to-run spread | 90.2%, 0.90, 0.91, 0.90 against 89.6%, 0.89, 0.90, 0.90. Forest seeds 1 to 11 give 88.9% to 90.2%. |
| Table 1, RPI369 | Other negatives; differs | Seed 1: RF 69.8% (paper 76.2%), SVM 58.8% (paper 72.8%). Seeds 1 to 10: RF 67.6% to 70.2%, SVM 58.8% to 63.7%. The paper never published RPI369's negatives. |
| Fig. 1, RPI2241 curves | Curves overlay | AUC 0.964 (RF) and 0.924 (SVM), printed 0.97 and 0.92; forest seeds give RF 0.962 to 0.966. 82.5% of the published blue curve pixels lie within 2 px of ours. |
| Fig. 1, RPI369 curves | Differs | AUC 0.80 (RF) and 0.66 (SVM) against 0.85 and 0.81; same cause as Table 1. |
| Fig. 2, SEN1 hub | SVM agrees; RF one short | Trained on RPI2241, the SVM predicts all 8 snoRNA partners of the SEN1 helicase, as the paper says; the RF predicts 7 (the eighth at P = 0.45). |
| Fig. 2, U6 hub | Partly agrees | Trained on RPI2241, the RF misses 2 and the SVM 1 of the 7 Lsm partners we test (paper: 1 of 8). |
| Tables 2 and 3 | Not reproduced; arithmetic checked | The 2011 NPInter "ncRNA binds protein" pairs are not available. Every column sum and all but one percentage agree with the printed counts; E. coli RF in Table 3, 20 of 37, is 54.05% and printed as 54.0. |
| Fig. 2A, 2B | Not reproduced | The 254 yeast NPInter pairs of 2011 are not available. |

Table 1's precision, recall and F-measure are those of the interacting class, by the formulas
in the paper's Performance Evaluation.

Earlier versions of this pipeline imitated Weka's SMO (attributes rescaled to [0, 1], the
logistic model fitted as Weka fits it) and returned the paper's SVM row exactly, 87.1%, 0.87,
0.88, 0.87. Built from the paper's text instead, the row moves by 0.3 points, inside the
spread of fold seeds.

## Methods, step by step: what the paper says and what the code does

| Step | The paper | This code | Where the paper is silent |
| --- | --- | --- | --- |
| Positives | RPI2241 (Additional File 2) and RPI369 (Additional File 3), from PRIDB complexes | Additional Files 2 and 3; sequences from the authors' RPIMotif files, whose 2,241 positives equal Additional File 2 pair for pair | The paper gives chain IDs, not sequences |
| Negatives, RPI2241 | Proteins and RNAs paired at random; pair A-B dropped if a positive C-B exists with A and C at ≥ 30% identity; balanced | The authors' published 2,241 negatives | |
| Negatives, RPI369 | Not described | `negatives369.py` applies the RPI2241 rule to RPI369's own chains, seeds 1 to 10 | The whole rule set; see Inputs |
| Protein features | 343 normalized frequencies of conjoint triads over {A,G,V} {I,L,F,P} {Y,M,T,S} {H,N,Q,W} {R,K} {D,E} {C} | `encode.py`, 3-mers over those groups | "Normalized" is deferred to Shen et al. (ref. 28); we use (f − min) / max over the 343 values, as the authors' later code does. Shen et al.'s formula is an image on PMC and was not checked here. |
| RNA features | 256 normalized frequencies of 4-mers | `encode.py`, 4-mers over A, C, G, U, same normalization | k-mers containing N or another non-RNA letter are not counted (65 of 4,482 pairs have one, mostly N); T is read as U |
| SVM | SMO, "normalized polykernel function of order 2 with ε = 1.0E-12", C = 1.0, tolerance T = 0.0010, a logistic model fitted "to the output of the resulting SVM classifier" | `SVC(C=1.0, tol=0.001)` on k(x,y)/√(k(x,x)k(y,y)) with k = (x·y)², then a logistic regression on that SVM's decision values on its training data | Features are not rescaled (the paper mentions no scaling). ε is the round-off threshold of Weka's SMO solver; libsvm, which `SVC` runs, has no such setting. |
| RF | 20 trees, 10 features at each node, each tree on a random sample of the training set, majority vote | `RandomForestClassifier(n_estimators=20, max_features=10, bootstrap=True, random_state=1)`; P(interact) is the fraction of trees voting "interact" | |
| Decision | P ≥ 0.5 counts as an interaction (Tables 2 and 3, Fig. 2C) | P ≥ 0.5 | |
| Evaluation | "Standard 10-fold cross-validation"; accuracy, precision, recall, F-measure, ROC AUC | `StratifiedKFold`, 10 folds, shuffled, seed 1; per-pair predictions saved | Stratification and fold seed |

Two of these choices move results, and we checked how much on RPI2241:

- **Where the logistic model is fitted.** On the SVM's own training outputs, as above, the SVM
  gives 86.8%. scikit-learn's `CalibratedClassifierCV`, which fits it on held-out folds of five
  further SVMs, gives 84.8% (recall 0.80). We follow the paper's wording, "the resulting SVM
  classifier".
- **Unknown letters in RNAs.** Skipping k-mers with N, rather than counting N as A as the
  authors' later code does, changes 65 of the 4,482 RPI2241 feature vectors. The SVM moves by
  at most 0.1 points; the forest is regrown from different data and moves within its seed
  spread.

Rescaling the features to [0, 1] first, as Weka does by default, changes the SVM by 0.2 points.

## Inputs

- **RPI2241**: Dobbs-Lab/RPIMotif `Data/Positive_Fasta_RPI2241.txt` and
  `Data/Negative_Fasta_RPI2241.txt` at commit 9cfa951.
- **RPI369**: Additional File 3's 369 positives (all within RPI2241, sequences from the file
  above). The paper describes no negatives for RPI369 and no source holds them.
  `pipeline/negatives369.py` draws them by the paper's RPI2241 rule: random protein and RNA
  from RPI369's pairs, dropped when the protein shares 30% identity or more with a known
  partner of that RNA. Seeds 1 to 10 are run; seed 1 is shown. IPMiner's RPI369 negatives
  (Pan et al. 2016: non-interacting chains of the same complex) are also run and reported:
  RF 70.5% (AUC 0.755), SVM 71.3% (AUC 0.742). In an exploratory Weka run outside the
  pipeline, 369 negatives taken from the authors' RPI2241 negatives whose RNA is in RPI369 gave
  RF 87 to 88% (AUC 0.95). The paper's 76.2% and 0.85 sit between these, so the RPI369 rows
  depend on a choice the paper does not record.
- **Fig. 2 hubs** (`pipeline/inputs/fig2c_hubs.tsv`): SEN1 (UniProt Q00416) with the eight
  snoRNAs that NPInter lists from the paper's ref. 38 (snR5, 10, 11, 13, 30, 31, 42, 45), and
  the snRNA hub. The paper calls that snRNA "u4560" and cites ref. 39, Vidal et al. 1999,
  "Characterization of U6 snRNA-protein interactions"; we take it to be U6 (snR6) and test it
  with Lsm2 to Lsm8. The paper counts 8 partners but names none, so the U6 counts are out of 7.
  Sequences from UniProt and SGD.
- **The paper's AUCs.** The abstract gives 0.96 and 0.92 for the two datasets; Results and
  Fig. 1 give 0.97 and 0.92 (RPI2241) and 0.85 and 0.81 (RPI369).

`pipeline/fetch_inputs.sh` downloads the data files and checks each SHA-256.

## Not attempted

- The comparison with Pancaldi and Bähler (text only, no figure or table): it needs the Hogan
  et al. mRNA-protein pairs and their negatives, which the paper does not give.
- Additional File 1, the feature-selection list (Weka's wrapper subset evaluator with best-first
  search): not a figure or table.

## Fitted presentation parameters

Fig. 1 is a MATLAB plot, drawn here with matplotlib in MATLAB's default look
(`pipeline/params/fig1.json`). Measured from the published image: the 600 × 466 px frame, the
axes box (x 65 to 549, y 34 to 407), the legend frame and the AUC label positions. Fitted to the
measured text sizes: font sizes (tick labels 9 pt, axis titles 11.5 pt bold, AUC labels
10.5 pt), legend spacing and handle length. Arial, or Liberation Sans in CI (same metrics).

## Layout

| Path | Content |
| --- | --- |
| `main.nf`, `nextflow.config` | Nextflow pipeline that runs every step below. |
| `pipeline/encode.py` | RPISeq's 599 features, written as ARFF. |
| `pipeline/negatives369.py` | RPI369 negatives by the paper's rule. |
| `pipeline/rpi_sklearn.py` | RPISeq-RF and RPISeq-SVM in scikit-learn: cross-validation with per-row predictions, and train-and-predict. |
| `pipeline/fig1.py`, `pipeline/compare_fig1.py` | Fig. 1 on the published pixel grid; curve-by-curve comparison. |
| `pipeline/compare_figure.py` | Whole-figure alignment and difference report, from Paper2Repro (MIT). |
| `pipeline/make_tables.py`, `pipeline/check_reproduction.py` | Collect results; the check step. |
| `pipeline/inputs/fig2c_hubs.tsv` | The 15 yeast hub pairs with sequences. |
| `published/` | Figs 1 and 2 of the paper (CC BY 2.0). |
| `output/` | Fig. 1 (PNG, PDF, comparison), cross-validation summaries and predictions, `tables.json`, `report.md`. |

## Run

```bash
nextflow run PMC3322362/figure-reproduction/main.nf --outdir results
```

Needs Python 3.12 with numpy, scipy, matplotlib, pillow, biopython and scikit-learn 1.9.1, and
Nextflow. The whole pipeline takes a few minutes on one core. The check step fails if, on
RPI2241, either classifier's accuracy is more than 1 point from Table 1, either AUC more than
0.01 from Fig. 1, fewer than 75% of the published blue curve pixels lie within 2 px of ours,
or either classifier predicts fewer than 7 of SEN1's 8 snoRNA partners. These margins cover
the spread of fold and forest seeds above, not a different result.
