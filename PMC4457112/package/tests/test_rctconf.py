"""Tests for the installed package. They use only the package and its bundled data.

check_package.py runs them from a copy outside the source tree, so they test the installed wheel.
"""

import csv
import math
import subprocess
import sys

import numpy as np
import pytest

import rctconf


def expected_labels():
    with open(rctconf.example_path("citations_test_expected.csv"), newline="", encoding="utf-8") as fh:
        return {r["pmid"]: int(r["rct"]) for r in csv.DictReader(fh)}


@pytest.fixture(scope="module")
def model():
    train = rctconf.read_citations(rctconf.example_path("citations_train.csv.gz"))
    return rctconf.train(train, [r["rct"] for r in train], rctconf.EXAMPLE_SETS)


def test_example_scores_agree_with_medline(model):
    test = rctconf.read_citations(rctconf.example_path("citations_test.csv.gz"))
    exp = expected_labels()
    y = np.array([exp[r["pmid"]] for r in test])
    f = model.margins(test)
    # MEDLINE's own RCT publication type is the expected output; the paper's models reach AUC 0.97.
    assert rctconf.auc(y, f) >= 0.90
    agree = int(((f > 0) == (y == 1)).sum())
    assert agree >= 0.85 * len(y)
    c = model.confidence_from_margins(f)
    assert ((c >= 0) & (c <= 1)).all()
    assert rctconf.mse(y, c) < rctconf.mse(y, rctconf.zero_sigmoid(f))


def test_command_line_matches_api(tmp_path, model):
    m = tmp_path / "model.npz"
    out = tmp_path / "scores.csv"
    train = rctconf.example_path("citations_train.csv.gz")
    test = rctconf.example_path("citations_test.csv.gz")
    subprocess.run([sys.executable, "-m", "rctconf", "train", str(train), "-o", str(m),
                    "--sets", *rctconf.EXAMPLE_SETS], check=True)
    subprocess.run([sys.executable, "-m", "rctconf", "score", str(m), str(test), "-o", str(out)], check=True)
    with open(out, newline="") as fh:
        rows = list(csv.DictReader(fh))
    api = model.confidence(rctconf.read_citations(test))
    assert len(rows) == len(api)
    assert np.allclose([float(r["confidence"]) for r in rows], api, atol=1e-6)


def test_saved_model_gives_same_scores(tmp_path, model):
    test = rctconf.read_citations(rctconf.example_path("citations_test.csv.gz"))
    model.save(tmp_path / "m.npz")
    again = rctconf.RCTModel.load(tmp_path / "m.npz")
    assert np.allclose(again.margins(test), model.margins(test))


def test_metrics_by_hand():
    # 3 positives, 3 negatives; one positive below one negative: AUC 8/9
    y = [1, 1, 1, 0, 0, 0]
    s = [0.9, 0.8, 0.3, 0.4, 0.2, 0.1]
    assert math.isclose(rctconf.auc(y, s), 8 / 9)
    # precision at the positives' ranks: 1/1, 2/2, 3/4
    assert math.isclose(rctconf.average_precision(y, s), (1 + 1 + 0.75) / 3)
    b = rctconf.binary_measures(y, [1, 1, 0, 1, 0, 0])
    assert (b["tp"], b["fp"], b["fn"], b["tn"]) == (2, 1, 1, 2)
    assert math.isclose(b["f1"], 2 / 3)
    assert math.isclose(rctconf.mse([1, 0], [0.8, 0.4]), (0.04 + 0.16) / 2)
    # Hanley and McNeil (1982), eq. 2 by hand for A 0.9 and 50 + 50 cases:
    # Q1 = 0.9/1.1, Q2 = 1.62/1.9, SE = sqrt((0.09 + 49 (Q1 - 0.81) + 49 (Q2 - 0.81)) / 2500) = 0.032123
    assert abs(rctconf.hanley_mcneil_se(0.9, 50, 50) - 0.032123) < 1e-6


def test_tokens_and_ngrams():
    assert rctconf.tokens("A Randomized, double-blind trial of X-ray therapy") == [
        "randomized", "double", "blind", "trial", "ray", "therapy"]
    raw = rctconf.raw_features({"title": "Randomized trial of aspirin", "pubtypes": "D016449|D016428"},
                               ["title_bigrams", "pubtypes"])
    assert raw["title_bigrams"] == {"randomized trial", "trial aspirin"}
    assert raw["pubtypes"] == {"D016428"}  # the RCT publication type is never a feature


def test_mdl_cut_points():
    # labels change at 5: one cut between 4 and 6
    v = [1, 2, 3, 4] * 25 + [6, 7, 8, 9] * 25
    y = [0] * 100 + [1] * 100
    assert list(rctconf.mdl_cut_points(v, y)) == [5.0]
    # no relation: no cut
    assert len(rctconf.mdl_cut_points([1, 2, 1, 2] * 10, [0, 0, 1, 1] * 10)) == 0


def test_bad_input_raises(tmp_path):
    with pytest.raises(ValueError):
        rctconf.auc([1, 1], [0.2, 0.3])
    with pytest.raises(ValueError):
        rctconf.raw_features({"title": "x"}, ["no_such_set"])
    bad = tmp_path / "bad.csv"
    bad.write_text("title\nx\n")
    with pytest.raises(ValueError, match="pmid"):
        rctconf.read_citations(bad)
