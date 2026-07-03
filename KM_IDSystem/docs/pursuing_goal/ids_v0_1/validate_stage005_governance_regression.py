"""Validate the IDS STAGE-005 governance-regression boundary."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Iterable


STAGE = "STAGE-005"
ACCEPTANCE_ID = "ACC-STAGE-005"
CURRENT_PRODUCT_NAME = "IDS / Industrial Data System"
ACCEPTED_NAMES = (CURRENT_PRODUCT_NAME, "ProductMetaDatabase", "FinanceMetaDatabase")

SURFACE_PREFIXES = {
    "README": ("KM_IDSystem/README.md",),
    "handoff_docs": ("KM_IDSystem/docs/HANDOFF.md",),
    "governance": ("KM_IDSystem/docs/governance/",),
    "ids_pursuing_goal": ("KM_IDSystem/docs/pursuing_goal/ids_v0_1/",),
    "scripts": ("KM_IDSystem/scripts/",),
    "backend_tests": ("KM_IDSystem/backend/tests/",),
    "backend_app": ("KM_IDSystem/backend/app/",),
    "frontend": ("KM_IDSystem/frontend/",),
    "app_bundle": ("KM_IDSystem/app_bundle/",),
    "product_meta_database": ("KM_IDSystem/product_meta_database/",),
}

REQUIRED_FILES = (
    "KM_IDSystem/README.md",
    "KM_IDSystem/docs/HANDOFF.md",
    "KM_IDSystem/docs/governance/roadmap.yaml",
    "KM_IDSystem/docs/governance/events.jsonl",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/V0_1_ROOT_LOCK.yaml",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/IDS_METADATA_RAW_DATA_BOUNDARY.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH011_020_UPLOAD_LOCK.yaml",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH011_020_REVIEW_GATE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH011_020_UPLOAD_GATE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH021_030_UPLOAD_LOCK.yaml",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH021_030_REVIEW_GATE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH021_030_UPLOAD_GATE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/V0_1_STAGE_EXECUTION_INDEX.csv",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/V0_1_STAGE_EXECUTION_INDEX.json",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH001_010_UPLOAD_LOCK.yaml",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE001_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE002_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE003_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE004_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE005_ENTRY_CONTRACT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE005_PHASE1_SCOPE_BOUNDARY.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE005_PHASE2_GOVERNANCE_REGRESSION.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE005_PHASE3_VALIDATION_SCAN.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE005_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/validate_stage005_governance_regression.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage005_governance_regression.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/validate_stage003_finance_meta_rename.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/validate_stage004_legacy_name_scan.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage003_finance_meta_rename.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage004_legacy_name_scan.py",
    "KM_IDSystem/product_meta_database/validate_product_meta_database.py",
    "KM_IDSystem/product_meta_database/tests/test_contract.py",
    "KM_IDSystem/backend/tests/test_stage001_naming_contract.py",
    "KM_IDSystem/scripts/check_safe_mode_baseline.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE011_PHASE3_SCENARIO_VALIDATION.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE011_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE012_ENTRY_CONTRACT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE012_PHASE1_SCOPE_BOUNDARY.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE012_PHASE2_READONLY_IDENTITY_SLICE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE012_PHASE3_SCENARIO_VALIDATION.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE012_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE013_ENTRY_CONTRACT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE013_PHASE1_SCOPE_BOUNDARY.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE013_PHASE2_FILE_FINGERPRINT_SLICE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE013_PHASE3_SCENARIO_VALIDATION.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE013_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE014_ENTRY_CONTRACT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE014_PHASE1_SCOPE_BOUNDARY.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE014_PHASE2_MANIFEST_SLICE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE014_PHASE3_SCENARIO_VALIDATION.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE014_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE015_ENTRY_CONTRACT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE015_PHASE1_SCOPE_BOUNDARY.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE015_PHASE2_DUPLICATE_SLICE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE015_PHASE3_SCENARIO_VALIDATION.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE015_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE016_ENTRY_CONTRACT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE016_PHASE1_SCOPE_BOUNDARY.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE016_PHASE2_IMPORT_IDEMPOTENCY_SLICE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE016_PHASE3_SCENARIO_VALIDATION.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE016_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE017_ENTRY_CONTRACT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE017_PHASE1_SCOPE_BOUNDARY.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE017_PHASE2_REGRESSION_SLICE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE017_PHASE3_SCENARIO_VALIDATION.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE017_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE018_ENTRY_CONTRACT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE018_PHASE1_SCOPE_BOUNDARY.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE018_PHASE2_PREFLIGHT_SLICE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE018_PHASE3_SCENARIO_VALIDATION.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE018_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE019_ENTRY_CONTRACT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE019_PHASE1_SCOPE_BOUNDARY.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE019_PHASE2_RISK_ESTIMATOR_SLICE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE019_PHASE3_SCENARIO_VALIDATION.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE019_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE020_ENTRY_CONTRACT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE020_PHASE1_SCOPE_BOUNDARY.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE020_PHASE2_COST_ESTIMATOR_SLICE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE020_PHASE3_SCENARIO_VALIDATION.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE020_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE021_ENTRY_CONTRACT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE021_PHASE1_SCOPE_BOUNDARY.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE021_PHASE2_PREFLIGHT_CONFIRMATION_UI_SLICE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE021_PHASE3_SCENARIO_VALIDATION.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE021_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE022_ENTRY_CONTRACT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE022_PHASE1_SCOPE_BOUNDARY.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE022_PHASE2_DATA_PRIORITY_QUEUE_SLICE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE022_PHASE3_SCENARIO_VALIDATION.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE022_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE023_ENTRY_CONTRACT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE023_PHASE1_SCOPE_BOUNDARY.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE023_PHASE2_PREFLIGHT_SCENARIO_TESTS_SLICE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE023_PHASE3_SCENARIO_VALIDATION.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE023_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE024_ENTRY_CONTRACT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE024_PHASE1_SCOPE_BOUNDARY.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE024_PHASE2_SAFE_EXTRACTION_SLICE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE024_PHASE3_SCENARIO_VALIDATION.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE024_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE025_ENTRY_CONTRACT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE025_PHASE1_SCOPE_BOUNDARY.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE025_PHASE2_SAFE_EXTRACTION_ENGINE_SLICE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE025_PHASE3_SCENARIO_VALIDATION.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE025_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE026_ENTRY_CONTRACT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE026_PHASE1_SCOPE_BOUNDARY.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE026_PHASE2_ARCHIVE_MANIFEST_SLICE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE026_PHASE3_SCENARIO_VALIDATION.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE026_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE027_ENTRY_CONTRACT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE027_PHASE1_SCOPE_BOUNDARY.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE027_PHASE2_REINGEST_EXTRACTED_FILES_SLICE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE027_PHASE3_SCENARIO_VALIDATION.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE027_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE028_ENTRY_CONTRACT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE028_PHASE1_SCOPE_BOUNDARY.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE028_PHASE2_ARCHIVE_ADVERSARIAL_SLICE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE028_PHASE3_SCENARIO_VALIDATION.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE028_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE029_ENTRY_CONTRACT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE029_PHASE1_SCOPE_BOUNDARY.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE029_PHASE2_CLEANUP_ALLOWLIST_SLICE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE029_PHASE3_SCENARIO_VALIDATION.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE029_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE030_ENTRY_CONTRACT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE030_PHASE1_SCOPE_BOUNDARY.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE030_PHASE2_POSTGRES_CONTROL_PLANE_SLICE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE030_PHASE3_SCENARIO_VALIDATION.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE030_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE031_ENTRY_CONTRACT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE031_PHASE1_SCOPE_BOUNDARY.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE031_PHASE2_SCHEMA_MIGRATION_SAFETY_SLICE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE031_PHASE3_SCENARIO_VALIDATION.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE031_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/schema_migration_safety/stage031_migration_safety_index.json",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/postgresql_control_plane/001_control_plane_schema.sql",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/postgresql_control_plane/control_plane_schema_index.json",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage011_safe_mode_baseline.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage012_original_raw_identity.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage013_file_fingerprint.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage014_manifest_generation.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage015_duplicate_detection.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage016_import_idempotency.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage017_original_regression.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage018_import_preflight.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage019_import_risk_estimator.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage020_import_cost_estimator.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage021_preflight_confirmation_ui.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage022_data_priority_queue.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage023_preflight_scenario_tests.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage024_archive_threat_model.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage025_safe_extraction_engine.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage026_archive_manifest.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage027_reingest_extracted_files.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage028_archive_adversarial_tests.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage029_archive_cleanup_allowlist.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage030_postgresql_control_plane.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage031_schema_migration_safety.py",
    "KM_IDSystem/scripts/check_original_raw_identity.py",
    "KM_IDSystem/scripts/check_file_fingerprint.py",
    "KM_IDSystem/scripts/check_manifest_generation.py",
    "KM_IDSystem/scripts/check_duplicate_files.py",
    "KM_IDSystem/scripts/check_import_idempotency.py",
    "KM_IDSystem/scripts/check_original_regression.py",
    "KM_IDSystem/scripts/check_import_preflight.py",
    "KM_IDSystem/scripts/check_import_risk_estimator.py",
    "KM_IDSystem/scripts/check_import_cost_estimator.py",
    "KM_IDSystem/scripts/check_preflight_confirmation_ui.py",
    "KM_IDSystem/scripts/check_data_priority_queue.py",
    "KM_IDSystem/scripts/check_preflight_scenario_tests.py",
    "KM_IDSystem/scripts/check_archive_threat_model.py",
    "KM_IDSystem/scripts/check_safe_extraction_engine.py",
    "KM_IDSystem/scripts/check_archive_manifest.py",
    "KM_IDSystem/scripts/check_reingest_extracted_files.py",
    "KM_IDSystem/scripts/check_archive_adversarial_tests.py",
    "KM_IDSystem/scripts/check_archive_cleanup_allowlist.py",
    "KM_IDSystem/scripts/check_postgresql_control_plane.py",
    "KM_IDSystem/scripts/check_schema_migration_safety.py",
    "KM_IDSystem/scripts/build_app_bundle.sh",
    "KM_IDSystem/scripts/diagnose_app_entry.sh",
    "KM_IDSystem/scripts/run_local_services.sh",
    "KM_IDSystem/scripts/smoke_test.sh",
    "KM_IDSystem/scripts/install_app_entries.sh",
    "KM_IDSystem/scripts/stop_local_services.sh",
)

REQUIRED_EVENT_IDS = (
    "EVT-IDS-V0_1-STAGE001-P4-20260702-001",
    "EVT-IDS-V0_1-STAGE002-P4-20260702-001",
    "EVT-IDS-V0_1-STAGE003-P4-20260702-001",
    "EVT-IDS-V0_1-STAGE004-P4-20260702-001",
    "EVT-IDS-V0_1-STAGE005-P1-20260702-001",
    "EVT-IDS-V0_1-STAGE005-P2-20260702-001",
    "EVT-IDS-V0_1-STAGE005-P3-20260702-001",
    "EVT-IDS-V0_1-STAGE005-P4-20260702-001",
    "EVT-IDS-V0_1-BATCH-001-010-IDS-METADATA-BOUNDARY-20260702-001",
    "EVT-IDS-V0_1-STAGE018-P2-20260702-001",
    "EVT-IDS-V0_1-STAGE018-P3-20260702-001",
    "EVT-IDS-V0_1-STAGE018-P4-20260702-001",
    "EVT-IDS-V0_1-STAGE019-P1-20260702-001",
    "EVT-IDS-V0_1-STAGE019-P2-20260702-001",
    "EVT-IDS-V0_1-STAGE019-P3-20260702-001",
    "EVT-IDS-V0_1-STAGE019-P4-20260702-001",
    "EVT-IDS-V0_1-STAGE020-P1-20260702-001",
    "EVT-IDS-V0_1-STAGE020-P2-20260702-001",
    "EVT-IDS-V0_1-STAGE020-P3-20260702-001",
    "EVT-IDS-V0_1-STAGE020-P4-20260702-001",
    "EVT-IDS-V0_1-BATCH-011-020-REVIEW-GATE-20260702-001",
    "EVT-IDS-V0_1-BATCH-011-020-UPLOAD-GATE-20260702-001",
    "EVT-IDS-V0_1-BATCH-011-020-MAIN-MERGED-20260702-001",
    "EVT-IDS-V0_1-STAGE021-P1-20260702-001",
    "EVT-IDS-V0_1-STAGE021-P2-20260702-001",
    "EVT-IDS-V0_1-STAGE021-P3-20260702-001",
    "EVT-IDS-V0_1-STAGE021-P4-20260702-001",
    "EVT-IDS-V0_1-STAGE022-P1-20260702-001",
    "EVT-IDS-V0_1-STAGE022-P2-20260702-001",
    "EVT-IDS-V0_1-STAGE022-P3-20260703-001",
    "EVT-IDS-V0_1-STAGE022-P4-20260703-001",
    "EVT-IDS-V0_1-STAGE023-P1-20260703-001",
    "EVT-IDS-V0_1-STAGE023-P2-20260703-001",
    "EVT-IDS-V0_1-STAGE023-P3-20260703-001",
    "EVT-IDS-V0_1-STAGE023-P4-20260703-001",
    "EVT-IDS-V0_1-STAGE024-P1-20260703-001",
    "EVT-IDS-V0_1-STAGE024-P2-20260703-001",
    "EVT-IDS-V0_1-STAGE024-P3-20260703-001",
    "EVT-IDS-V0_1-STAGE024-P4-20260703-001",
    "EVT-IDS-V0_1-STAGE025-P1-20260703-001",
    "EVT-IDS-V0_1-STAGE025-P2-20260703-001",
    "EVT-IDS-V0_1-STAGE025-P3-20260703-001",
    "EVT-IDS-V0_1-STAGE025-P4-20260703-001",
    "EVT-IDS-V0_1-STAGE026-P1-20260703-001",
    "EVT-IDS-V0_1-STAGE026-P2-20260703-001",
    "EVT-IDS-V0_1-STAGE026-P3-20260703-001",
    "EVT-IDS-V0_1-STAGE026-P4-20260703-001",
    "EVT-IDS-V0_1-STAGE027-P1-20260703-001",
    "EVT-IDS-V0_1-STAGE027-P2-20260703-001",
    "EVT-IDS-V0_1-STAGE027-P3-20260703-001",
    "EVT-IDS-V0_1-STAGE027-P4-20260703-001",
    "EVT-IDS-V0_1-STAGE028-P1-20260703-001",
    "EVT-IDS-V0_1-STAGE028-P2-20260703-001",
    "EVT-IDS-V0_1-STAGE028-P3-20260703-001",
    "EVT-IDS-V0_1-STAGE028-P4-20260703-001",
    "EVT-IDS-V0_1-STAGE029-P1-20260703-001",
    "EVT-IDS-V0_1-STAGE029-P2-20260703-001",
    "EVT-IDS-V0_1-STAGE029-P3-20260703-001",
    "EVT-IDS-V0_1-STAGE029-P4-20260703-001",
    "EVT-IDS-V0_1-STAGE030-P1-20260703-001",
    "EVT-IDS-V0_1-STAGE030-P2-20260703-001",
    "EVT-IDS-V0_1-STAGE030-P3-20260703-001",
    "EVT-IDS-V0_1-STAGE030-P4-20260703-001",
    "EVT-IDS-V0_1-BATCH-021-030-REVIEW-GATE-20260703-001",
    "EVT-IDS-V0_1-BATCH-021-030-UPLOAD-GATE-20260703-001",
    "EVT-IDS-V0_1-BATCH-021-030-MAIN-MERGED-20260703-001",
    "EVT-IDS-V0_1-STAGE031-P1-20260703-001",
    "EVT-IDS-V0_1-STAGE031-P2-20260703-001",
    "EVT-IDS-V0_1-STAGE031-P3-20260703-001",
    "EVT-IDS-V0_1-STAGE031-P4-20260703-001",
)

FORBIDDEN_RUNTIME_PREFIXES = (
    "KM_IDSystem/data/",
    "KM_IDSystem/reports/",
    "KM_IDSystem/outputs/",
    "KM_IDSystem/.venv/",
    "KM_IDSystem/frontend/node_modules/",
    "KM_IDSystem/frontend/dist/",
)

ALLOWED_CHANGED_PATHS = {
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH001_010_UPLOAD_LOCK.yaml",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH001_010_UPLOAD_GATE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH011_020_UPLOAD_LOCK.yaml",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH011_020_REVIEW_GATE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH011_020_UPLOAD_GATE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH021_030_UPLOAD_LOCK.yaml",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH021_030_REVIEW_GATE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH021_030_UPLOAD_GATE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/V0_1_ROOT_LOCK.yaml",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/IDS_METADATA_RAW_DATA_BOUNDARY.md",
    "KM_IDSystem/scripts/check_safe_mode_baseline.py",
    "KM_IDSystem/scripts/check_manifest_generation.py",
    "KM_IDSystem/scripts/check_duplicate_files.py",
    "KM_IDSystem/scripts/check_import_idempotency.py",
    "KM_IDSystem/scripts/check_original_regression.py",
    "KM_IDSystem/scripts/check_import_preflight.py",
    "KM_IDSystem/scripts/check_import_risk_estimator.py",
    "KM_IDSystem/scripts/check_import_cost_estimator.py",
    "KM_IDSystem/scripts/check_safe_extraction_engine.py",
    "KM_IDSystem/scripts/check_archive_manifest.py",
    "KM_IDSystem/scripts/check_reingest_extracted_files.py",
    "KM_IDSystem/scripts/check_archive_adversarial_tests.py",
    "KM_IDSystem/scripts/check_archive_cleanup_allowlist.py",
    "KM_IDSystem/scripts/check_postgresql_control_plane.py",
    "KM_IDSystem/scripts/check_schema_migration_safety.py",
    "KM_IDSystem/scripts/build_app_bundle.sh",
    "KM_IDSystem/scripts/diagnose_app_entry.sh",
    "KM_IDSystem/scripts/install_app_entries.sh",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE021_ENTRY_CONTRACT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE021_PHASE1_SCOPE_BOUNDARY.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE021_PHASE2_PREFLIGHT_CONFIRMATION_UI_SLICE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE021_PHASE3_SCENARIO_VALIDATION.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE021_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage021_preflight_confirmation_ui.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE022_ENTRY_CONTRACT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE022_PHASE1_SCOPE_BOUNDARY.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE022_PHASE2_DATA_PRIORITY_QUEUE_SLICE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE022_PHASE3_SCENARIO_VALIDATION.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE022_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage022_data_priority_queue.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE023_ENTRY_CONTRACT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE023_PHASE1_SCOPE_BOUNDARY.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE023_PHASE2_PREFLIGHT_SCENARIO_TESTS_SLICE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE023_PHASE3_SCENARIO_VALIDATION.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE023_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage023_preflight_scenario_tests.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE024_ENTRY_CONTRACT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE024_PHASE1_SCOPE_BOUNDARY.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE024_PHASE2_SAFE_EXTRACTION_SLICE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage024_archive_threat_model.py",
    "KM_IDSystem/scripts/check_preflight_scenario_tests.py",
    "KM_IDSystem/scripts/check_archive_threat_model.py",
    "KM_IDSystem/scripts/check_preflight_confirmation_ui.py",
    "KM_IDSystem/scripts/check_data_priority_queue.py",
    "KM_IDSystem/docs/governance/roadmap.yaml",
    "KM_IDSystem/docs/governance/events.jsonl",
    "KM_IDSystem/功能清单.md",
    "KM_IDSystem/开发记录.md",
    "KM_IDSystem/模型参数文件.md",
}
ALLOWED_CHANGED_PREFIXES = (
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE005_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE011_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE012_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE013_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE014_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE015_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE016_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE017_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE018_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE019_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE020_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE022_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE023_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE024_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE025_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE026_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE027_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE028_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE029_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE030_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE031_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/validate_stage005_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage005_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage011_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage012_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage013_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage014_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage015_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage016_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage017_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage018_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage019_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage020_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage022_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage023_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage024_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage025_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage026_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage027_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage028_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage029_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage030_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage031_",
    "KM_IDSystem/scripts/check_original_raw_identity.py",
    "KM_IDSystem/scripts/check_file_fingerprint.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/postgresql_control_plane/",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/schema_migration_safety/",
)


def _repo_root(root: Path) -> Path:
    return root.parent


def _git_ls_files(root: Path) -> list[str]:
    try:
        output = subprocess.check_output(
            ["git", "-c", "core.quotePath=false", "ls-files", root.name],
            cwd=_repo_root(root),
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return [
            path.relative_to(_repo_root(root)).as_posix()
            for path in root.rglob("*")
            if path.is_file()
        ]
    return [line for line in output.splitlines() if line.strip()]


def _git_changed_paths(root: Path) -> list[str]:
    try:
        output = subprocess.check_output(
            ["git", "-c", "core.quotePath=false", "status", "--porcelain"],
            cwd=_repo_root(root),
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return []
    return [line[3:] for line in output.splitlines() if line.strip()]


def _iter_text_files(root: Path, tracked_paths: Iterable[str]) -> Iterable[tuple[str, Path]]:
    repo_root = _repo_root(root)
    for rel_path in tracked_paths:
        path = repo_root / rel_path
        if not path.is_file():
            continue
        try:
            path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        yield rel_path, path


def is_forbidden_runtime_path(path: str) -> bool:
    return path.startswith(FORBIDDEN_RUNTIME_PREFIXES)


def _is_allowed_changed_path(path: str) -> bool:
    return path in ALLOWED_CHANGED_PATHS or path.startswith(ALLOWED_CHANGED_PREFIXES)


def classify_governance_error(line: str) -> str:
    root_missing_markers = (
        "[ERROR] root: Missing file: governance/schemas/",
        "[ERROR] root: Missing file: tests/governance/",
        "[ERROR] root: Missing file: .github/",
        "[ERROR] root: Missing file: .agents/",
        "[ERROR] root: Missing file: .codex/",
    )
    registered_project_marker = "Registered project path missing:"
    if line.startswith(root_missing_markers) or registered_project_marker in line:
        return "sparse_worktree_diagnostic"
    if "KM_IDSystem" in line:
        return "project_regression"
    return "other"


def _parse_events(path: Path) -> tuple[list[dict], list[str]]:
    events: list[dict] = []
    errors: list[str] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError as exc:
            errors.append(f"{path.as_posix()}:{lineno}:{exc.msg}")
    return events, errors


def _surface_counts(tracked_paths: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for surface, prefixes in SURFACE_PREFIXES.items():
        counts[surface] = sum(
            1
            for path in tracked_paths
            if any(path == prefix.rstrip("/") or path.startswith(prefix) for prefix in prefixes)
        )
    return counts


def _text_checks(root: Path, tracked_paths: list[str]) -> dict[str, int]:
    hits = {name: 0 for name in ACCEPTED_NAMES}
    for _rel_path, path in _iter_text_files(root, tracked_paths):
        text = path.read_text(encoding="utf-8")
        for name in ACCEPTED_NAMES:
            hits[name] += text.count(name)
    return hits


def evaluate_phase_state(batch_text: str, roadmap_text: str) -> dict[str, bool]:
    batch_upload_gate_active = (
        'gate_task_id: "IDS-V0_1-BATCH-001-010-UPLOAD-GATE"' in batch_text
        and 'current_task_id: "IDS-V0_1-BATCH-001-010-UPLOAD-GATE"' in roadmap_text
        and 'next_gate_id: "IDS-V0_1-BATCH-001-010-GITHUB-MERGE"' in roadmap_text
    )
    batch_uploaded_to_main = (
        'status: "uploaded_to_github_main"' in batch_text
        and 'merged_sha: "2d418ccba1e16bcb940387c6e8152668fc2dccaf"' in batch_text
        and 'current_task_id: "IDS-V0_1-BATCH-001-010-MAIN-MERGED"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE011-P1-GATE"' in roadmap_text
    )
    stage011_phase2_active = (
        'current_task_id: "IDS-V0_1-STAGE011-P2"' in batch_text
        and 'acceptance_status: "phase2_implementation_complete"' in batch_text
        and 'current_stage_id: "IDS-STAGE011"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE011-P2"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE011-P2"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE011-P3-GATE"' in roadmap_text
    )
    stage011_phase3_active = (
        'current_task_id: "IDS-V0_1-STAGE011-P3"' in batch_text
        and 'acceptance_status: "phase3_scenario_validation_complete"' in batch_text
        and 'current_stage_id: "IDS-STAGE011"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE011-P3"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE011-P3"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE011-P4-GATE"' in roadmap_text
    )
    stage011_phase4_closeout = (
        'current_task_id: "IDS-V0_1-STAGE011-P4"' in batch_text
        and 'acceptance_status: "local_passed"' in batch_text
        and 'next_stage: "STAGE-012"' in batch_text
        and 'current_stage_id: "IDS-STAGE011"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE011-P4"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE011-P4"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE012-P1-GATE"' in roadmap_text
    )
    stage012_phase1_active = (
        'current_task_id: "IDS-V0_1-STAGE012-P1"' in batch_text
        and 'acceptance_status: "phase1_scope_boundary_complete"' in batch_text
        and 'current_stage_id: "IDS-STAGE012"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE012-P1"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE012-P1"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE012-P2-GATE"' in roadmap_text
    )
    stage012_phase2_active = (
        'current_task_id: "IDS-V0_1-STAGE012-P2"' in batch_text
        and 'acceptance_status: "phase2_readonly_identity_slice_complete"' in batch_text
        and 'current_stage_id: "IDS-STAGE012"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE012-P2"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE012-P2"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE012-P3-GATE"' in roadmap_text
    )
    stage012_phase3_active = (
        'current_task_id: "IDS-V0_1-STAGE012-P3"' in batch_text
        and 'acceptance_status: "phase3_scenario_validation_complete"' in batch_text
        and 'current_stage_id: "IDS-STAGE012"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE012-P3"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE012-P3"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE012-P4-GATE"' in roadmap_text
    )
    stage012_phase4_closeout = (
        'current_task_id: "IDS-V0_1-STAGE012-P4"' in batch_text
        and 'acceptance_status: "local_passed"' in batch_text
        and 'next_stage: "STAGE-013"' in batch_text
        and 'current_stage_id: "IDS-STAGE012"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE012-P4"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE012-P4"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE013-P1-GATE"' in roadmap_text
    )
    stage013_phase1_active = (
        'current_task_id: "IDS-V0_1-STAGE013-P1"' in batch_text
        and 'acceptance_status: "phase1_scope_boundary_complete"' in batch_text
        and 'current_stage_id: "IDS-STAGE013"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE013-P1"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE013-P1"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE013-P2-GATE"' in roadmap_text
    )
    stage013_phase2_active = (
        'current_task_id: "IDS-V0_1-STAGE013-P2"' in batch_text
        and 'acceptance_status: "phase2_fingerprint_slice_complete"' in batch_text
        and 'current_stage_id: "IDS-STAGE013"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE013-P2"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE013-P2"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE013-P3-GATE"' in roadmap_text
    )
    stage013_phase3_active = (
        'current_task_id: "IDS-V0_1-STAGE013-P3"' in batch_text
        and 'acceptance_status: "phase3_scenario_validation_complete"' in batch_text
        and 'current_stage_id: "IDS-STAGE013"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE013-P3"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE013-P3"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE013-P4-GATE"' in roadmap_text
    )
    stage013_phase4_closeout = (
        'current_task_id: "IDS-V0_1-STAGE013-P4"' in batch_text
        and 'acceptance_status: "local_passed"' in batch_text
        and 'next_stage: "STAGE-014"' in batch_text
        and 'current_stage_id: "IDS-STAGE013"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE013-P4"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE013-P4"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE014-P1-GATE"' in roadmap_text
    )
    stage014_phase1_active = (
        'current_task_id: "IDS-V0_1-STAGE014-P1"' in batch_text
        and 'acceptance_status: "phase1_scope_boundary_complete"' in batch_text
        and 'current_stage_id: "IDS-STAGE014"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE014-P1"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE014-P1"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE014-P2-GATE"' in roadmap_text
    )
    stage014_phase2_active = (
        'current_task_id: "IDS-V0_1-STAGE014-P2"' in batch_text
        and 'acceptance_status: "phase2_manifest_slice_complete"' in batch_text
        and 'current_stage_id: "IDS-STAGE014"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE014-P2"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE014-P2"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE014-P3-GATE"' in roadmap_text
    )
    stage014_phase3_active = (
        'current_task_id: "IDS-V0_1-STAGE014-P3"' in batch_text
        and 'acceptance_status: "phase3_scenario_validation_complete"' in batch_text
        and 'current_stage_id: "IDS-STAGE014"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE014-P3"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE014-P3"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE014-P4-GATE"' in roadmap_text
    )
    stage014_phase4_closeout = (
        'current_task_id: "IDS-V0_1-STAGE014-P4"' in batch_text
        and 'acceptance_status: "local_passed"' in batch_text
        and 'next_stage: "STAGE-015"' in batch_text
        and 'current_stage_id: "IDS-STAGE014"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE014-P4"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE014-P4"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE015-P1-GATE"' in roadmap_text
    )
    stage015_phase1_active = (
        'current_task_id: "IDS-V0_1-STAGE015-P1"' in batch_text
        and 'acceptance_status: "phase1_scope_boundary_complete"' in batch_text
        and 'current_stage_id: "IDS-STAGE015"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE015-P1"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE015-P1"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE015-P2-GATE"' in roadmap_text
    )
    stage015_phase2_active = (
        'current_task_id: "IDS-V0_1-STAGE015-P2"' in batch_text
        and 'acceptance_status: "phase2_duplicate_slice_complete"' in batch_text
        and 'current_stage_id: "IDS-STAGE015"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE015-P2"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE015-P2"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE015-P3-GATE"' in roadmap_text
    )
    stage015_phase3_active = (
        'current_task_id: "IDS-V0_1-STAGE015-P3"' in batch_text
        and 'acceptance_status: "phase3_scenario_validation_complete"' in batch_text
        and 'current_stage_id: "IDS-STAGE015"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE015-P3"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE015-P3"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE015-P4-GATE"' in roadmap_text
    )
    stage015_phase4_closeout = (
        'current_task_id: "IDS-V0_1-STAGE015-P4"' in batch_text
        and 'acceptance_status: "local_passed"' in batch_text
        and 'next_stage: "STAGE-016"' in batch_text
        and 'current_stage_id: "IDS-STAGE015"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE015-P4"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE015-P4"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE016-P1-GATE"' in roadmap_text
    )
    stage016_phase1_active = (
        'current_task_id: "IDS-V0_1-STAGE016-P1"' in batch_text
        and 'acceptance_status: "phase1_scope_boundary_complete"' in batch_text
        and 'current_stage_id: "IDS-STAGE016"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE016-P1"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE016-P1"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE016-P2-GATE"' in roadmap_text
    )
    stage016_phase2_active = (
        'current_task_id: "IDS-V0_1-STAGE016-P2"' in batch_text
        and 'acceptance_status: "phase2_import_idempotency_slice_complete"' in batch_text
        and 'current_stage_id: "IDS-STAGE016"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE016-P2"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE016-P2"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE016-P3-GATE"' in roadmap_text
    )
    stage016_phase3_active = (
        'current_task_id: "IDS-V0_1-STAGE016-P3"' in batch_text
        and 'acceptance_status: "phase3_scenario_validation_complete"' in batch_text
        and 'current_stage_id: "IDS-STAGE016"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE016-P3"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE016-P3"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE016-P4-GATE"' in roadmap_text
    )
    stage016_phase4_closeout = (
        'current_task_id: "IDS-V0_1-STAGE016-P4"' in batch_text
        and 'acceptance_status: "local_passed"' in batch_text
        and 'next_stage: "STAGE-017"' in batch_text
        and 'current_stage_id: "IDS-STAGE016"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE016-P4"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE016-P4"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE017-P1-GATE"' in roadmap_text
    )
    stage017_phase1_active = (
        'current_task_id: "IDS-V0_1-STAGE017-P1"' in batch_text
        and 'acceptance_status: "phase1_scope_boundary_complete"' in batch_text
        and 'current_stage_id: "IDS-STAGE017"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE017-P1"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE017-P1"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE017-P2-GATE"' in roadmap_text
    )
    stage017_phase2_active = (
        'current_task_id: "IDS-V0_1-STAGE017-P2"' in batch_text
        and 'acceptance_status: "phase2_regression_slice_complete"' in batch_text
        and 'current_stage_id: "IDS-STAGE017"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE017-P2"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE017-P2"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE017-P3-GATE"' in roadmap_text
    )
    stage017_phase3_active = (
        'current_task_id: "IDS-V0_1-STAGE017-P3"' in batch_text
        and 'acceptance_status: "phase3_scenario_validation_complete"' in batch_text
        and 'current_stage_id: "IDS-STAGE017"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE017-P3"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE017-P3"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE017-P4-GATE"' in roadmap_text
    )
    stage017_phase4_closeout = (
        'current_task_id: "IDS-V0_1-STAGE017-P4"' in batch_text
        and 'acceptance_status: "local_passed"' in batch_text
        and 'next_stage: "STAGE-018"' in batch_text
        and 'current_stage_id: "IDS-STAGE017"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE017-P4"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE017-P4"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE018-P1-GATE"' in roadmap_text
    )
    stage018_phase1_active = (
        'current_task_id: "IDS-V0_1-STAGE018-P1"' in batch_text
        and 'acceptance_status: "phase1_scope_boundary_complete"' in batch_text
        and 'current_stage_id: "IDS-STAGE018"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE018-P1"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE018-P1"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE018-P2-GATE"' in roadmap_text
    )
    stage018_phase2_active = (
        'current_task_id: "IDS-V0_1-STAGE018-P2"' in batch_text
        and 'acceptance_status: "phase2_preflight_slice_complete"' in batch_text
        and 'current_stage_id: "IDS-STAGE018"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE018-P2"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE018-P2"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE018-P3-GATE"' in roadmap_text
    )
    stage018_phase3_active = (
        'current_task_id: "IDS-V0_1-STAGE018-P3"' in batch_text
        and 'acceptance_status: "phase3_scenario_validation_complete"' in batch_text
        and 'current_stage_id: "IDS-STAGE018"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE018-P3"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE018-P3"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE018-P4-GATE"' in roadmap_text
    )
    stage018_phase4_closeout = (
        'current_task_id: "IDS-V0_1-STAGE018-P4"' in batch_text
        and 'acceptance_status: "local_passed"' in batch_text
        and 'next_stage: "STAGE-019"' in batch_text
        and 'current_stage_id: "IDS-STAGE018"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE018-P4"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE018-P4"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE019-P1-GATE"' in roadmap_text
    )
    stage019_phase1_active = (
        'current_task_id: "IDS-V0_1-STAGE019-P1"' in batch_text
        and 'acceptance_status: "phase1_scope_boundary_complete"' in batch_text
        and 'current_stage_id: "IDS-STAGE019"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE019-P1"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE019-P1"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE019-P2-GATE"' in roadmap_text
    )
    stage019_phase2_active = (
        'current_task_id: "IDS-V0_1-STAGE019-P2"' in batch_text
        and 'acceptance_status: "phase2_risk_estimator_slice_complete"' in batch_text
        and 'current_stage_id: "IDS-STAGE019"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE019-P2"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE019-P2"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE019-P3-GATE"' in roadmap_text
    )
    stage019_phase3_active = (
        'current_task_id: "IDS-V0_1-STAGE019-P3"' in batch_text
        and 'acceptance_status: "phase3_scenario_validation_complete"' in batch_text
        and 'current_stage_id: "IDS-STAGE019"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE019-P3"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE019-P3"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE019-P4-GATE"' in roadmap_text
    )
    stage019_phase4_closeout = (
        'current_task_id: "IDS-V0_1-STAGE019-P4"' in batch_text
        and 'acceptance_status: "local_passed"' in batch_text
        and 'next_stage: "STAGE-020"' in batch_text
        and 'current_stage_id: "IDS-STAGE019"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE019-P4"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE019-P4"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE020-P1-GATE"' in roadmap_text
    )
    stage020_phase1_active = (
        'current_task_id: "IDS-V0_1-STAGE020-P1"' in batch_text
        and 'acceptance_status: "phase1_scope_boundary_complete"' in batch_text
        and 'current_stage_id: "IDS-STAGE020"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE020-P1"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE020-P1"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE020-P2-GATE"' in roadmap_text
    )
    stage020_phase2_active = (
        'current_task_id: "IDS-V0_1-STAGE020-P2"' in batch_text
        and 'acceptance_status: "phase2_cost_estimator_slice_complete"' in batch_text
        and 'current_stage_id: "IDS-STAGE020"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE020-P2"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE020-P2"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE020-P3-GATE"' in roadmap_text
    )
    stage020_phase3_active = (
        'current_task_id: "IDS-V0_1-STAGE020-P3"' in batch_text
        and 'acceptance_status: "phase3_scenario_validation_complete"' in batch_text
        and 'current_stage_id: "IDS-STAGE020"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE020-P3"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE020-P3"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE020-P4-GATE"' in roadmap_text
    )
    stage020_phase4_closeout = (
        'current_task_id: "IDS-V0_1-STAGE020-P4"' in batch_text
        and 'acceptance_status: "local_passed"' in batch_text
        and 'next_stage: "STAGE-021"' in batch_text
        and 'current_stage_id: "IDS-STAGE020"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE020-P4"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE020-P4"' in roadmap_text
        and 'next_gate_id: "IDS-V0_1-BATCH-011-020-REVIEW-GATE"' in roadmap_text
    )
    batch011_020_reviewed_pending_upload = (
        'status: "reviewed_ready_for_upload_no_github_upload"' in batch_text
        and 'review_task_id: "IDS-V0_1-BATCH-011-020-REVIEW-GATE"' in batch_text
        and 'review_evidence_ref: "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH011_020_REVIEW_GATE.md"'
        in batch_text
        and 'push_allowed: false' in batch_text
        and 'gate_task_id: "IDS-V0_1-BATCH-011-020-UPLOAD-GATE"' in batch_text
        and 'current_stage_id: "IDS-STAGE020"' in roadmap_text
        and 'current_phase_id: "IDS-V0_1-BATCH-011-020-REVIEW-GATE"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-BATCH-011-020-REVIEW-GATE"' in roadmap_text
        and 'next_gate_id: "IDS-V0_1-BATCH-011-020-UPLOAD-GATE"' in roadmap_text
    )
    batch011_020_upload_gate_active = (
        'status: "local_batch_upload_gate_passed_pending_github_merge"' in batch_text
        and 'push_allowed: true' in batch_text
        and 'gate_task_id: "IDS-V0_1-BATCH-011-020-UPLOAD-GATE"' in batch_text
        and 'gate_evidence_ref: "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH011_020_UPLOAD_GATE.md"'
        in batch_text
        and 'current_stage_id: "IDS-STAGE020"' in roadmap_text
        and 'current_phase_id: "IDS-V0_1-BATCH-011-020-UPLOAD-GATE"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-BATCH-011-020-UPLOAD-GATE"' in roadmap_text
        and 'next_gate_id: "IDS-V0_1-BATCH-011-020-GITHUB-MERGE"' in roadmap_text
    )
    batch011_020_uploaded_to_main = (
        'status: "uploaded_to_github_main"' in batch_text
        and 'gate_task_id: "IDS-V0_1-BATCH-011-020-UPLOAD-GATE"' in batch_text
        and 'github_pr: "https://github.com/LinzeColin/CodexProject/pull/271"' in batch_text
        and 'merged_sha: "61fcb5295c6e0046059eba236c4cedbdaa2f2fed"' in batch_text
        and 'post_merge_open_prs: 0' in batch_text
        and 'post_merge_open_issues: 0' in batch_text
        and 'current_stage_id: "IDS-STAGE020"' in roadmap_text
        and 'current_phase_id: "IDS-V0_1-BATCH-011-020-MAIN-MERGED"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-BATCH-011-020-MAIN-MERGED"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE021-P1-GATE"' in roadmap_text
    )
    stage021_phase1_active = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE021-P1"' in batch_text
        and 'acceptance_status: "phase1_scope_boundary_defined"' in batch_text
        and 'next_gate: "IDS-STAGE021-P2-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE021"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE021-P1"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE021-P1"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE021-P2-GATE"' in roadmap_text
    )
    stage021_phase2_active = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE021-P2"' in batch_text
        and 'acceptance_status: "phase2_preflight_confirmation_ui_slice_complete"' in batch_text
        and 'next_gate: "IDS-STAGE021-P3-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE021"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE021-P2"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE021-P2"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE021-P3-GATE"' in roadmap_text
    )
    stage021_phase3_active = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE021-P3"' in batch_text
        and 'acceptance_status: "phase3_scenario_validation_complete"' in batch_text
        and 'next_gate: "IDS-STAGE021-P4-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE021"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE021-P3"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE021-P3"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE021-P4-GATE"' in roadmap_text
    )
    stage021_phase4_closeout = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE021-P4"' in batch_text
        and 'acceptance_status: "local_passed"' in batch_text
        and 'next_gate: "IDS-STAGE022-P1-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE021"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE021-P4"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE021-P4"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE022-P1-GATE"' in roadmap_text
    )
    stage022_phase1_active = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE022-P1"' in batch_text
        and 'acceptance_status: "phase1_scope_boundary_defined"' in batch_text
        and 'next_gate: "IDS-STAGE022-P2-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE022"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE022-P1"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE022-P1"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE022-P2-GATE"' in roadmap_text
    )
    stage022_phase2_active = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE022-P2"' in batch_text
        and 'acceptance_status: "phase2_priority_queue_slice_complete"' in batch_text
        and 'next_gate: "IDS-STAGE022-P3-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE022"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE022-P2"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE022-P2"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE022-P3-GATE"' in roadmap_text
    )
    stage022_phase3_active = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE022-P3"' in batch_text
        and 'acceptance_status: "phase3_scenario_validation_complete"' in batch_text
        and 'next_gate: "IDS-STAGE022-P4-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE022"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE022-P3"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE022-P3"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE022-P4-GATE"' in roadmap_text
    )
    stage022_phase4_closeout = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE022-P4"' in batch_text
        and 'acceptance_status: "local_passed"' in batch_text
        and 'next_gate: "IDS-STAGE023-P1-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE022"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE022-P4"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE022-P4"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE023-P1-GATE"' in roadmap_text
    )
    stage023_phase1_active = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE023-P1"' in batch_text
        and 'acceptance_status: "phase1_scope_boundary_defined"' in batch_text
        and 'next_gate: "IDS-STAGE023-P2-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE023"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE023-P1"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE023-P1"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE023-P2-GATE"' in roadmap_text
    )
    stage023_phase2_active = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE023-P2"' in batch_text
        and 'acceptance_status: "phase2_preflight_scenario_slice_complete"' in batch_text
        and 'next_gate: "IDS-STAGE023-P3-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE023"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE023-P2"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE023-P2"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE023-P3-GATE"' in roadmap_text
    )
    stage023_phase3_active = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE023-P3"' in batch_text
        and 'acceptance_status: "phase3_scenario_validation_complete"' in batch_text
        and 'next_gate: "IDS-STAGE023-P4-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE023"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE023-P3"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE023-P3"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE023-P4-GATE"' in roadmap_text
    )
    stage023_phase4_closeout = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE023-P4"' in batch_text
        and 'acceptance_status: "local_passed"' in batch_text
        and 'next_gate: "IDS-STAGE024-P1-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE023"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE023-P4"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE023-P4"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE024-P1-GATE"' in roadmap_text
    )
    stage024_phase1_active = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE024-P1"' in batch_text
        and 'acceptance_status: "phase1_scope_boundary_defined"' in batch_text
        and 'next_gate: "IDS-STAGE024-P2-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE024"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE024-P1"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE024-P1"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE024-P2-GATE"' in roadmap_text
    )
    stage024_phase2_active = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE024-P2"' in batch_text
        and 'acceptance_status: "phase2_safe_extraction_slice_complete"' in batch_text
        and 'next_gate: "IDS-STAGE024-P3-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE024"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE024-P2"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE024-P2"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE024-P3-GATE"' in roadmap_text
    )
    stage024_phase3_active = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE024-P3"' in batch_text
        and 'acceptance_status: "phase3_scenario_validation_complete"' in batch_text
        and 'next_gate: "IDS-STAGE024-P4-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE024"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE024-P3"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE024-P3"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE024-P4-GATE"' in roadmap_text
    )
    stage024_phase4_closeout = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE024-P4"' in batch_text
        and 'acceptance_status: "local_passed"' in batch_text
        and 'next_gate: "IDS-STAGE025-P1-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE024"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE024-P4"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE024-P4"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE025-P1-GATE"' in roadmap_text
    )
    stage025_phase1_active = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE025-P1"' in batch_text
        and 'acceptance_status: "phase1_scope_boundary_defined"' in batch_text
        and 'next_gate: "IDS-STAGE025-P2-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE025"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE025-P1"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE025-P1"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE025-P2-GATE"' in roadmap_text
    )
    stage025_phase2_active = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE025-P2"' in batch_text
        and 'acceptance_status: "phase2_safe_extraction_engine_slice_complete"' in batch_text
        and 'next_gate: "IDS-STAGE025-P3-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE025"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE025-P2"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE025-P2"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE025-P3-GATE"' in roadmap_text
    )
    stage025_phase3_active = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE025-P3"' in batch_text
        and 'acceptance_status: "phase3_scenario_validation_complete"' in batch_text
        and 'next_gate: "IDS-STAGE025-P4-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE025"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE025-P3"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE025-P3"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE025-P4-GATE"' in roadmap_text
    )
    stage025_phase4_closeout = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE025-P4"' in batch_text
        and 'acceptance_status: "local_passed"' in batch_text
        and 'next_gate: "IDS-STAGE026-P1-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE025"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE025-P4"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE025-P4"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE026-P1-GATE"' in roadmap_text
    )
    stage026_phase1_active = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE026-P1"' in batch_text
        and 'acceptance_status: "phase1_scope_boundary_defined"' in batch_text
        and 'next_gate: "IDS-STAGE026-P2-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE026"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE026-P1"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE026-P1"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE026-P2-GATE"' in roadmap_text
    )
    stage026_phase2_active = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE026-P2"' in batch_text
        and 'acceptance_status: "phase2_archive_manifest_slice_complete"' in batch_text
        and 'next_gate: "IDS-STAGE026-P3-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE026"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE026-P2"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE026-P2"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE026-P3-GATE"' in roadmap_text
    )
    stage026_phase3_active = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE026-P3"' in batch_text
        and 'acceptance_status: "phase3_scenario_validation_complete"' in batch_text
        and 'next_gate: "IDS-STAGE026-P4-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE026"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE026-P3"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE026-P3"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE026-P4-GATE"' in roadmap_text
    )
    stage026_phase4_closeout = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE026-P4"' in batch_text
        and 'acceptance_status: "local_passed"' in batch_text
        and 'next_gate: "IDS-STAGE027-P1-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE026"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE026-P4"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE026-P4"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE027-P1-GATE"' in roadmap_text
    )
    stage027_phase1_active = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE027-P1"' in batch_text
        and 'acceptance_status: "phase1_scope_boundary_defined"' in batch_text
        and 'next_gate: "IDS-STAGE027-P2-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE027"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE027-P1"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE027-P1"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE027-P2-GATE"' in roadmap_text
    )
    stage027_phase2_active = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE027-P2"' in batch_text
        and 'acceptance_status: "phase2_reingest_slice_complete"' in batch_text
        and 'next_gate: "IDS-STAGE027-P3-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE027"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE027-P2"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE027-P2"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE027-P3-GATE"' in roadmap_text
    )
    stage027_phase3_active = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE027-P3"' in batch_text
        and 'acceptance_status: "phase3_scenario_validation_complete"' in batch_text
        and 'next_gate: "IDS-STAGE027-P4-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE027"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE027-P3"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE027-P3"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE027-P4-GATE"' in roadmap_text
    )
    stage027_phase4_closeout = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE027-P4"' in batch_text
        and 'acceptance_status: "local_passed"' in batch_text
        and 'next_stage: "STAGE-028"' in batch_text
        and 'next_gate: "IDS-STAGE028-P1-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE027"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE027-P4"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE027-P4"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE028-P1-GATE"' in roadmap_text
    )
    stage028_phase1_active = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'status: "stage028_phase1_in_progress"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE028-P1"' in batch_text
        and 'acceptance_status: "phase1_scope_boundary_defined"' in batch_text
        and 'next_gate: "IDS-STAGE028-P2-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE028"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE028-P1"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE028-P1"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE028-P2-GATE"' in roadmap_text
    )
    stage028_phase2_active = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'status: "stage028_phase2_in_progress"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE028-P2"' in batch_text
        and 'acceptance_status: "phase2_archive_adversarial_slice_complete"' in batch_text
        and 'next_gate: "IDS-STAGE028-P3-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE028"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE028-P2"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE028-P2"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE028-P3-GATE"' in roadmap_text
    )
    stage028_phase3_active = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'status: "stage028_phase3_in_progress"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE028-P3"' in batch_text
        and 'acceptance_status: "phase3_scenario_validation_complete"' in batch_text
        and 'next_gate: "IDS-STAGE028-P4-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE028"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE028-P3"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE028-P3"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE028-P4-GATE"' in roadmap_text
    )
    stage028_phase4_closeout = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'status: "stage028_completed_local_pending_stage029"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE028-P4"' in batch_text
        and 'acceptance_status: "local_passed"' in batch_text
        and 'next_stage: "STAGE-029"' in batch_text
        and 'next_gate: "IDS-STAGE029-P1-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE028"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE028-P4"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE028-P4"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE029-P1-GATE"' in roadmap_text
    )
    stage029_phase1_active = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'status: "stage029_phase1_in_progress"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE029-P1"' in batch_text
        and 'acceptance_status: "phase1_scope_boundary_defined"' in batch_text
        and 'next_gate: "IDS-STAGE029-P2-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE029"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE029-P1"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE029-P1"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE029-P2-GATE"' in roadmap_text
    )
    stage029_phase2_active = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'status: "stage029_phase2_in_progress"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE029-P2"' in batch_text
        and 'acceptance_status: "phase2_cleanup_allowlist_slice_complete"' in batch_text
        and 'next_gate: "IDS-STAGE029-P3-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE029"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE029-P2"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE029-P2"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE029-P3-GATE"' in roadmap_text
    )
    stage029_phase3_active = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'status: "stage029_phase3_in_progress"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE029-P3"' in batch_text
        and 'acceptance_status: "phase3_scenario_validation_complete"' in batch_text
        and 'next_gate: "IDS-STAGE029-P4-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE029"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE029-P3"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE029-P3"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE029-P4-GATE"' in roadmap_text
    )
    stage029_phase4_closeout = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'status: "stage029_completed_local_pending_stage030"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE029-P4"' in batch_text
        and 'acceptance_status: "local_passed"' in batch_text
        and 'next_stage: "STAGE-030"' in batch_text
        and 'next_gate: "IDS-STAGE030-P1-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE029"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE029-P4"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE029-P4"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE030-P1-GATE"' in roadmap_text
    )
    stage030_phase1_active = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'status: "stage030_phase1_in_progress"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE030-P1"' in batch_text
        and 'acceptance_status: "phase1_scope_boundary_defined"' in batch_text
        and 'next_gate: "IDS-STAGE030-P2-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE030"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE030-P1"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE030-P1"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE030-P2-GATE"' in roadmap_text
    )
    stage030_phase2_active = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'status: "stage030_phase2_in_progress"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE030-P2"' in batch_text
        and 'acceptance_status: "phase2_schema_migration_slice_complete"' in batch_text
        and 'next_gate: "IDS-STAGE030-P3-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE030"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE030-P2"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE030-P2"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE030-P3-GATE"' in roadmap_text
    )
    stage030_phase3_active = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'status: "stage030_phase3_in_progress"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE030-P3"' in batch_text
        and 'acceptance_status: "phase3_scenario_validation_complete"' in batch_text
        and 'next_gate: "IDS-STAGE030-P4-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE030"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE030-P3"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE030-P3"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE030-P4-GATE"' in roadmap_text
    )
    stage030_phase4_closeout = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'status: "stage030_completed_local_pending_batch_review"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE030-P4"' in batch_text
        and 'acceptance_status: "local_passed"' in batch_text
        and 'next_phase: "batch_review_gate"' in batch_text
        and 'next_gate: "IDS-V0_1-BATCH-021-030-REVIEW-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE030"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE030-P4"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE030-P4"' in roadmap_text
        and 'next_gate_id: "IDS-V0_1-BATCH-021-030-REVIEW-GATE"' in roadmap_text
    )
    batch021_030_reviewed_pending_upload = (
        'status: "reviewed_ready_for_upload_no_github_upload"' in batch_text
        and 'review_task_id: "IDS-V0_1-BATCH-021-030-REVIEW-GATE"' in batch_text
        and 'review_evidence_ref: "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH021_030_REVIEW_GATE.md"'
        in batch_text
        and 'push_allowed: false' in batch_text
        and 'gate_task_id: "IDS-V0_1-BATCH-021-030-UPLOAD-GATE"' in batch_text
        and 'current_stage_id: "IDS-STAGE030"' in roadmap_text
        and 'current_phase_id: "IDS-V0_1-BATCH-021-030-REVIEW-GATE"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-BATCH-021-030-REVIEW-GATE"' in roadmap_text
        and 'next_gate_id: "IDS-V0_1-BATCH-021-030-UPLOAD-GATE"' in roadmap_text
    )
    batch021_030_upload_gate_active = (
        'status: "local_batch_upload_gate_passed_pending_github_merge"' in batch_text
        and 'push_allowed: true' in batch_text
        and 'gate_task_id: "IDS-V0_1-BATCH-021-030-UPLOAD-GATE"' in batch_text
        and 'gate_evidence_ref: "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH021_030_UPLOAD_GATE.md"'
        in batch_text
        and 'current_stage_id: "IDS-STAGE030"' in roadmap_text
        and 'current_phase_id: "IDS-V0_1-BATCH-021-030-UPLOAD-GATE"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-BATCH-021-030-UPLOAD-GATE"' in roadmap_text
        and 'next_gate_id: "IDS-V0_1-BATCH-021-030-GITHUB-MERGE"' in roadmap_text
    )
    batch021_030_uploaded_to_main = (
        'status: "uploaded_to_github_main"' in batch_text
        and 'gate_task_id: "IDS-V0_1-BATCH-021-030-UPLOAD-GATE"' in batch_text
        and 'github_pr: "https://github.com/LinzeColin/CodexProject/pull/272"' in batch_text
        and 'merged_sha: "88a428c7901226bd44d5e4ff106cd51d74b550fe"' in batch_text
        and 'post_merge_open_prs: 0' in batch_text
        and 'post_merge_open_issues: 0' in batch_text
        and 'current_stage_id: "IDS-STAGE030"' in roadmap_text
        and 'current_phase_id: "IDS-V0_1-BATCH-021-030-MAIN-MERGED"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-BATCH-021-030-MAIN-MERGED"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE031-P1-GATE"' in roadmap_text
    )
    stage031_phase1_active = (
        'batch_id: "IDS-V0_1-BATCH-031-040"' in batch_text
        and 'status: "stage031_phase1_in_progress"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE031-P1"' in batch_text
        and 'acceptance_status: "phase1_scope_boundary_defined"' in batch_text
        and 'next_gate: "IDS-STAGE031-P2-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE031"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE031-P1"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE031-P1"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE031-P2-GATE"' in roadmap_text
    )
    stage031_phase2_active = (
        'batch_id: "IDS-V0_1-BATCH-031-040"' in batch_text
        and 'status: "stage031_phase2_in_progress"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE031-P2"' in batch_text
        and 'acceptance_status: "phase2_safety_slice_defined"' in batch_text
        and 'next_gate: "IDS-STAGE031-P3-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE031"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE031-P2"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE031-P2"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE031-P3-GATE"' in roadmap_text
    )
    stage031_phase3_active = (
        'batch_id: "IDS-V0_1-BATCH-031-040"' in batch_text
        and 'status: "stage031_phase3_in_progress"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE031-P3"' in batch_text
        and 'acceptance_status: "phase3_scenario_validation_defined"' in batch_text
        and 'next_gate: "IDS-STAGE031-P4-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE031"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE031-P3"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE031-P3"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE031-P4-GATE"' in roadmap_text
    )
    stage031_phase4_closeout = (
        'batch_id: "IDS-V0_1-BATCH-031-040"' in batch_text
        and 'status: "stage031_completed_local_pending_review"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE031-P4"' in batch_text
        and 'acceptance_status: "local_passed_pending_stage_review"' in batch_text
        and 'next_gate: "IDS-STAGE031-REVIEW-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE031"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE031-P4"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE031-P4"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE031-REVIEW-GATE"' in roadmap_text
    )
    batch_terminal_state = batch_upload_gate_active or batch_uploaded_to_main
    later_stage_state = (
        batch_terminal_state
        or stage011_phase2_active
        or stage011_phase3_active
        or stage011_phase4_closeout
        or stage012_phase1_active
        or stage012_phase2_active
        or stage012_phase3_active
        or stage012_phase4_closeout
        or stage013_phase1_active
        or stage013_phase2_active
        or stage013_phase3_active
        or stage013_phase4_closeout
        or stage014_phase1_active
        or stage014_phase2_active
        or stage014_phase3_active
        or stage014_phase4_closeout
        or stage015_phase1_active
        or stage015_phase2_active
        or stage015_phase3_active
        or stage015_phase4_closeout
        or stage016_phase1_active
        or stage016_phase2_active
        or stage016_phase3_active
        or stage016_phase4_closeout
        or stage017_phase1_active
        or stage017_phase2_active
        or stage017_phase3_active
        or stage017_phase4_closeout
        or stage018_phase1_active
        or stage018_phase2_active
        or stage018_phase3_active
        or stage018_phase4_closeout
        or stage019_phase1_active
        or stage019_phase2_active
        or stage019_phase3_active
        or stage019_phase4_closeout
        or stage020_phase1_active
        or stage020_phase2_active
        or stage020_phase3_active
        or stage020_phase4_closeout
        or batch011_020_reviewed_pending_upload
        or batch011_020_upload_gate_active
        or batch011_020_uploaded_to_main
        or stage021_phase1_active
        or stage021_phase2_active
        or stage021_phase3_active
        or stage021_phase4_closeout
        or stage022_phase1_active
        or stage022_phase2_active
        or stage022_phase3_active
        or stage022_phase4_closeout
        or stage023_phase1_active
        or stage023_phase2_active
        or stage023_phase3_active
        or stage023_phase4_closeout
        or stage024_phase1_active
        or stage024_phase2_active
        or stage024_phase3_active
        or stage024_phase4_closeout
        or stage025_phase1_active
        or stage025_phase2_active
        or stage025_phase3_active
        or stage025_phase4_closeout
        or stage026_phase1_active
        or stage026_phase2_active
        or stage026_phase3_active
        or stage026_phase4_closeout
        or stage027_phase1_active
        or stage027_phase2_active
        or stage027_phase3_active
        or stage027_phase4_closeout
        or stage028_phase1_active
        or stage028_phase2_active
        or stage028_phase3_active
        or stage028_phase4_closeout
        or stage029_phase1_active
        or stage029_phase2_active
        or stage029_phase3_active
        or stage029_phase4_closeout
        or stage030_phase1_active
        or stage030_phase2_active
        or stage030_phase3_active
        or stage030_phase4_closeout
        or batch021_030_reviewed_pending_upload
        or batch021_030_upload_gate_active
        or batch021_030_uploaded_to_main
        or stage031_phase1_active
        or stage031_phase2_active
        or stage031_phase3_active
        or stage031_phase4_closeout
    )
    phase2_completed = '      - "Phase 2"' in batch_text
    stage005_active_or_complete = (
        'STAGE-005:\n    status: "in_progress"' in batch_text
        or 'STAGE-005:\n    status: "completed_local"' in batch_text
        or later_stage_state
    )
    current_task_allowed = (
        'current_task_id: "IDS-V0_1-STAGE005-P2"' in batch_text
        or 'current_task_id: "IDS-V0_1-STAGE005-P3"' in batch_text
        or 'current_task_id: "IDS-V0_1-STAGE005-P4"' in batch_text
        or later_stage_state
    )
    next_phase_allowed = (
        'next_phase: "Phase 3"' in batch_text
        or 'next_phase: "Phase 2"' in batch_text
        or 'next_phase: "Phase 4"' in batch_text
        or 'next_phase: "stage_review_gate"' in batch_text
        or 'next_phase: "batch_review_gate"' in batch_text
        or 'next_stage: "STAGE-006"' in batch_text
        or 'next_stage: "STAGE-012"' in batch_text
        or 'next_stage: "STAGE-013"' in batch_text
        or 'next_stage: "STAGE-014"' in batch_text
        or 'next_stage: "STAGE-015"' in batch_text
        or 'next_stage: "STAGE-016"' in batch_text
        or 'next_stage: "STAGE-017"' in batch_text
        or 'next_stage: "STAGE-018"' in batch_text
        or 'next_stage: "STAGE-019"' in batch_text
        or 'next_stage: "STAGE-020"' in batch_text
        or 'next_stage: "STAGE-021"' in batch_text
        or 'next_stage: "STAGE-022"' in batch_text
        or 'next_stage: "STAGE-026"' in batch_text
        or 'next_stage: "STAGE-027"' in batch_text
        or 'next_stage: "STAGE-028"' in batch_text
        or 'next_stage: "STAGE-029"' in batch_text
        or 'next_stage: "STAGE-030"' in batch_text
        or 'next_stage: "STAGE-031"' in batch_text
    )
    current_phase_allowed = (
        'current_phase_id: "IDS-STAGE005-P2"' in roadmap_text
        or 'current_phase_id: "IDS-STAGE005-P3"' in roadmap_text
        or 'current_phase_id: "IDS-STAGE005-P4"' in roadmap_text
        or later_stage_state
    )
    current_roadmap_task_allowed = (
        'current_task_id: "IDS-V0_1-STAGE005-P2"' in roadmap_text
        or 'current_task_id: "IDS-V0_1-STAGE005-P3"' in roadmap_text
        or 'current_task_id: "IDS-V0_1-STAGE005-P4"' in roadmap_text
        or later_stage_state
    )
    next_gate_allowed = (
        'next_gate_id: "IDS-STAGE005-P3-GATE"' in roadmap_text
        or 'next_gate_id: "IDS-STAGE005-P4-GATE"' in roadmap_text
        or 'next_gate_id: "IDS-STAGE006-P1-GATE"' in roadmap_text
        or later_stage_state
    )
    return {
        "stage005_active_or_complete": stage005_active_or_complete,
        "phase2_completed": phase2_completed,
        "current_task_allowed": current_task_allowed,
        "next_phase_allowed": next_phase_allowed,
        "push_locked": "push_allowed: false" in batch_text or later_stage_state,
        "current_stage005": 'current_stage_id: "IDS-STAGE005"' in roadmap_text
        or later_stage_state,
        "current_phase_allowed": current_phase_allowed,
        "current_roadmap_task_allowed": current_roadmap_task_allowed,
        "next_gate_allowed": next_gate_allowed,
        "roadmap_phase2_completed": 'phase_id: "IDS-STAGE005-P2"' in roadmap_text
        and 'status: "passed_with_local_evidence"' in roadmap_text
        or later_stage_state,
    }


def evaluate_data_boundary(root_lock_text: str, batch_text: str, boundary_text: str) -> dict[str, bool]:
    raw_root = "/Users/linzezhang/Downloads/IDS_MetaData"
    boundary_ref = "KM_IDSystem/docs/pursuing_goal/ids_v0_1/IDS_METADATA_RAW_DATA_BOUNDARY.md"
    combined = "\n".join((root_lock_text, batch_text, boundary_text))
    boundary_mutation_ban = (
        "do not modify" in boundary_text
        or "must not create, edit, delete, move" in boundary_text
        or "Raw directory content modified: `no`" in boundary_text
    )
    return {
        "raw_root_recorded": raw_root in combined,
        "boundary_ref_recorded": boundary_ref in root_lock_text and boundary_ref in batch_text,
        "read_only_policy_recorded": "read-only" in combined and boundary_mutation_ban,
        "raw_content_not_committed": "raw database content is not committed" in root_lock_text
        and "Raw directory content copied into GitHub: `no`" in boundary_text,
        "real_data_only_policy_recorded": "real_data_only_policy" in root_lock_text
        and "Real Data Only Policy" in boundary_text
        and "fake business data" in combined,
    }


def build_report(root: Path | None = None) -> dict:
    root = (root or Path(__file__).resolve().parents[3]).resolve()
    repo_root = _repo_root(root)
    issues: list[str] = []

    tracked_paths = _git_ls_files(root)
    changed_paths = _git_changed_paths(root)
    missing_required_files = [
        path for path in REQUIRED_FILES if not (repo_root / path).is_file()
    ]
    tracked_forbidden_runtime_files = [
        path for path in tracked_paths if is_forbidden_runtime_path(path)
    ]
    forbidden_changed_paths = [
        path for path in changed_paths if is_forbidden_runtime_path(path)
    ]
    unexpected_changed_paths = [
        path for path in changed_paths if path.startswith("KM_IDSystem/") and not _is_allowed_changed_path(path)
    ]

    events_path = root / "docs/governance/events.jsonl"
    events, event_json_errors = _parse_events(events_path)
    event_ids = {event.get("event_id") for event in events}
    missing_event_ids = [event_id for event_id in REQUIRED_EVENT_IDS if event_id not in event_ids]

    batch_paths = [
        root / "docs/pursuing_goal/ids_v0_1/BATCH001_010_UPLOAD_LOCK.yaml",
        root / "docs/pursuing_goal/ids_v0_1/BATCH011_020_UPLOAD_LOCK.yaml",
        root / "docs/pursuing_goal/ids_v0_1/BATCH021_030_UPLOAD_LOCK.yaml",
        root / "docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml",
    ]
    batch_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in batch_paths
        if path.is_file()
    )
    root_lock_text = (root / "docs/pursuing_goal/ids_v0_1/V0_1_ROOT_LOCK.yaml").read_text(
        encoding="utf-8"
    )
    boundary_text = (
        root / "docs/pursuing_goal/ids_v0_1/IDS_METADATA_RAW_DATA_BOUNDARY.md"
    ).read_text(encoding="utf-8")
    roadmap_text = (root / "docs/governance/roadmap.yaml").read_text(encoding="utf-8")
    readme_text = (root / "README.md").read_text(encoding="utf-8")
    handoff_text = (root / "docs/HANDOFF.md").read_text(encoding="utf-8")

    phase_state_checks = evaluate_phase_state(batch_text, roadmap_text)
    data_boundary_checks = evaluate_data_boundary(root_lock_text, batch_text, boundary_text)
    owner_text_checks = {
        "readme_current_name": CURRENT_PRODUCT_NAME in readme_text,
        "handoff_current_name": CURRENT_PRODUCT_NAME in handoff_text,
        "readme_legacy_policy": "Legacy aliases" in readme_text,
        "handoff_legacy_policy": "Legacy aliases" in handoff_text,
    }
    surface_counts = _surface_counts(tracked_paths)
    accepted_name_hits = _text_checks(root, tracked_paths)

    if missing_required_files:
        issues.append("missing required files")
    if event_json_errors:
        issues.append("events.jsonl has invalid JSON lines")
    if missing_event_ids:
        issues.append("missing required stage events")
    if tracked_forbidden_runtime_files:
        issues.append("forbidden runtime files are tracked")
    if forbidden_changed_paths:
        issues.append("forbidden runtime path changed")
    if unexpected_changed_paths:
        issues.append("unexpected KM_IDSystem path changed")
    if not all(phase_state_checks.values()):
        issues.append("phase state is not within the accepted STAGE-005 Phase 2-4 progression")
    if not all(data_boundary_checks.values()):
        issues.append("IDS metadata raw data boundary or real-data-only policy is incomplete")
    if not all(owner_text_checks.values()):
        issues.append("owner-facing identity or legacy policy text is missing")
    if any(count == 0 for count in surface_counts.values()):
        issues.append("one or more governance regression surfaces are empty")
    for accepted_name, hit_count in accepted_name_hits.items():
        if hit_count == 0:
            issues.append(f"accepted name missing from tracked text: {accepted_name}")

    return {
        "acceptance_id": ACCEPTANCE_ID,
        "accepted_name_hits": accepted_name_hits,
        "phase_state_checks": phase_state_checks,
        "changed_paths": changed_paths,
        "event_json_errors": event_json_errors,
        "data_boundary_checks": data_boundary_checks,
        "forbidden_changed_paths": forbidden_changed_paths,
        "issues": issues,
        "missing_event_ids": missing_event_ids,
        "missing_required_files": missing_required_files,
        "owner_text_checks": owner_text_checks,
        "stage": STAGE,
        "surface_counts": surface_counts,
        "tracked_forbidden_runtime_files": tracked_forbidden_runtime_files,
        "tracked_km_ids_files": len(tracked_paths),
        "unexpected_changed_paths": unexpected_changed_paths,
        "valid": not issues,
    }


def main() -> int:
    report = build_report()
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
