from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping


THEME_ALIASES = {
    "AI": ["AI", "人工智能", "大模型", "生成式人工智能", "智能算力"],
    "人工智能": ["AI", "人工智能", "大模型", "生成式人工智能", "智能算力"],
    "半导体": ["半导体", "芯片", "集成电路", "晶圆", "先进制程"],
    "芯片": ["半导体", "芯片", "集成电路", "晶圆", "先进制程"],
    "机器人": ["机器人", "人形机器人", "工业机器人", "具身智能"],
    "算力": ["算力", "数据中心", "智算中心", "云计算"],
    "银行": ["银行", "金融", "资本市场", "信贷", "利率"],
    "金融": ["金融", "银行", "证券", "保险", "资本市场"],
    "红利": ["红利", "分红", "央企", "国企", "低波"],
    "黄金": ["黄金", "贵金属", "矿产", "有色金属"],
    "农业": ["农业", "种业", "农机", "粮食", "乡村"],
    "化工": ["化工", "新材料", "石化", "精细化工"],
    "港股": ["港股", "香港", "粤港澳", "科技", "平台经济"],
    "美股": ["美股", "纳斯达克", "汇率", "外贸", "跨境投资"],
    "宽基": ["宏观经济", "资本市场", "指数", "经济运行"],
}


def write_ai_research_priority_file(
    request_file: str | Path,
    base_file: str | Path,
    output_file: str | Path,
) -> dict[str, Any]:
    request_path = Path(request_file)
    base_path = Path(base_file)
    output_path = Path(output_file)
    request = json.loads(request_path.read_text(encoding="utf-8"))
    base = json.loads(base_path.read_text(encoding="utf-8"))
    base_rules = list(base.get("industries") or [])
    requested_themes = _ordered_strings(request.get("themes") or [])
    symbols = list(request.get("symbols") or [])

    focused_rules = []
    used_names: set[str] = set()
    for theme in requested_themes:
        rule = _best_base_rule(theme, base_rules)
        related_symbols = [item for item in symbols if str(item.get("theme") or "") == theme]
        if rule:
            name = str(rule.get("name") or theme)
            keywords = _dedupe([*rule.get("keywords", []), *_theme_keywords(theme), *_symbol_keywords(related_symbols)])
        else:
            name = f"AI自选池 / {theme}"
            keywords = _dedupe([*_theme_keywords(theme), *_symbol_keywords(related_symbols)])
        if name in used_names:
            continue
        used_names.add(name)
        focused_rules.append({"rank": len(focused_rules) + 1, "name": name, "keywords": keywords})

    remaining = []
    for rule in base_rules:
        name = str(rule.get("name") or "")
        if name in used_names:
            continue
        remaining.append(
            {
                "rank": len(focused_rules) + len(remaining) + 1,
                "name": name,
                "keywords": list(rule.get("keywords") or []),
            }
        )

    payload = {
        "version": "ai-research-request-priority-v1",
        "default_since": str(base.get("default_since") or request.get("document_since") or "2025-01-01"),
        "request_file": str(request_path),
        "request_as_of": str(request.get("as_of") or ""),
        "industries": [*focused_rules, *remaining],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "output": str(output_path),
        "request_file": str(request_path),
        "focused_count": len(focused_rules),
        "total_count": len(payload["industries"]),
        "focused_industries": [item["name"] for item in focused_rules],
    }


def _best_base_rule(theme: str, base_rules: list[Mapping[str, Any]]) -> Mapping[str, Any] | None:
    theme_tokens = set(_theme_keywords(theme))
    best_rule = None
    best_score = 0
    for rule in base_rules:
        name = str(rule.get("name") or "")
        keywords = {str(item) for item in rule.get("keywords") or []}
        rule_blob = " ".join([name, *keywords])
        score = 0
        for token in theme_tokens:
            if token and token in rule_blob:
                score += 2
        for keyword in keywords:
            if keyword and keyword in theme:
                score += 3
        if score > best_score:
            best_score = score
            best_rule = rule
    return best_rule if best_score > 0 else None


def _theme_keywords(theme: str) -> list[str]:
    tokens = _split_tokens(theme)
    expanded = list(tokens)
    for token in tokens:
        expanded.extend(THEME_ALIASES.get(token, []))
    for alias, keywords in THEME_ALIASES.items():
        if alias in theme:
            expanded.extend(keywords)
    return _dedupe(expanded)


def _symbol_keywords(symbols: list[Mapping[str, Any]]) -> list[str]:
    values = []
    for item in symbols:
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        values.extend(_split_tokens(name))
        values.append(name)
    return _dedupe(values)


def _ordered_strings(values: list[Any]) -> list[str]:
    seen = set()
    ordered = []
    for value in values:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        ordered.append(text)
    return ordered


def _split_tokens(value: str) -> list[str]:
    parts = re.split(r"[\s/_｜|,，;；()（）-]+", value)
    return [part.strip() for part in parts if len(part.strip()) >= 2]


def _dedupe(values: list[Any]) -> list[str]:
    seen = set()
    output = []
    for value in values:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        output.append(text)
    return output
