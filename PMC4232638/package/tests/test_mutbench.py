"""Tests for the installed package, with its bundled data only (run from a copy outside the source tree)."""

import csv
import math
import subprocess
import sys

import numpy as np
import pytest

import mutbench as mb

STATS = ["accuracy", "sensitivity", "specificity", "ppv", "npv", "composite"]


def expected():
    with open(mb.example_path("oncogene_expected.csv"), newline="") as f:
        return {r["predictor"]: r for r in csv.DictReader(f)}


def printed_match(value, printed):
    dec = len(printed.split(".")[1]) if "." in printed else 0
    return abs(value - float(printed)) <= 0.5 * 10 ** (-dec) + 1e-12


def ours():
    labels, calls = mb.read_calls_csv(mb.example_path())
    return {r["predictor"]: r for r in mb.evaluate(labels, calls, n_boot=0)}


def test_example_input_gives_the_papers_values():
    exp, got = expected(), ours()
    assert set(exp) == set(got) and len(exp) == 15
    for p, e in exp.items():
        for k in STATS:
            v = got[p][k] * (1 if k == "composite" else 100)
            assert printed_match(v, e[k]), (p, k, v, e[k])


def test_command_line_matches_api(tmp_path):
    out = tmp_path / "out.csv"
    subprocess.run([sys.executable, "-m", "mutbench", "evaluate", str(mb.example_path()), "--boot", "0", "-o", str(out)], check=True)
    with open(out, newline="") as f:
        rows = {r["predictor"]: r for r in csv.DictReader(f)}
    for p, r in ours().items():
        for k in STATS:
            assert math.isclose(float(rows[p][k]), r[k], rel_tol=1e-5), (p, k)


def test_kappa_of_identical_calls_is_one_and_null_interval():
    a = np.array([1, 0, 1, 1, 0, np.nan, 0, 1, 1, 0], dtype=float)
    k, lo, hi = mb.cohen_kappa(a, a)
    assert k == 1 and hi == 1 and lo < 1


def test_kappa_keeps_no_call_as_a_category():
    a = np.array([1, 1, 0, 0, np.nan], dtype=float)
    b = np.array([1, 1, 0, 0, 1], dtype=float)
    assert mb.cohen_kappa(a, b)[0] < 1


def test_eleven_predictors_give_11253_combinations():
    combos = mb.combinations([f"P{i}" for i in range(11)])
    assert len(combos) == 11253
    assert combos[0] == (("P0", "P1"), 1)


def test_low_confidence_rules():
    assert mb.low_confidence("CHASM (breast)", ["Driver", "Driver", "Passenger"], [0.25, 0.2, 0.36]) == ["low", "non-neutral", "neutral"]
    assert mb.low_confidence("CanDrA (lung)", ["No-call", "Driver"], [0.1, 0.9]) == ["low", "non-neutral"]


def test_split_sample_on_example():
    labels, calls = mb.read_calls_csv(mb.example_path())
    keep = ~np.isnan(labels)
    sel = {p: calls[p][keep] for p in ("CHASM (lung)", "MutationTaster")}
    combos = mb.combinations(list(sel))
    res = mb.split_sample(labels[keep], mb.combination_calls(sel, combos), mb.random_splits(int(keep.sum()), 50, seed=1))
    acc = res["subset1"]["accuracy"]
    assert acc["low"][0] <= acc["mean"][0] <= acc["high"][0]


def test_mismatched_lengths_raise():
    with pytest.raises(ValueError):
        mb.performance([1, 0], [1])


def test_missing_label_column_raises(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("gene,SIFT\nBRAF,Damaging\n")
    with pytest.raises(ValueError, match="label"):
        mb.read_calls_csv(path)
