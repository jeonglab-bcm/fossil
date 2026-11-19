#!/usr/bin/env python3
"""The acute cholecystitis example of the Discussion, on our dataset and our CITATION_PLUS_MESH scores.

Usage: topic.py PMIDS.txt DATA_DIR OUT.json
"""
import json
import sys

import numpy as np

pm_file, data_dir, out = sys.argv[1:4]
pm = np.array([int(l) for l in open(pm_file) if l.strip() and not l.startswith("#")])
z = np.load(f"{data_dir}/all_scores.npz")
sel = np.isin(z["pmid"], pm)
rct, conf = z["rct"][sel], z["confidence"][sel]
un = ~rct
res = {"query_pmids": int(len(pm)), "in_dataset": int(sel.sum()), "with_rct_pt": int(rct.sum()),
       "without_rct_pt": int(un.sum()), "without_rct_pt_le_0.10": int((un & (conf <= 0.10)).sum()),
       "without_rct_pt_gt_0.10": int((un & (conf > 0.10)).sum())}
json.dump(res, open(out, "w"), indent=1)
print(res)
