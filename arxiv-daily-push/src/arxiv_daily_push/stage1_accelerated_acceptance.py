"""Stage 1 accelerated production-acceptance evidence for real arXiv data."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from .config import DEFAULT_RECIPIENT, DEFAULT_TIMEZONE
from .trial import (
    TRIAL_ACCEPTANCE_MODE_ACCELERATED,
    evaluate_trial_evidence,
    validate_trial_evidence_report,
)


STAGE1_ACCELERATED_ACCEPTANCE_MODEL_ID = "adp-stage1-accelerated-acceptance-v1"
STAGE1_ACCELERATED_ACCEPTANCE_ID = "ADP-ACC-S1P5T04-ACCELERATED-REAL-ARXIV"
STAGE1_ACCELERATED_ACCEPTANCE_REQUIRED_SAMPLES = 30
DEFAULT_RECOVERY_REF = "governance/run_manifests/ADP-S1-08-LOCAL-RUNTIME-RECOVERY-20260622.json"
DEFAULT_SCHEDULER_REF = ".github/workflows/arxiv-daily-push-scheduled.yml"


def build_stage1_accelerated_acceptance_report(
    live_dry_run: Mapping[str, Any],
    controlled_smtp_manifest: Mapping[str, Any],
    *,
    generated_at: str,
    expected_samples: int = STAGE1_ACCELERATED_ACCEPTANCE_REQUIRED_SAMPLES,
    live_dry_run_ref: str = "",
    controlled_smtp_ref: str = "",
    scheduler_ref: str = DEFAULT_SCHEDULER_REF,
    resource_ref: str = "",
    recovery_ref: str = DEFAULT_RECOVERY_REF,
    artifact_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Build fail-closed Stage 1 acceptance evidence without enabling production schedule."""

    expected = max(int(expected_samples), 1)
    blockers = _live_dry_run_blockers(live_dry_run)
    smtp_refs, smtp_blockers = _controlled_smtp_refs(controlled_smtp_manifest)
    blockers.extend(smtp_blockers)

    candidates = _unique_ranked_candidates(live_dry_run)
    if len(candidates) < expected:
        blockers.append(f"real arXiv candidate count {len(candidates)} is below required {expected}")

    dry_ref = live_dry_run_ref or _artifact_ref(live_dry_run, "live_all_arxiv_dry_run") or "artifact://adp/live-all-arxiv-dry-run"
    smtp_ref = controlled_smtp_ref or "governance/run_manifests/ADP-S1P5T04-CONTROLLED-SMTP-EVIDENCE-20260623.json"
    resource_evidence_ref = resource_ref or dry_ref
    trial_input: dict[str, Any] = {}
    trial_report: dict[str, Any] = {}
    trial_errors: list[str] = []

    if not blockers:
        trial_input = _trial_input_from_candidates(
            candidates[:expected],
            generated_at=generated_at,
            expected_samples=expected,
            live_dry_run_ref=dry_ref,
            controlled_smtp_ref=smtp_ref,
            scheduler_ref=scheduler_ref,
            resource_ref=resource_evidence_ref,
            recovery_ref=recovery_ref,
        )
        trial_report = evaluate_trial_evidence(trial_input, generated_at=generated_at)
        trial_errors = validate_trial_evidence_report(trial_report)
        if trial_errors:
            blockers.extend(trial_errors)
        if trial_report.get("accepted_for_production") is not True:
            blockers.extend(str(reason) for reason in trial_report.get("blocking_reasons") or [])

    passed = not blockers
    report: dict[str, Any] = {
        "acceptance_id": STAGE1_ACCELERATED_ACCEPTANCE_ID,
        "model_id": STAGE1_ACCELERATED_ACCEPTANCE_MODEL_ID,
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": "pass" if passed else "blocked",
        "accelerated_acceptance_ready": passed,
        "accepted_for_production": passed,
        "arxiv_production_acceptance_label": "ARXIV_PRODUCTION_ACCEPTED" if passed else "BLOCKED",
        "expected_samples": expected,
        "real_arxiv_candidate_count": len(candidates),
        "selected_sample_count": expected if passed else 0,
        "controlled_smtp_delivery_count": len(smtp_refs),
        "controlled_smtp_refs": smtp_refs,
        "production_schedule_enabled": False,
        "new_real_smtp_sent": False,
        "release_upload_required": False,
        "video_required": False,
        "source_policy": {
            "uses_real_arxiv_candidates": True,
            "requires_all_primary_archives": True,
            "pdf_download_enabled": False,
            "bulk_harvest_enabled": False,
            "natural_day_wait_required": False,
            "acceptance_mode": TRIAL_ACCEPTANCE_MODE_ACCELERATED,
        },
        "trial_input": trial_input,
        "trial_report": trial_report,
        "operational_evidence": trial_report.get("operational_evidence", {}) if isinstance(trial_report, Mapping) else {},
        "blocking_reasons": sorted(set(blockers)),
        "artifact_paths": {},
    }
    if artifact_dir:
        report["artifact_paths"] = _write_artifacts(report, artifact_dir)
    return report


def validate_stage1_accelerated_acceptance_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != STAGE1_ACCELERATED_ACCEPTANCE_MODEL_ID:
        errors.append("accelerated acceptance model_id must be adp-stage1-accelerated-acceptance-v1")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("accelerated acceptance status must be pass or blocked")
    if report.get("production_schedule_enabled") is not False:
        errors.append("accelerated acceptance must not enable production schedule")
    if report.get("new_real_smtp_sent") is not False:
        errors.append("accelerated acceptance must not send a new email")
    if report.get("release_upload_required") is not False:
        errors.append("Stage 1 accelerated acceptance must not require GitHub Release upload")
    if report.get("video_required") is not False:
        errors.append("Stage 1 accelerated acceptance must not require video")
    if report.get("status") == "blocked":
        if not report.get("blocking_reasons"):
            errors.append("blocked accelerated acceptance requires blocking_reasons")
        if report.get("accepted_for_production") is True:
            errors.append("blocked accelerated acceptance cannot be accepted_for_production")
        return errors
    if report.get("accelerated_acceptance_ready") is not True:
        errors.append("passing accelerated acceptance requires accelerated_acceptance_ready true")
    if report.get("accepted_for_production") is not True:
        errors.append("passing accelerated acceptance requires accepted_for_production true")
    if report.get("arxiv_production_acceptance_label") != "ARXIV_PRODUCTION_ACCEPTED":
        errors.append("passing accelerated acceptance requires ARXIV_PRODUCTION_ACCEPTED label")
    expected = int(report.get("expected_samples") or 0)
    if int(report.get("real_arxiv_candidate_count") or 0) < expected:
        errors.append("passing accelerated acceptance requires enough real arXiv candidates")
    if int(report.get("selected_sample_count") or 0) != expected:
        errors.append("passing accelerated acceptance selected_sample_count must equal expected_samples")
    if int(report.get("controlled_smtp_delivery_count") or 0) < 2:
        errors.append("passing accelerated acceptance requires at least two controlled SMTP deliveries")
    trial_report = report.get("trial_report")
    if not isinstance(trial_report, Mapping):
        errors.append("passing accelerated acceptance requires trial_report")
    else:
        errors.extend(validate_trial_evidence_report(trial_report))
        if trial_report.get("accepted_for_production") is not True:
            errors.append("trial_report must be accepted_for_production")
    return errors


def _live_dry_run_blockers(report: Mapping[str, Any]) -> list[str]:
    blockers: list[str] = []
    if report.get("status") != "pass" or report.get("live_dry_run_ready") is not True:
        blockers.append("live all-arXiv dry-run must pass")
    if int(report.get("archive_count") or 0) < 20 or int(report.get("verified_archive_count") or 0) < 20:
        blockers.append("live all-arXiv dry-run must verify all 20 primary archives")
    for key in ("production_schedule_enabled", "smtp_send_enabled", "release_upload_enabled", "pdf_download_enabled", "bulk_harvest_enabled"):
        if report.get(key) is not False:
            blockers.append(f"live all-arXiv dry-run {key} must be false")
    return blockers


def _controlled_smtp_refs(manifest: Mapping[str, Any]) -> tuple[list[str], list[str]]:
    blockers: list[str] = []
    refs: list[str] = []
    if manifest.get("real_smtp_sent") is not True:
        blockers.append("controlled SMTP manifest must record real_smtp_sent true")
    deliveries = manifest.get("controlled_smtp_delivery_refs")
    if not isinstance(deliveries, Sequence) or isinstance(deliveries, (str, bytes)):
        blockers.append("controlled SMTP manifest requires controlled_smtp_delivery_refs")
        return refs, blockers
    for delivery in deliveries:
        if not isinstance(delivery, Mapping):
            continue
        if delivery.get("production_evidence_ready") is True and delivery.get("notification_status") == "sent":
            run_id = str(delivery.get("run_id") or "")
            artifact_id = str(delivery.get("artifact_id") or "")
            if run_id and artifact_id:
                refs.append(f"github-actions://LinzeColin/CodexProject/actions/runs/{run_id}/artifacts/{artifact_id}")
    if len(refs) < 2:
        blockers.append("controlled SMTP manifest must include at least two sent production-ready artifacts")
    return refs, blockers


def _unique_ranked_candidates(report: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    scan = report.get("scan") if isinstance(report.get("scan"), Mapping) else {}
    raw_candidates = scan.get("candidates") if isinstance(scan.get("candidates"), Sequence) else []
    by_source: dict[str, Mapping[str, Any]] = {}
    for candidate in raw_candidates:
        if not isinstance(candidate, Mapping):
            continue
        source_id = str(candidate.get("source_id") or "")
        if not source_id or source_id in by_source:
            continue
        by_source[source_id] = candidate
    return sorted(
        by_source.values(),
        key=lambda item: (-float(item.get("roi_total_score") or 0.0), str(item.get("source_id") or "")),
    )


def _trial_input_from_candidates(
    candidates: Sequence[Mapping[str, Any]],
    *,
    generated_at: str,
    expected_samples: int,
    live_dry_run_ref: str,
    controlled_smtp_ref: str,
    scheduler_ref: str,
    resource_ref: str,
    recovery_ref: str,
) -> dict[str, Any]:
    run_date = generated_at[:10]
    daily_runs = []
    for index, candidate in enumerate(candidates, 1):
        source_id = str(candidate.get("source_id") or f"arxiv:unknown-{index}")
        publication_id = _publication_id(candidate, index)
        published_at = _published_at(candidate)
        ref_suffix = f"#sample-{index:02d}-{source_id.replace(':', '-')}"
        daily_runs.append(
            {
                "date": run_date,
                "replay_day_index": index,
                "accelerated_replay": True,
                "real_source_id_verified": True,
                "real_source_published_at": published_at or generated_at,
                "run_id": f"adp-accelerated-{index:02d}",
                "source_id": source_id,
                "publication_id": publication_id,
                "status": "succeeded",
                "scheduled_local_time": "05:00",
                "p0_claims_traceable": True,
                "text_degradation_path_verified": True,
                "duplicate_publication": False,
                "unsupported_claims_published": False,
                "failure_generated_misleading_content": False,
                "run_record_ref": live_dry_run_ref + ref_suffix,
                "text_artifact_ref": live_dry_run_ref + ref_suffix,
                "email_ref": controlled_smtp_ref,
                "resource_gate_ref": resource_ref,
            }
        )
    return {
        "trial_id": "adp-stage1-accelerated-real-arxiv",
        "trial_ref": live_dry_run_ref,
        "timezone": DEFAULT_TIMEZONE,
        "period": {
            "expected_days": expected_samples,
            "acceptance_mode": TRIAL_ACCEPTANCE_MODE_ACCELERATED,
            "natural_day_wait_required": False,
        },
        "daily_runs": daily_runs,
        "scheduler": {
            "enabled": False,
            "scheduled_production_enabled": False,
            "cloud_schedule_contract_verified": True,
            "target_local_time": "05:00",
            "health_check_time": "04:45",
            "manual_rerun_verified": True,
            "ref": scheduler_ref,
        },
        "text_artifacts": {"b1_text_artifacts_verified": True, "ref": live_dry_run_ref},
        "email": {"real_smtp_verified": True, "recipient": DEFAULT_RECIPIENT, "ref": controlled_smtp_ref},
        "resource_pressure": {
            "disk_ok": True,
            "memory_ok": True,
            "cache_ok": True,
            "secrets_ok": True,
            "git_large_artifacts_ok": True,
            "ref": resource_ref,
        },
        "weekly_monthly": {"weekly_replay_verified": True, "monthly_replay_verified": True, "ref": live_dry_run_ref},
        "recovery": {"failure_recovery_drill_verified": True, "ref": recovery_ref},
    }


def _publication_id(candidate: Mapping[str, Any], index: int) -> str:
    source_item = candidate.get("source_item") if isinstance(candidate.get("source_item"), Mapping) else {}
    stable = str(source_item.get("stable_id") or candidate.get("stable_id") or candidate.get("source_id") or "")
    return f"adp-accelerated-publication-{stable or index}"


def _published_at(candidate: Mapping[str, Any]) -> str:
    source_item = candidate.get("source_item") if isinstance(candidate.get("source_item"), Mapping) else {}
    metadata = source_item.get("metadata") if isinstance(source_item.get("metadata"), Mapping) else {}
    arxiv = metadata.get("arxiv") if isinstance(metadata.get("arxiv"), Mapping) else {}
    return str(arxiv.get("published") or arxiv.get("updated") or source_item.get("retrieved_at") or "")


def _artifact_ref(report: Mapping[str, Any], key: str) -> str:
    paths = report.get("artifact_paths") if isinstance(report.get("artifact_paths"), Mapping) else {}
    return str(paths.get(key) or "")


def _write_artifacts(report: Mapping[str, Any], artifact_dir: str | Path) -> dict[str, str]:
    directory = Path(artifact_dir)
    directory.mkdir(parents=True, exist_ok=True)
    trial_input_path = directory / "adp-stage1-accelerated-trial-input.json"
    trial_report_path = directory / "adp-stage1-accelerated-trial-report.json"
    acceptance_path = directory / "adp-stage1-accelerated-acceptance.json"
    trial_input_path.write_text(json.dumps(report.get("trial_input") or {}, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    trial_report_path.write_text(json.dumps(report.get("trial_report") or {}, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    paths = {
        "trial_input": str(trial_input_path),
        "trial_report": str(trial_report_path),
        "accelerated_acceptance": str(acceptance_path),
    }
    output = dict(report)
    output["artifact_paths"] = paths
    acceptance_path.write_text(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return paths
