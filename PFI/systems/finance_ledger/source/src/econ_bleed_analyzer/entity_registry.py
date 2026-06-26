from __future__ import annotations

import csv
import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from .classifier import ClassifiedTransaction


SCHEMA_VERSION = "entity_registry.v1"


def build_entity_layer(
    rows: list[ClassifiedTransaction],
    *,
    tag_library_rows: list[dict[str, Any]] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    generated_at = datetime.now().isoformat(timespec="seconds")
    registry = _build_registry(rows, tag_library_rows or [], generated_at)
    alias_map = _build_alias_map(registry, generated_at)
    summary = summarize_entity_registry(registry, alias_map)
    return {"entity_registry": registry, "alias_map": alias_map, "entity_registry_summary": summary}


def summarize_entity_registry(registry_rows: list[dict[str, Any]], alias_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    alias_count_by_type = Counter(str(row.get("entity_type", "")) for row in alias_rows)
    conflicts_by_type = Counter(
        str(row.get("entity_type", "")) for row in alias_rows if str(row.get("collision_status", "")) == "collision"
    )
    output: list[dict[str, Any]] = []
    for entity_type in sorted({str(row.get("entity_type", "")) for row in registry_rows}):
        subset = [row for row in registry_rows if str(row.get("entity_type", "")) == entity_type]
        review_count = sum(1 for row in subset if str(row.get("review_required", "")) == "true")
        output.append(
            {
                "entity_type": entity_type,
                "entity_count": len(subset),
                "alias_count": alias_count_by_type.get(entity_type, 0),
                "alias_conflict_count": conflicts_by_type.get(entity_type, 0),
                "review_required_count": review_count,
                "evidence_classification": "FACT" if entity_type in {"counterparty", "source_platform", "payment_method", "source_file"} else "INFERENCE",
                "decision_grade": "Watch" if review_count or conflicts_by_type.get(entity_type, 0) else "Actionable",
                "schema_version": SCHEMA_VERSION,
            }
        )
    return output


def entity_registry_report_markdown(
    registry_rows: list[dict[str, Any]],
    alias_rows: list[dict[str, Any]],
    summary_rows: list[dict[str, Any]],
) -> str:
    run_id = hashlib.sha256(f"{len(registry_rows)}-{len(alias_rows)}-{datetime.now().isoformat()}".encode("utf-8")).hexdigest()[:16]
    generated_at = datetime.now().isoformat(timespec="seconds")
    review_entities = [row for row in registry_rows if str(row.get("review_required", "")) == "true"]
    conflicts = [row for row in alias_rows if str(row.get("collision_status", "")) == "collision"]
    top_counterparties = sorted(
        [row for row in registry_rows if row.get("entity_type") == "counterparty"],
        key=lambda item: _float(item.get("observed_expense_amount")),
        reverse=True,
    )[:25]
    lines = [
        "# Entity Registry / Alias Map 实体注册与别名映射报告",
        "",
        f"- run_id：`{run_id}`",
        f"- generated_at：`{generated_at}`",
        f"- schema_version：`{SCHEMA_VERSION}`",
        "",
        "口径：本报告只读取已清洗交易、标签库和本地文件状态，生成稳定 entity_id 与 alias_id；不改变生产金额、分类、复核确认或报告总支出。",
        "",
        "## 假设与边界",
        "",
        "- 交易对方、来源平台、支付方式和来源文件来自账单解析字段，标记为 `FACT`。",
        "- 主类、子类、机制和风险标签来自本地分类规则，标记为 `INFERENCE`。",
        "- 别名映射基于大小写、全半角、空白和常见符号归一化；复杂同名实体仍需人工复核。",
        "- 当前不合并银行账户、券商账户或真实身份信息；后续接入时必须先补权限和脱敏规则。",
        "",
        "## 实体摘要",
        "",
        "| 实体类型 | 实体数 | 别名数 | 别名冲突 | 需复核 | 证据等级 | 决策等级 |",
        "|---|---:|---:|---:|---:|---|---|",
    ]
    for row in summary_rows:
        lines.append(
            f"| {row.get('entity_type', '')} | {row.get('entity_count', 0)} | {row.get('alias_count', 0)} | "
            f"{row.get('alias_conflict_count', 0)} | {row.get('review_required_count', 0)} | "
            f"{row.get('evidence_classification', '')} | {row.get('decision_grade', '')} |"
        )
    lines.extend(
        [
            "",
            "## 需复核实体",
            "",
            "| entity_id | 类型 | 名称 | 状态 | 原因 | 决策等级 |",
            "|---|---|---|---|---|---|",
        ]
    )
    for row in sorted(review_entities, key=lambda item: (_entity_type_rank(item.get("entity_type")), item.get("canonical_name", "")))[:40]:
        lines.append(
            f"| {row.get('entity_id', '')} | {row.get('entity_type', '')} | {_safe_text(row.get('canonical_name', ''), 28)} | "
            f"{row.get('entity_status', '')} | {_safe_text(row.get('review_reason', ''), 42)} | {row.get('decision_grade', '')} |"
        )
    if not review_entities:
        lines.append("| 无 |  |  | ACTIVE | 当前未发现需要人工复核的实体。 | Actionable |")
    lines.extend(
        [
            "",
            "## 高频交易对方实体",
            "",
            "| entity_id | 名称 | 交易数 | 观察支出 | 待复核数 | 主平台 | 主类别 |",
            "|---|---|---:|---:|---:|---|---|",
        ]
    )
    for row in top_counterparties:
        lines.append(
            f"| {row.get('entity_id', '')} | {_safe_text(row.get('canonical_name', ''), 28)} | {row.get('transaction_count', 0)} | "
            f"¥{_float(row.get('observed_expense_amount')):,.2f} | {row.get('pending_review_count', 0)} | "
            f"{_safe_text(row.get('primary_source_platform', ''), 18)} | {_safe_text(row.get('primary_category', ''), 24)} |"
        )
    lines.extend(
        [
            "",
            "## 别名冲突",
            "",
            "| alias_normalized | entity_type | 冲突实体数 | 处理方式 |",
            "|---|---|---:|---|",
        ]
    )
    conflict_counter: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in conflicts:
        conflict_counter[(str(row.get("alias_normalized", "")), str(row.get("entity_type", "")))].add(str(row.get("canonical_entity_id", "")))
    for (alias, entity_type), entity_ids in sorted(conflict_counter.items())[:30]:
        lines.append(f"| {_safe_text(alias, 32)} | {entity_type} | {len(entity_ids)} | 保持 Watch，人工确认后再合并。 |")
    if not conflict_counter:
        lines.append("| 无 |  | 0 | 当前别名归一化未发现冲突。 |")
    lines.extend(
        [
            "",
            "## 机器可读产物",
            "",
            "- CSV：`audit/entity_registry.csv`、`audit/alias_map.csv`",
            "- JSON：`audit/entity_registry.json`、`audit/alias_map.json`",
            "- SQLite 表：`entity_registry`、`alias_map`、`entity_registry_summary`",
            "- SQLite 视图：`v_entity_registry`、`v_alias_map`、`v_entity_registry_summary`、`v_entity_alias_conflicts`",
            "",
            "## 验证方式",
            "",
            "```bash",
            "python3 scripts/validate_outputs.py --output outputs/finance_ledger_20220605_20260603 --db data/finance_ledger/finance_ledger.sqlite --require-ledger",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def write_entity_layer_outputs(layer: dict[str, list[dict[str, Any]]], output_dir: str | Path) -> dict[str, Path]:
    output = Path(output_dir)
    audit_dir = output / "audit"
    reports_dir = output / "reports"
    audit_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    registry_rows = layer["entity_registry"]
    alias_rows = layer["alias_map"]
    summary_rows = layer["entity_registry_summary"]
    paths = {
        "entity_registry_csv": audit_dir / "entity_registry.csv",
        "entity_registry_json": audit_dir / "entity_registry.json",
        "alias_map_csv": audit_dir / "alias_map.csv",
        "alias_map_json": audit_dir / "alias_map.json",
        "entity_registry_summary_csv": audit_dir / "entity_registry_summary.csv",
        "entity_registry_summary_json": audit_dir / "entity_registry_summary.json",
        "entity_registry_report_md": reports_dir / "entity_registry_report.md",
    }
    _write_csv(paths["entity_registry_csv"], registry_rows)
    _write_json(paths["entity_registry_json"], registry_rows)
    _write_csv(paths["alias_map_csv"], alias_rows)
    _write_json(paths["alias_map_json"], alias_rows)
    _write_csv(paths["entity_registry_summary_csv"], summary_rows)
    _write_json(paths["entity_registry_summary_json"], summary_rows)
    markdown = entity_registry_report_markdown(registry_rows, alias_rows, summary_rows)
    paths["entity_registry_report_md"].write_text(markdown, encoding="utf-8")
    return paths


def _build_registry(rows: list[ClassifiedTransaction], tag_library_rows: list[dict[str, Any]], generated_at: str) -> list[dict[str, Any]]:
    builders: dict[tuple[str, str], dict[str, Any]] = {}

    def bucket(entity_type: str, canonical_key: str, canonical_name: str, evidence: str, decision: str = "Actionable") -> dict[str, Any]:
        key = (entity_type, canonical_key or "_empty")
        return builders.setdefault(
            key,
            {
                "entity_id": _entity_id(entity_type, canonical_key or "_empty"),
                "entity_type": entity_type,
                "canonical_key": canonical_key or "_empty",
                "canonical_name": canonical_name or "未填写",
                "display_name": canonical_name or "未填写",
                "entity_status": "ACTIVE",
                "review_required": "false",
                "review_reason": "",
                "evidence_classification": evidence,
                "decision_grade": decision,
                "alias_values": set(),
                "source_platforms": Counter(),
                "source_files": Counter(),
                "categories": Counter(),
                "risk_tags": Counter(),
                "transaction_count": 0,
                "expense_count": 0,
                "income_count": 0,
                "pending_review_count": 0,
                "observed_expense_amount": 0.0,
                "observed_income_amount": 0.0,
                "first_seen": "",
                "last_seen": "",
                "generated_at": generated_at,
                "schema_version": SCHEMA_VERSION,
            },
        )

    for row in rows:
        row_date = str(getattr(row, "date", "") or "")
        source_platform = str(getattr(row, "source_platform", "") or "unknown")
        source_file = str(getattr(row, "source_file", "") or "unknown")
        main_category = str(getattr(row, "main_category", "") or "未分类")
        sub_category = str(getattr(row, "sub_category", "") or "未分类")
        risk_tags = _split_tags(getattr(row, "risk_tags", ""))
        direction = str(getattr(row, "direction", ""))
        amount = _float(getattr(row, "amount", 0.0))
        row_common = [
            ("counterparty", _normalize_alias(getattr(row, "counterparty", "")), str(getattr(row, "counterparty", "") or "未填写"), "FACT"),
            ("source_platform", source_platform.casefold(), source_platform, "FACT"),
            ("payment_method", _normalize_alias(getattr(row, "payment_method", "")), str(getattr(row, "payment_method", "") or "未填写"), "FACT"),
            ("source_file", _normalize_alias(source_file), Path(source_file).name or source_file, "FACT"),
            ("category", _normalize_alias(f"{main_category}/{sub_category}"), f"{main_category}/{sub_category}", "INFERENCE"),
            ("mechanism", _normalize_alias(getattr(row, "mechanism", "")), str(getattr(row, "mechanism", "") or "未识别"), "INFERENCE"),
        ]
        for entity_type, key, name, evidence in row_common:
            item = bucket(entity_type, key, name, evidence, "Observe" if evidence == "INFERENCE" else "Actionable")
            _apply_row_metrics(item, row, row_date, source_platform, source_file, main_category, sub_category, risk_tags, direction, amount)
            item["alias_values"].add(name)
            if entity_type == "source_file" and source_file and not Path(source_file).exists():
                _mark_review(item, "来源文件当前路径不存在，需要通过 source_archives 或 HANDOFF 复核。")
        for tag in risk_tags:
            item = bucket("risk_tag", _normalize_alias(tag), tag, "INFERENCE", "Observe")
            _apply_row_metrics(item, row, row_date, source_platform, source_file, main_category, sub_category, risk_tags, direction, amount)
            item["alias_values"].add(tag)

    for tag in tag_library_rows:
        name = str(tag.get("tag_name", "") or "")
        if not name:
            continue
        item = bucket("risk_tag", _normalize_alias(name), name, "INFERENCE", "Observe")
        item["alias_values"].add(name)
        item["review_reason"] = item.get("review_reason") or "来自标签库；如标签定义变化，应通过 tag_library.html 回灌。"

    output = []
    for item in builders.values():
        if item["pending_review_count"] and item["entity_type"] in {"counterparty", "source_platform", "payment_method"}:
            _mark_review(item, "存在待复核交易，确认前下游应降级为观察。")
        alias_values = sorted(str(value) for value in item.pop("alias_values") if str(value))
        source_platforms = item.pop("source_platforms")
        source_files = item.pop("source_files")
        categories = item.pop("categories")
        risk_tags_counter = item.pop("risk_tags")
        item.update(
            {
                "alias_values": "|".join(alias_values),
                "alias_count": len(alias_values),
                "source_platforms": "|".join(source_platforms.keys()),
                "source_file_count": len(source_files),
                "primary_source_platform": source_platforms.most_common(1)[0][0] if source_platforms else "",
                "primary_category": categories.most_common(1)[0][0] if categories else "",
                "primary_risk_tag": risk_tags_counter.most_common(1)[0][0] if risk_tags_counter else "",
                "observed_expense_amount": round(float(item["observed_expense_amount"]), 2),
                "observed_income_amount": round(float(item["observed_income_amount"]), 2),
            }
        )
        output.append(item)
    return sorted(output, key=lambda row: (str(row["entity_type"]), str(row["canonical_name"])))


def _build_alias_map(registry_rows: list[dict[str, Any]], generated_at: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for entity in registry_rows:
        aliases = [alias for alias in str(entity.get("alias_values", "")).split("|") if alias]
        aliases.append(str(entity.get("canonical_name", "")))
        seen: set[str] = set()
        for alias in aliases:
            normalized = _normalize_alias(alias)
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            rows.append(
                {
                    "alias_id": _entity_id("alias", f"{entity.get('entity_type')}:{normalized}:{entity.get('entity_id')}"),
                    "entity_type": entity.get("entity_type", ""),
                    "alias_value": alias,
                    "alias_normalized": normalized,
                    "canonical_entity_id": entity.get("entity_id", ""),
                    "canonical_name": entity.get("canonical_name", ""),
                    "match_rule": "unicode_nfkc_casefold_strip_symbol",
                    "evidence_classification": "INFERENCE",
                    "decision_grade": "Actionable",
                    "collision_status": "unique",
                    "generated_at": generated_at,
                    "schema_version": SCHEMA_VERSION,
                }
            )
    conflicts: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in rows:
        conflicts[(str(row["entity_type"]), str(row["alias_normalized"]))].add(str(row["canonical_entity_id"]))
    for row in rows:
        count = len(conflicts[(str(row["entity_type"]), str(row["alias_normalized"]))])
        if count > 1:
            row["collision_status"] = "collision"
            row["decision_grade"] = "Watch"
        row["collision_entity_count"] = count
    return sorted(rows, key=lambda row: (str(row["entity_type"]), str(row["alias_normalized"]), str(row["canonical_entity_id"])))


def _apply_row_metrics(
    item: dict[str, Any],
    row: ClassifiedTransaction,
    row_date: str,
    source_platform: str,
    source_file: str,
    main_category: str,
    sub_category: str,
    risk_tags: list[str],
    direction: str,
    amount: float,
) -> None:
    item["transaction_count"] += 1
    item["source_platforms"][source_platform] += 1
    item["source_files"][source_file] += 1
    item["categories"][f"{main_category}/{sub_category}"] += 1
    for tag in risk_tags:
        item["risk_tags"][tag] += 1
    if direction == "支出":
        item["expense_count"] += 1
        item["observed_expense_amount"] += amount
    elif direction == "收入":
        item["income_count"] += 1
        item["observed_income_amount"] += amount
    if getattr(row, "needs_review", False):
        item["pending_review_count"] += 1
    if row_date:
        if not item["first_seen"] or row_date < item["first_seen"]:
            item["first_seen"] = row_date
        if not item["last_seen"] or row_date > item["last_seen"]:
            item["last_seen"] = row_date


def _mark_review(item: dict[str, Any], reason: str) -> None:
    item["entity_status"] = "NEEDS_REVIEW"
    item["review_required"] = "true"
    item["decision_grade"] = "Watch"
    if reason and reason not in str(item.get("review_reason", "")):
        item["review_reason"] = f"{item.get('review_reason', '')}; {reason}".strip("; ")


def _split_tags(value: Any) -> list[str]:
    return [item.strip() for item in str(value or "").split("|") if item.strip()]


def _normalize_alias(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).casefold().strip()
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"[|,，。.;；:：/\\()（）\\[\\]【】{}<>《》\"'`~!！?？_-]+", "", text)
    return text or "_empty"


def _entity_id(entity_type: str, key: str) -> str:
    digest = hashlib.sha1(f"{entity_type}:{key}".encode("utf-8")).hexdigest()[:12]
    return f"{entity_type}_{digest}"


def _write_json(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(json.dumps(rows, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    columns: list[str] = []
    for row in rows:
        for key in row:
            if key not in columns:
                columns.append(key)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _float(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _safe_text(value: Any, limit: int) -> str:
    return str(value or "").replace("|", "/").replace("\n", " ")[:limit]


def _entity_type_rank(value: Any) -> int:
    order = {
        "counterparty": 0,
        "source_platform": 1,
        "payment_method": 2,
        "source_file": 3,
        "category": 4,
        "risk_tag": 5,
        "mechanism": 6,
    }
    return order.get(str(value), 99)
