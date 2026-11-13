# transtree

Bayesian reconstruction of transmission trees from genetic and epidemiological
data: who infected whom during an outbreak, from the pathogen genomes, the
premises' locations and the timing of detection and removal.

This is a reimplementation, from the paper's text and Text S1, of

> Morelli MJ, Thebaud G, Chadoeuf J, King DP, Haydon DT, Soubeyrand S.
> A Bayesian inference framework to reconstruct transmission trees using
> epidemiological and genetic data. *PLoS Comput Biol* 8(11):e1002768 (2012).
> [doi:10.1371/journal.pcbi.1002768](https://doi.org/10.1371/journal.pcbi.1002768)

The authors never released their R MCMC (no code link, no supplement code). This
package implements the model from the equations in the paper: the genetic
pseudo-likelihood of Eq. 5 (with the divergence-time tree traversal validated
against the worked Fig. S1 example), the spatial/timing likelihood of Eq. 7, the
gamma latency and detection distributions of Eq. 8, the exponential priors of
Eq. 9, and the Metropolis-Hastings sampler of Text S1.

## Language

Python. The default rule selects Python because the method relies on no R or
Bioconductor package; it is a self-contained MCMC over a model stated as
equations, implemented with NumPy. It is `source: reconstructed` (from the
paper's text), not a port of released code.

The published R code is lost, so the reconstruction is checked against the
paper: the pseudo-likelihood traversal against the Fig. S1 worked example, and
the full runs against the paper's printed medians, intervals and trees (see the
reproduction).

## Install

```bash
pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC3499255/package"
```

## Quick start

```python
import transtree as tt

data = tt.read_dataset(tt.example_path("example_epi.csv"),
                       tt.example_path("example_hamming.csv"),
                       s=4000.0, m=1e-4)
post = tt.run_mcmc(data, tt.MCMCConfig(iters=6000, seed=3))
for i, s in enumerate(post.best_tree):
    print(data.names[i], "<-", "external" if s == -1 else data.names[s])
print("mean latency (days):", post.median_ci(post.mean_latency))
```

Command line:

```bash
transtree EPI.csv HAMMING.csv --s 8176 --m 2.076e-5 --iters 50000 -o result.json
```

## What it does

- `read_fasta`, `hamming_matrix`, `read_epi_table`, `lonlat_to_km`, `read_dataset`:
  turn genomes and an epidemiological table into a `Data` object.
- `run_mcmc(data, MCMCConfig(...))`: run the sampler and return a `Posterior` with
  each premise's source probabilities, the most-likely tree, and the posteriors of
  the mean latency duration and the mean transmission distance.
- `simulate_outbreak(...)`: generate an outbreak from the model (used for the
  example data and the paper's simulation studies).
- `divergence_premise`, `genetic_log_pseudo_likelihood`: the genetic
  pseudo-likelihood and its tree traversal.

**Sampler note.** The sampler keeps the paper's Text S1 moves and adds one joint
`(source, infection-time)` move so the chain can, in one step, move a premise to
an early-infected source with a long latency (such as the IP5 link in the 2007
outbreak). It targets the same posterior; it is a mixing aid, recorded as a
deviation from the paper's exact move set.

## Tutorial

`tutorial/TUTORIAL.md` (generated from `tutorial/tutorial.ipynb`): install, the
example input, an API run, the command line, and the comparison with the expected
output.

## Reproduction

The paper's full 2007 and 2001 analyses, the simulated Fig. 2, the Table 1 /
Table S1 simulation series and the comparison against the published figures are in
the reproduction: <https://github.com/jeonglab-bcm/fossil/tree/main/PMC3499255>.

## Licence

MIT (reconstructed from the paper's text; the repository's licence). Cite the
paper above.
