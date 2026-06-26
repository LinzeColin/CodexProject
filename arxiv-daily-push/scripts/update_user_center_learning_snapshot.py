#!/usr/bin/env python3
"""Sync review/action/asset/ROI daily values into the GitHub user center."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


PENDING = "待今日运行快照写入"
REVIEW_REPORT_FILENAME = "stage2_s2pjt02_review_schedule_report.json"
ACTION_ROI_REPORT_FILENAME = "stage2_s2pjt03_action_asset_roi_ledger_report.json"
SNAPSHOT_FIELDS = (
    "今日到期复习",
    "未来 7 天复习",
    "已逾期复习",
    "已完成复习",
    "今日 15 分钟行动",
    "今日 2 小时行动",
    "今日 7 天行动",
    "今日 30 天行动",
    "新增能力资产",
    "可验证实际收益 / 转化",
)


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def default_page() -> Path:
    return project_root() / "用户中心" / "复习行动与收益.md"


def load_report(path: Path | None) -> dict[str, Any] | None:
    if path is None or not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def report_passed(report: dict[str, Any] | None, ready_key: str) -> bool:
    return bool(report and report.get("status") == "pass" and report.get(ready_key) is True)


def count_value(value: Any) -> str:
    if isinstance(value, bool):
        return PENDING
    if isinstance(value, int) and value >= 0:
        return f"{value} 项"
    return PENDING


def snapshot_values(
    review_report: dict[str, Any] | None,
    action_report: dict[str, Any] | None,
) -> dict[str, str]:
    values = {field: PENDING for field in SNAPSHOT_FIELDS}

    if report_passed(review_report, "s2pjt02_review_schedule_ready"):
        counts = review_report.get("computed_counts")
        if isinstance(counts, dict):
            values.update(
                {
                    "今日到期复习": count_value(counts.get("due_today")),
                    "未来 7 天复习": count_value(counts.get("due_next_7_days")),
                    "已逾期复习": count_value(counts.get("overdue")),
                    "已完成复习": count_value(counts.get("completed")),
                }
            )

    if report_passed(action_report, "s2pjt03_action_roi_ready"):
        counts = action_report.get("action_counts")
        if isinstance(counts, dict):
            values.update(
                {
                    "今日 15 分钟行动": count_value(counts.get("15m")),
                    "今日 2 小时行动": count_value(counts.get("2h")),
                    "今日 7 天行动": count_value(counts.get("7d")),
                    "今日 30 天行动": count_value(counts.get("30d")),
                }
            )
        assets = action_report.get("capability_assets")
        if isinstance(assets, list):
            values["新增能力资产"] = count_value(len(assets))
        roi_counts = action_report.get("actual_roi_status_counts")
        if isinstance(roi_counts, dict):
            values["可验证实际收益 / 转化"] = count_value(roi_counts.get("calculated"))

    return values


def replace_snapshot_values(text: str, values: dict[str, str]) -> str:
    lines = text.splitlines()
    changed_lines: list[str] = []
    seen: set[str] = set()
    row_re = re.compile(r"^\| (?P<field>[^|]+) \| (?P<value>[^|]+) \| (?P<source>[^|]+) \|$")
    for line in lines:
        match = row_re.match(line)
        if match:
            field = match.group("field").strip()
            if field in values:
                seen.add(field)
                line = f"| {field} | {values[field]} | {match.group('source').strip()} |"
        changed_lines.append(line)

    missing = [field for field in SNAPSHOT_FIELDS if field not in seen]
    if missing:
        raise ValueError("复习行动与收益.md missing snapshot rows: " + ", ".join(missing))

    return "\n".join(changed_lines) + ("\n" if text.endswith("\n") else "")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="write snapshot values")
    parser.add_argument("--check", action="store_true", help="check page values match reports")
    parser.add_argument("--page", type=Path, default=default_page())
    parser.add_argument("--state-dir", type=Path, default=project_root() / ".adp")
    parser.add_argument("--review-schedule-report", type=Path)
    parser.add_argument("--action-roi-report", type=Path)
    args = parser.parse_args()

    if not args.write and not args.check:
        parser.error("use --write or --check")

    review_path = args.review_schedule_report or args.state_dir / REVIEW_REPORT_FILENAME
    action_path = args.action_roi_report or args.state_dir / ACTION_ROI_REPORT_FILENAME
    values = snapshot_values(load_report(review_path), load_report(action_path))

    current = args.page.read_text(encoding="utf-8")
    expected = replace_snapshot_values(current, values)

    if args.write:
        args.page.write_text(expected, encoding="utf-8")
        print(f"updated learning snapshot: {args.page}")
        print(f"review_report={review_path if review_path.exists() else 'missing'}")
        print(f"action_roi_report={action_path if action_path.exists() else 'missing'}")

    if args.check:
        if current != expected:
            print(f"{args.page}: learning snapshot values are out of sync")
            return 1
        print(f"validated learning snapshot: {args.page}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
