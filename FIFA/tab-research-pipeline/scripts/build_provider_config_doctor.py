#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path


PIPELINE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PIPELINE_ROOT))

from tab_research.paths import resolve_output_dir
from tab_research.provider_config_doctor import write_provider_config_doctor_bundle


OUTPUT_DIR = resolve_output_dir(Path(__file__))


def main() -> None:
    payload = write_provider_config_doctor_bundle(OUTPUT_DIR, PIPELINE_ROOT)
    artifacts = payload.get("artifacts") or {}
    summary = payload.get("summary") or {}
    print(
        json.dumps(
            {
                "status": payload.get("status"),
                "json": artifacts.get("json"),
                "markdown": artifacts.get("markdown"),
                "pdf": artifacts.get("pdf"),
                "issue_count": summary.get("issue_count"),
                "legacy_sport_count": summary.get("legacy_sport_count"),
                "next_safe_action": summary.get("next_safe_action"),
                "current_executable_new_stake_aud": payload.get("current_executable_new_stake_aud", 0),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
