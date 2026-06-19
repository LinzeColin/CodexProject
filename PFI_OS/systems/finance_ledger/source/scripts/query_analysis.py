from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from econ_bleed_analyzer.query import main


if __name__ == "__main__":
    raise SystemExit(main())
