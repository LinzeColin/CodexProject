from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import stat
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping
from urllib.parse import quote


VERSION = "v0.2.5"
STAGE = 2
PHASE_ID = "V025-S2-P2.1"
TASK_IDS = ("S2-P1-T1", "S2-P1-T2", "S2-P1-T3", "S2-P1-T4")
ACCEPTANCE_ID = "ACC-PFI-V025-S2-P21-DATA-ROOT-SOURCE-MANIFEST"
CONTRACT_ID = "PFI-V025-STAGE2-PHASE21-DATA-ROOT-SOURCE-MANIFEST"
SOURCE_REGISTRY_PATH = Path(__file__).resolve().parents[2] / "config" / "sources" / "v025_phase_2_1_sources.json"
EXPECTED_SOURCE_IDS = (
    "SRC-TRANSACTIONS-ALIPAY",
    "SRC-OPERATIONAL-SQLITE",
    "SRC-ACCOUNT-BALANCES",
    "SRC-LIABILITIES",
    "SRC-HOLDINGS",
    "SRC-MARKET-PRICES",
    "SRC-FX-SNAPSHOT",
)

# Exact candidate set from the v0.2.5 Roadmap. These symbolic aliases are the
# only root path values permitted in public evidence.
CANDIDATE_ROOT_ALIASES = (
    "MetaDatabase/PFI",
    "PFI/MetaDatabase",
    "$PFI_DATA_HOME",
    "~/.pfi",
)

SOURCE_STATUS_ENUM = {
    "ready",
    "partial",
    "not_loaded",
    "source_missing",
    "path_error",
    "parse_failed",
    "outdated",
    "permission_denied",
    "blocked",
}

_KNOWN_DB_TABLES = (
    "source_records",
    "source_versions",
    "entity_records",
    "evidence_records",
    "job_records",
    "task_records",
    "holding_snapshots",
)
_DATABASE_HASH_SCHEME = "sha256-file-bytes-v1"
_GIT_HASH_SCHEME = "sha256-framed-mode-path-oid-size-blob-v2"
_PRIVACY_SCAN_INPUTS = (
    "PFI/reports/pfi_v025/stage_2/phase_2_1/data_root_inventory.json",
    "PFI/reports/pfi_v025/stage_2/phase_2_1/source_manifest.json",
    "PFI/reports/pfi_v025/stage_2/phase_2_1/metric_computability_matrix.json",
    "PFI/reports/pfi_v025/stage_2/phase_2_1/database_before_after.json",
    "PFI/reports/pfi_v025/stage_2/phase_2_1/evidence.json",
    "PFI/docs/pfi_v025/stage_2/data_root_decision.md",
    "PFI/reports/pfi_v025/stage_2/phase_2_1/risk_and_rollback.md",
    "PFI/reports/pfi_v025/stage_2/phase_2_1/terminal.log",
    "PFI/reports/pfi_v025/stage_2/phase_2_1/changed_files.txt",
)
_FORBIDDEN_CREDENTIAL_KEYS = {
    "api-key",
    "api_key",
    "apikey",
    "access_key",
    "access_key_id",
    "authorization",
    "client_secret",
    "credential",
    "credentials",
    "password",
    "passwd",
    "private_key",
    "secret_key",
}
_FORBIDDEN_PUBLIC_KEYS = {
    "absolute_path",
    "account_id",
    "account_number",
    "raw_filename",
    "raw_path",
    "row",
    "rows",
    "secret",
    "token",
    "transaction_details",
    "transactions_path",
} | _FORBIDDEN_CREDENTIAL_KEYS
_CREDENTIAL_ASSIGNMENT_RE = re.compile(
    r"(?i)(?:api[-_]?key|access[-_]?key(?:[-_]?id)?|password|passwd|authorization|"
    r"client[-_]?secret|private[-_]?key|secret[-_]?key|access[-_]?token|refresh[-_]?token)"
    r"[\"']?\s*[:=]"
)
_BEARER_CREDENTIAL_RE = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]+")
_OBSERVED_AT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:\d{2})$")


def build_phase21_contract() -> dict[str, Any]:
    return {
        "schema": "PFIV025Stage2Phase21ContractV1",
        "version": VERSION,
        "stage": STAGE,
        "phase_id": PHASE_ID,
        "contract_id": CONTRACT_ID,
        "task_ids": list(TASK_IDS),
        "acceptance_id": ACCEPTANCE_ID,
        "acceptance_id_origin": "project_governance_assigned_not_taskpack",
        "current_phase_only": True,
        "read_only_real_sources": True,
        "redacted_public_evidence_only": True,
        "finder_used": False,
        "risk_tier": "T3_PRIVACY",
        "explicitly_not_done": [
            "Phase 2.2",
            "Phase 2.3",
            "原始数据迁移、复制、合并或删除",
            "最终净资产、现金余额或投资市值计算",
            "GitHub push",
            "canonical App install",
        ],
    }


def collect_data_root_inventory(
    project_root: str | Path,
    *,
    data_home: str | Path | None = None,
    env: Mapping[str, str] | None = None,
    git_ref: str = "HEAD",
) -> dict[str, Any]:
    repo_root, pfi_root = _resolve_roots(project_root)
    values = os.environ if env is None else env
    configured = str(values.get("PFI_DATA_HOME", "")).strip()
    if data_home is not None:
        lexical_data_home = _absolute_lexical_path(data_home)
        data_home_resolution = "explicit_read_only_probe_override"
    elif configured:
        lexical_data_home = _absolute_lexical_path(configured)
        data_home_resolution = "environment"
    else:
        lexical_data_home = _absolute_lexical_path(Path.home() / ".pfi")
        data_home_resolution = "user_state_default"

    default_user_root = _absolute_lexical_path(Path.home() / ".pfi")

    physical_roots = {
        "ROOT-METADATABASE-PFI": repo_root / "MetaDatabase" / "PFI",
        "ROOT-PFI-METADATABASE": pfi_root / "MetaDatabase",
        "ROOT-PFI-DATA-HOME": lexical_data_home,
        "ROOT-USER-PFI": default_user_root,
    }
    before = {root_id: _root_fingerprint(path) for root_id, path in physical_roots.items()}
    git_surface = _git_surface(repo_root, git_ref)
    private_root_status = _private_root_status(
        lexical_data_home,
        repo_root,
        before["ROOT-PFI-DATA-HOME"],
    )
    user_root_exists = bool(before["ROOT-USER-PFI"].get("exists"))
    user_root_is_alias = _same_target(lexical_data_home, default_user_root)
    canonical_conflict = (
        data_home_resolution != "explicit_read_only_probe_override"
        and user_root_exists
        and not user_root_is_alias
    )
    canonical_root_gate = (
        "blocked_distinct_private_root_candidate"
        if canonical_conflict
        else private_root_status
    )
    if canonical_root_gate in {"canonical_active", "source_missing"}:
        database_probe = _probe_operational_database(lexical_data_home)
    else:
        database_probe = _blocked_database_probe("blocked_unsafe_root")
    after = {root_id: _root_fingerprint(path) for root_id, path in physical_roots.items()}
    root_metadata_unchanged = before == after
    database_unchanged = database_probe.get("unchanged_before_after")
    database_gate_pass = database_probe.get("status") in {"ready_metadata_only", "source_missing"}
    acceptance_gate_status = (
        "pass"
        if canonical_root_gate in {"canonical_active", "source_missing"}
        and database_gate_pass
        and root_metadata_unchanged
        and database_unchanged is not False
        else "blocked"
    )

    roots = [
        {
            "root_id": "ROOT-METADATABASE-PFI",
            "path_alias": "MetaDatabase/PFI",
            "role": "historical_git_object_source",
            "canonical_private_root": False,
            "exists_in_environment": before["ROOT-METADATABASE-PFI"]["exists"],
            "within_repo": True,
            "git_object_available": git_surface["status"] == "ready",
            "status": "ready_git_object" if git_surface["status"] == "ready" else "source_missing",
            "alias_of": None,
            "resolution_policy": "explicit_read_only_legacy_source",
            "migration_performed": False,
            "permission_mode": before["ROOT-METADATABASE-PFI"].get("mode"),
            "permission_risk": None,
        },
        {
            "root_id": "ROOT-PFI-METADATABASE",
            "path_alias": "PFI/MetaDatabase",
            "role": "repository_placeholder",
            "canonical_private_root": False,
            "exists_in_environment": before["ROOT-PFI-METADATABASE"]["exists"],
            "within_repo": True,
            "git_object_available": False,
            "status": "metadata_only" if before["ROOT-PFI-METADATABASE"]["exists"] else "source_missing",
            "alias_of": None,
            "resolution_policy": "not_a_private_data_root",
            "migration_performed": False,
            "permission_mode": before["ROOT-PFI-METADATABASE"].get("mode"),
            "permission_risk": None,
        },
        {
            "root_id": "ROOT-PFI-DATA-HOME",
            "path_alias": "$PFI_DATA_HOME",
            "role": "canonical_private_runtime_root",
            "canonical_private_root": True,
            "exists_in_environment": before["ROOT-PFI-DATA-HOME"]["exists"],
            "within_repo": _is_relative_to(lexical_data_home, repo_root),
            "git_object_available": False,
            "status": canonical_root_gate,
            "alias_of": None,
            "resolution_policy": "environment_or_user_state_default",
            "active_resolution": data_home_resolution,
            "migration_performed": False,
            "permission_mode": before["ROOT-PFI-DATA-HOME"].get("mode"),
            "permission_risk": _private_permission_risk(before["ROOT-PFI-DATA-HOME"].get("mode")),
        },
        {
            "root_id": "ROOT-USER-PFI",
            "path_alias": "~/.pfi",
            "role": "explicit_user_state_alias" if user_root_is_alias else "alternate_private_root_candidate",
            "canonical_private_root": False,
            "exists_in_environment": before["ROOT-USER-PFI"]["exists"],
            "within_repo": _is_relative_to(default_user_root, repo_root),
            "git_object_available": False,
            "status": (
                "alias_active"
                if user_root_is_alias and before["ROOT-USER-PFI"]["exists"]
                else "blocked_distinct_candidate"
                if before["ROOT-USER-PFI"]["exists"]
                else "source_missing"
            ),
            "alias_of": "ROOT-PFI-DATA-HOME" if user_root_is_alias else None,
            "resolution_policy": "explicit_alias_no_auto_migration",
            "migration_performed": False,
            "permission_mode": before["ROOT-USER-PFI"].get("mode"),
            "permission_risk": _private_permission_risk(before["ROOT-USER-PFI"].get("mode")),
        },
    ]

    payload = {
        "schema": "PFIV025Stage2DataRootInventoryV1",
        "version": VERSION,
        "stage": STAGE,
        "phase": "2.1",
        "observed_at": _utc_now(),
        "task_ids": list(TASK_IDS),
        "candidate_roots": roots,
        "canonical_private_root_id": "ROOT-PFI-DATA-HOME",
        "canonical_private_root_alias": "$PFI_DATA_HOME",
        "canonical_root_gate": canonical_root_gate,
        "canonical_candidate_conflict": canonical_conflict,
        "canonical_decision_basis": [
            "PFI OS runtime contract resolves private state through PFI_DATA_HOME",
            "default resolution is the explicit user-state alias ~/.pfi",
            "canonical private runtime state must remain outside public Git",
            "MetaDatabase/PFI remains a read-only historical Git-object source only",
        ],
        "git_object_surface": git_surface,
        "database_probe": database_probe,
        "observed_root_metadata_unchanged": root_metadata_unchanged,
        "operational_database_unchanged": database_unchanged,
        "acceptance_gate_status": acceptance_gate_status,
        "mutation_attempted": False,
        "migration_performed": False,
        "private_values_emitted": 0,
        "absolute_private_paths_emitted": 0,
    }
    assert_public_safe_payload(payload)
    if not root_metadata_unchanged or database_unchanged is False:
        raise RuntimeError("source_changed_during_read_only_inventory")
    return payload


def build_source_manifest(inventory: Mapping[str, Any]) -> dict[str, Any]:
    git_surface = _require_mapping(inventory, "git_object_surface")
    db_probe = _require_mapping(inventory, "database_probe")
    transaction_status = "ready" if git_surface.get("status") == "ready" else "source_missing"
    transaction_count = git_surface.get("transaction_count") if transaction_status == "ready" else None
    coverage = (
        {"start": git_surface.get("coverage_start"), "end": git_surface.get("coverage_end")}
        if transaction_status == "ready"
        else {"start": None, "end": None}
    )

    db_status_map = {
        "ready_metadata_only": "partial",
        "source_missing": "source_missing",
        "permission_denied": "permission_denied",
    }
    db_status = db_status_map.get(str(db_probe.get("status")), "blocked")
    db_reason = {
        "partial": "SQLite 仅完成只读完整性与结构元数据探测；未建立 source-level record_count、coverage 或 as_of，不能据此确认财务零值。",
        "source_missing": "canonical private root 下未发现 operational SQLite；未使用财务 fixture 回退。",
        "permission_denied": "operational SQLite 无法按只读权限打开；未暴露异常或路径。",
        "blocked": "operational SQLite 未满足静止性、sidecar、symlink 或完整性安全门；Phase 2.1 保持阻塞。",
    }[db_status]

    registry = _load_source_registry()
    definitions = {str(item["source_id"]): item for item in registry["sources"]}
    sources = [
        _source_from_definition(
            definitions["SRC-TRANSACTIONS-ALIPAY"],
            status=transaction_status,
            record_count=int(transaction_count) if transaction_count is not None else None,
            coverage=coverage,
            as_of=git_surface.get("coverage_end") if transaction_status == "ready" else None,
            content_hash=git_surface.get("content_hash") if transaction_status == "ready" else None,
            blocking_reason_zh=(
                None
                if transaction_status == "ready"
                else "历史 Git object 来源不可用；不允许联网或 fake fallback。"
            ),
        ),
        _source_from_definition(
            definitions["SRC-OPERATIONAL-SQLITE"],
            status=db_status,
            record_count=None,
            coverage={"start": None, "end": None},
            as_of=None,
            content_hash=db_probe.get("content_hash") if db_status == "partial" else None,
            blocking_reason_zh=db_reason,
        ),
    ]
    unverified_policy = _require_mapping(registry, "unverified_source_policy")
    for source_id in EXPECTED_SOURCE_IDS[2:]:
        sources.append(
            _source_from_definition(
                definitions[source_id],
                status=str(unverified_policy["status"]),
                record_count=None,
                coverage={"start": None, "end": None},
                as_of=None,
                content_hash=None,
                blocking_reason_zh=str(unverified_policy["blocking_reason_zh"]),
            )
        )
    payload = {
        "schema": "PFIV025SourceManifestCollectionV1",
        "version": VERSION,
        "stage": STAGE,
        "phase": "2.1",
        "observed_at": str(inventory.get("observed_at") or _utc_now()),
        "acceptance_id": ACCEPTANCE_ID,
        "canonical_private_root_id": "ROOT-PFI-DATA-HOME",
        "canonical_private_root_alias": "$PFI_DATA_HOME",
        "taskpack_source_schema": "PFI/config/schemas/v025/data_source_manifest.schema.json",
        "taskpack_schema_applies_to": "sources[*]",
        "wrapper_schema": "PFI/config/schemas/v025/source_manifest_collection.schema.json",
        "wrapper_schema_applies_to": "document",
        "sources": sources,
        "financial_fixture_fallback_used": False,
        "source_registry": "PFI/config/sources/v025_phase_2_1_sources.json",
        "source_registry_content_hash": _sha256_file(SOURCE_REGISTRY_PATH),
        "observed_root_metadata_unchanged": bool(inventory.get("observed_root_metadata_unchanged")),
        "operational_database_unchanged": inventory.get("operational_database_unchanged"),
        "acceptance_gate_status": inventory.get("acceptance_gate_status"),
        "privacy": {
            "contains_private_values": False,
            "raw_filenames_emitted": 0,
            "financial_rows_emitted": 0,
            "account_identifiers_emitted": 0,
            "absolute_private_paths_emitted": 0,
            "credentials_emitted": 0,
        },
    }
    assert_public_safe_payload(payload)
    return payload


def build_metric_computability_matrix(manifest: Mapping[str, Any]) -> dict[str, Any]:
    sources = {str(item["source_id"]): item for item in manifest["sources"]}
    ready = {source_id for source_id, item in sources.items() if item.get("status") == "ready"}
    definitions = (
        (
            "consumption_classification",
            "消费分类输入",
            None,
            ("SRC-TRANSACTIONS-ALIPAY",),
            ("S3-P2-T1", "S3-P2-T2", "S3-P2-T3", "S3-P2-T4", "S3-P3-T2"),
            "交易 source input 已可用，但标准化、关联组、经济事件、幂等账本与对账合同尚未完成。",
        ),
        (
            "consumption_outflow_cny",
            "消费总流出金额（CNY）",
            "CNY",
            ("SRC-TRANSACTIONS-ALIPAY", "SRC-FX-SNAPSHOT"),
            (
                "S2-P2-T1", "S2-P2-T2", "S2-P2-T3",
                "S3-P2-T1", "S3-P2-T2", "S3-P2-T3", "S3-P2-T4", "S3-P3-T2",
                "S5-P1-T1", "S5-P1-T2", "S5-P1-T3", "S5-P2-T1",
            ),
            "交易已存在，但 CNY 口径仍需 Phase 2.2 的生产 FX snapshot 与时间真相。",
        ),
        (
            "cash_balance_cny",
            "现金余额",
            "CNY",
            ("SRC-ACCOUNT-BALANCES", "SRC-TRANSACTIONS-ALIPAY", "SRC-FX-SNAPSHOT"),
            (
                "S2-P2-T1", "S2-P2-T2", "S2-P2-T3",
                "S3-P2-T2", "S3-P2-T3", "S3-P2-T4", "S3-P3-T2",
                "S4-P1-T1", "S4-P1-T2", "S4-P1-T3", "S4-P3-T1", "S4-P3-T2",
                "S5-P2-T2",
            ),
            "缺少期初/期末账户余额、转账对账与生产 FX；流水不能证明现金余额。",
        ),
        (
            "investment_market_value_cny",
            "投资市值",
            "CNY",
            ("SRC-HOLDINGS", "SRC-MARKET-PRICES", "SRC-FX-SNAPSHOT"),
            (
                "S2-P2-T1", "S2-P2-T2", "S2-P2-T3",
                "S3-P2-T4", "S3-P3-T2",
                "S4-P2-T1", "S4-P2-T2", "S4-P2-T3", "S4-P2-T4",
                "S4-P3-T1", "S4-P3-T2", "S5-P2-T3",
            ),
            "缺少真实持仓、价格与生产 FX；流水不能证明持仓或市值。",
        ),
        (
            "net_worth_cny",
            "净资产",
            "CNY",
            (
                "SRC-ACCOUNT-BALANCES",
                "SRC-LIABILITIES",
                "SRC-HOLDINGS",
                "SRC-MARKET-PRICES",
                "SRC-FX-SNAPSHOT",
            ),
            (
                "S2-P2-T1", "S2-P2-T2", "S2-P2-T3",
                "S3-P2-T2", "S3-P2-T3", "S3-P2-T4", "S3-P3-T2",
                "S4-P1-T1", "S4-P1-T2", "S4-P1-T3",
                "S4-P2-T1", "S4-P2-T2", "S4-P2-T3", "S4-P2-T4",
                "S4-P3-T1", "S4-P3-T2", "S5-P2-T2",
            ),
            "缺少余额、负债、持仓、价格与生产 FX；8815 条交易流水不等于净资产输入。",
        ),
    )
    metrics: list[dict[str, Any]] = []
    for metric_id, label, currency, required, required_contracts, reason in definitions:
        missing = [source_id for source_id in required if source_id not in ready]
        missing_contracts = list(required_contracts)
        computable = not missing and not missing_contracts
        metrics.append(
            {
                "metric_id": metric_id,
                "label": label,
                "computability": "computable_from_available_sources" if computable else "blocked_missing_dependencies",
                "source_inputs_available": not missing,
                "value": None,
                "currency": currency,
                "required_source_ids": list(required),
                "available_source_ids": [source_id for source_id in required if source_id in ready],
                "missing_source_ids": missing,
                "required_contract_task_ids": list(required_contracts),
                "satisfied_contract_task_ids": [],
                "missing_contract_task_ids": missing_contracts,
                "blocking_reason_zh": None if computable else reason,
                "no_false_zero": True,
            }
        )
    payload = {
        "schema": "PFIV025MetricComputabilityMatrixV1",
        "version": VERSION,
        "stage": STAGE,
        "phase": "2.1",
        "acceptance_id": ACCEPTANCE_ID,
        "source_manifest_observed_at": manifest.get("observed_at"),
        "transactions_available_is_not_balance_or_holdings_proof": True,
        "metric_values_computed_in_phase_2_1": False,
        "metrics": metrics,
    }
    assert_public_safe_payload(payload)
    return payload


def assert_public_safe_payload(payload: Any) -> None:
    _walk_public_payload(payload)
    rendered = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    lowered = rendered.lower()
    forbidden_fragments = ("/users/", "file:///", "begin private key", "access_token", "refresh_token")
    if any(fragment in lowered for fragment in forbidden_fragments) or _contains_credential_value(rendered):
        raise ValueError("private_or_secret_content_in_public_payload")


def build_privacy_scan_report(project_root: str | Path, observed_at: str) -> str:
    return build_public_artifact_scan_report(
        project_root,
        observed_at,
        inputs=_PRIVACY_SCAN_INPUTS,
        scanner_name="pfi-v025-public-artifact-scan-v3",
        scan_command=(
            "PYTHONDONTWRITEBYTECODE=1 PFI/.venv/bin/python -B -m pytest "
            "-p no:cacheprovider PFI/tests/test_v025_stage2_source_manifest.py "
            "-q -k privacy_scan_is_deterministic"
        ),
    )


def build_public_artifact_scan_report(
    project_root: str | Path,
    observed_at: str,
    *,
    inputs: Iterable[str],
    scanner_name: str,
    scan_command: str,
) -> str:
    _validate_observed_at(observed_at)
    if not scanner_name or any(character in scanner_name for character in "\r\n="):
        raise ValueError("invalid_scanner_name")
    if not scan_command or any(character in scan_command for character in "\r\n"):
        raise ValueError("invalid_scan_command")
    repo_root, _ = _resolve_roots(project_root)
    counts = {
        "absolute_private_paths": 0,
        "raw_filenames": 0,
        "financial_row_values": 0,
        "account_identifiers": 0,
        "credentials": 0,
        "sqlite_table_names": 0,
        "finder_operations": 0,
        "source_mutations": 0,
        "financial_fixture_fallback": 0,
    }
    scanned_inputs: list[tuple[str, str]] = []
    for raw_relative in inputs:
        relative = str(raw_relative)
        if not relative or relative.startswith("/") or ".." in Path(relative).parts:
            raise ValueError("invalid_scan_input")
        target = repo_root / relative
        raw = target.read_bytes()
        text = raw.decode("utf-8")
        scanned_inputs.append((relative, hashlib.sha256(raw).hexdigest()))
        _accumulate_privacy_violations(counts, target, text)

    _assert_privacy_counts_clean(counts)
    lines = [
        "PASS",
        f"scanner={scanner_name}",
        f"observed_at={observed_at}",
        f"input_count={len(scanned_inputs)}",
    ]
    lines.extend(f"input={relative}|sha256:{digest}" for relative, digest in scanned_inputs)
    lines.extend(f"{key}={value}" for key, value in counts.items())
    lines.extend(
        [
            f"scan_command={scan_command}",
            "generation_contract=fixed_input_list_semantic_and_text_recompute",
            "self_scan_excluded=true",
        ]
    )
    return "\n".join(lines) + "\n"


def _accumulate_privacy_violations(counts: dict[str, int], target: Path, text: str) -> None:
    lower = text.lower()
    counts["absolute_private_paths"] += lower.count("/users/") + lower.count("file:///")
    counts["credentials"] += len(_CREDENTIAL_ASSIGNMENT_RE.findall(text))
    counts["credentials"] += len(_BEARER_CREDENTIAL_RE.findall(text))
    counts["credentials"] += lower.count("begin private key")
    counts["sqlite_table_names"] += sum(lower.count(name.lower()) for name in _KNOWN_DB_TABLES)
    counts["finder_operations"] += sum(
        lower.count(marker)
        for marker in ("open -a finder", 'tell application "finder"', "finder_activate", "finder_reveal")
    )
    counts["financial_row_values"] += len(
        re.findall(r"(?:CNY|AUD|USD|RMB|¥|\$)\s*[-+]?\d+(?:[,.]\d+)*", text)
    )

    if target.suffix != ".json":
        return
    payload = json.loads(text)
    for key, value in _walk_key_values(payload):
        normalized = key.lower()
        if normalized in _FORBIDDEN_CREDENTIAL_KEYS:
            counts["credentials"] += 1
        if isinstance(value, str) and _contains_credential_value(value):
            counts["credentials"] += 1
        if normalized in {"raw_filename", "raw_path", "transactions_path"}:
            counts["raw_filenames"] += 1
        if normalized in {"account_id", "account_number"}:
            counts["account_identifiers"] += 1
        if normalized in {"row", "rows", "transaction_details", "transactions"}:
            counts["financial_row_values"] += 1
        if normalized == "value" and value is not None:
            counts["financial_row_values"] += 1
        if normalized in {"finder_used", "finder_operation_performed"} and value is True:
            counts["finder_operations"] += 1
        if normalized in {
            "mutation_attempted",
            "migration_performed",
            "source_mutation_performed",
            "financial_data_changed",
            "database_changed",
        } and value is True:
            counts["source_mutations"] += 1
        if normalized in {"financial_fixture_fallback", "financial_fixture_fallback_used"} and value is True:
            counts["financial_fixture_fallback"] += 1
        if normalized in {"raw_filenames_emitted", "account_identifiers_emitted"} and isinstance(value, int):
            bucket = "raw_filenames" if normalized.startswith("raw_") else "account_identifiers"
            counts[bucket] += max(value, 0)
        if normalized in {"credentials_emitted", "row_values_emitted", "table_names_emitted"} and isinstance(value, int):
            bucket = {
                "credentials_emitted": "credentials",
                "row_values_emitted": "financial_row_values",
                "table_names_emitted": "sqlite_table_names",
            }[normalized]
            counts[bucket] += max(value, 0)


def _walk_key_values(value: Any) -> Iterable[tuple[str, Any]]:
    if isinstance(value, Mapping):
        for key, item in value.items():
            yield str(key), item
            yield from _walk_key_values(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _walk_key_values(item)


def _walk_public_payload(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key).lower() in _FORBIDDEN_PUBLIC_KEYS:
                raise ValueError("forbidden_public_key")
            _walk_public_payload(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _walk_public_payload(item)
        return
    if isinstance(value, str):
        if value.startswith("/"):
            raise ValueError("absolute_path_in_public_payload")
        if _contains_credential_value(value):
            raise ValueError("credential_value_in_public_payload")


def _contains_credential_value(value: str) -> bool:
    return bool(_CREDENTIAL_ASSIGNMENT_RE.search(value) or _BEARER_CREDENTIAL_RE.search(value))


def _assert_privacy_counts_clean(counts: Mapping[str, int]) -> None:
    if any(int(value) != 0 for value in counts.values()):
        raise ValueError("privacy_scan_failed")


def _validate_observed_at(observed_at: str) -> None:
    if not _OBSERVED_AT_RE.fullmatch(observed_at):
        raise ValueError("invalid_privacy_observed_at")
    try:
        parsed = datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("invalid_privacy_observed_at") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("invalid_privacy_observed_at")


def _source(
    *,
    source_id: str,
    label: str,
    source_type: str,
    capabilities: Iterable[str],
    path_alias: str,
    parser_version: str | None,
    status: str,
    record_count: int | None,
    coverage: Mapping[str, str | None],
    as_of: str | None,
    content_hash: str | None,
    blocking_reason_zh: str | None,
    root_id: str | None,
    observation_mode: str,
    source_role: str,
    resolution_task_ids: Iterable[str],
) -> dict[str, Any]:
    if status not in SOURCE_STATUS_ENUM:
        raise ValueError("unsupported_source_status")
    return {
        "source_id": source_id,
        "label": label,
        "source_type": source_type,
        "capabilities": list(capabilities),
        "path_alias": path_alias,
        "parser_version": parser_version,
        "status": status,
        "record_count": record_count,
        "coverage": {"start": coverage.get("start"), "end": coverage.get("end")},
        "as_of": as_of,
        "content_hash": content_hash,
        "blocking_reason_zh": blocking_reason_zh,
        "root_id": root_id,
        "observation_mode": observation_mode,
        "source_role": source_role,
        "resolution_task_ids": list(resolution_task_ids),
    }


def _source_from_definition(
    definition: Mapping[str, Any],
    *,
    status: str,
    record_count: int | None,
    coverage: Mapping[str, str | None],
    as_of: str | None,
    content_hash: str | None,
    blocking_reason_zh: str | None,
) -> dict[str, Any]:
    return _source(
        source_id=str(definition["source_id"]),
        label=str(definition["label"]),
        source_type=str(definition["source_type"]),
        capabilities=tuple(str(item) for item in definition["capabilities"]),
        path_alias=str(definition["path_alias"]),
        parser_version=(
            str(definition["parser_version"])
            if definition.get("parser_version") is not None
            else None
        ),
        status=status,
        record_count=record_count,
        coverage=coverage,
        as_of=as_of,
        content_hash=content_hash,
        blocking_reason_zh=blocking_reason_zh,
        root_id=str(definition["root_id"]),
        observation_mode=str(definition["observation_mode"]),
        source_role=str(definition["source_role"]),
        resolution_task_ids=tuple(str(item) for item in definition["resolution_task_ids"]),
    )


def _load_source_registry() -> dict[str, Any]:
    payload = json.loads(SOURCE_REGISTRY_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("invalid_source_registry")
    sources = payload.get("sources")
    if not isinstance(sources, list) or not all(isinstance(item, dict) for item in sources):
        raise ValueError("invalid_source_registry_sources")
    source_ids = tuple(str(item.get("source_id")) for item in sources)
    if source_ids != EXPECTED_SOURCE_IDS or len(set(source_ids)) != len(source_ids):
        raise ValueError("source_registry_id_order_mismatch")
    if payload.get("version") != VERSION:
        raise ValueError("source_registry_version_mismatch")
    assert_public_safe_payload(payload)
    return payload


def _blocked_database_probe(status: str = "source_missing") -> dict[str, Any]:
    return {
        "status": status,
        "database_path_redacted": True,
        "candidate_count": 0,
        "query_mode": "mode=ro",
        "sqlite_header_mode": None,
        "query_only": True,
        "authorizer_deny_write": True,
        "quiescence_gate": "sqlite_shared_read_transaction",
        "sidecar_check": "before_and_after",
        "sidecars_present": False,
        "sidecar_count_before": None,
        "sidecar_count_after": None,
        "quick_check": None,
        "known_table_count": None,
        "record_count": None,
        "coverage": {"start": None, "end": None},
        "as_of": None,
        "content_hash": None,
        "content_hash_scheme": _DATABASE_HASH_SCHEME,
        "before": None,
        "after": None,
        "unchanged_before_after": None,
        "row_values_emitted": 0,
        "table_names_emitted": 0,
        "permission_risk": None,
    }


def _probe_operational_database(data_home: Path) -> dict[str, Any]:
    base = _blocked_database_probe()
    operational_dir = data_home / "private" / "operational"
    expected = operational_dir / "pfi.sqlite"
    chain_status = _path_chain_status(expected)
    if chain_status == "permission_denied":
        return {**base, "status": "permission_denied"}
    if chain_status == "invalid_type":
        return {**base, "status": "blocked_invalid_operational_directory"}
    if chain_status == "symlink":
        return {**base, "status": "blocked_symlink"}
    try:
        operational_info = operational_dir.lstat()
    except FileNotFoundError:
        return base
    except PermissionError:
        return {**base, "status": "permission_denied"}
    if not stat.S_ISDIR(operational_info.st_mode) or stat.S_ISLNK(operational_info.st_mode):
        return {**base, "status": "blocked_invalid_operational_directory"}
    try:
        with os.scandir(operational_dir) as entries:
            candidates = [operational_dir / entry.name for entry in entries if entry.name.endswith(".sqlite")]
    except PermissionError:
        return {**base, "status": "permission_denied"}
    except OSError:
        return {**base, "status": "blocked_integrity_check"}
    base["candidate_count"] = len(candidates)
    if not candidates:
        return base
    if len(candidates) != 1:
        return {**base, "status": "blocked_candidate_conflict"}
    if candidates[0] != expected:
        return {**base, "status": "blocked_candidate_conflict"}
    try:
        expected_info = expected.lstat()
    except FileNotFoundError:
        return {**base, "status": "blocked_candidate_changed"}
    except PermissionError:
        return {**base, "status": "permission_denied"}
    if not stat.S_ISREG(expected_info.st_mode) or stat.S_ISLNK(expected_info.st_mode):
        return {**base, "status": "blocked_non_regular_database"}
    try:
        sidecar_count_before = _sidecar_count(expected)
    except PermissionError:
        return {**base, "status": "permission_denied"}
    except OSError:
        return {**base, "status": "blocked_integrity_check"}
    if sidecar_count_before:
        return {
            **base,
            "status": "blocked_sidecar_present",
            "sidecars_present": True,
            "sidecar_count_before": sidecar_count_before,
        }

    try:
        before = _file_fingerprint(expected)
        operational_before = _directory_fingerprint(operational_dir)
    except PermissionError:
        return {**base, "status": "permission_denied"}
    except OSError:
        return {**base, "status": "blocked_integrity_check"}
    if before is None or operational_before is None:
        return {**base, "status": "blocked_integrity_check"}

    try:
        header_mode = _sqlite_header_mode(expected)
    except PermissionError:
        return {**base, "status": "permission_denied", "before": before}
    except OSError:
        return {**base, "status": "blocked_integrity_check", "before": before}
    if header_mode == "wal":
        return {
            **base,
            "status": "blocked_wal_header",
            "sqlite_header_mode": header_mode,
            "before": before,
        }
    if header_mode != "rollback_journal":
        return {
            **base,
            "status": "blocked_integrity_check",
            "sqlite_header_mode": header_mode,
            "before": before,
        }

    quick_check: str | None = None
    known_table_count: int | None = None
    try:
        uri = f"file:{quote(str(expected))}?mode=ro"
        connection = sqlite3.connect(uri, uri=True, timeout=0, isolation_level=None)
        try:
            connection.enable_load_extension(False)
            connection.set_progress_handler(lambda: 0, 10_000)
            connection.set_authorizer(_sqlite_read_only_authorizer)
            connection.execute("PRAGMA query_only=ON")
            connection.execute("BEGIN")
            quick_row = connection.execute("PRAGMA quick_check").fetchone()
            quick_check = "ok" if quick_row and str(quick_row[0]) == "ok" else "not_ok"
            placeholders = ",".join("?" for _ in _KNOWN_DB_TABLES)
            known_table_count = int(
                connection.execute(
                    f"SELECT COUNT(*) FROM sqlite_schema WHERE type='table' AND name IN ({placeholders})",
                    _KNOWN_DB_TABLES,
                ).fetchone()[0]
            )
        finally:
            connection.close()
    except (OSError, sqlite3.Error):
        return {**base, "status": "blocked_integrity_check", "before": before}

    try:
        after = _file_fingerprint(expected)
        operational_after = _directory_fingerprint(operational_dir)
        sidecar_count_after = _sidecar_count(expected)
    except PermissionError:
        return {**base, "status": "permission_denied", "before": before}
    except OSError:
        return {**base, "status": "blocked_integrity_check", "before": before}
    unchanged = (
        before == after
        and operational_before == operational_after
        and sidecar_count_before == 0
        and sidecar_count_after == 0
    )
    if not unchanged:
        return {
            **base,
            "status": "blocked_changed_during_probe",
            "quick_check": "ok" if quick_check == "ok" else "not_ok",
            "known_table_count": known_table_count,
            "sidecars_present": bool(sidecar_count_before or sidecar_count_after),
            "sidecar_count_before": sidecar_count_before,
            "sidecar_count_after": sidecar_count_after,
            "before": before,
            "after": after,
            "unchanged_before_after": False,
        }
    if quick_check != "ok":
        return {
            **base,
            "status": "blocked_integrity_check",
            "quick_check": "not_ok",
            "known_table_count": known_table_count,
            "sidecar_count_before": sidecar_count_before,
            "sidecar_count_after": sidecar_count_after,
            "before": before,
            "after": after,
            "unchanged_before_after": True,
        }
    return {
        **base,
        "status": "ready_metadata_only",
        "sqlite_header_mode": header_mode,
        "quick_check": "ok",
        "known_table_count": known_table_count,
        "content_hash": before["content_hash"],
        "sidecar_count_before": sidecar_count_before,
        "sidecar_count_after": sidecar_count_after,
        "operational_directory_unchanged": operational_before == operational_after,
        "candidate_set_unchanged": operational_before.get("candidate_identities") == operational_after.get("candidate_identities"),
        "permission_risk": _private_permission_risk(before.get("mode")),
        "before": before,
        "after": after,
        "unchanged_before_after": True,
    }


def _sqlite_read_only_authorizer(
    action: int,
    argument_1: str | None,
    argument_2: str | None,
    database_name: str | None,
    trigger_name: str | None,
) -> int:
    del argument_2, database_name, trigger_name
    allowed = {
        getattr(sqlite3, "SQLITE_SELECT", -1),
        getattr(sqlite3, "SQLITE_READ", -1),
        getattr(sqlite3, "SQLITE_FUNCTION", -1),
    }
    if action in allowed:
        return sqlite3.SQLITE_OK
    if action == getattr(sqlite3, "SQLITE_PRAGMA", -2) and str(argument_1 or "").lower() in {"query_only", "quick_check"}:
        return sqlite3.SQLITE_OK
    if action == getattr(sqlite3, "SQLITE_TRANSACTION", -3) and str(argument_1 or "").upper() == "BEGIN":
        return sqlite3.SQLITE_OK
    return sqlite3.SQLITE_DENY


def _git_surface(repo_root: Path, git_ref: str) -> dict[str, Any]:
    base = {
        "status": "source_missing",
        "storage_mode": "git_object_read_only",
        "tree_object_available": False,
        "file_count": 0,
        "bytes": 0,
        "transaction_count": None,
        "coverage_start": None,
        "coverage_end": None,
        "as_of": None,
        "content_hash": None,
        "content_hash_scheme": _GIT_HASH_SCHEME,
        "path_names_emitted": 0,
        "raw_rows_emitted": 0,
    }
    try:
        tree_hash = _git(repo_root, "rev-parse", f"{git_ref}:MetaDatabase/PFI").decode().strip()
        listing = _git(repo_root, "ls-tree", "-r", "-z", "--long", git_ref, "--", "MetaDatabase/PFI")
        entries = _parse_git_tree(listing)
        manifest_raw = _git(repo_root, "show", f"{git_ref}:MetaDatabase/PFI/alipay_daily/processed/alipay_import_manifest.json")
        metadata = json.loads(manifest_raw.decode("utf-8"))
        content_hash = _hash_git_blobs(repo_root, entries)
        transaction_count = int(metadata["transaction_count"])
        coverage_start = str(metadata["date_start"])
        coverage_end = str(metadata["date_end"])
    except (KeyError, ValueError, UnicodeError, json.JSONDecodeError, subprocess.CalledProcessError):
        return base
    return {
        **base,
        "status": "ready",
        "tree_object_available": True,
        "tree_hash": tree_hash,
        "file_count": len(entries),
        "bytes": sum(size for _, _, _, size in entries),
        "transaction_count": transaction_count,
        "coverage_start": coverage_start,
        "coverage_end": coverage_end,
        "as_of": coverage_end,
        "content_hash": content_hash,
    }


def _parse_git_tree(raw: bytes) -> list[tuple[bytes, bytes, str, int]]:
    entries: list[tuple[bytes, bytes, str, int]] = []
    for item in raw.split(b"\0"):
        if not item:
            continue
        metadata, path = item.split(b"\t", 1)
        mode, kind, oid, size = metadata.split(b" ", 3)
        if kind != b"blob":
            continue
        entries.append((mode, path, oid.decode("ascii"), int(size)))
    return sorted(entries, key=lambda item: item[1])


def _hash_git_blobs(repo_root: Path, entries: Iterable[tuple[bytes, bytes, str, int]]) -> str:
    digest = hashlib.sha256()
    digest.update(b"PFI_GIT_TREE_BLOB_V2\0")
    for mode, path, oid, size in entries:
        blob = _git(repo_root, "cat-file", "blob", oid)
        if len(blob) != size:
            raise ValueError("git_blob_size_mismatch")
        for field in (mode, path, oid.encode("ascii"), str(size).encode("ascii"), blob):
            digest.update(len(field).to_bytes(8, "big"))
            digest.update(field)
    return "sha256:" + digest.hexdigest()


def _git(repo_root: Path, *args: str) -> bytes:
    return subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=True,
        capture_output=True,
    ).stdout


def _root_fingerprint(path: Path) -> dict[str, Any]:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return {"exists": False}
    except PermissionError:
        return {"exists": True, "readable": False}
    except OSError:
        return {"exists": True, "readable": False, "path_error": True}
    if stat.S_ISLNK(info.st_mode):
        return {"exists": True, "symlink": True}
    kind = "directory" if stat.S_ISDIR(info.st_mode) else "regular" if stat.S_ISREG(info.st_mode) else "other"
    readable = True
    if kind == "directory":
        try:
            with os.scandir(path) as entries:
                next(entries, None)
        except (PermissionError, OSError):
            readable = False
    return {
        "exists": True,
        "readable": readable,
        "symlink": False,
        "kind": kind,
        "mode": format(stat.S_IMODE(info.st_mode), "04o"),
        "device": info.st_dev,
        "inode": info.st_ino,
        "size": info.st_size,
        "mtime_ns": info.st_mtime_ns,
        "ctime_ns": info.st_ctime_ns,
    }


def _directory_fingerprint(path: Path) -> dict[str, Any] | None:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return None
    if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode):
        return None
    identities: list[tuple[int, int, int, int, int]] = []
    for candidate in path.glob("*.sqlite"):
        child = candidate.lstat()
        if not stat.S_ISREG(child.st_mode) or stat.S_ISLNK(child.st_mode):
            continue
        identities.append(
            (
                child.st_dev,
                child.st_ino,
                child.st_size,
                child.st_mtime_ns,
                child.st_ctime_ns,
            )
        )
    return {
        "device": info.st_dev,
        "inode": info.st_ino,
        "mtime_ns": info.st_mtime_ns,
        "ctime_ns": info.st_ctime_ns,
        "candidate_identities": tuple(sorted(identities)),
    }


def _sidecar_count(database: Path) -> int:
    prefix = database.name + "-"
    with os.scandir(database.parent) as entries:
        return sum(1 for entry in entries if entry.name.startswith(prefix))


def _file_fingerprint(path: Path) -> dict[str, Any] | None:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return None
    if not stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode):
        return None
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return {
        "device": info.st_dev,
        "inode": info.st_ino,
        "size": info.st_size,
        "mtime_ns": info.st_mtime_ns,
        "ctime_ns": info.st_ctime_ns,
        "mode": format(stat.S_IMODE(info.st_mode), "04o"),
        "content_hash": "sha256:" + digest.hexdigest(),
    }


def _sqlite_header_mode(path: Path) -> str:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    with os.fdopen(descriptor, "rb") as stream:
        header = stream.read(20)
    if len(header) != 20 or header[:16] != b"SQLite format 3\x00":
        return "invalid"
    write_version, read_version = header[18], header[19]
    if (write_version, read_version) == (1, 1):
        return "rollback_journal"
    if 2 in {write_version, read_version}:
        return "wal"
    return "invalid"


def _sha256_file(path: Path) -> str:
    fingerprint = _file_fingerprint(path)
    if fingerprint is None:
        raise ValueError("required_file_missing")
    return str(fingerprint["content_hash"])


def _private_root_status(path: Path, repo_root: Path, fingerprint: Mapping[str, Any]) -> str:
    chain_status = _path_chain_status(path)
    if chain_status == "permission_denied":
        return "permission_denied"
    if chain_status == "invalid_type":
        return "blocked_invalid_root_type"
    if chain_status == "symlink":
        return "blocked_symlink_component"
    if _is_relative_to(path, repo_root):
        return "blocked_inside_public_git"
    if not fingerprint.get("exists"):
        return "source_missing"
    if not fingerprint.get("readable", True):
        return "permission_denied"
    if fingerprint.get("kind") != "directory":
        return "blocked_invalid_root_type"
    return "canonical_active"


def _path_chain_status(path: Path) -> str:
    absolute = _absolute_lexical_path(path)
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current = current / part
        try:
            info = current.lstat()
        except FileNotFoundError:
            break
        except PermissionError:
            return "permission_denied"
        except (NotADirectoryError, OSError):
            return "invalid_type"
        if stat.S_ISLNK(info.st_mode):
            return "symlink"
        if current != absolute and not stat.S_ISDIR(info.st_mode):
            return "invalid_type"
    return "clear"


def _private_permission_risk(mode: Any) -> str | None:
    if not isinstance(mode, str):
        return None
    try:
        value = int(mode, 8)
    except ValueError:
        return "permission_mode_unparseable"
    if value & 0o077:
        return "group_or_other_permissions_present_no_permission_change_in_phase_2_1"
    return None


def _same_target(left: Path, right: Path) -> bool:
    try:
        return left.samefile(right)
    except (FileNotFoundError, OSError):
        return left == right


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _absolute_lexical_path(value: str | Path) -> Path:
    return Path(os.path.abspath(os.path.expanduser(os.fspath(value))))


def _resolve_roots(project_root: str | Path) -> tuple[Path, Path]:
    root = Path(project_root).expanduser().resolve()
    if (root / "PFI" / "src" / "pfi_v02").is_dir():
        return root, root / "PFI"
    if (root / "src" / "pfi_v02").is_dir():
        return root.parent, root
    raise ValueError("invalid_pfi_project_root")


def _require_mapping(payload: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = payload.get(key)
    if not isinstance(value, Mapping):
        raise ValueError("invalid_inventory_mapping")
    return value


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
