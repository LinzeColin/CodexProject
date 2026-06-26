"""Generic Phase 2 data contracts.

These validators are intentionally deterministic and dependency-free. JSON
Schema files remain the external contract surface; this module provides the
runtime checks used by local tests and CLI tooling.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any


SOURCE_TYPES = {
    "arxiv",
    "preprint",
    "rss",
    "github",
    "standard",
    "industry_report",
    "web",
    "book",
    "course",
    "podcast",
    "user_document",
}
CLAIM_TYPES = {"reported_result", "author_claim", "system_inference", "analogy", "uncertainty", "metadata"}
CLAIM_PRIORITIES = {"P0", "P1", "P2"}
SUPPORT_STATUSES = {"supported", "unsupported", "conflict", "unverified"}
PUBLICATION_TYPES = {"daily", "weekly", "monthly", "manual_replay"}
PUBLICATION_STATUSES = {"draft", "blocked", "ready", "published", "degraded", "failed"}


def stable_content_hash(data: Mapping[str, Any]) -> str:
    payload = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _require_mapping(data: Any, label: str) -> list[str]:
    return [] if isinstance(data, Mapping) else [f"{label} must be an object"]


def _missing(data: Mapping[str, Any], fields: tuple[str, ...], label: str) -> list[str]:
    return [f"{label}.{field} is required" for field in fields if data.get(field) in (None, "", [])]


def _enum(value: Any, allowed: set[str], path: str) -> list[str]:
    return [] if value in allowed else [f"{path} must be one of {sorted(allowed)}"]


def validate_source_item(data: Mapping[str, Any]) -> list[str]:
    errors = _require_mapping(data, "SourceItem")
    if errors:
        return errors
    errors.extend(
        _missing(
            data,
            (
                "source_id",
                "source_type",
                "source_adapter",
                "stable_id",
                "title",
                "retrieved_at",
                "canonical_url",
                "metadata",
                "content_refs",
                "license",
            ),
            "SourceItem",
        )
    )
    errors.extend(_enum(data.get("source_type"), SOURCE_TYPES, "SourceItem.source_type"))
    if not isinstance(data.get("metadata"), Mapping):
        errors.append("SourceItem.metadata must be an object")
    content_refs = data.get("content_refs")
    if not isinstance(content_refs, list) or not content_refs:
        errors.append("SourceItem.content_refs must be a non-empty array")
    return errors


def validate_evidence_claim(data: Mapping[str, Any]) -> list[str]:
    errors = _require_mapping(data, "EvidenceClaim")
    if errors:
        return errors
    errors.extend(
        _missing(
            data,
            ("claim_id", "source_id", "claim_type", "priority", "statement", "locator", "support_status", "extracted_at"),
            "EvidenceClaim",
        )
    )
    errors.extend(_enum(data.get("claim_type"), CLAIM_TYPES, "EvidenceClaim.claim_type"))
    errors.extend(_enum(data.get("priority"), CLAIM_PRIORITIES, "EvidenceClaim.priority"))
    errors.extend(_enum(data.get("support_status"), SUPPORT_STATUSES, "EvidenceClaim.support_status"))
    locator = data.get("locator")
    if not isinstance(locator, Mapping):
        errors.append("EvidenceClaim.locator must be an object")
    elif data.get("priority") == "P0" and not any(locator.get(key) for key in ("stable_url", "page", "section", "table", "figure", "quote")):
        errors.append("EvidenceClaim P0 locator must include stable_url, page, section, table, figure, or quote")
    return errors


def validate_lesson(data: Mapping[str, Any]) -> list[str]:
    errors = _require_mapping(data, "Lesson")
    if errors:
        return errors
    errors.extend(
        _missing(
            data,
            (
                "lesson_id",
                "lesson_key",
                "lesson_revision_id",
                "source_item_id",
                "language",
                "title",
                "sections",
                "claim_ids",
                "generated_at",
            ),
            "Lesson",
        )
    )
    if data.get("lesson_id") != data.get("lesson_revision_id"):
        errors.append("Lesson.lesson_id must equal Lesson.lesson_revision_id")
    if data.get("language") not in {"zh-CN", "zh-Hans", "en"}:
        errors.append("Lesson.language must be zh-CN, zh-Hans, or en")
    if not isinstance(data.get("sections"), list) or not data.get("sections"):
        errors.append("Lesson.sections must be a non-empty array")
    if not isinstance(data.get("claim_ids"), list):
        errors.append("Lesson.claim_ids must be an array")
    return errors


def validate_storyboard(data: Mapping[str, Any]) -> list[str]:
    errors = _require_mapping(data, "Storyboard")
    if errors:
        return errors
    errors.extend(_missing(data, ("storyboard_id", "lesson_id", "scenes", "constraints", "generated_at"), "Storyboard"))
    scenes = data.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        errors.append("Storyboard.scenes must be a non-empty array")
    return errors


def validate_publication(data: Mapping[str, Any]) -> list[str]:
    errors = _require_mapping(data, "Publication")
    if errors:
        return errors
    errors.extend(_missing(data, ("publication_id", "run_id", "publication_type", "status", "artifacts", "created_at"), "Publication"))
    errors.extend(_enum(data.get("publication_type"), PUBLICATION_TYPES, "Publication.publication_type"))
    errors.extend(_enum(data.get("status"), PUBLICATION_STATUSES, "Publication.status"))
    if not isinstance(data.get("artifacts"), list):
        errors.append("Publication.artifacts must be an array")
    return errors


CONTRACT_VALIDATORS = {
    "source_item": validate_source_item,
    "evidence_claim": validate_evidence_claim,
    "lesson": validate_lesson,
    "storyboard": validate_storyboard,
    "publication": validate_publication,
}


def validate_contract(kind: str, data: Mapping[str, Any]) -> list[str]:
    validator = CONTRACT_VALIDATORS.get(kind)
    if validator is None:
        return [f"Unknown contract kind: {kind}"]
    return validator(data)
