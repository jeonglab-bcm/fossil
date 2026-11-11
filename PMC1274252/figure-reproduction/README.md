# PMC1274252 figure reproduction

Adie EA, Adams RR, Evans KL, Porteous DJ, Pickard BS. Speeding disease gene discovery by sequence based
candidate prioritization. *BMC Bioinformatics* 6:55 (2005).
[doi:10.1186/1471-2105-6-55](https://doi.org/10.1186/1471-2105-6-55). CC BY 2.0.

The figures in `published/` are the paper's (CC BY 2.0, attribution above): `figure-1.png`, `figure-3.png` and
`figure-4.png` are the authors' original files that BMC serves as additional files 2, 4 and 5; `figure-2.jpg` is
BMC's 1200 x 1050 rendering of the authors' Figure 2 EPS (additional file 3 is a raster EPS of the same image).
`published_values.json` holds every number the paper prints, transcribed by hand. Nothing else of the paper is in
this folder, and no Weka code: the pipeline downloads Weka 3.4.3 and runs it in its work folder.

## Results

<!-- summary from results.json (check_results.py); the full table: python3 figure-reproduction/pipeline/check_results.py results.json --markdown -->

35 results: 6 agree, 15 partly agree, 1 inconclusive, 6 differ, 7 not attempted; 1 open cause.

| Result | Verdict | Ours against the paper |
| --- | --- | --- |
| Table 3, the published tree on the archived sets | partly | Training: accuracy 67.2% (67%), AUC 0.744 (0.75), kappa 0.34 (0.35), recall 80% (77%). HGMD: 63.0% (64.5%), AUC 0.693 (0.69). Oligogenic: 67% (65%), AUC 0.767 (0.76); 39 disease genes found and 22 controls called disease, the text's counts, but of 50 + 50 genes, not 54 + 54 |
| Table 3, 10-fold cross-validation (retrained) | differs | 66.6% (63%), AUC 0.740 (0.70), kappa 0.33 (0.27): the archived features separate the classes better |
| Table 3, the tree retrained with the download page's recipe | differs or partly | Training 70.7% (67%), HGMD 64.2% (64.5%), oligogenic 70% (65%) |
| Fig. 2, the tree | partly | Retrained, the first rules are mouse identity (37.5 against 41.082; 1.031 / -0.13 against 0.827 / -0.163), signal peptide, gene length (996.5, printed 997) and exons > 32, as in the paper; the other 11 rules differ (6 of 59 fields) |
| Fig. 3, ROC curves | A agrees, B inconclusive, C partly | A: 92.6% of pixels within 2 px both ways (best control 76%). B: close, but the retrained tree's curve is as close. C: same hull, points on a 50-gene grid |
| Table 4, feature shares | partly | 5 of 11 at printed precision, 9 of 11 if truncated; paralog identity is empty in the archived files |
| Table 2 and Fig. 1, disease against control genes | partly | Every significant difference is significant; disease medians come back (gene length 27 k, exons 10, mouse identity 87%, signal peptide 36% against 35%); 54 of 119 histogram bars as printed |
| Text claims on our run | differs or partly | Spearman 0.70 and 0.39 (0.71, 0.35); 10 and 20 rules worse than 15 on AUC, 10 rules not on accuracy; length-only tree 84% / 58% (69% / 51%, open) |
| The authors' genome-wide dump | differs | 2 genes over 0.75 (97), 5,155 under 0.3 (4,357): another model than Figure 2 |
| Claims against the paper's own numbers | agrees | 52 of 58 follow. Slips: 36/97 is 37%, not ~33%; 29/219 is 13.2%, not 13.4%; the abstract's "twenty-fold" is the conclusion's 25-fold (Fig. 4 at the top 4%); the Lopez-Bigas kappas do not follow from the stated rates; "Euler's constant" is e |
| Port and Weka versions | agrees | `prospectr_adtree` gives Weka 3.4.3's trees, scores, folds and statistics exactly; Weka 3.4.1-3.4.4 build the same tree |
| Fig. 4, artificial loci, Lopez-Bigas, mutation types, Additional File 1, Table 1 | not attempted | No gene IDs, positions, HGMD records or genome-wide features survive; Table 1 is a feature list |

The main claim holds on the surviving data: the published tree separates disease genes from controls about as
well as Table 3 says, and its training-set ROC curve lies on the published one. The differences come from the
archived sets, a 2006 version of the paper's with other genes and features; the paper's slips are in its
arithmetic, not its method.

## What the code does, against the paper

| Paper | Here |
| --- | --- |
| Training and test sets: 1,084 OMIM genes + 1,084 controls; 675 HGMD + 675; 54 oligogenic + 54; features of Table 1 from EnsMart 22.1 and HomoloGene | PROSPECTR's own ARFF files from its web site, captured by the Wayback Machine on 2006-09-30: 1,080 + 1,080, 713 + 713 and 50 + 50 genes, 64 features (Table 1's, minus distance to the neighbouring gene, the paralog flag, yeast and Arabidopsis identity and the CpG flags, plus expression, isoelectric point, family size, amino-acid composition and more species). No gene IDs. The test files' relation names show they were cut from a larger file with Weka's Remove filter. |
| Weka's ADTree, 15 nodes ("Experiments were carried out using the Explorer") | Weka 3.4.3 (September 2004), `ADTree -B 15 -E -1`, the command on PROSPECTR's archived download page; run through `WekaRun.java`, which also records every score and Weka's own statistics. `-E -1` is Weka's z-pure search. Weka 3.4.1, 3.4.2 and 3.4.4 build the same tree. |
| The tree of Figure 2 | `package/src/prospectr_adtree/data/prospectr_fig2.json`, read node by node; scored by `prospectr_adtree.score`: start at 0, follow every rule whose feature is known, add the branch values; negative = disease-like. The figure prints no value for "Start": 0, as Weka gives for a balanced training set. CDS length is cDNA minus both UTRs (the ARFFs have none); the ARFFs' paralog identity is 0 for every gene and is read as unknown, as Table 1 enters genes without a paralog. |
| Table 3: accuracy, precision, recall, AUC and kappa "obtained directly from Weka" | `prospectr_adtree.evaluate`: Weka 3.4.3's confusion matrix, kappa and `ThresholdCurve.getROCArea`, for the disease class. Two sets of rows: the published tree on the archived sets (the classifier Table 3 describes), and the tree retrained with the recipe. Cross-validation exists only for a retrained tree: Weka's `crossValidateModel` with seed 1, as the Explorer runs it. |
| Figure 3: Weka's ROC plots | The published tree's threshold curves drawn as Weka draws them (red points, green convex hull) on the published axes, scored against the published pixels with controls. The published points are also read back to numbers and integrated (text.arithmetic). |
| Table 4: "for each gene, keeping track of the percentage contribution of each feature to the final score ... averaged out over all genes predicted as likely to be involved in disease" | `prospectr_adtree.average_contributions(by="net")` over the genes the published tree calls disease in the archived training set; five other readings are in `analysis.json` (`table4_variants`). |
| Table 2 and Figure 1: OMIM genes against ~18,000 controls | The archived training set: 1,080 disease and 1,080 control genes. Medians, Mann-Whitney and chi-squared tests; Figure 1's bins from its x labels (ten bars of width cap/10, the last holding everything above), percentages truncated, as the bar labels add up to 94-98%. |
| Normalisation 1/(1 + γ^α), "γ = Euler's constant" | 1/(1 + e^α): what the authors' own dump and Additional File 1 follow. |
| Artificial loci (Fig. 4), Lopez-Bigas comparison, mutation types, whole-genome scores, Additional File 1 | Not rerun: they need gene IDs, positions, HGMD records or every gene's features, none of which survive. The text's numbers are checked against Fig. 4 read back and against the paper's own counts; the authors' genome-wide dump is compared as it is. |

## The port

`prospectr_adtree.ADTree` is a port of Weka 3.4.3's `weka.classifiers.trees.ADTree` (and the parts of
`Instances`, `ThresholdCurve`, `Evaluation` and `java.util.Random` it relies on): the same Z criterion, smoothed
prediction values, cut points, Weka's quicksort and its tie-breaking, merging of repeated splitters, z-pure search,
and the same shuffles for cross-validation. On both feature sets it gives Weka's tree text character for
character, every score to the last bit (maximum difference 0.0), the same ten folds and the same statistics
(`output/analysis.json`, `port_check`). The pipeline checks this on every run.

## Layout

| Path | Content |
| --- | --- |
| `main.nf`, `nextflow.config` | The pipeline (profile `skyriver` for the BCM cluster). |
| `run_skyriver.sbatch` | The Nextflow head as a Slurm job on Skyriver. |
| `requirements.txt` | Pinned Python packages. |
| `results_notes.json` | Labels, assumptions and causes, written by hand; merged with the run into `../results.json`. |
| `results.json` | The repository's results check (`tools/check_results.py`): our value for every compared number. |
| `pipeline/` | `fetch_inputs.sh`, `prepare.py`, `WekaRun.java`, `run_weka.sh`, `weka_versions.py`, `reproduce.py`, `figures.py`, `build_results.py`, `check_reproduction.py`, `build_page.py` (+ `page_template.html`), `make_results_check.py`; copies of the skill's `check_results.py`, `compare_runs.py`, `check_package.py`. |
| `published/` | The paper's four figures (CC BY 2.0) and `published_values.json`. |
| `output/` | `analysis.json` (every number), `figures.json` (pixel scores, controls, figures read back), `results.json`, `checks/weka_versions.json`. |
| `output/figures/` | `fig*_ours.png` (ours drawn into the published frame) and `fig*_overlay.png` (Fig. 1: our bar tops in red on the published bars; Fig. 2: each published rule marked green when the retrained tree has it in the same place, red when not; Fig. 3: ours in blue on the published curves). |

## Run

```bash
pip install -r PMC1274252/figure-reproduction/requirements.txt
nextflow run PMC1274252/figure-reproduction/main.nf --outdir results                   # about 5 minutes on 4 cores
nextflow run PMC1274252/figure-reproduction/main.nf --outdir results --weka_versions   # + Weka 3.4.1, 3.4.2, 3.4.4
sbatch PMC1274252/figure-reproduction/run_skyriver.sbatch                               # the same, as a Slurm job
```

It needs Python 3.12 with `requirements.txt`, a JDK (8 or later; CI uses Temurin 21), uv for the package check,
and network access to the Wayback Machine, PMC's open-access bucket and SourceForge. `--sources DIR` reuses local
copies of the downloads. The workflow `.github/workflows/reproduce-pmc1274252.yml` runs it on every pull request
that touches this folder or the package.

## Pipeline steps

1. `FETCH`: the three ARFFs, the download page and `dump.tab` from the Wayback Machine, Additional File 1 from
   PMC (fallback: BMC), Weka 3.4.3 from SourceForge; SHA-256 checked.
2. `PREPARE`: the sets restricted to Table 1's features, with CDS length added.
3. `WEKA`: Weka 3.4.3's ADTree on both feature sets (`run_weka.sh`, `WekaRun.java`).
4. `WEKA_VERSIONS`: the committed comparison of Weka 3.4.1-3.4.4, or (`--weka_versions`) a fresh one.
5. `REPRODUCE`: through the package, the port check against `WEKA`, Table 3 (published and retrained trees,
   cross-validation), Figure 2 rule by rule, Table 4, Table 2, Figure 1, the claims, the authors' dump.
6. `FIGURES`: renders, overlays and pixel scores with controls; Figures 3 and 4 read back.
7. `PACKAGE`: `check_package.py` on `../package`.
8. `RESULTS`: `results.json`, the check step (`report.md`) and the results page.

## Limits

- **The archived sets are not the paper's.** They were first captured 18 months after publication, hold a few
  dozen genes more or fewer than the paper's sets, and carry a later feature set; the paper's gene lists were
  never published. No value that depends on the data can be expected to match exactly; Table 3's accuracy with
  the published tree comes within a point or two.
- **The paralog feature is empty** in the archived files (0 for all 3,686 genes), so the published tree's rule 7
  never fires; read as 0 instead of unknown it would send every gene towards "normal" (training recall 37%).
- **Unstated settings.** The Weka release (3.4.1-3.4.4 give the same tree), the cross-validation seed (Weka's
  default 1), Table 4's averaging (six readings in `analysis.json`), Figure 1's bins (read from its labels).
- **Figure 2** is printed with "Gene length >- 896bp"; read as >=. Its thresholds are Weka's rounded to whole base
  pairs (997 for 996.5).
- **Pixel scores** on Fig. 3B cannot tell the published tree from the retrained one (both curves are close to the
  published one); the AUCs can (0.693 and 0.699 against 0.69).
- **Not rerun:** Fig. 4 and the artificial loci, the Lopez-Bigas comparison, the mutation types, the whole-genome
  scores and Additional File 1, Table 2's distance and CpG rows, and the distance correlation: their inputs do not
  survive.
