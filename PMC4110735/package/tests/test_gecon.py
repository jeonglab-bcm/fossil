"""Tests of the installed gecon package on its bundled example data."""

import csv
import subprocess
import sys

import numpy as np
import pytest

import gecon


def read_tsv(name):
    with open(gecon.example_path(name), newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def test_figure7_worked_example():
    genes, _, X = gecon.read_matrix(gecon.example_path("fig7_profile.tsv"))
    r, a = gecon.edge_patterns(X[0])
    expected = read_tsv("fig7_expected.tsv")
    assert [f"{x:.0f}" for x in a] == [e["angle_printed"] for e in expected]
    assert [int(x) for x in r] == [int(e["regulation"]) for e in expected]


def test_figure2_pair_is_negative():
    genes, _, X = gecon.read_matrix(gecon.example_path("gds3702_mrps26_pfn2.tsv"))
    A, sup = gecon.gecon(X)
    exp = read_tsv("gds3702_expected.tsv")[0]
    i, j = genes.index(exp["gene1"]), genes.index(exp["gene2"])
    assert A[i, j] == int(exp["sign"]) == A[j, i]


def test_command_line_matches_api(tmp_path):
    path = gecon.example_path("gds3702_mrps26_pfn2.tsv")
    out = tmp_path / "edges.csv"
    subprocess.run([sys.executable, "-m", "gecon", str(path), "-o", str(out)], check=True)
    rows = gecon.read_edges(out)
    genes, _, X = gecon.read_matrix(path)
    A, sup = gecon.gecon(X)
    api = gecon.edge_list(A, sup, genes)
    assert [(r["gene1"], r["gene2"], r["sign"]) for r in rows] == [(r["gene1"], r["gene2"], r["sign"]) for r in api]


def test_segments_drop_the_joining_edge():
    X = np.array([[1.0, 2.0, 3.0, 1.0, 2.0, 3.0], [1.0, 2.0, 3.0, 1.0, 2.0, 3.0]])
    s = gecon.supports(X, segments=[3, 3])
    assert s.n_edges == 4 and s.pos[0, 1] == 1.0


def test_too_little_data():
    with pytest.raises(ValueError):
        gecon.supports(np.array([[1.0], [2.0]]))
    with pytest.raises(ValueError):
        gecon.supports(np.array([[1.0, np.nan], [2.0, 3.0]]))


def test_scores_on_a_known_ranking():
    y = np.array([1, 0, 1, 0])
    s = np.array([0.9, 0.8, 0.7, 0.1])
    assert gecon.auroc(y, s) == pytest.approx(0.75)
    assert gecon.fbeta(y, s > 0.75, beta=1.0) == pytest.approx(2 * 0.5 * 0.5 / 1.0)
