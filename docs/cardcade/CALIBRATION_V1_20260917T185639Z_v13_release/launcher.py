"""V13 non-authorizing release launcher identity; execution remains prohibited."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts.calibration_launcher_guard import validate_launcher
if __name__ == "__main__":
    raise SystemExit("V13 release packet only; execution_authorized is false")