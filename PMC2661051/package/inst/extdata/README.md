# Example data

| File | What it is |
| --- | --- |
| `sim_expression.csv` | One data set of the paper's simulation study: 600 genes (rows, `g001` to `g600`) by 20 samples, rounded to 4 decimals. Written by `scripts/make_example_data.R` with `simulate_ackermann(seed = 2009)`. |
| `sim_labels.csv` | The class of each sample: 0 for the first 10, 1 for the last 10 (the shifted class). |
| `sim_sets.gmt` | The nine gene sets of the simulation, in GMT format (name, description, genes). |
| `paper_table4_resampling.csv` | The expected output: the detection rates of the nine sets for the mean of the squared moderated t with gene sampling, as printed in Table 4 (and Tables 2 and 3) of Ackermann and Strimmer (2009). |

The expected output comes from the paper, not from this package: it is the share of 100
simulated data sets in which each set was significant at p <= 0.05 in the authors' lost R code.
A rerun with other random numbers can only agree within Monte Carlo error; the tutorial and the
tests compare with `rate_tolerance()` (a 99% two-proportion band, decided before the comparison).

The simulation design (600 genes, 20 samples, nine sets, shifts 0.75 and 1, correlation 0.6) is
from the paper's Methods. The data are synthetic and carry the package's MIT licence. The
paper is CC BY 2.0: Ackermann M, Strimmer K. A general modular framework for gene set enrichment
analysis. BMC Bioinformatics 10:47 (2009). doi:10.1186/1471-2105-10-47.
