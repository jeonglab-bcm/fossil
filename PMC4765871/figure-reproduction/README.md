# PMC4765871 figure reproduction

Ocone, Haghverdi, Mueller and Theis (2015) turn single-cell snapshots into pseudo time series and
fit ODE models of gene regulation to them. Their C++ and Matlab code
(`helmholtz-muenchen.de/fileadmin/ICB/software/inferenceSnapshot.zip`) is gone: the URL returns
404 and there is no Wayback capture. Everything here is rebuilt from the paper and its supplement.

## Run

```sh
# From the repository root. Light run: everything except the MCMC samplers, which are read from
# output/run (minutes on 4 cores). This is what CI runs.
nextflow run PMC4765871/figure-reproduction/main.nf --outdir results

# Everything, samplers included (about 1 hour on 48 cores), on the Skyriver cluster:
sbatch PMC4765871/figure-reproduction/run_skyriver.sbatch --full
```

Python 3.12 with `requirements.txt`; Nextflow 25.04. The samplers are compiled with numba for a
generic x86-64 CPU (`NUMBA_CPU_NAME=generic`) and OpenBLAS is pinned to its Haswell kernels, so a
light run gives the same numbers on the cluster and on GitHub's runners. A `--full` run on another
CPU gives other chains; its check reports the differences from the committed fits instead of
failing on them.

## Pipeline steps

| Process | Script | Does |
| --- | --- | --- |
| `FETCH` | `pipeline/fetch_inputs.sh` | The paper's PDF (PMC open-access copy on S3) and Moignard et al. 2013 Supplementary Table 3 (Springer, PMC mirror as fallback), checked against SHA-256. |
| `PUBLISHED` | `pipeline/published.py`, `pipeline/extract_published.py` | The nine figures rendered from the vector PDF at 600 dpi; the plotted curves, markers, dots and Fig. 6 bars read out of the vector drawing in data units. |
| `FFL` | `pipeline/ffl.py` | 300 cells of the OR-gate I1-FFL, deterministic reference, GENIE3, three Wanderlust replicates, GP emulators, the 12 candidate models, thermodynamic integration, posteriors and the three perturbations. |
| `TOGGLE` | `pipeline/toggle.py` | 400 cells of the six-gene toggle switch, diffusion map, branch clustering, Wanderlust, GENIE3, the 7 gC models of Fig. 6, the joint gC/gD fit, supp. Tables 1, 6 and 7. |
| `HAEM` | `pipeline/haem.py` | Moignard QC (597 cells), CT values, correlations, <d>(sigma), diffusion map, GENIE3 network, branch clustering, GMP and CLP pseudo time series, outlier removal, the 25 models of supp. Tables 8 and 9. |
| `FIGURES` | `pipeline/figures.py` | Our results drawn on the published pixel grid; renders, overlays, two-way scores within 2 px, wrong-input and near-miss controls. |
| `RESULTS` | `pipeline/build_results.py`, `pipeline/check_reproduction.py`, `pipeline/build_page.py` | `results.json` from the numbers and `results_notes.json`; `check_results.py --write`; the fresh run against the committed outputs (`compare_runs.py`); the results page. |

The shared code: `grn.py` (Hill ODE models, RK4, likelihood, Metropolis MCMC, differential
evolution start, thermodynamic integration, AIC and BIC), `geometry.py` (diffusion map, <d>,
branch clustering, Wanderlust, GENIE3), `emulate.py` (GP and piecewise-linear emulators),
`simulate.py` (the two stochastic systems).

`pipeline/sensitivity.py` is not part of the pipeline: it refits under single changes of unstated
settings and wrote `output/sensitivity.json`, which the causes in `../results.json` cite.

## What the code does against the paper

| Step | Paper | Here |
| --- | --- | --- |
| Simulation | Euler-Maruyama; kinetics in supp. Tables 3 and 5; FFL stops when gX > 960. Time step, noise, initial values, the FFL input and the toggle stopping rule not given. | Time step 0.01. Noise read from the traces of supp. Figs 12 and 16: sigma_s = 2 (FFL) and 6 (toggle). FFL input: logistic growth from 320 towards 1000 at rate 1/7. Toggle: gA = gB = 311 (the symmetric steady state), stop when a late gene exceeds 960. |
| Diffusion map | Gaussian kernel, sigma 1000 (toggle) and "100.9" (qPCR), density normalisation. | exp(-d^2 / (2 sigma^2)), density normalised. For the qPCR data sigma = 10^0.9: supp. Fig. 32A puts the maximum of <d> at log10 sigma = 0.9, and so does ours; 100.9 flattens the embedding (see Fig. 7B's controls). |
| Branch clustering | Dijkstra between hand-picked start and end cells, plus Nn = 15 neighbours. | Start at the centre (toggle: lowest late genes; qPCR: GATA2 high, GATA1 low); ends at the tips by farthest-point sampling among dense cells; Dijkstra on a 10-NN graph. |
| Wanderlust | Bendall et al. 2014; k = 18 or 15, l = k/3, three replicates with nearby starts. | A port of `wanderlust.m` (dpeerlab/cyt3, commit 1e8ec47) without band sampling or landmark flocking: 25 graphs, 20 landmarks, Euclidean distance, exponential weights. |
| GENIE3 | Thresholds 0.3, 0.1 and 0.08; settings not given. | Extra-trees, sqrt(p) inputs per split, 1,000 trees, weights normalised per target. Found by search: it gives 28 of Fig. 7C's 30 edges (random forests give 25 of 55). |
| Models | Hill functions; AND = product, OR = sum; supp. Eqs 4 and 5 for mixed gates. | As written; an OR with an AND inside gets one synthesis rate per term (Eq. 5, as supp. Table 8 prints two rates for those models). |
| Fitting | Metropolis on log parameters, diagonal proposal, RK4, uniform priors U(0,2000), U(0,30), U(0,50); likelihood variance, initial values, chain length, the informative prior not given. | Initial value and likelihood SD from a GP fit to the target series; start at the differential-evolution optimum; adaptive proposal; 20,000 kept iterations. Informative prior on lambda: N(0.25, 0.025). |
| Pseudo time | Not stated. The published axes run 0 to 100 (FFL), 0 to 140 (toggle) and 0 to 120 (qPCR); Fig. 9's points sit at integer pseudo times. | FFL and toggle fits on [0, T_f], T_f the mean stopping time, drawn on the published axes. qPCR: rank spread over 0 to 120. |
| Model choice | AIC = log L - W, BIC = log L - W/2 log N; thermodynamic integration, ladder not given. | As written; ladder t_i = (i/30)^5. |
| qPCR data | Moignard et al. 2013; "CT" with 15 = undetected; log expression = 20 - CT; outliers removed with a 22 to 28 cell window; CT = 15 replaced by Gaussian draws. | Moignard's QC gives exactly 597 cells (123 CLP, 124 GMP, 121 HSC, 116 LMPP, 113 PreMegE). CT = Ct - mean(Ubc, Polr2a), undetected 15. Window scaled to our series length; the first window that splits a series in two; draws N(15, SD of the detected CT). |

## Layout

| Path | Content |
| --- | --- |
| `main.nf`, `nextflow.config`, `run_skyriver.sbatch`, `requirements.txt` | The pipeline. |
| `pipeline/` | The steps above; `params/` holds the settings, the figure boxes and axis calibrations, and the numbers transcribed from the paper (`published_values.json`, `published_networks.json`, `supp_table7.tsv`). |
| `results_notes.json` | What `results.json` cannot compute: labels, assumptions and causes. |
| `published/figure-*.png` | The paper's figures, rendered from its PDF at 600 dpi, for comparison only (CC BY-NC 4.0; see `../README.md`). |
| `output/run/` | The analysis outputs, MCMC fits included (`*_fits.json`), as the light run reads them. |
| `output/fig*_ours.png`, `output/fig*_overlay.png`, `output/scores.json` | Renders on the published grid, overlays (red channel published, green and blue ours: cyan is ink only in the paper, red only ours, black both) and scores. |
| `output/sensitivity.json` | The one-off hypothesis tests (not part of the pipeline). |
| `output/report.md`, `output/site/index.html` | The check report and the results page (copied to `site/PMC4765871/`). |

## Limits

- No result can be exact: every one passes through unseeded simulation, Wanderlust and MCMC with
  settings the paper does not give. The paper's numbers are compared at their printed precision
  anyway, and the gap is a cause in `../results.json`.
- Our figures are drawn on the published axes from our own random draw, so a pixel score measures
  how close our curve lies to theirs, not whether the code is the same. Near-miss controls (a 1%
  shift, amplitude x 1.05) often score about as well as ours: those panels are inconclusive.
- The qPCR pseudo time series of the paper have 102 to 115 points (counted in the vector Fig. 9);
  the pathways have about 360 cells. The paper does not say which cells it kept; we keep all.
- The light run reads the committed MCMC fits; only a `--full` run tests them, and its chains
  depend on the CPU.
