"""Align the 138 pairs of Additional File 3 with the rebuilt ASH and compare with the published values.

Usage: af3_test.py BOUNDARIES AF3.csv AF2_MATRIX CIF_DIR OUT.json [SEEDS]
SEEDS: tm (TM-align, default), ddp (rebuilt Local ASH) or both.
"""
import csv
import json
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import tmtools

import ash
import domains
import localash
import ss
from tmseed import tm_pairs

bounds_path, af3_path, matrix_path, cif_dir, out_path = sys.argv[1:6]
SEEDS = sys.argv[6] if len(sys.argv) > 6 else 'tm'


def align(q, t, ss_q, ss_t):
    res = tmtools.tm_align(q.ca, t.ca, q.seq, t.seq)
    seed = tm_pairs(q, t)
    if SEEDS == 'tm':
        pairs, R, tr = ash.ner_maximization(q.ca, t.ca, seed)
    else:
        _, pairs, R, tr = localash.rash(q, t, ss_q, ss_t, extra_seeds=[seed] if SEEDS == 'both' else [])
    return pairs, R, tr, float(res.tm_norm_chain1)


def run(job):
    qn, tn, kind, published = job
    B = domains.read_boundaries(bounds_path)
    A = ash.read_matrix(matrix_path)
    doms = {n: domains.load_domain(n, B, cif_dir) for n in (qn, tn)}
    sss = {n: ss.assign(d.n, d.ca, d.c, d.o) for n, d in doms.items()}
    desc = {n: ash.descriptors(d, sss[n]) for n, d in doms.items()}
    pairs, R, tr, tm = align(doms[qn], doms[tn], sss[qn], sss[tn])
    terms = ash.score_terms(doms[qn], doms[tn], desc[qn], desc[tn], pairs, R, tr, A, ash.WEIGHTS['full'])
    terms.update(query=qn, template=tn, kind=kind, tm_score=tm, published=published, seeds=SEEDS)
    return terms


rows = list(csv.reader(open(af3_path)))[2:]
jobs = []
for r in rows:
    for kind, c in (('fp', 2), ('tn', 8)):
        jobs.append((r[0], r[c], kind, dict(nres_q=int(r[1]), nres_t=int(r[c + 1]), seqid=float(r[c + 2]),
                                            ner=float(r[c + 3]), sas=float(r[c + 4]), score=float(r[c + 5]))))
for pdb in sorted({n[:4] for job in jobs for n in job[:2]}):   # download once, before the workers start
    domains.fetch(pdb, cif_dir)
with ProcessPoolExecutor(4) as ex:
    out = list(ex.map(run, jobs))
json.dump(out, open(out_path, 'w'), separators=(',', ':'))
print(len(out), 'pairs')
