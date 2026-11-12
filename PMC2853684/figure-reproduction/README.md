# PMC2853684 figure reproduction

Navlakha S, Kingsford C. The power of protein interaction networks for associating genes with diseases.
*Bioinformatics* 26(8):1057-1063 (2010). [doi:10.1093/bioinformatics/btq076](https://doi.org/10.1093/bioinformatics/btq076).
CC BY-NC 2.5 (© The Author(s) 2010, Oxford University Press). `published/` holds Figs 2-4 and Supp. Figs S1-S2
cut from the open-access PDFs at 300 dpi (`pipeline/make_published.py`, run once by hand with Ghostscript),
redistributed for non-commercial use with this attribution. The paper, supplement, networks and prediction
files are downloaded at run time and not committed.

## Results

<!-- generated from ../results.json by check_results.py; full table: python3 pipeline/check_results.py ../results.json --markdown -->

25 results: 2 exact, 11 agree, 6 partly agree, 0 differ, 6 not attempted; 6 open causes. The table per item is in
the paper's [README](../README.md) and on the [results page](https://jeonglab-bcm.github.io/fossil/PMC2853684/).

| Kind of number | What it is | Where |
| --- | --- | --- |
| Ours | Our rerun of the methods (Neighborhood, Oti, RW, Prop, MCL) and the authors' GS and VI-Cut scores, evaluated by our code | every `observed` value in `../results.json` |
| Arithmetic check | Our code applied to the points the paper draws in Fig. 2a | `text.arithmetic` (12 of 15 Sec. 3.1 ranges come back; 3 are not the figure's extremes) |
| Sensitivity | none: no paper value is put into our run | |

The main findings of the paper hold: random walks are the most precise single methods, the consensus is Pareto
optimal, and homophilic diseases are predicted better. Three Sec. 3.1 ranges and four Supp. Table 1 scores are
slips in the paper; the consensus points differ because the forest's settings are not stated.

## What the code does, against the paper

- **Data** (Sec. 2.1). `HPRD.net` (8,776 proteins, 35,820 interactions, 1,839 of them self-interactions),
  `OPHID.net` (9,842, 73,130) and `DiseaseNetPreds.zip`, from the paper's site as the Wayback Machine captured it
  on 2 July 2010. The candidate pairs (every gene in a linkage interval of each of 450 diseases; 178,561 on HPRD,
  2,068 of them known associations) are those of the authors' `locus_disease_preds` files. The OMIM morbid map
  and the 2008 UniProt loci that made them are not needed.
- **Methods** (Sec. 2.2-2.3, Supp. Sec. 1), in the package `diseasenet`, all leave-one-out. Neighborhood,
  Oti and RW follow the text and give the authors' scores on every pair. Prop gives them only when the flow
  starts at zero (F(0) = 0; starting at the prior Y misses by a median 8e-5 relative). On OPHID, RW and Prop
  give them only with a self-interaction on every protein (without, a median 14% off). MCL (micans.org
  release 14-137, inflation 2.0) gives the authors' MCL scores with the score defined as the fraction of the
  *other* members of the cluster annotated with the disease.
- **Thresholds.** The paper gives only ranges. The grids 0.05-0.95 by 0.05 (fractions), 0.0001-0.09 (RW) and
  0.01-0.9 (Prop) (`analysis.py`), with "score > θ", give every point of Supp. Fig. S1 (353 of 353
  coordinates) and of Fig. 2a. Fig. 2 drops consecutive repeated points and points with recall below 1%;
  values are rounded to 0.1% with ties to even, as R rounds.
- **Figure values.** Figs 2 and 4 and Supp. Figs S1 and S2 are vector drawings. `read_published.py` reads
  every polyline vertex, bar and error bar from the PDF content streams and calibrates them with the tick
  marks; Fig. 2 and S1 coordinates sit on a 0.1% grid to within 0.001%. Fig. 3's margins, Fig. 4's bar
  counts and the legend values are printed in the figures and were read from 300-600 dpi renders.
- **Consensus** (Sec. 2.2, Fig. 2a). Weka 3.6.6 RandomForest with its defaults on the 13 scores, 10-fold
  cross-validation (our split). Settings and splits are not in the paper.
- **Per disease** (Fig. 3, Sec. 3.3, 3.5). The threshold of each method "corresponding to roughly 10% recall"
  is the grid value with recall closest to 10%. "At least half of the 13 methods achieved precision > 90%"
  gives the paper's 19 only as the supplement words it (predicted by at least 7 methods, all with precision
  of at least 90%); read literally it gives 35.
- **Homophily** (Fig. 4, Supp. Fig. S2). Neighbourhood homophily gives the published bin counts only when a
  gene's neighbours are counted among *annotated* genes (associated with any disease): all ten counts against
  356, 45, 22, ... with all neighbours. Bars and fits use only the method-disease pairs with a prediction; error
  bars are the variance of those F1 values; the legend values are Pearson r.

## Layout

| Path | Content |
| --- | --- |
| `main.nf`, `nextflow.config` | The pipeline; `-profile skyriver` runs each process as a Slurm job |
| `run_skyriver.sbatch` | The Nextflow head as a Slurm job on Skyriver (BCM) |
| `requirements.txt` | Pinned Python packages |
| `results_notes.json` | Labels, sources, assumptions and causes, written by hand |
| `results.json` | The repository's results-check file (971 values; `pipeline/make_results_check.py`) |
| `pipeline/fetch_inputs.sh` | Downloads with SHA-256 checks |
| `pipeline/run_mcl.sh` | MCL clusterings of both networks |
| `pipeline/analysis.py` | The rerun and every number of the paper |
| `pipeline/consensus.py` | The consensus Random Forest (Weka) |
| `pipeline/read_published.py`, `pdfvec.py` | Values of the published figures from the PDFs |
| `pipeline/compare.py`, `render.py` | Fields for `results.json`; renders and overlays |
| `pipeline/build_results.py`, `check_reproduction.py`, `build_page.py` | `results.json`, the check, the results page |
| `pipeline/check_results.py`, `compare_runs.py`, `check_package.py` | Copies of the Paper2Repro checkers |
| `published/` | The published figures and their crop boxes |
| `output/` | The committed outputs of the pipeline |

## Run

```sh
nextflow run PMC2853684/figure-reproduction/main.nf --outdir results
```

About 6 minutes on 4 cores (Skyriver `defq15`), 35 MB of downloads. It needs Python 3.12 with
`requirements.txt`, `uv` (package check), `mcl` 14-137 (`apt install mcl` on Ubuntu 24.04, or bioconda
`mcl=14.137`) and Java 21. On Skyriver: `sbatch PMC2853684/figure-reproduction/run_skyriver.sbatch`.
CI: `.github/workflows/reproduce-pmc2853684.yml` runs the same command on every pull request that touches this
folder or the package.

## Pipeline steps

1. `FETCH`: networks and prediction files (Wayback Machine), paper and supplement (PMC on AWS), Weka (Maven
   Central); SHA-256 checked.
2. `READ_PUBLISHED`: the published figures' values from the PDFs.
3. `MCL`: clusters of both networks.
4. `CONSENSUS`: Weka forest, cross-validated.
5. `ANALYSIS`: the rerun against the authors' scores, the curves, the per-disease statistics, homophily,
   the no-interval runs and Supp. Table 1.
6. `COMPARE`: fields for every printed or drawn value; renders and overlays.
7. `PACKAGE`: `check_package.py` on `../package`.
8. `RESULTS`: `results.json` with computed verdicts, the check against the committed `output/`
   (`report.md`), and the results page.

## Limits

- GS1-3, GS-All, VI-CutS and VI-CutL use the authors' scores: the graph summarization code is lost, and the
  surviving VI-Cut code needs its merge tree.
- Three Fig. 2a points that our curves give (GS1 at θ = 0.25, VI-CutS at 0.25 and 0.4) are not drawn in the
  paper; the cause is open.
- The consensus points depend on unstated forest settings; ours are near, not on, the published points.
- Without linkage intervals, GS and VI-Cut scores exist only above 1/3 (the authors' thresholded files).
- The whole HPRD network (9,182 proteins) and the 189 out-of-interval genes need data that were not released.
