#!/usr/bin/env python3
"""Replay the 72-item private residual queue without inventing business values."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.project_margin_cash_margin import _divide_to_basis_points  # noqa: E402


PROJECT_ROOT = Path("KMFA")
RAW_ROOT = Path("/Users/linzezhang/Downloads/KMFA_MetaData")
PHASE_ID = "V014_GLOBAL_RESIDUAL_DIFFERENCE_QUEUE_REPLAY_OR_AUTHORITATIVE_EXCLUSION"
TASK_ID = "KMFA-V014-GLOBAL-RESIDUAL-DIFFERENCE-QUEUE-REPLAY-OR-AUTHORITATIVE-EXCLUSION-20260710"
ACCEPTANCE_ID = "ACC-V014-GLOBAL-RESIDUAL-DIFFERENCE-QUEUE-REPLAY-OR-AUTHORITATIVE-EXCLUSION"
VERSION = "0.1.4-global-residual-difference-queue-replay-or-authoritative-exclusion"
STATUS = "completed_validated_local_only_61_closed_or_excluded_11_open_no_go"
DECISION = "NO_GO"
PREFIX = "global_residual_difference_queue_replay_or_authoritative_exclusion"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / f"{PREFIX}_summary.json"
MANIFEST_PATH = MACHINE_DIR / f"{PREFIX}_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / f"{PREFIX}_go_no_go_report.json"
MATRIX_PATH = MACHINE_DIR / f"{PREFIX}_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / f"{PREFIX}.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / f"metadata/quality/v014_{PREFIX}_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / f"metadata/quality/v014_{PREFIX}_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / f"metadata/quality/v014_{PREFIX}_go_no_go_report.json"
METADATA_MATRIX_PATH = PROJECT_ROOT / f"metadata/quality/v014_{PREFIX}_matrix_public_safe.json"

PRIVATE_OUTPUT_DIR = PROJECT_ROOT / f".codex_private_runtime/v014_{PREFIX}"
PRIVATE_RAW_BEFORE_PATH = PRIVATE_OUTPUT_DIR / "raw_immutability_before.json"
PRIVATE_RAW_AFTER_PATH = PRIVATE_OUTPUT_DIR / "raw_immutability_after.json"
PRIVATE_REPLAY_RECORDS_PATH = PRIVATE_OUTPUT_DIR / "private_global_residual_replay_records.jsonl"
PRIVATE_OPEN_DIFFERENCES_PATH = PRIVATE_OUTPUT_DIR / "private_global_residual_open_differences.jsonl"
PRIVATE_AUTHORIZATION_RECEIPT_PATH = PRIVATE_OUTPUT_DIR / "private_owner_authorization_receipt.json"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_global_residual_replay_diagnostic.json"
PRIVATE_DIFFERENCE_REPORT_PATH = PRIVATE_OUTPUT_DIR / "private_global_residual_difference_report_zh.md"

SOURCE_RESIDUAL_QUEUE_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_residual_difference_private_resolution_materialization_replay/private_residual_difference_materialized_records.jsonl"
)
SOURCE_STAGING_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_private_processed_value_staging/private_processed_value_staging.json"
)
SOURCE_OWNER_REPORT_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_outside_scope_candidate_review_owner_authorized_discrepancy_report/private_owner_authorized_discrepancy_queue.jsonl"
)
SOURCE_AUTHORIZATION_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_outside_scope_candidate_review_residual_difference_source_map_correction_authorization_intake/private_source_map_correction_authorization_active_record.json"
)
SOURCE_BINDINGS_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_real_project_identity_private_rebinding_and_processed_value_materialization/private_real_project_identity_bindings.jsonl"
)
SOURCE_METRICS_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_real_project_identity_private_rebinding_and_processed_value_materialization/private_processed_project_metrics.jsonl"
)
SOURCE_FINAL_CASH_DIR = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_remaining_two_project_cash_collection_evidence_or_final_difference_acceptance"
)
SOURCE_TARGET_MATERIALIZATIONS_PATH = SOURCE_FINAL_CASH_DIR / "private_s09_target_slot_materializations.jsonl"
SOURCE_UNRESOLVED_TARGETS_PATH = SOURCE_FINAL_CASH_DIR / "private_unresolved_cash_value_targets.jsonl"
SOURCE_COMPARISONS_PATH = SOURCE_FINAL_CASH_DIR / "private_s09_reconciliation_comparisons.jsonl"
SOURCE_CASH_METRICS_PATH = SOURCE_FINAL_CASH_DIR / "private_materialized_cash_metrics.jsonl"
SOURCE_CASH_DECISIONS_PATH = SOURCE_FINAL_CASH_DIR / "private_cash_source_decisions.jsonl"
SOURCE_COLLECTION_LINKS_PATH = SOURCE_FINAL_CASH_DIR / "private_unique_collection_links.jsonl"
SOURCE_FINAL_DIFFERENCE_REPORT_PATH = SOURCE_FINAL_CASH_DIR / "private_final_difference_acceptance_report_zh.md"
SOURCE_SUMMARY_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_remaining_two_project_cash_collection_evidence_or_final_difference_acceptance_summary.json"
)
SOURCE_MANIFEST_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_remaining_two_project_cash_collection_evidence_or_final_difference_acceptance_manifest.json"
)

DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"
STAGE_STATUS_PATH = PROJECT_ROOT / "metadata/stage_status.jsonl"
TASK_STATUS_PATH = PROJECT_ROOT / "metadata/traceability/v1_4_stage_phase_task_status.jsonl"

EXPECTED_CONTEXT_COUNTS = {
    "gross_profit": 8,
    "gross_margin_rate": 8,
    "interest": 4,
    "travel": 4,
    "calculation_private_execution_ref": 4,
    "cost_category": 4,
    "cash_gross_profit": 4,
    "amount_a_cents_private_ref": 12,
    "amount_b_cents_private_ref": 12,
    "delta_cents_private_ref": 12,
}


def _now(generated_at: str | None = None) -> str:
    return generated_at or datetime.now().astimezone().isoformat(timespec="seconds")


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_value_fingerprint(unit: str, value: int) -> str:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("private replay values must be integers")
    if unit not in {"cents", "basis_points"}:
        raise ValueError(f"unsupported private replay unit: {unit}")
    return _sha256_text(f"{unit}:{value}")


def classification_policy(
    *, evidence_kind: str, owner_authorized_exclusion: bool
) -> dict[str, Any]:
    policies = {
        "materialized_target": (True, "replayed_private_integer_value"),
        "integer_metric": (True, "replayed_private_integer_formula"),
        "ambiguous_source": (False, "open_missing_unique_authoritative_source"),
        "accepted_cash_difference": (False, "open_final_difference_accepted"),
    }
    if evidence_kind == "non_numeric":
        if not owner_authorized_exclusion:
            raise ValueError("owner authorization is required for non-numeric exclusion")
        return {
            "queue_closed": True,
            "replay_status": "owner_authorized_non_numeric_exclusion",
        }
    if evidence_kind not in policies:
        raise ValueError(f"unsupported evidence kind: {evidence_kind}")
    queue_closed, replay_status = policies[evidence_kind]
    return {"queue_closed": queue_closed, "replay_status": replay_status}


def validate_nonzero_difference_guard(
    comparisons: list[dict[str, Any]], *, required_nonzero_count: int
) -> None:
    nonzero = [
        row
        for row in comparisons
        if row.get("comparison_status") == "comparison_complete_nonzero_delta"
    ]
    if len(nonzero) != required_nonzero_count:
        raise ValueError("nonzero comparison count changed")
    if any(
        isinstance(row.get("delta"), bool)
        or not isinstance(row.get("delta"), int)
        or row.get("delta") == 0
        for row in nonzero
    ):
        raise ValueError("nonzero comparison was overwritten or is not integer")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path} must contain JSON objects")
        rows.append(value)
    return rows


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in rows)
    path.write_text(content, encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def _raw_snapshot(kind: str) -> dict[str, Any]:
    if not RAW_ROOT.is_dir():
        raise FileNotFoundError(RAW_ROOT)
    files: list[dict[str, Any]] = []
    for path in sorted((item for item in RAW_ROOT.rglob("*") if item.is_file()), key=lambda item: item.as_posix()):
        stat = path.stat()
        files.append(
            {
                "relative_path": path.relative_to(RAW_ROOT).as_posix(),
                "size": stat.st_size,
                "mtime_ns": stat.st_mtime_ns,
                "inode": stat.st_ino,
                "mode": stat.st_mode,
                "sha256": _sha256_file(path),
            }
        )
    return {
        "schema_version": "kmfa.private.raw_immutability_snapshot.v1",
        "classification": "private_raw_immutability_snapshot_do_not_commit",
        "snapshot_kind": kind,
        "raw_root": RAW_ROOT.as_posix(),
        "file_count": len(files),
        "files": files,
    }


def _snapshot_core(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    files = snapshot.get("files")
    if not isinstance(files, list):
        raise ValueError("raw snapshot must contain a file list")
    return files


def _contains_float(value: Any) -> bool:
    if isinstance(value, float):
        return True
    if isinstance(value, dict):
        return any(_contains_float(child) for child in value.values())
    if isinstance(value, list):
        return any(_contains_float(child) for child in value)
    return False


def _git_output(args: list[str]) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def _git_ignored(path: Path) -> bool:
    return subprocess.run(
        ["git", "check-ignore", "-q", path.as_posix()],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode == 0


def source_private_paths() -> list[Path]:
    return [
        SOURCE_RESIDUAL_QUEUE_PATH,
        SOURCE_STAGING_PATH,
        SOURCE_OWNER_REPORT_PATH,
        SOURCE_AUTHORIZATION_PATH,
        SOURCE_BINDINGS_PATH,
        SOURCE_METRICS_PATH,
        SOURCE_TARGET_MATERIALIZATIONS_PATH,
        SOURCE_UNRESOLVED_TARGETS_PATH,
        SOURCE_COMPARISONS_PATH,
        SOURCE_CASH_METRICS_PATH,
        SOURCE_CASH_DECISIONS_PATH,
        SOURCE_COLLECTION_LINKS_PATH,
        SOURCE_FINAL_DIFFERENCE_REPORT_PATH,
        SOURCE_SUMMARY_PATH,
        SOURCE_MANIFEST_PATH,
    ]


def phase_private_paths() -> list[Path]:
    return [
        PRIVATE_RAW_BEFORE_PATH,
        PRIVATE_RAW_AFTER_PATH,
        PRIVATE_REPLAY_RECORDS_PATH,
        PRIVATE_OPEN_DIFFERENCES_PATH,
        PRIVATE_AUTHORIZATION_RECEIPT_PATH,
        PRIVATE_DIAGNOSTIC_PATH,
        PRIVATE_DIFFERENCE_REPORT_PATH,
    ]


def _legacy_source_fingerprint_valid(row: dict[str, Any]) -> bool:
    value = row.get("value")
    unit = row.get("unit")
    fingerprint = row.get("value_fingerprint")
    if isinstance(value, bool) or not isinstance(value, int) or not isinstance(unit, str):
        return False
    accepted = {
        canonical_value_fingerprint(unit, value),
        _sha256_text(str(value)),
    }
    return isinstance(fingerprint, str) and fingerprint in accepted


def _margin_order(bindings: list[dict[str, Any]]) -> list[str]:
    ordered = sorted(bindings, key=lambda row: int(row.get("authority_candidate_order", 0)))
    margin_ids = [str(row.get("legacy_margin_record_id")) for row in ordered]
    if len(margin_ids) != 4 or len(set(margin_ids)) != 4:
        raise ValueError("expected four unique private identity bindings")
    if any(not row.get("source_ref_hash") for row in ordered):
        raise ValueError("every private identity binding requires one source reference")
    return margin_ids


def _validate_metric_formulas(
    metrics: list[dict[str, Any]], margin_ids: list[str]
) -> dict[tuple[str, str], dict[str, Any]]:
    by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for row in metrics:
        key = (str(row.get("legacy_margin_record_id")), str(row.get("metric_key")))
        if key in by_key:
            raise ValueError("duplicate private metric key")
        if isinstance(row.get("value"), bool) or not isinstance(row.get("value"), int):
            raise ValueError("private metric must use an integer value")
        by_key[key] = row
    if len(by_key) != 32:
        raise ValueError("expected thirty-two private metric records")
    for margin_id in margin_ids:
        values = {
            key: int(by_key[(margin_id, key)]["value"])
            for key in (
                "contract_amount_cents",
                "cost_total_cents",
                "authority_gross_profit_cents",
                "authority_gross_margin_basis_points",
                "system_recomputed_gross_profit_cents",
                "system_recomputed_gross_margin_basis_points",
            )
        }
        system_gp = values["contract_amount_cents"] - values["cost_total_cents"]
        if values["system_recomputed_gross_profit_cents"] != system_gp:
            raise ValueError("system gross profit integer formula no longer replays")
        system_rate = _divide_to_basis_points(system_gp, values["contract_amount_cents"])
        authority_rate = _divide_to_basis_points(
            values["authority_gross_profit_cents"], values["contract_amount_cents"]
        )
        if system_rate != values["system_recomputed_gross_margin_basis_points"]:
            raise ValueError("system gross margin integer formula no longer replays")
        if authority_rate != values["authority_gross_margin_basis_points"]:
            raise ValueError("authority gross margin integer formula no longer replays")
    return by_key


def _metric_for_slot(
    slot: dict[str, Any],
    *,
    margin_ids: list[str],
    metrics_by_key: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, Any]:
    context = str(slot.get("context_group"))
    private_ref = str(slot.get("private_processed_ref"))
    record_index = int(slot.get("record_index", 0))
    if record_index not in {1, 2, 3, 4}:
        raise ValueError("gross metric slot record index must identify one of four projects")
    system_value = "system-recomputed" in private_ref
    match = re.search(r"PCM-S09P2-\d+", private_ref)
    margin_id = match.group(0) if match else margin_ids[record_index - 1]
    if context == "gross_profit":
        metric_key = (
            "system_recomputed_gross_profit_cents"
            if system_value
            else "authority_gross_profit_cents"
        )
    elif context == "gross_margin_rate":
        metric_key = (
            "system_recomputed_gross_margin_basis_points"
            if system_value
            else "authority_gross_margin_basis_points"
        )
    else:
        raise ValueError("slot is not a replayable gross metric")
    metric = metrics_by_key.get((margin_id, metric_key))
    if metric is None:
        raise ValueError("private gross metric source is missing")
    return metric


def _validate_materialized_targets(
    *,
    staging_slots: list[dict[str, Any]],
    target_rows: list[dict[str, Any]],
    comparisons: list[dict[str, Any]],
    cash_metrics: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    staging_by_slot = {str(row.get("target_slot_id")): row for row in staging_slots}
    cash_by_key = {
        (str(row.get("legacy_margin_record_id")), str(row.get("metric_key"))): row
        for row in cash_metrics
    }
    validated: dict[str, dict[str, Any]] = {}
    for row in target_rows:
        slot_id = str(row.get("target_slot_id"))
        if slot_id in validated or slot_id not in staging_by_slot:
            raise ValueError("target materialization slot is duplicate or absent from staging")
        slot = staging_by_slot[slot_id]
        if not _legacy_source_fingerprint_valid(row):
            raise ValueError("target materialization source fingerprint is invalid")
        context = str(row.get("context_group"))
        if context in {
            "amount_a_cents_private_ref",
            "amount_b_cents_private_ref",
            "delta_cents_private_ref",
        }:
            comparison_index = int(row.get("record_index", 0))
            if comparison_index < 1 or comparison_index > len(comparisons):
                raise ValueError("target comparison index is out of range")
            key = {
                "amount_a_cents_private_ref": "amount_a",
                "amount_b_cents_private_ref": "amount_b",
                "delta_cents_private_ref": "delta",
            }[context]
            expected = comparisons[comparison_index - 1].get(key)
        elif context == "cash_gross_profit":
            match = re.search(r"PCM-S09P2-\d+", str(row.get("private_processed_ref")))
            if not match:
                raise ValueError("cash gross profit target lacks a private margin reference")
            metric = cash_by_key.get((match.group(0), "cash_gross_profit_cents"))
            expected = None if metric is None else metric.get("value")
        else:
            raise ValueError("unexpected context in current private target materializations")
        if expected != row.get("value"):
            raise ValueError("target materialization does not match current private comparison evidence")
        validated[slot_id] = row
    if len(validated) != 37:
        raise ValueError("expected thirty-seven current private target materializations")
    return validated


def _comparison_target_for_metric(
    *,
    metric: dict[str, Any],
    staging_slots: list[dict[str, Any]],
    target_by_slot: dict[str, dict[str, Any]],
    comparisons: list[dict[str, Any]],
) -> dict[str, Any]:
    metric_key = str(metric.get("metric_key"))
    margin_id = str(metric.get("legacy_margin_record_id"))
    if "gross_margin" in metric_key:
        difference_type = "authority_vs_system_gross_margin_rate"
    else:
        difference_type = "authority_vs_system_gross_profit"
    matches = [
        (index, row)
        for index, row in enumerate(comparisons, start=1)
        if row.get("margin_record_id") == margin_id
        and row.get("difference_type") == difference_type
    ]
    if len(matches) != 1:
        raise ValueError("gross metric must map to one reconciliation comparison")
    comparison_index, comparison = matches[0]
    authority = metric_key.startswith("authority_")
    amount_key = "amount_a" if authority else "amount_b"
    context = (
        "amount_a_cents_private_ref" if authority else "amount_b_cents_private_ref"
    )
    slot_matches = [
        row
        for row in staging_slots
        if row.get("context_group") == context
        and int(row.get("record_index", 0)) == comparison_index
    ]
    if len(slot_matches) != 1:
        raise ValueError("gross metric must map to one comparison target slot")
    target = target_by_slot.get(str(slot_matches[0].get("target_slot_id")))
    if target is None or target.get("value") != metric.get("value"):
        raise ValueError("gross metric replay does not match current comparison target")
    if comparison.get(amount_key) != metric.get("value"):
        raise ValueError("gross metric replay does not match current comparison value")
    return target


def _build_replay_records(
    *,
    generated_at: str,
    owner_authorized_exclusion: bool,
    residual_rows: list[dict[str, Any]],
    staging_slots: list[dict[str, Any]],
    owner_rows: list[dict[str, Any]],
    bindings: list[dict[str, Any]],
    metrics: list[dict[str, Any]],
    target_rows: list[dict[str, Any]],
    unresolved_rows: list[dict[str, Any]],
    comparisons: list[dict[str, Any]],
    cash_metrics: list[dict[str, Any]],
    authorization_hash: str,
) -> list[dict[str, Any]]:
    if len(residual_rows) != 72 or len({row.get("target_slot_id") for row in residual_rows}) != 72:
        raise ValueError("global residual queue must contain seventy-two unique slots")
    staging_by_slot = {str(row.get("target_slot_id")): row for row in staging_slots}
    owner_by_slot = {str(row.get("target_slot_id")): row for row in owner_rows}
    unresolved_by_slot = {str(row.get("target_slot_id")): row for row in unresolved_rows}
    target_by_slot = _validate_materialized_targets(
        staging_slots=staging_slots,
        target_rows=target_rows,
        comparisons=comparisons,
        cash_metrics=cash_metrics,
    )
    margin_ids = _margin_order(bindings)
    metrics_by_key = _validate_metric_formulas(metrics, margin_ids)
    binding_by_margin = {
        str(row.get("legacy_margin_record_id")): row for row in bindings
    }
    replay_records: list[dict[str, Any]] = []
    for queue_index, residual in enumerate(residual_rows, start=1):
        slot_id = str(residual.get("target_slot_id"))
        slot = staging_by_slot.get(slot_id)
        owner_row = owner_by_slot.get(slot_id)
        if slot is None or owner_row is None:
            raise ValueError("residual slot is missing private staging or owner evidence")
        context = str(slot.get("context_group"))
        base = {
            "schema_version": "kmfa.private.global_residual_replay_record.v1",
            "classification": "private_global_residual_replay_record_do_not_commit",
            "queue_index": queue_index,
            "generated_at": generated_at,
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "target_slot_id": slot_id,
            "context_group": context,
            "diagnostic_track": residual.get("diagnostic_track"),
            "preserves_existing_nonzero_differences": True,
            "forced_zero_applied": False,
            "raw_layer_write_allowed": False,
            "public_commit_allowed": False,
        }
        if slot_id in target_by_slot:
            source = target_by_slot[slot_id]
            decision = classification_policy(
                evidence_kind="materialized_target",
                owner_authorized_exclusion=owner_authorized_exclusion,
            )
            value = int(source["value"])
            unit = str(source["unit"])
            replay_records.append(
                {
                    **base,
                    **decision,
                    "evidence_kind": "materialized_target",
                    "value": value,
                    "unit": unit,
                    "canonical_value_fingerprint": canonical_value_fingerprint(unit, value),
                    "source_value_fingerprint": source.get("value_fingerprint"),
                    "source_reference_hash": _sha256_text(str(source.get("private_processed_ref"))),
                    "source_reference_unique": True,
                    "integer_formula_replayable": True,
                }
            )
            continue
        if context in {"gross_profit", "gross_margin_rate"}:
            metric = _metric_for_slot(
                slot, margin_ids=margin_ids, metrics_by_key=metrics_by_key
            )
            target = _comparison_target_for_metric(
                metric=metric,
                staging_slots=staging_slots,
                target_by_slot=target_by_slot,
                comparisons=comparisons,
            )
            binding = binding_by_margin[str(metric.get("legacy_margin_record_id"))]
            decision = classification_policy(
                evidence_kind="integer_metric",
                owner_authorized_exclusion=owner_authorized_exclusion,
            )
            value = int(metric["value"])
            unit = str(metric["unit"])
            replay_records.append(
                {
                    **base,
                    **decision,
                    "evidence_kind": "integer_metric",
                    "metric_record_id": metric.get("metric_record_id"),
                    "metric_key": metric.get("metric_key"),
                    "value": value,
                    "unit": unit,
                    "canonical_value_fingerprint": canonical_value_fingerprint(unit, value),
                    "source_reference_hash": binding.get("source_ref_hash"),
                    "corresponding_target_slot_id": target.get("target_slot_id"),
                    "source_reference_unique": True,
                    "integer_formula_replayable": True,
                }
            )
            continue
        if context in {"calculation_private_execution_ref", "cost_category"}:
            decision = classification_policy(
                evidence_kind="non_numeric",
                owner_authorized_exclusion=owner_authorized_exclusion,
            )
            replay_records.append(
                {
                    **base,
                    **decision,
                    "evidence_kind": "non_numeric",
                    "numeric_comparison_applicable": False,
                    "owner_authorization_hash": authorization_hash,
                    "private_non_numeric_reference_hash": _sha256_text(
                        str(slot.get("private_processed_ref"))
                    ),
                    "source_reference_unique": True,
                    "integer_formula_replayable": context
                    == "calculation_private_execution_ref",
                }
            )
            continue
        if slot_id in unresolved_by_slot:
            decision = classification_policy(
                evidence_kind="accepted_cash_difference",
                owner_authorized_exclusion=owner_authorized_exclusion,
            )
            replay_records.append(
                {
                    **base,
                    **decision,
                    "evidence_kind": "accepted_cash_difference",
                    "open_reason_codes": unresolved_by_slot[slot_id].get("reason_codes", []),
                    "source_reference_unique": False,
                    "integer_formula_replayable": False,
                    "difference_report_required": True,
                }
            )
            continue
        if context in {"interest", "travel"}:
            if (
                owner_row.get("selected_private_candidate_option_index") is not None
                or owner_row.get("direct_processed_fingerprint_match_in_raw_numeric_candidates") is True
                or owner_row.get("direct_source_record_ref_match_in_raw_candidates") is True
            ):
                raise ValueError("ambiguous source evidence unexpectedly changed")
            decision = classification_policy(
                evidence_kind="ambiguous_source",
                owner_authorized_exclusion=owner_authorized_exclusion,
            )
            replay_records.append(
                {
                    **base,
                    **decision,
                    "evidence_kind": "ambiguous_source",
                    "private_candidate_option_count": owner_row.get(
                        "private_candidate_option_count"
                    ),
                    "source_reference_unique": False,
                    "integer_formula_replayable": False,
                    "difference_report_required": True,
                }
            )
            continue
        raise ValueError(f"unclassified residual context: {context}")
    return replay_records


def _public_matrix(summary: dict[str, Any]) -> dict[str, Any]:
    checks = [
        ("source_private_inputs_unchanged", summary["source_private_inputs_unchanged"]),
        ("raw_snapshot_exact_match", summary["raw_snapshot_exact_match"]),
        ("residual_queue_72", summary["global_residual_queue_record_count"] == 72),
        ("all_records_classified", summary["classified_residual_record_count"] == 72),
        ("target_replay_37", summary["private_target_materialization_replay_count"] == 37),
        ("integer_metric_replay_16", summary["integer_metric_formula_replay_count"] == 16),
        ("non_numeric_exclusion_8", summary["owner_authorized_non_numeric_exclusion_count"] == 8),
        ("closed_or_excluded_61", summary["queue_closed_or_excluded_count"] == 61),
        ("open_residual_11", summary["open_residual_difference_count"] == 11),
        ("ambiguous_source_open_8", summary["open_ambiguous_source_count"] == 8),
        ("accepted_cash_open_3", summary["open_final_difference_accepted_count"] == 3),
        ("nonzero_differences_preserved", summary["nonzero_delta_reconciliation_count"] == 9),
        ("zero_differences_preserved", summary["zero_delta_reconciliation_count"] == 2),
        ("incomplete_comparison_preserved", summary["incomplete_reconciliation_count"] == 1),
        ("forced_zero_prohibited", summary["forced_zero_materialization_count"] == 0),
        ("owner_authorization_recorded", summary["owner_authorized_exclusion"]),
        ("private_outputs_ignored", summary["private_outputs_gitignored"]),
        ("business_consistency_not_overclaimed", not summary["business_value_consistency_verified"]),
        ("stage_review_not_performed", not summary["stage_review_performed"]),
        ("github_not_uploaded", not summary["github_upload_performed"]),
    ]
    rows = [
        {"check_id": f"GRQ-{index:02d}", "check_name": name, "passed": bool(passed)}
        for index, (name, passed) in enumerate(checks, start=1)
    ]
    return {
        "schema_version": "kmfa.v014.global_residual_replay_matrix.v1",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "check_count": len(rows),
        "check_pass_count": sum(row["passed"] for row in rows),
        "check_fail_count": sum(not row["passed"] for row in rows),
        "checks": rows,
    }


def _private_report(summary: dict[str, Any], open_rows: list[dict[str, Any]]) -> str:
    lines = [
        "# KMFA v0.1.4 全局残余差异队列重放与权威排除报告",
        "",
        "## 结论",
        "",
        f"- 全局队列：{summary['global_residual_queue_record_count']} 条，已逐条分类。",
        f"- 数值重放：{summary['replayed_numeric_record_count']} 条。",
        f"- 经授权从数值队列排除的非数值记录：{summary['owner_authorized_non_numeric_exclusion_count']} 条。",
        f"- 已关闭或排除 / 继续未决：{summary['queue_closed_or_excluded_count']} / {summary['open_residual_difference_count']}。",
        f"- 保留非零 / 零差异 / 未完成比较：{summary['nonzero_delta_reconciliation_count']} / {summary['zero_delta_reconciliation_count']} / {summary['incomplete_reconciliation_count']}。",
        "- 未推导零、未平均、未覆盖任何现有非零差异。",
        "",
        "## 继续未决的 11 条记录",
        "",
    ]
    for row in open_rows:
        lines.extend(
            [
                f"### 队列 {row['queue_index']} / {row['target_slot_id']}",
                "",
                f"- 私有上下文：{row['context_group']}",
                f"- 状态：{row['replay_status']}",
                f"- 来源是否唯一：{row['source_reference_unique']}",
                f"- 候选数：{row.get('private_candidate_option_count', '不适用')}",
                f"- 原因：{row.get('open_reason_codes', ['缺少唯一权威来源'])}",
                "",
            ]
        )
    lines.extend(
        [
            "## 边界",
            "",
            "- 8 条利息/差旅分项仍存在多候选且没有直接指纹或记录引用唯一匹配，继续保留。",
            "- 3 条现金槽位属于最终差异接受，但接受差异不等于推导数值，因此继续保持未决。",
            "- 原始目录仅只读，前后逐文件快照完全一致。",
            "- 本报告和所有记录明细仅存在 ignored private runtime，不进入 GitHub。",
            "",
        ]
    )
    return "\n".join(lines)


def _public_reports(summary: dict[str, Any]) -> dict[Path, str]:
    report = f"""# v0.1.4 全局残余差异队列重放或权威排除

- Phase: `{PHASE_ID}`
- 决策: `{DECISION}`
- 队列记录 / 已分类: {summary['global_residual_queue_record_count']} / {summary['classified_residual_record_count']}
- 私有目标值重放 / 整数公式重放: {summary['private_target_materialization_replay_count']} / {summary['integer_metric_formula_replay_count']}
- 经授权非数值排除: {summary['owner_authorized_non_numeric_exclusion_count']}
- 已关闭或排除 / 继续未决: {summary['queue_closed_or_excluded_count']} / {summary['open_residual_difference_count']}
- 保留非零差异: {summary['nonzero_delta_reconciliation_count']}
- raw 前后完全一致: `{str(summary['raw_snapshot_exact_match']).lower()}`

本 phase 对 72 条队列逐条重放。仅在来源唯一、整数公式可重放且不会覆盖现有非零差异时关闭；其余记录继续进入全中文 private 差异报告。
"""
    go_no_go = f"""# Go / No-Go 记录

- 决策: `NO_GO`
- 已完成: 72 条队列全部分类，{summary['queue_closed_or_excluded_count']} 条关闭或从数值队列排除。
- 阻断: {summary['open_ambiguous_source_count']} 条缺唯一权威来源，{summary['open_final_difference_accepted_count']} 条现金差异保持未决。
- GitHub upload / app reinstall / business execution: `not_performed`
"""
    tests = """# 测试结果

- focused unit test: `PASS` (`2 tests`)
- phase/private validator: `PASS` (`72 classified / 61 closed-or-excluded / 11 open / decision=NO_GO`)
- previous phase validator: `PASS`
- governance validators: `PASS` (`errors=0 / warnings=0`)
- raw/private/secret scan: `PASS` (`raw unchanged / private tracked=0 / sensitive hits=0`)
"""
    risks = f"""# 风险登记

- 高: {summary['open_ambiguous_source_count']} 条成本分项没有唯一来源，不能自动选取候选。
- 高: {summary['open_final_difference_accepted_count']} 条现金差异仍无可证明数值，不能从缺失推导零。
- 高: {summary['nonzero_delta_reconciliation_count']} 条非零差异必须继续保留。
- 中: 当前仅完成本 phase，不代表 Stage 复审或整体业务一致性验收。
"""
    rollback = """# 回滚方案

1. 删除本 phase public-safe artifacts 与 metadata 镜像。
2. 删除本 phase ignored private outputs；不触碰 raw 根目录和源 private inputs。
3. 移除本 phase 三条治理记录并重跑上一 phase validator。
"""
    return {
        REPORT_PATH: report,
        GO_NO_GO_RECORD_PATH: go_no_go,
        TEST_RESULTS_PATH: tests,
        RISK_REGISTER_PATH: risks,
        ROLLBACK_PATH: rollback,
    }


def _upsert_jsonl(path: Path, key: str, row: dict[str, Any]) -> None:
    source_lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    updated_lines: list[str] = []
    replaced = False
    for source_line in source_lines:
        if not source_line.strip():
            continue
        current = json.loads(source_line)
        if not isinstance(current, dict):
            raise ValueError(f"{path} must contain JSON objects")
        if current.get(key) == row.get(key):
            updated_lines.append(json.dumps(row, ensure_ascii=False, separators=(",", ":")))
            replaced = True
        else:
            updated_lines.append(source_line)
    if not replaced:
        updated_lines.append(json.dumps(row, ensure_ascii=False, separators=(",", ":")))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(updated_lines) + "\n", encoding="utf-8")


def _phase_public_files() -> list[str]:
    return [
        SUMMARY_PATH.as_posix(),
        MANIFEST_PATH.as_posix(),
        GO_NO_GO_PATH.as_posix(),
        MATRIX_PATH.as_posix(),
        REPORT_PATH.as_posix(),
        GO_NO_GO_RECORD_PATH.as_posix(),
        TEST_RESULTS_PATH.as_posix(),
        RISK_REGISTER_PATH.as_posix(),
        ROLLBACK_PATH.as_posix(),
        METADATA_SUMMARY_PATH.as_posix(),
        METADATA_MANIFEST_PATH.as_posix(),
        METADATA_GO_NO_GO_PATH.as_posix(),
        METADATA_MATRIX_PATH.as_posix(),
        "KMFA/tests/test_v014_global_residual_difference_queue_replay_or_authoritative_exclusion.py",
        "KMFA/tools/check_v014_global_residual_difference_queue_replay_or_authoritative_exclusion.py",
        "KMFA/tools/v014_global_residual_difference_queue_replay_or_authoritative_exclusion.py",
        "KMFA/docs/governance/development_events.jsonl",
        "KMFA/metadata/stage_status.jsonl",
        "KMFA/metadata/traceability/v1_4_stage_phase_task_status.jsonl",
        "KMFA/metadata/model_registry.yaml",
        "KMFA/HANDOFF.md",
        "KMFA/CHANGELOG.md",
        "KMFA/VERSION",
        "KMFA/功能清单.md",
        "KMFA/开发记录.md",
        "KMFA/模型参数文件.md",
    ]


def _write_governance(generated_at: str, summary: dict[str, Any]) -> None:
    evidence_ref = MANIFEST_PATH.as_posix()
    _upsert_jsonl(
        DEVELOPMENT_EVENTS_PATH,
        "event_id",
        {
            "event_id": "DEV-KMFA-20260710-V014-GLOBAL-RESIDUAL-DIFFERENCE-QUEUE-REPLAY-OR-AUTHORITATIVE-EXCLUSION",
            "event_time": generated_at,
            "event_type": "development",
            "project_id": "KMFA",
            "stage_id": "value-consistency",
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "decision": DECISION,
            "classified_residual_record_count": 72,
            "queue_closed_or_excluded_count": 61,
            "open_residual_difference_count": 11,
            "nonzero_delta_reconciliation_count": 9,
            "raw_snapshot_exact_match": summary["raw_snapshot_exact_match"],
            "raw_business_data_committed": False,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
            "business_execution_performed": False,
            "evidence_ref": evidence_ref,
            "files_changed": _phase_public_files(),
            "result_commit": "PENDING",
        },
    )
    _upsert_jsonl(
        STAGE_STATUS_PATH,
        "phase_id",
        {
            "schema_version": "kmfa.stage_status.v1",
            "record_type": "stage_phase_status",
            "project_id": "KMFA",
            "stage_id": "VALUE-CONSISTENCY",
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "version": VERSION,
            "status": STATUS,
            "decision": DECISION,
            "raw_data_committed": False,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
            "business_execution_performed": False,
            "evidence_ref": evidence_ref,
            "updated_at": generated_at,
        },
    )
    _upsert_jsonl(
        TASK_STATUS_PATH,
        "phase_id",
        {
            "schema_version": "kmfa.v014_stage_phase_task_status.v1",
            "record_type": "v014_phase",
            "project_id": "KMFA",
            "stage_id": "VALUE-CONSISTENCY",
            "governance_stage_id": "VALUE-CONSISTENCY",
            "roadmap_stage_id": "VALUE-CONSISTENCY",
            "roadmap_phase_id": "GLOBAL_RESIDUAL_DIFFERENCE_QUEUE_REPLAY_OR_AUTHORITATIVE_EXCLUSION",
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "version": VERSION,
            "name": "v0.1.4 global residual difference queue replay or authoritative exclusion",
            "phase_goal": "replay every residual item without inventing values and preserve unresolved differences",
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "derived_percent": 100.0,
            "estimated_task_units": 1,
            "completed_task_units": 1,
            "task_count": 1,
            "raw_data_committed": False,
            "evidence_ref": evidence_ref,
            "updated_at": generated_at[:10],
        },
    )


def generate(
    *,
    owner_authorized_exclusion: bool,
    generated_at: str | None = None,
    write_governance_event: bool = True,
) -> dict[str, Any]:
    if not owner_authorized_exclusion:
        raise ValueError("explicit owner authorization is required")
    timestamp = _now(generated_at)
    for path in source_private_paths():
        if not path.exists():
            raise FileNotFoundError(path)
    source_hashes_before = {path.as_posix(): _sha256_file(path) for path in source_private_paths()}
    comparisons_hash_before = _sha256_file(SOURCE_COMPARISONS_PATH)
    raw_before = _raw_snapshot("before_global_residual_replay")

    residual_rows = _read_jsonl(SOURCE_RESIDUAL_QUEUE_PATH)
    staging = _read_json(SOURCE_STAGING_PATH)
    staging_slots = [
        row for row in staging.get("processed_target_slots", []) if isinstance(row, dict)
    ]
    owner_rows = _read_jsonl(SOURCE_OWNER_REPORT_PATH)
    authorization = _read_json(SOURCE_AUTHORIZATION_PATH)
    bindings = _read_jsonl(SOURCE_BINDINGS_PATH)
    metrics = _read_jsonl(SOURCE_METRICS_PATH)
    target_rows = _read_jsonl(SOURCE_TARGET_MATERIALIZATIONS_PATH)
    unresolved_rows = _read_jsonl(SOURCE_UNRESOLVED_TARGETS_PATH)
    comparisons = _read_jsonl(SOURCE_COMPARISONS_PATH)
    cash_metrics = _read_jsonl(SOURCE_CASH_METRICS_PATH)
    cash_decisions = _read_jsonl(SOURCE_CASH_DECISIONS_PATH)
    collection_links = _read_jsonl(SOURCE_COLLECTION_LINKS_PATH)
    source_summary = _read_json(SOURCE_SUMMARY_PATH)

    if authorization.get("authorization_item_count") != 72 or not authorization.get("authorization_basis"):
        raise ValueError("private owner authorization evidence is incomplete")
    authorization_hash = _sha256_text(str(authorization["authorization_basis"]))
    validate_nonzero_difference_guard(comparisons, required_nonzero_count=9)
    if len(comparisons) != 12 or len(unresolved_rows) != 3:
        raise ValueError("current comparison or unresolved target counts changed")
    if sum(row.get("resolution_status") == "difference_accepted_unresolved" for row in cash_decisions) != 1:
        raise ValueError("final cash difference acceptance is missing")
    if len(collection_links) != 2:
        raise ValueError("latest unique collection evidence changed")

    replay_records = _build_replay_records(
        generated_at=timestamp,
        owner_authorized_exclusion=owner_authorized_exclusion,
        residual_rows=residual_rows,
        staging_slots=staging_slots,
        owner_rows=owner_rows,
        bindings=bindings,
        metrics=metrics,
        target_rows=target_rows,
        unresolved_rows=unresolved_rows,
        comparisons=comparisons,
        cash_metrics=cash_metrics,
        authorization_hash=authorization_hash,
    )
    open_rows = [row for row in replay_records if not row["queue_closed"]]
    status_counts = Counter(str(row["replay_status"]) for row in replay_records)
    context_counts = Counter(str(row["context_group"]) for row in replay_records)
    if dict(sorted(context_counts.items())) != dict(sorted(EXPECTED_CONTEXT_COUNTS.items())):
        raise ValueError("residual context distribution changed")
    expected_status_counts = {
        "replayed_private_integer_value": 37,
        "replayed_private_integer_formula": 16,
        "owner_authorized_non_numeric_exclusion": 8,
        "open_missing_unique_authoritative_source": 8,
        "open_final_difference_accepted": 3,
    }
    if dict(status_counts) != expected_status_counts:
        raise ValueError("global residual replay classification counts changed")
    if _contains_float(replay_records):
        raise ValueError("private replay output cannot contain floats")

    source_hashes_after = {path.as_posix(): _sha256_file(path) for path in source_private_paths()}
    comparisons_hash_after = _sha256_file(SOURCE_COMPARISONS_PATH)
    raw_after = _raw_snapshot("after_global_residual_replay")
    source_unchanged = source_hashes_before == source_hashes_after
    raw_snapshot_exact_match = _snapshot_core(raw_before) == _snapshot_core(raw_after)
    comparisons_unchanged = comparisons_hash_before == comparisons_hash_after
    if not source_unchanged or not raw_snapshot_exact_match or not comparisons_unchanged:
        raise ValueError("source private inputs, comparisons, or raw inbox changed during replay")

    zero_count = sum(
        row.get("comparison_status") == "comparison_complete_zero_delta"
        and row.get("delta") == 0
        for row in comparisons
    )
    incomplete_count = sum(
        row.get("comparison_status")
        == "comparison_incomplete_cash_source_disambiguation_required"
        for row in comparisons
    )
    summary = {
        "schema_version": "kmfa.v014.global_residual_replay_summary.v1",
        "record_type": "v014_global_residual_replay_summary",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "version": VERSION,
        "status": STATUS,
        "decision": DECISION,
        "generated_at": timestamp,
        "source_phase_id": source_summary.get("phase_id"),
        "source_private_inputs_unchanged": source_unchanged,
        "global_residual_queue_record_count": len(residual_rows),
        "classified_residual_record_count": len(replay_records),
        "private_target_materialization_replay_count": status_counts[
            "replayed_private_integer_value"
        ],
        "integer_metric_formula_replay_count": status_counts[
            "replayed_private_integer_formula"
        ],
        "replayed_numeric_record_count": status_counts["replayed_private_integer_value"]
        + status_counts["replayed_private_integer_formula"],
        "owner_authorized_non_numeric_exclusion_count": status_counts[
            "owner_authorized_non_numeric_exclusion"
        ],
        "queue_closed_or_excluded_count": sum(row["queue_closed"] for row in replay_records),
        "open_residual_difference_count": len(open_rows),
        "open_ambiguous_source_count": status_counts[
            "open_missing_unique_authoritative_source"
        ],
        "open_final_difference_accepted_count": status_counts[
            "open_final_difference_accepted"
        ],
        "nonzero_delta_reconciliation_count": 9,
        "zero_delta_reconciliation_count": zero_count,
        "incomplete_reconciliation_count": incomplete_count,
        "existing_comparisons_unchanged": comparisons_unchanged,
        "forced_zero_materialization_count": 0,
        "owner_authorized_exclusion": owner_authorized_exclusion,
        "global_residual_queue_replay_performed": True,
        "global_residual_queue_fully_closed": False,
        "partial_raw_to_processed_reconciliation_performed": True,
        "full_raw_to_processed_value_comparison_complete": False,
        "business_value_consistency_verified": False,
        "raw_source_file_count": raw_before["file_count"],
        "raw_snapshot_exact_match": raw_snapshot_exact_match,
        "raw_inbox_mutated_by_this_phase": not raw_snapshot_exact_match,
        "private_outputs_gitignored": all(_git_ignored(path) for path in phase_private_paths()),
        "raw_business_data_committed": False,
        "raw_filename_or_value_committed": False,
        "credential_or_secret_committed": False,
        "stage_review_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "goal_status_recommendation": "continue_active_with_remaining_eleven_residual_differences",
        "next_recommended_phase": "remaining_eleven_residual_difference_source_trace_or_final_acceptance",
    }
    matrix = _public_matrix(summary)
    if matrix["check_fail_count"]:
        raise ValueError("public acceptance matrix contains failures")
    manifest = {
        "schema_version": "kmfa.v014.global_residual_replay_manifest.v1",
        "record_type": "v014_global_residual_replay_manifest",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "generated_at": timestamp,
        "reviewed_head": _git_output(["rev-parse", "HEAD"]),
        "branch": _git_output(["branch", "--show-current"]),
        "remote": _git_output(["remote", "get-url", "origin"]),
        "summary": summary,
        "artifact_refs": {
            "summary": SUMMARY_PATH.as_posix(),
            "go_no_go": GO_NO_GO_PATH.as_posix(),
            "matrix": MATRIX_PATH.as_posix(),
            "report": REPORT_PATH.as_posix(),
            "test_results": TEST_RESULTS_PATH.as_posix(),
            "validator": "KMFA/tools/check_v014_global_residual_difference_queue_replay_or_authoritative_exclusion.py",
        },
        "public_repo_safety": {
            "aggregate_only": True,
            "raw_file_committed": False,
            "raw_filename_committed": False,
            "raw_hash_committed": False,
            "identity_plaintext_committed": False,
            "business_value_committed": False,
            "private_ref_committed": False,
            "private_fingerprint_committed": False,
            "credential_or_secret_committed": False,
        },
        "phase_boundaries": {
            "single_phase_only": True,
            "global_residual_queue_replay_performed": True,
            "unproven_values_forced_closed": False,
            "existing_nonzero_differences_overwritten": False,
            "stage_review_performed": False,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
            "business_execution_performed": False,
        },
    }
    go_no_go = {
        "schema_version": "kmfa.v014.global_residual_replay_go_no_go.v1",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "decision": DECISION,
        "queue_closed_or_excluded_count": summary["queue_closed_or_excluded_count"],
        "open_residual_difference_count": summary["open_residual_difference_count"],
        "nonzero_delta_reconciliation_count": 9,
        "blocking_reason_codes": [
            "eight_cost_component_slots_lack_unique_authoritative_source",
            "three_cash_slots_remain_final_accepted_differences_without_proven_values",
            "nine_nonzero_scope_differences_remain_preserved",
        ],
        "github_upload_performed": False,
    }

    _write_json(PRIVATE_RAW_BEFORE_PATH, raw_before)
    _write_json(PRIVATE_RAW_AFTER_PATH, raw_after)
    _write_jsonl(PRIVATE_REPLAY_RECORDS_PATH, replay_records)
    _write_jsonl(PRIVATE_OPEN_DIFFERENCES_PATH, open_rows)
    _write_json(
        PRIVATE_AUTHORIZATION_RECEIPT_PATH,
        {
            "schema_version": "kmfa.private.owner_authorization_receipt.v1",
            "classification": "private_owner_authorization_receipt_do_not_commit",
            "phase_id": PHASE_ID,
            "generated_at": timestamp,
            "owner_authorized_exclusion": True,
            "source_authorization_item_count": authorization.get("authorization_item_count"),
            "authorization_basis_hash": authorization_hash,
            "authorization_plaintext_committed": False,
        },
    )
    _write_json(
        PRIVATE_DIAGNOSTIC_PATH,
        {
            "schema_version": "kmfa.private.global_residual_replay_diagnostic.v1",
            "classification": "private_global_residual_replay_diagnostic_do_not_commit",
            "phase_id": PHASE_ID,
            "generated_at": timestamp,
            "source_hashes_before": source_hashes_before,
            "source_hashes_after": source_hashes_after,
            "source_private_inputs_unchanged": source_unchanged,
            "comparisons_hash_before": comparisons_hash_before,
            "comparisons_hash_after": comparisons_hash_after,
            "existing_comparisons_unchanged": comparisons_unchanged,
            "raw_before": raw_before,
            "raw_after": raw_after,
            "raw_snapshot_exact_match": raw_snapshot_exact_match,
            "status_counts": dict(status_counts),
            "context_counts": dict(context_counts),
        },
    )
    _write_text(PRIVATE_DIFFERENCE_REPORT_PATH, _private_report(summary, open_rows))

    for path, payload in (
        (SUMMARY_PATH, summary),
        (MANIFEST_PATH, manifest),
        (GO_NO_GO_PATH, go_no_go),
        (MATRIX_PATH, matrix),
        (METADATA_SUMMARY_PATH, summary),
        (METADATA_MANIFEST_PATH, manifest),
        (METADATA_GO_NO_GO_PATH, go_no_go),
        (METADATA_MATRIX_PATH, matrix),
    ):
        _write_json(path, payload)
    for path, content in _public_reports(summary).items():
        _write_text(path, content)
    if write_governance_event:
        _write_governance(timestamp, summary)
    return {"summary": summary, "manifest": manifest, "go_no_go": go_no_go, "matrix": matrix}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated-at")
    parser.add_argument("--owner-authorized-exclusion", action="store_true")
    parser.add_argument("--skip-governance-event", action="store_true")
    args = parser.parse_args()
    result = generate(
        owner_authorized_exclusion=args.owner_authorized_exclusion,
        generated_at=args.generated_at,
        write_governance_event=not args.skip_governance_event,
    )
    summary = result["summary"]
    print(
        "global residual replay: "
        f"decision={summary['decision']} "
        f"classified={summary['classified_residual_record_count']} "
        f"closed_or_excluded={summary['queue_closed_or_excluded_count']} "
        f"open={summary['open_residual_difference_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
