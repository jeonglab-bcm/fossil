# Example data

| File | What it is |
| --- | --- |
| `geometric_network.tsv` | Example input: a noisy geometric random graph, 150 proteins and 665 interactions, as an edge list with columns `protein_a`, `protein_b`. |
| `geometric_missing.tsv` | The 66 true edges that were deleted from it (what Algorithm 1 should recover). |
| `geometric_spurious.tsv` | The 66 spurious edges that were added to it (candidate false positives). |
| `geometric_numbered.txt` | The same network as 1-based number pairs (protein `P001` is 1), the input format of the authors' Matlab code. |
| `geometric_expected_distances.csv` | Expected output: the distance between every pair (11,175 rows) in the 2-dimensional embedding computed by the authors' Matlab code. |

## Where it comes from

- Input: synthetic, written by `scripts/make_example_data.py` (seed 20090807). 150 points uniform in the unit square, joined when closer than 0.15; 10% of the edges deleted and as many random non-adjacent pairs added; the largest connected component kept (all 150 points).
- Expected output: not from this package. `scripts/make_expected_output.sh` runs the authors' `embed_novi.m` (Kuchaiev et al., kuchaev.com/Denoising, archived by the Wayback Machine) under GNU Octave 10.3 on `geometric_numbered.txt` in 2 dimensions, and writes the pairwise distances of its coordinates. The authors' code is not included here.
- Compare with an absolute tolerance of 0.005: the authors' subspace iteration stops when no eigenvector moves by more than 0.001, so it is not exact. This package solves the eigenproblem exactly; on this example the largest difference is 0.002.
- Licence: synthetic data, released with the package under its licence (MIT).
