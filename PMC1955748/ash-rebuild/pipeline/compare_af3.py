"""Compare the rebuilt ASH with Additional File 3 and write the report.

Usage: compare_af3.py af3_pairs.json OUTDIR
Writes OUTDIR/af3_comparison.json, OUTDIR/af3_scatter.png and prints a Markdown report.
"""
import json
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

import ash

pairs_path, outdir = sys.argv[1:3]
d = json.load(open(pairs_path))
W = ash.WEIGHTS['full']
SAS_CUT = 8.0   # SAS over aligned pairs closer than this; the paper does not define the set

pub = lambda k: np.array([x['published'][k] for x in d])
ours = lambda k: np.array([x[k] for x in d])


def sas_within(x, cut=SAS_CUT):
    dd = np.array(x['d'])
    m = dd < cut
    return 100 * np.sqrt((dd[m] ** 2).mean()) / m.sum()


def score(ner_pct, fseq, sas, gaps, dist):
    return ash.ash_score(ner_pct / 100, fseq, sas, gaps, dist, W)


def stats(a, b):
    slope, icpt = np.polyfit(a, b, 1)
    return dict(r=round(float(np.corrcoef(a, b)[0, 1]), 3), median_abs_diff=round(float(np.median(abs(b - a))), 2),
                mean_diff=round(float((b - a).mean()), 2), fit_slope=round(float(slope), 3), fit_intercept=round(float(icpt), 2))


nq, nt = pub('nres_q'), pub('nres_t')
ner_pub, sas_pub, score_pub = pub('ner'), pub('sas'), pub('score')
sas_ours = np.array([sas_within(x) for x in d])
sas_all = ours('sas_fit')
fseq, gaps, dist = ours('fseq'), ours('gaps'), ours('dist')
f_pub_inputs = score(100 * ner_pub / ((nq + nt) / 2), fseq, sas_pub, gaps, dist)
f_ours = score(100 * ours('ner_rel'), fseq, sas_ours, gaps, dist)
f_fraction = score(ner_pub / ((nq + nt) / 2), fseq, sas_pub, gaps, dist)

result = {
    'pairs': len(d),
    'ner': stats(ner_pub, ours('ner')),
    'ner_ours_lower_by_more_than_10': int((ours('ner') - ner_pub < -10).sum()),
    'ner_ours_higher_by_more_than_10': int((ours('ner') - ner_pub > 10).sum()),
    'sas_all_aligned_pairs': stats(sas_pub, sas_all),
    f'sas_pairs_within_{SAS_CUT:g}A': stats(sas_pub, sas_ours),
    'seqid_over_aligned_pairs': stats(pub('seqid'), ours('seqid_aligned')),
    'score_formula_published_ner_sas_ner_rel_percent': stats(f_pub_inputs, score_pub),
    'score_formula_published_ner_sas_ner_rel_fraction': stats(f_fraction, score_pub),
    'score_formula_all_ours': stats(f_ours, score_pub),
}
q = sorted({x['query'] for x in d})
key = {(x['query'], x['kind']): k for k, x in enumerate(d)}
result['rows_fp_above_tn'] = {
    'published': int(sum(score_pub[key[(r, 'fp')]] > score_pub[key[(r, 'tn')]] for r in q)),
    'ours': int(sum(f_ours[key[(r, 'fp')]] > f_ours[key[(r, 'tn')]] for r in q)),
    'same_order': int(sum((f_ours[key[(r, 'fp')]] > f_ours[key[(r, 'tn')]]) ==
                          (score_pub[key[(r, 'fp')]] > score_pub[key[(r, 'tn')]]) for r in q)),
    'rows': len(q),
}
json.dump(result, open(f'{outdir}/af3_comparison.json', 'w'), indent=1)

# Four panels, one series each: ink points, a muted identity line, the fitted line in green.
INK, MUTED, GREEN, GRID = '#1f2a26', '#7b8b84', '#1f7a55', '#e3e8e4'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9, 'axes.edgecolor': MUTED,
                     'axes.labelcolor': INK, 'xtick.color': MUTED, 'ytick.color': MUTED})
fig, axes = plt.subplots(1, 4, figsize=(13, 3.5), constrained_layout=True)
panels = [
    (ner_pub, ours('ner'), 'NER, Additional File 3', 'NER, rebuilt', True, result['ner']),
    (sas_pub, sas_ours, 'SAS, Additional File 3', f'SAS, rebuilt (pairs < {SAS_CUT:g} Å)', True,
     result[f'sas_pairs_within_{SAS_CUT:g}A']),
    (f_pub_inputs, score_pub, 'Eq. 1 on published NER and SAS', 'Score, Additional File 3', False,
     result['score_formula_published_ner_sas_ner_rel_percent']),
    (f_ours, score_pub, 'Eq. 1, all terms rebuilt', 'Score, Additional File 3', False, result['score_formula_all_ours']),
]
for ax, (x, y, xl, yl, identity, st) in zip(axes, panels):
    ax.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    lo, hi = min(x.min(), y.min()), max(x.max(), y.max())
    if identity:
        ax.plot([lo, hi], [lo, hi], color=MUTED, linewidth=1, linestyle=(0, (4, 3)))
    xs = np.linspace(x.min(), x.max(), 2)
    ax.plot(xs, st['fit_slope'] * xs + st['fit_intercept'], color=GREEN, linewidth=2)
    ax.scatter(x, y, s=16, color=INK, alpha=0.75, edgecolors='white', linewidths=0.6)
    ax.set_xlabel(xl)
    ax.set_ylabel(yl)
    ax.set_title(f"r = {st['r']:.3f}", loc='left', fontsize=10, color=INK)
fig.savefig(f'{outdir}/af3_scatter.png', dpi=150)

r = result
print('# Rebuilt ASH against Additional File 3\n')
print(f"{r['pairs']} pairs: each of the 69 queries against its false positive and its true template.\n")
print('| Quantity | Correlation | Median difference | Note |')
print('| --- | --- | --- | --- |')
print(f"| NER | {r['ner']['r']} | {r['ner']['median_abs_diff']} | ours higher by {r['ner']['mean_diff']} on average; {r['ner_ours_lower_by_more_than_10']} pairs more than 10 lower, {r['ner_ours_higher_by_more_than_10']} more than 10 higher |")
print(f"| SAS, all aligned pairs | {r['sas_all_aligned_pairs']['r']} | {r['sas_all_aligned_pairs']['median_abs_diff']} | |")
print(f"| SAS, pairs within {SAS_CUT:g} Å | {r[f'sas_pairs_within_{SAS_CUT:g}A']['r']} | {r[f'sas_pairs_within_{SAS_CUT:g}A']['median_abs_diff']} | |")
print(f"| Sequence identity, % of aligned pairs | {r['seqid_over_aligned_pairs']['r']} | {r['seqid_over_aligned_pairs']['median_abs_diff']} | |")
s1, s0, s2 = r['score_formula_published_ner_sas_ner_rel_percent'], r['score_formula_published_ner_sas_ner_rel_fraction'], r['score_formula_all_ours']
print(f"| Score from eq. 1 on published NER and SAS, NER_rel in percent | {s1['r']} | | published = {s1['fit_slope']} x eq. 1 {s1['fit_intercept']:+} |")
print(f"| Same, NER_rel as a fraction | {s0['r']} | | |")
print(f"| Score from eq. 1, every term rebuilt | {s2['r']} | | published = {s2['fit_slope']} x eq. 1 {s2['fit_intercept']:+} |")
fr = r['rows_fp_above_tn']
print(f"\nFalse positive scoring above the true template: published {fr['published']} of {fr['rows']} rows, rebuilt {fr['ours']}; the same order in {fr['same_order']}.")

# Fail the run if the rebuild drifts: the score formula on published inputs, and our NER.
failures = []
if s1['r'] < 0.97:
    failures.append(f"eq. 1 on published NER and SAS: r = {s1['r']} (needs 0.97)")
if r['ner']['r'] < 0.95:
    failures.append(f"NER: r = {r['ner']['r']} (needs 0.95)")
print('\n## Check\n')
if failures:
    print('FAILED: ' + '; '.join(failures))
    sys.exit(1)
print('Eq. 1 on the published NER and SAS stays at r >= 0.97, and our NER at r >= 0.95.')
