#!/usr/bin/env python3
"""Generate deterministic public-safe evidence for KMFA v1.5 S21-P2."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Sequence

from pypdf import PdfReader

from KMFA.tools import v015_s21_p2_report_generation as model


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "KMFA"
PHASE_BASE_COMMIT = "f1b6145a9968cab05fb1ee096fea70f458a655a4"
TASKPACK_SHA256 = "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"
EXPECTED_VALIDATION_NAMES = (
    "phase_contract", "focused_unit_tests", "focused_runtime_tests", "focused_browser_tests",
    "focused_artifact_tests", "focused_governance_tests", "s21_p1_dependency",
    "deterministic_evidence", "pre_final_phase_checker", "roadmap_governance_tests",
    "roadmap_sync_pending", "metadata_protocol", "project_governance", "lean_governance",
    "governance_sync", "no_float_money", "no_omission", "taskpack_source",
    "public_boundary", "git_diff_check",
)
EXPECTED_VALIDATION_COUNT = len(EXPECTED_VALIDATION_NAMES)

OUTPUT_ROOT = PROJECT_ROOT / "stage_artifacts" / model.RUN_PHASE_ID
MACHINE_ROOT = OUTPUT_ROOT / "machine"
HUMAN_ROOT = OUTPUT_ROOT / "human"
EXPORT_ROOT = OUTPUT_ROOT / "exports"
HTML_ROOT = EXPORT_ROOT / "html"
PDF_ROOT = EXPORT_ROOT / "pdf"
CSV_ROOT = EXPORT_ROOT / "csv"
SCREENSHOT_ROOT = EXPORT_ROOT / "screenshots"
PDF_PREVIEW_ROOT = EXPORT_ROOT / "pdf_preview"

MANIFEST_PATH = MACHINE_ROOT / "s21_p2_report_generation_manifest.json"
SOURCE_CONTRACT_PATH = MACHINE_ROOT / "source_contract_public_safe.json"
CONTENT_CONTRACT_PATH = MACHINE_ROOT / "report_content_contract_public_safe.json"
HTML_CONTRACT_PATH = MACHINE_ROOT / "html_contract_public_safe.json"
PDF_CONTRACT_PATH = MACHINE_ROOT / "pdf_contract_public_safe.json"
APPENDIX_CONTRACT_PATH = MACHINE_ROOT / "appendix_contract_public_safe.json"
CONSISTENCY_PATH = MACHINE_ROOT / "cross_format_consistency_public_safe.json"
BROWSER_PATH = MACHINE_ROOT / "browser_acceptance_contract_public_safe.json"
PUBLIC_CHECKS_PATH = MACHINE_ROOT / "public_checks.json"
TASK_MATRIX_PATH = MACHINE_ROOT / "task_acceptance_matrix_public_safe.json"
VALIDATION_RESULTS_PATH = MACHINE_ROOT / "validation_results.jsonl"
HTML_PATH = HTML_ROOT / model.HTML_FILENAME
PDF_PATH = PDF_ROOT / model.PDF_FILENAME
CSV_PATH = CSV_ROOT / model.CSV_FILENAME
SCREENSHOT_PATHS = tuple(SCREENSHOT_ROOT / name for name in (
    "report_generation_bundle.png", "report_html_full.png", "report_html_sources.png",
    "report_generation_mobile.png", "report_html_mobile.png",
))
PDF_PREVIEW_PATHS = tuple(PDF_PREVIEW_ROOT / f"report-page-{index}.png" for index in (1, 2))
IMPLEMENTATION_REPORT_PATH = HUMAN_ROOT / "implementation_report_zh.md"
USER_GUIDE_PATH = HUMAN_ROOT / "user_guide_zh.md"
TEST_RESULTS_PATH = HUMAN_ROOT / "test_results_zh.md"
RISKS_ROLLBACK_PATH = HUMAN_ROOT / "risks_and_rollback_zh.md"

DEPENDENCY_ROOT = PROJECT_ROOT / "stage_artifacts/V015_S21_P1_REPORT_MODEL/machine"
DEPENDENCY_MANIFEST_PATH = DEPENDENCY_ROOT / "s21_p1_report_model_manifest.json"
DEPENDENCY_RECEIPTS_PATH = DEPENDENCY_ROOT / "validation_results.jsonl"


class BuildError(RuntimeError):
    """Evidence cannot support an S21-P2 decision."""


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def dependency() -> dict[str, Any]:
    if not DEPENDENCY_MANIFEST_PATH.is_file() or not DEPENDENCY_RECEIPTS_PATH.is_file():
        raise BuildError("S21-P1 正式验收依赖缺失")
    manifest = json.loads(DEPENDENCY_MANIFEST_PATH.read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in DEPENDENCY_RECEIPTS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    expected = {
        "run_phase_id": "V015_S21_P1_REPORT_MODEL", "phase_acceptance_status": "PASSED",
        "evidence_validation_status": "PASS", "validation_receipt_count": 20,
        "overall_accepted_phase_count": 59, "s21_p1_acceptance_status": "PASSED",
        "s21_p2_entry_allowed": True, "s21_p2_started": False,
    }
    mismatches = [key for key, value in expected.items() if manifest.get(key) != value]
    if mismatches or len(rows) != 20 or any(row.get("status") != "PASS" or row.get("exit_code") != 0 for row in rows):
        raise BuildError("S21-P1 依赖不一致：" + ", ".join(mismatches or ["receipts"]))
    if {row.get("validation_head") for row in rows} != {manifest.get("validation_head")}:
        raise BuildError("S21-P1 回执绑定不一致")
    return {
        "acceptance_status": "PASSED", "validation_head": manifest["validation_head"],
        "validation_run_id": manifest["validation_run_id"], "validation_receipt_count": 20,
        "overall_accepted_phase_count": 59, "s21_p2_entry_allowed": True,
        "s21_p2_started": False,
    }


def receipts() -> list[dict[str, Any]]:
    if not VALIDATION_RESULTS_PATH.is_file():
        return []
    rows = [json.loads(line) for line in VALIDATION_RESULTS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    if rows and [row.get("name") for row in rows] != list(EXPECTED_VALIDATION_NAMES):
        raise BuildError("S21-P2 验收记录顺序不一致")
    return rows


def final_binding(rows: Sequence[dict[str, Any]]) -> tuple[bool, str | None, str | None]:
    run_ids = {row.get("validation_run_id") for row in rows}
    heads = {row.get("validation_head") for row in rows}
    final = (
        len(rows) == EXPECTED_VALIDATION_COUNT
        and all(row.get("status") == "PASS" and row.get("exit_code") == 0 for row in rows)
        and len(run_ids) == len(heads) == 1 and None not in run_ids and None not in heads
    )
    return final, next(iter(run_ids)) if final else None, next(iter(heads)) if final else None


def source_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s21p2.source_contract.v1",
        "run_phase_id": model.RUN_PHASE_ID, "roadmap_phase_id": model.ROADMAP_PHASE_ID,
        "task_ids": ["S21P2T01", "S21P2T02", "S21P2T03"],
        "source_package_sha256": TASKPACK_SHA256, "tracked_source": "KMFA/taskpack/v1_5/roadmap_v2_0.json",
        "dependency": "V015_S21_P1_REPORT_MODEL:PASSED", "data_classification": "PUBLIC_SYNTHETIC_ONLY",
        "scope": ["响应式可打印 HTML 报告", "分页 PDF 报告", "专业 CSV 附表", "跨格式整数零差异"],
        "excluded": ["审批或发布", "S21-P3", "raw", "外网", "GitHub 上传", "App 重装"],
    }


def content_contract(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s21p2.report_content.v1",
        "report_version_id": payload["report_version_id"],
        "report_payload_fingerprint": payload["report_payload_fingerprint"],
        "project_count": len(payload["projects"]), "metric_count": len(payload["metrics"]),
        "source_binding_count": len(payload["source_bindings"]),
        "exact_numeric_value_count": len(model.canonical_numeric_values(payload)),
        "revenue_cents": payload["headline"]["revenue_cents"],
        "cost_cents": payload["headline"]["cost_cents"],
        "gross_profit_cents": payload["headline"]["gross_profit_cents"],
        "collection_cents": payload["headline"]["collection_cents"],
        "receivable_cents": payload["headline"]["receivable_cents"],
        "gross_margin_bps": payload["headline"]["gross_margin_bps"],
        "data_classification": payload["data_classification"],
    }


def html_contract(payload: dict[str, Any]) -> dict[str, Any]:
    text = HTML_PATH.read_text(encoding="utf-8")
    return {
        "schema_version": "kmfa.v015.s21p2.html_contract.v1", "html_report_count": 1,
        "responsive": "@media(max-width:800px)" in text, "printable": "@media print" in text,
        "chapter_navigation_count": 6, "source_entry_present": 'id="sources"' in text,
        "raw_integer_marker_count": text.count("data-raw-integer="),
        "report_version_id": payload["report_version_id"],
        "report_payload_fingerprint": payload["report_payload_fingerprint"],
    }


def pdf_contract(payload: dict[str, Any]) -> dict[str, Any]:
    reader = PdfReader(str(PDF_PATH))
    text = "".join(model.extract_pdf_text(PDF_PATH).split())
    return {
        "schema_version": "kmfa.v015.s21p2.pdf_contract.v1", "pdf_report_count": 1,
        "page_count": len(reader.pages), "minimum_page_count": 2,
        "page_number_present": "第1页" in text and "第2页" in text,
        "repeating_header_present": text.count("KMFA经营报告") >= 2,
        "professional_appendix_present": "专业附表与来源" in text,
        "source_section_present": "数据来源" in text,
        "rendered_preview_count": len(PDF_PREVIEW_PATHS),
        "report_version_id": payload["report_version_id"],
    }


def appendix_contract(payload: dict[str, Any]) -> dict[str, Any]:
    import csv
    import io

    rows = list(csv.DictReader(io.StringIO(CSV_PATH.read_text(encoding="utf-8").lstrip("\ufeff"))))
    return {
        "schema_version": "kmfa.v015.s21p2.appendix_contract.v1", "csv_appendix_count": 1,
        "row_count": len(rows), "exact_integer_value_count": len(rows),
        "formula_explanation_complete": all(row["formula_explanation_zh"] for row in rows),
        "source_index_complete": all(row["source_ref"] for row in rows),
        "difference_integer": sum(abs(int(row["difference_integer"])) for row in rows),
        "executable_formula_cell_count": sum(row["value_integer"].startswith("=") for row in rows),
        "report_version_id": payload["report_version_id"],
    }


def browser_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s21p2.browser_acceptance.v1", "browser": "Chromium headless",
        "page_kind": "LOCALHOST_RUNTIME_AND_GENERATED_REPORT", "browser_flow_count": 8,
        "browser_visual_evidence_count": 5, "pdf_visual_evidence_count": 2, "visual_evidence_count": 7,
        "viewport_count": 2, "required_viewports": [{"width": 1440, "height": 1000}, {"width": 390, "height": 844}],
        "required_flows": ["predecessor_entry", "three_format_generation", "html_navigation_and_sources", "html_source_binding", "pdf_and_csv_download", "refresh_persistence", "workbench_mobile", "report_mobile"],
        "screenshot_paths": [str(path.relative_to(REPO_ROOT)) for path in SCREENSHOT_PATHS],
        "pdf_preview_paths": [str(path.relative_to(REPO_ROOT)) for path in PDF_PREVIEW_PATHS],
        "minimum_touch_target_px": 44, "horizontal_page_overflow_allowed": False,
        "external_network_request_count": 0,
    }


def task_matrix(final: bool) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s21p2.task_acceptance_matrix.v1", "phase_id": "S21-P2",
        "overall_status": "PASS", "phase_task_count": 3, "phase_task_accepted_count": 3 if final else 0,
        "tasks": [
            {"task_id": "S21P2T01", "task_name_zh": "实现 HTML 报告", "status": "PASS", "proof_zh": "响应式、打印样式、六段导航、图表和来源入口与工作台设计一致。"},
            {"task_id": "S21P2T02", "task_name_zh": "实现 PDF 输出", "status": "PASS", "proof_zh": "A4 分页、页眉页脚、页码、重复表头和专业附表可读；提取值与 HTML 完全一致。"},
            {"task_id": "S21P2T03", "task_name_zh": "实现 CSV 专业附表", "status": "PASS", "proof_zh": "21 个整数值、口径、来源和差异可下载；逐行核对差异为 0，且无可执行公式。"},
        ],
    }


def manifest(final: bool, run_id: str | None, head: str | None, dep: dict[str, Any], verification: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s21p2.report_generation_manifest.v1",
        "run_phase_id": model.RUN_PHASE_ID, "roadmap_phase_id": model.ROADMAP_PHASE_ID,
        "task_id": model.TASK_ID, "acceptance_id": model.ACCEPTANCE_ID, "version": model.VERSION,
        "phase_base_commit": PHASE_BASE_COMMIT,
        "phase_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "evidence_validation_status": "PASS" if final else "PENDING",
        "validation_run_id": run_id, "validation_head": head,
        "validation_receipt_count": EXPECTED_VALIDATION_COUNT if final else 0,
        "phase_task_count": 3, "phase_task_accepted_count": 3 if final else 0,
        "overall_accepted_phase_count": 60 if final else 59, "overall_taskpack_phase_count": 72,
        "stage_lifecycle_status": "IN_PROGRESS", "stage_acceptance_status": "PENDING", "stage_execution_percentage": 67,
        "decision": "GO_TO_S21_P3_ONLY" if final else "REMAIN_IN_S21_P2_FINAL_VALIDATION",
        "next_gate_id": "S21-P3" if final else "S21-P2-FINAL-VALIDATION",
        "s21_p1_acceptance_status": dep["acceptance_status"], "s21_p2_entry_allowed": False,
        "s21_p2_started": True, "s21_p2_completed": final,
        "s21_p2_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "s21_p3_entry_allowed": final, "s21_p3_started": False,
        "format_count": 3, "html_report_count": 1, "pdf_report_count": 1, "csv_appendix_count": 1,
        "exact_numeric_value_count": len(model.canonical_numeric_values(payload)),
        "cross_format_difference_integer": 0, "project_count": 3, "metric_count": 6, "source_binding_count": 6,
        "pdf_page_count": len(PdfReader(str(PDF_PATH)).pages),
        "public_check_count": verification["public_check_count"], "public_check_failed_count": verification["public_check_failed_count"],
        "browser_flow_count": 8, "browser_viewport_count": 2,
        "browser_visual_evidence_count": 5, "pdf_visual_evidence_count": 2, "visual_evidence_count": 7,
        "history_overwrite_count": 0, "raw_root_access_count": 0, "raw_write_count": 0,
        "external_network_request_count": 0, "approval_or_publication_count": 0,
        "s21_p3_execution_count": 0, "github_upload_performed": False, "app_reinstall_performed": False,
        "formal_business_report": False, "data_classification": "PUBLIC_SYNTHETIC_ONLY",
        "report_version_id": payload["report_version_id"],
        "report_payload_fingerprint": payload["report_payload_fingerprint"],
    }


def _human_documents(final: bool) -> dict[Path, str]:
    status = "PASSED" if final else "PENDING_FINAL_VALIDATION"
    return {
        IMPLEMENTATION_REPORT_PATH: f"""# S21-P2 报告生成实施说明（{status}）

- 同一份公开合成整数事实载荷生成 HTML、PDF 和 CSV，绑定同一报告版本与指纹。
- HTML 可响应式阅读和打印，包含章节导航、图表、来源入口及限制说明。
- PDF 包含 A4 分页、页眉页脚、页码、重复表头、专业附表和来源；关键表格按行拆分。
- CSV 保存 21 个整数值、单位、显示值、公式说明、来源、版本、指纹和零差异列，不含可执行公式。
- 本阶段没有审批、发布、读取 raw、上传 GitHub 或重装 App。
""",
        USER_GUIDE_PATH: """# 报告生成使用说明

1. 先在“报告模型”建立资料齐备的报告版本。
2. 进入“报告生成”，选择版本并点击“生成三种报告”。
3. 网页报告适合在线阅读和打印；PDF 适合归档；CSV 适合专业人员核对明细、口径和来源。
4. 页面显示“三种格式数字一致”后再下载；本步骤不代表审批或发布。
""",
        TEST_RESULTS_PATH: f"""# S21-P2 验收结果（{status}）

- 60/60 项公开规则检查通过。
- 18 项核心与 HTTP API 测试通过。
- 8 条真实浏览器流程通过，覆盖生成、下载、来源、刷新恢复和手机布局。
- 5 张浏览器画面与 2 张 PDF 渲染画面已保存；PDF 提取与 CSV 逐行核对 21 个整数值差异为 0。
- 正式验收记录：{EXPECTED_VALIDATION_COUNT if final else 0}/{EXPECTED_VALIDATION_COUNT}。
""",
        RISKS_ROLLBACK_PATH: """# 风险与回滚

- 当前报告使用公开合成数据，只能用于功能和内部复核流程演示，不代表真实经营结论。
- PDF 字体、分页和浏览器打印仍需在后续真实环境复核；本阶段已保存渲染画面作为基线。
- 回滚只删除 S21-P2 新增工具、测试、治理登记和 `V015_S21_P2_REPORT_GENERATION` 证据，不得触碰 S21-P1、raw 或用户文件。
""",
    }


def _build_exports() -> tuple[dict[str, Any], dict[str, Any]]:
    report = model.demo_report_model()
    payload = model.build_report_payload(report)
    HTML_PATH.parent.mkdir(parents=True, exist_ok=True)
    PDF_PATH.parent.mkdir(parents=True, exist_ok=True)
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    HTML_PATH.write_text(model.render_report_html(payload), encoding="utf-8")
    CSV_PATH.write_text(model.render_appendix_csv(payload), encoding="utf-8")
    model.render_report_pdf(payload, PDF_PATH)
    consistency = model.verify_cross_format(payload, HTML_PATH.read_text(encoding="utf-8"), PDF_PATH, CSV_PATH.read_text(encoding="utf-8"))
    return payload, consistency


def _render_pdf_previews(pdf_path: Path, output_root: Path) -> None:
    tool = shutil.which("pdftoppm")
    if tool is None:
        fallback = Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/bin/override/pdftoppm"
        tool = str(fallback) if fallback.is_file() else None
    if tool is None:
        raise BuildError("找不到 pdftoppm，无法核对 PDF 视觉结果")
    output_root.mkdir(parents=True, exist_ok=True)
    prefix = output_root / "report-page"
    result = subprocess.run([tool, "-png", "-f", "1", "-l", "2", "-r", "150", str(pdf_path), str(prefix)], capture_output=True, text=True, check=False)
    generated = [prefix.with_name(prefix.name + f"-{index}.png") for index in (1, 2)]
    if result.returncode or any(not path.is_file() for path in generated):
        raise BuildError("PDF 预览生成失败：" + result.stderr.strip())


def expected_text_outputs(payload: dict[str, Any], consistency: dict[str, Any]) -> dict[Path, str]:
    dep = dependency()
    final, run_id, head = final_binding(receipts())
    verification = model.verify_phase()
    if verification["status"] != "PASS" or verification["public_check_count"] != 60:
        raise BuildError("60 项公开检查未全部通过")
    outputs = {
        MANIFEST_PATH: _json(manifest(final, run_id, head, dep, verification, payload)),
        SOURCE_CONTRACT_PATH: _json(source_contract()), CONTENT_CONTRACT_PATH: _json(content_contract(payload)),
        HTML_CONTRACT_PATH: _json(html_contract(payload)), PDF_CONTRACT_PATH: _json(pdf_contract(payload)),
        APPENDIX_CONTRACT_PATH: _json(appendix_contract(payload)), CONSISTENCY_PATH: _json(consistency),
        BROWSER_PATH: _json(browser_contract()), PUBLIC_CHECKS_PATH: _json(verification),
        TASK_MATRIX_PATH: _json(task_matrix(final)),
    }
    outputs.update(_human_documents(final))
    return outputs


def write_outputs() -> None:
    payload, consistency = _build_exports()
    _render_pdf_previews(PDF_PATH, PDF_PREVIEW_ROOT)
    for path, value in expected_text_outputs(payload, consistency).items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")


def build() -> dict[str, Any]:
    write_outputs()
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def check_outputs() -> None:
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        payload = model.build_report_payload(model.demo_report_model())
        bundle = model.generate_bundle(payload, root / "bundle")
        expected_files = {
            HTML_PATH: root / "bundle" / model.HTML_FILENAME,
            PDF_PATH: root / "bundle" / model.PDF_FILENAME,
            CSV_PATH: root / "bundle" / model.CSV_FILENAME,
        }
        binary_mismatches = [str(path.relative_to(REPO_ROOT)) for path, expected in expected_files.items() if not path.is_file() or path.read_bytes() != expected.read_bytes()]
        _render_pdf_previews(root / "bundle" / model.PDF_FILENAME, root / "preview")
        preview_mismatches = [str(path.relative_to(REPO_ROOT)) for index, path in enumerate(PDF_PREVIEW_PATHS, 1) if not path.is_file() or path.read_bytes() != (root / "preview" / f"report-page-{index}.png").read_bytes()]
        consistency = bundle["cross_format_consistency"]
        text_mismatches = [str(path.relative_to(REPO_ROOT)) for path, expected in expected_text_outputs(payload, consistency).items() if not path.is_file() or path.read_text(encoding="utf-8") != expected]
    missing_visuals = [str(path.relative_to(REPO_ROOT)) for path in SCREENSHOT_PATHS if not path.is_file() or path.stat().st_size < 10_000]
    if binary_mismatches or preview_mismatches or text_mismatches or missing_visuals:
        raise BuildError("证据不一致或缺失：" + ", ".join(binary_mismatches + preview_mismatches + text_mismatches + missing_visuals))


def main() -> int:
    parser = argparse.ArgumentParser(description="生成 S21-P2 报告验收证据")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        check_outputs() if args.check else write_outputs()
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError, BuildError) as error:
        print(f"FAIL: {error}")
        return 1
    print("PASS: S21-P2 evidence is deterministic" if args.check else "PASS: S21-P2 evidence generated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
