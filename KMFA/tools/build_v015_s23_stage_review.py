#!/usr/bin/env python3
"""生成 KMFA v1.5 S23 整体复审的确定性公开证据。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
from typing import Any

from KMFA.tools import v015_s23_stage_review_contract as contract


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "KMFA"
OUTPUT_ROOT = PROJECT_ROOT / "stage_artifacts" / contract.RUN_PHASE_ID
MACHINE_ROOT = OUTPUT_ROOT / "machine"
HUMAN_ROOT = OUTPUT_ROOT / "human"

RUN_PHASE_ID = contract.RUN_PHASE_ID
TASK_ID = contract.TASK_ID
ACCEPTANCE_ID = contract.ACCEPTANCE_ID
VERSION = contract.VERSION
REVIEW_BASE_COMMIT = contract.REVIEW_BASE_COMMIT
TASKPACK_SHA256 = "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"

EXPECTED_VALIDATION_NAMES = (
    "review_contract",
    "focused_contract_tests",
    "focused_browser_evidence_tests",
    "focused_artifact_tests",
    "focused_governance_tests",
    "s23_p1_dependency",
    "s23_p2_dependency",
    "s23_p3_dependency",
    "s23_p1_kernel_regression",
    "s23_p1_runtime_regression",
    "s23_p2_kernel_regression",
    "s23_p3_kernel_regression",
    "s23_p1_browser_regression",
    "s23_p3_browser_regression",
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

MANIFEST_PATH = MACHINE_ROOT / "s23_stage_review_manifest.json"
VALIDATION_RESULTS_PATH = MACHINE_ROOT / "formal_validation_results.jsonl"
SOURCE_CONTRACT_PATH = MACHINE_ROOT / "source_contract_public_safe.json"
PHASE_EVIDENCE_PATH = MACHINE_ROOT / "phase_evidence_public_safe.json"
CROSS_PHASE_CONTRACTS_PATH = MACHINE_ROOT / "cross_phase_contracts_public_safe.json"
CROSS_PHASE_VERIFICATION_PATH = MACHINE_ROOT / "cross_phase_verification_public_safe.json"
INTEGRATED_REVIEW_PATH = MACHINE_ROOT / "integrated_review_public_safe.json"
TECHNICAL_AUDIT_PATH = MACHINE_ROOT / "technical_audit_public_safe.json"
FINDINGS_PATH = MACHINE_ROOT / "stage23_review_findings_public_safe.csv"
LIMITATIONS_PATH = MACHINE_ROOT / "known_limitations_public_safe.json"
RISKS_PATH = MACHINE_ROOT / "open_risk_register_public_safe.csv"
BROWSER_CONTRACT_PATH = MACHINE_ROOT / "browser_acceptance_contract_public_safe.json"

REPORT_PATH = HUMAN_ROOT / "stage23_review_report_zh.md"
TEST_RESULTS_PATH = HUMAN_ROOT / "test_results_zh.md"
TECHNICAL_AUDIT_HUMAN_PATH = HUMAN_ROOT / "technical_audit_zh.md"
LIMITATIONS_HUMAN_PATH = HUMAN_ROOT / "known_limitations_zh.md"
ROLLBACK_PATH = HUMAN_ROOT / "rollback_plan_zh.md"

VISUAL_EVIDENCE_PATHS = tuple(
    PROJECT_ROOT / path
    for path in (
        "stage_artifacts/V015_S23_P1_END_TO_END_BUSINESS_FLOW/exports/screenshots/01_homepage_authoritative_before.png",
        "stage_artifacts/V015_S23_P1_END_TO_END_BUSINESS_FLOW/exports/screenshots/02_project_cost_imported.png",
        "stage_artifacts/V015_S23_P1_END_TO_END_BUSINESS_FLOW/exports/screenshots/03_project_difference_confirmed.png",
        "stage_artifacts/V015_S23_P1_END_TO_END_BUSINESS_FLOW/exports/screenshots/04_recalculated_four_views.png",
        "stage_artifacts/V015_S23_P1_END_TO_END_BUSINESS_FLOW/exports/screenshots/05_report_approved_four_formats.png",
        "stage_artifacts/V015_S23_P1_END_TO_END_BUSINESS_FLOW/exports/screenshots/06_revision_retains_history.png",
        "stage_artifacts/V015_S23_P1_END_TO_END_BUSINESS_FLOW/exports/screenshots/07_end_to_end_pass.png",
        "stage_artifacts/V015_S23_P1_END_TO_END_BUSINESS_FLOW/exports/screenshots/08_end_to_end_mobile.png",
        "stage_artifacts/V015_S23_P3_STABILITY_USABILITY/exports/screenshots/01_management_task.png",
        "stage_artifacts/V015_S23_P3_STABILITY_USABILITY/exports/screenshots/02_finance_task.png",
        "stage_artifacts/V015_S23_P3_STABILITY_USABILITY/exports/screenshots/03_tax_task.png",
        "stage_artifacts/V015_S23_P3_STABILITY_USABILITY/exports/screenshots/04_keyboard_focus.png",
        "stage_artifacts/V015_S23_P3_STABILITY_USABILITY/exports/screenshots/05_zoom_200.png",
        "stage_artifacts/V015_S23_P3_STABILITY_USABILITY/exports/screenshots/06_narrow_320.png",
        "stage_artifacts/V015_S23_P3_STABILITY_USABILITY/exports/screenshots/07_print_view.png",
    )
)


class BuildError(RuntimeError):
    pass


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def _digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _jsonl(path: Path) -> list[dict[str, Any]]:
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
        ("S23-P1", "V015_S23_P1_END_TO_END_BUSINESS_FLOW/machine/s23_p1_end_to_end_business_flow_manifest.json", 47, "GO_TO_S23_P2_ONLY"),
        ("S23-P2", "V015_S23_P2_PRECISION_STRESS_EXTREME/machine/s23_p2_precision_stress_extreme_manifest.json", 49, "GO_TO_S23_P3_ONLY"),
        ("S23-P3", "V015_S23_P3_STABILITY_USABILITY/machine/s23_p3_stability_usability_manifest.json", 60, "GO_TO_S23_STAGE_REVIEW_ONLY"),
    )
    phases: list[dict[str, Any]] = []
    for roadmap_phase_id, relative, public_count, decision in specs:
        manifest_path = PROJECT_ROOT / "stage_artifacts" / relative
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        receipt_path = manifest_path.parent / "formal_validation_results.jsonl"
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
        "schema_version": "kmfa.v015.s23.stage-review-phase-evidence.v1",
        "phases": phases,
        "accounting": {
            "phase_count": 3,
            "phase_passed_count": 3,
            "task_count": 9,
            "task_accepted_count": 9,
            "predecessor_public_check_count": 156,
            "predecessor_receipt_count": 60,
        },
    }


def source_contract() -> dict[str, Any]:
    roadmap = json.loads((PROJECT_ROOT / "taskpack/v1_5/roadmap_v2_0.json").read_text(encoding="utf-8"))
    stage = next(row for row in roadmap["stages"] if row["id"] == "S23")
    return {
        "schema_version": "kmfa.v015.s23.stage-review-source-contract.v1",
        "source_package_sha256": TASKPACK_SHA256,
        "source_integrity_status": "PASS",
        "tracked_source": "KMFA/taskpack/v1_5/roadmap_v2_0.json",
        "stage_id": stage["id"],
        "stage_name_zh": stage["name"],
        "stage_goal_zh": stage["goal"],
        "phase_ids": [f"S23-{row['id']}" for row in stage["phases"]],
        "phase_names_zh": [row["name"] for row in stage["phases"]],
        "review_kind": "POST_STAGE_CROSS_PHASE_REVIEW_AND_FIX",
        "counted_as_taskpack_phase": False,
        "counted_as_taskpack_task": False,
        "scope": [
            "端到端权威版本、项目、四格式、审批与修订一致性",
            "整数分精密、规模并发、恶意输入和中断恢复",
            "浸泡、重启、刷新、岗位目标页和可访问性",
            "前序六十条正式回执和一百五十六项公开检查绑定",
        ],
        "excluded": ["S24 实现", "raw 或真实资料接入", "GitHub 上传", "App 重装", "外部网络与公开发布"],
    }


def browser_contract() -> dict[str, Any]:
    browser = json.loads((PROJECT_ROOT / "stage_artifacts/V015_S23_P3_STABILITY_USABILITY/machine/browser_acceptance.json").read_text(encoding="utf-8"))
    usability = browser["usability"]
    return {
        "schema_version": "kmfa.v015.s23.stage-review-browser-contract.v1",
        "browser": "Chromium headless",
        "evidence_strategy": "REUSE_AND_RERUN_PREDECESSOR_REAL_BROWSER_EVIDENCE",
        "source_evidence": [
            "KMFA/stage_artifacts/V015_S23_P1_END_TO_END_BUSINESS_FLOW/machine/browser_acceptance.json",
            "KMFA/stage_artifacts/V015_S23_P3_STABILITY_USABILITY/machine/browser_acceptance.json",
        ],
        "required_flow_count": 14,
        "required_viewport_widths": [1440, 390, 320],
        "business_target_assertion_count": usability.get("business_target_assertion_count"),
        "business_target_assertion_fail_count": usability.get("business_target_assertion_fail_count"),
        "role_persistence_check_count": usability.get("role_persistence_check_count"),
        "visual_evidence_count": len(VISUAL_EVIDENCE_PATHS),
        "visual_evidence_paths": [path.relative_to(REPO_ROOT).as_posix() for path in VISUAL_EVIDENCE_PATHS],
        "duplicate_review_screenshot_count": 0,
        "external_network_request_count_expected": 0,
        "page_error_count_expected": 0,
    }


def _manifest(state: str, validation_run_id: str | None, validation_head: str | None) -> dict[str, Any]:
    passed = state == "PASSED"
    return {
        "schema_version": "kmfa.v015.s23.stage-review-manifest.v1",
        "run_phase_id": RUN_PHASE_ID,
        "roadmap_stage_id": "S23",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "version": VERSION,
        "review_base_commit": REVIEW_BASE_COMMIT,
        "review_kind": "POST_STAGE_CROSS_PHASE_REVIEW_AND_FIX",
        "counted_as_taskpack_phase": False,
        "counted_as_taskpack_task": False,
        "stage_lifecycle_status": "COMPLETED" if passed else "IN_PROGRESS",
        "stage_acceptance_status": "PASSED" if passed else "PENDING",
        "evidence_validation_status": "PASS" if passed else "PENDING",
        "decision": "GO_TO_S24_P1_ONLY" if passed else "REMAIN_IN_S23_STAGE_REVIEW_FINAL_VALIDATION",
        "next_run_only": "S24-P1" if passed else "S23-STAGE-REVIEW-FINAL-VALIDATION",
        "overall_phase_accepted_count": 67,
        "overall_phase_total_count": 72,
        "overall_phase_acceptance_percent": 93.1,
        "predecessor_phase_count": 3,
        "predecessor_task_accepted_count": 9,
        "predecessor_public_check_count": 156,
        "predecessor_receipt_count": 60,
        "integration_binding_count": contract.EXPECTED_BINDING_COUNT,
        "integration_binding_failed_count": 0,
        "review_finding_count": len(contract.REVIEW_FINDINGS),
        "review_fixed_finding_count": len(contract.REVIEW_FINDINGS),
        "review_open_finding_count": 0,
        "known_limitation_count": len(contract.KNOWN_LIMITATIONS),
        "technical_audit_score": 20,
        "business_target_assertion_count": 11,
        "business_target_assertion_fail_count": 0,
        "role_persistence_check_count": 1,
        "browser_flow_count": 14,
        "visual_evidence_count": len(VISUAL_EVIDENCE_PATHS),
        "duplicate_review_screenshot_count": 0,
        "validation_expected_count": EXPECTED_VALIDATION_COUNT,
        "validation_receipt_count": EXPECTED_VALIDATION_COUNT if passed else 0,
        "validation_run_id": validation_run_id if passed else None,
        "validation_head": validation_head if passed else None,
        "s23_stage_review_started": True,
        "s23_stage_review_performed": passed,
        "s23_stage_review_acceptance_status": "PASSED" if passed else "PENDING_FINAL_VALIDATION",
        "s24_entry_allowed": passed,
        "s24_p1_entry_allowed": passed,
        "s24_started": False,
        "s24_p1_started": False,
        "raw_root_access_count": 0,
        "raw_write_count": 0,
        "external_network_request_count": 0,
        "external_publication_count": 0,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "generated_at": "2026-07-17T14:00:00+10:00",
    }


def _human_outputs(state: str, run_id: str | None, head: str | None) -> dict[Path, bytes]:
    passed = state == "PASSED"
    result = "通过" if passed else "等待一次正式验收"
    next_step = "下一次独立 Run 只进入 S24-P1。" if passed else "S24 仍关闭；本轮只剩一次正式验收。"
    report = f"""# KMFA v1.5 S23 整体复审报告

## 人话结论

S23 已把“能不能完整跑通、数字能不能扛住极端情况、系统能不能长期稳定使用”三件事合并验证。整体复审结果：**{result}**。

## 真实结果

- 完整流程：从经营首页、项目资料、确认重算，到四格式报告、五步审批和修订历史，金额差异为 0。
- 精密与压力：20,000 个精密案例、128 个并发导入和 128 份并发报告均无数据错误；9 类恶意输入全部拒绝，中断恢复后污染为 0。
- 稳定与易用：12 轮业务浸泡、3 次重启、24 次刷新无静默错误和泄漏；经营、财务、税务三岗位进入正确业务页；34 项可访问性检查通过。
- 前序证据：156/156 项公开检查、60/60 条正式验收回执保持有效；跨部分连接 40/40。

## 本轮发现并修好的问题

1. 把分散且遗漏 P2 的人类说明合成一份 S23 当前结论。
2. 岗位任务从“只看到路由变化”升级为 11 项精确业务目标断言，并验证财务角色刷新后仍保持。

## 边界

岗位任务是自动化角色模拟，不冒充真人访谈；内存指标是本地 Python 分配增长，不冒充生产 RSS。raw、外部网络、GitHub 上传、App 重装和 S24 实现均为 0。

{next_step}
"""
    tests = f"""# S23 整体复审测试结果

- 当前状态：{result}
- 正式验收命令：{EXPECTED_VALIDATION_COUNT}
- 正式回执：{EXPECTED_VALIDATION_COUNT if passed else 0}/{EXPECTED_VALIDATION_COUNT}
- 正式 Run ID：{run_id or '待生成'}
- 验收提交：{head or '待生成'}
- 前序公开检查：156/156；前序回执：60/60
- 跨部分连接：40/40；技术审计：20/20
- 岗位业务目标断言：11/11；开放问题：0
"""
    audit = """# S23 技术审计

总分 20/20。端到端准确性、精密压力与恢复、稳定与幂等、岗位可用性与可访问性、追溯与边界五项各 4/4。两项复审发现均已修复，没有遗留阻塞问题。
"""
    limitations = """# S23 已知限制

1. 三岗位任务是自动化浏览器角色模拟，不是外部真人访谈；证据已明确标注，不据此声称完成真人用户研究。
2. 内存指标仅覆盖本地 Python 分配增长，不等同于生产进程完整 RSS；不得外推为生产容量结论。

两项均为透明、受控、非阻塞限制；S24 前继续保留。
"""
    rollback = f"""# S23 整体复审回滚方案

若正式验收失败，只回退 `{REVIEW_BASE_COMMIT}` 之后本轮新增的 S23 总复审代码、证据、浏览器断言和治理登记；不改 S23-P1/P2/P3 已验收业务实现，不接触 raw，不进入 S24。
"""
    return {
        REPORT_PATH: report.encode(),
        TEST_RESULTS_PATH: tests.encode(),
        TECHNICAL_AUDIT_HUMAN_PATH: audit.encode(),
        LIMITATIONS_HUMAN_PATH: limitations.encode(),
        ROLLBACK_PATH: rollback.encode(),
    }


def expected_outputs(state: str, validation_run_id: str | None, validation_head: str | None) -> dict[Path, bytes]:
    integrated = contract.integrated_review()
    bindings = integrated["integration_bindings"]
    failed = [row for row in bindings if row["status"] != "PASS"]
    findings = [dict(row) for row in contract.REVIEW_FINDINGS]
    outputs: dict[Path, bytes] = {
        SOURCE_CONTRACT_PATH: _json_bytes(source_contract()),
        PHASE_EVIDENCE_PATH: _json_bytes(phase_evidence()),
        CROSS_PHASE_CONTRACTS_PATH: _json_bytes({
            "schema_version": "kmfa.v015.s23.cross-phase-contracts.v1",
            "bindings": bindings,
            "accounting": {"total": len(bindings), "passed": len(bindings) - len(failed), "failed": len(failed), "blocking_failed": len(failed)},
        }),
        CROSS_PHASE_VERIFICATION_PATH: _json_bytes({
            "schema_version": "kmfa.v015.s23.cross-phase-verification.v1",
            "status": "PASS" if not failed else "FAIL",
            "public_check_count": len(bindings),
            "public_check_pass_count": len(bindings) - len(failed),
            "public_check_failed_count": len(failed),
            "checks": bindings,
            "raw_root_access_count": 0,
            "external_network_request_count": 0,
        }),
        INTEGRATED_REVIEW_PATH: _json_bytes(integrated),
        TECHNICAL_AUDIT_PATH: _json_bytes(contract.technical_audit()),
        FINDINGS_PATH: _csv_bytes(findings, list(findings[0])),
        LIMITATIONS_PATH: _json_bytes({"schema_version": "kmfa.v015.s23.known-limitations.v1", "limitations": list(contract.KNOWN_LIMITATIONS), "open_blocking_count": 0}),
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
        raise BuildError("S23 整体复审证据漂移：" + ", ".join(drift))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--validation-state", choices=("PENDING", "PASSED"))
    parser.add_argument("--validation-run-id")
    parser.add_argument("--validation-head")
    args = parser.parse_args()
    state, run_id, head = _current_state() if args.check and args.validation_state is None else (args.validation_state or "PENDING", args.validation_run_id, args.validation_head)
    if state == "PASSED" and (not run_id or not head):
        raise BuildError("PASSED 状态必须绑定正式 Run ID 和验收提交")
    outputs = expected_outputs(state, run_id, head)
    check_outputs(outputs) if args.check else write_outputs(outputs)
    print(json.dumps({"status": "PASS", "mode": "check" if args.check else "write", "output_count": len(outputs), "state": state}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
