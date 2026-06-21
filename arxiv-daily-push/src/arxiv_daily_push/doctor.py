"""Phase 1 readiness checks."""

from __future__ import annotations

import json
import platform
import shutil
import sys
from pathlib import Path

from .config import (
    FUTURE_RUNTIME_COMMANDS,
    MIN_VIDEO_TTS_FREE_DISK_GIB,
    PHASE1_REQUIRED_COMMANDS,
    runtime_parameters,
)


def command_status(command: str) -> dict[str, object]:
    path = shutil.which(command)
    return {"command": command, "available": path is not None, "path": path or ""}


def disk_status(path: Path | None = None) -> dict[str, object]:
    target = path or Path.cwd()
    usage = shutil.disk_usage(target)
    free_gib = round(usage.free / (1024**3), 2)
    return {
        "path": str(target),
        "free_gib": free_gib,
        "video_tts_min_free_gib": MIN_VIDEO_TTS_FREE_DISK_GIB,
        "video_tts_ready": free_gib >= MIN_VIDEO_TTS_FREE_DISK_GIB,
    }


def doctor_report(path: Path | None = None) -> dict[str, object]:
    required = [command_status(command) for command in PHASE1_REQUIRED_COMMANDS]
    future = [command_status(command) for command in FUTURE_RUNTIME_COMMANDS]
    missing_required = [item["command"] for item in required if not item["available"]]
    missing_future = [item["command"] for item in future if not item["available"]]
    disk = disk_status(path)
    status = "pass"
    if missing_required:
        status = "blocked"
    elif missing_future or not disk["video_tts_ready"]:
        status = "warn"
    return {
        "status": status,
        "phase": "1",
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "runtime_parameters": runtime_parameters(),
        "required_commands": required,
        "future_runtime_commands": future,
        "missing_required_commands": missing_required,
        "missing_future_runtime_commands": missing_future,
        "disk": disk,
        "notes": [
            "Phase 1 may proceed with status warn if required commands are available.",
            "TTS, video, GitHub automation, and real mail transport remain later-phase gates.",
        ],
    }


def render_report(report: dict[str, object], as_json: bool = False) -> str:
    if as_json:
        return json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
    lines = [
        f"status: {report['status']}",
        f"phase: {report['phase']}",
        f"python: {report['python']}",
        f"platform: {report['platform']}",
    ]
    disk = report["disk"]
    if isinstance(disk, dict):
        lines.append(f"disk_free_gib: {disk['free_gib']}")
        lines.append(f"video_tts_ready: {disk['video_tts_ready']}")
    return "\n".join(lines)

