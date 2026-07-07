#!/usr/bin/env python3
"""DWS-backed live attendance collection for KMFA S19."""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Callable

from KMFA.tools.dingtalk_attendance.report_renderer import render_hr_report, render_management_report


ROOT_DEPT_ID = 1
MAX_DEPTS_PER_CALL = 30
KNOWN_NO_RECORD_NAMES = frozenset({"张霖泽", "林全意"})
RETRYABLE_SERVER_CODES = frozenset({"PAT_AUTH_CALL_FAILED", "TOKEN_VERIFIED_FAILED", "ERROR"})

DwsRunner = Callable[[list[str]], dict[str, Any]]


class DwsAttendanceError(RuntimeError):
    """Raised when the organization-level DWS attendance run cannot start safely."""


def run_dws_json(args: list[str], *, timeout: int = 30, verbose: bool = False) -> dict[str, Any]:
    dws_bin = os.environ.get("DWS_BIN", "dws")
    command = [dws_bin, *args]
    if verbose:
        command.append("--verbose")
    command.extend(["--format", "json"])
    proc = subprocess.run(
        command,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
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
        return str(error.get("server_error_code") or "")
    return ""


def _should_retry(result: dict[str, Any]) -> bool:
    if _is_success(result):
        return False
    payload = result.get("payload", {})
    error = payload.get("error", {}) if isinstance(payload, dict) else {}
    retryable = bool(error.get("retryable")) if isinstance(error, dict) else False
    return retryable or _server_error_code(result) in RETRYABLE_SERVER_CODES


def _run_with_retry(
    runner: Callable[..., dict[str, Any]],
    args: list[str],
    *,
    timeout: int = 30,
) -> dict[str, Any]:
    first = _call_runner(runner, args, timeout=timeout, verbose=False)
    attempts = [first]
    final = first
    if _should_retry(first):
        final = _call_runner(runner, args, timeout=timeout, verbose=True)
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
        result = _call_runner(
            runner,
            ["contact", "dept", "list-children", "--dept", str(dept_id)],
            timeout=30,
        )
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
        result = _call_runner(
            runner,
            ["contact", "dept", "list-members", "--depts", ",".join(str(value) for value in batch)],
            timeout=45,
        )
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
        rows.append(
            {
                "member": member,
                "record": record,
                "summary": summary,
                "derived": {
                    "record_success": _is_success(record_final),
                    "summary_success": _is_success(summary_final),
                    "record_count": len(record_list),
                    "summary_item_count": len(summary_items),
                    "summary_abnormal_count": _summary_abnormal_count(summary_payload),
                    "known_no_record": member["name"] in KNOWN_NO_RECORD_NAMES and len(record_list) == 0 and _is_success(record_final),
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


def _summary_items(payload: dict[str, Any]) -> list[Any]:
    result = payload.get("result", {}) if isinstance(payload, dict) else {}
    items = result.get("items", []) if isinstance(result, dict) else []
    return items if isinstance(items, list) else []


def _summary_abnormal_count(payload: dict[str, Any]) -> int | None:
    result = payload.get("result", {}) if isinstance(payload, dict) else {}
    value = result.get("abnormalCount") if isinstance(result, dict) else None
    return value if isinstance(value, int) else None


def build_collection_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    record_success = [row for row in rows if row["derived"]["record_success"]]
    summary_success = [row for row in rows if row["derived"]["summary_success"]]
    record_empty_success = [row for row in record_success if row["derived"]["record_count"] == 0]
    known_no_record = [row for row in record_empty_success if row["derived"]["known_no_record"]]
    unexpected_empty = [row for row in record_empty_success if not row["derived"]["known_no_record"]]
    return {
        "member_count": len(rows),
        "record_success_count": len(record_success),
        "summary_success_count": len(summary_success),
        "record_nonempty_count": sum(1 for row in record_success if row["derived"]["record_count"] > 0),
        "record_empty_success_count": len(record_empty_success),
        "known_no_record_count": len(known_no_record),
        "unexpected_empty_record_count": len(unexpected_empty),
        "record_failure_count": len(rows) - len(record_success),
        "summary_failure_count": len(rows) - len(summary_success),
        "command_failure_count": (len(rows) - len(record_success)) + (len(rows) - len(summary_success)),
        "known_no_record_names": [row["member"]["name"] for row in known_no_record],
        "unexpected_empty_record_names": [row["member"]["name"] for row in unexpected_empty],
    }


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

    dispatch_receipt = {
        "run_id": plan["run_id"],
        "notification_status": "NOT_SENT_DWS_VALIDATION_MODE",
        "management_report": paths["management_report"],
        "hr_report": paths["hr_report"],
    }
    Path(paths["dispatch_receipt"]).write_text(json.dumps(dispatch_receipt, ensure_ascii=False, indent=2), encoding="utf-8")

    raw_hash = hashlib.sha256(raw_path.read_bytes()).hexdigest()
    manifest = {
        "run_id": plan["run_id"],
        "stage_id": plan["stage_id"],
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
    status = "完成" if stats["command_failure_count"] == 0 else "部分完成"
    return {
        "title": f"开明考勤管理报告｜{collection['work_date']}｜{plan['run_type']}",
        "一、总体情况": (
            f"本次 DWS 考勤接口验证{status}。覆盖 {stats['member_count']} 人，"
            f"record 成功 {stats['record_success_count']} 人，summary 成功 {stats['summary_success_count']} 人，"
            f"当天有打卡记录 {stats['record_nonempty_count']} 人。"
        ),
        "二、今日异常人员": (
            f"已知无需考勤记录人员：{_join_names(stats['known_no_record_names'])}。"
            f"非预期空 record 人员：{_join_names(stats['unexpected_empty_record_names'])}。"
        ),
        "三、建议动作": "如 command_failure_count 大于 0，先复跑失败人员；若仍失败，再检查 DWS profile 权限和钉钉考勤可见范围。",
        "四、系统运行状态": (
            f"后端：DWS attendance record/summary；mock 数据：否；原始数据仅写入私有 OneDrive 月目录。"
            f"命令失败数：{stats['command_failure_count']}。"
        ),
    }


def _hr_context(plan: dict[str, Any], collection: dict[str, Any]) -> dict[str, str]:
    stats = collection["stats"]
    failures = [
        row["member"]["name"]
        for row in collection["results"]
        if not row["derived"]["record_success"] or not row["derived"]["summary_success"]
    ]
    return {
        "title": f"开明考勤 HR 报告｜{collection['work_date']}｜{plan['run_type']}",
        "一、异常明细": (
            f"当天 record 为空且非已知豁免：{_join_names(stats['unexpected_empty_record_names'])}。"
            f"接口局部失败：{_join_names(failures)}。"
        ),
        "二、连续异常人员": "本轮只验证当天 record 与本月 summary，连续异常需依赖后续多日私有归档判断。",
        "三、待审批/待补卡/待核查": "补卡、审批、缺卡等明细保留在私有 raw JSONL；Git 仓库不保存员工考勤明文。",
        "四、数据质量与系统运行状态": (
            f"summary 成功 {stats['summary_success_count']}/{stats['member_count']}；"
            f"record 成功 {stats['record_success_count']}/{stats['member_count']}；"
            "张霖泽、林全意按已知无考勤记录处理。"
        ),
    }


def _join_names(names: list[str]) -> str:
    return "无" if not names else "、".join(names)
