from pathlib import Path

from tab_research.io import atomic_write_json, single_instance_lock
from tab_research.paths import resolve_output_dir, resolve_workspace_root
from tab_research.public_sources import audit_sources


ROOT = resolve_workspace_root(Path(__file__))
OUTPUT_DIR = resolve_output_dir(Path(__file__))
OUT = OUTPUT_DIR / "public_source_audit_v0_11.json"
LOCK_PATH = OUTPUT_DIR / ".tab_fifa_daily_report.lock"


if __name__ == "__main__":
    with single_instance_lock(LOCK_PATH):
        result = audit_sources()
        atomic_write_json(OUT, result)
    print(f"wrote={OUT}")
    print(f"all_sources_ok={result['all_sources_ok']}")
    print(f"ok_count={result['ok_count']}/{result['source_count']}")
