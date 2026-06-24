"""Phase 6 evidence-linked text lesson generation."""

from __future__ import annotations

import re
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
        "frontstage": _build_frontstage(source_item),
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


def _build_frontstage(source_item: Mapping[str, Any]) -> dict[str, Any]:
    arxiv = (source_item.get("metadata") or {}).get("arxiv", {})
    if not isinstance(arxiv, Mapping):
        arxiv = {}
    title = _clean_text(str(source_item.get("title") or ""))
    summary = _clean_text(str(arxiv.get("summary") or ""))
    category = str(arxiv.get("primary_category") or "")
    combined = f"{title} {summary} {category}".lower()
    score = _attention_score(category, combined)
    decision = "读" if score >= 4.2 else "扫读" if score >= 3.2 else "跳过"
    return {
        "decision": decision,
        "attention_score": score,
        "evidence_level": "摘要级预印本",
        "estimated_reading_time": "8-15分钟" if decision != "跳过" else "2-3分钟",
        "one_line_takeaway": _one_line_takeaway(title, combined),
        "first_principles_chain": _first_principles_chain(combined),
        "domain_mappings": _domain_mappings(category, combined),
        "key_questions": _key_questions(category, combined),
        "evidence_gaps": [
            "当前只基于 arXiv 摘要和分类元数据，不能当作同行评审或真实市场验证。",
            "需要确认论文正文中的数学定义、实验设定和失败条件是否支持摘要主张。",
            "若没有数据、回测、仿真或可复现实验，应只进入观察队列，不进入结论库。",
        ],
        "default_action": _default_action(category, combined),
        "video_card": {
            "duration": "45-60秒",
            "content": "用变量、反馈回路和失败条件解释今天是否值得继续读。",
            "learning_goal": "看完能回答：这篇论文的增量在哪里，什么条件下不成立。",
        },
    }


def _attention_score(category: str, text: str) -> float:
    score = 3.0
    if category.startswith("q-fin"):
        score += 0.45
    elif category.startswith(("cs.", "stat.", "econ.", "eess.", "math.")):
        score += 0.25
    finance_hits = ("finance", "market", "portfolio", "risk", "trading", "liquidity", "volatility", "order")
    method_hits = ("agent", "model", "benchmark", "optimization", "simulation", "control", "learning", "robustness")
    score += min(0.7, 0.12 * sum(1 for keyword in finance_hits if keyword in text))
    score += min(0.45, 0.08 * sum(1 for keyword in method_hits if keyword in text))
    return round(min(4.6, max(2.0, score)), 1)


def _one_line_takeaway(title: str, text: str) -> str:
    if "agent" in text and any(keyword in text for keyword in ("order", "synchron", "fragility", "response function", "power")):
        return "最值得看的不是模型名字，而是多智能体同步如何同时提高产出并放大系统脆弱性。"
    if any(keyword in text for keyword in ("portfolio", "risk", "trading", "market", "liquidity", "volatility")):
        return "这篇论文的价值在于把方法变量映射到市场风险、策略拥挤或组合决策的可验证问题。"
    if any(keyword in text for keyword in ("benchmark", "dataset", "evaluation")):
        return "核心价值是提供可复用评估框架；先看它能否降低你的研究验证成本。"
    if any(keyword in text for keyword in ("optimization", "control", "simulation")):
        return "核心价值是把复杂系统问题转成可实验的输入、输出和约束条件。"
    return f"先判断《{_truncate_text(title, max_chars=42)}》是否提供新变量、新机制或新实验，而不只停留在摘要主张。"


def _first_principles_chain(text: str) -> list[str]:
    if "agent" in text and any(keyword in text for keyword in ("order", "synchron", "fragility", "response function", "power")):
        return ["代理权力与响应函数", "行为相关性上升", "集体产出改善", "多样性下降", "脆弱性与切换成本上升"]
    if any(keyword in text for keyword in ("portfolio", "risk", "trading", "market")):
        return ["市场状态与约束", "策略或模型响应", "收益与风险分布改变", "拥挤、冲击或回撤暴露", "是否可复现实证验证"]
    return ["问题定义", "关键变量", "方法机制", "可观察输出", "失败条件"]


def _domain_mappings(category: str, text: str) -> list[dict[str, str]]:
    if category.startswith("q-fin") or any(keyword in text for keyword in ("portfolio", "risk", "trading", "market")):
        return [
            {"paper_variable": "Agent / model", "decision_mapping": "策略主体、资金规模、信息优势或执行约束"},
            {"paper_variable": "Response function", "decision_mapping": "策略对价格、波动率、订单流和群体信号的反应"},
            {"paper_variable": "Order / synchronization", "decision_mapping": "拥挤交易、共同去杠杆、同向反馈和流动性冲击"},
            {"paper_variable": "Fragility / mobility", "decision_mapping": "最大回撤、级联清算风险和市场切换到新均衡的能力"},
        ]
    if category.startswith("cs") or any(keyword in text for keyword in ("model", "agent", "benchmark", "learning")):
        return [
            {"paper_variable": "Model capability", "decision_mapping": "能否减少人工研究、筛选或验证成本"},
            {"paper_variable": "Benchmark / dataset", "decision_mapping": "能否成为后续自动化评估基准"},
            {"paper_variable": "Failure mode", "decision_mapping": "能否提前暴露部署、鲁棒性或安全风险"},
        ]
    return [
        {"paper_variable": "Core variable", "decision_mapping": "是否能转成你可观测、可记录、可复验的指标"},
        {"paper_variable": "Mechanism", "decision_mapping": "是否能解释一个真实决策中的因果链或约束"},
        {"paper_variable": "Evidence gap", "decision_mapping": "是否值得投入下一步阅读或实验时间"},
    ]


def _key_questions(category: str, text: str) -> list[str]:
    if category.startswith("q-fin") or any(keyword in text for keyword in ("portfolio", "risk", "trading", "market")):
        return [
            "论文变量能否从真实市场数据中稳定估计？",
            "它提供的是可交易/可风控增量，还是只是一种理论类比？",
            "在流动性枯竭、策略拥挤或 regime shift 下结论是否会反转？",
        ]
    return [
        "这篇论文解决的问题是否真实降低你的学习、研究或产品验证成本？",
        "摘要主张是否有正文实验、数据或数学定义支撑？",
        "如果结论不成立，最可能失败在哪个输入假设或评估指标上？",
    ]


def _default_action(category: str, text: str) -> str:
    if category.startswith("q-fin") or any(keyword in text for keyword in ("portfolio", "risk", "trading", "market")):
        return "只做一个最小实验：把论文核心变量映射到收益、波动、回撤和恢复时间，验证是否存在可复现的内点最优或风险改善。"
    return "只做一个最小验证：列出输入、输出、失败条件和复现实验，再决定是否深读全文。"


def _claim_sentence(claim: Mapping[str, Any], label: str) -> str:
    claim_id = str(claim["claim_id"])
    statement = str(claim["statement"]).strip().rstrip("。.")
    return f"{label}来自 Claim Ledger [{claim_id}]：{statement}"


def _takeaway_sentence(claims: Sequence[Mapping[str, Any]]) -> str:
    markers = "、".join(f"[{claim['claim_id']}]" for claim in claims)
    return f"本课只基于以上已支持证据组织讲解，不加入 Claim Ledger 之外的事实；复盘时优先核对 {markers}。"


def _truncate_text(value: str, *, max_chars: int) -> str:
    cleaned = _clean_text(value)
    if len(cleaned) <= max_chars:
        return cleaned
    return cleaned[: max(0, max_chars - 3)].rstrip(" ,.;:") + "..."


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()
