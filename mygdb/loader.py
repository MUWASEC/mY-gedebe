import sys, os

# add repo root (adjust relative path if needed)
here = os.path.dirname(__file__)
repo_root = os.path.abspath(os.path.join(here, ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

import mygdb
