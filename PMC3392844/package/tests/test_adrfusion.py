"""Tests for the installed package. They use only the package and its bundled data.

check_package.py runs them from a copy outside the source tree, so they test the installed wheel.
"""

import csv
import json
import subprocess
import sys

import adrfusion as A
import numpy as np
import pytest


def expected():
    data = A.read_dataset(A.example_path())
    E = np.zeros(data.Y.shape)
    with open(A.example_path("example_expected.csv"), newline="") as f:
        for r in csv.DictReader(f):
            E[data.drugs.index(r["drug"]), int(r["adr"][3:])] = float(r["decision"])
    return data, E


def test_example_input_gives_expected_output():
    data, E = expected()
    S = A.cross_validated_scores(data, "chem+bio+pheno", "svm", scores="decision")
    assert S.shape == (120, 30)
    assert np.abs(S - E).max() < 1e-3


def test_dimensions_and_feature_sets():
    data = A.read_dataset(A.example_path())
    assert data.dimensions() == {"chem": 40, "target": 20, "transporter": 5, "enzyme": 6, "pathway": 10,
                                 "indication": 25, "ade": 29}
    assert A.expand("chem+bio+pheno") == ("chem", "target", "transporter", "enzyme", "pathway", "indication", "ade")
    assert A.features_for(data, "pheno", 3).shape == (120, 25 + 29)
    # The kernel distance equals the squared Euclidean distance of the explicit features.
    X = A.features_for(data, "chem+bio+pheno", 5)
    D = A.core.distance_for(data, A.block_distances(data), "chem+bio+pheno", 5)
    assert np.array_equal(D, ((X[:, None, :] - X[None, :, :]) ** 2).sum(-1))


def test_micro_metrics_on_a_known_case():
    Y = np.array([[1, 0], [0, 1], [0, 0], [1, 0]])
    S = np.array([[0.9, 0.1], [0.2, 0.8], [0.3, 0.05], [0.4, 0.7]])
    m = A.micro_metrics(Y, S)
    # Ranking: 0.9+ 0.8+ 0.7- 0.4+ 0.3- 0.2- 0.1- 0.05-: 3 positives, 5 negatives.
    assert m.auc == pytest.approx((5 + 5 + 4) / 15)
    assert m.acc == pytest.approx(7 / 8)
    assert m.precision == pytest.approx(3 / 4) and m.recall == pytest.approx(1.0)


def test_every_algorithm_runs():
    data = A.read_dataset(A.example_path())
    for alg in A.ALGORITHMS:
        S = A.cross_validated_scores(data, "chem+bio", alg, adrs=[0, 1])
        assert S.shape == (120, 2) and np.isfinite(S).all()


def test_command_line_gives_the_api_result(tmp_path):
    out, met = tmp_path / "scores.csv", tmp_path / "m.json"
    subprocess.run([sys.executable, "-m", "adrfusion", str(A.example_path()), "--scores", "decision",
                    "-o", str(out), "--metrics", str(met)], check=True)
    data, E = expected()
    with open(out, newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 120 * 30
    got = {(r["drug"], r["adr"]): float(r["score"]) for r in rows}
    S = A.cross_validated_scores(data, "chem+bio+pheno", "svm", scores="decision")
    assert all(abs(got[(data.drugs[i], data.adrs[j])] - S[i, j]) < 1e-12 for i in range(120) for j in range(30))
    assert json.loads(met.read_text())["auc"] == pytest.approx(A.micro_metrics(data.Y, S).auc)


def test_invalid_input_raises(tmp_path):
    bad = tmp_path / "bad.txt"
    bad.write_text("D1|x||0102|0|0|0|0|0|0|0\n")
    with pytest.raises(ValueError):
        A.read_dataset(bad)
    data = A.read_dataset(A.example_path())
    with pytest.raises(ValueError):
        A.cross_validated_scores(data, "chem+nothing")
    data.folds = None
    with pytest.raises(ValueError):
        A.cross_validated_scores(data)
