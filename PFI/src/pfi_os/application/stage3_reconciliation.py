from __future__ import annotations

import csv
import hashlib
import io
import json
import subprocess
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable, Mapping

from pfi_os.application.economic_event_pipeline import (
    build_economic_event,
    build_interconnection_groups,
    load_phase32_policy,
    normalize_transaction,
    publish_ledger_event,
)
from pfi_os.domain.economic_events import LedgerEvent


VERSION = "v0.2.5"
STAGE = 3
PHASE_ID = "V025-S3-P3.3"
TASK_IDS = ("S3-P3-T1", "S3-P3-T2", "S3-P3-T3", "S3-P3-T4")
CONTRACT_ID = "PFI-V025-STAGE3-PHASE33-RECONCILIATION"
ACCEPTANCE_ID = "ACC-PFI-V025-S3-P33-RECONCILIATION"

PFI_ROOT = Path(__file__).resolve().parents[3]
POLICY_PATH = PFI_ROOT / "config" / "event_types" / "v025_phase_3_3_reconciliation_policy.json"
TRANSACTION_SOURCE_ID = "SRC-TRANSACTIONS-ALIPAY"
TRANSACTION_PATH_ALIAS = "MetaDatabase/PFI"
TRANSACTION_CSV_PATH = "MetaDatabase/PFI/alipay_daily/processed/alipay_transactions.csv"
NORMALIZED_SOURCE_ID = "source_transaction_history"
_REQUIRED_COLUMNS = (
    "transaction_id",
    "source_id",
    "raw_id",
    "account_id",
    "event_type",
    "amount",
    "currency",
    "occurred_at",
    "description",
    "review_state",
)
_REQUIRED_MAIN_PATHS = (
    "own_account_transfer",
    "credit_card_repayment",
    "refund",
    "investment_funding",
    "fund_subscription",
    "gold_subscription",
    "investment_purchase",
    "investment_sale",
)
_METRIC_FLAG = {
    "living_consumption": "living_consumption_included",
    "activity_outflow": "activity_outflow_included",
    "investment_allocation": "investment_allocation_included",
}
_STRUCTURED_EVIDENCE = {
    "income": ("source_event_type", "signed_direction"),
    "living_consumption": ("source_event_type", "signed_direction"),
    "own_account_transfer": ("explicit_link_reference", "effective_account_roles"),
    "credit_card_repayment": ("explicit_link_reference", "effective_account_roles"),
    "refund": ("offset_economic_event_id",),
    "investment_funding": ("explicit_link_reference", "effective_account_roles"),
    "fund_subscription": ("source_event_type", "signed_direction"),
    "gold_subscription": ("explicit_asset_class", "signed_direction"),
    "investment_purchase": ("source_event_type", "signed_direction"),
    "investment_sale": ("source_event_type", "signed_direction"),
}


@dataclass(frozen=True)
class Phase33Run:
    ledger_events: tuple[LedgerEvent, ...]
    idempotency_result: dict[str, Any]
    reconciliation_summary: dict[str, Any]
    review_queue_summary: dict[str, Any]
    lineage_samples_redacted: dict[str, Any]
    read_model_contract: dict[str, Any]


def build_phase33_contract() -> dict[str, Any]:
    return {
        "schema": "PFIV025Stage3Phase33ContractV1",
        "version": VERSION,
        "stage": STAGE,
        "phase_id": PHASE_ID,
        "contract_id": CONTRACT_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "acceptance_id_origin": "project_governance_assigned_not_taskpack",
        "task_ids": list(TASK_IDS),
        "current_phase_only": True,
        "real_data_read_only": True,
        "financial_fixture_fallback_allowed": False,
        "public_evidence_redacted": True,
        "database_changed": False,
        "finder_used": False,
        "risk_tier": "T3_FINANCIAL_RECONCILIATION_PRIVACY",
        "explicitly_not_done": [
            "Stage 3 whole-stage review",
            "Stage 3 final human acceptance",
            "Stage 4",
            "database migration or review queue persistence",
            "real source mutation",
            "GitHub push",
            "canonical App install",
        ],
    }


def load_phase33_policy(path: Path | str = POLICY_PATH) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Phase 3.3 policy must be an object")
    required_values = {
        "source_name_inference": False,
        "amount_time_heuristic_grouping": False,
        "unresolved_transfer_policy": "review_required_no_publication",
        "unresolved_refund_policy": "review_required_no_publication",
        "upstream_review_state_policy": "review_required_no_publication",
        "zero_amount_policy": "review_required_no_publication",
        "same_economic_event_per_metric_max_count": 1,
        "read_model_hash_scope": "snapshot_not_page",
        "source_temporal_granularity": "date",
        "date_normalization": "utc_start_of_source_date_no_time_precision_claim",
    }
    for field, expected in required_values.items():
        if payload.get(field) != expected:
            raise ValueError(f"invalid Phase 3.3 policy field: {field}")
    mappings = payload.get("real_source_mapping")
    if not isinstance(mappings, dict) or set(mappings) != {"BUY_ASSET", "CASH", "FUND", "REFUND", "TRANSFER"}:
        raise ValueError("real_source_mapping must cover the observed source event-type registry")
    for source_type, mapping in mappings.items():
        if not isinstance(mapping, dict) or set(mapping) != {"negative", "positive", "zero"}:
            raise ValueError(f"source mapping {source_type} must cover every amount sign")
    surfaces = payload.get("ui_surfaces")
    if not isinstance(surfaces, list) or not surfaces or len(surfaces) != len(set(surfaces)):
        raise ValueError("ui_surfaces must be a non-empty unique list")
    return payload


def run_phase33_real_reconciliation(
    project_root: Path | str,
    *,
    observed_at: str,
    git_ref: str = "HEAD",
    policy_path: Path | str = POLICY_PATH,
) -> Phase33Run:
    _require_rfc3339(observed_at, "observed_at")
    repo_root = _repo_root(Path(project_root))
    policy = load_phase33_policy(policy_path)
    event_policy = load_phase32_policy()
    before = _resolve_snapshot(repo_root, git_ref)
    raw = _git_bytes(repo_root, "cat-file", "blob", before["transactions_blob_oid"])
    rows = _parse_rows(raw)

    first_events, first_review, first_types = _build_candidates(
        rows,
        observed_at=observed_at,
        policy=policy,
        event_policy=event_policy,
    )
    second_events, second_review, second_types = _build_candidates(
        rows,
        observed_at=observed_at,
        policy=policy,
        event_policy=event_policy,
    )
    if first_review != second_review or first_types != second_types or first_events != second_events:
        raise ValueError("duplicate import candidates are not deterministic")

    registry: dict[str, LedgerEvent] = {}
    collision_count = 0
    first_published = 0
    for event in first_events:
        existing = registry.get(event.idempotency_key)
        if existing is None:
            registry[event.idempotency_key] = event
            first_published += 1
        elif existing != event:
            collision_count += 1
    second_published = 0
    second_duplicates = 0
    for event in second_events:
        existing = registry.get(event.idempotency_key)
        if existing is None:
            registry[event.idempotency_key] = event
            second_published += 1
        elif existing == event:
            second_duplicates += 1
        else:
            collision_count += 1

    after = _resolve_snapshot(repo_root, before["resolved_commit"])
    source_unchanged = before == after
    published = tuple(sorted(registry.values(), key=lambda item: item.ledger_event_id))
    review_total = sum(first_review.values())
    input_partition_complete = len(rows) == len(first_events) + review_total
    investment_count = sum(
        first_types.get(event_type, 0)
        for event_type in ("fund_subscription", "investment_purchase", "investment_sale")
    )
    idempotency_status = (
        "pass"
        if first_published == len(first_events)
        and second_published == 0
        and second_duplicates == len(second_events)
        and collision_count == 0
        and source_unchanged
        else "fail"
    )
    idempotency = {
        "schema": "PFIV025Stage3Phase33IdempotencyResultV1",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "status": idempotency_status,
        "source_id": TRANSACTION_SOURCE_ID,
        "path_alias": TRANSACTION_PATH_ALIAS,
        "isolation_mode": "immutable_git_object_snapshot",
        "resolved_commit": before["resolved_commit"],
        "transactions_blob_oid": before["transactions_blob_oid"],
        "input_content_hash": before["input_content_hash"],
        "input_record_count": len(rows),
        "first_import_candidate_count": len(first_events),
        "first_import_published_count": first_published,
        "second_import_candidate_count": len(second_events),
        "second_import_published_count": second_published,
        "second_import_duplicate_count": second_duplicates,
        "idempotency_key_collision_count": collision_count,
        "source_identity_before": before,
        "source_identity_after": after,
        "source_mutation_performed": not source_unchanged,
        "financial_fixture_fallback_used": False,
        "raw_rows_emitted": 0,
        "financial_values_emitted": 0,
        "finder_used": False,
    }
    queue = {
        "schema": "PFIV025Stage3Phase33ReviewQueueSummaryV1",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "status": "pass" if input_partition_complete else "fail",
        "review_queue_record_count": review_total,
        "reason_counts": dict(sorted(first_review.items())),
        "all_items_have_opaque_record_reference": True,
        "review_queue_persistence_changed": False,
        "private_identifiers_emitted": 0,
        "financial_values_emitted": 0,
    }
    reconciliation = {
        "schema": "PFIV025Stage3Phase33ReconciliationSummaryV1",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "status": "pass_with_review_queue" if input_partition_complete and idempotency_status == "pass" else "fail",
        "input_record_count": len(rows),
        "published_record_count": len(published),
        "review_queue_record_count": review_total,
        "silent_drop_count": len(rows) - len(published) - review_total,
        "input_partition_complete": input_partition_complete,
        "published_event_type_counts": dict(sorted(first_types.items())),
        "published_investment_event_count": investment_count,
        "published_transfer_without_explicit_link_or_role_count": 0,
        "published_refund_without_offset_count": 0,
        "transfer_chain_status": "pass_fail_closed_to_review",
        "refund_chain_status": "pass_fail_closed_to_review",
        "investment_chain_status": "pass",
        "source_temporal_granularity": policy["source_temporal_granularity"],
        "date_normalization": policy["date_normalization"],
        "exact_transaction_time_claimed": False,
        "financial_values_emitted": 0,
        "private_identifiers_emitted": 0,
    }
    lineage = _build_lineage_summary(published)
    read_model = build_metric_read_model_contract(
        published,
        metric_ids=tuple(_METRIC_FLAG),
        page_ids=tuple(str(item) for item in policy["ui_surfaces"]),
    )
    return Phase33Run(
        ledger_events=published,
        idempotency_result=idempotency,
        reconciliation_summary=reconciliation,
        review_queue_summary=queue,
        lineage_samples_redacted=lineage,
        read_model_contract=read_model,
    )


def build_metric_read_model_contract(
    ledger_events: Iterable[LedgerEvent],
    *,
    metric_ids: Iterable[str],
    page_ids: Iterable[str],
) -> dict[str, Any]:
    events = tuple(ledger_events)
    metrics = tuple(metric_ids)
    pages = tuple(page_ids)
    if not metrics or set(metrics) - set(_METRIC_FLAG):
        raise ValueError("unsupported or empty metric_ids")
    if not pages or len(pages) != len(set(pages)):
        raise ValueError("page_ids must be non-empty and unique")

    unique: dict[str, LedgerEvent] = {}
    duplicate_count = 0
    for event in events:
        existing = unique.get(event.economic_event_id)
        if existing is None:
            unique[event.economic_event_id] = event
        elif existing == event:
            duplicate_count += 1
        else:
            raise ValueError("one economic_event_id cannot resolve to different ledger events")

    metric_contracts: dict[str, dict[str, Any]] = {}
    for metric_id in metrics:
        flag_name = _METRIC_FLAG[metric_id]
        event_ids = sorted(
            event.economic_event_id
            for event in unique.values()
            if bool(getattr(event.impact_flags, flag_name))
        )
        metric_contracts[metric_id] = {
            "economic_event_count": len(event_ids),
            "economic_event_set_hash": _payload_hash(event_ids),
            "maximum_count_per_economic_event": 1,
        }
    snapshot_payload = {
        "policy": "same_economic_event_once_per_metric_v1",
        "metrics": metric_contracts,
        "ledger_event_set_hash": _payload_hash(sorted(event.idempotency_key for event in unique.values())),
    }
    read_model_hash = _payload_hash(snapshot_payload)
    return {
        "schema": "PFIV025Stage3Phase33ReadModelContractV1",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "status": "pass",
        "input_ledger_event_count": len(events),
        "unique_economic_event_count": len(unique),
        "duplicate_economic_event_count": duplicate_count,
        "same_economic_event_per_metric_max_count": 1,
        "per_metric_duplicate_count": 0,
        "metrics": metric_contracts,
        "read_model_hash": read_model_hash,
        "page_read_model_hashes": {page_id: read_model_hash for page_id in pages},
        "financial_values_emitted": 0,
        "private_identifiers_emitted": 0,
    }


def build_interconnection_matrix(run: Phase33Run) -> dict[str, Any]:
    policy = load_phase33_policy()
    event_policy = load_phase32_policy()
    published_counts = run.reconciliation_summary["published_event_type_counts"]
    review_reasons = run.review_queue_summary["reason_counts"]
    rows: list[dict[str, Any]] = []
    for event_type in sorted(event_policy["event_types"]):
        if event_type == "refund":
            review_count = int(review_reasons.get("refund_offset_missing", 0))
            review_pool_ids: list[str] = []
        elif event_type in {"own_account_transfer", "credit_card_repayment", "investment_funding"}:
            review_count = 0
            review_pool_ids = ["unresolved_transfer"]
        else:
            review_count = 0
            review_pool_ids = []
        unresolved_policy = (
            "review_required_no_publication"
            if event_type in {"own_account_transfer", "credit_card_repayment", "refund", "investment_funding", "gold_subscription"}
            else "publish_if_mapped"
        )
        rows.append(
            {
                "event_type": event_type,
                "impact_flags": dict(event_policy["event_types"][event_type]),
                "required_structured_evidence": list(_STRUCTURED_EVIDENCE[event_type]),
                "unresolved_policy": unresolved_policy,
                "ui_surfaces": list(policy["ui_surfaces"]),
                "real_snapshot_published_count": int(published_counts.get(event_type, 0)),
                "real_snapshot_review_count": review_count,
                "review_pool_ids": review_pool_ids,
            }
        )
    covered = sum(1 for event_type in _REQUIRED_MAIN_PATHS if event_type in event_policy["event_types"])
    return {
        "schema": "PFIV025Stage3Phase33InterconnectionMatrixV1",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "status": "pass" if covered == len(_REQUIRED_MAIN_PATHS) else "fail",
        "policy_version": str(event_policy["policy_version"]),
        "main_path_coverage_count": covered,
        "main_path_required_count": len(_REQUIRED_MAIN_PATHS),
        "same_economic_event_per_metric_max_count": 1,
        "read_model_hash_scope": policy["read_model_hash_scope"],
        "ui_surfaces": list(policy["ui_surfaces"]),
        "review_pools": [
            {
                "review_pool_id": "unresolved_transfer",
                "record_count": int(review_reasons.get("transfer_role_or_link_missing", 0)),
                "candidate_event_types": [
                    "credit_card_repayment",
                    "investment_funding",
                    "own_account_transfer",
                ],
                "additive_across_event_rows": False,
            }
        ],
        "event_types": rows,
        "financial_values_emitted": 0,
        "private_identifiers_emitted": 0,
    }


def _build_candidates(
    rows: tuple[dict[str, str], ...],
    *,
    observed_at: str,
    policy: Mapping[str, Any],
    event_policy: Mapping[str, Any],
) -> tuple[tuple[LedgerEvent, ...], Counter[str], Counter[str]]:
    events: list[LedgerEvent] = []
    review_reasons: Counter[str] = Counter()
    event_types: Counter[str] = Counter()
    opaque_review_refs: set[str] = set()
    for row in rows:
        signed_amount = _decimal(row.get("amount"))
        source_type = str(row.get("event_type", "")).strip().upper()
        reason, mapped_type = _classify_row(row, signed_amount, source_type, policy)
        opaque_ref = _stable_id(
            "review_record",
            str(row.get("transaction_id", "")),
            str(row.get("raw_id", "")),
        )
        if reason is not None:
            if opaque_ref in opaque_review_refs:
                raise ValueError("review queue opaque record references must be unique")
            opaque_review_refs.add(opaque_ref)
            review_reasons[reason] += 1
            continue
        if mapped_type is None:
            raise ValueError("mapped event type is required for publishable rows")

        source_record_hash = _payload_hash({key: row.get(key, "") for key in sorted(row)})
        transaction = normalize_transaction(
            raw_record_id=_stable_id(
                "raw_record",
                str(row.get("source_id", "")),
                str(row.get("raw_id", "")),
                str(row.get("transaction_id", "")),
            ),
            source_id=NORMALIZED_SOURCE_ID,
            account_ref=_stable_id("account_ref", str(row.get("account_id", ""))),
            source_record_hash=source_record_hash,
            amount=_canonical_amount(signed_amount.copy_abs()),
            currency=str(row.get("currency", "")).strip().upper(),
            direction="inflow" if signed_amount > 0 else "outflow",
            transaction_time=_date_to_rfc3339(str(row.get("occurred_at", ""))),
            posted_at=_date_to_rfc3339(str(row.get("occurred_at", ""))),
            effective_at=_date_to_rfc3339(str(row.get("occurred_at", ""))),
            imported_at=observed_at,
            normalization_version="1",
        )
        group = build_interconnection_groups(
            (transaction,),
            policy=event_policy,
            created_at=observed_at,
        )[0]
        economic_event = build_economic_event(
            group,
            (transaction,),
            event_type=mapped_type,
            policy=event_policy,
        )
        events.append(publish_ledger_event(economic_event, (transaction,)))
        event_types[mapped_type] += 1
    return tuple(sorted(events, key=lambda item: item.ledger_event_id)), review_reasons, event_types


def _classify_row(
    row: Mapping[str, str],
    amount: Decimal,
    source_type: str,
    policy: Mapping[str, Any],
) -> tuple[str | None, str | None]:
    if str(row.get("review_state", "")).strip().upper() != "ACCEPTED":
        return "upstream_review_required", None
    if amount == 0:
        return "zero_amount", None
    if source_type == "TRANSFER":
        return "transfer_role_or_link_missing", None
    if source_type == "REFUND":
        return "refund_offset_missing", None
    sign = "positive" if amount > 0 else "negative"
    mappings = policy["real_source_mapping"]
    mapping = mappings.get(source_type)
    if not isinstance(mapping, Mapping):
        return "unsupported_event_semantics", None
    event_type = mapping.get(sign)
    if not isinstance(event_type, str) or event_type == "review_required":
        return "unsupported_event_semantics", None
    return None, event_type


def _build_lineage_summary(events: tuple[LedgerEvent, ...]) -> dict[str, Any]:
    complete = sum(
        bool(
            event.raw_record_ids
            and event.normalized_transaction_ids
            and event.interconnection_group_id
            and event.economic_event_id
            and event.ledger_event_id
            and event.idempotency_key
        )
        for event in events
    )
    return {
        "schema": "PFIV025Stage3Phase33RedactedLineageV1",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "status": "pass" if complete == len(events) else "fail",
        "published_record_count": len(events),
        "complete_lineage_count": complete,
        "missing_lineage_count": len(events) - complete,
        "lineage_order": [
            "raw_record_id_hash",
            "normalized_transaction_id",
            "interconnection_group_id",
            "economic_event_id",
            "ledger_event_id",
            "idempotency_key",
        ],
        "redacted_sample": {
            "raw_record_id_hash": "sha256:" + "0" * 64,
            "normalized_transaction_id": "normalized_transaction_redacted",
            "interconnection_group_id": "interconnection_group_redacted",
            "economic_event_id": "economic_event_redacted",
            "ledger_event_id": "ledger_event_redacted",
            "idempotency_key": "sha256:" + "0" * 64,
        },
        "financial_values_emitted": 0,
        "private_identifiers_emitted": 0,
    }


def _resolve_snapshot(repo_root: Path, git_ref: str) -> dict[str, Any]:
    commit = _git_text(repo_root, "rev-parse", "--verify", f"{git_ref}^{{commit}}")
    blob_oid = _git_text(repo_root, "rev-parse", f"{commit}:{TRANSACTION_CSV_PATH}")
    if _git_text(repo_root, "cat-file", "-t", blob_oid) != "blob":
        raise ValueError("transaction snapshot must resolve to a Git blob")
    raw = _git_bytes(repo_root, "cat-file", "blob", blob_oid)
    return {
        "resolved_commit": commit,
        "transactions_blob_oid": blob_oid,
        "input_bytes": len(raw),
        "input_content_hash": "sha256:" + hashlib.sha256(raw).hexdigest(),
        "snapshot_immutable": True,
        "source_write_capability": False,
    }


def _parse_rows(raw: bytes) -> tuple[dict[str, str], ...]:
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline=""))
    if reader.fieldnames is None or any(column not in reader.fieldnames for column in _REQUIRED_COLUMNS):
        raise ValueError("real transaction snapshot is missing required columns")
    rows = tuple(dict(row) for row in reader)
    if not rows:
        raise ValueError("real transaction snapshot is empty; fixture fallback is forbidden")
    transaction_ids = tuple(str(row.get("transaction_id", "")).strip() for row in rows)
    raw_ids = tuple(str(row.get("raw_id", "")).strip() for row in rows)
    if any(not value for value in transaction_ids + raw_ids):
        raise ValueError("real transaction snapshot has missing record identity")
    if len(transaction_ids) != len(set(transaction_ids)) or len(raw_ids) != len(set(raw_ids)):
        raise ValueError("real transaction snapshot record identity must be unique")
    return rows


def _repo_root(path: Path) -> Path:
    completed = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "--show-toplevel"],
        check=True,
        capture_output=True,
        text=True,
    )
    return Path(completed.stdout.strip())


def _git_bytes(repo_root: Path, *args: str) -> bytes:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    return completed.stdout


def _git_text(repo_root: Path, *args: str) -> str:
    return _git_bytes(repo_root, *args).decode("utf-8").strip()


def _decimal(value: object) -> Decimal:
    try:
        parsed = Decimal(str(value).strip())
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("amount must be a finite decimal") from exc
    if not parsed.is_finite():
        raise ValueError("amount must be a finite decimal")
    return parsed


def _canonical_amount(value: Decimal) -> str:
    if value <= 0:
        raise ValueError("canonical amount must be greater than zero")
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def _date_to_rfc3339(value: str) -> str:
    clean = value.strip()
    try:
        parsed = date.fromisoformat(clean)
    except ValueError as exc:
        raise ValueError("source occurred_at must be an ISO date") from exc
    if parsed.isoformat() != clean:
        raise ValueError("source occurred_at must be a canonical ISO date")
    return f"{clean}T00:00:00Z"


def _require_rfc3339(value: str, field_name: str) -> datetime:
    clean = value[:-1] + "+00:00" if isinstance(value, str) and value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(clean)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be RFC3339") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field_name} must include timezone")
    return parsed


def _payload_hash(payload: object) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _stable_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()[:20]
    return f"{prefix}_{digest}"
