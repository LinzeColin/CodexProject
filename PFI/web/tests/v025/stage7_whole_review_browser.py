#!/usr/bin/env python3
"""Run all three Stage 7 formal-shell workflows on current HEAD.

Each existing Phase runner is redirected to a temporary evidence directory, so
immutable Phase evidence is not overwritten. Only redacted aggregate results
and hashes are persisted in the whole-stage review directory.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Any


PFI_ROOT = Path(__file__).resolve().parents[3]
REPO_ROOT = PFI_ROOT.parent
REPORT_DIR = PFI_ROOT / "reports/pfi_v025/stage_7/whole_stage_review"
RUNNERS = {
    "import_review_ledger": PFI_ROOT / "web/tests/v025/stage7_import_review_ledger_browser.py",
    "holding_settings": PFI_ROOT / "web/tests/v025/stage7_holding_settings_browser.py",
    "metric_lineage": PFI_ROOT / "web/tests/v025/stage7_metric_drilldown_browser.py",
}
PERSISTED_TRACES = {
    "import_browser_trace_sanitized.zip": ("import_review_ledger", "browser_trace_sanitized.zip"),
    "holding_browser_trace_sanitized.zip": ("holding_settings", "browser_trace_sanitized.zip"),
    "holding_restart_browser_trace_sanitized.zip": (
        "holding_settings", "browser_trace_restart_sanitized.zip"
    ),
    "metric_browser_trace_sanitized.zip": ("metric_lineage", "browser_trace_sanitized.zip"),
}


def _load(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(f"pfi_stage7_whole_{name}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load Stage 7 runner: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return payload


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _all_true(mapping: object) -> bool:
    return isinstance(mapping, dict) and bool(mapping) and all(bool(value) for value in mapping.values())


def _reviewed_worktree_overlay() -> dict[str, Any]:
    completed = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z", "-uall"],
        cwd=REPO_ROOT, check=True, stdout=subprocess.PIPE,
    )
    review_prefix = REPORT_DIR.relative_to(REPO_ROOT).as_posix() + "/"
    paths: set[str] = set()
    for entry in completed.stdout.decode("utf-8").split("\0"):
        if len(entry) < 4:
            continue
        status = entry[:2]
        if any(marker in status for marker in ("D", "R", "C")):
            raise RuntimeError(
                f"unsupported delete/rename/copy worktree state in reviewed overlay: {status!r}"
            )
        path = entry[3:]
        if path.startswith(review_prefix):
            continue
        absolute = REPO_ROOT / path
        if absolute.is_file():
            paths.add(path)
    files = [
        {"path": path, "sha256": _sha256(REPO_ROOT / path)}
        for path in sorted(paths)
    ]
    records = "".join(f"{item['path']}\0{item['sha256']}\n" for item in files).encode("utf-8")
    return {
        "schema": "PFIV025Stage7ReviewedWorktreeOverlayV1",
        "base_commit": subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT,
            check=True, text=True, capture_output=True,
        ).stdout.strip(),
        "file_count": len(files),
        "files": files,
        "content_manifest_sha256": "sha256:" + hashlib.sha256(records).hexdigest(),
        "whole_review_output_excluded_from_manifest": True,
    }


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    overlay = _reviewed_worktree_overlay()
    for name in PERSISTED_TRACES:
        (REPORT_DIR / name).unlink(missing_ok=True)
    scratch = Path(tempfile.mkdtemp(prefix="pfi-stage7-whole-review-", dir="/tmp"))
    modules: dict[str, Any] = {}
    return_codes: dict[str, int] = {}
    try:
        for name, runner in RUNNERS.items():
            output = scratch / name
            output.mkdir(parents=True, exist_ok=True)
            module = _load(name, runner)
            module.REPORT_DIR = output
            modules[name] = module
            return_codes[name] = int(module.main())

        p71 = scratch / "import_review_ledger"
        p72 = scratch / "holding_settings"
        p73 = scratch / "metric_lineage"
        b71 = _json(p71 / "browser_validation.json")
        b72 = _json(p72 / "browser_validation.json")
        b73 = _json(p73 / "browser_validation.json")
        db71 = _json(p71 / "db_integrity.json")
        db72 = _json(p72 / "db_integrity.json")
        upload = _json(p71 / "upload_import_trace.json")
        ledger = _json(p71 / "ledger_before_after.json")
        restart = _json(p72 / "restart_persistence.json")
        settings = _json(p72 / "settings_persistence.json")
        metric = _json(p73 / "metric_drilldown.json")

        for output_name, (workflow_name, source_name) in PERSISTED_TRACES.items():
            shutil.copyfile(scratch / workflow_name / source_name, REPORT_DIR / output_name)

        p71_checks = len(b71.get("checks", {}))
        p72_checks = len(b72.get("checks", {})) + len(b72.get("exercise_checks", {}))
        p73_checks = len(b73.get("checks", {}))
        workflow_status = {
            "import_review_ledger": (
                return_codes["import_review_ledger"] == 0
                and b71.get("status") == "pass"
                and _all_true(b71.get("checks"))
                and db71.get("status") == "pass"
                and upload.get("status") == "pass"
                and ledger.get("status") == "pass"
                and b71.get("trace_privacy_scan", {}).get("actual_playwright_trace") is True
            ),
            "holding_settings": (
                return_codes["holding_settings"] == 0
                and b72.get("status") == "pass"
                and _all_true(b72.get("checks"))
                and _all_true(b72.get("exercise_checks"))
                and db72.get("status") == "pass"
                and restart.get("status") == "pass"
                and settings.get("status") == "pass"
                and all(
                    item.get("actual_playwright_trace") is True
                    for item in b72.get("trace_privacy_scans", [])
                )
                and len(b72.get("trace_privacy_scans", [])) == 2
            ),
            "metric_lineage": (
                return_codes["metric_lineage"] == 0
                and b73.get("status") == "pass"
                and _all_true(b73.get("checks"))
                and metric.get("status") == "pass"
                and int(b73.get("financial_values_persisted") or 0) == 0
                and b73.get("trace_privacy_scan", {}).get("actual_playwright_trace") is True
            ),
        }
        overlay_after = _reviewed_worktree_overlay()
        if overlay_after != overlay:
            raise RuntimeError(
                "worktree changed during Stage 7 browser review; evidence is rejected"
            )
        payload = {
            "schema": "PFIV025Stage7WholeReviewWorkflowValidationV1",
            "status": "pass" if all(workflow_status.values()) else "fail",
            "acceptance_id": "ACC-PFI-V025-STAGE7-WHOLE-REVIEW",
            "current_head": subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT,
                check=True, text=True, capture_output=True,
            ).stdout.strip(),
            "reviewed_worktree_overlay": {
                "base_commit": overlay["base_commit"],
                "file_count": overlay["file_count"],
                "content_manifest_sha256": overlay["content_manifest_sha256"],
                "evidence_ref": "PFI/reports/pfi_v025/stage_7/whole_stage_review/reviewed_worktree_overlay.json",
                "post_run_rescan_identical": True,
            },
            "method": "three_actual_formal_shell_workflows_cached_playwright_local_chrome_ephemeral_loopback",
            "workflow_status": workflow_status,
            "browser_check_count": p71_checks + p72_checks + p73_checks,
            "workflows": {
                "import_review_ledger": {
                    "browser_check_count": p71_checks,
                    "source_content_sha256": upload.get("source_content_sha256"),
                    "transaction_count": upload.get("transaction_count"),
                    "review_count": upload.get("review_count"),
                    "preview_ledger_count": ledger.get("preview_ledger_count"),
                    "confirmed_ledger_count": ledger.get("confirmed_ledger_count"),
                    "duplicate_ledger_count": ledger.get("duplicate_ledger_count"),
                    "rolled_back_ledger_count": ledger.get("rolled_back_ledger_count"),
                    "reconfirmed_ledger_count": ledger.get("reconfirmed_ledger_count"),
                    "sqlite_integrity": db71.get("integrity_check"),
                    "sqlite_foreign_key_check": db71.get("foreign_key_check"),
                },
                "holding_settings": {
                    "browser_check_count": p72_checks,
                    "restart_persistence": restart,
                    "settings_persistence": settings,
                    "sqlite_before_after": db72,
                    "browser_storage_used_for_formal_settings": settings.get(
                        "browser_storage_used_for_formal_settings"
                    ),
                },
                "metric_lineage": {
                    "browser_check_count": p73_checks,
                    "formal_routes": metric.get("formal_routes"),
                    "parameter_center": metric.get("parameter_center"),
                    "interconnection_map": metric.get("interconnection_map"),
                    "metric_drilldown": metric.get("metric_drilldown"),
                    "financial_values_persisted": b73.get("financial_values_persisted"),
                },
            },
            "fresh_artifact_hashes": {
                "import_browser_validation": _sha256(p71 / "browser_validation.json"),
                "import_sanitized_trace": _sha256(p71 / "browser_trace_sanitized.zip"),
                "holding_browser_validation": _sha256(p72 / "browser_validation.json"),
                "holding_sanitized_trace": _sha256(p72 / "browser_trace_sanitized.zip"),
                "holding_restart_sanitized_trace": _sha256(
                    p72 / "browser_trace_restart_sanitized.zip"
                ),
                "metric_browser_validation": _sha256(p73 / "browser_validation.json"),
                "metric_sanitized_trace": _sha256(p73 / "browser_trace_sanitized.zip"),
            },
            "persisted_trace_hashes": {
                name: _sha256(REPORT_DIR / name) for name in PERSISTED_TRACES
            },
            "phase_evidence_overwritten": False,
            "real_financial_source_read": True,
            "real_financial_source_mutated": False,
            "database_changed": True,
            "database_scope": "isolated_/tmp_only",
            "contains_private_values": False,
            "finder_used": False,
            "network_performed": True,
            "network_scope": "ephemeral_local_loopback_only",
            "external_network_performed": False,
            "push_performed": False,
            "app_install_performed": False,
        }
        (REPORT_DIR / "workflow_validation.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (REPORT_DIR / "reviewed_worktree_overlay.json").write_text(
            json.dumps(overlay, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    finally:
        shutil.rmtree(scratch, ignore_errors=True)

    print(json.dumps({"status": payload["status"], "workflow_status": workflow_status}, ensure_ascii=False))
    return 0 if payload["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
