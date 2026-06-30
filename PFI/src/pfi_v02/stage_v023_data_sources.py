from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from pfi_v02.stage_v023_data_state import METRIC_DATA_STATUSES


VERSION = "v0.2.3"
STAGE = "Stage 8"
PHASE_ID = "V023-S8-P8.1"
PHASE_NAME = "数据源模型"
PHASE82_ID = "V023-S8-P8.2"
PHASE82_NAME = "检查板 UI"


@dataclass(frozen=True)
class Stage8Phase81Contract:
    version: str
    stage: str
    phase_id: str
    phase_name: str
    current_phase_only: bool
    max_one_phase_per_run: bool
    task_ids: tuple[str, ...]
    allowed_files: tuple[str, ...]
    changed_in_this_phase: tuple[str, ...]
    validation_commands: tuple[str, ...]
    evidence_files: tuple[str, ...]
    explicitly_not_done: tuple[str, ...]


@dataclass(frozen=True)
class Stage8Phase82Contract:
    version: str
    stage: str
    phase_id: str
    phase_name: str
    current_phase_only: bool
    max_one_phase_per_run: bool
    task_ids: tuple[str, ...]
    allowed_files: tuple[str, ...]
    changed_in_this_phase: tuple[str, ...]
    validation_commands: tuple[str, ...]
    evidence_files: tuple[str, ...]
    explicitly_not_done: tuple[str, ...]


def build_stage8_phase81_contract() -> dict[str, Any]:
    contract = Stage8Phase81Contract(
        version=VERSION,
        stage=STAGE,
        phase_id=PHASE_ID,
        phase_name=PHASE_NAME,
        current_phase_only=True,
        max_one_phase_per_run=True,
        task_ids=("T8.1.1", "T8.1.2", "T8.1.3", "T8.1.4"),
        allowed_files=(
            "PFI/src/pfi_v02/stage_v023_data_sources.py",
            "PFI/web/app/pages/upload.js",
            "PFI/web/app/components/dataGate*.js",
            "PFI/tests/test_v023_stage8_data_source_gate.py",
            "PFI/docs/pfi_v023/STAGE8_DATA_SOURCE_GATE.md",
            "PFI/reports/pfi_v023/stage_8/*",
        ),
        changed_in_this_phase=(
            "PFI/src/pfi_v02/stage_v023_data_sources.py",
            "PFI/web/app/pages/upload.js",
            "PFI/tests/test_v023_stage8_data_source_gate.py",
            "PFI/docs/pfi_v023/STAGE8_DATA_SOURCE_GATE.md",
            "PFI/reports/pfi_v023/stage_8/phase_8_1/*",
        ),
        validation_commands=(
            "node --check PFI/web/app/pages/upload.js",
            "python3 -m pytest PFI/tests/test_v023_stage8_data_source_gate.py -q",
            "python3 -m pytest PFI/tests/test_v023_*.py -q",
        ),
        evidence_files=(
            "PFI/docs/pfi_v023/STAGE8_DATA_SOURCE_GATE.md",
            "PFI/reports/pfi_v023/stage_8/phase_8_1/evidence.json",
            "PFI/reports/pfi_v023/stage_8/phase_8_1/data_source_gate.json",
            "PFI/reports/pfi_v023/stage_8/phase_8_1/data_source_gate_page_model.json",
            "PFI/reports/pfi_v023/stage_8/phase_8_1/error_reason_catalog.json",
            "PFI/reports/pfi_v023/stage_8/phase_8_1/no_source_term_scan.json",
            "PFI/reports/pfi_v023/stage_8/phase_8_1/screenshots/data_source_gate.png",
            "PFI/reports/pfi_v023/stage_8/phase_8_1/terminal.log",
            "PFI/reports/pfi_v023/stage_8/phase_8_1/changed_files.txt",
        ),
        explicitly_not_done=(
            "Phase 8.2 检查板 UI",
            "Phase 8.3 禁止假数据回退",
            "Stage 8 whole-stage review",
            "GitHub main upload for intermediate phase",
        ),
    )
    payload = asdict(contract)
    for key in ("task_ids", "allowed_files", "changed_in_this_phase", "validation_commands", "evidence_files", "explicitly_not_done"):
        payload[key] = list(payload[key])
    return payload


def build_stage8_phase82_contract() -> dict[str, Any]:
    contract = Stage8Phase82Contract(
        version=VERSION,
        stage=STAGE,
        phase_id=PHASE82_ID,
        phase_name=PHASE82_NAME,
        current_phase_only=True,
        max_one_phase_per_run=True,
        task_ids=("T8.2.1", "T8.2.2", "T8.2.3", "T8.2.4"),
        allowed_files=(
            "PFI/src/pfi_v02/stage_v023_data_sources.py",
            "PFI/web/app/pages/upload.js",
            "PFI/web/app/components/dataGate*.js",
            "PFI/tests/test_v023_stage8_data_source_gate.py",
            "PFI/docs/pfi_v023/STAGE8_DATA_SOURCE_GATE.md",
            "PFI/reports/pfi_v023/stage_8/*",
        ),
        changed_in_this_phase=(
            "PFI/src/pfi_v02/stage_v023_data_sources.py",
            "PFI/web/app/pages/upload.js",
            "PFI/tests/test_v023_stage8_data_source_gate.py",
            "PFI/docs/pfi_v023/STAGE8_DATA_SOURCE_GATE.md",
            "PFI/reports/pfi_v023/stage_8/phase_8_2/*",
        ),
        validation_commands=(
            "node --check PFI/web/app/pages/upload.js",
            "python3 -m pytest PFI/tests/test_v023_stage8_data_source_gate.py -q",
            "python3 -m pytest PFI/tests/test_v023_*.py -q",
        ),
        evidence_files=(
            "PFI/docs/pfi_v023/STAGE8_DATA_SOURCE_GATE.md",
            "PFI/reports/pfi_v023/stage_8/phase_8_2/evidence.json",
            "PFI/reports/pfi_v023/stage_8/phase_8_2/dashboard_ui.json",
            "PFI/reports/pfi_v023/stage_8/phase_8_2/dashboard_page_model.json",
            "PFI/reports/pfi_v023/stage_8/phase_8_2/no_source_term_scan.json",
            "PFI/reports/pfi_v023/stage_8/phase_8_2/screenshots/data_source_dashboard.png",
            "PFI/reports/pfi_v023/stage_8/phase_8_2/terminal.log",
            "PFI/reports/pfi_v023/stage_8/phase_8_2/changed_files.txt",
        ),
        explicitly_not_done=(
            "Phase 8.3 禁止假数据回退",
            "Stage 8 whole-stage review",
            "GitHub main upload for intermediate phase",
        ),
    )
    payload = asdict(contract)
    for key in ("task_ids", "allowed_files", "changed_in_this_phase", "validation_commands", "evidence_files", "explicitly_not_done"):
        payload[key] = list(payload[key])
    return payload


def build_stage8_error_reason_catalog() -> dict[str, Any]:
    reason_map = {
        "ready": ("真实数据已挂链并可读取。", "继续检查报告、账本或相关指标。"),
        "confirmed_zero": ("真实数据确认数值为零，必须保留证据链。", "打开证据来源复核零值是否仍有效。"),
        "not_loaded": ("未加载真实数据，不能显示财务数值。", "检查数据目录配置并重新读取真实文件。"),
        "not_mounted": ("数据源未挂链，相关指标保持阻断。", "挂载对应 read model 后重新生成指标。"),
        "path_error": ("路径不可用，系统无法定位本机真实文件。", "检查文件路径、挂载盘和目录权限。"),
        "permission_error": ("权限不足，系统无法读取本机真实文件。", "在 Finder 或终端修复读取权限后重试。"),
        "parse_error": ("解析失败，需查看文件、行号、字段或异常摘要。", "修正文件格式或字段映射后重新解析。"),
        "outdated": ("快照已过期，必须显示快照日期。", "刷新数据源或确认旧快照仍可用于只读复核。"),
        "filter_empty": ("当前筛选无结果，不代表真实余额为零。", "调整筛选条件或回到完整数据范围。"),
        "calculation_error": ("指标计算失败，不能输出财务结论。", "检查输入字段、公式参数和错误摘要。"),
        "review_required": ("需要人工复核，系统不能自动放行。", "进入账本或报告复核相关记录。"),
    }
    return {
        "schema": "PFIV023Stage8ErrorReasonCatalogV1",
        "version": VERSION,
        "stage": STAGE,
        "phase_id": PHASE_ID,
        "reasons": [
            {
                "status": status,
                "reason_zh": reason_map[status][0],
                "next_action_zh": reason_map[status][1],
            }
            for status in METRIC_DATA_STATUSES
        ],
    }


def build_stage8_dashboard_ui(
    *,
    core_metrics_read_model: dict[str, Any] | None = None,
    data_source_gate: dict[str, Any] | None = None,
    error_reason_catalog: dict[str, Any] | None = None,
) -> dict[str, Any]:
    gate = data_source_gate or build_stage8_data_source_gate(core_metrics_read_model=core_metrics_read_model)
    catalog = error_reason_catalog or build_stage8_error_reason_catalog()
    sources = list(gate.get("data_sources") or [])
    rows = [_dashboard_matrix_row(source, catalog) for source in sources]
    ready_count = sum(1 for row in rows if row["status"] in {"ready", "confirmed_zero"})
    blocked_count = len(rows) - ready_count
    return {
        "schema": "PFIV023Stage8DashboardUIV1",
        "version": VERSION,
        "stage": STAGE,
        "phase_id": PHASE82_ID,
        "phase_name": PHASE82_NAME,
        "source_core_metrics": gate.get("source_core_metrics", {}),
        "summary": {
            "source_count": len(rows),
            "ready_count": ready_count,
            "blocked_count": blocked_count,
            "auto_import_enabled": False,
            "read_model_hash": (gate.get("source_core_metrics") or {}).get("read_model_hash"),
            "as_of": (gate.get("source_core_metrics") or {}).get("as_of"),
        },
        "data_source_matrix": {
            "section_id": "data-source-matrix",
            "title_zh": "数据源矩阵",
            "columns": ("status", "records", "date range", "last updated", "blocked metrics"),
            "rows": rows,
        },
        "upload_import_status": {
            "section_id": "import-status",
            "title_zh": "上传/导入状态",
            "status": "read_only_gate",
            "status_zh": "当前仅展示真实数据挂链状态，不执行自动导入。",
            "auto_import_enabled": False,
            "import_actions": (
                {
                    "action_id": "open-ledger-review",
                    "label_zh": "打开账本流水复核",
                    "type": "route",
                    "route": "/ledger/review",
                    "reason_zh": "复核已读取的 Alipay 规范化流水。",
                },
                {
                    "action_id": "open-account-reconcile",
                    "label_zh": "打开账户余额复核",
                    "type": "route",
                    "route": "/accounts/reconcile",
                    "reason_zh": "账户余额 read model 未挂链，需从账户复核入口处理。",
                },
                {
                    "action_id": "open-investment-holdings",
                    "label_zh": "打开持仓复核",
                    "type": "route",
                    "route": "/investment/holdings",
                    "reason_zh": "持仓市值 read model 未挂链，需从持仓入口处理。",
                },
            ),
        },
        "parse_preview": {
            "section_id": "parse-preview",
            "title_zh": "解析预览",
            "entries": [_parse_preview_entry(row) for row in rows],
        },
        "field_mapping_entries": [_field_mapping_entry(row) for row in rows],
        "route_actions": _route_actions(rows),
        "stage_contract": {
            "phase_8_2_dashboard_ui_done": True,
            "phase_8_3_no_fallback_done": False,
            "stage_8_whole_review_done": False,
            "github_main_upload_done": False,
        },
        "explicitly_not_done": [
            "Phase 8.3 禁止假数据回退",
            "Stage 8 whole-stage review",
            "GitHub main upload for intermediate phase",
        ],
    }


def build_stage8_data_source_gate(core_metrics_read_model: dict[str, Any] | None = None) -> dict[str, Any]:
    read_model = core_metrics_read_model or {}
    source = read_model.get("source", {})
    metrics = {str(item.get("metric_id")): item for item in read_model.get("core_metrics", [])}
    blocked_metric_ids = list(read_model.get("blocked_metric_ids") or _blocked_metric_ids(metrics))
    return {
        "schema": "PFIV023Stage8DataSourceGateV1",
        "version": VERSION,
        "stage": STAGE,
        "phase_id": PHASE_ID,
        "phase_name": PHASE_NAME,
        "data_source_statuses": list(METRIC_DATA_STATUSES),
        "source_core_metrics": {
            "path": "PFI/reports/pfi_v023/stage_6/phase_6_1/core_metrics.json",
            "read_model_hash": read_model.get("read_model_hash"),
            "as_of": read_model.get("as_of"),
        },
        "data_sources": [
            _alipay_daily_source(source, metrics, read_model),
            _account_balance_source(blocked_metric_ids),
            _holding_market_value_source(blocked_metric_ids),
        ],
        "summary": {
            "ready_count": 1,
            "blocked_count": 2,
            "total_sources": 3,
            "blocked_metric_ids": blocked_metric_ids,
            "auto_import_enabled": False,
        },
        "explicitly_not_done": [
            "Phase 8.2 检查板 UI",
            "Phase 8.3 禁止假数据回退",
            "Stage 8 whole-stage review",
            "GitHub main upload for intermediate phase",
        ],
    }


def _alipay_daily_source(source: dict[str, Any], metrics: dict[str, dict[str, Any]], read_model: dict[str, Any]) -> dict[str, Any]:
    return {
        "data_source_id": "metadatabase_pfi_alipay_daily",
        "label": "MetaDatabase/PFI Alipay 日流水",
        "status": source.get("status", "not_loaded"),
        "status_zh": "真实数据已挂链",
        "path": source.get("transactions_path"),
        "manifest_path": source.get("manifest_path"),
        "records": {
            "raw_file_count": source.get("raw_file_count"),
            "normalized_record_count": source.get("transaction_count"),
            "account_count": 0,
            "holding_count": 0,
            "display_zh": f"记录数：{int(source.get('transaction_count') or 0):,} 条规范化流水，{int(source.get('raw_file_count') or 0):,} 个原始文件",
        },
        "date_range": source.get("date_range", {"start": None, "end": None}),
        "last_updated": read_model.get("as_of"),
        "read_model_hash": read_model.get("read_model_hash"),
        "evidence_hash": source.get("evidence_hash"),
        "ready_metric_ids": [
            metric_id
            for metric_id in ("life_consumption_cny", "total_consumption_outflow_cny", "data_health")
            if metrics.get(metric_id, {}).get("status") == "ready"
        ],
        "blocked_metric_ids": [],
        "affected_report_ids": ("consumption_structure_report", "data_quality_report"),
        "reason_zh": "真实 Alipay 日流水已读取，可支撑消费与数据健康报告。",
        "next_actions": ("打开账本流水复核", "打开报告与洞察查看消费结构缺口"),
        "route_targets": ("/ledger/review", "/reports"),
        "auto_import_enabled": False,
    }


def _account_balance_source(blocked_metric_ids: list[str]) -> dict[str, Any]:
    metrics = [metric_id for metric_id in ("net_worth_cny", "cash_balance_cny") if metric_id in blocked_metric_ids]
    return _blocked_source(
        data_source_id="account_balance_read_model",
        label="账户余额 read model",
        blocked_metric_ids=metrics,
        affected_report_ids=("net_worth_report", "cash_balance_report", "data_quality_report"),
        reason_zh="账户余额 read model 未挂链，净资产和现金余额保持阻断。",
        next_actions=("挂载账户余额 read model", "返回账户与资产复核数据目录"),
        route_targets=("/accounts/reconcile", "/reports"),
    )


def _holding_market_value_source(blocked_metric_ids: list[str]) -> dict[str, Any]:
    metrics = [metric_id for metric_id in ("net_worth_cny", "investment_market_value_cny") if metric_id in blocked_metric_ids]
    return _blocked_source(
        data_source_id="holding_market_value_read_model",
        label="持仓市值 read model",
        blocked_metric_ids=metrics,
        affected_report_ids=("net_worth_report", "investment_market_value_report", "data_quality_report"),
        reason_zh="持仓市值 read model 未挂链，净资产和投资市值保持阻断。",
        next_actions=("挂载持仓市值 read model", "返回投资管理复核持仓数据"),
        route_targets=("/investment/holdings", "/reports"),
    )


def _blocked_source(
    *,
    data_source_id: str,
    label: str,
    blocked_metric_ids: list[str],
    affected_report_ids: tuple[str, ...],
    reason_zh: str,
    next_actions: tuple[str, ...],
    route_targets: tuple[str, ...],
) -> dict[str, Any]:
    return {
        "data_source_id": data_source_id,
        "label": label,
        "status": "not_mounted",
        "status_zh": "数据源未挂链",
        "path": None,
        "manifest_path": None,
        "records": {
            "raw_file_count": None,
            "normalized_record_count": None,
            "account_count": None,
            "holding_count": None,
            "display_zh": "记录数：数据源未挂链",
        },
        "date_range": {"start": None, "end": None},
        "last_updated": None,
        "read_model_hash": None,
        "evidence_hash": None,
        "ready_metric_ids": [],
        "blocked_metric_ids": blocked_metric_ids,
        "affected_report_ids": affected_report_ids,
        "reason_zh": reason_zh,
        "next_actions": next_actions,
        "route_targets": route_targets,
        "auto_import_enabled": False,
    }


def _blocked_metric_ids(metrics: dict[str, dict[str, Any]]) -> list[str]:
    return [
        metric_id
        for metric_id, metric in metrics.items()
        if metric.get("status") not in {"ready", "confirmed_zero"}
    ]


def _dashboard_matrix_row(source: dict[str, Any], catalog: dict[str, Any]) -> dict[str, Any]:
    blocked_metric_ids = list(source.get("blocked_metric_ids") or [])
    records = dict(source.get("records") or {})
    date_range = dict(source.get("date_range") or {"start": None, "end": None})
    status = str(source.get("status") or "review_required")
    return {
        "data_source_id": source.get("data_source_id") or "",
        "label": source.get("label") or "未命名数据源",
        "status": status,
        "status_zh": source.get("status_zh") or _catalog_reason(catalog, status, "reason_zh"),
        "status_label": f"status: {status}",
        "records": records,
        "records_label": f"records: {_records_display(records)}",
        "date_range": date_range,
        "date_range_label": f"date range: {_date_range_display(date_range)}",
        "last_updated": source.get("last_updated"),
        "last_updated_label": f"last updated: {source.get('last_updated') or '未挂链'}",
        "blocked_metric_ids": blocked_metric_ids,
        "blocked_metrics_label": f"blocked metrics: {'、'.join(blocked_metric_ids) if blocked_metric_ids else '无'}",
        "reason_zh": source.get("reason_zh") or _catalog_reason(catalog, status, "reason_zh"),
        "next_actions": list(source.get("next_actions") or ()),
        "route_targets": list(source.get("route_targets") or ()),
        "affected_report_ids": list(source.get("affected_report_ids") or ()),
        "path": source.get("path"),
        "manifest_path": source.get("manifest_path"),
        "read_model_hash": source.get("read_model_hash"),
        "evidence_hash": source.get("evidence_hash") or source.get("read_model_hash"),
        "auto_import_enabled": bool(source.get("auto_import_enabled")),
        "parse_preview": _parse_preview_from_source(source),
    }


def _parse_preview_from_source(source: dict[str, Any]) -> dict[str, Any]:
    records = source.get("records") or {}
    count = records.get("normalized_record_count")
    if source.get("status") in {"ready", "confirmed_zero"} and count is not None:
        return {
            "status": "available",
            "detail_zh": f"解析预览可用：{int(count):,} 条规范化流水，来源为真实 read model。",
        }
    return {
        "status": "blocked",
        "detail_zh": "数据源未挂链，暂无解析预览。",
    }


def _parse_preview_entry(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "data_source_id": row["data_source_id"],
        "label": row["label"],
        "status": row["parse_preview"]["status"],
        "detail_zh": row["parse_preview"]["detail_zh"],
        "blocked_metric_ids": row["blocked_metric_ids"],
    }


def _field_mapping_entry(row: dict[str, Any]) -> dict[str, Any]:
    if row["data_source_id"] == "metadatabase_pfi_alipay_daily":
        return {
            "data_source_id": row["data_source_id"],
            "section_id": "field-mapping",
            "title_zh": "字段映射",
            "mapping_status": "available",
            "source_fields": ("transaction_id", "event_type", "amount", "occurred_at", "review_state"),
            "target_read_model": "PFIV023Stage6CoreMetricsReadModelV1",
            "detail_zh": "字段映射入口使用 Stage 6 已审计字段，不在本 phase 导入新文件。",
            "route": "/ledger/review",
        }
    return {
        "data_source_id": row["data_source_id"],
        "section_id": "field-mapping",
        "title_zh": "字段映射",
        "mapping_status": "blocked",
        "source_fields": (),
        "target_read_model": None,
        "detail_zh": f"{row['label']} 未挂链，字段映射入口保持阻断。",
        "route": row["route_targets"][0] if row["route_targets"] else "/reports",
    }


def _route_actions(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    labels = {
        "/reports": "查看报告与洞察",
        "/ledger/review": "复核账本流水",
        "/accounts/reconcile": "复核账户余额",
        "/investment/holdings": "复核投资持仓",
    }
    reasons = {
        "/reports": "查看受阻报告和数据健康说明。",
        "/ledger/review": "复核已挂链的真实 Alipay 流水。",
        "/accounts/reconcile": "处理账户余额 read model 未挂链。",
        "/investment/holdings": "处理持仓市值 read model 未挂链。",
    }
    route_order = ("/reports", "/ledger/review", "/accounts/reconcile", "/investment/holdings")
    active_routes = {route for row in rows for route in row.get("route_targets", [])}
    active_routes.add("/reports")
    actions = []
    for route in route_order:
        if route in active_routes:
            actions.append(
                {
                    "action_id": route.strip("/").replace("/", "-") or "home",
                    "label_zh": labels[route],
                    "type": "route",
                    "route": route,
                    "reason_zh": reasons[route],
                }
            )
    return actions


def _catalog_reason(catalog: dict[str, Any], status: str, field: str) -> str:
    for item in catalog.get("reasons") or []:
        if item.get("status") == status:
            return str(item.get(field) or "")
    return "需要人工复核，系统不能自动放行。"


def _records_display(records: dict[str, Any]) -> str:
    if records.get("display_zh"):
        return str(records["display_zh"])
    count = records.get("normalized_record_count")
    raw_count = records.get("raw_file_count")
    if count is None:
        return "数据源未挂链"
    return f"{int(count):,} 条记录 / {int(raw_count or 0):,} 个原始文件"


def _date_range_display(date_range: dict[str, Any]) -> str:
    start = date_range.get("start")
    end = date_range.get("end")
    if not start and not end:
        return "未挂链"
    return f"{start or '未知'} 至 {end or '未知'}"
