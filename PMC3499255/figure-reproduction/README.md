# PMC3499255 figure reproduction

The pipeline reconstructs the transmission trees of Morelli et al. (2012) and
compares them with the published Figures 2, 3 and 4. The method is the Python
package [`../package`](../package) (`transtree`), reimplemented from the paper and
Text S1; the pipeline imports it, so there is one copy of the method.

## Results

Every verdict and number is read from [`../results.json`](../results.json), which
`check_results.py` computes from the run outputs. See the paper
[README](../README.md#results) for the summary. In short: the 2007 and 2001 trees,
the IP5 two-phase link, the K-hub, and the latency and distance medians all come
back; the one number that differs is the 2001 most-likely-scenario probability
(explained there).

## What the code does against the paper

The authors' R MCMC is lost. `transtree` implements, from the equations:

- the Jukes-Cantor substitution model and the genetic pseudo-likelihood of Eq. 5,
  whose divergence-time tree traversal is checked against the worked Fig. S1
  example (`checks.py pseudolik`);
- the spatial/timing likelihood of Eq. 7 (exponential kernel, mean transmission
  distance 2*alpha2) and the gamma latency / detection distributions of Eq. 8;
- the exponential priors of Eq. 9 and the Metropolis-Hastings sampler of Text S1
  (proposals for J, Tinf, D, alpha, beta and the acceptance ratios).

**Deviation.** The sampler adds one joint `(source, infection-time)` move to the
paper's Text S1 moves, so the chain can move a premise to an early-infected source
with a long latency in one step. It targets the same posterior; it is a mixing aid.

## Layout

```
figure-reproduction/
├── main.nf, nextflow.config, requirements.txt
├── results_notes.json            hand-written labels, sources, assumptions, causes
├── results.json                  the CI results-check file (expected values and paths)
├── pipeline/
│   ├── fetch_inputs.sh           download Datasets S1-S4, check SHA-256
│   ├── datasets.py               load the three datasets into transtree.Data
│   ├── analyze.py                run the MCMC on one dataset -> posterior JSON
│   ├── series.py                 Table 1 / Table S1 simulation series
│   ├── textclaims.py             spatial-connectivity numbers in the text
│   ├── checks.py                 pseudo-likelihood (Fig. S1) and arithmetic checks
│   ├── render.py                 draw our Figs 2-4 and the side-by-side overlays
│   ├── build_results.py          merge everything into results.json; check_results --write
│   ├── check_reproduction.py     verdicts + fresh-vs-committed (compare_runs) + report.md
│   ├── build_page.py             the results page from results.json
│   ├── make_results_check.py     write results.json (the CI results-check file)
│   └── check_results.py, compare_runs.py, check_package.py   (copied from the skill)
├── published/                    Figures 2-4 (CC BY) for comparison
└── output/                       committed run outputs (JSON summaries, figures, results.json, report.md)
```

## Run

```bash
nextflow run PMC3499255/figure-reproduction/main.nf --outdir results
```

Default (CI, deterministic): download the datasets, reconstruct the 2007 and 2001
outbreaks (fixed seed, 30,000 iterations), render Figs 3 and 4, run the
pseudo-likelihood and arithmetic checks, check the package, build `results.json`
and the page, and compare the fresh run with the committed `output/`.

```bash
nextflow run PMC3499255/figure-reproduction/main.nf --outdir results --full
```

`--full` also reruns the simulated Fig. 2 (one 20-premise outbreak, 15,000
iterations) and the Table 1 / Table S1 simulation series (12 simulations per
series, 3,000 iterations). Without `--full` these are read from `output/`.

Offline rerun with local datasets: add `--sources /path/to/Datasets`.

## Pipeline steps

`FETCH` downloads the data and checks SHA-256. `ANALYZE` runs the MCMC for the 2007
and 2001 datasets. `ANALYZE_TEST` and `SERIES` rerun (with `--full`) or read the
committed simulated outputs. `TEXTCLAIMS` and `CHECKS` compute the text numbers and
the two validation checks. `PACKAGE` builds, installs and tests `transtree` and runs
its tutorial. `RENDER` draws Figs 2-4. `RESULTS` merges everything into
`results.json`, computes verdicts, and compares the fresh run with `output/`.
`BUILD_PAGE` writes the results page.

## Limits and deviations

- **Stochastic MCMC.** Every result is MCMC output; the comparison is on the
  medians, the 95% intervals and the tree structure, not pixel by pixel. Per-field
  Monte Carlo tolerances are in `results_notes.json`.
- **Iteration counts.** 30,000 (real data) and 15,000 (Fig. 2) against the paper's
  5x10^5; the series use 12 simulations at 3,000 iterations against the paper's 100
  at 5x10^5. These are recorded deviations; they converge on the same trees and
  medians.
- **Figure PNGs** are not compared pixel by pixel across environments (matplotlib
  rendering is not bit-reproducible); the numbers behind them are checked, and
  `compare_runs` ignores `*.png`.
- **Not attempted:** the 100-premise simulation (about a month of compute), Fig. S14
  (external TCS program) and the lesion-age sensitivity analysis (prior variances
  given only as images). See `results.json`.
- **2001 simulation domain.** The paper gives 22x11 km (Results, Text S1) and
  20x10 km (Methods) for the 20-premise simulation; we use 22x11 km. The 2007/2001
  performance series reuse the real premise layouts.
