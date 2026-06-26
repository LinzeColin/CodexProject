from __future__ import annotations

import re
from datetime import date, timedelta
from pathlib import Path


REPORTS_HOME = Path.home() / "Downloads" / "行研报告"
ARTIFACTS_HOME = Path(__file__).resolve().parents[2] / "data" / "report_artifacts"


def weekly_report_dir(as_of: str | date) -> Path:
    day = date.fromisoformat(as_of) if isinstance(as_of, str) else as_of
    monday = day - timedelta(days=day.weekday())
    sunday = monday + timedelta(days=6)
    week_of_month = (monday.day - 1) // 7 + 1
    return REPORTS_HOME / f"{monday.month}月第{week_of_month}周 {monday:%d%m}-{sunday:%d%m}"


def report_dir_for_name(name: str) -> Path:
    day = _date_from_report_name(name)
    return weekly_report_dir(day)


def pdf_path(name: str) -> Path:
    return report_dir_for_name(name).joinpath(name)


def markdown_path(name: str) -> Path:
    return _artifact_dir_for_name(name).joinpath("_markdown", name)


def source_log_path(report_name: str) -> Path:
    return _artifact_dir_for_name(report_name).joinpath("_source_logs", f"{report_name}_sources.json")


def image_dir(as_of: str, *parts: str) -> Path:
    return _artifact_dir(as_of).joinpath("_images", *parts)


def excel_dir(as_of: str) -> Path:
    return _artifact_dir(as_of).joinpath("_excel_outputs")


def pfi_os_dir(as_of: str) -> Path:
    return _artifact_dir(as_of).joinpath("_pfi_os")


def expected_weekly_pdf_count() -> int:
    return 22


def _date_from_report_name(name: str) -> date:
    stem = Path(name).stem
    match = re.search(r"_(\d{2})(\d{2})(\d{4})$", stem)
    if not match:
        match = re.search(r"(?:^|\s)(\d{2})(\d{2})(\d{4})_", stem)
    if match:
        day, month, year = match.groups()
        return date(int(year), int(month), int(day))
    iso_match = re.search(r"_(\d{4})-(\d{2})-(\d{2})$", stem)
    if iso_match:
        year, month, day = iso_match.groups()
        return date(int(year), int(month), int(day))
    return date.today()


def _artifact_dir(as_of: str | date) -> Path:
    return ARTIFACTS_HOME / weekly_report_dir(as_of).name


def _artifact_dir_for_name(name: str) -> Path:
    return _artifact_dir(_date_from_report_name(name))
