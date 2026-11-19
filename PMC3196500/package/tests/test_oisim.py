"""Tests for the installed package. They use only the package and its bundled data."""

import csv
import math
import subprocess
import sys

import numpy as np
import pytest

import oisim


def read(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_cumulative_matches_independent_implementation():
    ours = oisim.cumulative(oisim.read_trials(oisim.example_path("cumulative_trials.csv")))
    exp = read(oisim.example_path("cumulative_expected.csv"))
    assert len(ours) == len(exp) == 12
    for o, e in zip(ours, exp):
        assert o["trial"] == e["trial"]
        assert o["cum_patients"] == int(e["cum_patients"]) and o["cum_events"] == int(e["cum_events"])
        for k in ("rr", "rrr", "tau2"):
            assert math.isclose(o[k], float(e[k]), rel_tol=1e-8, abs_tol=1e-12), (o["trial"], k)


def test_command_line_matches_api(tmp_path):
    out = tmp_path / "out.csv"
    subprocess.run([sys.executable, "-m", "oisim", "cumulative", str(oisim.example_path()), "-o", str(out)], check=True)
    exp = read(oisim.example_path("cumulative_expected.csv"))
    got = read(out)
    assert [r["trial"] for r in got] == [r["trial"] for r in exp]
    for g, e in zip(got, exp):
        assert math.isclose(float(g["rrr"]), float(e["rrr"]), rel_tol=1e-8)


def test_ois_within_one_rounding_step_of_table2():
    for r in read(oisim.example_path("table2_printed.csv")):
        o = oisim.ois(float(r["pc"]), float(r["rrr"]), float(r["i2"]), beta=float(r["beta"]))
        step = 500 if o["patients"] > 10000 else 100
        assert abs(o["patients"] - int(r["patients_printed"])) <= step
        assert abs(o["events"] - int(r["events_printed"])) <= 50


def test_simulation_is_reproducible_and_shaped():
    sc = oisim.Scenario("common", "15-40", 0.05, 0.0, n_meta=50, n_trials=20)
    a = oisim.simulate(sc, seed=1)
    b = oisim.simulate(sc, seed=1)
    assert a.log_rr.shape == (50, 20)
    assert np.array_equal(np.nan_to_num(a.log_rr), np.nan_to_num(b.log_rr))
    assert np.all(np.diff(a.cum_patients, axis=1) > 0)


def test_required_number_rules():
    x = np.array([100, 200, 300, 400])
    p = np.array([0.2, 0.04, 0.06, 0.03])
    assert oisim.required_number(x, p, 0.05, rule="first") == 200
    assert oisim.required_number(x, p, 0.05, rule="stays") == 400
    assert oisim.required_number(x, p, 0.01) is None


def test_bad_input_raises():
    with pytest.raises(ValueError):
        oisim.ois(1.5, 0.2)
    with pytest.raises(ValueError):
        oisim.log_rr_and_variance([1], [10], [1], [10], zero="nope")
