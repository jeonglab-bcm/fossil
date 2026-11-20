"""Tests for the installed package, with its bundled data only.

check_package.py runs them from a copy outside the source tree, so they test the installed wheel.
"""

import csv
import math
import subprocess
import sys

import numpy as np
import pytest

import mlagq
from mlagq import simulation as sim

TOL = 1e-3  # the expected output maximizes a dense-grid integral, not the quadrature: see data/README.md
START = [-1.0, 0.3, 0.3, 0.3, 0.67, 0.0, 1.0]


def expected():
    with open(mlagq.example_path("clustered_binary_expected.csv")) as f:
        return {r["parameter"]: (float(r["estimate"]), float(r["se"])) for r in csv.DictReader(f)}


def example_fit():
    t = mlagq.read_long_csv(mlagq.example_path())
    return mlagq.fit_table(t, "y", "group", ["1", "z", "x", "x:z"], ["1", "x"], cov=True, start=START)


def test_example_input_gives_expected_output():
    f = example_fit()
    assert f.converged
    exp = expected()
    assert list(exp) == f.names
    for n, e, s in zip(f.names, f.estimate, f.se):
        assert abs(e - exp[n][0]) < TOL, (n, e, exp[n][0])
        assert abs(s - exp[n][1]) < TOL, (n, s, exp[n][1])


def test_command_line_matches_api(tmp_path):
    out = tmp_path / "out.csv"
    subprocess.run([sys.executable, "-m", "mlagq", str(mlagq.example_path()), "--cov", "--start", *map(str, START),
                    "-o", str(out)], check=True)
    rows = list(csv.DictReader(open(out)))
    f = example_fit()
    for r, n, e in zip(rows, f.names, f.estimate):
        assert r["parameter"] == n
        assert math.isclose(float(r["estimate"]), e, abs_tol=5e-7)


def test_likelihood_against_dense_integration():
    rng = np.random.default_rng(3)
    d = sim.generate(rng, 10, 8, var0=0.67)
    theta = np.array([-1, .3, .3, .3, .67, 0.1, 1.0])
    T = np.linspace(-7, 7, 241)
    B0, B1 = np.meshgrid(T, T, indexing="ij")
    phi = np.exp(-0.5 * (B0 ** 2 + B1 ** 2)) / (2 * np.pi) * (T[1] - T[0]) ** 2
    L = np.linalg.cholesky(np.array([[.67, .1], [.1, 1.0]]))
    tot = 0.0
    for j in range(10):
        lin = (d.X[j] @ theta[:4])[:, None, None] + L[0, 0] * B0 + (L[1, 0] * B0 + L[1, 1] * B1) * d.Z[j, :, 1][:, None, None]
        tot += np.log((np.exp((d.y[j][:, None, None] * lin - np.logaddexp(0, lin)).sum(0)) * phi).sum())
    assert math.isclose(mlagq.loglik(theta, d, cov=True, Q=21), tot, rel_tol=1e-6)


def test_boundary_maximum_does_not_converge_without_absxconv():
    # one random effect with no variance at all in the data: the maximum is at var = 0
    rng = np.random.default_rng(0)
    J, n = 30, 5
    x = rng.standard_normal((J, n))
    y = (rng.random((J, n)) < 1 / (1 + np.exp(-(-1 + 0.3 * x)))).astype(float)
    d = mlagq.group_data(y.ravel(), np.column_stack([np.ones(J * n), x.ravel()]), np.ones(J * n),
                         np.repeat(np.arange(J), n))
    f = mlagq.fit(d, [-1, 0.3, 0.5])
    if f.estimate[-1] < 1e-3:
        assert not f.converged
        g = mlagq.fit(d, [-1, 0.3, 0.5], absxconv=1e-8)
        assert g.status in ("absxconv", "gconv", "absgconv")


def test_invalid_outcome_raises():
    with pytest.raises(ValueError):
        mlagq.group_data([0, 2, 1], [[1], [1], [1]], [1, 1, 1], [1, 1, 2])


def test_qpoints_from_nlmixed_sequence():
    rng = np.random.default_rng(5)
    d = sim.generate(rng, 30, 30, var0=0.67)
    q = mlagq.select_qpoints([-1, .3, .3, .3, .67, 0, 1], d, cov=True)
    assert q in (1, 3, 5, 7, 9, 11, 21, 31)
