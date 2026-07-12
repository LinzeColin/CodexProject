#!/usr/bin/env python3
"""Reconstruct DingTalk's 49-column daily export from read-only source snapshots."""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from dataclasses import asdict, dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Mapping
from zoneinfo import ZoneInfo


EXACT = "EXACT"
FORMAT_ONLY = "FORMAT_ONLY"
VALUE_DIFFERENT = "VALUE_DIFFERENT"
NO_DATA_SOURCE = "NO_DATA_SOURCE"
PASS = "PASS"
BLOCKED = "BLOCKED"
RECONCILIATION_CERTIFICATE_SCHEMA = "kmfa.dingtalk_attendance.official_reconciliation.v1"
INDEPENDENT_EVIDENCE_KIND = "INDEPENDENT_OFFICIAL_EXPORT_VS_DWS"


class _NoSource:
    pass


NO_SOURCE = _NoSource()

OFFICIAL_COLUMNS = (
    "姓名", "考勤组", "部门", "工号", "职位", "UserId", "日期", "workDate",
    "班次", "上班1打卡时间", "上班1打卡结果", "下班1打卡时间", "下班1打卡结果",
    "上班2打卡时间", "上班2打卡结果", "下班2打卡时间", "下班2打卡结果",
    "上班3打卡时间", "上班3打卡结果", "下班3打卡时间", "下班3打卡结果",
    "关联的审批单", "出勤天数", "休息天数", "工作时长", "迟到次数", "迟到时长",
    "严重迟到次数", "严重迟到时长", "旷工迟到天数", "早退次数", "早退时长",
    "上班缺卡次数", "下班缺卡次数", "旷工天数", "出差时长", "外出时长",
    "事假(天)", "病假(天)", "年假(天)", "调休(天)", "婚假(天)", "产假(天)",
    "陪产假(天)", "路途假(天)", "加班总时长", "工作日（转调休）", "休息日（转调休）",
    "节假日（转调休）",
)
OPTIONAL_COLUMNS = ("部门",)
REQUIRED_COLUMNS = tuple(column for column in OFFICIAL_COLUMNS if column not in OPTIONAL_COLUMNS)
_OPTIONAL_COLUMN_INDICES = {OFFICIAL_COLUMNS.index(column) for column in OPTIONAL_COLUMNS}
_REQUIRED_COLUMN_INDICES = set(range(len(OFFICIAL_COLUMNS))) - _OPTIONAL_COLUMN_INDICES


@dataclass(frozen=True)
class ColumnSource:
    index: int
    column: str
    category: str
    endpoint: str
    source_field: str
    conversion: str


def _source(index: int, category: str, endpoint: str, field: str, conversion: str = "原值") -> ColumnSource:
    return ColumnSource(index, OFFICIAL_COLUMNS[index], category, endpoint, field, conversion)


COLUMN_SOURCES = (
    _source(0, "员工资料", "contact user get", "orgEmployeeModel.orgUserName"),
    _source(1, "考勤组", "attendance group search + filtered-get", "name + memberUsers"),
    _source(2, "员工资料", "contact user get + contact dept list-children", "orgEmployeeModel.depts[].deptId + 组织树", "单部门输出完整层级；多部门且无主部门字段时 fail closed"),
    _source(3, "员工资料", "contact user get", "orgEmployeeModel.jobNumber", "保留文本与前导零；占位值 0.0 按官方原件显示为空白"),
    _source(4, "员工资料", "contact user get", "orgEmployeeModel.orgTitle / 职务标签"),
    _source(5, "员工资料", "report query-data", "userId", "按文本保留前导零"),
    _source(6, "展示换算", "report query-data", "workDate", "YYYY-MM-DD → YY-MM-DD 星期X"),
    _source(7, "展示换算", "report query-data", "workDate", "Asia/Shanghai 日界毫秒字符串"),
    _source(8, "班次", "report query-data", "班次", "官方结算展示值"),
    *(
        _source(index, "打卡记录", "report query-data", OFFICIAL_COLUMNS[index], "官方结算展示值")
        for index in range(9, 21)
    ),
    _source(21, "审批记录", "report query-data + approve list", "关联的审批单", "保留审批证据；本企业每日统计原件该展示列为空白，结算状态体现在打卡结果"),
    *(
        _source(index, "官方统计字段", "report query-data", OFFICIAL_COLUMNS[index], "空白与数字 0 分离")
        for index in range(22, 37)
    ),
    *(
        _source(index, "审批记录", "report query-leave", OFFICIAL_COLUMNS[index].removesuffix("(天)"), "空白与数字 0 分离")
        for index in range(37, 45)
    ),
    *(
        _source(index, "官方统计字段", "report query-data", OFFICIAL_COLUMNS[index], "空白与数字 0 分离")
        for index in range(45, 49)
    ),
)

_LEAVE_NAME_BY_COLUMN = {index: OFFICIAL_COLUMNS[index].removesuffix("(天)") for index in range(37, 45)}
_NUMERIC_COLUMNS = set(range(22, 49)) - {37, 38, 39, 40, 41, 42, 43, 44}
_NUMERIC_COLUMNS.update(range(37, 45))
_TIME_COLUMNS = {9, 11, 13, 15, 17, 19}
_WEEKDAYS = ("星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日")


def _payload_results(payloads: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for payload in payloads:
        result = payload.get("result")
        if isinstance(result, list):
            rows.extend(row for row in result if isinstance(row, dict))
    return rows


def _blank_preserving(value: Any) -> Any:
    return None if value in (None, "") else value


def _profiles(snapshot: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    profiles: dict[str, dict[str, Any]] = {}
    for row in _payload_results(list(snapshot.get("user_profiles") or [])):
        model = row.get("orgEmployeeModel")
        if not isinstance(model, dict):
            continue
        user_id = model.get("orgUserId") or model.get("userId")
        if user_id is not None:
            profiles[str(user_id)] = model
    return profiles


def _group_names(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    candidates: dict[str, set[str]] = {}
    for payload in list(snapshot.get("attendance_groups") or []):
        result = payload.get("result") if isinstance(payload, Mapping) else None
        if not isinstance(result, dict) or not isinstance(result.get("memberUsers"), list):
            continue
        name = result.get("name")
        if name is None:
            continue
        for user_id in result["memberUsers"]:
            candidates.setdefault(str(user_id), set()).add(str(name))
    output: dict[str, Any] = {}
    for user_id, names in candidates.items():
        output[user_id] = next(iter(names)) if len(names) == 1 else NO_SOURCE
    return output


def _profile_title(profile: Mapping[str, Any]) -> Any:
    if profile.get("orgTitle") not in (None, ""):
        return profile["orgTitle"]
    for label in profile.get("labels") or []:
        if isinstance(label, Mapping) and label.get("groupName") == "职务" and label.get("name") not in (None, ""):
            return label["name"]
    return None


def _profile_department(profile: Mapping[str, Any], snapshot: Mapping[str, Any]) -> Any:
    depts = profile.get("depts")
    if not isinstance(depts, list):
        return None
    usable = [dept for dept in depts if isinstance(dept, Mapping) and dept.get("deptName") not in (None, "")]
    if not usable:
        return None
    if len(usable) != 1:
        return NO_SOURCE
    dept = usable[0]
    directory = snapshot.get("department_directory")
    entry = directory.get(str(dept.get("deptId"))) if isinstance(directory, Mapping) else None
    path = entry.get("path") if isinstance(entry, Mapping) else None
    if isinstance(path, list) and path and all(item not in (None, "") for item in path):
        return "-".join(str(item) for item in path)
    return dept["deptName"]


def _job_number_display(value: Any) -> Any:
    value = _blank_preserving(value)
    return None if value == "0.0" else value


def _official_numeric_display(value: Any) -> Any:
    if value is NO_SOURCE or value is None:
        return value
    try:
        number = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        return value
    if number == 0:
        return None
    if number == number.to_integral_value():
        return str(int(number))
    return format(number.normalize(), "f")


def _date_display(work_date: str) -> str:
    parsed = datetime.strptime(work_date, "%Y-%m-%d")
    return f"{parsed.strftime('%y-%m-%d')} {_WEEKDAYS[parsed.weekday()]}"


def _work_date_epoch_ms(work_date: str) -> str:
    parsed = datetime.strptime(work_date, "%Y-%m-%d").replace(tzinfo=ZoneInfo("Asia/Shanghai"))
    return str(int(parsed.timestamp() * 1000))


def build_reconstructed_rows(snapshot: Mapping[str, Any], *, work_date: str) -> dict[str, list[Any]]:
    report_names = [str(value) for value in snapshot.get("report_column_names") or []]
    report_ids = [str(value) for value in snapshot.get("report_column_ids") or []]
    if len(report_names) != len(report_ids):
        raise ValueError("report column names and ids must have equal length")
    column_id_by_name = dict(zip(report_names, report_ids, strict=True))
    report_rows = _payload_results(list((snapshot.get("report_query_data") or {}).get(work_date) or []))
    leave_rows = _payload_results(list((snapshot.get("report_query_leave") or {}).get(work_date) or []))
    profiles = _profiles(snapshot)
    group_names = _group_names(snapshot)
    leave_by_user: dict[str, dict[str, Any]] = {}
    for row in leave_rows:
        user_id = row.get("userId")
        if user_id is None:
            continue
        by_name: dict[str, Any] = {}
        for item in row.get("leaveVals") or []:
            if not isinstance(item, Mapping) or str(item.get("date") or "") not in {work_date, _work_date_epoch_ms(work_date)}:
                continue
            name = item.get("leaveName")
            if name is not None:
                by_name[str(name)] = _blank_preserving(item.get("value"))
        leave_by_user[str(user_id)] = by_name

    output: dict[str, list[Any]] = {}
    for row in report_rows:
        user_id_raw = row.get("userId")
        if user_id_raw is None or str(row.get("workDate") or "") != work_date:
            continue
        user_id = str(user_id_raw)
        profile = profiles.get(user_id)
        values_by_term = {
            str(item.get("termId")): item.get("value")
            for item in row.get("values") or []
            if isinstance(item, Mapping) and item.get("termId") is not None
        }

        def report_value(name: str) -> Any:
            term_id = column_id_by_name.get(name)
            if term_id is None or term_id not in values_by_term:
                return NO_SOURCE
            return _blank_preserving(values_by_term[term_id])

        result: list[Any] = [NO_SOURCE] * len(OFFICIAL_COLUMNS)
        if profile is not None:
            result[0] = _blank_preserving(profile.get("orgUserName"))
            result[2] = _profile_department(profile, snapshot)
            result[3] = _job_number_display(profile.get("jobNumber"))
            result[4] = _blank_preserving(_profile_title(profile))
        result[1] = group_names.get(user_id, "未加入考勤组")
        result[5] = user_id
        result[6] = _date_display(work_date)
        result[7] = _work_date_epoch_ms(work_date)
        for index in list(range(8, 37)) + list(range(45, 49)):
            result[index] = report_value(OFFICIAL_COLUMNS[index])
        if result[21] is not NO_SOURCE:
            result[21] = None
        for index in list(range(22, 37)) + list(range(45, 49)):
            result[index] = _official_numeric_display(result[index])
        user_leave = leave_by_user.get(user_id)
        for index, leave_name in _LEAVE_NAME_BY_COLUMN.items():
            result[index] = (
                NO_SOURCE
                if user_leave is None or leave_name not in user_leave
                else _official_numeric_display(user_leave[leave_name])
            )
        output[user_id] = result
    return output


def _normalized_text(value: Any) -> str:
    return " ".join(unicodedata.normalize("NFKC", str(value)).split())


def _normalized_decimal(value: Any) -> Decimal | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        return None


def _normalized_time(value: Any) -> str | None:
    if value is None:
        return None
    match = re.search(r"(?:^|\s)(\d{1,2}):(\d{2})(?::\d{2})?(?:$|\s)", str(value).strip())
    return f"{int(match.group(1)):02d}:{match.group(2)}" if match else None


def classify_cell(official: Any, reconstructed: Any, *, column_name: str) -> str:
    if reconstructed is NO_SOURCE:
        return NO_DATA_SOURCE
    if official == reconstructed and type(official) is type(reconstructed):
        return EXACT
    if (official is None) != (reconstructed is None):
        return VALUE_DIFFERENT
    index = OFFICIAL_COLUMNS.index(column_name)
    if index == 5:
        return FORMAT_ONLY if str(official) == str(reconstructed) else VALUE_DIFFERENT
    if index in _TIME_COLUMNS:
        left, right = _normalized_time(official), _normalized_time(reconstructed)
        return FORMAT_ONLY if left is not None and left == right else VALUE_DIFFERENT
    if index in _NUMERIC_COLUMNS:
        left, right = _normalized_decimal(official), _normalized_decimal(reconstructed)
        return FORMAT_ONLY if left is not None and left == right else VALUE_DIFFERENT
    return FORMAT_ONLY if _normalized_text(official) == _normalized_text(reconstructed) else VALUE_DIFFERENT


def compare_standard_entry(
    standard: Mapping[str, Any],
    reconstructed: Mapping[str, list[Any]],
    *,
    work_date: str,
) -> dict[str, Any]:
    values = standard.get("values")
    if not isinstance(values, list) or len(values) < 5:
        raise ValueError("standard workbook values are missing")
    standard_rows = [row for row in values[4:] if isinstance(row, list) and any(value not in (None, "") for value in row)]
    official_by_user = {str(row[5]): row for row in standard_rows}
    missing_people = sorted(set(official_by_user) - set(reconstructed))
    extra_people = sorted(set(reconstructed) - set(official_by_user))
    summaries = [
        {"index": index, "column": name, "exact": 0, "format_only": 0, "value_different": 0, "no_data_source": 0}
        for index, name in enumerate(OFFICIAL_COLUMNS)
    ]
    differences: list[dict[str, Any]] = []
    compared_cells = 0
    for user_id in sorted(set(official_by_user) & set(reconstructed)):
        official_row = official_by_user[user_id]
        rebuilt_row = reconstructed[user_id]
        if len(official_row) != len(OFFICIAL_COLUMNS) or len(rebuilt_row) != len(OFFICIAL_COLUMNS):
            raise ValueError("every standard and reconstructed row must contain 49 columns")
        for index, column_name in enumerate(OFFICIAL_COLUMNS):
            classification = classify_cell(official_row[index], rebuilt_row[index], column_name=column_name)
            if index in _REQUIRED_COLUMN_INDICES:
                compared_cells += 1
            summaries[index][classification.lower()] += 1
            if classification in {VALUE_DIFFERENT, NO_DATA_SOURCE}:
                differences.append({
                    "user_id": user_id,
                    "column_index": index,
                    "column": column_name,
                    "classification": classification,
                    "official": official_row[index],
                    "reconstructed": None if rebuilt_row[index] is NO_SOURCE else rebuilt_row[index],
                })
    missing_required_columns = [
        summary["column"]
        for summary in summaries
        if summary["index"] in _REQUIRED_COLUMN_INDICES and summary["no_data_source"] > 0
    ]
    true_differences = sum(
        summary["value_different"]
        for summary in summaries
        if summary["index"] in _REQUIRED_COLUMN_INDICES
    )
    required_missing_cells = sum(
        summary["no_data_source"]
        for summary in summaries
        if summary["index"] in _REQUIRED_COLUMN_INDICES
    )
    optional_unverified_fields = [
        summary["column"]
        for summary in summaries
        if summary["index"] in _OPTIONAL_COLUMN_INDICES
        and (summary["no_data_source"] > 0 or summary["value_different"] > 0)
    ]
    status = (
        PASS
        if not missing_people
        and not extra_people
        and not missing_required_columns
        and true_differences == 0
        else BLOCKED
    )
    return {
        "work_date": work_date,
        "official_people": len(official_by_user),
        "reconstructed_people": len(reconstructed),
        "matched_people": len(set(official_by_user) & set(reconstructed)),
        "compared_cells": compared_cells,
        "missing_people": missing_people,
        "extra_people": extra_people,
        "compared_columns": len(REQUIRED_COLUMNS),
        "missing_required_columns": missing_required_columns,
        "unmapped_columns": missing_required_columns,
        "true_differences": true_differences,
        "required_missing_cells": required_missing_cells,
        "no_source_cells": required_missing_cells,
        "format_only_differences": sum(
            summary["format_only"]
            for summary in summaries
            if summary["index"] in _REQUIRED_COLUMN_INDICES
        ),
        "optional_unverified_fields": optional_unverified_fields,
        "column_summary": summaries,
        "differences": differences,
        "status": status,
    }


def build_reconciliation_certificate(
    day_result: Mapping[str, Any],
    *,
    official_sha256: str,
) -> dict[str, Any]:
    """Build the only certificate shape accepted by the final reconciliation runner."""
    fingerprint = official_sha256.lower()
    if len(fingerprint) != 64 or any(char not in "0123456789abcdef" for char in fingerprint):
        raise ValueError("official_sha256 must be a 64-character lowercase hexadecimal digest")
    missing_people = day_result.get("missing_people")
    extra_people = day_result.get("extra_people")
    missing_columns = day_result.get("missing_required_columns")
    certificate = {
        "schema": RECONCILIATION_CERTIFICATE_SCHEMA,
        "evidence_kind": INDEPENDENT_EVIDENCE_KIND,
        "official_sha256": fingerprint,
        "work_date": str(day_result.get("work_date") or ""),
        "status": str(day_result.get("status") or BLOCKED),
        "official_people": int(day_result.get("official_people") or 0),
        "dws_people": int(day_result.get("reconstructed_people") or 0),
        "matched_people": int(day_result.get("matched_people") or 0),
        "compared_columns": len(REQUIRED_COLUMNS),
        "compared_cells": int(day_result.get("compared_cells") or 0),
        "missing_people": len(missing_people) if isinstance(missing_people, list) else int(missing_people or 0),
        "extra_people": len(extra_people) if isinstance(extra_people, list) else int(extra_people or 0),
        "missing_required_columns": (
            len(missing_columns) if isinstance(missing_columns, list) else int(missing_columns or 0)
        ),
        "missing_required_cells": int(day_result.get("required_missing_cells") or 0),
        "differing_required_cells": int(day_result.get("true_differences") or 0),
        "optional_unverified_fields": list(day_result.get("optional_unverified_fields") or []),
    }
    return certificate


def validate_reconciliation_certificate(
    certificate: Mapping[str, Any],
    *,
    expected_work_date: str | None = None,
) -> list[str]:
    """Return validation errors for the canonical aggregate-only certificate."""
    errors: list[str] = []
    if certificate.get("schema") != RECONCILIATION_CERTIFICATE_SCHEMA:
        errors.append("schema")
    if certificate.get("evidence_kind") != INDEPENDENT_EVIDENCE_KIND:
        errors.append("evidence_kind")
    work_date = certificate.get("work_date")
    try:
        datetime.strptime(str(work_date), "%Y-%m-%d")
    except ValueError:
        errors.append("work_date")
    if expected_work_date is not None and work_date != expected_work_date:
        errors.append("expected_work_date")
    fingerprint = str(certificate.get("official_sha256") or "")
    if len(fingerprint) != 64 or any(char not in "0123456789abcdef" for char in fingerprint.lower()):
        errors.append("official_sha256")
    official_people = certificate.get("official_people")
    dws_people = certificate.get("dws_people")
    matched_people = certificate.get("matched_people")
    if not (
        isinstance(official_people, int)
        and official_people > 0
        and official_people == dws_people == matched_people
    ):
        errors.append("people")
    if certificate.get("compared_columns") != len(REQUIRED_COLUMNS):
        errors.append("compared_columns")
    if not isinstance(matched_people, int) or certificate.get("compared_cells") != matched_people * len(REQUIRED_COLUMNS):
        errors.append("compared_cells")
    for field in (
        "missing_people",
        "extra_people",
        "missing_required_columns",
        "missing_required_cells",
        "differing_required_cells",
    ):
        if certificate.get(field) != 0:
            errors.append(field)
    if certificate.get("optional_unverified_fields") not in ([], list(OPTIONAL_COLUMNS)):
        errors.append("optional_unverified_fields")
    if certificate.get("status") != PASS:
        errors.append("status")
    return errors


def write_reconciliation_certificate(certificate: Mapping[str, Any], output_dir: Path) -> Path:
    errors = validate_reconciliation_certificate(certificate)
    if errors:
        raise ValueError("invalid reconciliation certificate: " + ", ".join(errors))
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"official_reconciliation_{certificate['work_date']}.certificate.json"
    path.write_text(json.dumps(dict(certificate), ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def compare_two_days(
    standards: list[Mapping[str, Any]],
    snapshot: Mapping[str, Any],
    *,
    official_sha256_by_date: Mapping[str, str],
) -> dict[str, Any]:
    by_date: dict[str, Mapping[str, Any]] = {}
    for standard in standards:
        title = str((standard.get("values") or [[""]])[0][0])
        match = re.search(r"20\d{2}-\d{2}-\d{2}", title)
        if match:
            by_date[match.group(0)] = standard
    days = []
    for work_date in ("2026-07-09", "2026-07-10"):
        if work_date not in by_date:
            raise ValueError(f"standard workbook missing {work_date}")
        days.append(compare_standard_entry(
            by_date[work_date],
            build_reconstructed_rows(snapshot, work_date=work_date),
            work_date=work_date,
        ))
    combined_columns = []
    for index, column_name in enumerate(OFFICIAL_COLUMNS):
        combined_columns.append({
            "index": index,
            "column": column_name,
            "exact": sum(day["column_summary"][index]["exact"] for day in days),
            "format_only": sum(day["column_summary"][index]["format_only"] for day in days),
            "value_different": sum(day["column_summary"][index]["value_different"] for day in days),
            "no_data_source": sum(day["column_summary"][index]["no_data_source"] for day in days),
        })
    missing_required_columns = [
        row["column"]
        for row in combined_columns
        if row["index"] in _REQUIRED_COLUMN_INDICES and row["no_data_source"] > 0
    ]
    true_differences = sum(
        row["value_different"] for row in combined_columns if row["index"] in _REQUIRED_COLUMN_INDICES
    )
    required_missing_cells = sum(
        row["no_data_source"] for row in combined_columns if row["index"] in _REQUIRED_COLUMN_INDICES
    )
    optional_unverified_fields = [
        row["column"]
        for row in combined_columns
        if row["index"] in _OPTIONAL_COLUMN_INDICES
        and (row["no_data_source"] > 0 or row["value_different"] > 0)
    ]
    missing_people = sum(len(day["missing_people"]) for day in days)
    extra_people = sum(len(day["extra_people"]) for day in days)
    status = (
        PASS
        if not missing_required_columns
        and true_differences == 0
        and missing_people == 0
        and extra_people == 0
        else BLOCKED
    )
    certificates = [
        build_reconciliation_certificate(
            day,
            official_sha256=official_sha256_by_date.get(day["work_date"], ""),
        )
        for day in days
    ]
    return {
        "schema_version": 2,
        "evidence_kind": INDEPENDENT_EVIDENCE_KIND,
        "dates": [day["work_date"] for day in days],
        "compared_cells": sum(day["compared_cells"] for day in days),
        "compared_columns": len(REQUIRED_COLUMNS),
        "missing_required_columns": missing_required_columns,
        "unmapped_columns": missing_required_columns,
        "true_differences": true_differences,
        "required_missing_cells": required_missing_cells,
        "no_source_cells": required_missing_cells,
        "format_only_differences": sum(
            row["format_only"] for row in combined_columns if row["index"] in _REQUIRED_COLUMN_INDICES
        ),
        "optional_unverified_fields": optional_unverified_fields,
        "missing_people": missing_people,
        "extra_people": extra_people,
        "column_summary": combined_columns,
        "days": days,
        "column_sources": [asdict(source) for source in COLUMN_SOURCES],
        "certificates": certificates,
        "status": status,
    }


def _parse_fingerprint_args(values: list[str]) -> dict[str, str]:
    output: dict[str, str] = {}
    for value in values:
        work_date, separator, fingerprint = value.partition("=")
        if not separator or work_date in output:
            raise ValueError("--official-sha256 must use unique WORK_DATE=SHA256 values")
        output[work_date] = fingerprint
    required_dates = {"2026-07-09", "2026-07-10"}
    if set(output) != required_dates:
        raise ValueError("--official-sha256 must provide exactly 2026-07-09 and 2026-07-10")
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--standards-json", type=Path, required=True)
    parser.add_argument("--source-json", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--certificate-dir", type=Path, required=True)
    parser.add_argument("--official-sha256", action="append", required=True, metavar="WORK_DATE=SHA256")
    args = parser.parse_args(argv)
    standards = json.loads(args.standards_json.read_text(encoding="utf-8"))
    snapshot = json.loads(args.source_json.read_text(encoding="utf-8"))
    fingerprints = _parse_fingerprint_args(args.official_sha256)
    result = compare_two_days(standards, snapshot, official_sha256_by_date=fingerprints)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    certificate_paths = [
        write_reconciliation_certificate(certificate, args.certificate_dir)
        for certificate in result["certificates"]
    ]
    print(json.dumps({
        "compared_cells": result["compared_cells"],
        "unmapped_columns": len(result["unmapped_columns"]),
        "true_differences": result["true_differences"],
        "format_only_differences": result["format_only_differences"],
        "missing_people": result["missing_people"],
        "extra_people": result["extra_people"],
        "status": result["status"],
        "certificate_count": len(certificate_paths),
    }, ensure_ascii=False))
    return 0 if result["status"] == PASS else 1


if __name__ == "__main__":
    raise SystemExit(main())
