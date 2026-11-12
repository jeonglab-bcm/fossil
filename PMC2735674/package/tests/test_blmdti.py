"""Tests for the installed package. They use only the package and its bundled data.

check_package.py runs them from a copy outside the source tree, so they test the installed wheel.
Do not add the source folder to sys.path.
"""

import json
import subprocess
import sys

import numpy as np
import pytest

import blmdti as B


def example():
    drugs, targets, adjacency = B.read_network(B.example_path("example_admat.txt"))
    _, _, chemical = B.read_matrix(B.example_path("example_simmat_dc.txt"))
    _, _, genomic = B.read_matrix(B.example_path("example_simmat_dg.txt"))
    expected = json.loads(B.example_path("example_expected.json").read_text())
    return drugs, targets, adjacency, chemical, genomic, expected


def scores_of(adjacency, chemical, genomic):
    drug_kernel, _ = B.make_psd(chemical)
    target_kernel, _ = B.make_psd(genomic)
    return B.aggregate(
        B.blm_drug_scores(adjacency, drug_kernel),
        B.blm_target_scores(adjacency, target_kernel),
    )


def ranked_non_edges(drugs, targets, adjacency, scores):
    rows = [
        (scores[i, j], drugs[i], targets[j])
        for i in range(len(drugs))
        for j in range(len(targets))
        if adjacency[i, j] == 0
    ]
    rows.sort(key=lambda row: -row[0])
    return [(drug, target) for _, drug, target in rows]


def test_planted_edges_rank_first():
    """The expected output of the bundled example: see src/blmdti/data/README.md."""
    drugs, targets, adjacency, chemical, genomic, expected = example()
    ranking = ranked_non_edges(drugs, targets, adjacency, scores_of(adjacency, chemical, genomic))
    planted = {tuple(pair) for pair in expected["planted_pairs"]}
    assert set(ranking[: len(planted)]) == planted


def test_command_line_matches_the_api(tmp_path):
    drugs, targets, adjacency, chemical, genomic, _ = example()
    out = tmp_path / "scores.tsv"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "blmdti",
            str(B.example_path("example_admat.txt")),
            "--chemical",
            str(B.example_path("example_simmat_dc.txt")),
            "--genomic",
            str(B.example_path("example_simmat_dg.txt")),
            "-o",
            str(out),
        ],
        check=True,
    )
    rows, columns, from_cli = B.read_matrix(out)
    assert rows == drugs
    assert columns == targets
    assert np.allclose(from_cli, scores_of(adjacency, chemical, genomic), rtol=1e-9, atol=1e-12)


def test_make_psd_symmetrizes_and_lifts_the_eigenvalues():
    similarity = np.array([[1.0, 0.9, 0.0], [0.5, 1.0, 0.9], [0.0, 0.9, 1.0]])
    kernel, shift = B.make_psd(similarity)
    assert np.allclose(kernel, kernel.T)
    assert np.linalg.eigvalsh(kernel).min() >= -1e-12
    assert shift > 0


def test_make_psd_leaves_a_valid_kernel_alone():
    kernel, shift = B.make_psd(np.eye(3))
    assert shift == 0
    assert np.array_equal(kernel, np.eye(3))


def test_auc_and_aupr_on_a_known_ranking():
    labels = [1, 0, 1, 0]
    scores = [0.9, 0.8, 0.7, 0.6]
    assert B.auc(labels, scores) == pytest.approx(0.75)
    # Precision is 1 at recall 1/2 and 2/3 at recall 1; the step rule averages the two steps.
    assert B.aupr(labels, scores, rule="step") == pytest.approx((1.0 + 2.0 / 3.0) / 2.0)


def test_auc_averages_tied_scores():
    assert B.auc([1, 0], [0.5, 0.5]) == pytest.approx(0.5)


def test_standardized_aggregate_differs_from_the_plain_maximum():
    first = np.array([[0.0, 2.0], [4.0, 6.0]])
    second = np.array([[1.0, 1.1], [1.2, 1.3]])
    assert np.array_equal(B.aggregate(first, second), [[1.0, 2.0], [4.0, 6.0]])
    standardized = B.aggregate(first, second, standardize=True)
    # Where the first matrix is at its lowest, the second one now wins.
    assert standardized[0, 0] > -1.4
    assert standardized[0, 0] == pytest.approx(
        max((0.0 - first.mean()) / first.std(), (1.0 - second.mean()) / second.std())
    )


def test_a_local_model_without_a_positive_example_follows_the_rule():
    adjacency = np.array([[1, 0], [0, 0], [0, 0]])
    kernel = np.eye(3) + 0.5
    scores = B.blm_drug_scores(adjacency, kernel, no_positive="minus_one")
    assert scores[0, 0] == -1.0  # the pair is the only known edge of target 0
    assert np.isnan(B.blm_drug_scores(adjacency, kernel, no_positive="nan")[0, 0])


def test_an_unknown_no_positive_rule_raises():
    with pytest.raises(ValueError, match="no_positive"):
        B.blm_drug_scores(np.array([[1, 0], [0, 1]]), np.eye(2), no_positive="guess")


def test_read_network_transposes_the_benchmark_layout():
    drugs, targets, adjacency = B.read_network(B.example_path("example_admat.txt"))
    assert adjacency.shape == (len(drugs), len(targets))
    assert drugs[0].startswith("D")
    assert targets[0].startswith("T")


def test_shortest_paths_marks_unreachable_pairs():
    edges = np.array([[0, 1, 0], [1, 0, 0], [0, 0, 0]])
    distance = B.shortest_paths(edges)
    assert distance[0, 1] == 1
    assert np.isinf(distance[0, 2])


def test_a_missing_example_file_raises():
    with pytest.raises(FileNotFoundError):
        B.example_path("not_a_file.txt")
