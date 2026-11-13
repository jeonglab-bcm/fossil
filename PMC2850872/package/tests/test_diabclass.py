"""Tests for the installed package. They use only the package and its bundled data.

check_package.py runs them from a copy outside the source tree, so they test the installed wheel.
"""

import json
import subprocess
import sys

import numpy as np
import pytest

import diabclass as dc


def example():
    rows = dc.read_records(dc.example_path())
    train = [r for r in rows if r["set"] == "train"]
    test = [r for r in rows if r["set"] == "test"]
    return train, test


def expected():
    with open(dc.example_path("nhanes_example_expected.json"), encoding="utf-8") as f:
        e = json.load(f)
    svm = dc.read_records(dc.example_path("nhanes_example_expected_svm.csv"))
    return e, np.array([float(r["decision_value"]) for r in svm])


def test_svm_matches_libsvm_in_r():
    train, test = example()
    e, dv = expected()
    m = dc.SVMClassifier("rbf", e["svm"]["C"], e["svm"]["gamma"], tol=1e-5)
    m.fit(dc.encode(train), dc.labels(train))
    assert len(m.train_index_) == len(train)  # already balanced: every row is kept
    assert np.allclose(m.decision_function(dc.encode(test)), dv, atol=1e-4, rtol=0)


def test_logistic_and_delong_match_r():
    train, test = example()
    e, dv = expected()
    w = [float(r["weight_mec6"]) for r in train]
    beta = dc.weighted_logistic(dc.encode(train), dc.labels(train), w)
    assert np.allclose(beta, e["beta"], atol=1e-8, rtol=0)
    y = dc.labels(test)
    p = dc.logistic_probability(dc.encode(test), beta)
    assert dc.auc(y, dv) == pytest.approx(e["auc_svm"], abs=1e-12)
    assert dc.auc(y, p) == pytest.approx(e["auc_logistic"], abs=1e-12)
    assert dc.delong_test(y, dv, p)["p"] == pytest.approx(e["delong_p"], abs=1e-9)


def test_command_line_matches_api(tmp_path):
    out = tmp_path / "out.csv"
    subprocess.run([sys.executable, "-m", "diabclass", str(dc.example_path()), "--C", "2",
                    "--gamma", "2", "-o", str(out)], check=True)
    cli = np.array([float(r["decision_value"]) for r in dc.read_records(out)])
    train, test = example()
    m = dc.SVMClassifier("rbf", 2, 2).fit(dc.encode(train), dc.labels(train))
    assert np.allclose(cli, m.decision_function(dc.encode(test)), atol=1e-8)


def test_grid_search_returns_a_grid_point():
    train, _ = example()
    g = dc.grid_search(dc.encode(train), dc.labels(train), "rbf", log2c=[-1, 1], log2g=[1, -1])
    assert np.log2(g.C) in (-1, 1) and np.log2(g.gamma) in (1, -1)
    assert len(g.table) == 4 and 0.5 < g.cv_accuracy <= 1


def test_metrics_at_cutoff_zero():
    m = dc.classification_metrics([1, 1, -1, -1], [0.5, -0.2, -0.4, 0.3])
    assert (m["sensitivity"], m["specificity"], m["ppv"], m["npv"]) == (0.5, 0.5, 0.5, 0.5)


def test_invalid_input_raises():
    with pytest.raises(ValueError, match="race"):
        dc.encode([{"family_history": 1, "age": 50, "race": "martian", "weight": 80,
                    "height": 170, "waist": 90, "bmi": 27, "hypertension": 0}])
    with pytest.raises(ValueError, match="missing"):
        dc.encode([{"age": 50}])
    with pytest.raises(ValueError, match="cases"):
        dc.undersample([1, 1, -1])
