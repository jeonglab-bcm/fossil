#!/usr/bin/env python3
"""Write the package's example data from the reproduction's outputs (run from the repository root).

    python PMC1800866/package/scripts/make_example_data.py PSSM_DIR

PSSM_DIR holds the ASCII PSSMs of run_psiblast.sh (for the CZIB file). The training subset is drawn
from output/predictions/candidates.tsv and output/profiles/pdb_profiles.npz; the 5ZLQ ligands are
read from the structure (downloaded from RCSB).
"""
import csv
import gzip
import random
import shutil
import sys
import urllib.request
from collections import defaultdict
from pathlib import Path

import gemmi
import spsvm

ROOT = Path("PMC1800866")
OUT = ROOT / "package/src/spsvm/data"
DONORS = {"SG", "ND1", "NE2", "OD1", "OD2", "OE1", "OE2"}


def main(pssm_dir):
    cands = defaultdict(dict)
    for r in csv.DictReader(open(ROOT / "figure-reproduction/output/predictions/candidates.tsv"), delimiter="\t"):
        if r["variant"] == "CH" and r["set"] == "cv":
            cands[r["chain"]][int(r["pos"])] = (int(r["label"]), r["aa"])
    zinc = sorted(c for c, v in cands.items() if any(l for l, _ in v.values()))
    free = sorted(c for c in cands if c not in zinc)
    rng = random.Random(1)
    chosen = sorted(rng.sample(zinc, 50) + rng.sample(free, 100))
    profiles = spsvm.read_profiles(ROOT / "figure-reproduction/output/profiles/pdb_profiles.npz")
    spsvm.write_profiles({c: profiles[c] for c in chosen}, OUT / "example_train_profiles.npz")
    with open(OUT / "example_train_labels.txt", "w") as f:
        for c in chosen:
            for p in sorted(cands[c]):
                lab, aa = cands[c][p]
                f.write(f"{1 if lab else -1}\t{c}\t{p}\t{aa}\t{'ZN' if lab else 'FREE'}\n")
    shutil.copyfile(Path(pssm_dir) / "NP_060357.1.pssm", OUT / "czib_NP_060357.1.pssm")
    path = OUT.parent / "5zlq.cif.gz"
    urllib.request.urlretrieve("https://files.rcsb.org/download/5ZLQ.cif.gz", path)
    st = gemmi.read_structure(str(path))
    path.unlink()
    m = st[0]
    rows = []
    for c in m:
        for r in c:
            for z in r:
                if z.element.name != "Zn":
                    continue
                for c2 in m:
                    for res in c2:
                        for a in res:
                            if a.name in DONORS and a.pos.dist(z.pos) <= 3.0:
                                rows.append((res.seqid.num, gemmi.find_tabulated_residue(res.name).one_letter_code.upper(), a.name, round(a.pos.dist(z.pos), 2)))
    with open(OUT / "czib_5zlq_zinc_ligands.csv", "w") as f:
        f.write("position,residue,atom,distance_A\n")
        for r in sorted(rows):
            f.write(",".join(map(str, r)) + "\n")


if __name__ == "__main__":
    main(sys.argv[1])
