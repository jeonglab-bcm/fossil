"""Write the runtime versions of the run (Python and the pinned packages) as JSON.  env_versions.py OUT"""
import json
import platform
import sys

import matplotlib
import numpy
import PIL
import scipy

json.dump({"python": platform.python_version(), "numpy": numpy.__version__, "scipy": scipy.__version__,
           "pillow": PIL.__version__, "matplotlib": matplotlib.__version__}, open(sys.argv[1], "w"), indent=1)
