"""Write the runtime versions of the run as JSON.  env_versions.py OUT.json"""
import json
import platform
import sys

import numpy
import PIL

import esrisk

json.dump({"python": platform.python_version(), "numpy": numpy.__version__, "pillow": PIL.__version__,
           "esrisk": esrisk.__version__, "platform": platform.machine()},
          open(sys.argv[1], "w"), indent=1)
