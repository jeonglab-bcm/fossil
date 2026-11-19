#!/usr/bin/env python3
"""Record the versions of the runtimes and packages the run used into a JSON file."""
import json
import platform
import subprocess
import sys
from importlib import metadata


def cmd(*a):
    try:
        return subprocess.run(a, capture_output=True, text=True).stdout + subprocess.run(a, capture_output=True, text=True).stderr
    except FileNotFoundError:
        return ""


env = {"python": platform.python_version(), "machine": platform.machine()}
for p in ("numpy", "scipy", "pandas", "matplotlib", "pillow", "pysam", "openpyxl", "xlrd"):
    try:
        env[p] = metadata.version(p)
    except metadata.PackageNotFoundError:
        pass
b = cmd("bowtie", "--version").split("\n")[0].split()
env["bowtie"] = b[-1] if b else None
r = cmd("Rscript", "-e", 'cat(R.version$major, R.version$minor, as.character(packageVersion("edgeR")))').split()
if len(r) >= 3:
    env["R"] = f"{r[0]}.{r[1]}"
    env["edgeR"] = r[2]
json.dump(env, open(sys.argv[1], "w"), indent=1)
print(json.dumps(env))
