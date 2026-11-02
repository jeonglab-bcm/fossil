# Figure reproduction (PMC3322362)

RPISeq encodes an RNA-protein pair as 599 numbers: 343 normalized 3-mer counts of the protein
over a 7-letter alphabet (conjoint triads) and 256 normalized 4-mer counts of the RNA. It
classifies the pair with a random forest (RPISeq-RF) or an SVM (RPISeq-SVM), both in Weka 3.7.
The paper ships no code, but the authors' lab later published the feature code
("Usha's conjoint triads" in `createARFF_test.pl`) and the full RPI2241 dataset, positives and
negatives with sequences, in [Dobbs-Lab/RPIMotif](https://github.com/Dobbs-Lab/RPIMotif). Its
2,241 positives are those of Additional File 2, in the same order.

We rerun the paper's 10-fold cross-validations with Weka 3.7.5 (the earliest 3.7 release on
Maven Central; the paper says 3.7) and the settings of its Methods, on the authors' RPI2241 data
and on RPI369.

## Results

| Item | Status | Evidence |
| --- | --- | --- |
| Table 1, RPI2241, SVM | **Identical at the printed precision** | 87.1%, precision 0.87, recall 0.88, F 0.87, as printed. 1,962 true positives, 279 false negatives, 299 false positives, 1,942 true negatives. |
| Table 1, RPI2241, RF | Same setup, close | 90.1%, 0.92, 0.88, 0.90 against 89.6%, 0.89, 0.90, 0.90. Eleven forest seeds give 89.8% to 90.5%. |
| Table 1, RPI369 | Same setup, other negatives; differs | Seed 1: RF 68.8% (paper 76.2%), SVM 60.4% (paper 72.8%); seeds 1 to 10 give 68.4 to 71.3% and 60.2 to 64.1%. The paper never published RPI369's negatives. |
| Fig. 1, RPI2241 curves | Same setup, curves overlay | AUC 0.967 (RF) and 0.923 (SVM), printed 0.97 and 0.92. 96.4% of the published blue curve pixels lie within 2 px of ours. |
| Fig. 1, RPI369 curves | Differs | AUC 0.78 (RF) and 0.66 (SVM) against 0.85 and 0.81 (seeds 1 to 10: 0.78 to 0.82 and 0.66 to 0.70); same cause as Table 1. |
| Fig. 2, SEN1 hub | Same setup, agrees | Trained on RPI2241, RF and SVM both predict all 8 snoRNA partners of the SEN1 helicase, as the paper says. |
| Fig. 2, U6 hub | Partly agrees | Trained on RPI2241, RF misses 1 of the 7 Lsm partners we test (paper: 1 of 8) and SVM misses 2. |
| Fig. 2C, RPI369 models | Differs | With our RPI369 negatives: RF 7 of 8 SEN1 and 1 of 7 U6 partners (paper 4 and 6 of 8), SVM 8 of 8 and 4 of 7 (paper 6 and 8 of 8). |
| Tables 2 and 3 | Not reproduced; arithmetic checked | The 2011 NPInter "ncRNA binds protein" pairs are not available. Every column sum and all but one percentage agree with the printed counts; E. coli RF in Table 3, 20 of 37, is 54.05% and printed as 54.0. |
| Fig. 2A, 2B | Not reproduced | The 254 yeast NPInter pairs of 2011 are not available. |

Table 1's precision, recall and F-measure are those of the interacting class. With them the
SVM row equals the paper's; Weka's weighted averages give recall 0.87, not 0.88.

## Inputs

- **RPI2241**: Dobbs-Lab/RPIMotif `Data/Positive_Fasta_RPI2241.txt` and
  `Data/Negative_Fasta_RPI2241.txt` at commit 9cfa951. The positives equal Additional File 2
  pair for pair and in order. The negatives pair proteins and RNAs from different complexes,
  as the Methods describe.
- **RPI369**: Additional File 3's 369 positives (all within RPI2241, sequences from the file
  above). No source holds the authors' 369 negatives. `pipeline/negatives369.py` draws them by
  the Methods' rule: random protein and RNA from RPI369's pairs, dropped when the protein shares
  30% identity or more with a known partner of that RNA. Seeds 1 to 10 are run; seed 1 is shown.
  Two other negative sets were tried and are reported, not used: IPMiner's (Pan et al. 2016:
  non-interacting chains of the same complex; RF 70.2%, AUC 0.75; SVM 71.5%, AUC 0.74, near the paper's 72.8%) and 369 drawn from the
  authors' RPI2241 negatives whose RNA is in RPI369 (RF 87 to 88%, AUC 0.95). The paper's 76.2%
  and 0.85 sit between them, so the RPI369 rows depend on a choice the paper does not record.
- **Fig. 2 hubs** (`pipeline/inputs/fig2c_hubs.tsv`): SEN1 (UniProt Q00416) with the eight
  snoRNAs that NPInter lists from the paper's ref. 38 (snR5, 10, 11, 13, 30, 31, 42, 45), and U6
  snRNA (snR6) with Lsm2 to Lsm8 (ref. 39). Sequences from UniProt and SGD. The paper's figure
  names neither the snoRNAs nor its eighth U6 partner.
- **Weka 3.7.5** and `pentaho-package-manager` 0.9.9 from Maven Central. Weka 3.7.3 and 3.7.4,
  the releases of the paper's time, are only on SourceForge. Weka 3.7.6 gives the same RF result
  as 3.7.5; 3.7.9 gives 89.9%.

`pipeline/fetch_inputs.sh` downloads all of these and checks each SHA-256.

## What the code does, against the paper

- **Features.** `pipeline/encode.py` follows the Perl code line by line, including two quirks:
  its filter for letters outside the alphabets never matches (the pattern string contains the
  slashes), so an unknown residue or base counts as group 0 (A, G, V or A); and numbers are
  written with Perl's 15 significant digits. Each block is scaled as (count − min) / max.
- **SVM.** Weka's SMO, normalized polykernel of exponent 2, C = 1.0, tolerance 0.001,
  epsilon 1.0E-12, logistic models fitted to the outputs, as the Methods say.
- **RF.** Weka's RandomForest with 20 trees and 10 features per node (seed 1).
- **Cross-validation.** Weka's stratified 10-fold split with seed 1, positives first and
  negatives second in file order. That the SVM row comes back exactly suggests the authors'
  folds were the same.
- **AUC in the abstract.** The abstract gives AUCs of 0.96 and 0.92 for the two datasets;
  Results and Fig. 1 give 0.97 and 0.92 (RPI2241) and 0.85 and 0.81 (RPI369).

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
| `pipeline/encode.py` | RPISeq's 599 features, written as Weka ARFF. |
| `pipeline/negatives369.py` | RPI369 negatives by the paper's rule. |
| `pipeline/RpiWeka.java` | Weka driver: cross-validation with per-row predictions, and train-and-predict. |
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

Needs Python 3.12 with numpy, scipy, matplotlib, pillow and biopython, a JDK (Java 21 tested)
and Nextflow. The RPI2241 SVM cross-validation takes about 13 minutes on one core. The check
step fails if the SVM row of Table 1, the RPI2241 AUCs, the Fig. 1 blue-curve overlay or the
SEN1 predictions stop agreeing with the paper.
