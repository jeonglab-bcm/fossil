#!/usr/bin/env python3
"""Add the Python, Pillow and NumPy versions to the env.json written by env_versions.R.

Usage: env_versions_py.py ENV_JSON
"""
import json
import sys

import numpy
import PIL

path = sys.argv[1]
env = json.load(open(path))
env.update({"python": sys.version.split()[0], "pillow": PIL.__version__, "numpy": numpy.__version__})
json.dump(env, open(path, "w"), indent=2)
