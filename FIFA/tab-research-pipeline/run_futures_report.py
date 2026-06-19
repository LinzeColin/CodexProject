import json
from pathlib import Path

from tab_research.boards import board_by_id
from tab_research.futures import generate_futures_report
from tab_research.io import single_instance_lock
from tab_research.paths import resolve_output_dir, resolve_workspace_root


ROOT = resolve_workspace_root(Path(__file__))
OUT = resolve_output_dir(Path(__file__))
BOARD = board_by_id("world_cup_futures")
RAW = OUT / BOARD.raw_snapshot
VERSION = BOARD.version
LOCK_PATH = OUT / ".tab_fifa_daily_report.lock"


if __name__ == "__main__":
    with single_instance_lock(LOCK_PATH):
        result = generate_futures_report(RAW, OUT, version=VERSION)
        print(json.dumps({
            "version": VERSION,
            "automation_ready": result["automation_gate"]["automation_ready"],
            "team_count": result["team_count"],
            "recommendations": len(result["recommendations"]),
            "report": str(OUT / f"tab_fifa_world_cup_futures_{VERSION}_report.md"),
        }, indent=2))
