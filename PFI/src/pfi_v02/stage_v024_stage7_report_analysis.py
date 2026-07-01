from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


TARGET_VERSION = "v0.2.4"
SOURCE_PACKAGE_VERSION = "v0.2.3-repair"
REPAIR_LABEL = "PFI v0.2.3 Repair"
STAGE = "Stage 7"
STAGE_NAME = "分析结论与报告中心"
PHASE_ID = "7.1"
PHASE_NAME = "报告结构"
PHASE_7_1_ID = "7.1"
PHASE_7_2_ID = "7.2"
PHASE_7_3_ID = "7.3"
WHOLE_REVIEW_ID = "stage_7_whole_review"
GITHUB_UPLOAD_ID = "stage_7_github_main_upload"

REPORT_IDS = [
    "net_worth_report",
    "cash_report",
    "investment_report",
    "consumption_report",
    "cashflow_report",
    "data_quality_report",
]

REQUIRED_REPORT_FIELDS = [
    "report_id",
    "report_type",
    "title_zh",
    "status",
    "conclusion_zh",
    "formula_zh",
    "parameters",
    "data_range",
    "sample_size",
    "metric_sources",
    "confidence",
    "gaps",
    "anomalies",
    "review_entry",
    "export_fields",
]

EXPORT_FIELDS = [
    "report_id",
    "report_type",
    "title_zh",
    "status",
    "conclusion_zh",
    "formula_zh",
    "parameter_summary_zh",
    "data_range_start",
    "data_range_end",
    "transaction_count",
    "raw_file_count",
    "confidence",
    "gap_count",
    "review_route",
]

REPORT_TYPE_LABELS = {
    "net_worth_report": ("net_worth", "净资产报告"),
    "cash_report": ("cash", "现金报告"),
    "investment_report": ("investment", "投资报告"),
    "consumption_report": ("consumption", "消费报告"),
    "cashflow_report": ("cashflow", "现金流报告"),
    "data_quality_report": ("data_quality", "数据质量报告"),
}


@dataclass(frozen=True)
class V024Stage7GithubUploadContract:
    target_version: str
    source_package_version: str
    repair_label: str
    stage_id: str
    upload_id: str
    review_id: str
    reviewed_phase_ids: list[str]
    validation_commands: list[str]
    stage_7_candidate_complete: bool
    stage_7_review_complete: bool
    stage_7_complete: bool
    github_main_uploaded: bool
    rebased_on_current_origin_main: bool
    remote_main_verification_required: bool
    stage_8_started: bool
    stage_8_allowed_without_user_instruction: bool
    app_bundle_changes_allowed: bool
    data_logic_changes_allowed: bool
    formal_fake_financial_data_allowed: bool
    max_phases_per_run: int
    explicitly_not_done: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def build_v024_stage7_github_upload_contract() -> V024Stage7GithubUploadContract:
    return V024Stage7GithubUploadContract(
        target_version=TARGET_VERSION,
        source_package_version=SOURCE_PACKAGE_VERSION,
        repair_label=REPAIR_LABEL,
        stage_id=STAGE,
        upload_id=GITHUB_UPLOAD_ID,
        review_id=WHOLE_REVIEW_ID,
        reviewed_phase_ids=[PHASE_7_1_ID, PHASE_7_2_ID, PHASE_7_3_ID],
        validation_commands=[
            "git fetch origin main",
            "git rebase origin/main",
            "pytest stage7 github upload contract",
            "pytest stage7 whole review and phase regression",
            "node stage7 phase73 browser validation",
            "pytest stage6 adjacent regression",
            "node --check PFI/web/app/pages/reports.js",
            "node --check PFI/web/app/shell.js",
            "node --check PFI/scripts/validate_v024_stage7_phase73_report_acceptance.js",
            "python3 -m py_compile PFI/src/pfi_v02/stage_v024_stage7_report_analysis.py",
            "python3 -m py_compile PFI/src/pfi_os/app/streamlit_app.py",
            "python3 -m json.tool stage7 upload/whole/phase evidence",
            "test -s PFI/reports/pfi_v024/stage_7/phase_7_3/formula_visibility.png",
            "git diff --check -- PFI",
            "git push origin HEAD:main",
            "git ls-remote origin refs/heads/main",
        ],
        stage_7_candidate_complete=True,
        stage_7_review_complete=True,
        stage_7_complete=True,
        github_main_uploaded=True,
        rebased_on_current_origin_main=True,
        remote_main_verification_required=True,
        stage_8_started=False,
        stage_8_allowed_without_user_instruction=False,
        app_bundle_changes_allowed=False,
        data_logic_changes_allowed=False,
        formal_fake_financial_data_allowed=False,
        max_phases_per_run=1,
        explicitly_not_done=[
            "Stage 8",
            "app bundle reinstall",
            "launcher C or Info.plist changes",
            "financial data or metric logic changes",
        ],
    )


@dataclass(frozen=True)
class V024Stage7Phase71Contract:
    target_version: str
    source_package_version: str
    repair_label: str
    stage: str
    stage_name: str
    phase_id: str
    phase_name: str
    current_phase_only: bool
    max_one_phase_per_run: bool
    task_ids: list[str]
    report_ids: list[str]
    required_report_fields: list[str]
    export_fields: list[str]
    data_insufficient_blocks_financial_conclusion: bool
    allowed_files: list[str]
    validation_commands: list[str]
    evidence_files: list[str]
    phase_7_2_started: bool
    phase_7_3_started: bool
    stage_7_whole_review_complete: bool
    github_main_uploaded: bool
    app_bundle_changes_allowed: bool
    data_logic_changes_allowed: bool
    formal_fake_financial_data_allowed: bool
    explicitly_not_done: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def build_v024_stage7_phase71_contract() -> V024Stage7Phase71Contract:
    return V024Stage7Phase71Contract(
        target_version=TARGET_VERSION,
        source_package_version=SOURCE_PACKAGE_VERSION,
        repair_label=REPAIR_LABEL,
        stage=STAGE,
        stage_name=STAGE_NAME,
        phase_id=PHASE_ID,
        phase_name=PHASE_NAME,
        current_phase_only=True,
        max_one_phase_per_run=True,
        task_ids=["T7.1.1", "T7.1.2", "T7.1.3", "T7.1.4"],
        report_ids=REPORT_IDS,
        required_report_fields=REQUIRED_REPORT_FIELDS,
        export_fields=EXPORT_FIELDS,
        data_insufficient_blocks_financial_conclusion=True,
        allowed_files=[
            "PFI/src/pfi_v02/stage_v024_stage7_report_analysis.py",
            "PFI/tests/test_v024_stage7_phase71_report_schema.py",
            "PFI/docs/pfi_v024/STAGE7_REPORT_ANALYSIS.md",
            "PFI/docs/pfi_v024/RUN_CONTRACT.md",
            "PFI/reports/pfi_v024/stage_7/phase_7_1/*",
            "PFI/README.md",
            "PFI/HANDOFF.md",
            "PFI/CHANGELOG.md",
            "PFI/功能清单.md",
            "PFI/开发记录.md",
            "PFI/模型参数文件.md",
        ],
        validation_commands=[
            "pytest PFI/tests/test_v024_stage7_phase71_report_schema.py -q",
            "pytest PFI/tests/test_v024_stage6_phase61_design_system.py PFI/tests/test_v024_stage6_phase62_motion_feedback.py PFI/tests/test_v024_stage6_phase63_haptics_settings.py -q",
            "python3 -m py_compile PFI/src/pfi_v02/stage_v024_stage7_report_analysis.py",
            "python3 -m json.tool PFI/reports/pfi_v024/stage_7/phase_7_1/evidence.json",
            "python3 -m json.tool PFI/reports/pfi_v024/stage_7/phase_7_1/report_schema.json",
            "python3 -m json.tool PFI/reports/pfi_v024/stage_7/phase_7_1/report_quality_gate.json",
            "git diff --check -- PFI",
        ],
        evidence_files=[
            "PFI/reports/pfi_v024/stage_7/phase_7_1/evidence.json",
            "PFI/reports/pfi_v024/stage_7/phase_7_1/report_schema.json",
            "PFI/reports/pfi_v024/stage_7/phase_7_1/report_quality_gate.json",
            "PFI/reports/pfi_v024/stage_7/phase_7_1/data_quality_report.json",
            "PFI/reports/pfi_v024/stage_7/phase_7_1/terminal.log",
            "PFI/reports/pfi_v024/stage_7/phase_7_1/changed_files.txt",
            "PFI/reports/pfi_v024/stage_7/phase_7_1/risk_and_rollback.md",
        ],
        phase_7_2_started=False,
        phase_7_3_started=False,
        stage_7_whole_review_complete=False,
        github_main_uploaded=False,
        app_bundle_changes_allowed=False,
        data_logic_changes_allowed=False,
        formal_fake_financial_data_allowed=False,
        explicitly_not_done=[
            "Phase 7.2 页面展示",
            "Phase 7.3 验收",
            "Stage 7 whole-stage review",
            "GitHub main upload",
            "app bundle reinstall",
            "financial data mutation or synthesis",
        ],
    )


def build_v024_stage7_phase71_report_pack(
    *,
    read_model_status: Mapping[str, Any],
) -> dict[str, object]:
    source = dict(read_model_status.get("source") or {})
    metrics = {
        str(item.get("metric_id")): dict(item)
        for item in read_model_status.get("core_metric_states", [])
    }
    shared = {
        "data_range": source.get("date_range") or {"start": None, "end": None},
        "sample_size": {
            "transaction_count": int(source.get("record_count") or 0),
            "raw_file_count": int(source.get("raw_file_count") or 0),
            "account_count": 0,
            "holding_count": 0,
        },
        "source_status": source.get("status") or "not_loaded",
        "source_path": _source_path(source),
    }
    reports = [
        _blocked_metric_report(
            report_id="net_worth_report",
            metric_ids=("net_worth_cny", "cash_balance_cny", "investment_market_value_cny"),
            formula_zh="净资产 = 现金余额 + 投资市值 + 其他真实资产 - 真实负债；任一核心输入缺失时阻断。",
            review_route="/reports?tab=data-quality&metric=net_worth_cny",
            metrics=metrics,
            shared=shared,
        ),
        _blocked_metric_report(
            report_id="cash_report",
            metric_ids=("cash_balance_cny",),
            formula_zh="现金余额 = 已挂链账户的真实余额合计；未挂链账户余额 read model 时阻断。",
            review_route="/accounts?tab=reconcile",
            metrics=metrics,
            shared=shared,
        ),
        _blocked_metric_report(
            report_id="investment_report",
            metric_ids=("investment_market_value_cny",),
            formula_zh="投资市值 = 持仓数量 * 最新真实价格 * 有效汇率；持仓市值 read model 缺失时阻断。",
            review_route="/investment?tab=holdings",
            metrics=metrics,
            shared=shared,
        ),
        _consumption_report(metrics=metrics, shared=shared),
        _cashflow_report(metrics=metrics, shared=shared),
        _data_quality_report(metrics=metrics, shared=shared, source=source),
    ]
    return {
        "schema": "PFIV024Stage7Phase71ReportPackV1",
        "target_version": TARGET_VERSION,
        "source_package_version": SOURCE_PACKAGE_VERSION,
        "stage": STAGE,
        "phase_id": PHASE_ID,
        "contract_version": "PFI-V024-STAGE7-PHASE71-REPORT-SCHEMA",
        "source": {
            "status": source.get("status"),
            "record_count": int(source.get("record_count") or 0),
            "raw_file_count": int(source.get("raw_file_count") or 0),
            "date_range": source.get("date_range") or {"start": None, "end": None},
            "as_of": source.get("as_of"),
            "evidence_hash": source.get("evidence_hash"),
        },
        "read_model_hash": read_model_status.get("read_model_hash"),
        "report_ids": REPORT_IDS,
        "required_report_fields": REQUIRED_REPORT_FIELDS,
        "export_fields": EXPORT_FIELDS,
        "reports": reports,
        "phase_7_2_started": False,
        "phase_7_3_started": False,
        "stage_7_whole_review_complete": False,
    }


def validate_v024_stage7_phase71_report_pack(report_pack: Mapping[str, Any]) -> dict[str, object]:
    reports = [dict(item) for item in report_pack.get("reports", [])]
    missing_report_ids = sorted(set(REPORT_IDS) - {str(item.get("report_id")) for item in reports})
    reports_missing_fields = []
    ai_paragraph_report_ids = []
    financial_conclusion_when_blocked = []
    forbidden_source_terms = []
    data_quality_report_generated = False

    for report in reports:
        report_id = str(report.get("report_id"))
        missing_fields = sorted(set(REQUIRED_REPORT_FIELDS) - set(report))
        if missing_fields:
            reports_missing_fields.append({"report_id": report_id, "missing_fields": missing_fields})
        if report_id == "data_quality_report" and report.get("status") in {"ready", "partial"}:
            data_quality_report_generated = True
        conclusion = str(report.get("conclusion_zh") or "")
        if "AI 总结" in conclusion or _looks_like_paragraph_only(report):
            ai_paragraph_report_ids.append(report_id)
        if report.get("status") == "blocked" and "完整财务结论" in conclusion:
            financial_conclusion_when_blocked.append(report_id)
        for source in report.get("metric_sources", []):
            source_text = str(source).lower()
            for term in ("mock", "sample", "synthetic", "fixture", "demo", "fake"):
                if term in source_text:
                    forbidden_source_terms.append(str(source))

    failures = []
    if missing_report_ids:
        failures.append("missing_report_ids")
    if reports_missing_fields:
        failures.append("reports_missing_fields")
    if not data_quality_report_generated:
        failures.append("missing_data_quality_report")
    if ai_paragraph_report_ids:
        failures.append("ai_paragraph_report")
    if financial_conclusion_when_blocked:
        failures.append("financial_conclusion_when_blocked")
    if forbidden_source_terms:
        failures.append("forbidden_source_terms")

    return {
        "schema": "PFIV024Stage7Phase71QualityGateV1",
        "target_version": TARGET_VERSION,
        "stage": STAGE,
        "phase_id": PHASE_ID,
        "status": "fail" if failures else "pass",
        "report_count": len(reports),
        "required_report_count": len(REPORT_IDS),
        "missing_report_ids": missing_report_ids,
        "reports_missing_fields": reports_missing_fields,
        "data_quality_report_generated": data_quality_report_generated,
        "ai_paragraph_report_ids": ai_paragraph_report_ids,
        "financial_conclusion_when_blocked": financial_conclusion_when_blocked,
        "forbidden_source_terms": sorted(set(forbidden_source_terms)),
        "failures": failures,
    }


def _blocked_metric_report(
    *,
    report_id: str,
    metric_ids: tuple[str, ...],
    formula_zh: str,
    review_route: str,
    metrics: Mapping[str, Mapping[str, Any]],
    shared: Mapping[str, Any],
) -> dict[str, object]:
    report_type, title_zh = REPORT_TYPE_LABELS[report_id]
    selected = [dict(metrics.get(metric_id) or {"metric_id": metric_id, "status": "source_missing"}) for metric_id in metric_ids]
    gaps = [_gap_from_metric(item, review_route) for item in selected if item.get("status") != "ready"]
    status = "blocked" if gaps else "ready"
    if status == "blocked":
        conclusion = f"{title_zh}缺少真实输入，当前只输出缺口与复核入口，不输出最终结论。"
    else:
        conclusion = f"{title_zh}输入已就绪，可进入后续页面展示。"
    return _report(
        report_id=report_id,
        report_type=report_type,
        title_zh=title_zh,
        status=status,
        conclusion_zh=conclusion,
        formula_zh=formula_zh,
        parameters=[
            _parameter("currency", "计价货币", "CNY", "Stage 4 read model status", False),
            _parameter("blocking_policy", "阻断策略", "缺少真实输入时不补零", "v0.2.4 Stage 7.1", False),
        ],
        metric_sources=[str(item.get("source_id") or "source_missing") for item in selected],
        confidence=None if gaps else _min_confidence(selected),
        gaps=gaps,
        anomalies=[],
        review_route=review_route,
        shared=shared,
    )


def _consumption_report(*, metrics: Mapping[str, Mapping[str, Any]], shared: Mapping[str, Any]) -> dict[str, object]:
    metric = dict(metrics.get("consumption_outflow_cny") or {})
    ready = metric.get("status") == "ready"
    gaps = [] if ready else [_gap_from_metric(metric or {"metric_id": "consumption_outflow_cny"}, "/consumption?tab=review")]
    conclusion = (
        "真实流水消费总流出已加载，当前形成消费报告的部分结构；缺少细分解释时不补造明细。"
        if ready
        else "消费报告缺少真实流水输入，当前只输出缺口与复核入口。"
    )
    return _report(
        report_id="consumption_report",
        report_type="consumption",
        title_zh="消费报告",
        status="partial" if ready else "blocked",
        conclusion_zh=conclusion,
        formula_zh="消费总流出 = 生活消费 + 投资入金 + 基金申购 + 黄金申购 + 投资买入 + 金融费用 - 退款抵消。",
        parameters=[
            _parameter("currency", "计价货币", "CNY", "Stage 4 read model status", False),
            _parameter("consumption_scope", "消费口径", "双消费口径，区分消费总流出与生活消费", "v0.2.4 Stage 4", False),
        ],
        metric_sources=[str(metric.get("source_id") or shared["source_path"])],
        confidence=metric.get("confidence"),
        gaps=gaps,
        anomalies=[],
        review_route="/consumption?tab=analysis",
        shared=shared,
    )


def _cashflow_report(*, metrics: Mapping[str, Mapping[str, Any]], shared: Mapping[str, Any]) -> dict[str, object]:
    cash = dict(metrics.get("cash_balance_cny") or {})
    gaps = [
        _gap_from_metric(cash or {"metric_id": "cash_balance_cny"}, "/accounts?tab=reconcile"),
        {
            "metric_id": "planned_cashflow_events",
            "status": "source_missing",
            "reason_zh": "尚未挂链真实计划现金流事件，现金流报告不得生成预测结论。",
            "review_route": "/reports?tab=data-quality&metric=planned_cashflow_events",
        },
    ]
    return _report(
        report_id="cashflow_report",
        report_type="cashflow",
        title_zh="现金流报告",
        status="blocked",
        conclusion_zh="现金流报告缺少现金余额与计划事件真实输入，当前只输出缺口与复核入口。",
        formula_zh="现金流窗口 = 期初现金 + 已确认流入 - 已确认流出 + 真实计划事件；缺少现金或计划事件时阻断。",
        parameters=[
            _parameter("currency", "计价货币", "CNY", "Stage 4 read model status", False),
            _parameter("window_policy", "窗口策略", "后续阶段只展示有真实输入的现金流窗口", "v0.2.4 Stage 7.1", False),
        ],
        metric_sources=[str(cash.get("source_id") or "read_model:cashflow"), "planned_cashflow_events"],
        confidence=None,
        gaps=gaps,
        anomalies=[],
        review_route="/reports?tab=data-quality&metric=cashflow",
        shared=shared,
    )


def _data_quality_report(
    *,
    metrics: Mapping[str, Mapping[str, Any]],
    shared: Mapping[str, Any],
    source: Mapping[str, Any],
) -> dict[str, object]:
    blocked = [dict(item) for item in metrics.values() if item.get("status") not in {"ready", "confirmed_zero"}]
    gaps = [_gap_from_metric(item, "/reports?tab=data-quality") for item in blocked]
    conclusion = (
        f"真实 MetaDatabase/PFI 已加载 {int(source.get('record_count') or 0)} 条记录，"
        f"仍有 {len(gaps)} 个核心指标缺少 read model，先生成数据质量报告。"
    )
    return _report(
        report_id="data_quality_report",
        report_type="data_quality",
        title_zh="数据质量报告",
        status="ready",
        conclusion_zh=conclusion,
        formula_zh="数据质量 = 真实数据源状态 + 核心指标阻断数量 + 缺口复核入口；阻断项清零前不输出完整财务分析。",
        parameters=[
            _parameter("source_status", "数据源状态", str(source.get("status") or "not_loaded"), "Stage 4 read model status", False),
            _parameter("blocked_metric_count", "阻断指标数量", len(gaps), "Stage 4 read model status", False),
        ],
        metric_sources=[str(shared["source_path"])],
        confidence=0.9 if source.get("status") == "ready" else None,
        gaps=gaps,
        anomalies=[],
        review_route="/reports?tab=data-quality",
        shared=shared,
    )


def _report(
    *,
    report_id: str,
    report_type: str,
    title_zh: str,
    status: str,
    conclusion_zh: str,
    formula_zh: str,
    parameters: list[dict[str, object]],
    metric_sources: list[str],
    confidence: object,
    gaps: list[dict[str, object]],
    anomalies: list[dict[str, object]],
    review_route: str,
    shared: Mapping[str, Any],
) -> dict[str, object]:
    return {
        "report_id": report_id,
        "report_type": report_type,
        "title_zh": title_zh,
        "status": status,
        "conclusion_zh": conclusion_zh,
        "formula_zh": formula_zh,
        "parameters": parameters,
        "data_range": dict(shared["data_range"]),
        "sample_size": dict(shared["sample_size"]),
        "metric_sources": metric_sources,
        "confidence": confidence,
        "gaps": gaps,
        "anomalies": anomalies,
        "review_entry": {
            "label_zh": "查看数据缺口与复核入口",
            "route": review_route,
        },
        "export_fields": EXPORT_FIELDS,
    }


def _gap_from_metric(metric: Mapping[str, Any], route: str) -> dict[str, object]:
    return {
        "metric_id": str(metric.get("metric_id") or "unknown_metric"),
        "status": str(metric.get("status") or "source_missing"),
        "reason_zh": str(metric.get("blocking_reason_zh") or "真实输入缺失，报告阻断。"),
        "review_route": route,
    }


def _parameter(
    parameter_id: str,
    label_zh: str,
    value: object,
    source: str,
    adjustable: bool,
) -> dict[str, object]:
    return {
        "parameter_id": parameter_id,
        "label_zh": label_zh,
        "value": value,
        "source": source,
        "adjustable": adjustable,
    }


def _min_confidence(metrics: list[Mapping[str, Any]]) -> object:
    values = [item.get("confidence") for item in metrics if item.get("confidence") is not None]
    return min(values) if values else None


def _source_path(source: Mapping[str, Any]) -> str:
    return str(source.get("transactions_path") or source.get("manifest_path") or "MetaDatabase/PFI")


def _looks_like_paragraph_only(report: Mapping[str, Any]) -> bool:
    conclusion = str(report.get("conclusion_zh") or "")
    has_formula = bool(str(report.get("formula_zh") or "").strip())
    has_parameters = bool(report.get("parameters"))
    has_sample_size = bool(report.get("sample_size"))
    return len(conclusion) > 80 and not (has_formula and has_parameters and has_sample_size)
