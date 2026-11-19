#!/usr/bin/env python3
"""Turn extract_medline.py's manifest into the committed record: per baseline file, its SHA-256, the
records it holds and how many we keep.  manifest.py IN.json OUT.json"""
import json
import sys

m = json.load(open(sys.argv[1]))
json.dump({"source": "https://ftp.ncbi.nlm.nih.gov/pubmed/baseline/", "files": m}, open(sys.argv[2], "w"), indent=0)
