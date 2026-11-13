# hivrecomb

The recombination rate and the distribution of selection coefficients from time series sequence
samples, as in:

> Neher RA, Leitner T. Recombination rate and selection strength in HIV intra-patient evolution.
> *PLoS Computational Biology* 6(1):e1000660 (2010).
> [doi:10.1371/journal.pcbi.1000660](https://doi.org/10.1371/journal.pcbi.1000660)

The authors' scripts were never released. This package is written from the paper's text, in
Python, because the paper's own analysis was in Python with NumPy and SciPy and the method needs
no R or Bioconductor package. It was checked against the paper, not against the original code;
the reproduction of the paper's figures and numbers is in
[PMC2813257](https://github.com/jeonglab-bcm/fossil/tree/main/PMC2813257).

## Install

```bash
pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC2813257/package"
```

## Quick start

```python
import hivrecomb as hr

seqs = hr.read_fasta(hr.example_path())           # names end in "|<time in generations>"
names = list(seqs)
X = hr.as_array([seqs[n] for n in names])
times = [float(n.rsplit("|", 1)[1]) for n in names]

events = hr.pair_events(X, times)                 # one row per qualifying pair of sites
fit = hr.estimate_rho(events, bin_width=600.0)    # Eq. 5 and Eq. 3
print(fit.c0, fit.c1, fit.c2, fit.rho)

rates = hr.frequency_changes(X, times)            # |dp| / dt per site, synonymous or not
```

On the command line:

```bash
hivrecomb example_alignment.fasta --bins 0 30 60 90
```

## What it does

| Function | What it gives |
| --- | --- |
| `codon_align` | A nucleotide alignment through the translations, with MUSCLE (the paper used v3.6). |
| `pair_events` | For every pair of biallelic gapless sites seen in three of four haplotypes at t_i: whether the missing haplotype shows up at t_{i+1}. |
| `bin_events`, `fit_saturation`, `estimate_rho` | The binned probability, the fit of Eq. 5 and the rate rho = c1 c2 / (<M pA pB> - c0). |
| `bootstrap_rho` | The spread of rho over resampled patients. |
| `frequency_changes` | The rate of allele frequency change at each site, classed synonymous or not. |
| `linked_mask`, `ks`, `share_above` | The hitch-hiking filter and the comparison of the two distributions. |

The tutorial, with an executed run on the bundled example, is in
[tutorial/TUTORIAL.md](tutorial/TUTORIAL.md).

## Licence

MIT, the repository's licence: the method is implemented from the paper's text, and no code of the
authors is used. The paper itself is in the public domain (CC0).
