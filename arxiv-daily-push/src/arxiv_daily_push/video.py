"""Phase 8 storyboard and video dry-run media gate."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .config import MIN_VIDEO_TTS_FREE_DISK_GIB
from .contracts import stable_content_hash, validate_storyboard
from .doctor import command_status, disk_status
from .narration import validate_narration_plan


VIDEO_REQUIRED_COMMANDS = ("ffmpeg",)


class VideoPlanError(ValueError):
    """Raised when storyboard or video planning would create unsafe media output."""


def video_media_gate(path: Path | None = None) -> dict[str, Any]:
    commands = [command_status(command) for command in VIDEO_REQUIRED_COMMANDS]
    missing_commands = [item["command"] for item in commands if not item["available"]]
    disk = disk_status(path)
    real_video_ready = not missing_commands and bool(disk["free_gib"] >= MIN_VIDEO_TTS_FREE_DISK_GIB)
    return {
        "dry_run_ready": True,
        "real_video_ready": real_video_ready,
        "video_render_allowed": False,
        "media_write_allowed": False,
        "asset_download_allowed": False,
        "required_commands": commands,
        "missing_commands": missing_commands,
        "disk": disk,
        "blocking_reasons": [] if real_video_ready else _real_video_blockers(missing_commands, disk),
    }


def generate_storyboard(
    narration: Mapping[str, Any],
    *,
    generated_at: str,
    path: Path | None = None,
) -> dict[str, Any]:
    narration_errors = validate_narration_plan(narration, _lesson_stub_from_narration(narration))
    if narration_errors:
        raise VideoPlanError("; ".join(narration_errors))
    scenes = [_scene_from_segment(segment, index) for index, segment in enumerate(narration["segments"])]
    storyboard = {
        "storyboard_id": f"storyboard:{narration['lesson_id']}:{stable_content_hash({'scenes': scenes})[:12]}",
        "lesson_id": narration["lesson_id"],
        "scenes": scenes,
        "constraints": {
            "dry_run_only": True,
            "video_render_allowed": False,
            "media_write_allowed": False,
            "asset_download_allowed": False,
            "style": "high-contrast 2D explainer draft",
            "media_gate": video_media_gate(path),
        },
        "generated_at": generated_at,
    }
    errors = validate_storyboard_against_narration(storyboard, narration)
    if errors:
        raise VideoPlanError("; ".join(errors))
    return storyboard


def validate_storyboard_against_narration(storyboard: Mapping[str, Any], narration: Mapping[str, Any]) -> list[str]:
    errors = validate_storyboard(storyboard)
    if storyboard.get("lesson_id") != narration.get("lesson_id"):
        errors.append("Storyboard.lesson_id must match Narration.lesson_id")
    scenes = storyboard.get("scenes")
    segments = narration.get("segments")
    if isinstance(scenes, list) and isinstance(segments, list) and len(scenes) != len(segments):
        errors.append("Storyboard.scenes length must match Narration.segments length")
    narration_claim_ids = {str(claim_id) for claim_id in narration.get("claim_ids", [])}
    if isinstance(scenes, list):
        for index, scene in enumerate(scenes):
            if not isinstance(scene, Mapping):
                errors.append(f"Storyboard.scenes[{index}] must be an object")
                continue
            scene_claim_ids = {str(claim_id) for claim_id in scene.get("claim_ids", [])}
            if not scene_claim_ids:
                errors.append(f"Storyboard.scenes[{index}].claim_ids must be non-empty")
            if not scene_claim_ids.issubset(narration_claim_ids):
                errors.append(f"Storyboard.scenes[{index}].claim_ids must be a subset of Narration.claim_ids")
            if scene.get("media_path") or scene.get("asset_path"):
                errors.append(f"Storyboard.scenes[{index}] media paths are forbidden in dry-run mode")
    constraints = storyboard.get("constraints")
    if not isinstance(constraints, Mapping):
        errors.append("Storyboard.constraints must be an object")
    else:
        for key in ("video_render_allowed", "media_write_allowed", "asset_download_allowed"):
            if constraints.get(key) is not False:
                errors.append(f"Storyboard.constraints.{key} must be false in Phase 8")
    return errors


def _scene_from_segment(segment: Mapping[str, Any], index: int) -> dict[str, Any]:
    claim_ids = list(segment["claim_ids"])
    return {
        "scene_id": f"scene-{index + 1:02d}",
        "duration_sec": int(segment["duration_estimate_sec"]),
        "narration": segment["text"],
        "visual_plan": f"2D explainer board for {segment['section_id']} using text callouts only; no external assets.",
        "claim_ids": claim_ids,
    }


def _lesson_stub_from_narration(narration: Mapping[str, Any]) -> dict[str, Any]:
    segments = narration.get("segments", [])
    sections = []
    if isinstance(segments, list):
        for segment in segments:
            if isinstance(segment, Mapping):
                sections.append(
                    {
                        "section_id": segment.get("section_id", ""),
                        "title": segment.get("section_id", "section"),
                        "body": segment.get("text", ""),
                        "claim_ids": segment.get("claim_ids", []),
                    }
                )
    return {
        "lesson_id": narration.get("lesson_id", ""),
        "source_item_id": narration.get("lesson_id", ""),
        "language": narration.get("language", "zh-CN"),
        "title": "Narration source lesson",
        "sections": sections,
        "claim_ids": narration.get("claim_ids", []),
        "generated_at": narration.get("generated_at", ""),
    }


def _real_video_blockers(missing_commands: list[str], disk: Mapping[str, Any]) -> list[str]:
    blockers = ["real video rendering disabled in Phase 8"]
    if missing_commands:
        blockers.append("missing video runtime commands: " + ", ".join(missing_commands))
    if not disk.get("video_tts_ready"):
        blockers.append("free disk below video/TTS threshold")
    return blockers
