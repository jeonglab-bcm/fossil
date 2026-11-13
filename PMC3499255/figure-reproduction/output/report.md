# PMC3499255 reproduction report

## Results

| Item | Verdict | Measure | Why |
| --- | --- | --- | --- |
| Fig. 1 (dynamical model schematic) | not attempted | not attempted | A diagram of the transmission dynamics between two premises; nothing to recompute. |
| Fig. 5 (model DAG schematic) | not attempted | not attempted | The directed acyclic graph of the model; nothing to recompute. |
| Pseudo-likelihood divergence traversal vs the Fig. S1 worked example | agrees | divergence traversal matches all 6 pairs of the Fig. S1 example |  |
| Fig. 2 (simulated 20-premise outbreak) | agrees | 3 of 3 fields as printed | A single simulated outbreak reconstructed from the model; the tree, like the paper's, misses at most a couple of transmissions, and the true mean latency and mean transmission distance fall inside the 95% intervals. Exact dot sizes and the specific simulated dataset depend on the (undeposited) random seed. |
| Fig. 3 (2007 UK outbreak) | agrees | 7 of 7 fields as printed | The highest-posterior tree reproduces the paper's two-phase scenario (IP1b to IP2b and IP5, IP5 to IP4b, IP4b to the rest), and IP5 links the two phases with posterior probability 1. Medians and intervals agree within Monte Carlo error. |
| Fig. 4 (2001 Darlington cluster) | partly | 4 of 5 fields as printed | The highest-posterior tree reproduces the paper's K-hub scenario with the two longer chains, and the 24-day median latency. Our single most-likely labelled tree holds a smaller share of the posterior than the paper's reported >99%, because the better-mixing sampler splits probability across trees that differ only in one leaf's parent; grouped by the K-hub scenario the share is far higher. |
| Table 1 (performance over simulation series) | agrees | 6 of 6 fields as printed | Monte Carlo averages over a scaled-down series (fewer than the paper's 100 simulations and shorter chains, recorded as deviations). The fractions of correctly predicted transmissions and the mean posterior probabilities of the true transmission fall within Monte Carlo spread of the paper's values. |
| Table S1 (95%-interval coverage) | partly | 15 of 18 fields as printed | Coverage of the 95% intervals over the scaled simulation series. With far fewer simulations than the paper the coverage estimates are noisy (each is a fraction over the series), but follow the paper's pattern: high coverage for infection and infectiousness times, lower and more variable coverage for the parameters. |
| Spatial connectivity (text) | agrees | 10 of 10 fields as printed | The inter-premise distances and the mean inferred transmission lengths in the highest-posterior trees match the paper (IP5 to IP1b 18.2 km exactly). The mean transmission distance intervals and IP5's long mean latency agree within Monte Carlo error. |
| Arithmetic checks from the paper's own data | agrees | 3 of 3 data arithmetic checks agree with the text |  |
| Fig. S14 (TCS statistical-parsimony network) | not attempted | not attempted | Fig. S14 is a statistical-parsimony network built with the external TCS program (ref 16), a separate tool not part of this method; not reproduced. |
| 100-premise simulation (Text S1, Figs. S15-S17) | not attempted | not attempted | The 100-premise run took about a month of compute in 2012 at 5e5 iterations; it is out of the CI budget and was not run. The 20-premise simulation (Fig. 2) and the two real-data analyses exercise the same method. |
| Lesion-age prior sensitivity (Figs. S12-S13) | not attempted | not attempted | The flatter / more peaked lesion-age prior variances used for the sensitivity analysis are given only as images (Fig. S13) and are not stated numerically; not reproduced. |
| Python package transtree and its tutorial | agrees | transtree 0.1.0: wheel installed in a fresh environment and imported from it; tests 7 passed; tutorial 5 cells compared, 0 skipped (nondeterministic); TUTORIAL.md in sync |  |

7 agrees, 2 partly, 5 not attempted; 0 open causes.


## Fresh run against committed outputs

| File | Fresh vs committed | Detail |
| --- | --- | --- |
| arithmetic_check.json | same |  |
| pseudolik_check.json | same |  |
| series.json | same |  |
| test.json | same |  |
| textclaims.json | same |  |
| y2001.json | same |  |
| y2007.json | same |  |

7 of 7 files agree.

