"""Write the runtime versions of the run as JSON.  env_versions.py OUT.json"""
import json
import platform
import subprocess
import sys

import matplotlib
import numpy
import openpyxl
import pdfplumber
import PIL

import mutbench

try:
    poppler = subprocess.run(["pdftotext", "-v"], capture_output=True, text=True).stderr.splitlines()[0]
except (OSError, IndexError):
    poppler = None
json.dump({"python": platform.python_version(), "numpy": numpy.__version__, "openpyxl": openpyxl.__version__,
           "pdfplumber": pdfplumber.__version__, "pillow": PIL.__version__, "matplotlib": matplotlib.__version__,
           "mutbench": mutbench.__version__, "pdftotext": poppler, "platform": platform.machine()},
          open(sys.argv[1], "w"), indent=1)
