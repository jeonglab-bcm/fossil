"""Tests for the installed package, with its bundled data only (check_package.py runs them outside the source tree)."""

import csv
import math
import subprocess
import sys

import numpy as np
import pytest

import robustrr as rr

TOL = 1e-6


def read(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def assert_close(ours, expected):
    assert [(r["model"], r["term"]) for r in ours] == [(r["model"], r["term"]) for r in expected]
    for o, e in zip(ours, expected):
        for k in ("log_rr", "se", "rr", "ci_low", "ci_high"):
            assert math.isclose(float(o[k]), float(e[k]), rel_tol=TOL), (o["model"], o["term"], k, o[k], e[k])
        if e["model"] == "log_binomial":
            assert o["method"] == e["method"]


def test_example_gives_expected_output():
    rows = rr.fit_relative_risk(rr.read_table(rr.example_path("cohort.csv")), "y", ["x", "z", "z^2"])
    assert_close([{k: str(v) for k, v in r.items()} for r in rows], read(rr.example_path("cohort_expected.csv")))


def test_command_line_matches_expected_output(tmp_path):
    out = tmp_path / "fit.csv"
    subprocess.run([sys.executable, "-m", "robustrr", "fit", str(rr.example_path("cohort.csv")), "--outcome", "y",
                    "--covariates", "x", "z", "z^2", "-o", str(out)], check=True)
    assert_close(read(out), read(rr.example_path("cohort_expected.csv")))


def test_interior_maximum_is_not_copied():
    rng = np.random.default_rng(1)
    s = rr.scenario(1.5, 25, "linear", "moderate")
    z, x, y, _ = rr.generate(s, 1500, 1, rng)
    X = np.column_stack([np.ones(1500), x[0], z[0]])
    fit = rr.log_binomial(X, y[0])
    assert fit["method"] == "mle" and fit["converged"]
    # the COPY fit of the same data is the same maximum to O(1/C)
    b, info = rr.log_binomial_coef(X[None], y, copies=1e6)
    assert np.allclose(b[0], fit["coef"])


def test_population_cutoffs_give_the_rate():
    s = rr.scenario(2.0, 40, "nonlinear", "strong")
    lo, hi = rr.population_cutoffs(s, 0.05)
    assert math.isclose(rr.simulation.population_cdf(s, lo)[0], 0.025, abs_tol=1e-9)
    assert math.isclose(rr.simulation.population_cdf(s, hi)[0], 0.975, abs_tol=1e-9)


def test_small_simulation_is_reproducible():
    s = rr.scenario(1.5, 10, "nonlinear", "moderate")
    a = rr.run_scenario(s, n=300, reps=20, seed=3, rates=(0.05,))
    b = rr.run_scenario(s, n=300, reps=20, seed=3, rates=(0.05,))
    assert np.array_equal(a[0.05]["lb"], b[0.05]["lb"])
    assert rr.summarize(a[0.05]["rp"], s["beta1"])["reps"] == 20


def test_bad_outcome_raises():
    with pytest.raises(ValueError, match="0 or 1"):
        rr.log_binomial(np.ones((3, 1)), [0, 2, 1])


def test_missing_column_raises(tmp_path):
    p = tmp_path / "bad.csv"
    p.write_text("y,x\n1,0\n0,1\n")
    with pytest.raises(ValueError, match="z"):
        rr.fit_relative_risk(rr.read_table(p), "y", ["x", "z"])


def test_unknown_scenario_raises():
    with pytest.raises(ValueError):
        rr.scenario(3.0, 10, "linear", "moderate")
