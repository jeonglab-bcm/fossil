"""Additional File 2 (the ASH substitution matrix) against BLOSUM62, AAindex2 and Additional File 4.

Usage: matrices.py AF2.txt BLOSUM62 blosum62_3.blast aaindex2 AF4.tiff OUTDIR
Writes OUTDIR/matrices.json and OUTDIR/af4_overlay.png.
"""
import itertools
import json
import re
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

af2_path, b62_path, b62_3_path, aaindex_path, af4_path, outdir = sys.argv[1:7]
AA = 'ARNDCQEGHILKMFPSTWYV'
TRI = np.tril_indices(20)


def read_af2(path):
    m = np.full((20, 20), np.nan)
    for i, line in enumerate(open(path)):
        f = line.split()
        assert f[0] == AA[i] and len(f) == i + 2
        for j, v in enumerate(f[1:]):
            m[i, j] = m[j, i] = float(v)
    return m


def read_blast_matrix(path):
    """NCBI layout; rows may or may not start with the residue letter."""
    lines = [l for l in open(path) if not l.startswith('#') and l.strip()]
    cols = lines[0].split()
    m = np.full((20, 20), np.nan)
    for r, line in zip(cols, lines[1:]):
        f = line.split()
        if f[0] in cols and not re.fullmatch(r'-?\d+', f[0]):
            f = f[1:]
        if r in AA:
            for c, v in zip(cols, f):
                if c in AA:
                    m[AA.index(r), AA.index(c)] = float(v)
    assert not np.isnan(m).any()
    return m


def read_aaindex2(path):
    """AAindex2 entries as symmetric 20x20 matrices (non-symmetric ones averaged with their transpose)."""
    entries, cur = {}, None
    for line in open(path):
        tag = line[:2]
        if tag == 'H ':
            cur = {'id': line[2:].strip(), 'desc': '', 'rows': []}
        elif tag == 'D ':
            cur['desc'] += line[2:].strip() + ' '
        elif tag == 'M ':
            m = re.match(r'M rows = (\S+), cols = (\S+)', line)
            cur['r'], cur['c'] = m.groups()
        elif line.startswith('//'):
            entries[cur['id']] = cur
        elif line.startswith('  ') and cur is not None and 'r' in cur:
            cur['rows'].append(line.split())
    out = {}
    for k, e in entries.items():
        raw = np.full((len(e['r']), len(e['c'])), np.nan)
        for i, row in enumerate(e['rows']):
            for j, v in enumerate(row):
                try:
                    raw[i, j] = float(v)
                except ValueError:
                    pass
        full = all(len(r) == len(e['c']) for r in e['rows'])
        s = np.full((20, 20), np.nan)
        for a in range(20):
            for b in range(a + 1):
                ia, ib = e['r'].index(AA[a]), e['c'].index(AA[b])
                v, vt = raw[ia, ib], raw[e['r'].index(AA[b]), e['c'].index(AA[a])]
                v = np.nanmean([v, vt]) if full else (vt if np.isnan(v) else v)   # triangles follow the entry's own order
                s[a, b] = s[b, a] = v
        out[k] = {'matrix': s, 'desc': e['desc'].strip()}
    return out


af2 = read_af2(af2_path)
b62 = read_blast_matrix(b62_path)
b62_3 = read_blast_matrix(b62_3_path)
result = {}

# BLOSUM62: the paper reports slope .52 and correlation .94 for the matrix plotted in AF4.
for name, b in [('blosum62_third_bit', b62_3), ('blosum62_half_bit', b62)]:
    x, y = b[TRI], af2[TRI]
    slope, icpt = np.polyfit(x, y, 1)
    result[name] = {'slope': round(float(slope), 3), 'intercept': round(float(icpt), 3),
                    'r': round(float(np.corrcoef(x, y)[0, 1]), 3)}

# AAindex2: the paper reports 98 entries, Gonnet best by dot product (.89), SDM best by RMSD (.13).
aaindex = read_aaindex2(aaindex_path)
usable = {k: v for k, v in aaindex.items() if not np.isnan(v['matrix'][TRI]).any() and np.ptp(v['matrix'][TRI]) > 0}


def unit(v):
    c = v - v.mean()
    return c / np.linalg.norm(c)


a = unit(af2[TRI])
ranked = sorted(((float(a @ unit(v['matrix'][TRI])), k) for k, v in usable.items()), reverse=True)
result['aaindex2'] = {
    'entries': len(aaindex), 'entries_without_missing_values': len(usable),
    'normalization': 'lower triangle with diagonal (210 values), centred on its mean, scaled to unit length',
    'top5_dot_product': [{'id': k, 'dot': round(d, 3), 'desc': usable[k]['desc'][:80]} for d, k in ranked[:5]],
    'gonnet_GONG920101': {'rank': [k for _, k in ranked].index('GONG920101') + 1,
                          'dot': round(dict((k, d) for d, k in ranked)['GONG920101'], 3)},
    'sdm_PRLA000101': {'rank': [k for _, k in ranked].index('PRLA000101') + 1,
                       'dot': round(dict((k, d) for d, k in ranked)['PRLA000101'], 3)},
}

# Other readings of "centering and normalizing": does any give Gonnet on top by dot product and
# SDM on top by RMSD, at .89 and .13?
sets = {'lower_210': TRI, 'full_400': tuple(np.indices((20, 20)).reshape(2, -1)), 'off_diagonal_190': np.tril_indices(20, -1)}
scales = {'unit_length': lambda v: v / np.linalg.norm(v), 'std': lambda v: v / v.std(),
          'max_abs': lambda v: v / np.abs(v).max(), 'range': lambda v: v / (v.max() - v.min())}
grid = []
for (sn, idx), (cn, scn) in itertools.product(sets.items(), itertools.product(['mean', 'none'], scales)):
    def norm(v):
        v = v - v.mean() if cn == 'mean' else v
        return scales[scn](v)
    x = norm(af2[idx])
    rows = [(k, float(x @ norm(v['matrix'][idx])) / len(x) if scn != 'unit_length' else float(x @ norm(v['matrix'][idx])),
             float(np.sqrt(np.mean((x - norm(v['matrix'][idx])) ** 2)))) for k, v in usable.items()]
    bd, br = max(rows, key=lambda t: t[1]), min(rows, key=lambda t: t[2])
    grid.append({'elements': sn, 'centre': cn, 'scale': scn, 'best_dot': [bd[0], round(bd[1], 3)],
                 'best_rmsd': [br[0], round(br[2], 3)]})
result['aaindex2']['normalization_grid'] = grid
result['aaindex2']['grid_matches_paper'] = any(g['best_dot'][0] == 'GONG920101' and g['best_rmsd'][0] == 'PRLA000101' for g in grid)

# Additional File 4: map its axes from the frame and ticks, read the black markers at
# BLOSUM62 (1/3 bit) >= 6, which are all diagonal elements, and draw AF2 on the same axes.
img = Image.open(af4_path).convert('RGB')
px = np.asarray(img).astype(int)
dark = px.sum(2) < 200
hl = np.where(dark.sum(1) > 0.6 * px.shape[1])[0]
vl = np.where(dark.sum(0) > 0.6 * px.shape[0])[0]
top, bottom = hl[hl < px.shape[0] / 2].mean(), hl[hl > px.shape[0] / 2].mean()
left, right = vl[vl < px.shape[1] / 2].mean(), vl[vl > px.shape[1] / 2].mean()
X0, X1, Y0, Y1 = -6, 20, -3, 10        # axis limits printed on the figure
to_px = lambda x, y: (left + (x - X0) / (X1 - X0) * (right - left), bottom - (y - Y0) / (Y1 - Y0) * (bottom - top))
to_data = lambda cx, cy: (X0 + (cx - left) / (right - left) * (X1 - X0), Y0 + (bottom - cy) / (bottom - top) * (Y1 - Y0))
black = (px[..., 0] < 90) & (px[..., 1] < 90) & (px[..., 2] < 90)
black[:int(top) + 8] = black[int(bottom) - 8:] = False
black[:, :int(left) + 8] = black[:, int(right) - 8:] = False
lab, n = ndimage.label(black)
markers = []
for i, sl in enumerate(ndimage.find_objects(lab), 1):
    h, w = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
    if 15 <= h <= 20 and 15 <= w <= 20:          # a single, unmerged circle
        cy, cx = ndimage.center_of_mass(lab == i)
        markers.append(to_data(cx, cy))
diag = {}
for k in range(20):
    x = b62_3[k, k]
    if sum(b62_3[j, j] == x for j in range(20)) == 1:  # unique BLOSUM62 value: one residue
        found = [m for m in markers if abs(m[0] - x) < 0.1]
        if len(found) == 1:
            diag[AA[k] + AA[k]] = {'blosum62_third_bit': x, 'af4': round(found[0][1], 2), 'af2': af2[k, k]}
result['af4'] = {'axes_px': {'left': left, 'right': right, 'top': top, 'bottom': bottom},
                 'x_marker_offsets': round(float(max(abs(m[0] - round(m[0])) for m in markers)), 3),
                 'diagonal_with_unique_x': diag}

draw = ImageDraw.Draw(img)
for i, j in zip(*TRI):
    cx, cy = to_px(b62_3[i, j], af2[i, j])
    draw.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], outline=(255, 140, 0), width=3)
img.save(f'{outdir}/af4_overlay.png')
json.dump(result, open(f'{outdir}/matrices.json', 'w'), indent=1)
print(json.dumps({k: v for k, v in result.items() if k != 'aaindex2'}, indent=1))
print(json.dumps({k: v for k, v in result['aaindex2'].items() if k != 'normalization_grid'}, indent=1))
