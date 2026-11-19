"""Write the runtime versions of the run as JSON.  env_versions.py OUT.json"""
import json
import platform
import sys

import liblinear
import numpy
import scipy

import rctconf

try:
    from importlib.metadata import version
    ll = version("liblinear-official")
except Exception:  # pragma: no cover
    ll = getattr(liblinear, "__version__", "unknown")

json.dump({"python": platform.python_version(), "numpy": numpy.__version__, "scipy": scipy.__version__,
           "liblinear-official": ll, "rctconf": rctconf.__version__, "platform": platform.machine()},
          open(sys.argv[1], "w"), indent=1)
