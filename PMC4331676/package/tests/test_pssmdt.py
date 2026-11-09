"""Tests for the installed package. They use only the package and its bundled data.

check_package.py runs them from a copy outside the source tree, so they test the installed wheel.
"""

import csv
import subprocess
import sys

import numpy as np
import pssmdt
import pytest


def expected():
    with open(pssmdt.example_path("expected_pssm_dt.csv"), newline="") as f:
        rows = list(csv.reader(f))
    return rows[0][1:], {r[0]: np.array([float(x) for x in r[1:]]) for r in rows[1:]}


def example_pssms():
    return sorted(pssmdt.example_path("pssm").glob("*.pssm"))


def test_example_input_gives_expected_output():
    names, exp = expected()
    assert names == pssmdt.feature_names(5)
    files = example_pssms()
    assert {f.stem for f in files} == set(exp)
    for f in files:
        seq, s = pssmdt.read_pssm(f)
        np.testing.assert_allclose(pssmdt.pssm_dt(s, 5), exp[f.stem], rtol=1e-12, atol=1e-12)


def test_command_line_matches_api(tmp_path):
    out = tmp_path / "out.csv"
    files = [str(f) for f in example_pssms()]
    subprocess.run([sys.executable, "-m", "pssmdt", *files, "-o", str(out)], check=True)
    with open(out, newline="") as f:
        rows = list(csv.reader(f))
    assert rows[0][1:] == pssmdt.feature_names(5)
    _, exp = expected()
    for r in rows[1:]:
        np.testing.assert_allclose(np.array([float(x) for x in r[1:]]), exp[r[0]], rtol=1e-12)


def test_hand_computed_values():
    # 3 positions; DT(A, R, 1) = (S[0,A] S[1,R] + S[1,A] S[2,R]) / 2 and DT(A, A, 2) = S[0,A] S[2,A]
    s = np.zeros((3, 20), int)
    s[:, 0] = [2, -1, 3]   # A
    s[:, 1] = [0, 4, -2]   # R
    v = pssmdt.pssm_dt(s, 2)
    names = pssmdt.feature_names(2)
    assert v[names.index("A-R_lg1")] == (2 * 4 + (-1) * (-2)) / 2
    assert v[names.index("A-A_lg2")] == 2 * 3
    assert len(pssmdt.pssm_sdt(s, 2)) == 40 and len(pssmdt.pssm_ddt(s, 2)) == 760


def test_encoding_sizes():
    seq, s = pssmdt.read_pssm(example_pssms()[0])
    sizes = {e: len(pssmdt.encode(s, seq, e, 5)) for e in pssmdt.ENCODINGS}
    assert sizes == {"PSSM-DT": 2000, "PSSM-SDT": 100, "PSSM-DDT": 1900, "AvePscore-20": 20,
                     "AvePscore-400": 400, "Pscore-100": 100, "ACC": 2000}


def test_metrics_follow_the_equations():
    y = np.array([1, 1, 1, 0, 0])
    d = np.array([2.0, 1.0, -1.0, -2.0, 0.5])
    m = pssmdt.metrics(y, d)
    assert (m["TP"], m["FN"], m["TN"], m["FP"]) == (2, 1, 1, 1)
    assert m["SN"] == pytest.approx(200 / 3) and m["SP"] == 50 and m["ACC"] == 60
    assert m["MCC"] == pytest.approx((2 * 1 - 1 * 1) / np.sqrt(3 * 3 * 2 * 2))


def test_too_short_sequence_raises():
    with pytest.raises(ValueError, match="too short"):
        pssmdt.pssm_dt(np.zeros((5, 20)), 5)
    with pytest.raises(ValueError, match="L x 20"):
        pssmdt.pssm_dt(np.zeros((10, 19)), 2)
