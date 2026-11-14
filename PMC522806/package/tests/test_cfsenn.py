"""Tests for the installed package. They use only the package and its bundled data.

check_package.py runs them from a copy outside the source tree, so they test the installed wheel.
"""

import csv
import subprocess
import sys

import numpy as np
import pytest

import cfsenn


def expected():
    with open(cfsenn.example_path("example_test_expected.csv"), newline="") as f:
        return [r["class"] for r in csv.DictReader(f)]


def example(**kw):
    train = cfsenn.read_table(cfsenn.example_path())
    test = cfsenn.read_table(cfsenn.example_path("example_test.csv"))
    return cfsenn.run(train, test, **kw)


def test_example_input_gives_expected_classes():
    res = example(n_bags=20)
    assert [p["predicted"] for p in res["predictions"]] == expected()
    assert res["accuracy"]["correct"] == 20


def test_command_line_matches_api(tmp_path):
    out = tmp_path / "pred.csv"
    subprocess.run(
        [sys.executable, "-m", "cfsenn", str(cfsenn.example_path()), str(cfsenn.example_path("example_test.csv")),
         "--bags", "20", "-o", str(out)],
        check=True,
    )
    with open(out, newline="") as f:
        rows = list(csv.DictReader(f))
    api = example(n_bags=20)["predictions"]
    assert [r["predicted"] for r in rows] == [p["predicted"] for p in api]
    assert [float(r["confidence"]) for r in rows] == pytest.approx([p["confidence"] for p in api], abs=1e-6)


def test_feature_counts_are_the_papers():
    X, y, _, _ = cfsenn.read_table(cfsenn.example_path())
    m = cfsenn.Ensemble(n_bags=1).fit(X, y)
    sizes = [fm(X).shape[1] for fm in m.members[0].maps]
    assert sizes == [30, 15, 30]  # 75 features in all, as the paper says


def test_masked_clustering_takes_one_gene_per_cluster():
    X, y, _, _ = cfsenn.read_table(cfsenn.example_path())
    genes = cfsenn.masked_cluster_genes(X, y, n_genes=30, n_clusters=50, n_prefilter=200)
    assert len(genes) == len(set(genes)) == 30


def test_three_classes():
    rng = np.random.default_rng(1)
    y = np.repeat([0, 1, 2], 8)
    X = rng.normal(size=(24, 60)) + np.eye(3)[y] @ np.hstack([np.eye(3) * 3, np.zeros((3, 57))])
    m = cfsenn.Ensemble(n_bags=5, n_rank=5, n_pc=3, n_cluster_genes=5, n_clusters=10, n_prefilter=30).fit(X, y)
    assert (m.predict(X) == y).mean() > 0.9
    assert m.predict_proba(X).shape == (24, 3)


def test_missing_values_are_filled():
    X, y, _, _ = cfsenn.read_table(cfsenn.example_path())
    X = X.copy()
    X[0, :5] = np.nan
    m = cfsenn.Ensemble(n_bags=2).fit(X, y)
    assert np.isfinite(m.predict_proba(X)).all()


def test_too_few_samples_raise():
    with pytest.raises(ValueError):
        cfsenn.Ensemble().fit(np.zeros((3, 10)), np.array([0, 1, 1]))


def test_unknown_setting_raises():
    with pytest.raises(TypeError):
        cfsenn.Ensemble(bags=3)
