#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path


PIPELINE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PIPELINE_ROOT))

from tab_research.paths import resolve_output_dir, resolve_workspace_root

WORKSPACE_ROOT = resolve_workspace_root(Path(__file__))
OUTPUT_DIR = resolve_output_dir(Path(__file__))

from tab_research.automation_doctor import write_automation_doctor_bundle


def main() -> None:
    payload = write_automation_doctor_bundle(OUTPUT_DIR)
    artifacts = payload.get("artifacts") or {}
    summary = {
        "status": "ok",
        "json": artifacts.get("json"),
        "markdown": artifacts.get("markdown"),
        "pdf": artifacts.get("pdf"),
        "ready_to_enter_recurring_automation": (payload.get("executive_status") or {}).get(
            "ready_to_enter_recurring_automation"
        ),
        "primary_blocker": (payload.get("executive_status") or {}).get("primary_blocker"),
        "command_count": len(payload.get("command_queue") or []),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
