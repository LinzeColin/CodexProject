from pathlib import Path

from tab_research.australia_markets import generate_australia_report
from tab_research.boards import board_by_id
from tab_research.io import single_instance_lock
from tab_research.paths import resolve_output_dir, resolve_workspace_root


ROOT = resolve_workspace_root(Path(__file__))
OUT = resolve_output_dir(Path(__file__))
BOARD = board_by_id("world_cup_australia_markets")
RAW = OUT / BOARD.raw_snapshot
VERSION = BOARD.version
LOCK_PATH = OUT / ".tab_fifa_daily_report.lock"


def main() -> None:
    with single_instance_lock(LOCK_PATH):
        result = generate_australia_report(RAW, OUT, version=VERSION)
        print(
            {
                "automation_ready": result["automation_gate"]["automation_ready"],
                "manual_report_ready": result["automation_gate"]["manual_report_ready"],
                "market_count": result["market_count"],
                "priced_market_count": result["priced_market_count"],
                "recommendations": len(result["recommendations"]),
            }
        )


if __name__ == "__main__":
    main()
