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
    profile = _source_profile(source_item)
    title = _clean_text(str(source_item.get("title") or ""))
    summary = str(profile["summary"])
    category = str(profile["primary_category"])
    evidence_label = str(profile["evidence_label"])
    combined = f"{title} {summary} {category}".lower()
    topic = _topic_label(category, combined)
    score = _attention_score(category, combined)
    decision = "读" if score >= 4.2 else "扫读" if score >= 3.2 else "跳过"
    return {
        "decision": decision,
        "attention_score": score,
        "evidence_level": evidence_label,
        "estimated_reading_time": "8-15分钟" if decision != "跳过" else "2-3分钟",
        "one_line_takeaway": _one_line_takeaway(title, combined),
        "first_principles_chain": _first_principles_chain(combined),
        "domain_mappings": _domain_mappings(category, combined),
        "key_questions": _key_questions(category, combined),
        "plain_language_explanation": _plain_language_explanation(title, summary, category, topic),
        "learning_outcomes": _learning_outcomes(topic, combined),
        "method_flow": _method_flow(topic, combined),
        "knowledge_units": _knowledge_units(topic, title, summary, category, combined),
        "reusable_methods": _reusable_methods(topic, combined),
        "transfer_scenarios": _transfer_scenarios(topic, combined),
        "learning_boundary": _learning_boundary(evidence_label),
        "evidence_gaps": [
            f"当前只基于{evidence_label}，不能当作同行评审结论或真实市场验证。",
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


def _topic_label(category: str, text: str) -> str:
    if category.startswith("q-fin") or any(keyword in text for keyword in ("portfolio", "risk", "trading", "market")):
        return "市场风险和策略验证"
    if any(keyword in text for keyword in ("agent", "artificial intelligence", "language model", "model")):
        return "AI 系统和证据验证"
    if any(keyword in text for keyword in ("benchmark", "dataset", "evaluation")):
        return "评估基准和可复现实验"
    if any(keyword in text for keyword in ("optimization", "control", "simulation")):
        return "复杂系统优化和仿真"
    if any(keyword in text for keyword in ("health", "clinical", "medical")):
        return "医学决策和风险控制"
    return "研究问题拆解和证据判断"


def _plain_language_explanation(title: str, summary: str, category: str, topic: str) -> str:
    title_text = _truncate_text(title or "这篇论文", max_chars=64)
    summary_text = _truncate_text(summary or "摘要没有给出足够细节", max_chars=150)
    category_text = category or "未标明分类"
    return (
        f"这篇论文可以先理解为：作者围绕“{topic}”提出一个需要被验证的研究线索。"
        f"现实难点是，标题《{title_text}》背后的主张不能只靠关键词判断；"
        f"需要看它把什么问题、方法、证据和失败条件连在一起。"
        f"从当前摘要级信息看，论文给出的核心上下文是：{summary_text}。"
        f"因此这封邮件只把它当作 {category_text} 下的学习材料和验证入口，"
        "不把摘要主张升级成已经证实的事实。"
    )


def _learning_outcomes(topic: str, text: str) -> list[str]:
    outcomes = [
        f"把“{topic}”拆成问题、方法、证据和失败条件。",
        "区分论文事实、邮件解释和迁移建议，避免把摘要当结论。",
        "学会从一个研究标题里找出可验证变量，而不是只记住术语。",
        "把论文方法改写成学习、研究或产品中的最小验证动作。",
    ]
    if any(keyword in text for keyword in ("benchmark", "dataset", "evaluation")):
        outcomes.append("判断一个评估基准能否减少后续研究和产品验证成本。")
    elif any(keyword in text for keyword in ("agent", "model", "learning")):
        outcomes.append("判断一个模型系统主张是否有足够证据支持真实使用。")
    else:
        outcomes.append("判断这篇论文最值得继续追问的证据缺口。")
    return outcomes[:5]


def _method_flow(topic: str, text: str) -> list[str]:
    if any(keyword in text for keyword in ("benchmark", "dataset", "evaluation")):
        return ["定义要比较的能力", "建立数据或任务", "运行可复现实验", "比较结果差异", "检查失败样例", "决定是否复用"]
    if any(keyword in text for keyword in ("portfolio", "risk", "trading", "market")):
        return ["确定市场状态", "定义策略或模型反应", "观察收益与风险变化", "检查拥挤和冲击", "用回撤或恢复时间验证"]
    if any(keyword in text for keyword in ("agent", "model", "learning")):
        return ["说明系统要解决的问题", "拆出输入和输出", "绑定证据来源", "检查模型能力边界", "用失败条件决定下一步"]
    return [f"锁定{topic}", "找出关键变量", "看作者怎样处理", "检查证据支持", "迁移为一个可执行动作"]


def _knowledge_units(topic: str, title: str, summary: str, category: str, text: str) -> list[dict[str, str]]:
    title_hint = _truncate_text(title or "本篇论文", max_chars=48)
    summary_hint = _truncate_text(summary or "当前摘要级证据", max_chars=90)
    units = [
        {
            "title": "论文不是结论库，而是证据入口",
            "what": f"《{title_hint}》现在只能证明作者报告了一个 {topic} 相关主张。",
            "why": "摘要和元数据能定位问题，但不能替代正文、图表和实验。",
            "paper_link": f"当前材料来自 {category or '未知分类'} 摘要级信息：{summary_hint}",
            "transfer": "读任何论文前，先标记事实层级，再决定是否深挖正文。",
            "mistake": "把摘要里的可能性直接写成确定结论。",
        },
        {
            "title": "先找变量，再谈方法",
            "what": f"这篇论文的学习价值取决于它是否把 {topic} 拆成可观察变量。",
            "why": "变量清楚，方法才可能复现；变量含糊，术语再多也无法迁移。",
            "paper_link": "邮件把标题、分类、摘要和证据边界放在同一条链上检查。",
            "transfer": "做研究、产品或自动化评估时，先列输入、输出和评价指标。",
            "mistake": "只记方法名，不知道它改变了哪个变量。",
        },
        {
            "title": "失败条件和方法本身一样重要",
            "what": "论文值得学的部分不只是它声称有效，还包括什么情况下可能失效。",
            "why": "失败条件能防止把局部实验或理论假设误用到真实系统。",
            "paper_link": "当前邮件保留证据缺口，提醒继续检查正文设定和限制。",
            "transfer": "为学习计划、交易研究或产品实验预先写下停止条件。",
            "mistake": "只保存看起来有用的结论，忽略不适用条件。",
        },
        {
            "title": "迁移要看共同结构，不看表面领域",
            "what": f"{topic} 可以迁移的不是原领域标签，而是问题结构和验证路径。",
            "why": "不同领域可能共享“输入-机制-输出-反馈”的同一结构。",
            "paper_link": "邮件把论文变量映射为学习、研究和产品中的可执行判断。",
            "transfer": "把新论文转成一个小实验、一条检查清单或一个产品假设。",
            "mistake": "用“这个领域也重要”代替真正的迁移解释。",
        },
    ]
    if any(keyword in text for keyword in ("benchmark", "dataset", "evaluation")):
        units.append(
            {
                "title": "评估基准的价值在于降低验证成本",
                "what": "一个好基准能让不同方法在同一任务上比较。",
                "why": "比较条件一致，后续选择才不是凭感觉。",
                "paper_link": "当前摘要出现 benchmark / evaluation 信号，应继续检查任务定义和样本来源。",
                "transfer": "为自己的项目设计小型验收集，而不是只看单次演示。",
                "mistake": "把基准分数当作真实世界效果。",
            }
        )
    return units[:5]


def _reusable_methods(topic: str, text: str) -> list[dict[str, str]]:
    methods = [
        {
            "name": "摘要级证据分层",
            "when": "刚看到论文、还没读正文时使用。",
            "how": "把已知事实、作者解释、你的迁移想法分开放。",
            "not_for": "不能用来替代全文事实核查。",
        },
        {
            "name": "变量-机制-输出拆解",
            "when": f"遇到 {topic} 这种跨学科主张时使用。",
            "how": "先写变量，再写变量如何互动，最后写能观察到的输出。",
            "not_for": "变量无法观察或测量时不要强行建模。",
        },
        {
            "name": "最小验证动作",
            "when": "论文看起来有价值，但还不值得投入长时间阅读时使用。",
            "how": "设计一个 15-30 分钟能完成的小检查，确认是否继续。",
            "not_for": "不能把小检查的结果包装成论文最终结论。",
        },
    ]
    if any(keyword in text for keyword in ("risk", "failure", "robustness", "security")):
        methods.append(
            {
                "name": "失败条件前置",
                "when": "论文涉及风险、鲁棒性、部署或决策系统时使用。",
                "how": "先写出什么证据会推翻当前判断，再看正文是否覆盖。",
                "not_for": "不要只寻找支持自己观点的证据。",
            }
        )
    return methods[:4]


def _transfer_scenarios(topic: str, text: str) -> list[dict[str, str]]:
    scenarios = [
        {
            "scenario": "学习",
            "connection": f"把 {topic} 拆成 4-6 个知识单元，每个单元都写清事实、解释和迁移。",
        },
        {
            "scenario": "研究工作流",
            "connection": "把论文先放入证据队列，只在关键事实可追踪时进入结论库。",
        },
        {
            "scenario": "产品或自动化系统",
            "connection": "把论文主张改成一个可验收的小功能假设，而不是直接写进产品宣传。",
        },
    ]
    if any(keyword in text for keyword in ("portfolio", "risk", "market", "trading")):
        scenarios.append(
            {
                "scenario": "量化研究",
                "connection": "把论文变量映射到收益、波动、回撤、流动性和恢复时间，再决定是否回测。",
            }
        )
    return scenarios[:4]


def _learning_boundary(evidence_label: str) -> dict[str, list[str]]:
    return {
        "can_determine": [
            f"当前来源层级是{evidence_label}。",
            "可以确定邮件中的事实入口来自当前论文对象和受支持 claim。",
        ],
        "cannot_determine": [
            "不能确定正文图表、实验细节和限制是否完全支持摘要主张。",
            "不能确定同行评审、真实部署、商业价值或长期效果已经成立。",
        ],
    }


def _source_profile(source_item: Mapping[str, Any]) -> dict[str, str]:
    metadata = source_item.get("metadata") if isinstance(source_item.get("metadata"), Mapping) else {}
    arxiv = metadata.get("arxiv") if isinstance(metadata.get("arxiv"), Mapping) else {}
    if isinstance(arxiv, Mapping) and arxiv:
        return {
            "summary": _clean_text(str(arxiv.get("summary") or "")),
            "primary_category": str(arxiv.get("primary_category") or ""),
            "evidence_label": "摘要级 arXiv 分类元数据",
        }
    preprint = metadata.get("preprint") if isinstance(metadata.get("preprint"), Mapping) else {}
    if isinstance(preprint, Mapping) and preprint:
        server = str(preprint.get("server") or "预印本").strip()
        return {
            "summary": _clean_text(str(preprint.get("abstract") or "")),
            "primary_category": _clean_text(str(preprint.get("category") or server)),
            "evidence_label": f"摘要级 {server} 来源元数据",
        }
    top_journal = metadata.get("top_journal") if isinstance(metadata.get("top_journal"), Mapping) else {}
    if isinstance(top_journal, Mapping) and top_journal:
        journal = str(top_journal.get("journal") or "顶级期刊").strip()
        article_type = _clean_text(str(top_journal.get("article_type") or "research article"))
        return {
            "summary": _clean_text(str(top_journal.get("summary") or "")),
            "primary_category": _clean_text(f"{journal} {article_type}"),
            "evidence_label": f"摘要级 {journal} RSS/Research Articles 元数据",
        }
    return {"summary": "", "primary_category": "", "evidence_label": "摘要级来源元数据"}


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
