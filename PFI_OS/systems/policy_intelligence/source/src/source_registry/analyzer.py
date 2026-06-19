from __future__ import annotations

import re
import subprocess
from typing import Any, Mapping

from .interpretation import count_reference_items, reference_platforms, research_digest

MAJOR_KEYWORDS = ("国务院", "国办", "规划", "意见", "办法", "白皮书", "决定", "金融", "科技", "产业", "财政")
TEMPLATE_ANALYSIS_MODE = "template_zh_single_v1"
CODEX_ANALYSIS_MODE = "codex_zh_v1"

POLICY_TYPE_RULES = [
    ("规划", ("规划", "纲要", "计划")),
    ("行政法规/规章", ("条例", "规定", "办法", "细则")),
    ("政策意见", ("意见", "若干措施", "政策措施")),
    ("通知/批复", ("通知", "批复", "公告")),
    ("白皮书/蓝皮书/报告", ("白皮书", "蓝皮书", "报告")),
]

INDUSTRY_RULES = [
    ("宏观经济", ("国民经济", "宏观", "发展规划", "经济运行", "投资", "消费")),
    ("财政税收", ("财政", "税", "预算", "政府采购", "转移支付", "债务")),
    ("金融与资本市场", ("金融", "银行", "证券", "保险", "资本", "外汇", "融资")),
    ("科技与数字经济", ("科技", "数字", "数据", "人工智能", "算力", "软件", "互联网")),
    ("先进制造与工业", ("制造", "工业", "装备", "产业链", "供应链", "质量强国")),
    ("农业农村", ("农业", "农村", "乡村", "粮食", "农产品", "耕地")),
    ("能源与双碳", ("能源", "电力", "煤炭", "油气", "新能源", "碳", "绿色")),
    ("房地产与城市更新", ("房地产", "住房", "城市更新", "城镇化", "物业", "保障房")),
    ("交通物流", ("交通", "物流", "港口", "铁路", "公路", "民航", "航运")),
    ("医疗健康与民生", ("医疗", "医保", "卫生", "养老", "残疾人", "教育", "就业")),
    ("外贸与跨境投资", ("外贸", "出口", "进口", "对外投资", "跨境", "自贸", "关税")),
]

REGION_WORDS = (
    "北京",
    "天津",
    "河北",
    "山西",
    "内蒙古",
    "辽宁",
    "吉林",
    "黑龙江",
    "上海",
    "江苏",
    "浙江",
    "安徽",
    "福建",
    "江西",
    "山东",
    "河南",
    "湖北",
    "湖南",
    "广东",
    "广西",
    "海南",
    "重庆",
    "四川",
    "贵州",
    "云南",
    "西藏",
    "陕西",
    "甘肃",
    "青海",
    "宁夏",
    "新疆",
    "香港",
    "澳门",
    "台湾",
    "粤港澳",
    "长三角",
    "京津冀",
    "成渝",
)


def template_analysis(
    document: Mapping[str, Any],
    interpretation_items: list[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    title = _clean_title(str(document.get("title") or ""))
    source_name = _clean(str(document.get("source_name") or ""))
    tier = _clean(str(document.get("authority_tier_snapshot") or "?"))
    score = int(document.get("authority_score_snapshot") or 0)
    excerpt = _clean_excerpt(str(document.get("text_excerpt") or ""))
    url = str(document.get("canonical_url") or document.get("url") or "")
    policy_type = _classify_policy_type(title, excerpt)
    industries = _match_terms(title + " " + excerpt, INDUSTRY_RULES) or ["待研判行业"]
    regions = _match_regions(title + " " + excerpt) or ["全国/跨区域"]
    importance = min(100, score + _keyword_bonus(title + excerpt))
    research_items = interpretation_items or []
    research_lines = research_digest(research_items, limit=8)
    reference_count = count_reference_items(research_items)
    platforms = reference_platforms(research_items)

    return {
        "document_id": document["document_id"],
        "analysis_mode": TEMPLATE_ANALYSIS_MODE,
        "language": "zh",
        "importance_score": importance,
        "importance_reason": _importance_reason(score, title, policy_type, industries),
        "chinese_summary": _summary(
            title=title,
            source_name=source_name,
            tier=tier,
            score=score,
            policy_type=policy_type,
            industries=industries,
            regions=regions,
            research_count=reference_count,
            platforms=platforms,
        ),
        "english_summary": "本报告已切换为全中文输出。",
        "policy_points": _policy_points(
            title,
            source_name,
            tier,
            score,
            policy_type,
            industries,
            regions,
            excerpt,
            url,
            research_lines,
        ),
        "business_impacts": _business_impacts(policy_type, industries, regions, research_items),
        "risks": _risks(policy_type, industries, excerpt, research_items),
        "actions": _actions(policy_type, industries, regions, research_items),
        "raw_analysis": None,
    }


def codex_analysis(
    document: Mapping[str, Any],
    interpretation_items: list[Mapping[str, Any]] | None = None,
    timeout_seconds: int = 240,
) -> dict[str, Any]:
    research_lines = research_digest(interpretation_items or [], limit=8)
    context = "\n".join(
        [
            f"标题：{document.get('title')}",
            f"来源：{document.get('source_name')}",
            f"权威等级：{document.get('authority_tier_snapshot')} / {document.get('authority_score_snapshot')}",
            f"链接：{document.get('url')}",
            "",
            "正文/页面摘录：",
            str(document.get("text_excerpt") or ""),
            "",
            "网络公开研究/解读资料：",
            "\n".join(f"- {line}" for line in research_lines) or "暂无。",
        ]
    )
    prompt = (
        "请用全中文为商业决策者生成一份专业、全面、深度的政策情报分析。"
        "必须包含：执行摘要、政策属性、政策背景与脉络、核心条款/方向、影响行业、影响地区、"
        "商业机会、风险与不确定性、企业行动建议、后续跟踪问题。"
        "禁止输出英文。若正文信息不足，请明确标注“基于标题与公开摘录的初步研判”。"
    )
    result = subprocess.run(
        ["codex", "exec", "--skip-git-repo-check", prompt],
        input=context,
        text=True,
        capture_output=True,
        timeout=timeout_seconds,
        check=False,
    )
    if result.returncode != 0:
        fallback = template_analysis(document, interpretation_items)
        fallback["importance_reason"] += f" Codex 深度分析失败，已回退到模板分析：{result.stderr[:200]}"
        return fallback
    analysis = template_analysis(document, interpretation_items)
    analysis["analysis_mode"] = CODEX_ANALYSIS_MODE
    analysis["raw_analysis"] = result.stdout.strip()
    analysis["chinese_summary"] = result.stdout.strip()[:1600] or analysis["chinese_summary"]
    analysis["english_summary"] = "本报告已切换为全中文输出。"
    return analysis


def _summary(
    title: str,
    source_name: str,
    tier: str,
    score: int,
    policy_type: str,
    industries: list[str],
    regions: list[str],
    research_count: int,
    platforms: list[str],
) -> str:
    research_sentence = (
        f"本次已同步参考{research_count}条网络公开研究/解读资料，覆盖{_join(platforms) or '多个公开平台'}，用于补充市场观点、专家表达和传播热度。"
        if research_count
        else "本次暂未匹配到可用的网络公开研究/解读资料，外部观点仍需后续补采。"
    )
    return (
        f"{source_name}发布或列示《{title}》。该文件初步归类为“{policy_type}”，"
        f"来源权威等级为{tier}、权威分为{score}。"
        f"从商业决策视角看，应优先关注其对{_join(industries)}的影响，"
        f"地域口径暂按{_join(regions)}处理。"
        f"{research_sentence}"
        "当前结论为自动化初步研判，适合用于每日监测、优先级排序和后续深度解读排队。"
    )


def _policy_points(
    title: str,
    source_name: str,
    tier: str,
    score: int,
    policy_type: str,
    industries: list[str],
    regions: list[str],
    excerpt: str,
    url: str,
    research_lines: list[str],
) -> list[str]:
    points = [
        f"文件标题：《{title}》。",
        f"发布/列示来源：{source_name}，来源权威性为{tier}/{score}。",
        f"政策属性：{policy_type}。",
        f"行业映射：{_join(industries)}。",
        f"地区映射：{_join(regions)}。",
        f"证据链：来源链接 {url}。",
    ]
    if excerpt:
        points.append(f"公开页面摘录：{excerpt[:260]}。")
    else:
        points.append("正文摘录暂缺，当前主要基于标题、来源和链接结构进行初步研判。")
    if research_lines:
        points.append("网络公开研究/解读参考：" + "；".join(research_lines[:3]) + "。")
    return points


def _business_impacts(
    policy_type: str,
    industries: list[str],
    regions: list[str],
    research_items: list[Mapping[str, Any]],
) -> list[str]:
    impacts = [
        f"对{_join(industries)}相关企业，文件可能影响政策预期、项目审批、投资节奏、合规要求或财政资金流向。",
        f"对{_join(regions)}，建议关注地方配套政策、专项资金、试点城市/园区、监管执行口径是否随后出台。",
    ]
    if policy_type == "规划":
        impacts.append("规划类文件通常影响中长期产业方向、基础设施布局、财政预算安排和地方政府项目储备。")
    elif policy_type == "行政法规/规章":
        impacts.append("法规/规章类文件更可能带来硬约束，企业需优先评估合规义务、处罚风险和内部制度调整。")
    elif policy_type == "政策意见":
        impacts.append("意见类文件通常是政策方向和工作部署信号，需跟踪后续部门细则、地方方案和配套资金。")
    elif policy_type == "白皮书/蓝皮书/报告":
        impacts.append("报告类文件更适合作为趋势判断和政策叙事材料，应与正式政策文件分开标注权威层级。")
    else:
        impacts.append("通知/批复类文件通常执行性较强，建议核查是否涉及具体区域、项目、主体或时间节点。")
    themes = _research_themes(research_items)
    if themes:
        impacts.append(f"外部解读资料当前集中出现的主题包括：{_join(themes)}；可作为判断市场关注点和传播方向的辅助线索。")
    return impacts


def _risks(
    policy_type: str,
    industries: list[str],
    excerpt: str,
    research_items: list[Mapping[str, Any]],
) -> list[str]:
    risks = [
        "当前自动化分析不能替代全文条款审阅；涉及投资、合规、税费、补贴申请时必须回看原文。",
        "若文件为转载、解读或新闻稿，应与政策原文分开判断，避免把媒体口径误当成监管要求。",
    ]
    if not excerpt:
        risks.append("正文摘录不足，存在标题误判、链接页非正式原文或附件未解析导致的信息缺口。")
    if "金融与资本市场" in industries:
        risks.append("金融相关政策可能涉及牌照、资本约束、信息披露和跨境合规，需单独做法律/合规复核。")
    if policy_type == "规划":
        risks.append("规划类政策落地周期较长，商业机会需等待细则、预算、项目清单和地方执行方案确认。")
    if research_items:
        risks.append("B站、媒体、智库和自媒体解读只能作为观点与传播热度参考；正式结论必须以官方原文、附件和主管部门解释为准。")
    return risks


def _actions(
    policy_type: str,
    industries: list[str],
    regions: list[str],
    research_items: list[Mapping[str, Any]],
) -> list[str]:
    actions = [
        f"将该文件加入{_join(industries)}政策跟踪清单，标注影响地区为{_join(regions)}。",
        "安排后续步骤：抓取全文/附件、提取关键条款、识别主管部门、比对既有政策变化。",
        "对业务部门输出一页式行动建议：受影响产品/区域、潜在机会、合规动作、需要管理层决策的事项。",
        "跟踪后续信号：部门实施细则、地方配套政策、财政资金安排、试点名单、公开征求意见稿。",
        f"若确认为{policy_type}且重要性高，进入深度解读队列并由 Codex 模式或人工复核补充完整研判。",
    ]
    if research_items:
        actions.append("复核高播放/高相关外部解读中的关键观点，提取可验证判断，并与官方条款逐条对照。")
    return actions


def _importance_reason(score: int, title: str, policy_type: str, industries: list[str]) -> str:
    return (
        f"评分由来源权威分{score}、政策属性“{policy_type}”、标题关键词命中情况和行业映射综合形成。"
        f"当前命中行业：{_join(industries)}；标题关键词：{_matched_keywords(title) or '未命中重大关键词'}。"
    )


def _classify_policy_type(title: str, excerpt: str) -> str:
    text = title + " " + excerpt
    for policy_type, keywords in POLICY_TYPE_RULES:
        if any(keyword in text for keyword in keywords):
            return policy_type
    return "政策信息/待分类"


def _match_terms(text: str, rules: list[tuple[str, tuple[str, ...]]]) -> list[str]:
    return [label for label, keywords in rules if any(keyword in text for keyword in keywords)]


def _match_regions(text: str) -> list[str]:
    return [region for region in REGION_WORDS if region in text]


def _keyword_bonus(text: str) -> int:
    return min(14, sum(3 for keyword in MAJOR_KEYWORDS if keyword in text))


def _matched_keywords(text: str) -> str:
    return "、".join(keyword for keyword in MAJOR_KEYWORDS if keyword in text)


def _research_themes(items: list[Mapping[str, Any]]) -> list[str]:
    text = " ".join(
        str(item.get("title") or "") + " " + str(item.get("content_excerpt") or "")
        for item in items
    )
    themes = []
    for label, keywords in INDUSTRY_RULES:
        if any(keyword in text for keyword in keywords):
            themes.append(label)
    for keyword in ("政策解读", "投资", "申报", "合规", "就业", "地产", "消费", "出海"):
        if keyword in text and keyword not in themes:
            themes.append(keyword)
    return themes[:5]


def _join(items: list[str]) -> str:
    return "、".join(items)


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _clean_title(value: str) -> str:
    title = _clean(value)
    suffixes = (
        "_国务院办公厅政府信息公开指南（试行）_信息公开_政策_中国政府网",
        "_其他_中国政府网",
        "__中国政府网",
        "_中国政府网",
        "_其他",
    )
    for suffix in suffixes:
        if title.endswith(suffix):
            title = title[: -len(suffix)]
    return title.strip(" _-")


def _clean_excerpt(value: str) -> str:
    text = _clean(value)
    noise_patterns = (
        r"var\s+INFO_FLAG=.*?(?=首页|国务院|新华社|[一-龥]{4,})",
        r"@media\s+screen.*?(?=首页|国务院|新华社|[一-龥]{4,})",
        r"/\*\s*20231023.*?(?=首页|国务院|新华社|[一-龥]{4,})",
        r"function\s+\w+\(.*?(?=首页|国务院|新华社|[一-龥]{4,})",
    )
    for pattern in noise_patterns:
        text = re.sub(pattern, "", text)
    fragments = []
    for fragment in re.split(r"[。；;]", text):
        item = fragment.strip()
        if not item:
            continue
        if any(
            marker in item
            for marker in (
                "font-size",
                "header_toolbar",
                "无障碍",
                "登录 个人中心",
                "邮箱",
                "window.open",
                "encodeURIComponent",
                "currUrl",
                "big5.www",
                "url =",
                "function ",
                "var ",
                "繁体和简体",
            )
        ):
            continue
        fragments.append(item)
        if len("。".join(fragments)) > 700:
            break
    return "。".join(fragments).strip()
