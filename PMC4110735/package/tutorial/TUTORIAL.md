<!-- Generated from tutorial.ipynb by check_package.py --write. Do not edit by hand. -->

# gecon tutorial

GeCON builds a signed gene co-expression network from local expression patterns. It turns each step between two neighbouring conditions into an angle and a direction (up or down), counts for every gene pair the steps that match (same direction, similar angle) or mirror each other (opposite direction), and connects the pairs whose matching share exceeds a threshold θ. The sign of an edge says whether the pair moves together (+1) or in opposite directions (−1).

The method is from Roy S, Bhattacharyya DK, Kalita JK. Reconstruction of gene co-expression network from microarray data using local expression patterns. *BMC Bioinformatics* 15(Suppl 7):S10 (2014). doi:10.1186/1471-2105-15-S7-S10. The authors' Java program is lost; this package reimplements it from the paper's equations.

## 1. Install

```bash
pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC4110735/package"
```

It needs Python 3.10 or later and NumPy.

```python
import gecon

print("gecon", gecon.__version__)
```

```text
gecon 0.1.0
```

## 2. The example input

Two examples ship with the package. The first is the paper's Figure 7: one gene with the three values 343, 314 and 409. The second is the pair of rat genes of the paper's Figure 2 (GEO GDS3702, Mrps26 and Pfn2, 12 samples). `data/README.md` says where each file comes from.

```python
fig7 = gecon.example_path("fig7_profile.tsv")
pair = gecon.example_path("gds3702_mrps26_pfn2.tsv")
for path in (fig7, pair):
    genes, conditions, X = gecon.read_matrix(path)
    print(path.name, "-", len(genes), "genes x", len(conditions), "conditions")
    for g, row in zip(genes, X):
        print(f"  {g:<8}", " ".join(f"{v:7.1f}" for v in row))
```

```text
fig7_profile.tsv - 1 genes x 3 conditions
  G          343.0   314.0   409.0
gds3702_mrps26_pfn2.tsv - 2 genes x 12 conditions
  Mrps26     329.3   369.1   290.3   362.0   322.8   367.8   325.5   300.0   372.0   310.9   409.8   333.3
  Pfn2       180.9   163.5   209.6   126.6   225.9   189.4   223.0   251.5   141.3   169.3    71.5   169.7
```

## 3. Run the method

`edge_patterns` gives each edge's angle (Eq. 5) and regulation (Eq. 4). `gecon` builds the network with θ = 0.5 (half of the edges must match) and τ = 20 degrees, and returns the signed adjacency matrix and the supports behind it.

```python
genes, _, X = gecon.read_matrix(fig7)
regulation, angle = gecon.edge_patterns(X[0])
for k, (a, r) in enumerate(zip(angle, regulation), 1):
    print(f"edge {k}: angle {a:.2f} degrees, regulation {int(r):+d}")

genes, _, X = gecon.read_matrix(pair)
A, sup = gecon.gecon(X, theta=0.5, tau=20)
for e in gecon.edge_list(A, sup, genes):
    print(e)
```

```text
edge 1: angle 137.53 degrees, regulation -1
edge 2: angle 52.49 degrees, regulation +1
{'gene1': 'Mrps26', 'gene2': 'Pfn2', 'sign': -1, 'pos_support': 0.0, 'neg_support': 0.6363636363636364}
```

## 4. Compare with the expected output

The expected outputs come from the paper's text, not from this package: Figure 7 prints the angles (138 and 52 degrees) and the regulation (−1, +1), and the paper says the two Figure 2 genes show negative regulation.

```python
import csv


def rows(name):
    with open(gecon.example_path(name), newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


exp7 = rows("fig7_expected.tsv")
genes7, _, X7 = gecon.read_matrix(fig7)
r7, a7 = gecon.edge_patterns(X7[0])
checks = [f"{a:.0f}" == e["angle_printed"] and int(r) == int(e["regulation"]) for a, r, e in zip(a7, r7, exp7)]

exp2 = rows("gds3702_expected.tsv")[0]
i, j = genes.index(exp2["gene1"]), genes.index(exp2["gene2"])
checks.append(int(A[i, j]) == int(exp2["sign"]))
print(sum(checks), "of", len(checks), "expected values match")
assert all(checks)
```

```text
3 of 3 expected values match
```

## 5. From the command line

The same run as a command. Without `-o` the edge list goes to standard output; `--patterns` prints the angles instead.

```python
!gecon "{pair}"
!gecon "{fig7}" --patterns
```

```text
gene1,gene2,sign,pos_support,neg_support
Mrps26,Pfn2,-1,0,0.636364
gene	edge	angle	regulation
G	1	137.5274	-1
G	2	52.4856	1
```

## 6. Your own data

- **Input:** a tab- or comma-separated file with a header row, then one row per gene: its name, then one value per condition, in the order the conditions were measured (GeCON compares neighbouring conditions, so the order matters).
- **θ** (`theta`, `--theta`): the share of the M − 1 edges that must match for two genes to be connected. The paper keeps it above 0.5.
- **τ** (`tau`, `--tau`): how close two angles must be, in degrees. The paper uses 15 to 25.
- **Standardise** (`--standardize`): the angle of Eq. (5) uses the two raw values, so for positive values of similar size every edge sits near 45 degrees (up) or 135 degrees (down) and almost every pair matches. Centring and scaling each gene first gives a sparse network. The reproduction found this necessary on every real dataset.
- **Several time series** (`segments`, `--segments 21,21,21`): edges that join two series are left out.
- **Output columns:** `gene1`, `gene2`, `sign` (+1 together, −1 opposite), `pos_support` and `neg_support` (the shares of matching and mirrored edges).

## 7. The reproduction

The paper's figures and tables, rerun with this package on the paper's data, are in the [PMC4110735 folder](https://github.com/jeonglab-bcm/fossil/tree/main/PMC4110735) of the fossil repository, with a [results page](https://jeonglab-bcm.github.io/fossil/PMC4110735/).
