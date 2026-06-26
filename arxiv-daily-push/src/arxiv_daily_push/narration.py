"""Phase 7 narration script and TTS dry-run gate."""

from __future__ import annotations

from collections.abc import Mapping
from math import ceil
from pathlib import Path
from typing import Any

from .config import TTS_REQUIRED_COMMANDS
from .contracts import stable_content_hash, validate_lesson
from .doctor import command_status, disk_status


DEFAULT_TTS_MODE = "dry_run"
CHARS_PER_SECOND = 5
MIN_SEGMENT_SECONDS = 5


class NarrationError(ValueError):
    """Raised when narration generation would cross the dry-run boundary."""


def tts_resource_gate(path: Path | None = None) -> dict[str, Any]:
    commands = [command_status(command) for command in TTS_REQUIRED_COMMANDS]
    missing_commands = [item["command"] for item in commands if not item["available"]]
    disk = disk_status(path)
    real_tts_ready = not missing_commands and bool(disk["video_tts_ready"])
    return {
        "tts_mode": DEFAULT_TTS_MODE,
        "dry_run_ready": True,
        "real_tts_ready": real_tts_ready,
        "audio_synthesis_allowed": False,
        "model_download_allowed": False,
        "audio_write_allowed": False,
        "required_commands": commands,
        "missing_commands": missing_commands,
        "disk": disk,
        "blocking_reasons": [] if real_tts_ready else _real_tts_blockers(missing_commands, disk),
    }


def generate_narration_plan(
    lesson: Mapping[str, Any],
    *,
    generated_at: str,
    tts_mode: str = DEFAULT_TTS_MODE,
    path: Path | None = None,
) -> dict[str, Any]:
    if tts_mode != DEFAULT_TTS_MODE:
        raise NarrationError("Phase 7 only permits dry_run narration; real TTS synthesis remains blocked")
    errors = validate_lesson(lesson)
    if errors:
        raise NarrationError("; ".join(errors))
    segments = [_segment_from_section(section, index) for index, section in enumerate(lesson["sections"])]
    narration = {
        "narration_id": f"narration:{lesson['lesson_id']}:{stable_content_hash({'segments': segments})[:12]}",
        "lesson_id": lesson["lesson_id"],
        "lesson_key": lesson["lesson_key"],
        "lesson_revision_id": lesson["lesson_revision_id"],
        "language": lesson["language"],
        "tts_mode": tts_mode,
        "audio_synthesis_allowed": False,
        "segments": segments,
        "claim_ids": list(lesson["claim_ids"]),
        "resource_gate": tts_resource_gate(path),
        "generated_at": generated_at,
    }
    validation_errors = validate_narration_plan(narration, lesson)
    if validation_errors:
        raise NarrationError("; ".join(validation_errors))
    return narration


def validate_narration_plan(narration: Mapping[str, Any], lesson: Mapping[str, Any]) -> list[str]:
    errors = validate_lesson(lesson)
    if narration.get("lesson_id") != lesson.get("lesson_id"):
        errors.append("Narration.lesson_id must match Lesson.lesson_id")
    if narration.get("tts_mode") != DEFAULT_TTS_MODE:
        errors.append("Narration.tts_mode must be dry_run in Phase 7")
    if narration.get("audio_synthesis_allowed") is not False:
        errors.append("Narration.audio_synthesis_allowed must be false in Phase 7")
    lesson_claim_ids = {str(claim_id) for claim_id in lesson.get("claim_ids", [])}
    narration_claim_ids = {str(claim_id) for claim_id in narration.get("claim_ids", [])}
    if narration_claim_ids != lesson_claim_ids:
        errors.append("Narration.claim_ids must equal Lesson.claim_ids")
    segments = narration.get("segments")
    if not isinstance(segments, list) or not segments:
        errors.append("Narration.segments must be a non-empty array")
    elif isinstance(lesson.get("sections"), list) and len(segments) != len(lesson["sections"]):
        errors.append("Narration.segments length must match Lesson.sections length")
    if isinstance(segments, list):
        for index, segment in enumerate(segments):
            if not isinstance(segment, Mapping):
                errors.append(f"Narration.segments[{index}] must be an object")
                continue
            if segment.get("audio_path"):
                errors.append(f"Narration.segments[{index}].audio_path is forbidden in dry_run mode")
            segment_claim_ids = {str(claim_id) for claim_id in segment.get("claim_ids", [])}
            if not segment_claim_ids:
                errors.append(f"Narration.segments[{index}].claim_ids must be non-empty")
            if not segment_claim_ids.issubset(lesson_claim_ids):
                errors.append(f"Narration.segments[{index}].claim_ids must be a subset of Lesson.claim_ids")
    gate = narration.get("resource_gate")
    if not isinstance(gate, Mapping):
        errors.append("Narration.resource_gate must be an object")
    elif gate.get("audio_write_allowed") is not False or gate.get("model_download_allowed") is not False:
        errors.append("Narration.resource_gate must block audio writes and model downloads in Phase 7")
    return errors


def _segment_from_section(section: Mapping[str, Any], index: int) -> dict[str, Any]:
    body = str(section["body"]).strip()
    text = f"{section['title']}。{body}"
    return {
        "segment_id": f"seg-{index + 1:02d}",
        "section_id": section["section_id"],
        "text": text,
        "duration_estimate_sec": max(MIN_SEGMENT_SECONDS, ceil(len(text) / CHARS_PER_SECOND)),
        "claim_ids": list(section["claim_ids"]),
    }


def _real_tts_blockers(missing_commands: list[str], disk: Mapping[str, Any]) -> list[str]:
    blockers = ["real TTS synthesis disabled in Phase 7"]
    if missing_commands:
        blockers.append("missing TTS runtime commands: " + ", ".join(missing_commands))
    if not disk.get("video_tts_ready"):
        blockers.append("free disk below video/TTS threshold")
    return blockers
