<!-- Generated from tutorial.ipynb by check_package.py --write. Do not edit by hand. -->

# rfld tutorial

`rfld` grows random forests on SNP genotypes and ranks the SNPs by permutation importance. It implements the two revisions of Meng et al. (2009) for SNPs in linkage disequilibrium (LD):

- **RF1**, the revised tree builder: once a tree splits on a SNP, the SNPs whose r² with it exceeds a threshold R leave that tree's pool of candidates, so SNPs in LD never share a tree.
- **IM1**, the revised importance: the permutation importance is averaged over the trees that use the SNP, not over all trees (IM0).

The forest itself follows Breiman and Cutler's Fortran Random Forests 5.1, the program the authors modified.

> Meng YA, Yu Y, Cupples LA, Farrer LA, Lunetta KL. Performance of random forest when SNPs are in linkage disequilibrium. *BMC Bioinformatics* 10:78 (2009). [doi:10.1186/1471-2105-10-78](https://doi.org/10.1186/1471-2105-10-78)

## 1. Install

```bash
pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC2666661/package"
```

It needs Python 3.10 or later, NumPy and Numba. This notebook was run in a fresh environment with the package installed from its wheel.

```python
import rfld

print("rfld", rfld.__version__)
```

```text
rfld 0.1.0
```

## 2. The example input

One simulated case-control data set from the paper's simulation design: 250 cases and 250 controls, 104 SNPs coded as the number of risk alleles. `snp1`-`snp4` are risk SNPs (model H4M4), `snp5`-`snp100` are noise SNPs, and `snp101`-`snp104` are perfect LD proxies of the four risk SNPs (LD model r1). `data/README.md` says how it was made.

```python
path = rfld.example_path("h4m4_r1.csv")
X, y, names = rfld.read_genotypes(path)
print(X.shape[0], "people:", int(y.sum()), "cases,", int((1 - y).sum()), "controls;", X.shape[1], "SNPs")
print("first columns:", names[:5], "... last:", names[-4:])
print("r^2 of snp1 with its proxy snp101:", round(float(rfld.r2_matrix(X)[0, 100]), 3))
```

```text
500 people: 250 cases, 250 controls; 104 SNPs
first columns: ['snp1', 'snp2', 'snp3', 'snp4', 'snp5'] ... last: ['snp101', 'snp102', 'snp103', 'snp104']
r^2 of snp1 with its proxy snp101: 1.0
```

## 3. Run the method

The paper's settings: 5000 trees, 35 candidate SNPs per split, genotypes as categories. First the original forest (RF0), then the revised one (RF1, R = 0.5). Each run takes a few seconds; the seed makes it repeatable.

```python
rf0 = rfld.importance_table(X, y, names, ntree=5000, mtry=35, seed=1)
rf1 = rfld.importance_table(X, y, names, ntree=5000, mtry=35, seed=1, revised_tree=True, ld_threshold=0.5)

risk = {"snp1", "snp2", "snp3", "snp4", "snp101", "snp102", "snp103", "snp104"}


def top(rows, key, n=8):
    return sorted(rows, key=lambda r: -r[key])[:n]


print("RF0 ranked by IM0          RF1 ranked by IM1")
for a, b in zip(top(rf0, "im0"), top(rf1, "im1")):
    print(f"{a['snp']:>7}{'*' if a['snp'] in risk else ' '} {a['im0']:6.3f}         "
          f"{b['snp']:>7}{'*' if b['snp'] in risk else ' '} {b['im1']:6.3f}  ({b['trees']} trees)")
print("* risk SNP or its proxy")
```

```text
RF0 ranked by IM0          RF1 ranked by IM1
 snp102*  0.482            snp2*  0.857  (2324 trees)
   snp2*  0.382          snp102*  0.790  (2378 trees)
  snp65   0.177            snp1*  0.417  (2124 trees)
  snp38   0.174          snp101*  0.348  (2064 trees)
 snp101*  0.164          snp104*  0.289  (2245 trees)
  snp47   0.158            snp4*  0.246  (2194 trees)
 snp104*  0.150           snp65   0.215  (3771 trees)
   snp1*  0.148           snp76   0.202  (3176 trees)
* risk SNP or its proxy
```

In RF0 a risk SNP and its perfect proxy share the trees and stand in for each other when one is permuted, so both get a lower importance. In RF1 they never share a tree; IM1 averages over the trees that use each one.

## 4. Compare with the expected output

The expected importances come from Breiman and Cutler's Fortran program run on the same file (mean and SD over 5 seeds; RF1 with our patch of that program), not from this package. Forests are random, so a SNP agrees when it is within 4 SD of the difference between one run and a 5-seed mean.

```python
import csv
import math

expected = {r["snp"]: r for r in csv.DictReader(open(rfld.example_path("h4m4_r1_expected.csv")))}


def agree(rows, ours, col):
    n = 0
    for r in rows:
        e = expected[r["snp"]]
        tol = 4 * max(float(e[col + "_sd"]), 1e-3) * math.sqrt(1 + 1 / 5)
        n += abs(r[ours] - float(e[col])) <= tol
    return n


checks = [("RF0, IM0", agree(rf0, "im0", "rf0_im0")), ("RF0, IM1", agree(rf0, "im1", "rf0_im1")),
          ("RF1, IM0", agree(rf1, "im0", "rf1_im0")), ("RF1, IM1", agree(rf1, "im1", "rf1_im1"))]
for name, n in checks:
    print(f"{name}: {n} of {len(names)} SNPs agree with the Fortran program")
assert all(n >= 102 for _, n in checks)
```

```text
RF0, IM0: 104 of 104 SNPs agree with the Fortran program
RF0, IM1: 104 of 104 SNPs agree with the Fortran program
RF1, IM0: 103 of 104 SNPs agree with the Fortran program
RF1, IM1: 103 of 104 SNPs agree with the Fortran program
```

## 5. From the command line

`rfld` reads the same CSV and writes one row per SNP. Here RF1 with 1000 trees:

```python
!rfld "{path}" --revised-tree --ld-threshold 0.5 --ntree 1000 --seed 2 -o rf1_example.csv
print(open("rf1_example.csv").read().splitlines()[:5])
```

```text
['snp,im0,im1,trees,rank_im0,rank_im1', 'snp1,0.192407,0.465877,413,4,3', 'snp2,0.384058,0.806844,476,2,2', 'snp3,0.112557,0.266092,423,11,8', 'snp4,0.182976,0.440905,415,6,4']
```

## 6. Your own data

- **Input:** a CSV with a `status` column (1 case, 0 control; `--status` names another) and one column per SNP holding the number of risk alleles (0, 1, 2). Any small category codes 0..L-1 work (for example haplo-genotypes, 10 categories). No missing values.
- **Options:** `ntree` and `mtry` (paper: 5000 and 35); `revised_tree=True` for RF1 with `ld_threshold` R (pairwise genotypic r² above R keeps two SNPs out of one tree; the paper does not give its R); `seed`.
- **Output:** `im0` (100 × the mean decrease in out-of-bag accuracy over all trees, as Random Forests 5.1 prints it), `im1` (the same over the trees that split on the SNP), `trees` (that number) and the ranks by each. The paper recommends RF0 with IM1 when the genetic model and the LD are unknown.
- **Simulation:** `rfld.snp_dataset` and `rfld.haplotype_dataset` draw case-control data under the paper's heterogeneity-multiplicative models (`rfld.MODELS`, Table 1); `rfld.haplotype_em` and `rfld.sample_haplotype_pairs` phase two-SNP genotypes as the paper did with haplo.stats.

## 7. The reproduction

The paper's Figures 1-6 and Table 1 recomputed with this package, and how they compare: [PMC2666661 in the fossil repository](https://github.com/jeonglab-bcm/fossil/tree/main/PMC2666661) and its [results page](https://jeonglab-bcm.github.io/fossil/PMC2666661/).
