"""Tests for the installed package, with its bundled data only (check_package.py runs them from a copy)."""

import csv
import math
import subprocess
import sys

import numpy as np
import pytest

import stratpower as sp

WEIGHTS = {f"rf{i}": 1.0 for i in range(1, 7)}


def expected():
    with open(sp.example_path("trial_expected.csv"), newline="") as f:
        return {(r["subgroup"], r["term"]): r for r in csv.DictReader(f)}


def close(a, b, rel=1e-6):
    return math.isclose(float(a), float(b), rel_tol=rel, abs_tol=1e-15)


def check(result, label):
    e = expected()
    for term in ("intercept", "z", "arm", "z_x_arm"):
        assert close(result["coef"][term], e[(label, term)]["coef"]), (label, term)
        assert close(result["se"][term], e[(label, term)]["se"]), (label, term)
    assert close(result["p_interaction"], e[(label, "p_interaction")]["coef"])


def test_example_trial_gives_expected_output():
    d = sp.read_trial(sp.example_path())
    check(sp.interaction_test(d["rf1"], d["arm"], d["outcome"]), "rf1")
    check(sp.interaction_test(sp.risk_score(d, WEIGHTS), d["arm"], d["outcome"]), "score")


def test_command_line_matches_expected_output(tmp_path):
    out = tmp_path / "out.csv"
    subprocess.run([sys.executable, "-m", "stratpower", "test", str(sp.example_path()),
                    "--weights", ",".join(f"{k}=1" for k in WEIGHTS), "-o", str(out)], check=True)
    with open(out, newline="") as f:
        rows = {r["term"]: r for r in csv.DictReader(f)}
    e = expected()
    for term in ("intercept", "z", "arm", "z_x_arm", "p_interaction"):
        assert close(rows[term]["coef"], e[("score", term)]["coef"]), term


def test_table1_shares_and_fig1a_formula():
    # Table 1's shares follow from six independent RFs of prevalence 25% (binomial), and Fig. 1A's
    # formula puts net RRR at 0 at a CER of 3%.
    pop = sp.population(6, 0.25, 2.0, 0.0075, "or")
    k = pop.count()
    shares = [pop.share[k == j].sum() for j in range(4)]
    assert np.allclose(shares, [math.comb(6, j) * 0.25 ** j * 0.75 ** (6 - j) for j in range(4)])
    assert abs(sp.net_rrr(0.03)) < 1e-12
    assert math.isclose(float(sp.net_rrr(0.0075)), -1.5)


def test_simulated_power_is_reproducible_and_ordered():
    pop = sp.population(6, 0.25, 2.0, 0.0075, "or")
    k = pop.count()
    subs = {"conventional": pop.patterns[:, 0], "continuous": k}
    a = sp.simulate_power(pop, subs, iterations=400, seed=3)
    b = sp.simulate_power(pop, subs, iterations=400, seed=3)
    assert a == b
    assert a["continuous"]["power"] > a["conventional"]["power"]


def test_bad_input_raises():
    with pytest.raises(ValueError):
        sp.population(6, 0.25, 3.0, 0.0075, "rr")  # risks above 1 on the relative-risk scale
    with pytest.raises(ValueError):
        sp.interaction_test([0, 1], [0, 2], [0, 1])
    with pytest.raises(ValueError):
        sp.risk_score({"a": np.zeros(2)}, {"b": 1.0})
