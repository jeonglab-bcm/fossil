# Example data

| File | What it is |
| --- | --- |
| `example_alignment.fasta` | 42 sequences of 90 bp from a simulated population at three time points (14 each), 40 generations apart. Each name ends in `|<time in generations>`. |
| `example_expected.csv` | The expected output for that alignment in three distance bins (0-30, 30-60, 60-90 columns): `pairs`, `found` and `probability`. |

## Where it comes from

- Input: simulated by `scripts/make_example_data.py` (seed 20100129). A Wright-Fisher population
  of 200 sequences, mutation 1.5e-3 and recombination 3.0e-4 per site and generation, 300
  generations of burn-in and then two intervals of 40 generations. It is an example of the input
  format, not a copy of the paper's data (HIV env C2-V5 clones from GenBank; see the reproduction).
- Expected output: computed in the same script by a slow enumeration in plain Python over every
  pair of sites, independent of the package's vectorized NumPy code. The package reproduces it
  exactly: 116, 85 and 29 pairs with 27, 32 and 10 reappearances.
- Licence: simulated data, released with the package under its licence.

Compare the probabilities with an absolute tolerance of 5e-7, the precision they are written at.
