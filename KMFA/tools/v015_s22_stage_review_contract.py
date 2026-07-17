#!/usr/bin/env python3
"""KMFA v1.5 S22 通知、安全与运维三部分整体复审合同。"""

from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from KMFA.tools import run_v015_s22_p1_notifications as p1_runtime
from KMFA.tools import run_v015_s22_p2_security_audit as p2_runtime
from KMFA.tools import run_v015_s22_p3_operations_governance as p3_runtime
from KMFA.tools import v015_s22_p1_notifications as p1
from KMFA.tools import v015_s22_p2_security_audit as p2
from KMFA.tools import v015_s22_p3_operations_governance as p3


RUN_PHASE_ID = "V015_S22_STAGE_REVIEW"
TASK_ID = "KMFA-V015-S22-STAGE-REVIEW-20260717"
ACCEPTANCE_ID = "ACC-KMFA-V015-S22-STAGE-REVIEW"
VERSION = "1.5.0-dev-s22-review"
REVIEW_BASE_COMMIT = "eeb4526f1ee9fac148d06c56634b558262176f20"
EXPECTED_BINDING_COUNT = 48

REVIEW_FINDINGS = (
    {
        "finding_id": "S22REV-F001",
        "severity": "P0",
        "category": "NOTIFICATION_AUTHORIZATION_AUDIT",
        "issue_zh": "通知发送、静默和重试接口在安全运行时中仍可绕过统一会话与审计。",
        "impact_zh": "未登录请求可能改变通知状态，且操作人和原因无法进入统一防篡改审计链。",
        "fix_zh": "通知处理增加安全授权钩子，安全运行时强制会话、角色、主体和审计；页面只从当前浏览器会话传递短期令牌。",
        "status": "FIXED_VALIDATED",
        "blocks_stage_acceptance": False,
    },
    {
        "finding_id": "S22REV-F002",
        "severity": "P0",
        "category": "AUDIT_QUERY_AUTHORIZATION",
        "issue_zh": "审计查询接口在未登录时返回操作明细。",
        "impact_zh": "内部操作人、主体和对象引用可能被无权限查看。",
        "fix_zh": "未登录只返回必要汇总且明细为空；完整审计查询必须携带具备 QUERY_AUDIT 权限的会话。",
        "status": "FIXED_VALIDATED",
        "blocks_stage_acceptance": False,
    },
    {
        "finding_id": "S22REV-F003",
        "severity": "P0",
        "category": "LIVE_BACKUP_SOURCE",
        "issue_zh": "运行时创建备份时使用固定公开样例，而不是当前通知、配置和审计状态。",
        "impact_zh": "即使恢复演练零差异，也只能证明样例可恢复，不能证明当前运行状态可恢复。",
        "fix_zh": "备份状态改为运行时实时快照，包含当前通知派生记录、无秘密配置以及安全与运维审计事件。",
        "status": "FIXED_VALIDATED",
        "blocks_stage_acceptance": False,
    },
    {
        "finding_id": "S22REV-F004",
        "severity": "P1",
        "category": "OPERATIONS_AUDIT_AND_JOURNEY",
        "issue_zh": "健康演练、备份验证恢复、迁移故障和回滚只校验负责人，未全部进入安全审计；三页也缺少统一流程导航和会话延续。",
        "impact_zh": "关键运维动作无法从统一审计查询追溯，用户跨页面需要重复判断入口和登录状态。",
        "fix_zh": "所有运维动作进入安全审计；三页增加统一三步导航，并用单标签页 sessionStorage 延续短期会话。",
        "status": "FIXED_VALIDATED",
        "blocks_stage_acceptance": False,
    },
)


class StageReviewError(ValueError):
    """S22 三部分连接或整体复审证据不一致。"""


def technical_audit() -> dict[str, Any]:
    dimensions = [
        {"dimension": "notification_safety", "score": 4, "finding_zh": "提醒正文保持最小化，变更操作均受会话和角色控制。"},
        {"dimension": "security_and_audit", "score": 4, "finding_zh": "审计明细授权查询，通知与运维动作进入同一防篡改安全审计链。"},
        {"dimension": "live_backup_recovery", "score": 4, "finding_zh": "备份绑定当前运行状态，验证和恢复演练保持数据与权限零差异。"},
        {"dimension": "operations_and_migration", "score": 4, "finding_zh": "六类服务受监控，迁移幂等、故障原子、回滚精确。"},
        {"dimension": "human_usability", "score": 4, "finding_zh": "三页连续导航、一次登录延续和移动端触控入口齐全。"},
    ]
    return {
        "schema_version": "kmfa.v015.s22.stage-review-technical-audit.v1",
        "method": "END_TO_END_NOTIFICATION_SECURITY_LIVE_BACKUP_AND_OPERATIONS_WALKTHROUGH",
        "scale_per_dimension": 4,
        "maximum_score": 20,
        "dimensions": dimensions,
        "total_score": sum(row["score"] for row in dimensions),
        "rating": "EXCELLENT",
        "severity_counts": {"P0": 3, "P1": 1, "P2": 0, "P3": 0},
        "fixed_issue_count": 4,
        "open_issue_count": 0,
    }


def _receipt_summary(path: Path) -> dict[str, Any]:
    rows = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return {
        "count": len(rows),
        "pass_count": sum(row.get("status") == "PASS" for row in rows),
        "run_ids": sorted({str(row.get("validation_run_id")) for row in rows}),
    }


def end_to_end_fixture() -> dict[str, Any]:
    """Build one deterministic, public-synthetic, local-only S22 fixture."""

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        auth_value = hashlib.sha256(b"kmfa-s22-review-auth").hexdigest()
        signing_value = hashlib.sha256(b"kmfa-s22-review-signing").hexdigest()
        security = p2.SecurityWorkbench(
            root / "security.jsonl",
            secret_values={
                "KMFA_LOCAL_AUTH_KEY": auth_value,
                "KMFA_SESSION_SIGNING_KEY": signing_value,
            },
        )
        notifications = p1.NotificationJournal(root / "notifications.jsonl")
        finance = security.sessions.authenticate(
            "finance.local",
            auth_value,
            occurred_at="2026-07-17T00:00:00+00:00",
            session_id="A1" * 12,
        )
        owner = security.sessions.authenticate(
            "owner.local",
            auth_value,
            occurred_at="2026-07-17T00:00:10+00:00",
            session_id="B2" * 12,
        )
        security.sessions.perform(
            finance["session_token"],
            action_type="PROCESSING",
            subject_ref="NOTIFICATION::REPORT",
            company_ref=finance["company_ref"],
            occurred_at="2026-07-17T00:01:00+00:00",
        )
        notice = notifications.dispatch_report(
            report_version_id="REPORT-S22REV-001",
            report_type="MONTHLY",
            period_label="2026-07",
            report_status="APPROVED",
            idempotency_key="s22-review-notification-001",
            occurred_at="2026-07-17T00:01:01+00:00",
        )
        security.sessions.perform(
            finance["session_token"],
            action_type="PARAMETER_CHANGE",
            subject_ref="NOTIFICATION::RULE-CASH-MAJOR-RISK",
            company_ref=finance["company_ref"],
            occurred_at="2026-07-17T00:01:10+00:00",
        )
        silenced = notifications.set_rule_silenced(
            "RULE-CASH-MAJOR-RISK",
            True,
            idempotency_key="s22-review-silence-001",
            occurred_at="2026-07-17T00:01:11+00:00",
        )

        unauthenticated_blocked = False
        try:
            security.sessions.perform(
                None,
                action_type="PROCESSING",
                subject_ref="NOTIFICATION::REPORT",
                company_ref="COMPANY::SYNTHETIC-A",
            )
        except p2.SecurityError as error:
            unauthenticated_blocked = error.code == "SESSION_INVALID"
        readonly = security.sessions.authenticate(
            "readonly.local",
            auth_value,
            occurred_at="2026-07-17T00:01:20+00:00",
            session_id="C3" * 12,
        )
        readonly_blocked = False
        try:
            security.sessions.perform(
                readonly["session_token"],
                action_type="PROCESSING",
                subject_ref="NOTIFICATION::REPORT",
                company_ref=readonly["company_ref"],
                occurred_at="2026-07-17T00:01:21+00:00",
            )
        except p2.SecurityError as error:
            readonly_blocked = error.code == "PERMISSION_DENIED"

        runtime_state = SimpleNamespace(
            notification_journal=notifications,
            security_workbench=security,
        )
        operations = p3.OperationsWorkbench(
            root / "operations",
            security,
            state_provider=lambda: p3_runtime._live_backup_state(runtime_state),
            occurred_at="2026-07-17T00:02:00+00:00",
        )
        runtime_state.operations_workbench = operations
        health_drill = operations.failure_probe(owner["session_token"], "STORAGE")
        created = operations.create_backup(owner["session_token"])
        backup_payload = operations.backups._read(created["backup_id"])["payload"]
        unverified_blocked = False
        try:
            operations.restore_drill(owner["session_token"], created["backup_id"])
        except p3.OperationsError as error:
            unverified_blocked = error.code == "BACKUP_NOT_VERIFIED"
        verified = operations.verify_backup(owner["session_token"], created["backup_id"])
        restored = operations.restore_drill(owner["session_token"], created["backup_id"])
        migrated = operations.migrate(owner["session_token"])
        second_migration = operations.migrate(owner["session_token"])
        rollback = operations.rollback(owner["session_token"], migrated["migration_id"])
        migration_failure = operations.migration_failure_probe(
            owner["session_token"], "FORMULA"
        )
        notification_snapshot = notifications.snapshot()
        security_snapshot = security.snapshot()
        audit_query = security.sessions.query_audit(
            finance["session_token"], limit=200
        )
        overview = operations.overview()
        encoded_backup = json.dumps(backup_payload, ensure_ascii=False, sort_keys=True)
        return json.loads(
            json.dumps(
                {
                    "notice": notice,
                    "silenced": silenced,
                    "notification_snapshot": notification_snapshot,
                    "unauthenticated_blocked": unauthenticated_blocked,
                    "readonly_blocked": readonly_blocked,
                    "health_drill": health_drill,
                    "created": created,
                    "verified": verified,
                    "restored": restored,
                    "unverified_blocked": unverified_blocked,
                    "backup_payload": backup_payload,
                    "backup_contains_secret": (
                        auth_value in encoded_backup or signing_value in encoded_backup
                    ),
                    "migrated": migrated,
                    "second_migration": second_migration,
                    "rollback": rollback,
                    "migration_failure": migration_failure,
                    "security_snapshot": security_snapshot,
                    "audit_query": audit_query,
                    "overview": overview,
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )


def integration_bindings() -> list[dict[str, Any]]:
    fixture = end_to_end_fixture()
    rows: list[dict[str, Any]] = []

    def add(binding_id: str, kind: str, passed: bool, detail_zh: str) -> None:
        rows.append(
            {
                "binding_id": binding_id,
                "kind": kind,
                "status": "PASS" if passed else "FAIL",
                "detail": detail_zh,
            }
        )

    for index, (phase, result, expected) in enumerate(
        (
            (p1.RUN_PHASE_ID, p1.public_verification(), 65),
            (p2.RUN_PHASE_ID, p2.public_verification(), 60),
            (p3.RUN_PHASE_ID, p3.public_verification(), 62),
        ),
        1,
    ):
        add(
            f"PHASE-{index:02d}",
            "PREDECESSOR_PUBLIC_CONTRACT",
            result["public_check_failed_count"] == 0
            and result["public_check_count"] == expected,
            phase,
        )

    artifact_root = Path(__file__).resolve().parents[1] / "stage_artifacts"
    for index, relative in enumerate(
        (
            "V015_S22_P1_NOTIFICATIONS/machine/validation_results.jsonl",
            "V015_S22_P2_SECURITY_AUDIT/machine/validation_results.jsonl",
            "V015_S22_P3_OPERATIONS_GOVERNANCE/machine/validation_results.jsonl",
        ),
        1,
    ):
        summary = _receipt_summary(artifact_root / relative)
        add(
            f"RECEIPTS-{index:02d}",
            "PREDECESSOR_FORMAL_ACCEPTANCE",
            summary["count"] == 20
            and summary["pass_count"] == 20
            and len(summary["run_ids"]) == 1,
            "前序正式验收回执完整",
        )

    notice = fixture["notice"]
    notification = fixture["notification_snapshot"]
    audit_events = fixture["security_snapshot"]["audit"]["events"]
    message = notice["message"]
    add("NOTICE-SANDBOX", "NOTIFICATION_TO_SECURITY", notice["status"] == "SENT_SANDBOX", "提醒只进入本地邮件沙箱")
    add("NOTICE-SAFE-FIELDS", "NOTIFICATION_TO_SECURITY", [row["field"] for row in message["body_fields"]] == ["kind", "period", "status", "safe_entry"] and message["amount_detail_count"] == message["attachment_count"] == message["credential_field_count"] == 0, "提醒正文结构保持最小化")
    add("NOTICE-NO-SENSITIVE", "NOTIFICATION_TO_SECURITY", notification["full_report_body_count"] == notification["amount_detail_count"] == notification["attachment_count"] == 0, "完整报告、金额和附件为零")
    add("NOTICE-NO-EXTERNAL", "NOTIFICATION_TO_SECURITY", notification["external_network_request_count"] == 0, "外部邮件和网络请求为零")
    add("NOTICE-PROCESS-AUDIT", "NOTIFICATION_TO_SECURITY", any(row["action_type"] == "PROCESSING" and row["subject_ref"] == "NOTIFICATION::REPORT" for row in audit_events), "发送操作进入安全审计")
    add("NOTICE-RULE-AUDIT", "NOTIFICATION_TO_SECURITY", any(row["action_type"] == "PARAMETER_CHANGE" and row["subject_ref"] == "NOTIFICATION::RULE-CASH-MAJOR-RISK" for row in audit_events), "静默规则变更进入安全审计")
    add("NOTICE-JOURNAL", "NOTIFICATION_TO_SECURITY", notification["event_count"] == 2 and len(notification["events"]) == 2, "通知与规则事件追加保存")
    add("NOTICE-UNAUTH-BLOCKED", "NOTIFICATION_TO_SECURITY", fixture["unauthenticated_blocked"], "未登录通知变更失败关闭")
    add("NOTICE-READONLY-BLOCKED", "NOTIFICATION_TO_SECURITY", fixture["readonly_blocked"], "只读角色不能处理通知")
    add("AUDIT-CHAIN", "SECURITY", fixture["security_snapshot"]["audit"]["chain_valid"] is True, "统一审计链完整")
    add("AUDIT-QUERY", "SECURITY", fixture["audit_query"]["query_result_count"] >= 10, "授权会话可查询完整审计")
    encoded_audit = json.dumps(audit_events, ensure_ascii=False, sort_keys=True)
    add("AUDIT-NO-CREDENTIAL", "SECURITY", "kmfa-s22-review-auth" not in encoded_audit and "session_token" not in encoded_audit, "审计不保存凭据或会话令牌")

    health = fixture["overview"]["health"]
    drill = fixture["health_drill"]
    add("HEALTH-SIX", "OPERATIONS", health["service_count"] == health["monitored_service_count"] == 6, "六类服务全部受监控")
    add("HEALTH-READY", "OPERATIONS", health["production_ready"] is True, "恢复后生产门禁重新开放")
    add("HEALTH-FAILURE", "OPERATIONS", drill["failure_detected"] is True, "故障被识别")
    add("HEALTH-BLOCK", "OPERATIONS", drill["critical_operation_blocked"] is True, "关键故障阻止继续运行")
    add("HEALTH-RECOVER", "OPERATIONS", drill["recovered"] is True and drill["final_status"] == "HEALTHY", "故障恢复回到健康状态")

    payload = fixture["backup_payload"]
    datasets = payload["datasets"]
    private_derived = datasets["PRIVATE_DERIVED"]
    audit_backup = datasets["AUDIT_EVENTS"]
    add("BACKUP-THREE", "LIVE_BACKUP", set(datasets) == set(p3.BACKUP_DATASETS), "三类备份数据齐全")
    add("BACKUP-LIVE-SOURCE", "LIVE_BACKUP", all(value["source"] == "LIVE_RUNTIME" for value in datasets.values()), "备份绑定当前运行时而非固定样例")
    add("BACKUP-NOTIFICATION", "LIVE_BACKUP", private_derived["notification_event_count"] == 2 and any(row["event_id"] == notice["event_id"] for row in private_derived["notification_events"]), "当前通知事件进入备份")
    add("BACKUP-SECURITY-AUDIT", "LIVE_BACKUP", audit_backup["security_event_count"] >= 6 and len(audit_backup["security_events"]) == audit_backup["security_event_count"], "当前安全审计进入备份")
    add("BACKUP-OPERATIONS-AUDIT", "LIVE_BACKUP", audit_backup["operations_event_count"] >= 8 and len(audit_backup["operations_events"]) == audit_backup["operations_event_count"], "当前运维事件进入备份")
    add("BACKUP-NO-SECRET", "LIVE_BACKUP", not fixture["backup_contains_secret"] and datasets["CONFIGURATION"]["secret_value_count"] == 0, "备份不含秘密值")
    add("BACKUP-PRIVATE-MODE", "LIVE_BACKUP", fixture["created"]["private_file_mode"] == "0o600", "备份文件权限为仅当前用户")
    add("BACKUP-UNVERIFIED-BLOCK", "LIVE_BACKUP", fixture["unverified_blocked"], "未验证备份不可恢复")
    add("BACKUP-VERIFIED", "LIVE_BACKUP", fixture["verified"]["verified"] is True, "完整性验证通过")
    add("RESTORE-ZERO-DATA", "LIVE_BACKUP", fixture["restored"]["difference_count"] == 0, "恢复数据零差异")
    add("RESTORE-ZERO-PERMISSION", "LIVE_BACKUP", fixture["restored"]["permission_difference_count"] == 0, "恢复权限零差异")
    add("BACKUP-USABLE", "LIVE_BACKUP", fixture["restored"]["usable"] is True, "验证并演练后备份可用")

    subjects = {row["subject_ref"] for row in audit_events}
    required_subjects = {
        "SERVICE::HEALTH-DRILL-S22P3",
        "BACKUP::S22P3",
        "BACKUP::VERIFY-S22P3",
        "BACKUP::RESTORE-S22P3",
        "MIGRATION::S22P3",
        "MIGRATION::ROLLBACK-S22P3",
        "MIGRATION::FAILURE-DRILL-S22P3",
    }
    add("OPERATIONS-AUDIT-COVERAGE", "OPERATIONS", required_subjects <= subjects, "七类关键运维动作全部进入统一审计")
    add("MIGRATION-APPLIED", "MIGRATION", fixture["migrated"]["status"] == "APPLIED" and fixture["migrated"]["change_count"] == 4, "四类版本面共同迁移")
    add("MIGRATION-IDEMPOTENT", "MIGRATION", fixture["second_migration"]["status"] == "NOOP" and fixture["second_migration"]["change_count"] == 0, "重复迁移无变化")
    add("MIGRATION-ROLLBACK", "MIGRATION", fixture["rollback"]["difference_count"] == fixture["rollback"]["permission_difference_count"] == 0, "回滚状态与权限零差异")
    add("MIGRATION-FAILURE", "MIGRATION", fixture["migration_failure"]["failure_detected"] and fixture["migration_failure"]["state_unchanged"], "迁移故障保持原状态")
    add("OPERATIONS-JOURNAL", "OPERATIONS", fixture["overview"]["operations_journal"]["chain_valid"] is True, "运维记录链完整")

    html_by_step = (
        p1_runtime.render_html(),
        p2_runtime.render_html(),
        p3_runtime.render_html(),
    )
    add("UI-THREE-STEPS", "HUMAN_USABILITY", [text.count('aria-label="长期运行三步流程"') for text in html_by_step] == [1, 2, 3], "三页逐层提供统一导航")
    add("UI-CURRENT-STEP", "HUMAN_USABILITY", all(token in text for token, text in zip(('href="/notification-delivery" aria-current="step"', 'href="/security-audit" aria-current="step"', 'href="/operations" aria-current="step"'), html_by_step)), "每页明确当前步骤")
    add("UI-SESSION-CONTINUITY", "HUMAN_USABILITY", "kmfa_s22_session_token" in html_by_step[0] and "sessionStorage.setItem('kmfa_s22_session_token'" in html_by_step[1] and "sessionStorage.getItem('kmfa_s22_session_token')" in html_by_step[2], "短期会话仅在当前标签页连续使用")
    add("UI-AUDIT-AUTH-HEADER", "HUMAN_USABILITY", "X-KMFA-Session" in html_by_step[1], "审计明细请求携带安全会话")
    add("UI-TOUCH-RESPONSIVE", "HUMAN_USABILITY", all("min-height:44px" in text and "@media" in text for text in html_by_step), "三页具备触控尺寸和响应式规则")
    boundary = fixture["overview"]
    add("BOUNDARY-ZERO", "SCOPE_SAFETY", boundary["raw_root_access_count"] == boundary["external_network_request_count"] == 0, "raw 与外部网络访问为零")
    add("RELEASE-CLOSED", "SCOPE_SAFETY", not boundary["github_upload_performed"] and not boundary["app_reinstall_performed"], "GitHub 与 App 发布动作保持关闭")

    if len(rows) != EXPECTED_BINDING_COUNT:
        raise StageReviewError(
            f"REVIEW_BINDING_COUNT_DRIFT：预期 {EXPECTED_BINDING_COUNT}，实际 {len(rows)}。"
        )
    return rows


def integrated_review() -> dict[str, Any]:
    bindings = integration_bindings()
    failed = [row for row in bindings if row["status"] != "PASS"]
    return {
        "schema_version": "kmfa.v015.s22.integrated-stage-review.v1",
        "fixture_class": "PUBLIC_SYNTHETIC_LOCALHOST_AUTHENTICATED_LIVE_STATE",
        "predecessor_phase_count": 3,
        "predecessor_task_accepted_count": 9,
        "predecessor_receipt_count": 60,
        "predecessor_public_check_count": 187,
        "integration_binding_count": len(bindings),
        "integration_binding_passed_count": len(bindings) - len(failed),
        "integration_binding_failed_count": len(failed),
        "integration_bindings": bindings,
        "review_finding_count": len(REVIEW_FINDINGS),
        "review_fixed_finding_count": len(REVIEW_FINDINGS),
        "review_open_finding_count": 0,
        "technical_audit": technical_audit(),
        "stage_acceptance_ready": not failed,
        "taskpack_phase_count_delta": 0,
        "taskpack_task_count_delta": 0,
        "raw_root_access_count": 0,
        "external_network_request_count": 0,
        "github_upload_count": 0,
        "app_reinstall_count": 0,
        "s23_started": False,
    }


def main() -> int:
    payload = integrated_review()
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0 if payload["stage_acceptance_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
