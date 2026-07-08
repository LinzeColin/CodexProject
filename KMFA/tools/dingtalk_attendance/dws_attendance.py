#!/usr/bin/env python3
"""DWS-backed live attendance collection for KMFA S19."""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Callable, Mapping

from KMFA.tools.dingtalk_attendance.dws_auth_guard import dws_command_safety_status, dws_subprocess_env
from KMFA.tools.dingtalk_attendance.notification_template import display_run_type
from KMFA.tools.dingtalk_attendance.report_renderer import render_hr_report, render_management_report


ROOT_DEPT_ID = 1
MAX_DEPTS_PER_CALL = 30
DEFAULT_DWS_TIMEOUT_SECONDS = 120
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


class DwsAttendanceError(RuntimeError):
    """Raised when the organization-level DWS attendance run cannot start safely."""


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
    proc = subprocess.run(
        command,
        text=True,
        capture_output=True,
        timeout=effective_timeout + 5,
        check=False,
        env=dws_subprocess_env(),
    )
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


def _should_retry(result: dict[str, Any]) -> bool:
    if _is_success(result):
        return False
    if _is_pat_auth_required(result):
        return False
    payload = result.get("payload", {})
    error = payload.get("error", {}) if isinstance(payload, dict) else {}
    retryable = bool(error.get("retryable")) if isinstance(error, dict) else False
    code = _server_error_code(result)
    reason = str(payload.get("reason") or "") if isinstance(payload, dict) else ""
    return (
        retryable
        or code in RETRYABLE_SERVER_CODES
        or code in RETRYABLE_DWS_ERROR_CODES
        or reason.lower() in RETRYABLE_DWS_ERROR_CODES
        or _contains_timeout(payload)
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
            raise DwsAttendanceError(f"department discovery failed for dept {dept_id}: {_server_error_code(result)}")
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
            raise DwsAttendanceError(f"member listing failed: {_server_error_code(result)}")
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
    rows: list[dict[str, Any]] = []

    for member in members:
        user_id = member["userId"]
        record = _run_with_retry(
            runner,
            ["attendance", "record", "get", "--user", user_id, "--date", work_date],
            timeout=60,
        )
        summary = _run_with_retry(
            runner,
            ["attendance", "summary", "--user", user_id, "--date", summary_datetime, "--stats-type", "month"],
            timeout=60,
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
        known_no_record = member["name"] in KNOWN_NO_RECORD_NAMES and len(record_list) == 0 and _is_success(record_final)
        record_anomaly = _is_success(record_final) and not known_no_record and (
            (len(record_list) == 0 and (record_payload_requires_attendance or summary_today_present))
            or (len(record_list) > 0 and not record_has_full_day)
        )
        rows.append(
            {
                "member": member,
                "record": record,
                "summary": summary,
                "derived": {
                    "record_success": _is_success(record_final),
                    "summary_success": _is_success(summary_final),
                    "record_count": len(record_list),
                    "record_requires_attendance": record_requires_attendance,
                    "record_has_full_day": record_has_full_day,
                    "record_anomaly": record_anomaly,
                    "summary_item_count": len(summary_items),
                    "summary_abnormal_count": _summary_abnormal_count(summary_payload),
                    "summary_today_present": summary_today_present,
                    "summary_today_issues": summary_today_issues,
                    "summary_today_issue_count": len(summary_today_issues),
                    "summary_today_anomaly": _is_success(summary_final) and bool(summary_today_issues) and not known_no_record,
                    "known_no_record": known_no_record,
                },
            }
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
    return {
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


def _dedupe_rows_by_user(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for row in rows:
        user_id = str(row.get("member", {}).get("userId") or row.get("member", {}).get("name") or "")
        if user_id and user_id not in seen:
            seen.add(user_id)
            result.append(row)
    return result


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
    attendance_anomaly_names = _visible_names(stats.get("attendance_anomaly_names", []))
    empty_record_names = _visible_names(stats.get("unexpected_empty_record_names", []))
    incomplete_record_names = _visible_names(stats.get("incomplete_record_names", []))
    abnormal_lines = [
        f"今日异常人员 / 无考勤人员：{_join_names(attendance_anomaly_names)}。",
        f"无考勤记录人员：{_join_names(empty_record_names)}。",
        f"打卡记录不完整人员：{_join_names(incomplete_record_names)}。",
    ]
    return {
        "title": f"开明考勤管理报告｜{collection['work_date']}｜{display_run_type(plan['run_type'])}",
        "一、总体情况": (
            f"本次考勤检查完成。覆盖 {stats['member_count']} 人，"
            f"应考勤 {stats.get('attendance_required_count', stats['member_count'])} 人，"
            f"当天有打卡记录 {stats['record_nonempty_count']} 人。"
        ),
        "二、今日异常人员": "".join(abnormal_lines),
        "三、建议动作": "如今日异常人员不为无，请按现场考勤复核流程处理；无异常时无需处理。",
        "四、系统运行状态": "本次结果已写入私有月度归档；公开仓库不保存员工考勤明文。",
    }


def _hr_context(plan: dict[str, Any], collection: dict[str, Any]) -> dict[str, str]:
    stats = collection["stats"]
    attendance_anomaly_names = _visible_names(stats.get("attendance_anomaly_names", []))
    empty_record_names = _visible_names(stats.get("unexpected_empty_record_names", []))
    incomplete_record_names = _visible_names(stats.get("incomplete_record_names", []))
    return {
        "title": f"开明考勤 HR 报告｜{collection['work_date']}｜{display_run_type(plan['run_type'])}",
        "一、异常明细": (
            f"今日异常人员 / 无考勤人员：{_join_names(attendance_anomaly_names)}。"
            f"无考勤记录人员：{_join_names(empty_record_names)}。"
            f"打卡记录不完整人员：{_join_names(incomplete_record_names)}。"
        ),
        "二、连续异常人员": "连续异常按自然月历史归档统计，人员名单以通知正文和私有台账为准。",
        "三、数据质量与系统运行状态": (
            f"覆盖 {stats['member_count']} 人；"
            f"应考勤 {stats.get('attendance_required_count', stats['member_count'])} 人；"
            f"当天有打卡记录 {stats['record_nonempty_count']} 人。"
        ),
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
    raise DwsAttendanceError(
        "DWS_PAT_SCOPE_AUTH_REQUIRED: "
        f"{command_text} requires PAT scopes [{scope_text}]. "
        "Browser launch is suppressed by DWS PAT browser policy; authorize scopes manually before live collection."
    )


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
