"""Optional local-only sample data (do NOT use in production)."""
from pathlib import Path
import sys
import runpy
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
runpy.run_path(str(ROOT / "backend" / "seed_demo.py"), run_name="__main__")
