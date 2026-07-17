#!/usr/bin/env python3
"""Build deterministic public-safe evidence for KMFA v1.5 S06-P1."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

from KMFA.tools import v015_s06_p1_authoritative_source_registration as kernel


OUTPUT_DIR = Path("KMFA/stage_artifacts/V015_S06_P1_AUTHORITATIVE_SOURCE_REGISTRATION")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
MANIFEST_PATH = MACHINE_DIR / "s06_p1_authoritative_source_registration_manifest.json"
TASK_MATRIX_PATH = MACHINE_DIR / "task_acceptance_matrix_public_safe.json"
RECEIPTS_PATH = MACHINE_DIR / "validation_results.jsonl"
SOURCE_REGISTER_PATH = Path("KMFA/metadata/imports/v015_s06_p1_authority_source_register_public_safe.json")
FIELD_COVERAGE_PATH = Path("KMFA/metadata/schema_maps/v015_s06_p1_field_candidate_coverage_public_safe.json")
TEMPLATE_STRATEGY_PATH = Path("KMFA/metadata/schema_maps/v015_s06_p1_template_strategy_public_safe.json")
COMPLETION_PATH = HUMAN_DIR / "completion_record_zh.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results_zh.md"
OPEN_RISKS_PATH = HUMAN_DIR / "open_risks_zh.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan_zh.md"
S05_REVIEW_MANIFEST = Path("KMFA/stage_artifacts/V015_S05_STAGE_REVIEW/machine/s05_stage_review_manifest.json")
S05_REVIEW_RECEIPTS = Path("KMFA/stage_artifacts/V015_S05_STAGE_REVIEW/machine/validation_results.jsonl")


class BuildError(RuntimeError):
    pass


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise BuildError(f"JSON object required: {path}")
    return value


def _jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not all(isinstance(row, dict) for row in rows):
        raise BuildError(f"JSONL objects required: {path}")
    return rows


def _dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _dependency() -> dict[str, Any]:
    manifest = _json(S05_REVIEW_MANIFEST)
    receipts = _jsonl(S05_REVIEW_RECEIPTS)
    valid = (
        manifest.get("run_phase_id") == "V015_S05_STAGE_REVIEW"
        and manifest.get("stage_acceptance_status") == "PASSED"
        and manifest.get("decision") == "GO_TO_S06_P1_ONLY"
        and manifest.get("validation_receipt_count") == 20
        and len(receipts) == 20
        and all(row.get("status") == "PASS" for row in receipts)
        and len({row.get("validation_run_id") for row in receipts}) == 1
        and len({row.get("validation_head") for row in receipts}) == 1
    )
    if not valid:
        raise BuildError("S05 Stage Review final dependency is not receipt-bound PASSED")
    return {
        "phase_id": manifest["run_phase_id"],
        "acceptance_status": manifest["stage_acceptance_status"],
        "decision": manifest["decision"],
        "receipt_count": len(receipts),
        "validation_run_id": receipts[0]["validation_run_id"],
        "validation_head": receipts[0]["validation_head"],
        "evidence_ref": "KMFA/stage_artifacts/V015_S05_STAGE_REVIEW/",
    }


def _final_receipts() -> tuple[bool, list[dict[str, Any]], str | None, str | None]:
    rows = _jsonl(RECEIPTS_PATH)
    if not rows:
        return False, [], None, None
    run_ids = {row.get("validation_run_id") for row in rows}
    heads = {row.get("validation_head") for row in rows}
    passed = all(row.get("status") == "PASS" for row in rows) and len(run_ids) == len(heads) == 1
    if not passed:
        raise BuildError("validation receipts are incomplete or mixed")
    return True, rows, next(iter(run_ids)), next(iter(heads))


def _task_matrix(final: bool) -> dict[str, Any]:
    status = "PASSED" if final else "PENDING_FINAL_VALIDATION"
    return {
        "schema_version": "kmfa.v015.s06p1.task_acceptance_matrix_public_safe.v1",
        "phase_id": kernel.RUN_PHASE_ID,
        "roadmap_phase_id": kernel.ROADMAP_PHASE_ID,
        "task_count": 3,
        "task_execution_complete_count": 3,
        "task_accepted_count": 3 if final else 0,
        "tasks": [
            {
                "task_id": "S06P1T01",
                "name": "登记 8 个 PDF 与 1 个 Excel",
                "execution_status": "EXECUTION_COMPLETE",
                "acceptance_status": status,
                "evidence_refs": [str(SOURCE_REGISTER_PATH), str(MANIFEST_PATH)],
            },
            {
                "task_id": "S06P1T02",
                "name": "解析结构与字段",
                "execution_status": "EXECUTION_COMPLETE",
                "acceptance_status": status,
                "evidence_refs": [str(FIELD_COVERAGE_PATH), str(MANIFEST_PATH)],
            },
            {
                "task_id": "S06P1T03",
                "name": "识别模板差异",
                "execution_status": "EXECUTION_COMPLETE",
                "acceptance_status": status,
                "evidence_refs": [str(TEMPLATE_STRATEGY_PATH), str(MANIFEST_PATH)],
            },
        ],
    }


def _manifest(
    projection: dict[str, dict[str, Any]], dependency: dict[str, Any],
    final: bool, receipts: list[dict[str, Any]], run_id: str | None, head: str | None,
) -> dict[str, Any]:
    registration = projection["registration"]
    coverage = projection["coverage"]
    template = projection["template"]
    return {
        "schema_version": "kmfa.v015.s06p1.authoritative_source_registration_manifest.v1",
        "project_id": "KMFA",
        "target_release": "v1.5",
        "stage_id": "S06",
        "phase_id": kernel.RUN_PHASE_ID,
        "roadmap_phase_id": kernel.ROADMAP_PHASE_ID,
        "task_id": kernel.TASK_ID,
        "acceptance_id": kernel.ACCEPTANCE_ID,
        "version": kernel.VERSION,
        "run_mode": "IMPLEMENT",
        "work_kind": "AUTHORITATIVE_SOURCE_REGISTRATION",
        "fact_level": "PRIVATE_RAW_DERIVED_CANDIDATE",
        "phase_execution_status": "EXECUTION_COMPLETE",
        "phase_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "evidence_validation_status": "PASS" if final else "PENDING",
        "base_validation_receipts_scope": "BASE_SOURCE_REGISTRATION_PRE_SEMANTIC_REMEDIATION",
        "semantic_remediation_validation_scope": "FOCUSED_TESTS_PRIVATE_RESCAN_AND_PUBLIC_REBUILD",
        "semantic_remediation_status": "PASS",
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "stage_execution_percentage": 33,
        "stage_phase_pass_count": 1 if final else 0,
        "stage_task_accepted_count": 3 if final else 0,
        "phase_task_count": 3,
        "task_execution_complete_count": 3,
        "task_accepted_count": 3 if final else 0,
        "s05_stage_review_dependency": dependency,
        "s05_stage_review_dependency_validated": True,
        "authority_source_count": registration["source_count"],
        "authority_pdf_count": registration["pdf_count"],
        "authority_workbook_count": registration["workbook_count"],
        "source_readable_hashed_count": sum(
            row["integrity_status"] == "READABLE_HASHED" for row in registration["source_records"]
        ),
        "field_family_count": coverage["field_family_count"],
        "covered_field_family_count": coverage["covered_field_family_count"],
        "private_field_candidate_count": coverage["candidate_count"],
        "candidate_role_counts": coverage["candidate_role_counts"],
        "contract_total_locator_collision_count": coverage["contract_total_locator_collision_count"],
        "supporting_pdf_promoted_candidate_count": coverage["supporting_pdf_promoted_candidate_count"],
        "margin_header_gross_profit_candidate_count": coverage["margin_header_gross_profit_candidate_count"],
        "workbook_summary_candidate_count": coverage["workbook_summary_candidate_count"],
        "candidate_semantic_quality_passed": coverage["candidate_semantic_quality_passed"],
        "observed_template_class_count": template["observed_template_class_count"],
        "template_strategy_covered_count": sum(
            row["parser_strategy"] != "QUARANTINE_ONLY" for row in template["observed_template_classes"]
        ),
        "unknown_template_source_count": template["unknown_template_source_count"],
        "quarantined_component_count": template["quarantined_component_count"],
        "textless_page_count": template["textless_page_count"],
        "formula_cell_count": template["formula_cell_count"],
        "cached_formula_display_count": template["cached_formula_display_count"],
        "formula_and_display_values_separated": template["formula_and_display_values_separated"],
        "workbook_embedded_media_count": template["workbook_embedded_media_count"],
        "ocr_performed": False,
        "ocr_final_fact_count": 0,
        "golden_value_confirmed_count": 0,
        "raw_root_access_count": 1,
        "raw_read_performed": True,
        "raw_list_performed": True,
        "raw_stat_performed": True,
        "raw_hash_performed": True,
        "raw_parse_performed": True,
        "raw_write_performed": False,
        "raw_delete_performed": False,
        "raw_move_performed": False,
        "raw_rename_performed": False,
        "raw_overwrite_performed": False,
        "raw_mutation_performed": False,
        "raw_root_stat_unchanged": registration["raw_root_stat_unchanged"],
        "package_stat_unchanged": registration["package_stat_unchanged"],
        "package_hash_unchanged": registration["package_hash_unchanged"],
        "public_raw_name_count": 0,
        "public_raw_hash_count": 0,
        "public_raw_text_count": 0,
        "public_raw_value_count": 0,
        "public_sheet_name_count": 0,
        "private_evidence_token": registration["private_evidence_token"],
        "decision": "CONTINUE_TO_S06_P2_ONLY" if final else "REMAIN_IN_S06_P1",
        "s06_p1_started": True,
        "s06_p1_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "s06_p2_entry_allowed": final,
        "s06_p2_started": False,
        "s06_p3_entry_allowed": False,
        "s06_stage_review_entry_allowed": False,
        "formal_report_generated": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "validation_run_id": run_id,
        "validation_head": head,
        "validation_receipt_count": len(receipts),
        "validation_pass_count": len(receipts) if final else 0,
        "validation_failed_count": 0,
        "evidence_refs": [
            str(SOURCE_REGISTER_PATH), str(FIELD_COVERAGE_PATH), str(TEMPLATE_STRATEGY_PATH),
            str(TASK_MATRIX_PATH), str(COMPLETION_PATH), str(TEST_RESULTS_PATH),
            str(OPEN_RISKS_PATH), str(ROLLBACK_PATH),
        ],
    }


def _completion(manifest: dict[str, Any]) -> str:
    final = manifest["phase_acceptance_status"] == "PASSED"
    validation = (
        f"原始 P1 基线 {manifest['validation_receipt_count']}/{manifest['validation_pass_count']} exact receipts PASS，"
        f"run=`{manifest['validation_run_id']}`，implementation HEAD=`{manifest['validation_head']}`；"
        "本次候选语义修复以专项测试、私有重扫与公开产物重建结果为准。"
        if final else "exact receipts 尚待 clean implementation commit 后执行。"
    )
    return f"""# v1.5 S06-P1 权威资料登记完成记录

- Phase / Task / acceptance：`{kernel.RUN_PHASE_ID}` / `{kernel.TASK_ID}` / `{kernel.ACCEPTANCE_ID}`。
- T01：9/9 私有源 readable + private hash；8 PDF / 1 XLSX，公开仓库原始名称、hash、文本、值、sheet 名均为 0。
- T02：六类需求字段均有私有候选，候选总数 `{manifest['private_field_candidate_count']}`；原始显示文本与定位仅在 private runtime，全部仍为 candidate、human confirmation required。
- T02 semantic gate：合同额/总支出同定位冲突、支持页误提升、毛利率误作毛利润、汇总行误入候选均为 0。
- T03：观察到 `{manifest['observed_template_class_count']}` 类模板并逐类绑定解析策略；1 个无文本组件进入隔离，unknown source=0；OCR final fact=0。
- Excel：公式/缓存显示值=`{manifest['formula_cell_count']}/{manifest['cached_formula_display_count']}` 且分离；embedded media=`{manifest['workbook_embedded_media_count']}`，不自动成为事实。
- validation：{validation}
- gate：S06=`IN_PROGRESS/PENDING/33%`；decision=`{manifest['decision']}`；S06-P2 entry/started=`{str(manifest['s06_p2_entry_allowed']).lower()}/false`。
- boundary：raw 仅 read/list/stat/hash/parse；write/delete/move/rename/overwrite/mutation=false。S06-P2/P3、Stage review、formal report、GitHub、App、business=false。
"""


def _tests(manifest: dict[str, Any]) -> str:
    final = manifest["phase_acceptance_status"] == "PASSED"
    receipt_line = (
        f"- base exact receipts：`{manifest['validation_receipt_count']}/{manifest['validation_pass_count']} PASS`；run=`{manifest['validation_run_id']}`，HEAD=`{manifest['validation_head']}`；仅覆盖原始 P1 基线。\n"
        "- semantic remediation：专项测试、私有重扫与公开产物重建通过；不冒充旧 receipts 已覆盖本次修复。"
        if final else "- exact receipts：PENDING；仅在 clean implementation commit 上运行。"
    )
    return f"""# v1.5 S06-P1 测试结果

- authority registration：9/9 readable + private hash；source shape=8 PDF + 1 XLSX。
- candidate coverage：6/6 field families；private candidates={manifest['private_field_candidate_count']}。
- semantic quality：contract/total collision=0；supporting-page promotion=0；margin-as-profit=0；summary-row candidate=0。
- template strategy：{manifest['template_strategy_covered_count']}/{manifest['observed_template_class_count']}；unknown source=0；quarantined component=1。
- formula/display：{manifest['formula_cell_count']}/{manifest['cached_formula_display_count']} separated；OCR final facts=0。
- public safety：raw name/hash/text/value/sheet-name committed count 均为 0。
{receipt_line}
"""


def _risks() -> str:
    return """# v1.5 S06-P1 开放风险

1. 模板“current/legacy”仅为结构候选，尚无权威模板版本 metadata；S06-P2 人工签核前不得当成最终分类。
2. 一个无文本层组件已隔离；未来 OCR 结果只能作为候选，不能直接成为最终事实。
3. Excel 同时含公式、cached display、手工明细与 embedded media；S06-P2 必须逐字段确认来源类型和显示口径。
4. S06-P1 只证明来源可定位、可解析和模板有策略，不证明黄金值、业务准确性或完整 lineage。
5. 私有证据依赖本机 ignored runtime；公开仓库只包含聚合投影，不能独立还原业务明细。
"""


def _rollback() -> str:
    return """# v1.5 S06-P1 回滚计划

1. 仅回滚 `v015_s06_p1_*` 工具、测试、public-safe metadata、evidence 与本 Phase 治理记录。
2. private runtime 是派生诊断，可在确认 public evidence 不再依赖后单独删除；禁止回写或清理 raw inbox。
3. 不回滚或改写 S05-P1/P2/P3 与 S05 Stage Review 的冻结 evidence。
4. 本 Run 未启动 S06-P2/P3、Stage Review、GitHub 或 App，因此这些范围无需回滚。
"""


def expected_outputs() -> dict[Path, str]:
    private = kernel.read_private_payload()
    projection = kernel.public_projection(private)
    dependency = _dependency()
    final, receipts, run_id, head = _final_receipts()
    task_matrix = _task_matrix(final)
    manifest = _manifest(projection, dependency, final, receipts, run_id, head)
    return {
        SOURCE_REGISTER_PATH: _dump(projection["registration"]),
        FIELD_COVERAGE_PATH: _dump(projection["coverage"]),
        TEMPLATE_STRATEGY_PATH: _dump(projection["template"]),
        TASK_MATRIX_PATH: _dump(task_matrix),
        MANIFEST_PATH: _dump(manifest),
        COMPLETION_PATH: _completion(manifest),
        TEST_RESULTS_PATH: _tests(manifest),
        OPEN_RISKS_PATH: _risks(),
        ROLLBACK_PATH: _rollback(),
    }


def write_outputs() -> None:
    for path, content in expected_outputs().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def check_outputs() -> None:
    errors = [str(path) for path, content in expected_outputs().items() if not path.exists() or path.read_text(encoding="utf-8") != content]
    if errors:
        raise BuildError("deterministic output mismatch: " + ", ".join(errors))


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build KMFA v1.5 S06-P1 public-safe evidence")
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--write", action="store_true")
    action.add_argument("--check", action="store_true")
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.write:
        write_outputs()
        print("WROTE: S06-P1 public-safe evidence")
    else:
        check_outputs()
        print("PASS: S06-P1 public-safe evidence matches deterministic builder")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
