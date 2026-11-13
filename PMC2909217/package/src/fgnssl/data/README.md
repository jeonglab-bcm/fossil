# Example data

Synthetic, made by `scripts/make_example_data.py` (seeded; numpy, scipy, networkx and scikit-learn, not
fgnssl). Released with the package under the MIT licence.

| File | What it is |
| --- | --- |
| `expression.csv` | 40 genes x 12 conditions: four groups, each a noisy copy of one of four profiles whose pairwise correlation is -1/3. |
| `interactions.csv` | A connected random graph on the 40 genes (84 edges), standing in for protein interactions and complex co-memberships. |
| `pairs.csv` | 60 gene pairs. `true_label` is 1 for a pair inside one expression cluster and 0 across clusters; `label` shows every second one and leaves the rest blank (unlabelled). |
| `expected_clusters.csv` | Divisive correlation clustering written out from the paper's description with plain loops. |
| `expected_weights.csv` | Eq. 2 (L1 = 0.3) from those clusters' centroids. |
| `expected_properties.csv` | The 8 node properties: networkx for betweenness and closeness on 1 / w, eigenvector centrality (scaled to a maximum of 1), current-flow betweenness and information centrality (times n, the Stephenson and Zelen scale); strength and Barrat clustering by their formulas; stress by enumerating every shortest path. |
| `expected_features.csv` | The 18 pair features from those properties, networkx's weighted shortest paths and mutual neighbours. |
| `expected_scores.csv` | scikit-learn's `LabelSpreading` (rbf kernel, gamma = 1 / (2 sigma^2), alpha = 0.99) on the scaled features, sigma the median distance. |

Compare at a relative tolerance of 1e-6 (clusters exactly; scores to 1e-6 absolute).
