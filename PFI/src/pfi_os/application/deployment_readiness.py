from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pfi_os.application.operational_store import default_data_home, default_operational_db_path


PHASE_D_DEPLOYMENT_READINESS_SCHEMA = "PFIOSPhaseDLocalDeploymentReadinessV1"
PHASE_D_DEPLOYMENT_CONTRACT_SCHEMA = "PFIOSPhaseDDeploymentReadinessContractV1"

REQUIRED_REPO_SURFACES: tuple[tuple[str, str], ...] = (
    ("pyproject", "pyproject.toml"),
    ("web_shell", "web/index.html"),
    ("operational_store", "src/pfi_os/application/operational_store.py"),
    ("start_script", "scripts/startPFI.sh"),
    ("status_script", "scripts/statusPFI.sh"),
    ("macos_app_template", "macos/PFI.app"),
)


def build_phase_d_deployment_readiness_contract(
    project_root: Path | str,
    data_home: Path | str | None = None,
) -> dict[str, Any]:
    root = _resolve(project_root)
    resolved_data_home = _resolve(data_home) if data_home is not None else _resolve(default_data_home())
    return {
        "schema": PHASE_D_DEPLOYMENT_CONTRACT_SCHEMA,
        "phase": "Phase D",
        "read_model_schema": PHASE_D_DEPLOYMENT_READINESS_SCHEMA,
        "project_root": str(root),
        "data_home": str(resolved_data_home),
        "required_repo_surfaces": [
            {"key": key, "path": relative_path} for key, relative_path in REQUIRED_REPO_SURFACES
        ],
        "runtime_paths": _runtime_paths(resolved_data_home),
        "local_model_policy": {
            "default_provider": "DisabledProvider",
            "ollama_provider_optional": True,
            "network_probe_required": False,
            "provider_failure_blocks_core_workflows": False,
        },
        "backup_restore_policy": {
            "backup_dir": "$PFI_DATA_HOME/runtime/backups",
            "restore_staging_dir": "$PFI_DATA_HOME/runtime/restore_staging",
            "readiness_check_creates_directories": False,
            "phase5_requires_backup_restore_acceptance": True,
        },
        "safety_boundary": _safety_boundary(),
    }


def build_phase_d_deployment_readiness(
    project_root: Path | str,
    data_home: Path | str | None = None,
    *,
    env: dict[str, str] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    root = _resolve(project_root)
    resolved_data_home = _resolve(data_home) if data_home is not None else _resolve(default_data_home(env))
    generated_at = (now or datetime.now(timezone.utc)).isoformat(timespec="seconds")
    checks: list[dict[str, Any]] = []
    checks.extend(_repo_surface_checks(root))
    checks.extend(_data_home_checks(root, resolved_data_home))
    checks.extend(_backup_restore_checks(resolved_data_home))
    checks.append(_local_model_check(env or os.environ))

    status = _overall_status(checks)
    return {
        "schema": PHASE_D_DEPLOYMENT_READINESS_SCHEMA,
        "phase": "Phase D",
        "status": status,
        "generated_at": generated_at,
        "project_root": str(root),
        "data_home": str(resolved_data_home),
        "operational_db_path": str(default_operational_db_path(resolved_data_home)),
        "runtime_paths": _runtime_paths(resolved_data_home),
        "checks": checks,
        "backup_restore": {
            "backup_dir": str(resolved_data_home / "runtime" / "backups"),
            "restore_staging_dir": str(resolved_data_home / "runtime" / "restore_staging"),
            "readiness_check_created_paths": False,
            "acceptance_required_before_phase5": True,
        },
        "local_model": _local_model_summary(env or os.environ),
        "phase6_preparation": {
            "package_inputs": [
                "PFI_OS source tree",
                "HANDOFF.md",
                "docs/development/PFI_PHASE_0_TO_A_RECORD.md",
                "docs/phase/PHASE_D_DEPLOYMENT_READINESS.md",
                "backup/restore acceptance evidence",
            ],
            "ready_for_phase6": False,
            "reason": "Phase D readiness is a contract/read-model gate; Phase 5 acceptance package is still required.",
        },
        "safety_boundary": _safety_boundary(),
        "next_action": _next_action(status),
    }


def _repo_surface_checks(project_root: Path) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for key, relative_path in REQUIRED_REPO_SURFACES:
        path = project_root / relative_path
        exists = path.exists()
        checks.append(
            _check(
                category="repo_surface",
                code=f"{key.upper()}_PRESENT",
                status="Pass" if exists else "Fail",
                evidence=str(path),
                required=True,
                message=f"{relative_path} {'exists' if exists else 'is missing'}.",
            )
        )
    return checks


def _data_home_checks(project_root: Path, data_home: Path) -> list[dict[str, Any]]:
    operational_db = _resolve(default_operational_db_path(data_home))
    return [
        _check(
            category="data_boundary",
            code="DATA_HOME_OUTSIDE_REPO",
            status="Pass" if not _is_relative_to(data_home, project_root) else "Fail",
            evidence=str(data_home),
            required=True,
            message="$PFI_DATA_HOME must stay outside the public repository.",
        ),
        _check(
            category="data_boundary",
            code="OPERATIONAL_DB_UNDER_DATA_HOME",
            status="Pass" if _is_relative_to(operational_db, data_home / "private" / "operational") else "Fail",
            evidence=str(operational_db),
            required=True,
            message="Operational SQLite must resolve under $PFI_DATA_HOME/private/operational.",
        ),
        _check(
            category="data_boundary",
            code="OPERATIONAL_DB_OUTSIDE_REPO",
            status="Pass" if not _is_relative_to(operational_db, project_root) else "Fail",
            evidence=str(operational_db),
            required=True,
            message="Operational SQLite must not be stored in public Git.",
        ),
    ]


def _backup_restore_checks(data_home: Path) -> list[dict[str, Any]]:
    paths = {
        "BACKUP_TARGET_UNDER_DATA_HOME": data_home / "runtime" / "backups",
        "RESTORE_STAGING_UNDER_DATA_HOME": data_home / "runtime" / "restore_staging",
    }
    checks: list[dict[str, Any]] = []
    for code, path in paths.items():
        checks.append(
            _check(
                category="backup_restore",
                code=code,
                status="Pass" if _is_relative_to(_resolve(path), data_home) else "Fail",
                evidence=str(path),
                required=True,
                message="Path plan is under $PFI_DATA_HOME; readiness check does not create it.",
                exists=path.exists(),
            )
        )
    return checks


def _local_model_check(env: dict[str, str]) -> dict[str, Any]:
    summary = _local_model_summary(env)
    if summary["provider"] == "DisabledProvider":
        status = "Pass"
        message = "DisabledProvider is the default and keeps core workflows independent from local LLM availability."
    elif summary["provider"] == "OllamaProvider" and summary["base_url"]:
        status = "Review"
        message = "OllamaProvider is configured but this readiness check does not perform network/model probes."
    else:
        status = "Review"
        message = "Optional local model provider is incomplete; core workflows must continue with DisabledProvider."
    return _check(
        category="local_model",
        code="LOCAL_MODEL_OPTIONAL",
        status=status,
        evidence=summary["provider"],
        required=False,
        message=message,
        provider=summary["provider"],
        base_url_configured=bool(summary["base_url"]),
    )


def _local_model_summary(env: dict[str, str]) -> dict[str, Any]:
    provider = str(env.get("PFI_LLM_PROVIDER") or "DisabledProvider").strip()
    return {
        "provider": provider,
        "base_url": str(env.get("OLLAMA_BASE_URL", "") or "").strip(),
        "required_for_core_workflows": False,
        "network_probe_performed": False,
    }


def _runtime_paths(data_home: Path) -> dict[str, str]:
    return {
        "operational_db": str(default_operational_db_path(data_home)),
        "backup_dir": str(data_home / "runtime" / "backups"),
        "restore_staging_dir": str(data_home / "runtime" / "restore_staging"),
        "runtime_logs_dir": str(data_home / "runtime" / "logs"),
    }


def _check(
    *,
    category: str,
    code: str,
    status: str,
    evidence: str,
    required: bool,
    message: str,
    **extra: Any,
) -> dict[str, Any]:
    payload = {
        "category": category,
        "code": code,
        "status": status,
        "required": required,
        "evidence": evidence,
        "message": message,
    }
    payload.update(extra)
    return payload


def _overall_status(checks: list[dict[str, Any]]) -> str:
    if any(check["required"] and check["status"] == "Fail" for check in checks):
        return "Blocked"
    if any(check["status"] == "Review" for check in checks):
        return "Review"
    return "Pass"


def _next_action(status: str) -> str:
    if status == "Blocked":
        return "Fix required repository surfaces or data-home boundary before Phase D acceptance."
    if status == "Review":
        return "Review optional local model configuration, then add backup/restore acceptance evidence."
    return "Add backup/restore acceptance evidence and prepare Phase 5 package."


def _safety_boundary() -> dict[str, bool]:
    return {
        "read_only": True,
        "creates_directories": False,
        "starts_services": False,
        "network_calls": False,
        "provider_calls": False,
        "broker_calls": False,
        "order_execution": False,
        "holding_mutation": False,
        "research_only": True,
    }


def _resolve(path: Path | str) -> Path:
    return Path(path).expanduser().resolve(strict=False)


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False
