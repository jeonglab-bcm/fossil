# PMC2735674: figure reproduction

> Bleakley K, Yamanishi Y. Supervised prediction of drug-target interactions using bipartite local
> models. *Bioinformatics* 25(18):2397-2403 (2009).
> [doi:10.1093/bioinformatics/btp433](https://doi.org/10.1093/bioinformatics/btp433)

## Results

Generated from [`../results.json`](../results.json).

<!--__RESULTS_TABLE__-->

| Item | Verdict | Measure | Why |
| --- | --- | --- | --- |
| Table 1, enzyme dataset | partly | 11 of 24 fields as printed | 11 of the 24 printed values come back to the digit and 21 are within one point. The largest gaps are the KRM AUPRs (KRMd 35.0 against 38.7, KRMt 78.3 against 80.6): the AUCs the paper stars for those rows are copied from Yamanishi et al. (2008), where they came from 10-fold cross-validation, so their leave-one-out AUPR cannot be checked against the same run. Three settings the paper does not give were identified against its own values and are listed as assumptions. |
| Table 2, ion channel dataset | partly | 6 of 24 fields as printed | 6 of the 24 printed values come back to the digit and 18 are within one point. The largest gaps are again the KRM AUPRs (m(KRMd,KRMt) 73.3 against 77.8, KRMd 29.5 against 33.7). Every BLM and nearest-neighbour AUC is within 0.5 of the printed value, and BLMt and m(BLMd,BLMt) come back to the digit. |
| Table 3, GPCR dataset | partly | 8 of 24 fields as printed | 8 of the 24 printed values come back to the digit and 22 are within one point; no value is more than 1.4 away. The largest gap is KRMt's AUC, 84.2 against 82.8, a row whose printed AUC is copied from Yamanishi et al. (2008). |
| Table 4, nuclear receptor dataset | partly | 4 of 24 fields as printed | 4 of the 24 printed values come back to the digit and 17 are within one point. BLMt (53.6 AUC, 35.8 AUPR) and m(BLMd,BLMt) AUPR (60.0) come back exactly, which is what fixed the rule for a local model with no positive example: on this dataset that case covers 39 of the 90 known interactions. The largest gaps are the KRM AUPRs. |
| Fig. 1a, enzyme precision-recall curves | agrees | 48.17% within 2 px (pass 42.0%, best control 15.6%) | The curves agree where it can be measured: the published precision is within 0.01 of ours at most grid points (enzyme panel: BLMd 19 of 20 grid points, BLMt 18, the aggregate 15), while another dataset's curves on the same panel reach at most 6 of 20. The pixel score sits near 50 per cent because two of the three curves are dashed and the phase of the dashes, which the PDF does not fix to the data, decides where ink falls inside a line. |
| Fig. 1b, ion channel precision-recall curves | agrees | 47.68% within 2 px (pass 42.0%, best control 33.4%) | The curves agree where it can be measured: the published precision is within 0.01 of ours at most grid points (ion channel panel: BLMd 15 of 20 grid points, BLMt 18, the aggregate 1), while another dataset's curves on the same panel reach at most 6 of 20. The pixel score sits near 50 per cent because two of the three curves are dashed and the phase of the dashes, which the PDF does not fix to the data, decides where ink falls inside a line. The aggregate curve is the one that differs: in the published panel it follows BLMd at the top of the ranking and in ours it follows BLMt, which is the same scale question as the aggregated rows of Table 2, and the reason the curves were put on one scale before the maximum. |
| Fig. 1c, GPCR precision-recall curves | agrees | 44.88% within 2 px (pass 42.0%, best control 18.2%) | The curves agree where it can be measured: the published precision is within 0.01 of ours at most grid points (GPCR panel: BLMd 15 of 20 grid points, BLMt 17, the aggregate 11), while another dataset's curves on the same panel reach at most 6 of 20. The pixel score sits near 50 per cent because two of the three curves are dashed and the phase of the dashes, which the PDF does not fix to the data, decides where ink falls inside a line. |
| Fig. 1d, nuclear receptor precision-recall curves | agrees | 51.24% within 2 px (pass 42.0%, best control 36.4%) | The curves agree where it can be measured: the published precision is within 0.01 of ours at most grid points (nuclear receptor panel: BLMd 7 of 20 grid points, BLMt 15, the aggregate 9), while another dataset's curves on the same panel reach at most 6 of 20. The pixel score sits near 50 per cent because two of the three curves are dashed and the phase of the dashes, which the PDF does not fix to the data, decides where ink falls inside a line. The BLMd curve of this panel is the weakest of the twelve: its 90 interactions make each precision step 1/90 wide, so a single pair in a different order moves the curve by more than the reading tolerance. |
| Table 5, top 10 predicted nuclear receptor pairs | partly | 1 of 2 fields as printed | All ten pairs of the paper's Table 5 are in our top ten, and the five pairs of the Isotretinoin block come out in the paper's own order. Five sit at a different rank: our ranks 1 and 2 are the paper's 2 and 1, and its ranks 8, 9 and 10 are our 9, 10 and 8. Those five pairs are separated by at most 0.08 of a score unit, and the five Isotretinoin pairs are exactly tied at 0.194683 because they come from one local model, so their printed order is a tie break the paper does not state. |
| Fig. 2, part of the predicted nuclear receptor network | partly | 8 of 9 fields as printed | Six of the seven dashed edges of the published figure are in our top 20, at ranks 2, 3, 4, 5, 7 and 13. The seventh, D01132 with hsa:6095, is our rank 23. The caption says the dashed edges are some of the 20 highest scoring predictions, so a pair just outside our top 20 is the same kind of near miss as the rank swaps of Table 5. |
| The statements of Section 4, recomputed from the paper's own tables | agrees | 19 of 19 statements of Section 4 come back when they are recomputed from the paper's own tables |  |
| Section 4.4, the best AUC passes from 92.9 to 97.6, 91.7 to 97.3, 87.3 to 95.5 and 83.6 to 88.1 | partly | 3 of 8 fields as printed | The four values the claim moves to come back as 97.6, 97.3, 95.7 and 88.3 against the printed 97.6, 97.3, 95.5 and 88.1, so the claim itself holds in our run: on each dataset the best score of the article's own methods beats the best kernel regression score. The four values it moves from are the starred KRM AUCs, which the paper copies from the 10-fold cross-validation of Yamanishi et al. (2008); our leave-one-out run gives 93.2, 91.7, 84.2 and 83.3 against their 92.9, 91.7, 87.3 and 83.6. |
| Section 4.4, the best AUPR passes from 80.6 to 84.1, 79.6 to 81.3, 57.7 to 66.7 and 43.6 to 61.2 | differs | 0 of 8 fields as printed | The claim holds in our run, but none of its eight numbers is exact. The values it moves to come back as 84.2, 80.9, 66.6 and 60.0 against the printed 84.1, 81.3, 66.7 and 61.2, and the ones it moves from, the best KRM AUPRs, as 78.3, 76.9, 57.5 and 39.3 against 80.6, 79.6, 57.7 and 43.6. The gap is on the comparison method: its AUPR sits 2 to 4 points low on three datasets, while every BLM row is within a point. The rows whose AUC the paper took from Yamanishi et al. (2008) are the rows whose AUPR we cannot check against that paper, because it prints none. |
| Sections 4.1 to 4.3, how many of the eight conditions the local models win | partly | 1 of 3 fields as printed | Two of the three counts are one higher in our run: eight of eight conditions instead of seven in Section 4.1 and seven instead of six in Section 4.2. Both differences come from values that tie in the paper and separate here. The paper's seven of eight needs its ion channel AUC tie (KRMd and BLMd both 74.5) to count against the local models; our run gives 74.7 and 74.0, so the tie is gone. In Section 4.2 the paper's own tables give six only when the nearest-neighbour row is left out of the comparison, which is how this check reads it. |
| Section 1, nearly 90% precision at 60% recall on the ion channel dataset | exact | 2 of 2 fields as printed |  |
| Section 2.1, the drugs, targets and interactions of each dataset | exact | 12 of 12 fields as printed |  |
| Sections 4.5 and 5, at least 4 of the top 10 nuclear receptor predictions were later confirmed | not attempted | not attempted | The confirmation status is a lookup in the SuperTarget database as of January 2009 and a literature search, not a computation. SuperTarget has been superseded and no January 2009 release is archived, so the status of the ten pairs cannot be recovered as the paper found it. Our run ranks the same ten pairs first, which is the part of the claim the method decides. |
| The authors' implementation against this one | not attempted | not attempted | The authors' MATLAB implementation is lost. The paper offers it on request and links a project page, which is now a redirect to the laboratory's home page; the Wayback Machine holds the page from 2014 and 2015, which lists bipartiteLocalModel.m and a data archive, but no capture of either file, and no copy is on GitHub. The method is therefore written from the paper's text and checked against its printed values. |
| Python package blmdti and its tutorial | agrees | blmdti 0.1.0: wheel installed in a fresh environment and imported from it; tests 12 passed; tutorial 7 cells compared, 0 skipped (nondeterministic); TUTORIAL.md in sync |  |

2 exact, 6 agrees, 8 partly, 1 differs, 2 not attempted; 0 open causes.

<!--__RESULTS_TABLE_END__-->

<!--__CLAIMS_LINE__-->

The main claim of the paper holds: on all four networks the best score of its own methods beats the kernel regression method it compares with. The headline AUCs come back at 97.6, 97.3, 95.7 and 88.3 against the printed 97.6, 97.3, 95.5 and 88.1. The counts in Sections 4.1 and 4.2 are one higher in our run, because values that tie in the paper separate here.

<!--__CLAIMS_LINE_END__-->

## What the code does, against the paper

The method is in the package [`../package`](../package) (`blmdti`), and the pipeline calls it, so
there is one copy of it. The pipeline adds the benchmark input, the leave-one-out driver, the
comparisons and the pages.

| The paper says | What the code does |
| --- | --- |
| The gold standard is the dataset of Yamanishi et al. (2008): 445, 210, 223 and 54 drugs, 664, 204, 95 and 26 targets, 2926, 1476, 635 and 90 interactions (Section 2.1) | `fetch_inputs.sh` downloads the twelve files from the Kyoto supplement page and checks their SHA-256. The counts come out exactly. |
| The similarity matrices are made into kernels by symmetrizing, then adding a small multiple of the identity until no eigenvalue is negative (Section 3.5) | `make_psd` adds the smallest such multiple. The chemical matrices need 0.123, 0.0024, 0.0106 and 8e-17 of the identity (enzyme, ion channel, GPCR, nuclear receptor); the genomic matrices are already kernels and need nothing. |
| LIBSVM 2.88, C-SVC, C = 1, no class weighting (Section 3.5) | scikit-learn's `SVC` with a precomputed kernel, which wraps the same LIBSVM solver, C = 1 and no class weight. |
| A score is the SVM decision value; the pair is left out of training (Sections 3.2, 3.3) | One fit for every (drug, target) pair in each direction: 1.5 million fits over the four datasets. |
| Scores are aggregated with m(x, y) = max(x, y) (Section 3.2) | `aggregate(..., standardize=True)`: the maximum of the z-scores. The paper does not say that it standardized, and its discussion raises the scale problem; the plain maximum does not reproduce its aggregated rows and the standardized one does (item `table1` to `table4`, assumption "aggregation scale"). |
| The quality of a ranking is the AUC and the AUPR over every pair (Section 3.5) | `auc` averages tied ranks; `aupr` joins the precision-recall points with straight lines (the trapezoid rule, as R's ROCR draws them). The step rule is also available and moves the nearest-neighbour rows by up to 10 points. |
| KRM is the kernel regression method of Yamanishi et al. (2008) | Rebuilt from that paper: the Gaussian of the shortest-path distance with h = 2 (the value it reports), the eigen-embedding, and the regression solved as W = pinv(S) U. The solve needs a regularization that neither paper gives (item `table1`, assumption "KRM regularization"). |
| The nearest neighbour baseline assigns the highest similarity value (Section 3.4) | The nearest-profile method of Yamanishi et al. (2008), equation 1: the most similar other drug, scored where that drug binds the target. Its AUCs come back to the printed digit on all four datasets. |
| A local model may have no positive training example | The paper does not define this case, which covers 288, 23, 34 and 8 pairs for BLMd and 177, 81, 106 and 39 for BLMt. The score is then -1 (item `table4`, assumption "no positive example"). |

## Layout

```text
figure-reproduction/
├── main.nf, nextflow.config, requirements.txt   the pipeline and its pinned versions
├── results_notes.json                           labels, sources, assumptions, causes, page text
├── run_skyriver.sbatch                          one dataset and method as a Slurm job array
├── pipeline/
│   ├── fetch_inputs.sh         the benchmark files and the article PDF, with checksums
│   ├── compute_scores.py       leave-one-out scores of one method on one dataset (shardable)
│   ├── run_scores.py           the score step: committed matrices, or a full recompute
│   ├── published.py            Figure 1 read out of the PDF as curves and as a 600 dpi image
│   ├── tables.py               Tables 1 to 4 against the printed values
│   ├── figure1.py              our curves against the published ones, as values and as pixels
│   ├── predictions.py          Table 5 and Figure 2: the top nuclear-receptor predictions
│   ├── claims.py               the statements of the text, from the paper's tables and from ours
│   ├── build_results.py        results.json from the outputs and the notes
│   ├── check_results.py        verdicts and rules (from the paper2repro skill)
│   ├── compare_runs.py         a fresh run against the committed outputs (same skill)
│   ├── check_reproduction.py   the check step
│   ├── check_package.py        builds, installs and tests the package (same skill)
│   └── build_page.py, page_template.html
├── published/                  Figures 1 and 2 as published, for comparison
└── output/                     the committed outputs of the run, including the score matrices
```

## Run

```bash
nextflow run PMC2735674/figure-reproduction/main.nf --outdir results
```

About 12 minutes on 4 cores: the nuclear-receptor scores are recomputed and the other three
datasets are read from `output/scores`. To recompute every score matrix:

```bash
nextflow run PMC2735674/figure-reproduction/main.nf --outdir results --full --cpus 48
```

That is about 6 hours of CPU (1.5 million SVM fits and 2,200 eigen-embeddings), 10 minutes on 48
cores. On the Skyriver cluster, submit it rather than running it on the login node:

```bash
sbatch --array=0-23 --export=ALL,DATASET=e,METHOD=blmt figure-reproduction/run_skyriver.sbatch
```

## Pipeline steps

| Process | Does |
| --- | --- |
| `FETCH` | Downloads the twelve benchmark files and the article PDF, from the Kyoto page or, if it does not answer, from the Wayback Machine, and checks the SHA-256 of each. |
| `SCORES` | The six score matrices of each dataset: BLMd, BLMt, KRMd, KRMt, NNd, NNt. |
| `PUBLISHED` | Reads Figure 1's four panels out of the PDF as curves, and renders it at 600 dpi. |
| `TABLES` | Tables 1 to 4: twelve rows of AUC and AUPR each, against the printed values. |
| `FIGURE1` | Our precision-recall curves against the published ones: values at a recall grid, and pixels on the published panel grid, with controls. |
| `PREDICTIONS` | Table 5 and Figure 2: the top 20 nuclear-receptor predictions, their ranks against the paper's. |
| `CLAIMS` | The statements of Section 4, from the paper's own tables and from our run. |
| `PACKAGE` | Builds the package, installs it in a fresh environment, runs its tests and its tutorial. |
| `RESULTS` | Merges the numbers with the notes into `results.json` and computes the verdicts. |
| `CHECK` | Fails on a broken rule or any difference from the committed outputs; writes `report.md`. |
| `BUILD_PAGE` | The results page from `results.json`. |

## Limits

- The benchmark files come from one page. The Kyoto supplement page is the primary source and
  the Wayback Machine is the fallback: every one of the twelve files has a capture, and an `id_`
  capture is byte for byte the original, so the checksums pass either way. `--sources DIR` reuses
  local copies instead.
- The score matrices of the enzyme, ion channel and GPCR datasets are committed under
  `output/scores` and read by the default run. A full recompute needs `--full`, which the CI
  workflow runs only when started by hand.
- Two settings the paper does not give were identified against its printed values: the score of a
  local model with no positive example, and the standardization before the maximum. Both are
  recorded as assumptions in `results.json` with their sensitivity.
- The KRM rows depend on a third such setting, the regularization of the kernel regression solve.
  The AUCs the paper marks with a star are copied from Yamanishi et al. (2008), where they came
  from 10-fold cross-validation, not from the leave-one-out runs of this paper.
- Figure 2's layout and its choice of sub-network are manual, so only its nodes and its edges are
  compared, not any geometry. The asterisks that mark later confirmed pairs record a database
  lookup made in January 2009 and are not recomputable.
