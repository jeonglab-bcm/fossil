"""Tests for the installed package, with its bundled data only."""

import csv
import subprocess
import sys

import numpy as np
import pytest

import geodenoise as gd

TOL = 0.005  # the authors' subspace iteration stops at a change of 1e-3 per vector


def expected():
    with open(gd.example_path("geometric_expected_distances.csv"), newline="") as f:
        return {(r["protein_a"], r["protein_b"]): float(r["distance"]) for r in csv.DictReader(f)}


def ours(net, D):
    idx = {v: i for i, v in enumerate(net.nodes)}
    return lambda a, b: D[idx[a], idx[b]]


def test_example_matches_the_authors_code():
    net = gd.read_network(gd.example_path())
    D = gd.pairwise_distances(gd.embed(net, 2))
    get = ours(net, D)
    exp = expected()
    assert len(exp) == net.n * (net.n - 1) // 2
    worst = max(abs(get(a, b) - d) for (a, b), d in exp.items())
    assert worst <= TOL, worst


def test_command_line_matches_the_api(tmp_path):
    out = tmp_path / "d.csv"
    subprocess.run([sys.executable, "-m", "geodenoise", "distances", str(gd.example_path()),
                    "--dim", "2", "-o", str(out)], check=True)
    net = gd.read_network(gd.example_path())
    get = ours(net, gd.pairwise_distances(gd.embed(net, 2)))
    with open(out, newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == net.n * (net.n - 1) // 2
    assert max(abs(float(r["distance"]) - get(r["protein_a"], r["protein_b"])) for r in rows) < 1e-5


def test_missing_edges_are_recovered():
    net = gd.read_network(gd.example_path())
    D = gd.pairwise_distances(gd.embed(net, 2))
    miss = gd.read_network(gd.example_path("geometric_missing.tsv"))
    idx = {v: i for i, v in enumerate(net.nodes)}
    iu, ju = np.triu_indices(net.n, 1)
    A = net.adjacency().toarray().astype(bool)
    non = ~A[iu, ju]
    code = {tuple(sorted((idx[miss.nodes[i]], idx[miss.nodes[j]]))) for i, j in miss.edges}
    pos = np.array([(a, b) in code for a, b in zip(iu[non], ju[non])])
    _, tp, fp, P, N = gd.roc_curve(D[iu[non], ju[non]], pos)
    assert gd.auc(tp, fp, P, N) > 0.8  # chance is 0.5; 0.87 on this example


def test_scores_are_between_zero_and_one():
    net = gd.read_network(gd.example_path())
    D = gd.pairwise_distances(gd.embed(net, 2))
    fe, fn = gd.learn_densities(net, D, size=net.m, rng=0)
    sc = gd.confidence_scores(net, D, fe, fn, delta=0.2)
    assert sc["score"].max() == pytest.approx(1.0)
    assert (sc["score"] >= 0).all() and (sc["distance"] <= 0.2).all()


def test_mixture_recovers_two_gaussians():
    rng = np.random.default_rng(1)
    x = np.r_[rng.normal(0.2, 0.05, 3000), rng.normal(0.7, 0.1, 3000)]
    rng.shuffle(x)
    m = gd.fit_mixture(x, 2, rng=2, stop=1e-6)
    assert sorted(np.round(m.means, 1)) == [0.2, 0.7]


def test_too_small_network_raises():
    net = gd.network_from_edges([("a", "b"), ("b", "c")])
    with pytest.raises(ValueError):
        gd.embed(net, 5)


def test_bad_prior_raises():
    net = gd.read_network(gd.example_path())
    D = gd.pairwise_distances(gd.embed(net, 2))
    fe, fn = gd.learn_densities(net, D, size=200, rng=0)
    with pytest.raises(ValueError):
        gd.confidence_scores(net, D, fe, fn, prior_edge=1.5)
