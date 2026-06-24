from __future__ import annotations

import csv
import json
import shutil
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from app.config import Settings
from app.core.intake_validator import validate_intake
from app.core.path_display import display_path


@dataclass(frozen=True)
class PromotionIssue:
    file_key: str
    path: str
    severity: str
    message: str


PROMOTION_FILES = {
    "fund_rules": {
        "pack_name": "02_fund_rules_to_fill.csv",
        "destination": ("manual", "fund_rules.csv"),
    },
    "candidates": {
        "pack_name": "03_candidates_to_fill.csv",
        "destination": ("manual", "candidates.csv"),
    },
}

PLACEHOLDER_MARKERS = ("REPLACE_", "YYYY-MM-DD")
EVIDENCE_DIR_NAME = "evidence"


def _now(settings: Settings) -> str:
    return datetime.now(ZoneInfo(settings.timezone_primary)).isoformat(timespec="seconds")


def _safe_timestamp(settings: Settings) -> str:
    return datetime.now(ZoneInfo(settings.timezone_primary)).strftime("%Y%m%dT%H%M%S")


def _destination_path(settings: Settings, file_key: str) -> Path:
    group, filename = PROMOTION_FILES[file_key]["destination"]
    base = settings.imports_dir if group == "imports" else settings.manual_dir
    return base / filename


def _pack_path(pack_dir: Path, file_key: str) -> Path:
    return pack_dir / str(PROMOTION_FILES[file_key]["pack_name"])


def _read_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def _write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def _copy_evidence_dir(source_dir: Path, destination_dir: Path, *, backup_dir: Path | None = None) -> list[str]:
    copied: list[str] = []
    if not source_dir.exists():
        return copied
    for source in source_dir.rglob("*"):
        if not source.is_file() or source.is_symlink():
            continue
        relative = source.relative_to(source_dir)
        destination = destination_dir / relative
        if backup_dir is not None and destination.exists():
            backup_path = backup_dir / EVIDENCE_DIR_NAME / relative
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(destination, backup_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        copied.append(str(destination))
    return copied


def _scan_pack_file(path: Path, file_key: str) -> list[PromotionIssue]:
    issues: list[PromotionIssue] = []
    if not path.exists():
        return [
            PromotionIssue(
                file_key=file_key,
                path=str(path),
                severity="block",
                message="Required intake pack file is missing",
            )
        ]
    fieldnames, rows = _read_rows(path)
    if not fieldnames:
        issues.append(PromotionIssue(file_key, str(path), "block", "CSV has no header"))
    if not rows:
        issues.append(PromotionIssue(file_key, str(path), "block", "CSV has no rows"))
    for line_no, row in enumerate(rows, start=2):
        for field, value in row.items():
            text = str(value or "")
            if any(marker in text for marker in PLACEHOLDER_MARKERS):
                issues.append(
                    PromotionIssue(
                        file_key=file_key,
                        path=str(path),
                        severity="block",
                        message=f"Line {line_no} field `{field}` still contains placeholder `{text}`",
                    )
                )
    return issues


def _temp_settings(settings: Settings, root: Path) -> Settings:
    data = root / "data"
    return Settings(
        root_dir=root,
        data_dir=data,
        db_path=data / "serenity_daily.sqlite",
        imports_dir=data / "imports",
        manual_dir=data / "manual",
        reports_dir=data / "reports",
        notifications_dir=data / "notifications",
        exports_dir=data / "exports",
        timezone_primary=settings.timezone_primary,
        timezone_secondary=settings.timezone_secondary,
        recipient_email=settings.recipient_email,
        model_profile=settings.model_profile,
        dry_run_default=settings.dry_run_default,
        fallback_aggregated_enabled=settings.fallback_aggregated_enabled,
        mail_send_enabled=settings.mail_send_enabled,
        secret_storage_enabled=settings.secret_storage_enabled,
        max_drawdown_block=settings.max_drawdown_block,
        recovery_time_block_days=settings.recovery_time_block_days,
        deviation_threshold=settings.deviation_threshold,
        top5_change_rate_threshold=settings.top5_change_rate_threshold,
        drawdown_7d_worsen_threshold=settings.drawdown_7d_worsen_threshold,
        min_official_sources_action_ready=settings.min_official_sources_action_ready,
        min_candidate_nav_history_months=settings.min_candidate_nav_history_months,
        min_candidate_nav_history_span_days=settings.min_candidate_nav_history_span_days,
    )


def _prepare_validation_workspace(settings: Settings, pack_dir: Path, root: Path) -> Settings:
    temp = _temp_settings(settings, root)
    temp.ensure_dirs()
    shutil.copytree(settings.manual_dir, temp.manual_dir, dirs_exist_ok=True)
    shutil.copytree(settings.imports_dir, temp.imports_dir, dirs_exist_ok=True)
    for file_key in PROMOTION_FILES:
        source = _pack_path(pack_dir, file_key)
        destination = _destination_path(temp, file_key)
        fieldnames, rows = _read_rows(source)
        _write_rows(destination, fieldnames, rows)
    _copy_evidence_dir(pack_dir / EVIDENCE_DIR_NAME, temp.root_dir / EVIDENCE_DIR_NAME)
    return temp


def _backup_and_copy(settings: Settings, pack_dir: Path) -> dict[str, str]:
    backup_dir = settings.data_dir / "backups" / "intake_promotions" / _safe_timestamp(settings)
    copied: dict[str, str] = {}
    for file_key in PROMOTION_FILES:
        source = _pack_path(pack_dir, file_key)
        destination = _destination_path(settings, file_key)
        backup_path = backup_dir / destination.relative_to(settings.data_dir)
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            shutil.copy2(destination, backup_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        copied[file_key] = str(destination)
    evidence_copied = _copy_evidence_dir(pack_dir / EVIDENCE_DIR_NAME, settings.root_dir / EVIDENCE_DIR_NAME, backup_dir=backup_dir)
    return {"backup_dir": str(backup_dir), "copied": copied, "evidence_copied": evidence_copied}


def promote_intake_pack(
    settings: Settings,
    *,
    pack_dir: Path | None = None,
    apply: bool = False,
    scan_paths: list[Path] | None = None,
) -> dict[str, object]:
    settings.ensure_dirs()
    resolved_pack_dir = pack_dir or (settings.root_dir / "outputs" / "intake_pack")
    issues = [
        issue
        for file_key in PROMOTION_FILES
        for issue in _scan_pack_file(_pack_path(resolved_pack_dir, file_key), file_key)
    ]
    placeholder_blocked = any(issue.severity == "block" for issue in issues)
    validation: dict[str, object] | None = None
    applied = False
    copy_result: dict[str, object] | None = None

    if not placeholder_blocked:
        with tempfile.TemporaryDirectory(prefix="serenity_intake_promotion_") as tmp:
            temp_settings = _prepare_validation_workspace(settings, resolved_pack_dir, Path(tmp))
            validation = validate_intake(temp_settings, scan_paths=scan_paths or [], write_output=False)
        if apply and validation["production_ready"]:
            copy_result = _backup_and_copy(settings, resolved_pack_dir)
            validation = validate_intake(settings, scan_paths=scan_paths or [], write_output=True)
            applied = bool(validation["production_ready"])

    generated_at = _now(settings)
    result: dict[str, object] = {
        "generated_at": generated_at,
        "pack_dir": str(resolved_pack_dir),
        "apply_requested": apply,
        "applied": applied,
        "placeholder_blocked": placeholder_blocked,
        "issues": [asdict(issue) for issue in issues],
        "validation": validation,
        "copy_result": copy_result,
        "production_ready": bool(validation and validation.get("production_ready")),
    }

    output_dir = settings.root_dir / "outputs" / "intake_pack"
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "promotion_latest.json"
    md_path = output_dir / "promotion_latest.md"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    md_lines = [
        "# Intake Pack Promotion",
        "",
        f"- Generated: {generated_at}",
        f"- Pack dir: {display_path(settings.root_dir, resolved_pack_dir)}",
        f"- Apply requested: {apply}",
        f"- Applied: {applied}",
        f"- Production ready: {result['production_ready']}",
        f"- Placeholder blocked: {placeholder_blocked}",
        "",
        "## Issues",
        "",
    ]
    if issues:
        for issue in issues[:50]:
            md_lines.append(f"- `{issue.file_key}` [{issue.severity}]: {issue.message}")
    else:
        md_lines.append("- None")
    if validation:
        md_lines.extend(
            [
                "",
                "## Validation",
                "",
                f"- Production ready: {validation.get('production_ready')}",
                f"- Block count: {validation.get('block_count')}",
                f"- Warn count: {validation.get('warn_count')}",
            ]
        )
    if copy_result:
        md_lines.extend(["", "## Copy Result", "", f"- Backup dir: {display_path(settings.root_dir, copy_result['backup_dir'])}"])
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    result["json_path"] = str(json_path)
    result["markdown_path"] = str(md_path)
    return result
