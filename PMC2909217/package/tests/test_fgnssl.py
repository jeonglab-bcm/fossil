"""Tests for the installed package, with its bundled data only.

check_package.py runs them from a copy outside the source tree. Do not add the source folder to sys.path.
"""

import itertools
import math
import subprocess
import sys

import fgnssl as f
import numpy as np
import pytest

REL = 1e-6


def example_net():
    genes, X = f.read_expression(f.example_path("expression.csv"))
    return f.build_fgn(genes, X, f.read_edges(f.example_path("interactions.csv")))


def test_clusters_match_expected():
    net = example_net()
    exp = np.array([int(r["cluster"]) for r in f.read_table(f.example_path("expected_clusters.csv"))])
    assert np.array_equal(net.clusters, exp)


def test_weights_match_eq2():
    net = example_net()
    exp = {(r["gene_a"], r["gene_b"]): float(r["weight"]) for r in f.read_table(f.example_path("expected_weights.csv"))}
    ours = {(net.genes[a], net.genes[b]): w for (a, b), w in zip(net.edges, net.weights)}
    assert ours.keys() == exp.keys()
    for k, v in exp.items():
        assert math.isclose(ours[k], v, rel_tol=REL), k


def test_node_properties_match_expected():
    props = f.node_properties(example_net())
    rows = f.read_table(f.example_path("expected_properties.csv"))
    for p in f.NODE_PROPERTIES:
        e = np.array([float(r[p]) for r in rows])
        assert np.allclose(props[p], e, rtol=REL, atol=1e-9), p


def test_features_and_scores_match_expected():
    net = example_net()
    pairs, labels = f.read_pairs(f.example_path("pairs.csv"))
    F = f.pair_features(net, pairs)
    ef = np.array([[float(r[k]) for k in f.FEATURE_NAMES] for r in f.read_table(f.example_path("expected_features.csv"))])
    assert np.allclose(F, ef, rtol=REL, atol=1e-9)
    s = f.predict(F, labels)
    es = np.array([float(r["sgi_score"]) for r in f.read_table(f.example_path("expected_scores.csv"))])
    assert np.allclose(s, es, atol=1e-6)


def test_command_line_matches_api(tmp_path):
    out = tmp_path / "out.csv"
    subprocess.run([sys.executable, "-m", "fgnssl", str(f.example_path("expression.csv")),
                    str(f.example_path("interactions.csv")), str(f.example_path("pairs.csv")), "-o", str(out)],
                   check=True)
    rows = f.read_table(out)
    es = [float(r["sgi_score"]) for r in f.read_table(f.example_path("expected_scores.csv"))]
    assert len(rows) == len(es)
    for r, e in zip(rows, es):
        assert math.isclose(float(r["sgi_score"]), e, abs_tol=1e-6)


def test_stress_counts_shortest_paths_on_a_small_graph():
    # a 4-cycle 0-1-2-3-0 plus a pendant 4 on 0: count shortest paths through each node by hand
    from fgnssl import network as N
    g = N.make_graph(5, np.array([(0, 1), (1, 2), (2, 3), (3, 0), (0, 4)]))
    # (0,2) via 1 or 3; (1,3) via 0 or 2; (1,4) via 0; (2,4) via 1-0 or 3-0; (3,4) via 0
    # node 0: (1,3), (1,4), (2,4) twice, (3,4) -> 5; node 1: (0,2), (2,4) -> 2; node 2: (1,3) -> 1; node 3: 2
    assert np.allclose(N.stress_centrality(g), [5, 2, 1, 2, 0])


def test_label_spreading_needs_both_classes():
    X = np.random.default_rng(0).normal(size=(6, 2))
    with pytest.raises(ValueError):
        f.label_spreading(X, np.array([1, 1, -1, -1, -1, -1]))


def test_dcca_clusters_are_positively_correlated():
    genes, X = f.read_expression(f.example_path("expression.csv"))
    lab = f.dcca(X)
    R = np.corrcoef(X)
    for i, j in itertools.combinations(range(len(lab)), 2):
        if lab[i] == lab[j]:
            assert R[i, j] >= 0


def test_unknown_gene_in_pairs_raises():
    with pytest.raises(KeyError):
        f.pair_features(example_net(), [("G00", "NOT_A_GENE")])
