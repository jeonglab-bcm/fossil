"""Tests for the installed package, with its bundled data only (check_package.py runs them from a copy
outside the source tree)."""

import json
import math
import subprocess
import sys

import numpy as np
import pytest

import rommeta

Z_METAFOR = 1.959963984540054
FIELDS = ("k", "estimate", "ci_low", "ci_high", "p", "log_estimate", "se", "q", "tau2", "i2")


def assert_same(ours, expected):
    assert [r["measure"] for r in ours] == [r["measure"] for r in expected]
    for o, e in zip(ours, expected):
        for k in FIELDS:
            if e[k] is None:
                assert o[k] is None, (o["measure"], k)
            else:
                assert math.isclose(o[k], e[k], rel_tol=1e-9, abs_tol=1e-12), (o["measure"], k, o[k], e[k])


def test_example_input_gives_metafor_output():
    ours = rommeta.analyze(rommeta.read_studies(rommeta.example_path()), z=Z_METAFOR)
    assert_same([r.as_dict() for r in ours], rommeta.read_results(rommeta.example_path("trials_expected.csv")))


def test_command_line_matches_expected_output(tmp_path):
    out = tmp_path / "out.csv"
    subprocess.run([sys.executable, "-m", "rommeta", "meta", str(rommeta.example_path()), "-o", str(out),
                    "--z", repr(Z_METAFOR)], check=True)
    assert_same(rommeta.read_results(out), rommeta.read_results(rommeta.example_path("trials_expected.csv")))


def test_rom_by_hand():
    # Two studies: ln RoM and its delta-method variance as printed in the Methods.
    y, v = rommeta.effect_sizes([120, 90], [40, 30], [10, 20], [100, 100], [40, 30], [10, 20], "RoM")
    assert np.allclose(y, np.log([1.2, 0.9]))
    assert np.allclose(v, [40**2 / (10 * 120**2) + 40**2 / (10 * 100**2), 30**2 / (20 * 90**2) + 30**2 / (20 * 100**2)])


def test_pool_vectorized_equals_one_by_one():
    rng = np.random.default_rng(1)
    y, v = rng.normal(0, 1, (50, 6)), rng.uniform(0.1, 1, (50, 6))
    many = rommeta.pool(y, v)
    for i in (0, 17, 49):
        one = rommeta.pool(y[i], v[i])
        for k in ("estimate", "se", "q", "tau2", "i2"):
            assert math.isclose(float(many[k][i]), float(one[k]), rel_tol=1e-12)


def test_non_positive_mean_leaves_the_study_out():
    r = rommeta.meta_analysis([120, 110, 130], [40, 40, 40], [10, 10, 10], [100, -5, 100], [40, 40, 40], [10, 10, 10])
    assert r.k == 2
    assert rommeta.meta_analysis([120, 110, 130], [40, 40, 40], [10, 10, 10], [100, -5, 100], [40, 40, 40], [10, 10, 10], "MD").k == 3


def test_one_study_raises():
    with pytest.raises(ValueError, match="at least two"):
        rommeta.meta_analysis([120], [40], [10], [100], [40], [10])


def test_unknown_measure_raises():
    with pytest.raises(ValueError, match="measure"):
        rommeta.effect_sizes(1, 1, 2, 1, 1, 2, "OR")


def test_missing_column_raises(tmp_path):
    p = tmp_path / "bad.csv"
    p.write_text("mean_exp,sd_exp,n_exp\n1,1,2\n")
    with pytest.raises(ValueError, match="mean_contr"):
        rommeta.read_studies(p)


def test_skewed_mixture_moments():
    mean, sd, skew = rommeta.mixture_moments()
    assert round(mean, 2) == 1.0 and round(sd, 2) == 0.40 and round(skew, 2) == 0.88


def test_summary_draws_equal_individual_values_in_distribution():
    sc = rommeta.Scenario(sd=40, effect=0.5, n_exp=10, n_contr=10, k=5)
    a = rommeta.run_scenario(sc, 4000, seed=1)
    b = rommeta.run_scenario(sc, 4000, seed=2, draw="values")
    for m in ("MD", "SMD", "RoM"):
        se = math.hypot(a[m]["coverage_se"], b[m]["coverage_se"])
        assert abs(a[m]["coverage"] - b[m]["coverage"]) < 4 * se


def test_simulate_command_line():
    out = subprocess.run([sys.executable, "-m", "rommeta", "simulate", "--sd", "70", "--effect", "0.8", "--n-exp", "10",
                          "--n-contr", "10", "--k", "30", "--reps", "500", "--seed", "1"], check=True, capture_output=True, text=True)
    d = json.loads(out.stdout)
    assert d["true"]["RoM"] == pytest.approx(1.56)
    assert set(d["performance"]) == {"MD", "SMD", "RoM"}
