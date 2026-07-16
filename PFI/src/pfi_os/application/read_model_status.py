from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pfi_v02.stage_v023_core_metrics import build_stage6_core_metrics_read_model
from pfi_v02.stage_v023_read_model import build_stage6_read_model_audit
from pfi_v02.stage_v024_stage4_data_state import build_v024_metric_state


TARGET_VERSION = "v0.2.4"
SOURCE_PACKAGE_VERSION = "v0.2.3-repair"
STAGE_ID = "Stage 4"
PHASE_ID = "4.2"
PHASE_NAME = "read model 挂链"
CONTRACT_VERSION = "PFI-V024-STAGE4-PHASE42-READ-MODEL-STATUS"
SHARED_SURFACES = ("home", "accounts", "investment", "consumption", "insights")
CORE_METRIC_IDS = (
    "net_worth_cny",
    "cash_balance_cny",
    "investment_market_value_cny",
    "consumption_outflow_cny",
    "report_summary_status",
)

_V023_TO_V024_STATUS = {
    "ready": "ready",
    "confirmed_zero": "confirmed_zero",
    "not_loaded": "not_loaded",
    "not_mounted": "source_missing",
    "path_error": "path_error",
    "permission_error": "permission_denied",
    "parse_error": "parse_failed",
    "outdated": "outdated_snapshot",
    "filter_empty": "filtered_empty",
    "calculation_error": "calculation_failed",
    "review_required": "calculation_failed",
}


@dataclass(frozen=True)
class V024Stage4Phase42Contract:
    target_version: str
    source_package_version: str
    stage_id: str
    phase_id: str
    phase_name: str
    contract_version: str
    current_phase_only: bool
    max_phases_per_run: int
    read_model_wiring_done: bool
    ui_core_cards_wiring_done: bool
    phase_4_3_started: bool
    stage_4_whole_review_complete: bool
    github_main_uploaded: bool
    shared_surfaces: list[str]
    allowed_files: list[str]
    validation_commands: list[str]
    evidence_files: list[str]
    explicitly_not_done: list[str]


def build_v024_stage4_phase42_contract() -> dict[str, Any]:
    contract = V024Stage4Phase42Contract(
        target_version=TARGET_VERSION,
        source_package_version=SOURCE_PACKAGE_VERSION,
        stage_id=STAGE_ID,
        phase_id=PHASE_ID,
        phase_name=PHASE_NAME,
        contract_version=CONTRACT_VERSION,
        current_phase_only=True,
        max_phases_per_run=1,
        read_model_wiring_done=True,
        ui_core_cards_wiring_done=True,
        phase_4_3_started=False,
        stage_4_whole_review_complete=False,
        github_main_uploaded=False,
        shared_surfaces=list(SHARED_SURFACES),
        allowed_files=[
            "PFI/src/pfi_os/application/read_model_status.py",
            "PFI/src/pfi_v02/stage_v021_runtime_api.py",
            "PFI/web/app/data_state.js",
            "PFI/web/app/shell.js",
            "PFI/web/index.html",
            "PFI/src/pfi_os/app/streamlit_app.py",
            "PFI/tests/test_v024_stage4_phase42_read_model_link.py",
            "PFI/docs/pfi_v024/STAGE4_DATA_STATE_MACHINE.md",
            "PFI/reports/pfi_v024/stage_4/phase_4_2/*",
            "PFI/README.md",
            "PFI/HANDOFF.md",
            "PFI/CHANGELOG.md",
            "PFI/功能清单.md",
            "PFI/开发记录.md",
            "PFI/模型参数文件.md",
        ],
        validation_commands=[
            "/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --check PFI/web/app/data_state.js",
            "/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --check PFI/web/app/shell.js",
            "python3 -m py_compile PFI/src/pfi_os/application/read_model_status.py PFI/src/pfi_v02/stage_v021_runtime_api.py PFI/tests/test_v024_stage4_phase42_read_model_link.py",
            "pytest PFI/tests/test_v024_stage4_phase42_read_model_link.py PFI/tests/test_v024_stage4_phase41_data_state_contract.py PFI/tests/test_v024_stage4_no_mock_financial_data.py -q",
            "python3 -m json.tool PFI/reports/pfi_v024/stage_4/phase_4_2/evidence.json",
            "git diff --check -- PFI",
        ],
        evidence_files=[
            "PFI/reports/pfi_v024/stage_4/phase_4_2/data_source_scan.json",
            "PFI/reports/pfi_v024/stage_4/phase_4_2/read_model_status.json",
            "PFI/reports/pfi_v024/stage_4/phase_4_2/core_metric_states.json",
            "PFI/reports/pfi_v024/stage_4/phase_4_2/page_metric_states.json",
            "PFI/reports/pfi_v024/stage_4/phase_4_2/evidence.json",
            "PFI/reports/pfi_v024/stage_4/phase_4_2/terminal.log",
            "PFI/reports/pfi_v024/stage_4/phase_4_2/changed_files.txt",
            "PFI/reports/pfi_v024/stage_4/phase_4_2/risk_and_rollback.md",
        ],
        explicitly_not_done=[
            "Stage 4 Phase 4.3 验收",
            "Stage 4 whole-stage review",
            "GitHub main upload",
            "app bundle reinstall",
            "financial data mutation or synthesis",
        ],
    )
    return asdict(contract)


def build_v024_data_source_scan(
    project_root: str | Path | None = None,
    *,
    data_root: str | Path | None = None,
) -> dict[str, Any]:
    audit = build_stage6_read_model_audit(project_root=project_root, data_root=data_root)
    return {
        "schema": "PFIV024Stage4DataSourceScanV1",
        "target_version": TARGET_VERSION,
        "source_package_version": SOURCE_PACKAGE_VERSION,
        "stage": STAGE_ID,
        "phase_id": PHASE_ID,
        "status": _map_status(audit.get("status")),
        "source_type": audit.get("source_type"),
        "storage_mode": audit.get("storage_mode"),
        "data_root": audit.get("data_root"),
        "transactions_path": audit.get("transactions_path"),
        "manifest_path": audit.get("manifest_path"),
        "raw_file_count": int(audit.get("raw_file_count") or 0),
        "record_count": int(audit.get("transaction_count") or 0),
        "date_range": audit.get("date_range") or {"start": None, "end": None},
        "as_of": audit.get("as_of"),
        "evidence_hash": audit.get("evidence_hash"),
        "blocking_reason_zh": _source_message(audit),
        "generated_at_utc": _utc_now(),
    }


def build_v024_read_model_status(
    project_root: str | Path | None = None,
    *,
    data_root: str | Path | None = None,
) -> dict[str, Any]:
    scan = build_v024_data_source_scan(project_root=project_root, data_root=data_root)
    v023_model = build_stage6_core_metrics_read_model(project_root=project_root, data_root=data_root)
    metrics = _build_core_metric_states(scan, v023_model)
    read_model_hash = _hash_payload({"source": scan, "metrics": metrics, "phase_id": PHASE_ID})
    stage5_financial_model = _build_stage5_financial_model(project_root)
    return {
        "schema": "PFIV024Stage4ReadModelStatusV1",
        "target_version": TARGET_VERSION,
        "source_package_version": SOURCE_PACKAGE_VERSION,
        "stage": STAGE_ID,
        "phase_id": PHASE_ID,
        "contract_version": CONTRACT_VERSION,
        "source": {
            "type": scan["source_type"],
            "status": scan["status"],
            "storage_mode": scan["storage_mode"],
            "data_root": scan["data_root"],
            "transactions_path": scan["transactions_path"],
            "manifest_path": scan["manifest_path"],
            "record_count": scan["record_count"],
            "raw_file_count": scan["raw_file_count"],
            "date_range": scan["date_range"],
            "as_of": scan["as_of"],
            "evidence_hash": scan["evidence_hash"],
            "blocking_reason_zh": scan["blocking_reason_zh"],
        },
        "as_of": scan["as_of"],
        "read_model_hash": read_model_hash,
        "core_metric_states": metrics,
        "stage5_financial_model": stage5_financial_model,
        "blocked_metric_ids": [
            metric["metric_id"]
            for metric in metrics
            if metric["status"] not in {"ready", "confirmed_zero"}
        ],
        "surface_ids": list(SHARED_SURFACES),
        "generated_at_utc": _utc_now(),
    }


def _build_stage5_financial_model(project_root: str | Path | None) -> dict[str, Any]:
    from pfi_os.application.metrics.model_validation import build_stage5_private_surface_payload

    pfi_root = (
        Path(project_root).expanduser().resolve()
        if project_root is not None
        else Path(__file__).resolve().parents[3]
    )
    try:
        return build_stage5_private_surface_payload(pfi_root)
    except Exception as exc:
        return {
            "schema": "PFIV025Stage5PrivateFinancialSurfaceV1",
            "version": "v0.2.5",
            "stage": 5,
            "status": "blocked_runtime_validation_failed",
            "components": [],
            "surface_ids": ["homepage", "consumption_page", "report"],
            "actual_ui_render_binding_completed": False,
            "actual_report_render_binding_completed": False,
            "financial_fixture_fallback_used": False,
            "private_runtime_only": True,
            "persist_to_tracked_evidence_allowed": False,
            "blocking_reason_code": type(exc).__name__,
        }


def build_v024_surface_state_views(read_model_status: dict[str, Any]) -> dict[str, Any]:
    metrics = [dict(metric) for metric in read_model_status.get("core_metric_states", [])]
    surfaces = {
        surface_id: {
            "surface": surface_id,
            "read_model_hash": read_model_status.get("read_model_hash"),
            "as_of": read_model_status.get("as_of"),
            "metrics": [dict(metric) for metric in metrics],
        }
        for surface_id in SHARED_SURFACES
    }
    return {
        "schema": "PFIV024Stage4SurfaceStateViewsV1",
        "target_version": TARGET_VERSION,
        "stage": STAGE_ID,
        "phase_id": PHASE_ID,
        "surfaces": surfaces,
    }


def _build_core_metric_states(scan: dict[str, Any], v023_model: dict[str, Any]) -> list[dict[str, Any]]:
    v023_metrics = {str(metric.get("metric_id")): metric for metric in v023_model.get("core_metrics", [])}
    source_missing_metrics = [
        ("net_worth_cny", "net_worth_v1", "read_model:accounts_holdings", "未挂链账户余额与持仓 read model，无法计算净资产"),
        ("cash_balance_cny", "cash_balance_v1", "read_model:accounts", "未挂链账户余额 read model，无法计算现金余额"),
        ("investment_market_value_cny", "investment_market_value_v1", "read_model:holdings", "未挂链持仓市值 read model，无法计算投资市值"),
    ]
    metrics = [
        build_v024_metric_state(
            metric_id,
            status="source_missing",
            source_id=source_id,
            record_count=None,
            as_of=None,
            formula_id=formula_id,
            confidence=None,
            blocking_reason_zh=message,
            calculation_state="blocked_by_missing_source",
        )
        for metric_id, formula_id, source_id, message in source_missing_metrics
    ]
    metrics.append(_consumption_metric(scan, v023_metrics.get("total_consumption_outflow_cny")))
    metrics.append(_report_summary_metric(scan, metrics))
    return metrics


def _consumption_metric(scan: dict[str, Any], source_metric: dict[str, Any] | None) -> dict[str, Any]:
    status = _map_status(source_metric.get("status") if source_metric else scan.get("status"))
    if status == "ready" and source_metric and source_metric.get("value") is not None:
        return build_v024_metric_state(
            "consumption_outflow_cny",
            status="ready",
            value=source_metric["value"],
            currency="CNY",
            source_id=str(source_metric.get("source") or scan.get("transactions_path") or "MetaDatabase/PFI"),
            record_count=int(scan.get("record_count") or 0),
            as_of=str(source_metric.get("as_of") or scan.get("as_of")),
            formula_id="total_consumption_outflow_v1",
            confidence=0.98,
            blocking_reason_zh="真实流水消费总流出已加载",
            calculation_state="calculated",
        )
    return build_v024_metric_state(
        "consumption_outflow_cny",
        status=status,
        value=None,
        currency="CNY",
        source_id=str(scan.get("transactions_path") or "MetaDatabase/PFI"),
        record_count=int(scan.get("record_count") or 0) if scan.get("record_count") else None,
        as_of=scan.get("as_of"),
        formula_id="total_consumption_outflow_v1",
        confidence=None,
        blocking_reason_zh=str(scan.get("blocking_reason_zh") or "消费流水状态不可用"),
        calculation_state="blocked",
    )


def _report_summary_metric(scan: dict[str, Any], metrics: list[dict[str, Any]]) -> dict[str, Any]:
    blocked = [metric["metric_id"] for metric in metrics if metric["status"] not in {"ready", "confirmed_zero"}]
    if scan.get("status") == "ready":
        return build_v024_metric_state(
            "report_summary_status",
            status="ready",
            value=None,
            currency=None,
            source_id=str(scan.get("manifest_path") or "MetaDatabase/PFI"),
            record_count=int(scan.get("record_count") or 0),
            as_of=str(scan.get("as_of")),
            formula_id="report_summary_status_v1",
            confidence=0.9,
            blocking_reason_zh=f"真实数据源已加载，仍有 {len(blocked)} 个核心指标等待 read model 挂链",
            calculation_state="partially_ready" if blocked else "calculated",
        )
    return build_v024_metric_state(
        "report_summary_status",
        status=scan.get("status") or "not_loaded",
        value=None,
        currency=None,
        source_id=str(scan.get("manifest_path") or "MetaDatabase/PFI"),
        record_count=None,
        as_of=None,
        formula_id="report_summary_status_v1",
        confidence=None,
        blocking_reason_zh=str(scan.get("blocking_reason_zh") or "报告状态不可用"),
        calculation_state="blocked",
    )


def _map_status(status: Any) -> str:
    return _V023_TO_V024_STATUS.get(str(status or "not_loaded"), "calculation_failed")


def _source_message(audit: dict[str, Any]) -> str:
    status = _map_status(audit.get("status"))
    if status == "ready":
        return "真实 MetaDatabase/PFI 数据已加载"
    return str(audit.get("message_zh") or "真实数据状态不可用")


def _hash_payload(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
