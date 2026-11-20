<!-- Generated from tutorial.ipynb by check_package.py --write. Do not edit by hand. -->

# transtree: reconstructing a transmission tree

`transtree` reconstructs who infected whom during an outbreak, by combining the
pathogen genomes with the premises' locations and timing. It is a reimplementation,
from the paper's text and Text S1, of the Bayesian MCMC of

> Morelli MJ, Thebaud G, Chadoeuf J, King DP, Haydon DT, Soubeyrand S.
> A Bayesian inference framework to reconstruct transmission trees using
> epidemiological and genetic data. PLoS Comput Biol 8(11):e1002768 (2012).
> doi:10.1371/journal.pcbi.1002768

The authors never released their R code. This package implements the model, the
genetic pseudo-likelihood (Eq. 5), the MCMC and a simulator from the paper.

## 1. Install

```bash
pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC3499255/package"
```

```python
import transtree as tt

print("transtree", tt.__version__)
print(tt.CITATION)
```

```text
transtree 0.1.0
Morelli MJ, Thebaud G, Chadoeuf J, King DP, Haydon DT, Soubeyrand S. A Bayesian inference framework to reconstruct transmission trees using epidemiological and genetic data. PLoS Comput Biol 8(11):e1002768 (2012). doi:10.1371/journal.pcbi.1002768
```

## 2. The example input

The package ships a small 6-premise outbreak simulated from the model (see
`data/README.md`). The input is an epidemiological table (location in km,
detection time `Tobs`, removal time `Tend`, clinical lesion-age `Dobs`) and the
matrix of pairwise Hamming distances between the premises' genomes.

```python
data = tt.read_dataset(tt.example_path("example_epi.csv"),
                       tt.example_path("example_hamming.csv"),
                       s=4000.0, m=1e-4)
print("premises:", data.names)
print("Hamming distances between genomes:")
print(data.M.astype(int))
```

```text
premises: ['F1', 'F2', 'F3', 'F4', 'F5', 'F6']
Hamming distances between genomes:
[[ 0 13  5  7 19  9]
 [13  0 22 20 27  8]
 [ 5 22  0 15 13 23]
 [ 7 20 15  0 27 17]
 [19 27 13 27  0 22]
 [ 9  8 23 17 22  0]]
```

## 3. Run the method

`run_mcmc` returns a posterior summary: each premise's source probabilities, the
most-likely transmission tree, and the posteriors of the mean latency duration and
the mean transmission distance. A fixed seed makes the run reproducible.

```python
post = tt.run_mcmc(data, tt.MCMCConfig(iters=6000, burn_in_frac=0.4, seed=3))
print("most likely tree (premise <- source):")
for i, s in enumerate(post.best_tree):
    print(f"  {data.names[i]} <- {'external' if s == -1 else data.names[s]}")
lat = post.median_ci(post.mean_latency)
dist = post.median_ci(post.mean_distance)
print(f"mean latency duration: median {lat[0]:.1f} days, 95% ({lat[1]:.1f}, {lat[2]:.1f})")
print(f"mean transmission distance: median {dist[0]:.1f} km, 95% ({dist[1]:.1f}, {dist[2]:.1f})")
```

```text
most likely tree (premise <- source):
  F1 <- external
  F2 <- F6
  F3 <- F1
  F4 <- F1
  F5 <- F3
  F6 <- F1
mean latency duration: median 14.7 days, 95% (7.0, 71.2)
mean transmission distance: median 14.6 km, 95% (2.9, 56.8)
```

## 4. Compare with the expected output

The example was simulated, so the true transmission tree is known. The expected
output below comes from the simulator (not from `transtree`), so this is a genuine
check that the inference recovers a tree it was not told.

```python
import json
import numpy as np

expected = json.loads(tt.example_path("example_expected.json").read_text())
true_tree = expected["true_tree"]
correct = 0
for i in range(data.I):
    pred = int(np.argmax(post.trans_prob[i]))
    pred = -1 if pred == data.I else pred
    correct += int(pred == true_tree[i])
print(f"{correct} of {data.I} premises: most-likely source equals the true source")
assert correct >= data.I - 1, "inference should recover almost every true source"
```

```text
5 of 6 premises: most-likely source equals the true source
```

## 5. From the command line

The same run from the shell, writing a JSON summary:

```python
import subprocess
import sys

epi = tt.example_path("example_epi.csv")
ham = tt.example_path("example_hamming.csv")
subprocess.run([sys.executable, "-m", "transtree", str(epi), str(ham),
                "--s", "4000", "--m", "1e-4", "--iters", "4000", "--seed", "3",
                "-o", "cli_out.json"], check=True)
cli = json.load(open("cli_out.json"))
print("most likely tree from the CLI:")
for child, src in zip(cli["names"], cli["most_likely_tree"]):
    print(f"  {child} <- {src}")
```

```text
most likely tree from the CLI:
  F1 <- external
  F2 <- F6
  F3 <- F1
  F4 <- F1
  F5 <- F3
  F6 <- F1
```

## 6. Your own data

- **Input:** for each premise, its location in km (`x_km`, `y_km`; project
  longitude and latitude with `tt.lonlat_to_km`), the detection time `Tobs`, the
  removal time `Tend`, the clinical lesion-age assessment `Dobs`, and one consensus
  genome. Build the Hamming matrix with `tt.hamming_matrix`.
- **Constants:** `s` is the genome length, `m` the substitution rate per
  nucleotide per day.
- **Output:** each premise's source probabilities, the most-likely tree, and the
  posterior median and 95% interval of the mean latency duration and the mean
  transmission distance. Use more iterations (10^5 or more) for real outbreaks.

For the paper's full 2007 and 2001 analyses, with the comparison against the
published figures, open the reproduction:
<https://github.com/jeonglab-bcm/fossil/tree/main/PMC3499255>.
