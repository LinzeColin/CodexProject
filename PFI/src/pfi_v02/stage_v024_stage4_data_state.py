from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable


TARGET_VERSION = "v0.2.4"
SOURCE_PACKAGE_VERSION = "v0.2.3-repair"
REPAIR_LABEL = "PFI v0.2.3 Repair"
STAGE_ID = "Stage 4"
PHASE_4_1_ID = "4.1"
PHASE_4_1_NAME = "状态机定义"
DATA_STATE_CONTRACT_VERSION = "PFI-V024-STAGE4-PHASE41-DATA-STATE"

METRIC_DATA_STATUSES = (
    "ready",
    "confirmed_zero",
    "not_loaded",
    "source_missing",
    "path_error",
    "parse_failed",
    "outdated_snapshot",
    "permission_denied",
    "calculation_failed",
    "filtered_empty",
)

REQUIRED_METRIC_FIELDS = (
    "metric_id",
    "value",
    "currency",
    "status",
    "source_id",
    "record_count",
    "as_of",
    "formula_id",
    "confidence",
    "blocking_reason_zh",
    "calculation_state",
)

DISPLAY_VALUE_STATUSES = ("ready", "confirmed_zero")
FINANCIAL_DATA_FORBIDDEN_TERMS = ("mock", "sample", "synthetic", "fixture", "demo", "fake")
POLICY_FILE_NAMES = {
    "DATA_TRUST_RULES.md",
    "DATA_TRUST_SPEC.md",
    "HISTORY_DEPRECATION_POLICY.md",
    "TASK_PACK.md",
    "ROADMAP_COPY.md",
    "STAGE4_DATA_STATE_MACHINE.md",
}

BLOCKING_REASON_ZH = {
    "ready": "真实数据已加载",
    "confirmed_zero": "真实数据确认数值为零",
    "not_loaded": "未加载真实数据",
    "source_missing": "真实数据源未挂链",
    "path_error": "数据路径错误，请检查本机数据目录",
    "parse_failed": "解析失败，请检查文件、行或字段",
    "outdated_snapshot": "快照过期，请刷新或确认日期",
    "permission_denied": "权限失败，请检查本机文件权限",
    "calculation_failed": "计算失败，请查看公式和输入字段",
    "filtered_empty": "当前筛选无结果，不代表全局为零",
}

CORE_METRIC_IDS = (
    "net_worth_cny",
    "cash_balance_cny",
    "investment_market_value_cny",
    "consumption_outflow_cny",
    "report_summary_status",
)


@dataclass(frozen=True)
class V024Stage4Phase41Contract:
    target_version: str
    source_package_version: str
    repair_label: str
    stage_id: str
    phase_id: str
    phase_name: str
    data_state_contract_version: str
    current_phase_only: bool
    max_phases_per_run: int
    no_mock_financial_data: bool
    financial_data_forbidden_terms: list[str]
    statuses: list[str]
    required_metric_fields: list[str]
    display_value_statuses: list[str]
    core_metric_ids: list[str]
    read_model_wiring_done: bool
    ui_core_cards_wiring_done: bool
    github_main_uploaded: bool
    allowed_files: list[str]
    validation_commands: list[str]
    evidence_files: list[str]
    explicitly_not_done: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def build_v024_stage4_phase41_contract() -> V024Stage4Phase41Contract:
    return V024Stage4Phase41Contract(
        target_version=TARGET_VERSION,
        source_package_version=SOURCE_PACKAGE_VERSION,
        repair_label=REPAIR_LABEL,
        stage_id=STAGE_ID,
        phase_id=PHASE_4_1_ID,
        phase_name=PHASE_4_1_NAME,
        data_state_contract_version=DATA_STATE_CONTRACT_VERSION,
        current_phase_only=True,
        max_phases_per_run=1,
        no_mock_financial_data=True,
        financial_data_forbidden_terms=list(FINANCIAL_DATA_FORBIDDEN_TERMS),
        statuses=list(METRIC_DATA_STATUSES),
        required_metric_fields=list(REQUIRED_METRIC_FIELDS),
        display_value_statuses=list(DISPLAY_VALUE_STATUSES),
        core_metric_ids=list(CORE_METRIC_IDS),
        read_model_wiring_done=False,
        ui_core_cards_wiring_done=False,
        github_main_uploaded=False,
        allowed_files=[
            "PFI/src/pfi_v02/stage_v024_stage4_data_state.py",
            "PFI/web/app/data_state.js",
            "PFI/tests/test_v024_stage4_phase41_data_state_contract.py",
            "PFI/tests/test_v024_stage4_no_mock_financial_data.py",
            "PFI/docs/pfi_v024/STAGE4_DATA_STATE_MACHINE.md",
            "PFI/reports/pfi_v024/stage_4/phase_4_1/*",
            "PFI/README.md",
            "PFI/HANDOFF.md",
            "PFI/CHANGELOG.md",
            "PFI/功能清单.md",
            "PFI/开发记录.md",
            "PFI/模型参数文件.md",
        ],
        validation_commands=[
            "/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --check PFI/web/app/data_state.js",
            "python3 -m py_compile PFI/src/pfi_v02/stage_v024_stage4_data_state.py",
            "pytest PFI/tests/test_v024_stage4_phase41_data_state_contract.py PFI/tests/test_v024_stage4_no_mock_financial_data.py -q",
            "python3 -m json.tool PFI/reports/pfi_v024/stage_4/phase_4_1/evidence.json",
            "git diff --check -- PFI",
        ],
        evidence_files=[
            "PFI/reports/pfi_v024/stage_4/phase_4_1/evidence.json",
            "PFI/reports/pfi_v024/stage_4/phase_4_1/terminal.log",
            "PFI/reports/pfi_v024/stage_4/phase_4_1/changed_files.txt",
            "PFI/reports/pfi_v024/stage_4/phase_4_1/risk_and_rollback.md",
        ],
        explicitly_not_done=[
            "Stage 4 Phase 4.2 read model 挂链",
            "Stage 4 Phase 4.3 验收",
            "首页核心卡片挂链",
            "账户/投资/消费/报告共享状态挂链",
            "app bundle reinstall",
            "GitHub main upload",
        ],
    )


def build_v024_blocking_reason_zh() -> dict[str, str]:
    return dict(BLOCKING_REASON_ZH)


def build_v024_metric_state_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "PFI v0.2.4 Stage 4 Metric Data State",
        "type": "object",
        "required": list(REQUIRED_METRIC_FIELDS),
        "properties": {
            "metric_id": {"type": "string"},
            "value": {"type": ["number", "null"]},
            "currency": {"type": ["string", "null"]},
            "status": {"enum": list(METRIC_DATA_STATUSES)},
            "source_id": {"type": ["string", "null"]},
            "record_count": {"type": ["integer", "null"], "minimum": 0},
            "as_of": {"type": ["string", "null"]},
            "formula_id": {"type": ["string", "null"]},
            "confidence": {"type": ["number", "null"], "minimum": 0, "maximum": 1},
            "blocking_reason_zh": {"type": "string"},
            "calculation_state": {"type": "string"},
        },
    }


def build_v024_metric_state(
    metric_id: str,
    *,
    status: str,
    value: float | int | None = None,
    currency: str | None = "CNY",
    source_id: str | None = None,
    record_count: int | None = None,
    as_of: str | None = None,
    formula_id: str | None = None,
    confidence: float | None = None,
    blocking_reason_zh: str | None = None,
    calculation_state: str | None = None,
) -> dict[str, Any]:
    if status not in METRIC_DATA_STATUSES:
        raise ValueError(f"Unsupported metric data status: {status}")
    if status not in DISPLAY_VALUE_STATUSES and value is not None:
        raise ValueError(f"{status} must not carry a financial value")
    if status == "confirmed_zero" and value != 0:
        raise ValueError("confirmed_zero requires value 0")
    if status in DISPLAY_VALUE_STATUSES:
        _require_evidence_chain(status, source_id, record_count, as_of, formula_id, confidence)

    return {
        "metric_id": metric_id,
        "value": value,
        "currency": currency,
        "status": status,
        "source_id": source_id,
        "record_count": record_count,
        "as_of": as_of,
        "formula_id": formula_id,
        "confidence": confidence,
        "blocking_reason_zh": blocking_reason_zh or BLOCKING_REASON_ZH[status],
        "calculation_state": calculation_state or _default_calculation_state(status),
    }


def can_display_v024_financial_value(metric: dict[str, Any]) -> bool:
    return metric.get("status") in DISPLAY_VALUE_STATUSES and metric.get("value") is not None


def render_v024_metric_value_zh(metric: dict[str, Any]) -> str:
    if not can_display_v024_financial_value(metric):
        reason = str(metric.get("blocking_reason_zh") or BLOCKING_REASON_ZH.get(str(metric.get("status")), "数据状态未知"))
        if metric.get("status") == "outdated_snapshot" and metric.get("as_of"):
            return f"{reason}（快照日期：{metric['as_of']}）"
        return reason
    currency = metric.get("currency") or "CNY"
    return f"{currency} {float(metric['value']):,.2f}"


def scan_v024_forbidden_financial_data_terms(paths: Iterable[Path | str]) -> list[dict[str, object]]:
    violations: list[dict[str, object]] = []
    for raw_path in paths:
        path = Path(raw_path)
        if _is_policy_file(path):
            continue
        if not path.exists() or not path.is_file():
            continue
        for line_number, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
            lower = line.lower()
            for term in FINANCIAL_DATA_FORBIDDEN_TERMS:
                if term in lower:
                    violations.append({"path": str(path), "line": line_number, "term": term})
    return violations


def _require_evidence_chain(
    status: str,
    source_id: str | None,
    record_count: int | None,
    as_of: str | None,
    formula_id: str | None,
    confidence: float | None,
) -> None:
    missing = [
        name
        for name, value in (
            ("source_id", source_id),
            ("record_count", record_count),
            ("as_of", as_of),
            ("formula_id", formula_id),
            ("confidence", confidence),
        )
        if value is None
    ]
    if missing:
        raise ValueError(f"{status} requires evidence field(s): {', '.join(missing)}")


def _default_calculation_state(status: str) -> str:
    if status == "ready":
        return "calculated"
    if status == "confirmed_zero":
        return "confirmed"
    return "blocked"


def _is_policy_file(path: Path) -> bool:
    return path.name in POLICY_FILE_NAMES or "/docs/" in str(path)
