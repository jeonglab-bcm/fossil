# PMC4015815 figure reproduction

Table 1 (the SVM-DR and SVM-DT rows), Figures 3, 4 and 5 and the claims in the text of Liu, Xu,
Zou, Xu, Wang and Chen (2014), rerun on the SCOP 1.53 benchmark. The authors' DistanceSVM
package and server are gone (bioinformatics.hitsz.edu.cn answers 503), so the method is rebuilt
from the paper: the feature vectors from its Eq. 1–2 and Fig. 2, the SVM by porting Gist 2.3 (the
package and "default parameters" the paper names) from its C source, and the profiles with
PSI-BLAST against the same lab's later nrdb90.

## Run

```bash
# From the repository root, with the committed Top-1-gram sequences (about 40 min on 4 cores;
# add --dmax 10,20,40,50,60,80,100,150,200 to read the slow dMAX = 0 points from output/):
nextflow run PMC4015815/figure-reproduction/main.nf --outdir results

# Everything, PSI-BLAST included (about 4 CPU hours more; downloads Pse-in-One 2.0's nrdb90 and BLAST+):
nextflow run PMC4015815/figure-reproduction/main.nf --outdir results --profiles

# The same steps without Nextflow (how the committed output/ was written):
bash PMC4015815/figure-reproduction/run_local.sh results
```

Needs Python 3.12 with the packages in `requirements.txt` (numpy, scipy, numba, pillow,
pymupdf). `.github/workflows/reproduce-pmc4015815.yml` runs the pipeline on `ubuntu-24.04`
(x86_64) at dMAX 10–200 on pull requests and pushes, and with dMAX = 0 when started by hand
(`dmax_zero`), then checks it against `results.json` and the committed outputs.

## Results

From `check_results.py ../results.json --markdown` on the committed run:

| Item | Verdict | Measure | Why |
| --- | --- | --- | --- |
| Gist 2.3 port against Gist's own sample run | agrees | Gist's printed weights through our kernel give its printed training discriminants within 0.003 (weight rounding). Retrained with the sample's settings and seed: objective 0.0173670 against Gist's 0.0173686, 1591 of 1644 weights equal as printed, 196 passes against 200. The sample came from Gist 2.0. |  |
| Fig. 1 | not attempted | not attempted | A worked example of the feature vector (AGLP to KFFK, dMAX = 2); nothing to recompute. |
| Fig. 2 | not attempted | not attempted | Pseudocode of the Distance-based Top-1-gram vector; it is the method, implemented in features.py. |
| Fig. 3, SVM-DR curve | partly | 84.40% within 2 px (pass 85.0%, best control 75.9%) | Nine of ten points come back within 0.0005 ROC; dMAX 20 is 0.0013 above the published point (0.9004 against 0.8991, about 10 px). |
| Fig. 3, SVM-DT curve | inconclusive | 0.43% within 2 px (pass 85.0%, best control 4.6%) | The SVM-DT curve rises and flattens as published, but our profiles are not the paper's; the points sit up to a few thousandths of ROC from the published ones. |
| Fig. 3, SVM-DR points (values) | partly | 9 of 10 fields as printed | Nine of ten points come back within 0.0005 ROC; dMAX 20 is 0.0013 above the published point (0.9004 against 0.8991, about 10 px). |
| Fig. 3, SVM-DT points (values) | differs | 0 of 10 fields as printed | The SVM-DT curve rises and flattens as published, but our profiles are not the paper's; the points sit up to a few thousandths of ROC from the published ones. |
| Table 1, SVM-DR (ROC, ROC50) | partly | 1 of 2 fields as printed | ROC comes back exactly (0.919); ROC50 does not (0.497 against 0.715). Our ROC matches at every dMAX, so the rankings agree; the gap is in how ROC50 was computed, which the paper's one-line definition does not settle. |
| Table 1, SVM-DT (ROC, ROC50) | differs | 0 of 2 fields as printed | Two causes: the profiles (2016 database, settings from the lab's 2017 code) move ROC by a few thousandths, and ROC50 is computed some other way than the stated definition (see Table 1, SVM-DR). |
| Table 1, the nine other methods | not attempted | not attempted | Quoted by the paper from earlier work (Monomer-dist, SVM-LA, SVM-Pairwise, SVM-Top-n-gram and -LSA, SVM-PDT-Profile, PseAACIndex-Profile, BioSVM-2L, HHSearch); not results of this paper. |
| Fig. 4A, Top-1-gram pairs (SVM-DT) | partly | 73.25% within 24 grey levels per cell px (pass 95.0%, best control 69.2%) | Our Top-1-gram sequences come from a 2016 database with PSI-BLAST settings taken from the lab's 2017 code; the 2014 profiles are gone. The SVM-DT heatmap keeps (G,G) on top but (L,L) drops, and its correlation with the published panel is little better than the SVM-DR panel's. |
| Fig. 4B, residue pairs (SVM-DR) | agrees | 100.00% within 24 grey levels per cell px (pass 95.0%, best control 71.8%) | Assumed: The L2 norm of a pair (t_i, t_i) includes its distance-0 weight (the composition T0_i), as Fig. 1 counts pairs 'at distance 0, 1, 2' |
| Fig. 5A, (G,G) of SVM-DT | inconclusive | 12.84% within 2 px (pass 98.0%, best control 12.8%) | As Fig. 4A: our SVM-DT weights come from other profiles. The ladder shape and the mostly negative signs come back; the bar heights do not. |
| Fig. 5B, (L,L) of SVM-DT | partly | 10.81% within 2 px (pass 98.0%, best control 9.5%) | As Fig. 4A: our SVM-DT weights come from other profiles. The ladder shape and the mostly negative signs come back; the bar heights do not. |
| Fig. 5C, (G,G) of SVM-DR | agrees | 100.00% within 2 px (pass 98.0%, best control 89.9%) | Assumed: The bars are plotted at x = d + 1 (the bar at x shows distance x - 1; x = 1 is distance 0) |
| Fig. 5D, (L,L) of SVM-DR | agrees | 100.00% within 2 px (pass 98.0%, best control 96.6%) | Assumed: The bars are plotted at x = d + 1 (the bar at x shows distance x - 1; x = 1 is distance 0) |
| Claims recomputed from the paper's own Table 1 | agrees | From Table 1's printed values: SVM-DT minus SVM-Top-n-gram is 4.1 ROC and 10.4 ROC50 points (text: 4.1 and 10.4), and the five comparison sentences hold on the paper's own numbers (with 'outperforms Monomer-dist' resting on ROC50: both rows print ROC 0.919). |  |
| Benchmark: 54 families, 4,352 proteins | exact | 2 of 2 fields as printed |  |
| SVM-DT improves SVM-Top-n-gram by 4.1% ROC and 10.4% ROC50 | differs | 0 of 2 fields as printed | The gains are measured against SVM-Top-n-gram's values quoted from another paper. Our ROC gain is 4.3 points (paper 4.1); our ROC50 is lower across the board, so against the quoted 0.696 it shows a loss. Against our own position-independent baseline (SVM-DT at dMAX 0, Top-1-gram composition) the gains are 4.0 ROC and 25.7 ROC50 points, so the direction of the claim holds. |
| Family 2.5.1.3: SVM-DT 0.993 against SVM-DR 0.844 (ROC) | partly | 1 of 2 fields as printed | SVM-DR comes back (0.844); SVM-DT is 0.961 against 0.993, from other profiles. It still beats SVM-DR on this family by a wide margin. |
| ROC rises from dMAX 0 to 100 and is stable over 100 to 200 | agrees | 2 of 2 fields as printed | Assumed: PSI-BLAST profiles from the lab's 2016 nrdb90 (Pse-in-One 2.0), 3 iterations, E = 0.001, BLAST+ 2.17.0; Top-1-gram = largest weighted observed percentage, an all-zero column giving the query residue |
| (G,G) and (L,L) are the two most discriminative pairs for both methods | partly | 1 of 2 fields as printed | True for SVM-DR. For SVM-DT (G,G) comes first but (L,L) is sixth, behind (V,G) and (G,V): our Top-1-gram sequences come from other profiles. |
| Distance 0 always has the largest weight (Fig. 5) | agrees | 3 of 3 fields as printed, 1 paper errors | Assumed: PSI-BLAST profiles from the lab's 2016 nrdb90 (Pse-in-One 2.0), 3 iterations, E = 0.001, BLAST+ 2.17.0; Top-1-gram = largest weighted observed percentage, an all-zero column giving the query residue |
| Shorter distances weigh more than longer ones (Fig. 5) | agrees | 4 of 4 fields as printed | Assumed: PSI-BLAST profiles from the lab's 2016 nrdb90 (Pse-in-One 2.0), 3 iterations, E = 0.001, BLAST+ 2.17.0; Top-1-gram = largest weighted observed percentage, an all-zero column giving the query residue |
| Most (G,G) weights of SVM-DT are positive; SVM-DR has more positive ones | agrees | 1 of 1 fields as printed, 1 paper errors | Assumed: PSI-BLAST profiles from the lab's 2016 nrdb90 (Pse-in-One 2.0), 3 iterations, E = 0.001, BLAST+ 2.17.0; Top-1-gram = largest weighted observed percentage, an all-zero column giving the query residue |
| SVM-DR outperforms Monomer-dist and SVM-Pairwise and is comparable with SVM-LA | partly | 2 of 3 fields as printed | SVM-DR beats SVM-Pairwise and is within a point of SVM-LA. 'Outperforms Monomer-dist' rests on ROC50 (both rows print ROC 0.919), and our ROC50 (0.497) is computed differently from the paper's (see Table 1). |
| SVM-DT outperforms every other method except SVM-PDT-Profile in average ROC | partly | 1 of 2 fields as printed | Our SVM-DT reaches ROC 0.9502, above every quoted profile method including SVM-PDT-Profile (0.950) by 0.0002; with Pse-in-One's Top-1-gram rule it is 0.9412, below it. The ranking against SVM-PDT-Profile turns on the profiles. |

1 exact, 9 agrees, 9 partly, 2 inconclusive, 3 differs, 3 not attempted; 6 open causes.


## What the code does against the paper

| Step | Paper | Here |
| --- | --- | --- |
| Benchmark | SCOP 1.53, 54 families, 4,352 proteins (Liao and Noble's svm-pairwise page) | The same files, by checksum. Codes 1/2 train, 3/4 test. |
| DR features | Counts of residues (distance 0) and of ordered residue pairs at distances 1..dMAX; 20 + 400 dMAX dimensions (Eq. 1–2, Fig. 2) | `features.py`. x/X residues (529 of 560,022) are not counted, alone or in a pair. Pse-in-One 2.0's `dr_method` (the lab's 2017 code) counts the same way. |
| DT features | The same on the Top-1-gram sequence: the most frequent amino acid of each column of a PSI-BLAST frequency profile against "a non-redundant database" | `run_psiblast.sh` and `top1.py`: BLAST+ 2.17.0, 3 iterations, E = 0.001, against the lab's 2016 nrdb90 (Pse-in-One 2.0), the largest "weighted observed percentage" per column, ties to the first in ARNDCQEGHILKMFPSTWYV order. These settings come from Pse-in-One 2.0's `profile.py`, not from the paper. |
| SVM | Gist 2.3, default parameters | `gist_port.py`: Gist 2.3's `gist-train-svm` and `gist-classify` with no options, ported line by line (normalized linear kernel + 10, 2-norm soft margin with diagonal factor 0.1, Jaakkola's coordinate updates in drand48 order, convergence 1e-6, weights written with `%.4g`). One change, below. |
| Scores | ROC and ROC50 per family, averaged | `roc.py`: Gribskov and Robinson's ROC_n with n = all negatives and n = 50. |
| dMAX | "between 0 and the longest sequence"; 150 for the results | 0, 10, 20, 40, 50, 60, 80, 100, 150, 200: Figure 3's markers. |
| Weights | w = M α (Eq. 3); L2 norm per pair; family 2.5.1.3 | `discriminant_weights.py`: α = Gist's signed weights as written, M = raw count vectors, w summed over training rows. |

### The port and its one change

Gist 2.3 could not be built here, so it was ported from its source (`gist_port.py`, with the
file and function each step comes from). `port_check.py` checks the port on Gist's own sample
run (`doc/sample.weights`, written by Gist 2.0 with non-default options): Gist's printed weights
through our kernel give its printed training discriminants within 0.003 (the weights' 4-digit
rounding), and retraining with the same settings and seed reaches its objective within 1.6e-6.

The change: Gist's normalization sets a normalized value above 1 to 0 off the diagonal. The
benchmark holds identical sequences (for example the four chains d1bdxa1–d1bdxd1), and on x86-64
doubles K/(√K·√K) comes out 1 + 2⁻⁵² for some of them (279 pairs at dMAX = 0, 1,535 at 150). The
0 makes the kernel indefinite. At dMAX = 0 the updates then diverge to NaN, and Gist's loop
never ends, so the published run cannot have done this. We cap those values at 1. The capped
kernel gives the published weights (Fig. 4B Spearman 0.9999, Fig. 5C–D bars r ≥ 0.9997); Gist's
rule gives weights 1.3 times too large (Spearman 0.963, r 0.85 and 0.76;
`output/causes/weight_scale_dr.json`). A 32-bit x87 build of Gist, which keeps these values at
exactly 1, would behave like the cap.

## What the figures pinned down

1. **Fig. 3's grid.** The markers sit at dMAX 0, 10, 20, 40, 50, 60, 80, 100, 150 and 200 on the
   tick-fitted axis (largest tick residual 0.75 px). The paper names only 150.
2. **Fig. 4's L2 norm includes distance 0.** Fig. 1 counts "Top-1-gram pairs at distance 0, 1,
   2", the pairs at distance 0 being (tᵢ, tᵢ). With the composition weight in the diagonal cells our
   SVM-DR panel has maximum 78.1 (paper 78) and Spearman 0.9999; without it, 76.8 and 0.988, and
   (L,L) falls from second to 36th.
3. **Fig. 5 is plotted at x = d + 1.** The bar at x shows distance x − 1, as if the 151 weights
   (distance 0 to 150) were plotted against their row numbers. The correlation with our SVM-DR bars is
   1.000 at that offset and between −0.09 and 0.03 at x = d.
4. **The sign of the weights.** w = Σ αᵢyᵢxᵢ with Gist's signed weights as written gives the
   published signs; 81–83% of the SVM-DR bars are negative in both.
5. **Profile columns with no counts.** 9,042 of the 560,022 PSSM columns have all-zero observed
   percentages. Pse-in-One 2.0's parser turns them into A; the paper's definition (the most
   frequent residue of a profile that includes the query) gives the query residue, which we use.
   The choice moves SVM-DT's mean ROC at dMAX 150 from 0.9412 to 0.9502 (paper 0.948).

## ROC50

Our ROC agrees at every dMAX for SVM-DR, but our ROC50 (Gribskov and Robinson's normalized area to
the first 50 false positives, the paper's wording) is 0.497 against 0.715. Tested
(`output/causes/roc50_variants.json`): the true-positive rate at the 50th false positive (0.662),
the seed (0.4973) and ROC_n for other n. ROC_200 gives 0.720 for SVM-DR; for SVM-DT, whose ROC
also differs, 0.819 against 0.800. We do not know how the paper computed ROC50. Because the
paper's other rows are quoted from papers that may define ROC50 differently again, comparisons on
ROC50 (the gain over SVM-Top-n-gram, SVM-DR against Monomer-dist) are not settled here either.


## Layout

| Path | Content |
| --- | --- |
| `main.nf`, `nextflow.config` | The pipeline. `run_local.sh` runs the same steps without Nextflow. |
| `results.json` | What CI checks (`tools/check_results.py`): the values the reproduction stands on, with tolerances. |
| `results_notes.json` | Labels, sources, assumptions, causes and pass marks, written by hand; `build_results.py` merges them with the pipeline's numbers into `../results.json`. |
| `pipeline/` | The scripts; `inputs/top1_nrdb90_i3.fasta.gz` (our Top-1-gram sequences, written by `--profiles`); `params/SHA256SUMS`. |
| `published/` | Figures 3, 4 and 5 as embedded in the PMC open-access PDF (1,200 px PNG), under CC BY 2.0. |
| `output/` | The committed run: sweeps, weights, renders (`fig*_ours.png`), overlays, scores, `tables.json`, `report.md`, and `causes/` (hypothesis tests, not part of the pipeline). |

## Pipeline steps

| Process | Script | What it does |
| --- | --- | --- |
| FETCH | `fetch_inputs.sh` | Benchmark, Gist 2.3 source, the paper's PDF; with `--profiles` also Pse-in-One 2.0 and BLAST+. Checked against `params/SHA256SUMS`. |
| FIGURES_CHECK | `extract_figures.py` | The committed `published/` figures equal the PDF's embedded images. |
| PORT_CHECK | `port_check.py` | The Gist port against Gist's sample run. |
| PROFILES (`--profiles`) | `run_psiblast.sh`, `top1.py` | PSI-BLAST for all 4,352 sequences; Top-1-gram sequences. |
| SWEEP | `run_sweep.py`, `merge_sweep.py` | Train and test on 54 families at each dMAX, for DR and DT; dMAX values not run are copied from `output/`. |
| WEIGHTS | `discriminant_weights.py` | w for families 2.5.1.3 (Figs 4–5) and 2.5.1.1 (control). |
| FIGURES | `figure3_axes.py`, `figure3.py`, `figure4.py`, `figure5_read.py`, `figure5.py`, `tables.py`, `compare_figure.py` | Published values read back, ours drawn on the published grid, scores and controls, Table 1 and the claims. |
| RESULTS | `build_results.py`, `check_results.py` | `results.json` with computed verdicts. |
| CHECK | `check_reproduction.py`, `compare_runs.py` | Fails on a broken rule or any difference from `output/`. |
| PAGE | `build_page.py` | `site/PMC4015815/index.html`. |

## Limits

- **SVM-DT profiles.** The paper's PSI-BLAST database and settings are not given; the 2008
  Top-n-gram paper it builds on used EBI nrdb90 (gone) and 10 iterations. We use the lab's 2016
  nrdb90 with 3 iterations and E = 0.001 from its 2017 Pse-in-One 2.0, and BLAST+ 2.17.0. The
  SVM-DT items are re-measured, not reproduced.
- **Gist.** Ported, not run: building the 2006 C source was not possible in this environment. The
  port matches Gist's own sample run within its convergence threshold. It differs from Gist's code
  in one place, the cap above, which the published weights support.
- **dMAX = 0 is slow.** On the composition-only kernel Gist's coordinate ascent needs 2,000 to
  4,000 passes per family (about 2 CPU hours for both methods); CI reads those points from
  `output/` unless started with `dmax_zero`.
- **Fig. 3, dMAX 20 (SVM-DR).** 0.0013 above the published point; the seed (0.0002) and Gist's clip
  rule (0.8885) do not explain it. Open.
- **Determinism.** Every sum in the port runs in a fixed order, so a rerun on x86_64 gives the same
  bits; the committed dMAX 150 rows came back byte for byte in an independent run.
- The pipeline was run here with `run_local.sh` (the same scripts and arguments as `main.nf`);
  running Nextflow itself was not possible in this environment, so `main.nf` is exercised by CI.

