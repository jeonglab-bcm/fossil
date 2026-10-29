"""Cut CATH 3.0.0 domains out of PDB entries.

Each domain's segments come from cath-domain-boundaries-v3_0_0.txt, read with their insertion
codes, and are taken from the first model of the entry's mmCIF file in file order. A residue is
kept when it is an ATOM record (not HETATM) with a CA atom: this gives CATH's domain lengths, as
printed in Additional File 3, for 187 of its 190 domains (the other three differ by one residue).

Usage as a module: load_domain(name, boundaries, cif_dir) -> Domain
"""
import collections
import os
import urllib.request

import gemmi
import numpy as np

Domain = collections.namedtuple('Domain', 'name seq ca n c o')


def read_boundaries(path):
    """Domain name -> list of (chain, (start, icode), (end, icode))."""
    out = {}
    for line in open(path):
        if line.startswith('#') or not line.strip():
            continue
        f = line.split()
        name, nd, nf = f[0], int(f[1][1:]), int(f[2][1:])
        k, doms = 3, []
        for d in range(1, nd + 1):
            nseg = int(f[k]); k += 1
            segs = []
            for _ in range(nseg):
                c, s, si, _, e, ei = f[k:k + 6]; k += 6
                segs.append((c, (int(s), si.replace('-', ' ')), (int(e), ei.replace('-', ' '))))
            doms.append(segs)
        k += 7 * nf
        for d, segs in enumerate(doms, 1):
            out[name + ('00' if nd == 1 and nf == 0 else '%02d' % d)] = segs
    return out


def fetch(pdb, cif_dir):
    path = os.path.join(cif_dir, pdb + '.cif')
    if not os.path.exists(path):
        for url in (f'https://files.rcsb.org/download/{pdb}.cif',
                    f'https://files.rcsb.org/pub/pdb/data/structures/obsolete/mmCIF/{pdb[1:3]}/{pdb}.cif.gz'):
            try:
                data = urllib.request.urlopen(url, timeout=60).read()
            except Exception:
                continue
            if url.endswith('.gz'):
                import gzip
                data = gzip.decompress(data)
            tmp = path + '.part'
            open(tmp, 'wb').write(data)
            os.replace(tmp, path)          # never leave a half-written file for another reader
            break
        else:
            raise FileNotFoundError(pdb)
    return path


def load_domain(name, boundaries, cif_dir):
    st = gemmi.read_structure(fetch(name[:4], cif_dir))
    model = st[0]
    chains = {ch.name: ch for ch in model}
    res_all = []
    for c, start, end in boundaries[name]:
        if c == '0' or c not in chains:
            ch = next(ch for ch in model if any(gemmi.find_tabulated_residue(r.name) and
                                                 gemmi.find_tabulated_residue(r.name).is_amino_acid() for r in ch))
        else:
            ch = chains[c]
        residues = [r for r in ch if r.find_atom('CA', '*') and r.het_flag != 'H']
        key = [(r.seqid.num, r.seqid.icode) for r in residues]
        try:
            i, j = key.index(start), key.index(end)
        except ValueError:
            # boundary residue missing today: fall back to numeric range
            i = next(k for k, (n, _) in enumerate(key) if n >= start[0])
            j = max(k for k, (n, _) in enumerate(key) if n <= end[0])
        res_all += residues[i:j + 1]
    def coords(atom):
        out = []
        for r in res_all:
            a = r.find_atom(atom, '*')
            out.append([a.pos.x, a.pos.y, a.pos.z] if a else [np.nan] * 3)
        return np.array(out)
    seq = ''.join(gemmi.find_tabulated_residue(r.name).one_letter_code.upper()
                  if gemmi.find_tabulated_residue(r.name) else 'X' for r in res_all)
    return Domain(name, seq, coords('CA'), coords('N'), coords('C'), coords('O'))
