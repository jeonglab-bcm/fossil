#!/usr/bin/env python3
"""Train and test the SP-SVM (package spsvm) on the paper's own evaluation sets.

The candidate residues, their labels, the LOO set and the five CV folds are those of Additional
file 1; only the profiles are ours. Supplement positions are mapped onto today's SEQRES with the
offset found by parse_structures.py; residues whose letter still differs are left out.

Usage:
  run_svm.py prepare SUPPLEMENT_DIR CHAINS_TSV PROFILES_NPZ OUT_DIR
      writes candidates.tsv (variant, set, fold, chain, position, residue, label) and mapping.json
  run_svm.py cv VARIANT OUT_DIR [FOLD]            five-fold CV (or one fold), writes cv_<variant>[_<fold>].tsv
  run_svm.py loo VARIANT OUT_DIR TASK NTASKS       leave-one-chain-out for every NTASKS-th chain
  run_svm.py merge VARIANT OUT_DIR                 joins the LOO parts into loo_<variant>.tsv

VARIANT is CH or CHDE. Prediction tables hold, per residue: chain, position, residue, label,
the local and semi-pattern margins and the three probabilities of Eq. (2).
"""
import csv
import json
import shutil
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import spsvm

FILES = {("CH", "loo"): "CH_loo", ("CHDE", "loo"): "CHDE_loo"}
FILES.update({(v, f"cv{i}"): f"{v}_split_{i}" for v in ("CH", "CHDE") for i in range(5)})


def prepare(sup, chains_tsv, profiles_npz, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    chains = {r["chain"]: r for r in csv.DictReader(open(chains_tsv), delimiter="\t")}
    profiles = spsvm.read_profiles(profiles_npz)
    if Path(profiles_npz).resolve() != (out / "profiles.npz").resolve():
        shutil.copyfile(profiles_npz, out / "profiles.npz")
    kept = defaultdict(int)
    dropped = defaultdict(lambda: defaultdict(int))
    rows = []
    for (variant, part), fname in sorted(FILES.items()):
        for line in open(Path(sup) / fname):
            cls, chain, pos, aa = line.split()[:4]
            key = f"{variant}_{part[:3] if part.startswith('cv') else part}"
            if chain not in chains:
                dropped[key]["chain_not_in_pdb"] += 1
                continue
            if chain not in profiles:
                dropped[key]["no_profile"] += 1
                continue
            p = int(pos) + int(chains[chain]["shift"])
            seq = chains[chain]["sequence"]
            if not (0 <= p < len(seq)) or seq[p] != aa:
                dropped[key]["letter_differs"] += 1
                continue
            if profiles[chain].sequence[p] != aa:
                dropped[key]["profile_letter_differs"] += 1
                continue
            fold = part[2:] if part.startswith("cv") else "-"
            rows.append((variant, "cv" if part.startswith("cv") else "loo", fold, chain, p, aa, 1 if cls == "1" else 0))
            kept[key] += 1
    with open(out / "candidates.tsv", "w") as f:
        f.write("variant\tset\tfold\tchain\tpos\taa\tlabel\n")
        for r in rows:
            f.write("\t".join(map(str, r)) + "\n")
    json.dump({"kept": kept, "dropped": {k: dict(v) for k, v in dropped.items()}}, open(out / "mapping.json", "w"), indent=1)
    print(json.dumps({"kept": kept, "dropped": {k: dict(v) for k, v in dropped.items()}}))


def load(out, variant, which):
    profiles = spsvm.read_profiles(Path(out) / "profiles.npz")
    cands = defaultdict(dict)
    folds = {}
    for r in csv.DictReader(open(Path(out) / "candidates.tsv"), delimiter="\t"):
        if r["variant"] == variant and r["set"] == which:
            cands[r["chain"]][int(r["pos"])] = int(r["label"])
            folds[r["chain"]] = r["fold"]
    return profiles, cands, folds


def make_chains(profiles, cands):
    return {c: spsvm.Chain(c, profiles[c].sequence, spsvm.descriptors(profiles[c]), cands[c]) for c in sorted(cands)}


def predict_rows(model, chain):
    loc, sp = model.margins(chain)
    probs = spsvm.gate(loc, sp, model.params)
    best_sp = defaultdict(lambda: None)
    for (i, j), f in sp.items():
        for p in (i, j):
            if best_sp[p] is None or f > best_sp[p]:
                best_sp[p] = f
    rows = []
    for p in sorted(chain.candidates):
        rows.append((chain.name, p, chain.sequence[p], chain.candidates[p], f"{loc[p]:.6f}",
                     "" if best_sp[p] is None else f"{best_sp[p]:.6f}",
                     f"{probs[p]['local']:.6f}", f"{probs[p]['semipattern']:.6f}", f"{probs[p]['gated']:.6f}"))
    return rows


HEADER = "chain\tpos\taa\tlabel\tlocal_margin\tsp_margin\tp_local\tp_semipattern\tp_gated\n"


def write(path, rows):
    with open(path, "w") as f:
        f.write(HEADER)
        for r in rows:
            f.write("\t".join(map(str, r)) + "\n")


def run_cv(variant, out, only=None):
    profiles, cands, folds = load(out, variant, "cv")
    chains = make_chains(profiles, cands)
    rows = []
    for k in (range(5) if only is None else [int(only)]):
        t = time.time()
        train = [c for n, c in chains.items() if folds[n] != str(k)]
        test = [c for n, c in chains.items() if folds[n] == str(k)]
        model = spsvm.SPSVM(variant).fit(train)
        for c in test:
            rows.extend(predict_rows(model, c))
        print(f"{variant} fold {k}: {len(train)} train chains, {len(test)} test, {time.time() - t:.0f} s", flush=True)
    write(Path(out) / (f"cv_{variant}.tsv" if only is None else f"cv_{variant}_{only}.tsv"), rows)


def run_loo(variant, out, task, ntasks):
    profiles, cands, _ = load(out, variant, "loo")
    chains = make_chains(profiles, cands)
    names = sorted(chains)
    part = Path(out) / f"loo_{variant}_parts"
    part.mkdir(exist_ok=True)
    for i in range(int(task), len(names), int(ntasks)):
        n = names[i]
        dest = part / f"{n}.tsv"
        if dest.exists():
            continue
        t = time.time()
        model = spsvm.SPSVM(variant).fit([chains[m] for m in names if m != n])
        write(dest, predict_rows(model, chains[n]))
        print(f"{variant} {n} {time.time() - t:.0f} s", flush=True)


def merge(variant, out):
    _, cands, _ = load(out, variant, "loo")
    part = Path(out) / f"loo_{variant}_parts"
    rows = []
    missing = [n for n in sorted(cands) if not (part / f"{n}.tsv").exists()]
    if missing:
        sys.exit(f"{len(missing)} LOO chains missing, e.g. {missing[:5]}")
    with open(Path(out) / f"loo_{variant}.tsv", "w") as f:
        f.write(HEADER)
        for n in sorted(cands):
            lines = open(part / f"{n}.tsv").read().splitlines()[1:]
            f.write("".join(line + "\n" for line in lines))


if __name__ == "__main__":
    cmd, *a = sys.argv[1:]
    {"prepare": prepare, "cv": run_cv, "loo": run_loo, "merge": merge}[cmd](*a)
