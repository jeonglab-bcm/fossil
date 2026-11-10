#!/usr/bin/env python3
"""Read the PDB chains of Additional file 1 from their mmCIF files.

For every chain named in the supplement this writes its SEQRES sequence, and for every zinc
ion in the entry the residues of that chain whose donor atoms (N, O, S) lie within 3 A of it
(the paper's cutoff). Positions are 0-based SEQRES indices, the numbering the supplement uses.

Usage: parse_structures.py SUPPLEMENT_DIR CIF_DIR OUT_DIR
Writes chains.tsv (chain, entry, auth chain, sequence, the offset from the supplement's
positions to today's SEQRES and the letters that still differ) and ligands.tsv (chain, zinc id,
SEQRES index, residue, atom, distance).
"""
import gzip
import sys
from pathlib import Path

import gemmi

CUTOFF = 3.0
DONORS = {"N", "O", "S"}


def supplement_chains(sup):
    chains = {}
    for f in sorted(Path(sup).glob("C*_*")):
        for line in open(f):
            cls, chain, pos, aa, cof = line.split()[:5]
            chains.setdefault(chain, set()).add((int(pos), aa, cls, cof))
    return chains


def read_entry(cif_dir, entry):
    """The entry's structure; for obsolete entries archived without a sequence table, the
    PDB-format file of the obsolete archive (which keeps SEQRES)."""
    pdb = Path(cif_dir) / f"{entry.lower()}.pdb.gz"
    if pdb.exists():
        st = gemmi.read_structure(str(pdb))
    else:
        doc = gemmi.cif.read_string(gzip.open(Path(cif_dir) / f"{entry.lower()}.cif.gz", "rt").read())
        st = gemmi.make_structure_from_block(doc.sole_block())
    st.setup_entities()
    return st


def best_shift(seq, rows):
    """Offset that makes most supplement letters match the SEQRES sequence. Remediation since
    2005 added or removed leading residues (acetyl caps, tags) in a few entries."""
    def hits(o):
        return sum(1 for p, aa, _, _ in rows if 0 <= p + o < len(seq) and seq[p + o] == aa)
    return max(range(-60, 61), key=lambda o: (hits(o), -abs(o)))


def seqres_map(st, auth_chain):
    """SEQRES sequence of a chain and a map from (seqnum, icode) to the 0-based SEQRES index."""
    model = st[0]
    ch = model.find_chain(auth_chain)
    if ch is None:
        return None, None
    poly = ch.get_polymer()
    ent = st.get_entity_of(poly)
    if ent is None or not ent.full_sequence:
        return None, None
    seq = gemmi.one_letter_code([gemmi.Entity.first_mon(m) for m in ent.full_sequence])
    if all(res.label_seq is None for res in poly):
        st.assign_label_seq_id(False)  # PDB-format input: align residues to SEQRES
    index = {}
    for res in poly:
        if res.label_seq is not None:
            index[(res.seqid.num, res.seqid.icode)] = res.label_seq - 1
    return seq.upper(), index


def pick_chain(st, code):
    names = [c.name for c in st[0] if c.get_polymer().length() > 0]
    if code != "_" and code in names:
        return code
    if code == "_":
        # Chains without an identifier became "A" (or the only chain) on remediation.
        return "A" if "A" in names else (names[0] if names else None)
    return None


def main(sup, cif_dir, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    chains = supplement_chains(sup)
    entries = sorted({c[:4] for c in chains})
    rows, lig_rows, problems = [], [], []
    for e in entries:
        st = read_entry(cif_dir, e)
        st.remove_alternative_conformations()
        model = st[0]
        zincs = [(c.name, r, a) for c in model for r in c for a in r if a.element.name == "Zn"]
        for chain in sorted(c for c in chains if c[:4] == e):
            auth = pick_chain(st, chain[4:])
            seq, index = seqres_map(st, auth) if auth else (None, None)
            if seq is None:
                problems.append(f"{chain}\tno polymer chain")
                continue
            # Check the supplement's residue letters against the SEQRES sequence.
            bad = sum(1 for p, aa, _, _ in chains[chain] if p >= len(seq) or seq[p] != aa)
            shift = best_shift(seq, chains[chain]) if bad else 0
            bad_after = sum(1 for p, aa, _, _ in chains[chain] if not (0 <= p + shift < len(seq) and seq[p + shift] == aa))
            rows.append((chain, e, auth, seq, len(chains[chain]), bad, shift, bad_after))
            for zc, zr, za in zincs:
                zid = f"ZN_{zr.seqid.num}_{zc}"
                # Asymmetric unit only: no crystal symmetry mates.
                for res in model[auth]:
                    key = (res.seqid.num, res.seqid.icode)
                    if key not in index:
                        continue
                    for atom in res:
                        if atom.element.name not in DONORS:
                            continue
                        d = atom.pos.dist(za.pos)
                        if d <= CUTOFF:
                            lig_rows.append((chain, zid, index[key], seq[index[key]], atom.name, f"{d:.3f}"))
    with open(out / "chains.tsv", "w") as f:
        f.write("chain\tentry\tauth_chain\tsequence\tsupplement_rows\tletter_mismatches\tshift\tmismatches_after_shift\n")
        for r in rows:
            f.write("\t".join(map(str, r)) + "\n")
    with open(out / "ligands.tsv", "w") as f:
        f.write("chain\tzinc\tpos\taa\tatom\tdistance\n")
        for r in lig_rows:
            f.write("\t".join(map(str, r)) + "\n")
    with open(out / "parse_problems.tsv", "w") as f:
        f.write("\n".join(problems) + ("\n" if problems else ""))
    print(f"{len(rows)} chains, {len(lig_rows)} ligand atoms, {len(problems)} problems")


if __name__ == "__main__":
    main(*sys.argv[1:4])
