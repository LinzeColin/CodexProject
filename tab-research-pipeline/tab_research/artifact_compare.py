from __future__ import annotations

import json
from pathlib import Path
from typing import Any


MetricSpec = tuple[str, str]


def build_artifact_old_new_compare(
    previous_json_path: Path,
    current_payload: dict[str, Any],
    metrics: list[MetricSpec],
) -> dict[str, Any]:
    previous_payload = load_previous_payload(previous_json_path)
    current_rows = metric_rows(current_payload, previous_payload, metrics)
    if previous_payload is None:
        return {
            "status": "no_previous_artifact",
            "previous_generated_at": "",
            "metric_count": len(current_rows),
            "changed_count": 0,
            "rows": current_rows,
            "summary": "暂无上一版 artifact 可比；已建立本次新旧对比基线。",
        }
    changed_count = len([row for row in current_rows if row["changed"]])
    return {
        "status": "compared_with_previous_artifact",
        "previous_generated_at": str(previous_payload.get("generated_at") or ""),
        "metric_count": len(current_rows),
        "changed_count": changed_count,
        "rows": current_rows,
        "summary": f"{changed_count}/{len(current_rows)} 个关键指标发生变化。",
    }


def load_previous_payload(path: Path) -> dict[str, Any] | None:
    try:
        if not Path(path).exists():
            return None
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def metric_rows(current: dict[str, Any], previous: dict[str, Any] | None, metrics: list[MetricSpec]) -> list[dict[str, Any]]:
    rows = []
    for label, path in metrics:
        current_value = get_path(current, path)
        previous_value = get_path(previous or {}, path) if previous else None
        delta = value_delta(current_value, previous_value)
        rows.append(
            {
                "metric": label,
                "path": path,
                "current": display_value(current_value),
                "previous": display_value(previous_value) if previous else "",
                "delta": delta,
                "changed": bool(previous) and normalize(current_value) != normalize(previous_value),
            }
        )
    return rows


def get_path(payload: dict[str, Any], path: str) -> Any:
    value: Any = payload
    for part in path.split("."):
        if isinstance(value, dict):
            value = value.get(part)
        else:
            return None
    return value


def value_delta(current: Any, previous: Any) -> str:
    if previous is None:
        return ""
    if isinstance(current, bool) or isinstance(previous, bool):
        return str(int(bool(current)) - int(bool(previous)))
    try:
        return format_delta(float(current or 0) - float(previous or 0))
    except (TypeError, ValueError):
        return "changed" if normalize(current) != normalize(previous) else "0"


def format_delta(value: float) -> str:
    if abs(value) < 0.000001:
        return "0"
    return f"{value:+.4f}".rstrip("0").rstrip(".")


def normalize(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.8f}"
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def display_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return f"{value:.4f}".rstrip("0").rstrip(".")
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)
