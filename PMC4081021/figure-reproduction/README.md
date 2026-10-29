# Figure reproduction (PMC4081021)

Code S1 of the paper is the authors' MATLAB implementation, with the measurement data, the
fitting script of every model, the saved result of every fit (`project/results/*_all.mat`:
multi-start optima, Hessians, profile likelihoods) and the plotting scripts behind each figure
(`plots_for_paper.m`, `plotODEMix_*_paper.m`, `plots_for_paper__model_comparison.m`). MATLAB
and its toolboxes are not available here, so the model, the likelihood and the plotting scripts
are ported to Python and checked against the saved results:

- **Port.** `pipeline/odemm.py` reads each model definition (rates, mean or median constraint,
  noise parameters, weights) from the authors' fitting script and evaluates `logLikelihood.m`.
  At the 51 saved optima (24 conversion-reaction models, 9 models for each of pathway models
  A, B and C) it gives the saved log-likelihood to within 9 × 10⁻⁴; the conversion reaction is
  solved in closed form, where the authors used CVODES at a tolerance of 10⁻⁷
  (`output/port_check.json`).
- **Figures.** `pipeline/figdata.py` computes what each data panel plots, step by step as the
  authors' scripts do (MATLAB's `hist` with bin centres, the staircase fills, `pchip`
  interpolation of the noise parameters, profile-likelihood intervals from
  `getConfidenceIntervals.m`). `pipeline/compare.py` draws these on the published figures'
  pixel grids (PLOS original-size files, 600 dpi) and counts, per colour, the published pixels
  within 4 px of ours and ours within 4 px of the published ones.
- **Tables.** `pipeline/make_tables.py` recomputes ℓ(θ*), BIC, rank, ΔBIC and the decision for
  Tables 1 and 2 and for Supporting Information S1 Table 1 (all 27 NGF models, the numbers
  behind Fig. 5B).
- **Refit.** `pipeline/refit.py` fits the 24 conversion-reaction models of Table 1 again from
  scratch: 2,000 Latin hypercube starts each inside the authors' bounds, L-BFGS-B with exact
  gradients (`pipeline/odemm_jax.py`, JAX). The authors used fmincon from 40 to 100 starts.

## Results

| Item | Result |
| --- | --- |
| Fig. 2B, 2E | The ODE-MM mean, both subpopulation means and the measured means: 100% both ways (2B), 98% and 89% (2E). The dashed means of the sample trajectories are 500 random cells in the original; we draw their exact expectation, and 20 seeded sample trajectories that are not scored. |
| Fig. 2C, 2F | Histograms and mixture densities at the six time points: 99.9% or better both ways for the curves, 91% or better for the histogram fills. |
| Fig. 2D, 2G | True parameter densities: 99% or better. The interval bars (profile likelihoods saved by the authors): edges 96% and 91% or better. |
| Fig. 3B–D, 4B–D | NGF pathway model A. Means against data: 99.8% or better both ways (3B); 81% and 99.8% (4B, where the coloured "w = …%" labels sit inside the axes). Histograms at 5 time points and 6 doses: 90% and 99% or better. Interval bars: 99% and 92% or better. The subpopulation weights are those printed in Fig. 4B: 69.7% (M_H3,2) and 68.8% (M_H3,3). |
| Fig. 5B | BIC of the 27 models: 96% and 100%. All 27 values equal S1 Table 1 to the printed four digits. |
| Fig. 5C | w₁ of M_H3,3: 68.8% (model A) and 70.0% (C), as published. Model B gives 69.8%; the figure shows 71.5%, which no saved fit of model B gives. |
| Fig. 6 | Correlations 0.895 and 0.696 and the mixture weights 68.0 / 32.0%, as published; scatter, histograms and ellipses 99% or better. |
| Table 1 | 116 of 120 fields as printed, from the saved fits and equally from our refit. The four differences are in the paper: scenario 1 M_H3,1 prints ℓ = 0.9911 (saved 0.99105); in scenario 2 the ranks of M_H1,1, M_H1,2, M_H1,3 are printed 12, 10, 11, but their printed BICs (−13.831, −13.768, −13.766) put them at 10, 11, 12. |
| Table 2, S1 Table 1 | All 180 fields as printed. |
| Refit (Table 1) | All 24 models reach the saved optimum (within 10⁻³ in ℓ); the best value is found by 12 to 1,865 of the 2,000 starts. With the authors' 40 or 100 starts, L-BFGS-B missed it for 8 models. |
| Saved optima (NGF) | For 49 of the 51 saved optima the exact gradient was computed and a local L-BFGS-B run started there gains at most 6 × 10⁻⁵ in ℓ (`output/optima_check.json`). The JAX solver fails at two pathway-model-C optima; the numpy port reproduces their ℓ. |

`output/report.md` lists every check and its threshold. Fig. 1 and the schematic panels 2A,
3A, 4A and 5A are not attempted.

## Details

- **Figs 3B and 4B plot the dose response at 60 min.** The data are at 30 min, and the model is
  fitted at 30 min, but the plotting script reuses the time vector of the kinetic panel
  (0 to 60 min) and takes its last point. The difference is small because pErk has nearly
  settled by 30 min; we draw it as the script does.
- **Fig. 6's mixture stopped early.** MATLAB's `gmdistribution.fit` stops when the
  log-likelihood changes by less than 10⁻⁶ of its value. From a random start, EM run that way
  stops at 68.0 / 32.0% in 289 of 300 starts; run to convergence it gives 68.1 / 31.9%. We
  emulate the MATLAB stopping rule. Panel B draws the control and stimulated cells together,
  as the script does.
- **Data.** The kinetic CSV labels its second time point "10 min"; the scripts and the paper use
  5 min. The scaling factors per experiment are fixed numbers in the fitting scripts
  (computed by `data_scaling.m`); the saved data structures already contain the scaled values,
  and we use those.
- **Fig. 2E.** The scenario-2 script writes two versions of the panel; the published one is
  `sample_trajectories.eps`, which includes the two ODE-MM subpopulation means.
- **Refit of the NGF models.** A blind multi-start with L-BFGS-B at the authors' start counts
  did not reach the saved optima of pathway model A (for example −43,278 against −40,348 for
  M_H2,1; `output/refit_ngfA_attempt.json`): about half the starts fail because the ODE solve
  fails at the extreme rates the bounds allow (10⁻¹⁰ to 10¹⁰), and L-BFGS-B stops early on the
  rest. We therefore check the saved NGF optima locally instead of refitting them.

## Layout

| Path | Content |
| --- | --- |
| `main.nf`, `nextflow.config` | Nextflow pipeline that runs every step below. |
| `pipeline/odemm.py` | The ODE-MM likelihood and the conversion-reaction and NGF pathway models A–C, in Python. |
| `pipeline/odemm_jax.py` | The same likelihood in JAX, with exact gradients, for refitting. |
| `pipeline/saved.py` | Reads the authors' fitting scripts and saved results. |
| `pipeline/figdata.py` | What each published panel plots, computed as in the authors' plotting scripts. |
| `pipeline/` | The other scripts (Python, shell). |
| `published/` | Figs 1 to 6 of the paper (PLOS original-size files, converted from TIFF to PNG) and Tables 1, 2 and S1 Table 1 as CSV, © 2014 Hasenauer et al., CC BY 4.0. |
| `output/` | `fig*_ours.png` (our panels, drawn with matplotlib), `fig*_overlay.png` (published faded, ours on top, at half the published resolution), `comparison.json`, `tables.json`, `port_check.json`, `optima_check.json`, `refit/` (one JSON per refitted model), `report.md`; `refit_ngfA_attempt.json` records the one-off blind refit of pathway model A described above (not part of the pipeline). |

## Run

Requirements: Python 3 with numpy, scipy, matplotlib and pillow; jax and diffrax for `--refit`;
Nextflow with Java 17 or later.

```sh
nextflow run PMC4081021/figure-reproduction/main.nf --outdir results
nextflow run PMC4081021/figure-reproduction/main.nf --outdir results --refit   # also refit Table 1 and check the saved optima
```

The run downloads Code S1 from Europe PMC (PLOS refuses scripted downloads) and checks its
SHA-256 (`--sources DIR` reuses a local `pcbi.1003686.s001.zip`). On a 12-core machine it
takes about 7 minutes without `--refit` and 14 with it; the refit runs on all cores. It writes the renders, the comparison, the tables
and `results/report.md`, and fails if a check falls below its threshold. The GitHub workflow
`.github/workflows/reproduce-pmc4081021.yml` does the same run, with `--refit`, on Ubuntu.

## Pipeline steps

| Step | Script | Output |
| --- | --- | --- |
| Fetch and check Code S1 | `fetch_inputs.sh` | `sources/ODEMM_implementation_v01` |
| Port check | `check_port.py`, `odemm.py` | `port_check.json` |
| Refit (with `--refit`) | `refit_all.sh`, `refit.py`, `odemm_jax.py` | `refit/` |
| Saved optima (with `--refit`) | `check_optima.py` | `optima_check.json` |
| Figures | `compare.py`, `figmeasure.py`, `figdata.py`, `render.py` | `fig*_ours.png`, `fig*_overlay.png`, `comparison.json` |
| Tables | `make_tables.py` | `tables.json` |
| Check | `check_reproduction.py` | `report.md` |
