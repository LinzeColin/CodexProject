"""Phase 6 evidence-linked text lesson generation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .contracts import stable_content_hash, validate_lesson, validate_source_item
from .evidence_gate import build_claim_ledger


DEFAULT_LANGUAGE = "zh-CN"
MIN_SUPPORTED_CLAIMS = 1


class LessonGenerationError(ValueError):
    """Raised when a lesson would introduce unsupported or unlinked claims."""


def generate_lesson(
    source_item: Mapping[str, Any],
    claims: Sequence[Mapping[str, Any]],
    *,
    generated_at: str,
    language: str = DEFAULT_LANGUAGE,
) -> dict[str, Any]:
    """Generate a deterministic text-only lesson linked to supported claims."""

    source_errors = validate_source_item(source_item)
    if source_errors:
        raise LessonGenerationError("; ".join(source_errors))
    ledger = build_claim_ledger(source_item, claims, extracted_at=generated_at)
    if ledger["blocking_reasons"]:
        raise LessonGenerationError("; ".join(ledger["blocking_reasons"]))
    supported_claims = [claim for claim in ledger["claims"] if claim.get("support_status") == "supported"]
    if len(supported_claims) < MIN_SUPPORTED_CLAIMS:
        raise LessonGenerationError("Lesson requires at least one supported claim")
    source_id = str(source_item["source_id"])
    lesson_claim_ids = [str(claim["claim_id"]) for claim in supported_claims]
    lesson = {
        "lesson_id": f"lesson:{source_id}:{stable_content_hash({'claim_ids': lesson_claim_ids, 'language': language})[:12]}",
        "source_item_id": source_id,
        "language": language,
        "title": f"今日论文学习：{source_item['title']}",
        "sections": _build_sections(supported_claims),
        "claim_ids": lesson_claim_ids,
        "generated_at": generated_at,
    }
    errors = validate_lesson_against_ledger(lesson, ledger)
    if errors:
        raise LessonGenerationError("; ".join(errors))
    return lesson


def validate_lesson_against_ledger(lesson: Mapping[str, Any], ledger: Mapping[str, Any]) -> list[str]:
    """Validate lesson contract plus Claim Ledger coverage."""

    errors = validate_lesson(lesson)
    supported_claim_ids = {
        str(claim.get("claim_id"))
        for claim in ledger.get("claims", [])
        if isinstance(claim, Mapping) and claim.get("support_status") == "supported" and claim.get("claim_id")
    }
    if ledger.get("status") != "pass":
        errors.append("Lesson Claim Ledger status must be pass")
    if lesson.get("source_item_id") != ledger.get("source_id"):
        errors.append("Lesson.source_item_id must match Claim Ledger source_id")
    lesson_claim_ids = [str(claim_id) for claim_id in lesson.get("claim_ids", []) if claim_id]
    if not lesson_claim_ids:
        errors.append("Lesson.claim_ids must include at least one supported claim")
    unknown_lesson_claims = sorted(set(lesson_claim_ids) - supported_claim_ids)
    if unknown_lesson_claims:
        errors.append(f"Lesson.claim_ids include unsupported or unknown claims: {', '.join(unknown_lesson_claims)}")
    sections = lesson.get("sections")
    if isinstance(sections, list):
        for index, section in enumerate(sections):
            if not isinstance(section, Mapping):
                errors.append(f"Lesson.sections[{index}] must be an object")
                continue
            section_claim_ids = [str(claim_id) for claim_id in section.get("claim_ids", []) if claim_id]
            if not section_claim_ids:
                errors.append(f"Lesson.sections[{index}].claim_ids must include at least one claim")
            unknown_section_claims = sorted(set(section_claim_ids) - set(lesson_claim_ids))
            if unknown_section_claims:
                errors.append(
                    f"Lesson.sections[{index}].claim_ids include claims absent from Lesson.claim_ids: "
                    + ", ".join(unknown_section_claims)
                )
            body = str(section.get("body") or "")
            missing_markers = [claim_id for claim_id in section_claim_ids if f"[{claim_id}]" not in body]
            if missing_markers:
                errors.append(
                    f"Lesson.sections[{index}].body must include visible claim markers: " + ", ".join(missing_markers)
                )
    return errors


def _build_sections(supported_claims: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    p0_claims = [claim for claim in supported_claims if claim.get("priority") == "P0"]
    first_key_claim = p0_claims[0] if p0_claims else supported_claims[0]
    evidence_claims = supported_claims[:3]
    return [
        {
            "section_id": "overview",
            "title": "研究问题",
            "body": _claim_sentence(first_key_claim, "这篇内容的学习入口"),
            "claim_ids": [str(first_key_claim["claim_id"])],
        },
        {
            "section_id": "evidence",
            "title": "关键证据",
            "body": "；".join(_claim_sentence(claim, "证据") for claim in evidence_claims) + "。",
            "claim_ids": [str(claim["claim_id"]) for claim in evidence_claims],
        },
        {
            "section_id": "learning_takeaway",
            "title": "学习要点",
            "body": _takeaway_sentence(evidence_claims),
            "claim_ids": [str(claim["claim_id"]) for claim in evidence_claims],
        },
    ]


def _claim_sentence(claim: Mapping[str, Any], label: str) -> str:
    claim_id = str(claim["claim_id"])
    statement = str(claim["statement"]).strip().rstrip("。.")
    return f"{label}来自 Claim Ledger [{claim_id}]：{statement}"


def _takeaway_sentence(claims: Sequence[Mapping[str, Any]]) -> str:
    markers = "、".join(f"[{claim['claim_id']}]" for claim in claims)
    return f"本课只基于以上已支持证据组织讲解，不加入 Claim Ledger 之外的事实；复盘时优先核对 {markers}。"
