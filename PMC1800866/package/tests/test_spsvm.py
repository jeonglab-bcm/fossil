"""Tests for the installed package. They use only the package and its bundled data.

check_package.py runs them from a copy outside the source tree, so they test the installed wheel.
"""

import csv
import subprocess
import sys

import numpy as np
import pytest
import spsvm


@pytest.fixture(scope="module")
def model():
    profiles = spsvm.read_profiles(spsvm.example_path("example_train_profiles.npz"))
    labels = spsvm.read_table(spsvm.example_path("example_train_labels.txt"))
    chains = [spsvm.Chain(n, profiles[n].sequence, spsvm.descriptors(profiles[n]), labels[n]) for n in sorted(labels)]
    return spsvm.SPSVM("CH").fit(chains)


@pytest.fixture(scope="module")
def czib():
    return spsvm.read_ascii_pssm(spsvm.example_path("czib_NP_060357.1.pssm"))


def expected_ligands():
    with open(spsvm.example_path("czib_5zlq_zinc_ligands.csv"), encoding="utf-8") as f:
        return sorted(int(r["position"]) for r in csv.DictReader(f))


def test_feature_map_equals_semipattern_kernel(czib):
    d = spsvm.descriptors(czib)
    pairs = [(32, 35), (66, 69), (5, 6), (100, 108), (150, 158)]
    X = spsvm.semipattern_features(d, pairs, 6)
    for a, pa in enumerate(pairs):
        for b, pb in enumerate(pairs):
            assert np.isclose(X[a] @ X[b], spsvm.semipattern_kernel(d, pa, d, pb, 6), rtol=1e-12)


def test_pssm_reader(czib):
    assert len(czib) == 160
    assert czib.sequence[32] == czib.sequence[35] == czib.sequence[66] == czib.sequence[69] == "C"
    assert czib.frequencies.shape == (160, 20)


def test_example_matches_crystal_structure(model, czib):
    """The four cysteines that bind zinc in PDB 5ZLQ are the four highest-scoring residues."""
    probs = model.predict_chain(spsvm.chain_from_profile("CZIB", czib, min_weight=0.015))
    top4 = sorted(p + 1 for p in sorted(probs, key=lambda p: -probs[p]["gated"])[:4])
    assert top4 == expected_ligands()
    assert spsvm.predict_protein(probs, 0.5, 3)


def test_command_line_matches_api(model, czib, tmp_path):
    out = tmp_path / "out.csv"
    subprocess.run([sys.executable, "-m", "spsvm", str(spsvm.example_path("czib_NP_060357.1.pssm")), "-o", str(out)], check=True)
    rows = list(csv.DictReader(open(out, encoding="utf-8")))
    probs = model.predict_chain(spsvm.chain_from_profile("CZIB", czib, min_weight=0.015))
    assert len(rows) == len(probs)
    for r in rows:
        assert abs(float(r["p_gated"]) - probs[int(r["position"]) - 1]["gated"]) < 1e-4


def test_gating_rule():
    p = spsvm.gate({0: 0.0, 1: 1.0}, {(0, 1): 0.0}, spsvm.PAPER_PARAMS["CH"])
    sp = spsvm.platt(0.0, 3.2717, -0.077639)
    for i, f in ((0, 0.0), (1, 1.0)):
        loc = spsvm.platt(f, 2.6343, -0.495946)
        assert np.isclose(p[i]["gated"], sp + (1 - sp) * loc)


def test_bad_input_raises():
    with pytest.raises(ValueError):
        spsvm.SPSVM("CHX")
    d = np.zeros((20, spsvm.core.P))
    with pytest.raises(ValueError):
        spsvm.SPSVM("CH").fit([spsvm.Chain("x", "C" * 20, d, {1: 0, 5: 0})])


def test_gap_out_of_range_raises(czib):
    with pytest.raises(ValueError):
        spsvm.semipattern_features(spsvm.descriptors(czib), [(10, 19)], 6)
