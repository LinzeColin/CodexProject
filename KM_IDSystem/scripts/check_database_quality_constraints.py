"""Validate the static IDS STAGE-036 database-quality constraint contract.

The checker reads tracked SQL and JSON contracts and prints JSON to stdout. It
does not connect to PostgreSQL, inspect database rows or raw metadata, execute a
migration, seed state values, or write runtime outputs.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any


SCHEMA_VERSION = "ids.stage036.database_quality_constraints.phase2.v1"
INDEX_SCHEMA_VERSION = "ids.stage036.database_quality_constraints.index.v1"
STAGE = "STAGE-036"
TASK_ID = "IDS-V0_1-STAGE036-P2"
ACCEPTANCE_ID = "ACC-STAGE-036"
CONTRACT_ID = "ids_stage036_database_quality_constraints_static_slice"
MIGRATION_ID = "ids_stage036_002_database_quality_constraints"
RAW_METADATA_ROOT = "/Users/linzezhang/Downloads/IDS_MetaData"
BLOCKED_PENDING_PROFILE = "BLOCKED_PENDING_OWNER_AUTHORIZED_REAL_DATA_PROFILE"
BLOCKED_INVALID_CONTRACT = "BLOCKED_INVALID_QUALITY_CONSTRAINT_CONTRACT"
INVALID_CONTRACT_STATE = "INVALID_QUALITY_CONSTRAINT_CONTRACT"

ROOT = Path(__file__).resolve().parents[1]
PURSUE_ROOT = ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
QUALITY_ROOT = PURSUE_ROOT / "database_quality_constraints"
INDEX_PATH = QUALITY_ROOT / "stage036_database_quality_constraints_index.json"
MIGRATION_PATH = QUALITY_ROOT / "002_database_quality_constraints.sql"
CONTROL_SCHEMA_PATH = (
    PURSUE_ROOT / "postgresql_control_plane" / "001_control_plane_schema.sql"
)

EXPECTED_SOURCE_REFS = {
    "phase1_scope_ref": "../STAGE036_PHASE1_SCOPE_BOUNDARY.md",
    "phase2_slice_ref": "../STAGE036_PHASE2_DATABASE_QUALITY_CONSTRAINTS_SLICE.md",
    "stage030_control_plane_schema_ref": "../postgresql_control_plane/001_control_plane_schema.sql",
    "stage030_control_plane_index_ref": "../postgresql_control_plane/control_plane_schema_index.json",
    "stage031_migration_safety_index_ref": "../schema_migration_safety/stage031_migration_safety_index.json",
    "stage032_connection_pool_index_ref": "../database_connection_pool/stage032_connection_pool_index.json",
    "stage033_database_size_guard_index_ref": "../database_size_guard/stage033_database_size_guard_index.json",
    "stage034_data_retention_table_index_ref": "../data_retention_table/stage034_data_retention_table_index.json",
    "stage035_database_recovery_smoke_index_ref": "../database_recovery_smoke/stage035_database_recovery_smoke_index.json",
    "migration_sql_ref": "002_database_quality_constraints.sql",
    "raw_data_boundary_ref": "../IDS_METADATA_RAW_DATA_BOUNDARY.md",
    "phase2_checker_ref": "../../../../scripts/check_database_quality_constraints.py",
}

EXPECTED_TABLES = {
    "ids_metadata_sources",
    "ids_jobs",
    "ids_documents",
    "ids_chunks",
    "ids_evidence_records",
    "ids_audit_events",
    "ids_index_versions",
    "ids_schema_migrations",
}

EXPECTED_FOREIGN_KEYS = {
    "ids_documents.source_id -> ids_metadata_sources.source_id",
    "ids_chunks.document_id -> ids_documents.document_id",
    "ids_jobs.parent_job_id -> ids_jobs.job_id",
}

EXPECTED_CANDIDATE_CONSTRAINTS = {
    "uq_ids_chunks_document_ordinal",
    "chk_ids_metadata_sources_quality_v2",
    "chk_ids_jobs_quality_v2",
    "chk_ids_documents_quality_v2",
    "chk_ids_chunks_quality_v2",
    "chk_ids_evidence_records_quality_v2",
    "chk_ids_audit_events_quality_v2",
    "chk_ids_index_versions_quality_v2",
    "chk_ids_schema_migrations_quality_v2",
}

EXPECTED_PRIMARY_KEYS = {
    "ids_schema_migrations(migration_id)",
    "ids_metadata_sources(source_id)",
    "ids_jobs(job_id)",
    "ids_documents(document_id)",
    "ids_chunks(chunk_id)",
    "ids_evidence_records(evidence_id)",
    "ids_audit_events(audit_id)",
    "ids_index_versions(index_id, index_version)",
}

EXPECTED_CANDIDATE_SPECS = {
    "uq_ids_chunks_document_ordinal": {
        "constraint_class": "COMPOSITE_UNIQUENESS",
        "table": "ids_chunks",
        "columns": ("document_id", "chunk_ordinal"),
        "validation_kind": "duplicate_count_must_be_zero",
    },
    "chk_ids_metadata_sources_quality_v2": {
        "constraint_class": "NOT_NULL_REQUIRED+CROSS_FIELD_CONSISTENCY",
        "table": "ids_metadata_sources",
        "columns": (
            "source_id",
            "source_uri",
            "source_boundary",
            "storage_class",
            "source_size_bytes",
            "payload_size_bytes",
            "is_raw_content_stored",
        ),
        "validation_kind": "nonblank_nonnegative_bounded_no_raw",
    },
    "chk_ids_jobs_quality_v2": {
        "constraint_class": "NOT_NULL_REQUIRED+CROSS_FIELD_CONSISTENCY",
        "table": "ids_jobs",
        "columns": (
            "job_id",
            "job_type",
            "job_state",
            "retry_count",
            "max_retries",
            "connection_pool_size",
            "payload_size_bytes",
        ),
        "validation_kind": "nonblank_retry_pool_payload_bounds",
    },
    "chk_ids_documents_quality_v2": {
        "constraint_class": "NOT_NULL_REQUIRED+CROSS_FIELD_CONSISTENCY",
        "table": "ids_documents",
        "columns": (
            "document_id",
            "source_id",
            "source_uri",
            "parser_state",
            "payload_size_bytes",
        ),
        "validation_kind": "nonblank_bounded_payload",
    },
    "chk_ids_chunks_quality_v2": {
        "constraint_class": "NOT_NULL_REQUIRED+CROSS_FIELD_CONSISTENCY",
        "table": "ids_chunks",
        "columns": (
            "chunk_id",
            "document_id",
            "parser_state",
            "chunk_ordinal",
            "byte_start",
            "byte_end",
            "payload_size_bytes",
        ),
        "validation_kind": "nonblank_ordinal_offsets_payload_consistency",
    },
    "chk_ids_evidence_records_quality_v2": {
        "constraint_class": "NOT_NULL_REQUIRED+STATUS_VALUESET_INTEGRITY",
        "table": "ids_evidence_records",
        "columns": (
            "evidence_id",
            "evidence_kind",
            "fact_level",
            "source_ref",
            "validation_state",
        ),
        "validation_kind": "nonblank_and_existing_fact_level_check",
    },
    "chk_ids_audit_events_quality_v2": {
        "constraint_class": "NOT_NULL_REQUIRED+STATUS_VALUESET_INTEGRITY",
        "table": "ids_audit_events",
        "columns": (
            "audit_id",
            "actor_role",
            "action_type",
            "object_ref",
            "decision_state",
        ),
        "validation_kind": "nonblank_audit_identity_and_state",
    },
    "chk_ids_index_versions_quality_v2": {
        "constraint_class": (
            "NOT_NULL_REQUIRED+STATUS_VALUESET_INTEGRITY+"
            "CROSS_FIELD_CONSISTENCY"
        ),
        "table": "ids_index_versions",
        "columns": (
            "index_id",
            "index_version",
            "index_state",
            "coverage_ref",
            "hot_index_pointer_ref",
            "payload_size_bytes",
        ),
        "validation_kind": "nonblank_existing_state_check_bounded_payload",
    },
    "chk_ids_schema_migrations_quality_v2": {
        "constraint_class": "NOT_NULL_REQUIRED+CROSS_FIELD_CONSISTENCY",
        "table": "ids_schema_migrations",
        "columns": (
            "migration_id",
            "checksum_sha256",
            "dry_run_required",
            "rollback_required",
            "rollback_sql_ref",
            "recovery_checkpoint_ref",
        ),
        "validation_kind": "nonblank_dry_run_rollback_recovery_refs",
    },
}

EXPECTED_CHECK_SQL_CLAUSES = {
    "chk_ids_metadata_sources_quality_v2": (
        "btrim(source_id) <> ''",
        "btrim(source_uri) <> ''",
        "btrim(source_boundary) <> ''",
        "btrim(storage_class) <> ''",
        "source_size_bytes >= 0",
        "payload_size_bytes >= 0",
        "payload_size_bytes <= 1048576",
        "is_raw_content_stored = false",
    ),
    "chk_ids_jobs_quality_v2": (
        "btrim(job_id) <> ''",
        "btrim(job_type) <> ''",
        "btrim(job_state) <> ''",
        "retry_count >= 0",
        "max_retries >= 0",
        "retry_count <= max_retries",
        "connection_pool_size >= 1",
        "connection_pool_size <= 10",
        "payload_size_bytes >= 0",
        "payload_size_bytes <= 1048576",
    ),
    "chk_ids_documents_quality_v2": (
        "btrim(document_id) <> ''",
        "btrim(source_id) <> ''",
        "btrim(source_uri) <> ''",
        "btrim(parser_state) <> ''",
        "payload_size_bytes >= 0",
        "payload_size_bytes <= 1048576",
    ),
    "chk_ids_chunks_quality_v2": (
        "btrim(chunk_id) <> ''",
        "btrim(document_id) <> ''",
        "btrim(parser_state) <> ''",
        "chunk_ordinal >= 0",
        "payload_size_bytes >= 0",
        "payload_size_bytes <= 1048576",
        "byte_start is null and byte_end is null",
        "byte_start is not null",
        "byte_end is not null",
        "byte_start >= 0",
        "byte_end >= byte_start",
    ),
    "chk_ids_evidence_records_quality_v2": (
        "btrim(evidence_id) <> ''",
        "btrim(evidence_kind) <> ''",
        "btrim(fact_level) <> ''",
        "btrim(source_ref) <> ''",
        "btrim(validation_state) <> ''",
    ),
    "chk_ids_audit_events_quality_v2": (
        "btrim(audit_id) <> ''",
        "btrim(actor_role) <> ''",
        "btrim(action_type) <> ''",
        "btrim(object_ref) <> ''",
        "btrim(decision_state) <> ''",
    ),
    "chk_ids_index_versions_quality_v2": (
        "btrim(index_id) <> ''",
        "btrim(index_version) <> ''",
        "btrim(index_state) <> ''",
        "btrim(coverage_ref) <> ''",
        "btrim(hot_index_pointer_ref) <> ''",
        "payload_size_bytes >= 0",
        "payload_size_bytes <= 1048576",
    ),
    "chk_ids_schema_migrations_quality_v2": (
        "btrim(migration_id) <> ''",
        "btrim(checksum_sha256) <> ''",
        "btrim(rollback_sql_ref) <> ''",
        "btrim(recovery_checkpoint_ref) <> ''",
        "dry_run_required = true",
        "rollback_required = true",
    ),
}

EXPECTED_CHECK_CONSTRAINTS = EXPECTED_CANDIDATE_CONSTRAINTS - {
    "uq_ids_chunks_document_ordinal"
}

EXPECTED_STABLE_VALUE_CHECKS = {
    "chk_source_storage_class",
    "chk_fact_level",
    "chk_index_state",
}

EXPECTED_STATE_NAMESPACES = {
    "job_type",
    "job_state",
    "parser_state",
    "validation_state",
    "decision_state",
}

EXPECTED_RUNTIME_POLICY_KEYS = {
    "connect_to_postgres",
    "instantiate_connection_pool",
    "query_real_rows",
    "execute_data_profile",
    "execute_migration",
    "execute_constraint_validation",
    "execute_backup",
    "execute_restore",
    "execute_recovery_smoke",
    "write_runtime_outputs",
    "read_raw_metadata",
    "write_raw_metadata",
    "seed_state_values",
    "install_dependencies",
    "start_services",
    "github_upload",
    "app_reinstall",
}

EXPECTED_FORBIDDEN_REAL_DATA_SUBSTITUTES = {
    "fake IDS business data",
    "fake database rows",
    "fake source documents",
    "fabricated data profile",
    "placeholder corpus",
    "fabricated evidence",
    "plaintext secrets",
}

FORBIDDEN_SQL_SECRET_PATTERNS = (
    r"postgres(?:ql)?://",
    r"password\s*=",
    r"api[_-]?key\s*=",
    r"secret\s*=",
)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _strip_sql_comments(sql: str) -> str:
    return re.sub(r"--.*?$|/\*.*?\*/", "", sql, flags=re.MULTILINE | re.DOTALL)


def _normalized_sql(sql: str) -> str:
    return " ".join(_strip_sql_comments(sql).split()).lower()


def _resolve_source_refs(index_path: Path, index: dict[str, Any]) -> dict[str, Path]:
    refs = index.get("source_refs", {})
    if not isinstance(refs, dict):
        return {}
    return {
        key: (index_path.parent / value).resolve()
        for key, value in refs.items()
        if isinstance(key, str) and isinstance(value, str)
    }


def _source_integrity_results(
    index_path: Path, index: dict[str, Any], baseline_schema_path: Path
) -> dict[str, bool]:
    refs = index.get("source_refs", {})
    refs = refs if isinstance(refs, dict) else {}
    resolved = _resolve_source_refs(index_path, index)
    dependency = index.get("dependency_contract", {})
    dependency = dependency if isinstance(dependency, dict) else {}

    required_json_keys = {
        "stage030_control_plane_index_ref",
        "stage031_migration_safety_index_ref",
        "stage032_connection_pool_index_ref",
        "stage033_database_size_guard_index_ref",
        "stage034_data_retention_table_index_ref",
        "stage035_database_recovery_smoke_index_ref",
    }
    dependency_indexes: dict[str, dict[str, Any]] = {}
    if required_json_keys.issubset(resolved) and all(
        resolved[key].is_file() for key in required_json_keys
    ):
        dependency_indexes = {
            key: _load_json(resolved[key]) for key in required_json_keys
        }

    dependency_schema_pairs = {
        "stage030_control_plane_index_ref": "stage030_schema_version",
        "stage031_migration_safety_index_ref": "stage031_schema_version",
        "stage032_connection_pool_index_ref": "stage032_schema_version",
        "stage033_database_size_guard_index_ref": "stage033_schema_version",
        "stage034_data_retention_table_index_ref": "stage034_schema_version",
        "stage035_database_recovery_smoke_index_ref": "stage035_schema_version",
    }
    dependency_schemas_match = bool(dependency_indexes) and all(
        dependency_indexes[index_key].get("schema_version")
        == dependency.get(dependency_key)
        for index_key, dependency_key in dependency_schema_pairs.items()
    )
    stage030 = dependency_indexes.get("stage030_control_plane_index_ref", {})

    return {
        "source_refs_exact": refs == EXPECTED_SOURCE_REFS,
        "source_refs_resolve": (
            set(resolved) == set(EXPECTED_SOURCE_REFS)
            and all(path.is_file() for path in resolved.values())
        ),
        "baseline_schema_path_matches": resolved.get(
            "stage030_control_plane_schema_ref"
        )
        == baseline_schema_path.resolve(),
        "dependency_schema_versions_match": dependency_schemas_match,
        "stage030_migration_identity_matches": (
            stage030.get("migration", {}).get("id")
            == dependency.get("stage030_migration_id")
            == "ids_stage030_001_control_plane"
        ),
        "required_control_plane_tables_match": (
            set(dependency.get("required_control_plane_tables", []))
            == EXPECTED_TABLES
            and set(stage030.get("required_tables", [])) == EXPECTED_TABLES
        ),
    }


def _baseline_schema_results(sql: str) -> dict[str, bool]:
    normalized = _normalized_sql(sql)
    table_presence = {
        table: f"create table if not exists {table}" in normalized
        for table in EXPECTED_TABLES
    }
    foreign_key_patterns = {
        "documents_source_fk": (
            "source_id text not null references ids_metadata_sources(source_id)"
        ),
        "chunks_document_fk": (
            "document_id text not null references ids_documents(document_id)"
        ),
        "jobs_parent_fk": "parent_job_id text references ids_jobs(job_id)",
    }
    return {
        "eight_control_plane_tables_present": all(table_presence.values())
        and len(table_presence) == 8,
        "existing_primary_keys_present": normalized.count("primary key") >= 8,
        "existing_foreign_keys_present": all(
            pattern in normalized for pattern in foreign_key_patterns.values()
        ),
        "stable_value_checks_present": all(
            constraint_id.lower() in normalized
            for constraint_id in EXPECTED_STABLE_VALUE_CHECKS
        ),
        "raw_content_guard_present": (
            "chk_no_raw_content_stored" in normalized
            and "is_raw_content_stored = false" in normalized
        ),
        "payload_upper_bounds_present": normalized.count("<= 1048576") >= 4,
    }


def _candidate_sql_definitions_exact(normalized_sql: str) -> bool:
    unique_pattern = (
        r"alter table ids_chunks add constraint uq_ids_chunks_document_ordinal "
        r"unique \(document_id, chunk_ordinal\)"
    )
    if re.search(unique_pattern, normalized_sql) is None:
        return False

    for constraint_id, clauses in EXPECTED_CHECK_SQL_CLAUSES.items():
        table = EXPECTED_CANDIDATE_SPECS[constraint_id]["table"]
        pattern = (
            rf"alter table {re.escape(str(table))} add constraint "
            rf"{re.escape(constraint_id)} check \((.*?)\) not valid"
        )
        match = re.search(pattern, normalized_sql)
        if match is None or not all(clause in match.group(1) for clause in clauses):
            return False
    return True


def _migration_contract_results(
    sql: str, index: dict[str, Any]
) -> dict[str, bool]:
    uncommented = _strip_sql_comments(sql)
    normalized = " ".join(uncommented.split()).lower()
    migration = index.get("migration_contract", {})
    migration = migration if isinstance(migration, dict) else {}
    registry = index.get("versioned_state_registry", {})
    registry = registry if isinstance(registry, dict) else {}
    up_count = sql.count("-- migrate:up")
    down_count = sql.count("-- migrate:down")
    forbidden_dml = re.search(
        r"\b(?:insert|update|delete|truncate|copy)\b", uncommented, re.I
    )
    secret_free = all(
        re.search(pattern, uncommented, re.I) is None
        for pattern in FORBIDDEN_SQL_SECRET_PATTERNS
    )
    return {
        "migration_identity_matches": (
            migration.get("migration_id") == MIGRATION_ID
            and migration.get("migration_sql_ref")
            == "002_database_quality_constraints.sql"
            and migration.get("mode")
            == "tracked_static_migration_contract_not_executed"
            and migration.get("up_marker_required") is True
            and migration.get("down_marker_required") is True
            and migration.get("on_error_stop_required") is True
            and migration.get("single_transaction_required") is True
            and migration.get("owner_authorized_real_profile_ref_required")
            is True
            and migration.get("backup_checkpoint_ref_required") is True
            and migration.get("rollback_plan_ref_required") is True
            and migration.get("constraint_validation_required") is True
            and MIGRATION_ID in sql
        ),
        "ordered_up_down_markers": (
            up_count == 1
            and down_count == 1
            and sql.index("-- migrate:up") < sql.index("-- migrate:down")
        ),
        "owner_profile_backup_rollback_guards_present": all(
            f"current_setting('{ref}', true)" in normalized
            for ref in (
                "ids.owner_authorized_real_profile_ref",
                "ids.migration_backup_checkpoint_ref",
                "ids.migration_rollback_plan_ref",
            )
        )
        and normalized.count("raise exception 'stage-036 apply blocked:") == 3,
        "state_registry_structure_present": (
            "create table if not exists ids_state_value_registry" in normalized
            and "primary key (state_namespace, state_value)" in normalized
            and "insert into ids_state_value_registry" not in normalized
        ),
        "state_registry_definition_exact": all(
            fragment in normalized
            for fragment in (
                "state_namespace text not null",
                "state_value text not null",
                "introduced_version text not null",
                "retired_version text",
                "is_active boolean not null default true",
                "owner_label_zh text not null",
                "owner_description_zh text",
                "created_at timestamptz not null default now()",
                "constraint chk_ids_state_value_registry_identity check",
                "constraint chk_ids_state_value_registry_version check",
                "idx_ids_state_value_registry_active",
            )
        ),
        "candidate_constraints_present": all(
            constraint_id.lower() in normalized
            for constraint_id in EXPECTED_CANDIDATE_CONSTRAINTS
        ),
        "candidate_sql_definitions_exact": _candidate_sql_definitions_exact(
            normalized
        ),
        "future_check_validation_steps_present": all(
            f"validate constraint {constraint_id}" in normalized
            for constraint_id in EXPECTED_CHECK_CONSTRAINTS
        ),
        "state_registry_rollback_requires_empty": (
            registry.get("rollback_requires_empty") is True
            and "select exists (select 1 from ids_state_value_registry)" in normalized
            and "stage-036 rollback blocked: ids_state_value_registry is not empty"
            in normalized
        ),
        "rollback_covers_candidates": all(
            f"drop constraint if exists {constraint_id}" in normalized
            for constraint_id in EXPECTED_CANDIDATE_CONSTRAINTS
        )
        and "drop table if exists ids_state_value_registry" in normalized,
        "no_data_changing_dml": forbidden_dml is None,
        "no_plaintext_secrets_or_dsn": secret_free,
        "raw_metadata_path_absent_from_sql": RAW_METADATA_ROOT not in sql,
        "runtime_execution_blocked_by_index": (
            migration.get("runtime_execution_allowed") is False
            and migration.get("data_repair_allowed") is False
            and migration.get("state_value_seed_allowed") is False
            and migration.get("destructive_migration_allowed") is False
        ),
    }


def _constraint_inventory_results(index: dict[str, Any]) -> dict[str, bool]:
    inventory = index.get("constraint_inventory", {})
    inventory = inventory if isinstance(inventory, dict) else {}
    candidates = inventory.get("candidates", [])
    candidates = candidates if isinstance(candidates, list) else []
    candidate_by_id = {
        item.get("constraint_id"): item
        for item in candidates
        if isinstance(item, dict) and isinstance(item.get("constraint_id"), str)
    }
    candidate_specs = {
        constraint_id: {
            "constraint_class": item.get("constraint_class"),
            "table": item.get("table"),
            "columns": tuple(item.get("columns", [])),
            "validation_kind": item.get("validation_kind"),
        }
        for constraint_id, item in candidate_by_id.items()
    }
    registry = index.get("versioned_state_registry", {})
    registry = registry if isinstance(registry, dict) else {}
    classes = {
        part
        for item in candidates
        if isinstance(item, dict)
        for part in str(item.get("constraint_class", "")).split("+")
    }
    unique_candidate = candidate_by_id.get("uq_ids_chunks_document_ordinal", {})
    return {
        "candidate_ids_exact": (
            set(candidate_by_id) == EXPECTED_CANDIDATE_CONSTRAINTS
            and len(candidates) == len(EXPECTED_CANDIDATE_CONSTRAINTS)
        ),
        "candidate_specs_exact": candidate_specs == EXPECTED_CANDIDATE_SPECS,
        "required_constraint_classes_covered": {
            "COMPOSITE_UNIQUENESS",
            "NOT_NULL_REQUIRED",
            "STATUS_VALUESET_INTEGRITY",
            "CROSS_FIELD_CONSISTENCY",
        }.issubset(classes),
        "all_candidates_fail_closed_pending_real_profile": bool(candidates)
        and all(
            item.get("owner_authorized_real_data_profile_required") is True
            and item.get("live_apply_blocked") is True
            and item.get("rollback_required") is True
            and item.get("candidate_state")
            == "OWNER_AUTHORIZED_REAL_DATA_PROFILE_REQUIRED"
            for item in candidate_by_id.values()
        ),
        "unique_candidate_exact": (
            unique_candidate.get("table") == "ids_chunks"
            and unique_candidate.get("columns")
            == ["document_id", "chunk_ordinal"]
            and unique_candidate.get("validation_kind")
            == "duplicate_count_must_be_zero"
        ),
        "existing_foreign_keys_exact": set(
            inventory.get("existing_foreign_keys", [])
        )
        == EXPECTED_FOREIGN_KEYS,
        "existing_primary_keys_exact": set(
            inventory.get("existing_primary_keys", [])
        )
        == EXPECTED_PRIMARY_KEYS,
        "stable_value_checks_exact": set(
            inventory.get("existing_stable_value_checks", [])
        )
        == EXPECTED_STABLE_VALUE_CHECKS,
        "state_registry_is_unpopulated_and_stage037_owned": (
            registry.get("contract_kind") == "versioned_state_registry"
            and registry.get("table") == "ids_state_value_registry"
            and registry.get("primary_key")
            == ["state_namespace", "state_value"]
            and set(registry.get("state_namespaces_reserved_for_future_contracts", []))
            == EXPECTED_STATE_NAMESPACES
            and registry.get("populated") is False
            and registry.get("state_values_defined") is False
            and registry.get("state_values_owner") == "STAGE-037"
            and registry.get("transition_rules_defined") is False
            and registry.get("native_postgresql_enum_used") is False
            and registry.get("runtime_registry_write_allowed") is False
            and registry.get("rollback_requires_empty") is True
            and set(registry.get("required_metadata", []))
            == {
                "introduced_version",
                "retired_version",
                "is_active",
                "owner_label_zh",
                "owner_description_zh",
            }
            and "allowed_values" not in registry
        ),
    }


def _guardrail_results(index: dict[str, Any]) -> dict[str, bool]:
    guardrails = index.get("guardrails", {})
    guardrails = guardrails if isinstance(guardrails, dict) else {}
    pool = guardrails.get("connection_pool", {})
    storage = guardrails.get("storage_boundary", {})
    migration = guardrails.get("migration_safety", {})
    recovery = guardrails.get("recovery", {})
    raw = index.get("raw_metadata_boundary", {})
    real_data = index.get("real_data_only_guard", {})
    return {
        "connection_pool_budget_preserved": (
            pool.get("aggregate_max_pool_size") == 10
            and pool.get("max_overflow") == 0
            and pool.get("backpressure_required") is True
            and pool.get("instantiate_pool_allowed") is False
        ),
        "storage_boundary_preserved": (
            storage.get("stores_control_plane_metadata") is True
            and storage.get("stores_status_and_state") is True
            and storage.get("stores_hot_index_metadata") is True
            and all(
                storage.get(key) is False
                for key in (
                    "stores_raw_files",
                    "stores_raw_database_rows",
                    "stores_document_bodies",
                    "stores_ocr_full_text",
                    "stores_vector_payloads",
                    "stores_report_binaries",
                    "stores_raw_log_bodies",
                    "stores_unbounded_derived_artifacts",
                )
            )
        ),
        "migration_safety_preserved": (
            migration.get("stage031_authoritative") is True
            and migration.get("dry_run_required") is True
            and migration.get("backup_required") is True
            and migration.get("validation_required") is True
            and migration.get("rollback_required") is True
            and migration.get("recovery_smoke_required") is True
            and migration.get("destructive_owner_confirmation_required") is True
        ),
        "recovery_source_non_interference_preserved": (
            recovery.get("stage035_authoritative") is True
            and recovery.get("isolated_target_required") is True
            and recovery.get("source_database_mutation_allowed") is False
            and recovery.get("runtime_recovery_allowed") is False
        ),
        "raw_metadata_boundary_path_only": (
            raw.get("path") == RAW_METADATA_ROOT
            and raw.get("path_only") is True
            and all(
                raw.get(key) is False
                for key in (
                    "content_access_allowed",
                    "recursive_listing_allowed",
                    "hashing_allowed",
                    "copy_allowed",
                    "modify_allowed",
                    "delete_allowed",
                    "dump_allowed",
                    "scan_allowed",
                    "normalize_allowed",
                )
            )
        ),
        "real_data_only_gate_preserved": (
            real_data.get("owner_authorized_real_data_profile_required") is True
            and real_data.get("real_data_profile_available") is False
            and real_data.get("fake_rows_allowed") is False
            and real_data.get("fabricated_profile_allowed") is False
            and real_data.get("placeholder_corpus_allowed") is False
            and set(real_data.get("forbidden", []))
            == EXPECTED_FORBIDDEN_REAL_DATA_SUBSTITUTES
        ),
    }


def _runtime_policy_results(index: dict[str, Any]) -> dict[str, bool]:
    runtime = index.get("runtime_policy", {})
    runtime = runtime if isinstance(runtime, dict) else {}
    return {
        "runtime_policy_keys_exact": set(runtime) == EXPECTED_RUNTIME_POLICY_KEYS,
        "all_runtime_actions_disabled": bool(runtime)
        and all(value is False for value in runtime.values()),
        "top_level_execution_blocked": (
            index.get("execution_ready") is False
            and index.get("execution_state") == BLOCKED_PENDING_PROFILE
            and index.get("github_upload_allowed") is False
            and index.get("app_reinstall_allowed") is False
            and index.get("next_gate") == "IDS-STAGE036-P3-GATE"
        ),
    }


def build_stage036_quality_constraint_report(
    index_path: Path = INDEX_PATH,
    migration_path: Path = MIGRATION_PATH,
    baseline_schema_path: Path = CONTROL_SCHEMA_PATH,
    *,
    index_snapshot: dict[str, Any] | None = None,
    migration_sql_snapshot: str | None = None,
    baseline_sql_snapshot: str | None = None,
) -> dict[str, Any]:
    index = index_snapshot if index_snapshot is not None else _load_json(index_path)
    migration_sql = (
        migration_sql_snapshot
        if migration_sql_snapshot is not None
        else migration_path.read_text(encoding="utf-8")
    )
    baseline_sql = (
        baseline_sql_snapshot
        if baseline_sql_snapshot is not None
        else baseline_schema_path.read_text(encoding="utf-8")
    )

    source_results = _source_integrity_results(
        index_path, index, baseline_schema_path
    )
    baseline_results = _baseline_schema_results(baseline_sql)
    migration_results = _migration_contract_results(migration_sql, index)
    inventory_results = _constraint_inventory_results(index)
    guardrail_results = _guardrail_results(index)
    runtime_results = _runtime_policy_results(index)
    identity_valid = (
        index.get("schema_version") == INDEX_SCHEMA_VERSION
        and index.get("stage") == STAGE
        and index.get("phase") == "Phase 2"
        and index.get("task_id") == TASK_ID
        and index.get("acceptance_id") == ACCEPTANCE_ID
        and index.get("database_quality_constraint_contract_id") == CONTRACT_ID
        and index.get("contract_state")
        == "STATIC_QUALITY_CONSTRAINT_CONTRACT_VALID"
    )
    contract_valid = identity_valid and all(
        all(group.values())
        for group in (
            source_results,
            baseline_results,
            migration_results,
            inventory_results,
            guardrail_results,
            runtime_results,
        )
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "stage": STAGE,
        "phase": "Phase 2",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "contract_id": CONTRACT_ID,
        "declared_contract_state": index.get("contract_state"),
        "contract_state": (
            "STATIC_QUALITY_CONSTRAINT_CONTRACT_VALID"
            if contract_valid
            else INVALID_CONTRACT_STATE
        ),
        "identity_valid": identity_valid,
        "contract_valid": contract_valid,
        "execution_ready": False,
        "execution_state": (
            BLOCKED_PENDING_PROFILE if contract_valid else BLOCKED_INVALID_CONTRACT
        ),
        "migration_execution_performed": False,
        "real_data_profile_executed": False,
        "state_values_seeded": False,
        "source_integrity_results": source_results,
        "baseline_schema_results": baseline_results,
        "migration_contract_results": migration_results,
        "constraint_inventory_results": inventory_results,
        "guardrail_results": guardrail_results,
        "runtime_policy_results": runtime_results,
        "candidate_constraint_count": len(EXPECTED_CANDIDATE_CONSTRAINTS),
        "existing_foreign_key_count": len(EXPECTED_FOREIGN_KEYS),
        "next_gate": "IDS-STAGE036-P3-GATE",
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "raw_metadata_boundary": {
            "path": RAW_METADATA_ROOT,
            "path_only": True,
            "content_access_performed": False,
        },
        "owner_feedback_zh": (
            "静态数据库质量约束合同有效；当前未连接或修改数据库。"
            "唯一性和存量行相关约束继续等待 owner 授权真实数据 profile。"
            if contract_valid
            else "静态数据库质量约束合同无效；已失败关闭，禁止执行迁移或约束验证。"
        ),
    }


def main() -> int:
    report = build_stage036_quality_constraint_report()
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["contract_valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
