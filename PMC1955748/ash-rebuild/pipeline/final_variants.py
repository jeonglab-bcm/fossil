"""Variants of the final step of NER maximization, scored against Additional File 3 (TM-align seeds).

current: as in ash.ner_maximization. no_final_max: NER read at the superposition that produced the
realignment. gap_open_plus_ext: a gap of length L costs 0.25 + L x 0.125. iterate: superposition and
realignment repeated until the alignment stops changing (the 2005 paper says it does not iterate).

Usage: final_variants.py BOUNDARIES AF3.csv AF2_MATRIX CIF_DIR OUT.json
"""
import csv
import json
import sys

from concurrent.futures import ProcessPoolExecutor

import numpy as np

import ash
import domains
import ss
from tmseed import tm_pairs

bounds_path, af3_path, matrix_path, cif_dir, out_path = sys.argv[1:6]
B = domains.read_boundaries(bounds_path)
A = ash.read_matrix(matrix_path)
rows = list(csv.reader(open(af3_path)))[2:]
jobs = [(r[0], r[c], kind, dict(nres_q=int(r[1]), nres_t=int(r[c+1]), seqid=float(r[c+2]), ner=float(r[c+3]), sas=float(r[c+4]), score=float(r[c+5])))
        for r in rows for kind, c in (('fp', 2), ('tn', 8))]

def final(q, t, seed, variant):
    X, Y = q.ca, t.ca
    R, tr = ash.kabsch(X[seed[:, 0]], Y[seed[:, 1]])
    R, tr = ash.maximize_ner(X, Y, seed, R, tr)
    go, ge = (0.375, 0.125) if variant == 'gap_open_plus_ext' else (0.25, 0.125)
    pairs = ash.realign(X, Y, R, tr, go, ge)
    if variant == 'no_final_max':
        return pairs, R, tr
    if variant == 'iterate':
        for _ in range(10):
            R, tr = ash.maximize_ner(X, Y, pairs, R, tr)
            new = ash.realign(X, Y, R, tr, go, ge)
            if len(new) == len(pairs) and (new == pairs).all():
                break
            pairs = new
    R2, t2 = ash.maximize_ner(X, Y, pairs, R, tr)
    return pairs, R2, t2

def run(job):
    qn, tn, kind, pub = job
    doms = {n: domains.load_domain(n, B, cif_dir) for n in (qn, tn)}
    sss = {n: ss.assign(d.n, d.ca, d.c, d.o) for n, d in doms.items()}
    desc = {n: ash.descriptors(d, sss[n]) for n, d in doms.items()}
    seed = tm_pairs(doms[qn], doms[tn])
    out = {}
    for v in ['current', 'no_final_max', 'gap_open_plus_ext', 'iterate']:
        pairs, R, tr = final(doms[qn], doms[tn], seed, v)
        t = ash.score_terms(doms[qn], doms[tn], desc[qn], desc[tn], pairs, R, tr, A, ash.WEIGHTS['full'])
        D = np.array(t['d']); m = D < 8
        out[v] = dict(ner=t['ner'], ner_rel=t['ner_rel'], fseq=t['fseq'], gaps=t['gaps'], dist=t['dist'],
                      sas8=100 * np.sqrt((D[m] ** 2).mean()) / m.sum())
    return dict(pub=pub, **out)

if __name__ == '__main__':
    for pdb in sorted({n[:4] for job in jobs for n in job[:2]}):   # download once, before the workers start
        domains.fetch(pdb, cif_dir)
    with ProcessPoolExecutor(4) as ex:
        res = list(ex.map(run, jobs))
    json.dump(res, open(out_path, 'w'), separators=(',', ':'))
    w = ash.WEIGHTS['full']
    pub = lambda k: np.array([r['pub'][k] for r in res])
    for v in ['current', 'no_final_max', 'gap_open_plus_ext', 'iterate']:
        g = lambda k: np.array([r[v][k] for r in res])
        sc = w['ner'] * 100 * g('ner_rel') + w['seq'] * g('fseq') - w['sas'] * g('sas8') - w['gap'] * g('gaps') - w['dist'] * g('dist')
        print(f"{v:18s} NER r={np.corrcoef(g('ner'), pub('ner'))[0,1]:.3f} mean diff {np.mean(g('ner') - pub('ner')):+.2f} | "
              f"SAS r={np.corrcoef(g('sas8'), pub('sas'))[0,1]:.3f} | score r={np.corrcoef(sc, pub('score'))[0,1]:.3f}")
