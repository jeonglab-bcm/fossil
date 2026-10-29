"""CATH 3.0.0 and SCOP 1.69 for the paper's training set.

Rebuilds the paper's equivalence step (a CATH and a SCOP domain of the same PDB entry are
equivalent when they share 75% or more of the residues of the larger one), classifies the
2,911 training domains of Additional File 1 by CATH topology and SCOP fold, counts the
queries that have a template with the same topology and fold (the paper: 1,641), and checks
the 69 rows of Additional File 3 against both classifications.

Residues are counted from the PDB residue numbers in the domain boundary files; insertion
codes are ignored, so a range counts end - start + 1 residues.

Usage: cath_scop.py CATH_DIR SCOP_DIR AF1.txt AF3.csv OUT.json
"""
import collections
import csv
import json
import re
import sys

cath_dir, scop_dir, af1_path, af3_path, out_path = sys.argv[1:6]


def read_cath_list(path):
    dom = {}
    for line in open(path):
        if line.startswith('#'):
            continue
        f = line.split()
        dom[f[0]] = {'topology': '.'.join(f[1:4]), 'superfamily': '.'.join(f[1:5]), 'length': int(f[10])}
    return dom


def read_cath_boundaries(path):
    """Domain name -> list of (chain, start, end); chain name -> list of all (chain, start, end)."""
    dom, chain_segs = {}, {}
    for line in open(path):
        if line.startswith('#') or not line.strip():
            continue
        f = line.split()
        name, nd, nf = f[0], int(f[1][1:]), int(f[2][1:])
        k = 3
        segs_all = []
        for d in range(1, nd + 1):
            nseg = int(f[k]); k += 1
            segs = []
            for _ in range(nseg):
                c, s, si, c2, e, ei = f[k:k + 6]; k += 6
                segs.append((c, int(s), int(e)))
            dom['%s%02d' % (name, d)] = segs
            segs_all += segs
        for _ in range(nf):
            c, s, si, c2, e, ei, nr = f[k:k + 7]; k += 7
            segs_all.append((c, int(s), int(e)))
        assert k == len(f), line
        if nd == 1 and nf == 0 and name + '01' in dom:
            dom[name + '00'] = dom.pop(name + '01')   # whole-chain domains are named ...00
        chain_segs[name] = segs_all
    return dom, chain_segs


RANGE = re.compile(r'^(?:([A-Za-z0-9]):)?(-?\d+)[A-Za-z]?-(-?\d+)[A-Za-z]?$')


def read_scop(path):
    dom = {}
    for line in open(path):
        if line.startswith('#'):
            continue
        sid, pdb, region, sccs, px, hier = line.rstrip('\n').split('\t')
        h = dict(kv.split('=') for kv in hier.split(','))
        parts = []
        for p in region.split(','):
            if p == '-':
                parts.append(('*', None, None))
            elif re.fullmatch(r'[A-Za-z0-9]:', p):
                parts.append((p[0], None, None))
            else:
                m = RANGE.match(p)
                assert m, (sid, region)
                parts.append((m.group(1) or '0', int(m.group(2)), int(m.group(3))))
        dom[sid] = {'pdb': pdb, 'parts': parts, 'fold': h['cf'], 'sccs': sccs,
                    'fold_sccs': '.'.join(sccs.split('.')[:2])}
    return dom


def residues(segs):
    return {(c, r) for c, s, e in segs for r in range(s, e + 1)}


cath = read_cath_list(f'{cath_dir}/cath-domain-list-v3_0_0.txt')
bounds, chain_segs = read_cath_boundaries(f'{cath_dir}/cath-domain-boundaries-v3_0_0.txt')
scop = read_scop(f'{scop_dir}/dir.cla.scop.1.69.txt')

chains_of = collections.defaultdict(set)
for ch in chain_segs:
    chains_of[ch[:4]].add(ch[4])


def scop_residues(d):
    """Residue set of a SCOP domain; whole chains and whole entries take CATH's chain extents."""
    out = set()
    for c, s, e in d['parts']:
        if c == '*':
            for c2 in chains_of[d['pdb']]:
                out |= residues(chain_segs[d['pdb'] + c2])
        elif s is None:
            if d['pdb'] + c in chain_segs:
                out |= residues(chain_segs[d['pdb'] + c])
        else:
            out |= residues([(c, s, e)])
    return out


scop_by_pdb = collections.defaultdict(list)
for sid, d in scop.items():
    scop_by_pdb[d['pdb']].append(sid)

common = set(scop_by_pdb) & {n[:4] for n in cath}
compared = [n for n in cath if n[:4] in common and n in bounds]
scop_res = {}
equivalent, equivalent_smaller, closest = {}, set(), {}
for n in compared:
    a = residues(bounds[n])
    best = None
    for sid in scop_by_pdb[n[:4]]:
        if sid not in scop_res:
            scop_res[sid] = scop_residues(scop[sid])
        b = scop_res[sid]
        shared = len(a & b)
        if not b:
            continue
        if shared >= 0.75 * min(len(a), len(b)):      # the other reading: 75% of the smaller domain
            equivalent_smaller.add(n)
        if shared >= 0.75 * max(len(a), len(b)):      # the paper's rule: 75% of the larger domain
            if best is None or shared > best[1]:
                best = (sid, shared)
        if n not in closest or shared / max(len(a), len(b)) > closest[n][1]:
            closest[n] = (sid, round(shared / max(len(a), len(b)), 3))
    if best:
        equivalent[n] = best[0]

af1 = [l.strip() for l in open(af1_path) if l.strip()]
missing = [d for d in af1 if d not in equivalent]
topo = {d: cath[d]['topology'] for d in af1}
fold = {d: scop[equivalent[d]]['fold'] for d in af1 if d in equivalent}

by_pair = collections.Counter((topo[d], fold[d]) for d in af1 if d in fold)
by_topo = collections.Counter(topo[d] for d in af1)
by_fold = collections.Counter(fold[d] for d in af1 if d in fold)
with_true = [d for d in af1 if d in fold and by_pair[(topo[d], fold[d])] > 1]

# The same count for every pairing of CATH level (architecture, topology, superfamily) with
# SCOP level (fold, superfamily, family).
by_level = {}
for cl, cn in (('architecture', 2), ('topology', 3), ('superfamily', 4)):
    for sl, sn in (('fold', 2), ('superfamily', 3), ('family', 4)):
        key = {d: ('.'.join(cath[d]['superfamily'].split('.')[:cn]),
                   '.'.join(scop[equivalent[d]]['sccs'].split('.')[:sn])) for d in af1 if d in equivalent}
        n = collections.Counter(key.values())
        by_level[f'cath_{cl}+scop_{sl}'] = sum(n[k] > 1 for k in key.values())
with_true_cath = [d for d in af1 if by_topo[topo[d]] > 1]
with_true_scop = [d for d in af1 if d in fold and by_fold[fold[d]] > 1]


def relation(q, t):
    same_t = topo.get(q, cath[q]['topology']) == cath[t]['topology']
    fq, ft = fold.get(q), (scop[equivalent[t]]['fold'] if t in equivalent else None)
    same_f = None if fq is None or ft is None else fq == ft
    return same_t, same_f


rows = list(csv.reader(open(af3_path)))[2:]
af3 = []
for r in rows:
    q, fp, tn = r[0], r[2], r[8]
    af3.append({
        'query': q, 'fp': fp, 'tn': tn,
        'in_training_set': [x in set(af1) for x in (q, fp, tn)],
        'fp_same_topology_fold': relation(q, fp),
        'tn_same_topology_fold': relation(q, tn),
        'nres_listed': [int(float(r[1])), int(float(r[3])), int(float(r[9]))],
        'nres_cath': [cath[x]['length'] for x in (q, fp, tn)],
        'fp_score_above_tn': float(r[7]) > float(r[13]),
        'fp_score': float(r[7]), 'tn_score': float(r[13]),
    })

summary = {
    'cath_domains': len(cath),
    'scop_domains': len(scop),
    'pdb_entries_in_both': len(common),
    'cath_domains_compared': len(compared),
    'scop_domains_compared': sum(len(scop_by_pdb[p]) for p in common),
    'cath_domains_equivalent': len(equivalent),
    'af1_domains': len(af1),
    'af1_unique': len(set(af1)),
    'af1_in_cath_3_0_0': sum(d in cath for d in af1),
    'af1_without_scop_equivalent': {d: {'closest_scop_domain': closest[d][0], 'shared_fraction_of_larger': closest[d][1]}
                                    for d in missing},
    'cath_domains_equivalent_75pct_of_smaller': len(equivalent_smaller),
    'af1_without_scop_equivalent_75pct_of_smaller': [d for d in af1 if d not in equivalent_smaller],
    'af1_cath_topologies': len(by_topo),
    'af1_scop_folds': len(by_fold),
    'queries_with_same_topology_and_fold_template': len(with_true),
    'queries_with_template_by_level': by_level,
    'queries_with_same_topology_template': len(with_true_cath),
    'queries_with_same_fold_template': len(with_true_scop),
    'af3_rows': len(af3),
    'af3_all_in_training_set': all(all(x['in_training_set']) for x in af3),
    'af3_fp_differs_in_both': sum(x['fp_same_topology_fold'] == (False, False) for x in af3),
    'af3_tn_same_in_both': sum(x['tn_same_topology_fold'] == (True, True) for x in af3),
    'af3_fp_score_above_tn': sum(x['fp_score_above_tn'] for x in af3),
    'af3_nres_equal_cath_length': sum(a == b for x in af3 for a, b in zip(x['nres_listed'], x['nres_cath'])),
    'af3_queries_with_same_topology_and_fold_template': sum(x['query'] in set(with_true) for x in af3),
}
json.dump({'summary': summary, 'af3': af3}, open(out_path, 'w'), indent=1)
print(json.dumps(summary, indent=1))
