#!/usr/bin/env python3
"""Fail closed on PFI public, Alpha Context, and excluded-system boundary drift."""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
import re
import sys
from typing import Any


PFI_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PFI_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from pfi_os.security.pfi_context_export import (  # noqa: E402
    CONTEXT_PAYLOAD_FIELDS,
    DEFAULT_SCHEMA_PATH,
    build_blocked_pfi_context_export,
    load_distribution_boundary_policy,
    validate_pfi_context_export,
)


PUBLIC_SOURCE = PFI_ROOT / "web/cloudflare-public/public"
PUBLIC_CONFIG = PFI_ROOT / "web/cloudflare-public/wrangler.jsonc"
PUBLIC_MANIFEST_NAME = "public-surface.json"
MAIN_INDEX = PFI_ROOT / "web/index.html"
ACTIVE_PYTHON_FILES = (
    PFI_ROOT / "src/pfi_os/application/homepage_summary.py",
    PFI_ROOT / "src/pfi_os/security/pfi_context_export.py",
    PFI_ROOT / "src/pfi_v02/stage5_advice_report_alpha.py",
    PFI_ROOT / "src/pfi_v02/stage6_e2e_stabilization.py",
    PFI_ROOT / "src/pfi_v02/stage_v021_runtime_api.py",
)
FORBIDDEN_PUBLIC_SUFFIXES = {
    ".db",
    ".duckdb",
    ".js",
    ".key",
    ".p12",
    ".pem",
    ".pfx",
    ".sqlite",
    ".sqlite3",
}
FORBIDDEN_PUBLIC_NAMES = {".env", ".env.local", "id_ed25519", "id_rsa"}
FORBIDDEN_PUBLIC_PATTERNS = {
    "absolute_path": re.compile(r"(?:/Users/[^/\s]+/|/home/[^/\s]+/|[A-Za-z]:\\\\Users\\\\)"),
    "private_domain": re.compile(r"\b(?:PRIVATE_USER|PRIVATE_DERIVED|SECRET)\b"),
    "credential": re.compile(
        r"(?:-----BEGIN [A-Z ]*PRIVATE KEY-----|\bsk-[A-Za-z0-9_-]{16,}\b|"
        r"\bgh[pousr]_[A-Za-z0-9]{20,}\b)"
    ),
    "local_runtime": re.compile(r"(?:localhost|127\.0\.0\.1|PFI_DATA_HOME|\.sqlite\b)"),
    "runtime_api": re.compile(r"(?:\bfetch\s*\(|\bWebSocket\s*\(|/api/)"),
    "financial_amount": re.compile(r"(?:\b(?:AUD|CNY|USD|HKD)\s+[-+]?\d|[$¥]\s*\d)"),
}
FORBIDDEN_HTML_ELEMENTS = re.compile(
    r"<(?:button|canvas|form|iframe|input|script|select|textarea)\b",
    re.IGNORECASE,
)
FORBIDDEN_WRANGLER_KEYS = {
    "ai",
    "analytics_engine_datasets",
    "browser",
    "d1_databases",
    "dispatch_namespaces",
    "durable_objects",
    "hyperdrive",
    "kv_namespaces",
    "main",
    "mtls_certificates",
    "queues",
    "r2_buckets",
    "services",
    "unsafe",
    "vars",
    "vectorize",
    "workflows",
}
LEGACY_CONTEXT_FIELDS = {
    "behavior_tags",
    "investable_cash_aud",
    "net_worth_aud",
    "portfolio_allocation",
}


def scan_boundaries(
    *,
    public_source: Path = PUBLIC_SOURCE,
    public_dist: Path | None = None,
) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    try:
        policy = load_distribution_boundary_policy()
    except Exception as exc:  # fail closed without leaking a local path
        _finding(findings, "distribution_policy_unavailable", type(exc).__name__)
        return _scan_result(findings=findings, scanned_files=0, public_dist=public_dist)
    scanned_files = 0
    source_result = _scan_public_tree(public_source, "public_source", policy, findings)
    scanned_files += source_result
    if public_dist is not None:
        scanned_files += _scan_public_tree(public_dist, "public_dist", policy, findings)
    _scan_public_manifest(public_source / PUBLIC_MANIFEST_NAME, policy, findings)
    _scan_wrangler(PUBLIC_CONFIG, findings)
    _scan_main_ui(MAIN_INDEX, findings)
    _scan_context_contract(policy, findings)
    scanned_files += _scan_active_python_dependencies(findings)
    return _scan_result(
        findings=findings,
        scanned_files=scanned_files,
        public_dist=public_dist,
    )


def _scan_result(
    *,
    findings: list[dict[str, str]],
    scanned_files: int,
    public_dist: Path | None,
) -> dict[str, Any]:
    finding_ids = [item["finding_id"] for item in findings]
    context_contract_findings = {
        "context_contract_rejected",
        "context_schema_not_minimized",
        "context_schema_unavailable",
        "distribution_policy_unavailable",
        "legacy_context_field",
        "numeric_context_payload",
    }
    return {
        "schema": "PFIV025Stage11DistributionBoundaryScanV1",
        "status": "pass" if not findings else "fail",
        "finding_count": len(findings),
        "findings": findings,
        "scanned_file_count": scanned_files,
        "public_source_scanned": True,
        "public_dist_scanned": public_dist is not None,
        "public_active_ui": any(
            item in {"application_navigation_marker", "interactive_html_element"}
            for item in finding_ids
        ),
        "public_runtime_bindings": finding_ids.count("public_runtime_binding"),
        "public_context_fields_exposed": finding_ids.count("pfi_context_field_exposed"),
        "alpha_context_read_only": not any(item in context_contract_findings for item in finding_ids),
        "alpha_context_writeback_allowed": False,
        "ralpha_active_dependency_count": sum(
            1
            for item in findings
            if item["finding_id"] == "excluded_system_import" and item["ref"].endswith(":ralpha")
        ),
        "serenity_alipay_active_dependency_count": sum(
            1
            for item in findings
            if item["finding_id"] == "excluded_system_import"
            and item["ref"].rsplit(":", 1)[-1] in {"serenity", "serenity_alipay"}
        ),
        "contains_absolute_paths": "absolute_path" in finding_ids,
        "contains_private_values": any(
            item in {"credential", "financial_amount", "private_domain"}
            for item in finding_ids
        ),
    }


def _scan_public_tree(
    root: Path,
    scope: str,
    policy: dict[str, Any],
    findings: list[dict[str, str]],
) -> int:
    if not root.is_dir():
        _finding(findings, "missing_public_tree", scope)
        return 0
    files = sorted(path for path in root.rglob("*") if path.is_file())
    if not files:
        _finding(findings, "empty_public_tree", scope)
    if not (root / "index.html").is_file():
        _finding(findings, "missing_index", scope)
    allowed_suffixes = set(policy["public_cloudflare"]["allowed_asset_types"])
    context_field_names = set(CONTEXT_PAYLOAD_FIELDS)
    for path in files:
        relative = path.relative_to(root).as_posix()
        if path.name.lower() in FORBIDDEN_PUBLIC_NAMES:
            _finding(findings, "forbidden_public_filename", f"{scope}:{relative}")
        if path.suffix.lower() in FORBIDDEN_PUBLIC_SUFFIXES:
            _finding(findings, "forbidden_public_file_type", f"{scope}:{relative}")
        if path.suffix.lower() not in allowed_suffixes:
            _finding(findings, "unapproved_public_asset_type", f"{scope}:{relative}")
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            _finding(findings, "unreadable_public_text", f"{scope}:{relative}")
            continue
        for label, pattern in FORBIDDEN_PUBLIC_PATTERNS.items():
            if pattern.search(text):
                _finding(findings, label, f"{scope}:{relative}")
        if any(field in text for field in context_field_names):
            _finding(findings, "pfi_context_field_exposed", f"{scope}:{relative}")
        if path.suffix.lower() == ".html":
            if FORBIDDEN_HTML_ELEMENTS.search(text):
                _finding(findings, "interactive_html_element", f"{scope}:{relative}")
            if "data-workspace" in text or "data-primary-entry" in text:
                _finding(findings, "application_navigation_marker", f"{scope}:{relative}")
    return len(files)


def _scan_public_manifest(
    path: Path,
    policy: dict[str, Any],
    findings: list[dict[str, str]],
) -> None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        _finding(findings, "invalid_public_manifest", "public_source:public-surface.json")
        return
    expected = policy["public_cloudflare"]
    checks = {
        "schema_version": "cloudflare_public_surface.v2",
        "project_id": "pfi",
        "surface_type": expected["surface_type"],
        "active_ui": False,
        "application_routes_enabled": False,
        "worker_runtime_enabled": False,
        "local_runtime_connection": False,
        "pfi_context_export_exposed": False,
        "data_classification": expected["data_classification"],
        "private_domains_readable": [],
        "data_sources": [],
        "external_actions_enabled": False,
        "financial_accounts_connected": False,
        "broker_connections_enabled": False,
    }
    for field, value in checks.items():
        if payload.get(field) != value:
            _finding(findings, "public_manifest_mismatch", field)


def _scan_wrangler(path: Path, findings: list[dict[str, str]]) -> None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        _finding(findings, "invalid_wrangler_config", "wrangler.jsonc")
        return
    for key in sorted(FORBIDDEN_WRANGLER_KEYS & set(payload)):
        _finding(findings, "public_runtime_binding", key)
    assets = payload.get("assets")
    if not isinstance(assets, dict):
        _finding(findings, "missing_static_assets_config", "assets")
        return
    if assets.get("directory") != "./dist":
        _finding(findings, "unexpected_public_asset_directory", "assets.directory")
    if assets.get("not_found_handling") != "404-page":
        _finding(findings, "public_surface_must_not_be_spa", "assets.not_found_handling")


def _scan_main_ui(path: Path, findings: list[dict[str, str]]) -> None:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        _finding(findings, "main_ui_unavailable", "web/index.html")
        return
    if text.count('data-primary-entry="true"') != 10:
        _finding(findings, "main_ui_primary_entry_count", "web/index.html")
    lowered = text.lower()
    for workspace in ("alpha", "ralpha", "serenity-alipay"):
        if f'data-workspace="{workspace}"' in lowered:
            _finding(findings, "excluded_system_navigation", workspace)


def _scan_context_contract(policy: dict[str, Any], findings: list[dict[str, str]]) -> None:
    try:
        schema = json.loads(DEFAULT_SCHEMA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        _finding(findings, "context_schema_unavailable", "pfi_context_v1.schema.json")
        return
    required = set(schema.get("required", ()))
    expected = set(policy["pfi_context"]["metadata_fields"])
    expected.update(policy["pfi_context"]["payload_fields"])
    properties = set(schema.get("properties", {}))
    if (
        required != expected
        or properties != expected
        or schema.get("additionalProperties") is not False
    ):
        _finding(findings, "context_schema_not_minimized", "pfi_context_v1.schema.json")
    if any(field in schema.get("properties", {}) for field in LEGACY_CONTEXT_FIELDS):
        _finding(findings, "legacy_context_field", "pfi_context_v1.schema.json")
    try:
        sample = build_blocked_pfi_context_export(
            as_of="2026-07-16T00:00:00+10:00",
            source_payload={"state": "blocked"},
            read_model_payload={"state": "not_loaded"},
        )
        validate_pfi_context_export(sample, policy=policy)
    except Exception as exc:  # fail closed with type only
        _finding(findings, "context_contract_rejected", type(exc).__name__)
        return
    if any(
        isinstance(value, (int, float)) and not isinstance(value, bool)
        for field, value in sample.items()
        if field in CONTEXT_PAYLOAD_FIELDS
    ):
        _finding(findings, "numeric_context_payload", "pfi_context.v1")


def _scan_active_python_dependencies(findings: list[dict[str, str]]) -> int:
    count = 0
    for path in ACTIVE_PYTHON_FILES:
        if not path.is_file():
            _finding(findings, "active_boundary_source_missing", path.name)
            continue
        count += 1
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, SyntaxError):
            _finding(findings, "active_boundary_source_invalid", path.name)
            continue
        modules: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules.append(node.module)
        for module in modules:
            root = module.split(".", 1)[0].lower()
            if root in {"alpha", "ralpha", "serenity", "serenity_alipay"}:
                _finding(findings, "excluded_system_import", f"{path.name}:{root}")
    return count


def _finding(findings: list[dict[str, str]], finding_id: str, ref: str) -> None:
    findings.append({"finding_id": finding_id, "ref": ref})


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--public-source", type=Path, default=PUBLIC_SOURCE)
    parser.add_argument("--public-dist", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv or sys.argv[1:])
    result = scan_boundaries(public_source=args.public_source, public_dist=args.public_dist)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
