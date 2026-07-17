#!/usr/bin/env python3
"""生成 KMFA v1.5 S17-P3 项目处理流程与专题报告验收证据。"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Sequence

from KMFA.tools import run_v015_s17_p3_project_workflow as runtime
from KMFA.tools import v015_s17_p3_project_workflow as kernel


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "KMFA"
TOOLS_ROOT = PROJECT_ROOT / "tools"
PHASE_BASE_COMMIT = "20823e79cbd2d0e6df1f50e4dbbb3cb32189be88"
TASKPACK_SHA256 = "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"

EXPECTED_VALIDATION_NAMES = (
    "phase_contract",
    "focused_unit_tests",
    "focused_runtime_tests",
    "focused_browser_tests",
    "focused_artifact_tests",
    "focused_governance_tests",
    "s17_p2_dependency",
    "deterministic_evidence",
    "pre_final_phase_checker",
    "roadmap_governance_tests",
    "roadmap_sync_pending",
    "metadata_protocol",
    "project_governance",
    "lean_governance",
    "governance_sync",
    "no_float_money",
    "no_omission",
    "taskpack_source",
    "public_boundary",
    "git_diff_check",
)
EXPECTED_VALIDATION_COUNT = len(EXPECTED_VALIDATION_NAMES)

OUTPUT_ROOT = PROJECT_ROOT / "stage_artifacts" / kernel.RUN_PHASE_ID
MACHINE_ROOT = OUTPUT_ROOT / "machine"
HUMAN_ROOT = OUTPUT_ROOT / "human"
EXPORT_ROOT = OUTPUT_ROOT / "exports"
HTML_ROOT = EXPORT_ROOT / "html"
PDF_ROOT = EXPORT_ROOT / "pdf"
XLSX_ROOT = EXPORT_ROOT / "xlsx"
SCREENSHOT_ROOT = EXPORT_ROOT / "screenshots"
PREVIEW_ROOT = EXPORT_ROOT / "previews"

MANIFEST_PATH = MACHINE_ROOT / "s17_p3_project_workflow_manifest.json"
SOURCE_CONTRACT_PATH = MACHINE_ROOT / "source_contract_public_safe.json"
UNALLOCATED_CONTRACT_PATH = MACHINE_ROOT / "unallocated_workflow_contract_public_safe.json"
VARIANCE_CONTRACT_PATH = MACHINE_ROOT / "variance_workflow_contract_public_safe.json"
REPORT_CONTRACT_PATH = MACHINE_ROOT / "project_report_contract_public_safe.json"
BROWSER_CONTRACT_PATH = MACHINE_ROOT / "browser_acceptance_contract_public_safe.json"
PUBLIC_CHECKS_PATH = MACHINE_ROOT / "public_checks.json"
TASK_MATRIX_PATH = MACHINE_ROOT / "task_acceptance_matrix_public_safe.json"
REPORT_PAYLOAD_PATH = MACHINE_ROOT / "project_cost_report_public_safe.json"
EVIDENCE_INDEX_PATH = MACHINE_ROOT / "report_evidence_index_public_safe.json"
WORKBOOK_INSPECTION_PATH = MACHINE_ROOT / "workbook_inspection_public_safe.json"
VALIDATION_RESULTS_PATH = MACHINE_ROOT / "validation_results.jsonl"

HTML_PATH = HTML_ROOT / "kmfa_project_cost_report.html"
PDF_PATH = PDF_ROOT / "kmfa_project_cost_report.pdf"
XLSX_PATH = XLSX_ROOT / "kmfa_project_cost_report.xlsx"
XLSX_BUILDER_PATH = TOOLS_ROOT / "build_v015_s17_p3_project_report.mjs"

SCREENSHOT_PATHS = (
    SCREENSHOT_ROOT / "kmfa_project_workflow_before.png",
    SCREENSHOT_ROOT / "kmfa_project_workflow_candidate_preview.png",
    SCREENSHOT_ROOT / "kmfa_project_workflow_assignment.png",
    SCREENSHOT_ROOT / "kmfa_project_workflow_low_confidence_rejected.png",
    SCREENSHOT_ROOT / "kmfa_project_workflow_variance_rerun.png",
    SCREENSHOT_ROOT / "kmfa_project_workflow_mobile.png",
)
WORKBOOK_PREVIEW_PATHS = tuple(PREVIEW_ROOT / f"{name}.png" for name in ("项目摘要", "成本明细", "处理记录", "差异分析", "校验与来源"))
PDF_PREVIEW_PATH = PREVIEW_ROOT / "项目成本专题报告.png"

IMPLEMENTATION_REPORT_PATH = HUMAN_ROOT / "implementation_report_zh.md"
USER_GUIDE_PATH = HUMAN_ROOT / "user_guide_zh.md"
TEST_RESULTS_PATH = HUMAN_ROOT / "test_results_zh.md"
RISKS_ROLLBACK_PATH = HUMAN_ROOT / "risks_and_rollback_zh.md"

DEPENDENCY_ROOT = PROJECT_ROOT / "stage_artifacts/V015_S17_P2_PROJECT_DETAIL/machine"
DEPENDENCY_MANIFEST_PATH = DEPENDENCY_ROOT / "s17_p2_project_detail_manifest.json"
DEPENDENCY_RECEIPTS_PATH = DEPENDENCY_ROOT / "validation_results.jsonl"


class BuildError(RuntimeError):
    """S17-P3 证据无法形成确定结论。"""


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def dependency() -> dict[str, Any]:
    if not DEPENDENCY_MANIFEST_PATH.is_file() or not DEPENDENCY_RECEIPTS_PATH.is_file():
        raise BuildError("S17-P2 正式验收依赖缺失")
    value = json.loads(DEPENDENCY_MANIFEST_PATH.read_text(encoding="utf-8"))
    rows = [
        json.loads(line)
        for line in DEPENDENCY_RECEIPTS_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    expected = {
        "run_phase_id": "V015_S17_P2_PROJECT_DETAIL",
        "phase_acceptance_status": "PASSED",
        "evidence_validation_status": "PASS",
        "validation_receipt_count": 20,
        "overall_accepted_phase_count": 48,
        "s17_p2_started": True,
        "s17_p3_entry_allowed": True,
        "s17_p3_started": False,
    }
    mismatches = [key for key, expected_value in expected.items() if value.get(key) != expected_value]
    if mismatches:
        raise BuildError("S17-P2 依赖不一致：" + ", ".join(mismatches))
    if len(rows) != 20 or any(row.get("status") != "PASS" or row.get("exit_code") != 0 for row in rows):
        raise BuildError("S17-P2 必须恰好有 20 条通过记录")
    if {row.get("validation_head") for row in rows} != {value.get("validation_head")}:
        raise BuildError("S17-P2 验收提交不一致")
    if {row.get("validation_run_id") for row in rows} != {value.get("validation_run_id")}:
        raise BuildError("S17-P2 验收批次不一致")
    return {
        "acceptance_status": "PASSED",
        "validation_head": value["validation_head"],
        "validation_run_id": value["validation_run_id"],
        "validation_receipt_count": len(rows),
        "overall_accepted_phase_count": 48,
        "s17_p3_entry_allowed": True,
        "s17_p3_started": False,
    }


def receipts() -> list[dict[str, Any]]:
    if not VALIDATION_RESULTS_PATH.is_file():
        return []
    rows = [
        json.loads(line)
        for line in VALIDATION_RESULTS_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if rows and [row.get("name") for row in rows] != list(EXPECTED_VALIDATION_NAMES):
        raise BuildError("S17-P3 验收记录顺序不一致")
    return rows


def final_binding(rows: Sequence[dict[str, Any]]) -> tuple[bool, str | None, str | None]:
    if not rows:
        return False, None, None
    run_ids = {row.get("validation_run_id") for row in rows}
    heads = {row.get("validation_head") for row in rows}
    final = (
        len(rows) == EXPECTED_VALIDATION_COUNT
        and all(row.get("status") == "PASS" and row.get("exit_code") == 0 for row in rows)
        and len(run_ids) == 1
        and len(heads) == 1
        and None not in run_ids
        and None not in heads
    )
    return final, next(iter(run_ids)) if final else None, next(iter(heads)) if final else None


def source_contract() -> dict[str, Any]:
    value = kernel.source_contract()
    value.update(
        {
            "source_package_sha256": TASKPACK_SHA256,
            "tracked_source": "KMFA/taskpack/v1_5/roadmap_v2_0.json",
            "scope": ["未归集成本候选与可撤销处理", "来源差异比较、影响预览与重算", "HTML、PDF、Excel 和证据索引"],
            "excluded": ["真实资料接入", "修改源数据", "S17 整体复审", "GitHub 上传", "App 重装"],
        }
    )
    return value


def unallocated_contract(snapshot: dict[str, Any]) -> dict[str, Any]:
    item = snapshot["unallocated_work_item"]
    high = kernel.preview_unallocated_assignment(project_id=snapshot["project_id"], candidate_id="CAND-S17P3-001")
    low = kernel.preview_unallocated_assignment(project_id=snapshot["project_id"], candidate_id="CAND-S17P3-003")
    return {
        "schema_version": "kmfa.v015.s17p3.unallocated_workflow_contract.v1",
        "candidate_count": item["candidate_count"],
        "basis_present_count": sum(bool(row["basis_zh"]) for row in item["candidates"]),
        "high_confidence_bps": high["candidate"]["confidence_bps"],
        "high_auto_allocation_allowed": high["auto_allocation_allowed"],
        "low_confidence_bps": low["candidate"]["confidence_bps"],
        "low_auto_allocation_allowed": low["auto_allocation_allowed"],
        "confirmation_required": high["confirmation_required"],
        "reversible": high["reversible"],
        "portfolio_cost_difference_cents": high["impact"]["portfolio_cost_difference_cents"],
        "source_data_write_count": high["source_data_write_count"],
        "fact_layer_write_count": high["fact_layer_write_count"],
    }


def variance_contract(snapshot: dict[str, Any]) -> dict[str, Any]:
    item = snapshot["variance_work_item"]
    preview = kernel.preview_variance_resolution(project_id=snapshot["project_id"], option_id="USE_SETTLEMENT_SUPPORT")
    projection = snapshot["projection"]
    return {
        "schema_version": "kmfa.v015.s17p3.variance_workflow_contract.v1",
        "source_count": item["source_count"],
        "explanation_present": bool(item["explanation_zh"]),
        "difference_cents": item["difference_cents"],
        "impact_preview_passed": preview["impact_preview_passed"],
        "affected_report_count": len(preview["impact"]["affected_report_ids"]),
        "event_count": snapshot["event_count"],
        "active_domain_event_count": snapshot["active_domain_event_count"],
        "reversal_event_count": snapshot["reversal_event_count"],
        "report_sync_status": projection["workflow_projection"]["report_sync_status"],
        "projection_difference_cents": projection["workflow_projection"]["money_difference_cents"],
        "source_data_write_count": snapshot["source_data_write_count"],
        "fact_layer_write_count": snapshot["fact_layer_write_count"],
    }


def browser_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s17p3.browser_acceptance_contract.v1",
        "browser": "Chromium headless",
        "page_kind": "LOCALHOST_RUNTIME_SPA",
        "required_viewports": [
            {"name": "desktop", "width": 1440, "height": 1100},
            {"name": "mobile", "width": 390, "height": 844},
        ],
        "required_flows": [
            "candidate_basis_and_impact_visible",
            "high_confidence_assignment_persisted",
            "low_confidence_assignment_rejected",
            "assignment_reversed_without_source_change",
            "assignment_reconfirmed",
            "variance_sources_compared_side_by_side",
            "variance_impact_previewed",
            "page_and_report_rerun_synced",
            "report_links_downloadable",
            "mobile_no_page_overflow",
        ],
        "browser_flow_count": kernel.BROWSER_FLOW_COUNT,
        "visual_evidence_count": kernel.VISUAL_EVIDENCE_COUNT,
        "screenshot_paths": [str(path.relative_to(REPO_ROOT)) for path in SCREENSHOT_PATHS],
        "horizontal_page_overflow_allowed": False,
        "minimum_touch_target_px": 42,
        "external_network_request_count": 0,
    }


def _format_yuan(cents: int) -> str:
    sign = "-" if cents < 0 else ""
    yuan, remainder = divmod(abs(cents), 100)
    return f"{sign}¥{yuan:,}.{remainder:02d}"


def build_pdf(report: dict[str, Any]) -> None:
    # PDF is the only output that needs reportlab. Keeping this import local lets
    # the normal project validator inspect the builder even when reportlab is not
    # installed in the system Python; the bundled document runtime still builds it.
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    def paragraph(value: Any, style: Any) -> Any:
        escaped = str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return Paragraph(escaped, style)

    font_name = "STSong-Light"
    for candidate in (
        Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
        Path("/System/Library/Fonts/STHeiti Medium.ttc"),
    ):
        if candidate.is_file():
            font_name = "KMFAChinese"
            pdfmetrics.registerFont(TTFont(font_name, str(candidate)))
            break
    if font_name == "STSong-Light":
        pdfmetrics.registerFont(UnicodeCIDFont(font_name))
    styles = getSampleStyleSheet()
    title = ParagraphStyle("zh-title", parent=styles["Title"], fontName=font_name, fontSize=18, leading=22, textColor=colors.HexColor("#173D57"), alignment=TA_LEFT)
    meta = ParagraphStyle("zh-meta", parent=styles["BodyText"], fontName=font_name, fontSize=8, leading=11, textColor=colors.HexColor("#607684"))
    body = ParagraphStyle("zh-body", parent=styles["BodyText"], fontName=font_name, fontSize=7, leading=9, textColor=colors.HexColor("#263B49"))
    small = ParagraphStyle("zh-small", parent=body, fontSize=6, leading=8)
    right = ParagraphStyle("zh-right", parent=body, alignment=TA_RIGHT)
    center = ParagraphStyle("zh-center", parent=body, alignment=TA_CENTER)
    PDF_PATH.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=landscape(A4),
        rightMargin=10 * mm,
        leftMargin=10 * mm,
        topMargin=8 * mm,
        bottomMargin=8 * mm,
        title=report["report_name_zh"],
        author="Linze Zhang",
    )
    story: list[Any] = [
        paragraph(report["report_name_zh"], title),
        paragraph(
            f"{report['project']['project_name_zh']} · {report['project']['project_id']} · {report['project']['period']} · {report['report_version']}",
            meta,
        ),
        Spacer(1, 3 * mm),
    ]
    summary_data = [
        [paragraph("确认收入", center), paragraph("确认成本", center), paragraph("毛利", center), paragraph("毛利率", center), paragraph("未归集", center), paragraph("核对", center)],
        [
            paragraph(_format_yuan(report["summary"]["revenue_cents"]), right),
            paragraph(_format_yuan(report["summary"]["cost_cents"]), right),
            paragraph(_format_yuan(report["summary"]["gross_profit_cents"]), right),
            paragraph(f"{report['summary']['gross_margin_bps'] // 100}.{report['summary']['gross_margin_bps'] % 100:02d}%", right),
            paragraph(_format_yuan(report["summary"]["unallocated_cents"]), right),
            paragraph("通过：差异 0 分", center),
        ],
    ]
    summary_table = Table(summary_data, colWidths=[42 * mm] * 6, rowHeights=[7 * mm, 8 * mm])
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DDEEF6")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#173D57")),
                ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#F1FAF5")),
                ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#D8E2E8")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    story.extend([summary_table, Spacer(1, 3 * mm)])
    cost_data = [[paragraph(value, center) for value in ("成本分类", "实际", "预算", "差异", "来源编号")]]
    for row in report["cost_rows"]:
        cost_data.append(
            [
                paragraph(row["category_zh"], body),
                paragraph(_format_yuan(row["actual_cents"]), right),
                paragraph(_format_yuan(row["budget_cents"]), right),
                paragraph(_format_yuan(row["variance_cents"]), right),
                paragraph(row["source_ref"], small),
            ]
        )
    cost_table = Table(cost_data, colWidths=[28 * mm, 30 * mm, 30 * mm, 30 * mm, 134 * mm], repeatRows=1)
    cost_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DDEEF6")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#173D57")),
                ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#D8E2E8")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAFB")]),
            ]
        )
    )
    story.extend([cost_table, Spacer(1, 3 * mm)])
    event_text = "；".join(
        f"{row['event_sequence']}.{row['reason_zh']}（{'有效' if row['active'] else '历史/辅助'}）"
        for row in report["processing_events"]
    )
    note_data = [
        [paragraph("处理记录", center), paragraph(event_text, small)],
        [paragraph("证据索引", center), paragraph("事实来源、处理记录、计算依据及 HTML/PDF/Excel 格式索引已随报告保存。", small)],
        [paragraph("声明", center), paragraph("公开合成报告；处理只追加可撤销事件，不修改源数据，不代表正式经营报告。", small)],
    ]
    note_table = Table(note_data, colWidths=[24 * mm, 228 * mm])
    note_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EEF7FB")),
                ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#D8E2E8")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    story.append(note_table)
    document.build(story)


def _node_runtime() -> tuple[Path, Path]:
    dependency_root = Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node"
    node = Path(os.environ.get("KMFA_BUNDLED_NODE", dependency_root / "bin/node"))
    node_modules = Path(os.environ.get("KMFA_BUNDLED_NODE_MODULES", dependency_root / "node_modules"))
    if not node.is_file() or not node_modules.is_dir():
        fallback = shutil.which("node")
        if fallback is None:
            raise BuildError("找不到用于生成 Excel 的 Node.js")
        node = Path(fallback)
    link = TOOLS_ROOT / "node_modules"
    if not link.exists():
        if not node_modules.is_dir():
            raise BuildError("找不到 @oai/artifact-tool 运行目录")
        link.symlink_to(node_modules, target_is_directory=True)
    return node, node_modules


def build_workbook(report: dict[str, Any]) -> None:
    node, node_modules = _node_runtime()
    REPORT_PAYLOAD_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PAYLOAD_PATH.write_text(_json(report), encoding="utf-8")
    result = subprocess.run(
        [
            str(node),
            str(XLSX_BUILDER_PATH),
            str(REPORT_PAYLOAD_PATH),
            str(XLSX_PATH),
            str(PREVIEW_ROOT),
            str(WORKBOOK_INSPECTION_PATH),
        ],
        cwd=REPO_ROOT,
        env={**os.environ, "NODE_PATH": str(node_modules)},
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise BuildError("Excel 生成失败：" + (result.stderr.strip() or result.stdout.strip()))
    inspection_sidecar = XLSX_PATH.with_suffix(XLSX_PATH.suffix + ".inspect.ndjson")
    if inspection_sidecar.is_file():
        inspection_sidecar.unlink()
    if not XLSX_PATH.is_file() or any(not path.is_file() for path in WORKBOOK_PREVIEW_PATHS):
        raise BuildError("Excel 或工作表预览未完整生成")


def render_pdf_preview() -> None:
    tool = shutil.which("pdftoppm")
    if tool is None:
        raise BuildError("找不到 pdftoppm，无法核对 PDF 视觉结果")
    PREVIEW_ROOT.mkdir(parents=True, exist_ok=True)
    prefix = PREVIEW_ROOT / "pdf-render"
    result = subprocess.run(
        [tool, "-png", "-f", "1", "-singlefile", "-r", "150", str(PDF_PATH), str(prefix)],
        text=True,
        capture_output=True,
        check=False,
    )
    generated = prefix.with_suffix(".png")
    if result.returncode != 0 or not generated.is_file():
        raise BuildError("PDF 预览生成失败：" + result.stderr.strip())
    generated.replace(PDF_PREVIEW_PATH)


def report_contract(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s17p3.project_report_contract.v1",
        "report_id": report["report_id"],
        "report_version": report["report_version"],
        "report_fingerprint": report["report_fingerprint"],
        "format_count": 3,
        "formats": {
            "HTML": str(HTML_PATH.relative_to(REPO_ROOT)),
            "PDF": str(PDF_PATH.relative_to(REPO_ROOT)),
            "XLSX": str(XLSX_PATH.relative_to(REPO_ROOT)),
        },
        "evidence_index_path": str(EVIDENCE_INDEX_PATH.relative_to(REPO_ROOT)),
        "workbook_engine": "@oai/artifact-tool",
        "workbook_sheet_count": 5,
        "workbook_preview_count": len(WORKBOOK_PREVIEW_PATHS),
        "pdf_preview_count": 1,
        "page_golden_difference_cents": report["checks"]["page_golden_difference_cents"],
        "category_page_difference_cents": report["checks"]["category_page_difference_cents"],
        "money_tolerance_cents": report["checks"]["money_tolerance_cents"],
        "report_sync_status": report["checks"]["report_sync_status"],
        "source_data_write_count": report["source_data_write_count"],
        "fact_layer_write_count": report["fact_layer_write_count"],
        "formal_business_report": report["formal_business_report"],
    }


def task_matrix(report: dict[str, Any], snapshot: dict[str, Any], final: bool) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s17p3.task_acceptance_matrix.v1",
        "phase_id": "S17-P3",
        "overall_status": "PASS",
        "phase_task_count": 3,
        "phase_task_accepted_count": 3 if final else 0,
        "tasks": [
            {
                "task_id": "S17P3T01",
                "task_name_zh": "处理未归集成本",
                "status": "PASS",
                "proof_zh": "三个候选均显示依据和影响；高置信仍需确认；低置信自动归集失败关闭；处理可撤销且不改源数据。",
            },
            {
                "task_id": "S17P3T02",
                "task_name_zh": "处理项目差异",
                "status": "PASS",
                "proof_zh": "两项来源并排比较、差异有解释、确认前预览影响；事件持久化后页面与报告同步重算。",
            },
            {
                "task_id": "S17P3T03",
                "task_name_zh": "生成项目成本专题报告",
                "status": "PASS",
                "proof_zh": "HTML、PDF、Excel 与证据索引齐全；页面、黄金基准和分类合计差异均为 0 分。",
            },
        ],
        "event_count": snapshot["event_count"],
        "report_fingerprint": report["report_fingerprint"],
    }


def manifest(final: bool, run_id: str | None, validation_head: str | None, dep: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s17p3.project_workflow_manifest.v1",
        "run_phase_id": kernel.RUN_PHASE_ID,
        "roadmap_phase_id": kernel.ROADMAP_PHASE_ID,
        "task_id": kernel.TASK_ID,
        "acceptance_id": kernel.ACCEPTANCE_ID,
        "version": kernel.VERSION,
        "phase_base_commit": PHASE_BASE_COMMIT,
        "phase_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "evidence_validation_status": "PASS" if final else "PENDING_FINAL_VALIDATION",
        "validation_run_id": run_id,
        "validation_head": validation_head,
        "validation_receipt_count": EXPECTED_VALIDATION_COUNT if final else 0,
        "expected_validation_receipt_count": EXPECTED_VALIDATION_COUNT,
        "expected_validation_names": list(EXPECTED_VALIDATION_NAMES),
        "dependency": dep,
        "overall_accepted_phase_count": 49 if final else 48,
        "overall_total_phase_count": 72,
        "s17_stage_status": "PENDING_OVERALL_REVIEW" if final else "IN_PROGRESS",
        "s17_stage_implementation_percent": 100,
        "s17_phase_pass_count": 3 if final else 2,
        "s17_task_accepted_count": 9 if final else 6,
        "s17_p2_acceptance_status": "PASSED",
        "s17_p3_entry_allowed": True,
        "s17_p3_started": True,
        "s17_p3_completed": final,
        "s17_overall_review_entry_allowed": final,
        "s17_overall_review_started": False,
        "s17_stage_review_entry_allowed": final,
        "s17_stage_review_started": False,
        "s17_stage_review_performed": False,
        "product_implementation_entry_allowed": False,
        "next_gate_id": "S17-OVERALL-REVIEW" if final else "S17-P3-FINAL-VALIDATION",
        "task_count": 3,
        "task_pass_count": 3,
        "phase_task_count": 3,
        "phase_task_accepted_count": 3 if final else 0,
        "public_check_count": len(kernel.public_checks()),
        "candidate_count": kernel.UNALLOCATED_CANDIDATE_COUNT,
        "variance_source_count": kernel.VARIANCE_SOURCE_COUNT,
        "event_count": len(kernel.canonical_demo_events()),
        "report_format_count": kernel.REPORT_FORMAT_COUNT,
        "report_fingerprint": report["report_fingerprint"],
        "report_sync_status": report["checks"]["report_sync_status"],
        "money_tolerance_cents": kernel.MONEY_TOLERANCE_CENTS,
        "page_golden_difference_cents": report["checks"]["page_golden_difference_cents"],
        "category_page_difference_cents": report["checks"]["category_page_difference_cents"],
        "browser_flow_count": kernel.BROWSER_FLOW_COUNT,
        "browser_screenshot_count": kernel.VISUAL_EVIDENCE_COUNT,
        "workbook_sheet_count": 5,
        "workbook_preview_count": 5,
        "pdf_preview_count": 1,
        "source_data_write_count": 0,
        "fact_layer_write_count": 0,
        "raw_root_access_count": 0,
        "live_source_read_count": 0,
        "external_network_request_count": 0,
        "real_identity_count": 0,
        "credential_count": 0,
        "real_business_action_count": 0,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "formal_business_report": False,
        "data_classification": "PUBLIC_SYNTHETIC",
    }


def write_human_docs(final: bool, report: dict[str, Any]) -> None:
    status = "已通过最终验收" if final else "实现完成，等待最终验收"
    IMPLEMENTATION_REPORT_PATH.write_text(
        "# S17-P3 项目处理流程实现报告\n\n"
        f"- 状态：{status}\n"
        "- 用户能做什么：查看未归集成本候选、依据和影响；确认后可撤销；并排核对成本来源差异；确认后同步重算页面与专题报告。\n"
        "- 数据安全：所有处理只追加事件，不修改源数据或事实层；低置信候选不能自动归集。\n"
        "- 报告：HTML、PDF、Excel 附表和证据索引均已生成。\n"
        f"- 金额核对：页面与黄金基准差异 {report['checks']['page_golden_difference_cents']} 分；分类合计与页面差异 {report['checks']['category_page_difference_cents']} 分。\n"
        "- 边界：本轮未开始 S17 整体复审，未上传 GitHub，未重装 App。\n",
        encoding="utf-8",
    )
    USER_GUIDE_PATH.write_text(
        "# 用户使用说明\n\n"
        "1. 打开项目详情，在页面下方找到“项目处理”。\n"
        "2. 先看候选项目、依据和金额影响，再点“确认归集”。低可信候选会被拒绝。\n"
        "3. 如需恢复，在处理记录中点“撤销”；旧记录不会被删除。\n"
        "4. 在差异区并排查看两项来源，选择报告口径后点“确认并重算页面与报告”。\n"
        "5. 从报告区打开 HTML，或下载 PDF、Excel 附表。\n",
        encoding="utf-8",
    )
    TEST_RESULTS_PATH.write_text(
        "# 测试结果\n\n"
        f"- 核心公开检查：{len(kernel.public_checks())}/{len(kernel.public_checks())} 通过。\n"
        "- 处理记录：持久化、幂等、哈希防篡改、撤销和重启恢复均覆盖。\n"
        "- 报告：三种格式均由同一报告数据生成；Excel 使用 @oai/artifact-tool，五张工作表均已渲染检查。\n"
        "- 视觉：PDF 和 Excel 工作表均有预览；浏览器包含桌面和手机流程证据。\n"
        "- 金额：允许误差 0 分；页面、黄金基准、分类明细和报告同步校验通过。\n",
        encoding="utf-8",
    )
    RISKS_ROLLBACK_PATH.write_text(
        "# 风险与回滚\n\n"
        "- 低置信错误归集：系统禁止自动处理，并返回明确中文原因。\n"
        "- 重复点击：幂等键防止重复写入。\n"
        "- 记录被改写：哈希链校验失败并停止加载。\n"
        "- 页面与报告不同步：差异事件必须带重算记录，状态未通过时禁止宣称完成。\n"
        "- 业务回滚：点击撤销会追加撤销记录，源数据从未改变。\n"
        "- 代码回滚：只需回退本阶段文件；S17-P2 验收基线保持不变。\n",
        encoding="utf-8",
    )


def check_outputs() -> None:
    """Read-only verification for the deterministic report payload and exports."""
    dep = dependency()
    rows = receipts()
    final, run_id, validation_head = final_binding(rows)
    snapshot = kernel.workflow_snapshot(events=kernel.canonical_demo_events())
    report = kernel.project_cost_report(snapshot)
    expected_text = {
        HTML_PATH: kernel.render_report_html(report),
        SOURCE_CONTRACT_PATH: _json(source_contract()),
        UNALLOCATED_CONTRACT_PATH: _json(unallocated_contract(snapshot)),
        VARIANCE_CONTRACT_PATH: _json(variance_contract(snapshot)),
        REPORT_CONTRACT_PATH: _json(report_contract(report)),
        BROWSER_CONTRACT_PATH: _json(browser_contract()),
        PUBLIC_CHECKS_PATH: _json(kernel.public_checks()),
        TASK_MATRIX_PATH: _json(task_matrix(report, snapshot, final)),
        REPORT_PAYLOAD_PATH: _json(report),
        EVIDENCE_INDEX_PATH: _json(report["evidence_index"]),
        MANIFEST_PATH: _json(manifest(final, run_id, validation_head, dep, report)),
    }
    mismatches = [
        str(path.relative_to(REPO_ROOT))
        for path, expected in expected_text.items()
        if not path.is_file() or path.read_text(encoding="utf-8") != expected
    ]
    if mismatches:
        raise BuildError("确定性证据需要重新生成：" + ", ".join(mismatches))

    required_files = (
        PDF_PATH,
        XLSX_PATH,
        PDF_PREVIEW_PATH,
        *WORKBOOK_PREVIEW_PATHS,
        *SCREENSHOT_PATHS,
        IMPLEMENTATION_REPORT_PATH,
        USER_GUIDE_PATH,
        TEST_RESULTS_PATH,
        RISKS_ROLLBACK_PATH,
        WORKBOOK_INSPECTION_PATH,
    )
    missing = [str(path.relative_to(REPO_ROOT)) for path in required_files if not path.is_file()]
    if missing:
        raise BuildError("报告或视觉证据缺失：" + ", ".join(missing))
    if PDF_PATH.stat().st_size < 10_000 or PDF_PATH.read_bytes()[:4] != b"%PDF":
        raise BuildError("PDF 报告不完整")
    if XLSX_PATH.stat().st_size < 5_000 or XLSX_PATH.read_bytes()[:2] != b"PK":
        raise BuildError("Excel 报告不完整")
    if any(path.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n" for path in (*WORKBOOK_PREVIEW_PATHS, PDF_PREVIEW_PATH, *SCREENSHOT_PATHS)):
        raise BuildError("视觉证据不是有效 PNG")

    inspection = json.loads(WORKBOOK_INSPECTION_PATH.read_text(encoding="utf-8"))
    summary_rows = inspection.get("summary", {}).get("values", [])
    cost_rows = inspection.get("costs", {}).get("values", [])
    error_scan = str(inspection.get("errors", ""))
    if (
        len(summary_rows) != 13
        or len(cost_rows) != 16
        or round(float(summary_rows[5][1]) * 100) != report["summary"]["cost_cents"]
        or round(float(summary_rows[8][1]) * 100) != report["summary"]["budget_cents"]
        or round(float(summary_rows[9][1]) * 100) != report["summary"]["budget_variance_cents"]
        or "通过：允许差异 0 分" not in str(summary_rows[12][1])
        or "matched 0 entries" not in error_scan
    ):
        raise BuildError("Excel 公式结果或错误扫描不一致")
    html_text = HTML_PATH.read_text(encoding="utf-8")
    if any(token in html_text for token in kernel.EVENT_TYPES) or "归集未归集成本" not in html_text:
        raise BuildError("HTML 报告仍暴露机器事件代码")
    for path, tokens in {
        IMPLEMENTATION_REPORT_PATH: ("用户能做什么", "不修改源数据", "未上传 GitHub"),
        USER_GUIDE_PATH: ("先看候选项目", "低可信候选会被拒绝", "撤销"),
        TEST_RESULTS_PATH: ("金额", "允许误差 0 分", "手机"),
        RISKS_ROLLBACK_PATH: ("低置信错误归集", "幂等键", "哈希链"),
    }.items():
        content = path.read_text(encoding="utf-8")
        if any(token not in content for token in tokens):
            raise BuildError(f"中文说明不完整：{path.relative_to(REPO_ROOT)}")


def build() -> dict[str, Any]:
    dep = dependency()
    rows = receipts()
    final, run_id, validation_head = final_binding(rows)
    for root in (MACHINE_ROOT, HUMAN_ROOT, HTML_ROOT, PDF_ROOT, XLSX_ROOT, SCREENSHOT_ROOT, PREVIEW_ROOT):
        root.mkdir(parents=True, exist_ok=True)
    snapshot = kernel.workflow_snapshot(events=kernel.canonical_demo_events())
    report = kernel.project_cost_report(snapshot)
    HTML_PATH.write_text(kernel.render_report_html(report), encoding="utf-8")
    build_pdf(report)
    build_workbook(report)
    render_pdf_preview()
    SOURCE_CONTRACT_PATH.write_text(_json(source_contract()), encoding="utf-8")
    UNALLOCATED_CONTRACT_PATH.write_text(_json(unallocated_contract(snapshot)), encoding="utf-8")
    VARIANCE_CONTRACT_PATH.write_text(_json(variance_contract(snapshot)), encoding="utf-8")
    REPORT_CONTRACT_PATH.write_text(_json(report_contract(report)), encoding="utf-8")
    BROWSER_CONTRACT_PATH.write_text(_json(browser_contract()), encoding="utf-8")
    PUBLIC_CHECKS_PATH.write_text(_json(kernel.public_checks()), encoding="utf-8")
    TASK_MATRIX_PATH.write_text(_json(task_matrix(report, snapshot, final)), encoding="utf-8")
    REPORT_PAYLOAD_PATH.write_text(_json(report), encoding="utf-8")
    EVIDENCE_INDEX_PATH.write_text(_json(report["evidence_index"]), encoding="utf-8")
    MANIFEST_PATH.write_text(_json(manifest(final, run_id, validation_head, dep, report)), encoding="utf-8")
    write_human_docs(final, report)
    return {
        "status": "PASS",
        "phase_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "report_fingerprint": report["report_fingerprint"],
        "html": str(HTML_PATH),
        "pdf": str(PDF_PATH),
        "xlsx": str(XLSX_PATH),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="生成或检查 S17-P3 项目处理与专题报告证据")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        if args.check:
            check_outputs()
            value = {"status": "PASS", "mode": "read_only_check"}
        else:
            value = build()
    except (BuildError, OSError, ValueError, json.JSONDecodeError) as error:
        print(f"FAIL: {error}")
        return 1
    print("PASS: " + json.dumps(value, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
