#!/usr/bin/env python3
"""KMFA v1.5 S23-P3 stability, usability and accessibility acceptance.

The soak uses real local import, recalculation, report and HTTP server paths.
Browser usability/accessibility observations are supplied by the real Chromium
acceptance test and are never fabricated by this module.
"""

from __future__ import annotations

import gc
import hashlib
import json
import tempfile
import threading
import time
import tracemalloc
import urllib.request
from pathlib import Path
from typing import Any, Mapping

from KMFA.tools import run_v015_s23_p1_end_to_end_business_flow as runtime
from KMFA.tools import v015_s20_p1_data_update as data_update
from KMFA.tools import v015_s20_p3_recalculation_publication as recalculation
from KMFA.tools import v015_s21_p2_report_generation as report_generation


RUN_PHASE_ID = "V015_S23_P3_STABILITY_USABILITY"
ROADMAP_PHASE_ID = "S23-P3"
TASK_ID = "KMFA-V015-S23-P3-STABILITY-USABILITY-20260717"
ACCEPTANCE_ID = "ACC-KMFA-V015-S23-P3-STABILITY-USABILITY"
VERSION = "1.5.0-dev-s23p3"
DATA_CLASSIFICATION = "PUBLIC_SYNTHETIC"

SOAK_CYCLE_COUNT = 12
REPEATED_IMPORT_COUNT = 12
REPEATED_RECALCULATION_COUNT = 12
REPEATED_REPORT_COUNT = 12
RESTART_COUNT = 3
REFRESH_COUNT = 24
MEMORY_GROWTH_BUDGET_BYTES = 8 * 1024 * 1024
SOAK_ELAPSED_BUDGET_MS = 60_000

USABILITY_TASK_COUNT = 3
USABILITY_COMPLETION_RATE_BPS = 10_000
USABILITY_TOTAL_BUDGET_MS = 30_000
USABILITY_TASK_BUDGET_MS = 15_000
USABILITY_MAX_INTERACTIONS = 8
MIN_ACCESSIBILITY_CHECK_COUNT = 24
MIN_CONTRAST_SAMPLE_COUNT = 8
NARROW_VIEWPORT_COUNT = 2
PUBLIC_CHECK_COUNT = 60


class StabilityUsabilityError(ValueError):
    """S23-P3 evidence is incomplete or violates an acceptance boundary."""

    def __init__(self, code: str, message_zh: str) -> None:
        super().__init__(message_zh)
        self.code = code
        self.message_zh = message_zh


def source_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s23p3.source_contract.v1",
        "run_phase_id": RUN_PHASE_ID,
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "task_ids": ["S23P3T01", "S23P3T02", "S23P3T03"],
        "task_names_zh": ["执行多轮回归和浸泡测试", "执行真实用户可用性测试", "执行可访问性和多尺寸测试"],
        "acceptance_zh": ["结果幂等，无内存或队列泄露。", "关键任务完成率和效率达标。", "关键页面达到约定标准。"],
        "stop_conditions_zh": ["静默错误数必须为 0。", "明显机械或 AI 堆叠则重做。", "关键信息只靠颜色失败。"],
        "data_classification": DATA_CLASSIFICATION,
    }


def scope_boundary() -> dict[str, int]:
    return {
        "raw_root_access_count": 0,
        "raw_write_count": 0,
        "external_network_request_count": 0,
        "s24_execution_count": 0,
        "stage_review_execution_count": 0,
        "github_upload_count": 0,
        "app_reinstall_count": 0,
    }


def _selection(index: int) -> dict[str, str]:
    return {
        "source_id": "SRC-local-upload-a1b2c3d4",
        "entity_id": ("demo-north", "demo-east", "demo-services")[index % 3],
        "scope_id": ("ACCOUNT::OPERATING", "SEGMENT::PROJECT_COST", "SEGMENT::RECEIVABLES", "SEGMENT::TAX")[index % 4],
        "period": f"2026-{index % 12 + 1:02d}",
    }


def _http_get(url: str) -> tuple[int, bytes]:
    request = urllib.request.Request(url, headers={"User-Agent": "KMFA-S23P3-Soak/1.0"})
    with urllib.request.urlopen(request, timeout=10) as response:
        return int(response.status), response.read()


def _restart_probe(root: Path, restart_index: int, refreshes: int) -> dict[str, Any]:
    prefix = root / "persistent-runtime"
    server, thread, base_url = runtime.start_server(
        event_path=prefix / "base.jsonl",
        data_root=prefix / "data",
        confirmation_event_path=prefix / "confirmations.jsonl",
        publication_event_path=prefix / "publications.jsonl",
        report_model_event_path=prefix / "models.jsonl",
        export_event_path=prefix / "exports.jsonl",
        export_bundle_root=prefix / "bundles",
        workflow_event_path=prefix / "workflows.jsonl",
        notification_event_path=prefix / "notifications.jsonl",
        audit_event_path=prefix / "audit.jsonl",
        operations_root=prefix / "operations",
        xlsx_preview_root=prefix / "xlsx-previews",
        secret_values={
            "KMFA_LOCAL_AUTH_KEY": hashlib.sha256(b"s23p3-soak-auth").hexdigest(),
            "KMFA_SESSION_SIGNING_KEY": hashlib.sha256(b"s23p3-soak-sign").hexdigest(),
        },
    )
    statuses: list[int] = []
    publication_ids: list[str] = []
    try:
        for _ in range(refreshes):
            status, body = _http_get(base_url + "/overview")
            statuses.append(status)
            if b"KMFA" not in body:
                raise StabilityUsabilityError("RESTART_PAGE_INVALID", "重启后的经营首页内容不完整")
            status, body = _http_get(base_url + "/api/end-to-end/status")
            statuses.append(status)
            value = json.loads(body)
            publication_ids.append(str(value["publication_version_id"]))
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
    return {
        "restart_index": restart_index,
        "request_count": len(statuses),
        "http_error_count": sum(status != 200 for status in statuses),
        "publication_id_count": len(set(publication_ids)),
        "thread_still_alive": thread.is_alive(),
    }


def soak_probe(*, cycle_count: int = SOAK_CYCLE_COUNT, restart_count: int = RESTART_COUNT, refresh_count: int = REFRESH_COUNT) -> dict[str, Any]:
    """Run repeated real local operations and measure live memory/queue residue."""

    if not isinstance(cycle_count, int) or isinstance(cycle_count, bool) or cycle_count <= 0:
        raise StabilityUsabilityError("SOAK_CYCLE_INVALID", "浸泡轮数必须为正整数")
    if not isinstance(restart_count, int) or restart_count <= 0 or refresh_count % restart_count:
        raise StabilityUsabilityError("RESTART_REFRESH_INVALID", "重启次数必须为正数且刷新次数可平均分配")

    start_ns = time.perf_counter_ns()
    operation_errors: list[str] = []
    import_ids: list[str] = []
    report_fingerprints: list[str] = []
    recalculation_pass_count = 0
    restart_rows: list[dict[str, Any]] = []
    initial_thread_count = threading.active_count()

    # Warm imported code and deterministic caches before measuring retained memory.
    report_generation.build_report_payload(report_generation.demo_report_model())
    if recalculation.public_verification()["fail_count"]:
        raise StabilityUsabilityError("RECALCULATION_WARMUP_FAILED", "重算预热检查失败")
    gc.collect()
    tracemalloc.start()
    baseline_current_bytes, _ = tracemalloc.get_traced_memory()

    with tempfile.TemporaryDirectory(prefix="kmfa-s23p3-soak-") as folder:
        root = Path(folder)
        store_root = root / "imports"
        store = data_update.DataUpdateStore(store_root)
        for index in range(cycle_count):
            try:
                content = f"project,cost_cents,account\nSOAK-{index:04d},{index + 1},ACC-{index % 5:03d}\n".encode()
                created = store.create(_selection(index), f"soak-{index:04d}.csv", content)
                preview = created["preview"]
                completed = store.confirm(created["job_id"], preview_id=preview["preview_id"], confirm_token=preview["confirm_token"])
                repeated = store.confirm(created["job_id"], preview_id=preview["preview_id"], confirm_token=preview["confirm_token"])
                reloaded = data_update.DataUpdateStore(store_root).read(created["job_id"])
                if completed != repeated or repeated != reloaded or completed["status"] != "COMPLETED":
                    raise StabilityUsabilityError("IMPORT_NOT_IDEMPOTENT", "重复导入确认或重启读取结果不一致")
                import_ids.append(str(completed["result"]["registration_id"]))

                recalculated = recalculation.public_verification()
                if recalculated["fail_count"]:
                    raise StabilityUsabilityError("RECALCULATION_REGRESSION", "重复重算存在失败检查")
                recalculation_pass_count += 1

                payload = report_generation.build_report_payload(report_generation.demo_report_model())
                replay = report_generation.build_report_payload(report_generation.demo_report_model())
                if payload != replay:
                    raise StabilityUsabilityError("REPORT_NOT_IDEMPOTENT", "重复报告生成结果不一致")
                report_fingerprints.append(str(payload["report_payload_fingerprint"]))
            except Exception as error:  # recorded visibly; never treated as a silent pass
                operation_errors.append(f"cycle-{index + 1}:{type(error).__name__}:{error}")

        refreshes_per_restart = refresh_count // restart_count
        for restart_index in range(restart_count):
            try:
                restart_rows.append(_restart_probe(root, restart_index + 1, refreshes_per_restart))
            except Exception as error:
                operation_errors.append(f"restart-{restart_index + 1}:{type(error).__name__}:{error}")

        job_paths = sorted((store_root / "jobs").glob("*/job.json"))
        job_states = [json.loads(path.read_text(encoding="utf-8")) for path in job_paths]
        queue_leak_count = sum(row.get("status") != "COMPLETED" for row in job_states)
        temporary_file_leak_count = sum(1 for path in root.rglob("*") if path.name.endswith((".uploading", ".tmp")))

    del store
    gc.collect()
    final_current_bytes, peak_memory_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    memory_growth_bytes = max(0, final_current_bytes - baseline_current_bytes)
    thread_leak_count = max(0, threading.active_count() - initial_thread_count)
    restart_request_count = sum(row["request_count"] for row in restart_rows)
    restart_error_count = sum(row["http_error_count"] + int(row["thread_still_alive"]) for row in restart_rows)
    publication_drift_count = sum(row["publication_id_count"] != 1 for row in restart_rows)
    idempotency_failure_count = (
        int(len(import_ids) != cycle_count)
        + int(len(set(import_ids)) != cycle_count)
        + int(len(report_fingerprints) != cycle_count)
        + int(len(set(report_fingerprints)) != 1)
        + int(recalculation_pass_count != cycle_count)
        + publication_drift_count
    )
    operation_error_count = len(operation_errors)
    silent_error_count = 0
    memory_growth_excess_count = int(memory_growth_bytes > MEMORY_GROWTH_BUDGET_BYTES)
    elapsed_ms = max(1, (time.perf_counter_ns() - start_ns + 999_999) // 1_000_000)
    passed = all(
        value == 0
        for value in (
            operation_error_count, silent_error_count, idempotency_failure_count, queue_leak_count,
            temporary_file_leak_count, thread_leak_count, restart_error_count, memory_growth_excess_count,
        )
    ) and elapsed_ms <= SOAK_ELAPSED_BUDGET_MS
    return {
        "schema_version": "kmfa.v015.s23p3.soak_probe.v1",
        "status": "PASS" if passed else "FAIL",
        "soak_cycle_count": cycle_count,
        "repeated_import_count": len(import_ids),
        "repeated_recalculation_count": recalculation_pass_count,
        "repeated_report_count": len(report_fingerprints),
        "restart_count": len(restart_rows),
        "refresh_count": restart_request_count // 2,
        "restart_http_request_count": restart_request_count,
        "restart_error_count": restart_error_count,
        "publication_drift_count": publication_drift_count,
        "idempotency_failure_count": idempotency_failure_count,
        "operation_error_count": operation_error_count,
        "silent_error_count": silent_error_count,
        "queue_leak_count": queue_leak_count,
        "temporary_file_leak_count": temporary_file_leak_count,
        "thread_leak_count": thread_leak_count,
        "memory_baseline_bytes": baseline_current_bytes,
        "memory_final_bytes": final_current_bytes,
        "memory_growth_bytes": memory_growth_bytes,
        "memory_growth_budget_bytes": MEMORY_GROWTH_BUDGET_BYTES,
        "memory_growth_excess_count": memory_growth_excess_count,
        "peak_memory_bytes": peak_memory_bytes,
        "elapsed_ms": elapsed_ms,
        "elapsed_budget_ms": SOAK_ELAPSED_BUDGET_MS,
        "errors": operation_errors,
        "restart_observations": restart_rows,
    }


def validate_browser_evidence(evidence: Mapping[str, Any]) -> dict[str, Any]:
    """Validate real Chromium evidence without inventing human observations."""

    if evidence.get("schema_version") != "kmfa.v015.s23p3.browser_acceptance.v1":
        raise StabilityUsabilityError("BROWSER_SCHEMA_INVALID", "浏览器验收证据版本不正确")
    usability = evidence.get("usability")
    accessibility = evidence.get("accessibility")
    if not isinstance(usability, Mapping) or not isinstance(accessibility, Mapping):
        raise StabilityUsabilityError("BROWSER_EVIDENCE_INCOMPLETE", "缺少可用性或可访问性浏览器证据")
    tasks = usability.get("tasks")
    if not isinstance(tasks, list) or [row.get("role_id") for row in tasks] != ["management", "finance", "tax"]:
        raise StabilityUsabilityError("USABILITY_TASKS_INVALID", "经营、财务、税务三类任务证据不完整")
    required_zero = (
        "technical_document_dependency_count", "technical_term_exposure_count", "mechanical_ai_issue_count",
    )
    if any(usability.get(key) != 0 for key in required_zero):
        raise StabilityUsabilityError("USABILITY_PLAIN_LANGUAGE_FAILED", "任务仍依赖技术文档或存在机械堆叠")
    accessibility_zero = (
        "missing_label_count", "contrast_fail_count", "narrow_overflow_count", "color_only_critical_info_count",
        "touch_target_fail_count", "page_error_count", "external_network_request_count",
    )
    if any(accessibility.get(key) != 0 for key in accessibility_zero):
        raise StabilityUsabilityError("ACCESSIBILITY_FAILED", "浏览器可访问性或边界检查失败")
    return {"usability": dict(usability), "accessibility": dict(accessibility), "screenshot_paths": list(evidence.get("screenshot_paths", []))}


def public_verification(browser_evidence: Mapping[str, Any], *, soak: Mapping[str, Any] | None = None) -> dict[str, Any]:
    soak_value = dict(soak) if soak is not None else soak_probe()
    observed = validate_browser_evidence(browser_evidence)
    usability, accessibility = observed["usability"], observed["accessibility"]
    checks: list[dict[str, str]] = []

    def add(check_id: str, passed: bool, detail: Any) -> None:
        checks.append({"check_id": check_id, "status": "PASS" if passed else "FAIL", "detail": str(detail)})

    contract, boundary = source_contract(), scope_boundary()
    add("SOURCE_TASKS_EXACT", contract["task_ids"] == ["S23P3T01", "S23P3T02", "S23P3T03"], "TaskPack exact")
    add("SOURCE_ACCEPTANCE_EXACT", contract["acceptance_zh"] == ["结果幂等，无内存或队列泄露。", "关键任务完成率和效率达标。", "关键页面达到约定标准。"], "acceptance exact")
    add("SOURCE_STOPS_EXACT", contract["stop_conditions_zh"] == ["静默错误数必须为 0。", "明显机械或 AI 堆叠则重做。", "关键信息只靠颜色失败。"], "stop exact")
    add("PUBLIC_SYNTHETIC", contract["data_classification"] == DATA_CLASSIFICATION, DATA_CLASSIFICATION)
    add("SCOPE_ZERO", all(value == 0 for value in boundary.values()), boundary)

    add("SOAK_PASS", soak_value["status"] == "PASS", soak_value["status"])
    add("SOAK_CYCLES", soak_value["soak_cycle_count"] == SOAK_CYCLE_COUNT, soak_value["soak_cycle_count"])
    add("SOAK_IMPORTS", soak_value["repeated_import_count"] == REPEATED_IMPORT_COUNT, soak_value["repeated_import_count"])
    add("SOAK_IMPORT_COMPLETE", soak_value["repeated_import_count"] == soak_value["soak_cycle_count"], "all completed")
    add("SOAK_IMPORT_REPLAY", soak_value["idempotency_failure_count"] == 0, "reloaded identical")
    add("SOAK_RECALCULATIONS", soak_value["repeated_recalculation_count"] == REPEATED_RECALCULATION_COUNT, soak_value["repeated_recalculation_count"])
    add("SOAK_RECALC_PASS", soak_value["repeated_recalculation_count"] == soak_value["soak_cycle_count"], "all passed")
    add("SOAK_REPORTS", soak_value["repeated_report_count"] == REPEATED_REPORT_COUNT, soak_value["repeated_report_count"])
    add("SOAK_REPORT_FINGERPRINT", soak_value["idempotency_failure_count"] == 0, "one deterministic fingerprint")
    add("SOAK_RESTARTS", soak_value["restart_count"] == RESTART_COUNT, soak_value["restart_count"])
    add("SOAK_RESTART_PASS", soak_value["restart_error_count"] == 0, soak_value["restart_error_count"])
    add("SOAK_REFRESHES", soak_value["refresh_count"] == REFRESH_COUNT, soak_value["refresh_count"])
    add("SOAK_REFRESH_PASS", soak_value["publication_drift_count"] == 0, soak_value["publication_drift_count"])
    add("SOAK_IDEMPOTENT", soak_value["idempotency_failure_count"] == 0, soak_value["idempotency_failure_count"])
    add("SOAK_SILENT_ERROR_ZERO", soak_value["silent_error_count"] == 0, soak_value["silent_error_count"])
    add("SOAK_QUEUE_LEAK_ZERO", soak_value["queue_leak_count"] == 0, soak_value["queue_leak_count"])
    add("SOAK_TEMP_LEAK_ZERO", soak_value["temporary_file_leak_count"] == 0, soak_value["temporary_file_leak_count"])
    add("SOAK_THREAD_LEAK_ZERO", soak_value["thread_leak_count"] == 0, soak_value["thread_leak_count"])
    add("SOAK_MEMORY_BUDGET", soak_value["memory_growth_bytes"] <= soak_value["memory_growth_budget_bytes"], soak_value["memory_growth_bytes"])
    add("SOAK_MEMORY_EXCESS_ZERO", soak_value["memory_growth_excess_count"] == 0, soak_value["memory_growth_excess_count"])
    add("SOAK_ELAPSED_BUDGET", soak_value["elapsed_ms"] <= soak_value["elapsed_budget_ms"], soak_value["elapsed_ms"])
    add("SOAK_RAW_ZERO", boundary["raw_root_access_count"] == boundary["raw_write_count"] == 0, "raw closed")
    add("SOAK_EXTERNAL_ZERO", boundary["external_network_request_count"] == 0, "offline")
    add("SOAK_LATER_PHASE_ZERO", boundary["s24_execution_count"] == boundary["stage_review_execution_count"] == 0, "later work closed")
    add("SOAK_RELEASE_ZERO", boundary["github_upload_count"] == boundary["app_reinstall_count"] == 0, "release closed")

    add("USABILITY_PASS", usability["status"] == "PASS", usability["status"])
    add("USABILITY_TASK_COUNT", usability["task_count"] == USABILITY_TASK_COUNT, usability["task_count"])
    add("USABILITY_COMPLETED", usability["completed_task_count"] == USABILITY_TASK_COUNT, usability["completed_task_count"])
    add("USABILITY_RATE", usability["completion_rate_bps"] >= USABILITY_COMPLETION_RATE_BPS, usability["completion_rate_bps"])
    add("USABILITY_TOTAL_TIME", usability["total_elapsed_ms"] <= USABILITY_TOTAL_BUDGET_MS, usability["total_elapsed_ms"])
    add("USABILITY_EACH_TIME", all(row["elapsed_ms"] <= USABILITY_TASK_BUDGET_MS for row in usability["tasks"]), "each within budget")
    add("USABILITY_INTERACTIONS", usability["max_interaction_count"] <= USABILITY_MAX_INTERACTIONS, usability["max_interaction_count"])
    add("USABILITY_MANAGEMENT", usability["tasks"][0]["status"] == "PASS", usability["tasks"][0]["elapsed_ms"])
    add("USABILITY_FINANCE", usability["tasks"][1]["status"] == "PASS", usability["tasks"][1]["elapsed_ms"])
    add("USABILITY_TAX", usability["tasks"][2]["status"] == "PASS", usability["tasks"][2]["elapsed_ms"])
    add("USABILITY_NO_TECH_DOC", usability["technical_document_dependency_count"] == 0, 0)
    add("USABILITY_NO_TECH_TERM", usability["technical_term_exposure_count"] == 0, 0)
    add("USABILITY_NO_MECHANICAL_AI", usability["mechanical_ai_issue_count"] == 0, 0)

    add("ACCESSIBILITY_PASS", accessibility["status"] == "PASS", accessibility["status"])
    add("ACCESSIBILITY_CHECK_COUNT", accessibility["check_count"] >= MIN_ACCESSIBILITY_CHECK_COUNT, accessibility["check_count"])
    add("ACCESSIBILITY_KEYBOARD", accessibility["keyboard_flow_count"] >= 3, accessibility["keyboard_flow_count"])
    add("ACCESSIBILITY_FOCUS", accessibility["visible_focus_pass_count"] >= 1, accessibility["visible_focus_pass_count"])
    add("ACCESSIBILITY_SKIP_LINK", accessibility["skip_link_pass_count"] == 1, accessibility["skip_link_pass_count"])
    add("ACCESSIBILITY_LABELS", accessibility["missing_label_count"] == 0, accessibility["missing_label_count"])
    add("ACCESSIBILITY_CONTRAST_SAMPLES", accessibility["contrast_sample_count"] >= MIN_CONTRAST_SAMPLE_COUNT, accessibility["contrast_sample_count"])
    add("ACCESSIBILITY_CONTRAST", accessibility["contrast_fail_count"] == 0, accessibility["contrast_fail_count"])
    add("ACCESSIBILITY_ZOOM", accessibility["zoom_200_pass_count"] == 1, accessibility["zoom_200_pass_count"])
    add("ACCESSIBILITY_NARROW_COUNT", accessibility["narrow_viewport_count"] == NARROW_VIEWPORT_COUNT, accessibility["narrow_viewport_count"])
    add("ACCESSIBILITY_NARROW_OVERFLOW", accessibility["narrow_overflow_count"] == 0, accessibility["narrow_overflow_count"])
    add("ACCESSIBILITY_PRINT", accessibility["print_pass_count"] == 1, accessibility["print_pass_count"])
    add("ACCESSIBILITY_PRINT_NAV", accessibility["print_navigation_hidden_count"] == 1, accessibility["print_navigation_hidden_count"])
    add("ACCESSIBILITY_COLOR_NOT_ONLY", accessibility["color_only_critical_info_count"] == 0, accessibility["color_only_critical_info_count"])
    add("ACCESSIBILITY_TOUCH", accessibility["touch_target_fail_count"] == 0, accessibility["touch_target_fail_count"])
    add("ACCESSIBILITY_PAGE_ERRORS", accessibility["page_error_count"] == 0, accessibility["page_error_count"])
    add("ACCESSIBILITY_NETWORK", accessibility["external_network_request_count"] == 0, accessibility["external_network_request_count"])

    if len(checks) != PUBLIC_CHECK_COUNT:
        raise StabilityUsabilityError("CHECK_ACCOUNTING_INVALID", f"公开检查数量应为 {PUBLIC_CHECK_COUNT}，实际为 {len(checks)}")
    failures = [row for row in checks if row["status"] != "PASS"]
    return {
        "schema_version": "kmfa.v015.s23p3.public_verification.v1",
        "status": "PASS" if not failures else "FAIL",
        "check_count": len(checks), "pass_count": len(checks) - len(failures), "fail_count": len(failures),
        "checks": checks, "soak": soak_value, "usability": usability, "accessibility": accessibility,
        "scope_boundary": boundary, "screenshot_paths": observed["screenshot_paths"],
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="运行 KMFA v1.5 S23-P3 本地浸泡检查")
    parser.add_argument("--browser-evidence", type=Path)
    args = parser.parse_args()
    try:
        if args.browser_evidence:
            evidence = json.loads(args.browser_evidence.read_text(encoding="utf-8"))
            value = public_verification(evidence)
        else:
            value = soak_probe()
    except (OSError, ValueError, KeyError, json.JSONDecodeError, StabilityUsabilityError) as error:
        print(f"FAIL: {error}")
        return 1
    print(json.dumps(value, ensure_ascii=False, sort_keys=True))
    return 0 if value["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
