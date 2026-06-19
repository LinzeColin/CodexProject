from __future__ import annotations

import math
from collections import Counter
from typing import Dict, Iterable, List, Tuple


def mermaid_pie(title: str, items: Iterable[Tuple[str, float]]) -> str:
    rows = [(clean_label(label), max(0.0, float(value or 0))) for label, value in items]
    rows = [(label, value) for label, value in rows if value > 0]
    if not rows:
        return "_暂无可绘制数据。_"
    lines = ["```mermaid", "pie showData", f"    title {clean_title(title)}"]
    for label, value in rows:
        lines.append(f'    "{label}" : {round(value, 2)}')
    lines.append("```")
    return "\n".join(lines)


def mermaid_bar(title: str, items: Iterable[Tuple[str, float]], y_label: str = "value") -> str:
    rows = [(clean_axis_label(label), max(0.0, float(value or 0))) for label, value in items]
    rows = [(label, value) for label, value in rows if value > 0][:8]
    if not rows:
        return "_暂无可绘制数据。_"
    labels = ", ".join(label for label, _value in rows)
    values = ", ".join(str(round(value, 4)) for _label, value in rows)
    y_max = nice_axis_max(max(value for _label, value in rows))
    lines = [
        "```mermaid",
        "xychart-beta",
        f'    title "{clean_title(title)}"',
        f"    x-axis [{labels}]",
        f'    y-axis "{clean_axis_label(y_label)}" 0 --> {y_max}',
        f"    bar [{values}]",
        "```",
    ]
    return "\n".join(lines)


def decision_distribution(recommendations: Iterable[Dict]) -> List[Tuple[str, int]]:
    counter = Counter(str(item.get("decision") or item.get("action") or "unknown") for item in recommendations)
    return sorted(counter.items(), key=lambda item: (-item[1], item[0]))


def top_items(items: Iterable[Dict], label_key: str, value_key: str, limit: int = 6) -> List[Tuple[str, float]]:
    rows = []
    for item in items:
        label = str(item.get(label_key) or item.get("selection") or item.get("team") or item.get("market") or "")
        rows.append((label, float(item.get(value_key) or 0)))
    rows.sort(key=lambda item: item[1], reverse=True)
    return rows[:limit]


def nice_axis_max(value: float) -> float:
    if value <= 1:
        return round(max(0.1, value * 1.2), 2)
    magnitude = 10 ** math.floor(math.log10(value))
    return math.ceil(value * 1.15 / magnitude) * magnitude


def clean_title(value: str) -> str:
    return str(value or "").replace("\n", " ").replace('"', "'").strip()


def clean_label(value: str) -> str:
    return clean_title(value).replace("|", "/")[:48] or "unknown"


def clean_axis_label(value: str) -> str:
    text = clean_label(value)
    return text.replace(",", " ").replace("[", "(").replace("]", ")")[:28] or "unknown"
