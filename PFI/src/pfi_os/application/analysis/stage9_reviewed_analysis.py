"""Stage 9 whole-review analysis snapshot built from immutable public evidence.

The Phase 9.2 candidate remains immutable.  This module creates a new reviewed
version that binds the later Stage 5 render attestation, removes phase-relative
stale wording, and exposes the four dual-consumption components without
persisting private financial values.
"""

from __future__ import annotations

from copy import deepcopy
from html import escape
import json
from pathlib import Path
import re
from typing import Any, Mapping

from pfi_os.application.analysis.report_analysis import validate_phase92_analysis_pack
from pfi_os.application.reports.contracts import canonical_hash, file_hash


VERSION = "v0.2.5"
STAGE = 9
PHASE = "whole_stage_review"
PHASE_ID = "V025-S9-WHOLE-REVIEW"
ACCEPTANCE_ID = "ACC-PFI-V025-STAGE9-WHOLE-REVIEW"
PFI_ROOT = Path(__file__).resolve().parents[4]
PHASE92_SNAPSHOT_RELATIVE = Path("config/reports/v025_phase92_analysis_snapshot.json")
STAGE5_ATTESTATION_RELATIVE = Path(
    "reports/pfi_v025/stage_5/whole_stage_review/private_runtime_attestation.json"
)
PHASE91_DATA_QUALITY_RELATIVE = Path(
    "reports/pfi_v025/stage_9/phase_9_1/data_quality_report.json"
)
BUILDER_RELATIVE = Path("src/pfi_os/application/analysis/stage9_reviewed_analysis.py")

COMPONENT_LABELS = {
    "total_consumption_outflow_cny": "消费总流出",
    "living_consumption_cny": "生活消费",
    "investment_funding_outflow_cny": "投资资金流出",
    "investment_allocation_amount_cny": "投资域内配置",
}
STALE_TEXT = (
    "本 Phase 只建立",
    "不实现 Phase 9.2",
    "Phase 9.2 不生成",
    "Tracked Web/report renderers do not yet consume",
)


def _json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _clean_limitations(values: object) -> list[str]:
    rows = [str(value) for value in values or []]
    return [row for row in rows if not any(marker in row for marker in STALE_TEXT)]


def _component_cards(attestation: Mapping[str, Any]) -> list[dict[str, Any]]:
    statuses = attestation.get("component_statuses")
    if not isinstance(statuses, Mapping) or set(statuses) != set(COMPONENT_LABELS):
        raise ValueError("Stage 5 four-component attestation is incomplete")
    return [
        {
            "metric_id": metric_id,
            "label_zh": COMPONENT_LABELS[metric_id],
            "status": str(statuses[metric_id]),
            "status_zh": "本机真实快照已验证",
            "formula_id": "FORM-PFI-015",
            "value_visibility": "private_runtime_only_not_persisted",
            "scope_zh": (
                "gross activity 口径，不等于净资产损失。"
                if metric_id == "total_consumption_outflow_cny"
                else "独立活动组件；与其他组件分开展示和复核。"
            ),
            "review_route": "/reports?tab=consumption-components",
            "financial_values_emitted": 0,
            "contains_private_values": False,
        }
        for metric_id in COMPONENT_LABELS
    ]


def build_stage9_reviewed_analysis_pack(
    pfi_root: Path | str | None = None,
    *,
    observed_at: str,
) -> dict[str, Any]:
    root = Path(pfi_root).expanduser().resolve() if pfi_root is not None else PFI_ROOT
    source = _json_object(root / PHASE92_SNAPSHOT_RELATIVE)
    source_gate = validate_phase92_analysis_pack(source, pfi_root=root)
    if source_gate.get("status") != "pass":
        raise ValueError("immutable Phase 9.2 source snapshot is not current and passing")
    attestation = _json_object(root / STAGE5_ATTESTATION_RELATIVE)
    if (
        attestation.get("status") != "pass"
        or attestation.get("actual_ui_render_binding_completed") is not True
        or attestation.get("actual_report_render_binding_completed") is not True
        or attestation.get("contains_private_values") is not False
        or attestation.get("financial_values_emitted") != 0
    ):
        raise ValueError("Stage 5 render attestation is not passing and public-safe")
    timestamp = str(observed_at or "").strip()
    if not timestamp:
        raise ValueError("observed_at is required")

    hashes = {
        **dict(source["hashes"]),
        "source_phase92_snapshot_hash": file_hash(root / PHASE92_SNAPSHOT_RELATIVE),
        "stage5_render_attestation_hash": file_hash(root / STAGE5_ATTESTATION_RELATIVE),
        "source_phase91_data_quality_hash": file_hash(root / PHASE91_DATA_QUALITY_RELATIVE),
        "reviewed_analysis_builder_hash": file_hash(root / BUILDER_RELATIVE),
    }
    components = _component_cards(attestation)
    reports = deepcopy(source["report_set"])
    for report in reports:
        report["schema"] = "PFIV025Stage9ReviewedFinancialReportV1"
        report["analysis_version"] = "pfi-v025-stage9-reviewed-analysis-v1"
        report["generated_at"] = timestamp
        report["hashes"] = dict(hashes)
        report["limitations"] = _clean_limitations(report.get("limitations")) + [
            "缺失输入继续保持 blocked/partial，不解释为零或完整财务结论。",
            "人工复核与导出不会改变报告的来源、公式、参数或计算状态。",
        ]
        if report.get("report_type") == "consumption":
            report["component_cards"] = deepcopy(components)
            report["actual_report_render_binding_completed"] = True
        report["snapshot_hash"] = canonical_hash(
            {key: value for key, value in report.items() if key != "snapshot_hash"}
        )

    model_cards = deepcopy(source["model_validation_cards"])
    for card in model_cards:
        card["schema"] = "PFIV025Stage9ReviewedModelValidationCardV1"
        card["limitations"] = _clean_limitations(card.get("limitations")) + [
            "正式 Stage 9 报告已分别渲染四个活动组件；公开证据只保存状态、lineage 与 hash。",
            "真实金额仅在本机私有运行时显示，不写入 tracked evidence。",
        ]
        card["coverage_dimensions"]["report_completeness"] = "actual_four_component_render_binding_complete"
        card["actual_ui_render_binding_completed"] = True
        card["actual_report_render_binding_completed"] = True

    source_data_quality = _json_object(root / PHASE91_DATA_QUALITY_RELATIVE)
    data_quality = deepcopy(source_data_quality)
    data_quality["schema"] = "PFIV025Stage9ReviewedDataQualityReportV1"
    data_quality["generated_at"] = timestamp
    data_quality["limitations"] = _clean_limitations(data_quality.get("limitations")) + [
        "数据质量报告只说明来源、lineage、覆盖与异常，不输出财务数值。",
        "当前财务分析与人工判断使用 reviewed snapshot；缺失来源继续阻断。",
    ]
    data_quality["dependencies"] = [
        row
        for row in data_quality.get("dependencies", [])
        if row.get("dependency_id") != "financial_analysis_implementation"
    ] + [
        {
            "dependency_id": "reviewed_analysis_snapshot",
            "status": "ready",
            "critical": False,
            "blocking_reason_zh": None,
        }
    ]
    data_quality["gaps"] = [
        row
        for row in data_quality.get("gaps", [])
        if row.get("dependency_id") != "financial_analysis_implementation"
    ]
    data_quality["completeness"]["gap_count"] = len(data_quality["gaps"])
    data_quality["completeness"]["ready_dependency_count"] = 2
    data_quality["source_phase91_snapshot_hash"] = file_hash(root / PHASE91_DATA_QUALITY_RELATIVE)
    data_quality["hashes"] = dict(hashes)
    data_quality["snapshot_hash"] = canonical_hash(
        {key: value for key, value in data_quality.items() if key != "snapshot_hash"}
    )

    ui_source = source["ui_contract"]
    report_by_type = {str(row["report_type"]): row for row in reports}
    ui_contract: dict[str, Any] = {
        **deepcopy(ui_source),
        "schema": "PFIV025Stage9ReviewedAnalysisUIContractV1",
        "phase_id": PHASE_ID,
        "title_zh": "Stage 9 财务报告、模型验证与人工判断",
        "subtitle_zh": "四项活动组件分别可见；缺失来源保持阻断，部分报告只声明真实覆盖。",
        "component_count": len(components),
        "component_cards": deepcopy(components),
        "report_cards": [
            {
                **deepcopy(row),
                "snapshot_hash": report_by_type[str(row["report_type"])]["snapshot_hash"],
            }
            for row in ui_source["report_cards"]
        ],
        "model_cards": [
            {
                **deepcopy(row),
                "limitation_count": len(model_cards[index]["limitations"]),
                "actual_ui_render_binding_completed": True,
                "actual_report_render_binding_completed": True,
            }
            for index, row in enumerate(ui_source["model_cards"])
        ],
        "hashes": dict(hashes),
        "source_phase92_pack_hash": source["pack_hash"],
        "phase_9_3_candidate_complete": True,
        "stage_9_whole_stage_review_done": False,
        "stage_10_started": False,
    }
    ui_contract.pop("phase_9_3_started", None)

    pack: dict[str, Any] = {
        "schema": "PFIV025Stage9ReviewedAnalysisPackV1",
        "version": VERSION,
        "stage": STAGE,
        "phase": PHASE,
        "phase_id": PHASE_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": "candidate_pass_pending_whole_stage_rereview",
        "observed_at": timestamp,
        "source_phase92_pack_hash": source["pack_hash"],
        "source_phase92_snapshot_hash": hashes["source_phase92_snapshot_hash"],
        "stage5_render_attestation_hash": hashes["stage5_render_attestation_hash"],
        "hashes": hashes,
        "report_set": reports,
        "formula_drilldowns": deepcopy(source["formula_drilldowns"]),
        "sensitivity_previews": deepcopy(source["sensitivity_previews"]),
        "model_validation_cards": model_cards,
        "source_review_index": deepcopy(source["source_review_index"]),
        "data_quality_report": data_quality,
        "component_cards": components,
        "ui_contract": ui_contract,
        "phase_9_3_candidate_complete": True,
        "stage_9_whole_stage_review_done": False,
        "stage_10_started": False,
        "automatic_trading_allowed": False,
        "trade_execution_available": False,
        "financial_values_emitted": 0,
        "contains_private_values": False,
        "real_financial_rows_read": False,
        "database_read": False,
        "database_changed": False,
        "model_values_changed": False,
        "formula_values_changed": False,
        "parameter_values_changed": False,
    }
    pack["pack_hash"] = canonical_hash(pack)
    return pack


def validate_stage9_reviewed_analysis_pack(
    pack: Mapping[str, Any],
    *,
    pfi_root: Path | str | None = None,
) -> dict[str, Any]:
    root = Path(pfi_root).expanduser().resolve() if pfi_root is not None else PFI_ROOT
    errors: list[str] = []
    try:
        rebuilt = build_stage9_reviewed_analysis_pack(
            root, observed_at=str(pack.get("observed_at") or "")
        )
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        rebuilt = None
        errors.append(f"current-input rebuild failed: {type(exc).__name__}")
    if rebuilt is not None and dict(pack) != rebuilt:
        errors.append("reviewed analysis pack differs from current-input rebuild")
    reports = pack.get("report_set") if isinstance(pack.get("report_set"), list) else []
    components = pack.get("component_cards") if isinstance(pack.get("component_cards"), list) else []
    if len(reports) != 5:
        errors.append("five reports are required")
    if len(components) != 4 or {row.get("metric_id") for row in components if isinstance(row, Mapping)} != set(COMPONENT_LABELS):
        errors.append("four dual-consumption component cards are required")
    consumption = next((row for row in reports if row.get("report_type") == "consumption"), {})
    if consumption.get("component_cards") != components:
        errors.append("main consumption report is not bound to all four component cards")
    data_quality = pack.get("data_quality_report") if isinstance(pack.get("data_quality_report"), Mapping) else {}
    if data_quality.get("status") != "complete" or data_quality.get("completeness", {}).get("gap_count") != 7:
        errors.append("reviewed data-quality report is missing or stale")
    serialized = json.dumps(pack, ensure_ascii=False, sort_keys=True)
    if any(marker in serialized for marker in STALE_TEXT):
        errors.append("stale phase-relative wording remains")
    if (
        re.search(r"\bCNY\s+-?[0-9]", serialized)
        or re.search(r'"(?:value|amount|financial_value)"\s*:', serialized)
        or re.search(r'"[a-z0-9_]+_cny"\s*:', serialized)
    ):
        errors.append("public reviewed analysis contains a financial value")
    for key, expected in (
        ("phase_9_3_candidate_complete", True),
        ("stage_9_whole_stage_review_done", False),
        ("stage_10_started", False),
        ("automatic_trading_allowed", False),
        ("trade_execution_available", False),
        ("contains_private_values", False),
    ):
        if pack.get(key) is not expected:
            errors.append(f"unsafe or stale state: {key}")
    if pack.get("financial_values_emitted") != 0:
        errors.append("financial values emitted")
    cross_hashes = bool(reports) and all(
        isinstance(row, Mapping) and row.get("hashes") == pack.get("hashes")
        for row in reports
    )
    if not cross_hashes:
        errors.append("cross-report hashes differ")
    return {
        "schema": "PFIV025Stage9ReviewedAnalysisValidationV1",
        "phase_id": PHASE_ID,
        "status": "pass" if not errors else "fail",
        "errors": errors,
        "report_count": len(reports),
        "component_count": len(components),
        "cross_report_hashes_consistent": cross_hashes,
        "financial_values_emitted": int(pack.get("financial_values_emitted") or 0),
        "contains_private_values": bool(pack.get("contains_private_values")),
    }


def render_model_validation_report_html(pack: Mapping[str, Any]) -> str:
    gate = validate_stage9_reviewed_analysis_pack(pack)
    if gate["status"] != "pass":
        raise ValueError("cannot render an invalid reviewed analysis pack")
    model = pack["model_validation_cards"][0]
    component_rows = "".join(
        "<tr>"
        f"<td>{escape(str(row['label_zh']))}</td>"
        f"<td>{escape(str(row['status_zh']))}</td>"
        f"<td><code>{escape(str(row['formula_id']))}</code></td>"
        f"<td>{escape(str(row['scope_zh']))}</td>"
        "</tr>"
        for row in pack["component_cards"]
    )
    formula_rows = "".join(
        "<tr>"
        f"<td><code>{escape(str(row['formula_id']))}</code></td>"
        f"<td>{escape(str(row['validation_status']))}</td>"
        f"<td>{escape(', '.join(row['parameters']))}</td>"
        f"<td>{escape(str(row['limitation']))}</td>"
        "</tr>"
        for row in pack["formula_drilldowns"]
    )
    sensitivity_rows = "".join(
        "<tr>"
        f"<td>{escape(str(row['title_zh']))}</td>"
        f"<td>{escape(str(row['status']))}</td>"
        f"<td>{escape(', '.join(row['parameter_ids']))}</td>"
        f"<td>{escape(str(row['impact_summary_zh']))}</td>"
        f"<td>{escape(str(row['limitation_zh']))}</td>"
        "</tr>"
        for row in pack["sensitivity_previews"]
    )
    limitations = "".join(f"<li>{escape(str(row))}</li>" for row in model["limitations"])
    counters = "".join(f"<li>{escape(str(row))}</li>" for row in model["counter_evidence"])
    return (
        "<!doctype html>\n<html lang=\"zh-CN\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        "<title>PFI v0.2.5 Stage 9 模型验证报告</title>"
        "<style>body{font:15px/1.65 system-ui,sans-serif;max-width:1100px;margin:32px auto;padding:0 24px;color:#17212b}"
        "table{width:100%;border-collapse:collapse;margin:16px 0 28px}th,td{padding:9px;border:1px solid #ccd4dc;text-align:left;vertical-align:top}"
        "code{overflow-wrap:anywhere}.gate{padding:14px;border-radius:12px;background:#eef4f8}</style>"
        "</head><body><h1>Stage 9 模型验证与参数影响</h1>"
        f"<p class=\"gate\">Reviewed snapshot: <code>{escape(str(pack['pack_hash']))}</code><br>"
        f"Source Phase 9.2: <code>{escape(str(pack['source_phase92_pack_hash']))}</code></p>"
        "<h2>四项活动组件</h2><p>四项分别显示；真实金额仅在本机私有运行时可见，投资活动不等于净资产损失。</p>"
        f"<table><thead><tr><th>组件</th><th>状态</th><th>公式</th><th>口径</th></tr></thead><tbody>{component_rows}</tbody></table>"
        "<h2>公式、不变量与限制</h2>"
        f"<p>不变量：{escape(str(model['invariant_status']))}；变形验证：{escape(str(model['metamorphic_status']))}；"
        f"历史/样本外：{escape(str(model['historical_out_of_sample_validation']['status']))}。"
        f"{escape(str(model['historical_out_of_sample_validation']['reason']))}</p>"
        f"<table><thead><tr><th>公式</th><th>验证状态</th><th>参数</th><th>限制</th></tr></thead><tbody>{formula_rows}</tbody></table>"
        "<h2>敏感性与参数调整影响</h2>"
        f"<table><thead><tr><th>敏感性</th><th>状态</th><th>参数</th><th>可见影响</th><th>限制</th></tr></thead><tbody>{sensitivity_rows}</tbody></table>"
        f"<h2>模型限制</h2><ul>{limitations}</ul><h2>反方证据</h2><ul>{counters}</ul>"
        "<h2>人工复核问题</h2><ol><li>数据覆盖是否足够支持当前 partial 结论？</li>"
        "<li>公式与双消费口径是否正确？</li><li>模型有效性是否被准确限制？</li>"
        "<li>参数调整影响是可见、还是因缺少 ground truth 保持阻断？</li></ol>"
        "<p>本报告不提供自动交易或订单执行能力。</p></body></html>\n"
    )
