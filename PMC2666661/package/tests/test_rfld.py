import csv
import subprocess
import sys

import numpy as np
import pytest

import rfld


def _expected():
    rows = list(csv.DictReader(open(rfld.example_path("h4m4_r1_expected.csv"))))
    return {k: np.array([float(r[k]) for r in rows]) for k in rows[0] if k != "snp"}


def _within(ours, mean, sd):
    return np.abs(ours - mean) <= 4 * np.maximum(sd, 1e-3) * np.sqrt(1 + 1 / 5)


def test_example_matches_fortran_rf0():
    X, y, names = rfld.read_genotypes(rfld.example_path())
    assert X.shape == (500, 104) and names[0] == "snp1"
    res = rfld.grow_forest(X, y, ntree=5000, mtry=35, seed=1)
    e = _expected()
    ok = _within(res["im0"], e["rf0_im0"], e["rf0_im0_sd"])
    assert ok.sum() >= 102, f"{ok.sum()} of 104 SNPs within tolerance of the Fortran program"


def test_example_matches_fortran_rf1():
    X, y, _ = rfld.read_genotypes(rfld.example_path())
    res = rfld.grow_forest(X, y, ntree=5000, mtry=35, seed=1, revised_tree=True, ld_threshold=0.5)
    e = _expected()
    ok = _within(res["im1"], e["rf1_im1"], e["rf1_im1_sd"])
    assert ok.sum() >= 102, f"{ok.sum()} of 104 SNPs within tolerance"
    # RF1 never puts a SNP and its perfect proxy in one tree, so the pair splits the trees
    assert res["trees"][1] + res["trees"][101] < 1.2 * 5000


def test_cli_matches_api(tmp_path):
    out = tmp_path / "imp.csv"
    subprocess.run([sys.executable, "-m", "rfld", str(rfld.example_path()), "-o", str(out),
                    "--ntree", "200", "--seed", "7"], check=True)
    rows = list(csv.DictReader(open(out)))
    X, y, names = rfld.read_genotypes(rfld.example_path())
    api = rfld.importance_table(X, y, names, ntree=200, seed=7)
    assert [r["snp"] for r in rows] == names
    assert np.allclose([float(r["im0"]) for r in rows], [r["im0"] for r in api], atol=1e-6)


def test_same_seed_same_forest():
    X, y, _ = rfld.read_genotypes(rfld.example_path())
    a = rfld.grow_forest(X, y, ntree=100, seed=3)
    b = rfld.grow_forest(X, y, ntree=100, seed=3)
    assert np.array_equal(a["im0"], b["im0"]) and np.array_equal(a["trees"], b["trees"])


def test_bad_input():
    with pytest.raises(ValueError):
        rfld.grow_forest(np.zeros((10, 3), int), np.full(10, 2))
    with pytest.raises(ValueError):
        rfld.grow_forest(np.full((10, 3), -1), np.zeros(10, int))


def test_table1_and_haplotype_em():
    s = rfld.table1_statistics(rfld.MODELS["H4M4"])
    assert round(s["K"], 2) == 0.10 and round(s["lambda_s"]) == 2
    f = rfld.haplotype_frequencies(0.5)
    assert abs(f[1] - 0.287) < 1e-12 and abs(f.sum() - 1) < 1e-12
    rng = np.random.default_rng(1)
    d = rfld.haplotype_dataset(rng, rfld.MODELS["H4M4"], f)
    em, _ = rfld.haplotype_em(d["snps"][:, 0], d["snps"][:, 1])
    assert abs(em.sum() - 1) < 1e-9 and abs(em[1] - 0.287) < 0.05
