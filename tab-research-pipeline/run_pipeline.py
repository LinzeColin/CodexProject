from pathlib import Path

from tab_research.boards import board_by_id
from tab_research.io import single_instance_lock
from tab_research.paths import resolve_output_dir, resolve_workspace_root
from tab_research.pipeline import write_outputs


ROOT = resolve_workspace_root(Path(__file__))
OUT = resolve_output_dir(Path(__file__))
BOARD = board_by_id("world_cup_matches")
RAW = OUT / BOARD.raw_snapshot
PREVIOUS_BASELINE = OUT / "previous_report_baseline_v0_10.json"
PUBLIC_SOURCE_AUDIT = OUT / "public_source_audit_v0_11.json"
EVENT_AUDIT = OUT / "event_monitor_v0_11.json"
LOCK_PATH = OUT / ".tab_fifa_daily_report.lock"


if __name__ == "__main__":
    with single_instance_lock(LOCK_PATH):
        result = write_outputs(
            RAW,
            OUT,
            version=BOARD.version,
            previous_baseline_path=PREVIOUS_BASELINE,
            public_source_audit_path=PUBLIC_SOURCE_AUDIT,
            event_audit_path=EVENT_AUDIT,
        )
    print(f"recommendations={len(result['recommendations'])}")
    print(f"automation_ready={result['automation_gate']['automation_ready']}")
    print(f"daily_compare={result['daily_compare']['summary']}")
