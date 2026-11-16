"""Tests for the installed package. They use only the package and its bundled data.

check_package.py runs them from a copy outside the source tree, so they test the installed wheel.
"""

import math
import subprocess
import sys

import numpy as np
import pacorg as pc
import pytest


def run_example():
    genes, _, X = pc.read_gct(pc.example_path("example.gct"))
    return pc.infer_pathways(X, genes, pc.read_cls(pc.example_path("example.cls")),
                             pc.read_gmt(pc.example_path("example.gmt")))


def assert_same(ours, expected):
    assert [r["pathway"] for r in ours] == [r["pathway"] for r in expected]
    for o, e in zip(ours, expected):
        assert o["corgs"] == e["corgs"], o["pathway"]
        assert (o["members"], o["measured"], o["n_corgs"]) == (e["members"], e["measured"], e["n_corgs"])
        for k in ("tian", "score"):
            assert math.isclose(o[k], e[k], rel_tol=1e-9), (o["pathway"], k)


def as_rows(results):
    return [{"pathway": r.name, "members": r.members, "measured": r.measured, "n_corgs": len(r.corgs),
             "corgs": r.corgs, "tian": r.tian, "score": r.score} for r in results]


def test_example_input_gives_expected_output():
    assert_same(as_rows(run_example()), pc.read_results(pc.example_path("example_expected.csv")))


def test_command_line_matches_expected_output(tmp_path):
    out = tmp_path / "out.csv"
    subprocess.run([sys.executable, "-m", "pacorg", "--example", "-o", str(out)], check=True)
    assert_same(pc.read_results(out), pc.read_results(pc.example_path("example_expected.csv")))


def test_corg_search_stops_at_first_drop():
    # gene 0 alone separates the classes; gene 1 is noise and must not be added
    y = np.array([True] * 5 + [False] * 5)
    Z = pc.zscore(np.array([[3, 3.2, 2.9, 3.1, 3.0, 0, 0.1, -0.1, 0.2, 0.0],
                            [0.3, -0.2, 0.1, 0.0, -0.1, 0.2, -0.3, 0.1, 0.0, 0.2]]))
    assert pc.find_corgs(Z, y, [1, 0]) == [0]


def test_activity_is_sum_over_sqrt_k():
    Z = np.array([[1.0, -1.0], [3.0, -3.0]])
    assert np.allclose(pc.activity(Z, [0, 1]), np.array([4.0, -4.0]) / math.sqrt(2))


def test_invalid_input_raises():
    with pytest.raises(ValueError):
        pc.zscore(np.array([[1.0, 1.0, 1.0]]))  # zero variance
    with pytest.raises(ValueError):
        pc.t_scores(np.array([1.0, 2.0, 3.0]), ["a", "a", "a"])  # one class
