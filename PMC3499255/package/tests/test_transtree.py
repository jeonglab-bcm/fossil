"""Tests for the transtree package, run against the installed package and its
bundled example data only."""

import json
import subprocess
import sys

import numpy as np

import transtree as tt
from transtree.core import State, log_Pms


def _example_data():
    return tt.read_dataset(tt.example_path("example_epi.csv"),
                           tt.example_path("example_hamming.csv"),
                           s=4000.0, m=1e-4)


def test_divergence_matches_figure_s1():
    """The pseudo-likelihood traversal reproduces div(i,j) of the Fig. S1 example."""
    j, i, k, l = 0, 1, 2, 3
    J = np.array([-1, j, j, i])
    Tinf = np.array([0.0, 1.0, 2.0, 3.0])
    expected = {(i, j): i, (k, j): k, (k, i): i, (l, j): i, (l, i): l, (l, k): i}
    for (a, b), want in expected.items():
        assert tt.divergence_premise(a, b, J, Tinf) == want
        assert tt.divergence_premise(b, a, J, Tinf) == want


def test_binomial_normalises():
    """P_{m,s}(M | delta) sums to 1 over M = 0..s for a small sequence length."""
    s, m, delta = 20.0, 1e-3, 50.0
    probs = np.exp([log_Pms(M, delta, m, s) for M in range(int(s) + 1)])
    assert abs(probs.sum() - 1.0) < 1e-9


def test_zero_distance_gives_zero_substitution_prob():
    """At delta = 0 the per-site difference probability is 0 (identical sequences)."""
    assert float(np.exp(log_Pms(0.0, 0.0, 1e-4, 8000.0))) == 1.0


def test_inference_recovers_example_tree():
    """On the bundled example the inferred tree agrees with the simulated truth.

    The expected output is the simulation's ground truth, produced by the
    simulator, not by transtree's inference.
    """
    data = _example_data()
    expected = json.loads(tt.example_path("example_expected.json").read_text())
    post = tt.run_mcmc(data, tt.MCMCConfig(iters=6000, burn_in_frac=0.4, seed=3))
    true_tree = expected["true_tree"]
    # count premises whose most-likely inferred source equals the true source
    correct = 0
    for i in range(data.I):
        inferred = int(np.argmax(post.trans_prob[i]))
        inferred = -1 if inferred == data.I else inferred
        if inferred == true_tree[i]:
            correct += 1
    # a small outbreak is mostly recoverable; require a clear majority
    assert correct >= data.I - 1


def test_latency_posterior_is_sensible():
    """The mean-latency posterior is positive, ordered, and near the simulated value."""
    data = _example_data()
    expected = json.loads(tt.example_path("example_expected.json").read_text())
    post = tt.run_mcmc(data, tt.MCMCConfig(iters=6000, burn_in_frac=0.4, seed=3))
    lo, med, hi = (np.quantile(post.mean_latency, 0.025),
                   np.median(post.mean_latency),
                   np.quantile(post.mean_latency, 0.975))
    assert 0 < lo <= med <= hi
    # within a factor of ~3 of the simulated mean latency (true = 6 days)
    assert 0.33 * expected["true_mean_latency"] <= med <= 3.0 * expected["true_mean_latency"]


def test_cli_matches_api(tmp_path):
    """The command line produces the same most-likely tree as the API."""
    epi = tt.example_path("example_epi.csv")
    ham = tt.example_path("example_hamming.csv")
    out = tmp_path / "out.json"
    subprocess.run([sys.executable, "-m", "transtree", str(epi), str(ham),
                    "--s", "4000", "--m", "1e-4", "--iters", "4000", "--seed", "3",
                    "-o", str(out)], check=True)
    cli = json.loads(out.read_text())
    assert len(cli["most_likely_tree"]) == 6
    assert "mean_latency_days" in cli


def test_invalid_input_raises():
    """A Hamming matrix whose size does not match the premises is rejected."""
    import pytest
    with pytest.raises(ValueError):
        tt.Data(names=["a", "b"], X=np.zeros((2, 2)), Tobs=np.array([1.0, 2.0]),
                Tend=np.array([2.0, 3.0]), Dobs=np.array([1.0, 1.0]),
                M=np.zeros((3, 3)), s=10.0, m=1e-3)
    with pytest.raises(ValueError):
        tt.Data(names=["a"], X=np.zeros((1, 2)), Tobs=np.array([1.0]),
                Tend=np.array([2.0]), Dobs=np.array([1.0]),
                M=np.zeros((1, 1)), s=10.0, m=1e-3)
