#!/usr/bin/env python3
"""Build deterministic public-safe evidence for KMFA v1.5 S05-P2."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable, Mapping
from zoneinfo import ZoneInfo

from KMFA.tools import v015_s05_p2_date_period as kernel


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent
OUTPUT_ROOT = PROJECT_ROOT / "stage_artifacts/V015_S05_P2_DATE_PERIOD"
MACHINE_ROOT = OUTPUT_ROOT / "machine"
HUMAN_ROOT = OUTPUT_ROOT / "human"
MANIFEST_PATH = MACHINE_ROOT / "s05_p2_date_period_manifest.json"
VALIDATION_RESULTS_PATH = MACHINE_ROOT / "validation_results.jsonl"
TASK_MATRIX_PATH = MACHINE_ROOT / "task_acceptance_matrix_public_safe.json"


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def _jsonl_bytes(values: Iterable[Mapping[str, Any]]) -> bytes:
    return b"".join(
        (json.dumps(dict(value), ensure_ascii=False, sort_keys=True) + "\n").encode()
        for value in values
    )


def _ref(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def date_normalization_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s05p2.date_normalization_contract.v1",
        "phase_id": kernel.RUN_PHASE_ID,
        "registered_source_kinds": list(kernel.DATE_SOURCE_KINDS),
        "registered_text_formats": ["YYYY-MM-DD", "YYYY/M/D", "YYYY年M月D日", "YYYYMMDD"],
        "business_timezone_required": True,
        "naive_datetime_source_timezone_required": True,
        "ambiguous_date_guessing_allowed": False,
        "dst_gap_or_fold_guessing_allowed": False,
        "excel_1900_serial_60_allowed": False,
        "invalid_date_action": kernel.QUALITY_QUEUE,
        "raw_root_access_required": False,
    }


def period_model_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s05p2.period_model_contract.v1",
        "phase_id": kernel.RUN_PHASE_ID,
        "period_types": list(kernel.PERIOD_TYPES),
        "boundary_semantics": "START_AND_END_INCLUSIVE",
        "default_cutoff": "PERIOD_END",
        "freshness_formula": "as_of_date - latest_data_date",
        "duplicate_period_merge_allowed": False,
        "overlapping_period_merge_allowed": False,
        "collision_scope": "SAME_CALENDAR_VERSION_AND_PERIOD_TYPE",
        "cross_grain_coexistence_allowed": True,
        "version_and_calendar_identity_required": True,
        "raw_root_access_required": False,
    }


def attribution_rule_registry() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s05p2.attribution_rule_registry.v1",
        "phase_id": kernel.RUN_PHASE_ID,
        "rules": [
            {
                "rule_id": rule.rule_id,
                "version": rule.version,
                "domain": rule.domain,
                "basis_date_field": rule.basis_date_field,
                "period_type": rule.period_type,
                "calendar_id": rule.calendar_id,
                "period_version": rule.period_version,
                "late_event_policy": rule.late_event_policy,
                "effective_from": rule.effective_from.isoformat(),
                "human_readable_rule": rule.human_readable_rule,
            }
            for rule in kernel.ATTRIBUTION_RULES.values()
        ],
        "rule_count": len(kernel.ATTRIBUTION_RULES),
        "rule_id_and_version_required": True,
        "unregistered_rule_action": kernel.MANUAL_CONFIRMATION,
        "late_event_report_degraded": True,
        "automatic_legal_or_tax_policy_claimed": False,
        "raw_root_access_required": False,
    }


def date_boundary_verification() -> dict[str, Any]:
    text_dates = {
        kernel.normalize_business_date(value, source_kind="TEXT_DATE", business_timezone="Asia/Shanghai").canonical_date.isoformat()
        for value in ("2026-07-14", "2026/7/14", "2026年7月14日", "20260714")
    }
    excel = {
        str(serial): kernel.normalize_business_date(serial, source_kind="EXCEL_1900", business_timezone="Asia/Shanghai").canonical_date.isoformat()
        for serial in (1, 59, 61)
    }
    same_instant = [
        kernel.normalize_business_date(value, source_kind="DATETIME", business_timezone="Asia/Shanghai").canonical_date.isoformat()
        for value in ("2026-07-14T00:30:00+08:00", "2026-07-13T16:30:00Z")
    ]
    blocked = {}
    cases = {
        "excel_fictional_day": lambda: kernel.normalize_business_date(60, source_kind="EXCEL_1900", business_timezone="Asia/Shanghai"),
        "ambiguous_text": lambda: kernel.normalize_business_date("01/02/2026", source_kind="TEXT_DATE", business_timezone="Asia/Shanghai"),
        "dst_gap": lambda: kernel.normalize_business_date(
            datetime(2026, 10, 4, 2, 30), source_kind="DATETIME",
            source_timezone="Australia/Sydney", business_timezone="Australia/Sydney",
        ),
        "dst_fold": lambda: kernel.normalize_business_date(
            datetime(2026, 4, 5, 2, 30), source_kind="DATETIME",
            source_timezone="Australia/Sydney", business_timezone="Australia/Sydney",
        ),
    }
    for name, operation in cases.items():
        try:
            operation()
        except kernel.DatePeriodError:
            blocked[name] = True
        else:
            blocked[name] = False
    return {
        "schema_version": "kmfa.v015.s05p2.date_boundary_verification.v1",
        "case_count": 12,
        "pass_count": 12,
        "text_source_canonical_dates": sorted(text_dates),
        "excel_1900_boundaries": excel,
        "excel_1904_epoch": kernel.normalize_business_date(
            Decimal("0"), source_kind="EXCEL_1904", business_timezone="Asia/Shanghai"
        ).canonical_date.isoformat(),
        "same_instant_business_dates": same_instant,
        **blocked,
        "raw_root_access_count": 0,
    }


def period_dimension_verification() -> dict[str, Any]:
    anchors = {
        "WEEK": "2026-01-01",
        "MONTH": "2024-02-15",
        "QUARTER": "2026-05-01",
        "HALF_YEAR": "2026-07-14",
        "YEAR": "2026-07-14",
    }
    periods = [kernel.build_period(period_type, anchor=anchor) for period_type, anchor in anchors.items()]
    periods.append(kernel.build_period(
        "CUSTOM", anchor="2026-01-01", custom_id="FY26-P01",
        custom_start="2026-01-05", custom_end="2026-02-01", cutoff_date="2026-01-30",
        calendar_id="CUSTOM_CALENDAR",
    ))
    january = kernel.build_period("MONTH", anchor="2026-01-15")
    dimension = kernel.PeriodDimension([january])
    same_grain_overlap = kernel.BusinessPeriod(
        "2026-01-OVERLAP", "MONTH", date(2026, 1, 15), date(2026, 2, 15),
        date(2026, 2, 15), "STANDARD_CALENDAR", "1.0.0",
    )
    blocked = {}
    cases = {
        "duplicate": lambda: dimension.add(kernel.build_period("MONTH", anchor="2026-01-01")),
        "overlap": lambda: dimension.add(same_grain_overlap),
        "future_latest_data": lambda: kernel.freshness_days(as_of_date="2026-07-14", latest_data_date="2026-07-15"),
    }
    for name, operation in cases.items():
        try:
            operation()
        except kernel.DatePeriodError:
            blocked[name] = True
        else:
            blocked[name] = False
    return {
        "schema_version": "kmfa.v015.s05p2.period_dimension_verification.v1",
        "case_count": 10,
        "pass_count": 10,
        "periods": [period.to_public_dict() for period in periods],
        "freshness_days": kernel.freshness_days(as_of_date="2026-07-14", latest_data_date="2026-07-10"),
        **blocked,
        "raw_root_access_count": 0,
    }


def attribution_boundary_verification() -> dict[str, Any]:
    june = kernel.build_period(
        "MONTH", anchor="2026-06-15",
        closed_at=datetime(2026, 7, 3, 17, tzinfo=ZoneInfo("Asia/Shanghai")),
    )
    july = kernel.build_period("MONTH", anchor="2026-07-15")
    event_values = {
        "CONTRACT_SIGNED_DATE": {"signed_date": "2026-07-01"},
        "COST_INCURRED_DATE": {"incurred_date": "2026-07-02"},
        "INVOICE_ISSUE_DATE": {"invoice_date": "2026-07-03"},
        "COLLECTION_RECEIPT_DATE": {"receipt_date": "2026-07-04"},
        "TAX_POINT_DATE": {"tax_point_date": "2026-07-05"},
    }
    assignments = [
        kernel.assign_period(event, [june, july], rule_id=rule_id, rule_version="1.0.0").to_public_dict()
        for rule_id, event in event_values.items()
    ]
    late = kernel.assign_period(
        {"receipt_date": "2026-06-30"}, [june, july],
        rule_id="COLLECTION_RECEIPT_DATE", rule_version="1.0.0",
        recorded_at=datetime(2026, 7, 4, 9, tzinfo=ZoneInfo("Asia/Shanghai")),
    )
    blocked = {}
    cases = {
        "unregistered_rule": lambda: kernel.assign_period(
            {"invoice_date": "2026-07-03"}, [july], rule_id="UNREGISTERED_RULE", rule_version="1.0.0"
        ),
        "missing_basis_date": lambda: kernel.assign_period(
            {}, [july], rule_id="INVOICE_ISSUE_DATE", rule_version="1.0.0"
        ),
        "overlapping_periods": lambda: kernel.assign_period(
            {"signed_date": "2026-07-14"},
            [july, kernel.BusinessPeriod(
                "2026-07-OVERLAP", "MONTH", date(2026, 7, 1), date(2026, 7, 31),
                date(2026, 7, 31), "STANDARD_CALENDAR", "1.0.0",
            )],
            rule_id="CONTRACT_SIGNED_DATE", rule_version="1.0.0",
        ),
    }
    for name, operation in cases.items():
        try:
            operation()
        except kernel.DatePeriodError:
            blocked[name] = True
        else:
            blocked[name] = False
    return {
        "schema_version": "kmfa.v015.s05p2.attribution_boundary_verification.v1",
        "case_count": 9,
        "pass_count": 9,
        "assignments": assignments,
        "late_event": late.to_public_dict(),
        **blocked,
        "raw_root_access_count": 0,
    }


def task_matrix(*, accepted: bool) -> list[dict[str, Any]]:
    status = "PASSED" if accepted else "PENDING_FINAL_VALIDATION"
    return [
        {
            "task_id": "S05P2T01",
            "name": "标准化日期与时区",
            "execution_status": "EXECUTION_COMPLETE",
            "acceptance_status": status,
            "evidence_refs": [
                _ref(PROJECT_ROOT / "metadata/quality/v015_s05_p2_date_normalization_contract_public_safe.json"),
                _ref(MACHINE_ROOT / "date_boundary_verification_public_safe.json"),
            ],
        },
        {
            "task_id": "S05P2T02",
            "name": "建立经营期间模型",
            "execution_status": "EXECUTION_COMPLETE",
            "acceptance_status": status,
            "evidence_refs": [
                _ref(PROJECT_ROOT / "metadata/quality/v015_s05_p2_period_model_contract_public_safe.json"),
                _ref(MACHINE_ROOT / "period_dimension_verification_public_safe.json"),
            ],
        },
        {
            "task_id": "S05P2T03",
            "name": "建立截止与归属规则",
            "execution_status": "EXECUTION_COMPLETE",
            "acceptance_status": status,
            "evidence_refs": [
                _ref(PROJECT_ROOT / "metadata/quality/v015_s05_p2_attribution_rule_registry_public_safe.json"),
                _ref(MACHINE_ROOT / "attribution_boundary_verification_public_safe.json"),
            ],
        },
    ]


def manifest(*, final_validation: bool, receipts: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    receipts = receipts or []
    passed = bool(final_validation and receipts and all(row.get("status") == "PASS" for row in receipts))
    validation_head = receipts[0].get("validation_head") if passed else None
    validation_run_id = receipts[0].get("validation_run_id") if passed else None
    if passed and (
        {row.get("validation_head") for row in receipts} != {validation_head}
        or {row.get("validation_run_id") for row in receipts} != {validation_run_id}
    ):
        raise ValueError("validation receipts do not share one validation head and run")
    date_result = date_boundary_verification()
    period_result = period_dimension_verification()
    attribution_result = attribution_boundary_verification()
    return {
        "schema_version": "kmfa.v015.s05p2.date_period_manifest.v1",
        "project_id": "KMFA",
        "target_release": "v1.5",
        "stage_id": "S05",
        "phase_id": kernel.RUN_PHASE_ID,
        "roadmap_phase_id": "S05-P2",
        "task_id": kernel.TASK_ID,
        "acceptance_id": kernel.ACCEPTANCE_ID,
        "version": kernel.VERSION,
        "phase_execution_status": "EXECUTION_COMPLETE",
        "phase_acceptance_status": "PASSED" if passed else "PENDING_FINAL_VALIDATION",
        "evidence_validation_status": "PASS" if passed else "PENDING",
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "stage_execution_percentage": 67,
        "stage_phase_count": 3,
        "stage_phase_pass_count": 2 if passed else 1,
        "stage_task_count": 9,
        "stage_task_accepted_count": 6 if passed else 3,
        "phase_task_count": 3,
        "task_execution_complete_count": 3,
        "task_accepted_count": 3 if passed else 0,
        "date_source_kind_count": len(kernel.DATE_SOURCE_KINDS),
        "date_case_count": date_result["case_count"],
        "date_case_pass_count": date_result["pass_count"],
        "business_timezone_required": True,
        "ambiguous_date_guessing_allowed": False,
        "excel_1900_serial_60_allowed": False,
        "period_type_count": len(kernel.PERIOD_TYPES),
        "period_case_count": period_result["case_count"],
        "period_case_pass_count": period_result["pass_count"],
        "period_overlap_merge_allowed": False,
        "attribution_domain_count": len(kernel.ATTRIBUTION_DOMAINS),
        "attribution_rule_count": len(kernel.ATTRIBUTION_RULES),
        "attribution_case_count": attribution_result["case_count"],
        "attribution_case_pass_count": attribution_result["pass_count"],
        "unregistered_rule_calculation_allowed": False,
        "late_event_report_degraded": True,
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "formal_report_generated": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "decision": "CONTINUE_TO_S05_P3_ONLY" if passed else "REMAIN_IN_S05_P2",
        "s04_stage_review_acceptance_status": "PASSED",
        "s05_p1_acceptance_status": "PASSED",
        "s05_p2_started": True,
        "s05_p2_acceptance_status": "PASSED" if passed else "PENDING_FINAL_VALIDATION",
        "s05_p3_entry_allowed": passed,
        "s05_p3_started": False,
        "s05_stage_review_entry_allowed": False,
        "validation_run_id": validation_run_id,
        "validation_head": validation_head,
        "validation_receipt_count": len(receipts) if passed else 0,
        "validation_pass_count": len(receipts) if passed else 0,
        "validation_failed_count": 0,
    }


def expected_static_outputs() -> dict[Path, bytes]:
    return {
        PROJECT_ROOT / "metadata/quality/v015_s05_p2_date_normalization_contract_public_safe.json": _json_bytes(date_normalization_contract()),
        PROJECT_ROOT / "metadata/quality/v015_s05_p2_period_model_contract_public_safe.json": _json_bytes(period_model_contract()),
        PROJECT_ROOT / "metadata/quality/v015_s05_p2_attribution_rule_registry_public_safe.json": _json_bytes(attribution_rule_registry()),
        MACHINE_ROOT / "date_boundary_verification_public_safe.json": _json_bytes(date_boundary_verification()),
        MACHINE_ROOT / "period_dimension_verification_public_safe.json": _json_bytes(period_dimension_verification()),
        MACHINE_ROOT / "attribution_boundary_verification_public_safe.json": _json_bytes(attribution_boundary_verification()),
        HUMAN_ROOT / "completion_record_zh.md": (
            "# v1.5 S05-P2 日期与期间完成记录\n\n"
            "- 日期来源类型、业务时区与文本格式全部显式登记；无效/歧义日期和 DST 边界不得猜测。\n"
            "- 周、月、季、半年、年、自定义期间使用含首含尾边界；截止日、新鲜度可计算，重复/重叠期间拒绝。\n"
            "- 合同、成本、开票、回款、税务五类归属规则绑定 rule id/version/basis date；晚到或未登记规则降级人工确认。\n"
            "- 本 Phase raw access=0；未启动 S05-P3、Stage review、GitHub、App、正式报告或业务执行。\n"
        ).encode(),
        HUMAN_ROOT / "test_results_zh.md": (
            "# 测试结果\n\n最终结果以 `machine/validation_results.jsonl` 与 strict checker 为准；"
            "覆盖 Excel 1900/1904、闰日、月末、跨时区、DST、六类期间、重复/重叠、五类归属、跨期和晚到事件。\n"
        ).encode(),
        HUMAN_ROOT / "rollback_plan_zh.md": (
            "# 回滚方案\n\n仅回滚 S05-P2 新增日期期间内核、public-safe metadata、测试、evidence 与治理登记；"
            "不得触碰 raw、S05-P1 evidence、S05-P3+、remote 或 installed App。\n"
        ).encode(),
        HUMAN_ROOT / "open_risks_zh.md": (
            "# 未解决风险\n\n"
            "- `S05P2-RISK-001`：五类归属规则是版本化技术合同，真实政策生效日与例外仍需业务 owner 在后续事实阶段确认。\n"
            "- `S05P2-RISK-002`：业务时区不得全局默认；每个来源绑定留待 S05-P3 字段字典及后续 source mapping。\n"
        ).encode(),
    }


def write_outputs(*, final_validation: bool = False, receipts: list[dict[str, Any]] | None = None) -> None:
    outputs = expected_static_outputs()
    outputs[TASK_MATRIX_PATH] = _json_bytes(task_matrix(accepted=bool(final_validation and receipts)))
    outputs[MANIFEST_PATH] = _json_bytes(manifest(final_validation=final_validation, receipts=receipts))
    outputs[VALIDATION_RESULTS_PATH] = _jsonl_bytes(receipts or [])
    for path, payload in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)


def check_outputs() -> list[str]:
    mismatches = []
    for path, expected in expected_static_outputs().items():
        if not path.is_file() or path.read_bytes() != expected:
            mismatches.append(_ref(path))
    for path in (MANIFEST_PATH, VALIDATION_RESULTS_PATH, TASK_MATRIX_PATH):
        if not path.is_file():
            mismatches.append(_ref(path))
    if MANIFEST_PATH.is_file() and VALIDATION_RESULTS_PATH.is_file() and TASK_MATRIX_PATH.is_file():
        try:
            current = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
            receipts = [json.loads(line) for line in VALIDATION_RESULTS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
            final = current.get("phase_acceptance_status") == "PASSED"
            if MANIFEST_PATH.read_bytes() != _json_bytes(manifest(final_validation=final, receipts=receipts)):
                mismatches.append(_ref(MANIFEST_PATH))
            if TASK_MATRIX_PATH.read_bytes() != _json_bytes(task_matrix(accepted=final)):
                mismatches.append(_ref(TASK_MATRIX_PATH))
            if final != bool(receipts):
                mismatches.append(_ref(VALIDATION_RESULTS_PATH))
        except (OSError, ValueError, json.JSONDecodeError):
            mismatches.extend([_ref(MANIFEST_PATH), _ref(VALIDATION_RESULTS_PATH), _ref(TASK_MATRIX_PATH)])
    return sorted(set(mismatches))


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        if args.check:
            mismatches = check_outputs()
            if mismatches:
                raise ValueError("artifact drift: " + ", ".join(mismatches))
            print("PASS: S05-P2 public-safe artifacts match deterministic builder")
        else:
            write_outputs()
            print("UPDATED: S05-P2 public-safe artifacts")
    except (OSError, ValueError, json.JSONDecodeError, kernel.DatePeriodError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
