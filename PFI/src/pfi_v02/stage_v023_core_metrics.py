from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any

from pfi_v02.stage_v023_data_state import METRIC_DATA_STATUSES, build_metric_state
from pfi_v02.stage_v023_read_model import build_stage6_read_model_input, iter_stage6_transactions


VERSION = "v0.2.3"
STAGE = "Stage 6"
PHASE_ID = "V023-S6-P6.1"
PHASE_NAME = "read model adapter"

CORE_METRICS = (
    ("net_worth_cny", "净资产", "CNY"),
    ("cash_balance_cny", "现金余额", "CNY"),
    ("investment_market_value_cny", "投资市值", "CNY"),
    ("life_consumption_cny", "生活消费", "CNY"),
    ("total_consumption_outflow_cny", "消费总流出", "CNY"),
    ("data_health", "数据健康", "records"),
)
CORE_METRIC_IDS = tuple(metric_id for metric_id, _label, _currency in CORE_METRICS)
TRANSACTION_SOURCE = "MetaDatabase/PFI/alipay_daily/processed/alipay_transactions.csv"


@dataclass(frozen=True)
class Stage6Phase61Contract:
    version: str
    stage: str
    phase_id: str
    phase_name: str
    current_phase_only: bool
    max_one_phase_per_run: bool
    real_data_only_financial_metrics: bool
    task_ids: tuple[str, ...]
    allowed_files: tuple[str, ...]
    changed_in_this_phase: tuple[str, ...]
    validation_commands: tuple[str, ...]
    evidence_files: tuple[str, ...]
    explicitly_not_done: tuple[str, ...]


@dataclass(frozen=True)
class Stage6Phase62Contract:
    version: str
    stage: str
    phase_id: str
    phase_name: str
    current_phase_only: bool
    max_one_phase_per_run: bool
    real_data_only_financial_metrics: bool
    task_ids: tuple[str, ...]
    allowed_files: tuple[str, ...]
    changed_in_this_phase: tuple[str, ...]
    validation_commands: tuple[str, ...]
    evidence_files: tuple[str, ...]
    explicitly_not_done: tuple[str, ...]


@dataclass(frozen=True)
class Stage6Phase63Contract:
    version: str
    stage: str
    phase_id: str
    phase_name: str
    current_phase_only: bool
    max_one_phase_per_run: bool
    real_data_only_financial_metrics: bool
    task_ids: tuple[str, ...]
    allowed_files: tuple[str, ...]
    changed_in_this_phase: tuple[str, ...]
    validation_commands: tuple[str, ...]
    evidence_files: tuple[str, ...]
    explicitly_not_done: tuple[str, ...]


def build_stage6_phase61_contract() -> dict[str, Any]:
    contract = Stage6Phase61Contract(
        version=VERSION,
        stage=STAGE,
        phase_id=PHASE_ID,
        phase_name=PHASE_NAME,
        current_phase_only=True,
        max_one_phase_per_run=True,
        real_data_only_financial_metrics=True,
        task_ids=("T6.1.1", "T6.1.2", "T6.1.3", "T6.1.4"),
        allowed_files=(
            "PFI/src/pfi_v02/stage_v023_read_model.py",
            "PFI/src/pfi_v02/stage_v023_core_metrics.py",
            "PFI/web/app/data/coreMetrics.js",
            "PFI/tests/test_v023_stage6_core_metrics.py",
            "PFI/docs/pfi_v023/STAGE6_CORE_METRICS.md",
            "PFI/reports/pfi_v023/stage_6/*",
        ),
        changed_in_this_phase=(
            "PFI/src/pfi_v02/stage_v023_read_model.py",
            "PFI/src/pfi_v02/stage_v023_core_metrics.py",
            "PFI/web/app/data/coreMetrics.js",
            "PFI/tests/test_v023_stage6_core_metrics.py",
            "PFI/docs/pfi_v023/STAGE6_CORE_METRICS.md",
            "PFI/reports/pfi_v023/stage_6/phase_6_1/*",
        ),
        validation_commands=(
            "node --check PFI/web/app/data/coreMetrics.js",
            "python3 -m pytest PFI/tests/test_v023_stage6_core_metrics.py -q",
        ),
        evidence_files=(
            "PFI/docs/pfi_v023/STAGE6_CORE_METRICS.md",
            "PFI/reports/pfi_v023/stage_6/phase_6_1/evidence.json",
            "PFI/reports/pfi_v023/stage_6/phase_6_1/core_metrics.json",
            "PFI/reports/pfi_v023/stage_6/phase_6_1/read_model_audit.json",
            "PFI/reports/pfi_v023/stage_6/phase_6_1/terminal.log",
            "PFI/reports/pfi_v023/stage_6/phase_6_1/changed_files.txt",
        ),
        explicitly_not_done=(
            "Phase 6.2 UI wiring",
            "Phase 6.3 cross-page consistency",
            "Stage 6 whole-stage review",
            "GitHub main upload for intermediate phase",
        ),
    )
    payload = asdict(contract)
    for key in ("task_ids", "allowed_files", "changed_in_this_phase", "validation_commands", "evidence_files", "explicitly_not_done"):
        payload[key] = list(payload[key])
    return payload


def build_stage6_phase62_contract() -> dict[str, Any]:
    contract = Stage6Phase62Contract(
        version=VERSION,
        stage=STAGE,
        phase_id="V023-S6-P6.2",
        phase_name="页面接入",
        current_phase_only=True,
        max_one_phase_per_run=True,
        real_data_only_financial_metrics=True,
        task_ids=("T6.2.1", "T6.2.2", "T6.2.3", "T6.2.4"),
        allowed_files=(
            "PFI/src/pfi_v02/stage_v023_core_metrics.py",
            "PFI/src/pfi_v02/stage_v023_read_model.py",
            "PFI/web/app/data/*.js",
            "PFI/web/app/data/coreMetrics.js",
            "PFI/web/app/pages/home.js",
            "PFI/web/app/pages/accounts.js",
            "PFI/web/app/pages/investment.js",
            "PFI/web/app/pages/consumption.js",
            "PFI/tests/test_v023_stage6_core_metrics.py",
            "PFI/docs/pfi_v023/STAGE6_CORE_METRICS.md",
            "PFI/reports/pfi_v023/stage_6/*",
        ),
        changed_in_this_phase=(
            "PFI/src/pfi_v02/stage_v023_core_metrics.py",
            "PFI/web/app/data/coreMetrics.js",
            "PFI/web/app/pages/home.js",
            "PFI/web/app/pages/accounts.js",
            "PFI/web/app/pages/investment.js",
            "PFI/web/app/pages/consumption.js",
            "PFI/tests/test_v023_stage6_core_metrics.py",
            "PFI/docs/pfi_v023/STAGE6_CORE_METRICS.md",
            "PFI/reports/pfi_v023/stage_6/phase_6_2/*",
        ),
        validation_commands=(
            "node --check PFI/web/app/data/coreMetrics.js",
            "node --check PFI/web/app/pages/home.js",
            "node --check PFI/web/app/pages/accounts.js",
            "node --check PFI/web/app/pages/investment.js",
            "node --check PFI/web/app/pages/consumption.js",
            "python3 -m pytest PFI/tests/test_v023_stage6_core_metrics.py -q",
        ),
        evidence_files=(
            "PFI/docs/pfi_v023/STAGE6_CORE_METRICS.md",
            "PFI/reports/pfi_v023/stage_6/phase_6_2/evidence.json",
            "PFI/reports/pfi_v023/stage_6/phase_6_2/page_view_models.json",
            "PFI/reports/pfi_v023/stage_6/phase_6_2/terminal.log",
            "PFI/reports/pfi_v023/stage_6/phase_6_2/changed_files.txt",
        ),
        explicitly_not_done=(
            "Phase 6.3 cross-page consistency",
            "Stage 6 whole-stage review",
            "GitHub main upload for intermediate phase",
        ),
    )
    payload = asdict(contract)
    for key in ("task_ids", "allowed_files", "changed_in_this_phase", "validation_commands", "evidence_files", "explicitly_not_done"):
        payload[key] = list(payload[key])
    return payload


def build_stage6_phase63_contract() -> dict[str, Any]:
    contract = Stage6Phase63Contract(
        version=VERSION,
        stage=STAGE,
        phase_id="V023-S6-P6.3",
        phase_name="指标一致性",
        current_phase_only=True,
        max_one_phase_per_run=True,
        real_data_only_financial_metrics=True,
        task_ids=("T6.3.1", "T6.3.2", "T6.3.3", "T6.3.4"),
        allowed_files=(
            "PFI/src/pfi_v02/stage_v023_core_metrics.py",
            "PFI/src/pfi_v02/stage_v023_read_model.py",
            "PFI/web/app/data/*.js",
            "PFI/web/app/data/coreMetrics.js",
            "PFI/web/app/pages/home.js",
            "PFI/web/app/pages/accounts.js",
            "PFI/web/app/pages/investment.js",
            "PFI/web/app/pages/consumption.js",
            "PFI/tests/test_v023_stage6_core_metrics.py",
            "PFI/docs/pfi_v023/STAGE6_CORE_METRICS.md",
            "PFI/reports/pfi_v023/stage_6/*",
        ),
        changed_in_this_phase=(
            "PFI/src/pfi_v02/stage_v023_core_metrics.py",
            "PFI/web/app/data/coreMetrics.js",
            "PFI/tests/test_v023_stage6_core_metrics.py",
            "PFI/docs/pfi_v023/STAGE6_CORE_METRICS.md",
            "PFI/reports/pfi_v023/stage_6/phase_6_3/*",
        ),
        validation_commands=(
            "node --check PFI/web/app/data/coreMetrics.js",
            "python3 -m pytest PFI/tests/test_v023_stage6_core_metrics.py -q",
        ),
        evidence_files=(
            "PFI/docs/pfi_v023/STAGE6_CORE_METRICS.md",
            "PFI/reports/pfi_v023/stage_6/phase_6_3/evidence.json",
            "PFI/reports/pfi_v023/stage_6/phase_6_3/consistency_matrix.json",
            "PFI/reports/pfi_v023/stage_6/phase_6_3/metric_basis.json",
            "PFI/reports/pfi_v023/stage_6/phase_6_3/no_source_term_scan.json",
            "PFI/reports/pfi_v023/stage_6/phase_6_3/error_state_view_models.json",
            "PFI/reports/pfi_v023/stage_6/phase_6_3/screenshots/error_states.png",
            "PFI/reports/pfi_v023/stage_6/phase_6_3/terminal.log",
            "PFI/reports/pfi_v023/stage_6/phase_6_3/changed_files.txt",
        ),
        explicitly_not_done=(
            "Stage 6 whole-stage review",
            "GitHub main upload for intermediate phase",
        ),
    )
    payload = asdict(contract)
    for key in ("task_ids", "allowed_files", "changed_in_this_phase", "validation_commands", "evidence_files", "explicitly_not_done"):
        payload[key] = list(payload[key])
    return payload


def build_stage6_metric_basis_catalog() -> dict[str, Any]:
    status_policy = "只有 ready 或 confirmed_zero 且带 source/as_of/evidence_hash 时显示数值；其他状态显示中文原因。"
    hash_policy = "所有可显示值必须保留 as_of 和 evidence_hash，跨页面不得改写。"
    return {
        "schema": "PFIV023Stage6MetricBasisCatalogV1",
        "version": VERSION,
        "stage": STAGE,
        "phase_id": "V023-S6-P6.3",
        "metrics": {
            "net_worth_cny": {
                "label": "净资产",
                "basis_zh": "来自真实账户余额与持仓 read model；未挂载时返回中文阻塞状态。",
                "status_policy_zh": status_policy,
                "as_of_hash_policy_zh": hash_policy,
            },
            "cash_balance_cny": {
                "label": "现金余额",
                "basis_zh": "来自真实账户余额 read model；当前未挂载账户余额时不得显示金额替代。",
                "status_policy_zh": status_policy,
                "as_of_hash_policy_zh": hash_policy,
            },
            "investment_market_value_cny": {
                "label": "投资市值",
                "basis_zh": "来自真实持仓市值 read model；当前未挂载持仓市值时不得显示金额替代。",
                "status_policy_zh": status_policy,
                "as_of_hash_policy_zh": hash_policy,
            },
            "life_consumption_cny": {
                "label": "生活消费",
                "basis_zh": "来自真实 Alipay 交易，口径为生活消费流出减退款。",
                "status_policy_zh": status_policy,
                "as_of_hash_policy_zh": hash_policy,
            },
            "total_consumption_outflow_cny": {
                "label": "消费总流出",
                "basis_zh": "来自真实 Alipay 交易，口径为生活消费、基金申购、资产买入流出减退款。",
                "status_policy_zh": status_policy,
                "as_of_hash_policy_zh": hash_policy,
            },
            "data_health": {
                "label": "数据健康",
                "basis_zh": "来自真实导入清单的交易记录数、原始文件数和数据时间范围。",
                "status_policy_zh": status_policy,
                "as_of_hash_policy_zh": hash_policy,
            },
        },
    }


def build_stage6_phase63_consistency_matrix(
    core_metrics_read_model: dict[str, Any],
    page_view_models: dict[str, Any],
) -> dict[str, Any]:
    source_metrics = {
        str(metric.get("metric_id")): _metric_chain(metric)
        for metric in core_metrics_read_model.get("core_metrics", [])
    }
    source_hash = core_metrics_read_model.get("read_model_hash")
    source_as_of = core_metrics_read_model.get("as_of")
    home_metrics = [_metric_chain(metric) for metric in page_view_models.get("home", {}).get("cards", [])]
    account_metrics = [_metric_chain(metric) for metric in page_view_models.get("accounts", {}).get("cards", [])]
    report_metrics = list(source_metrics.values())
    surfaces = {
        "home": _surface_consistency_record("home", home_metrics, source_hash, source_as_of),
        "accounts": _surface_consistency_record("accounts", account_metrics, source_hash, source_as_of),
        "report": _surface_consistency_record("report", report_metrics, source_hash, source_as_of),
    }
    findings = _consistency_findings(source_metrics, surfaces)
    return {
        "schema": "PFIV023Stage6MetricConsistencyMatrixV1",
        "version": VERSION,
        "stage": STAGE,
        "phase_id": "V023-S6-P6.3",
        "source_core_metrics": {
            "schema": core_metrics_read_model.get("schema"),
            "read_model_hash": source_hash,
            "as_of": source_as_of,
            "source_status": core_metrics_read_model.get("source", {}).get("status"),
        },
        "surfaces": surfaces,
        "findings": findings,
    }


def build_stage6_core_metrics_read_model(
    project_root: str | Path | None = None,
    *,
    data_root: str | Path | None = None,
) -> dict[str, Any]:
    read_input = build_stage6_read_model_input(project_root=project_root, data_root=data_root)
    if read_input["status"] != "ready":
        metrics = _blocked_metrics(read_input["status"], read_input["message_zh"])
        return _read_model_payload(read_input=read_input, metrics=metrics, read_model_hash=None)

    try:
        transaction_metrics = _calculate_transaction_metrics(read_input)
        metrics = [
            _blocked_metric(
                "net_worth_cny",
                "净资产",
                "CNY",
                "not_mounted",
                "未挂载账户余额与持仓 read model，无法计算净资产",
            ),
            _blocked_metric(
                "cash_balance_cny",
                "现金余额",
                "CNY",
                "not_mounted",
                "未挂载账户余额 read model，无法计算现金余额",
            ),
            _blocked_metric(
                "investment_market_value_cny",
                "投资市值",
                "CNY",
                "not_mounted",
                "未挂载持仓市值 read model，无法计算投资市值",
            ),
            _ready_metric(
                "life_consumption_cny",
                "生活消费",
                "CNY",
                transaction_metrics["life_consumption_cny"],
                read_input,
                "真实 Alipay 交易：生活消费流出减退款",
            ),
            _ready_metric(
                "total_consumption_outflow_cny",
                "消费总流出",
                "CNY",
                transaction_metrics["total_consumption_outflow_cny"],
                read_input,
                "真实 Alipay 交易：生活消费、基金申购、资产买入流出减退款",
            ),
            _ready_metric(
                "data_health",
                "数据健康",
                "records",
                Decimal(str(read_input["transaction_count"])),
                read_input,
                "真实交易记录数已完成 read model 输入校验",
                source="MetaDatabase/PFI/alipay_daily/processed/alipay_import_manifest.json",
            ),
        ]
    except (InvalidOperation, KeyError, OSError, ValueError):
        metrics = _blocked_metrics("calculation_error", "指标计算失败，请检查真实交易字段")

    return _read_model_payload(read_input=read_input, metrics=metrics, read_model_hash=_model_hash(read_input, metrics))


def _calculate_transaction_metrics(read_input: dict[str, Any]) -> dict[str, Decimal]:
    living_outflow = Decimal("0")
    total_outflow = Decimal("0")
    refund_offset = Decimal("0")

    for row in iter_stage6_transactions(read_input):
        raw_type = str(row.get("event_type") or "").strip().upper()
        amount = Decimal(str(row.get("amount") or "0"))
        if raw_type == "CASH" and amount < 0:
            living_outflow += abs(amount)
            total_outflow += abs(amount)
        elif raw_type == "FUND" and amount < 0:
            total_outflow += abs(amount)
        elif raw_type == "BUY_ASSET" and amount < 0:
            total_outflow += abs(amount)
        elif raw_type == "REFUND":
            refund_offset += abs(amount)

    return {
        "life_consumption_cny": _money(max(Decimal("0"), living_outflow - refund_offset)),
        "total_consumption_outflow_cny": _money(max(Decimal("0"), total_outflow - refund_offset)),
    }


def _blocked_metrics(status: str, message_zh: str) -> list[dict[str, Any]]:
    return [_blocked_metric(metric_id, label, currency, status, message_zh) for metric_id, label, currency in CORE_METRICS]


def _blocked_metric(metric_id: str, label: str, currency: str, status: str, message_zh: str) -> dict[str, Any]:
    safe_status = status if status in METRIC_DATA_STATUSES else "review_required"
    return build_metric_state(metric_id, label, status=safe_status, currency=currency, message_zh=message_zh)


def _ready_metric(
    metric_id: str,
    label: str,
    currency: str,
    value: Decimal,
    read_input: dict[str, Any],
    message_zh: str,
    *,
    source: str = TRANSACTION_SOURCE,
) -> dict[str, Any]:
    value_number: float | int
    if value == value.to_integral_value():
        value_number = int(value)
    else:
        value_number = float(value)
    return build_metric_state(
        metric_id,
        label,
        status="ready",
        value=value_number,
        currency=currency,
        source=source,
        as_of=str(read_input["as_of"]),
        evidence_hash=_metric_hash(read_input["evidence_hash"], metric_id, str(value)),
        message_zh=message_zh,
    )


def _read_model_payload(
    *,
    read_input: dict[str, Any],
    metrics: list[dict[str, Any]],
    read_model_hash: str | None,
) -> dict[str, Any]:
    return {
        "schema": "PFIV023Stage6CoreMetricsReadModelV1",
        "version": VERSION,
        "stage": STAGE,
        "phase_id": PHASE_ID,
        "source": {
            "type": read_input["source_type"],
            "status": read_input["status"],
            "data_root": read_input["data_root"],
            "transactions_path": read_input["transactions_path"],
            "manifest_path": read_input["manifest_path"],
            "transaction_count": read_input["transaction_count"],
            "raw_file_count": read_input["raw_file_count"],
            "date_range": read_input["date_range"],
            "evidence_hash": read_input["evidence_hash"],
        },
        "as_of": read_input["as_of"],
        "read_model_hash": read_model_hash,
        "core_metrics": metrics,
        "blocked_metric_ids": [metric["metric_id"] for metric in metrics if metric["status"] not in {"ready", "confirmed_zero"}],
    }


def _metric_hash(read_input_hash: str | None, metric_id: str, value: str) -> str:
    payload = json.dumps(
        {"input": read_input_hash, "metric_id": metric_id, "value": value, "phase_id": PHASE_ID},
        ensure_ascii=False,
        sort_keys=True,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _model_hash(read_input: dict[str, Any], metrics: list[dict[str, Any]]) -> str:
    payload = json.dumps(
        {"input_hash": read_input.get("evidence_hash"), "metrics": metrics, "phase_id": PHASE_ID},
        ensure_ascii=False,
        sort_keys=True,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _metric_chain(metric: dict[str, Any]) -> dict[str, Any]:
    return {
        "metric_id": metric.get("metric_id"),
        "label": metric.get("label"),
        "value": metric.get("value"),
        "currency": metric.get("currency"),
        "status": metric.get("status"),
        "source": metric.get("source"),
        "as_of": metric.get("as_of"),
        "evidence_hash": metric.get("evidence_hash"),
        "message_zh": metric.get("message_zh"),
    }


def _surface_consistency_record(
    surface: str,
    metrics: list[dict[str, Any]],
    read_model_hash: str | None,
    as_of: str | None,
) -> dict[str, Any]:
    return {
        "surface": surface,
        "read_model_hash": read_model_hash,
        "as_of": as_of,
        "metrics": metrics,
    }


def _consistency_findings(
    source_metrics: dict[str, dict[str, Any]],
    surfaces: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    comparable_fields = ("status", "value", "source", "as_of", "evidence_hash")
    findings: list[dict[str, Any]] = []
    for surface_name, surface in surfaces.items():
        for metric in surface["metrics"]:
            metric_id = str(metric.get("metric_id"))
            source = source_metrics.get(metric_id)
            if not source:
                findings.append({"surface": surface_name, "metric_id": metric_id, "field": "metric_id", "reason_zh": "核心指标源中不存在该指标"})
                continue
            for field in comparable_fields:
                if metric.get(field) != source.get(field):
                    findings.append(
                        {
                            "surface": surface_name,
                            "metric_id": metric_id,
                            "field": field,
                            "expected": source.get(field),
                            "actual": metric.get(field),
                            "reason_zh": "页面指标链路与核心 read model 不一致",
                        }
                    )
    return findings
