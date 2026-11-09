"""Fig. 2C: where the descriptors of the top four pairs occur on 1AKH chain A (MATa1).

Usage: akh_occurrences.py 1AKH.cif OUT.json

An occurrence of descriptor (a1, a2, lg) is a position j with residue a1 at j and a2 at j + lg
(lg = 1..5), the residue pairs that PSSM-DT's term S[j, a1] * S[j+lg, a2] weighs most when the
profile follows the sequence. A residue is in contact with DNA when any of its heavy atoms lies
within 4.5 A of a DNA heavy atom in the crystal structure (an assumption: the paper does not say
how it delimited the DNA-binding region). An occurrence is in the DNA-binding region when either
residue of the pair is in contact, and inside the contact span when both lie between the first
and last contacting residue.
"""
import json
import sys
from pathlib import Path

import numpy as np

PAIRS = ["RR", "RP", "PR", "AR"]
CUTOFF = 4.5


def atoms(cif):
    lines = Path(cif).read_text().splitlines()
    cols, rows, i = [], [], 0
    while i < len(lines):
        if lines[i].startswith("_atom_site."):
            while lines[i].startswith("_atom_site."):
                cols.append(lines[i].split(".", 1)[1].strip()); i += 1
            while i < len(lines) and lines[i].startswith(("ATOM", "HETATM")):
                rows.append(lines[i].split()); i += 1
            break
        i += 1
    c = {n: k for k, n in enumerate(cols)}
    out = []
    for r in rows:
        if r[c["pdbx_PDB_model_num"]] != "1" or r[c["type_symbol"]] == "H":
            continue
        out.append((r[c["label_asym_id"]], r[c["auth_asym_id"]], int(r[c["label_seq_id"]]) if r[c["label_seq_id"]] != "." else None,
                    r[c["label_comp_id"]], float(r[c["Cartn_x"]]), float(r[c["Cartn_y"]]), float(r[c["Cartn_z"]])))
    return out


def main(cif, out):
    A = atoms(cif)
    dna = np.array([a[4:] for a in A if a[1] in ("C", "D") and a[3] in ("DA", "DC", "DG", "DT")])
    prot = [a for a in A if a[1] == "A" and a[2] is not None]
    seq3 = {}
    mind = {}
    for a in prot:
        seq3[a[2]] = a[3]
        d = float(np.min(np.linalg.norm(dna - np.array(a[4:]), axis=1)))
        mind[a[2]] = min(mind.get(a[2], 1e9), d)
    contact = {k for k, d in mind.items() if d <= CUTOFF}
    three = {"ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C", "GLN": "Q", "GLU": "E", "GLY": "G",
             "HIS": "H", "ILE": "I", "LEU": "L", "LYS": "K", "MET": "M", "PHE": "F", "PRO": "P", "SER": "S",
             "THR": "T", "TRP": "W", "TYR": "Y", "VAL": "V"}
    entity = "KKEKSPKGKSSISPQARAFLEEVFRRKQSLNSKEKEEVAKKCGITPLQVRVWFINKRMRSK"
    lo, hi = min(contact), max(contact)
    occ = []
    for p in PAIRS:
        for lg in range(1, 6):
            for j in range(len(entity) - lg):
                if entity[j] == p[0] and entity[j + lg] == p[1]:
                    i1, i2 = j + 1, j + 1 + lg
                    occ.append({"pair": p, "lg": lg, "positions": [i1, i2],
                                "modelled": i1 in seq3 and i2 in seq3,
                                "min_distance_to_dna_A": round(min(mind.get(i1, 1e9), mind.get(i2, 1e9)), 2),
                                "contacts_dna": (i1 in contact) or (i2 in contact),
                                "inside_contact_span": lo <= i1 and i2 <= hi})
    res = {"chain_length": len(entity), "modelled_residues": [min(seq3), max(seq3)],
           "dna_contact_residues": sorted(contact), "contact_span": [lo, hi], "cutoff_A": CUTOFF,
           "occurrences": occ,
           "descriptors": [f"{o['pair']}{o['lg']}" for o in occ],
           "in_binding_region": sum(o["contacts_dna"] for o in occ),
           "outside_binding_region": sum(not o["contacts_dna"] for o in occ)}
    assert all(three[seq3[k]] == entity[k - 1] for k in seq3)
    Path(out).write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps({k: v for k, v in res.items() if k != "occurrences"}))
    for o in occ:
        print(o)


if __name__ == "__main__":
    main(*sys.argv[1:3])
