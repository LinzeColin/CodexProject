from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from app.config import Settings
from app.core.alipay_position_normalizer import normalize_alipay_positions
from app.core.candidate_normalizer import normalize_candidates
from app.core.fund_rule_normalizer import normalize_fund_rules
from app.core.intake_promoter import promote_intake_pack
from app.core.source_evidence_audit import build_source_evidence_audit


def _now(settings: Settings) -> str:
    return datetime.now(ZoneInfo(settings.timezone_primary)).isoformat(timespec="seconds")


def _rel(settings: Settings, value: object) -> object:
    if isinstance(value, dict):
        return {key: _rel(settings, item) for key, item in value.items()}
    if isinstance(value, list):
        return [_rel(settings, item) for item in value]
    if not isinstance(value, str):
        return value
    try:
        return Path(value).relative_to(settings.root_dir).as_posix()
    except (ValueError, OSError):
        return value


def _stage(name: str, status: str, summary: dict[str, object], *, skipped_reason: str = "") -> dict[str, object]:
    return {
        "name": name,
        "status": status,
        "summary": summary,
        "skipped_reason": skipped_reason,
    }


def _normalization_summary(result: dict[str, object]) -> dict[str, object]:
    return {
        "status": result.get("status"),
        "row_count": result.get("row_count"),
        "block_count": result.get("block_count"),
        "warn_count": result.get("warn_count"),
        "output_csv": result.get("output_csv"),
        "write_pack": result.get("write_pack"),
    }


def _evidence_summary(result: dict[str, object]) -> dict[str, object]:
    return {
        "status": result.get("status"),
        "row_count": result.get("row_count"),
        "valid_count": result.get("valid_count"),
        "invalid_count": result.get("invalid_count"),
        "local_hashed_count": result.get("local_hashed_count"),
        "url_count": result.get("url_count"),
    }


def _promotion_summary(result: dict[str, object]) -> dict[str, object]:
    validation = result.get("validation") if isinstance(result.get("validation"), dict) else {}
    return {
        "apply_requested": result.get("apply_requested"),
        "applied": result.get("applied"),
        "placeholder_blocked": result.get("placeholder_blocked"),
        "issue_count": len(result.get("issues") or []),
        "production_ready": result.get("production_ready"),
        "validation_block_count": validation.get("block_count") if validation else None,
        "validation_warn_count": validation.get("warn_count") if validation else None,
    }


def _write_markdown(path: Path, result: dict[str, object], settings: Settings) -> None:
    lines = [
        "# Intake Bundle Normalization",
        "",
        f"- Generated: {result['generated_at']}",
        f"- Status: {result['status']}",
        f"- Write pack: {result['write_pack']}",
        f"- Pack dir: `{_rel(settings, result['pack_dir'])}`",
        f"- Production files touched: {result['production_files_touched']}",
        f"- Mail sent: {result['mail_sent']}",
        f"- Trades placed: {result['trades_placed']}",
        "",
        "## Stages",
        "",
        "| Stage | Status | Summary |",
        "|---|---|---|",
    ]
    for stage in result["stages"]:
        summary = json.dumps(_rel(settings, stage["summary"]), ensure_ascii=False, sort_keys=True)
        if stage.get("skipped_reason"):
            summary = f"{summary}; skipped_reason={stage['skipped_reason']}"
        lines.append(f"| {stage['name']} | {stage['status']} | `{summary}` |")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- This command only normalizes source CSVs into the intake pack.",
            "- This command does not copy production files.",
            "- This command does not send mail.",
            "- This command does not place trades.",
            "- Promotion is dry-run only; use `production-unlock-check --apply` separately after evidence and preflight pass.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def normalize_intake_bundle(
    settings: Settings,
    *,
    alipay_csv: Path | None = None,
    fund_rules_csv: Path | None = None,
    candidates_csv: Path | None = None,
    alipay_evidence: str | None = None,
    fund_rules_evidence: str | None = None,
    candidates_evidence: str | None = None,
    as_of: str | None = None,
    write_pack: bool = False,
    audit_pack: bool = True,
    promote_dry_run: bool = True,
) -> dict[str, object]:
    settings.ensure_dirs()
    pack_dir = settings.root_dir / "outputs" / "intake_pack"
    pack_dir.mkdir(parents=True, exist_ok=True)
    stages: list[dict[str, object]] = []

    provided = {
        "normalize_alipay_positions": alipay_csv,
        "normalize_fund_rules": fund_rules_csv,
        "normalize_candidates": candidates_csv,
    }
    if not any(provided.values()):
        stages.append(
            _stage(
                "input_check",
                "block",
                {"provided_sources": {key: bool(value) for key, value in provided.items()}},
            )
        )
    else:
        stages.append(
            _stage(
                "input_check",
                "pass",
                {"provided_sources": {key: bool(value) for key, value in provided.items()}},
            )
        )

    if alipay_csv:
        result = normalize_alipay_positions(
            settings,
            csv_path=alipay_csv,
            evidence=alipay_evidence,
            as_of=as_of,
            write_pack=write_pack,
        )
        stages.append(_stage("normalize_alipay_positions", str(result["status"]), _normalization_summary(result)))
    else:
        stages.append(_stage("normalize_alipay_positions", "skipped", {}, skipped_reason="--alipay-csv not provided"))

    if fund_rules_csv:
        result = normalize_fund_rules(
            settings,
            csv_path=fund_rules_csv,
            evidence=fund_rules_evidence,
            as_of=as_of,
            write_pack=write_pack,
        )
        stages.append(_stage("normalize_fund_rules", str(result["status"]), _normalization_summary(result)))
    else:
        stages.append(_stage("normalize_fund_rules", "skipped", {}, skipped_reason="--fund-rules-csv not provided"))

    if candidates_csv:
        result = normalize_candidates(
            settings,
            csv_path=candidates_csv,
            evidence=candidates_evidence,
            as_of=as_of,
            write_pack=write_pack,
        )
        stages.append(_stage("normalize_candidates", str(result["status"]), _normalization_summary(result)))
    else:
        stages.append(_stage("normalize_candidates", "skipped", {}, skipped_reason="--candidates-csv not provided"))

    normalization_blocked = any(stage["status"] == "blocked" for stage in stages)
    if not write_pack:
        stages.append(
            _stage(
                "source_evidence_audit_pack",
                "skipped",
                {"write_pack": write_pack},
                skipped_reason="candidate outputs were generated only; pass --write-pack to audit staged intake files",
            )
        )
        stages.append(
            _stage(
                "promote_intake_pack_dry_run",
                "skipped",
                {"write_pack": write_pack},
                skipped_reason="candidate outputs were generated only; pass --write-pack to dry-run promotion",
            )
        )
    elif normalization_blocked:
        stages.append(
            _stage(
                "source_evidence_audit_pack",
                "skipped",
                {"normalization_blocked": True},
                skipped_reason="normalization did not pass",
            )
        )
        stages.append(
            _stage(
                "promote_intake_pack_dry_run",
                "skipped",
                {"normalization_blocked": True},
                skipped_reason="normalization did not pass",
            )
        )
    else:
        if audit_pack:
            audit = build_source_evidence_audit(settings, pack_dir=pack_dir)
            stages.append(_stage("source_evidence_audit_pack", str(audit["status"]), _evidence_summary(audit)))
        else:
            stages.append(
                _stage(
                    "source_evidence_audit_pack",
                    "skipped",
                    {"audit_pack": audit_pack},
                    skipped_reason="--no-audit-pack requested",
                )
            )
        if promote_dry_run:
            promotion = promote_intake_pack(settings, pack_dir=pack_dir, apply=False)
            stages.append(
                _stage(
                    "promote_intake_pack_dry_run",
                    "pass" if promotion.get("production_ready") else "block",
                    _promotion_summary(promotion),
                )
            )
        else:
            stages.append(
                _stage(
                    "promote_intake_pack_dry_run",
                    "skipped",
                    {"promote_dry_run": promote_dry_run},
                    skipped_reason="--no-promote-dry-run requested",
                )
            )

    blocking_statuses = {"block", "blocked"}
    status = "blocked" if any(stage["status"] in blocking_statuses for stage in stages) else "pass"
    result: dict[str, object] = {
        "generated_at": _now(settings),
        "status": status,
        "pack_dir": str(pack_dir),
        "write_pack": write_pack,
        "audit_pack": audit_pack,
        "promote_dry_run": promote_dry_run,
        "production_files_touched": False,
        "mail_sent": False,
        "trades_placed": False,
        "stages": stages,
        "next_command": "python -m app.cli production-unlock-check --json",
    }
    json_path = pack_dir / "intake_bundle_normalization_latest.json"
    markdown_path = pack_dir / "intake_bundle_normalization_latest.md"
    result["json_path"] = str(json_path)
    result["markdown_path"] = str(markdown_path)
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_markdown(markdown_path, result, settings)
    return result
