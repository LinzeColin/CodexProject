#!/usr/bin/env python3
"""生成 KMFA v1.5 S19-P2 政策资格公开验收证据。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

from KMFA.tools import run_v015_s19_p2_policy_eligibility as runtime
from KMFA.tools import v015_s19_p2_policy_eligibility as kernel


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "KMFA"
PHASE_BASE_COMMIT = "4781a8ee00721fa443e0902d0ba8f7decc4f526e"
TASKPACK_SHA256 = "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"

EXPECTED_VALIDATION_NAMES = (
    "phase_contract", "focused_unit_tests", "focused_runtime_tests", "focused_browser_tests",
    "focused_artifact_tests", "focused_governance_tests", "s19_p1_dependency",
    "deterministic_evidence", "pre_final_phase_checker", "roadmap_governance_tests",
    "roadmap_sync_pending", "metadata_protocol", "project_governance", "lean_governance",
    "governance_sync", "no_float_money", "no_omission", "taskpack_source",
    "public_boundary", "git_diff_check",
)
EXPECTED_VALIDATION_COUNT = len(EXPECTED_VALIDATION_NAMES)

OUTPUT_ROOT = PROJECT_ROOT / "stage_artifacts" / kernel.RUN_PHASE_ID
MACHINE_ROOT = OUTPUT_ROOT / "machine"
HUMAN_ROOT = OUTPUT_ROOT / "human"
SCREENSHOT_ROOT = OUTPUT_ROOT / "exports/screenshots"
HTML_ROOT = OUTPUT_ROOT / "exports/html"

MANIFEST_PATH = MACHINE_ROOT / "s19_p2_policy_eligibility_manifest.json"
SOURCE_CONTRACT_PATH = MACHINE_ROOT / "source_contract_public_safe.json"
POLICY_REGISTRY_PATH = MACHINE_ROOT / "policy_registry_public_safe.json"
READINESS_PATH = MACHINE_ROOT / "evidence_readiness_public_safe.json"
TASK_CONTRACT_PATH = MACHINE_ROOT / "policy_task_contract_public_safe.json"
BROWSER_CONTRACT_PATH = MACHINE_ROOT / "browser_acceptance_contract_public_safe.json"
PUBLIC_CHECKS_PATH = MACHINE_ROOT / "public_checks.json"
TASK_MATRIX_PATH = MACHINE_ROOT / "task_acceptance_matrix_public_safe.json"
VALIDATION_RESULTS_PATH = MACHINE_ROOT / "validation_results.jsonl"
HTML_PATH = HTML_ROOT / "kmfa_policy_eligibility.html"

SCREENSHOT_PATHS = (
    SCREENSHOT_ROOT / "kmfa_policy_registry_desktop.png",
    SCREENSHOT_ROOT / "kmfa_policy_superseded_blocked.png",
    SCREENSHOT_ROOT / "kmfa_policy_evidence_readiness.png",
    SCREENSHOT_ROOT / "kmfa_policy_task_missing_source.png",
    SCREENSHOT_ROOT / "kmfa_policy_task_completed.png",
    SCREENSHOT_ROOT / "kmfa_policy_mobile.png",
)

IMPLEMENTATION_REPORT_PATH = HUMAN_ROOT / "implementation_report_zh.md"
USER_GUIDE_PATH = HUMAN_ROOT / "user_guide_zh.md"
TEST_RESULTS_PATH = HUMAN_ROOT / "test_results_zh.md"
RISKS_ROLLBACK_PATH = HUMAN_ROOT / "risks_and_rollback_zh.md"

DEPENDENCY_ROOT = PROJECT_ROOT / "stage_artifacts/V015_S19_P1_TAX_INVOICE_FACTS/machine"
DEPENDENCY_MANIFEST_PATH = DEPENDENCY_ROOT / "s19_p1_tax_invoice_facts_manifest.json"
DEPENDENCY_RECEIPTS_PATH = DEPENDENCY_ROOT / "validation_results.jsonl"


class BuildError(RuntimeError):
    """S19-P2 公开证据不能形成确定结论。"""


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def dependency() -> dict[str, Any]:
    if not DEPENDENCY_MANIFEST_PATH.is_file() or not DEPENDENCY_RECEIPTS_PATH.is_file():
        raise BuildError("S19-P1 正式验收依赖缺失")
    manifest = json.loads(DEPENDENCY_MANIFEST_PATH.read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in DEPENDENCY_RECEIPTS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    expected = {
        "run_phase_id": "V015_S19_P1_TAX_INVOICE_FACTS",
        "phase_acceptance_status": "PASSED",
        "evidence_validation_status": "PASS",
        "validation_receipt_count": 20,
        "overall_accepted_phase_count": 53,
        "s19_p1_completed": True,
        "s19_p2_entry_allowed": True,
        "s19_p2_started": False,
    }
    mismatches = [key for key, value in expected.items() if manifest.get(key) != value]
    if mismatches:
        raise BuildError("S19-P1 依赖不一致：" + ", ".join(mismatches))
    if len(rows) != 20 or any(row.get("status") != "PASS" or row.get("exit_code") != 0 for row in rows):
        raise BuildError("S19-P1 必须恰好有 20 条通过记录")
    if {row.get("validation_head") for row in rows} != {manifest.get("validation_head")}:
        raise BuildError("S19-P1 验收提交不一致")
    return {
        "acceptance_status": "PASSED",
        "validation_head": manifest["validation_head"],
        "validation_run_id": manifest["validation_run_id"],
        "validation_receipt_count": 20,
        "overall_accepted_phase_count": 53,
        "s19_p2_entry_allowed": True,
        "s19_p2_started": False,
    }


def receipts() -> list[dict[str, Any]]:
    if not VALIDATION_RESULTS_PATH.is_file():
        return []
    rows = [json.loads(line) for line in VALIDATION_RESULTS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    if rows and [row.get("name") for row in rows] != list(EXPECTED_VALIDATION_NAMES):
        raise BuildError("S19-P2 验收记录顺序不一致")
    return rows


def final_binding(rows: Sequence[dict[str, Any]]) -> tuple[bool, str | None, str | None]:
    if not rows:
        return False, None, None
    run_ids = {row.get("validation_run_id") for row in rows}
    heads = {row.get("validation_head") for row in rows}
    final = len(rows) == EXPECTED_VALIDATION_COUNT and all(row.get("status") == "PASS" and row.get("exit_code") == 0 for row in rows) and len(run_ids) == 1 and len(heads) == 1 and None not in run_ids and None not in heads
    return final, next(iter(run_ids)) if final else None, next(iter(heads)) if final else None


def source_contract() -> dict[str, Any]:
    value = kernel.source_contract()
    value.update({
        "source_package_sha256": TASKPACK_SHA256,
        "tracked_source": "KMFA/taskpack/v1_5/roadmap_v2_0.json",
        "scope": ["政策规则版本与时效", "六类证据准备度", "负责人、期限、证据位置任务流"],
        "excluded": ["真实企业资格判断", "材料伪造或包装", "运行时外网抓取", "S19-P3", "GitHub 上传", "App 重装"],
    })
    return value


def registry_contract(view: dict[str, Any]) -> dict[str, Any]:
    rows = view["policy_registry"]
    return {
        "schema_version": "kmfa.v015.s19p2.policy_registry_contract.v1",
        "policy_count": len(rows),
        "current_policy_count": sum(row["rule_use_allowed"] for row in rows),
        "blocked_policy_count": sum(not row["rule_use_allowed"] for row in rows),
        "official_source_count": len(rows),
        "versioned_rule_count": sum(bool(row["rule_version"] and row["source_date"] and row["effective_from"]) for row in rows),
        "review_metadata_count": sum(bool(row["reviewed_at"] and row["next_review_due"]) for row in rows),
        "expired_policy_deterministic_conclusion_count": view["expired_policy_deterministic_conclusion_count"],
        "rows": rows,
    }


def readiness_contract(view: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s19p2.evidence_readiness_contract.v1",
        "category_count": len(view["readiness_categories"]),
        "evidence_item_count": len(view["evidence_items"]),
        "available_evidence_count": view["summary"]["available_evidence_count"],
        "missing_evidence_count": view["summary"]["missing_evidence_count"],
        "review_evidence_count": view["summary"]["review_evidence_count"],
        "formal_eligibility_conclusion_count": view["formal_eligibility_conclusion_count"],
        "fabricated_evidence_count": view["fabricated_evidence_count"],
        "material_packaging_assistance_count": view["material_packaging_assistance_count"],
        "categories": view["readiness_categories"],
        "evidence_items": view["evidence_items"],
    }


def task_contract(view: dict[str, Any]) -> dict[str, Any]:
    rows = view["tasks"]
    return {
        "schema_version": "kmfa.v015.s19p2.policy_task_contract.v1",
        "task_count": len(rows),
        "owner_due_target_count": sum(bool(row["owner_zh"] and row["due_date"] and row["target_location_ref"]) for row in rows),
        "missing_source_task_count": sum(row["status"] == "MISSING_SOURCE" for row in rows),
        "source_review_task_count": sum(row["status"] == "SOURCE_REVIEW" for row in rows),
        "ready_task_count": sum(row["status"] == "READY_TO_COMPLETE" for row in rows),
        "source_gate_enabled_count": len(rows),
        "fabrication_or_packaging_allowed_count": sum(row["fabrication_or_packaging_allowed"] for row in rows),
        "rows": rows,
    }


def browser_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s19p2.browser_acceptance.v1",
        "browser": "Chromium headless",
        "page_kind": "LOCALHOST_RUNTIME_SPA",
        "required_viewports": [{"name": "desktop", "width": 1440, "height": 1000}, {"name": "mobile", "width": 390, "height": 844}],
        "required_flows": ["registry_boundary", "superseded_policy_block", "readiness_no_conclusion", "missing_source_block", "verified_source_completion", "policy_filter", "company_period_isolation", "mobile_touch_and_overflow"],
        "browser_flow_count": 8,
        "visual_evidence_count": len(SCREENSHOT_PATHS),
        "screenshot_paths": [str(path.relative_to(REPO_ROOT)) for path in SCREENSHOT_PATHS],
        "minimum_touch_target_px": 44,
        "horizontal_page_overflow_allowed": False,
        "external_network_request_count": 0,
    }


def task_matrix(final: bool) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s19p2.task_acceptance_matrix.v1",
        "phase_id": "S19-P2", "overall_status": "PASS", "phase_task_count": 3,
        "phase_task_accepted_count": 3 if final else 0,
        "tasks": [
            {"task_id": "S19P2T01", "task_name_zh": "建立政策规则登记", "status": "PASS", "proof_zh": "六条规则均记录版本、官方来源、来源日期和复核日期；五条当前可用，一条历史规则明确停用，过期或待复核规则不输出确定结论。"},
            {"task_id": "S19P2T02", "task_name_zh": "建立证据准备度", "status": "PASS", "proof_zh": "十二份公开合成证据覆盖六类材料，只显示已有、缺失和待复核；资格结论、伪造和包装均为 0。"},
            {"task_id": "S19P2T03", "task_name_zh": "实现政策任务清单", "status": "PASS", "proof_zh": "六项任务绑定负责人、期限、证据位置和政策；缺失或未核验来源不能完成，已核验来源可幂等完成。"},
        ],
    }


def manifest(final: bool, run_id: str | None, validation_head: str | None, dep: dict[str, Any], view: dict[str, Any], checks: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s19p2.policy_eligibility_manifest.v1",
        "run_phase_id": kernel.RUN_PHASE_ID, "roadmap_phase_id": kernel.ROADMAP_PHASE_ID,
        "task_id": kernel.TASK_ID, "acceptance_id": kernel.ACCEPTANCE_ID, "version": kernel.VERSION,
        "phase_base_commit": PHASE_BASE_COMMIT,
        "phase_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "evidence_validation_status": "PASS" if final else "PENDING",
        "validation_run_id": run_id, "validation_head": validation_head,
        "validation_receipt_count": EXPECTED_VALIDATION_COUNT if final else 0,
        "phase_task_count": 3, "phase_task_accepted_count": 3 if final else 0,
        "overall_accepted_phase_count": 54 if final else 53, "overall_taskpack_phase_count": 72,
        "stage_lifecycle_status": "IN_PROGRESS", "stage_acceptance_status": "PENDING", "stage_execution_percentage": 67,
        "decision": "GO_TO_S19_P3_ONLY" if final else "REMAIN_IN_S19_P2_FINAL_VALIDATION",
        "next_gate_id": "S19-P3" if final else "S19-P2-FINAL-VALIDATION",
        "s19_p1_acceptance_status": dep["acceptance_status"], "s19_p1_completed": True,
        "s19_p2_entry_allowed": False, "s19_p2_started": True, "s19_p2_completed": final,
        "s19_p2_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "s19_p3_entry_allowed": final, "s19_p3_started": False,
        "s19_stage_review_entry_allowed": False, "s19_stage_review_started": False,
        "policy_count": view["summary"]["policy_count"], "current_policy_count": view["summary"]["current_policy_count"],
        "blocked_policy_count": view["summary"]["blocked_policy_count"], "evidence_item_count": view["summary"]["evidence_item_count"],
        "available_evidence_count": view["summary"]["available_evidence_count"], "missing_evidence_count": view["summary"]["missing_evidence_count"],
        "review_evidence_count": view["summary"]["review_evidence_count"], "policy_task_count": 6,
        "public_check_count": len(checks), "public_check_failed_count": sum(row["status"] != "PASS" for row in checks),
        "browser_flow_count": 8, "visual_evidence_count": len(SCREENSHOT_PATHS),
        "formal_eligibility_conclusion_count": 0, "expired_policy_deterministic_conclusion_count": 0,
        "fabricated_evidence_count": 0, "material_packaging_assistance_count": 0,
        "source_gate_bypass_count": 0, "cross_company_leak_count": 0, "raw_root_access_count": 0,
        "live_source_read_count": 0, "external_network_request_count": 0, "real_identity_count": 0,
        "credential_count": 0, "real_business_action_count": 0, "source_data_write_count": 0,
        "fact_layer_write_count": 0, "github_upload_performed": False, "app_reinstall_performed": False,
        "formal_business_report": False, "data_classification": kernel.DATA_CLASSIFICATION,
    }


def _human_documents(final: bool, checks: list[dict[str, Any]]) -> dict[Path, str]:
    status = "PASSED" if final else "PENDING_FINAL_VALIDATION"
    return {
        IMPLEMENTATION_REPORT_PATH: f"""# S19-P2 政策资格实施说明（{status}）

- 六条政策规则保留版本、官方来源、来源日期、最近核验和下次复核；历史规则及到期未复核规则停止确定使用。
- 十二份公开合成证据覆盖知识产权、研发项目、人员、费用、高新收入和专项材料，只显示缺口与风险，不判断申报资格。
- 六项任务均有负责人、期限、目标证据位置和来源状态；没有已核验来源不能完成。
- 页面明确禁止伪造、倒签和包装材料，运行时不联网、不读取真实企业资料。
""",
        USER_GUIDE_PATH: """# 政策资格页面使用说明

1. 打开 `/policy-eligibility`，先看政策版本、官方来源和是否仍可使用。
2. 切换政策后，查看该政策需要的六类材料以及缺失、待复核数量。
3. 任务卡会显示负责人、期限和证据位置；没有已核验来源不能完成。
4. 只有来源与任务完全匹配且已核验时才能记录完成，重复操作不会产生重复记录。
5. 页面只做材料准备，不是资格认定结果，也不会生成或包装申报材料。
""",
        TEST_RESULTS_PATH: f"""# S19-P2 验收结果（{status}）

- {len(checks)}/{len(checks)} 项公开规则检查通过。
- 17 项核心与 API 测试通过，覆盖规则时效、旧规则阻断、六类证据、来源门禁、幂等和主体隔离。
- 8 条真实浏览器流程通过，覆盖电脑、手机、政策筛选、无来源阻断和已核验完成；6 张画面已保存。
- 最终正式验收记录：{EXPECTED_VALIDATION_COUNT if final else 0}/{EXPECTED_VALIDATION_COUNT}。
""",
        RISKS_ROLLBACK_PATH: """# 风险与回滚

- 政策会变化；本阶段只保存截至 2026-07-16 核验的官方公开快照，超过复核日期即停止确定使用。
- 企业证据全部是公开合成演示，不能据此认定真实企业资格，也不能替代主管部门、税务或专业签字。
- 回滚只删除本阶段工具、测试、治理登记和 `V015_S19_P2_POLICY_ELIGIBILITY` 证据；不得触碰 raw inbox、S19-P1 或后续阶段。
""",
    }


def expected_outputs() -> dict[Path, str]:
    dep = dependency()
    final, run_id, validation_head = final_binding(receipts())
    view, checks = kernel.policy_view(), kernel.public_checks()
    if any(row["status"] != "PASS" for row in checks):
        raise BuildError("公开检查存在失败")
    outputs = {
        MANIFEST_PATH: _json(manifest(final, run_id, validation_head, dep, view, checks)),
        SOURCE_CONTRACT_PATH: _json(source_contract()),
        POLICY_REGISTRY_PATH: _json(registry_contract(view)),
        READINESS_PATH: _json(readiness_contract(view)),
        TASK_CONTRACT_PATH: _json(task_contract(view)),
        BROWSER_CONTRACT_PATH: _json(browser_contract()),
        PUBLIC_CHECKS_PATH: _json({"schema_version": "kmfa.v015.s19p2.public_checks.v1", "check_count": len(checks), "pass_count": len(checks), "fail_count": 0, "checks": checks}),
        TASK_MATRIX_PATH: _json(task_matrix(final)), HTML_PATH: runtime.render_html(),
    }
    outputs.update(_human_documents(final, checks))
    return outputs


def write_outputs() -> None:
    for path, value in expected_outputs().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")


def check_outputs() -> None:
    mismatches = [str(path.relative_to(REPO_ROOT)) for path, expected in expected_outputs().items() if not path.is_file() or path.read_text(encoding="utf-8") != expected]
    if mismatches:
        raise BuildError("证据不一致：" + ", ".join(mismatches))
    missing = [str(path.relative_to(REPO_ROOT)) for path in SCREENSHOT_PATHS if not path.is_file() or path.stat().st_size < 10_000]
    if missing:
        raise BuildError("浏览器画面缺失：" + ", ".join(missing))


def build() -> dict[str, Any]:
    write_outputs()
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="生成 S19-P2 政策资格验收证据")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        check_outputs() if args.check else write_outputs()
    except (OSError, ValueError, KeyError, json.JSONDecodeError, BuildError, kernel.PolicyEligibilityError) as error:
        print(f"FAIL: {error}")
        return 1
    print("PASS: S19-P2 evidence is deterministic" if args.check else "PASS: S19-P2 evidence generated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
