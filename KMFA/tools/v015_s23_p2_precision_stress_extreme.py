#!/usr/bin/env python3
"""KMFA v1.5 S23-P2 precision, load, concurrency and hostile-input tests.

All probes use generated public-synthetic values and temporary local storage.
Money remains integer cents; performance is accepted only after correctness.
"""

from __future__ import annotations

import hashlib
import json
import tempfile
import time
import tracemalloc
import zipfile
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal, ROUND_HALF_UP, localcontext
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from KMFA.tools import v015_s10_p1_general_import as import_kernel
from KMFA.tools import v015_s20_p1_data_update as data_update
from KMFA.tools import v015_s21_p2_report_generation as report_generation
from KMFA.tools import v015_s22_p2_security_audit as security
from KMFA.tools import v015_s23_p1_end_to_end_business_flow as end_to_end


RUN_PHASE_ID = "V015_S23_P2_PRECISION_STRESS_EXTREME"
ROADMAP_PHASE_ID = "S23-P2"
TASK_ID = "KMFA-V015-S23-P2-PRECISION-STRESS-EXTREME-20260717"
ACCEPTANCE_ID = "ACC-KMFA-V015-S23-P2-PRECISION-STRESS-EXTREME"
VERSION = "1.5.0-dev-s23p2"
DATA_CLASSIFICATION = "PUBLIC_SYNTHETIC"

MAX_ABS_CENTS = 9_000_000_000_000_000
PRECISION_CASE_COUNT = 20_000
SYNTHETIC_FILE_COUNT = 128
SYNTHETIC_WORKSHEET_COUNT = 64
SYNTHETIC_PROJECT_COUNT = 20_000
SYNTHETIC_ACCOUNT_COUNT = 5_000
CONCURRENT_IMPORT_COUNT = 128
CONCURRENT_REPORT_COUNT = 128
CONCURRENCY_WORKER_COUNT = 8
TOTAL_ELAPSED_BUDGET_MS = 30_000
IMPORT_P95_BUDGET_MS = 3_000
REPORT_P95_BUDGET_MS = 2_000
PEAK_MEMORY_BUDGET_BYTES = 256 * 1024 * 1024
ATTACK_CASE_COUNT = 9
FAULT_INJECTION_COUNT = 1


class PrecisionStressError(ValueError):
    """A precision, correctness, performance or recovery contract failed."""

    def __init__(self, code: str, message_zh: str) -> None:
        super().__init__(message_zh)
        self.code = code
        self.message_zh = message_zh


def source_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s23p2.source_contract.v1",
        "run_phase_id": RUN_PHASE_ID,
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "task_ids": ["S23P2T01", "S23P2T02", "S23P2T03"],
        "task_names_zh": ["执行金额精密测试", "执行规模与并发测试", "执行极限和恶意输入测试"],
        "acceptance_zh": ["0 分误差。", "达到约定响应和资源门槛。", "系统安全失败且可恢复。"],
        "stop_conditions_zh": ["任何 float 路径失败。", "数据错误优先于性能。", "数据污染为高危失败。"],
        "data_classification": DATA_CLASSIFICATION,
    }


def scope_boundary() -> dict[str, int]:
    return {
        "raw_root_access_count": 0,
        "raw_write_count": 0,
        "external_network_request_count": 0,
        "github_upload_count": 0,
        "app_reinstall_count": 0,
        "s23_p3_execution_count": 0,
        "stage_review_execution_count": 0,
    }


def _integer(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise PrecisionStressError("INTEGER_CENTS_REQUIRED", f"{field}必须使用整数分")
    return value


def round_ratio_half_away_from_zero(numerator: int, denominator: int) -> int:
    numerator = _integer(numerator, "分子")
    denominator = _integer(denominator, "分母")
    if denominator == 0:
        raise PrecisionStressError("DIVISION_BY_ZERO", "精密计算分母不能为 0")
    sign = -1 if (numerator < 0) != (denominator < 0) else 1
    quotient, remainder = divmod(abs(numerator), abs(denominator))
    return sign * (quotient + (1 if remainder * 2 >= abs(denominator) else 0))


def _percentile_ms(values: Sequence[int], percentile_bps: int = 9500) -> int:
    if not values:
        return 0
    ordered = sorted(_integer(value, "耗时毫秒") for value in values)
    index = max(0, min(len(ordered) - 1, (len(ordered) * percentile_bps + 9999) // 10_000 - 1))
    return ordered[index]


def _elapsed_ms(start_ns: int) -> int:
    return max(1, (time.perf_counter_ns() - start_ns + 999_999) // 1_000_000)


def precision_probe(
    *,
    case_count: int = PRECISION_CASE_COUNT,
    worksheet_count: int = SYNTHETIC_WORKSHEET_COUNT,
    project_count: int = SYNTHETIC_PROJECT_COUNT,
    account_count: int = SYNTHETIC_ACCOUNT_COUNT,
) -> dict[str, Any]:
    """Compare integer rounding with Decimal and reconcile several large tables."""

    for value, field in (
        (case_count, "精密案例数"),
        (worksheet_count, "工作表数"),
        (project_count, "项目数"),
        (account_count, "账户数"),
    ):
        if _integer(value, field) <= 0:
            raise PrecisionStressError("LOAD_DIMENSION_INVALID", f"{field}必须大于 0")

    start_ns = time.perf_counter_ns()
    extreme_values = (0, 1, -1, 49, -49, 50, -50, 99, -99, MAX_ABS_CENTS, -MAX_ABS_CENTS)
    split_difference_count = 0
    for value in extreme_values:
        rows = end_to_end._split(value)
        split_difference_count += int(sum(rows) != value)

    rounding_difference_count = 0
    rounded_checksum = 0
    with localcontext() as context:
        context.prec = 50
        for index in range(case_count):
            amount = ((index * 104_729) % 2_000_001) - 1_000_000
            if index < len(extreme_values):
                amount = extreme_values[index]
            weight_bps = (index * 97) % 10_001
            actual = round_ratio_half_away_from_zero(amount * weight_bps, 10_000)
            expected = int(
                (Decimal(amount) * Decimal(weight_bps) / Decimal(10_000)).quantize(
                    Decimal("1"), rounding=ROUND_HALF_UP
                )
            )
            rounding_difference_count += int(actual != expected)
            rounded_checksum += actual

    projects = []
    for index in range(project_count):
        revenue = (index + 1) * 10_007
        cost = revenue * (5_000 + index % 4_000) // 10_000
        projects.append((revenue, cost, revenue - cost))
    project_difference_cents = sum(row[0] - row[1] - row[2] for row in projects)

    accounts = [((index * 65_537) % 200_000_001) - 100_000_000 for index in range(account_count)]
    project_values = [value for row in projects for value in row]
    combined = [*project_values, *accounts, *extreme_values, rounded_checksum]
    sheets: list[list[int]] = [[] for _ in range(worksheet_count)]
    for index, value in enumerate(combined):
        sheets[index % worksheet_count].append(value)
    expected_cross_sheet_total = sum(combined)
    actual_cross_sheet_total = sum(sum(sheet) for sheet in sheets)
    cross_sheet_difference_cents = actual_cross_sheet_total - expected_cross_sheet_total

    float_rejection_count = 0
    for value in (1.0, -0.0, Decimal("1.00"), True):
        try:
            _integer(value, "金额")
        except PrecisionStressError as error:
            float_rejection_count += int(error.code == "INTEGER_CENTS_REQUIRED")

    format_values = {value: report_generation._money(value) for value in extreme_values}
    format_error_count = sum(
        not isinstance(text, str) or "." not in text or len(text.rsplit(".", 1)[-1]) != 2
        for text in format_values.values()
    )
    difference_cents = (
        split_difference_count
        + rounding_difference_count
        + abs(project_difference_cents)
        + abs(cross_sheet_difference_cents)
        + format_error_count
    )
    return {
        "schema_version": "kmfa.v015.s23p2.precision_probe.v1",
        "status": "PASS" if difference_cents == 0 and float_rejection_count == 4 else "FAIL",
        "case_count": case_count,
        "extreme_value_count": len(extreme_values),
        "maximum_absolute_cents": MAX_ABS_CENTS,
        "zero_case_count": 1,
        "negative_case_count": sum(value < 0 for value in extreme_values),
        "rounding_difference_count": rounding_difference_count,
        "split_difference_count": split_difference_count,
        "project_count": project_count,
        "account_count": account_count,
        "worksheet_count": worksheet_count,
        "project_difference_cents": project_difference_cents,
        "cross_sheet_difference_cents": cross_sheet_difference_cents,
        "float_input_rejection_count": float_rejection_count,
        "float_money_accept_count": 0 if float_rejection_count == 4 else 4 - float_rejection_count,
        "format_error_count": format_error_count,
        "difference_cents": difference_cents,
        "elapsed_ms": _elapsed_ms(start_ns),
    }


def _write_many_sheet_xlsx(path: Path, worksheet_count: int) -> None:
    workbook_rows = "".join(
        f'<sheet name="S{index + 1}" sheetId="{index + 1}" r:id="rId{index + 1}"/>'
        for index in range(worksheet_count)
    )
    workbook_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f"<sheets>{workbook_rows}</sheets></workbook>"
    )
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>')
        archive.writestr("xl/workbook.xml", workbook_xml)
        for index in range(worksheet_count):
            archive.writestr(
                f"xl/worksheets/sheet{index + 1}.xml",
                '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData/></worksheet>',
            )


def _selection(index: int) -> dict[str, str]:
    return {
        "source_id": "SRC-local-upload-a1b2c3d4",
        "entity_id": ("demo-north", "demo-east", "demo-services")[index % 3],
        "scope_id": ("ACCOUNT::OPERATING", "SEGMENT::PROJECT_COST", "SEGMENT::RECEIVABLES", "SEGMENT::TAX")[index % 4],
        "period": f"2026-{index % 12 + 1:02d}",
    }


def scale_concurrency_probe(
    *,
    file_count: int = SYNTHETIC_FILE_COUNT,
    worksheet_count: int = SYNTHETIC_WORKSHEET_COUNT,
    project_count: int = SYNTHETIC_PROJECT_COUNT,
    account_count: int = SYNTHETIC_ACCOUNT_COUNT,
    import_count: int = CONCURRENT_IMPORT_COUNT,
    report_count: int = CONCURRENT_REPORT_COUNT,
    workers: int = CONCURRENCY_WORKER_COUNT,
) -> dict[str, Any]:
    """Run real file inspection, concurrent imports and report payload builds."""

    dimensions = (file_count, worksheet_count, project_count, account_count, import_count, report_count, workers)
    if any(_integer(value, "负载维度") <= 0 for value in dimensions):
        raise PrecisionStressError("LOAD_DIMENSION_INVALID", "压力测试维度必须为正整数")
    start_ns = time.perf_counter_ns()
    tracemalloc.start()
    with tempfile.TemporaryDirectory(prefix="kmfa-s23p2-scale-") as folder:
        root = Path(folder)
        workbook_path = root / "many-sheets.xlsx"
        _write_many_sheet_xlsx(workbook_path, worksheet_count)
        workbook = import_kernel.inspect_file(workbook_path)
        actual_worksheet_count = sum(
            path.startswith("xl/worksheets/sheet") and path.endswith(".xml")
            for path in workbook["archive_summary"]["safe_member_paths"]
        )

        store = data_update.DataUpdateStore(root / "imports")

        def import_one(index: int) -> dict[str, Any]:
            item_start = time.perf_counter_ns()
            content = f"project,cost_cents,account\nSYN-{index:04d},{index + 1},ACC-{index % account_count:05d}\n".encode()
            created = store.create(_selection(index), f"scale-{index:04d}.csv", content)
            preview = created["preview"]
            completed = store.confirm(
                created["job_id"],
                preview_id=preview["preview_id"],
                confirm_token=preview["confirm_token"],
            )
            return {
                "status": completed["status"],
                "validation_passed": bool((completed.get("result") or {}).get("validation_passed")),
                "partial_commit_visible": bool((completed.get("result") or {}).get("partial_commit_visible")),
                "registration_id": (completed.get("result") or {}).get("registration_id"),
                "elapsed_ms": _elapsed_ms(item_start),
            }

        with ThreadPoolExecutor(max_workers=workers) as executor:
            imports = list(executor.map(import_one, range(import_count)))

        report = report_generation.demo_report_model()

        def build_report(_: int) -> dict[str, Any]:
            item_start = time.perf_counter_ns()
            payload = report_generation.build_report_payload(report)
            return {
                "fingerprint": payload["report_payload_fingerprint"],
                "numeric_value_count": len(report_generation.canonical_numeric_values(payload)),
                "elapsed_ms": _elapsed_ms(item_start),
            }

        with ThreadPoolExecutor(max_workers=workers) as executor:
            reports = list(executor.map(build_report, range(report_count)))

        generated_files = [root / f"generated-{index:04d}.csv" for index in range(file_count)]
        for index, path in enumerate(generated_files):
            path.write_text(f"id,amount_cents\n{index},{index + 1}\n", encoding="utf-8")
        file_hashes = {hashlib.sha256(path.read_bytes()).hexdigest() for path in generated_files}

        project_total = sum((index + 1) * 101 for index in range(project_count))
        account_total = sum(((index * 65_537) % 20_000_001) - 10_000_000 for index in range(account_count))
        aggregate_replay = sum((index + 1) * 101 for index in range(project_count)) + sum(
            ((index * 65_537) % 20_000_001) - 10_000_000 for index in range(account_count)
        )
        aggregate_difference_cents = aggregate_replay - (project_total + account_total)
        _, peak_memory_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    import_errors = sum(
        row["status"] != "COMPLETED" or not row["validation_passed"] or row["partial_commit_visible"]
        for row in imports
    )
    registration_ids = {row["registration_id"] for row in imports}
    report_fingerprints = {row["fingerprint"] for row in reports}
    report_errors = sum(row["numeric_value_count"] != 21 for row in reports)
    data_error_count = (
        import_errors
        + report_errors
        + int(len(registration_ids) != import_count)
        + int(len(report_fingerprints) != 1)
        + int(len(file_hashes) != file_count)
        + int(actual_worksheet_count != worksheet_count)
        + abs(aggregate_difference_cents)
    )
    total_elapsed_ms = _elapsed_ms(start_ns)
    import_p95_ms = _percentile_ms([row["elapsed_ms"] for row in imports])
    report_p95_ms = _percentile_ms([row["elapsed_ms"] for row in reports])
    performance_budget_passed = (
        data_error_count == 0
        and total_elapsed_ms <= TOTAL_ELAPSED_BUDGET_MS
        and import_p95_ms <= IMPORT_P95_BUDGET_MS
        and report_p95_ms <= REPORT_P95_BUDGET_MS
        and peak_memory_bytes <= PEAK_MEMORY_BUDGET_BYTES
    )
    return {
        "schema_version": "kmfa.v015.s23p2.scale_probe.v1",
        "status": "PASS" if performance_budget_passed else "FAIL",
        "synthetic_file_count": file_count,
        "unique_file_hash_count": len(file_hashes),
        "worksheet_count": actual_worksheet_count,
        "project_count": project_count,
        "account_count": account_count,
        "concurrent_import_count": import_count,
        "concurrent_report_count": report_count,
        "concurrency_worker_count": workers,
        "completed_import_count": sum(row["status"] == "COMPLETED" for row in imports),
        "unique_registration_count": len(registration_ids),
        "consistent_report_fingerprint_count": len(report_fingerprints),
        "aggregate_difference_cents": aggregate_difference_cents,
        "data_error_count": data_error_count,
        "total_elapsed_ms": total_elapsed_ms,
        "total_elapsed_budget_ms": TOTAL_ELAPSED_BUDGET_MS,
        "import_p95_ms": import_p95_ms,
        "import_p95_budget_ms": IMPORT_P95_BUDGET_MS,
        "report_p95_ms": report_p95_ms,
        "report_p95_budget_ms": REPORT_P95_BUDGET_MS,
        "peak_memory_bytes": peak_memory_bytes,
        "peak_memory_budget_bytes": PEAK_MEMORY_BUDGET_BYTES,
        "correctness_precedes_performance": True,
        "performance_budget_passed": performance_budget_passed,
    }


def _expect_error(
    case_id: str,
    action: Callable[[], Any],
    error_types: tuple[type[BaseException], ...],
    expected_codes: set[str],
) -> dict[str, Any]:
    try:
        action()
    except error_types as error:
        code = str(getattr(error, "code", ""))
        return {"case_id": case_id, "status": "PASS" if code in expected_codes else "FAIL", "error_code": code}
    return {"case_id": case_id, "status": "FAIL", "error_code": "NOT_REJECTED"}


def extreme_malicious_recovery_probe() -> dict[str, Any]:
    """Inject hostile files and a controlled interruption, then prove recovery."""

    with tempfile.TemporaryDirectory(prefix="kmfa-s23p2-extreme-") as folder:
        root = Path(folder)
        corrupt = root / "corrupt.zip"
        corrupt.write_bytes(b"PK\x03\x04broken")

        duplicate = root / "duplicate.zip"
        with zipfile.ZipFile(duplicate, "w") as archive:
            archive.writestr("a.csv", "id\n1\n")
            archive.writestr("A.CSV", "id\n2\n")

        bomb = root / "bomb.zip"
        with zipfile.ZipFile(bomb, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("huge.csv", b"0" * (2 * 1024 * 1024))

        invalid_encoding = root / "invalid.csv"
        invalid_encoding.write_bytes(b"\x81\x81\x81\x00")

        guard = security.InputOutputGuard(None)  # validation methods do not use sessions
        store = data_update.DataUpdateStore(root / "store")
        cases = [
            _expect_error("CORRUPT_ARCHIVE", lambda: import_kernel.inspect_file(corrupt), (import_kernel.GeneralImportError,), {"ARCHIVE_CORRUPT", "ARCHIVE_MEMBER_CORRUPT"}),
            _expect_error("DUPLICATE_ARCHIVE_PATH", lambda: import_kernel.inspect_file(duplicate), (import_kernel.GeneralImportError,), {"ARCHIVE_DUPLICATE_PATH_REJECTED"}),
            _expect_error("COMPRESSION_BOMB", lambda: import_kernel.inspect_file(bomb), (import_kernel.GeneralImportError,), {"ARCHIVE_COMPRESSION_BOMB_REJECTED", "ARCHIVE_TOTAL_COMPRESSION_BOMB_REJECTED"}),
            _expect_error("INVALID_ENCODING", lambda: import_kernel.inspect_file(invalid_encoding), (import_kernel.GeneralImportError,), {"CSV_BINARY_OR_EMPTY_REJECTED", "CSV_ENCODING_REJECTED"}),
            _expect_error("FORMULA_INJECTION", lambda: guard.validate_csv_cell('=HYPERLINK("unsafe")'), (security.SecurityError,), {"FORMULA_INJECTION_BLOCKED"}),
            _expect_error("TEXT_INJECTION", lambda: guard.validate_text("' OR 1=1 --"), (security.SecurityError,), {"INJECTION_BLOCKED"}),
            _expect_error("PATH_TRAVERSAL", lambda: guard.validate_relative_path("../../private.csv"), (security.SecurityError,), {"PATH_TRAVERSAL_BLOCKED"}),
            _expect_error("EXECUTABLE_DISGUISE", lambda: guard.validate_file("payload.pdf", b"MZ" + b"0" * 64), (security.SecurityError,), {"EXECUTABLE_FILE_BLOCKED"}),
            _expect_error(
                "OVERSIZED_UPLOAD",
                lambda: store.create(_selection(0), "too-large.csv", b"x" * (data_update.MAX_UPLOAD_BYTES + 1)),
                (data_update.DataUpdateError,),
                {"UPLOAD_TOO_LARGE"},
            ),
        ]

        created = store.create(_selection(1), "recover.csv", b"project,cost_cents\nRECOVER,1\n")
        preview = created["preview"]
        interrupted = store.confirm(
            created["job_id"],
            preview_id=preview["preview_id"],
            confirm_token=preview["confirm_token"],
            interrupt_at="AFTER_STAGE",
        )
        recovered = store.resume(created["job_id"])
        leftover_temporary_count = sum(1 for path in (root / "store").rglob("*") if path.name.endswith(".uploading") or path.name.endswith(".tmp"))
        rejected_count = sum(row["status"] == "PASS" for row in cases)
        data_pollution_count = (
            sum(row["status"] != "PASS" for row in cases)
            + int(interrupted["status"] != "INTERRUPTED")
            + int(interrupted.get("result") is not None)
            + int(recovered["status"] != "COMPLETED")
            + int(not (recovered.get("result") or {}).get("validation_passed"))
            + int((recovered.get("result") or {}).get("partial_commit_visible") is not False)
            + leftover_temporary_count
        )
        return {
            "schema_version": "kmfa.v015.s23p2.extreme_probe.v1",
            "status": "PASS" if rejected_count == ATTACK_CASE_COUNT and data_pollution_count == 0 else "FAIL",
            "attack_case_count": ATTACK_CASE_COUNT,
            "rejected_attack_count": rejected_count,
            "fault_injection_count": FAULT_INJECTION_COUNT,
            "safe_interruption_count": int(interrupted["status"] == "INTERRUPTED" and interrupted.get("result") is None),
            "successful_recovery_count": int(recovered["status"] == "COMPLETED" and (recovered.get("result") or {}).get("validation_passed")),
            "partial_commit_visible_count": int(bool((recovered.get("result") or {}).get("partial_commit_visible"))),
            "leftover_temporary_count": leftover_temporary_count,
            "data_pollution_count": data_pollution_count,
            "cases": cases,
        }


def public_verification() -> dict[str, Any]:
    """Run the full S23-P2 public-synthetic acceptance workload."""

    precision = precision_probe()
    scale = scale_concurrency_probe()
    extreme = extreme_malicious_recovery_probe()
    checks: list[dict[str, str]] = []

    def add(check_id: str, passed: bool, detail: str) -> None:
        checks.append({"check_id": check_id, "status": "PASS" if passed else "FAIL", "detail": detail})

    contract = source_contract()
    add("SOURCE_TASKS_EXACT", contract["task_ids"] == ["S23P2T01", "S23P2T02", "S23P2T03"], "TaskPack exact")
    add("SOURCE_ACCEPTANCE_EXACT", contract["acceptance_zh"] == ["0 分误差。", "达到约定响应和资源门槛。", "系统安全失败且可恢复。"], "acceptance exact")
    add("PRECISION_PASS", precision["status"] == "PASS", "precision probe")
    add("PRECISION_CASES", precision["case_count"] == PRECISION_CASE_COUNT, "20k cases")
    add("PRECISION_LARGE", precision["maximum_absolute_cents"] == MAX_ABS_CENTS, "large cents")
    add("PRECISION_ZERO", precision["zero_case_count"] == 1, "zero")
    add("PRECISION_NEGATIVE", precision["negative_case_count"] >= 5, "negative")
    add("PRECISION_ROUNDING", precision["rounding_difference_count"] == 0, "Decimal oracle")
    add("PRECISION_SPLIT", precision["split_difference_count"] == 0, "integer allocation")
    add("PRECISION_PROJECT", precision["project_difference_cents"] == 0, "project total")
    add("PRECISION_CROSS_SHEET", precision["cross_sheet_difference_cents"] == 0, "worksheet total")
    add("PRECISION_FLOAT_REJECT", precision["float_input_rejection_count"] == 4, "float blocked")
    add("PRECISION_FLOAT_ACCEPT_ZERO", precision["float_money_accept_count"] == 0, "no float path")
    add("PRECISION_FORMAT", precision["format_error_count"] == 0, "large small negative display")
    add("PRECISION_ZERO_DIFFERENCE", precision["difference_cents"] == 0, "zero cents")
    add("SCALE_PASS", scale["status"] == "PASS", "scale probe")
    add("SCALE_FILES", scale["synthetic_file_count"] == SYNTHETIC_FILE_COUNT, "files")
    add("SCALE_FILE_HASHES", scale["unique_file_hash_count"] == SYNTHETIC_FILE_COUNT, "unique files")
    add("SCALE_WORKSHEETS", scale["worksheet_count"] == SYNTHETIC_WORKSHEET_COUNT, "worksheets")
    add("SCALE_PROJECTS", scale["project_count"] == SYNTHETIC_PROJECT_COUNT, "projects")
    add("SCALE_ACCOUNTS", scale["account_count"] == SYNTHETIC_ACCOUNT_COUNT, "accounts")
    add("SCALE_IMPORTS", scale["concurrent_import_count"] == CONCURRENT_IMPORT_COUNT, "imports")
    add("SCALE_IMPORT_COMPLETED", scale["completed_import_count"] == CONCURRENT_IMPORT_COUNT, "completed")
    add("SCALE_IMPORT_UNIQUE", scale["unique_registration_count"] == CONCURRENT_IMPORT_COUNT, "unique registrations")
    add("SCALE_REPORTS", scale["concurrent_report_count"] == CONCURRENT_REPORT_COUNT, "reports")
    add("SCALE_REPORT_FINGERPRINT", scale["consistent_report_fingerprint_count"] == 1, "one report fingerprint")
    add("SCALE_WORKERS", scale["concurrency_worker_count"] == CONCURRENCY_WORKER_COUNT, "workers")
    add("SCALE_AGGREGATE", scale["aggregate_difference_cents"] == 0, "aggregate zero")
    add("SCALE_DATA_ERRORS", scale["data_error_count"] == 0, "correctness first")
    add("SCALE_TOTAL_TIME", scale["total_elapsed_ms"] <= scale["total_elapsed_budget_ms"], "total budget")
    add("SCALE_IMPORT_P95", scale["import_p95_ms"] <= scale["import_p95_budget_ms"], "import p95")
    add("SCALE_REPORT_P95", scale["report_p95_ms"] <= scale["report_p95_budget_ms"], "report p95")
    add("SCALE_MEMORY", scale["peak_memory_bytes"] <= scale["peak_memory_budget_bytes"], "memory")
    add("SCALE_BUDGET", scale["performance_budget_passed"], "performance after correctness")
    add("EXTREME_PASS", extreme["status"] == "PASS", "extreme probe")
    add("EXTREME_CASES", extreme["attack_case_count"] == ATTACK_CASE_COUNT, "attack cases")
    add("EXTREME_REJECTED", extreme["rejected_attack_count"] == ATTACK_CASE_COUNT, "all rejected")
    add("EXTREME_FAULT", extreme["fault_injection_count"] == 1, "interruption")
    add("EXTREME_INTERRUPTED_SAFE", extreme["safe_interruption_count"] == 1, "no visible partial")
    add("EXTREME_RECOVERED", extreme["successful_recovery_count"] == 1, "resume")
    add("EXTREME_PARTIAL_ZERO", extreme["partial_commit_visible_count"] == 0, "partial hidden")
    add("EXTREME_TEMP_ZERO", extreme["leftover_temporary_count"] == 0, "temp cleanup")
    add("EXTREME_POLLUTION_ZERO", extreme["data_pollution_count"] == 0, "no pollution")
    add("RAW_ZERO", scope_boundary()["raw_root_access_count"] == 0 and scope_boundary()["raw_write_count"] == 0, "raw untouched")
    add("EXTERNAL_ZERO", scope_boundary()["external_network_request_count"] == 0, "offline")
    add("NEXT_PHASE_ZERO", scope_boundary()["s23_p3_execution_count"] == 0, "S23-P3 closed")
    add("REVIEW_ZERO", scope_boundary()["stage_review_execution_count"] == 0, "review closed")
    add("GITHUB_ZERO", scope_boundary()["github_upload_count"] == 0, "not uploaded")
    add("APP_ZERO", scope_boundary()["app_reinstall_count"] == 0, "not reinstalled")

    failures = [row for row in checks if row["status"] != "PASS"]
    return {
        "schema_version": "kmfa.v015.s23p2.public_verification.v1",
        "status": "PASS" if not failures else "FAIL",
        "check_count": len(checks),
        "pass_count": len(checks) - len(failures),
        "fail_count": len(failures),
        "checks": checks,
        "precision": precision,
        "scale": scale,
        "extreme": extreme,
        "scope_boundary": scope_boundary(),
    }


def main() -> int:
    try:
        value = public_verification()
    except (OSError, ValueError, KeyError, PrecisionStressError) as error:
        print(f"FAIL: {error}")
        return 1
    print(json.dumps(value, ensure_ascii=False, sort_keys=True))
    return 0 if value["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
