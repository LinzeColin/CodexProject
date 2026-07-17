#!/usr/bin/env python3
"""Build deterministic public-safe evidence for KMFA v1.5 S08-P1."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from KMFA.tools import v015_s08_p1_project_composite_identity as kernel


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "KMFA"
PHASE_BASE_COMMIT = "cca7a65d575bf506903e444cc73e36a277171409"

OUTPUT_ROOT = PROJECT_ROOT / "stage_artifacts" / "V015_S08_P1_PROJECT_COMPOSITE_IDENTITY"
MACHINE_ROOT = OUTPUT_ROOT / "machine"
HUMAN_ROOT = OUTPUT_ROOT / "human"
MANIFEST_PATH = MACHINE_ROOT / "s08_p1_project_composite_identity_manifest.json"
TASK_MATRIX_PATH = MACHINE_ROOT / "task_acceptance_matrix_public_safe.json"
MATCHING_MODEL_PATH = MACHINE_ROOT / "matching_model_public_safe.json"
NAME_FIXTURES_PATH = MACHINE_ROOT / "name_normalization_fixtures_public_safe.json"
AUXILIARY_CASES_PATH = MACHINE_ROOT / "auxiliary_matching_cases_public_safe.json"
VALIDATION_RESULTS_PATH = MACHINE_ROOT / "validation_results.jsonl"
CONTRACT_PATH = PROJECT_ROOT / "metadata" / "quality" / "v015_s08_p1_project_composite_identity_public_safe.json"

IMPLEMENTATION_REPORT_PATH = HUMAN_ROOT / "implementation_report_zh.md"
MATCHING_RULES_PATH = HUMAN_ROOT / "matching_rules_zh.md"
TEST_RESULTS_PATH = HUMAN_ROOT / "test_results_zh.md"
OPEN_RISKS_PATH = HUMAN_ROOT / "open_risks_zh.md"
ROLLBACK_PATH = HUMAN_ROOT / "rollback_plan_zh.md"

S07_REVIEW_MANIFEST_PATH = (
    PROJECT_ROOT / "stage_artifacts" / "V015_S07_STAGE_REVIEW" / "machine" / "s07_stage_review_manifest.json"
)
S07_REVIEW_RECEIPTS_PATH = (
    PROJECT_ROOT / "stage_artifacts" / "V015_S07_STAGE_REVIEW" / "machine" / "validation_results.jsonl"
)

EXPECTED_VALIDATION_NAMES = (
    "focused_kernel_tests",
    "focused_artifact_tests",
    "focused_governance_tests",
    "pre_final_phase_checker",
    "s07_review_dependency_check",
    "legacy_project_identity_regression",
    "roadmap_governance_tests",
    "roadmap_sync_pending",
    "metadata_protocol",
    "project_governance",
    "lean_governance",
    "governance_sync",
    "no_omission",
    "no_float_money",
    "deterministic_evidence",
    "python_compile",
    "structured_public_diff",
    "public_boundary",
    "git_diff_check",
)


class BuildError(RuntimeError):
    pass


def _dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise BuildError(f"JSON object required: {path}")
    return value


def _jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not all(isinstance(row, dict) for row in rows):
        raise BuildError(f"JSONL object rows required: {path}")
    return rows


def dependency() -> dict[str, Any]:
    manifest = _json(S07_REVIEW_MANIFEST_PATH)
    receipts = _jsonl(S07_REVIEW_RECEIPTS_PATH)
    required = {
        "run_phase_id": "V015_S07_STAGE_REVIEW",
        "phase_acceptance_status": "PASSED",
        "evidence_validation_status": "PASS",
        "stage_lifecycle_status": "COMPLETED",
        "stage_acceptance_status": "PASSED",
        "decision": "GO_TO_S08_P1_ONLY",
        "s08_p1_entry_allowed": True,
        "s08_p1_started": False,
        "validation_receipt_count": 22,
        "overall_accepted_phase_count": 19,
    }
    mismatches = [key for key, value in required.items() if manifest.get(key) != value]
    if mismatches:
        raise BuildError("S07 review dependency mismatch: " + ", ".join(mismatches))
    if len(receipts) != 22 or any(row.get("status") != "PASS" or row.get("exit_code") != 0 for row in receipts):
        raise BuildError("S07 review receipt set is not exactly 22 PASS records")
    if {row.get("validation_head") for row in receipts} != {manifest.get("validation_head")}:
        raise BuildError("S07 review validation head mismatch")
    if {row.get("validation_run_id") for row in receipts} != {manifest.get("validation_run_id")}:
        raise BuildError("S07 review validation run mismatch")
    return {
        "phase_id": manifest["run_phase_id"],
        "acceptance_status": manifest["phase_acceptance_status"],
        "stage_acceptance_status": manifest["stage_acceptance_status"],
        "validation_head": manifest["validation_head"],
        "validation_run_id": manifest["validation_run_id"],
        "validation_receipt_count": len(receipts),
        "s08_p1_entry_allowed": True,
        "s08_p1_started": False,
    }


def final_receipts() -> list[dict[str, Any]]:
    receipts = _jsonl(VALIDATION_RESULTS_PATH)
    if not receipts:
        return []
    if len(receipts) != len(EXPECTED_VALIDATION_NAMES):
        raise BuildError("S08-P1 validation receipt count mismatch")
    if [row.get("name") for row in receipts] != list(EXPECTED_VALIDATION_NAMES):
        raise BuildError("S08-P1 validation receipt order mismatch")
    if any(row.get("status") != "PASS" or row.get("exit_code") != 0 for row in receipts):
        raise BuildError("S08-P1 validation receipt set contains a failure")
    if len({row.get("validation_head") for row in receipts}) != 1:
        raise BuildError("S08-P1 receipts do not share one validation head")
    if len({row.get("validation_run_id") for row in receipts}) != 1:
        raise BuildError("S08-P1 receipts do not share one validation run")
    return receipts


def _task_matrix(final: bool) -> dict[str, Any]:
    common = {
        "execution_status": "EXECUTION_COMPLETE",
        "acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "current_result": "TASK_ACCEPTED" if final else "AWAITING_FINAL_VALIDATION",
    }
    return {
        "schema_version": "kmfa.v015.s08p1.task_acceptance_matrix.v1",
        "phase_id": kernel.RUN_PHASE_ID,
        "roadmap_phase_id": kernel.ROADMAP_PHASE_ID,
        "task_execution_complete_count": 3,
        "task_accepted_count": 3 if final else 0,
        "tasks": [
            {
                "task_id": "S08P1T01",
                "name_zh": "实现组合证据模型",
                "acceptance_zh": "八类证据按可比较字段重新归一化；缺一个字段不使项目失效，低覆盖不得自动合并。",
                "evidence_refs": [MATCHING_MODEL_PATH.relative_to(REPO_ROOT).as_posix()],
                **common,
            },
            {
                "task_id": "S08P1T02",
                "name_zh": "实现名称标准化",
                "acceptance_zh": "原始名称始终保留；简称、括号、空格、错别字、历史名和公司后缀均有可解释步骤。",
                "evidence_refs": [NAME_FIXTURES_PATH.relative_to(REPO_ROOT).as_posix()],
                **common,
            },
            {
                "task_id": "S08P1T03",
                "name_zh": "实现时间和金额辅助匹配",
                "acceptance_zh": "时间和整数分金额只辅助区分；金额单独命中或关键冲突必须人工确认。",
                "evidence_refs": [AUXILIARY_CASES_PATH.relative_to(REPO_ROOT).as_posix()],
                **common,
            },
        ],
    }


def _matching_model(cases: dict[str, Any]) -> dict[str, Any]:
    matches = cases["match_cases"]
    missing = matches["missing_contract_renormalized"]
    low_coverage = matches["low_coverage_fail_closed"]
    return {
        "schema_version": "kmfa.v015.s08p1.matching_model_public_safe.v1",
        "fixture_scope": "PUBLIC_SAFE_SYNTHETIC",
        "component_weights_bps": cases["component_weights_bps"],
        "configured_weight_total_bps": cases["configured_weight_total_bps"],
        "decision_policy": cases["decision_policy"],
        "missing_contract_case": missing,
        "low_coverage_case": low_coverage,
        "acceptance": {
            "missing_contract_available_weight_bps": missing["available_weight_bps"],
            "missing_contract_renormalized_similarity_bps": missing["renormalized_similarity_bps"],
            "missing_contract_auto_merge_allowed": missing["auto_merge_allowed"],
            "low_coverage_renormalized_similarity_bps": low_coverage["renormalized_similarity_bps"],
            "low_coverage_auto_merge_allowed": low_coverage["auto_merge_allowed"],
        },
        "private_business_values_published": False,
    }


def _name_fixtures(cases: dict[str, Any]) -> dict[str, Any]:
    fixtures = cases["name_fixtures"]
    return {
        "schema_version": "kmfa.v015.s08p1.name_normalization_fixtures.v1",
        "fixture_scope": "PUBLIC_SAFE_SYNTHETIC",
        "fixture_count": len(fixtures),
        "raw_name_preserved_count": sum(row["raw_name_preserved"] for row in fixtures),
        "irreversible_overwrite_count": sum(row["irreversible_overwrite_performed"] for row in fixtures),
        "fixtures": fixtures,
        "private_business_values_published": False,
    }


def _auxiliary_cases(cases: dict[str, Any]) -> dict[str, Any]:
    names = ("same_name_time_amount_conflict", "company_conflict", "amount_only")
    selected = {name: cases["match_cases"][name] for name in names}
    return {
        "schema_version": "kmfa.v015.s08p1.auxiliary_matching_cases.v1",
        "fixture_scope": "PUBLIC_SAFE_SYNTHETIC",
        "time_fields": list(kernel.TIME_SUBWEIGHTS_BPS),
        "amount_fields": list(kernel.AMOUNT_SUBWEIGHTS_BPS),
        "amount_unit": "integer_cents",
        "amount_evidence_auxiliary_only": True,
        "amount_alone_decided_match": False,
        "case_count": len(selected),
        "manual_confirmation_count": sum(row["manual_review_required"] for row in selected.values()),
        "cases": selected,
        "private_business_values_published": False,
    }


def _contract(model: dict[str, Any], names: dict[str, Any], auxiliary: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s08p1.project_composite_identity_contract.v1",
        "project_id": "KMFA",
        "target_release": "v1.5",
        "phase_id": kernel.RUN_PHASE_ID,
        "roadmap_phase_id": kernel.ROADMAP_PHASE_ID,
        "component_count": len(kernel.COMPONENT_WEIGHTS_BPS),
        "configured_weight_total_bps": model["configured_weight_total_bps"],
        "missing_weight_renormalization_required": True,
        "minimum_auto_coverage_bps": kernel.MIN_AUTO_COVERAGE_BPS,
        "minimum_auto_primary_match_count": kernel.MIN_AUTO_PRIMARY_MATCH_COUNT,
        "name_fixture_count": names["fixture_count"],
        "raw_name_preserved_count": names["raw_name_preserved_count"],
        "irreversible_overwrite_count": names["irreversible_overwrite_count"],
        "auxiliary_case_count": auxiliary["case_count"],
        "amount_evidence_auxiliary_only": True,
        "amount_alone_decided_match": False,
        "raw_root_access_count": 0,
        "private_business_values_published": False,
        "formal_report_generated": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
    }


def _manifest(
    cases: dict[str, Any],
    model: dict[str, Any],
    names: dict[str, Any],
    auxiliary: dict[str, Any],
    receipts: list[dict[str, Any]],
) -> dict[str, Any]:
    final = bool(receipts)
    match_cases = cases["match_cases"]
    value: dict[str, Any] = {
        "schema_version": "kmfa.v015.s08p1.project_composite_identity_manifest.v1",
        "project_id": "KMFA",
        "target_release": "v1.5",
        "version": kernel.VERSION,
        "stage_id": "S08",
        "phase_id": kernel.RUN_PHASE_ID,
        "roadmap_phase_id": kernel.ROADMAP_PHASE_ID,
        "task_id": kernel.TASK_ID,
        "acceptance_id": kernel.ACCEPTANCE_ID,
        "run_mode": "CONTROLLED_RUN",
        "work_kind": "PRODUCT_IMPLEMENTATION",
        "counted_as_taskpack_phase": True,
        "counted_as_taskpack_task_count": 3,
        "phase_base_commit": PHASE_BASE_COMMIT,
        "dependency": dependency(),
        "phase_execution_status": "EXECUTION_COMPLETE",
        "phase_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "evidence_validation_status": "PASS" if final else "PENDING",
        "task_execution_complete_count": 3,
        "task_accepted_count": 3 if final else 0,
        "component_count": len(kernel.COMPONENT_WEIGHTS_BPS),
        "configured_weight_total_bps": model["configured_weight_total_bps"],
        "name_fixture_count": names["fixture_count"],
        "raw_name_preserved_count": names["raw_name_preserved_count"],
        "irreversible_overwrite_count": names["irreversible_overwrite_count"],
        "match_case_count": len(match_cases),
        "auto_match_case_count": sum(not row["manual_review_required"] for row in match_cases.values()),
        "manual_confirmation_case_count": sum(row["manual_review_required"] for row in match_cases.values()),
        "missing_contract_renormalized_similarity_bps": match_cases["missing_contract_renormalized"]["renormalized_similarity_bps"],
        "missing_contract_auto_merge_allowed": match_cases["missing_contract_renormalized"]["auto_merge_allowed"],
        "low_coverage_auto_merge_allowed": match_cases["low_coverage_fail_closed"]["auto_merge_allowed"],
        "amount_evidence_auxiliary_only": auxiliary["amount_evidence_auxiliary_only"],
        "amount_alone_decided_match": auxiliary["amount_alone_decided_match"],
        "hard_conflict_auto_merge_allowed": match_cases["company_conflict"]["auto_merge_allowed"],
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "stage_execution_percentage": 33,
        "decision": "CONTINUE_TO_S08_P2_ONLY" if final else "REMAIN_IN_S08_P1_FINAL_VALIDATION",
        "s08_p1_started": True,
        "s08_p1_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "s08_p2_entry_allowed": final,
        "s08_p2_started": False,
        "s08_p3_entry_allowed": False,
        "s08_stage_review_entry_allowed": False,
        "overall_accepted_phase_count": 20 if final else 19,
        "overall_taskpack_phase_count": 72,
        "current_private_open_unconfirmed_item_count": 128,
        "current_private_conflict_candidate_count": 6,
        "current_report_display_label_zh": "暂不可使用",
        "current_formal_report_release_allowed": False,
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "source_mutation_performed": False,
        "formal_report_generated": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "validation_receipt_count": len(receipts),
        "validation_failed_count": 0,
    }
    if final:
        value.update(
            {
                "validation_head": receipts[0]["validation_head"],
                "validation_run_id": receipts[0]["validation_run_id"],
                "validation_pass_count": len(receipts),
            }
        )
    return value


def _implementation_report(final: bool) -> str:
    status = "已通过" if final else "等待最终验收"
    return f"""# KMFA v1.5 S08-P1 项目组合识别

- 当前状态：{status}。
- 系统综合合同号、项目名、对手方、公司主体、时间、金额、责任人和来源版本识别项目。
- 缺少字段时只在可比较证据内重新计算相似度，同时保留最低证据覆盖要求，避免少量证据得到虚高结论。
- 原始名称始终保留；简称、括号、空格、已登记错别字、历史名称和公司后缀的处理都有中文解释。
- 时间和金额只辅助判断；金额单独命中、合同或公司主体冲突、证据不足均进入人工确认。
- 本轮未读取原始数据，未开始 S08-P2/P3 或阶段复审，未上传 GitHub，未重装 App。
"""


def _matching_rules() -> str:
    return """# 项目识别规则

1. 八类证据初始权重合计 100%，某项缺失时仅按双方都具备的证据重新计算。
2. 重新计算后的相似度不能替代证据覆盖要求；可比较证据不足 60% 时必须人工确认。
3. 自动匹配至少需要合同号或项目名形成锚点，并至少有两个主要身份字段一致。
4. 合同号或公司主体冲突时必须人工确认。
5. 时间和金额用于区分同名项目；金额永远不能单独决定项目身份。
6. 名称标准化只生成解释明确的标准名称，不覆盖原始名称。
"""


def _test_results(final: bool, receipts: list[dict[str, Any]]) -> str:
    if final:
        return (
            "# 测试结果\n\n"
            f"- 最终验收：{len(receipts)}/{len(EXPECTED_VALIDATION_NAMES)} 全部通过。\n"
            f"- 验收批次：`{receipts[0]['validation_run_id']}`。\n"
            f"- 绑定实现提交：`{receipts[0]['validation_head']}`。\n"
            "- 覆盖缺字段重新归一化、证据覆盖不足、名称可解释转换、时间金额冲突、金额单独命中、关键字段冲突和整数分约束。\n"
        )
    return "# 测试结果\n\n- 实现与阶段证据已生成，等待一次干净提交上的最终验收。\n"


def _open_risks() -> str:
    return """# 开放风险

- 名称规则只能使用经过登记和复核的简称、错别字和历史名称；规则冲突会停止自动匹配，后续由 S08-P3 统一管理阈值与确认质量。
- 公司主体、银行和账户层级尚未实施，按 Roadmap 留给 S08-P2。
- 面向普通用户的并排确认界面和决定持久化尚未实施，按 Roadmap 留给 S08-P3。
- 当前 128 项待确认事项和 6 项冲突仍未关闭，报告继续显示“暂不可使用”。
"""


def _rollback() -> str:
    return """# 回滚方案

- 只撤销 S08-P1 新增内核、测试、公开安全证据和对应治理记录。
- 保留已经通过的 S07 及更早阶段证据。
- 不修改原始数据、私有黄金数据、远端 GitHub 或已安装 App。
"""


def expected_outputs() -> dict[Path, str]:
    cases = kernel.synthetic_acceptance_cases()
    receipts = final_receipts()
    final = bool(receipts)
    model = _matching_model(cases)
    names = _name_fixtures(cases)
    auxiliary = _auxiliary_cases(cases)
    manifest = _manifest(cases, model, names, auxiliary, receipts)
    return {
        TASK_MATRIX_PATH: _dump(_task_matrix(final)),
        MATCHING_MODEL_PATH: _dump(model),
        NAME_FIXTURES_PATH: _dump(names),
        AUXILIARY_CASES_PATH: _dump(auxiliary),
        MANIFEST_PATH: _dump(manifest),
        CONTRACT_PATH: _dump(_contract(model, names, auxiliary)),
        IMPLEMENTATION_REPORT_PATH: _implementation_report(final),
        MATCHING_RULES_PATH: _matching_rules(),
        TEST_RESULTS_PATH: _test_results(final, receipts),
        OPEN_RISKS_PATH: _open_risks(),
        ROLLBACK_PATH: _rollback(),
    }


def write_outputs() -> None:
    for path, content in expected_outputs().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    if not VALIDATION_RESULTS_PATH.exists():
        VALIDATION_RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        VALIDATION_RESULTS_PATH.write_text("", encoding="utf-8")


def check_outputs() -> list[str]:
    mismatches: list[str] = []
    for path, expected in expected_outputs().items():
        if not path.is_file() or path.read_text(encoding="utf-8") != expected:
            mismatches.append(path.relative_to(REPO_ROOT).as_posix())
    if not VALIDATION_RESULTS_PATH.is_file():
        mismatches.append(VALIDATION_RESULTS_PATH.relative_to(REPO_ROOT).as_posix())
    return mismatches


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        if args.check:
            mismatches = check_outputs()
            if mismatches:
                raise BuildError("deterministic output drift: " + ", ".join(mismatches))
            print("PASS: S08-P1 public-safe artifacts match deterministic builder")
        else:
            write_outputs()
            print("PASS: S08-P1 public-safe artifacts written")
    except (OSError, ValueError, KeyError, json.JSONDecodeError, BuildError) as error:
        print(f"FAIL: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
