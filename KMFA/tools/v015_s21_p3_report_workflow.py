#!/usr/bin/env python3
"""KMFA v1.5 S21-P3 report workflow, revision comparison and report center.

The kernel is deliberately local and public-synthetic.  It turns immutable
S21-P1/S21-P2 report versions into an append-only preview/review/approval/
internal-publication workflow, explains revisions, and applies report-center
view/download permissions.  It never creates a public share link, reads raw
business files, uploads GitHub, or reinstalls the App.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from KMFA.tools import v015_s15_p2_identity_roles as identity
from KMFA.tools import v015_s21_p1_report_model as report_model
from KMFA.tools import v015_s21_p2_report_generation as report_generation


RUN_PHASE_ID = "V015_S21_P3_REPORT_WORKFLOW"
ROADMAP_PHASE_ID = "S21-P3"
TASK_ID = "KMFA-V015-S21-P3-REPORT-WORKFLOW-20260717"
ACCEPTANCE_ID = "ACC-KMFA-V015-S21-P3-REPORT-WORKFLOW"
VERSION = "1.5.0-dev-s21p3"
DATA_CLASSIFICATION = report_generation.DATA_CLASSIFICATION
DEFAULT_EVENT_PATH = (
    Path(__file__).resolve().parents[1]
    / ".codex_private_runtime/v015_s21_p3_report_workflow/report_workflow_events.jsonl"
)

WORKFLOW_ACTIONS = ("PREVIEW", "SUBMIT", "REVIEW", "APPROVE", "PUBLISH")
WORKFLOW_STATES = (
    "PREVIEWED", "IN_REVIEW", "REVIEWED", "CHANGES_REQUESTED", "APPROVED", "PUBLISHED_INTERNAL"
)
ACTION_ROLES = {
    "PREVIEW": frozenset({"management", "finance", "reviewer"}),
    "SUBMIT": frozenset({"management", "finance"}),
    "REVIEW": frozenset({"reviewer"}),
    "APPROVE": frozenset({"reviewer"}),
    "PUBLISH": frozenset({"management"}),
}
VIEW_ROLES = frozenset({"management", "finance", "tax", "reviewer"})
DOWNLOAD_ROLES = frozenset({"management", "finance", "reviewer"})
FORMATS = frozenset({"HTML", "PDF", "CSV"})
REVIEW_DECISIONS = frozenset({"PASS", "REQUEST_CHANGES"})
EVENT_TYPES = (
    "REPORT_PREVIEWED", "REPORT_SUBMITTED", "REPORT_REVIEWED",
    "REPORT_CHANGES_REQUESTED", "REPORT_APPROVED", "REPORT_PUBLISHED_INTERNAL",
)

_IDEMPOTENCY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,127}$")
_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")


class ReportWorkflowError(ValueError):
    """A stable fail-closed error safe for the local report workbench."""

    def __init__(self, code: str, message_zh: str, *, status: int = 400) -> None:
        super().__init__(message_zh)
        self.code = code
        self.message_zh = message_zh
        self.status = status


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value)).hexdigest()


def _text(value: Any, field: str, *, minimum: int = 1, maximum: int = 240) -> str:
    result = str(value or "").strip()
    if len(result) < minimum or len(result) > maximum or any(ord(char) < 32 for char in result):
        raise ReportWorkflowError("FIELD_INVALID", f"{field} 不完整或过长")
    return result


def _actor(user_id: Any, role_id: Any, company_id: Any, allowed_roles: Iterable[str]) -> dict[str, Any]:
    user = _text(user_id, "人员", maximum=80)
    role = _text(role_id, "角色", maximum=40)
    company = _text(company_id, "公司", maximum=80)
    snapshot = identity.identity_snapshot(user, role, company)
    if snapshot.get("allowed") is not True:
        raise ReportWorkflowError(
            str(snapshot.get("reason_code") or "ACTOR_NOT_ALLOWED"),
            str(snapshot.get("reason_zh") or "当前人员、角色或公司无权执行此操作"),
            status=403,
        )
    if role not in set(allowed_roles):
        raise ReportWorkflowError("ROLE_NOT_ALLOWED", "当前角色不能执行这一步", status=403)
    return snapshot


def quality_gate(report: Mapping[str, Any], export: Mapping[str, Any]) -> dict[str, Any]:
    """Prove a generated report is fit to enter or leave the workflow."""

    try:
        snapshot = export.get("report_payload_snapshot")
        payload = dict(snapshot) if isinstance(snapshot, Mapping) else report_generation.build_report_payload(report)
        supplied_fingerprint = payload.get("report_payload_fingerprint")
        unsigned_payload = {key: value for key, value in payload.items() if key != "report_payload_fingerprint"}
        if supplied_fingerprint != report_generation._digest(unsigned_payload):
            raise report_generation.ReportGenerationError("REPORT_PAYLOAD_TAMPERED", "报告数字快照完整性校验失败", status=409)
    except (report_generation.ReportGenerationError, KeyError, TypeError) as error:
        return {
            "schema_version": "kmfa.v015.s21p3.quality_gate.v1",
            "status": "FAIL", "check_count": 1, "pass_count": 0, "failed_count": 1,
            "checks": [{"check_id": "REPORT-PAYLOAD", "status": "FAIL", "detail": str(error)}],
            "quality_fingerprint": None,
        }
    consistency = export.get("cross_format_consistency") if isinstance(export.get("cross_format_consistency"), Mapping) else {}
    files = export.get("files") if isinstance(export.get("files"), Mapping) else {}
    checks = {
        "REPORT-CLASSIFICATION": report.get("data_classification") == report_model.DATA_CLASSIFICATION,
        "REPORT-COMPLETE": report.get("trust_and_limitations", {}).get("complete_report_claim_allowed") is True,
        "VERSION-BOUND": export.get("report_version_id") == report.get("report_version_id"),
        "PAYLOAD-BOUND": export.get("report_payload_fingerprint") == payload.get("report_payload_fingerprint"),
        "SOURCE-BOUND": export.get("source_binding_fingerprint") == report.get("source_binding_fingerprint"),
        "FORMULA-BOUND": export.get("formula_binding_fingerprint") == report.get("formula_binding_fingerprint"),
        "THREE-FORMATS": FORMATS.issubset(files),
        "FILE-HASHES": FORMATS.issubset(files) and all(_SHA256.fullmatch(str(files[name].get("sha256", ""))) for name in FORMATS),
        "FILE-SIZES": FORMATS.issubset(files) and all(isinstance(files[name].get("size_bytes"), int) and files[name]["size_bytes"] > 0 for name in FORMATS),
        "CONSISTENCY-PASS": consistency.get("status") == "PASS",
        "VALUE-COUNT": consistency.get("numeric_value_count") == len(report_generation.canonical_numeric_values(payload)),
        "ZERO-DIFFERENCE": consistency.get("difference_integer") == 0,
        "APPROVAL-CLEAN": export.get("approval_or_publication_performed") is False,
        "RAW-CLEAN": export.get("raw_access_count") == 0,
        "PUBLIC-SYNTHETIC": export.get("data_classification") == DATA_CLASSIFICATION,
    }
    rows = [
        {"check_id": key, "status": "PASS" if passed else "FAIL", "detail": "verified" if passed else "blocked"}
        for key, passed in checks.items()
    ]
    failed = [row for row in rows if row["status"] == "FAIL"]
    fingerprint_input = {
        "report_version_id": report.get("report_version_id"),
        "report_payload_fingerprint": payload.get("report_payload_fingerprint"),
        "export_id": export.get("export_id"),
        "files": files,
        "cross_format_consistency": consistency,
    }
    return {
        "schema_version": "kmfa.v015.s21p3.quality_gate.v1",
        "status": "PASS" if not failed else "FAIL",
        "check_count": len(rows), "pass_count": len(rows) - len(failed), "failed_count": len(failed),
        "checks": rows,
        "quality_fingerprint": _digest(fingerprint_input) if not failed else None,
    }


def _source_index(report: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    return {str(row.get("domain_id")): row for row in report.get("source_bindings", [])}


def _formula_index(report: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    return {str(row.get("formula_id")): row for row in report.get("formula_bindings", [])}


def revision_bindings(
    report: Mapping[str, Any], source_version_updates: Mapping[str, Any]
) -> list[dict[str, Any]]:
    """Return a complete immutable source-binding snapshot for a revision."""

    if not isinstance(source_version_updates, Mapping) or not source_version_updates:
        raise ReportWorkflowError("REVISION_CHANGE_REQUIRED", "修订必须说明至少一项资料版本变化")
    rows = [dict(row) for row in report.get("source_bindings", [])]
    by_domain = {row.get("domain_id"): row for row in rows}
    unknown = sorted(set(source_version_updates) - set(by_domain))
    if unknown:
        raise ReportWorkflowError("REVISION_SOURCE_UNKNOWN", "修订包含未知资料类别")
    changed = 0
    for domain, raw_version in source_version_updates.items():
        version = _text(raw_version, "资料版本", maximum=120)
        if by_domain[domain].get("version_ref") != version:
            by_domain[domain]["version_ref"] = version
            by_domain[domain]["state"] = "AVAILABLE"
            changed += 1
    if not changed:
        raise ReportWorkflowError("REVISION_HAS_NO_CHANGE", "新资料版本与当前版本相同")
    return rows


def compare_versions(left: Mapping[str, Any], right: Mapping[str, Any]) -> dict[str, Any]:
    """Explain every source, formula and report-value difference."""

    if left.get("report_family_id") != right.get("report_family_id") or left.get("company_id") != right.get("company_id"):
        raise ReportWorkflowError("REPORT_FAMILY_MISMATCH", "只能比较同一公司、同一期间的报告版本", status=409)
    if int(right.get("version_number", 0)) <= int(left.get("version_number", 0)):
        raise ReportWorkflowError("VERSION_ORDER_INVALID", "比较顺序必须从旧版本到新版本", status=409)
    reason = str(right.get("revision_reason_zh") or "").strip()
    changes: list[dict[str, Any]] = []
    left_sources, right_sources = _source_index(left), _source_index(right)
    for domain in sorted(set(left_sources) | set(right_sources)):
        before, after = left_sources.get(domain, {}), right_sources.get(domain, {})
        for field in ("version_ref", "state"):
            if before.get(field) != after.get(field):
                changes.append({
                    "change_type": "SOURCE", "field": f"{domain}.{field}",
                    "before": before.get(field), "after": after.get(field),
                    "source_ref": after.get("version_ref") or before.get("version_ref"),
                    "reason_zh": reason,
                })
    left_formulas, right_formulas = _formula_index(left), _formula_index(right)
    for formula_id in sorted(set(left_formulas) | set(right_formulas)):
        before, after = left_formulas.get(formula_id, {}), right_formulas.get(formula_id, {})
        if before.get("formula_version") != after.get("formula_version"):
            changes.append({
                "change_type": "FORMULA", "field": formula_id,
                "before": before.get("formula_version"), "after": after.get("formula_version"),
                "source_ref": formula_id, "reason_zh": reason,
            })
    left_values = report_generation.canonical_numeric_values(report_generation.build_report_payload(left))
    right_values = report_generation.canonical_numeric_values(report_generation.build_report_payload(right))
    for key in sorted(set(left_values) | set(right_values)):
        if left_values.get(key) != right_values.get(key):
            changes.append({
                "change_type": "VALUE", "field": key,
                "before": left_values.get(key), "after": right_values.get(key),
                "source_ref": right.get("source_binding_fingerprint"), "reason_zh": reason,
            })
    unexplained = [row for row in changes if not row.get("source_ref") or len(str(row.get("reason_zh") or "")) < 6]
    result = {
        "schema_version": "kmfa.v015.s21p3.report_comparison.v1",
        "report_family_id": left.get("report_family_id"),
        "from_version_id": left.get("report_version_id"),
        "to_version_id": right.get("report_version_id"),
        "direct_revision": right.get("supersedes_version_id") == left.get("report_version_id"),
        "revision_reason_zh": reason,
        "difference_count": len(changes),
        "source_difference_count": sum(row["change_type"] == "SOURCE" for row in changes),
        "formula_difference_count": sum(row["change_type"] == "FORMULA" for row in changes),
        "value_difference_count": sum(row["change_type"] == "VALUE" for row in changes),
        "unexplained_difference_count": len(unexplained),
        "changes": changes,
        "publication_allowed": bool(changes) and not unexplained,
    }
    result["comparison_fingerprint"] = _digest(result)
    return result


class ReportWorkflowJournal:
    """Append-only, hash-linked workflow events with derived projections."""

    def __init__(self, path: Path | str = DEFAULT_EVENT_PATH) -> None:
        self.path = Path(path)
        self.lock_path = self.path.with_suffix(self.path.suffix + ".lock")

    def _locked(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        handle = self.lock_path.open("a+", encoding="utf-8")
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        return handle

    def _read_unlocked(self) -> list[dict[str, Any]]:
        if not self.path.is_file():
            return []
        rows: list[dict[str, Any]] = []
        previous, keys = "GENESIS", set()
        for sequence, line in enumerate(self.path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as error:
                raise ReportWorkflowError("WORKFLOW_HISTORY_CORRUPTED", "报告流程历史无法读取", status=409) from error
            supplied = row.get("event_hash")
            expected = _digest({key: value for key, value in row.items() if key != "event_hash"})
            if (
                row.get("sequence") != sequence or row.get("previous_event_hash") != previous
                or supplied != expected or row.get("idempotency_key") in keys
            ):
                raise ReportWorkflowError("WORKFLOW_HISTORY_CORRUPTED", "报告流程历史完整性校验失败", status=409)
            rows.append(row)
            previous, keys = str(supplied), keys | {row.get("idempotency_key")}
        return rows

    def read(self) -> list[dict[str, Any]]:
        lock = self._locked()
        try:
            return self._read_unlocked()
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
            lock.close()

    def _append_locked(self, rows: list[dict[str, Any]], event: dict[str, Any]) -> dict[str, Any]:
        existing = next((row for row in rows if row["idempotency_key"] == event["idempotency_key"]), None)
        if existing:
            if existing.get("request_fingerprint") != event.get("request_fingerprint"):
                raise ReportWorkflowError("IDEMPOTENCY_CONFLICT", "同一请求编号不能用于不同流程操作", status=409)
            return existing
        value = dict(event)
        value["sequence"] = len(rows) + 1
        value["event_id"] = f"EVT-S21P3-{value['sequence']:04d}"
        value["previous_event_hash"] = rows[-1]["event_hash"] if rows else "GENESIS"
        value["event_hash"] = _digest(value)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        self._read_unlocked()
        return value

    @staticmethod
    def _project(case_events: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
        if not case_events or case_events[0].get("event_type") != "REPORT_PREVIEWED":
            raise ReportWorkflowError("WORKFLOW_CASE_CORRUPTED", "报告流程缺少预览起点", status=409)
        first = case_events[0]
        state = "PREVIEWED"
        for event in case_events[1:]:
            state = {
                "REPORT_SUBMITTED": "IN_REVIEW",
                "REPORT_REVIEWED": "REVIEWED",
                "REPORT_CHANGES_REQUESTED": "CHANGES_REQUESTED",
                "REPORT_APPROVED": "APPROVED",
                "REPORT_PUBLISHED_INTERNAL": "PUBLISHED_INTERNAL",
            }.get(str(event.get("event_type")), state)
        latest = case_events[-1]
        return {
            "schema_version": "kmfa.v015.s21p3.report_workflow_case.v1",
            "case_id": first["case_id"], "report_version_id": first["report_version_id"],
            "report_family_id": first["report_snapshot"]["report_family_id"],
            "company_id": first["company_id"], "period": first["report_snapshot"]["period"],
            "export_id": first["export_snapshot"]["export_id"],
            "report_snapshot": first["report_snapshot"], "export_snapshot": first["export_snapshot"],
            "quality_gate": first["quality_gate"], "state": state,
            "state_zh": {
                "PREVIEWED": "已预览", "IN_REVIEW": "复核中", "REVIEWED": "复核通过",
                "CHANGES_REQUESTED": "需要修订", "APPROVED": "已批准", "PUBLISHED_INTERNAL": "已发布到内部报告中心",
            }[state],
            "event_count": len(case_events), "created_at": first["occurred_at"],
            "updated_at": latest["occurred_at"], "latest_comment_zh": latest["comment_zh"],
            "events": [
                {key: event.get(key) for key in (
                    "event_id", "event_type", "actor_user_id", "actor_role", "actor_label_zh",
                    "occurred_at", "comment_zh", "decision", "event_hash",
                ) if event.get(key) is not None}
                for event in case_events
            ],
            "internal_report_center_published": state == "PUBLISHED_INTERNAL",
            "external_publication_performed": False,
            "public_share_link": None,
        }

    def list(self) -> dict[str, Any]:
        rows = self.read()
        case_ids = list(dict.fromkeys(str(row["case_id"]) for row in rows))
        cases = [self._project([row for row in rows if row["case_id"] == case_id]) for case_id in case_ids]
        return {
            "schema_version": "kmfa.v015.s21p3.report_workflow_list.v1",
            "case_count": len(cases), "cases": list(reversed(cases)),
            "history_overwrite_count": 0, "external_publication_count": 0,
        }

    def get(self, case_id: str) -> dict[str, Any]:
        key = _text(case_id, "流程编号", maximum=80)
        rows = [row for row in self.read() if row.get("case_id") == key]
        if not rows:
            raise ReportWorkflowError("WORKFLOW_CASE_NOT_FOUND", "没有找到这条报告流程", status=404)
        return self._project(rows)

    def preview(
        self, report: Mapping[str, Any], export: Mapping[str, Any], *,
        user_id: str, role_id: str, company_id: str, comment_zh: str,
        idempotency_key: str, occurred_at: str | None = None,
    ) -> dict[str, Any]:
        actor = _actor(user_id, role_id, company_id, ACTION_ROLES["PREVIEW"])
        comment = _text(comment_zh, "预览意见", minimum=4)
        key = _text(idempotency_key, "请求编号", minimum=8, maximum=128)
        if not _IDEMPOTENCY.fullmatch(key):
            raise ReportWorkflowError("IDEMPOTENCY_INVALID", "请求编号格式不正确")
        if report.get("company_id") != company_id:
            raise ReportWorkflowError("COMPANY_MISMATCH", "报告与当前公司主体不一致", status=403)
        gate = quality_gate(report, export)
        if gate["status"] != "PASS":
            raise ReportWorkflowError("QUALITY_GATE_FAILED", "报告质量门禁未通过，不能进入流程", status=409)
        case_id = "CASE-S21P3-" + hashlib.sha256(
            f"{report.get('report_version_id')}|{export.get('export_id')}".encode()
        ).hexdigest()[:12].upper()
        event = {
            "schema_version": "kmfa.v015.s21p3.report_workflow_event.v1",
            "event_type": "REPORT_PREVIEWED", "case_id": case_id,
            "report_version_id": report.get("report_version_id"), "company_id": company_id,
            "report_snapshot": json.loads(json.dumps(report)),
            "export_snapshot": json.loads(json.dumps(export)), "quality_gate": gate,
            "actor_user_id": user_id, "actor_role": role_id, "actor_label_zh": actor["user_label_zh"],
            "occurred_at": occurred_at or _now(), "comment_zh": comment,
            "idempotency_key": key,
        }
        event["request_fingerprint"] = _digest({key: value for key, value in event.items() if key not in {"occurred_at"}})
        lock = self._locked()
        try:
            rows = self._read_unlocked()
            duplicate_case = [row for row in rows if row["case_id"] == case_id]
            if duplicate_case and not any(row["idempotency_key"] == key for row in duplicate_case):
                raise ReportWorkflowError("WORKFLOW_CASE_EXISTS", "这个报告导出已经进入流程", status=409)
            self._append_locked(rows, event)
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
            lock.close()
        return self.get(case_id)

    def _transition(
        self, case_id: str, *, action: str, user_id: str, role_id: str,
        company_id: str, comment_zh: str, idempotency_key: str,
        decision: str | None = None, occurred_at: str | None = None,
    ) -> dict[str, Any]:
        target_action = _text(action, "流程动作", maximum=20).upper()
        if target_action not in WORKFLOW_ACTIONS[1:]:
            raise ReportWorkflowError("WORKFLOW_ACTION_INVALID", "报告流程动作不正确")
        actor = _actor(user_id, role_id, company_id, ACTION_ROLES[target_action])
        comment = _text(comment_zh, "处理意见", minimum=4)
        key = _text(idempotency_key, "请求编号", minimum=8, maximum=128)
        if not _IDEMPOTENCY.fullmatch(key):
            raise ReportWorkflowError("IDEMPOTENCY_INVALID", "请求编号格式不正确")
        lock = self._locked()
        try:
            rows = self._read_unlocked()
            existing = next((row for row in rows if row.get("idempotency_key") == key), None)
            if existing:
                same_request = (
                    existing.get("case_id") == case_id
                    and existing.get("actor_user_id") == user_id
                    and existing.get("actor_role") == role_id
                    and existing.get("company_id") == company_id
                    and existing.get("comment_zh") == comment
                    and (
                        target_action != "REVIEW"
                        or existing.get("decision") == str(decision or "").strip().upper()
                    )
                )
                if not same_request:
                    raise ReportWorkflowError("IDEMPOTENCY_CONFLICT", "同一请求编号不能用于不同流程操作", status=409)
                case_rows = [row for row in rows if row.get("case_id") == case_id]
                return self._project(case_rows)
            case_rows = [row for row in rows if row.get("case_id") == case_id]
            if not case_rows:
                raise ReportWorkflowError("WORKFLOW_CASE_NOT_FOUND", "没有找到这条报告流程", status=404)
            case = self._project(case_rows)
            if case["company_id"] != company_id:
                raise ReportWorkflowError("COMPANY_MISMATCH", "报告与当前公司主体不一致", status=403)
            expected_state = {"SUBMIT": "PREVIEWED", "REVIEW": "IN_REVIEW", "APPROVE": "REVIEWED", "PUBLISH": "APPROVED"}[target_action]
            if case["state"] != expected_state:
                raise ReportWorkflowError("WORKFLOW_STATE_INVALID", "当前状态不能执行这一步", status=409)
            event_type = {
                "SUBMIT": "REPORT_SUBMITTED", "APPROVE": "REPORT_APPROVED", "PUBLISH": "REPORT_PUBLISHED_INTERNAL"
            }.get(target_action)
            normalized_decision = None
            if target_action == "REVIEW":
                normalized_decision = _text(decision, "复核决定", maximum=30).upper()
                if normalized_decision not in REVIEW_DECISIONS:
                    raise ReportWorkflowError("REVIEW_DECISION_INVALID", "复核决定不正确")
                event_type = "REPORT_REVIEWED" if normalized_decision == "PASS" else "REPORT_CHANGES_REQUESTED"
            if target_action in {"SUBMIT", "PUBLISH"}:
                gate = quality_gate(case["report_snapshot"], case["export_snapshot"])
                if gate["status"] != "PASS" or gate["quality_fingerprint"] != case["quality_gate"]["quality_fingerprint"]:
                    raise ReportWorkflowError("QUALITY_GATE_FAILED", "报告质量门禁已失效，不能继续", status=409)
            if target_action == "APPROVE":
                submit = next(row for row in case_rows if row["event_type"] == "REPORT_SUBMITTED")
                if role_id == submit.get("actor_role"):
                    raise ReportWorkflowError("ROLE_SEPARATION_REQUIRED", "发起角色不能同时批准", status=403)
            event = {
                "schema_version": "kmfa.v015.s21p3.report_workflow_event.v1",
                "event_type": event_type, "case_id": case_id,
                "report_version_id": case["report_version_id"], "company_id": company_id,
                "actor_user_id": user_id, "actor_role": role_id, "actor_label_zh": actor["user_label_zh"],
                "occurred_at": occurred_at or _now(), "comment_zh": comment,
                "decision": normalized_decision, "idempotency_key": key,
                "external_publication_performed": False,
                "publication_scope": "INTERNAL_REPORT_CENTER_ONLY" if target_action == "PUBLISH" else None,
            }
            event["request_fingerprint"] = _digest({key: value for key, value in event.items() if key not in {"occurred_at"}})
            self._append_locked(rows, event)
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
            lock.close()
        return self.get(case_id)

    def submit(self, case_id: str, **kwargs: Any) -> dict[str, Any]:
        return self._transition(case_id, action="SUBMIT", **kwargs)

    def review(self, case_id: str, **kwargs: Any) -> dict[str, Any]:
        return self._transition(case_id, action="REVIEW", **kwargs)

    def approve(self, case_id: str, **kwargs: Any) -> dict[str, Any]:
        return self._transition(case_id, action="APPROVE", **kwargs)

    def publish(self, case_id: str, **kwargs: Any) -> dict[str, Any]:
        return self._transition(case_id, action="PUBLISH", **kwargs)


def _status_for_report(report_version_id: str, cases: Sequence[Mapping[str, Any]]) -> str:
    case = next((row for row in cases if row.get("report_version_id") == report_version_id), None)
    return str(case.get("state")) if case else "GENERATED"


def authorize_download(
    report: Mapping[str, Any], case: Mapping[str, Any] | None, *,
    user_id: str, role_id: str, company_id: str, format_name: str,
) -> dict[str, Any]:
    try:
        actor = _actor(user_id, role_id, company_id, DOWNLOAD_ROLES)
    except ReportWorkflowError as error:
        return {"allowed": False, "code": error.code, "reason_zh": error.message_zh}
    format_key = str(format_name or "").upper()
    if report.get("company_id") != company_id:
        return {"allowed": False, "code": "COMPANY_MISMATCH", "reason_zh": "报告与当前公司主体不一致"}
    if format_key not in FORMATS:
        return {"allowed": False, "code": "FORMAT_NOT_ALLOWED", "reason_zh": "报告格式不正确"}
    state = str(case.get("state")) if case else "GENERATED"
    if role_id == "management" and state != "PUBLISHED_INTERNAL":
        return {"allowed": False, "code": "REPORT_NOT_PUBLISHED", "reason_zh": "经营负责人只能下载已发布到内部报告中心的版本"}
    return {
        "allowed": True, "code": "DOWNLOAD_ALLOWED", "reason_zh": "允许受控下载",
        "actor_label_zh": actor["user_label_zh"], "format": format_key,
        "authenticated_download_required": True, "public_link_created": False,
    }


def report_center(
    reports: Sequence[Mapping[str, Any]], exports: Sequence[Mapping[str, Any]],
    cases: Sequence[Mapping[str, Any]], *, user_id: str, role_id: str, company_id: str,
    period_kind: str | None = None, period_key: str | None = None,
    status: str | None = None, version: str | None = None, report_type: str | None = None,
) -> dict[str, Any]:
    actor = _actor(user_id, role_id, company_id, VIEW_ROLES)
    export_by_version = {str(row.get("report_version_id")): row for row in exports}
    case_by_version = {str(row.get("report_version_id")): row for row in cases}
    rows: list[dict[str, Any]] = []
    for report in reports:
        if report.get("company_id") != company_id:
            continue
        current_status = _status_for_report(str(report.get("report_version_id")), cases)
        period = report.get("period", {})
        if period_kind and period.get("period_kind") != period_kind:
            continue
        if period_key and period.get("period_key") != period_key:
            continue
        if status and current_status != status:
            continue
        if version and report.get("report_version_id") != version:
            continue
        if report_type and period.get("period_kind") != report_type:
            continue
        export = export_by_version.get(str(report.get("report_version_id")))
        case = case_by_version.get(str(report.get("report_version_id")))
        downloadable = []
        if export:
            for format_name in ("HTML", "PDF", "CSV"):
                if authorize_download(
                    report, case, user_id=user_id, role_id=role_id,
                    company_id=company_id, format_name=format_name,
                )["allowed"]:
                    downloadable.append(format_name)
        rows.append({
            "report_version_id": report.get("report_version_id"),
            "report_family_id": report.get("report_family_id"),
            "version_number": report.get("version_number"), "version_label_zh": report.get("version_label_zh"),
            "company_id": company_id, "period": period,
            "report_type": period.get("period_kind"), "report_type_label_zh": period.get("period_kind_label_zh"),
            "status": current_status, "status_zh": case.get("state_zh") if case else "已生成",
            "export_id": export.get("export_id") if export else None,
            "view_allowed": True, "download_formats": downloadable,
            "public_url": None, "share_link_enabled": False,
            "authenticated_download_required": True,
        })
    rows.sort(key=lambda row: (str(row["period"].get("end_date")), int(row.get("version_number") or 0)), reverse=True)
    return {
        "schema_version": "kmfa.v015.s21p3.report_center.v1",
        "user_id": user_id, "user_label_zh": actor["user_label_zh"], "role_id": role_id,
        "company_id": company_id, "result_count": len(rows), "reports": rows,
        "filter_count": sum(bool(value) for value in (period_kind, period_key, status, version, report_type)),
        "public_link_count": 0, "cross_company_result_count": 0,
    }


def options_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s21p3.report_workflow_options.v1",
        "workflow_actions": list(WORKFLOW_ACTIONS), "workflow_states": list(WORKFLOW_STATES),
        "review_decisions": list(sorted(REVIEW_DECISIONS)),
        "report_center_filters": ["period_kind", "period_key", "company_id", "report_type", "status", "version"],
        "view_roles": list(sorted(VIEW_ROLES)), "download_roles": list(sorted(DOWNLOAD_ROLES)),
        "internal_publication_only": True, "public_share_links_allowed": False,
        "github_upload_in_scope": False, "app_reinstall_in_scope": False,
    }


def verify_phase() -> dict[str, Any]:
    """Exercise the three S21-P3 tasks without persistent or external effects."""

    checks: list[dict[str, Any]] = []

    def add(check_id: str, passed: bool, detail: str) -> None:
        checks.append({"check_id": check_id, "status": "PASS" if passed else "FAIL", "detail": detail})

    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        models = report_model.ReportModelJournal(root / "models.jsonl")
        exports = report_generation.ReportExportJournal(root / "exports.jsonl", root / "bundles")
        workflows = ReportWorkflowJournal(root / "workflow.jsonl")
        first = models.create(
            company_id="demo-north", period_kind="MONTHLY", period_key="2026-07",
            source_bindings=report_model.default_source_bindings(),
            formula_bindings=report_model.default_formula_bindings(), created_by="公开演示负责人",
            idempotency_key="verify-s21p3-model-001", recorded_at="2026-07-17T00:00:00+00:00",
        )
        first_export = exports.create(first, idempotency_key="verify-s21p3-export-001", recorded_at="2026-07-17T00:01:00+00:00")
        gate = quality_gate(first, first_export)
        for row in gate["checks"]:
            add("GATE-" + row["check_id"], row["status"] == "PASS", row["detail"])
        case = workflows.preview(
            first, first_export, user_id="demo-owner", role_id="finance", company_id="demo-north",
            comment_zh="已核对网页、PDF 和专业附表", idempotency_key="verify-s21p3-preview-001",
            occurred_at="2026-07-17T00:02:00+00:00",
        )
        add("PREVIEW-STATE", case["state"] == "PREVIEWED", case["state"])
        add("PREVIEW-ACTOR", case["events"][0]["actor_role"] == "finance", case["events"][0]["actor_role"])
        case = workflows.submit(
            case["case_id"], user_id="demo-owner", role_id="finance", company_id="demo-north",
            comment_zh="提交审核并保留完整来源说明", idempotency_key="verify-s21p3-submit-001",
            occurred_at="2026-07-17T00:03:00+00:00",
        )
        add("SUBMIT-STATE", case["state"] == "IN_REVIEW", case["state"])
        try:
            workflows.publish(
                case["case_id"], user_id="demo-owner", role_id="management", company_id="demo-north",
                comment_zh="尝试跳过审核", idempotency_key="verify-s21p3-early-publish-001",
            )
            early_publish_denied = False
        except ReportWorkflowError as error:
            early_publish_denied = error.code == "WORKFLOW_STATE_INVALID"
        add("EARLY-PUBLISH-DENIED", early_publish_denied, "state gate")
        case = workflows.review(
            case["case_id"], user_id="demo-owner", role_id="reviewer", company_id="demo-north",
            comment_zh="数字一致且来源完整，复核通过", decision="PASS",
            idempotency_key="verify-s21p3-review-001", occurred_at="2026-07-17T00:04:00+00:00",
        )
        add("REVIEW-STATE", case["state"] == "REVIEWED", case["state"])
        add("REVIEW-DECISION", case["events"][-1]["decision"] == "PASS", str(case["events"][-1].get("decision")))
        case = workflows.approve(
            case["case_id"], user_id="demo-owner", role_id="reviewer", company_id="demo-north",
            comment_zh="确认质量门禁、范围和内部用途", idempotency_key="verify-s21p3-approve-001",
            occurred_at="2026-07-17T00:05:00+00:00",
        )
        add("APPROVE-STATE", case["state"] == "APPROVED", case["state"])
        case = workflows.publish(
            case["case_id"], user_id="demo-owner", role_id="management", company_id="demo-north",
            comment_zh="发布到内部报告中心供授权人员查看", idempotency_key="verify-s21p3-publish-001",
            occurred_at="2026-07-17T00:06:00+00:00",
        )
        add("PUBLISH-STATE", case["state"] == "PUBLISHED_INTERNAL", case["state"])
        add("FIVE-EVENTS", case["event_count"] == 5, str(case["event_count"]))
        add("EACH-EVENT-ACTOR", all(row.get("actor_user_id") and row.get("actor_role") for row in case["events"]), "actor bound")
        add("EACH-EVENT-TIME", all(row.get("occurred_at") for row in case["events"]), "time bound")
        add("EACH-EVENT-COMMENT", all(row.get("comment_zh") for row in case["events"]), "comment bound")
        add("NO-EXTERNAL-PUBLICATION", case["external_publication_performed"] is False, "zero")
        add("NO-PUBLIC-LINK", case["public_share_link"] is None, "none")
        same = workflows.publish(
            case["case_id"], user_id="demo-owner", role_id="management", company_id="demo-north",
            comment_zh="发布到内部报告中心供授权人员查看", idempotency_key="verify-s21p3-publish-001",
            occurred_at="2026-07-17T00:06:00+00:00",
        )
        add("PUBLISH-IDEMPOTENT", same["event_count"] == 5, str(same["event_count"]))

        bindings = revision_bindings(first, {"key_matters": "S20P2-CONFIRMATIONS-2026-07-V2"})
        second = models.revise(
            first["report_version_id"], source_bindings=bindings,
            revision_reason_zh="补充本期重点事项复核结果和负责人意见",
            created_by="公开演示负责人", idempotency_key="verify-s21p3-model-002",
            recorded_at="2026-07-17T00:07:00+00:00",
        )
        second_export = exports.create(second, idempotency_key="verify-s21p3-export-002", recorded_at="2026-07-17T00:08:00+00:00")
        comparison = compare_versions(first, second)
        add("REVISION-NEW-VERSION", second["version_number"] == 2 and second["supersedes_version_id"] == first["report_version_id"], second["report_version_id"])
        add("COMPARISON-DIRECT", comparison["direct_revision"] is True, "direct")
        add("COMPARISON-CHANGE", comparison["difference_count"] >= 1, str(comparison["difference_count"]))
        add("COMPARISON-SOURCE", comparison["source_difference_count"] >= 1, str(comparison["source_difference_count"]))
        add("COMPARISON-EXPLAINED", comparison["unexplained_difference_count"] == 0, "zero")
        add("COMPARISON-PUBLISHABLE", comparison["publication_allowed"] is True, "true")
        add("OLD-VERSION-PRESERVED", models.get(first["report_version_id"])["event_hash"] == first["event_hash"], "immutable")
        add("SECOND-EXPORT-BOUND", second_export["report_version_id"] == second["report_version_id"], second_export["export_id"])

        revision_case = workflows.preview(
            second, second_export, user_id="demo-owner", role_id="finance", company_id="demo-north",
            comment_zh="预览修订版并核对变化来源", idempotency_key="verify-s21p3-preview-002",
            occurred_at="2026-07-17T00:09:00+00:00",
        )
        all_reports = models.list()["reports"]
        all_exports = exports.list()["exports"]
        all_cases = workflows.list()["cases"]
        finance_center = report_center(
            all_reports, all_exports, all_cases,
            user_id="demo-owner", role_id="finance", company_id="demo-north",
        )
        add("CENTER-TWO-VERSIONS", finance_center["result_count"] == 2, str(finance_center["result_count"]))
        add("CENTER-ORDER", finance_center["reports"][0]["report_version_id"] == second["report_version_id"], "latest first")
        add("CENTER-FILTERS", report_center(
            all_reports, all_exports, all_cases, user_id="demo-owner", role_id="finance",
            company_id="demo-north", status="PUBLISHED_INTERNAL",
        )["result_count"] == 1, "status filter")
        add("CENTER-NO-PUBLIC-LINKS", finance_center["public_link_count"] == 0 and all(row["public_url"] is None for row in finance_center["reports"]), "zero")
        add("FINANCE-DOWNLOAD", set(finance_center["reports"][0]["download_formats"]) == FORMATS, "three formats")
        management_center = report_center(
            all_reports, all_exports, all_cases,
            user_id="demo-owner", role_id="management", company_id="demo-north",
        )
        published = next(row for row in management_center["reports"] if row["status"] == "PUBLISHED_INTERNAL")
        draft = next(row for row in management_center["reports"] if row["status"] == "PREVIEWED")
        add("MANAGEMENT-PUBLISHED-DOWNLOAD", set(published["download_formats"]) == FORMATS, "allowed")
        add("MANAGEMENT-DRAFT-DENIED", draft["download_formats"] == [], "denied")
        tax_center = report_center(
            all_reports, all_exports, all_cases,
            user_id="demo-owner", role_id="tax", company_id="demo-north",
        )
        add("TAX-VIEW", tax_center["result_count"] == 2, "view")
        add("TAX-DOWNLOAD-DENIED", all(not row["download_formats"] for row in tax_center["reports"]), "denied")
        try:
            report_center(all_reports, all_exports, all_cases, user_id="demo-finance", role_id="finance", company_id="demo-south")
            cross_company_denied = False
        except ReportWorkflowError as error:
            cross_company_denied = error.code == "COMPANY_NOT_GRANTED"
        add("CROSS-COMPANY-DENIED", cross_company_denied, "default deny")
        add("CENTER-AUTHENTICATED", all(row["authenticated_download_required"] for row in finance_center["reports"]), "required")
        add("REVISION-CASE-PREVIEWED", revision_case["state"] == "PREVIEWED", revision_case["state"])
        add("HISTORY-APPEND-ONLY", workflows.list()["history_overwrite_count"] == 0, "zero")
        add("OPTIONS-NO-GITHUB", options_contract()["github_upload_in_scope"] is False, "closed")
        add("OPTIONS-NO-APP", options_contract()["app_reinstall_in_scope"] is False, "closed")

    failed = [row for row in checks if row["status"] != "PASS"]
    return {
        "schema_version": "kmfa.v015.s21p3.public_checks.v1",
        "run_phase_id": RUN_PHASE_ID, "roadmap_phase_id": ROADMAP_PHASE_ID,
        "status": "PASS" if not failed else "FAIL",
        "public_check_count": len(checks), "public_check_pass_count": len(checks) - len(failed),
        "public_check_failed_count": len(failed), "checks": checks,
        "raw_root_access_count": 0, "raw_write_count": 0,
        "external_network_request_count": 0, "external_publication_count": 0,
        "github_upload_performed": False, "app_reinstall_performed": False,
    }
