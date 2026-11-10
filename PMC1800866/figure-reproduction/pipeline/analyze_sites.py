#!/usr/bin/env python3
"""Tables 1-3 and Figs 1-2: zinc sites of the zinc-binding chains of Additional file 1.

A site is a zinc ion with at least one residue of the chain within 3 A (donor atoms N, O, S);
its type is the number of coordinating residues in the chain (Zn1..Zn4; more than four counts as
Zn4). Ligands come from today's mmCIF files (parse_structures.py), not from the supplement, so
N, Q and residues the profile filter dropped are counted too.

Usage: analyze_sites.py SUPPLEMENT_DIR STRUCT_DIR OUT_DIR [side_chain|any]
(side_chain, the default: only side-chain donors of C, H, D, E, N, Q; any: every N, O, S atom)
Writes sites.tsv, tables.json (Tables 1-3, Fig. 2 counts, the check of our ligands against the
supplement's positive residues) and fig1.tsv (the two curves of Fig. 1).
"""
import csv
import json
import math
import sys
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

import numpy as np

AA = ["C", "H", "D", "E", "N", "Q"]
# Side-chain donor atoms of the six residue types Table 2 lists. Table 2's total (1,492) is the
# sum of the site sizes, so a residue type outside these six was not counted as a ligand.
SIDE_CHAIN_DONORS = {"C": {"SG"}, "H": {"ND1", "NE2"}, "D": {"OD1", "OD2"}, "E": {"OE1", "OE2"},
                     "N": {"OD1", "ND2"}, "Q": {"OE1", "NE2"}}


def read_supplement(sup):
    rows = defaultdict(set)
    for f in sorted(Path(sup).glob("C*_*")):
        for line in open(f):
            cls, chain, pos, aa, cof = line.split()[:5]
            rows[chain].add((int(pos), aa, int(cls), cof))
    return rows


def load(sup, struct, donors="side_chain"):
    chains = {r["chain"]: r for r in csv.DictReader(open(Path(struct) / "chains.tsv"), delimiter="\t")}
    lig = defaultdict(lambda: defaultdict(dict))
    for r in csv.DictReader(open(Path(struct) / "ligands.tsv"), delimiter="\t"):
        if donors == "side_chain" and r["atom"] not in SIDE_CHAIN_DONORS.get(r["aa"], ()):
            continue
        lig[r["chain"]][r["zinc"]][int(r["pos"])] = r["aa"]
    return read_supplement(sup), chains, lig


def site_type(n):
    return min(n, 4)


def patterns(site):
    """Table 3 patterns matched by one site: ligand letters in sequence order and their gaps."""
    pos = sorted(site)
    aas = [site[p] for p in pos]
    gaps = [b - a - 1 for a, b in zip(pos, pos[1:])]
    n = len(pos)
    out = set()
    for name, alphabet in (("CHDE", set("CHDE")), ("CH", set("CH")), ("C", set("C")), ("DE", set("DE"))):
        if all(a in alphabet for a in aas):
            out.add(f"[{name}]x{n}")
    if all(a in set("CHDE") for a in aas) and n >= 2:
        sl = "".join("S" if g <= 7 else "L" for g in gaps)
        out.add(sl)
    return out


TABLE3 = [  # pattern key, printed label, N in the paper, Type column
    ("[CHDE]x4", "[CHDE] x(.) [CHDE] x(.) [CHDE] x(.) [CHDE]", 232, ""),
    ("[CH]x4", "[CH] x(.) [CH] x(.) [CH] x(.) [CH]", 196, ""),
    ("S?S", "[CHDE] x(0-7) [CHDE] x(.) [CHDE] x(0-7) [CHDE]", 161, ""),
    ("SLS", "[CHDE] x(0-7) [CHDE] x(>7) [CHDE] x(0-7) [CHDE]", 141, "SLS"),
    ("[CHDE]x3", "[CHDE] x(.) [CHDE] x(.) [CHDE]", 122, ""),
    ("[C]x4", "[C] x(.) [C] x(.) [C] x(.) [C]", 85, ""),
    ("[CHDE]x2", "[CHDE] x(.) [CHDE]", 62, ""),
    ("SL", "[CHDE] x(0-7) [CHDE] x(>7) [CHDE]", 55, "SL"),
    ("[CH]x3", "[CH] x(.) [CH] x(.) [CH]", 37, ""),
    ("LS", "[CHDE] x(>7) [CHDE] x(0-7) [CHDE]", 24, "LS"),
    ("[CH]x2", "[CH] x(.) [CH]", 21, ""),
    ("SLL", "[CHDE] x(0-7) [CHDE] x(>7) [CHDE] x(>7) [CHDE]", 17, "SLL"),
    ("LSS", "[CHDE] x(>7) [CHDE] x(0-7) [CHDE] x(0-7) [CHDE]", 16, "LSS"),
    ("[DE]x2", "[DE] x(.) [DE]", 15, ""),
    ("[DE]x3", "[DE] x(.) [DE] x(.) [DE]", 10, ""),
    ("LLS", "[CHDE] x(>7) [CHDE] x(>7) [CHDE] x(0-7) [CHDE]", 10, "LLS"),
    ("SSL", "[CHDE] x(0-7) [CHDE] x(0-7) [CHDE] x(>7) [CHDE]", 8, "SSL"),
    ("[DE]x4", "[DE] x(.) [DE] x(.) [DE] x(.) [DE]", 1, ""),
]


def matches(key, pats):
    if key == "S?S":
        return "SLS" in pats or "SSS" in pats
    return key in pats


def has_semipattern(site):
    pos = sorted(p for p, a in site.items() if a in "CHDE")
    return any(0 <= b - a - 1 <= 7 for a, b in combinations(pos, 2))


def fig1(seqs, bound, residues, dmax=1000, offset=1):
    """Fig. 1 curves over the residues of ``residues`` in the zinc chains, for d = 1..dmax.

    (a) P(X bound) and P(X bound | Y bound) over the pairs (X, Y) within separation d (the
        legend's Pr(X=bonded|Y=bonded)); ``neighbour`` is the other reading, P(X bound | some
        other bound residue within d), kept as a control;
    (b) correlation between the binding states of the pairs of residues within separation d.
    Separation is |i - j| - ``offset``: with offset 1 it is the number of residues between the two
    (the reading that matches the published curve); with offset 0 it is the index difference."""
    n_pos = n_all = 0
    m_count = np.zeros(dmax + 2)   # residues whose nearest other bound residue is at separation s
    m_bound = np.zeros(dmax + 2)   # ... of which bound
    pairs = np.zeros((dmax + 2, 4))  # pair counts by separation: n, sum a, sum a*b, sum a^2 (a=b symmetric)
    for c, seq in seqs.items():
        idx = np.array([i for i, a in enumerate(seq) if a in residues])
        if len(idx) == 0:
            continue
        y = np.array([1 if i in bound[c] else 0 for i in idx])
        n_pos += y.sum()
        n_all += len(y)
        sep = np.abs(idx[:, None] - idx[None, :]) - offset
        np.fill_diagonal(sep, 10 ** 9)
        sb = np.where(y[None, :] == 1, sep, 10 ** 9).min(axis=1)
        for s_, yy in zip(sb, y):
            if s_ <= dmax:
                m_count[max(s_, 0)] += 1
                m_bound[max(s_, 0)] += yy
        iu = np.triu_indices(len(idx), 1)
        sp = np.clip(sep[iu], 0, None)
        keep = sp <= dmax
        a, b = y[iu[0]][keep], y[iu[1]][keep]
        np.add.at(pairs[:, 0], sp[keep], 1)
        np.add.at(pairs[:, 1], sp[keep], a + b)
        np.add.at(pairs[:, 2], sp[keep], 2 * a * b)
    prior = n_pos / n_all
    cc, cb, cp = np.cumsum(m_count), np.cumsum(m_bound), np.cumsum(pairs, axis=0)
    rows = []
    for d in range(1, dmax + 1):
        neighbour = cb[d] / cc[d] if cc[d] else float("nan")
        cond = cp[d, 2] / cp[d, 1] if cp[d, 1] else float("nan")
        # Pearson correlation of the two states over ordered pairs (symmetric, so both margins agree).
        n2 = 2 * cp[d, 0]
        if n2:
            m = cp[d, 1] / n2
            corr = (cp[d, 2] / n2 - m * m) / (m - m * m) if 0 < m < 1 else float("nan")
        else:
            corr = float("nan")
        rows.append((d, prior, cond, corr, neighbour))
    return rows


def main(sup, struct, out, donors="side_chain"):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    rows, chains, lig = load(sup, struct, donors)
    zinc_chains = sorted(c for c, r in rows.items() if any(cls == 1 for _, _, cls, _ in r))
    sites = []  # (chain, zinc, {pos: aa})
    for c in zinc_chains:
        for z, res in sorted(lig.get(c, {}).items()):
            if res:
                sites.append((c, z, dict(res)))
    with open(out / "sites.tsv", "w") as f:
        f.write("chain\tzinc\ttype\tligands\n")
        for c, z, s in sites:
            f.write(f"{c}\t{z}\tZn{site_type(len(s))}\t{' '.join(f'{s[p]}{p}' for p in sorted(s))}\n")

    # Table 1
    t1 = {f"Zn{k}": {"sites": 0, "chains": set()} for k in range(1, 5)}
    types_by_chain = defaultdict(set)
    for c, z, s in sites:
        k = site_type(len(s))
        t1[f"Zn{k}"]["sites"] += 1
        t1[f"Zn{k}"]["chains"].add(c)
        types_by_chain[c].add(k)
    combos = Counter()
    for c, ks in types_by_chain.items():
        for r in range(2, 5):
            for comb in combinations(range(1, 5), r):
                if set(comb) <= ks:
                    combos["{" + ",".join(map(str, comb)) + "}"] += 1
    table1 = {k: {"sites": v["sites"], "chains": len(v["chains"])} for k, v in t1.items()}
    table1["Any"] = {"sites": len(sites), "chains": len(types_by_chain)}
    table1["multiple_types"] = {k: combos.get(k, 0) for k in
                                ["{1,2}", "{1,3}", "{1,4}", "{2,3}", "{2,4}", "{3,4}", "{1,2,3}", "{1,2,4}", "{1,3,4}", "{2,3,4}", "{1,2,3,4}"]}

    # Table 2
    na = {t: Counter() for t in ["Zn4", "Zn3", "Zn2", "Zn1"]}
    for c, z, s in sites:
        for p, a in s.items():
            na[f"Zn{site_type(len(s))}"][a] += 1
    allc = Counter()
    for t in na:
        allc.update(na[t])
    table2 = {}
    for a in AA + ["other"]:
        row = {}
        for t in na:
            n = na[t][a] if a != "other" else sum(v for k, v in na[t].items() if k not in AA)
            tot = sum(na[t].values())
            alln = allc[a] if a != "other" else sum(v for k, v in allc.items() if k not in AA)
            row[t] = {"Na": n, "fa": round(100 * n / tot, 1) if tot else 0.0, "fs": round(100 * n / alln, 1) if alln else 0.0}
        row["All"] = allc[a] if a != "other" else sum(v for k, v in allc.items() if k not in AA)
        table2[a] = row
    table2["Total"] = {t: sum(na[t].values()) for t in na} | {"All": sum(allc.values())}

    # Table 3
    pats = [patterns(s) for _, _, s in sites]
    table3 = [{"pattern": label, "key": key, "type": typ, "paper": n, "ours": sum(1 for p in pats if matches(key, p))}
              for key, label, n, typ in TABLE3]

    # Fig. 2
    fig2 = {"sites": {}, "chains": {}}
    # A chain counts as covered when any of its sites holds the semi-pattern, and it is listed under
    # every site type it has: Fig. 2b shows 13 covered Zn1 chains, though no Zn1 site can hold it.
    chain_hit = defaultdict(bool)
    for c, z, s in sites:
        t = f"Zn{site_type(len(s))}"
        hit = has_semipattern(s)
        chain_hit[c] |= hit
        for key in ("Overall", t):
            d = fig2["sites"].setdefault(key, {"covered": 0, "not_covered": 0})
            d["covered" if hit else "not_covered"] += 1
    for key in ("Overall", "Zn4", "Zn3", "Zn2", "Zn1"):
        cs = [c for c in types_by_chain if key == "Overall" or int(key[2]) in types_by_chain[c]]
        fig2["chains"][key] = {"covered": sum(chain_hit[c] for c in cs), "not_covered": sum(not chain_hit[c] for c in cs)}

    # Our ligands against the supplement's positive residues.
    check = Counter()
    for c in zinc_chains:
        shift = int(chains[c]["shift"]) if c in chains else 0
        ours = {p for res in lig.get(c, {}).values() for p in res}
        for pos, aa, cls, cof in rows[c]:
            key = ("pos" if cls == 1 else "neg") + ("_in_ours" if pos + shift in ours else "_not_in_ours")
            check[key] += 1

    # Fig. 1, on the C and H residues of the zinc chains (the residue set is not stated; see notes).
    bound = defaultdict(set)
    for c, z, s in sites:
        bound[c].update(s)
    seqs = {c: chains[c]["sequence"] for c in zinc_chains if c in chains}
    variants = {"CH": (set("CH"), 1), "CH_index_difference": (set("CH"), 0),
                "CHDE": (set("CHDE"), 1), "all": (set("ACDEFGHIKLMNPQRSTVWYX"), 1)}
    with open(out / "fig1.tsv", "w") as f:
        f.write("residues\td\tprior\tconditional\tcorrelation\tneighbour\n")
        for name, (rs, off) in variants.items():
            for d, pr, co, cr, nb in fig1(seqs, bound, rs, offset=off):
                f.write(f"{name}\t{d}\t{pr:.5f}\t{co:.5f}\t{cr:.5f}\t{nb:.5f}\n")

    res = {"zinc_chains_in_supplement": len(zinc_chains), "zinc_chains_with_sites": len(types_by_chain),
           "table1": table1, "table2": table2, "table3": table3, "fig2": fig2,
           "supplement_check": dict(check)}
    json.dump(res, open(out / "tables.json", "w"), indent=1)
    print(json.dumps({k: res[k] for k in ("zinc_chains_in_supplement", "zinc_chains_with_sites", "table1", "fig2", "supplement_check")}, indent=None))
    for r in table3:
        print(r["paper"], r["ours"], r["pattern"])
    for a in table2:
        print(a, table2[a])


if __name__ == "__main__":
    main(*sys.argv[1:5])
