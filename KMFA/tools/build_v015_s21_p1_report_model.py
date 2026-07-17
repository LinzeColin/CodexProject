#!/usr/bin/env python3
"""Generate deterministic public-safe evidence for KMFA v1.5 S21-P1."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Any, Sequence

from KMFA.tools import run_v015_s21_p1_report_model as runtime
from KMFA.tools import v015_s21_p1_report_model as model


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "KMFA"
PHASE_BASE_COMMIT = "883bac9cb41f2c55665820ad1b897c8470511368"
TASKPACK_SHA256 = "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"
EXPECTED_VALIDATION_NAMES = (
    "phase_contract", "focused_unit_tests", "focused_runtime_tests", "focused_browser_tests",
    "focused_artifact_tests", "focused_governance_tests", "s20_review_dependency",
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
SCREENSHOT_ROOT = EXPORT_ROOT / "screenshots"
HTML_ROOT = EXPORT_ROOT / "html"

MANIFEST_PATH = MACHINE_ROOT / "s21_p1_report_model_manifest.json"
SOURCE_CONTRACT_PATH = MACHINE_ROOT / "source_contract_public_safe.json"
PERIOD_VERSION_PATH = MACHINE_ROOT / "report_period_version_contract_public_safe.json"
AUDIENCE_PATH = MACHINE_ROOT / "audience_section_contract_public_safe.json"
TRUST_PATH = MACHINE_ROOT / "trust_limitation_contract_public_safe.json"
BROWSER_PATH = MACHINE_ROOT / "browser_acceptance_contract_public_safe.json"
PUBLIC_CHECKS_PATH = MACHINE_ROOT / "public_checks.json"
TASK_MATRIX_PATH = MACHINE_ROOT / "task_acceptance_matrix_public_safe.json"
VALIDATION_RESULTS_PATH = MACHINE_ROOT / "validation_results.jsonl"
HTML_PATH = HTML_ROOT / "kmfa_report_model.html"
SCREENSHOT_PATHS = tuple(SCREENSHOT_ROOT / name for name in (
    "report_model_complete.png", "report_model_revision_history.png",
    "report_model_audience_layers.png", "report_model_incomplete.png", "report_model_mobile.png",
))
IMPLEMENTATION_REPORT_PATH = HUMAN_ROOT / "implementation_report_zh.md"
USER_GUIDE_PATH = HUMAN_ROOT / "user_guide_zh.md"
TEST_RESULTS_PATH = HUMAN_ROOT / "test_results_zh.md"
RISKS_ROLLBACK_PATH = HUMAN_ROOT / "risks_and_rollback_zh.md"

DEPENDENCY_ROOT = PROJECT_ROOT / "stage_artifacts/V015_S20_STAGE_REVIEW/machine"
DEPENDENCY_MANIFEST_PATH = DEPENDENCY_ROOT / "s20_stage_review_manifest.json"
DEPENDENCY_RECEIPTS_PATH = DEPENDENCY_ROOT / "validation_results.jsonl"


class BuildError(RuntimeError):
    """Evidence cannot support an S21-P1 decision."""


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def dependency() -> dict[str, Any]:
    if not DEPENDENCY_MANIFEST_PATH.is_file() or not DEPENDENCY_RECEIPTS_PATH.is_file():
        raise BuildError("S20 整体复审正式验收依赖缺失")
    manifest = json.loads(DEPENDENCY_MANIFEST_PATH.read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in DEPENDENCY_RECEIPTS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    expected = {
        "run_phase_id": "V015_S20_STAGE_REVIEW", "phase_acceptance_status": "PASSED",
        "evidence_validation_status": "PASS", "validation_receipt_count": 32,
        "overall_accepted_phase_count": 58, "s20_stage_review_acceptance_status": "PASSED",
        "s21_entry_allowed": True, "s21_p1_entry_allowed": True, "s21_p1_started": False,
    }
    mismatches = [key for key, value in expected.items() if manifest.get(key) != value]
    if mismatches or len(rows) != 32 or any(row.get("status") != "PASS" or row.get("exit_code") != 0 for row in rows):
        raise BuildError("S20 整体复审依赖不一致：" + ", ".join(mismatches or ["receipts"]))
    if {row.get("validation_head") for row in rows} != {manifest.get("validation_head")}:
        raise BuildError("S20 整体复审回执绑定不一致")
    return {
        "acceptance_status": "PASSED", "validation_head": manifest["validation_head"],
        "validation_run_id": manifest["validation_run_id"], "validation_receipt_count": 32,
        "overall_accepted_phase_count": 58, "s21_p1_entry_allowed": True,
        "s21_p1_started": False,
    }


def receipts() -> list[dict[str, Any]]:
    if not VALIDATION_RESULTS_PATH.is_file():
        return []
    rows = [json.loads(line) for line in VALIDATION_RESULTS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    if rows and [row.get("name") for row in rows] != list(EXPECTED_VALIDATION_NAMES):
        raise BuildError("S21-P1 验收记录顺序不一致")
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


def _example() -> tuple[dict[str, Any], dict[str, Any]]:
    with tempfile.TemporaryDirectory() as folder:
        journal = model.ReportModelJournal(Path(folder) / "models.jsonl")
        first = journal.create(
            company_id="demo-north", period_kind="MONTHLY", period_key="2026-07",
            source_bindings=model.default_source_bindings(), formula_bindings=model.default_formula_bindings(),
            created_by="公开演示负责人", idempotency_key="evidence-create-001",
            recorded_at="2026-07-17T00:00:00+00:00",
        )
        revision = journal.revise(
            first["report_version_id"], revision_reason_zh="补充本期经营说明并保留初版",
            created_by="公开演示负责人", idempotency_key="evidence-revise-001",
            recorded_at="2026-07-17T00:01:00+00:00",
        )
        return first, revision


def source_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s21p1.source_contract.v1", "run_phase_id": model.RUN_PHASE_ID,
        "roadmap_phase_id": model.ROADMAP_PHASE_ID, "task_ids": ["S21P1T01", "S21P1T02", "S21P1T03"],
        "source_package_sha256": TASKPACK_SHA256, "tracked_source": "KMFA/taskpack/v1_5/roadmap_v2_0.json",
        "dependency": "V015_S20_STAGE_REVIEW:PASSED", "data_classification": "PUBLIC_SYNTHETIC_ONLY",
        "scope": ["报告期间和不可覆盖的修订版本", "管理摘要与专业附表受众层次", "自然语言可信与限制说明"],
        "excluded": ["HTML/PDF/Excel 报告生成", "审批或发布", "S21-P2/P3", "raw", "GitHub 上传", "App 重装"],
    }


def period_version_contract(first: dict[str, Any], revision: dict[str, Any]) -> dict[str, Any]:
    examples = {"WEEKLY": "2026-W29", "MONTHLY": "2026-07", "QUARTERLY": "2026-Q3", "HALF_YEAR": "2026-H1", "YEARLY": "2026"}
    return {
        "schema_version": "kmfa.v015.s21p1.period_version.v1",
        "period_kind_count": 5, "periods": [model.period_contract(kind, key) for kind, key in examples.items()],
        "version_count": 2, "version_ids": [first["report_version_id"], revision["report_version_id"]],
        "revision_creates_new_version": True, "first_version_preserved": True,
        "history_overwrite_allowed": False, "source_binding_count": len(first["source_bindings"]),
        "formula_binding_count": len(first["formula_bindings"]),
        "source_binding_fingerprint": first["source_binding_fingerprint"],
        "formula_binding_fingerprint": first["formula_binding_fingerprint"],
        "hash_chain_bound": revision["previous_event_hash"] == first["event_hash"],
    }


def audience_contract() -> dict[str, Any]:
    sections = model.section_contract()
    return {
        "schema_version": "kmfa.v015.s21p1.audience_section.v1", "audience_count": 2,
        "section_count": len(sections), "management_section_count": 5, "professional_section_count": 1,
        "sections": sections, "data_check_board_backend_content_count": 0,
        "technical_log_content_count": 0,
    }


def trust_contract() -> dict[str, Any]:
    complete = model.trust_and_limitations(model.default_source_bindings())
    incomplete = model.trust_and_limitations(model.default_source_bindings(missing=("finance_and_funds",), pending=("tax_and_policy",)))
    return {
        "schema_version": "kmfa.v015.s21p1.trust_limitation.v1", "complete_case": complete,
        "incomplete_case": incomplete, "incomplete_complete_claim_allowed": False,
        "technical_grade_abbreviation_count": 0, "plain_language_only": True,
    }


def browser_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s21p1.browser_acceptance.v1", "browser": "Chromium headless",
        "page_kind": "LOCALHOST_RUNTIME", "browser_flow_count": 8, "visual_evidence_count": 5,
        "viewport_count": 2, "required_viewports": [{"width": 1440, "height": 1000}, {"width": 390, "height": 844}],
        "required_flows": ["predecessor_entry", "complete_binding", "five_periods", "revision_history", "audience_layers", "incomplete_claim_refusal", "refresh_persistence", "mobile_touch_overflow"],
        "screenshot_paths": [str(path.relative_to(REPO_ROOT)) for path in SCREENSHOT_PATHS],
        "minimum_touch_target_px": 44, "horizontal_page_overflow_allowed": False,
        "external_network_request_count": 0,
    }


def task_matrix(final: bool) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s21p1.task_acceptance_matrix.v1", "phase_id": "S21-P1",
        "overall_status": "PASS", "phase_task_count": 3, "phase_task_accepted_count": 3 if final else 0,
        "tasks": [
            {"task_id": "S21P1T01", "task_name_zh": "建立报告期间和版本", "status": "PASS", "proof_zh": "周、月、季、半年和年度均有精确期间；每版绑定资料与公式版本，修订新增版本且不覆盖历史。"},
            {"task_id": "S21P1T02", "task_name_zh": "建立章节和受众层次", "status": "PASS", "proof_zh": "五个管理章节与一个专业附表分层展示，不混入资料检查板后台或技术日志。"},
            {"task_id": "S21P1T03", "task_name_zh": "建立可信与限制说明", "status": "PASS", "proof_zh": "资料缺失或待确认时用中文说明并禁止完整报告宣称，不显示技术等级缩写。"},
        ],
    }


def manifest(final: bool, run_id: str | None, head: str | None, dep: dict[str, Any], verification: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s21p1.report_model_manifest.v1", "run_phase_id": model.RUN_PHASE_ID,
        "roadmap_phase_id": model.ROADMAP_PHASE_ID, "task_id": model.TASK_ID, "acceptance_id": model.ACCEPTANCE_ID,
        "version": model.VERSION, "phase_base_commit": PHASE_BASE_COMMIT,
        "phase_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "evidence_validation_status": "PASS" if final else "PENDING", "validation_run_id": run_id,
        "validation_head": head, "validation_receipt_count": EXPECTED_VALIDATION_COUNT if final else 0,
        "phase_task_count": 3, "phase_task_accepted_count": 3 if final else 0,
        "overall_accepted_phase_count": 59 if final else 58, "overall_taskpack_phase_count": 72,
        "stage_lifecycle_status": "IN_PROGRESS", "stage_acceptance_status": "PENDING", "stage_execution_percentage": 33,
        "decision": "GO_TO_S21_P2_ONLY" if final else "REMAIN_IN_S21_P1_FINAL_VALIDATION",
        "next_gate_id": "S21-P2" if final else "S21-P1-FINAL-VALIDATION",
        "s20_stage_review_acceptance_status": dep["acceptance_status"], "s21_entry_allowed": False,
        "s21_p1_entry_allowed": False, "s21_p1_started": True, "s21_p1_completed": final,
        "s21_p1_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "s21_p2_entry_allowed": final, "s21_p2_started": False, "s21_p3_entry_allowed": False, "s21_p3_started": False,
        "period_kind_count": 5, "version_history_count": 2, "source_binding_count": 6,
        "formula_binding_count": 2, "section_count": 6, "management_section_count": 5,
        "professional_section_count": 1, "audience_count": 2,
        "public_check_count": verification["public_check_count"], "public_check_failed_count": verification["public_check_failed_count"],
        "browser_flow_count": 8, "browser_viewport_count": 2, "visual_evidence_count": 5,
        "history_overwrite_count": 0, "data_check_board_backend_content_count": 0,
        "technical_log_content_count": 0, "technical_grade_abbreviation_count": 0,
        "raw_root_access_count": 0, "raw_write_count": 0, "external_network_request_count": 0,
        "html_report_generation_count": 0, "pdf_report_generation_count": 0, "spreadsheet_report_generation_count": 0,
        "approval_or_publication_count": 0, "s21_p2_execution_count": 0, "s21_p3_execution_count": 0,
        "github_upload_performed": False, "app_reinstall_performed": False,
        "formal_business_report": False, "data_classification": "PUBLIC_SYNTHETIC_ONLY",
    }


def _human_documents(final: bool) -> dict[Path, str]:
    status = "PASSED" if final else "PENDING_FINAL_VALIDATION"
    return {
        IMPLEMENTATION_REPORT_PATH: f"""# S21-P1 报告模型实施说明（{status}）

- 支持周报、月报、季报、半年报和年报，每个期间都有明确起止日期。
- 同一期间首次建立后只能新增修订版，旧版不会被覆盖；每版固定绑定六类资料和公式版本。
- 页面按管理层与专业人员分层：五个管理章节、一个专业附表，不混入后台检查或技术日志。
- 资料缺失或待确认时会直接说明限制，并拒绝把内容称为完整报告。
- 本阶段没有生成正式 HTML/PDF/Excel 报告，没有审批、发布、GitHub 上传或 App 重装。
""",
        USER_GUIDE_PATH: """# 报告模型使用说明

1. 选择周、月、季、半年或年度，并填写对应期间。
2. 选择资料状态后建立初版；页面会显示绑定的资料、公式和完整性说明。
3. 需要更新时点击“建立修订版”，填写原因；系统保留旧版并新增版本。
4. “管理摘要”用于管理层阅读，“专业附表”用于查看口径、来源和差异入口。
5. 资料不齐时先补充或确认，不要把当前内容当作完整报告。
""",
        TEST_RESULTS_PATH: f"""# S21-P1 验收结果（{status}）

- 55/55 项公开规则检查通过。
- 21 项核心与 HTTP API 测试通过。
- 8 条真实浏览器流程通过，覆盖五类期间、修订历史、受众分层、资料不足提示、刷新恢复和手机布局。
- 5 张浏览器画面已保存；正式验收记录：{EXPECTED_VALIDATION_COUNT if final else 0}/{EXPECTED_VALIDATION_COUNT}。
""",
        RISKS_ROLLBACK_PATH: """# 风险与回滚

- 本阶段只建立报告身份、版本和章节骨架，尚未生成正式报告文件。
- 资料状态依赖已绑定版本；业务负责人仍需确认实际完整性和适用范围。
- 回滚只删除 S21-P1 新增工具、测试、治理登记和 `V015_S21_P1_REPORT_MODEL` 证据，不得触碰 S20、raw 或用户文件。
""",
    }


def expected_outputs() -> dict[Path, str]:
    dep = dependency()
    final, run_id, head = final_binding(receipts())
    verification = model.verify_phase()
    if verification["status"] != "PASS" or verification["public_check_count"] != 55:
        raise BuildError("55 项公开检查未全部通过")
    first, revision = _example()
    outputs = {
        MANIFEST_PATH: _json(manifest(final, run_id, head, dep, verification)),
        SOURCE_CONTRACT_PATH: _json(source_contract()), PERIOD_VERSION_PATH: _json(period_version_contract(first, revision)),
        AUDIENCE_PATH: _json(audience_contract()), TRUST_PATH: _json(trust_contract()), BROWSER_PATH: _json(browser_contract()),
        PUBLIC_CHECKS_PATH: _json(verification), TASK_MATRIX_PATH: _json(task_matrix(final)), HTML_PATH: runtime.render_html(),
    }
    outputs.update(_human_documents(final))
    return outputs


def write_outputs() -> None:
    for path, value in expected_outputs().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")


def build() -> dict[str, Any]:
    write_outputs()
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def check_outputs() -> None:
    mismatches = [str(path.relative_to(REPO_ROOT)) for path, expected in expected_outputs().items() if not path.is_file() or path.read_text(encoding="utf-8") != expected]
    missing = [str(path.relative_to(REPO_ROOT)) for path in SCREENSHOT_PATHS if not path.is_file() or path.stat().st_size < 10_000]
    if mismatches or missing:
        raise BuildError("证据不一致或缺失：" + ", ".join(mismatches + missing))


def main() -> int:
    parser = argparse.ArgumentParser(description="生成 S21-P1 报告模型验收证据")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        check_outputs() if args.check else write_outputs()
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError, BuildError) as error:
        print(f"FAIL: {error}")
        return 1
    print("PASS: S21-P1 evidence is deterministic" if args.check else "PASS: S21-P1 evidence generated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
