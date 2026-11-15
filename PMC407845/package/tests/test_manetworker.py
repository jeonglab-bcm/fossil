"""Tests of the installed package, with its bundled example data only."""

import json
import subprocess
import sys

import numpy as np
import pytest

import manetworker as mn


def load():
    genes, arrays, E = mn.read_matrix(mn.example_path("expression.tsv"))
    _, tfs, R = mn.read_matrix(mn.example_path("binding_ratio.tsv"))
    _, _, P = mn.read_matrix(mn.example_path("binding_p.tsv"))
    expected = json.loads(mn.example_path("expected.json").read_text())
    return genes, arrays, E, tfs, R, P, expected


def test_example_recovers_planted_network():
    genes, arrays, E, tfs, R, P, ex = load()
    res = mn.run(E, mn.log_ratio(R), P, tfs)
    assert res["tfs"] == ex["active_tfs"]
    found = planted = wrong = 0
    for j, tf in enumerate(res["tfs"]):
        cc = {genes[i] for i in np.nonzero(res["classes"][:, j] == 1)[0]}
        found += len(cc & set(ex["functional_targets"][tf]))
        planted += len(ex["functional_targets"][tf])
        wrong += len(cc & set(ex["nonfunctional_bound"][tf]))
        assert np.corrcoef(res["activity_t"][j], ex["true_activity"][tf])[0, 1] > 0.95
    assert found >= 72 and planted == 75   # tolerance stated in data/README.md
    assert wrong == 0


def test_regression_matches_least_squares():
    genes, arrays, E, tfs, R, P, ex = load()
    B = mn.fill_binding(mn.log_ratio(R))
    fit = mn.regress_activities(E, B)
    j = 0
    ok = ~np.isnan(E[:, j])
    X = np.column_stack([np.ones(ok.sum()), B[ok]])
    beta = np.linalg.lstsq(X, E[ok, j], rcond=None)[0]
    assert np.allclose(fit["coef"][:, j], beta[1:], rtol=1e-8, atol=1e-10)


def test_coupling_matches_pearson():
    genes, arrays, E, tfs, R, P, ex = load()
    F = np.array([ex["true_activity"]["TF1"]])
    c = mn.coupling(E, F)
    g = 0
    ok = ~np.isnan(E[g])
    assert np.isclose(c["r"][g, 0], np.corrcoef(E[g, ok], F[0, ok])[0, 1])


def test_bh_reject():
    p = np.array([0.001, 0.008, 0.039, 0.041, 0.042, 0.06, 0.074, 0.205, 0.212, 0.216])
    assert mn.bh_reject(p, 0.05).tolist() == [True, True] + [False] * 8


def test_command_line_matches_api(tmp_path):
    subprocess.run([sys.executable, "-m", "manetworker", "--example", "-o", str(tmp_path)], check=True)
    sel = json.loads((tmp_path / "selection.json").read_text())
    genes, arrays, E, tfs, R, P, ex = load()
    assert sel["selected"] == mn.run(E, mn.log_ratio(R), P, tfs)["tfs"]
    assert (tmp_path / "classes.tsv").read_text().count("B+/C+") >= 72


def test_too_few_genes_raises():
    E = np.random.default_rng(0).normal(size=(5, 3))
    B = np.random.default_rng(1).normal(size=(5, 6))
    with pytest.raises(ValueError):
        mn.regress_activities(E, B)
