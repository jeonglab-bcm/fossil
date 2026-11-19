"""Write the runtime versions of the run as JSON.  env_versions.py OUT.json"""
import json
import platform
import sys

import numpy

import rommeta

json.dump({"python": platform.python_version(), "numpy": numpy.__version__, "rommeta": rommeta.__version__,
           "platform": platform.machine()}, open(sys.argv[1], "w"), indent=1)
