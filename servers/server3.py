import sys
import runpy
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

sys.argv = ["server.py", "5003"]

runpy.run_path(
    str(PROJECT_ROOT / "servers" / "server.py"),
    run_name="__main__"
)
