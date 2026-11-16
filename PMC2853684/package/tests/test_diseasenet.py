"""Tests for the installed package, with its bundled data only."""

import csv
import subprocess
import sys

import numpy as np
import pytest

import diseasenet as dn

TOL = {"neighborhood": 0.0, "oti": 0.0, "rw": 1e-5, "prop": 1e-5}


def expected():
    with open(dn.example_path("expected_scores.csv")) as f:
        return list(csv.DictReader(f))


def example():
    net = dn.read_network(dn.example_path("network.tsv"))
    cands = dn.read_candidates(dn.example_path("candidates.csv"))
    return net, cands, cands.annotations()


@pytest.mark.parametrize("name,fn", [("neighborhood", dn.neighborhood_scores), ("oti", dn.oti_scores),
                                     ("rw", dn.rw_scores), ("prop", dn.prop_scores)])
def test_example_scores_match_expected(name, fn):
    net, cands, ann = example()
    ours = fn(net, ann, cands)
    exp = np.array([float(r[name]) for r in expected()])
    assert np.all(np.abs(ours - exp) <= TOL[name] + 1e-12), (name, np.abs(ours - exp).max())


def test_command_line_matches_api(tmp_path):
    out = tmp_path / "scores.csv"
    subprocess.run([sys.executable, "-m", "diseasenet", str(dn.example_path("network.tsv")),
                    str(dn.example_path("candidates.csv")), "-o", str(out)], check=True)
    net, cands, ann = example()
    rows = list(csv.DictReader(open(out)))
    assert [r["gene"] for r in rows] == cands.genes
    api = dn.rw_scores(net, ann, cands)
    assert np.allclose([float(r["rw"]) for r in rows], api, rtol=0, atol=1e-15)


def test_leave_one_out_ignores_own_association():
    # a triangle where A and B are the only genes of D: scoring A must not use A itself
    net = dn.network_from_edges([("A", "B"), ("B", "C"), ("A", "C")])
    cands = dn.Candidates(["A", "C"], ["D", "D"], np.array([True, False]))
    s = dn.neighborhood_scores(net, {"D": {"A", "B"}}, cands)
    assert s.tolist() == [0.5, 1.0]


def test_precision_recall_and_empty_prediction():
    p, r, n = dn.precision_recall(np.array([True, False, True]), np.array([True, True, False]))
    assert (p, r, n) == (50.0, 50.0, 2)
    p, r, n = dn.precision_recall(np.zeros(3, dtype=bool), np.array([True, False, False]))
    assert np.isnan(p) and r == 0.0 and n == 0


def test_missing_candidate_columns_raise(tmp_path):
    bad = tmp_path / "bad.csv"
    bad.write_text("gene,disease\nA,D\n")
    with pytest.raises(KeyError):
        dn.read_candidates(bad)
