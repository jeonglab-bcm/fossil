"""Tests of the installed package with its bundled data only."""

import csv
import subprocess
import sys

import numpy as np
import pytest

import nmdsplice as nm


def expected():
    with open(nm.example_path("example_expected.tsv")) as f:
        return {(r["chrom"], int(r["donor"]), int(r["acceptor"])): int(r["ptc_distance"])
                for r in csv.DictReader(f, delimiter="\t")}


def run_example():
    return nm.ptc_table(nm.read_junctions(nm.example_path("example_junctions.tsv")),
                        nm.load_annotation(nm.example_path("example_annotation")),
                        nm.example_path("example_genome.fa"))


def test_example_ptc_distances_match_the_paper():
    exp = expected()
    rows = run_example()
    assert len(rows) == len(exp) == 12
    for r in rows:
        assert r["ptc"], r
        assert r["ptc_distance"] == exp[(r["chrom"], r["donor"], r["acceptor"])], r


def test_command_line_matches_api(tmp_path):
    out = tmp_path / "out.tsv"
    subprocess.run([sys.executable, "-m", "nmdsplice", "ptc", str(nm.example_path("example_junctions.tsv")),
                    "--annotation", str(nm.example_path("example_annotation")),
                    "--genome", str(nm.example_path("example_genome.fa")), "-o", str(out)], check=True)
    with open(out) as f:
        cli = {(r["chrom"], int(r["donor"]), int(r["acceptor"])): int(r["ptc_distance"])
               for r in csv.DictReader(f, delimiter="\t")}
    assert cli == expected()


def test_tmm_matches_edger_on_a_small_matrix():
    # edgeR 4.4.0, calcNormFactors(x) for this matrix: 1.08700799 1.08914262 0.84466113
    x = np.array([[10, 12, 30], [20, 22, 18], [5, 6, 50], [100, 110, 90], [7, 9, 3], [40, 44, 35]], float)
    f = nm.tmm_factors(x)
    assert f == pytest.approx([1.08700799, 1.08914262, 0.84466113], abs=1e-8)
    assert np.prod(f) == pytest.approx(1.0)


def test_bad_junction_raises(tmp_path):
    p = tmp_path / "bad.tsv"
    p.write_text("chrom\tstrand\tdonor\tacceptor\nchr1\t+\t200\t100\n")
    with pytest.raises(ValueError):
        nm.read_junctions(p)


def test_unannotated_junction_is_excluded():
    rows = nm.ptc_table([{"chrom": "chr2", "strand": "-", "donor": 164625446, "acceptor": 164630190}],
                        nm.load_annotation(nm.example_path("example_annotation")),
                        nm.example_path("example_genome.fa"))
    assert rows[0]["status"] == "unannotated"
