<!-- Generated from tutorial.ipynb by check_package.py --write. Do not edit by hand. -->

# diseasenet tutorial

Scores that associate genes with diseases from a protein interaction network, evaluated
leave-one-out, as compared by Navlakha and Kingsford (2010): **Neighborhood** (fraction of a gene's
neighbours known to cause the disease), **Oti** (number of such neighbours), **RW** (random walk with
restart from the disease's genes) and **Prop** (network propagation). A gene-disease pair is
predicted when its score exceeds a threshold θ and the gene lies in a linkage interval of the disease.

> Navlakha S, Kingsford C. The power of protein interaction networks for associating genes with
> diseases. *Bioinformatics* 26(8):1057-1063 (2010). doi:10.1093/bioinformatics/btq076

## Install

```bash
pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC2853684/package"
```

```python
import diseasenet as dn
print(dn.__version__)
```

```text
0.1.0
```

## Example input

A synthetic network of 240 proteins and eight diseases, each with a linkage interval of 30 candidate genes (see `data/README.md`).

```python
import csv
net = dn.read_network(dn.example_path("network.tsv"))
cands = dn.read_candidates(dn.example_path("candidates.csv"))
ann = cands.annotations()
print(len(net), "proteins,", net.n_interactions, "interactions")
print(len(cands), "candidate pairs,", int(cands.known.sum()), "known associations,", len(ann), "diseases")
for g, d, k in list(zip(cands.genes, cands.diseases, cands.known))[:5]:
    print(g, d, int(k))
```

```text
240 proteins, 700 interactions
240 candidate pairs, 31 known associations, 8 diseases
P002 Disease1 1
P003 Disease1 1
P004 Disease1 1
P016 Disease1 0
P024 Disease1 0
```

## Run the methods

Each score is leave-one-out: when a gene is scored, its own disease associations are ignored.

```python
scores = {
    "neighborhood": dn.neighborhood_scores(net, ann, cands),
    "oti": dn.oti_scores(net, ann, cands),
    "rw": dn.rw_scores(net, ann, cands),
    "prop": dn.prop_scores(net, ann, cands),
}
thresholds = {"neighborhood": 0.25, "oti": 0.5, "rw": 0.01, "prop": 0.15}
print(f"{'method':14s}{'theta':>8s}{'precision %':>13s}{'recall %':>10s}{'predicted':>11s}")
for m, s in scores.items():
    p, r, n = dn.precision_recall(dn.predictions(s, thresholds[m]), cands.known)
    print(f"{m:14s}{thresholds[m]:>8}{p:>13.1f}{r:>10.1f}{n:>11d}")
```

```text
method           theta  precision %  recall %  predicted
neighborhood      0.25        100.0      38.7         12
oti                0.5         65.0      83.9         40
rw                0.01         80.8      67.7         26
prop              0.15        100.0      25.8          8
```

## Compare with the expected output

The expected scores were computed without the package, from the method definitions (`data/README.md`). Neighborhood and Oti must match exactly; RW and Prop within 1e-5, because the iteration stops when the L2 change is below 1e-6, as in the paper.

```python
expected = list(csv.DictReader(open(dn.example_path("expected_scores.csv"))))
tol = {"neighborhood": 0.0, "oti": 0.0, "rw": 1e-5, "prop": 1e-5}
for m, s in scores.items():
    ok = sum(abs(a - float(e[m])) <= tol[m] + 1e-12 for a, e in zip(s, expected))
    print(f"{m}: {ok} of {len(expected)} pairs match the expected output")
    assert ok == len(expected)
```

```text
neighborhood: 240 of 240 pairs match the expected output
oti: 240 of 240 pairs match the expected output
rw: 240 of 240 pairs match the expected output
prop: 240 of 240 pairs match the expected output
```

## Command line

The same scores, written to a CSV file.

```python
net_path, cand_path = dn.example_path("network.tsv"), dn.example_path("candidates.csv")
!diseasenet "{net_path}" "{cand_path}" -m rw -m oti -o scores.csv
rows = list(csv.DictReader(open("scores.csv")))
print(len(rows), "rows; first:", rows[0]["gene"], rows[0]["disease"], rows[0]["known"])
same = sum(abs(float(r["rw"]) - s) < 1e-15 for r, s in zip(rows, scores["rw"]))
print(same, "of", len(rows), "RW scores equal the API's")
```

```text
240 rows; first: P002 Disease1 1
240 of 240 RW scores equal the API's
```

## Your own data

- **Network**: one interaction per line, two protein names separated by white space (unweighted).
  `dn.read_network(path, self_loops=True)` adds a self-interaction to every protein.
- **Candidates**: CSV with `gene`, `disease`, `known` (1 or 0): every gene in a linkage interval of
  each disease. Known associations (`known` = 1) are the seeds of each disease; genes outside the
  network score 0.
- **Options**: `rw_scores(..., restart=0.75, tol=1e-6)`, `prop_scores(..., alpha=0.6, tol=1e-6)`.
  Cluster scores: `dn.cluster_scores(clusters, ann, cands)` with clusters from any clustering (the
  paper used MCL at inflation 2.0).
- **Output**: one score per candidate pair, in the candidates' order. `dn.pr_curve(scores, known,
  thetas)` gives precision and recall (percent) over thresholds; `dn.per_disease(predicted, cands)`
  gives them per disease; `dn.neighborhood_homophily` and `dn.average_pairwise_distance` measure how
  close a disease's genes sit in the network.

## The paper's data

The reproduction reruns these methods on the paper's HPRD and OPHID networks and compares every
score, figure and number with the paper: results page <https://jeonglab-bcm.github.io/fossil/PMC2853684/>,
pipeline <https://github.com/jeonglab-bcm/fossil/tree/main/PMC2853684/figure-reproduction>.
