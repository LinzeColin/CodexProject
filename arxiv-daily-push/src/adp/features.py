"""8 特征打分（R1-2）—— 全部 0..1 纯函数 + 人话理由；权重只来自阈值注册表.

score = Σ weight_i × value_i − attention_cost_penalty × attention_cost
最高分 = Σ weights（v0.3 = 104）。每次打分保存特征贡献与抽取器版本，可整体重放（不变量 10）。

特征内部的塑形常数（如相关度 0.55/0.45 配比、兴趣词表）属于「排序策略」版本域，
由 FEATURE_EXTRACTOR_VER 单指针标识；任何修改必须换版本号并在 CHANGELOG 落行。
治理参数（8 权重/弃权线/扣分系数/多样性上限）仍只读 config/thresholds_v0_3.yaml。
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Mapping

from .config import FEATURE_EXTRACTOR_VER, FEATURE_KEYS  # noqa: F401 (版本指针再导出)

# Owner 兴趣画像（owner_controls.yaml interest_profile）到 arXiv 类目/词面的映射。
INTEREST_CATEGORIES = {
    "cs.AI", "cs.LG", "cs.CL", "cs.CV", "cs.NE", "stat.ML",          # AI
    "cs.AR", "cs.ET", "physics.app-ph", "cond-mat.mes-hall",          # 半导体/硬件
    "q-bio.BM", "q-bio.GN", "q-bio.QM",                               # 生物科技
    "q-fin.CP", "q-fin.GN", "q-fin.PM", "econ.GN",                    # 金融资本/数字经济
    "eess.SY", "cs.RO", "cs.SE", "cs.DC",                             # 先进制造/系统
    "physics.soc-ph", "cs.CY",
}
INTEREST_TERMS = (
    "artificial intelligence", "machine learning", "large language model", "llm",
    "semiconductor", "chip", "transistor", "lithography",
    "biotech", "protein", "genom", "drug", "clinical", "medical", "health",
    "finance", "financial", "market", "capital", "investment", "trading",
    "manufacturing", "robot", "energy", "battery", "solar", "grid",
    "digital economy", "blockchain", "privacy", "agent",
)
TRANSFER_TERMS = (
    "application", "deploy", "real-world", "production", "clinical", "industrial",
    "benchmark", "open-source", "dataset", "system", "hardware", "practical",
    "cost", "efficient", "scalable", "product",
)


def _tokens(text: str) -> set[str]:
    return {tok for tok in re.findall(r"[a-z][a-z0-9\-]{2,}", text.lower())}


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def score_features(candidate: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    """返回 {feature: {value, reason}}；context 见各特征函数注释."""
    meta = (candidate.get("metadata") or {}).get("arxiv") or {}
    title = candidate.get("title") or ""
    summary = meta.get("summary") or ""
    text = f"{title} {summary}".lower()
    tokens = _tokens(text)
    categories = set(meta.get("categories") or [])
    primary = meta.get("primary_category") or ""

    out: dict[str, dict[str, Any]] = {}

    # 1. user_relevance —— 类目命中 + 兴趣词面命中
    cat_hits = categories & INTEREST_CATEGORIES
    term_hits = [term for term in INTEREST_TERMS if term in text]
    value = _clamp(0.55 * min(1.0, len(cat_hits) / 2) + 0.45 * min(1.0, len(term_hits) / 3))
    out["user_relevance"] = {
        "value": value,
        "reason": f"命中兴趣类目 {sorted(cat_hits) or '无'}；兴趣词 {term_hits[:3] or '无'}",
    }

    # 2. knowledge_gap —— 与已学讲义词面的差集比例（无历史 → 0.8 默认高差距）
    learned_tokens: set[str] = set(context.get("learned_tokens") or set())
    if not learned_tokens:
        gap, gap_reason = 0.8, "尚无已学历史，默认高知识差距"
    else:
        overlap = len(tokens & learned_tokens) / max(1, len(tokens))
        gap = _clamp(1.0 - overlap)
        gap_reason = f"与已学内容词面重叠 {overlap:.0%}，差距 {gap:.0%}"
    out["knowledge_gap"] = {"value": gap, "reason": gap_reason}

    # 3. novelty_to_user —— 与近期已见候选的最大 Jaccard 相似度取反
    #    复审修复：排除候选自身（自匹配会把新颖度恒压为 0，14 分权重失效）
    own_doc_id = str(candidate.get("doc_id") or "")
    seen_docs: list[tuple[str, set[str]]] = list(context.get("seen_docs") or [])
    other_sets = [s for doc_id, s in seen_docs if doc_id != own_doc_id]
    if not other_sets:
        novelty, novelty_reason = 0.7, "近期未见类似内容（无对照池）"
    else:
        best = max((len(tokens & s) / max(1, len(tokens | s))) for s in other_sets)
        novelty = _clamp(1.0 - best)
        novelty_reason = f"与近期最相似候选的相似度 {best:.0%}"
    out["novelty_to_user"] = {"value": novelty, "reason": novelty_reason}

    # 4. transfer_potential —— 应用/落地信号词 + 跨域类目数
    transfer_hits = [term for term in TRANSFER_TERMS if term in text]
    cross_domains = len({cat.split(".")[0] for cat in categories})
    value = _clamp(0.7 * min(1.0, len(transfer_hits) / 3) + 0.3 * min(1.0, (cross_domains - 1) / 2))
    out["transfer_potential"] = {
        "value": value,
        "reason": f"落地信号 {transfer_hits[:3] or '无'}；跨 {cross_domains} 个学科域",
    }

    # 5. forgetting_pressure —— 到期复习项与本文的主题重叠（新学习巩固旧记忆）
    due_topic_tokens: set[str] = set(context.get("due_topic_tokens") or set())
    if not due_topic_tokens:
        value, reason = 0.0, "当前无到期复习项"
    else:
        overlap = len(tokens & due_topic_tokens) / max(1, len(due_topic_tokens))
        value = _clamp(overlap * 2)
        reason = f"与 {len(due_topic_tokens)} 个到期复习主题词重叠 {overlap:.0%}"
    out["forgetting_pressure"] = {"value": value, "reason": reason}

    # 6. urgency —— 发表新鲜度（24h 内 1.0，7 天线性衰减）+ 版本更新加成
    published = meta.get("published") or ""
    as_of: datetime = context.get("as_of") or datetime.now(timezone.utc)
    age_hours = _age_hours(published, as_of)
    fresh = _clamp(1.0 - max(0.0, age_hours - 24) / (7 * 24)) if age_hours is not None else 0.3
    version_bump = 0.2 if int(candidate.get("version_no") or 1) > 1 else 0.0
    out["urgency"] = {
        "value": _clamp(fresh + version_bump),
        "reason": f"发表距今 {age_hours:.0f} 小时" if age_hours is not None else "发表时间未知",
    }

    # 7. evidence_quality —— DOI/期刊引用/篇幅注记（硬门已保底可溯源，此处只做加分）
    quality = 0.3
    marks: list[str] = []
    if meta.get("doi"):
        quality += 0.35
        marks.append("有 DOI")
    if meta.get("journal_ref"):
        quality += 0.25
        marks.append("有期刊引用")
    if re.search(r"\d+\s*(pages|figures)", meta.get("comment") or ""):
        quality += 0.10
        marks.append("注明篇幅/图表")
    out["evidence_quality"] = {"value": _clamp(quality), "reason": "、".join(marks) or "仅摘要级证据"}

    # 8. diversity —— 近期入选类目占比取反（鼓励跨板块广度）
    recent_primary: list[str] = list(context.get("recent_selected_primary") or [])
    if not recent_primary:
        value, reason = 0.6, "近期无入选记录，广度中性"
    else:
        share = recent_primary.count(primary) / len(recent_primary)
        value = _clamp(1.0 - share)
        reason = f"类目 {primary or '未知'} 占近期入选 {share:.0%}"
    out["diversity"] = {"value": value, "reason": reason}

    return out


def attention_cost(candidate: Mapping[str, Any]) -> tuple[float, str]:
    """注意力成本 0..1：摘要长度 + 数学密度."""
    meta = (candidate.get("metadata") or {}).get("arxiv") or {}
    summary = meta.get("summary") or ""
    words = len(summary.split())
    length_cost = _clamp((words - 120) / 300)
    math_density = len(re.findall(r"[\$\\{}^_=<>≤≥]|\b[A-Z]{3,}\b", summary)) / max(1, words)
    math_cost = _clamp(math_density * 6)
    cost = _clamp(0.6 * length_cost + 0.4 * math_cost)
    return cost, f"摘要 {words} 词，术语/符号密度 {math_density:.2f}"


def total_score(features: Mapping[str, Mapping[str, Any]], weights: Mapping[str, float],
                attention: float, penalty: float) -> tuple[float, dict[str, float]]:
    contributions = {
        key: round(float(weights[key]) * float(features[key]["value"]), 3) for key in FEATURE_KEYS
    }
    raw = sum(contributions.values()) - penalty * attention
    return round(raw, 3), contributions


def _age_hours(published: str, as_of: datetime) -> float | None:
    try:
        stamp = datetime.fromisoformat(published.replace("Z", "+00:00"))
    except ValueError:
        return None
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=timezone.utc)
    return max(0.0, (as_of - stamp).total_seconds() / 3600)


def legacy_score(features: Mapping[str, Mapping[str, Any]], attention: float,
                 legacy_weights: Mapping[str, float] | None = None) -> float:
    """旧 V7 research 权重的近似映射（R1-3 新旧头名对照用，只读不参与决策）.

    复审修复：权重不再硬编码——读 owner_controls.yaml scoring.research
    （config.load_legacy_research_weights），本函数只做维度映射。
    """
    if legacy_weights is None:
        from .config import load_legacy_research_weights

        legacy_weights = load_legacy_research_weights()
    val = {k: float(v["value"]) for k, v in features.items()}
    dims = {
        "relevance": val["user_relevance"],
        "novelty": val["novelty_to_user"],
        "evidence_quality": val["evidence_quality"],
        "technical_breakthrough": (val["knowledge_gap"] + val["novelty_to_user"]) / 2,
        "conversion_economic_value": val["transfer_potential"],
        "impact_scale": (val["user_relevance"] + val["transfer_potential"]) / 2,
        "timeliness_version_change": val["urgency"],
        "diversity_coverage": val["diversity"],
    }
    raw = sum(float(legacy_weights.get(dim, 0)) * value for dim, value in dims.items())
    return round(raw, 3)
