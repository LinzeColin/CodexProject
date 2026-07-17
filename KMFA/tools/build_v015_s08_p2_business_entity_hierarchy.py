#!/usr/bin/env python3
"""Build deterministic public-safe evidence for KMFA v1.5 S08-P2."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from KMFA.tools import v015_s08_p2_business_entity_hierarchy as kernel


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "KMFA"
PHASE_BASE_COMMIT = "42ca10ec915335f87fdb549cc406c144542e4acd"

OUTPUT_ROOT = PROJECT_ROOT / "stage_artifacts" / "V015_S08_P2_BUSINESS_ENTITY_HIERARCHY"
MACHINE_ROOT = OUTPUT_ROOT / "machine"
HUMAN_ROOT = OUTPUT_ROOT / "human"
MANIFEST_PATH = MACHINE_ROOT / "s08_p2_business_entity_hierarchy_manifest.json"
TASK_MATRIX_PATH = MACHINE_ROOT / "task_acceptance_matrix_public_safe.json"
COMPANY_MODEL_PATH = MACHINE_ROOT / "company_entity_model_public_safe.json"
ACCOUNT_DIRECTORY_PATH = MACHINE_ROOT / "bank_account_directory_public_safe.json"
COUNTERPARTY_MASTER_PATH = MACHINE_ROOT / "counterparty_master_public_safe.json"
VALIDATION_RESULTS_PATH = MACHINE_ROOT / "validation_results.jsonl"
CONTRACT_PATH = PROJECT_ROOT / "metadata" / "quality" / "v015_s08_p2_business_entity_hierarchy_public_safe.json"

IMPLEMENTATION_REPORT_PATH = HUMAN_ROOT / "implementation_report_zh.md"
ENTITY_ACCOUNT_RULES_PATH = HUMAN_ROOT / "entity_account_rules_zh.md"
TEST_RESULTS_PATH = HUMAN_ROOT / "test_results_zh.md"
OPEN_RISKS_PATH = HUMAN_ROOT / "open_risks_zh.md"
ROLLBACK_PATH = HUMAN_ROOT / "rollback_plan_zh.md"

S08_P1_MANIFEST_PATH = (
    PROJECT_ROOT
    / "stage_artifacts/V015_S08_P1_PROJECT_COMPOSITE_IDENTITY/machine/s08_p1_project_composite_identity_manifest.json"
)
S08_P1_RECEIPTS_PATH = (
    PROJECT_ROOT / "stage_artifacts/V015_S08_P1_PROJECT_COMPOSITE_IDENTITY/machine/validation_results.jsonl"
)

EXPECTED_VALIDATION_NAMES = (
    "focused_kernel_tests",
    "focused_artifact_tests",
    "focused_governance_tests",
    "pre_final_phase_checker",
    "s08_p1_dependency_check",
    "legacy_business_entity_regression",
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
    manifest = _json(S08_P1_MANIFEST_PATH)
    receipts = _jsonl(S08_P1_RECEIPTS_PATH)
    required = {
        "phase_id": "V015_S08_P1_PROJECT_COMPOSITE_IDENTITY",
        "roadmap_phase_id": "S08-P1",
        "phase_acceptance_status": "PASSED",
        "evidence_validation_status": "PASS",
        "decision": "CONTINUE_TO_S08_P2_ONLY",
        "s08_p2_entry_allowed": True,
        "s08_p2_started": False,
        "validation_receipt_count": 19,
        "overall_accepted_phase_count": 20,
    }
    mismatches = [key for key, value in required.items() if manifest.get(key) != value]
    if mismatches:
        raise BuildError("S08-P1 dependency mismatch: " + ", ".join(mismatches))
    if len(receipts) != 19 or any(row.get("status") != "PASS" or row.get("exit_code") != 0 for row in receipts):
        raise BuildError("S08-P1 receipt set is not exactly 19 PASS records")
    if {row.get("validation_head") for row in receipts} != {manifest.get("validation_head")}:
        raise BuildError("S08-P1 validation head mismatch")
    if {row.get("validation_run_id") for row in receipts} != {manifest.get("validation_run_id")}:
        raise BuildError("S08-P1 validation run mismatch")
    return {
        "phase_id": manifest["phase_id"],
        "acceptance_status": manifest["phase_acceptance_status"],
        "validation_head": manifest["validation_head"],
        "validation_run_id": manifest["validation_run_id"],
        "validation_receipt_count": len(receipts),
        "s08_p2_entry_allowed": True,
        "s08_p2_started": False,
    }


def final_receipts() -> list[dict[str, Any]]:
    receipts = _jsonl(VALIDATION_RESULTS_PATH)
    if not receipts:
        return []
    if len(receipts) != len(EXPECTED_VALIDATION_NAMES):
        raise BuildError("S08-P2 validation receipt count mismatch")
    if [row.get("name") for row in receipts] != list(EXPECTED_VALIDATION_NAMES):
        raise BuildError("S08-P2 validation receipt order mismatch")
    if any(row.get("status") != "PASS" or row.get("exit_code") != 0 for row in receipts):
        raise BuildError("S08-P2 validation receipt set contains a failure")
    if len({row.get("validation_head") for row in receipts}) != 1:
        raise BuildError("S08-P2 receipts do not share one validation head")
    if len({row.get("validation_run_id") for row in receipts}) != 1:
        raise BuildError("S08-P2 receipts do not share one validation run")
    return receipts


def _company_model(cases: dict[str, Any]) -> dict[str, Any]:
    registry = cases["company_registry"]
    assignments = cases["entity_assignment_cases"]
    return {
        "schema_version": "kmfa.v015.s08p2.company_entity_model_public_safe.v1",
        "fixture_scope": "PUBLIC_SAFE_SYNTHETIC",
        "company_registry": registry,
        "entity_assignment_cases": assignments,
        "valid_funds_aggregation": cases["valid_funds_aggregation"],
        "unknown_entity_funds_aggregation": cases["unknown_entity_funds_aggregation"],
        "acceptance": {
            "company_entity_count": registry["company_entity_count"],
            "company_relationship_count": registry["company_relationship_count"],
            "assignment_case_count": len(assignments),
            "assigned_count": sum(row["assignment_status"] == "ASSIGNED" for row in assignments),
            "requires_confirmation_count": sum(
                row["assignment_status"] == "REQUIRES_CONFIRMATION" for row in assignments
            ),
            "unknown_entity_funds_aggregation_allowed": False,
            "partial_aggregation_performed": False,
        },
        "private_business_values_published": False,
    }


def _account_directory(cases: dict[str, Any]) -> dict[str, Any]:
    directory = cases["account_directory"]
    resolution = cases["account_resolution_cases"]
    return {
        "schema_version": "kmfa.v015.s08p2.bank_account_directory_public_safe.v1",
        "fixture_scope": "PUBLIC_SAFE_SYNTHETIC",
        "directory": directory,
        "resolution_cases": resolution,
        "acceptance": {
            "bank_count": directory["bank_count"],
            "account_count": directory["account_count"],
            "masked_account_count": directory["masked_account_count"],
            "public_full_account_value_count": directory["public_full_account_value_count"],
            "same_entity_resolution_status": resolution["same_entity_resolved"]["status"],
            "cross_entity_resolution_status": resolution["cross_entity_high_risk"]["status"],
            "cross_entity_funds_aggregation_allowed": resolution["cross_entity_high_risk"][
                "funds_aggregation_allowed"
            ],
            "ambiguous_alias_status": resolution["ambiguous_requires_confirmation"]["status"],
        },
        "private_business_values_published": False,
    }


def _counterparty_master(cases: dict[str, Any]) -> dict[str, Any]:
    master = cases["counterparty_master"]
    resolution = cases["counterparty_resolution_cases"]
    return {
        "schema_version": "kmfa.v015.s08p2.counterparty_master_public_safe.v1",
        "fixture_scope": "PUBLIC_SAFE_SYNTHETIC",
        "master": master,
        "resolution_cases": resolution,
        "acceptance": {
            "counterparty_master_count": master["counterparty_master_count"],
            "multi_role_counterparty_count": master["multi_role_counterparty_count"],
            "historical_name_count": master["historical_name_count"],
            "forced_merge_count": master["forced_merge_count"],
            "same_name_status": resolution["same_name_not_force_merged"]["status"],
            "historical_name_status": resolution["historical_name_resolved"]["status"],
        },
        "private_business_values_published": False,
    }


def _task_matrix(final: bool) -> dict[str, Any]:
    common = {
        "execution_status": "EXECUTION_COMPLETE",
        "acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "current_result": "TASK_ACCEPTED" if final else "AWAITING_FINAL_VALIDATION",
    }
    return {
        "schema_version": "kmfa.v015.s08p2.task_acceptance_matrix.v1",
        "phase_id": kernel.RUN_PHASE_ID,
        "roadmap_phase_id": kernel.ROADMAP_PHASE_ID,
        "task_execution_complete_count": 3,
        "task_accepted_count": 3 if final else 0,
        "tasks": [
            {
                "task_id": "S08P2T01",
                "name_zh": "建立公司主体模型",
                "acceptance_zh": "每笔记录明确公司主体或待确认；主体不明的资金整批禁止汇总。",
                "evidence_refs": [COMPANY_MODEL_PATH.relative_to(REPO_ROOT).as_posix()],
                **common,
            },
            {
                "task_id": "S08P2T02",
                "name_zh": "建立银行与账户模型",
                "acceptance_zh": "账户按公司和银行分层；公开账号全部脱敏；跨公司误匹配高危阻断。",
                "evidence_refs": [ACCOUNT_DIRECTORY_PATH.relative_to(REPO_ROOT).as_posix()],
                **common,
            },
            {
                "task_id": "S08P2T03",
                "name_zh": "建立客户与对手方模型",
                "acceptance_zh": "客户、甲方、供应商、外协方和历史名可统一登记且角色关系保留多值。",
                "evidence_refs": [COUNTERPARTY_MASTER_PATH.relative_to(REPO_ROOT).as_posix()],
                **common,
            },
        ],
    }


def _contract(company: dict[str, Any], account: dict[str, Any], counterparty: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s08p2.business_entity_hierarchy_contract.v1",
        "project_id": "KMFA",
        "target_release": "v1.5",
        "phase_id": kernel.RUN_PHASE_ID,
        "roadmap_phase_id": kernel.ROADMAP_PHASE_ID,
        "company_entity_count": company["acceptance"]["company_entity_count"],
        "company_relationship_count": company["acceptance"]["company_relationship_count"],
        "unknown_entity_funds_aggregation_allowed": False,
        "bank_count": account["acceptance"]["bank_count"],
        "account_count": account["acceptance"]["account_count"],
        "masked_account_count": account["acceptance"]["masked_account_count"],
        "public_full_account_value_count": 0,
        "cross_entity_account_match_is_high_risk": True,
        "cross_entity_funds_aggregation_allowed": False,
        "counterparty_master_count": counterparty["acceptance"]["counterparty_master_count"],
        "multi_role_counterparty_count": counterparty["acceptance"]["multi_role_counterparty_count"],
        "forced_counterparty_merge_count": 0,
        "raw_root_access_count": 0,
        "private_business_values_published": False,
        "formal_report_generated": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
    }


def _manifest(
    company: dict[str, Any],
    account: dict[str, Any],
    counterparty: dict[str, Any],
    receipts: list[dict[str, Any]],
) -> dict[str, Any]:
    final = bool(receipts)
    value: dict[str, Any] = {
        "schema_version": "kmfa.v015.s08p2.business_entity_hierarchy_manifest.v1",
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
        "company_entity_count": company["acceptance"]["company_entity_count"],
        "company_relationship_count": company["acceptance"]["company_relationship_count"],
        "entity_assignment_case_count": company["acceptance"]["assignment_case_count"],
        "entity_requires_confirmation_count": company["acceptance"]["requires_confirmation_count"],
        "unknown_entity_funds_aggregation_allowed": False,
        "partial_funds_aggregation_performed": False,
        "bank_count": account["acceptance"]["bank_count"],
        "account_count": account["acceptance"]["account_count"],
        "masked_account_count": account["acceptance"]["masked_account_count"],
        "public_full_account_value_count": 0,
        "same_entity_account_resolution_status": account["acceptance"]["same_entity_resolution_status"],
        "cross_entity_account_resolution_status": account["acceptance"]["cross_entity_resolution_status"],
        "cross_entity_funds_aggregation_allowed": False,
        "ambiguous_account_alias_status": account["acceptance"]["ambiguous_alias_status"],
        "counterparty_master_count": counterparty["acceptance"]["counterparty_master_count"],
        "multi_role_counterparty_count": counterparty["acceptance"]["multi_role_counterparty_count"],
        "historical_name_count": counterparty["acceptance"]["historical_name_count"],
        "forced_counterparty_merge_count": 0,
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "stage_execution_percentage": 67,
        "decision": "CONTINUE_TO_S08_P3_ONLY" if final else "REMAIN_IN_S08_P2_FINAL_VALIDATION",
        "s08_p1_acceptance_status": "PASSED",
        "s08_p2_started": True,
        "s08_p2_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "s08_p3_entry_allowed": final,
        "s08_p3_started": False,
        "s08_stage_review_entry_allowed": False,
        "overall_accepted_phase_count": 21 if final else 20,
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
    return f"""# KMFA v1.5 S08-P2 公司、账户与往来方归属

- 当前状态：{status}。
- 每笔资金必须先归到已登记公司；公司不明时整批停止汇总，不会给出残缺合计。
- 银行账户按“公司 → 银行 → 账户”登记；公开材料只保留末四位，完整账号不进入公开仓库。
- 账户别名只能在预期公司内匹配；匹配到另一家公司时按高风险失败处理。
- 同一客户或供应商可以同时有多个角色和多种关系；同名但编号不同的往来方不会被强制合并。
- 本轮没有读取原始资料，没有开始 S08-P3 或阶段复审，没有上传 GitHub，也没有重装 App。
"""


def _rules() -> str:
    return """# 公司、账户与往来方规则

1. 每笔记录只能是“已归属公司”或“等待确认”，不能把主体不明的资金混入汇总。
2. 金额一律使用整数分；只要一笔资金的公司不明确，整批汇总停止，不返回部分结果。
3. 账户必须同时归属一家已登记公司和一家已登记银行；公开账号统一显示为 `****末四位`。
4. 账户别名命中其他公司时属于高风险错误，禁止继续汇总；别名有歧义时转人工确认。
5. 客户、甲方、供应商和外协方的角色及关系都可以多选；历史名称可用于查找，但同名不等于同一主体。
"""


def _test_results(final: bool, receipts: list[dict[str, Any]]) -> str:
    if not final:
        return "# 测试结果\n\n- 实现和公开安全证据已生成，等待一次干净提交上的最终验收。\n"
    return (
        "# 测试结果\n\n"
        f"- 最终验收：{len(receipts)}/{len(EXPECTED_VALIDATION_NAMES)} 全部通过。\n"
        f"- 验收批次：`{receipts[0]['validation_run_id']}`。\n"
        f"- 绑定实现提交：`{receipts[0]['validation_head']}`。\n"
        "- 已覆盖主体缺失阻断、整数分汇总、账号脱敏、同公司匹配、跨公司高风险失败、别名歧义、历史名称和多角色不强制合并。\n"
    )


def _open_risks() -> str:
    return """# 开放风险

- 本阶段只建立规则和公开安全模拟证据；128 项待确认事项与 6 项冲突没有被当作已解决，报告仍为“暂不可使用”。
- 完整账号必须只留在受控私有空间；公开目录只允许账户编号、公司编号、银行编号、别名和末四位。
- 自动/候选/人工三类阈值、普通用户确认界面和决定事件留给 S08-P3，本轮不提前实现。
"""


def _rollback() -> str:
    return """# 回滚方案

- 只撤销 S08-P2 新增内核、测试、公开安全证据和对应治理记录。
- 保留已经通过的 S08-P1 及更早阶段证据。
- 不修改原始资料、私有黄金数据、远端 GitHub 或已安装 App。
"""


def expected_outputs() -> dict[Path, str]:
    cases = kernel.synthetic_acceptance_cases()
    receipts = final_receipts()
    final = bool(receipts)
    company = _company_model(cases)
    account = _account_directory(cases)
    counterparty = _counterparty_master(cases)
    return {
        COMPANY_MODEL_PATH: _dump(company),
        ACCOUNT_DIRECTORY_PATH: _dump(account),
        COUNTERPARTY_MASTER_PATH: _dump(counterparty),
        TASK_MATRIX_PATH: _dump(_task_matrix(final)),
        MANIFEST_PATH: _dump(_manifest(company, account, counterparty, receipts)),
        CONTRACT_PATH: _dump(_contract(company, account, counterparty)),
        IMPLEMENTATION_REPORT_PATH: _implementation_report(final),
        ENTITY_ACCOUNT_RULES_PATH: _rules(),
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
    mismatches = [
        path.relative_to(REPO_ROOT).as_posix()
        for path, expected in expected_outputs().items()
        if not path.is_file() or path.read_text(encoding="utf-8") != expected
    ]
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
            print("PASS: S08-P2 public-safe artifacts match deterministic builder")
        else:
            write_outputs()
            print("PASS: S08-P2 public-safe artifacts written")
    except (OSError, ValueError, KeyError, json.JSONDecodeError, BuildError) as error:
        print(f"FAIL: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
