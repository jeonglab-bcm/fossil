"""Check our transcription (af2_matrix.txt) of Additional File 2 against the TIFF glyph by glyph.
Every glyph is compared with the mean image of all glyphs transcribed as the same character;
a transcription error shows up as a glyph closer to another character's mean.
Usage: check_af2.py S2.tiff af2_matrix.txt"""
import sys
import numpy as np
from PIL import Image
im = np.array(Image.open(sys.argv[1]).convert('L')).astype(float)
lines = [l.split() for l in open(sys.argv[2])]
ink = im < 160
def runs(mask):
    out, s = [], None
    for x, v in enumerate(mask):
        if v and s is None: s = x
        if not v and s is not None: out.append((s, x)); s = None
    if s is not None: out.append((s, len(mask)))
    return out
bands = runs(ink.any(1))
assert len(bands) == 21, bands
aa = 'ARNDCQEGHILKMFPSTWYV'
G, L = [], []
for bi, (y0, y1) in enumerate(bands):
    exp = ['A'] if bi == 0 else [lines[bi-1][0]] + [c for t in lines[bi-1][1:] for c in t] + ([aa[bi]] if bi < 20 else [])
    band = ink[y0:y0 + 14]
    rs = runs(band.any(0))
    assert len(rs) == len(exp), (bi, len(rs), len(exp))
    for (x0, x1), ch in zip(rs, exp):
        g = np.zeros((16, 16)); sub = (255 - im[y0:y0 + 16, x0:x1]) / 255.
        g[:, :min(16, sub.shape[1])] = sub[:, :16]
        G.append(g.ravel()); L.append(ch)
G, L = np.array(G), np.array(L)
T = {c: G[L == c].mean(0) for c in set(L)}
dist = lambda g, c: np.abs(g - T[c]).sum()
bad = [(i, c) for i, (g, c) in enumerate(zip(G, L)) if min(T, key=lambda k: dist(g, k)) != c]
print(f'{len(G)} glyphs, {len(bad)} closer to another character than to their own'
      + ''.join(f'; glyph {i} written as {c!r}' for i, c in bad))
sys.exit(1 if bad else 0)
