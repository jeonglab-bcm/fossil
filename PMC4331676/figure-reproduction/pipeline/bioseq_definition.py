"""PSSM-DT as the authors' later toolkit computes it, against the pssmdt package.

Usage: bioseq_definition.py PSSMS.npz OUT.json

BioSeq-Analysis2.0 (Liu's lab, the senior author's; bliulab.net/BioSeq-Analysis2.0, mode PSSM-DT)
ships PSSM-DT only as compiled Python 3.6 (profile.pyc). Its functions preHandleColumns,
generate_ksb_pssm and aver were read from the bytecode (disassembled with xdis; nothing of it is
redistributed here). transliterated() repeats those loops in plain Python: for each lag 1..LG,
M[i][j] += PSSM[k][i] * PSSM[k + lag][j] over k < L - lag, divided by L - lag, flattened row by
row; PSSM holds the 20 raw integer scores of the ASCII PSSM. The check: the package's pssm_dt equals
it on every tenth PSSM of the run (127 of 1,261; the plain loops are slow), to 1e-12.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pssmdt


def transliterated(pssm_rows, lag):
    seq_cn = len(pssm_rows)
    vector = []
    for step in range(1, lag + 1):
        matrix_final = [[0.0] * 20 for _ in range(20)]
        for i in range(20):
            for j in range(20):
                for k in range(seq_cn - step):
                    matrix_final[i][j] += float(pssm_rows[k][i]) * float(pssm_rows[k + step][j])
        vector += [matrix_final[i][j] / float(seq_cn - step) for i in range(20) for j in range(20)]
    return vector


def main(npz, out):
    z = np.load(npz)
    offs = np.concatenate([[0], np.cumsum(z["length"])])
    worst = 0.0
    n = 0
    for k in range(0, len(z["id"]), 10):
        s = z["scores"][offs[k]:offs[k + 1]].astype(int).tolist()
        ref = np.array(transliterated(s, pssmdt.DEFAULT_LG))
        ours = pssmdt.pssm_dt(np.array(s), pssmdt.DEFAULT_LG)
        worst = max(worst, float(np.max(np.abs(ref - ours) / np.maximum(1.0, np.abs(ref)))))
        n += 1
    res = {"pssms": n, "LG": pssmdt.DEFAULT_LG, "max_relative_difference": worst, "passed": worst < 1e-12}
    Path(out).write_text(json.dumps(res, indent=1) + "\n")
    print(res)
    sys.exit(0 if res["passed"] else 1)


if __name__ == "__main__":
    main(*sys.argv[1:3])
