"""Tests for the installed package, using only the package and its bundled data.

check_package.py runs them from a copy outside the source tree, so they test the installed wheel.
"""

import csv
import math
import subprocess
import sys

import condloc as cl
import numpy as np
import pytest


def table(name):
    with open(cl.example_path(name), newline="") as h:
        rows = [r for r in csv.reader(h, delimiter="\t") if r and not r[0].startswith("#")]
    return rows[0], rows[1:]


def test_coherence_matches_expected():
    _, rows = table("expected_coherence.tsv")
    ours = cl.link_coherence(cl.example_path("example_expression.tsv"), cl.example_path("example_network.tsv"))
    assert [(a, b) for a, b, _ in ours] == [(r[0], r[1]) for r in rows]
    for (_, _, p), r in zip(ours, rows):
        assert math.isclose(p, float(r[2]), rel_tol=1e-9, abs_tol=1e-12)


def test_neighbourhood_weights_match_expected():
    _, locs = table("example_locations.tsv")
    names = [r[0] for r in locs]
    idx = {p: i for i, p in enumerate(names)}
    loc_names = sorted({x for r in locs for x in r[1].split(",") if x})
    masks = cl.location_masks([[loc_names.index(x) for x in r[1].split(",") if x] for r in locs], len(loc_names))
    links = cl.read_links(cl.example_path("example_network.tsv"))
    adj = cl.adjacency(len(names), np.array([(idx[a], idx[b]) for a, b in links]))
    _, rows = table("expected_weights.tsv")
    for d in (1, 2):
        w = cl.neighbourhood_weights(adj, masks, d, rho=2.0).toarray()
        expected = np.zeros_like(w)
        for r in rows:
            if int(r[0]) == d:
                expected[idx[r[1]], idx[r[2]]] = float(r[3])
        assert np.allclose(w, expected, rtol=1e-9, atol=1e-12)


def test_possibility_matches_expected():
    with open(cl.example_path("expected_possibility.tsv")) as h:
        lines = h.read().splitlines()
    pos = [float(x) for x in lines[0].split(":")[1].split()]
    neg = [float(x) for x in lines[1].split(":")[1].split()]
    rows = [r.split("\t") for r in lines[3:]]
    c = np.array([float(r[0]) for r in rows])
    assert np.allclose(cl.possibility(c, np.array(pos), np.array(neg)), [float(r[1]) for r in rows], atol=1e-12)


def test_command_line_matches_api(tmp_path):
    out = tmp_path / "phi.tsv"
    subprocess.run([sys.executable, "-m", "condloc", str(cl.example_path("example_expression.tsv")),
                    str(cl.example_path("example_network.tsv")), "-o", str(out)], check=True)
    _, rows = table("expected_coherence.tsv")
    got = [line.split("\t") for line in out.read_text().splitlines()[1:]]
    assert [g[:2] for g in got] == [r[:2] for r in rows]
    assert all(math.isclose(float(g[2]), float(r[2]), rel_tol=1e-9, abs_tol=1e-12) for g, r in zip(got, rows))


def test_single_features_shapes():
    s = cl.single_features(["MKTAYIAKQR", "GG"], [["IPR1"], []], [["GO:1"], []], ["IPR1"], ["GO:1"])
    assert s["AA"].shape == (2, 20) and s["dAA"].shape == (2, 400) and s["cHPo"].shape == (2, 40)
    assert math.isclose(float(s["AA"][0].sum()), 1.0, rel_tol=1e-6)
    assert s["cHPo"][1, 1:].sum() == 0  # a two-residue protein has a single lag


def test_auc_edge_cases():
    assert cl.auc(np.array([0.1, 0.9]), np.array([False, True])) == 1.0
    assert math.isnan(cl.auc(np.array([0.1, 0.9]), np.array([True, True])))


def test_bad_distance_raises():
    adj = cl.adjacency(2, np.array([[0, 1]]))
    with pytest.raises(ValueError):
        cl.neighbourhood_weights(adj, np.zeros(2, dtype=np.int64), 3)
