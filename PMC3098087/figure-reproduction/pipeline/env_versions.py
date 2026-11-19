"""Write the runtime versions of the run as JSON.  env_versions.py OUT.json"""
import json
import platform
import subprocess
import sys

import PIL
import pymupdf

r = subprocess.run(["Rscript", "-e", "pk <- c('multds', 'class', 'randomForest', 'e1071', 'pamr', 'stepPlr', 'Hmisc', 'jsonlite'); "
                    "cat(R.version$major, '.', R.version$minor, '\\n', sep = ''); for (p in pk) cat(p, as.character(packageVersion(p)), '\\n')"],
                   capture_output=True, text=True, check=True)
lines = r.stdout.split("\n")
env = {"python": platform.python_version(), "pymupdf": pymupdf.__version__, "pillow": PIL.__version__,
       "R": lines[0].strip(), "platform": platform.machine()}
for ln in lines[1:]:
    if ln.strip():
        k, v = ln.split()
        env["R:" + k] = v
json.dump(env, open(sys.argv[1], "w"), indent=1)
