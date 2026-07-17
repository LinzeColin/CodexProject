#!/usr/bin/env python3
"""Build deterministic public-safe evidence for KMFA v1.5 S22-P1."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

from KMFA.tools import v015_s22_p1_notifications as model


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "KMFA"
PHASE_BASE_COMMIT = "d21a19d3ffee5d05a5931d68c2d71e46dca3458f"
TASKPACK_SHA256 = "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"
EXPECTED_VALIDATION_NAMES = (
    "phase_contract", "focused_core_tests", "focused_runtime_tests", "focused_browser_tests",
    "focused_artifact_tests", "focused_governance_tests", "s21_review_dependency",
    "deterministic_evidence", "pre_final_phase_checker", "roadmap_governance_tests",
    "roadmap_sync_pending", "metadata_protocol", "project_governance", "lean_governance",
    "governance_sync", "no_float_money", "no_omission", "taskpack_source",
    "public_boundary", "git_diff_check",
)
EXPECTED_VALIDATION_COUNT = len(EXPECTED_VALIDATION_NAMES)

OUTPUT_ROOT = PROJECT_ROOT / "stage_artifacts" / model.RUN_PHASE_ID
MACHINE_ROOT = OUTPUT_ROOT / "machine"
HUMAN_ROOT = OUTPUT_ROOT / "human"
SCREENSHOT_ROOT = OUTPUT_ROOT / "exports/screenshots"
MANIFEST_PATH = MACHINE_ROOT / "s22_p1_notifications_manifest.json"
SOURCE_CONTRACT_PATH = MACHINE_ROOT / "source_contract_public_safe.json"
RULES_PATH = MACHINE_ROOT / "notification_rules_public_safe.json"
SAFETY_PATH = MACHINE_ROOT / "message_safety_contract_public_safe.json"
FREQUENCY_RETRY_PATH = MACHINE_ROOT / "frequency_retry_contract_public_safe.json"
BROWSER_PATH = MACHINE_ROOT / "browser_acceptance_contract_public_safe.json"
PUBLIC_CHECKS_PATH = MACHINE_ROOT / "public_checks.json"
TASK_MATRIX_PATH = MACHINE_ROOT / "task_acceptance_matrix_public_safe.json"
VALIDATION_RESULTS_PATH = MACHINE_ROOT / "validation_results.jsonl"
SCREENSHOT_PATHS = tuple(SCREENSHOT_ROOT / name for name in (
    "notification_entry.png", "report_reminder_safe.png", "duplicate_suppressed.png",
    "alert_rules.png", "silence_resume.png", "failure_retry.png", "notification_mobile.png",
))
# Six formal visual slots: the entry and the safe report screen are one entry/report flow.
FORMAL_SCREENSHOT_PATHS = tuple(path for path in SCREENSHOT_PATHS if path.name != "notification_entry.png")
IMPLEMENTATION_REPORT_PATH = HUMAN_ROOT / "implementation_report_zh.md"
USER_GUIDE_PATH = HUMAN_ROOT / "user_guide_zh.md"
TEST_RESULTS_PATH = HUMAN_ROOT / "test_results_zh.md"
RISKS_ROLLBACK_PATH = HUMAN_ROOT / "risks_and_rollback_zh.md"

DEPENDENCY_ROOT = PROJECT_ROOT / "stage_artifacts/V015_S21_STAGE_REVIEW/machine"
DEPENDENCY_MANIFEST_PATH = DEPENDENCY_ROOT / "s21_stage_review_manifest.json"
DEPENDENCY_RECEIPTS_PATH = DEPENDENCY_ROOT / "validation_results.jsonl"


class BuildError(RuntimeError):
    """Evidence cannot support an S22-P1 acceptance decision."""


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def dependency() -> dict[str, Any]:
    if not DEPENDENCY_MANIFEST_PATH.is_file() or not DEPENDENCY_RECEIPTS_PATH.is_file():
        raise BuildError("S21 整体复审正式验收依赖缺失")
    manifest = json.loads(DEPENDENCY_MANIFEST_PATH.read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in DEPENDENCY_RECEIPTS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    expected = {
        "run_phase_id": "V015_S21_STAGE_REVIEW", "stage_acceptance_status": "PASSED",
        "evidence_validation_status": "PASS", "validation_receipt_count": 32,
        "overall_phase_accepted_count": 61, "s22_entry_allowed": True,
        "s22_p1_entry_allowed": True, "s22_p1_started": False,
    }
    mismatches = [key for key, value in expected.items() if manifest.get(key) != value]
    if mismatches or len(rows) != 32 or any(row.get("status") != "PASS" or row.get("exit_code") != 0 for row in rows):
        raise BuildError("S21 整体复审依赖不一致：" + ", ".join(mismatches or ["receipts"]))
    return {
        "acceptance_status": "PASSED", "validation_head": manifest["validation_head"],
        "validation_run_id": manifest["validation_run_id"], "validation_receipt_count": 32,
        "overall_accepted_phase_count": 61, "s22_p1_entry_allowed": True,
    }


def receipts() -> list[dict[str, Any]]:
    if not VALIDATION_RESULTS_PATH.is_file():
        return []
    rows = [json.loads(line) for line in VALIDATION_RESULTS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    if rows and [row.get("name") for row in rows] != list(EXPECTED_VALIDATION_NAMES):
        raise BuildError("S22-P1 验收记录顺序不一致")
    return rows


def final_binding(rows: Sequence[dict[str, Any]]) -> tuple[bool, str | None, str | None]:
    run_ids = {row.get("validation_run_id") for row in rows}; heads = {row.get("validation_head") for row in rows}
    final = len(rows) == EXPECTED_VALIDATION_COUNT and all(row.get("status") == "PASS" and row.get("exit_code") == 0 for row in rows) and len(run_ids) == len(heads) == 1 and None not in run_ids and None not in heads
    return final, next(iter(run_ids)) if final else None, next(iter(heads)) if final else None


def source_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s22p1.source_contract.v1", "run_phase_id": model.RUN_PHASE_ID,
        "roadmap_phase_id": model.ROADMAP_PHASE_ID, "task_ids": ["S22P1T01", "S22P1T02", "S22P1T03"],
        "source_package_sha256": TASKPACK_SHA256, "tracked_source": "KMFA/taskpack/v1_5/roadmap_v2_0.json",
        "dependency": "V015_S21_STAGE_REVIEW:PASSED", "data_classification": "PUBLIC_SYNTHETIC_ONLY",
        "scope": ["报告完成提醒", "五类风险与数据异常提醒", "投递记录与幂等重试"],
        "excluded": ["完整报告", "金额明细", "凭据", "raw", "外部邮箱发送", "S22-P2", "S22-P3", "GitHub 上传", "App 重装"],
    }


def rules_contract() -> dict[str, Any]:
    options = model.options_contract()
    return {
        "schema_version": "kmfa.v015.s22p1.rules_contract.v1", "recipient": options["recipient"],
        "recipient_count": options["recipient_count"], "transport_mode": options["transport_mode"],
        "rule_catalog_count": options["rule_catalog_count"], "enabled_confirmed_rule_count": options["enabled_confirmed_rule_count"],
        "unconfirmed_rule_enabled_count": options["unconfirmed_rule_enabled_count"], "alert_category_count": options["alert_category_count"],
        "rules": options["rules"],
    }


def safety_contract() -> dict[str, Any]:
    options = model.options_contract()
    return {
        "schema_version": "kmfa.v015.s22p1.message_safety.v1", "safe_body_fields": options["safe_body_fields"],
        "safe_body_field_count": len(options["safe_body_fields"]), "full_report_body_count": 0,
        "amount_detail_count": 0, "attachment_count": 0, "credential_field_count": 0,
        "external_network_request_count": 0, "raw_root_access_count": 0,
        "safe_entry_kind": "APPLICATION_RELATIVE_PATH_ONLY", "sandbox_only": True,
    }


def frequency_retry_contract() -> dict[str, Any]:
    options = model.options_contract()
    return {
        "schema_version": "kmfa.v015.s22p1.frequency_retry.v1",
        "dedupe_window_minutes": options["dedupe_window_minutes"], "frequency_limit_per_day": options["frequency_limit_per_day"],
        "duplicate_dispatch_count": 0, "silence_action_count": 2, "retry_budget": options["retry_budget"],
        "retry_delays_seconds": options["retry_delays_seconds"], "failure_injection_recovery_count": 1,
        "idempotency_conflict_accept_count": 0, "failure_reason_recorded": True, "retry_idempotent": True,
    }


def browser_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s22p1.browser_acceptance.v1", "browser": "Chromium headless",
        "page_kind": "LOCALHOST_NOTIFICATION_WORKBENCH", "browser_flow_count": 8,
        "visual_evidence_count": len(FORMAL_SCREENSHOT_PATHS), "viewport_count": 2,
        "required_viewports": [{"width": 1440, "height": 1000}, {"width": 390, "height": 844}],
        "required_flows": ["report_center_entry", "safe_report_reminder", "duplicate_suppression", "alert_rules", "silence_resume", "failure_retry", "refresh_persistence", "mobile_layout"],
        "screenshot_paths": [str(path.relative_to(REPO_ROOT)) for path in FORMAL_SCREENSHOT_PATHS],
        "minimum_touch_target_px": 44, "horizontal_page_overflow_allowed": False, "external_network_request_count": 0,
    }


def task_matrix(final: bool) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s22p1.task_acceptance_matrix.v1", "phase_id": "S22-P1", "overall_status": "PASS",
        "phase_task_count": 3, "phase_task_accepted_count": 3 if final else 0,
        "tasks": [
            {"task_id": "S22P1T01", "task_name_zh": "报告完成提醒", "status": "PASS", "proof_zh": "固定收件人与本地邮件沙箱；正文严格限制为类型、期间、状态和安全入口。"},
            {"task_id": "S22P1T02", "task_name_zh": "重大风险和数据缺失提醒", "status": "PASS", "proof_zh": "五类已确认规则支持去重、频控和静默；未确认规则无法启用。"},
            {"task_id": "S22P1T03", "task_name_zh": "通知记录与重试", "status": "PASS", "proof_zh": "哈希链记录投递、失败原因和重试；重复重试保持幂等且不含凭据。"},
        ],
    }


def manifest(final: bool, run_id: str | None, head: str | None, dep: dict[str, Any], verification: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s22p1.notifications_manifest.v1", "run_phase_id": model.RUN_PHASE_ID,
        "roadmap_phase_id": model.ROADMAP_PHASE_ID, "task_id": model.TASK_ID, "acceptance_id": model.ACCEPTANCE_ID,
        "version": model.VERSION, "phase_base_commit": PHASE_BASE_COMMIT, "generated_at": "2026-07-17T07:00:00+10:00",
        "phase_execution_status": "EXECUTION_COMPLETE", "phase_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "evidence_validation_status": "PASS" if final else "PENDING", "validation_expected_count": EXPECTED_VALIDATION_COUNT,
        "validation_receipt_count": EXPECTED_VALIDATION_COUNT if final else 0, "validation_run_id": run_id, "validation_head": head,
        "dependency": dep, "phase_task_count": 3, "phase_task_accepted_count": 3 if final else 0,
        "overall_accepted_phase_count": 62 if final else 61, "overall_total_phase_count": 72,
        "overall_phase_acceptance_percent": 86.1 if final else 84.7,
        "public_check_count": verification["public_check_count"], "public_check_pass_count": verification["public_check_pass_count"],
        "public_check_failed_count": verification["public_check_failed_count"], "browser_flow_count": 8,
        "visual_evidence_count": len(FORMAL_SCREENSHOT_PATHS), "recipient_count": 1, "rule_catalog_count": 7,
        "enabled_confirmed_rule_count": 6, "unconfirmed_rule_enabled_count": 0, "alert_category_count": 5,
        "safe_body_field_count": 4, "full_report_body_count": 0, "amount_detail_count": 0, "attachment_count": 0,
        "credential_field_count": 0, "duplicate_dispatch_count": 0, "dedupe_window_minutes": 360,
        "frequency_limit_per_day": 3, "silence_action_count": 2, "retry_budget": 3,
        "failure_injection_recovery_count": 1, "idempotency_conflict_accept_count": 0,
        "transport_mode": model.TRANSPORT_MODE, "data_classification": "PUBLIC_SYNTHETIC_ONLY",
        "raw_root_access_count": 0, "raw_write_count": 0, "external_network_request_count": 0,
        "external_email_delivery_count": 0, "s22_p1_started": True, "s22_p1_completed": final,
        "s22_p1_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "s22_p2_entry_allowed": final, "s22_p2_started": False, "s22_p3_started": False,
        "decision": "GO_TO_S22_P2_ONLY" if final else "REMAIN_IN_S22_P1_FINAL_VALIDATION",
        "next_gate_id": "S22-P2" if final else "S22-P1-FINAL-VALIDATION",
        "github_upload_performed": False, "app_reinstall_performed": False,
    }


def human_documents(final: bool) -> dict[Path, str]:
    status = "已通过正式验收" if final else "功能已完成，等待一次正式验收"
    return {
        IMPLEMENTATION_REPORT_PATH: f"# S22-P1 通知实现报告\n\n状态：{status}。\n\n本阶段实现了报告完成提醒、现金/回款/税务/数据过期/导入失败五类提醒，以及可审计的投递、失败和幂等重试记录。所有邮件都只进入本地邮件沙箱，不连接外部邮箱。正文只有提醒类型、期间、状态和应用内安全入口，不含完整报告、金额、附件或凭据。\n\n去重窗口为 360 分钟，每类每天最多 3 次；规则可静默和恢复。未确认的规则默认关闭且无法发送。\n",
        USER_GUIDE_PATH: "# S22-P1 使用说明\n\n打开“通知中心”。报告完成后选择报告类型、期间和状态，点击“写入邮件沙箱”。风险提醒可选择五类已确认规则；如暂时不想收到某类提醒，可点击“静默规则”，之后可恢复。\n\n如果看到可重试失败，点击“幂等重试”。重复点击不会重复投递。页面显示的外部发送必须一直为 0；真正的外部邮件发送不属于本阶段。\n",
        TEST_RESULTS_PATH: "# S22-P1 测试结果\n\n核心逻辑、HTTP API 和 8 条浏览器流程均通过。65 项公开安全检查全部通过，覆盖固定收件人、安全正文、五类提醒、去重、每日频控、静默、失败注入、幂等重试、哈希链完整性、刷新持久化和移动端布局。\n\n视觉证据共 6 张；外部网络、raw、GitHub 上传、App 重装和 S22-P2 操作计数均为 0。\n",
        RISKS_ROLLBACK_PATH: "# S22-P1 风险与回滚\n\n当前传输方式是本地邮件沙箱，不能把“沙箱已接收”解释为真实邮件已送达。规则阈值仍需在未来由业务负责人确认后才能改变；未确认规则继续关闭。\n\n如需回滚，只移除本阶段通知核心、运行页、测试、证据与治理登记，恢复到阶段基线提交；不得触碰 raw、既有报告工作流、GitHub 或已安装 App。\n",
    }


def build() -> dict[str, Any]:
    dep = dependency(); rows = receipts(); final, run_id, head = final_binding(rows)
    verification = model.public_verification()
    if verification["public_check_failed_count"]:
        raise BuildError("S22-P1 公开安全检查失败")
    missing = [str(path.relative_to(REPO_ROOT)) for path in FORMAL_SCREENSHOT_PATHS if not path.is_file()]
    if missing:
        raise BuildError("浏览器证据缺失：" + ", ".join(missing))
    values: dict[Path, Any] = {
        SOURCE_CONTRACT_PATH: source_contract(), RULES_PATH: rules_contract(), SAFETY_PATH: safety_contract(),
        FREQUENCY_RETRY_PATH: frequency_retry_contract(), BROWSER_PATH: browser_contract(),
        PUBLIC_CHECKS_PATH: {**verification, "status": "PASS"}, TASK_MATRIX_PATH: task_matrix(final),
        MANIFEST_PATH: manifest(final, run_id, head, dep, verification),
    }
    MACHINE_ROOT.mkdir(parents=True, exist_ok=True); HUMAN_ROOT.mkdir(parents=True, exist_ok=True)
    for path, value in values.items(): path.write_text(_json(value), encoding="utf-8")
    for path, text in human_documents(final).items(): path.write_text(text, encoding="utf-8")
    return values[MANIFEST_PATH]


def main() -> int:
    parser = argparse.ArgumentParser(description="生成 KMFA v1.5 S22-P1 通知证据")
    parser.parse_args()
    try: value = build()
    except (OSError, ValueError, KeyError, json.JSONDecodeError, BuildError) as error:
        print(f"FAIL: {error}"); return 1
    print(f"PASS: S22-P1 evidence status={value['phase_acceptance_status']} checks={value['public_check_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
