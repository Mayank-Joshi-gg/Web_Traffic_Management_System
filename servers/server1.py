import runpy
import sys

sys.argv = ["server.py", "5001"]
runpy.run_path("servers/server.py", run_name="__main__")
