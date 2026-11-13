"""Make the bundled example data and their expected outputs, independently of fgnssl.

    python scripts/make_example_data.py src/fgnssl/data

Needs numpy, scipy, networkx and scikit-learn (not fgnssl). The inputs are synthetic:
  expression.csv     40 genes x 12 conditions: four planted groups, each a noisy copy of one of four
                     profiles whose pairwise correlation is -1/3
  interactions.csv   a connected random graph on the 40 genes (seed 5)
  pairs.csv          60 gene pairs, label 1 for pairs inside one group, 0 across groups; 30 labels hidden
The expected outputs come from the definitions, computed here with other code:
  expected_clusters.csv    divisive correlation clustering written out from the paper's description
                           (plain loops over gene pairs, not fgnssl's code)
  expected_weights.csv     eq. 2 from those clusters' centroids, L1 = 0.3
  expected_properties.csv  networkx (betweenness and closeness on 1 / w, eigenvector centrality,
                           current-flow betweenness, information centrality x n), Barrat clustering
                           and strength by their formulas, stress by enumerating all shortest paths
  expected_features.csv    the 18 pair features from those properties
  expected_scores.csv      scikit-learn LabelSpreading (rbf, gamma = 1 / (2 sigma^2), alpha = 0.99) on
                           the scaled features, sigma the median distance
"""

import csv
import itertools
import sys
from pathlib import Path

import networkx as nx
import numpy as np
from scipy.spatial.distance import pdist
from sklearn.semi_supervised import LabelSpreading

N_GROUP, GROUPS, COND = 10, 4, 12


def write(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        for r in rows:
            w.writerow([f"{v:.10g}" if isinstance(v, float) else v for v in r])


def dcca_loops(X):
    """The paper's divisive correlation clustering, step by step: split the cluster holding the most
    negative Pearson correlation between genes x_i and x_j (i < j, first such pair in row order);
    a gene joins x_i when it correlates more with x_i than with x_j. Stop when no cluster holds a
    negative correlation. Clusters are numbered by their smallest gene index."""
    n = len(X)
    R = np.corrcoef(X)
    clusters = [list(range(n))]
    while True:
        best = None
        for ci, members in enumerate(clusters):
            for a in range(len(members)):
                for b in range(a + 1, len(members)):
                    i, j = members[a], members[b]
                    if R[i, j] < 0 and (best is None or R[i, j] < best[0]):
                        best = (R[i, j], ci, i, j)
        if best is None:
            break
        _, ci, i, j = best
        members = clusters.pop(ci)
        left = [g for g in members if g == i or (g != j and R[g, i] > R[g, j])]
        right = [g for g in members if g not in left]
        clusters += [left, right]
    labels = np.zeros(n, dtype=int)
    for k, members in enumerate(sorted(clusters, key=min)):
        labels[members] = k
    return labels


def main(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(2010)
    # four profiles with pairwise correlation -1/3: centred simplex vertices in a random 12-d basis
    V = np.eye(GROUPS) - 1.0 / GROUPS
    Q, _ = np.linalg.qr(rng.normal(size=(COND, COND)))
    base = 2.0 * V @ Q[:GROUPS]
    genes, rows, group = [], [], []
    for g in range(GROUPS):
        for k in range(N_GROUP):
            genes.append(f"G{g}{k}")
            rows.append(base[g] + rng.normal(scale=0.25, size=COND))
            group.append(g)
    X = np.array(rows)
    group = np.array(group)
    write(out / "expression.csv", ["gene"] + [f"c{j + 1}" for j in range(COND)],
          [[genes[i]] + [float(v) for v in X[i]] for i in range(len(genes))])
    group = dcca_loops(X)
    write(out / "expected_clusters.csv", ["gene", "cluster"], [[genes[i], int(group[i])] for i in range(len(genes))])

    # eq. 2 with those clusters
    C = np.array([X[group == g].mean(0) for g in range(group.max() + 1)])
    own = ((X - C[group]) ** 2).sum(1)
    G = nx.connected_watts_strogatz_graph(len(genes), 4, 0.3, seed=5)
    G.add_edges_from([(0, 15), (12, 33), (21, 38), (5, 27)])
    edges = sorted(tuple(sorted(e)) for e in G.edges())
    write(out / "interactions.csv", ["gene_a", "gene_b"], [[genes[a], genes[b]] for a, b in edges])
    w = {}
    for a, b in edges:
        w[(a, b)] = 0.3 * (own[a] + own[b]) + 0.7 * float(((C[group[a]] - C[group[b]]) ** 2).sum())
    write(out / "expected_weights.csv", ["gene_a", "gene_b", "weight"], [[genes[a], genes[b], w[(a, b)]] for a, b in edges])
    for (a, b), v in w.items():
        G[a][b]["weight"] = v
        G[a][b]["dist"] = 1.0 / v

    n = len(genes)
    strength = np.array([sum(G[u][v]["weight"] for v in G[u]) for u in range(n)])
    barrat = np.zeros(n)
    for i in range(n):
        k = G.degree(i)
        if k < 2:
            continue
        tot = 0.0
        for j, h in itertools.combinations(list(G[i]), 2):
            if G.has_edge(j, h):
                tot += (G[i][j]["weight"] + G[i][h]["weight"]) / 2.0
        barrat[i] = 2.0 * tot / (strength[i] * (k - 1))   # sum over ordered pairs / (s (k - 1))
    btw = nx.betweenness_centrality(G, weight="dist", normalized=False)
    clo = nx.closeness_centrality(G, distance="dist")
    eig = nx.eigenvector_centrality_numpy(G, weight="weight")
    m = max(eig.values())
    stress = np.zeros(n)
    for s, t in itertools.combinations(range(n), 2):
        for p in nx.all_shortest_paths(G, s, t):
            for v in p[1:-1]:
                stress[v] += 1
    info = nx.information_centrality(G)
    flow = nx.current_flow_betweenness_centrality(G, normalized=True)
    props = {
        "degree": strength, "clustering": barrat, "betweenness": np.array([btw[i] for i in range(n)]),
        "closeness": np.array([clo[i] for i in range(n)]), "eigenvector": np.array([eig[i] / m for i in range(n)]),
        "stress": stress, "information": np.array([info[i] * n for i in range(n)]),
        "flow": np.array([flow[i] for i in range(n)]),
    }
    names = list(props)
    write(out / "expected_properties.csv", ["gene"] + names, [[genes[i]] + [float(props[p][i]) for p in names] for i in range(n)])

    # pairs: 30 inside a group (label 1), 30 across groups (label 0); every second label hidden
    pr = np.random.default_rng(7)
    inside, across = [], []
    while len(inside) < 30 or len(across) < 30:
        a, b = sorted(pr.choice(n, 2, replace=False).tolist())
        if (a, b) in inside or (a, b) in across:
            continue
        (inside if group[a] == group[b] else across).append((a, b)) if (
            (group[a] == group[b] and len(inside) < 30) or (group[a] != group[b] and len(across) < 30)) else None
    pairs = inside + across
    labels = [1] * 30 + [0] * 30
    shown = [lab if k % 2 == 0 else -1 for k, lab in enumerate(labels)]
    write(out / "pairs.csv", ["gene_a", "gene_b", "label", "true_label"],
          [[genes[a], genes[b], "" if s < 0 else s, t] for (a, b), s, t in zip(pairs, shown, labels)])

    feats = []
    for a, b in pairs:
        row = [(props[p][a] + props[p][b]) / 2.0 for p in names] + [abs(props[p][a] - props[p][b]) for p in names]
        row.append(nx.dijkstra_path_length(G, a, b, weight="dist"))
        row.append(float(len(set(G[a]) & set(G[b]))))
        feats.append(row)
    F = np.array(feats)
    fnames = [f"avg_{p}" for p in names] + [f"diff_{p}" for p in names] + ["shortest_path", "mutual_neighbors"]
    write(out / "expected_features.csv", ["gene_a", "gene_b"] + fnames,
          [[genes[a], genes[b]] + [float(v) for v in F[k]] for k, (a, b) in enumerate(pairs)])

    Gs = np.sign(F) * np.log1p(np.abs(F))
    sd = Gs.std(0)
    sd[sd == 0] = 1.0
    Z = (Gs - Gs.mean(0)) / sd
    sigma = float(np.median(pdist(Z)))
    ls = LabelSpreading(kernel="rbf", gamma=1.0 / (2 * sigma ** 2), alpha=0.99, max_iter=1000000, tol=1e-15)
    ls.fit(Z, np.array(shown))
    score = ls.label_distributions_[:, 1]
    write(out / "expected_scores.csv", ["gene_a", "gene_b", "sgi_score"],
          [[genes[a], genes[b], float(score[k])] for k, (a, b) in enumerate(pairs)])
    print(f"{n} genes, {len(edges)} interactions, {len(pairs)} pairs, sigma {sigma:.4f}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "src/fgnssl/data")
