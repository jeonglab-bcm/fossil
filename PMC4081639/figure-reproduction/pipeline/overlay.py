import sys, json
import numpy as np
from PIL import Image
sys.path.insert(0, ".")
from fit_render import fit, paper
fig, font, dpi = sys.argv[1], sys.argv[2], int(sys.argv[3])
extra = json.loads(sys.argv[4]) if len(sys.argv) > 4 else None
r, al = fit(fig, font, dpi, extra, keep=f"ov/fig{fig}")
P = paper(fig)
rgb = np.stack([P, al, al], -1).clip(0, 255).astype(np.uint8)
Image.fromarray(rgb).resize((P.shape[1] * 2, P.shape[0] * 2), Image.NEAREST).save(f"ov/fig{fig}_overlay.png")
Image.fromarray(al.clip(0, 255).astype(np.uint8)).save(f"ov/fig{fig}_ours.png")
print(json.dumps(r, default=int))
