"""Static Phase 1 runtime defaults.

The values here are intentionally small and local. Real source, mail, TTS,
video, and GitHub automation configuration belongs to later phases.
"""

from __future__ import annotations

DEFAULT_RECIPIENT = "linzezhang35@gmail.com"
DEFAULT_TIMEZONE = "Australia/Sydney"
PROJECT_NAME = "arXiv Daily Push"
MIN_VIDEO_TTS_FREE_DISK_GIB = 80
PHASE1_REQUIRED_COMMANDS = ("python3", "git")
FUTURE_RUNTIME_COMMANDS = ("node", "npm", "gh", "ffmpeg", "docker")


def runtime_parameters() -> dict[str, object]:
    return {
        "project": PROJECT_NAME,
        "recipient": DEFAULT_RECIPIENT,
        "timezone": DEFAULT_TIMEZONE,
        "min_video_tts_free_disk_gib": MIN_VIDEO_TTS_FREE_DISK_GIB,
        "phase1_required_commands": list(PHASE1_REQUIRED_COMMANDS),
        "future_runtime_commands": list(FUTURE_RUNTIME_COMMANDS),
        "paid_api_allowed": False,
        "real_email_send_enabled": False,
    }

