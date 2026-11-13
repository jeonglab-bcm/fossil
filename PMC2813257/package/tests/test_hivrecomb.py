"""Tests for the installed package. They use only the package and its bundled data.

check_package.py runs them from a copy outside the source tree, so they test the installed wheel.
Do not add the source folder to sys.path.
"""

import csv
import subprocess
import sys

import hivrecomb as hr
import numpy as np
import pytest

BINS = [0, 30, 60, 90]


def load_example():
    seqs = hr.read_fasta(hr.example_path())
    names = list(seqs)
    X = hr.as_array([seqs[n] for n in names])
    times = [float(n.rsplit("|", 1)[1]) for n in names]
    return X, times


def expected_rows():
    with open(hr.example_path("example_expected.csv"), newline="") as f:
        return list(csv.DictReader(f))


def test_example_matches_the_reference_enumeration():
    """The vectorized code gives the counts of the brute-force enumeration in scripts/."""
    X, times = load_example()
    ev = hr.pair_events(X, times)
    binned = hr.bin_events(ev["d"], ev["found"], BINS)
    for k, row in enumerate(expected_rows()):
        assert int(binned.pairs[k]) == int(row["pairs"]), row
        assert int(binned.counts[k]) == int(row["found"]), row
        assert binned.p[k] == pytest.approx(float(row["probability"]), abs=5e-7)


def test_command_line_gives_the_same_numbers():
    out = subprocess.run([sys.executable, "-m", "hivrecomb", str(hr.example_path())],
                         capture_output=True, text=True, check=True).stdout
    rows = list(csv.DictReader(out.splitlines()))
    for ours, expected in zip(rows, expected_rows()):
        assert ours["pairs"] == expected["pairs"]
        assert ours["found"] == expected["found"]
        assert float(ours["probability"]) == pytest.approx(float(expected["probability"]))


def test_translation_and_codon_alignment_keep_the_reading_frame():
    assert hr.translate("ATGGGGTAA") == "MG*"
    seqs = {"a": "ATGGGGCCCAAA", "b": "ATGCCCAAA"}
    assert hr.align.back_translate("MG-PK", "ATGGGGCCCAAA") == "ATGGGG---CCCAAA"
    assert set(seqs) == {"a", "b"}


def test_rho_is_positive_and_the_fit_is_bounded():
    X, times = load_example()
    ev = hr.pair_events(X, times)
    fit = hr.estimate_rho(ev, bin_width=600.0)
    assert fit.rho > 0
    assert 0.0 <= fit.c0 <= 1.0 and 0.0 <= fit.c1 <= 1.0 and fit.c2 >= 0.0
    assert fit.MpApB > 0


def test_frequency_changes_and_the_hitchhiking_filter():
    X, times = load_example()
    rates = hr.frequency_changes(X, times, min_size=10)
    assert len(rates["rate"]) > 0
    assert np.all(rates["rate"] >= 0)
    assert set(np.unique(rates["case"])) <= {1, 2, 3}
    mask = hr.linked_mask(rates)
    assert mask.shape == rates["rate"].shape
    assert not mask[~rates["synonymous"].astype(bool)].any()


def test_unaligned_input_raises_a_clear_error():
    with pytest.raises(ValueError, match="not aligned"):
        hr.as_array(["ACGT", "ACG"])


def test_one_time_point_gives_no_events():
    X, times = load_example()
    ev = hr.pair_events(X, [times[0]] * len(times))
    assert len(ev["d"]) == 0
