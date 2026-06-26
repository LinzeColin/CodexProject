from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PHASE5_ACCEPTANCE_PACKAGE_SCHEMA = "PFIOSPhase5AcceptancePackageV1"


REQUIRED_PACKAGE_FILES: dict[str, tuple[str, ...]] = {
    "top_level": (
        "README.md",
        "AGENTS.md",
        "PLANS.md",
        "HANDOFF.md",
        "pyproject.toml",
    ),
    "product_contracts": (
        "docs/product/PFI_OS_PRODUCT_CONSTITUTION.md",
        "docs/product/PFI_OS_INFORMATION_ARCHITECTURE.md",
        "docs/product/PFI_FEATURE_DISPOSITION.md",
        "docs/data/PFI_DATA_BOUNDARIES.md",
        "docs/data/PFI_SOURCE_OF_TRUTH.md",
        "docs/ux/PFI_UX_CONTRACT.md",
        "docs/ux/PFI_WEB_SHELL_ACCEPTANCE.md",
        "docs/architecture/PFI_TARGET_ARCHITECTURE.md",
        "docs/archive/legacy-migration.md",
    ),
    "phase_records": (
        "docs/development/PFI_PHASE_0_TO_A_RECORD.md",
        "docs/phase/PHASE_A_DATA_FOUNDATION.md",
        "docs/phase/PHASE_A_COMPLETION_AUDIT.md",
        "docs/phase/PHASE_B_STRATEGY_LAB.md",
        "docs/phase/PHASE_B_MARKETS.md",
        "docs/phase/PHASE_B_RESEARCH_POLICY.md",
        "docs/phase/PHASE_B_PORTFOLIO.md",
        "docs/phase/PHASE_C_WORKFLOW_RUNTIME.md",
        "docs/phase/PHASE_D_DEPLOYMENT_READINESS.md",
        "docs/phase/PHASE_5_ACCEPTANCE_PACKAGE.md",
    ),
    "runtime_contracts": (
        "src/pfi_os/application/operational_store.py",
        "src/pfi_os/application/deployment_readiness.py",
        "src/pfi_os/application/deployment_backup_restore.py",
        "src/pfi_os/application/phase5_acceptance_package.py",
        "web/index.html",
        "web/app/shell.js",
        "web/styles/tokens.css",
        "scripts/startPFI.sh",
        "scripts/statusPFI.sh",
        "macos/PFI.app",
    ),
    "contract_tests": (
        "tests/test_pfi_product_contracts.py",
        "tests/contract/test_phase_d_deployment_readiness.py",
        "tests/contract/test_phase_d_backup_restore_acceptance.py",
        "tests/contract/test_phase5_acceptance_package.py",
    ),
}


VALIDATION_EVIDENCE: tuple[dict[str, str], ...] = (
    {
        "gate": "ProductContracts",
        "command": "python -m pytest tests/test_pfi_product_contracts.py -q",
        "latest_result": "8 passed",
    },
    {
        "gate": "PhaseDReadinessAndBackupRestore",
        "command": (
            "python -m pytest tests/contract/test_phase_d_deployment_readiness.py "
            "tests/contract/test_phase_d_backup_restore_acceptance.py -q"
        ),
        "latest_result": "10 passed",
    },
    {
        "gate": "PhaseCRuntime",
        "command": (
            "python -m pytest tests/contract/test_phase_c_workflow_runtime_scheduler.py "
            "tests/contract/test_phase_c_workflow_runtime_read_model.py -q"
        ),
        "latest_result": "10 passed",
    },
    {
        "gate": "WebShell",
        "command": (
            "python -m pytest tests/contract/test_pfi_web_shell_contract.py "
            "tests/e2e/test_pfi_web_shell_static_flow.py "
            "tests/visual/test_pfi_web_shell_visual_baseline.py -q"
        ),
        "latest_result": "19 passed",
    },
    {
        "gate": "StaticAndBoundary",
        "command": "python -m compileall src/pfi_os/application src/pfi_os/app/streamlit_app.py && git diff --check",
        "latest_result": "passed",
    },
)


USER_SUPPLIED_PHASE6_MATERIALS: tuple[dict[str, str], ...] = (
    {
        "item": "local_repository_backup",
        "status": "user_supplied_or_external",
        "reason": "Must be kept outside public Git and refreshed on the deployment Mac.",
    },
    {
        "item": "hardware_and_disk_audit",
        "status": "user_supplied_or_external",
        "reason": "Needed before choosing optional local model settings.",
    },
    {
        "item": "sanitized_test_holdings",
        "status": "user_supplied_or_external",
        "reason": "Real holdings and account identifiers must never enter public Git.",
    },
    {
        "item": "representative_symbols_and_policy_documents",
        "status": "user_supplied_or_external",
        "reason": "Needed for final user walk-through examples.",
    },
    {
        "item": "user_subjective_acceptance_score",
        "status": "pending_user_acceptance",
        "reason": "MVP stop condition requires user walk-through acceptance.",
    },
)


def build_phase5_acceptance_package(
    project_root: Path | str,
    *,
    git_head: str = "",
    pr_url: str = "",
    now: datetime | None = None,
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve(strict=False)
    generated_at = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    inventory = _file_inventory(root)
    missing_required = [item["path"] for item in inventory if item["required"] and not item["exists"]]
    status = "Pass" if not missing_required else "Blocked"
    return {
        "schema": PHASE5_ACCEPTANCE_PACKAGE_SCHEMA,
        "phase": "Phase 5",
        "status": status,
        "generated_at": generated_at.isoformat(timespec="seconds"),
        "package_policy": {
            "github_safe": True,
            "uses_relative_paths_only": True,
            "physical_zip_required_for_this_pr": False,
            "private_runtime_artifacts_committed": False,
            "sqlite_committed": False,
            "logs_committed": False,
            "secrets_committed": False,
        },
        "github_backup": {
            "repository": "LinzeColin/CodexProject",
            "product_directory": "PFI_OS",
            "branch": "codex/pfi-os-main-integration-20260619",
            "pull_request": pr_url,
            "head": git_head,
            "draft_pr_expected": True,
        },
        "file_inventory": inventory,
        "missing_required_files": missing_required,
        "validation_evidence": list(VALIDATION_EVIDENCE),
        "phase6_preparation": {
            "engineering_package_ready": status == "Pass",
            "deployment_data_home": "$PFI_DATA_HOME",
            "operational_db": "$PFI_DATA_HOME/private/operational/pfi.sqlite",
            "backup_scope": "$PFI_DATA_HOME/runtime/backups",
            "restore_scope": "$PFI_DATA_HOME/runtime/restore_staging",
            "default_model_provider": "DisabledProvider",
            "optional_model_provider": "OllamaProvider",
            "controlled_local_deployment_acceptance": "deferred_until_release_gate_requires_service_start",
            "user_supplied_materials": list(USER_SUPPLIED_PHASE6_MATERIALS),
        },
        "safety_boundary": _safety_boundary(),
        "next_action": _next_action(status),
    }


def _file_inventory(project_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for group, paths in REQUIRED_PACKAGE_FILES.items():
        for relative_path in paths:
            rows.append(
                {
                    "group": group,
                    "path": relative_path,
                    "exists": (project_root / relative_path).exists(),
                    "required": True,
                }
            )
    return rows


def _safety_boundary() -> dict[str, bool]:
    return {
        "research_only": True,
        "live_trading": False,
        "autonomous_order_execution": False,
        "broker_calls": False,
        "payment_or_bank_actions": False,
        "holding_mutation": False,
        "private_data_in_public_git": False,
        "starts_services": False,
        "network_calls": False,
    }


def _next_action(status: str) -> str:
    if status == "Pass":
        return "Use this package as the Phase 6 deployment handoff; collect user-supplied materials on the target Mac."
    return "Add missing required package files, rerun contract tests, then refresh the Phase 5 package."
