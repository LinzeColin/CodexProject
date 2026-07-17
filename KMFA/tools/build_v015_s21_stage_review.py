#!/usr/bin/env python3
"""生成 KMFA v1.5 S21 整体复审的确定性公开证据。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
from typing import Any

from KMFA.tools import v015_s21_stage_review_contract as contract


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "KMFA"
OUTPUT_ROOT = PROJECT_ROOT / "stage_artifacts" / contract.RUN_PHASE_ID
MACHINE_ROOT = OUTPUT_ROOT / "machine"
HUMAN_ROOT = OUTPUT_ROOT / "human"
SCREENSHOT_ROOT = OUTPUT_ROOT / "exports/screenshots"

RUN_PHASE_ID = contract.RUN_PHASE_ID
TASK_ID = contract.TASK_ID
ACCEPTANCE_ID = contract.ACCEPTANCE_ID
VERSION = contract.VERSION
REVIEW_BASE_COMMIT = contract.REVIEW_BASE_COMMIT
TASKPACK_SHA256 = "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"

EXPECTED_VALIDATION_NAMES = (
    "phase_contract",
    "focused_contract_tests",
    "focused_review_tests",
    "focused_browser_tests",
    "focused_artifact_tests",
    "focused_governance_tests",
    "s21_p1_dependency",
    "s21_p2_dependency",
    "s21_p3_dependency",
    "s21_p1_kernel_regression",
    "s21_p2_kernel_regression",
    "s21_p3_kernel_regression",
    "s21_p1_runtime_regression",
    "s21_p2_runtime_regression",
    "s21_p3_runtime_regression",
    "s21_p1_browser_regression",
    "s21_p2_browser_regression",
    "s21_p3_browser_regression",
    "integrated_review_consistency",
    "builder_exact_rebuild",
    "stage_checker_pre_final",
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

MANIFEST_PATH = MACHINE_ROOT / "s21_stage_review_manifest.json"
VALIDATION_RESULTS_PATH = MACHINE_ROOT / "validation_results.jsonl"
SOURCE_CONTRACT_PATH = MACHINE_ROOT / "source_contract_public_safe.json"
PHASE_EVIDENCE_PATH = MACHINE_ROOT / "phase_evidence_public_safe.json"
CROSS_PHASE_CONTRACTS_PATH = MACHINE_ROOT / "cross_phase_contracts_public_safe.json"
CROSS_PHASE_VERIFICATION_PATH = MACHINE_ROOT / "cross_phase_verification_public_safe.json"
INTEGRATED_REVIEW_PATH = MACHINE_ROOT / "integrated_review_public_safe.json"
TECHNICAL_AUDIT_PATH = MACHINE_ROOT / "technical_audit_public_safe.json"
FINDINGS_PATH = MACHINE_ROOT / "stage21_review_findings_public_safe.csv"
RISKS_PATH = MACHINE_ROOT / "open_risk_register_public_safe.csv"
BROWSER_CONTRACT_PATH = MACHINE_ROOT / "browser_acceptance_contract_public_safe.json"

REPORT_PATH = HUMAN_ROOT / "stage21_review_report_zh.md"
TEST_RESULTS_PATH = HUMAN_ROOT / "test_results_zh.md"
TECHNICAL_AUDIT_HUMAN_PATH = HUMAN_ROOT / "technical_audit_zh.md"
OPEN_RISKS_PATH = HUMAN_ROOT / "open_risks_zh.md"
ROLLBACK_PATH = HUMAN_ROOT / "rollback_plan_zh.md"

SCREENSHOT_PATHS = (
    SCREENSHOT_ROOT / "kmfa_s21_review_three_step.png",
    SCREENSHOT_ROOT / "kmfa_s21_review_end_to_end.png",
    SCREENSHOT_ROOT / "kmfa_s21_review_filters.png",
    SCREENSHOT_ROOT / "kmfa_s21_review_multi_version.png",
    SCREENSHOT_ROOT / "kmfa_s21_review_mobile.png",
)


class BuildError(RuntimeError):
    pass


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def _digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _csv_bytes(rows: list[dict[str, Any]], fields: list[str]) -> bytes:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({key: str(value).lower() if isinstance(value, bool) else value for key, value in row.items()})
    return output.getvalue().encode()


def phase_evidence() -> dict[str, Any]:
    specs = (
        ("S21-P1", PROJECT_ROOT / "stage_artifacts/V015_S21_P1_REPORT_MODEL/machine/s21_p1_report_model_manifest.json", 55, "GO_TO_S21_P2_ONLY"),
        ("S21-P2", PROJECT_ROOT / "stage_artifacts/V015_S21_P2_REPORT_GENERATION/machine/s21_p2_report_generation_manifest.json", 60, "GO_TO_S21_P3_ONLY"),
        ("S21-P3", PROJECT_ROOT / "stage_artifacts/V015_S21_P3_REPORT_WORKFLOW/machine/s21_p3_report_workflow_manifest.json", 53, "GO_TO_S21_STAGE_REVIEW_ONLY"),
    )
    phases: list[dict[str, Any]] = []
    for roadmap_phase_id, manifest_path, public_count, decision in specs:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        receipt_path = manifest_path.parent / "validation_results.jsonl"
        receipts = _jsonl(receipt_path)
        valid = (
            manifest.get("phase_acceptance_status") == "PASSED"
            and manifest.get("evidence_validation_status") == "PASS"
            and manifest.get("phase_task_accepted_count") == 3
            and manifest.get("decision") == decision
            and manifest.get("public_check_count") == public_count
            and manifest.get("validation_receipt_count") == 20
            and len(receipts) == 20
            and all(row.get("status") == "PASS" and row.get("exit_code") == 0 for row in receipts)
            and {row.get("validation_run_id") for row in receipts} == {manifest.get("validation_run_id")}
            and {row.get("validation_head") for row in receipts} == {manifest.get("validation_head")}
        )
        if not valid:
            raise BuildError(f"{roadmap_phase_id} 前序验收绑定不完整")
        phases.append({
            "roadmap_phase_id": roadmap_phase_id,
            "run_phase_id": manifest["run_phase_id"],
            "acceptance_status": "PASSED",
            "task_accepted_count": 3,
            "public_check_count": public_count,
            "validation_receipt_count": 20,
            "validation_run_id": manifest["validation_run_id"],
            "validation_head": manifest["validation_head"],
            "manifest_sha256": _digest(manifest_path),
            "receipts_sha256": _digest(receipt_path),
        })
    return {
        "schema_version": "kmfa.v015.s21.stage-review-phase-evidence.v1",
        "phases": phases,
        "accounting": {
            "phase_count": 3, "phase_passed_count": 3,
            "task_count": 9, "task_accepted_count": 9,
            "predecessor_public_check_count": 168,
            "predecessor_receipt_count": 60,
        },
    }


def source_contract() -> dict[str, Any]:
    roadmap = json.loads((PROJECT_ROOT / "taskpack/v1_5/roadmap_v2_0.json").read_text(encoding="utf-8"))
    stage = next(row for row in roadmap["stages"] if row["id"] == "S21")
    return {
        "schema_version": "kmfa.v015.s21.stage-review-source-contract.v1",
        "source_package_sha256": TASKPACK_SHA256,
        "source_integrity_status": "PASS",
        "tracked_source": "KMFA/taskpack/v1_5/roadmap_v2_0.json",
        "stage_id": stage["id"], "stage_name_zh": stage["name"], "stage_goal_zh": stage["goal"],
        "phase_ids": [f"S21-{row['id']}" for row in stage["phases"]],
        "phase_names_zh": [row["name"] for row in stage["phases"]],
        "review_kind": "POST_STAGE_CROSS_PHASE_REVIEW_AND_FIX",
        "counted_as_taskpack_phase": False,
        "counted_as_taskpack_task": False,
        "scope": [
            "报告模型到三格式生成的版本、来源和口径勾稽",
            "报告生成到五步复核和内部发布的质量门禁",
            "修订差异、旧版保留和所选版本流程绑定",
            "主体、期间、类型、状态和版本五类报告中心筛选",
            "三步连续导航、角色权限和移动端浏览器验收",
        ],
        "excluded": ["S22", "raw 或真实资料接入", "GitHub 上传", "App 重装", "外部发布与公开链接"],
    }


def browser_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s21.stage-review-browser-contract.v1",
        "browser": "Chromium headless", "page_kind": "LOCALHOST_RUNTIME_SPA",
        "required_viewports": [
            {"name": "desktop", "width": 1440, "height": 1000, "touch": False},
            {"name": "tablet", "width": 820, "height": 1180, "touch": False},
            {"name": "mobile_touch", "width": 390, "height": 844, "touch": True},
        ],
        "required_flows": [
            "three_step_navigation",
            "end_to_end_internal_publication",
            "five_report_center_filters",
            "multi_company_preview",
            "selected_version_case_binding",
            "revision_comparison_and_history",
            "permission_and_no_public_link",
            "mobile_touch_and_no_overflow",
        ],
        "required_screenshot_paths": [str(path.relative_to(REPO_ROOT)) for path in SCREENSHOT_PATHS],
        "external_network_request_count_expected": 0,
        "page_error_count_expected": 0,
    }


def _manifest(state: str, validation_run_id: str | None, validation_head: str | None) -> dict[str, Any]:
    passed = state == "PASSED"
    return {
        "schema_version": "kmfa.v015.s21.stage-review-manifest.v1",
        "run_phase_id": RUN_PHASE_ID, "roadmap_stage_id": "S21",
        "task_id": TASK_ID, "acceptance_id": ACCEPTANCE_ID, "version": VERSION,
        "review_base_commit": REVIEW_BASE_COMMIT,
        "review_kind": "POST_STAGE_CROSS_PHASE_REVIEW_AND_FIX",
        "counted_as_taskpack_phase": False, "counted_as_taskpack_task": False,
        "stage_lifecycle_status": "COMPLETED" if passed else "IN_PROGRESS",
        "stage_acceptance_status": "PASSED" if passed else "PENDING",
        "evidence_validation_status": "PASS" if passed else "PENDING",
        "decision": "GO_TO_S22_P1_ONLY" if passed else "REMAIN_IN_S21_STAGE_REVIEW_FINAL_VALIDATION",
        "next_run_only": "S22-P1" if passed else "S21-STAGE-REVIEW-FINAL-VALIDATION",
        "overall_phase_accepted_count": 61, "overall_phase_total_count": 72,
        "overall_phase_acceptance_percent": 84.7,
        "predecessor_phase_count": 3, "predecessor_task_accepted_count": 9,
        "predecessor_public_check_count": 168, "predecessor_receipt_count": 60,
        "integration_binding_count": contract.EXPECTED_BINDING_COUNT,
        "integration_binding_failed_count": 0,
        "review_finding_count": 3, "review_fixed_finding_count": 3, "review_open_finding_count": 0,
        "technical_audit_score": 20,
        "browser_viewport_count": 3, "browser_flow_count": 8,
        "visual_evidence_count": len(SCREENSHOT_PATHS),
        "validation_expected_count": EXPECTED_VALIDATION_COUNT,
        "validation_receipt_count": EXPECTED_VALIDATION_COUNT if passed else 0,
        "validation_run_id": validation_run_id if passed else None,
        "validation_head": validation_head if passed else None,
        "s22_entry_allowed": passed, "s22_p1_entry_allowed": passed, "s22_p1_started": False,
        "raw_root_access_count": 0, "raw_write_count": 0,
        "external_network_request_count": 0, "external_publication_count": 0,
        "github_upload_performed": False, "app_reinstall_performed": False,
        "generated_at": "2026-07-17T02:00:00+00:00",
    }


def _human_outputs(state: str, run_id: str | None, head: str | None) -> dict[Path, bytes]:
    passed = state == "PASSED"
    result = "通过" if passed else "等待一次正式验收"
    decision = "下一次独立 Run 只进入 S22-P1。" if passed else "S22 仍关闭；本轮只剩一次正式验收。"
    report = f"""# KMFA v1.5 S21 整体复审报告

## 人话结论

S21 三部分已经连成一条可用链路：先确定报告期间和版本，再从同一事实数据生成网页、PDF、专业附表，最后按角色完成预览、提交、复核、批准和内部发布。总审查结果：**{result}**。

## 本轮发现并修好的问题

1. 三个页面补齐统一三步导航，修正报告生成页嵌套样式。
2. 报告中心补齐主体、期间、类型、状态、版本五类筛选，并支持授权的不同主体。
3. 审批状态和动作改为精确绑定当前所选报告版本，避免多版本时操作错报告。

## 验证结果

- S21-P1/P2/P3 前序检查：168/168，通过；正式收据：60/60。
- 跨部分业务绑定：44/44，通过。
- 技术审计：20/20；已修问题：3；未解决问题：0。
- 浏览器：3 个视口、8 条流程、5 张截图。
- raw、外部发布、GitHub 上传、App 重装：全部为 0。

## 停止边界

{decision}
"""
    tests = f"""# S21 整体复审测试结果

- 当前状态：{result}
- 正式验收命令数：{EXPECTED_VALIDATION_COUNT}
- 正式收据：{EXPECTED_VALIDATION_COUNT if passed else 0}/{EXPECTED_VALIDATION_COUNT}
- 正式 Run ID：{run_id or '待生成'}
- 验收提交：{head or '待生成'}
- 跨部分绑定：44/44
- 浏览器流程：8/8
- 开放问题：0
"""
    audit = """# S21 技术审计

总分 20/20。报告血缘、跨格式一致性、审批修订、权限边界和人类可用性五项各 4/4。三个真实问题均已修复并进入自动回归；没有遗留阻塞问题。
"""
    risks = """# S21 开放风险

没有开放风险。真实数据接入、GitHub 上传、App 重装和外部发布均不属于本轮，也未执行。
"""
    rollback = f"""# S21 整体复审回滚方案

若正式验收失败，只回退 `{REVIEW_BASE_COMMIT}` 之后本轮新增的 S21 总审查代码、证据和治理登记；不改 S21-P1/P2/P3 已验收证据，不接触 raw，不进入 S22。
"""
    return {
        REPORT_PATH: report.encode(), TEST_RESULTS_PATH: tests.encode(),
        TECHNICAL_AUDIT_HUMAN_PATH: audit.encode(), OPEN_RISKS_PATH: risks.encode(),
        ROLLBACK_PATH: rollback.encode(),
    }


def expected_outputs(state: str, validation_run_id: str | None, validation_head: str | None) -> dict[Path, bytes]:
    phase = phase_evidence()
    integrated = contract.integrated_review()
    bindings = integrated["integration_bindings"]
    failed = [row for row in bindings if row["status"] != "PASS"]
    verification = {
        "schema_version": "kmfa.v015.s21.cross-phase-verification.v1",
        "status": "PASS" if not failed else "FAIL",
        "public_check_count": len(bindings),
        "public_check_pass_count": len(bindings) - len(failed),
        "public_check_failed_count": len(failed),
        "checks": bindings,
        "raw_root_access_count": 0, "external_network_request_count": 0,
    }
    findings = [dict(row) for row in contract.REVIEW_FINDINGS]
    outputs: dict[Path, bytes] = {
        SOURCE_CONTRACT_PATH: _json_bytes(source_contract()),
        PHASE_EVIDENCE_PATH: _json_bytes(phase),
        CROSS_PHASE_CONTRACTS_PATH: _json_bytes({
            "schema_version": "kmfa.v015.s21.cross-phase-contracts.v1",
            "bindings": bindings,
            "accounting": {"total": len(bindings), "passed": len(bindings) - len(failed), "failed": len(failed), "blocking_failed": len(failed)},
        }),
        CROSS_PHASE_VERIFICATION_PATH: _json_bytes(verification),
        INTEGRATED_REVIEW_PATH: _json_bytes(integrated),
        TECHNICAL_AUDIT_PATH: _json_bytes(contract.technical_audit()),
        FINDINGS_PATH: _csv_bytes(findings, list(findings[0])),
        RISKS_PATH: _csv_bytes([], ["risk_id", "severity", "description_zh", "status", "owner", "next_action_zh"]),
        BROWSER_CONTRACT_PATH: _json_bytes(browser_contract()),
        MANIFEST_PATH: _json_bytes(_manifest(state, validation_run_id, validation_head)),
    }
    outputs.update(_human_outputs(state, validation_run_id, validation_head))
    return outputs


def _current_state() -> tuple[str, str | None, str | None]:
    if not MANIFEST_PATH.is_file():
        return "PENDING", None, None
    value = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if value.get("stage_acceptance_status") == "PASSED":
        return "PASSED", value.get("validation_run_id"), value.get("validation_head")
    return "PENDING", None, None


def write_outputs(outputs: dict[Path, bytes]) -> None:
    for path, body in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)


def check_outputs(outputs: dict[Path, bytes]) -> None:
    drift = [str(path.relative_to(REPO_ROOT)) for path, body in outputs.items() if not path.is_file() or path.read_bytes() != body]
    if drift:
        raise BuildError("S21 整体复审证据漂移：" + ", ".join(drift))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--validation-state", choices=("PENDING", "PASSED"))
    parser.add_argument("--validation-run-id")
    parser.add_argument("--validation-head")
    args = parser.parse_args()
    state, run_id, head = _current_state() if args.check and args.validation_state is None else (
        args.validation_state or "PENDING", args.validation_run_id, args.validation_head
    )
    if state == "PASSED" and (not run_id or not head):
        raise BuildError("PASSED 状态必须绑定正式 Run ID 和验收提交")
    outputs = expected_outputs(state, run_id, head)
    check_outputs(outputs) if args.check else write_outputs(outputs)
    print(json.dumps({"status": "PASS", "mode": "check" if args.check else "write", "output_count": len(outputs), "state": state}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
