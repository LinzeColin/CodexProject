from pathlib import Path

from tab_research.event_monitor import audit_event_feeds
from tab_research.io import atomic_write_json, single_instance_lock
from tab_research.paths import resolve_output_dir, resolve_workspace_root


ROOT = resolve_workspace_root(Path(__file__))
VERSION = "v0_11"
OUTPUT_DIR = resolve_output_dir(Path(__file__))
OUT = OUTPUT_DIR / f"event_monitor_{VERSION}.json"
LOCK_PATH = OUTPUT_DIR / ".tab_fifa_daily_report.lock"


if __name__ == "__main__":
    with single_instance_lock(LOCK_PATH):
        result = audit_event_feeds()
        atomic_write_json(OUT, result)
    print(f"wrote={OUT}")
    print(f"all_feeds_ok={result['all_feeds_ok']}")
    print(f"ok_count={result['ok_count']}/{result['feed_count']}")
    print(f"flagged_item_count={result['flagged_item_count']}")
