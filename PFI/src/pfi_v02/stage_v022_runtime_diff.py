from __future__ import annotations

import hashlib
import json
import csv
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Mapping

from pfi_v02.stage_v022_ledger_taxonomy import (
    build_stage5_consumption_taxonomy,
    build_stage5_ledger_event_type_table,
)
from pfi_v02.stage_v022_tags_views import build_stage6_default_tag_library, build_stage6_tag_rules


STAGE8_DEPENDENCY_HASH_KEYS = (
    "raw_data_hash",
    "normalized_transactions_hash",
    "ledger_events_hash",
    "interconnection_hash",
    "parameter_hash",
    "category_hash",
    "tag_hash",
    "fx_snapshot_hash",
)

_INPUT_TO_HASH_KEY = {
    "raw_data": "raw_data_hash",
    "normalized_transactions": "normalized_transactions_hash",
    "ledger_events": "ledger_events_hash",
    "interconnection": "interconnection_hash",
    "parameters": "parameter_hash",
    "categories": "category_hash",
    "tags": "tag_hash",
    "fx_snapshot": "fx_snapshot_hash",
}

STAGE8_ALIPAY_RAW_ROOT = "MetaDatabase/PFI/alipay_daily/raw"
STAGE8_ALIPAY_TRANSACTION_SOURCE = "MetaDatabase/PFI/alipay_daily/processed/alipay_transactions.csv"
STAGE8_FX_SNAPSHOT_SOURCE = "PFI/data/fx_snapshots/AUD_CNY/2026-06-28.json"
STAGE8_PARAMETER_SOURCE = "PFI/config/pfi_parameters.yaml"
STAGE8_LEDGER_STANDARD_SOURCE = "PFI/docs/pfi_v02/LEDGER_CLASSIFICATION_STANDARD.md"
STAGE8_INTERCONNECTION_EMPTY_STATE_ZH = "暂无真实 Interconnection 分组文件，使用真实空态，不生成模拟分组。"

STAGE8_P0_CORE_METRICS = (
    "净资产",
    "生活现金",
    "投资资产",
    "消费总流出",
    "生活消费",
    "投资收益",
    "现金流窗口",
    "待复核数量",
    "Interconnection 异常数量",
)

STAGE8_P1_ANALYSIS_METRICS = (
    "分类占比",
    "标签视图",
    "订阅",
    "夜间",
    "大额",
    "商户集中度",
    "投资风格",
    "交易频率",
    "费用拖累",
    "现金拖累",
)

STAGE8_P2_DISPLAY_METRICS = (
    "图表排序",
    "趋势图",
    "辅助说明",
    "tooltip",
    "参数中心展示",
)

STAGE8_LLM_TRIGGER_REASONS = (
    "业务语义变化",
    "公式逻辑变化",
    "分类冲突",
    "标签冲突",
    "跨板块不一致",
    "测试无法解释",
)

STAGE8_NO_LLM_SCENARIOS = (
    "无 diff",
    "只刷新缓存",
    "只重绘图表",
    "汇率快照未变",
    "参数未变",
    "普通本地重算",
)

_DEPENDENCY_GRAPH = {
    "raw_data_hash": {
        "P0": ("待复核数量",),
        "P1": ("分类占比", "标签视图"),
        "P2": ("趋势图", "辅助说明"),
        "not_impacted": ("图表排序", "tooltip", "参数中心展示"),
    },
    "normalized_transactions_hash": {
        "P0": ("净资产", "生活现金", "消费总流出", "生活消费", "现金流窗口", "待复核数量"),
        "P1": ("分类占比", "订阅", "夜间", "大额"),
        "P2": ("趋势图", "辅助说明"),
        "not_impacted": ("参数中心展示",),
    },
    "ledger_events_hash": {
        "P0": ("净资产", "生活现金", "投资资产", "消费总流出", "生活消费", "投资收益", "现金流窗口"),
        "P1": ("交易频率", "费用拖累", "现金拖累"),
        "P2": ("趋势图", "辅助说明"),
        "not_impacted": ("图表排序", "tooltip"),
    },
    "interconnection_hash": {
        "P0": ("净资产", "投资资产", "消费总流出", "生活消费", "现金流窗口", "Interconnection 异常数量"),
        "P1": ("分类占比", "标签视图"),
        "P2": ("趋势图", "辅助说明"),
        "not_impacted": ("图表排序", "tooltip", "参数中心展示"),
    },
    "parameter_hash": {
        "P0": ("现金流窗口", "待复核数量"),
        "P1": ("订阅", "夜间", "大额", "交易频率", "费用拖累", "现金拖累"),
        "P2": ("参数中心展示", "辅助说明"),
        "not_impacted": ("净资产", "生活现金", "投资资产"),
    },
    "category_hash": {
        "P0": ("待复核数量",),
        "P1": ("分类占比",),
        "P2": ("辅助说明", "tooltip"),
        "not_impacted": ("净资产", "投资收益", "现金流窗口", "生活现金", "投资资产"),
    },
    "tag_hash": {
        "P0": (),
        "P1": ("标签视图",),
        "P2": ("辅助说明", "tooltip"),
        "not_impacted": STAGE8_P0_CORE_METRICS,
    },
    "fx_snapshot_hash": {
        "P0": ("净资产", "投资资产", "投资收益", "现金流窗口"),
        "P1": ("费用拖累", "现金拖累"),
        "P2": ("趋势图", "辅助说明"),
        "not_impacted": ("分类占比", "标签视图", "订阅", "夜间", "大额"),
    },
}


def _json_default(value: object) -> str:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return str(value)


def stable_json_hash(payload: object) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=_json_default)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _resolve_stage8_roots(project_root: str | Path | None = None) -> tuple[Path, Path]:
    root = Path(project_root).expanduser().resolve() if project_root is not None else Path(__file__).resolve().parents[2]
    if root.name == "PFI":
        return root, root.parent
    if (root / "PFI").is_dir() and (root / "MetaDatabase").is_dir():
        return root / "PFI", root
    return root, root.parent


def _repo_relative(path: Path, repo_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path.resolve())


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_obj:
        for chunk in iter(lambda: file_obj.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _file_payload(path: Path, repo_root: Path, *, parse_json: bool = False) -> dict[str, object]:
    payload: dict[str, object] = {
        "path": _repo_relative(path, repo_root),
        "exists": path.exists(),
    }
    if not path.exists():
        payload["state_zh"] = "文件不存在，保持真实空态，不生成替代数据。"
        return payload

    payload.update(
        {
            "sha256": _sha256_file(path),
            "size_bytes": path.stat().st_size,
        }
    )
    if parse_json:
        payload["content"] = json.loads(path.read_text(encoding="utf-8"))
    return payload


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as file_obj:
        return [dict(row) for row in csv.DictReader(file_obj)]


def _stage8_money(value: object) -> str:
    return str(Decimal(str(value or "0")).copy_abs().quantize(Decimal("0.01")))


def _stage8_event_type(raw_event_type: str, amount: Decimal, description: str) -> str:
    normalized = raw_event_type.strip().upper()
    if normalized == "CASH" and amount < 0:
        return "ordinary_consumption"
    if normalized == "CASH" and amount >= 0:
        return "cash_inflow"
    if normalized == "FUND" and amount < 0:
        return "fund_subscription"
    if normalized == "FUND" and amount >= 0:
        return "investment_return"
    if normalized == "BUY_ASSET" and amount < 0:
        return "bullion_purchase" if "黄金" in description else "investment_buy"
    if normalized == "REFUND":
        return "refund"
    if normalized == "TRANSFER":
        return "internal_transfer"
    return "unclassified_real_event"


def _ledger_events_from_transactions(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    events: list[dict[str, object]] = []
    for index, row in enumerate(rows, 1):
        amount = Decimal(str(row.get("amount") or "0"))
        description = str(row.get("description") or "").strip()
        transaction_id = str(row.get("transaction_id") or "").strip()
        raw_id = str(row.get("raw_id") or "").strip()
        if not transaction_id:
            continue
        events.append(
            {
                "ledger_event_id": f"ledger:{transaction_id}",
                "transaction_id": transaction_id,
                "source_record_id": raw_id or transaction_id,
                "source_id": str(row.get("source_id") or "alipay_daily").strip(),
                "account_id": str(row.get("account_id") or "acct_alipay").strip(),
                "event_type": _stage8_event_type(str(row.get("event_type") or ""), amount, description),
                "amount_cny": _stage8_money(amount),
                "signed_amount_cny": str(amount.quantize(Decimal("0.01"))),
                "direction": "inflow" if amount >= 0 else "outflow",
                "currency": str(row.get("currency") or "CNY").strip(),
                "occurred_at": str(row.get("occurred_at") or "").strip(),
                "description_hash": hashlib.sha256(description.encode("utf-8")).hexdigest(),
                "review_state": str(row.get("review_state") or "").strip(),
                "row_number": index,
                "real_data_source": STAGE8_ALIPAY_TRANSACTION_SOURCE,
            }
        )
    return events


def load_stage8_runtime_diff_inputs_from_canonical_sources(
    project_root: str | Path | None = None,
) -> dict[str, object]:
    """Load Stage 8 diff dependencies from canonical real local sources only."""
    pfi_root, repo_root = _resolve_stage8_roots(project_root)
    raw_root = repo_root / STAGE8_ALIPAY_RAW_ROOT
    transactions_path = repo_root / STAGE8_ALIPAY_TRANSACTION_SOURCE
    parameter_path = repo_root / STAGE8_PARAMETER_SOURCE
    ledger_standard_path = repo_root / STAGE8_LEDGER_STANDARD_SOURCE
    fx_snapshot_path = repo_root / STAGE8_FX_SNAPSHOT_SOURCE

    raw_files = [_file_payload(path, repo_root) for path in sorted(raw_root.glob("*.csv"))]
    normalized_transactions = _read_csv_rows(transactions_path)
    ledger_events = _ledger_events_from_transactions(normalized_transactions)
    parameters = _file_payload(parameter_path, repo_root, parse_json=True)
    categories = {
        "schema": "PFIV022Stage8CategoryInputsV1",
        "standard_document": _file_payload(ledger_standard_path, repo_root),
        "ledger_event_type_table": build_stage5_ledger_event_type_table(),
        "consumption_taxonomy": build_stage5_consumption_taxonomy(),
    }
    tags = {
        "schema": "PFIV022Stage8TagInputsV1",
        "default_tag_library": build_stage6_default_tag_library(),
        "tag_rules": build_stage6_tag_rules(),
    }
    fx_snapshot = _file_payload(fx_snapshot_path, repo_root, parse_json=True)

    inputs = {
        "raw_data": raw_files,
        "normalized_transactions": normalized_transactions,
        "ledger_events": ledger_events,
        "interconnection": [],
        "parameters": parameters,
        "categories": categories,
        "tags": tags,
        "fx_snapshot": fx_snapshot,
    }
    return {
        "schema": "PFIV022Stage8CanonicalRuntimeDiffInputsV1",
        "inputs": inputs,
        "source_summary": {
            "pfi_root": _repo_relative(pfi_root, repo_root),
            "raw_data_root": STAGE8_ALIPAY_RAW_ROOT,
            "raw_file_count": len(raw_files),
            "normalized_transactions_path": STAGE8_ALIPAY_TRANSACTION_SOURCE,
            "normalized_transaction_count": len(normalized_transactions),
            "ledger_event_count": len(ledger_events),
            "interconnection_count": 0,
            "interconnection_state_zh": STAGE8_INTERCONNECTION_EMPTY_STATE_ZH,
            "parameter_source": STAGE8_PARAMETER_SOURCE,
            "category_source": STAGE8_LEDGER_STANDARD_SOURCE,
            "tag_source": "PFI/src/pfi_v02/stage_v022_tags_views.py",
            "fx_snapshot_source": STAGE8_FX_SNAPSHOT_SOURCE,
            "network_allowed": False,
            "data_boundary_zh": "Stage 8 只读取 MetaDatabase 与 PFI 本地配置/合同文件；缺失来源保持中文真实空态，不生成测试、样例或模拟数据。",
        },
    }


def build_dependency_hash_snapshot(inputs: Mapping[str, object], *, run_id: str) -> dict[str, object]:
    missing = tuple(key for key in _INPUT_TO_HASH_KEY if key not in inputs)
    if missing:
        raise ValueError(f"Stage 8 依赖输入缺失，无法判断数据是否变化: {', '.join(missing)}")

    dependency_hashes = {
        hash_key: stable_json_hash(inputs[input_key])
        for input_key, hash_key in _INPUT_TO_HASH_KEY.items()
    }
    ordered_hashes = {key: dependency_hashes[key] for key in STAGE8_DEPENDENCY_HASH_KEYS}
    return {
        "schema": "PFIV022RuntimeDiffSnapshotV1",
        "run_id": run_id,
        "dependency_hashes": ordered_hashes,
        "run_hash": stable_json_hash(ordered_hashes),
        "hash_inputs_zh": "原始数据、标准化交易、账本事件、interconnection、参数、分类、标签、汇率快照 hash",
        "network_allowed": False,
    }


def compare_dependency_snapshots(previous: Mapping[str, object], current: Mapping[str, object]) -> dict[str, object]:
    previous_hashes = previous.get("dependency_hashes")
    current_hashes = current.get("dependency_hashes")
    if not isinstance(previous_hashes, Mapping) or not isinstance(current_hashes, Mapping):
        raise ValueError("Stage 8 diff 需要两个包含 dependency_hashes 的 run snapshot。")

    changed = tuple(
        key
        for key in STAGE8_DEPENDENCY_HASH_KEYS
        if previous_hashes.get(key) != current_hashes.get(key)
    )
    unchanged = tuple(key for key in STAGE8_DEPENDENCY_HASH_KEYS if key not in changed)
    return {
        "schema": "PFIV022RuntimeDiffReportV1",
        "previous_run_id": previous.get("run_id"),
        "current_run_id": current.get("run_id"),
        "has_diff": bool(changed),
        "changed_dependency_keys": changed,
        "unchanged_dependency_keys": unchanged,
        "run_hash_changed": previous.get("run_hash") != current.get("run_hash"),
        "network_allowed": False,
    }


def _dedupe(values: list[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return tuple(result)


def build_impacted_metrics_report(diff: Mapping[str, object], *, trigger_reason: str | None = None) -> dict[str, object]:
    changed_keys = tuple(diff.get("changed_dependency_keys", ()) or ())
    if not diff.get("has_diff"):
        return {
            "schema": "PFIV022ImpactedMetricsReportV1",
            "has_diff": False,
            "changed_dependency_keys": (),
            "recompute_scope": "none",
            "full_recompute": False,
            "direct_impacted_metrics": {"P0": (), "P1": (), "P2": ()},
            "indirect_impacted_metrics": (),
            "not_impacted_metrics": STAGE8_P0_CORE_METRICS + STAGE8_P1_ANALYSIS_METRICS + STAGE8_P2_DISPLAY_METRICS,
            "network_allowed": False,
            "external_analysis_required": False,
            "llm_review_required": False,
            "codex_ticket_required": False,
            "policy_zh": "无 diff 不联网、不生成 Codex ticket、不触发 LLM。",
        }

    impacted = {"P0": [], "P1": [], "P2": []}
    not_impacted: list[str] = []
    for key in changed_keys:
        graph_item = _DEPENDENCY_GRAPH.get(key, {})
        for tier in ("P0", "P1", "P2"):
            impacted[tier].extend(graph_item.get(tier, ()))
        not_impacted.extend(graph_item.get("not_impacted", ()))

    direct_impacted = {
        "P0": _dedupe(impacted["P0"]),
        "P1": _dedupe(impacted["P1"]),
        "P2": _dedupe(impacted["P2"]),
    }
    llm_required = should_trigger_llm_review(trigger_reason or "")
    return {
        "schema": "PFIV022ImpactedMetricsReportV1",
        "has_diff": True,
        "changed_dependency_keys": changed_keys,
        "recompute_scope": "changed_dependency_only",
        "full_recompute": False,
        "direct_impacted_metrics": direct_impacted,
        "indirect_impacted_metrics": _dedupe(direct_impacted["P1"] + direct_impacted["P2"]),
        "not_impacted_metrics": _dedupe(not_impacted),
        "network_allowed": False,
        "external_analysis_required": False,
        "llm_review_required": llm_required,
        "codex_ticket_required": llm_required,
        "trigger_reason": trigger_reason or "普通本地重算",
        "policy_zh": "有 diff 时只重算受影响指标；普通 diff 只生成本地报告，重要冲突才生成 Codex Review Ticket。",
    }


def build_llm_trigger_policy() -> dict[str, object]:
    return {
        "schema": "PFIV022Stage8LLMTriggerPolicyV1",
        "trigger_mode": "local_ticket_only_no_network",
        "allowed_trigger_reasons": STAGE8_LLM_TRIGGER_REASONS,
        "no_llm_scenarios": STAGE8_NO_LLM_SCENARIOS,
        "policy_zh": "只有业务语义、公式逻辑、分类冲突、标签冲突、跨板块不一致、测试无法解释时触发本地 Codex Review Ticket。",
    }


def should_trigger_llm_review(reason: str, *, policy: Mapping[str, object] | None = None) -> bool:
    active_policy = policy or build_llm_trigger_policy()
    allowed = tuple(active_policy.get("allowed_trigger_reasons", STAGE8_LLM_TRIGGER_REASONS))
    blocked = tuple(active_policy.get("no_llm_scenarios", STAGE8_NO_LLM_SCENARIOS))
    return reason in allowed and reason not in blocked


def _related_files_for_diff(changed_keys: tuple[str, ...]) -> tuple[str, ...]:
    mapping = {
        "raw_data_hash": "PFI/MetaDatabase/",
        "normalized_transactions_hash": "PFI/src/pfi_v02/",
        "ledger_events_hash": "PFI/src/pfi_v02/stage_v022_ledger_taxonomy.py",
        "interconnection_hash": "PFI/src/pfi_v02/stage_v022_interconnection.py",
        "parameter_hash": "PFI/config/pfi_parameters.yaml",
        "category_hash": "PFI/docs/pfi_v02/LEDGER_CLASSIFICATION_STANDARD.md",
        "tag_hash": "PFI/src/pfi_v02/stage_v022_tags_views.py",
        "fx_snapshot_hash": "PFI/data/fx_snapshots/",
    }
    return tuple(f"{mapping.get(key, 'PFI/')}：与 {key} 对应的本地依赖文件或目录" for key in changed_keys)


def build_codex_review_ticket(report: Mapping[str, object], *, trigger_reason: str) -> dict[str, object]:
    changed_keys = tuple(report.get("changed_dependency_keys", ()) or ())
    impacted = report.get("direct_impacted_metrics", {})
    return {
        "schema": "PFIV022CodexReviewTicketTemplateV1",
        "触发原因": f"{trigger_reason}：本地 diff report 无法用普通依赖重算解释，需要复核业务口径。",
        "影响指标": {
            "直接受影响指标": impacted,
            "间接受影响指标": report.get("indirect_impacted_metrics", ()),
            "不应受影响指标": report.get("not_impacted_metrics", ()),
        },
        "涉及文件": _related_files_for_diff(changed_keys),
        "期望检查": (
            "检查变更是否符合中文业务定义。",
            "检查 P0/P1/P2 指标是否被错误混用。",
            "检查同一事实层在首页、消费、投资、现金流、报告中是否一致。",
            "检查测试失败是否来自业务口径冲突，而不是普通代码错误。",
        ),
        "禁止事项": (
            "不得联网。",
            "不得调用外部 LLM。",
            "不得全仓无差别扫描。",
            "不得扩大到 Stage 9-13 功能。",
            "不得修改真实交易、支付、券商下单或任何实盘执行路径。",
        ),
        "中文业务解释": "该票据只用于本地 Codex 复核，帮助确认 diff 是否真的影响用户可见金融指标，避免标签、文案或图表变化误报为核心金额变化。",
    }


def build_stage8_contract_payload() -> dict[str, object]:
    return {
        "schema": "PFIV022RuntimeDiffStage8PayloadV1",
        "dependency_hash_keys": STAGE8_DEPENDENCY_HASH_KEYS,
        "p0_core_metrics": STAGE8_P0_CORE_METRICS,
        "p1_analysis_metrics": STAGE8_P1_ANALYSIS_METRICS,
        "p2_display_metrics": STAGE8_P2_DISPLAY_METRICS,
        "dependency_graph": _DEPENDENCY_GRAPH,
        "llm_trigger_policy": build_llm_trigger_policy(),
        "review_queue_template": "PFI/review_queue/CODEX_REVIEW_TICKET_TEMPLATE.md",
    }
