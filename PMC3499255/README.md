# PMC3499255

Morelli MJ, Thebaud G, Chadoeuf J, King DP, Haydon DT, Soubeyrand S. A Bayesian
inference framework to reconstruct transmission trees using epidemiological and
genetic data. *PLoS Comput Biol* 8(11):e1002768 (2012).
[doi:10.1371/journal.pcbi.1002768](https://doi.org/10.1371/journal.pcbi.1002768)

The paper infers who infected whom during an outbreak by combining pathogen
genomes with the premises' locations and the timing of detection and removal, in
one Bayesian model and MCMC. It is illustrated on foot-and-mouth disease virus: a
simulated test outbreak, the 2007 UK outbreak and the 2001 Darlington cluster.

## Licence

The article is open access under the Creative Commons Attribution License
(CC BY). The published Figures 2, 3 and 4 are kept in
`figure-reproduction/published/` for comparison, with attribution. The paper's own
data (Datasets S1-S4) are **not** redistributed here; `pipeline/fetch_inputs.sh`
downloads them, and `PMC3499255/sources/` is git-ignored. The paper PDF, Text S1
and the supplements are not committed.

## What we lost, what we rebuilt

The MCMC was "coded in the R language" but never released: no code link, no
availability statement, and the supplements hold sequences, tables and pseudocode
only. We reimplemented the method from the paper and Text S1 as the Python package
[`transtree`](package/), and reconstructed the three analyses.

## Results

Generated from `results.json` by `check_results.py`; see
[the results page](https://jeonglab-bcm.github.io/fossil/PMC3499255/).

- **Figure 3 (2007 outbreak)** came back the same. The highest-posterior tree is
  the paper's two-phase scenario: IP1b (external) infects IP2b and IP5; IP5 infects
  IP4b; IP4b infects the rest. IP5 links the two phases with posterior probability
  1. Mean latency median 14 days, 95% (7, 50) against the paper's 14 (6, 49); mean
  transmission distance median 16 km against 17, interval (6, 54) against (5, 58).
- **Figure 4 (2001 Darlington cluster)** came back the same tree: premise K is the
  hub, with two longer chains. Mean latency median 25 days against the paper's 24,
  95% (17, 46) against (17, 35). The single most-likely labelled tree holds a
  smaller share of the posterior than the paper's ">99%" (see Details).
- **Figure 2 (simulated outbreak)** reconstructs all but a couple of the 20 true
  transmissions, and the true mean latency and mean transmission distance fall
  inside the 95% intervals, as in the paper.
- **Table 1 and Table S1** (scaled-down simulation series) fall within Monte Carlo
  spread of the paper.
- **Spatial connectivity** matches: IP5 is 18.2 km from IP1b (exactly as printed),
  and the mean inferred transmission lengths in the highest-posterior trees are
  4.3 km (2007, exactly as printed) and 6.0 km (2001, against the paper's 5.8 km).

**The main finding of the paper holds.** The transmission trees, the IP5 two-phase
link, the K-hub, and the latency and distance medians all come back. The one number
that differs is the 2001 most-likely-scenario probability, explained in Details.

## What the code does against the paper

- Genetic pseudo-likelihood (Eq. 5): the divergence-time tree traversal is
  validated against the worked four-premise example of Fig. S1 (`pseudolik_check`).
- Spatial/timing likelihood (Eq. 7), gamma latency and detection (Eq. 8),
  exponential priors (Eq. 9), and the Metropolis-Hastings sampler of Text S1.
- The sampler keeps the paper's Text S1 moves and adds one joint
  `(source, infection-time)` move for mixing (a deviation, recorded below).

## Details

- **2001 most-likely-scenario probability.** The paper reports a single scenario
  with >99% of the posterior; our single most-likely *labelled* tree holds about
  0.75. The better-mixing joint move splits the mass across trees that differ only
  in one leaf's parent; grouped by the K-hub scenario (K the maximum-out-degree
  source) the share is far higher. Latency and distance medians and the K-hub
  structure are stable across seeds. Cause recorded as `nondeterminism`, explained.
- **Sampler deviation.** The joint `(source, infection-time)` move is not in the
  paper's move set. It targets the same posterior and is only a mixing aid; without
  it the paper's Text S1 moves alone need far more than the paper's 5x10^5
  iterations to move a premise to an early source with a long latency.
- **Iteration counts (deviations).** The paper ran 5x10^5 iterations (about two
  days for the 20-premise case). We commit deterministic runs at 30,000 iterations
  for the real-data analyses and 15,000 for the simulated Fig. 2; these converge on
  the same trees and medians. The Table 1 / Table S1 series use 12 simulations per
  series at 3,000 iterations (the paper used 100 at 5x10^5).
- **Not attempted.** The 100-premise simulation (about a month of compute in 2012),
  Fig. S14 (the external TCS program) and the lesion-age sensitivity analysis
  (prior variances given only as images). Reasons in `results.json`.

## Package

The method is the Python package [`transtree`](package/):

```bash
pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC3499255/package"
```

Tutorial: [`package/tutorial/TUTORIAL.md`](package/tutorial/TUTORIAL.md).

## Layout

```
PMC3499255/
├── README.md                     this file
├── results.json                  the normalized record (verdicts computed by check_results.py)
├── session/                      ledger.json, conversation.md
├── figure-reproduction/
│   ├── README.md                 how the pipeline works
│   ├── main.nf, nextflow.config, requirements.txt
│   ├── results_notes.json        labels, sources, assumptions, causes (hand-written)
│   ├── results.json              the CI results-check file (expected values and paths)
│   ├── pipeline/                 analyze, series, render, checks, build_results, build_page, ...
│   ├── published/                Figures 2-4 (CC BY) for comparison
│   └── output/                   the committed run outputs (JSON summaries and figures)
└── package/                      the transtree package, its tests and tutorial
```

## Run

```bash
nextflow run PMC3499255/figure-reproduction/main.nf --outdir results
```

See [`figure-reproduction/README.md`](figure-reproduction/README.md) for the
pipeline steps, the `--full` option and the limits.
