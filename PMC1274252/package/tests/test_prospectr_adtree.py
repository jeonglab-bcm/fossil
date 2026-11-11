"""Tests for the installed package. They use only the package and its bundled data."""

import csv
import math
import subprocess
import sys

import prospectr_adtree as pa
import pytest


def weka_scores(name):
    with open(pa.example_path(name), newline="") as f:
        return {int(r["index"]): (int(r["fold"]), float(r["score"])) for r in csv.DictReader(f, delimiter="\t")}


def test_tree_is_wekas():
    d = pa.read_arff(pa.example_path())
    model = pa.ADTree(15, "zpure").fit(d)
    weka = pa.example_path("example_train_weka_tree.txt").read_text()
    assert model.to_weka_string().strip() == weka[weka.index("Alternating"):].strip()


def test_scores_are_wekas():
    d = pa.read_arff(pa.example_path())
    ours = pa.ADTree(15).fit(d).scores(d)
    weka = weka_scores("example_train_weka_scores.tsv")
    assert all(math.isclose(ours[i], s, abs_tol=1e-12) for i, (_, s) in weka.items())


def test_cross_validation_is_wekas():
    d = pa.read_arff(pa.example_path())
    weka = weka_scores("example_train_weka_cv.tsv")
    for r in pa.cross_validate(d, 15, "zpure", 10, 1):
        fold, s = weka[r["index"]]
        assert r["fold"] == fold
        assert math.isclose(r["score"], s, abs_tol=1e-12)


def test_published_tree_matches_hand_sums():
    with open(pa.example_path("example_genes.csv"), newline="") as f:
        genes = list(csv.DictReader(f))
    with open(pa.example_path("example_genes_expected.csv"), newline="") as f:
        expected = {r["gene"]: r for r in csv.DictReader(f)}
    for g in genes:
        feats = {k: float(v) for k, v in g.items() if k != "gene" and v != ""}
        raw = pa.score(feats)
        assert math.isclose(raw, float(expected[g["gene"]]["raw_score"]), abs_tol=1e-9)
        assert math.isclose(pa.normalise(raw), float(expected[g["gene"]]["normalised_score"]), abs_tol=1e-6)


def test_command_line_matches_api(tmp_path):
    out = tmp_path / "scores.csv"
    subprocess.run([sys.executable, "-m", "prospectr_adtree", "train", str(pa.example_path()), "-o", str(out)], check=True)
    with open(out, newline="") as f:
        rows = list(csv.DictReader(f))
    d = pa.read_arff(pa.example_path())
    ours = pa.ADTree(15).fit(d).scores(d)
    assert [float(r["score"]) for r in rows] == ours
    out2 = tmp_path / "genes.csv"
    subprocess.run([sys.executable, "-m", "prospectr_adtree", "score", str(pa.example_path("example_genes.csv")), "-o", str(out2)], check=True)
    with open(out2, newline="") as f:
        got = {r["gene"]: r["raw_score"] for r in csv.DictReader(f)}
    assert got == {"long_conserved_secreted": "-1.126", "short_no_homolog": "1.168", "partly_unknown": "-0.511"}


def test_needs_two_classes(tmp_path):
    p = tmp_path / "three.arff"
    p.write_text("@relation x\n@attribute a numeric\n@attribute c {u,v,w}\n@data\n1,u\n2,v\n3,w\n")
    with pytest.raises(ValueError):
        pa.ADTree(3).fit(pa.read_arff(p))


def test_unknown_features_are_skipped():
    assert pa.score({}) == 0.0
    assert pa.contributions({}) == {}
