"""Add the Python runtime and package versions to the run's environment record (env.json)."""
import json
import platform
import sys
from importlib.metadata import version

p = sys.argv[1]
env = json.load(open(p))
env["python"] = platform.python_version()
for k in ("numpy", "scipy", "pillow"):
    env[k] = version(k)
json.dump(env, open(p, "w"), indent=1)
