"""Phase 8 storyboard and video dry-run media gate."""

from __future__ import annotations

import hashlib
import shutil
import subprocess
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from .config import MIN_VIDEO_TTS_FREE_DISK_GIB
from .contracts import stable_content_hash, validate_storyboard
from .doctor import command_status, disk_status
from .narration import validate_narration_plan


VIDEO_REQUIRED_COMMANDS = ("ffmpeg",)
REAL_MP4_RENDER_MODEL_ID = "adp-real-mp4-render-v1"

CommandResolver = Callable[[str], str | None]
CommandRunner = Callable[[Sequence[str]], Mapping[str, Any] | subprocess.CompletedProcess[str]]


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


def render_lightweight_mp4(
    daily_input: Mapping[str, Any],
    *,
    output_path: str | Path,
    generated_at: str,
    command_resolver: CommandResolver | None = None,
    command_runner: CommandRunner | None = None,
    duration_seconds: int = 12,
) -> dict[str, Any]:
    """Render a small MP4 title-card artifact without downloading assets.

    The generated video is intentionally lightweight. It is suitable for a
    GitHub Release link in the manual production-enablement path, while the
    Chinese lesson text remains in the email body.
    """

    resolver = command_resolver or shutil.which
    ffmpeg_path = resolver("ffmpeg")
    output = Path(output_path)
    transcript = _video_transcript(daily_input)
    report = _mp4_base_report(daily_input, output, generated_at, transcript, duration_seconds, bool(ffmpeg_path))
    if not ffmpeg_path:
        return _mp4_blocked(report, ["ffmpeg command is required for real MP4 rendering"])

    output.parent.mkdir(parents=True, exist_ok=True)
    text_path = output.with_suffix(".txt")
    text_path.write_text(transcript + "\n", encoding="utf-8")
    command = [
        ffmpeg_path,
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"color=c=0x111827:s=1280x720:r=25:d={int(duration_seconds)}",
        "-vf",
        f"drawtext=textfile={text_path}:fontcolor=white:fontsize=34:x=60:y=80:line_spacing=14",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(output),
    ]
    report["command"] = {
        "ffmpeg_required": True,
        "ffmpeg_available": True,
        "stdout_logged": False,
        "stderr_logged": False,
        "command_preview": ["ffmpeg", "-y", "-f", "lavfi", "-i", "color=...", "-vf", "drawtext=textfile=...", str(output)],
    }
    runner = command_runner or _run_command
    try:
        result = _normalize_command_result(runner(command))
    except Exception as error:  # noqa: BLE001 - report class only; no command output logging.
        return _mp4_blocked(report, [f"ffmpeg render failed: {error.__class__.__name__}"])
    if int(result["returncode"]) != 0:
        return _mp4_blocked(report, [f"ffmpeg render failed with exit code {result['returncode']}"])
    if not output.is_file() or output.stat().st_size <= 0:
        return _mp4_blocked(report, ["ffmpeg completed but MP4 artifact is missing or empty"])

    rendered = dict(report)
    rendered["status"] = "rendered"
    rendered["mp4_rendered"] = True
    rendered["video_path"] = str(output)
    rendered["video_filename"] = output.name
    rendered["size_bytes"] = output.stat().st_size
    rendered["sha256"] = _sha256_file(output)
    rendered["transcript_path"] = str(text_path)
    rendered["release_asset_paths"] = [str(output), str(text_path)]
    rendered["blocking_reasons"] = []
    return rendered


def validate_mp4_render_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != REAL_MP4_RENDER_MODEL_ID:
        errors.append("MP4 render report model_id must be adp-real-mp4-render-v1")
    if report.get("status") not in {"rendered", "blocked"}:
        errors.append("MP4 render status must be rendered or blocked")
    command = report.get("command")
    if not isinstance(command, Mapping):
        errors.append("MP4 render report requires command evidence")
    elif command.get("stdout_logged") is not False or command.get("stderr_logged") is not False:
        errors.append("MP4 render must not log ffmpeg stdout or stderr")
    if report.get("video_attachment_allowed") is not False:
        errors.append("MP4 render must keep video email attachments disabled")
    if report.get("status") == "rendered":
        if report.get("mp4_rendered") is not True:
            errors.append("rendered MP4 report requires mp4_rendered true")
        if not str(report.get("video_path") or "").endswith(".mp4"):
            errors.append("rendered MP4 report requires a .mp4 video_path")
        if int(report.get("size_bytes") or 0) <= 0:
            errors.append("rendered MP4 report requires positive size_bytes")
        if len(str(report.get("sha256") or "")) != 64:
            errors.append("rendered MP4 report requires sha256")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked MP4 render report requires blocking_reasons")
    return errors


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
        "lesson_key": narration.get("lesson_key", f"lesson-key:{narration.get('lesson_id', '')}"),
        "lesson_revision_id": narration.get("lesson_revision_id", narration.get("lesson_id", "")),
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


def _video_transcript(daily_input: Mapping[str, Any]) -> str:
    source = daily_input.get("source_item") if isinstance(daily_input.get("source_item"), Mapping) else {}
    queue = daily_input.get("queue_summary") if isinstance(daily_input.get("queue_summary"), Mapping) else {}
    frontstage = daily_input.get("frontstage") if isinstance(daily_input.get("frontstage"), Mapping) else {}
    title = str(source.get("title") or "arXiv Daily Push").strip()
    category = str((source.get("metadata") or {}).get("arxiv", {}).get("primary_category") or "").strip()
    queued = queue.get("queued_item_count", 0)
    takeaway = str(frontstage.get("one_line_takeaway") or "Use the email first: decide whether this paper is worth deeper reading.").strip()
    lines = [
        "arXiv Daily Push visual brief",
        title[:96],
        f"Category: {category or 'unknown'}",
        f"Decision: {takeaway[:120]}",
        "Visual goal: variables -> feedback loop -> evidence gap -> one next experiment.",
        f"Candidate queue: {queued} saved items; email shows only front-stage qualified candidates.",
        "Read the Chinese email first. This MP4 is an optional 45-60 second explainer link, never an attachment.",
    ]
    return "\n".join(lines)


def _mp4_base_report(
    daily_input: Mapping[str, Any],
    output: Path,
    generated_at: str,
    transcript: str,
    duration_seconds: int,
    ffmpeg_available: bool,
) -> dict[str, Any]:
    source = daily_input.get("source_item") if isinstance(daily_input.get("source_item"), Mapping) else {}
    return {
        "render_id": f"mp4-render:{hashlib.sha256((generated_at + str(source.get('source_id', ''))).encode('utf-8')).hexdigest()[:16]}",
        "model_id": REAL_MP4_RENDER_MODEL_ID,
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": "blocked",
        "mp4_rendered": False,
        "video_path": str(output),
        "video_filename": output.name,
        "source_id": source.get("source_id", ""),
        "title": source.get("title", ""),
        "duration_seconds": int(duration_seconds),
        "render_mode": "cloud_ffmpeg_title_card",
        "asset_download_enabled": False,
        "video_attachment_allowed": False,
        "release_storage_required": "github_release",
        "transcript_sha256": hashlib.sha256(transcript.encode("utf-8")).hexdigest(),
        "command": {
            "ffmpeg_required": True,
            "ffmpeg_available": bool(ffmpeg_available),
            "stdout_logged": False,
            "stderr_logged": False,
            "command_preview": [],
        },
        "blocking_reasons": [],
    }


def _mp4_blocked(report: Mapping[str, Any], reasons: list[str]) -> dict[str, Any]:
    blocked = dict(report)
    blocked["status"] = "blocked"
    blocked["mp4_rendered"] = False
    blocked["blocking_reasons"] = reasons
    return blocked


def _run_command(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)


def _normalize_command_result(result: Mapping[str, Any] | subprocess.CompletedProcess[str]) -> dict[str, int]:
    if isinstance(result, subprocess.CompletedProcess):
        return {"returncode": int(result.returncode)}
    return {"returncode": int(result.get("returncode", 1))}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
