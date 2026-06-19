from __future__ import annotations

import json
import sys
from contextlib import redirect_stdout
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from app.config import Settings
from app.core.completion_audit import run_completion_audit
from app.core.intake_promoter import promote_intake_pack
from app.core.packaging import build_delivery_package
from app.core.preflight import run_preflight
from app.core.source_evidence_audit import build_source_evidence_audit


def _now(settings: Settings) -> str:
    return datetime.now(ZoneInfo(settings.timezone_primary)).isoformat(timespec="seconds")


def _redact_for_markdown(value: object, root_dir: Path) -> object:
    home = Path.home().as_posix()
    root = root_dir.as_posix()
    if isinstance(value, dict):
        return {key: _redact_for_markdown(item, root_dir) for key, item in value.items()}
    if isinstance(value, list):
        return [_redact_for_markdown(item, root_dir) for item in value]
    if isinstance(value, str):
        redacted = value.replace(root, "<workspace>")
        if home and home in redacted:
            redacted = redacted.replace(home, "<home>")
        return redacted
    return value


def _stage(name: str, status: str, summary: dict[str, object], *, skipped_reason: str = "") -> dict[str, object]:
    return {
        "name": name,
        "status": status,
        "summary": summary,
        "skipped_reason": skipped_reason,
    }


def _evidence_summary(result: dict[str, object]) -> dict[str, object]:
    return {
        "status": result.get("status"),
        "row_count": result.get("row_count"),
        "valid_count": result.get("valid_count"),
        "invalid_count": result.get("invalid_count"),
        "local_hashed_count": result.get("local_hashed_count"),
        "url_count": result.get("url_count"),
        "pack_dir": result.get("pack_dir"),
        "files": result.get("files"),
    }


def _promotion_summary(result: dict[str, object]) -> dict[str, object]:
    validation = result.get("validation") if isinstance(result.get("validation"), dict) else {}
    copy_result = result.get("copy_result") if isinstance(result.get("copy_result"), dict) else {}
    return {
        "apply_requested": result.get("apply_requested"),
        "applied": result.get("applied"),
        "placeholder_blocked": result.get("placeholder_blocked"),
        "issue_count": len(result.get("issues") or []),
        "production_ready": result.get("production_ready"),
        "validation_block_count": validation.get("block_count") if validation else None,
        "validation_warn_count": validation.get("warn_count") if validation else None,
        "backup_dir": copy_result.get("backup_dir") if copy_result else None,
        "evidence_copied_count": len(copy_result.get("evidence_copied") or []) if copy_result else 0,
        "json_path": result.get("json_path"),
        "markdown_path": result.get("markdown_path"),
    }


def _preflight_summary(result: dict[str, object]) -> dict[str, object]:
    blockers = result.get("blockers") or []
    warnings = result.get("warnings") or []
    return {
        "production_ready": result.get("production_ready"),
        "shadow_ready": result.get("shadow_ready"),
        "status": result.get("status"),
        "blockers": [item.get("name") for item in blockers if isinstance(item, dict)],
        "warnings": [item.get("name") for item in warnings if isinstance(item, dict)],
        "json_path": result.get("json_path"),
        "markdown_path": result.get("markdown_path"),
    }


def _completion_summary(result: dict[str, object]) -> dict[str, object]:
    return {
        "overall_status": result.get("overall_status"),
        "completion_percent": result.get("completion_percent"),
        "pass_count": result.get("pass_count"),
        "warn_count": result.get("warn_count"),
        "block_count": result.get("block_count"),
        "total_count": result.get("total_count"),
        "json_path": result.get("json_path"),
        "markdown_path": result.get("markdown_path"),
        "csv_path": result.get("csv_path"),
    }


def _package_summary(result: dict[str, object]) -> dict[str, object]:
    return {
        "status": result.get("status"),
        "member_count": result.get("member_count"),
        "size_bytes": result.get("size_bytes"),
        "include_private_evidence": result.get("include_private_evidence"),
        "included_private_like_members": result.get("included_private_like_members"),
        "zip_path": result.get("zip_path"),
        "json_path": result.get("json_path"),
        "manifest_path": result.get("manifest_path"),
    }


def _run_preflight_for_unlock(settings: Settings, scan_paths: list[Path]) -> dict[str, object]:
    # The MooMoo SDK may emit connection diagnostics to stdout. Keep CLI --json
    # machine-readable by shifting those child diagnostics to stderr.
    with redirect_stdout(sys.stderr):
        return run_preflight(settings, scan_paths=scan_paths)


def _write_markdown(path: Path, result: dict[str, object], root_dir: Path) -> None:
    lines = [
        "# Production Unlock Check",
        "",
        f"- Generated: {result['generated_at']}",
        f"- Status: {result['status']}",
        f"- Apply requested: {result['apply_requested']}",
        f"- Apply performed: {result['apply_performed']}",
        f"- Full diagnostics: {result.get('full_diagnostics', False)}",
        f"- Pack ready to apply: {result['pack_ready_to_apply']}",
        f"- Production ready: {result['production_ready']}",
        f"- Stop reason: {result['stop_reason'] or 'None'}",
        "",
        "## Stages",
        "",
        "| Stage | Status | Summary |",
        "|---|---|---|",
    ]
    for stage in result["stages"]:
        redacted_summary = _redact_for_markdown(stage["summary"], root_dir)
        summary = json.dumps(redacted_summary, ensure_ascii=False, sort_keys=True)
        if stage.get("skipped_reason"):
            summary = f"{summary}; skipped_reason={stage['skipped_reason']}"
        lines.append(f"| {stage['name']} | {stage['status']} | `{summary}` |")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
        "- This command does not send mail.",
        "- This command does not place trades.",
        "- `--apply` only promotes the intake pack after evidence and dry-run promotion checks pass.",
        "- `--full-diagnostics` only continues read-only checks after a pack blocker; it does not apply files.",
        "- Production remains locked unless preflight and completion audit both pass.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_outputs(settings: Settings, result: dict[str, object]) -> dict[str, object]:
    output_dir = settings.root_dir / "outputs" / "preflight"
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "production_unlock_check_latest.json"
    markdown_path = output_dir / "production_unlock_check_latest.md"
    result["json_path"] = str(json_path)
    result["markdown_path"] = str(markdown_path)
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_markdown(markdown_path, result, settings.root_dir)
    return result


def run_production_unlock_check(
    settings: Settings,
    *,
    pack_dir: Path | None = None,
    apply: bool = False,
    scan_paths: list[Path] | None = None,
    package: bool = False,
    full_diagnostics: bool = False,
) -> dict[str, object]:
    settings.ensure_dirs()
    resolved_pack_dir = pack_dir or (settings.root_dir / "outputs" / "intake_pack")
    scan_paths = scan_paths or []
    stages: list[dict[str, object]] = []

    evidence = build_source_evidence_audit(settings, pack_dir=resolved_pack_dir)
    evidence_pass = evidence.get("status") == "pass"
    stages.append(_stage("source_evidence_audit_pack", "pass" if evidence_pass else "block", _evidence_summary(evidence)))

    dry_promotion = promote_intake_pack(settings, pack_dir=resolved_pack_dir, apply=False, scan_paths=scan_paths)
    dry_promotion_ready = bool(dry_promotion.get("production_ready")) and not bool(dry_promotion.get("placeholder_blocked"))
    stages.append(
        _stage(
            "promote_intake_pack_dry_run",
            "pass" if dry_promotion_ready else "block",
            _promotion_summary(dry_promotion),
        )
    )

    pack_ready_to_apply = evidence_pass and dry_promotion_ready
    apply_result: dict[str, object] | None = None
    apply_performed = False
    if apply and pack_ready_to_apply:
        apply_result = promote_intake_pack(settings, pack_dir=resolved_pack_dir, apply=True, scan_paths=scan_paths)
        apply_performed = bool(apply_result.get("applied"))
        stages.append(
            _stage(
                "promote_intake_pack_apply",
                "pass" if apply_performed else "block",
                _promotion_summary(apply_result),
            )
        )
    elif apply:
        stages.append(
            _stage(
                "promote_intake_pack_apply",
                "skipped",
                {"apply_requested": True, "pack_ready_to_apply": pack_ready_to_apply},
                skipped_reason="pack evidence or dry-run promotion is not production-ready",
            )
        )

    if not pack_ready_to_apply and not full_diagnostics:
        stop_reason = "pack source evidence audit failed" if not evidence_pass else "intake pack dry-run promotion is not production-ready"
        stages.append(
            _stage(
                "preflight",
                "skipped",
                {"pack_ready_to_apply": pack_ready_to_apply},
                skipped_reason=stop_reason,
            )
        )
        stages.append(
            _stage(
                "completion_audit",
                "skipped",
                {"overall_status": "not_run"},
                skipped_reason=stop_reason,
            )
        )
        result: dict[str, object] = {
            "generated_at": _now(settings),
            "status": "blocked",
            "pack_dir": str(resolved_pack_dir),
            "apply_requested": apply,
            "apply_performed": apply_performed,
            "package_requested": package,
            "full_diagnostics": full_diagnostics,
            "pack_ready_to_apply": pack_ready_to_apply,
            "production_ready": False,
            "stop_reason": stop_reason,
            "stages": stages,
        }
        return _write_outputs(settings, result)

    blocked_pack_reason = ""
    if not pack_ready_to_apply:
        blocked_pack_reason = (
            "pack source evidence audit failed"
            if not evidence_pass
            else "intake pack dry-run promotion is not production-ready"
        )

    preflight = _run_preflight_for_unlock(settings, scan_paths)
    preflight_ready = bool(preflight.get("production_ready"))
    stages.append(_stage("preflight", "pass" if preflight_ready else "block", _preflight_summary(preflight)))

    provisional_result: dict[str, object] = {
        "generated_at": _now(settings),
        "status": "blocked",
        "pack_dir": str(resolved_pack_dir),
        "apply_requested": apply,
        "apply_performed": apply_performed,
        "package_requested": package,
        "full_diagnostics": full_diagnostics,
        "pack_ready_to_apply": pack_ready_to_apply,
        "production_ready": False,
        "stop_reason": blocked_pack_reason or "completion audit pending",
        "stages": stages
        + [
            _stage(
                "completion_audit",
                "pending",
                {"overall_status": "pending"},
                skipped_reason="pending final completion audit",
            )
        ],
    }
    _write_outputs(settings, provisional_result)

    completion = run_completion_audit(settings)
    completion_ready = completion.get("overall_status") == "complete"
    stages.append(_stage("completion_audit", "pass" if completion_ready else "block", _completion_summary(completion)))

    package_result: dict[str, object] | None = None
    if package and pack_ready_to_apply:
        package_result = build_delivery_package(settings)
        package_ready = package_result.get("status") == "pass"
        stages.append(_stage("package_delivery", "pass" if package_ready else "block", _package_summary(package_result)))
        completion = run_completion_audit(settings)
        completion_ready = completion.get("overall_status") == "complete"
        stages.append(_stage("completion_audit_after_package", "pass" if completion_ready else "block", _completion_summary(completion)))
    elif package:
        stages.append(
            _stage(
                "package_delivery",
                "skipped",
                {"package_requested": True, "pack_ready_to_apply": pack_ready_to_apply},
                skipped_reason=blocked_pack_reason or "pack is not production-ready",
            )
        )

    stop_reason = ""
    if not evidence_pass:
        stop_reason = "pack source evidence audit failed"
    elif not dry_promotion_ready:
        stop_reason = "intake pack dry-run promotion is not production-ready"
    elif apply and not apply_performed:
        stop_reason = "apply requested but promotion was not performed"
    elif not preflight_ready:
        stop_reason = "production preflight is still blocked"
    elif not completion_ready:
        stop_reason = "completion audit is still blocked"

    production_ready = preflight_ready and completion_ready
    result: dict[str, object] = {
        "generated_at": _now(settings),
        "status": "pass" if production_ready else "blocked",
        "pack_dir": str(resolved_pack_dir),
        "apply_requested": apply,
        "apply_performed": apply_performed,
        "package_requested": package,
        "full_diagnostics": full_diagnostics,
        "pack_ready_to_apply": pack_ready_to_apply,
        "production_ready": production_ready,
        "stop_reason": stop_reason,
        "stages": stages,
    }

    return _write_outputs(settings, result)
