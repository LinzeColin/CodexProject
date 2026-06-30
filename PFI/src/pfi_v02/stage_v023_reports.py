from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from pfi_v02.stage_v023_formula_registry import build_stage7_formula_registry


VERSION = "v0.2.3"
STAGE = "Stage 7"
PHASE_ID = "V023-S7-P7.1"
PHASE_NAME = "报告合同"
PHASE72_ID = "V023-S7-P7.2"
PHASE72_NAME = "核心报告"
REPORT_STATUSES = ("complete", "partial", "blocked", "outdated", "review_required")
REQUIRED_REPORT_FIELDS = (
    "report_id",
    "title",
    "status",
    "conclusion_zh",
    "data_range",
    "sample_size",
    "core_metrics",
    "formulas",
    "parameters",
    "data_sources",
    "evidence_hash",
    "missing_data",
    "anomalies",
    "next_actions",
)


@dataclass(frozen=True)
class Stage7Phase71Contract:
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
class Stage7Phase72Contract:
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


def build_stage7_phase71_contract() -> dict[str, Any]:
    contract = Stage7Phase71Contract(
        version=VERSION,
        stage=STAGE,
        phase_id=PHASE_ID,
        phase_name=PHASE_NAME,
        current_phase_only=True,
        max_one_phase_per_run=True,
        task_ids=("T7.1.1", "T7.1.2", "T7.1.3", "T7.1.4"),
        allowed_files=(
            "PFI/src/pfi_v02/stage_v023_reports.py",
            "PFI/src/pfi_v02/stage_v023_formula_registry.py",
            "PFI/web/app/pages/reports.js",
            "PFI/web/app/components/report*.js",
            "PFI/tests/test_v023_stage7_reports.py",
            "PFI/docs/pfi_v023/STAGE7_REPORTS.md",
            "PFI/reports/pfi_v023/stage_7/*",
        ),
        changed_in_this_phase=(
            "PFI/src/pfi_v02/stage_v023_reports.py",
            "PFI/src/pfi_v02/stage_v023_formula_registry.py",
            "PFI/web/app/pages/reports.js",
            "PFI/tests/test_v023_stage7_reports.py",
            "PFI/docs/pfi_v023/STAGE7_REPORTS.md",
            "PFI/reports/pfi_v023/stage_7/phase_7_1/*",
        ),
        validation_commands=(
            "node --check PFI/web/app/pages/reports.js",
            "python3 -m pytest PFI/tests/test_v023_stage7_reports.py -q",
            "python3 -m pytest PFI/tests/test_v023_*.py -q",
        ),
        evidence_files=(
            "PFI/docs/pfi_v023/STAGE7_REPORTS.md",
            "PFI/reports/pfi_v023/stage_7/phase_7_1/evidence.json",
            "PFI/reports/pfi_v023/stage_7/phase_7_1/report_contract.json",
            "PFI/reports/pfi_v023/stage_7/phase_7_1/formula_registry.json",
            "PFI/reports/pfi_v023/stage_7/phase_7_1/report_page_model.json",
            "PFI/reports/pfi_v023/stage_7/phase_7_1/no_source_term_scan.json",
            "PFI/reports/pfi_v023/stage_7/phase_7_1/terminal.log",
            "PFI/reports/pfi_v023/stage_7/phase_7_1/changed_files.txt",
        ),
        explicitly_not_done=(
            "Phase 7.2 核心报告",
            "Phase 7.3 数据质量与调参",
            "Stage 7 whole-stage review",
            "GitHub main upload for intermediate phase",
        ),
    )
    payload = asdict(contract)
    for key in ("task_ids", "allowed_files", "changed_in_this_phase", "validation_commands", "evidence_files", "explicitly_not_done"):
        payload[key] = list(payload[key])
    return payload


def build_stage7_phase72_contract() -> dict[str, Any]:
    contract = Stage7Phase72Contract(
        version=VERSION,
        stage=STAGE,
        phase_id=PHASE72_ID,
        phase_name=PHASE72_NAME,
        current_phase_only=True,
        max_one_phase_per_run=True,
        task_ids=("T7.2.1", "T7.2.2", "T7.2.3", "T7.2.4"),
        allowed_files=(
            "PFI/src/pfi_v02/stage_v023_reports.py",
            "PFI/src/pfi_v02/stage_v023_formula_registry.py",
            "PFI/web/app/pages/reports.js",
            "PFI/web/app/components/report*.js",
            "PFI/tests/test_v023_stage7_reports.py",
            "PFI/docs/pfi_v023/STAGE7_REPORTS.md",
            "PFI/reports/pfi_v023/stage_7/*",
        ),
        changed_in_this_phase=(
            "PFI/src/pfi_v02/stage_v023_reports.py",
            "PFI/web/app/pages/reports.js",
            "PFI/tests/test_v023_stage7_reports.py",
            "PFI/docs/pfi_v023/STAGE7_REPORTS.md",
            "PFI/reports/pfi_v023/stage_7/phase_7_2/*",
        ),
        validation_commands=(
            "node --check PFI/web/app/pages/reports.js",
            "python3 -m pytest PFI/tests/test_v023_stage7_reports.py -q",
            "python3 -m pytest PFI/tests/test_v023_*.py -q",
        ),
        evidence_files=(
            "PFI/docs/pfi_v023/STAGE7_REPORTS.md",
            "PFI/reports/pfi_v023/stage_7/phase_7_2/evidence.json",
            "PFI/reports/pfi_v023/stage_7/phase_7_2/core_reports.json",
            "PFI/reports/pfi_v023/stage_7/phase_7_2/core_reports_page_model.json",
            "PFI/reports/pfi_v023/stage_7/phase_7_2/no_source_term_scan.json",
            "PFI/reports/pfi_v023/stage_7/phase_7_2/terminal.log",
            "PFI/reports/pfi_v023/stage_7/phase_7_2/changed_files.txt",
        ),
        explicitly_not_done=(
            "Phase 7.3 数据质量与调参",
            "Stage 7 whole-stage review",
            "GitHub main upload for intermediate phase",
        ),
    )
    payload = asdict(contract)
    for key in ("task_ids", "allowed_files", "changed_in_this_phase", "validation_commands", "evidence_files", "explicitly_not_done"):
        payload[key] = list(payload[key])
    return payload


def build_stage7_report_contract(core_metrics_read_model: dict[str, Any] | None = None) -> dict[str, Any]:
    read_model = core_metrics_read_model or {}
    metrics = {str(item.get("metric_id")): item for item in read_model.get("core_metrics", [])}
    registry = build_stage7_formula_registry(read_model)
    formulas = {str(item["metric_id"]): item for item in registry["formulas"]}
    source = read_model.get("source", {})
    shared_context = {
        "data_range": source.get("date_range", {"start": None, "end": None}),
        "sample_size": {
            "transaction_count": source.get("transaction_count", 0),
            "raw_file_count": source.get("raw_file_count", 0),
            "account_count": 0,
            "holding_count": 0,
        },
        "read_model_hash": read_model.get("read_model_hash"),
        "source_status": source.get("status", "not_loaded"),
    }
    reports = [
        _metric_report(
            "net_worth_report",
            "净资产报告",
            ("net_worth_cny",),
            "净资产报告被阻断：未挂载账户余额与持仓 read model，不能生成完整结论。",
            metrics,
            formulas,
            shared_context,
            next_actions=("挂载账户余额 read model", "挂载持仓市值 read model"),
        ),
        _metric_report(
            "cash_balance_report",
            "现金余额报告",
            ("cash_balance_cny",),
            "现金余额报告被阻断：未挂载账户余额 read model，不能生成完整结论。",
            metrics,
            formulas,
            shared_context,
            next_actions=("挂载账户余额 read model",),
        ),
        _metric_report(
            "investment_market_value_report",
            "投资市值报告",
            ("investment_market_value_cny",),
            "投资市值报告被阻断：未挂载持仓市值 read model，不能生成完整结论。",
            metrics,
            formulas,
            shared_context,
            next_actions=("挂载持仓市值 read model",),
        ),
        _consumption_report(metrics, formulas, shared_context),
        _data_quality_report(metrics, formulas, shared_context),
    ]
    return {
        "schema": "PFIV023Stage7ReportContractV1",
        "version": VERSION,
        "stage": STAGE,
        "phase_id": PHASE_ID,
        "report_statuses": list(REPORT_STATUSES),
        "required_report_fields": list(REQUIRED_REPORT_FIELDS),
        "source_core_metrics": "PFI/reports/pfi_v023/stage_6/phase_6_1/core_metrics.json",
        "read_model_hash": read_model.get("read_model_hash"),
        "as_of": read_model.get("as_of"),
        "reports": reports,
    }


def build_stage7_core_reports(core_metrics_read_model: dict[str, Any] | None = None) -> dict[str, Any]:
    read_model = core_metrics_read_model or {}
    contract = build_stage7_report_contract(read_model)
    reports = {str(item["report_id"]): item for item in contract["reports"]}
    core_report_ids = (
        "net_worth_report",
        "cash_balance_report",
        "investment_market_value_report",
        "consumption_structure_report",
    )
    selected = []
    for report_id in core_report_ids:
        report = dict(reports[report_id])
        report["phase_id"] = PHASE72_ID
        if report_id == "consumption_structure_report":
            report["conclusion_zh"] = _consumption_phase72_conclusion(report)
            report["missing_data"] = [
                "缺少消费分类结构、商户、预算和异常消费明细，当前只能生成 partial 结论。",
            ]
        selected.append(report)
    return {
        "schema": "PFIV023Stage7CoreReportsV1",
        "version": VERSION,
        "stage": STAGE,
        "phase_id": PHASE72_ID,
        "phase_name": PHASE72_NAME,
        "source_core_metrics": {
            "path": "PFI/reports/pfi_v023/stage_6/phase_6_1/core_metrics.json",
            "read_model_hash": read_model.get("read_model_hash"),
            "as_of": read_model.get("as_of"),
        },
        "reports": selected,
        "summary": {
            "complete": sum(1 for item in selected if item["status"] == "complete"),
            "partial": sum(1 for item in selected if item["status"] == "partial"),
            "blocked": sum(1 for item in selected if item["status"] == "blocked"),
        },
        "explicitly_not_done": [
            "Phase 7.3 数据质量与调参",
            "Stage 7 whole-stage review",
            "GitHub main upload for intermediate phase",
        ],
    }


def _metric_report(
    report_id: str,
    title: str,
    metric_ids: tuple[str, ...],
    blocked_conclusion: str,
    metrics: dict[str, dict[str, Any]],
    formulas: dict[str, dict[str, Any]],
    shared_context: dict[str, Any],
    *,
    next_actions: tuple[str, ...],
) -> dict[str, Any]:
    metric_rows = [_metric_row(metrics.get(metric_id, {})) for metric_id in metric_ids]
    blocked = [item for item in metric_rows if item["status"] not in {"ready", "confirmed_zero"}]
    return _report_payload(
        report_id=report_id,
        title=title,
        status="blocked" if blocked else "partial",
        conclusion_zh=blocked_conclusion if blocked else f"{title}已有真实输入，但 Phase 7.2 才生成正式报告结论。",
        metric_rows=metric_rows,
        formula_rows=[formulas[metric_id] for metric_id in metric_ids],
        missing_data=[_missing_metric_text(item) for item in blocked],
        anomalies=[],
        next_actions=list(next_actions),
        shared_context=shared_context,
    )


def _consumption_report(
    metrics: dict[str, dict[str, Any]],
    formulas: dict[str, dict[str, Any]],
    shared_context: dict[str, Any],
) -> dict[str, Any]:
    metric_ids = ("life_consumption_cny", "total_consumption_outflow_cny")
    metric_rows = [_metric_row(metrics.get(metric_id, {})) for metric_id in metric_ids]
    missing_data = ["缺少消费分类、商户、预算和异常消费明细，Phase 7.2 才生成消费结构正式报告。"]
    return _report_payload(
        report_id="consumption_structure_report",
        title="消费结构报告",
        status="partial",
        conclusion_zh="消费结构报告已有真实生活消费和消费总流出输入，但缺少分类结构明细，当前只能给出部分结论。",
        metric_rows=metric_rows,
        formula_rows=[formulas[metric_id] for metric_id in metric_ids],
        missing_data=missing_data,
        anomalies=[],
        next_actions=["接入消费分类结构 read model", "接入商户与预算视图"],
        shared_context=shared_context,
    )


def _data_quality_report(
    metrics: dict[str, dict[str, Any]],
    formulas: dict[str, dict[str, Any]],
    shared_context: dict[str, Any],
) -> dict[str, Any]:
    metric_rows = [_metric_row(metric) for metric in metrics.values()]
    blocked_rows = [item for item in metric_rows if item["status"] not in {"ready", "confirmed_zero"}]
    return _report_payload(
        report_id="data_quality_report",
        title="数据质量报告",
        status="partial" if blocked_rows else "complete",
        conclusion_zh="数据质量报告可解释当前阻断项：未挂载账户余额、现金余额和持仓市值 read model。",
        metric_rows=metric_rows,
        formula_rows=[formulas[metric_id] for metric_id in formulas],
        missing_data=[_missing_metric_text(item) for item in blocked_rows],
        anomalies=[],
        next_actions=["补齐账户余额 read model", "补齐持仓市值 read model", "复核 406 条待复核流水"],
        shared_context=shared_context,
    )


def _report_payload(
    *,
    report_id: str,
    title: str,
    status: str,
    conclusion_zh: str,
    metric_rows: list[dict[str, Any]],
    formula_rows: list[dict[str, Any]],
    missing_data: list[str],
    anomalies: list[dict[str, Any]],
    next_actions: list[str],
    shared_context: dict[str, Any],
) -> dict[str, Any]:
    return {
        "report_id": report_id,
        "title": title,
        "status": status,
        "conclusion_zh": conclusion_zh,
        "data_range": shared_context["data_range"],
        "sample_size": shared_context["sample_size"],
        "core_metrics": metric_rows,
        "formulas": [_formula_ref(item) for item in formula_rows],
        "parameters": [parameter for item in formula_rows for parameter in item.get("parameters", [])],
        "data_sources": [source for item in formula_rows for source in item.get("data_sources", [])],
        "evidence_hash": shared_context["read_model_hash"],
        "missing_data": missing_data,
        "anomalies": anomalies,
        "next_actions": next_actions,
    }


def _metric_row(metric: dict[str, Any]) -> dict[str, Any]:
    return {
        "metric_id": metric.get("metric_id"),
        "label": metric.get("label"),
        "value": metric.get("value"),
        "currency": metric.get("currency"),
        "status": metric.get("status", "not_loaded"),
        "source": metric.get("source"),
        "as_of": metric.get("as_of"),
        "evidence_hash": metric.get("evidence_hash"),
        "message_zh": metric.get("message_zh", "未加载真实数据"),
    }


def _formula_ref(formula: dict[str, Any]) -> dict[str, Any]:
    return {
        "formula_id": formula["formula_id"],
        "metric_id": formula["metric_id"],
        "formula_zh": formula["formula_zh"],
        "input_status": formula["input_status"],
        "missing_inputs": formula["missing_inputs"],
        "status_policy_zh": formula["status_policy_zh"],
    }


def _missing_metric_text(metric: dict[str, Any]) -> str:
    label = metric.get("label") or metric.get("metric_id")
    message = metric.get("message_zh") or "未加载真实数据"
    return f"{label}：{message}"


def _consumption_phase72_conclusion(report: dict[str, Any]) -> str:
    metrics = {str(item.get("metric_id")): item for item in report.get("core_metrics", [])}
    life = metrics.get("life_consumption_cny", {})
    total = metrics.get("total_consumption_outflow_cny", {})
    return (
        "消费结构报告已有真实 Alipay 输入："
        f"生活消费 {_display_metric_value(life)}，"
        f"消费总流出 {_display_metric_value(total)}。"
        "当前缺少分类结构、商户、预算和异常消费明细，因此报告状态为 partial。"
    )


def _display_metric_value(metric: dict[str, Any]) -> str:
    value = metric.get("value")
    currency = metric.get("currency") or "CNY"
    if value is None:
        return str(metric.get("message_zh") or "未加载真实数据")
    if currency == "records":
        return f"{int(value):,} records"
    return f"{currency} {float(value):,.2f}"
