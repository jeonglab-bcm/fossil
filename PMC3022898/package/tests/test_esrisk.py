"""Tests for the installed package. They use only the package and its bundled data.

check_package.py runs them from a copy outside the source tree, so they test the installed wheel.
"""

import csv
import json
import math
import subprocess
import sys

import esrisk as E
import numpy as np
import pytest

COLS = ("esr_s", "esr_s_log_lower", "esr_s_log_upper", "esr_r", "esr_r_log_lower", "esr_r_log_upper",
        "esr_r_binomial_lower", "esr_r_binomial_upper")


def read_expected():
    with open(E.example_path("two_samples_expected.csv"), newline="") as f:
        return {r["label"]: {c: float(r[c]) for c in COLS} for r in csv.DictReader(f)}


def close(a, b):
    if math.isinf(a) or math.isinf(b):
        return a == b
    return math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-12)


def test_example_input_gives_expected_output():
    expected = read_expected()
    for r in E.read_counts(E.example_path()):
        e = E.estimate(r["d1"], r["n1"], r["d2_exposed"], r["n2_exposed"], r["d2_unexposed"], r["n2_unexposed"]).as_dict()
        ours = {"esr_s": e["esr_s"], "esr_s_log_lower": e["ci_s_log_lower"], "esr_s_log_upper": e["ci_s_log_upper"],
                "esr_r": e["esr_r"], "esr_r_log_lower": e["ci_r_log_lower"], "esr_r_log_upper": e["ci_r_log_upper"],
                "esr_r_binomial_lower": e["ci_r_binomial_lower"], "esr_r_binomial_upper": e["ci_r_binomial_upper"]}
        for c in COLS:
            assert close(float(ours[c]), expected[r["label"]][c]), (r["label"], c, float(ours[c]), expected[r["label"]][c])


def test_command_line_matches_api(tmp_path):
    out = tmp_path / "out.csv"
    subprocess.run([sys.executable, "-m", "esrisk", "estimate", str(E.example_path()), "-o", str(out), "--digits", "12"],
                   check=True)
    expected = read_expected()
    with open(out, newline="") as f:
        rows = list(csv.DictReader(f))
    assert [r["label"] for r in rows] == list(expected)
    for r in rows:
        for c in COLS:
            assert math.isclose(float(r[c]), expected[r["label"]][c], rel_tol=1e-9, abs_tol=1e-11) or \
                float(r[c]) == expected[r["label"]][c], (r["label"], c)


def test_revised_estimator_recovers_the_risk_in_the_exposed():
    # With the population values themselves the revised estimator is exact and the simple one is not.
    p_e, p0, rr = 0.2, 0.02, 5.0
    p_d = rr * p0 * p_e + p0 * (1 - p_e)
    assert math.isclose(float(E.esr_revised(p_d, rr, p_e)), rr * p0)
    assert float(E.esr_simple(p_d, rr)) > rr * p0 * 1.5


def test_zero_cell_rules():
    args = (31, 1000, 0, 48, 19, 933)
    assert E.estimate(*args).ci_s_log == (0.0, np.inf)
    assert all(np.isnan(x) for x in E.estimate(*args, zero_cells="missing").ci_r_log)
    with pytest.raises(ValueError):
        E.estimate(*args, zero_cells="drop")


def test_invalid_counts_raise():
    with pytest.raises(ValueError):
        E.estimate(10, 100, 5, 0, 3, 100)       # no exposed people
    with pytest.raises(ValueError):
        E.estimate(10, 100, 50, 40, 3, 100)     # more cases than people
    with pytest.raises(ValueError):
        E.esr_from_summaries(0.01, 1000, 2.0, (2.5, 3.0), 0.3)  # RR outside its CI


def test_summaries_match_counts():
    # The same data given as counts and as published summaries give the same estimates.
    d1, n1, a, ne, c, nu = 120, 5000, 30, 1000, 60, 4000
    rr = (a / ne) / (c / nu)
    v = (1 - a / ne) / a + (1 - c / nu) / c
    lo, hi = rr * math.exp(-E.core.Z95 * math.sqrt(v)), rr * math.exp(E.core.Z95 * math.sqrt(v))
    s = E.esr_from_summaries(d1 / n1, n1, rr, (lo, hi), ne / (ne + nu))
    e = E.estimate(d1, n1, a, ne, c, nu)
    assert math.isclose(s["esr_r"], float(e.esr_r))
    assert math.isclose(s["esr_r_log_upper"], float(e.ci_r_log[1]), rel_tol=1e-9)


def test_simulation_is_reproducible_and_shows_the_bias():
    a, *_ = E.simulate(0.2, 0.02, 5.0, 1000, 1000, reps=200, size=1_000_000, rng=7)
    b, *_ = E.simulate(0.2, 0.02, 5.0, 1000, 1000, reps=200, size=1_000_000, rng=7)
    assert np.array_equal(a.esr_s, b.esr_s)
    ev = E.evaluate(a, 0.10)
    assert ev["esr_s"]["relative_bias"] > 0.6          # the paper: 93.9% in this setting
    assert abs(ev["esr_r"]["relative_bias"]) < 0.1     # the paper: 0.3%


def test_simulate_command(tmp_path):
    out = tmp_path / "sim.json"
    subprocess.run([sys.executable, "-m", "esrisk", "simulate", "--p-exposed", "0.2", "--p-unexposed", "0.02",
                    "--rr", "5", "--n1", "1000", "--n2", "1000", "--reps", "100", "--population", "100000",
                    "-o", str(out)], check=True)
    d = json.loads(out.read_text())
    assert set(d) == {"esr_s", "esr_r", "ci_s_log", "ci_r_log", "ci_r_binomial"}
