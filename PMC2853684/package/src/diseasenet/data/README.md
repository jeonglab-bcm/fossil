# Example data

Synthetic, written by `scripts/make_example_data.py` (seed 20100224). The paper's data cannot be
redistributed: HPRD is free for academic use only, and the disease annotations come from OMIM's
morbid map.

| File | What it is |
| --- | --- |
| `network.tsv` | 700 interactions among 240 proteins (`P000`-`P239`), one pair per line. Eight dense modules of 6-8 proteins, plus random background interactions. |
| `candidates.csv` | 240 gene-disease pairs (`gene`, `disease`, `known`): for each of eight diseases, a "linkage interval" of 30 genes holding its 3-5 known genes (`known` = 1) and 25-27 others (`known` = 0). |
| `expected_scores.csv` | The expected leave-one-out scores of each pair: `neighborhood`, `oti`, `rw`, `prop`. |

## Where the expected scores come from

Not from the package. `make_example_data.py` computes them from the method definitions:
Neighborhood and Oti by counting neighbours in plain Python, RW and Prop as the exact fixed points
of their iterations (dense linear solves with numpy: p = r (I - (1 - r) W)^-1 p0 with r = 0.75,
and W'F with F = (1 - alpha) (I - alpha W')^-1 Y, alpha = 0.6).

Compare at these tolerances: Neighborhood and Oti exactly; RW and Prop within 1e-5 (absolute),
because the package iterates until the L2 change is below 1e-6, as the paper does, and stops short
of the fixed point by less than that.

Licence: MIT, as the package.
