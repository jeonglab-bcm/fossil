# Example data

| File | What it is |
| --- | --- |
| `example_expression.tsv` | Example input: expression (log2 scale) of eight proteins P1 to P8 over eight samples of one study. Columns `protein`, `s1` to `s8`. |
| `example_network.tsv` | Example input: nine interacting pairs among P1 to P8. Columns `protein_a`, `protein_b`. |
| `example_locations.tsv` | Example input: known locations (NU, CY, PM; comma-separated; empty when unknown). |
| `expected_coherence.tsv` | Expected output: the expression coherence of each pair (Lee et al. 2013, Methods). |
| `expected_weights.tsv` | Expected output: the neighbour weights w_ki = 1 / (Psi_ki + rho) of the distance-1 and distance-2 neighbourhoods, rho = 2 (Lee et al. 2008). |
| `expected_possibility.tsv` | Expected output: degrees of possibility of eight confidence values, given the confidence scores of five positive and seven negative gold-standard proteins (Lee et al. 2013, Methods). |

## Where it comes from

- Input: synthetic, written by `scripts/make_example_data.py` from fixed formulas (no random numbers).
- Expected output: computed in the same script in plain Python, straight from the published formulas: Pearson
  correlations, medians and the share of links at or above each value for the coherence; every path of length
  one and two for the weights; the two cumulative shares for the possibility degree. The script does not import
  this package, so the comparison checks the package against the formulas.
- Licence: synthetic data, released with the package under its licence (MIT).

Compare with a relative tolerance of 1e-9.
