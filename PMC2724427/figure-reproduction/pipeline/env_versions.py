"""Write the runtime versions of the run (Python, R and the pinned packages) as JSON.  env_versions.py OUT"""
import json
import platform
import subprocess
import sys

import numpy
import PIL
import scipy

r = subprocess.run(["Rscript", "-e", 'cat(paste(R.version$major, R.version$minor, sep = "."), '
                    'as.character(packageVersion("lokern")), as.character(packageVersion("logitbias")))'],
                   capture_output=True, text=True)
rv = (r.stdout.split() + [None] * 3)[:3]
json.dump({"python": platform.python_version(), "numpy": numpy.__version__, "scipy": scipy.__version__,
           "pillow": PIL.__version__, "R": rv[0], "lokern": rv[1], "logitbias": rv[2],
           "machine": platform.machine()}, open(sys.argv[1], "w"), indent=1)
