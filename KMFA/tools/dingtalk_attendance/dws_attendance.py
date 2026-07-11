#!/usr/bin/env python3
"""DWS-backed live attendance collection for KMFA S19."""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Mapping
from zoneinfo import ZoneInfo

from KMFA.tools.dingtalk_attendance.dws_auth_guard import dws_command_safety_status, dws_subprocess_env
from KMFA.tools.dingtalk_attendance.notification_template import display_run_type
from KMFA.tools.dingtalk_attendance.report_renderer import render_hr_report, render_management_report


ROOT_DEPT_ID = 1
MAX_DEPTS_PER_CALL = 30
DEFAULT_DWS_TIMEOUT_SECONDS = 120
OFFICIAL_REPORT_USER_BATCH_SIZE = 5
OFFICIAL_REPORT_REQUIRED_COLUMNS = (
    "考勤结果",
    "应出勤天数",
    "出勤天数",
    "休息天数",
    "迟到次数",
    "早退次数",
    "上班缺卡次数",
    "下班缺卡次数",
    "旷工天数",
)
OFFICIAL_REPORT_ANOMALY_COLUMNS = (
    "迟到次数",
    "早退次数",
    "上班缺卡次数",
    "下班缺卡次数",
    "旷工天数",
)
OFFICIAL_STATUS_ANOMALY_TOKENS = (
    "缺卡",
    "上班缺卡",
    "下班缺卡",
    "未打卡",
    "上班未打卡",
    "下班未打卡",
    "旷工",
    "迟到",
    "早退",
    "late",
    "early",
    "absenteeism",
    "notsigned",
)
OFFICIAL_STATUS_REST_TOKENS = ("休息", "rest")
OFFICIAL_STATUS_NON_ANOMALY_TOKENS = (
    "正常",
    "外勤",
    "上班外勤",
    "下班外勤",
    "请假",
    "出差",
    "调休",
    "补休",
    "公出",
    "年假",
    "病假",
    "事假",
    "婚假",
    "产假",
    "陪产假",
    "丧假",
    "哺乳假",
    "工伤假",
    "育儿假",
    "放假",
    "加班",
    "出勤",
    "normal",
    "field",
    "outside",
    "leave",
    "business trip",
    "vacation",
)
KNOWN_NO_RECORD_NAMES = frozenset({"张霖泽", "林全意"})
USER_VISIBLE_HIDDEN_NAMES = frozenset()
SUMMARY_TODAY_ANOMALY_TOKENS = frozenset(
    {
        "lack",
        "absent",
        "late",
        "early",
        "缺卡",
        "未打卡",
        "旷工",
        "迟到",
        "早退",
    }
)
RETRYABLE_SERVER_CODES = frozenset({"PAT_AUTH_CALL_FAILED", "TOKEN_VERIFIED_FAILED", "ERROR"})
RETRYABLE_DWS_ERROR_CODES = frozenset({"6", "ERROR", "request_timeout", "timed_out", "timeout"})
SUMMARY_BACKED_RECORD_DETAIL_UNAVAILABLE_CODES = frozenset({"AGENT_CODE_NOT_EXISTS"})
KNOWN_NO_RECORD_SUMMARY_NOT_APPLICABLE_CODES = frozenset({"AGENT_CODE_NOT_EXISTS"})
RECORD_BACKED_SUMMARY_DETAIL_UNAVAILABLE_CODES = frozenset({"AGENT_CODE_NOT_EXISTS"})
PAT_AUTH_REQUIRED_CODES = frozenset(
    {
        "PAT_SCOPE_AUTH_REQUIRED",
        "PAT_AUTH_REQUIRED",
        "PAT_LOW_RISK_NO_PERMISSION",
        "PAT_MEDIUM_RISK_NO_PERMISSION",
        "PAT_HIGH_RISK_NO_PERMISSION",
    }
)

DwsRunner = Callable[[list[str]], dict[str, Any]]


def attendance_run_sort_key(run_id: str) -> str:
    """Return the shared chronological ordering key for standard or suffixed run IDs."""
    value = str(run_id or "")
    match = re.search(r"(\d{8})_(\d{6})(?:\D|$)", value)
    return f"{match.group(1)}{match.group(2)}" if match else value


class DwsAttendanceError(RuntimeError):
    """Raised when the organization-level DWS attendance run cannot start safely."""


class OfficialAttendanceParityError(DwsAttendanceError):
    """Raised when official DingTalk report evidence cannot support exact parity."""

    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")


def run_dws_json(args: list[str], *, timeout: int = 30, verbose: bool = False) -> dict[str, Any]:
    safety = dws_command_safety_status()
    if safety["status"] != "READY":
        raise DwsAttendanceError(str(safety["failure_reason"]))
    dws_bin = os.environ.get("DWS_BIN", "dws")
    command = [dws_bin, *args]
    if verbose:
        command.append("--verbose")
    effective_timeout = max(int(os.environ.get("KMFA_S19_DWS_TIMEOUT_SECONDS", str(timeout))), timeout)
    command.extend(["--timeout", str(effective_timeout), "--format", "json"])
    subprocess_env = dws_subprocess_env()
    subprocess_env["TZ"] = "Asia/Shanghai"
    try:
        proc = subprocess.run(
            command,
            text=True,
            capture_output=True,
            timeout=effective_timeout + 5,
            check=False,
            env=subprocess_env,
        )
    except subprocess.TimeoutExpired:
        return {
            "returncode": 124,
            "payload": {
                "success": False,
                "code": "request_timeout",
                "reason": "dws subprocess timeout",
                "error": {"retryable": True},
            },
        }
    payload_text = proc.stdout.strip() or proc.stderr.strip() or "{}"
    payload = _parse_json_payload(payload_text)
    return {"returncode": proc.returncode, "payload": payload}


def _parse_json_payload(payload_text: str) -> dict[str, Any]:
    start = payload_text.find("{")
    if start == -1:
        return {"raw": payload_text[:2000]}
    try:
        return json.loads(payload_text[start:])
    except json.JSONDecodeError as exc:
        tail = payload_text[start:]
        decoder = json.JSONDecoder()
        try:
            payload, _ = decoder.raw_decode(tail)
            return payload
        except json.JSONDecodeError:
            return {"parse_error": str(exc), "raw": payload_text[:2000]}


def _call_runner(
    runner: Callable[..., dict[str, Any]],
    args: list[str],
    *,
    timeout: int = 30,
    verbose: bool = False,
) -> dict[str, Any]:
    return runner(args, timeout=timeout, verbose=verbose)


def _is_success(result: dict[str, Any]) -> bool:
    payload = result.get("payload", {})
    return result.get("returncode") == 0 and isinstance(payload, dict) and payload.get("success") is True


def _server_error_code(result: dict[str, Any]) -> str:
    payload = result.get("payload", {})
    if not isinstance(payload, dict):
        return ""
    error = payload.get("error", {})
    if isinstance(error, dict):
        return str(error.get("server_error_code") or error.get("code") or "")
    return ""


def _payload_code(result: dict[str, Any]) -> str:
    payload = result.get("payload", {})
    if not isinstance(payload, dict):
        return ""
    code = payload.get("code")
    if code:
        return str(code)
    return _server_error_code(result)


def _should_retry(result: dict[str, Any]) -> bool:
    if _is_success(result):
        return False
    if _is_pat_auth_required(result):
        return False
    payload = result.get("payload", {})
    error = payload.get("error", {}) if isinstance(payload, dict) else {}
    retryable = bool(error.get("retryable")) if isinstance(error, dict) else False
    code = _payload_code(result)
    reason = str(payload.get("reason") or "") if isinstance(payload, dict) else ""
    message = str(payload.get("message") or payload.get("errmsg") or "") if isinstance(payload, dict) else ""
    has_failure_detail = bool(code or reason or message)
    return (
        retryable
        or code in RETRYABLE_SERVER_CODES
        or code in RETRYABLE_DWS_ERROR_CODES
        or reason.lower() in RETRYABLE_DWS_ERROR_CODES
        or message.lower() in RETRYABLE_DWS_ERROR_CODES
        or _contains_timeout(payload)
        or not has_failure_detail
    )


def _run_with_retry(
    runner: Callable[..., dict[str, Any]],
    args: list[str],
    *,
    timeout: int = 30,
    max_attempts: int = 3,
) -> dict[str, Any]:
    first = _call_runner(runner, args, timeout=timeout, verbose=False)
    _raise_if_pat_auth_required(first, args=args)
    attempts = [first]
    final = first
    if max_attempts < 1:
        return {"final": final, "attempts": attempts}
    attempt = 1
    while _should_retry(final) and attempt < max_attempts:
        attempt += 1
        final = _call_runner(runner, args, timeout=timeout, verbose=True)
        _raise_if_pat_auth_required(final, args=args)
        attempts.append(final)
    return {"final": final, "attempts": attempts}


def discover_department_ids(
    *,
    runner: Callable[..., dict[str, Any]],
    root_dept_id: int = ROOT_DEPT_ID,
) -> list[int]:
    seen: set[int] = set()
    pending = [root_dept_id]
    ordered: list[int] = []
    while pending:
        dept_id = pending.pop(0)
        if dept_id in seen:
            continue
        seen.add(dept_id)
        ordered.append(dept_id)
        result = _run_with_retry(
            runner,
            ["contact", "dept", "list-children", "--dept", str(dept_id)],
            timeout=DEFAULT_DWS_TIMEOUT_SECONDS,
        )["final"]
        _raise_if_pat_auth_required(result, args=["contact", "dept", "list-children"])
        if not _is_success(result):
            raise DwsAttendanceError(f"department discovery failed for dept {dept_id}: {_failure_label(result)}")
        payload = result["payload"]
        for child in payload.get("result", []):
            child_id = child.get("deptId")
            if child_id is not None:
                pending.append(int(child_id))
    return ordered


def list_org_members(
    *,
    runner: Callable[..., dict[str, Any]],
    dept_ids: list[int],
) -> list[dict[str, str]]:
    members: dict[str, dict[str, str]] = {}
    for index in range(0, len(dept_ids), MAX_DEPTS_PER_CALL):
        batch = dept_ids[index : index + MAX_DEPTS_PER_CALL]
        result = _run_with_retry(
            runner,
            ["contact", "dept", "list-members", "--depts", ",".join(str(value) for value in batch)],
            timeout=DEFAULT_DWS_TIMEOUT_SECONDS,
        )["final"]
        _raise_if_pat_auth_required(result, args=["contact", "dept", "list-members"])
        if not _is_success(result):
            raise DwsAttendanceError(f"member listing failed: {_failure_label(result)}")
        for row in result["payload"].get("deptUserList", []):
            user_info = row.get("userInfo", {})
            user_id = str(user_info.get("userId") or "")
            name = str(user_info.get("name") or "")
            if user_id and name:
                members[user_id] = {"name": name, "userId": user_id}
    return sorted(members.values(), key=lambda item: item["name"])


def collect_org_attendance(
    *,
    work_date: str,
    summary_datetime: str,
    runner: Callable[..., dict[str, Any]] = run_dws_json,
) -> dict[str, Any]:
    dept_ids = discover_department_ids(runner=runner)
    members = list_org_members(runner=runner, dept_ids=dept_ids)
    rows = _collect_member_attendance_rows(
        members=members,
        work_date=work_date,
        summary_datetime=summary_datetime,
        runner=runner,
    )
    stats = build_collection_stats(rows)
    return {
        "dws_live": True,
        "uses_mock_data": False,
        "work_date": work_date,
        "summary_datetime": summary_datetime,
        "dept_ids": dept_ids,
        "member_count": len(members),
        "results": rows,
        "stats": stats,
    }


def collect_official_org_attendance(
    *,
    work_date: str,
    summary_datetime: str,
    runner: Callable[..., dict[str, Any]] = run_dws_json,
) -> dict[str, Any]:
    """Collect attendance with DingTalk's admin report as the sole business truth."""

    try:
        parsed_work_date = datetime.strptime(work_date, "%Y-%m-%d")
    except (TypeError, ValueError) as exc:
        raise OfficialAttendanceParityError(
            "OFFICIAL_REPORT_INVALID_WORK_DATE",
            f"expected YYYY-MM-DD, received {work_date!r}",
        ) from exc
    if parsed_work_date.strftime("%Y-%m-%d") != work_date:
        raise OfficialAttendanceParityError(
            "OFFICIAL_REPORT_INVALID_WORK_DATE",
            f"expected canonical YYYY-MM-DD, received {work_date!r}",
        )

    dept_ids = discover_department_ids(runner=runner)
    org_members = list_org_members(runner=runner, dept_ids=dept_ids)
    group_scope = _collect_attendance_group_scope(runner=runner)
    scoped_user_ids = set(group_scope["member_user_ids"])
    org_by_user_id = {member["userId"]: member for member in org_members}
    missing_from_org = scoped_user_ids - set(org_by_user_id)
    if missing_from_org:
        raise OfficialAttendanceParityError(
            "OFFICIAL_ATTENDANCE_GROUP_MEMBER_NOT_IN_ORG",
            f"{len(missing_from_org)} attendance-group member(s) lack an organization name mapping",
        )
    members = [member for member in org_members if member["userId"] in scoped_user_ids]
    if not members:
        raise OfficialAttendanceParityError(
            "OFFICIAL_ATTENDANCE_GROUP_SCOPE_EMPTY",
            "no organization member belongs to an attendance group",
        )

    report_columns = _resolve_official_report_columns(runner=runner)
    official_by_user, report_query_evidence = _query_official_report(
        runner=runner,
        members=members,
        work_date=work_date,
        column_ids=report_columns["column_ids"],
    )
    rows = _collect_member_attendance_rows(
        members=members,
        work_date=work_date,
        summary_datetime=summary_datetime,
        runner=runner,
        tolerate_diagnostic_errors=True,
    )
    for row in rows:
        user_id = row["member"]["userId"]
        row["derived"].update(official_by_user[user_id])

    stats = build_collection_stats(rows)
    stats.update(
        {
            "attendance_group_count": len(group_scope["group_ids"]),
            "attendance_group_member_count": len(members),
        }
    )
    official_report_evidence = {
        "private": True,
        "source": "dws attendance report query-data",
        "work_date": work_date,
        "query_start": f"{work_date} 00:00:00",
        "query_end": f"{work_date} 23:59:59",
        "attendance_group_scope": group_scope,
        "report_columns": report_columns,
        "query_batches": report_query_evidence,
    }
    return {
        "dws_live": True,
        "uses_mock_data": False,
        "work_date": work_date,
        "summary_datetime": summary_datetime,
        "dept_ids": dept_ids,
        "member_count": len(members),
        "results": rows,
        "stats": stats,
        "official_report_evidence": official_report_evidence,
    }


def _collect_attendance_group_scope(*, runner: Callable[..., dict[str, Any]]) -> dict[str, Any]:
    limit = 200
    page = 1
    groups_by_id: dict[str, dict[str, Any]] = {}
    search_evidence: list[dict[str, Any]] = []
    expected_total: int | None = None
    while True:
        args = ["attendance", "group", "search", "--page", str(page), "--limit", str(limit)]
        final = _run_with_retry(
            runner,
            args,
            timeout=DEFAULT_DWS_TIMEOUT_SECONDS,
        )["final"]
        result = _official_success_result(final, code="OFFICIAL_ATTENDANCE_GROUP_SEARCH_FAILED", args=args)
        items, page_total = _extract_group_search_items(result)
        search_evidence.append({"page": page, "response": final.get("payload", {})})
        if page_total is not None:
            if expected_total is not None and page_total != expected_total:
                raise OfficialAttendanceParityError(
                    "OFFICIAL_ATTENDANCE_GROUP_STRUCTURE_UNKNOWN",
                    "attendance group totalCount changed during pagination",
                )
            expected_total = page_total
        previous_count = len(groups_by_id)
        for item in items:
            group_id = _first_nonempty_value(item, ("id", "groupId", "group_id"))
            if group_id is None:
                raise OfficialAttendanceParityError(
                    "OFFICIAL_ATTENDANCE_GROUP_STRUCTURE_UNKNOWN",
                    "attendance group row is missing its id",
                )
            group_id_text = str(group_id)
            if group_id_text in groups_by_id and groups_by_id[group_id_text] != dict(item):
                raise OfficialAttendanceParityError(
                    "OFFICIAL_ATTENDANCE_GROUP_STRUCTURE_UNKNOWN",
                    "duplicate attendance group id has conflicting data",
                )
            groups_by_id[group_id_text] = dict(item)
        if expected_total is not None and len(groups_by_id) >= expected_total:
            break
        if len(items) < limit:
            break
        if len(groups_by_id) == previous_count:
            raise OfficialAttendanceParityError(
                "OFFICIAL_ATTENDANCE_GROUP_STRUCTURE_UNKNOWN",
                "attendance group pagination made no progress",
            )
        page += 1

    if expected_total is not None and len(groups_by_id) != expected_total:
        raise OfficialAttendanceParityError(
            "OFFICIAL_ATTENDANCE_GROUP_COVERAGE_MISMATCH",
            f"expected {expected_total} groups, received {len(groups_by_id)}",
        )
    if not groups_by_id:
        raise OfficialAttendanceParityError(
            "OFFICIAL_ATTENDANCE_GROUP_SCOPE_EMPTY",
            "attendance group search returned no groups",
        )

    member_user_ids: set[str] = set()
    member_evidence: list[dict[str, Any]] = []
    for group_id in groups_by_id:
        args = [
            "attendance",
            "group",
            "filtered-get",
            "--group-id",
            group_id,
            "--member",
        ]
        final = _run_with_retry(
            runner,
            args,
            timeout=DEFAULT_DWS_TIMEOUT_SECONDS,
        )["final"]
        result = _official_success_result(final, code="OFFICIAL_ATTENDANCE_GROUP_MEMBERS_FAILED", args=args)
        group_members = _extract_group_member_user_ids(result)
        member_user_ids.update(group_members)
        member_evidence.append(
            {
                "group_id": group_id,
                "member_count": len(group_members),
                "response": final.get("payload", {}),
            }
        )
    if not member_user_ids:
        raise OfficialAttendanceParityError(
            "OFFICIAL_ATTENDANCE_GROUP_SCOPE_EMPTY",
            "attendance groups contain no memberUsers",
        )
    return {
        "group_ids": list(groups_by_id),
        "member_user_ids": sorted(member_user_ids),
        "search_evidence": search_evidence,
        "member_evidence": member_evidence,
    }


def _extract_group_search_items(result: Any) -> tuple[list[Mapping[str, Any]], int | None]:
    total: int | None = None
    if isinstance(result, list):
        raw_items = result
    elif isinstance(result, Mapping):
        raw_total = _first_nonempty_value(result, ("totalCount", "total", "count"))
        if raw_total is not None:
            try:
                total = int(raw_total)
            except (TypeError, ValueError) as exc:
                raise OfficialAttendanceParityError(
                    "OFFICIAL_ATTENDANCE_GROUP_STRUCTURE_UNKNOWN",
                    "attendance group totalCount is not an integer",
                ) from exc
        raw_items = _first_list_value(result, ("items", "records", "data", "list", "groups"))
        if raw_items is None:
            raise OfficialAttendanceParityError(
                "OFFICIAL_ATTENDANCE_GROUP_STRUCTURE_UNKNOWN",
                f"unrecognized attendance group search keys: {sorted(str(key) for key in result)}",
            )
    else:
        raise OfficialAttendanceParityError(
            "OFFICIAL_ATTENDANCE_GROUP_STRUCTURE_UNKNOWN",
            f"unexpected attendance group search type: {type(result).__name__}",
        )
    if not all(isinstance(item, Mapping) for item in raw_items):
        raise OfficialAttendanceParityError(
            "OFFICIAL_ATTENDANCE_GROUP_STRUCTURE_UNKNOWN",
            "attendance group search contains a non-object row",
        )
    return list(raw_items), total


def _extract_group_member_user_ids(result: Any) -> list[str]:
    if not isinstance(result, Mapping):
        raise OfficialAttendanceParityError(
            "OFFICIAL_ATTENDANCE_GROUP_STRUCTURE_UNKNOWN",
            f"unexpected filtered-get result type: {type(result).__name__}",
        )
    member_lists: list[list[Any]] = []

    def walk(value: Any) -> None:
        if not isinstance(value, Mapping):
            return
        for key, child in value.items():
            if str(key) == "memberUsers":
                if not isinstance(child, list):
                    raise OfficialAttendanceParityError(
                        "OFFICIAL_ATTENDANCE_GROUP_STRUCTURE_UNKNOWN",
                        "filtered-get memberUsers is not a list",
                    )
                member_lists.append(child)
            elif isinstance(child, Mapping):
                walk(child)

    walk(result)
    if len(member_lists) != 1:
        raise OfficialAttendanceParityError(
            "OFFICIAL_ATTENDANCE_GROUP_STRUCTURE_UNKNOWN",
            f"filtered-get must expose exactly one memberUsers list, found {len(member_lists)}",
        )
    user_ids: list[str] = []
    for member in member_lists[0]:
        if isinstance(member, Mapping):
            user_id = _first_nonempty_value(member, ("userId", "userid", "user_id", "id"))
        elif isinstance(member, (str, int)) and not isinstance(member, bool):
            user_id = member
        else:
            user_id = None
        if user_id is None or not str(user_id).strip():
            raise OfficialAttendanceParityError(
                "OFFICIAL_ATTENDANCE_GROUP_STRUCTURE_UNKNOWN",
                "filtered-get contains a member without userId",
            )
        user_ids.append(str(user_id).strip())
    return list(dict.fromkeys(user_ids))


def _resolve_official_report_columns(*, runner: Callable[..., dict[str, Any]]) -> dict[str, Any]:
    args = ["attendance", "report", "columns"]
    final = _run_with_retry(
        runner,
        args,
        timeout=DEFAULT_DWS_TIMEOUT_SECONDS,
    )["final"]
    result = _official_success_result(final, code="OFFICIAL_REPORT_COLUMNS_FAILED", args=args)
    columns = _extract_report_record_array(result, purpose="columns")
    resolved: dict[str, str] = {}
    for column in columns:
        column_id = _first_nonempty_value(column, ("id", "columnId", "code", "key", "termId"))
        column_name = _first_nonempty_value(column, ("name", "columnName", "title", "label"))
        if column_id is None or column_name is None:
            raise OfficialAttendanceParityError(
                "OFFICIAL_REPORT_COLUMNS_STRUCTURE_UNKNOWN",
                "report columns contains a row without id or name",
            )
        exact_name = str(column_name).strip()
        if exact_name not in OFFICIAL_REPORT_REQUIRED_COLUMNS:
            continue
        if exact_name in resolved:
            raise OfficialAttendanceParityError(
                "OFFICIAL_REPORT_REQUIRED_COLUMN_AMBIGUOUS",
                f"required column {exact_name!r} appears more than once",
            )
        resolved[exact_name] = str(column_id).strip()
    missing = [name for name in OFFICIAL_REPORT_REQUIRED_COLUMNS if name not in resolved]
    if missing:
        raise OfficialAttendanceParityError(
            "OFFICIAL_REPORT_REQUIRED_COLUMN_MISSING",
            f"missing required column(s): {', '.join(missing)}",
        )
    if len(set(resolved.values())) != len(resolved):
        raise OfficialAttendanceParityError(
            "OFFICIAL_REPORT_REQUIRED_COLUMN_AMBIGUOUS",
            "multiple required column names resolve to the same id",
        )
    ordered = {name: resolved[name] for name in OFFICIAL_REPORT_REQUIRED_COLUMNS}
    return {
        "column_ids": ordered,
        "response": final.get("payload", {}),
    }


def _query_official_report(
    *,
    runner: Callable[..., dict[str, Any]],
    members: list[dict[str, str]],
    work_date: str,
    column_ids: Mapping[str, str],
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    expected_user_ids = [member["userId"] for member in members]
    expected_user_id_set = set(expected_user_ids)
    parsed_by_user: dict[str, dict[str, Any]] = {}
    evidence: list[dict[str, Any]] = []
    ordered_column_ids = [column_ids[name] for name in OFFICIAL_REPORT_REQUIRED_COLUMNS]
    for offset in range(0, len(expected_user_ids), OFFICIAL_REPORT_USER_BATCH_SIZE):
        user_batch = expected_user_ids[offset : offset + OFFICIAL_REPORT_USER_BATCH_SIZE]
        user_batch_set = set(user_batch)
        args = [
            "attendance",
            "report",
            "query-data",
            "--users",
            ",".join(user_batch),
            "--columns",
            ",".join(ordered_column_ids),
            "--start",
            f"{work_date} 00:00:00",
            "--end",
            f"{work_date} 23:59:59",
        ]
        final = _run_with_retry(
            runner,
            args,
            timeout=DEFAULT_DWS_TIMEOUT_SECONDS,
        )["final"]
        result = _official_success_result(final, code="OFFICIAL_REPORT_QUERY_FAILED", args=args)
        records = _extract_report_record_array(result, purpose="query-data")
        evidence.append(
            {
                "requested_user_ids": user_batch,
                "response": final.get("payload", {}),
            }
        )
        returned_batch_user_ids: set[str] = set()
        for record in records:
            user_id_value = _first_nonempty_value(record, ("userId", "userid", "user_id", "targetUserId"))
            if user_id_value is None:
                raise OfficialAttendanceParityError(
                    "OFFICIAL_REPORT_STRUCTURE_UNKNOWN",
                    "query-data record is missing userId",
                )
            user_id = str(user_id_value).strip()
            if user_id not in expected_user_id_set:
                raise OfficialAttendanceParityError(
                    "OFFICIAL_REPORT_EXTRA_USER",
                    "query-data returned a user outside the attendance-group scope",
                )
            if user_id not in user_batch_set:
                raise OfficialAttendanceParityError(
                    "OFFICIAL_REPORT_BATCH_SCOPE_MISMATCH",
                    "query-data returned a scoped user outside the current request batch",
                )
            record_date = _official_record_work_date(record)
            if record_date != work_date:
                raise OfficialAttendanceParityError(
                    "OFFICIAL_REPORT_DATE_MISMATCH",
                    f"expected {work_date}, received {record_date or 'missing date'}",
                )
            if user_id in parsed_by_user:
                raise OfficialAttendanceParityError(
                    "OFFICIAL_REPORT_COVERAGE_MISMATCH",
                    "query-data returned duplicate rows for a scoped user/date",
                )
            parsed_by_user[user_id] = _parse_official_report_record(
                record=record,
                column_ids=column_ids,
                work_date=work_date,
            )
            returned_batch_user_ids.add(user_id)
        if returned_batch_user_ids != user_batch_set:
            raise OfficialAttendanceParityError(
                "OFFICIAL_REPORT_COVERAGE_MISMATCH",
                f"batch expected {len(user_batch_set)} users, received {len(returned_batch_user_ids)}",
            )

    missing_users = expected_user_id_set - set(parsed_by_user)
    if missing_users or len(parsed_by_user) != len(expected_user_ids):
        raise OfficialAttendanceParityError(
            "OFFICIAL_REPORT_COVERAGE_MISMATCH",
            f"expected {len(expected_user_ids)} users, received {len(parsed_by_user)}",
        )
    return parsed_by_user, evidence


def _parse_official_report_record(
    *,
    record: Mapping[str, Any],
    column_ids: Mapping[str, str],
    work_date: str,
) -> dict[str, Any]:
    values = record.get("values")
    if not isinstance(values, list):
        raise OfficialAttendanceParityError(
            "OFFICIAL_REPORT_STRUCTURE_UNKNOWN",
            "query-data record values must be a list",
        )
    values_by_id: dict[str, Any] = {}
    for entry in values:
        if not isinstance(entry, Mapping):
            raise OfficialAttendanceParityError(
                "OFFICIAL_REPORT_STRUCTURE_UNKNOWN",
                "query-data values contains a non-object entry",
            )
        term_id = _first_nonempty_value(entry, ("termId", "columnId", "id"))
        if term_id is None:
            raise OfficialAttendanceParityError(
                "OFFICIAL_REPORT_STRUCTURE_UNKNOWN",
                "query-data value is missing termId",
            )
        term_id_text = str(term_id).strip()
        if term_id_text in values_by_id:
            raise OfficialAttendanceParityError(
                "OFFICIAL_REPORT_STRUCTURE_UNKNOWN",
                "query-data contains a duplicate termId",
            )
        values_by_id[term_id_text] = entry.get("value", entry.get("data"))
    missing_value_names = [name for name, column_id in column_ids.items() if column_id not in values_by_id]
    if missing_value_names:
        raise OfficialAttendanceParityError(
            "OFFICIAL_REPORT_REQUIRED_VALUE_MISSING",
            f"query-data row lacks required value(s): {', '.join(missing_value_names)}",
        )

    status_value = values_by_id[column_ids["考勤结果"]]
    if not isinstance(status_value, str) or not status_value.strip():
        raise OfficialAttendanceParityError(
            "OFFICIAL_REPORT_STATUS_MISSING",
            "query-data row has no non-empty 考勤结果",
        )
    status_text = status_value.strip()
    status_category = _classify_official_status(status_text)
    metrics = {
        name: _parse_official_nonnegative_number(values_by_id[column_ids[name]], column_name=name)
        for name in OFFICIAL_REPORT_REQUIRED_COLUMNS
        if name != "考勤结果"
    }
    metrics_anomaly = any(metrics[name] > 0 for name in OFFICIAL_REPORT_ANOMALY_COLUMNS)
    if status_category == "rest" and metrics_anomaly:
        raise OfficialAttendanceParityError(
            "OFFICIAL_REPORT_ROW_INCONSISTENT",
            "休息 status conflicts with non-zero official anomaly columns",
        )
    official_anomaly = status_category == "anomaly" or metrics_anomaly
    official_issues: list[str] = []
    if status_category == "anomaly":
        official_issues.append(f"考勤结果={status_text}")
    for column_name in OFFICIAL_REPORT_ANOMALY_COLUMNS:
        metric_value = metrics[column_name]
        if metric_value > 0:
            display_value = str(int(metric_value)) if metric_value.is_integer() else str(metric_value)
            official_issues.append(f"{column_name}={display_value}")
    attendance_required = status_category != "rest" and metrics["应出勤天数"] > 0
    official_effective_day = status_category != "rest" and metrics["出勤天数"] > 0
    return {
        "official_report_covered": True,
        "official_work_date": work_date,
        "official_status_text": status_text,
        "official_status_category": status_category,
        "official_report_anomaly": official_anomaly,
        "official_report_issues": official_issues,
        "official_attendance_required": attendance_required,
        "official_effective_day": official_effective_day,
        "official_report_metrics": metrics,
    }


def _classify_official_status(status_text: str) -> str:
    components = [
        _normalize_official_status_component(component)
        for component in re.split(r"[+＋,，、;/；|&\n]+", status_text)
        if component.strip()
    ]
    anomaly = {_normalize_official_status_component(token) for token in OFFICIAL_STATUS_ANOMALY_TOKENS}
    rest = {_normalize_official_status_component(token) for token in OFFICIAL_STATUS_REST_TOKENS}
    non_anomaly = {
        _normalize_official_status_component(token) for token in OFFICIAL_STATUS_NON_ANOMALY_TOKENS
    }
    known = anomaly | rest | non_anomaly
    if not components or any(component not in known for component in components):
        raise OfficialAttendanceParityError(
            "OFFICIAL_REPORT_STATUS_UNKNOWN",
            f"unsupported official attendance status: {status_text!r}",
        )
    if any(component in anomaly for component in components):
        return "anomaly"
    if any(component in rest for component in components):
        return "rest"
    if all(component in non_anomaly for component in components):
        return "non_anomaly"
    raise OfficialAttendanceParityError(
        "OFFICIAL_REPORT_STATUS_UNKNOWN",
        f"unsupported official attendance status: {status_text!r}",
    )


def _normalize_official_status_component(value: str) -> str:
    return re.sub(r"[\s_\-]", "", value).lower()


def _parse_official_nonnegative_number(value: Any, *, column_name: str) -> float:
    if isinstance(value, bool) or value is None:
        number: float | None = None
    elif isinstance(value, (int, float)):
        number = float(value)
    elif isinstance(value, str):
        match = re.fullmatch(r"\s*([+-]?(?:\d+(?:\.\d+)?|\.\d+))\s*(?:天|次)?\s*", value)
        number = float(match.group(1)) if match else None
    else:
        number = None
    if number is None or number < 0:
        raise OfficialAttendanceParityError(
            "OFFICIAL_REPORT_NUMERIC_VALUE_INVALID",
            f"column {column_name!r} must contain a non-negative number",
        )
    return number


def _official_record_work_date(record: Mapping[str, Any]) -> str | None:
    raw = _first_nonempty_value(
        record,
        ("workDate", "work_date", "date", "statDate", "attendanceDate"),
    )
    if raw is None:
        return None
    if isinstance(raw, bool):
        return None
    if isinstance(raw, (int, float)):
        timestamp = float(raw)
        if timestamp >= 1_000_000_000_000:
            timestamp /= 1000
        try:
            return datetime.fromtimestamp(timestamp, tz=ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d")
        except (OSError, OverflowError, ValueError):
            return None
    text = str(raw).strip()
    if re.fullmatch(r"\d{10,13}", text):
        return _official_record_work_date(int(text))
    if len(text) >= 10:
        candidate = text[:10]
        try:
            return datetime.strptime(candidate, "%Y-%m-%d").strftime("%Y-%m-%d")
        except ValueError:
            return None
    return None


def _extract_report_record_array(result: Any, *, purpose: str) -> list[Mapping[str, Any]]:
    current = result
    for _ in range(3):
        if isinstance(current, list):
            if not all(isinstance(item, Mapping) for item in current):
                break
            return list(current)
        if isinstance(current, Mapping):
            next_value = _first_list_value(current, ("records", "data", "items", "list", "columns"))
            if next_value is not None:
                if not all(isinstance(item, Mapping) for item in next_value):
                    break
                return list(next_value)
            nested = current.get("result")
            if isinstance(nested, (Mapping, list)):
                current = nested
                continue
        break
    raise OfficialAttendanceParityError(
        "OFFICIAL_REPORT_STRUCTURE_UNKNOWN",
        f"unrecognized {purpose} result structure",
    )


def _official_success_result(
    result: dict[str, Any],
    *,
    code: str,
    args: list[str],
) -> Any:
    _raise_if_pat_auth_required(result, args=args)
    if not _is_success(result):
        raise OfficialAttendanceParityError(code, _failure_label(result))
    payload = result.get("payload", {})
    if not isinstance(payload, Mapping) or "result" not in payload:
        raise OfficialAttendanceParityError(
            "OFFICIAL_REPORT_STRUCTURE_UNKNOWN",
            "successful DWS response is missing result",
        )
    return payload["result"]


def _first_nonempty_value(mapping: Mapping[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        value = mapping.get(key)
        if value is not None and value != "":
            return value
    return None


def _first_list_value(mapping: Mapping[str, Any], keys: tuple[str, ...]) -> list[Any] | None:
    for key in keys:
        value = mapping.get(key)
        if isinstance(value, list):
            return value
    return None


def _collect_member_attendance_rows(
    *,
    members: list[dict[str, str]],
    work_date: str,
    summary_datetime: str,
    runner: Callable[..., dict[str, Any]],
    tolerate_diagnostic_errors: bool = False,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    def diagnostic_call(args: list[str]) -> dict[str, Any]:
        try:
            return _run_with_retry(runner, args, timeout=60)
        except DwsAttendanceError as exc:
            if not tolerate_diagnostic_errors:
                raise
            final = {
                "returncode": 1,
                "payload": {
                    "success": False,
                    "code": "DIAGNOSTIC_UNAVAILABLE",
                    "reason": str(exc),
                },
            }
            return {"final": final, "attempts": [final]}

    for member in members:
        user_id = member["userId"]
        record = diagnostic_call(
            ["attendance", "record", "get", "--user", user_id, "--date", work_date],
        )
        summary = diagnostic_call(
            ["attendance", "summary", "--user", user_id, "--date", summary_datetime, "--stats-type", "month"],
        )
        record_final = record["final"]
        summary_final = summary["final"]
        record_payload = record_final.get("payload", {})
        summary_payload = summary_final.get("payload", {})
        record_list = _record_list(record_payload)
        summary_items = _summary_items(summary_payload)
        summary_today_present = _summary_has_work_date(summary_payload, work_date)
        summary_today_issues = _summary_today_issues(summary_payload, work_date)
        record_payload_requires_attendance = _record_requires_attendance(record_payload)
        record_requires_attendance = bool(record_list) or record_payload_requires_attendance or summary_today_present
        record_has_full_day = _record_list_has_morning_and_evening(record_list)
        record_raw_success = _is_success(record_final)
        summary_raw_success = _is_success(summary_final)
        record_detail_unavailable = _is_summary_backed_record_detail_unavailable(
            record_final=record_final,
            summary_final=summary_final,
        )
        record_success = record_raw_success or record_detail_unavailable
        known_no_record = member["name"] in KNOWN_NO_RECORD_NAMES and len(record_list) == 0 and record_raw_success
        summary_not_applicable = _is_known_no_record_summary_not_applicable(
            summary_final=summary_final,
            known_no_record=known_no_record,
        )
        summary_detail_unavailable = _is_record_backed_summary_detail_unavailable(
            summary_final=summary_final,
            record_success=record_success,
            record_has_full_day=record_has_full_day,
        )
        summary_success = summary_raw_success or summary_not_applicable or summary_detail_unavailable
        record_anomaly = record_success and not record_detail_unavailable and not known_no_record and (
            (len(record_list) == 0 and (record_payload_requires_attendance or summary_today_present))
            or (len(record_list) > 0 and not record_has_full_day)
        )
        rows.append(
            {
                "member": member,
                "record": record,
                "summary": summary,
                "derived": {
                    "record_success": record_success,
                    "record_raw_success": record_raw_success,
                    "record_detail_unavailable": record_detail_unavailable,
                    "record_detail_unavailable_code": _payload_code(record_final) if record_detail_unavailable else "",
                    "summary_success": summary_success,
                    "summary_raw_success": summary_raw_success,
                    "summary_not_applicable": summary_not_applicable,
                    "summary_not_applicable_code": _payload_code(summary_final) if summary_not_applicable else "",
                    "summary_detail_unavailable": summary_detail_unavailable,
                    "summary_detail_unavailable_code": _payload_code(summary_final) if summary_detail_unavailable else "",
                    "record_count": len(record_list),
                    "record_requires_attendance": record_requires_attendance,
                    "record_has_full_day": record_has_full_day,
                    "record_anomaly": record_anomaly,
                    "summary_item_count": len(summary_items),
                    "summary_abnormal_count": _summary_abnormal_count(summary_payload),
                    "summary_today_present": summary_today_present,
                    "summary_today_issues": summary_today_issues,
                    "summary_today_issue_count": len(summary_today_issues),
                    "summary_today_anomaly": summary_success and bool(summary_today_issues) and not known_no_record,
                    "known_no_record": known_no_record,
                },
            }
        )
    return rows


def _record_list(payload: dict[str, Any]) -> list[Any]:
    result = payload.get("result", {}) if isinstance(payload, dict) else {}
    record_list = result.get("recordList", []) if isinstance(result, dict) else []
    return record_list if isinstance(record_list, list) else []


def _record_requires_attendance(payload: dict[str, Any]) -> bool:
    result = payload.get("result", {}) if isinstance(payload, dict) else {}
    if not isinstance(result, dict):
        return True
    if result.get("isRest") is True:
        return False
    if result.get("isHasSchedule") is False:
        return False
    return True


def _record_list_has_morning_and_evening(record_list: list[Any]) -> bool:
    has_morning = False
    has_evening = False
    for item in record_list:
        if not isinstance(item, Mapping):
            continue
        values = " ".join(
            str(item.get(key) or "")
            for key in ("checkTypeDesc", "checkType", "timeResult", "sourceType")
        )
        has_morning = has_morning or "上班" in values or "OnDuty" in values
        has_evening = has_evening or "下班" in values or "OffDuty" in values
    return has_morning and has_evening


def _summary_items(payload: dict[str, Any]) -> list[Any]:
    result = payload.get("result", {}) if isinstance(payload, dict) else {}
    items = result.get("items", []) if isinstance(result, dict) else []
    return items if isinstance(items, list) else []


def _summary_abnormal_count(payload: dict[str, Any]) -> int | None:
    result = payload.get("result", {}) if isinstance(payload, dict) else {}
    value = result.get("abnormalCount") if isinstance(result, dict) else None
    return value if isinstance(value, int) else None


def _summary_has_work_date(payload: dict[str, Any], work_date: str) -> bool:
    return any(_summary_child_matches_work_date(child, work_date) for child in _summary_children(payload))


def _summary_today_issues(payload: dict[str, Any], work_date: str) -> list[str]:
    issues: list[str] = []
    result = payload.get("result", {}) if isinstance(payload, dict) else {}
    items = result.get("items", []) if isinstance(result, dict) else []
    if not isinstance(items, list):
        return issues
    for item in items:
        if not isinstance(item, Mapping) or not _is_summary_today_anomaly_item(item):
            continue
        item_name = str(item.get("name") or item.get("id") or "异常").strip()
        children = item.get("children", [])
        if not isinstance(children, list):
            continue
        for child in children:
            if not isinstance(child, Mapping) or not _summary_child_matches_work_date(child, work_date):
                continue
            child_name = str(child.get("name") or "").strip()
            issues.append(f"{item_name}（{child_name}）" if child_name else item_name)
    return _dedupe_strings(issues)


def _summary_children(payload: dict[str, Any]) -> list[Mapping[str, Any]]:
    result = payload.get("result", {}) if isinstance(payload, dict) else {}
    items = result.get("items", []) if isinstance(result, dict) else []
    children: list[Mapping[str, Any]] = []
    if not isinstance(items, list):
        return children
    for item in items:
        if not isinstance(item, Mapping):
            continue
        item_children = item.get("children", [])
        if isinstance(item_children, list):
            children.extend(child for child in item_children if isinstance(child, Mapping))
    return children


def _summary_child_matches_work_date(child: Mapping[str, Any], work_date: str) -> bool:
    if work_date in str(child.get("name") or ""):
        return True
    extension = child.get("extension", {})
    return isinstance(extension, Mapping) and work_date in str(extension.get("date") or "")


def _is_summary_today_anomaly_item(item: Mapping[str, Any]) -> bool:
    text = f"{item.get('id') or ''} {item.get('name') or ''}".lower()
    return any(token.lower() in text for token in SUMMARY_TODAY_ANOMALY_TOKENS)


def build_collection_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    record_success = [row for row in rows if row["derived"]["record_success"]]
    summary_success = [row for row in rows if row["derived"]["summary_success"]]
    record_empty_success = [row for row in record_success if row["derived"]["record_count"] == 0]
    known_no_record = [row for row in record_empty_success if row["derived"]["known_no_record"]]
    summary_today_scope_available = any(row["derived"].get("summary_today_present") for row in summary_success)
    attendance_required = [
        row
        for row in record_success
        if not row["derived"].get("known_no_record")
        and (
            row["derived"].get("summary_today_present")
            if summary_today_scope_available
            else row["derived"].get("record_requires_attendance")
        )
    ]
    unexpected_empty = [row for row in record_empty_success if row["derived"].get("record_anomaly")]
    incomplete_records = [
        row
        for row in record_success
        if row["derived"].get("record_anomaly") and row["derived"]["record_count"] > 0
    ]
    summary_today_anomalies = [row for row in summary_success if row["derived"].get("summary_today_anomaly")]
    attendance_anomalies = _dedupe_rows_by_user([*unexpected_empty, *incomplete_records, *summary_today_anomalies])
    stats = {
        "member_count": len(rows),
        "record_success_count": len(record_success),
        "summary_success_count": len(summary_success),
        "record_nonempty_count": sum(1 for row in record_success if row["derived"]["record_count"] > 0),
        "record_empty_success_count": len(record_empty_success),
        "known_no_record_count": len(known_no_record),
        "attendance_required_count": len(attendance_required),
        "summary_today_present_count": sum(1 for row in summary_success if row["derived"].get("summary_today_present")),
        "unexpected_empty_record_count": len(unexpected_empty),
        "record_incomplete_success_count": len(incomplete_records),
        "summary_today_anomaly_count": len(summary_today_anomalies),
        "attendance_anomaly_count": len(attendance_anomalies),
        "record_failure_count": len(rows) - len(record_success),
        "summary_failure_count": len(rows) - len(summary_success),
        "command_failure_count": (len(rows) - len(record_success)) + (len(rows) - len(summary_success)),
        "record_detail_unavailable_count": sum(1 for row in rows if row["derived"].get("record_detail_unavailable")),
        "record_detail_unavailable_names": [
            row["member"]["name"] for row in rows if row["derived"].get("record_detail_unavailable")
        ],
        "summary_not_applicable_count": sum(1 for row in rows if row["derived"].get("summary_not_applicable")),
        "summary_not_applicable_names": [
            row["member"]["name"] for row in rows if row["derived"].get("summary_not_applicable")
        ],
        "summary_detail_unavailable_count": sum(
            1 for row in rows if row["derived"].get("summary_detail_unavailable")
        ),
        "summary_detail_unavailable_names": [
            row["member"]["name"] for row in rows if row["derived"].get("summary_detail_unavailable")
        ],
        "known_no_record_names": [row["member"]["name"] for row in known_no_record],
        "attendance_required_names": [row["member"]["name"] for row in attendance_required],
        "unexpected_empty_record_names": [row["member"]["name"] for row in unexpected_empty],
        "incomplete_record_names": [row["member"]["name"] for row in incomplete_records],
        "summary_today_anomaly_names": [row["member"]["name"] for row in summary_today_anomalies],
        "summary_today_anomaly_issues": {
            row["member"]["name"]: row["derived"].get("summary_today_issues", []) for row in summary_today_anomalies
        },
        "attendance_anomaly_names": [row["member"]["name"] for row in attendance_anomalies],
    }
    official_rows = [row for row in rows if row["derived"].get("official_report_covered")]
    if official_rows:
        if len(official_rows) != len(rows):
            raise OfficialAttendanceParityError(
                "OFFICIAL_REPORT_COVERAGE_MISMATCH",
                f"expected {len(rows)} official rows, received {len(official_rows)}",
            )
        official_required = [
            row for row in official_rows if row["derived"].get("official_attendance_required") is True
        ]
        official_anomalies = [
            row for row in official_rows if row["derived"].get("official_report_anomaly") is True
        ]
        official_effective_days = [
            row for row in official_rows if row["derived"].get("official_effective_day") is True
        ]
        official_anomaly_names = [row["member"]["name"] for row in official_anomalies]
        stats.update(
            {
                "official_report_parity_status": "PASS",
                "official_report_failure_count": 0,
                "official_report_expected_count": len(rows),
                "official_report_coverage_count": len(official_rows),
                "official_report_anomaly_count": len(official_anomalies),
                "official_report_anomaly_names": official_anomaly_names,
                "official_effective_day_count": len(official_effective_days),
                "official_effective_day_names": [row["member"]["name"] for row in official_effective_days],
                "attendance_required_count": len(official_required),
                "attendance_required_names": [row["member"]["name"] for row in official_required],
                "attendance_anomaly_count": len(official_anomalies),
                "attendance_anomaly_names": official_anomaly_names,
            }
        )
    return stats


def _dedupe_rows_by_user(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for row in rows:
        user_id = str(row.get("member", {}).get("userId") or row.get("member", {}).get("name") or "")
        if user_id and user_id not in seen:
            seen.add(user_id)
            result.append(row)
    return result


def _is_summary_backed_record_detail_unavailable(
    *,
    record_final: dict[str, Any],
    summary_final: dict[str, Any],
) -> bool:
    if _is_success(record_final) or not _is_success(summary_final):
        return False
    return _payload_code(record_final) in SUMMARY_BACKED_RECORD_DETAIL_UNAVAILABLE_CODES


def _is_known_no_record_summary_not_applicable(
    *,
    summary_final: dict[str, Any],
    known_no_record: bool,
) -> bool:
    if not known_no_record or _is_success(summary_final):
        return False
    return _payload_code(summary_final) in KNOWN_NO_RECORD_SUMMARY_NOT_APPLICABLE_CODES


def _is_record_backed_summary_detail_unavailable(
    *,
    summary_final: dict[str, Any],
    record_success: bool,
    record_has_full_day: bool,
) -> bool:
    if not record_success or not record_has_full_day or _is_success(summary_final):
        return False
    return _payload_code(summary_final) in RECORD_BACKED_SUMMARY_DETAIL_UNAVAILABLE_CODES


def _failure_label(result: dict[str, Any]) -> str:
    payload = result.get("payload", {})
    parts: list[str] = []
    code = _payload_code(result)
    if code:
        parts.append(f"code={code}")
    if isinstance(payload, dict):
        for key in ("reason", "message", "errmsg"):
            value = payload.get(key)
            if value:
                parts.append(f"{key}={value}")
    return "; ".join(parts) or f"returncode={result.get('returncode')}; unknown_failure"


def _dedupe_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def write_private_outputs(
    *,
    plan: dict[str, Any],
    collection: dict[str, Any],
    cleanup_status: dict[str, Any],
) -> dict[str, Any]:
    paths = plan["archive_paths"]
    month_dir = Path(paths["month_dir"])
    month_dir.mkdir(parents=True, exist_ok=True)

    raw_path = Path(paths["raw_jsonl_gz"])
    with gzip.open(raw_path, "wt", encoding="utf-8") as handle:
        handle.write(json.dumps({"type": "metadata", "run_plan": plan, "stats": collection["stats"]}, ensure_ascii=False) + "\n")
        official_report_evidence = collection.get("official_report_evidence")
        if isinstance(official_report_evidence, Mapping):
            handle.write(
                json.dumps(
                    {"type": "official_report_evidence", **official_report_evidence},
                    ensure_ascii=False,
                )
                + "\n"
            )
        for row in collection["results"]:
            handle.write(json.dumps({"type": "employee_attendance", **row}, ensure_ascii=False) + "\n")

    management_report = render_management_report(_management_context(plan, collection))
    hr_report = render_hr_report(_hr_context(plan, collection))
    Path(paths["management_report"]).write_text(management_report, encoding="utf-8")
    Path(paths["hr_report"]).write_text(hr_report, encoding="utf-8")

    raw_hash = hashlib.sha256(raw_path.read_bytes()).hexdigest()
    manifest = {
        "run_id": plan["run_id"],
        "stage_id": plan["stage_id"],
        "run_type": plan["run_type"],
        "work_date": collection["work_date"],
        "backend": "dws",
        "raw_jsonl_gz": str(raw_path),
        "raw_jsonl_gz_sha256": raw_hash,
        "management_report": paths["management_report"],
        "hr_report": paths["hr_report"],
        "dispatch_receipt": paths["dispatch_receipt"],
        "cleanup_audit": paths["cleanup_audit"],
        "stats": collection["stats"],
        "repo_safety": plan["public_repo_safety"],
    }
    Path(paths["archive_manifest"]).write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    Path(paths["cleanup_audit"]).write_text(json.dumps(cleanup_status, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "status": "WRITTEN",
        "month_dir": paths["month_dir"],
        "raw_jsonl_gz": str(raw_path),
        "raw_jsonl_gz_sha256": raw_hash,
        "management_report": paths["management_report"],
        "hr_report": paths["hr_report"],
        "dispatch_receipt": paths["dispatch_receipt"],
        "archive_manifest": paths["archive_manifest"],
        "cleanup_audit": paths["cleanup_audit"],
    }


def _management_context(plan: dict[str, Any], collection: dict[str, Any]) -> dict[str, str]:
    stats = collection["stats"]
    official_parity = stats.get("official_report_parity_status") == "PASS"
    attendance_anomaly_names = _visible_names(stats.get("attendance_anomaly_names", []))
    empty_record_names = [] if official_parity else _visible_names(stats.get("unexpected_empty_record_names", []))
    incomplete_record_names = [] if official_parity else _visible_names(stats.get("incomplete_record_names", []))
    abnormal_lines = [f"今日异常人员 / 无考勤人员：{_join_names(attendance_anomaly_names)}。"]
    if not official_parity:
        abnormal_lines.extend(
            [
                f"无考勤记录人员：{_join_names(empty_record_names)}。",
                f"打卡记录不完整人员：{_join_names(incomplete_record_names)}。",
            ]
        )
    overall = (
        f"本次官方考勤检查完成。官方报表覆盖 {stats['official_report_coverage_count']} 人，"
        f"应考勤 {stats['attendance_required_count']} 人，"
        f"有效出勤 {stats.get('official_effective_day_count', 0)} 人。"
        if official_parity
        else (
            f"本次考勤检查完成。覆盖 {stats['member_count']} 人，"
            f"应考勤 {stats.get('attendance_required_count', stats['member_count'])} 人，"
            f"当天有打卡记录 {stats['record_nonempty_count']} 人。"
        )
    )
    return {
        "title": f"开明考勤管理报告｜{collection['work_date']}｜{display_run_type(plan['run_type'])}",
        "一、总体情况": overall,
        "二、今日异常人员": "".join(abnormal_lines),
        "三、建议动作": "如今日异常人员不为无，请按现场考勤复核流程处理；无异常时无需处理。",
        "四、系统运行状态": "本次结果已写入私有月度归档；公开仓库不保存员工考勤明文。",
    }


def _hr_context(plan: dict[str, Any], collection: dict[str, Any]) -> dict[str, str]:
    stats = collection["stats"]
    official_parity = stats.get("official_report_parity_status") == "PASS"
    attendance_anomaly_names = _visible_names(stats.get("attendance_anomaly_names", []))
    empty_record_names = [] if official_parity else _visible_names(stats.get("unexpected_empty_record_names", []))
    incomplete_record_names = [] if official_parity else _visible_names(stats.get("incomplete_record_names", []))
    anomaly_detail = f"今日异常人员 / 无考勤人员：{_join_names(attendance_anomaly_names)}。"
    if not official_parity:
        anomaly_detail += (
            f"无考勤记录人员：{_join_names(empty_record_names)}。"
            f"打卡记录不完整人员：{_join_names(incomplete_record_names)}。"
        )
    system_status = (
        f"官方报表覆盖 {stats['official_report_coverage_count']} 人；"
        f"应考勤 {stats['attendance_required_count']} 人；"
        f"有效出勤 {stats.get('official_effective_day_count', 0)} 人。"
        if official_parity
        else (
            f"覆盖 {stats['member_count']} 人；"
            f"应考勤 {stats.get('attendance_required_count', stats['member_count'])} 人；"
            f"当天有打卡记录 {stats['record_nonempty_count']} 人。"
        )
    )
    return {
        "title": f"开明考勤 HR 报告｜{collection['work_date']}｜{display_run_type(plan['run_type'])}",
        "一、异常明细": anomaly_detail,
        "二、连续异常人员": "连续异常按自然月历史归档统计，人员名单以通知正文和私有台账为准。",
        "三、数据质量与系统运行状态": system_status,
    }


def _join_names(names: list[str]) -> str:
    return "无" if not names else "、".join(names)


def _visible_names(names: list[str]) -> list[str]:
    return [name for name in names if name not in USER_VISIBLE_HIDDEN_NAMES]


def _raise_if_pat_auth_required(result: dict[str, Any], *, args: list[str]) -> None:
    if not _is_pat_auth_required(result):
        return
    scopes = _pat_required_scopes(result.get("payload", {}))
    scope_text = ", ".join(scopes) if scopes else "unknown scope"
    command_text = " ".join(args[:4])
    detail = (
        f"{command_text} requires PAT scopes [{scope_text}]. "
        "Browser launch is suppressed by DWS PAT browser policy; authorize scopes manually before live collection."
    )
    if args[:2] == ["attendance", "report"] or args[:2] == ["attendance", "group"]:
        raise OfficialAttendanceParityError("OFFICIAL_REPORT_PERMISSION_REQUIRED", detail)
    raise DwsAttendanceError(f"DWS_PAT_SCOPE_AUTH_REQUIRED: {detail}")


def _is_pat_auth_required(result: dict[str, Any]) -> bool:
    payload = result.get("payload", {})
    return _contains_pat_auth_code(payload) or _find_key_value(payload, "openBrowser") is True or _contains_open_browser_marker(payload)


def _contains_pat_auth_code(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key).lower() in {"code", "errorcode", "error_code", "server_error_code"} and str(child) in PAT_AUTH_REQUIRED_CODES:
                return True
            if _contains_pat_auth_code(child):
                return True
    if isinstance(value, list):
        return any(_contains_pat_auth_code(child) for child in value)
    if isinstance(value, str):
        return any(code in value for code in PAT_AUTH_REQUIRED_CODES)
    return False


def _find_key_value(value: Any, key_name: str) -> Any:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) == key_name:
                return child
            found = _find_key_value(child, key_name)
            if found is not None:
                return found
    if isinstance(value, list):
        for child in value:
            found = _find_key_value(child, key_name)
            if found is not None:
                return found
    return None


def _contains_open_browser_marker(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(_contains_open_browser_marker(child) for child in value.values())
    if isinstance(value, list):
        return any(_contains_open_browser_marker(child) for child in value)
    if isinstance(value, str):
        return '"openBrowser":true' in value.replace(" ", "") or '"open_browser":true' in value.replace(" ", "")
    return False


def _contains_timeout(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(_contains_timeout(child) for child in value.values())
    if isinstance(value, list):
        return any(_contains_timeout(child) for child in value)
    if isinstance(value, str):
        lowered = value.lower()
        return "timeout" in lowered or "timed out" in lowered
    return False


def _pat_required_scopes(value: Any) -> list[str]:
    scopes: list[str] = []

    def walk(node: Any, inside_required_scopes: bool = False) -> None:
        if isinstance(node, Mapping):
            next_inside = inside_required_scopes
            for key, child in node.items():
                if str(key) == "requiredScopes":
                    walk(child, True)
                elif inside_required_scopes and str(key) == "scope" and child:
                    scopes.append(str(child))
                else:
                    walk(child, next_inside)
        elif isinstance(node, list):
            for child in node:
                walk(child, inside_required_scopes)
        elif isinstance(node, str):
            scopes.extend(re.findall(r'"scope"\s*:\s*"([^"]+)"', node))

    walk(value)
    return sorted(set(scopes))
