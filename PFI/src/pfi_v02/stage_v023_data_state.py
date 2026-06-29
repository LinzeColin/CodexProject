from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable


VERSION = "v0.2.3"
STAGE = "Stage 2"
PHASE_ID = "V023-S2-P2.1"
PHASE_NAME = "数据状态合同"

METRIC_DATA_STATUSES = (
    "ready",
    "confirmed_zero",
    "not_loaded",
    "not_mounted",
    "path_error",
    "permission_error",
    "parse_error",
    "outdated",
    "filter_empty",
    "calculation_error",
    "review_required",
)

REQUIRED_METRIC_FIELDS = (
    "metric_id",
    "label",
    "value",
    "currency",
    "status",
    "source",
    "as_of",
    "evidence_hash",
    "message_zh",
)

DISPLAY_VALUE_STATUSES = ("ready", "confirmed_zero")
FINANCIAL_DATA_FORBIDDEN_TERMS = ("mock", "sample", "synthetic", "fixture", "demo", "fake")
POLICY_FILE_NAMES = {
    "DATA_TRUST_RULES.md",
    "DATA_TRUST_SPEC.md",
    "HISTORY_DEPRECATION_POLICY.md",
    "TASK_PACK.md",
    "ROADMAP_COPY.md",
}

STATUS_COPY_ZH = {
    "ready": "真实数据已加载",
    "confirmed_zero": "真实数据确认数值为零",
    "not_loaded": "未加载真实数据",
    "not_mounted": "真实数据源未挂链",
    "path_error": "数据路径不可用",
    "permission_error": "无权限读取，请检查本机文件权限",
    "parse_error": "解析失败，请检查文件、行或字段",
    "outdated": "使用旧快照，请查看快照日期",
    "filter_empty": "当前筛选无结果",
    "calculation_error": "指标计算失败",
    "review_required": "需要人工复核",
}

CORE_METRICS = (
    ("net_worth_cny", "净资产", "CNY"),
    ("cash_balance_cny", "现金余额", "CNY"),
    ("investment_market_value_cny", "投资市值", "CNY"),
)


@dataclass(frozen=True)
class Stage2Phase21Contract:
    version: str
    stage: str
    phase_id: str
    phase_name: str
    current_phase_only: bool
    max_one_phase_per_run: bool
    taskpack_restored: bool
    no_mock_financial_data: bool
    financial_data_forbidden_terms: tuple[str, ...]
    allowed_files: tuple[str, ...]
    validation_commands: tuple[str, ...]
    evidence_files: tuple[str, ...]
    explicitly_not_done: tuple[str, ...]


@dataclass(frozen=True)
class Stage2Phase23Contract:
    version: str
    stage: str
    phase_id: str
    phase_name: str
    current_phase_only: bool
    max_one_phase_per_run: bool
    no_mock_financial_data: bool
    allowed_files: tuple[str, ...]
    validation_commands: tuple[str, ...]
    evidence_files: tuple[str, ...]
    explicitly_not_done: tuple[str, ...]


def build_stage2_phase21_contract() -> dict[str, Any]:
    contract = Stage2Phase21Contract(
        version=VERSION,
        stage=STAGE,
        phase_id=PHASE_ID,
        phase_name=PHASE_NAME,
        current_phase_only=True,
        max_one_phase_per_run=True,
        taskpack_restored=True,
        no_mock_financial_data=True,
        financial_data_forbidden_terms=FINANCIAL_DATA_FORBIDDEN_TERMS,
        allowed_files=(
            "PFI/src/pfi_v02/stage_v023_data_state.py",
            "PFI/web/app/dataStatus.js",
            "PFI/tests/test_v023_stage2_data_state_machine.py",
            "PFI/tests/test_v023_no_mock_financial_data.py",
            "PFI/docs/pfi_v023/STAGE2_DATA_TRUST.md",
            "PFI/reports/pfi_v023/stage_2/*",
        ),
        validation_commands=(
            "node --check PFI/web/app/dataStatus.js",
            "python3 -m py_compile PFI/src/pfi_v02/stage_v023_data_state.py",
            "python3 -m py_compile PFI/tests/test_v023_stage2_data_state_machine.py PFI/tests/test_v023_no_mock_financial_data.py",
            "python3 -m pytest PFI/tests/test_v023_stage2_data_state_machine.py -q",
            "python3 -m pytest PFI/tests/test_v023_no_mock_financial_data.py -q",
        ),
        evidence_files=(
            "PFI/docs/pfi_v023/STAGE2_DATA_TRUST.md",
            "PFI/reports/pfi_v023/stage_2/phase_2_1/evidence.json",
            "PFI/reports/pfi_v023/stage_2/phase_2_1/terminal.log",
            "PFI/reports/pfi_v023/stage_2/phase_2_1/changed_files.txt",
        ),
        explicitly_not_done=(
            "真实数据源路径审计",
            "文件数/记录数统计",
            "账户/持仓/read model 统计",
            "页面门禁接入",
            "核心指标接入 UI",
            "app bundle reinstall",
            "GitHub main upload for intermediate phase",
        ),
    )
    payload = asdict(contract)
    payload["financial_data_forbidden_terms"] = list(contract.financial_data_forbidden_terms)
    return payload


def build_stage2_phase23_contract() -> dict[str, Any]:
    contract = Stage2Phase23Contract(
        version=VERSION,
        stage=STAGE,
        phase_id="V023-S2-P2.3",
        phase_name="页面门禁",
        current_phase_only=True,
        max_one_phase_per_run=True,
        no_mock_financial_data=True,
        allowed_files=(
            "PFI/src/pfi_v02/stage_v023_data_state.py",
            "PFI/web/app/dataStatus.js",
            "PFI/tests/test_v023_stage2_data_state_machine.py",
            "PFI/tests/test_v023_no_mock_financial_data.py",
            "PFI/docs/pfi_v023/STAGE2_DATA_TRUST.md",
            "PFI/reports/pfi_v023/stage_2/*",
        ),
        validation_commands=(
            "node --check PFI/web/app/dataStatus.js",
            "python3 -m py_compile PFI/src/pfi_v02/stage_v023_data_state.py",
            "python3 -m pytest PFI/tests/test_v023_stage2_data_state_machine.py -q",
            "python3 -m pytest PFI/tests/test_v023_no_mock_financial_data.py -q",
        ),
        evidence_files=(
            "PFI/docs/pfi_v023/STAGE2_DATA_TRUST.md",
            "PFI/reports/pfi_v023/stage_2/phase_2_3/evidence.json",
            "PFI/reports/pfi_v023/stage_2/phase_2_3/terminal.log",
            "PFI/reports/pfi_v023/stage_2/phase_2_3/changed_files.txt",
            "PFI/reports/pfi_v023/stage_2/phase_2_3/browser_validation.json",
            "PFI/reports/pfi_v023/stage_2/phase_2_3/screenshots/data_gate.png",
        ),
        explicitly_not_done=(
            "Stage 3 navigation routes",
            "PFI/web/index.html route wiring",
            "PFI/web/app/shell.js route wiring",
            "app bundle reinstall",
            "GitHub main upload before Stage 2 review",
        ),
    )
    return asdict(contract)


def build_status_copy_zh() -> dict[str, str]:
    return dict(STATUS_COPY_ZH)


def build_metric_data_state_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "PFI v0.2.3 Metric Data State",
        "type": "object",
        "required": list(REQUIRED_METRIC_FIELDS),
        "properties": {
            "metric_id": {"type": "string"},
            "label": {"type": "string"},
            "value": {"type": ["number", "null"]},
            "currency": {"type": ["string", "null"]},
            "status": {"enum": list(METRIC_DATA_STATUSES)},
            "source": {"type": ["string", "null"]},
            "as_of": {"type": ["string", "null"]},
            "evidence_hash": {"type": ["string", "null"]},
            "message_zh": {"type": "string"},
        },
    }


def build_metric_state(
    metric_id: str,
    label: str,
    *,
    status: str,
    value: float | int | None = None,
    currency: str | None = "CNY",
    source: str | None = None,
    as_of: str | None = None,
    evidence_hash: str | None = None,
    message_zh: str | None = None,
) -> dict[str, Any]:
    if status not in METRIC_DATA_STATUSES:
        raise ValueError(f"Unsupported metric data status: {status}")
    if status not in DISPLAY_VALUE_STATUSES and value is not None:
        raise ValueError(f"{status} must not carry a financial value")
    if status == "ready":
        _require_evidence_chain(status, value, source, as_of, evidence_hash)
    if status == "confirmed_zero":
        if value != 0:
            raise ValueError("confirmed_zero requires value 0")
        _require_evidence_chain(status, value, source, as_of, evidence_hash)

    return {
        "metric_id": metric_id,
        "label": label,
        "value": value,
        "currency": currency,
        "status": status,
        "source": source,
        "as_of": as_of,
        "evidence_hash": evidence_hash,
        "message_zh": message_zh or STATUS_COPY_ZH[status],
    }


def build_core_metric_states_not_loaded() -> list[dict[str, Any]]:
    return [
        build_metric_state(metric_id, label, status="not_loaded", currency=currency)
        for metric_id, label, currency in CORE_METRICS
    ]


def can_display_financial_value(metric: dict[str, Any]) -> bool:
    return metric.get("status") in DISPLAY_VALUE_STATUSES and metric.get("value") is not None


def render_metric_value_zh(metric: dict[str, Any]) -> str:
    if not can_display_financial_value(metric):
        message = str(metric.get("message_zh") or STATUS_COPY_ZH.get(str(metric.get("status")), "数据状态未知"))
        if metric.get("status") == "outdated" and metric.get("as_of"):
            return f"{message}（快照日期：{metric['as_of']}）"
        return message
    currency = metric.get("currency") or "CNY"
    return f"{currency} {float(metric['value']):,.2f}"


def scan_forbidden_financial_data_terms(paths: Iterable[str | Path]) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    for raw_path in paths:
        path = Path(raw_path)
        if path.name in POLICY_FILE_NAMES:
            continue
        text = path.read_text(encoding="utf-8")
        for line_number, line in enumerate(text.splitlines(), start=1):
            lower_line = line.lower()
            for term in FINANCIAL_DATA_FORBIDDEN_TERMS:
                if term in lower_line:
                    violations.append(
                        {
                            "path": str(path),
                            "line": line_number,
                            "term": term,
                            "excerpt": line.strip()[:160],
                        }
                    )
    return violations


def _require_evidence_chain(
    status: str,
    value: float | int | None,
    source: str | None,
    as_of: str | None,
    evidence_hash: str | None,
) -> None:
    if value is None:
        raise ValueError(f"{status} requires value")
    missing = [
        name
        for name, item in (
            ("source", source),
            ("as_of", as_of),
            ("evidence_hash", evidence_hash),
        )
        if not item
    ]
    if missing:
        raise ValueError(f"{status} requires evidence chain fields: {', '.join(missing)}")
