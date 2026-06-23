"""Stage 1 historical B1/arXiv report and email preview evidence builder."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from .config import DEFAULT_RECIPIENT, DEFAULT_TIMEZONE
from .contracts import stable_content_hash
from .stage1_b1_report import (
    STAGE1_B1_BOARD_ID,
    build_b1_report_email_package,
    validate_b1_report_email_package,
)


STAGE1_HISTORICAL_PREVIEW_MODEL_ID = "adp-stage1-historical-b1-previews-v1"
STAGE1_HISTORICAL_PREVIEW_SCHEMA_VERSION = 1
STAGE1_HISTORICAL_PREVIEW_ACCEPTANCE_ID = "ADP-ACC-S1-11-HISTORICAL-B1-PREVIEWS"
STAGE1_HISTORICAL_PREVIEW_REQUIRED_COUNT = 30
STAGE1_HISTORICAL_PREVIEW_MIN_UNIQUE_DATES = 30
STAGE1_HISTORICAL_PREVIEW_MIN_UNIQUE_SOURCE_IDS = 30
STAGE1_HISTORICAL_PREVIEW_ARTIFACT_KIND_COUNT = 5
STAGE1_HISTORICAL_PREVIEW_SOURCE_TYPE = "arxiv"
STAGE1_HISTORICAL_PREVIEW_SUPPORTED_INPUT_FORMATS = ("json_array", "jsonl", "json_object_with_daily_inputs")
STAGE1_HISTORICAL_PREVIEW_SIDE_EFFECT_KEYS = (
    "real_smtp_sent",
    "release_uploaded",
    "video_generated",
    "network_fetch_performed",
    "scheduler_enabled",
    "secret_values_logged",
)


_HISTORICAL_TOPICS = (
    {
        "category": "cs.AI",
        "title": "Causal Agent Memory for Robust Research Planning",
        "theme": "agent memory failure modes",
        "mechanism": "agent memory, planning feedback, and intervention tests",
    },
    {
        "category": "cs.CL",
        "title": "Evidence Grounded Retrieval for Long Form Explanation",
        "theme": "retrieval evidence teaching",
        "mechanism": "retrieval evidence, explanation structure, and citation pressure",
    },
    {
        "category": "cs.LG",
        "title": "Small Sample Model Selection under Distribution Shift",
        "theme": "distribution shift selection",
        "mechanism": "sample efficiency, validation drift, and failure detection",
    },
    {
        "category": "stat.ML",
        "title": "Uncertainty Calibration for Sequential Decision Systems",
        "theme": "uncertainty calibration",
        "mechanism": "posterior calibration, sequential decisions, and loss control",
    },
    {
        "category": "math.OC",
        "title": "Constrained Optimization with Recoverable Policy Updates",
        "theme": "recoverable optimization",
        "mechanism": "constraints, rollback paths, and stable policy improvement",
    },
    {
        "category": "physics.comp-ph",
        "title": "Simulation Fidelity in Multi Scale Complex Systems",
        "theme": "simulation fidelity",
        "mechanism": "multi scale simulation, fidelity gaps, and sensitivity checks",
    },
    {
        "category": "q-bio.NC",
        "title": "Adaptive Neural Signals for Learning and Control",
        "theme": "adaptive signal control",
        "mechanism": "adaptive signals, feedback loops, and control boundaries",
    },
    {
        "category": "econ.EM",
        "title": "Market Response Functions under Information Frictions",
        "theme": "market response functions",
        "mechanism": "market response, information friction, and measurable risk",
    },
    {
        "category": "eess.IV",
        "title": "Reliable Image Evidence Extraction for Scientific Workflows",
        "theme": "image evidence extraction",
        "mechanism": "image evidence, workflow reliability, and verification cost",
    },
    {
        "category": "quant-ph",
        "title": "Quantum Measurement Models for Noisy Learning Signals",
        "theme": "quantum noisy signals",
        "mechanism": "measurement noise, signal extraction, and uncertainty bounds",
    },
)


def load_historical_daily_inputs(path: str | Path) -> list[dict[str, Any]]:
    """Load S1-11 historical daily-input packages from JSON array, JSONL, or object wrapper."""

    source = Path(path)
    text = source.read_text(encoding="utf-8")
    stripped = text.strip()
    if not stripped:
        return []
    if stripped.startswith("[") or stripped.startswith("{"):
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            payload = None
        if payload is None:
            pass
        elif isinstance(payload, list):
            return [dict(item) for item in payload if isinstance(item, Mapping)]
        elif isinstance(payload, Mapping):
            for key in ("daily_inputs", "historical_inputs", "inputs"):
                values = payload.get(key)
                if isinstance(values, list):
                    return [dict(item) for item in values if isinstance(item, Mapping)]
            return [dict(payload)]
        else:
            return []
    rows: list[dict[str, Any]] = []
    for line in stripped.splitlines():
        value = line.strip()
        if not value:
            continue
        payload = json.loads(value)
        if isinstance(payload, Mapping):
            rows.append(dict(payload))
    return rows


def build_historical_b1_previews_report(
    historical_inputs: Sequence[Mapping[str, Any]],
    *,
    generated_at: str,
    recipient: str = DEFAULT_RECIPIENT,
    artifact_dir: str | Path | None = None,
    write: bool = False,
    required_count: int = STAGE1_HISTORICAL_PREVIEW_REQUIRED_COUNT,
) -> dict[str, Any]:
    """Build a 30-preview S1-11 B1 report/email evidence package from supplied inputs."""

    artifact_root = Path(artifact_dir) if artifact_dir is not None else None
    if write and artifact_root is None:
        return _blocked_report(generated_at=generated_at, reasons=["artifact_dir is required when write is true"])

    package_errors: list[str] = []
    previews: list[dict[str, Any]] = []
    content_ledger_updates: list[dict[str, Any]] = []
    artifact_files_written = 0
    future_leakage_count = 0
    future_leakage_refs: list[str] = []

    for index, payload in enumerate(historical_inputs):
        daily_input = _extract_daily_input(payload)
        leakage_refs = _future_leakage_refs(daily_input)
        future_leakage_count += len(leakage_refs)
        future_leakage_refs.extend(leakage_refs)
        package = build_b1_report_email_package(
            payload,
            generated_at=generated_at,
            recipient=recipient,
            artifact_dir=artifact_root,
            write=write,
        )
        errors = validate_b1_report_email_package(package)
        if errors or package.get("status") != "pass":
            package_errors.extend(f"preview[{index}]: {error}" for error in errors)
            package_errors.extend(
                f"preview[{index}]: {reason}" for reason in package.get("blocking_reasons", []) if reason
            )
        artifact_files = package.get("artifact_files") if isinstance(package.get("artifact_files"), Mapping) else {}
        artifact_files_written += len(artifact_files)
        preview = {
            "preview_index": index + 1,
            "date": package.get("date") or daily_input.get("date"),
            "source_id": package.get("source_id") or _source_id(daily_input),
            "status": package.get("status"),
            "report_id": package.get("report_id"),
            "email_id": package.get("email_id"),
            "email_subject": package.get("email_subject"),
            "content_hash": package.get("content_hash"),
            "claim_evidence_audit": package.get("claim_evidence_audit") or {},
            "critical_claim_coverage_percent": (
                package.get("claim_evidence_audit", {}).get("critical_claim_coverage_percent")
                if isinstance(package.get("claim_evidence_audit"), Mapping)
                else None
            ),
            "artifact_files": artifact_files,
            "side_effect_policy": package.get("side_effect_policy", {}),
            "future_leakage_refs": leakage_refs,
            "email_plain_sha256": stable_content_hash({"email_plain": package.get("email_plain", "")}),
            "report_markdown_sha256": stable_content_hash({"report_markdown": package.get("report_markdown", "")}),
        }
        previews.append(preview)
        if isinstance(package.get("content_ledger_update"), Mapping):
            content_ledger_updates.append(dict(package["content_ledger_update"]))

    date_values = [str(preview.get("date") or "") for preview in previews if preview.get("date")]
    source_values = [str(preview.get("source_id") or "") for preview in previews if preview.get("source_id")]
    content_hash_values = [
        str(preview.get("content_hash") or "") for preview in previews if preview.get("content_hash")
    ]
    email_id_values = [str(preview.get("email_id") or "") for preview in previews if preview.get("email_id")]
    pass_count = sum(1 for preview in previews if preview.get("status") == "pass")
    side_effect_policy = {key: False for key in STAGE1_HISTORICAL_PREVIEW_SIDE_EFFECT_KEYS}
    report: dict[str, Any] = {
        "model_id": STAGE1_HISTORICAL_PREVIEW_MODEL_ID,
        "schema_version": STAGE1_HISTORICAL_PREVIEW_SCHEMA_VERSION,
        "project_id": "arxiv-daily-push",
        "board_id": STAGE1_B1_BOARD_ID,
        "acceptance_id": STAGE1_HISTORICAL_PREVIEW_ACCEPTANCE_ID,
        "status": "pass",
        "generated_at": generated_at,
        "preview_count": len(previews),
        "required_preview_count": required_count,
        "pass_count": pass_count,
        "unique_date_count": len(set(date_values)),
        "unique_source_count": len(set(source_values)),
        "unique_source_id_count": len(set(source_values)),
        "unique_content_hash_count": len(set(content_hash_values)),
        "unique_email_id_count": len(set(email_id_values)),
        "future_leakage_count": future_leakage_count,
        "future_leakage_refs": future_leakage_refs,
        "package_status_counts": _status_counts(previews),
        "quality_gates": {
            "preview_count_equals_required": len(previews) == required_count,
            "unique_dates_at_least_required": len(set(date_values))
            >= STAGE1_HISTORICAL_PREVIEW_MIN_UNIQUE_DATES,
            "unique_source_ids_at_least_required": len(set(source_values))
            >= STAGE1_HISTORICAL_PREVIEW_MIN_UNIQUE_SOURCE_IDS,
            "all_packages_passed": pass_count == len(previews) and len(previews) > 0,
            "all_content_hashes_unique": _unique_nonempty(previews, "content_hash"),
            "all_email_ids_unique": _unique_nonempty(previews, "email_id"),
            "all_critical_claims_covered": all(
                preview.get("critical_claim_coverage_percent") == 100.0 for preview in previews
            ),
            "content_ledger_rows_match_preview_count": len(content_ledger_updates) == len(previews),
            "future_leakage_zero": future_leakage_count == 0,
            "artifact_kinds_per_preview": STAGE1_HISTORICAL_PREVIEW_ARTIFACT_KIND_COUNT,
            "artifact_files_written_match_expected": (
                not write
                or artifact_files_written
                == len(previews) * STAGE1_HISTORICAL_PREVIEW_ARTIFACT_KIND_COUNT
            ),
            "no_real_smtp_send": True,
            "no_release_upload": True,
            "no_video_generation": True,
            "no_network_fetch": True,
        },
        "side_effect_policy": side_effect_policy,
        "source_policy": {
            "source_type": STAGE1_HISTORICAL_PREVIEW_SOURCE_TYPE,
            "supported_input_formats": list(STAGE1_HISTORICAL_PREVIEW_SUPPORTED_INPUT_FORMATS),
            "offline_historical_fixture_only": True,
            "pdf_download_enabled": False,
            "bulk_harvest_enabled": False,
            "peer_review_claim_enabled": False,
            "video_required": False,
        },
        "previews": previews,
        "preview_records": previews,
        "content_ledger_updates": content_ledger_updates,
        "content_ledger_rows": content_ledger_updates,
        "artifact_manifest": {},
        "artifact_summary": {
            "write_enabled": write,
            "artifact_dir": str(artifact_root) if artifact_root is not None else "",
            "artifact_files_written": artifact_files_written,
            "manifest_path": "",
        },
        "blocking_reasons": package_errors,
    }
    validation_errors = validate_historical_b1_previews_report(report)
    if validation_errors:
        report["status"] = "blocked"
        report["blocking_reasons"] = sorted(set([*package_errors, *validation_errors]))
    if write and artifact_root is not None:
        manifest_ref = _write_manifest(report, artifact_root)
        report["artifact_manifest"] = manifest_ref
        report["artifact_summary"]["manifest_path"] = manifest_ref["path"]
        report["artifact_summary"]["manifest_sha256"] = manifest_ref["sha256"]
        report["artifact_summary"]["manifest_size_bytes"] = manifest_ref["size_bytes"]
    return report


def build_historical_b1_previews(
    *,
    generated_at: str,
    start_date: str = "2026-05-01",
    preview_count: int = STAGE1_HISTORICAL_PREVIEW_REQUIRED_COUNT,
    recipient: str = DEFAULT_RECIPIENT,
    artifact_dir: str | Path | None = None,
    write: bool = False,
) -> dict[str, Any]:
    """Build 30 deterministic historical B1 report/email previews without side effects."""

    start = _parse_date(start_date)
    if start is None:
        return _blocked_report(generated_at=generated_at, reasons=[f"invalid start_date: {start_date}"])
    artifact_root = Path(artifact_dir) if artifact_dir is not None else None
    if write and artifact_root is None:
        return _blocked_report(generated_at=generated_at, reasons=["artifact_dir is required when write is true"])

    historical_inputs = []
    for index in range(max(0, preview_count)):
        local_date = start + timedelta(days=index)
        historical_inputs.append(_historical_payload(index, local_date, generated_at=generated_at))
    return build_historical_b1_previews_report(
        historical_inputs,
        generated_at=generated_at,
        recipient=recipient,
        artifact_dir=artifact_root,
        write=write,
        required_count=STAGE1_HISTORICAL_PREVIEW_REQUIRED_COUNT,
    )


def validate_historical_b1_previews_report(report: Mapping[str, Any]) -> list[str]:
    """Validate the S1-11 historical B1 preview evidence package."""

    errors: list[str] = []
    if report.get("model_id") != STAGE1_HISTORICAL_PREVIEW_MODEL_ID:
        errors.append("model_id must be adp-stage1-historical-b1-previews-v1")
    if report.get("schema_version") != STAGE1_HISTORICAL_PREVIEW_SCHEMA_VERSION:
        errors.append("schema_version must be 1")
    if report.get("acceptance_id") != STAGE1_HISTORICAL_PREVIEW_ACCEPTANCE_ID:
        errors.append("acceptance_id must be ADP-ACC-S1-11-HISTORICAL-B1-PREVIEWS")
    if report.get("board_id") != STAGE1_B1_BOARD_ID:
        errors.append("board_id must be B1")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("status must be pass or blocked")

    records = report.get("previews")
    if not isinstance(records, list):
        errors.append("previews must be an array")
        records = []
    ledger_rows = report.get("content_ledger_updates")
    if not isinstance(ledger_rows, list):
        errors.append("content_ledger_updates must be an array")
        ledger_rows = []

    if len(records) != int(report.get("required_preview_count") or STAGE1_HISTORICAL_PREVIEW_REQUIRED_COUNT):
        errors.append("preview_count must be at least 30")
        errors.append("preview_count must equal required_preview_count")
    if report.get("preview_count") != len(records):
        errors.append("preview_count must match previews length")
    if report.get("pass_count") != len(records):
        errors.append("pass_count must match previews length")
    if report.get("unique_date_count", 0) < STAGE1_HISTORICAL_PREVIEW_MIN_UNIQUE_DATES:
        errors.append("unique_date_count must be at least 30")
    if report.get("unique_source_count", 0) < STAGE1_HISTORICAL_PREVIEW_MIN_UNIQUE_SOURCE_IDS:
        errors.append("unique_source_count must be at least 30")
    if report.get("unique_content_hash_count") != len(records):
        errors.append("unique_content_hash_count must match preview_count")
    if report.get("unique_email_id_count") != len(records):
        errors.append("unique_email_id_count must match preview_count")
    if report.get("future_leakage_count") != 0:
        errors.append("future leakage detected")

    gates = report.get("quality_gates")
    if not isinstance(gates, dict):
        errors.append("quality_gates must be an object")
    else:
        for key in (
            "preview_count_equals_required",
            "unique_dates_at_least_required",
            "unique_source_ids_at_least_required",
            "all_packages_passed",
            "all_content_hashes_unique",
            "all_email_ids_unique",
            "all_critical_claims_covered",
            "content_ledger_rows_match_preview_count",
            "future_leakage_zero",
            "artifact_files_written_match_expected",
            "no_real_smtp_send",
            "no_release_upload",
            "no_video_generation",
            "no_network_fetch",
        ):
            if gates.get(key) is not True:
                errors.append(f"quality_gates.{key} must be true")

    side_effects = report.get("side_effect_policy")
    if not isinstance(side_effects, dict):
        errors.append("side_effect_policy must be an object")
    else:
        for key in STAGE1_HISTORICAL_PREVIEW_SIDE_EFFECT_KEYS:
            if side_effects.get(key) is not False:
                errors.append(f"side_effect_policy.{key} must be false")

    source_policy = report.get("source_policy")
    if not isinstance(source_policy, dict):
        errors.append("source_policy must be an object")
    else:
        for key in (
            "offline_historical_fixture_only",
            "pdf_download_enabled",
            "bulk_harvest_enabled",
            "peer_review_claim_enabled",
            "video_required",
        ):
            expected = key == "offline_historical_fixture_only"
            if source_policy.get(key) is not expected:
                errors.append(f"source_policy.{key} must be {str(expected).lower()}")
        if source_policy.get("source_type") != STAGE1_HISTORICAL_PREVIEW_SOURCE_TYPE:
            errors.append("source_policy.source_type must be arxiv")

    for index, record in enumerate(records):
        if not isinstance(record, dict):
            errors.append(f"previews[{index}] must be an object")
            continue
        if record.get("status") != "pass":
            errors.append(f"previews[{index}].status must be pass")
        if record.get("critical_claim_coverage_percent") != 100.0:
            errors.append(f"previews[{index}].critical_claim_coverage_percent must be 100.0")
        policy = record.get("side_effect_policy")
        if not isinstance(policy, dict):
            errors.append(f"previews[{index}].side_effect_policy must be an object")
        elif any(policy.get(key) is not False for key in ("real_smtp_sent", "release_uploaded", "video_generated")):
            errors.append(f"previews[{index}].side_effect_policy must not contain side effects")
        if record.get("future_leakage_refs"):
            errors.append(f"previews[{index}].future_leakage_refs must be empty")

    if len(ledger_rows) != len(records):
        errors.append("content_ledger_updates length must match preview_count")
    for index, row in enumerate(ledger_rows):
        if not isinstance(row, dict):
            errors.append(f"content_ledger_rows[{index}] must be an object")
            continue
        if row.get("board_id") != STAGE1_B1_BOARD_ID:
            errors.append(f"content_ledger_rows[{index}].board_id must be B1")
        if row.get("email_state") != "preview_generated":
            errors.append(f"content_ledger_rows[{index}].email_state must be preview_generated")
        if row.get("email_sent_at") != "NOT_SENT_DRY_RUN":
            errors.append(f"content_ledger_rows[{index}].email_sent_at must be NOT_SENT_DRY_RUN")
    return errors


validate_historical_b1_previews = validate_historical_b1_previews_report


def _extract_daily_input(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    if isinstance(payload.get("daily_input"), Mapping):
        return payload["daily_input"]  # type: ignore[return-value]
    if {"run_id", "publication_id", "date", "source_item", "claims"}.issubset(payload.keys()):
        return payload
    return {}


def _source_id(daily_input: Mapping[str, Any]) -> str:
    source_item = daily_input.get("source_item")
    if isinstance(source_item, Mapping):
        return str(source_item.get("source_id") or "")
    return ""


def _future_leakage_refs(daily_input: Mapping[str, Any]) -> list[str]:
    as_of = _parse_date(str(daily_input.get("date") or ""))
    if as_of is None:
        return []
    source_item = daily_input.get("source_item")
    metadata = source_item.get("metadata") if isinstance(source_item, Mapping) else {}
    arxiv = metadata.get("arxiv") if isinstance(metadata, Mapping) else {}
    if not isinstance(arxiv, Mapping):
        return []
    refs: list[str] = []
    for field in ("published", "updated"):
        observed_date = _parse_datetime_date(str(arxiv.get(field) or ""))
        if observed_date is not None and observed_date > as_of:
            refs.append(f"{_source_id(daily_input)}:{field}:{observed_date.isoformat()}>{as_of.isoformat()}")
    return refs


def _parse_datetime_date(value: str) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        return _parse_date(value[:10])


def _historical_payload(index: int, local_date: date, *, generated_at: str) -> dict[str, Any]:
    topic = _HISTORICAL_TOPICS[index % len(_HISTORICAL_TOPICS)]
    category = str(topic["category"])
    stable_id = f"2605.{index + 1:05d}v1"
    source_id = f"arxiv:{stable_id}"
    title = f"{topic['title']} #{index + 1:02d}"
    url = f"https://arxiv.org/abs/{stable_id}"
    summary = (
        f"This offline historical preview sample studies {topic['mechanism']} for board B1 teaching. "
        f"It is synthetic arXiv metadata used to test report and email generation for {topic['theme']} "
        "without PDF download, network fetch, release upload, SMTP send, scheduler enablement, or video generation."
    )
    source_item = {
        "source_id": source_id,
        "source_type": STAGE1_HISTORICAL_PREVIEW_SOURCE_TYPE,
        "source_adapter": "offline_historical_preview_fixture",
        "stable_id": stable_id,
        "title": title,
        "retrieved_at": generated_at,
        "canonical_url": url,
        "metadata": {
            "arxiv": {
                "id": stable_id,
                "primary_category": category,
                "categories": [category],
                "summary": summary,
                "authors": [f"Historical Preview Author {index + 1}"],
                "published": f"{local_date.isoformat()}T00:00:00Z",
                "updated": f"{local_date.isoformat()}T00:00:00Z",
                "abs_url": url,
            },
            "preview_fixture_index": index + 1,
            "metadata_conflicts": [],
        },
        "content_refs": [
            {
                "ref_type": "arxiv_atom_summary",
                "stable_url": url,
                "section": "summary",
                "sha256": stable_content_hash({"summary": summary}),
            }
        ],
        "license": "arXiv metadata only; synthetic historical preview fixture",
    }
    claims = [
        {
            "claim_id": f"claim:{source_id}:abstract-summary",
            "source_id": source_id,
            "claim_type": "author_claim",
            "priority": "P0",
            "statement": f"The offline arXiv-style Atom summary states: {summary}",
            "locator": {
                "locator_type": "abstract",
                "stable_url": url,
                "section": "abstract",
                "quote": summary,
            },
            "support_status": "supported",
            "extracted_at": generated_at,
            "notes": "Generated from an offline historical preview fixture; not peer review or independent validation.",
        },
        {
            "claim_id": f"claim:{source_id}:primary-category",
            "source_id": source_id,
            "claim_type": "metadata",
            "priority": "P1",
            "statement": f"The offline arXiv-style metadata lists primary category {category}.",
            "locator": {
                "locator_type": "metadata",
                "stable_url": url,
                "section": "arxiv:primary_category",
                "quote": category,
            },
            "support_status": "supported",
            "extracted_at": generated_at,
        },
    ]
    daily_input = {
        "run_id": f"historical-b1:{local_date.isoformat()}:{stable_id}",
        "publication_id": f"pub:historical-b1:{local_date.isoformat()}:{stable_id}",
        "date": local_date.isoformat(),
        "generated_at": generated_at,
        "timezone": DEFAULT_TIMEZONE,
        "source_item": source_item,
        "claims": claims,
        "selection_audit": {
            "status": "pass",
            "selected": {"source_id": source_id, "rank": 1},
            "audits": [{"policy": "offline_historical_preview", "result": "pass"}],
        },
    }
    return {
        "daily_input": daily_input,
        "candidate_count": STAGE1_HISTORICAL_PREVIEW_REQUIRED_COUNT,
        "queue_report": {
            "total_items": STAGE1_HISTORICAL_PREVIEW_REQUIRED_COUNT,
            "active_count": STAGE1_HISTORICAL_PREVIEW_REQUIRED_COUNT - 1,
        },
    }


def _status_counts(records: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        status = str(record.get("status") or "unknown")
        counts[status] = counts.get(status, 0) + 1
    return counts


def _unique_nonempty(records: list[dict[str, Any]], key: str) -> bool:
    values = [str(record.get(key) or "") for record in records]
    return bool(values) and all(values) and len(set(values)) == len(values)


def _parse_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _write_manifest(report: dict[str, Any], artifact_dir: Path) -> dict[str, Any]:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    path = artifact_dir / "historical_b1_previews_manifest.json"
    serializable = {
        key: value for key, value in report.items() if key != "artifact_summary"
    }
    artifact_summary = dict(report.get("artifact_summary", {}))
    artifact_summary["manifest_path"] = str(path)
    serializable["artifact_summary"] = artifact_summary
    payload = json.dumps(serializable, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    path.write_text(payload, encoding="utf-8")
    return {
        "path": str(path),
        "sha256": stable_content_hash({"content": payload}),
        "size_bytes": len(path.read_bytes()),
    }


def _blocked_report(*, generated_at: str, reasons: list[str]) -> dict[str, Any]:
    return {
        "model_id": STAGE1_HISTORICAL_PREVIEW_MODEL_ID,
        "schema_version": STAGE1_HISTORICAL_PREVIEW_SCHEMA_VERSION,
        "project_id": "arxiv-daily-push",
        "board_id": STAGE1_B1_BOARD_ID,
        "acceptance_id": STAGE1_HISTORICAL_PREVIEW_ACCEPTANCE_ID,
        "status": "blocked",
        "generated_at": generated_at,
        "preview_count": 0,
        "required_preview_count": STAGE1_HISTORICAL_PREVIEW_REQUIRED_COUNT,
        "previews": [],
        "preview_records": [],
        "content_ledger_updates": [],
        "content_ledger_rows": [],
        "future_leakage_count": 0,
        "quality_gates": {
            "preview_count_equals_required": False,
            "unique_dates_at_least_required": False,
            "unique_source_ids_at_least_required": False,
            "all_packages_passed": False,
            "all_content_hashes_unique": False,
            "all_email_ids_unique": False,
            "all_critical_claims_covered": False,
            "content_ledger_rows_match_preview_count": False,
            "future_leakage_zero": True,
            "artifact_files_written_match_expected": False,
            "no_real_smtp_send": True,
            "no_release_upload": True,
            "no_video_generation": True,
            "no_network_fetch": True,
        },
        "side_effect_policy": {
            "real_smtp_sent": False,
            "release_uploaded": False,
            "video_generated": False,
            "network_fetch_performed": False,
            "scheduler_enabled": False,
            "secret_values_logged": False,
        },
        "source_policy": {
            "source_type": STAGE1_HISTORICAL_PREVIEW_SOURCE_TYPE,
            "supported_input_formats": list(STAGE1_HISTORICAL_PREVIEW_SUPPORTED_INPUT_FORMATS),
            "offline_historical_fixture_only": True,
            "pdf_download_enabled": False,
            "bulk_harvest_enabled": False,
            "peer_review_claim_enabled": False,
            "video_required": False,
        },
        "artifact_manifest": {},
        "blocking_reasons": reasons,
    }
