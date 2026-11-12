# PMC2949886 figure reproduction

van Iterson M, Boer JM, Menezes RX. Filtering, FDR and power. *BMC Bioinformatics* 11:450 (2010).
[doi:10.1186/1471-2105-11-450](https://doi.org/10.1186/1471-2105-11-450). CC BY 2.0.

The pipeline reads the paper's figures back from the authors' vector files, reruns the simulation study, the
single-data-set analyses and the leukemia analysis with the R package `filterfdr` (`../package`), draws our
curves on the published axes, scores them against the published curves and negative controls, computes the
claims of the text, and writes `../results.json` and the results page. Nothing of the paper is committed;
the figures and the GEO data are downloaded by `pipeline/fetch_inputs.sh`.

## Results

47 results: 6 exact, 7 agree, 22 partly agree, 8 inconclusive, 2 differ, 2 not attempted; 25 open causes
(`../results.json`; the table: `python3 pipeline/check_results.py ../results.json --markdown`). The paper
README summarises them. The main finding holds: the fold-change filter biases the FDR and raises power, and
the signal and variance filters do not bias it. Three sentences overstate the paper's own figures and Fig. 3's
caption swaps two curves; the power gaps of Figs 5, S2, S5 and S6 are open.

## What the code does, against the paper

| Paper (Additional File 1) | Ours | Source |
| --- | --- | --- |
| m = 5000, n = 10 per group, N = 1000, pi0 = 0.8 (section 8) | The same; data set i with `set.seed(i)` | paper; seeds ours |
| mu from "a symmetric bitriangular distribution as described by [Langaas et al.]" | a = log2 1.2, b = log2 4, mode log2 2 | the first author's SSPA `rbitri` defaults |
| X = log(e^R + e^eps), eps ~ N(0, 0.01) | eps with SD 0.1, one draw per feature and group | found by search over SD 0, 0.01, 0.1 (Fig. 4 at x = 0); SSPA's `simdat` draws per feature |
| Filters W_S, W_FC, W_V = S_Z^2; "the same fraction removed based on the empirical quantiles" | `stat > quantile(stat, x)` | paper; the cut rule ours |
| BH, BY, aBH [Benjamini, Krieger, Yekutieli 2006], q-value | `p.adjust`; multtest `TSBH`; qvalue 2.34.0 defaults | paper names the methods; versions ours |
| Achieved FDR, power out of all non-null features ("4000"; 1000 with pi0 = 0.8) | out of the 1000 non-null features | paper (the 4000 is a slip) |
| Fig. 1: densities after filtering, t with 8 df, 25% removed | numerical integration over the pooled variance; variance filter on Sp^2, thresholds set under the null, delta the noncentrality | found by search (see `../results.json`, fig1) |
| Fig. 2: one data set "chosen at random" | our data set 1; variance axis 19 S_Z^2; the published bins | read from the figure |
| Figs 5, S3: BH at "various levels" | 0, 0.05, ..., 0.95, 0.99 and fractions 0 to 0.9 and 0.99 | read from the figure |
| FDR-bias test: permute per row, filter, BH = one-sided KS, N0 = 1000, then KS of the p-values | the same; the final KS one-sided | paper |
| Fig. 6 | data set 1 simulated without the noise term | found by search: the box medians come back only so |
| Leukemia: TEL-AML1 (44) against hyperdiploid (44), limma, BH 5%, subsets of 8, 16, 24 | GEO's 43 TEL-AML1 plus the one "TEL-AML1 (+hyperdiploidy)"; one subset per size (`set.seed(size)`), 20 more for the spread | ours |
| Post-FDR filtering, situations A, B (25, 50%), C (10, 20%) | C drops that fraction of the selected list; data sets 1 to 100 | ours (two readings tested); the count read from the figure |

## Reading the published figures

`pipeline/published.py` opens the authors' original figure files (R 2.10.0 and cairo PDFs) and the figure
pages of Additional File 1. Each panel's pixel-to-data map is fitted to its tick marks and printed labels (the
largest residual is 0.002 data units); each series is found by line style and colour, so its plotted values
come back as numbers (`output/published_values.json`). Fig. 7 and Figure S5 are drawn as segments between
markers; their points are read from the lines through the segments.

## Scoring

`pipeline/compare.py` draws each series of ours on a blank page with the published panel's axis map and line
width, does the same for the published series, renders both at 300 dpi and counts the share of each one's
ink within 2 px of the other's. The smaller share is the score. The same score is computed for wrong inputs
(another panel's quantity, another FDR method, another filter, pi0 = 0.7) and near misses (values x1.05 and
x0.95, the other noise reading, another random subset, the other readings of Fig. 1); the pass mark is 95%
or 1 point above the best control. The renders: `output/figures/fig*_ours.png` (ours on the published
figure with its series painted out) and `fig*_overlay.png` (ours in red over the published).
Where the published values can be read at our x, `comparison.json` also gives the differences in data units.

The claims (`pipeline/claims.py`) turn each sentence into a rule, evaluated on our run and, first, on the
values read from the paper's own figures (`text.arithmetic`).

## Layout

| Path | Content |
| --- | --- |
| `main.nf`, `nextflow.config` | The pipeline; `run_skyriver.sbatch` runs it on the BCM Skyriver cluster |
| `requirements.txt` | Python packages, pinned |
| `results_notes.json` | Labels, sources, assumptions and causes, written by hand; `pipeline/build_results.py` merges it with the run into `../results.json` |
| `results.json` | The repository's results check (`tools/check_results.py`): every panel's score and largest difference |
| `pipeline/fetch_inputs.sh` | Downloads the figure files, Additional File 1 and GSE13425, checks SHA-256 |
| `pipeline/published.py` | Reads the published figures back |
| `pipeline/simulate.R`, `summarize.py` | The simulation study in chunks of 50 data sets, and their means |
| `pipeline/one_dataset.R`, `fig1.R`, `leukemia.R` | Figs 2, 6, S4; Fig. 1; Figs 7, S5 |
| `pipeline/series.py`, `compare.py`, `claims.py` | Our series and the controls; renders and scores; claims |
| `pipeline/check_package.sh`, `make_rd.py` | The R package check; the Rd files from the roxygen comments |
| `pipeline/build_results.py`, `check_reproduction.py`, `check_results.py`, `compare_runs.py`, `sim_check.py` | `results.json` and the checks |
| `pipeline/build_page.py`, `page_template.html` | The results page |
| `output/` | Everything the pipeline writes: `sim/` (chunk sums of the 1000 data sets for both noise readings, and pi0 = 0.7), the means, the single-data-set and leukemia results, `figures/`, `comparison.json` |

## Run

From the repository root, with R 4.3.3 (multtest, qvalue, limma, jsonlite, knitr, markdown, testthat),
Python 3.12 with `requirements.txt`, and Nextflow:

```sh
nextflow run PMC2949886/figure-reproduction/main.nf --outdir results          # about 15 min
nextflow run PMC2949886/figure-reproduction/main.nf --outdir results --full   # all 1000 data sets again
sbatch PMC2949886/figure-reproduction/run_skyriver.sbatch --full                # on Skyriver
```

The default run (and CI, `.github/workflows/reproduce-pmc2949886.yml`) simulates data sets 1 to 50 again and
checks them against the committed `output/sim/sd0.1/chunk00`, then forms every mean from the committed
chunks. `--full` simulates all of them again (44 tasks of about a minute each).

## Pipeline steps

1. `FETCH`: the inputs, checksummed. `INSTALL_PACKAGE`: `filterfdr` into a library of the run.
2. `READ_PUBLISHED`: `published_values.json`.
3. `SIM_CHECK` (default) or `SIM_CHUNK` (`--full`), then `SUMMARIZE`: the simulation means.
4. `ONE_DATASET` (noise SD 0.1, 0.01 and none; 1000 permutations each), `FIG1`, `LEUKEMIA` (20 extra subsets).
5. `COMPARE`: renders, overlays, scores, controls, `comparison.json`.
6. `PACKAGE`: `R CMD build`, `R CMD check --no-manual`, the tutorial rendered and compared with the committed one.
7. `RESULTS`: `claims.json`, `../results.json` (`check_results.py --write`), `check_reproduction.py` (fails on a
   broken rule, a stale verdict, a rerun chunk that differs, a failed package check, or any difference from the
   committed outputs beyond 1e-6), `report.md` and the results page.

## Limits

- Seeds are not given, so the single-data-set figures (2, 6, S4) and the leukemia subsets (7, S5) can only agree
  in distribution; their verdicts are mostly partly or inconclusive for that reason.
- The published power is a little higher than ours in Figs 5, S2 and S6 (up to 0.016) and clearly higher in
  Figure S5; the causes are open (see `../results.json`).
- Figure S7 (bootFDR, permFDR) is not attempted: the implementations and their settings are not given.
- The first author's SSPA code was read, not run, in this session: our simulation follows its formulas and its
  order of random draws.
- The package check renders the tutorial with knitr's markdown engine (no pandoc on the cluster) and draws no
  plots (the cluster's R has no graphics device).
