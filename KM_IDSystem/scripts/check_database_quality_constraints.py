"""Validate the static IDS STAGE-036 database-quality constraint contract.

The checker reads tracked SQL and JSON contracts and prints JSON to stdout. It
does not connect to PostgreSQL, inspect database rows or raw metadata, execute a
migration, seed state values, or write runtime outputs.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any


SCHEMA_VERSION = "ids.stage036.database_quality_constraints.phase2.v1"
PHASE3_SCHEMA_VERSION = "ids.stage036.database_quality_constraints.phase3.v1"
PHASE4_SCHEMA_VERSION = "ids.stage036.database_quality_constraints.phase4.v1"
PHASE4_CONTRACT_SCHEMA_VERSION = (
    "ids.stage036.database_quality_constraints.delivery_contract.v1"
)
INDEX_SCHEMA_VERSION = "ids.stage036.database_quality_constraints.index.v1"
STAGE = "STAGE-036"
TASK_ID = "IDS-V0_1-STAGE036-P2"
PHASE3_TASK_ID = "IDS-V0_1-STAGE036-P3"
PHASE4_TASK_ID = "IDS-V0_1-STAGE036-P4"
ACCEPTANCE_ID = "ACC-STAGE-036"
CONTRACT_ID = "ids_stage036_database_quality_constraints_static_slice"
MIGRATION_ID = "ids_stage036_002_database_quality_constraints"
EXPECTED_MIGRATION_SHA256 = (
    "b8e3e49473fe89fae34b81042e7bc456499ba4702e4f6e6c637b65d91b5f3af1"
)
EXPECTED_BASELINE_SCHEMA_SHA256 = (
    "9fa7b8e535fe799c0aed14d738f568b33a19fc2835eeb492c8217bc35b588479"
)
RAW_METADATA_ROOT = "/Users/linzezhang/Downloads/IDS_MetaData"
BLOCKED_PENDING_PROFILE = "BLOCKED_PENDING_OWNER_AUTHORIZED_REAL_DATA_PROFILE"
BLOCKED_INVALID_CONTRACT = "BLOCKED_INVALID_QUALITY_CONSTRAINT_CONTRACT"
INVALID_CONTRACT_STATE = "INVALID_QUALITY_CONSTRAINT_CONTRACT"
PHASE3_EXECUTION_MODE = "STATIC_TRACKED_CONTRACT_SCENARIO_VALIDATION_ONLY"
PHASE4_EXECUTION_MODE = "STATIC_TRACKED_CLOSEOUT_EVIDENCE_ONLY"

EXPECTED_PHASE3_SCENARIOS = {
    "migration_dry_run",
    "repeat_execution",
    "failure_rollback",
    "recovery_smoke",
    "candidate_constraint_semantics",
    "duplicate_uniqueness_profile_gate",
    "existing_foreign_key_integrity",
    "state_registry_deferred",
    "raw_large_file_block",
    "unbounded_derived_artifact_block",
    "connection_pool_boundary",
    "transaction_boundary",
    "constraint_error_explanations",
    "source_non_interference",
}

PHASE3_SCENARIO_EXPLANATIONS = {
    "migration_dry_run": "migration dry-run 场景只验证 STAGE-031 的静态门禁、单事务和当前禁止执行状态；没有连接 PostgreSQL，也没有运行 dry-run、apply、backup、restore 或 validation。",
    "repeat_execution": "重复执行场景验证 migration 使用稳定约束 id 和存在性保护，并验证 checker 对同一 tracked 快照输出确定结果；没有重复执行 SQL 或写运行产物。",
    "failure_rollback": "失败回滚场景验证 down 覆盖、单事务要求和非空状态 registry 保护；没有执行 rollback、删除约束或恢复数据库。",
    "recovery_smoke": "缺少 owner 授权真实数据 profile 时 recovery smoke 必须按预期阻断；PASS 只证明停止合同有效，不代表恢复已执行。",
    "candidate_constraint_semantics": "九个候选约束必须同时匹配精确 table、columns、validation kind 和 SQL 语义；任何漂移都失败关闭。",
    "duplicate_uniqueness_profile_gate": "chunk 复合唯一性在 owner 授权真实数据 duplicate profile 证明为零前不得应用，禁止用虚构行替代。",
    "existing_foreign_key_integrity": "三条既有外键按 tracked STAGE-030 schema 保持完整，不从名称相似的 text ref 推导新外键。",
    "state_registry_deferred": "versioned state registry 只验证空结构、回滚保护和 STAGE-037 ownership，不写入状态值或 transition。",
    "raw_large_file_block": "PostgreSQL 继续只存控制面、状态和热索引，不读取或写入原始大文件、raw rows、正文、向量或报告二进制。",
    "unbounded_derived_artifact_block": "STAGE-033 的无界派生产物禁令保持有效；场景不生成 report、output、fixture 或 runtime artifact。",
    "connection_pool_boundary": "STAGE-032 连接池总预算 10、overflow 0 和 backpressure 保持不变，当前不创建 pool 或连接配置。",
    "transaction_boundary": "future apply 必须 ON_ERROR_STOP 和 single transaction；当前不打开、提交或回滚真实数据库事务。",
    "constraint_error_explanations": "每个专项场景必须提供非空中文 owner 解释，明确区分静态合同通过、预期阻断和真实执行。",
    "source_non_interference": "STAGE-035 source non-interference 与 isolated-target 要求保持有效；当前不迁移、修改、删除或恢复 source database。",
}

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

EXPECTED_PHASE4_ROLLBACK_GUARDS = {
    "stop_on_invalid_contract": {
        "required": True,
        "stop_all_database_actions": True,
    },
    "require_prechange_checkpoint": {
        "required": True,
        "backup_checkpoint_required": True,
    },
    "execute_tracked_down_section": {
        "required": True,
        "tracked_down_section_only": True,
    },
    "preserve_source_database": {
        "required": True,
        "source_database_mutation_allowed": False,
    },
    "guard_nonempty_state_registry": {
        "required": True,
        "nonempty_registry_auto_drop_allowed": False,
    },
    "separate_cleanup_owner_gate": {
        "required": True,
        "automatic_cleanup_allowed": False,
    },
}

EXPECTED_PHASE4_BACKUP_RESTORE_GUARDS = {
    "owner_authorized_real_profile": {
        "required": True,
        "owner_authorized_real_profile_required": True,
    },
    "managed_secret_ref": {
        "required": True,
        "plaintext_credentials_allowed": False,
    },
    "verified_backup_checkpoint": {
        "required": True,
        "backup_checkpoint_verification_required": True,
    },
    "isolated_target_dry_run": {
        "required": True,
        "isolated_non_production_target_required": True,
    },
    "apply_and_validate_constraints": {
        "required": True,
        "bounded_profile_zero_violations_required": True,
    },
    "recovery_verification": {
        "required": True,
        "recovery_smoke_and_schema_verification_required": True,
    },
    "restore_checkpoint_on_failure": {
        "required": True,
        "source_database_overwrite_allowed": False,
    },
}

EXPECTED_PHASE4_KNOWN_LIMIT_IDS = {
    "no_owner_authorized_real_profile",
    "no_live_postgresql_execution",
    "static_pass_is_not_readiness",
    "no_runtime_artifacts_created",
    "raw_metadata_path_only",
    "state_registry_values_deferred",
    "stage_review_and_batch_upload_blocked",
}

FORBIDDEN_SQL_SECRET_PATTERNS = (
    r"postgres(?:ql)?://",
    r"password\s*=",
    r"api[_-]?key\s*=",
    r"secret\s*=",
)


def _as_json_object(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _load_json(path: Path) -> dict[str, Any]:
    try:
        return _as_json_object(json.loads(path.read_text(encoding="utf-8")))
    except (AttributeError, OSError, TypeError, UnicodeError, json.JSONDecodeError):
        return {}


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
    if len(re.findall(unique_pattern, normalized_sql)) != 1:
        return False

    for constraint_id, clauses in EXPECTED_CHECK_SQL_CLAUSES.items():
        table = EXPECTED_CANDIDATE_SPECS[constraint_id]["table"]
        pattern = (
            rf"alter table {re.escape(str(table))} add constraint "
            rf"{re.escape(constraint_id)} check \((.*?)\) not valid"
        )
        matches = re.findall(pattern, normalized_sql)
        if len(matches) != 1:
            return False
        if constraint_id == "chk_ids_chunks_quality_v2":
            expected_expression = (
                " and ".join(clauses[:6])
                + f" and ( ({clauses[6]}) or ( "
                + " and ".join(clauses[7:])
                + " ) )"
            )
        else:
            expected_expression = " and ".join(clauses)
        if matches[0].strip() != expected_expression:
            return False
    return True


def _candidate_existence_guards_exact(sql: str) -> bool:
    if "-- migrate:up" not in sql or "-- migrate:down" not in sql:
        return False
    normalized_up = _normalized_sql(sql.split("-- migrate:down", 1)[0])
    for constraint_id, spec in EXPECTED_CANDIDATE_SPECS.items():
        table = spec["table"]
        expected_guard = (
            f"if not exists ( select 1 from pg_constraint where conname = "
            f"'{constraint_id}' and conrelid = '{table}'::regclass ) then "
            f"alter table {table} add constraint {constraint_id}"
        )
        if expected_guard not in normalized_up:
            return False
    return normalized_up.count("if not exists ( select 1 from pg_constraint") == 9


def _state_registry_rollback_guard_exact(sql: str) -> bool:
    if "-- migrate:down" not in sql:
        return False
    normalized_down = _normalized_sql(sql.split("-- migrate:down", 1)[1])
    expected_guard = " ".join(
        (
            "do $ids_quality_rollback_gate$",
            "declare registry_has_rows boolean := false;",
            "begin",
            "if to_regclass('public.ids_state_value_registry') is not null then",
            "execute 'select exists (select 1 from ids_state_value_registry)'",
            "into registry_has_rows;",
            "if registry_has_rows then",
            "raise exception 'stage-036 rollback blocked: ids_state_value_registry is not empty';",
            "end if;",
            "end if;",
            "end",
            "$ids_quality_rollback_gate$;",
        )
    )
    registry_drop = "drop table if exists ids_state_value_registry"
    registry_drop_count = len(
        re.findall(
            r"\bdrop table(?: if exists)? ids_state_value_registry\b",
            normalized_down,
        )
    )
    return (
        expected_guard in normalized_down
        and registry_drop_count == 1
        and normalized_down.index(expected_guard) < normalized_down.index(registry_drop)
    )


def _destructive_ddl_is_exact(sql: str) -> bool:
    normalized = _normalized_sql(sql)
    dropped_tables = re.findall(
        r"\bdrop table(?: if exists)? ([a-z_][a-z0-9_]*)\b", normalized
    )
    dropped_constraints = re.findall(
        r"\balter table ([a-z_][a-z0-9_]*) drop constraint if exists "
        r"([a-z_][a-z0-9_]*)\b",
        normalized,
    )
    expected_constraint_drops = {
        (str(spec["table"]), constraint_id)
        for constraint_id, spec in EXPECTED_CANDIDATE_SPECS.items()
    }
    forbidden_destructive_ddl = re.search(
        r"\b(?:drop database|drop schema|drop index|drop view|drop materialized view|"
        r"truncate|delete from|cascade)\b|\balter table\b.*?\bdrop column\b",
        normalized,
    )
    return (
        hashlib.sha256(sql.encode("utf-8")).hexdigest()
        == EXPECTED_MIGRATION_SHA256
        and dropped_tables == ["ids_state_value_registry"]
        and normalized.count("drop table") == 1
        and len(dropped_constraints) == len(expected_constraint_drops)
        and set(dropped_constraints) == expected_constraint_drops
        and normalized.count("drop constraint") == len(expected_constraint_drops)
        and forbidden_destructive_ddl is None
    )


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
        "candidate_existence_guards_exact": _candidate_existence_guards_exact(sql),
        "future_check_validation_steps_present": all(
            f"validate constraint {constraint_id}" in normalized
            for constraint_id in EXPECTED_CHECK_CONSTRAINTS
        ),
        "state_registry_rollback_requires_empty": (
            registry.get("rollback_requires_empty") is True
            and _state_registry_rollback_guard_exact(sql)
        ),
        "rollback_covers_candidates": all(
            f"drop constraint if exists {constraint_id}" in normalized
            for constraint_id in EXPECTED_CANDIDATE_CONSTRAINTS
        )
        and "drop table if exists ids_state_value_registry" in normalized,
        "destructive_ddl_exact": _destructive_ddl_is_exact(sql),
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
    def string_set(value: object) -> set[str]:
        if not isinstance(value, list) or not all(
            isinstance(item, str) for item in value
        ):
            return set()
        return set(value)

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
            "columns": (
                tuple(item["columns"])
                if isinstance(item.get("columns"), list)
                and all(isinstance(column, str) for column in item["columns"])
                else ()
            ),
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
        "existing_foreign_keys_exact": string_set(
            inventory.get("existing_foreign_keys")
        )
        == EXPECTED_FOREIGN_KEYS,
        "existing_primary_keys_exact": string_set(
            inventory.get("existing_primary_keys")
        )
        == EXPECTED_PRIMARY_KEYS,
        "stable_value_checks_exact": string_set(
            inventory.get("existing_stable_value_checks")
        )
        == EXPECTED_STABLE_VALUE_CHECKS,
        "state_registry_is_unpopulated_and_stage037_owned": (
            registry.get("contract_kind") == "versioned_state_registry"
            and registry.get("table") == "ids_state_value_registry"
            and registry.get("primary_key")
            == ["state_namespace", "state_value"]
            and string_set(
                registry.get("state_namespaces_reserved_for_future_contracts")
            )
            == EXPECTED_STATE_NAMESPACES
            and registry.get("populated") is False
            and registry.get("state_values_defined") is False
            and registry.get("state_values_owner") == "STAGE-037"
            and registry.get("transition_rules_defined") is False
            and registry.get("native_postgresql_enum_used") is False
            and registry.get("runtime_registry_write_allowed") is False
            and registry.get("rollback_requires_empty") is True
            and string_set(registry.get("required_metadata"))
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
    pool = pool if isinstance(pool, dict) else {}
    storage = storage if isinstance(storage, dict) else {}
    migration = migration if isinstance(migration, dict) else {}
    recovery = recovery if isinstance(recovery, dict) else {}
    raw = raw if isinstance(raw, dict) else {}
    real_data = real_data if isinstance(real_data, dict) else {}
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
    index = (
        _as_json_object(index_snapshot)
        if index_snapshot is not None
        else _load_json(index_path)
    )
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


def _scenario_result(
    passed: bool,
    evidence: str,
    owner_explanation_zh: str,
    *,
    observed_state: str | None = None,
    expected_block: bool = False,
) -> dict[str, Any]:
    return {
        "status": "PASS" if passed else "FAIL",
        "evidence": evidence,
        "owner_explanation_zh": owner_explanation_zh,
        "observed_state": observed_state,
        "expected_block": expected_block,
        "live_execution_performed": False,
    }


def _repeat_execution_contract_valid(sql: str) -> bool:
    if "-- migrate:up" not in sql or "-- migrate:down" not in sql:
        return False
    up_sql = sql.split("-- migrate:down", 1)[0]
    normalized = _normalized_sql(up_sql)
    return (
        "create table if not exists ids_state_value_registry" in normalized
        and "create index if not exists idx_ids_state_value_registry_active"
        in normalized
        and _candidate_existence_guards_exact(sql)
    )


def _has_chinese_text(value: object) -> bool:
    return isinstance(value, str) and re.search(r"[\u4e00-\u9fff]", value) is not None


def _items_by_id(value: object, id_field: str) -> dict[str, dict[str, Any]]:
    if not isinstance(value, list):
        return {}
    indexed: dict[str, dict[str, Any]] = {}
    for item in value:
        if not isinstance(item, dict):
            return {}
        item_id = item.get(id_field)
        if not isinstance(item_id, str) or not item_id or item_id in indexed:
            return {}
        indexed[item_id] = item
    return indexed


def _phase4_contract_results(index: dict[str, Any]) -> dict[str, bool]:
    delivery = index.get("phase4_delivery_contract", {})
    delivery = delivery if isinstance(delivery, dict) else {}
    schema_diff = delivery.get("schema_diff", {})
    migration_output = delivery.get("migration_output", {})
    recovery_log = delivery.get("recovery_test_log", {})
    confirmation = delivery.get("destructive_migration_confirmation", {})
    schema_diff = schema_diff if isinstance(schema_diff, dict) else {}
    migration_output = (
        migration_output if isinstance(migration_output, dict) else {}
    )
    recovery_log = recovery_log if isinstance(recovery_log, dict) else {}
    confirmation = confirmation if isinstance(confirmation, dict) else {}
    rollback_steps = _items_by_id(delivery.get("rollback_steps"), "step_id")
    backup_restore_steps = _items_by_id(
        delivery.get("backup_restore_steps"), "step_id"
    )
    known_limits = _items_by_id(delivery.get("known_limits"), "limit_id")
    owner_feedback = delivery.get("chinese_owner_feedback")

    rollback_steps_valid = (
        set(rollback_steps) == set(EXPECTED_PHASE4_ROLLBACK_GUARDS)
        and all(
            set(item)
            == {"step_id", "owner_message_zh", *guards}
            and all(item.get(field) is expected for field, expected in guards.items())
            and _has_chinese_text(item.get("owner_message_zh"))
            for step_id, guards in EXPECTED_PHASE4_ROLLBACK_GUARDS.items()
            for item in [rollback_steps.get(step_id, {})]
        )
    )
    backup_restore_steps_valid = (
        set(backup_restore_steps) == set(EXPECTED_PHASE4_BACKUP_RESTORE_GUARDS)
        and all(
            set(item)
            == {"step_id", "owner_message_zh", *guards}
            and all(item.get(field) is expected for field, expected in guards.items())
            and _has_chinese_text(item.get("owner_message_zh"))
            for step_id, guards in EXPECTED_PHASE4_BACKUP_RESTORE_GUARDS.items()
            for item in [backup_restore_steps.get(step_id, {})]
        )
    )
    known_limits_valid = (
        set(known_limits) == EXPECTED_PHASE4_KNOWN_LIMIT_IDS
        and all(
            set(item) == {"limit_id", "acknowledged", "owner_message_zh"}
            and item.get("acknowledged") is True
            and _has_chinese_text(item.get("owner_message_zh"))
            for item in known_limits.values()
        )
    )

    return {
        "root_keys_exact": set(delivery)
        == {
            "schema_version",
            "schema_diff",
            "migration_output",
            "recovery_test_log",
            "destructive_migration_confirmation",
            "rollback_steps",
            "backup_restore_steps",
            "known_limits",
            "chinese_owner_feedback",
        },
        "identity_valid": (
            delivery.get("schema_version") == PHASE4_CONTRACT_SCHEMA_VERSION
        ),
        "schema_diff_valid": schema_diff
        == {
            "mode": "static_tracked_schema_diff_not_executed",
            "baseline_schema_ref": "../postgresql_control_plane/001_control_plane_schema.sql",
            "migration_sql_ref": "002_database_quality_constraints.sql",
            "baseline_schema_sha256": EXPECTED_BASELINE_SCHEMA_SHA256,
            "migration_sha256": EXPECTED_MIGRATION_SHA256,
            "added_table_contracts": ["ids_state_value_registry"],
            "candidate_constraint_count": 9,
            "existing_foreign_key_count": 3,
            "live_schema_diff_result": "NOT_EXECUTED",
        },
        "migration_output_valid": migration_output
        == {
            "mode": "static_tracked_migration_output_not_executed",
            "migration_id": MIGRATION_ID,
            "tracked_migration_sha256": EXPECTED_MIGRATION_SHA256,
            "live_migration_result": "NOT_EXECUTED",
            "live_constraint_validation_result": "NOT_EXECUTED",
            "dry_run_required": True,
            "backup_checkpoint_required": True,
            "rollback_required": True,
            "destructive_migration_allowed": False,
        },
        "recovery_test_log_valid": recovery_log
        == {
            "mode": "static_quality_constraint_recovery_log_expected_block",
            "expected_valid_result": "PASS_WITH_EXPECTED_BLOCK",
            "live_recovery_smoke_result": "NOT_EXECUTED",
            "scenario_count": 14,
            "execution_ready": False,
            "execution_state": BLOCKED_PENDING_PROFILE,
        },
        "destructive_confirmation_valid": (
            set(confirmation)
            == {
                "required",
                "destructive_allowed_by_default",
                "current_migration_destructive",
                "authorized_this_run",
                "manual_owner_confirmation_required",
                "owner_message_zh",
            }
            and confirmation.get("required") is True
            and confirmation.get("destructive_allowed_by_default") is False
            and confirmation.get("current_migration_destructive") is False
            and confirmation.get("authorized_this_run") is False
            and confirmation.get("manual_owner_confirmation_required") is True
            and _has_chinese_text(confirmation.get("owner_message_zh"))
            and "单独人工确认" in confirmation.get("owner_message_zh", "")
        ),
        "rollback_steps_valid": rollback_steps_valid,
        "backup_restore_steps_valid": backup_restore_steps_valid,
        "known_limits_valid": known_limits_valid,
        "owner_feedback_valid": (
            isinstance(owner_feedback, str)
            and "未执行真实 migration" in owner_feedback
            and "owner 授权真实数据 profile" in owner_feedback
            and "STAGE-036 review" in owner_feedback
        ),
    }


def build_stage036_scenario_validation_report(
    index_path: Path = INDEX_PATH,
    migration_path: Path = MIGRATION_PATH,
    baseline_schema_path: Path = CONTROL_SCHEMA_PATH,
    *,
    index_snapshot: dict[str, Any] | None = None,
    migration_sql_snapshot: str | None = None,
    baseline_sql_snapshot: str | None = None,
) -> dict[str, Any]:
    index = (
        _as_json_object(index_snapshot)
        if index_snapshot is not None
        else _load_json(index_path)
    )
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
    phase2_report = build_stage036_quality_constraint_report(
        index_path,
        migration_path,
        baseline_schema_path,
        index_snapshot=index,
        migration_sql_snapshot=migration_sql,
        baseline_sql_snapshot=baseline_sql,
    )
    phase2_valid = phase2_report["contract_valid"]
    execution_state = phase2_report["execution_state"]
    migration_results = phase2_report["migration_contract_results"]
    inventory_results = phase2_report["constraint_inventory_results"]
    guardrail_results = phase2_report["guardrail_results"]
    baseline_results = phase2_report["baseline_schema_results"]
    runtime = index.get("runtime_policy", {})
    runtime = runtime if isinstance(runtime, dict) else {}
    migration_contract = index.get("migration_contract", {})
    migration_contract = (
        migration_contract if isinstance(migration_contract, dict) else {}
    )
    inventory = index.get("constraint_inventory", {})
    inventory = inventory if isinstance(inventory, dict) else {}
    candidates = inventory.get("candidates", [])
    candidates = candidates if isinstance(candidates, list) else []
    candidate_by_id = {
        item.get("constraint_id"): item
        for item in candidates
        if isinstance(item, dict) and isinstance(item.get("constraint_id"), str)
    }
    unique_candidate = candidate_by_id.get("uq_ids_chunks_document_ordinal", {})

    def runtime_actions_disabled(*keys: str) -> bool:
        return all(runtime.get(key) is False for key in keys)

    explanations_valid = (
        set(PHASE3_SCENARIO_EXPLANATIONS) == EXPECTED_PHASE3_SCENARIOS
        and all(
            _has_chinese_text(value)
            for value in PHASE3_SCENARIO_EXPLANATIONS.values()
        )
    )
    scenario_results = {
        "migration_dry_run": _scenario_result(
            phase2_valid
            and guardrail_results["migration_safety_preserved"]
            and migration_results["migration_identity_matches"]
            and migration_results["owner_profile_backup_rollback_guards_present"]
            and migration_contract.get("on_error_stop_required") is True
            and migration_contract.get("single_transaction_required") is True
            and runtime_actions_disabled(
                "connect_to_postgres",
                "execute_data_profile",
                "execute_migration",
                "execute_constraint_validation",
                "execute_backup",
                "execute_restore",
                "execute_recovery_smoke",
            ),
            "STAGE031 migration safety, apply guards, ON_ERROR_STOP, and single-transaction requirements are present while every live action remains disabled",
            PHASE3_SCENARIO_EXPLANATIONS["migration_dry_run"],
        ),
        "repeat_execution": _scenario_result(
            phase2_valid
            and _repeat_execution_contract_valid(migration_sql)
            and runtime_actions_disabled(
                "connect_to_postgres",
                "execute_migration",
                "write_runtime_outputs",
            ),
            "tracked SQL uses table/index IF NOT EXISTS plus nine pg_constraint existence guards; checker remains stdout-only",
            PHASE3_SCENARIO_EXPLANATIONS["repeat_execution"],
        ),
        "failure_rollback": _scenario_result(
            phase2_valid
            and migration_results["rollback_covers_candidates"]
            and migration_results["state_registry_rollback_requires_empty"]
            and migration_contract.get("single_transaction_required") is True
            and runtime_actions_disabled(
                "connect_to_postgres",
                "execute_migration",
                "execute_constraint_validation",
                "execute_backup",
                "execute_restore",
                "execute_recovery_smoke",
            ),
            "down migration covers all candidates, refuses a nonempty state registry, and remains an unexecuted single-transaction contract",
            PHASE3_SCENARIO_EXPLANATIONS["failure_rollback"],
        ),
        "recovery_smoke": _scenario_result(
            phase2_valid
            and execution_state == BLOCKED_PENDING_PROFILE
            and guardrail_results["recovery_source_non_interference_preserved"]
            and runtime_actions_disabled(
                "connect_to_postgres",
                "execute_data_profile",
                "execute_migration",
                "execute_backup",
                "execute_restore",
                "execute_recovery_smoke",
            ),
            "contract is valid but remains blocked pending owner-authorized real-data profile; no recovery action is enabled",
            PHASE3_SCENARIO_EXPLANATIONS["recovery_smoke"],
            observed_state=execution_state,
            expected_block=phase2_valid
            and execution_state == BLOCKED_PENDING_PROFILE,
        ),
        "candidate_constraint_semantics": _scenario_result(
            phase2_valid
            and inventory_results["candidate_ids_exact"]
            and inventory_results["candidate_specs_exact"]
            and migration_results["candidate_sql_definitions_exact"],
            "nine candidate ids, table/column/validation specs, and normalized SQL definitions match exactly",
            PHASE3_SCENARIO_EXPLANATIONS["candidate_constraint_semantics"],
        ),
        "duplicate_uniqueness_profile_gate": _scenario_result(
            phase2_valid
            and inventory_results["unique_candidate_exact"]
            and unique_candidate.get("owner_authorized_real_data_profile_required")
            is True
            and unique_candidate.get("live_apply_blocked") is True
            and unique_candidate.get("candidate_state")
            == "OWNER_AUTHORIZED_REAL_DATA_PROFILE_REQUIRED"
            and runtime_actions_disabled(
                "query_real_rows", "execute_data_profile", "execute_migration"
            ),
            "ids_chunks(document_id, chunk_ordinal) remains blocked until a real duplicate-count profile exists",
            PHASE3_SCENARIO_EXPLANATIONS["duplicate_uniqueness_profile_gate"],
        ),
        "existing_foreign_key_integrity": _scenario_result(
            phase2_valid
            and baseline_results["existing_foreign_keys_present"]
            and inventory_results["existing_foreign_keys_exact"],
            "the three tracked STAGE030 foreign keys are present and exactly inventoried; no inferred text-reference foreign key is added",
            PHASE3_SCENARIO_EXPLANATIONS["existing_foreign_key_integrity"],
        ),
        "state_registry_deferred": _scenario_result(
            phase2_valid
            and migration_results["state_registry_definition_exact"]
            and migration_results["state_registry_rollback_requires_empty"]
            and inventory_results["state_registry_is_unpopulated_and_stage037_owned"]
            and runtime_actions_disabled("seed_state_values"),
            "registry structure and rollback guard are exact; values/transitions remain unpopulated and STAGE037-owned",
            PHASE3_SCENARIO_EXPLANATIONS["state_registry_deferred"],
        ),
        "raw_large_file_block": _scenario_result(
            phase2_valid
            and guardrail_results["storage_boundary_preserved"]
            and guardrail_results["raw_metadata_boundary_path_only"]
            and runtime_actions_disabled("read_raw_metadata", "write_raw_metadata"),
            "storage guard excludes raw files/rows/bodies/vectors/binaries and the raw root remains path-only",
            PHASE3_SCENARIO_EXPLANATIONS["raw_large_file_block"],
        ),
        "unbounded_derived_artifact_block": _scenario_result(
            phase2_valid
            and guardrail_results["storage_boundary_preserved"]
            and runtime_actions_disabled("write_runtime_outputs"),
            "stores_unbounded_derived_artifacts=false and write_runtime_outputs=false",
            PHASE3_SCENARIO_EXPLANATIONS["unbounded_derived_artifact_block"],
        ),
        "connection_pool_boundary": _scenario_result(
            phase2_valid
            and guardrail_results["connection_pool_budget_preserved"]
            and runtime_actions_disabled(
                "connect_to_postgres", "instantiate_connection_pool"
            ),
            "aggregate pool max=10, overflow=0, backpressure required, and no pool/connection action is enabled",
            PHASE3_SCENARIO_EXPLANATIONS["connection_pool_boundary"],
        ),
        "transaction_boundary": _scenario_result(
            phase2_valid
            and migration_contract.get("on_error_stop_required") is True
            and migration_contract.get("single_transaction_required") is True
            and runtime_actions_disabled(
                "connect_to_postgres",
                "execute_migration",
                "execute_constraint_validation",
            ),
            "future apply requires ON_ERROR_STOP and one transaction while no live connection, migration, or validation action is enabled",
            PHASE3_SCENARIO_EXPLANATIONS["transaction_boundary"],
        ),
        "constraint_error_explanations": _scenario_result(
            phase2_valid and explanations_valid,
            "all fourteen exact scenario ids have nonempty Chinese owner explanations and explicit no-live semantics",
            PHASE3_SCENARIO_EXPLANATIONS["constraint_error_explanations"],
        ),
        "source_non_interference": _scenario_result(
            phase2_valid
            and guardrail_results["recovery_source_non_interference_preserved"]
            and guardrail_results["raw_metadata_boundary_path_only"]
            and runtime_actions_disabled(
                "connect_to_postgres",
                "execute_migration",
                "execute_backup",
                "execute_restore",
                "execute_recovery_smoke",
                "write_raw_metadata",
            ),
            "isolated-target/source-preservation guards remain authoritative and all source-affecting actions are disabled",
            PHASE3_SCENARIO_EXPLANATIONS["source_non_interference"],
        ),
    }
    scenario_validation_valid = (
        phase2_valid
        and set(scenario_results) == EXPECTED_PHASE3_SCENARIOS
        and all(result["status"] == "PASS" for result in scenario_results.values())
        and scenario_results["recovery_smoke"]["expected_block"] is True
    )
    return {
        "schema_version": PHASE3_SCHEMA_VERSION,
        "phase2_schema_version": SCHEMA_VERSION,
        "index_schema_version": INDEX_SCHEMA_VERSION,
        "stage": STAGE,
        "phase": "Phase 3",
        "task_id": PHASE3_TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "phase2_contract_valid": phase2_valid,
        "scenario_validation_valid": scenario_validation_valid,
        "scenario_results": scenario_results,
        "execution_mode": PHASE3_EXECUTION_MODE,
        "execution_ready": False,
        "execution_state": execution_state,
        "live_execution_performed": False,
        "postgresql_connection_performed": False,
        "migration_dry_run_performed": False,
        "migration_apply_performed": False,
        "constraint_validation_performed": False,
        "rollback_performed": False,
        "backup_performed": False,
        "restore_performed": False,
        "recovery_smoke_performed": False,
        "real_data_profile_executed": False,
        "state_values_seeded": False,
        "runtime_output_written": False,
        "raw_metadata_boundary": phase2_report["raw_metadata_boundary"],
        "phase2_report": phase2_report,
        "next_gate": "IDS-STAGE036-P4-GATE",
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "owner_feedback_zh": (
            "数据库质量约束 Phase 3 静态场景验证通过；当前仍未连接或修改数据库，"
            "真实数据 profile 和所有 live 操作继续阻断。"
            if scenario_validation_valid
            else "数据库质量约束 Phase 3 静态场景验证失败；已失败关闭，禁止进入任何 live 数据库操作。"
        ),
    }


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def build_stage036_delivery_report(
    index_path: Path = INDEX_PATH,
    migration_path: Path = MIGRATION_PATH,
    baseline_schema_path: Path = CONTROL_SCHEMA_PATH,
    *,
    index_snapshot: dict[str, Any] | None = None,
    migration_sql_snapshot: str | None = None,
    baseline_sql_snapshot: str | None = None,
) -> dict[str, Any]:
    in_memory_snapshot_supplied = any(
        snapshot is not None
        for snapshot in (
            index_snapshot,
            migration_sql_snapshot,
            baseline_sql_snapshot,
        )
    )
    try:
        canonical_paths_bound = (
            index_path.resolve() == INDEX_PATH.resolve()
            and migration_path.resolve() == MIGRATION_PATH.resolve()
            and baseline_schema_path.resolve() == CONTROL_SCHEMA_PATH.resolve()
        )
    except (AttributeError, OSError, RuntimeError):
        canonical_paths_bound = False
    if in_memory_snapshot_supplied:
        snapshot_source = "in_memory_validation_snapshot"
    elif canonical_paths_bound:
        snapshot_source = "tracked_files"
    else:
        snapshot_source = "noncanonical_path_validation_snapshot"
    tracked_snapshot_bound = not in_memory_snapshot_supplied and canonical_paths_bound
    index = (
        _as_json_object(index_snapshot)
        if index_snapshot is not None
        else _load_json(index_path)
    )
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
    scenario_report = build_stage036_scenario_validation_report(
        index_path,
        migration_path,
        baseline_schema_path,
        index_snapshot=index,
        migration_sql_snapshot=migration_sql,
        baseline_sql_snapshot=baseline_sql,
    )
    phase2_report = scenario_report["phase2_report"]
    phase4_contract = index.get("phase4_delivery_contract", {})
    phase4_contract = (
        phase4_contract if isinstance(phase4_contract, dict) else {}
    )
    schema_diff_contract = phase4_contract.get("schema_diff", {})
    migration_output_contract = phase4_contract.get("migration_output", {})
    recovery_log_contract = phase4_contract.get("recovery_test_log", {})
    schema_diff_contract = (
        schema_diff_contract if isinstance(schema_diff_contract, dict) else {}
    )
    migration_output_contract = (
        migration_output_contract
        if isinstance(migration_output_contract, dict)
        else {}
    )
    recovery_log_contract = (
        recovery_log_contract if isinstance(recovery_log_contract, dict) else {}
    )
    migration_contract = index.get("migration_contract", {})
    migration_contract = (
        migration_contract if isinstance(migration_contract, dict) else {}
    )
    runtime_results = phase2_report["runtime_policy_results"]
    inventory_results = phase2_report["constraint_inventory_results"]
    migration_results = phase2_report["migration_contract_results"]
    guardrail_results = phase2_report["guardrail_results"]
    phase4_contract_results = _phase4_contract_results(index)
    scenario_results = scenario_report["scenario_results"]
    migration_sha256 = _sha256_text(migration_sql)
    baseline_schema_sha256 = _sha256_text(baseline_sql)
    canonical_index_sha256 = _sha256_text(
        json.dumps(index, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    )

    delivery_check_results = {
        "phase2_contract_valid": phase2_report["contract_valid"],
        "phase3_scenarios_valid": scenario_report["scenario_validation_valid"],
        "fourteen_scenarios_pass": (
            len(scenario_results) == 14
            and set(scenario_results) == EXPECTED_PHASE3_SCENARIOS
            and all(item["status"] == "PASS" for item in scenario_results.values())
        ),
        "expected_profile_block_preserved": (
            scenario_report["execution_ready"] is False
            and scenario_report["execution_state"] == BLOCKED_PENDING_PROFILE
            and scenario_results.get("recovery_smoke", {}).get("expected_block")
            is True
            and scenario_report["live_execution_performed"] is False
        ),
        "phase4_machine_contract_valid": all(phase4_contract_results.values()),
        "tracked_snapshot_bound": tracked_snapshot_bound,
        "snapshot_hashes_match_contract": (
            migration_sha256 == EXPECTED_MIGRATION_SHA256
            and baseline_schema_sha256 == EXPECTED_BASELINE_SCHEMA_SHA256
            and schema_diff_contract.get("migration_sha256")
            == EXPECTED_MIGRATION_SHA256
            and schema_diff_contract.get("baseline_schema_sha256")
            == EXPECTED_BASELINE_SCHEMA_SHA256
            and migration_output_contract.get("tracked_migration_sha256")
            == EXPECTED_MIGRATION_SHA256
        ),
        "tracked_schema_sources_valid": (
            all(phase2_report["source_integrity_results"].values())
            and all(phase2_report["baseline_schema_results"].values())
        ),
        "tracked_migration_contract_valid": all(migration_results.values()),
        "candidate_inventory_valid": all(inventory_results.values()),
        "state_registry_still_deferred": inventory_results.get(
            "state_registry_is_unpopulated_and_stage037_owned", False
        ),
        "raw_metadata_boundary_preserved": (
            guardrail_results.get("raw_metadata_boundary_path_only", False)
            and guardrail_results.get("storage_boundary_preserved", False)
        ),
        "source_non_interference_preserved": guardrail_results.get(
            "recovery_source_non_interference_preserved", False
        ),
        "all_runtime_actions_disabled": runtime_results.get(
            "all_runtime_actions_disabled", False
        ),
        "destructive_migration_blocked": (
            migration_contract.get("destructive_migration_allowed") is False
            and migration_contract.get("data_repair_allowed") is False
            and migration_results.get("destructive_ddl_exact", False)
        ),
        "github_and_app_delivery_blocked": (
            index.get("github_upload_allowed") is False
            and index.get("app_reinstall_allowed") is False
        ),
    }
    delivery_contract_valid = all(delivery_check_results.values())
    execution_state = (
        BLOCKED_PENDING_PROFILE
        if delivery_contract_valid
        else BLOCKED_INVALID_CONTRACT
    )
    result = "PASS_WITH_EXPECTED_BLOCK" if delivery_contract_valid else "FAIL_CLOSED"

    return {
        "schema_version": PHASE4_SCHEMA_VERSION,
        "phase3_schema_version": PHASE3_SCHEMA_VERSION,
        "phase2_schema_version": SCHEMA_VERSION,
        "index_schema_version": INDEX_SCHEMA_VERSION,
        "stage": STAGE,
        "phase": "Phase 4",
        "task_id": PHASE4_TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "delivery_contract_valid": delivery_contract_valid,
        "delivery_check_results": delivery_check_results,
        "phase4_contract_results": phase4_contract_results,
        "result": result,
        "execution_mode": PHASE4_EXECUTION_MODE,
        "execution_ready": False,
        "execution_state": execution_state,
        "stage_review_status": "pending_next_run",
        "next_gate": "IDS-STAGE036-REVIEW-GATE",
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "snapshot_binding": {
            "source": snapshot_source,
            "tracked_snapshot_bound": tracked_snapshot_bound,
            "single_snapshot_reused": True,
            "index_ref": index_path.as_posix(),
            "migration_ref": migration_path.as_posix(),
            "baseline_schema_ref": baseline_schema_path.as_posix(),
            "index_canonical_sha256": canonical_index_sha256,
            "migration_sha256": migration_sha256,
            "baseline_schema_sha256": baseline_schema_sha256,
        },
        "schema_diff": {
            "mode": schema_diff_contract.get("mode"),
            "baseline_schema_ref": schema_diff_contract.get(
                "baseline_schema_ref"
            ),
            "migration_sql_ref": schema_diff_contract.get("migration_sql_ref"),
            "baseline_schema_sha256": baseline_schema_sha256,
            "migration_sha256": migration_sha256,
            "added_table_contracts": schema_diff_contract.get(
                "added_table_contracts", []
            ),
            "candidate_constraint_ids": sorted(EXPECTED_CANDIDATE_CONSTRAINTS),
            "candidate_constraint_count": schema_diff_contract.get(
                "candidate_constraint_count"
            ),
            "existing_foreign_key_count": schema_diff_contract.get(
                "existing_foreign_key_count"
            ),
            "live_schema_diff_result": schema_diff_contract.get(
                "live_schema_diff_result"
            ),
            "live_output_ref": "NOT_AVAILABLE_BY_POLICY_NO_POSTGRESQL_CONNECTION",
        },
        "migration_output": {
            "mode": migration_output_contract.get("mode"),
            "migration_id": migration_output_contract.get("migration_id"),
            "tracked_migration_sha256": migration_sha256,
            "up_down_markers_valid": migration_results.get(
                "ordered_up_down_markers", False
            ),
            "candidate_guards_exact": migration_results.get(
                "candidate_existence_guards_exact", False
            ),
            "rollback_covers_candidates": migration_results.get(
                "rollback_covers_candidates", False
            ),
            "dry_run_required": migration_output_contract.get(
                "dry_run_required"
            ),
            "backup_checkpoint_required": migration_output_contract.get(
                "backup_checkpoint_required"
            ),
            "rollback_required": migration_output_contract.get(
                "rollback_required"
            ),
            "destructive_migration_allowed": migration_output_contract.get(
                "destructive_migration_allowed"
            ),
            "live_migration_result": migration_output_contract.get(
                "live_migration_result"
            ),
            "live_constraint_validation_result": migration_output_contract.get(
                "live_constraint_validation_result"
            ),
            "live_output_ref": "NOT_AVAILABLE_BY_POLICY_NO_MIGRATION_EXECUTION",
        },
        "recovery_test_log": {
            "mode": recovery_log_contract.get("mode"),
            "result": result,
            "execution_ready": False,
            "execution_state": execution_state,
            "scenario_count": len(scenario_results),
            "scenario_results": scenario_results,
            "delivery_check_results": delivery_check_results,
            "live_recovery_smoke_result": recovery_log_contract.get(
                "live_recovery_smoke_result"
            ),
            "live_execution_performed": False,
            "live_log_ref": "NOT_AVAILABLE_BY_POLICY_NO_OWNER_AUTHORIZED_REAL_DATA_PROFILE",
            "owner_message_zh": (
                "静态质量约束合同与十四项场景已验证；没有 owner 授权真实数据 profile，"
                "因此 schema diff、migration、constraint validation、rollback、backup、"
                "restore 和 recovery smoke 均未执行。"
                if delivery_contract_valid
                else "数据库质量约束交付合同无效；已失败关闭，禁止任何 live 数据库动作。"
            ),
        },
        "destructive_migration_confirmation": phase4_contract.get(
            "destructive_migration_confirmation", {}
        ),
        "rollback_steps": phase4_contract.get("rollback_steps", []),
        "backup_restore_steps": phase4_contract.get("backup_restore_steps", []),
        "known_limits": phase4_contract.get("known_limits", []),
        "chinese_owner_feedback": (
            phase4_contract.get("chinese_owner_feedback")
            if delivery_contract_valid
            else "数据库质量约束 Phase 4 交付合同无效；已失败关闭，禁止执行 schema diff、migration、constraint validation、rollback、backup、restore 或 recovery smoke。"
        ),
        "live_execution_performed": False,
        "postgresql_connection_performed": False,
        "migration_dry_run_performed": False,
        "migration_apply_performed": False,
        "constraint_validation_performed": False,
        "rollback_performed": False,
        "backup_performed": False,
        "restore_performed": False,
        "recovery_smoke_performed": False,
        "real_data_profile_executed": False,
        "state_values_seeded": False,
        "runtime_output_written": False,
        "raw_metadata_boundary": phase2_report["raw_metadata_boundary"],
        "scenario_report": scenario_report,
        "phase2_report": phase2_report,
    }


def main() -> int:
    report = build_stage036_delivery_report()
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    checks = [
        report["delivery_contract_valid"],
        all(report["delivery_check_results"].values()),
        all(report["phase4_contract_results"].values()),
        report["result"] == "PASS_WITH_EXPECTED_BLOCK",
        report["execution_ready"] is False,
        report["execution_state"] == BLOCKED_PENDING_PROFILE,
        report["stage_review_status"] == "pending_next_run",
        report["next_gate"] == "IDS-STAGE036-REVIEW-GATE",
        report["github_upload_allowed"] is False,
        report["app_reinstall_allowed"] is False,
        report["live_execution_performed"] is False,
        report["postgresql_connection_performed"] is False,
        report["migration_apply_performed"] is False,
        report["constraint_validation_performed"] is False,
        report["rollback_performed"] is False,
        report["backup_performed"] is False,
        report["restore_performed"] is False,
        report["recovery_smoke_performed"] is False,
        report["real_data_profile_executed"] is False,
        report["state_values_seeded"] is False,
        report["runtime_output_written"] is False,
        report["schema_diff"]["live_schema_diff_result"] == "NOT_EXECUTED",
        report["migration_output"]["live_migration_result"] == "NOT_EXECUTED",
        report["migration_output"]["live_constraint_validation_result"]
        == "NOT_EXECUTED",
        report["recovery_test_log"]["live_recovery_smoke_result"]
        == "NOT_EXECUTED",
        report["scenario_report"]["scenario_validation_valid"],
        report["phase2_report"]["contract_valid"],
    ]
    return 0 if all(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
