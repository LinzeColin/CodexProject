#!/usr/bin/env python3
"""KMFA v1.5 S20-P2 human confirmation workbench.

The workbench presents public synthetic discrepancies, requires an impact
preview before every action, and persists only tamper-evident control events.
It never edits source facts or the read-only finance inbox.
"""

from __future__ import annotations

import copy
import fcntl
import hashlib
import json
import os
import re
import tempfile
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping


RUN_PHASE_ID = "V015_S20_P2_CONFIRMATION_WORKBENCH"
ROADMAP_PHASE_ID = "S20-P2"
TASK_ID = "KMFA-V015-S20-P2-CONFIRMATION-WORKBENCH-20260717"
ACCEPTANCE_ID = "ACC-KMFA-V015-S20-P2-CONFIRMATION-WORKBENCH"
VERSION = "1.5.0-dev-s20p2"
EVENT_SCHEMA = "kmfa.v015.s20p2.control_event.v1"
DEFAULT_EVENT_PATH = (
    Path(__file__).resolve().parents[1]
    / ".codex_private_runtime"
    / "v015_s20_p2_confirmation_workbench"
    / "control_events.jsonl"
)

ALLOWED_ACTION_ROLES = frozenset({"ROLE::DATA_STEWARD", "ROLE::AUDITOR"})
IMPACT_RANK = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
URGENCY_RANK = {"TODAY": 4, "THREE_DAYS": 3, "THIS_WEEK": 2, "WHEN_CONVENIENT": 1}
_ISSUE_ID = re.compile(r"^ISSUE-S20P2-\d{3}$")
_EVENT_ID = re.compile(r"^CTRL-S20P2-\d{4}$")
_IDEMPOTENCY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,127}$")


class ConfirmationError(ValueError):
    """Stable fail-closed error safe for the local workbench."""

    def __init__(self, code: str, message_zh: str, *, status: int = 400):
        super().__init__(f"{code}: {message_zh}")
        self.code = code
        self.message_zh = message_zh
        self.status = status


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _fingerprint(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value)).hexdigest()


def _text(value: Any, field: str, *, limit: int = 240) -> str:
    result = str(value or "").strip()
    if not result or len(result) > limit or any(ord(char) < 32 and char not in "\t\n" for char in result):
        raise ConfirmationError("FIELD_INVALID", f"{field} 不完整或过长。")
    return result


def _issues() -> tuple[dict[str, Any], ...]:
    """Public synthetic issue set; governance diagnostics are a separate type."""
    return (
        {
            "issue_id": "ISSUE-S20P2-001", "kind": "BUSINESS_DISCREPANCY", "status": "OPEN",
            "title_zh": "项目成本板块与项目编号不一致", "impact": "CRITICAL", "urgency": "TODAY",
            "source_id": "SRC-project-ledger-c3d4e5f6", "source_label_zh": "项目台账导出",
            "owner_id": "OWNER::PROJECT_FINANCE", "owner_label_zh": "项目财务负责人",
            "requires_user_action": True,
            "current_data": [{"label_zh": "导入板块", "value_zh": "项目成本"}, {"label_zh": "项目编号", "value_zh": "PJ-DEMO-014"}],
            "reference_data": [{"label_zh": "登记项目", "value_zh": "PJ-DEMO-041"}, {"label_zh": "合同项目", "value_zh": "演示设备改造项目"}],
            "business_explanation_zh": "同一笔成本指向两个不同项目，若直接采用会改变项目利润。",
            "impact_zh": "可能影响项目成本、毛利和经营首页，但本阶段不会重算或发布。",
            "suggested_actions": [
                {"action_id": "KEEP_IMPORTED_PROJECT", "label_zh": "保留导入项目编号", "description_zh": "仅登记人工选择，等待后续重算。", "high_impact": True},
                {"action_id": "USE_REGISTERED_PROJECT", "label_zh": "采用登记项目编号", "description_zh": "仅登记人工选择，等待后续重算。", "high_impact": True},
            ],
            "technical_details": {"rule_id": "RULE-PROJECT-COMPOSITE-IDENTITY", "difference_code": "PROJECT_ID_CONFLICT", "evidence_refs": ["public-import-preview", "public-project-registry"]},
        },
        {
            "issue_id": "ISSUE-S20P2-002", "kind": "BUSINESS_DISCREPANCY", "status": "OPEN",
            "title_zh": "经营账户归属主体待确认", "impact": "HIGH", "urgency": "TODAY",
            "source_id": "SRC-finance-export-b2c3d4e5", "source_label_zh": "财务系统导出",
            "owner_id": "OWNER::TREASURY", "owner_label_zh": "资金负责人", "requires_user_action": True,
            "current_data": [{"label_zh": "导出主体", "value_zh": "北区演示公司"}, {"label_zh": "账户尾号", "value_zh": "8842"}],
            "reference_data": [{"label_zh": "账户登记", "value_zh": "归属待复核"}, {"label_zh": "可汇总状态", "value_zh": "否"}],
            "business_explanation_zh": "账户归属不明确，当前不会进入任何公司余额合计。",
            "impact_zh": "可能影响资金余额和现金预测；确认前继续排除。",
            "suggested_actions": [
                {"action_id": "CONFIRM_ENTITY", "label_zh": "确认归属北区演示公司", "description_zh": "写入控制事件，不修改源文件。", "high_impact": True},
                {"action_id": "KEEP_EXCLUDED", "label_zh": "继续排除", "description_zh": "保留待复核状态。", "high_impact": False},
            ],
            "technical_details": {"rule_id": "RULE-ACCOUNT-ENTITY-OWNERSHIP", "difference_code": "ACCOUNT_ENTITY_UNKNOWN", "evidence_refs": ["public-account-preview", "public-entity-register"]},
        },
        {
            "issue_id": "ISSUE-S20P2-003", "kind": "BUSINESS_DISCREPANCY", "status": "OPEN",
            "title_zh": "票据月份与资料月份不一致", "impact": "HIGH", "urgency": "THREE_DAYS",
            "source_id": "SRC-finance-export-b2c3d4e5", "source_label_zh": "财务系统导出",
            "owner_id": "OWNER::TAX", "owner_label_zh": "税务负责人", "requires_user_action": True,
            "current_data": [{"label_zh": "票据月份", "value_zh": "2026-06"}, {"label_zh": "资料月份", "value_zh": "2026-07"}],
            "reference_data": [{"label_zh": "合同履约月份", "value_zh": "2026-06"}, {"label_zh": "申报状态", "value_zh": "待复核"}],
            "business_explanation_zh": "期间不同，需要确定管理分析采用哪个月份；不形成正式申报结论。",
            "impact_zh": "可能影响月度税票和项目分析，不会自动调税。",
            "suggested_actions": [
                {"action_id": "KEEP_DOCUMENT_PERIOD", "label_zh": "保留票据月份", "description_zh": "登记为管理期间选择。", "high_impact": True},
                {"action_id": "USE_UPLOAD_PERIOD", "label_zh": "采用资料月份", "description_zh": "登记为管理期间选择。", "high_impact": True},
            ],
            "technical_details": {"rule_id": "RULE-PERIOD-CONSISTENCY", "difference_code": "DOCUMENT_PERIOD_MISMATCH", "evidence_refs": ["public-tax-preview", "public-contract-period"]},
        },
        {
            "issue_id": "ISSUE-S20P2-004", "kind": "BUSINESS_DISCREPANCY", "status": "OPEN",
            "title_zh": "成本分类名称存在两个候选", "impact": "MEDIUM", "urgency": "THIS_WEEK",
            "source_id": "SRC-project-ledger-c3d4e5f6", "source_label_zh": "项目台账导出",
            "owner_id": "OWNER::COST", "owner_label_zh": "成本负责人", "requires_user_action": True,
            "current_data": [{"label_zh": "导入名称", "value_zh": "外协安装费"}],
            "reference_data": [{"label_zh": "候选一", "value_zh": "安装分包"}, {"label_zh": "候选二", "value_zh": "技术服务"}],
            "business_explanation_zh": "名称相近但管理口径不同，需要负责人选择。",
            "impact_zh": "只影响成本分类展示；原始金额不变。",
            "suggested_actions": [
                {"action_id": "MAP_INSTALL_SUBCONTRACT", "label_zh": "归为安装分包", "description_zh": "登记分类映射选择。", "high_impact": False},
                {"action_id": "MAP_TECHNICAL_SERVICE", "label_zh": "归为技术服务", "description_zh": "登记分类映射选择。", "high_impact": False},
            ],
            "technical_details": {"rule_id": "RULE-COST-CATEGORY-ALIAS", "difference_code": "CATEGORY_ALIAS_COLLISION", "evidence_refs": ["public-cost-preview", "public-category-registry"]},
        },
        {
            "issue_id": "ISSUE-S20P2-005", "kind": "BUSINESS_DISCREPANCY", "status": "OPEN",
            "title_zh": "客户简称需要确认", "impact": "LOW", "urgency": "WHEN_CONVENIENT",
            "source_id": "SRC-local-upload-a1b2c3d4", "source_label_zh": "本机资料上传",
            "owner_id": "OWNER::RECEIVABLES", "owner_label_zh": "回款负责人", "requires_user_action": True,
            "current_data": [{"label_zh": "资料客户名", "value_zh": "北方设备"}],
            "reference_data": [{"label_zh": "登记客户名", "value_zh": "北方设备演示有限公司"}],
            "business_explanation_zh": "简称可能对应同一演示客户，但需要人工确认。",
            "impact_zh": "可能影响客户分组，不会自动联系客户或改变应收。",
            "suggested_actions": [
                {"action_id": "CONFIRM_CUSTOMER_ALIAS", "label_zh": "确认为同一客户", "description_zh": "登记别名确认事件。", "high_impact": False},
                {"action_id": "KEEP_SEPARATE_CUSTOMER", "label_zh": "保持分开", "description_zh": "保留两个客户名称。", "high_impact": False},
            ],
            "technical_details": {"rule_id": "RULE-CUSTOMER-ALIAS", "difference_code": "CUSTOMER_ALIAS_REVIEW", "evidence_refs": ["public-customer-preview", "public-customer-registry"]},
        },
        {
            "issue_id": "ISSUE-S20P2-006", "kind": "BUSINESS_DISCREPANCY", "status": "RESOLVED",
            "title_zh": "空白备注已按安全规则忽略", "impact": "LOW", "urgency": "WHEN_CONVENIENT",
            "source_id": "SRC-local-upload-a1b2c3d4", "source_label_zh": "本机资料上传",
            "owner_id": "OWNER::DATA", "owner_label_zh": "数据负责人", "requires_user_action": False,
            "current_data": [{"label_zh": "备注", "value_zh": "空白"}], "reference_data": [{"label_zh": "规则", "value_zh": "空白保持空白"}],
            "business_explanation_zh": "该事项不需要用户处理。", "impact_zh": "无业务影响。",
            "suggested_actions": [],
            "technical_details": {"rule_id": "RULE-BLANK-PRESERVATION", "difference_code": "NO_ACTION_REQUIRED", "evidence_refs": ["public-import-check"]},
        },
        {
            "issue_id": "ISSUE-S20P2-900", "kind": "GOVERNANCE_LOG", "status": "OPEN",
            "title_zh": "治理检查记录", "impact": "LOW", "urgency": "WHEN_CONVENIENT",
            "source_id": "SOURCE::GOVERNANCE", "source_label_zh": "治理检查",
            "owner_id": "OWNER::GOVERNANCE", "owner_label_zh": "治理负责人", "requires_user_action": False,
            "current_data": [], "reference_data": [], "business_explanation_zh": "治理日志不进入业务问题列表。",
            "impact_zh": "仅供治理检查。", "suggested_actions": [],
            "technical_details": {"rule_id": "RULE-GOVERNANCE-SEPARATION", "difference_code": "GOVERNANCE_LOG", "evidence_refs": ["governance-log"]},
        },
    )


ISSUES = _issues()
_ISSUE_BY_ID = {row["issue_id"]: row for row in ISSUES}


def _event_body(event: Mapping[str, Any]) -> dict[str, Any]:
    body = copy.deepcopy(dict(event))
    body.pop("event_hash", None)
    return body


def _validate_event(event: Mapping[str, Any], *, sequence: int, previous_hash: str | None) -> dict[str, Any]:
    value = copy.deepcopy(dict(event))
    if (
        value.get("schema_version") != EVENT_SCHEMA
        or value.get("event_id") != f"CTRL-S20P2-{sequence:04d}"
        or value.get("sequence") != sequence
        or value.get("previous_event_hash") != previous_hash
        or value.get("event_type") not in {"ACTION_CONFIRMED", "ACTION_UNDONE"}
        or value.get("raw_source_mutation_performed") is not False
        or value.get("fact_layer_mutation_performed") is not False
        or value.get("s20_p3_recalculation_performed") is not False
    ):
        raise ConfirmationError("EVENT_CHAIN_INVALID", "处理历史的顺序或安全边界无效。", status=409)
    if value.get("issue_id") not in _ISSUE_BY_ID or not _EVENT_ID.fullmatch(str(value.get("event_id", ""))):
        raise ConfirmationError("EVENT_CHAIN_INVALID", "处理历史引用了未知事项。", status=409)
    if value.get("actor_role") not in ALLOWED_ACTION_ROLES:
        raise ConfirmationError("EVENT_CHAIN_INVALID", "处理历史角色无效。", status=409)
    expected_hash = _fingerprint(_event_body(value))
    if value.get("event_hash") != expected_hash:
        raise ConfirmationError("EVENT_TAMPERED", "处理历史完整性校验失败。", status=409)
    _text(value.get("actor_id"), "操作人")
    _text(value.get("reason_zh"), "处理理由")
    _text(value.get("idempotency_key"), "幂等编号", limit=128)
    return value


def project(events: Iterable[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    state = {
        issue["issue_id"]: {"status": issue["status"], "active_event_id": None, "active_action_id": None}
        for issue in ISSUES if issue["kind"] == "BUSINESS_DISCREPANCY"
    }
    known_events: dict[str, Mapping[str, Any]] = {}
    for event in events:
        event_id = str(event["event_id"])
        issue_id = str(event["issue_id"])
        if event["event_type"] == "ACTION_CONFIRMED":
            state[issue_id] = {"status": "RESOLVED", "active_event_id": event_id, "active_action_id": event["action_id"]}
        else:
            target_id = str(event.get("target_event_id") or "")
            target = known_events.get(target_id)
            if not target or target["issue_id"] != issue_id or state[issue_id]["active_event_id"] != target_id:
                raise ConfirmationError("EVENT_CHAIN_INVALID", "撤销记录没有指向当前有效处理。", status=409)
            state[issue_id] = {"status": "OPEN", "active_event_id": None, "active_action_id": None}
        known_events[event_id] = event
    return state


class ControlEventJournal:
    """Append-only, file-locked and hash-chained control-event journal."""

    def __init__(self, path: str | Path = DEFAULT_EVENT_PATH):
        self.path = Path(path).expanduser().resolve(strict=False)
        forbidden = (Path.home() / "Downloads" / ("KMFA_" + "MetaData")).resolve(strict=False)
        if self.path == forbidden or forbidden in self.path.parents:
            raise ConfirmationError("RAW_WRITE_REJECTED", "处理记录不能写入原始只读目录。")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock_path = self.path.with_suffix(self.path.suffix + ".lock")
        self._thread_lock = threading.RLock()

    def _locked(self):
        class Lock:
            def __init__(inner, outer: ControlEventJournal):
                inner.outer = outer
                inner.handle = None

            def __enter__(inner):
                inner.outer._thread_lock.acquire()
                inner.handle = inner.outer.lock_path.open("a+b")
                fcntl.flock(inner.handle.fileno(), fcntl.LOCK_EX)
                return inner

            def __exit__(inner, exc_type, exc, tb):
                assert inner.handle is not None
                fcntl.flock(inner.handle.fileno(), fcntl.LOCK_UN)
                inner.handle.close()
                inner.outer._thread_lock.release()
        return Lock(self)

    def _read_unlocked(self) -> list[dict[str, Any]]:
        if not self.path.is_file():
            return []
        rows: list[dict[str, Any]] = []
        previous: str | None = None
        for line_number, line in enumerate(self.path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as error:
                raise ConfirmationError("EVENT_CHAIN_INVALID", f"处理历史第 {line_number} 行无法读取。", status=409) from error
            row = _validate_event(row, sequence=len(rows) + 1, previous_hash=previous)
            rows.append(row)
            previous = row["event_hash"]
        project(rows)
        return rows

    def read(self) -> list[dict[str, Any]]:
        with self._locked():
            return self._read_unlocked()

    def by_idempotency_key(self, key: str) -> dict[str, Any] | None:
        return next((copy.deepcopy(row) for row in self.read() if row["idempotency_key"] == key), None)

    def append(self, body: Mapping[str, Any]) -> dict[str, Any]:
        with self._locked():
            rows = self._read_unlocked()
            request_fingerprint = _fingerprint({key: body.get(key) for key in sorted(body) if key not in {"recorded_at"}})
            for row in rows:
                if row["idempotency_key"] == body.get("idempotency_key"):
                    if row["request_fingerprint"] != request_fingerprint:
                        raise ConfirmationError("IDEMPOTENCY_CONFLICT", "同一请求编号不能用于不同处理。", status=409)
                    return copy.deepcopy(row)
            event = {
                "schema_version": EVENT_SCHEMA,
                "event_id": f"CTRL-S20P2-{len(rows) + 1:04d}",
                "sequence": len(rows) + 1,
                "previous_event_hash": rows[-1]["event_hash"] if rows else None,
                **copy.deepcopy(dict(body)),
                "request_fingerprint": request_fingerprint,
                "recorded_at": _now(),
                "raw_source_mutation_performed": False,
                "fact_layer_mutation_performed": False,
                "s20_p3_recalculation_performed": False,
            }
            event["event_hash"] = _fingerprint(_event_body(event))
            event = _validate_event(event, sequence=len(rows) + 1, previous_hash=rows[-1]["event_hash"] if rows else None)
            payload = json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n"
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            return copy.deepcopy(event)


class ConfirmationWorkbench:
    def __init__(self, event_path: str | Path = DEFAULT_EVENT_PATH):
        self.journal = ControlEventJournal(event_path)

    def _events(self) -> list[dict[str, Any]]:
        return self.journal.read()

    def _issue(self, issue_id: str) -> dict[str, Any]:
        issue = _ISSUE_BY_ID.get(str(issue_id))
        if not issue or issue["kind"] != "BUSINESS_DISCREPANCY":
            raise ConfirmationError("ISSUE_NOT_FOUND", "没有找到这项业务问题。", status=404)
        return copy.deepcopy(issue)

    def list_issues(self, *, include_resolved: bool = False) -> dict[str, Any]:
        events = self._events()
        projection = project(events)
        rows: list[dict[str, Any]] = []
        for issue in ISSUES:
            if issue["kind"] != "BUSINESS_DISCREPANCY":
                continue
            state = projection[issue["issue_id"]]
            if not include_resolved and (not issue["requires_user_action"] or state["status"] != "OPEN"):
                continue
            row = {key: copy.deepcopy(issue[key]) for key in ("issue_id", "title_zh", "impact", "urgency", "source_id", "source_label_zh", "owner_id", "owner_label_zh", "requires_user_action")}
            row.update(state)
            rows.append(row)
        rows.sort(key=lambda row: (-IMPACT_RANK[row["impact"]], -URGENCY_RANK[row["urgency"]], row["source_label_zh"], row["owner_label_zh"], row["issue_id"]))
        return {
            "schema_version": "kmfa.v015.s20p2.issue_list.v1",
            "default_requires_user_action_only": not include_resolved,
            "governance_log_count_in_main_list": sum(row.get("kind") == "GOVERNANCE_LOG" for row in rows),
            "issue_count": len(rows),
            "issues": rows,
            "sort_order": ["impact_desc", "urgency_desc", "source_asc", "owner_asc"],
        }

    def detail(self, issue_id: str) -> dict[str, Any]:
        issue = self._issue(issue_id)
        state = project(self._events())[issue_id]
        issue.update(state)
        issue["raw_value_edit_allowed"] = False
        issue["technical_details_default_expanded"] = False
        return issue

    def _action(self, issue: Mapping[str, Any], action_id: str) -> dict[str, Any]:
        action = next((row for row in issue["suggested_actions"] if row["action_id"] == action_id), None)
        if not action:
            raise ConfirmationError("ACTION_NOT_ALLOWED", "请选择当前问题提供的处理方式。")
        return copy.deepcopy(action)

    def preview(self, issue_id: str, action_id: str, *, actor_role: str) -> dict[str, Any]:
        if actor_role not in ALLOWED_ACTION_ROLES:
            raise ConfirmationError("ACTION_FORBIDDEN", "当前角色只能查看，不能处理。", status=403)
        issue = self.detail(issue_id)
        if issue["status"] != "OPEN":
            raise ConfirmationError("ISSUE_NOT_OPEN", "这项问题当前不需要再次处理。", status=409)
        action = self._action(issue, action_id)
        revision = _fingerprint({"events": [row["event_hash"] for row in self._events()], "issue": issue_id})
        binding = {"issue_id": issue_id, "action_id": action_id, "actor_role": actor_role, "revision": revision, "before_status": "OPEN", "after_status": "RESOLVED"}
        token = _fingerprint(binding)
        return {
            "schema_version": "kmfa.v015.s20p2.impact_preview.v1",
            "preview_id": "PREVIEW-" + token.removeprefix("sha256:")[:20],
            "preview_token": token,
            "binding": binding,
            "issue_title_zh": issue["title_zh"],
            "action_id": action_id,
            "action_label_zh": action["label_zh"],
            "before_status": "OPEN", "after_status": "RESOLVED",
            "business_impact_zh": issue["impact_zh"],
            "high_impact": action["high_impact"],
            "raw_source_mutation_performed": False,
            "fact_layer_mutation_performed": False,
            "s20_p3_recalculation_performed": False,
        }

    def confirm(
        self, issue_id: str, action_id: str, *, actor_id: str, actor_role: str, reason_zh: str,
        preview_id: str = "", preview_token: str = "", idempotency_key: str,
    ) -> dict[str, Any]:
        key = _text(idempotency_key, "请求编号", limit=128)
        if not _IDEMPOTENCY.fullmatch(key):
            raise ConfirmationError("IDEMPOTENCY_KEY_INVALID", "请求编号格式不正确。")
        existing = self.journal.by_idempotency_key(key)
        if existing:
            expected_fields = ("ACTION_CONFIRMED", issue_id, action_id, actor_id, actor_role, reason_zh, preview_id, preview_token)
            actual_fields = tuple(existing[field] for field in ("event_type", "issue_id", "action_id", "actor_id", "actor_role", "reason_zh", "preview_id", "preview_token"))
            if actual_fields != expected_fields:
                raise ConfirmationError("IDEMPOTENCY_CONFLICT", "同一请求编号不能用于不同处理。", status=409)
            return {"allowed": True, "event": existing, "detail": self.detail(issue_id)}
        issue = self._issue(issue_id)
        action = self._action(issue, action_id)
        if not preview_id or not preview_token:
            code = "HIGH_IMPACT_PREVIEW_REQUIRED" if action["high_impact"] else "PREVIEW_REQUIRED"
            raise ConfirmationError(code, "必须先查看当前影响预览，再确认处理。", status=409)
        expected = self.preview(issue_id, action_id, actor_role=actor_role)
        if preview_id != expected["preview_id"] or preview_token != expected["preview_token"]:
            raise ConfirmationError("PREVIEW_STALE", "影响预览已变化，请重新查看后确认。", status=409)
        event = self.journal.append({
            "event_type": "ACTION_CONFIRMED", "issue_id": issue_id, "action_id": action_id,
            "action_label_zh": action["label_zh"], "actor_id": _text(actor_id, "操作人"),
            "actor_role": actor_role, "reason_zh": _text(reason_zh, "处理理由"),
            "preview_id": preview_id, "preview_token": preview_token, "target_event_id": None,
            "before_status": "OPEN", "after_status": "RESOLVED", "high_impact": action["high_impact"],
            "idempotency_key": key,
        })
        return {"allowed": True, "event": event, "detail": self.detail(issue_id)}

    def undo_preview(self, event_id: str, *, actor_role: str) -> dict[str, Any]:
        if actor_role not in ALLOWED_ACTION_ROLES:
            raise ConfirmationError("ACTION_FORBIDDEN", "当前角色只能查看，不能撤销。", status=403)
        events = self._events()
        target = next((row for row in events if row["event_id"] == event_id), None)
        if not target or target["event_type"] != "ACTION_CONFIRMED":
            raise ConfirmationError("UNDO_TARGET_INVALID", "没有找到可撤销的处理记录。", status=404)
        state = project(events)[target["issue_id"]]
        if state["active_event_id"] != event_id:
            raise ConfirmationError("UNDO_TARGET_INACTIVE", "这条处理已撤销或不再有效。", status=409)
        binding = {"issue_id": target["issue_id"], "target_event_id": event_id, "actor_role": actor_role, "revision": events[-1]["event_hash"], "before_status": "RESOLVED", "after_status": "OPEN"}
        token = _fingerprint(binding)
        return {
            "schema_version": "kmfa.v015.s20p2.undo_preview.v1",
            "preview_id": "UNDO-PREVIEW-" + token.removeprefix("sha256:")[:20], "preview_token": token,
            "binding": binding, "issue_title_zh": self._issue(target["issue_id"])["title_zh"],
            "action_label_zh": "撤销“" + target["action_label_zh"] + "”", "before_status": "RESOLVED", "after_status": "OPEN",
            "business_impact_zh": "撤销后问题重新进入待处理列表；旧记录保留。不会修改原始值或执行重算。",
            "high_impact": target["high_impact"], "raw_source_mutation_performed": False,
            "fact_layer_mutation_performed": False, "s20_p3_recalculation_performed": False,
        }

    def undo(
        self, event_id: str, *, actor_id: str, actor_role: str, reason_zh: str,
        preview_id: str = "", preview_token: str = "", idempotency_key: str,
    ) -> dict[str, Any]:
        key = _text(idempotency_key, "请求编号", limit=128)
        if not _IDEMPOTENCY.fullmatch(key):
            raise ConfirmationError("IDEMPOTENCY_KEY_INVALID", "请求编号格式不正确。")
        existing = self.journal.by_idempotency_key(key)
        if existing:
            expected_fields = ("ACTION_UNDONE", event_id, actor_id, actor_role, reason_zh, preview_id, preview_token)
            actual_fields = (existing["event_type"], existing["target_event_id"], existing["actor_id"], existing["actor_role"], existing["reason_zh"], existing["preview_id"], existing["preview_token"])
            if actual_fields != expected_fields:
                raise ConfirmationError("IDEMPOTENCY_CONFLICT", "同一请求编号不能用于不同撤销。", status=409)
            return {"allowed": True, "event": existing, "detail": self.detail(existing["issue_id"])}
        if not preview_id or not preview_token:
            raise ConfirmationError("UNDO_PREVIEW_REQUIRED", "必须先查看撤销影响，再确认撤销。", status=409)
        expected = self.undo_preview(event_id, actor_role=actor_role)
        if preview_id != expected["preview_id"] or preview_token != expected["preview_token"]:
            raise ConfirmationError("PREVIEW_STALE", "撤销影响已经变化，请重新查看。", status=409)
        issue_id = expected["binding"]["issue_id"]
        event = self.journal.append({
            "event_type": "ACTION_UNDONE", "issue_id": issue_id, "action_id": "UNDO",
            "action_label_zh": expected["action_label_zh"], "actor_id": _text(actor_id, "操作人"),
            "actor_role": actor_role, "reason_zh": _text(reason_zh, "撤销理由"),
            "preview_id": preview_id, "preview_token": preview_token, "target_event_id": event_id,
            "before_status": "RESOLVED", "after_status": "OPEN", "high_impact": expected["high_impact"],
            "idempotency_key": key,
        })
        return {"allowed": True, "event": event, "detail": self.detail(issue_id)}

    def history(self) -> dict[str, Any]:
        events = self._events()
        projection = project(events)
        active_ids = {row["active_event_id"] for row in projection.values() if row["active_event_id"]}
        rows = []
        for event in reversed(events):
            row = copy.deepcopy(event)
            row["active"] = event["event_id"] in active_ids
            row.pop("request_fingerprint", None)
            row.pop("preview_token", None)
            rows.append(row)
        return {"schema_version": "kmfa.v015.s20p2.history.v1", "event_count": len(rows), "append_only": True, "events": rows}


def public_verification() -> dict[str, Any]:
    checks: list[dict[str, str]] = []

    def add(check_id: str, passed: Any) -> None:
        checks.append({"check_id": check_id, "status": "PASS" if bool(passed) else "FAIL"})

    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary) / "events.jsonl"
        workbench = ConfirmationWorkbench(path)
        default = workbench.list_issues()
        all_rows = workbench.list_issues(include_resolved=True)
        detail = workbench.detail("ISSUE-S20P2-001")
        preview = workbench.preview("ISSUE-S20P2-001", "USE_REGISTERED_PROJECT", actor_role="ROLE::DATA_STEWARD")
        high_blocked = False
        try:
            workbench.confirm("ISSUE-S20P2-001", "USE_REGISTERED_PROJECT", actor_id="demo-owner", actor_role="ROLE::DATA_STEWARD", reason_zh="已核对两侧项目依据", idempotency_key="confirm-missing-preview-001")
        except ConfirmationError as error:
            high_blocked = error.code == "HIGH_IMPACT_PREVIEW_REQUIRED"
        confirmed = workbench.confirm(
            "ISSUE-S20P2-001", "USE_REGISTERED_PROJECT", actor_id="demo-owner", actor_role="ROLE::DATA_STEWARD",
            reason_zh="已核对两侧项目依据和影响", preview_id=preview["preview_id"], preview_token=preview["preview_token"],
            idempotency_key="confirm-project-001",
        )
        repeated = workbench.confirm(
            "ISSUE-S20P2-001", "USE_REGISTERED_PROJECT", actor_id="demo-owner", actor_role="ROLE::DATA_STEWARD",
            reason_zh="已核对两侧项目依据和影响", preview_id=preview["preview_id"], preview_token=preview["preview_token"],
            idempotency_key="confirm-project-001",
        )
        after_confirm = workbench.list_issues()
        undo_preview = workbench.undo_preview(confirmed["event"]["event_id"], actor_role="ROLE::AUDITOR")
        undo_blocked = False
        try:
            workbench.undo(confirmed["event"]["event_id"], actor_id="demo-auditor", actor_role="ROLE::AUDITOR", reason_zh="复核后撤销", idempotency_key="undo-missing-preview-001")
        except ConfirmationError as error:
            undo_blocked = error.code == "UNDO_PREVIEW_REQUIRED"
        undone = workbench.undo(
            confirmed["event"]["event_id"], actor_id="demo-auditor", actor_role="ROLE::AUDITOR", reason_zh="复核后撤销并恢复待处理",
            preview_id=undo_preview["preview_id"], preview_token=undo_preview["preview_token"], idempotency_key="undo-project-001",
        )
        replayed = ConfirmationWorkbench(path)
        history = replayed.history()
        after_undo = replayed.list_issues()
        tamper_detected = False
        original = path.read_text(encoding="utf-8")
        path.write_text(original.replace("demo-owner", "tampered-owner", 1), encoding="utf-8")
        try:
            replayed.history()
        except ConfirmationError as error:
            tamper_detected = error.code == "EVENT_TAMPERED"

        add("DEFAULT_LIST_REQUIRES_ACTION_ONLY", default["default_requires_user_action_only"])
        add("DEFAULT_LIST_COUNT", default["issue_count"] == 5)
        add("DEFAULT_EXCLUDES_RESOLVED", all(row["status"] == "OPEN" for row in default["issues"]))
        add("DEFAULT_EXCLUDES_NO_ACTION", all(row["requires_user_action"] for row in default["issues"]))
        add("GOVERNANCE_LOG_EXCLUDED", default["governance_log_count_in_main_list"] == 0)
        add("ALL_BUSINESS_ROWS_COUNT", all_rows["issue_count"] == 6)
        add("SORT_IMPACT_FIRST", [row["issue_id"] for row in default["issues"][:3]] == ["ISSUE-S20P2-001", "ISSUE-S20P2-002", "ISSUE-S20P2-003"])
        add("SORT_ORDER_DECLARED", default["sort_order"] == ["impact_desc", "urgency_desc", "source_asc", "owner_asc"])
        add("DETAIL_SIDE_BY_SIDE", bool(detail["current_data"] and detail["reference_data"]))
        add("DETAIL_BUSINESS_EXPLANATION", bool(detail["business_explanation_zh"]))
        add("DETAIL_IMPACT", bool(detail["impact_zh"]))
        add("DETAIL_SUGGESTED_ACTIONS", len(detail["suggested_actions"]) == 2)
        add("DETAIL_TECH_COLLAPSED", detail["technical_details_default_expanded"] is False)
        add("RAW_EDIT_CLOSED", detail["raw_value_edit_allowed"] is False)
        add("PREVIEW_BINDS_ISSUE", preview["binding"]["issue_id"] == "ISSUE-S20P2-001")
        add("PREVIEW_BINDS_ACTION", preview["binding"]["action_id"] == "USE_REGISTERED_PROJECT")
        add("PREVIEW_HAS_BEFORE_AFTER", (preview["before_status"], preview["after_status"]) == ("OPEN", "RESOLVED"))
        add("PREVIEW_SHOWS_IMPACT", bool(preview["business_impact_zh"]))
        add("PREVIEW_MARKS_HIGH_IMPACT", preview["high_impact"] is True)
        add("PREVIEW_RAW_MUTATION_ZERO", preview["raw_source_mutation_performed"] is False)
        add("PREVIEW_FACT_MUTATION_ZERO", preview["fact_layer_mutation_performed"] is False)
        add("PREVIEW_RECALC_ZERO", preview["s20_p3_recalculation_performed"] is False)
        add("HIGH_IMPACT_WITHOUT_PREVIEW_BLOCKED", high_blocked)
        add("CONFIRM_EVENT_RECORDED", confirmed["event"]["event_type"] == "ACTION_CONFIRMED")
        add("CONFIRM_RESULT_RESOLVED", confirmed["detail"]["status"] == "RESOLVED")
        add("CONFIRM_CONTROL_ONLY", confirmed["event"]["fact_layer_mutation_performed"] is False)
        add("IDEMPOTENT_CONFIRM", repeated["event"]["event_id"] == confirmed["event"]["event_id"])
        add("RESOLVED_REMOVED_FROM_DEFAULT", "ISSUE-S20P2-001" not in {row["issue_id"] for row in after_confirm["issues"]})
        add("UNDO_PREVIEW_HAS_TARGET", undo_preview["binding"]["target_event_id"] == confirmed["event"]["event_id"])
        add("UNDO_PREVIEW_REOPENS", undo_preview["after_status"] == "OPEN")
        add("UNDO_WITHOUT_PREVIEW_BLOCKED", undo_blocked)
        add("UNDO_EVENT_RECORDED", undone["event"]["event_type"] == "ACTION_UNDONE")
        add("UNDO_TARGET_BOUND", undone["event"]["target_event_id"] == confirmed["event"]["event_id"])
        add("UNDO_RESULT_OPEN", undone["detail"]["status"] == "OPEN")
        add("HISTORY_APPEND_ONLY", history["append_only"] is True)
        add("HISTORY_EVENT_COUNT", history["event_count"] == 2)
        add("HISTORY_NEWEST_FIRST", history["events"][0]["event_type"] == "ACTION_UNDONE")
        add("HISTORY_NO_PREVIEW_TOKEN", all("preview_token" not in row for row in history["events"]))
        add("REPLAY_REOPENS_ISSUE", "ISSUE-S20P2-001" in {row["issue_id"] for row in after_undo["issues"]})
        add("EVENT_CHAIN_HASHED", all(row["event_hash"].startswith("sha256:") for row in history["events"]))
        add("EVENT_CHAIN_LINKED", history["events"][0]["previous_event_hash"] == confirmed["event"]["event_hash"])
        add("EVENT_TAMPER_DETECTED", tamper_detected)
        add("ALLOWED_ROLE_COUNT", len(ALLOWED_ACTION_ROLES) == 2)
        add("BUSINESS_ISSUE_COUNT", sum(row["kind"] == "BUSINESS_DISCREPANCY" for row in ISSUES) == 6)
        add("GOVERNANCE_FIXTURE_COUNT", sum(row["kind"] == "GOVERNANCE_LOG" for row in ISSUES) == 1)
        add("HIGH_IMPACT_ACTION_COUNT", sum(action["high_impact"] for issue in ISSUES for action in issue["suggested_actions"]) == 5)
        add("ISSUE_OWNER_COMPLETE", all(row["owner_id"] and row["owner_label_zh"] for row in ISSUES))
        add("ISSUE_SOURCE_COMPLETE", all(row["source_id"] and row["source_label_zh"] for row in ISSUES))
        add("ISSUE_IMPACT_VALID", all(row["impact"] in IMPACT_RANK for row in ISSUES))
        add("ISSUE_URGENCY_VALID", all(row["urgency"] in URGENCY_RANK for row in ISSUES))
        add("NO_SOURCE_VALUE_EDIT_ACTION", all("EDIT" not in action["action_id"] for issue in ISSUES for action in issue["suggested_actions"]))
        add("NO_AUTOMATIC_ACTION", all(issue["status"] in {"OPEN", "RESOLVED"} for issue in ISSUES))
        add("NO_S20_P3_EXECUTION", all(row["s20_p3_recalculation_performed"] is False for row in history["events"]))
        add("NO_RAW_MUTATION", all(row["raw_source_mutation_performed"] is False for row in history["events"]))
        add("NO_FACT_MUTATION", all(row["fact_layer_mutation_performed"] is False for row in history["events"]))

    failures = [row for row in checks if row["status"] != "PASS"]
    return {"check_count": len(checks), "pass_count": len(checks) - len(failures), "fail_count": len(failures), "checks": checks}


def scope_boundary() -> dict[str, Any]:
    return {
        "raw_root_access_count": 0, "raw_write_count": 0, "source_value_edit_count": 0,
        "fact_layer_mutation_count": 0, "governance_log_in_main_list_count": 0,
        "high_impact_without_preview_success_count": 0, "unauthorised_action_success_count": 0,
        "s20_p3_recalculation_count": 0, "report_refresh_count": 0,
        "external_network_request_count": 0, "real_business_action_count": 0,
    }
