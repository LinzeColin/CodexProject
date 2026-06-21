#!/usr/bin/env python3
"""Validate that v5 production blockers are registered in EEI governance."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

EXPECTED_BLOCKERS = {
    "ARCH-001": ("T1300", "A201"),
    "ARCH-003": ("T1301", "A202"),
    "ARCH-002": ("T1302", "A203"),
    "STRESS-010": ("T1303", "A204"),
    "STRESS-007": ("T1304", "A206"),
    "STRESS-011": ("T1305", "A207"),
    "STRESS-008": ("T1306", "A208"),
    "STRESS-012": ("T1307", "A209"),
    "UX-012": ("T1308", "A211"),
}

EXPECTED_TASKS = {
    "T1300": "A201",
    "T1301": "A202",
    "T1302": "A203",
    "T1303": "A204",
    "T1304": "A206",
    "T1305": "A207",
    "T1306": "A208",
    "T1307": "A209",
    "T1308": "A211",
    "T1309": "A210",
}

IMPLEMENTED_TASKS = {
    "T1300": "A201",
    "T1305": "A207",
    "T1306": "A208",
    "T1308": "A211",
}

PARTIAL_TASKS = {
    "T1301": "A202",
    "T1302": "A203",
    "T1303": "A204",
    "T1304": "A206",
    "T1307": "A209",
    "T1309": "A210",
}

PARTIAL_ACCEPTANCE_IDS = {"A202", "A203", "A204", "A205", "A206", "A209", "A210"}

IMPLEMENTED_EVIDENCE = {
    "T1300": {
        "infra/db/migrations/0003_production_fact_version_layers/up.sql",
        "infra/db/migrations/0003_production_fact_version_layers/down.sql",
        "scripts/check_database_schema.py",
        "tests/integration/test_database_migrations.py",
    },
    "T1306": {
        "scripts/run_scale_benchmarks.py",
        "scripts/run_browser_scale_benchmarks.mjs",
        "tests/unit/test_scale_benchmarks.py",
        "artifacts/tests/a208/t1306_scale_benchmark_smoke.json",
        "artifacts/tests/a208/t1306_scale_benchmark_operator_contract.json",
        "artifacts/tests/a208/t1306_browser_runtime_benchmark.json",
    },
    "T1305": {
        "infra/db/migrations/0008_server_saved_views/up.sql",
        "infra/db/migrations/0008_server_saved_views/down.sql",
        ".env.example",
        "apps/api/app/domain.py",
        "apps/api/app/domain_repository.py",
        "apps/api/app/main.py",
        "apps/api/app/settings.py",
        "apps/web/src/app/page.tsx",
        "apps/web/src/app/saved-view-client.ts",
        "Makefile",
        "playwright.live.config.ts",
        "scripts/run_live_e2e_api.sh",
        "scripts/check_database_schema.py",
        "specs/api_contract.yaml",
        "tests/integration/test_database_migrations.py",
        "tests/e2e/state-contract.spec.ts",
        "tests/e2e/saved-view-live.spec.ts",
        "tests/unit/test_api_health.py",
        "artifacts/tests/a207/t1305_frontend_saved_view_api_adapter_contract.json",
        "artifacts/tests/a207/t1305_live_saved_view_multisession_e2e_contract.json",
        "artifacts/tests/a207/t1305_server_saved_view_conflict_recovery_contract.json",
        "artifacts/tests/a207/t1305_saved_view_trusted_gateway_contract.json",
    },
    "T1308": {
        "apps/web/src/app/workspace-context.tsx",
        "apps/web/src/app/workspace-navigation.tsx",
        "apps/web/src/app/model-activation-client.ts",
        "apps/web/src/app/explore-api-client.ts",
        "apps/web/src/app/production-data-client.ts",
        "apps/web/src/app/page.tsx",
        "scripts/run_live_e2e_api.sh",
        "tests/e2e/home.spec.ts",
        "tests/e2e/saved-view-live.spec.ts",
        "tests/e2e/state-contract.spec.ts",
        "artifacts/tests/a211/t1308_frontend_workspace_context_contract.json",
    },
}

PARTIAL_EVIDENCE = {
    "T1301": {
        "infra/db/migrations/0004_curated_ingestion_audit_layers/up.sql",
        "infra/db/migrations/0004_curated_ingestion_audit_layers/down.sql",
        "infra/db/migrations/0005_relationship_fact_candidates/up.sql",
        "infra/db/migrations/0005_relationship_fact_candidates/down.sql",
        "infra/db/migrations/0011_operator_source_capture_constraints/up.sql",
        "infra/db/migrations/0011_operator_source_capture_constraints/down.sql",
        "data/golden_vertical_fact_candidates.json",
        "scripts/load_curated_ingestion_anchors.py",
        "scripts/fetch_official_source_full_text.py",
        "scripts/load_operator_source_captures.py",
        "scripts/publish_reviewed_relationship_facts.py",
        "tests/fixtures/official_source_full_text/nvidia_official_full_text_dry_run.json",
        "tests/fixtures/operator_source_captures/nvidia_operator_source_captures.json",
        "tests/fixtures/golden_vertical_review_decisions.json",
        "tests/fixtures/golden_vertical_owner_signoff_decisions.json",
        "scripts/check_database_schema.py",
        "tests/integration/test_database_migrations.py",
        "artifacts/tests/a202/t1301_curated_official_ingestion_contract.json",
        "artifacts/tests/a202/t1301_official_full_text_dry_run_contract.json",
        "artifacts/tests/a202/t1301_operator_source_capture_contract.json",
    },
    "T1302": {
        "apps/api/app/domain.py",
        "apps/api/app/domain_repository.py",
        "apps/web/src/app/explore-api-client.ts",
        "apps/web/src/app/page.tsx",
        "specs/api_contract.yaml",
        "tests/integration/test_database_migrations.py",
        "tests/e2e/state-contract.spec.ts",
        "artifacts/tests/a203/t1302_production_api_graph_scoring_contract.json",
    },
    "T1303": {
        "infra/db/migrations/0006_model_activation_refresh_state/up.sql",
        "infra/db/migrations/0006_model_activation_refresh_state/down.sql",
        "infra/db/migrations/0009_transactional_outbox/up.sql",
        "infra/db/migrations/0009_transactional_outbox/down.sql",
        "apps/api/app/domain.py",
        "apps/api/app/domain_repository.py",
        "scripts/check_database_schema.py",
        "scripts/load_seed_catalogs.py",
        "specs/api_contract.yaml",
        "tests/integration/test_database_migrations.py",
        "apps/web/src/app/model-activation-client.ts",
        "apps/web/src/app/use-analysis-context.ts",
        "apps/web/src/app/page.tsx",
        "tests/e2e/state-contract.spec.ts",
        "artifacts/tests/a204/t1303_transactional_model_activation_contract.json",
        "artifacts/tests/a205/t1303_atomic_refresh_context_contract.json",
    },
    "T1304": {
        "infra/db/migrations/0007_scheduler_job_queue/up.sql",
        "infra/db/migrations/0007_scheduler_job_queue/down.sql",
        "infra/db/migrations/0009_transactional_outbox/up.sql",
        "infra/db/migrations/0009_transactional_outbox/down.sql",
        "scripts/job_scheduler.py",
        "scripts/check_database_schema.py",
        "tests/integration/test_database_migrations.py",
        "artifacts/tests/a206/t1304_scheduler_retry_dead_letter_contract.json",
    },
    "T1307": {
        "scripts/run_soak_smoke.mjs",
        "scripts/run_operator_soak.mjs",
        "scripts/validate_operator_soak_evidence.py",
        "artifacts/tests/a209/t1307_soak_smoke.json",
        "artifacts/tests/a209/t1307_operator_soak_readiness.json",
        "artifacts/tests/a209/t1307_operator_soak_readiness.checkpoints.jsonl",
        "artifacts/tests/a209/t1307_operator_soak_evidence_validation.json",
    },
    "T1309": {
        "config/brand_policy.yaml",
        "data/brand_name_conflict_register.csv",
        "brand/BRAND_AND_COMPETITIVE_LANDSCAPE_RESEARCH.md",
        "artifacts/tests/a210/t1309_brand_clearance_preflight_contract.json",
        "scripts/validate_brand_clearance.py",
    },
}

EXPECTED_PARAMETERS = {
    "database.migration_lock_timeout_seconds",
    "database.rollback_required",
    "ingestion.entity_resolution_min_confidence",
    "ingestion.evidence_independent_source_min",
    "scheduler.lease_ttl_seconds",
    "scheduler.heartbeat_interval_seconds",
    "scheduler.max_retry_attempts",
    "scheduler.dead_letter_after_attempts",
    "saved_view.conflict_retry_limit",
    "saved_view.gateway_secret_required",
    "saved_view.identity_mode",
    "saved_view.signature_ttl_seconds",
    "benchmark.scale_10k_p95_ms",
    "benchmark.scale_100k_p95_ms",
    "benchmark.scale_1m_p95_ms",
    "soak.short_duration_hours",
    "soak.long_duration_hours",
    "soak.operator_window_seconds",
    "brand.clearance_required",
}


def read_csv(path: str) -> list[dict[str, str]]:
    with (ROOT / path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate_brand_policy() -> dict[str, Any]:
    policy_text = read_text("config/brand_policy.yaml")
    require("system_name_zh: 商域图谱" in policy_text, "EEI Chinese name changed")
    require(
        "system_name_en: Enterprise Ecosystem Intelligence" in policy_text,
        "EEI English name changed",
    )
    require("system_abbreviation: EEI" in policy_text, "EEI abbreviation changed")
    for phrase in [
        "CN/US/EU/UK/AU trademark knockout",
        "legal counsel sign-off or explicit risk waiver",
    ]:
        require(phrase in policy_text, f"brand release gate missing {phrase}")
    return {
        "system_name_zh": "商域图谱",
        "system_name_en": "Enterprise Ecosystem Intelligence",
        "release_gate": "BRAND-G1",
    }


def validate_review_issue_mapping() -> dict[str, Any]:
    issues = {row["issue_id"]: row for row in read_csv("data/review_issue_register.csv")}
    tasks = {row["task_id"]: row for row in read_csv("data/task_backlog.csv")}
    acceptance = {row["acceptance_id"]: row for row in read_csv("data/acceptance_matrix.csv")}

    for issue_id, (task_id, acceptance_id) in EXPECTED_BLOCKERS.items():
        issue = issues.get(issue_id)
        require(issue is not None, f"missing v5 issue {issue_id}")
        require(
            issue["blocks_production_merge"] == "YES",
            f"{issue_id} must block production merge",
        )
        require(issue["status"] == "OPEN_PRODUCTION", f"{issue_id} status drifted")
        require(task_id in tasks, f"{issue_id} missing mapped task {task_id}")
        require(acceptance_id in acceptance, f"{issue_id} missing acceptance {acceptance_id}")

    brand_task = tasks.get("T1309", {})
    require(brand_task.get("acceptance_ids") == "A210", "T1309 must map to A210")
    return {"mapped_v5_blockers": len(EXPECTED_BLOCKERS), "tasks_checked": len(EXPECTED_TASKS)}


def validate_task_acceptance_status() -> dict[str, Any]:
    tasks = {row["task_id"]: row for row in read_csv("data/task_backlog.csv")}
    acceptance = {row["acceptance_id"]: row for row in read_csv("data/acceptance_matrix.csv")}

    for task_id, acceptance_id in EXPECTED_TASKS.items():
        task = tasks.get(task_id)
        require(task is not None, f"missing task {task_id}")
        require(acceptance_id in task["acceptance_ids"], f"{task_id} missing {acceptance_id}")
        if task_id in IMPLEMENTED_TASKS:
            require(task["status"] == "DONE", f"{task_id} must be DONE once implemented")
            for evidence_path in IMPLEMENTED_EVIDENCE[task_id]:
                require((ROOT / evidence_path).is_file(), f"{task_id} missing {evidence_path}")
        elif task_id in PARTIAL_TASKS:
            require(
                task["status"] == "IN PROGRESS",
                f"{task_id} must be IN PROGRESS while partially implemented",
            )
            for evidence_path in PARTIAL_EVIDENCE[task_id]:
                require((ROOT / evidence_path).is_file(), f"{task_id} missing {evidence_path}")
        else:
            require(task["status"] == "NOT STARTED", f"{task_id} must remain NOT STARTED")

    for acceptance_id in [f"A{number}" for number in range(201, 212)]:
        row = acceptance.get(acceptance_id)
        require(row is not None, f"missing acceptance {acceptance_id}")
        if acceptance_id in IMPLEMENTED_TASKS.values():
            require(row["status"] == "DONE", f"{acceptance_id} must be DONE once implemented")
        elif acceptance_id in PARTIAL_ACCEPTANCE_IDS:
            require(
                row["status"] == "IN PROGRESS",
                f"{acceptance_id} must be IN PROGRESS while partially implemented",
            )
        else:
            require(row["status"] == "NOT STARTED", f"{acceptance_id} must remain NOT STARTED")
    return {
        "tasks": len(EXPECTED_TASKS),
        "acceptance": 11,
        "implemented_tasks": len(IMPLEMENTED_TASKS),
        "partial_tasks": len(PARTIAL_TASKS),
        "not_done_tasks": len(EXPECTED_TASKS) - len(IMPLEMENTED_TASKS),
        "not_started_tasks": len(EXPECTED_TASKS) - len(IMPLEMENTED_TASKS) - len(PARTIAL_TASKS),
    }


def validate_parameters_and_docs() -> dict[str, Any]:
    parameters = {row["parameter_key"] for row in read_csv("data/parameter_catalog.csv")}
    missing_parameters = sorted(EXPECTED_PARAMETERS - parameters)
    require(not missing_parameters, f"missing parameters: {missing_parameters}")

    required_docs = {
        "REVIEW_AND_ITERATION_INDEX.md",
        "TEST_STRATEGY.md",
        "CONTINUITY_PLAN.md",
        "docs/phase/V5_TASK_PACK_SYNCHRONIZATION.md",
        "brand/BRAND_AND_COMPETITIVE_LANDSCAPE_RESEARCH.md",
    }
    missing_docs = sorted(path for path in required_docs if not (ROOT / path).is_file())
    require(not missing_docs, f"missing v5 sync docs: {missing_docs}")

    pursuing_goal = read_text("PURSUING_GOAL.md")
    require("Target product version: v0.1" in pursuing_goal, "v0.1 target wording missing")
    require("PostgreSQL production database" in pursuing_goal, "MVP blocker wording missing")
    return {"parameters": len(EXPECTED_PARAMETERS), "docs": len(required_docs)}


def validate_manifest_counts() -> dict[str, int]:
    manifest = {row["catalog_path"]: row for row in read_csv("data/data_catalog_manifest.csv")}
    actual_counts = {
        "data/review_issue_register.csv": len(read_csv("data/review_issue_register.csv")),
        "data/brand_name_conflict_register.csv": len(
            read_csv("data/brand_name_conflict_register.csv")
        ),
        "data/competitive_product_landscape.csv": len(
            read_csv("data/competitive_product_landscape.csv")
        ),
    }
    for path, actual in actual_counts.items():
        require(path in manifest, f"manifest missing {path}")
        require(int(manifest[path]["row_count"]) == actual, f"manifest count drift: {path}")
    return actual_counts


def main() -> int:
    result = {
        "valid": True,
        "brand_policy": validate_brand_policy(),
        "review_issue_mapping": validate_review_issue_mapping(),
        "task_acceptance_status": validate_task_acceptance_status(),
        "parameters_and_docs": validate_parameters_and_docs(),
        "manifest_counts": validate_manifest_counts(),
    }
    print("V5 production readiness synchronization validation: PASS")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, csv.Error) as exc:
        print(f"V5 production readiness synchronization validation: FAIL - {exc}")
        raise SystemExit(1) from None
