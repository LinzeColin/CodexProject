from __future__ import annotations

from dataclasses import asdict, dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from pfi_v02.stage_v024_stage4_data_state import (
    METRIC_DATA_STATUSES,
    build_v024_metric_state,
    render_v024_metric_value_zh,
    scan_v024_forbidden_financial_data_terms,
)


TARGET_VERSION = "v0.2.4"
SOURCE_PACKAGE_VERSION = "v0.2.3-repair"
REPAIR_LABEL = "PFI v0.2.3 Repair"
STAGE = "Stage 9"
STAGE_NAME = "回归防线与交付冻结"
PHASE_9_1_ID = "9.1"
PHASE_9_1_NAME = "回归规则"
PHASE_9_1_TASK_IDS = ["T9.1.1", "T9.1.2", "T9.1.3", "T9.1.4"]
GUARDRAIL_VERSION = "PFI-V024-STAGE9-PHASE91-REGRESSION-GUARDRAILS"

PRIMARY_ENTRY_LABELS = [
    "首页总览",
    "账户与资产",
    "账本流水",
    "投资管理",
    "消费管理",
    "数据源与上传",
    "建议与复盘",
    "报告与洞察",
    "市场与研究",
    "设置",
]

LEGACY_ALIAS_LABELS = ["首页", "市场", "研究", "持仓", "策略实验室", "数据与系统"]

REQUIRED_GUARDRAILS = [
    "old_ui_signature",
    "primary_entry_stack",
    "false_financial_zero",
    "mock_financial_data",
    "mechanical_copy",
    "dark_console_default",
]

OLD_UI_FORBIDDEN_SIGNATURES = [
    "功能面板",
    "PFI 功能入口",
    "功能已准备",
    "进入操作面板",
    "系统能力面板",
    "Task Pack",
    "Prototype",
    "AI console",
    "运行边界",
    "验收边界",
    "安全边界",
]

MECHANICAL_COPY_SCOPED_TERMS = [
    "页面说明",
    "依据",
    "参数",
    "记录链路",
    "反馈控制台",
]

DARK_CONSOLE_FORBIDDEN_DEFAULTS = [
    "dark AI console",
    "暗色 AI 控制台",
    "dark-console-default",
]

RUNTIME_UI_SCAN_FILES = [
    "web/index.html",
    "web/app/shell.js",
]

FORMAL_FINANCIAL_RUNTIME_FILES = [
    "web/app/data_state.js",
]


@dataclass(frozen=True)
class V024Stage9Phase91Contract:
    target_version: str
    source_package_version: str
    repair_label: str
    stage: str
    stage_name: str
    phase_id: str
    phase_name: str
    guardrail_version: str
    current_phase_only: bool
    max_phases_per_run: int
    stage_8_github_main_uploaded_required: bool
    task_ids: list[str]
    required_guardrails: list[str]
    allowed_files: list[str]
    validation_commands: list[str]
    evidence_files: list[str]
    phase_9_2_started: bool
    phase_9_3_started: bool
    stage_9_whole_review_complete: bool
    github_main_uploaded: bool
    app_bundle_changes_allowed: bool
    data_logic_changes_allowed: bool
    formal_fake_financial_data_allowed: bool
    explicitly_not_done: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class V024Stage9Phase91Evaluation:
    schema: str
    target_version: str
    source_package_version: str
    stage: str
    phase_id: str
    guardrail_version: str
    primary_entry_labels: list[str]
    primary_entry_count: int
    mobile_primary_entry_labels: list[str]
    mobile_primary_entry_count: int
    legacy_alias_primary_entry_violations: list[str]
    old_ui_signature_scan_files: list[str]
    old_ui_signature_violations: list[dict[str, object]]
    primary_entry_stack_violations: list[dict[str, object]]
    false_financial_zero_violations: list[dict[str, object]]
    mock_financial_data_scan_files: list[str]
    mock_financial_data_violations: list[dict[str, object]]
    old_ui_signature_test_passed: bool
    primary_entry_stack_test_passed: bool
    false_zero_test_passed: bool
    mock_financial_data_test_passed: bool
    mechanical_copy_guardrail_defined: bool
    dark_console_default_guardrail_defined: bool
    all_guardrails_passed: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def build_v024_stage9_phase91_contract() -> V024Stage9Phase91Contract:
    return V024Stage9Phase91Contract(
        target_version=TARGET_VERSION,
        source_package_version=SOURCE_PACKAGE_VERSION,
        repair_label=REPAIR_LABEL,
        stage=STAGE,
        stage_name=STAGE_NAME,
        phase_id=PHASE_9_1_ID,
        phase_name=PHASE_9_1_NAME,
        guardrail_version=GUARDRAIL_VERSION,
        current_phase_only=True,
        max_phases_per_run=1,
        stage_8_github_main_uploaded_required=True,
        task_ids=PHASE_9_1_TASK_IDS,
        required_guardrails=list(REQUIRED_GUARDRAILS),
        allowed_files=[
            "PFI/src/pfi_v02/stage_v024_stage9_regression_freeze.py",
            "PFI/tests/test_v024_stage9_phase91_regression_guardrails.py",
            "PFI/docs/pfi_v024/STAGE9_REGRESSION_FREEZE.md",
            "PFI/docs/pfi_v024/RUN_CONTRACT.md",
            "PFI/reports/pfi_v024/stage_9/phase_9_1/*",
            "PFI/README.md",
            "PFI/HANDOFF.md",
            "PFI/CHANGELOG.md",
            "PFI/功能清单.md",
            "PFI/开发记录.md",
            "PFI/模型参数文件.md",
        ],
        validation_commands=[
            "python3 -m pytest PFI/tests/test_v024_stage9_phase91_regression_guardrails.py -q",
            "python3 -m pytest PFI/tests/test_v024_stage8_github_upload_contract.py PFI/tests/test_v024_stage8_whole_review_contract.py -q",
            "python3 -m py_compile PFI/src/pfi_v02/stage_v024_stage9_regression_freeze.py",
            "python3 -m json.tool PFI/reports/pfi_v024/stage_9/phase_9_1/evidence.json",
            "python3 -m json.tool PFI/reports/pfi_v024/stage_9/phase_9_1/regression_guardrails.json",
            "git diff --check -- PFI",
        ],
        evidence_files=[
            "PFI/reports/pfi_v024/stage_9/phase_9_1/evidence.json",
            "PFI/reports/pfi_v024/stage_9/phase_9_1/regression_guardrails.json",
            "PFI/reports/pfi_v024/stage_9/phase_9_1/terminal.log",
            "PFI/reports/pfi_v024/stage_9/phase_9_1/changed_files.txt",
            "PFI/reports/pfi_v024/stage_9/phase_9_1/risk_and_rollback.md",
        ],
        phase_9_2_started=False,
        phase_9_3_started=False,
        stage_9_whole_review_complete=False,
        github_main_uploaded=False,
        app_bundle_changes_allowed=False,
        data_logic_changes_allowed=False,
        formal_fake_financial_data_allowed=False,
        explicitly_not_done=[
            "Stage 9 Phase 9.2 delivery freeze",
            "Stage 9 Phase 9.3 user acceptance",
            "Stage 9 whole-stage review",
            "Stage 9 GitHub main upload",
            "app bundle reinstall",
            "financial data mutation or synthesis",
        ],
    )


def evaluate_v024_stage9_phase91_guardrails(root: Path | str) -> V024Stage9Phase91Evaluation:
    pfi_root = Path(root)
    index_path = pfi_root / "web" / "index.html"
    html = index_path.read_text(encoding="utf-8")
    nav = _PrimaryEntryParser()
    nav.feed(html)

    legacy_alias_violations = [label for label in nav.primary_labels if label in LEGACY_ALIAS_LABELS]
    primary_entry_stack_violations = _primary_entry_stack_violations(nav)
    old_ui_signature_violations = _scan_old_ui_signatures(pfi_root)
    false_zero_violations = _false_financial_zero_violations()
    financial_scan_paths = [pfi_root / rel for rel in FORMAL_FINANCIAL_RUNTIME_FILES]
    mock_financial_data_violations = scan_v024_forbidden_financial_data_terms(financial_scan_paths)

    old_ui_passed = not old_ui_signature_violations
    primary_stack_passed = not legacy_alias_violations and not primary_entry_stack_violations
    false_zero_passed = not false_zero_violations
    mock_financial_passed = not mock_financial_data_violations
    mechanical_defined = bool(MECHANICAL_COPY_SCOPED_TERMS)
    dark_defined = bool(DARK_CONSOLE_FORBIDDEN_DEFAULTS)

    return V024Stage9Phase91Evaluation(
        schema="PFIV024Stage9Phase91GuardrailEvaluationV1",
        target_version=TARGET_VERSION,
        source_package_version=SOURCE_PACKAGE_VERSION,
        stage=STAGE,
        phase_id=PHASE_9_1_ID,
        guardrail_version=GUARDRAIL_VERSION,
        primary_entry_labels=list(nav.primary_labels),
        primary_entry_count=len(nav.primary_labels),
        mobile_primary_entry_labels=list(nav.mobile_primary_labels),
        mobile_primary_entry_count=len(nav.mobile_primary_labels),
        legacy_alias_primary_entry_violations=legacy_alias_violations,
        old_ui_signature_scan_files=RUNTIME_UI_SCAN_FILES,
        old_ui_signature_violations=old_ui_signature_violations,
        primary_entry_stack_violations=primary_entry_stack_violations,
        false_financial_zero_violations=false_zero_violations,
        mock_financial_data_scan_files=FORMAL_FINANCIAL_RUNTIME_FILES,
        mock_financial_data_violations=mock_financial_data_violations,
        old_ui_signature_test_passed=old_ui_passed,
        primary_entry_stack_test_passed=primary_stack_passed,
        false_zero_test_passed=false_zero_passed,
        mock_financial_data_test_passed=mock_financial_passed,
        mechanical_copy_guardrail_defined=mechanical_defined,
        dark_console_default_guardrail_defined=dark_defined,
        all_guardrails_passed=all(
            [
                old_ui_passed,
                primary_stack_passed,
                false_zero_passed,
                mock_financial_passed,
                mechanical_defined,
                dark_defined,
            ]
        ),
    )


class _PrimaryEntryParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.primary_labels: list[str] = []
        self.mobile_primary_labels: list[str] = []
        self._current_kind: str | None = None
        self._current_text: list[str] = []
        self._hidden_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {key: value for key, value in attrs}
        if tag == "button" and attr.get("data-primary-entry") == "true":
            self._current_kind = "desktop"
            self._current_text = []
            return
        if tag == "button" and attr.get("data-mobile-primary-entry") == "true":
            self._current_kind = "mobile"
            self._current_text = []
            return
        if self._current_kind and attr.get("aria-hidden") == "true":
            self._hidden_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if self._hidden_depth and tag == "span":
            self._hidden_depth -= 1
            return
        if tag == "button" and self._current_kind:
            label = _compact_label("".join(self._current_text))
            if label:
                if self._current_kind == "desktop":
                    self.primary_labels.append(label)
                else:
                    self.mobile_primary_labels.append(label)
            self._current_kind = None
            self._current_text = []
            self._hidden_depth = 0

    def handle_data(self, data: str) -> None:
        if self._current_kind and not self._hidden_depth:
            self._current_text.append(data)


def _compact_label(value: str) -> str:
    return " ".join(value.split()).strip()


def _primary_entry_stack_violations(nav: _PrimaryEntryParser) -> list[dict[str, object]]:
    violations: list[dict[str, object]] = []
    if nav.primary_labels != PRIMARY_ENTRY_LABELS:
        violations.append(
            {
                "rule": "desktop_primary_entries_equal_10",
                "expected": PRIMARY_ENTRY_LABELS,
                "actual": nav.primary_labels,
            }
        )
    if nav.mobile_primary_labels != PRIMARY_ENTRY_LABELS:
        violations.append(
            {
                "rule": "mobile_primary_entries_equal_10",
                "expected": PRIMARY_ENTRY_LABELS,
                "actual": nav.mobile_primary_labels,
            }
        )
    for label in nav.primary_labels:
        if label in LEGACY_ALIAS_LABELS:
            violations.append({"rule": "legacy_alias_not_primary", "label": label})
    return violations


def _scan_old_ui_signatures(pfi_root: Path) -> list[dict[str, object]]:
    violations: list[dict[str, object]] = []
    for rel_path in RUNTIME_UI_SCAN_FILES:
        path = pfi_root / rel_path
        if not path.exists():
            violations.append({"path": rel_path, "line": None, "term": "missing runtime file"})
            continue
        for line_number, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
            lowered = line.lower()
            for term in OLD_UI_FORBIDDEN_SIGNATURES:
                if term == "Prototype" and "Object.prototype" in line:
                    continue
                if term.lower() in lowered:
                    violations.append({"path": rel_path, "line": line_number, "term": term})
            for term in DARK_CONSOLE_FORBIDDEN_DEFAULTS:
                if term.lower() in lowered:
                    violations.append({"path": rel_path, "line": line_number, "term": term})
    return violations


def _false_financial_zero_violations() -> list[dict[str, object]]:
    violations: list[dict[str, object]] = []
    for status in METRIC_DATA_STATUSES:
        if status in {"ready", "confirmed_zero"}:
            continue
        metric = build_v024_metric_state(f"guardrail_{status}", status=status, value=None)
        rendered = render_v024_metric_value_zh(metric)
        if "0.00" in rendered or "CNY " in rendered:
            violations.append({"status": status, "rendered": rendered})
    try:
        build_v024_metric_state("guardrail_confirmed_zero_without_evidence", status="confirmed_zero", value=0)
    except ValueError:
        pass
    else:
        violations.append({"status": "confirmed_zero", "rendered": "confirmed zero accepted without evidence"})

    confirmed = build_v024_metric_state(
        "guardrail_confirmed_zero_with_evidence",
        status="confirmed_zero",
        value=0,
        source_id="guardrail_real_source",
        record_count=1,
        as_of="2026-07-01",
        formula_id="guardrail_zero_formula",
        confidence=1.0,
    )
    rendered_confirmed = render_v024_metric_value_zh(confirmed)
    if "CNY 0.00" not in rendered_confirmed:
        violations.append({"status": "confirmed_zero", "rendered": rendered_confirmed})
    return violations
