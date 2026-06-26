"""Owner-editable controls and generated owner-readable views."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from .stage1_queue import (
    STAGE1_CONTENT_LEDGER_COLUMNS,
    placeholder_content_ledger_rows,
    render_content_ledger_csv,
)


OWNER_CONTROLS_MODEL_ID = "adp-owner-controls-v1"
OWNER_CONTROLS_SCHEMA_VERSION = 1
OWNER_CONTROL_DOCS: tuple[str, ...] = (
    "docs/owner/OWNER_CONSOLE.md",
    "docs/owner/SOURCE_CATALOG.md",
    "docs/owner/MODEL_AND_QUEUE.md",
    "docs/owner/CONTENT_LEDGER.csv",
)
CONTENT_LEDGER_COLUMNS: tuple[str, ...] = STAGE1_CONTENT_LEDGER_COLUMNS
SECRET_KEY_PATTERN = re.compile(
    r"(^|[_-])(password|token|secret|private[_-]?key|client[_-]?secret|credential)([_-]|$)",
    re.I,
)
SECRET_VALUE_PATTERN = re.compile(r"(sk-[A-Za-z0-9_-]{12,}|gh[pousr]_[A-Za-z0-9_]{12,}|xox[baprs]-[A-Za-z0-9-]{12,})")


class OwnerControlsError(ValueError):
    """Raised when owner controls cannot be parsed or rendered."""


def project_root_default(cwd: Path | None = None) -> Path:
    base = cwd or Path.cwd()
    nested = base / "arxiv-daily-push"
    return nested if nested.is_dir() else base


def default_controls_path(cwd: Path | None = None) -> Path:
    root = project_root_default(cwd)
    return root / "config" / "owner_controls.yaml"


def load_owner_controls(path: str | Path | None = None) -> dict[str, Any]:
    controls_path = Path(path) if path else default_controls_path()
    if not controls_path.is_file():
        raise OwnerControlsError(f"owner controls file not found: {controls_path}")
    data = _load_yaml(controls_path)
    if not isinstance(data, dict):
        raise OwnerControlsError("owner controls root must be a mapping")
    return data


def validate_owner_controls(controls: Mapping[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    required_sections = (
        "schema_version",
        "config_version",
        "project",
        "cost_policy",
        "runtime",
        "intelligence_provider",
        "boards",
        "sources",
        "email",
        "outputs",
        "queue",
        "scoring",
        "source_defaults",
        "iteration",
        "validation",
    )
    for section in required_sections:
        if section not in controls:
            errors.append(f"missing required section: {section}")
    if controls.get("schema_version") != OWNER_CONTROLS_SCHEMA_VERSION:
        errors.append(f"schema_version must be {OWNER_CONTROLS_SCHEMA_VERSION}")
    project = _mapping(controls.get("project"))
    if project.get("production_enabled") is not False:
        errors.append("project.production_enabled must remain false until production acceptance")
    outputs = _mapping(controls.get("outputs"))
    if outputs.get("production_acceptance_claimed") is not False:
        errors.append("outputs.production_acceptance_claimed must be false")
    cost_policy = _mapping(controls.get("cost_policy"))
    for flag in ("paid_data_api_allowed", "paid_cloud_compute_allowed", "paid_openai_api_allowed"):
        if cost_policy.get(flag) is True:
            errors.append(f"cost_policy.{flag} must not be true in Window A")
    intelligence = _mapping(controls.get("intelligence_provider"))
    if intelligence.get("paid_openai_api_allowed") is True:
        errors.append("intelligence_provider.paid_openai_api_allowed must not be true in Window A")
    errors.extend(_secret_hygiene_errors(controls))
    weight_groups = _weight_group_reports(controls)
    for group in weight_groups:
        if group["status"] != "pass":
            errors.append(
                f"weight group {group['group_id']} must sum to {group['target']:g} "
                f"within tolerance {group['tolerance']:g}; got {group['total']:g}"
            )
    window_errors, window_warnings = _window_a_resource_messages(controls)
    errors.extend(window_errors)
    warnings.extend(window_warnings)
    owner_views = _generated_owner_views(controls)
    if tuple(owner_views) != OWNER_CONTROL_DOCS:
        errors.append("validation.machine_generated_owner_views must list the four canonical owner docs in order")
    return {
        "model_id": OWNER_CONTROLS_MODEL_ID,
        "status": "pass" if not errors else "blocked",
        "schema_valid": not errors,
        "config_version": str(controls.get("config_version") or ""),
        "task_id": str(controls.get("task_id") or ""),
        "production_enabled": project.get("production_enabled"),
        "weight_groups": weight_groups,
        "owner_view_files": owner_views,
        "rollback_config_version": str(_mapping(controls.get("validation")).get("rollback_config_version") or ""),
        "warnings": warnings,
        "errors": errors,
    }


def build_owner_impact_preview(controls: Mapping[str, Any], *, days: int = 30) -> dict[str, Any]:
    validation = validate_owner_controls(controls)
    enabled_sources = [item for item in _sequence_of_mappings(controls.get("sources")) if item.get("enabled") is True]
    enabled_boards = [item for item in _sequence_of_mappings(controls.get("boards")) if item.get("enabled") is True]
    queue = _mapping(controls.get("queue"))
    runtime = _mapping(controls.get("runtime"))
    window = _mapping(runtime.get("window_a_resource_limits"))
    email = _mapping(controls.get("email"))
    outputs = _mapping(controls.get("outputs"))
    return {
        "model_id": OWNER_CONTROLS_MODEL_ID,
        "status": validation["status"],
        "days": int(days),
        "config_version": str(controls.get("config_version") or ""),
        "schema_status": "pass" if validation["schema_valid"] else "blocked",
        "source_or_board_changes": "NOT_COMPUTED_NO_PRIOR_OWNER_CONTROLS_BASELINE",
        "enabled_sources": [str(item.get("source_id")) for item in enabled_sources],
        "enabled_boards": [str(item.get("board_id")) for item in enabled_boards],
        "ranking_change_preview": "S1_06_DETERMINISTIC_QUEUE_READY_NO_PRODUCTION_REPLAY_DATA",
        "queue_change_preview": {
            "max_active_items": int(queue.get("max_active_items") or 0),
            "new_items": "NOT_COMPUTED_NO_REPLAY_DATA",
            "exited_items": "NOT_COMPUTED_NO_REPLAY_DATA",
        },
        "email_coverage_preview": {
            "enabled": bool(email.get("enabled")),
            "split_mode": str(email.get("split_mode") or ""),
            "send_order": [str(item) for item in _as_sequence(email.get("send_order"))],
            "report_enabled": bool(outputs.get("report_enabled")),
            "audit_formats": ["markdown", "html", "json"],
        },
        "resource_estimate": {
            "max_fetch_concurrency": int(runtime.get("max_fetch_concurrency") or 0),
            "max_temp_cache_gb": float(runtime.get("max_temp_cache_gb") or 0),
            "window_a_max_online_arxiv_metadata": int(window.get("max_online_arxiv_metadata") or 0),
        },
        "rollback_config_version": validation["rollback_config_version"],
        "warnings": validation["warnings"],
        "errors": validation["errors"],
    }


def render_owner_documents(
    controls: Mapping[str, Any],
    *,
    project_path: str | Path | None = None,
    generated_at: str,
    write: bool = True,
) -> dict[str, Any]:
    root = Path(project_path) if project_path else project_root_default()
    validation = validate_owner_controls(controls)
    preview = build_owner_impact_preview(controls)
    docs = {
        "docs/owner/OWNER_CONSOLE.md": _render_owner_console(controls, validation, preview, generated_at),
        "docs/owner/SOURCE_CATALOG.md": _render_source_catalog(controls, generated_at),
        "docs/owner/MODEL_AND_QUEUE.md": _render_model_and_queue(controls, validation, preview, generated_at),
        "docs/owner/CONTENT_LEDGER.csv": _render_content_ledger_csv(generated_at),
    }
    written: list[str] = []
    if write:
        for relative_path, content in docs.items():
            output_path = root / relative_path
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(content, encoding="utf-8", newline="")
            written.append(relative_path)
    return {
        "model_id": OWNER_CONTROLS_MODEL_ID,
        "status": "rendered" if validation["status"] == "pass" else "blocked",
        "generated_at": generated_at,
        "config_version": str(controls.get("config_version") or ""),
        "generated_from": "config/owner_controls.yaml",
        "owner_view_files": list(docs),
        "written_files": written,
        "errors": validation["errors"],
    }


def _render_owner_console(
    controls: Mapping[str, Any],
    validation: Mapping[str, Any],
    preview: Mapping[str, Any],
    generated_at: str,
) -> str:
    project = _mapping(controls.get("project"))
    email = _mapping(controls.get("email"))
    outputs = _mapping(controls.get("outputs"))
    lines = [
        "# Owner Console",
        "",
        f"- generated_at: {generated_at}",
        "- generated_from: `config/owner_controls.yaml`",
        f"- config_version: `{controls.get('config_version')}`",
        f"- task_id: `{controls.get('task_id')}`",
        f"- model_id: `{OWNER_CONTROLS_MODEL_ID}`",
        f"- validation_status: `{validation.get('status')}`",
        f"- production_enabled: `{_bool_text(project.get('production_enabled'))}`",
        f"- production_acceptance_claimed: `{_bool_text(outputs.get('production_acceptance_claimed'))}`",
        "",
        "## Current Conclusion",
        "",
        "Owner controls are installed for Stage 1 Window A. Production remains disabled; this run does not prove scheduled production, 30-day trial evidence, or live two-day operation.",
        "",
        "## Today Mail Plan",
        "",
        f"- email_enabled: `{_bool_text(email.get('enabled'))}`",
        f"- split_mode: `{email.get('split_mode')}`",
        f"- send_order: {_comma_list(_as_sequence(email.get('send_order')))}",
        f"- recipients: {_comma_list(_as_sequence(email.get('recipients')))}",
        "",
        "## Queue And Resource Pressure",
        "",
        f"- max_active_items: `{_mapping(controls.get('queue')).get('max_active_items')}`",
        f"- max_temp_cache_gb: `{_mapping(controls.get('runtime')).get('max_temp_cache_gb')}`",
        f"- window_a_max_online_arxiv_metadata: `{_mapping(_mapping(controls.get('runtime')).get('window_a_resource_limits')).get('max_online_arxiv_metadata')}`",
        f"- ranking_change_preview: `{preview.get('ranking_change_preview')}`",
        "",
        "## Required Human Decisions",
        "",
        "- No production enablement decision is accepted by this file alone.",
        "- S1-06 deterministic queue fixtures are available; production replay remains unclaimed until later runtime evidence exists.",
        "",
        "## Commands",
        "",
        "- `adp owner validate`",
        "- `adp owner preview-impact --days 30`",
        "- `adp owner render-docs --write`",
    ]
    return "\n".join(lines) + "\n"


def _render_source_catalog(controls: Mapping[str, Any], generated_at: str) -> str:
    lines = [
        "# 来源目录",
        "",
        f"- 生成时间: {generated_at}",
        "- 来源配置: `config/owner_controls.yaml`",
        f"- 配置版本: `{controls.get('config_version')}`",
        "",
        "## 板块",
        "",
        "| 板块 ID | 启用 | 名称 | 权重 |",
        "|---|---:|---|---:|",
    ]
    for board in _sequence_of_mappings(controls.get("boards")):
        lines.append(
            f"| `{board.get('board_id')}` | {_bool_text_zh(board.get('enabled'))} | {board.get('name')} | {board.get('weight')} |"
        )
    lines.extend(["", "## 来源", "", "| 来源 ID | 板块 | 启用 | 名称 | 采集方式 | 层级 | 频率 | 权重 | 健康状态 |", "|---|---|---:|---|---|---|---|---:|---|"])
    for source in _sequence_of_mappings(controls.get("sources")):
        lines.append(
            "| "
            f"`{source.get('source_id')}` | `{source.get('board_id')}` | {_bool_text_zh(source.get('enabled'))} | "
            f"{source.get('name')} | `{source.get('access_method')}` | `{source.get('tier')}` | "
            f"`{source.get('frequency')}` | {source.get('weight')} | {_health_status_text_zh(source.get('health_status'))} |"
        )
    return "\n".join(lines) + "\n"


def _render_model_and_queue(
    controls: Mapping[str, Any],
    validation: Mapping[str, Any],
    preview: Mapping[str, Any],
    generated_at: str,
) -> str:
    lines = [
        "# Model And Queue",
        "",
        f"- generated_at: {generated_at}",
        "- generated_from: `config/owner_controls.yaml`",
        f"- model_id: `{OWNER_CONTROLS_MODEL_ID}`",
        f"- validation_status: `{validation.get('status')}`",
        f"- rollback_config_version: `{validation.get('rollback_config_version')}`",
        "",
        "## Weight Groups",
        "",
        "| Group | Total | Target | Tolerance | Status |",
        "|---|---:|---:|---:|---|",
    ]
    for group in validation.get("weight_groups", []):
        if isinstance(group, Mapping):
            lines.append(
                f"| `{group.get('group_id')}` | {group.get('total')} | {group.get('target')} | {group.get('tolerance')} | `{group.get('status')}` |"
            )
    lines.extend(["", "## Scoring Cards"])
    scoring = _mapping(controls.get("scoring"))
    for name, weights in scoring.items():
        lines.extend(["", f"### {name}", "", "| Component | Weight |", "|---|---:|"])
        for component, value in _mapping(weights).items():
            lines.append(f"| `{component}` | {value} |")
    queue = _mapping(controls.get("queue"))
    lines.extend(
        [
            "",
            "## Queue",
            "",
            f"- max_active_items: `{queue.get('max_active_items')}`",
            f"- max_event_age_days: `{queue.get('max_event_age_days')}`",
            f"- source_share_cap_per_board: `{queue.get('source_share_cap_per_board')}`",
            f"- replay_status: `{preview.get('ranking_change_preview')}`",
        ]
    )
    return "\n".join(lines) + "\n"


def _render_content_ledger_csv(generated_at: str) -> str:
    return render_content_ledger_csv(placeholder_content_ledger_rows(generated_at=generated_at))


def _weight_group_reports(controls: Mapping[str, Any]) -> list[dict[str, Any]]:
    validation = _mapping(controls.get("validation"))
    target = float(validation.get("weight_target") or 100)
    tolerance = float(validation.get("weight_tolerance") or 0.0001)
    reports: list[dict[str, Any]] = []
    reports.append(_weight_group("owner_sources", _weights_from_sequence(controls.get("sources")), target, tolerance))
    reports.append(_weight_group("owner_boards", _weights_from_sequence(controls.get("boards")), target, tolerance))
    scoring = _mapping(controls.get("scoring"))
    for group_id, weights in scoring.items():
        reports.append(_weight_group(f"owner_scoring_{group_id}", _weights_from_mapping(weights), target, tolerance))
    if "us_attention_budget" in controls:
        reports.append(_weight_group("owner_us_attention_budget", _weights_from_mapping(controls.get("us_attention_budget")), target, tolerance))
    return reports


def _weight_group(group_id: str, weights: Sequence[float], target: float, tolerance: float) -> dict[str, Any]:
    total = float(sum(weights))
    return {
        "group_id": group_id,
        "total": round(total, 10),
        "target": target,
        "tolerance": tolerance,
        "status": "pass" if abs(total - target) <= tolerance else "blocked",
        "component_count": len(weights),
    }


def _weights_from_sequence(value: Any) -> list[float]:
    return [float(item.get("weight") or 0) for item in _sequence_of_mappings(value)]


def _weights_from_mapping(value: Any) -> list[float]:
    return [float(item) for item in _mapping(value).values()]


def _window_a_resource_messages(controls: Mapping[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    runtime = _mapping(controls.get("runtime"))
    window = _mapping(runtime.get("window_a_resource_limits"))
    if int(window.get("max_online_arxiv_metadata") or 0) > 10:
        errors.append("runtime.window_a_resource_limits.max_online_arxiv_metadata must be <= 10")
    if float(window.get("max_temp_cache_gb") or 0) > 2:
        errors.append("runtime.window_a_resource_limits.max_temp_cache_gb must be <= 2")
    if window.get("large_pdf_download_allowed") is not False:
        errors.append("runtime.window_a_resource_limits.large_pdf_download_allowed must be false")
    if float(runtime.get("min_free_disk_gb") or 0) < 40:
        warnings.append("runtime.min_free_disk_gb is below emergency buffer guidance")
    return errors, warnings


def _secret_hygiene_errors(value: Any, path: str = "$") -> list[str]:
    errors: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            if SECRET_KEY_PATTERN.search(key_text) and item not in (False, "", None, "NOT_APPLICABLE"):
                errors.append(f"{path}.{key_text} looks like a secret-bearing key and must not contain values")
            errors.extend(_secret_hygiene_errors(item, f"{path}.{key_text}"))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            errors.extend(_secret_hygiene_errors(item, f"{path}[{index}]"))
    elif isinstance(value, str) and SECRET_VALUE_PATTERN.search(value):
        errors.append(f"{path} contains a token-like value")
    return errors


def _generated_owner_views(controls: Mapping[str, Any]) -> list[str]:
    return [str(item) for item in _as_sequence(_mapping(controls.get("validation")).get("machine_generated_owner_views"))]


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _as_sequence(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _sequence_of_mappings(value: Any) -> list[Mapping[str, Any]]:
    return [item for item in _as_sequence(value) if isinstance(item, Mapping)]


def _bool_text(value: Any) -> str:
    return "true" if value is True else "false" if value is False else str(value)


def _bool_text_zh(value: Any) -> str:
    return "是" if value is True else "否" if value is False else str(value)


def _health_status_text_zh(value: Any) -> str:
    status = str(value or "")
    labels = {
        "active": "已启用",
        "stage2_test": "影子测试",
        "planned": "规划中",
    }
    label = labels.get(status, status or "未填写")
    return f"{label} (`{status}`)" if status else label


def _comma_list(values: Sequence[Any]) -> str:
    return ", ".join(f"`{item}`" for item in values) if values else "`NOT_APPLICABLE`"


def _strip_comment(raw: str) -> str:
    in_single = False
    in_double = False
    escaped = False
    chars: list[str] = []
    for char in raw:
        if char == "\\" and in_double and not escaped:
            escaped = True
            chars.append(char)
            continue
        if char == "'" and not in_double and not escaped:
            in_single = not in_single
        elif char == '"' and not in_single and not escaped:
            in_double = not in_double
        if char == "#" and not in_single and not in_double:
            break
        chars.append(char)
        escaped = False
    return "".join(chars).rstrip()


def _parse_scalar(value: str) -> Any:
    if value == "":
        return ""
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"null", "none"}:
        return None
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        return [] if not inner else [_parse_scalar(part.strip()) for part in inner.split(",")]
    if value.startswith("{") and value.endswith("}"):
        return {} if value == "{}" else json.loads(value)
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    if re.fullmatch(r"-?\d+\.\d+", value):
        return float(value)
    return value


def _split_key_value(text: str) -> tuple[str, str | None]:
    if ":" not in text:
        return text.strip(), None
    key, value = text.split(":", 1)
    return key.strip(), value.strip()


def _fallback_yaml_load(text: str) -> Any:
    lines: list[tuple[int, str]] = []
    for raw in text.splitlines():
        cleaned = _strip_comment(raw)
        if not cleaned.strip():
            continue
        indent = len(cleaned) - len(cleaned.lstrip(" "))
        lines.append((indent, cleaned.strip()))
    if not lines:
        return {}

    def parse_block(index: int, indent: int) -> tuple[Any, int]:
        if index >= len(lines):
            return {}, index
        if lines[index][1].startswith("- ") or lines[index][1] == "-":
            result: list[Any] = []
            while index < len(lines) and lines[index][0] == indent and (
                lines[index][1].startswith("- ") or lines[index][1] == "-"
            ):
                item_text = lines[index][1][1:].strip()
                index += 1
                if item_text == "":
                    child_indent = lines[index][0] if index < len(lines) else indent + 2
                    item, index = parse_block(index, child_indent)
                    result.append(item)
                    continue
                key, value = _split_key_value(item_text)
                if value is None:
                    result.append(_parse_scalar(item_text))
                    continue
                item_map: dict[str, Any] = {key: _parse_scalar(value) if value != "" else {}}
                while index < len(lines) and lines[index][0] > indent:
                    child_indent, child_text = lines[index]
                    child_key, child_value = _split_key_value(child_text)
                    if child_value is None:
                        break
                    if child_value == "":
                        next_index = index + 1
                        if next_index < len(lines) and lines[next_index][0] > child_indent:
                            child, index = parse_block(next_index, lines[next_index][0])
                            item_map[child_key] = child
                        else:
                            item_map[child_key] = {}
                            index += 1
                    else:
                        item_map[child_key] = _parse_scalar(child_value)
                        index += 1
                result.append(item_map)
            return result, index

        result_map: dict[str, Any] = {}
        while index < len(lines) and lines[index][0] == indent and not (
            lines[index][1].startswith("- ") or lines[index][1] == "-"
        ):
            key, value = _split_key_value(lines[index][1])
            if value is None:
                raise OwnerControlsError(f"Invalid YAML line: {lines[index][1]}")
            if value == "":
                next_index = index + 1
                if next_index < len(lines) and lines[next_index][0] > indent:
                    child, index = parse_block(next_index, lines[next_index][0])
                    result_map[key] = child
                else:
                    result_map[key] = {}
                    index += 1
            else:
                result_map[key] = _parse_scalar(value)
                index += 1
        return result_map, index

    parsed, end = parse_block(0, lines[0][0])
    if end != len(lines):
        raise OwnerControlsError(f"Could not parse YAML near line: {lines[end][1]}")
    return parsed


def _load_yaml(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        return yaml.safe_load(text) or {}
    except ModuleNotFoundError:
        return _fallback_yaml_load(text)
