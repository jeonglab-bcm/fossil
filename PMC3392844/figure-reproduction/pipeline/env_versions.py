"""Write the runtime versions of the run as JSON.  env_versions.py OUT.json"""
import json
import platform
import sys

import matplotlib
import numpy
import PIL
import scipy
import sklearn

import adrfusion

json.dump({"python": platform.python_version(), "numpy": numpy.__version__, "scipy": scipy.__version__,
           "scikit-learn": sklearn.__version__, "matplotlib": matplotlib.__version__, "pillow": PIL.__version__,
           "adrfusion": adrfusion.__version__, "platform": platform.machine()},
          open(sys.argv[1], "w"), indent=1)
