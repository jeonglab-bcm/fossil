#!/usr/bin/env python3
"""Pack the ASCII PSSMs of run_psiblast.sh into one profiles.npz (spsvm.write_profiles).
Usage: collect_profiles.py PSSM_DIR OUT_NPZ"""
import sys
from pathlib import Path

import spsvm

profiles = {p.stem: spsvm.read_ascii_pssm(p) for p in sorted(Path(sys.argv[1]).glob("*.pssm"))}
spsvm.write_profiles(profiles, sys.argv[2])
print(f"{len(profiles)} profiles")
