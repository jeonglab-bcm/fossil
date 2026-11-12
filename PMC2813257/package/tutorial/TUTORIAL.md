<!-- Generated from tutorial.ipynb by check_package.py --write. Do not edit by hand. -->

# hivrecomb tutorial

`hivrecomb` estimates the effective recombination rate and the distribution of selection
coefficients from sequence samples taken from one population at several times. It asks how often
a two-site haplotype that was missing at one time point shows up at the next, and how fast allele
frequencies change at synonymous and non-synonymous sites.

> Neher RA, Leitner T. Recombination rate and selection strength in HIV intra-patient evolution.
> *PLoS Computational Biology* 6(1):e1000660 (2010).
> [doi:10.1371/journal.pcbi.1000660](https://doi.org/10.1371/journal.pcbi.1000660)

The authors' scripts were never released; this package is written from the paper's text.

## 1. Install

```bash
pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC2813257/package"
```

```python
import hivrecomb as hr

print("hivrecomb", hr.__version__)
print(hr.CITATION)
```

```text
hivrecomb 0.1.0
Neher RA, Leitner T. Recombination rate and selection strength in HIV intra-patient evolution. PLoS Comput Biol 6(1):e1000660 (2010). doi:10.1371/journal.pcbi.1000660
```

## 2. The example input

The package ships a simulated alignment: 42 sequences of 90 bp from three samples of one
population, 40 generations apart. Each name ends in `|<time in generations>`, which is how the
package reads the sampling time.

```python
path = hr.example_path()
lines = path.read_text().splitlines()
print(path.name, len(lines) // 2, "sequences")
for line in lines[:4]:
    print(line[:70])
```

```text
example_alignment.fasta 42 sequences
>t0_s00|0
CCGCGCTGTCGTTTTCGGGAAGGAAAAAAATAAAGACAGTATTAGGAAGTGTCATTGCGCTCGCTACTGG
>t0_s01|0
CCGCACTGTCGTTTTCGGGACGGAAAAAAATACAGTCAGCGATTGGGTGTGTCTAAGGGCTGGCTCCTGG
```

```python
seqs = hr.read_fasta(path)
names = list(seqs)
X = hr.as_array([seqs[n] for n in names])
times = [float(n.rsplit("|", 1)[1]) for n in names]
print("alignment", X.shape[0], "x", X.shape[1], "columns")
print("sample times", sorted(set(times)))
```

```text
alignment 42 x 90 columns
sample times [0.0, 40.0, 80.0]
```

## 3. Run the method

`pair_events` finds every pair of sites that is biallelic and gapless at one time point, whose
alleles are each seen at least three times, and that shows three of the four possible haplotypes.
For each it records the distance between the sites, the elapsed time, and whether the fourth
(missing) haplotype turns up at the next time point.

```python
events = hr.pair_events(X, times)
print(len(events["d"]), "qualifying pairs")
print("missing haplotype seen again:", round(float(events["found"].mean()), 3))

binned = hr.bin_events(events["d"], events["found"], [0, 30, 60, 90])
for k in range(len(binned.centers)):
    print(f"{binned.edges[k]:>3.0f}-{binned.edges[k+1]:<3.0f} bp  "
          f"pairs {int(binned.pairs[k]):>4d}  found {int(binned.counts[k]):>3d}  "
          f"probability {binned.p[k]:.3f}")
```

```text
230 qualifying pairs
missing haplotype seen again: 0.3
  0-30  bp  pairs  116  found  27  probability 0.233
 30-60  bp  pairs   85  found  32  probability 0.376
 60-90  bp  pairs   29  found  10  probability 0.345
```

The probability rises with the distance between the sites, which is what recombination does
and what mutation and undersampling do not. Fitting Eq. 5 of the paper to the probability against
distance times elapsed time gives the rate (Eq. 3).

```python
fit = hr.estimate_rho(events, bin_width=600.0)
print(f"c0 {fit.c0:.3f}  c1 {fit.c1:.3f}  c2 {fit.c2:.3g}")
print(f"<M pA pB> {fit.MpApB:.3f}")
print(f"rho {fit.rho:.3g} per site and generation")
```

```text
c0 0.066  c1 0.276  c2 0.00226
<M pA pB> 1.970
rho 0.000327 per site and generation
```

## 4. Compare with the expected output

`example_expected.csv` was written by a slow enumeration over every pair of sites, in plain
Python, in `scripts/make_example_data.py`. It does not come from this package, so it checks the
vectorized code here.

```python
import csv

with open(hr.example_path("example_expected.csv"), newline="") as f:
    expected = list(csv.DictReader(f))

hits = 0
for k, row in enumerate(expected):
    same = (int(binned.pairs[k]) == int(row["pairs"])
            and int(binned.counts[k]) == int(row["found"]))
    hits += same
    print(f"{row['bin_low']:>3}-{row['bin_high']:<3} bp  ours {int(binned.pairs[k])}/"
          f"{int(binned.counts[k])}  expected {row['pairs']}/{row['found']}  "
          f"{'same' if same else 'DIFFERENT'}")
print(f"{hits} of {len(expected)} bins match the expected output")
assert hits == len(expected)
```

```text
  0-30  bp  ours 116/27  expected 116/27  same
 30-60  bp  ours 85/32  expected 85/32  same
 60-90  bp  ours 29/10  expected 29/10  same
3 of 3 bins match the expected output
```

## 5. Selection

`frequency_changes` gives the rate of allele frequency change at each site between consecutive
samples, classed synonymous or non-synonymous from the consensus codon. The example alignment is
simulated without selection, so the two distributions should be alike.

```python
rates = hr.frequency_changes(X, times, min_size=10)
syn = rates["synonymous"].astype(bool)
print(len(rates["rate"]), "observations:", int(syn.sum()), "synonymous,",
      int((~syn).sum()), "non-synonymous")
D, p = hr.ks(rates["rate"][~syn], rates["rate"][syn])
print(f"Kolmogorov-Smirnov D {D:.3f}, p {p:.3f}")
```

```text
114 observations: 21 synonymous, 93 non-synonymous
Kolmogorov-Smirnov D 0.098, p 0.989
```

## 6. From the command line

The same run as `hivrecomb`. Without `-o` it writes CSV to standard output.

```python
!hivrecomb "{path}" --bins 0 30 60 90
```

```text
bin_low,bin_high,pairs,found,probability,error
0,30,116,27,0.232759,0.044794
30,60,85,32,0.376471,0.066551
60,90,29,10,0.344828,0.109044
```

## 7. Your own data

- **Input:** one aligned FASTA per population, all sequences the same length, each name ending in
  `|<time in generations>`. Use `codon_align` to build the alignment through the translations, as
  the paper does (`codon_align(seqs, muscle="muscle")` needs MUSCLE on the path).
- **Options that matter:** `min_count` (how often each allele must be seen; the paper uses 3),
  the bin edges, and `weights` in the fit (`relative` weights each bin by 1/sqrt(counts)).
- **Output:** `pair_events` returns one row per pair of sites with `d` (distance in alignment
  columns), `dt` (generations), `found`, the sample sizes and the allele frequencies.
  `estimate_rho` returns the three fit parameters, `<M pA pB>` and `rho`, the recombination rate
  per site and generation.
- **Several populations:** run `pair_events` per population and join the tables with
  `concat_events`; `bootstrap_rho` resamples the populations to give the spread of `rho`.

The reproduction of the paper's figures and numbers on its own data, with the pipeline that runs
it, is in [PMC2813257](https://github.com/jeonglab-bcm/fossil/tree/main/PMC2813257).
