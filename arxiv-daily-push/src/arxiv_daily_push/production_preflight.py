"""Fail-closed production preflight for scheduled arXiv Daily Push runs."""

from __future__ import annotations

import os
import shutil
import subprocess
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from .config import DEFAULT_RECIPIENT, DEFAULT_TIMEZONE
from .doctor import disk_status


PRODUCTION_PREFLIGHT_VALIDATOR_ID = "adp-production-preflight-v1"
PRODUCTION_REQUIRED_COMMANDS = ("python3", "git", "gh")
PRODUCTION_SECRET_ENV_KEYS = (
    "ADP_SMTP_HOST",
    "ADP_SMTP_PORT",
    "ADP_SMTP_USERNAME",
    "ADP_SMTP_PASSWORD",
)
MIN_PRODUCTION_FREE_DISK_GIB = 8.0
MIN_PRODUCTION_MEMORY_GIB = 8.0
MAX_GIT_FILE_MIB = 20
FORBIDDEN_PATH_NAMES = {".env", "auth.json"}
FORBIDDEN_SUFFIXES = {
    ".ckpt",
    ".flac",
    ".key",
    ".m4a",
    ".mov",
    ".mp4",
    ".pem",
    ".pt",
    ".pth",
    ".safetensors",
    ".wav",
}
LOCAL_ARTIFACT_DIRS = (
    ".cache",
    "tmp",
    "staging",
    "renders",
    "media",
    "models",
    "model_weights",
    "voice_samples",
    "release_assets",
)


CommandResolver = Callable[[str], str | None]


def build_production_preflight(
    path: Path | str | None = None,
    *,
    generated_at: str,
    env: Mapping[str, str] | None = None,
    command_resolver: CommandResolver | None = None,
    github_cli_equivalent: Mapping[str, Any] | None = None,
    disk_free_gib: float | None = None,
    memory_total_gib: float | None = None,
    git_scan: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    root = Path(path or ".").resolve()
    environment = env if env is not None else os.environ
    resolver = command_resolver or shutil.which

    command_gate = _command_gate(resolver, github_cli_equivalent=github_cli_equivalent)
    secret_gate = _secret_gate(environment)
    disk_gate = _disk_gate(root, disk_free_gib=disk_free_gib)
    memory_gate = _memory_gate(memory_total_gib=memory_total_gib)
    git_gate = dict(git_scan) if git_scan is not None else _git_artifact_gate(root)
    cache_gate = _cache_gate(root)

    gates = [
        command_gate,
        secret_gate,
        disk_gate,
        memory_gate,
        git_gate,
        cache_gate,
    ]
    status = "pass" if all(gate["passed"] for gate in gates) else "blocked"
    return {
        "preflight_id": "production-preflight:arxiv-daily-push",
        "validator_id": PRODUCTION_PREFLIGHT_VALIDATOR_ID,
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "timezone": DEFAULT_TIMEZONE,
        "recipient": DEFAULT_RECIPIENT,
        "status": status,
        "production_run_allowed": status == "pass",
        "gates": gates,
        "blocking_reasons": [
            reason
            for gate in gates
            for reason in gate.get("blocking_reasons", [])
            if gate.get("passed") is not True
        ],
        "secret_policy": {
            "secret_values_logged": False,
            "secret_names_only": True,
            "codex_auth_read": False,
        },
        "resource_evidence": {
            "resource_pressure_ok": status == "pass",
            "resource_pressure_ok_ref": _resource_pressure_ref(generated_at) if status == "pass" else "",
        },
    }


def validate_production_preflight(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("validator_id") != PRODUCTION_PREFLIGHT_VALIDATOR_ID:
        errors.append("preflight.validator_id must be adp-production-preflight-v1")
    gates = report.get("gates")
    if not isinstance(gates, list) or not gates:
        errors.append("preflight.gates must be a non-empty list")
        return errors
    allowed = bool(report.get("production_run_allowed"))
    failed_gates = [
        str(gate.get("gate_id"))
        for gate in gates
        if isinstance(gate, Mapping) and gate.get("passed") is not True
    ]
    if allowed and failed_gates:
        errors.append("production_run_allowed cannot be true with failed gates: " + ", ".join(failed_gates))
    if allowed and report.get("blocking_reasons"):
        errors.append("production_run_allowed cannot be true with blocking_reasons")
    if not allowed and not report.get("blocking_reasons"):
        errors.append("blocked production preflight must include blocking_reasons")
    secret_policy = report.get("secret_policy")
    if not isinstance(secret_policy, Mapping) or secret_policy.get("secret_values_logged") is not False:
        errors.append("preflight must explicitly avoid logging secret values")
    return errors


def _command_gate(
    resolver: CommandResolver,
    *,
    github_cli_equivalent: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    commands = []
    for command in PRODUCTION_REQUIRED_COMMANDS:
        path = resolver(command)
        equivalent_accepted = _github_cli_equivalent_accepted(command, github_cli_equivalent)
        command_record = {
            "command": command,
            "available": path is not None,
            "path_present": path is not None,
        }
        if equivalent_accepted:
            command_record.update(
                {
                    "equivalent_accepted": True,
                    "equivalent_id": str(github_cli_equivalent.get("equivalent_id")),
                    "equivalent_source": str(github_cli_equivalent.get("source")),
                }
            )
        commands.append(command_record)
    missing = [item["command"] for item in commands if not item["available"] and not item.get("equivalent_accepted")]
    return _gate(
        "required_commands",
        not missing,
        [f"missing production runtime commands: {', '.join(missing)}"] if missing else [],
        {"commands": commands},
    )


def _github_cli_equivalent_accepted(command: str, equivalent: Mapping[str, Any] | None) -> bool:
    if command != "gh" or not isinstance(equivalent, Mapping):
        return False
    return (
        equivalent.get("equivalent_id") == "github_open_pr_count_zero_api_v1"
        and equivalent.get("source") in {"github_api", "github_rest_api", "curl_github_api"}
        and equivalent.get("open_pr_count") == 0
        and equivalent.get("reviewed") is True
    )


def _secret_gate(env: Mapping[str, str]) -> dict[str, Any]:
    keys = [{"name": key, "present": bool(env.get(key))} for key in PRODUCTION_SECRET_ENV_KEYS]
    missing = [item["name"] for item in keys if not item["present"]]
    return _gate(
        "secret_environment",
        not missing,
        [f"missing required secret environment keys: {', '.join(missing)}"] if missing else [],
        {"keys": keys, "values_logged": False},
    )


def _disk_gate(root: Path, *, disk_free_gib: float | None = None) -> dict[str, Any]:
    if disk_free_gib is None:
        disk = disk_status(root)
        free_gib = float(disk["free_gib"])
        disk = {
            "path": str(root),
            "free_gib": round(free_gib, 2),
            "production_min_free_gib": MIN_PRODUCTION_FREE_DISK_GIB,
            "stage1_text_delivery_ready": free_gib >= MIN_PRODUCTION_FREE_DISK_GIB,
        }
    else:
        free_gib = float(disk_free_gib)
        disk = {
            "path": str(root),
            "free_gib": round(free_gib, 2),
            "production_min_free_gib": MIN_PRODUCTION_FREE_DISK_GIB,
            "stage1_text_delivery_ready": free_gib >= MIN_PRODUCTION_FREE_DISK_GIB,
        }
    passed = free_gib >= MIN_PRODUCTION_FREE_DISK_GIB
    return _gate(
        "disk_pressure",
        passed,
        [f"free disk {free_gib:.2f} GiB is below required {MIN_PRODUCTION_FREE_DISK_GIB:.2f} GiB"] if not passed else [],
        {"disk": disk},
    )


def _memory_gate(*, memory_total_gib: float | None = None) -> dict[str, Any]:
    total_gib = memory_total_gib if memory_total_gib is not None else _memory_total_gib()
    if total_gib is None:
        return _gate("memory_pressure", False, ["total memory could not be determined"], {"total_gib": None})
    passed = total_gib >= MIN_PRODUCTION_MEMORY_GIB
    return _gate(
        "memory_pressure",
        passed,
        [f"memory {total_gib:.2f} GiB is below required {MIN_PRODUCTION_MEMORY_GIB:.2f} GiB"] if not passed else [],
        {"total_gib": round(total_gib, 2), "min_required_gib": MIN_PRODUCTION_MEMORY_GIB},
    )


def _git_artifact_gate(root: Path) -> dict[str, Any]:
    try:
        files = _git_files(root, "--cached") + _git_files(root, "--others", "--exclude-standard")
    except (OSError, subprocess.SubprocessError) as error:
        return _gate("git_artifact_hygiene", False, [f"git file scan failed: {error}"], {"violations": []})

    violations = []
    max_bytes = MAX_GIT_FILE_MIB * 1024 * 1024
    for relative in sorted(set(files)):
        candidate = root / relative
        name = candidate.name
        suffix = candidate.suffix.lower()
        if name in FORBIDDEN_PATH_NAMES or suffix in FORBIDDEN_SUFFIXES:
            violations.append({"path": relative, "reason": "forbidden production artifact or secret suffix"})
            continue
        try:
            size = candidate.stat().st_size
        except OSError:
            continue
        if size > max_bytes:
            violations.append({"path": relative, "reason": f"file exceeds {MAX_GIT_FILE_MIB} MiB"})
    reasons = [f"git artifact hygiene violations: {len(violations)}"] if violations else []
    return _gate("git_artifact_hygiene", not violations, reasons, {"violations": violations})


def _cache_gate(root: Path) -> dict[str, Any]:
    non_empty = []
    for name in LOCAL_ARTIFACT_DIRS:
        directory = root / name
        if directory.is_dir() and any(directory.iterdir()):
            non_empty.append(name)
    return _gate(
        "local_artifact_cache",
        not non_empty,
        [f"local artifact/cache directories are not empty: {', '.join(non_empty)}"] if non_empty else [],
        {"checked_dirs": list(LOCAL_ARTIFACT_DIRS), "non_empty_dirs": non_empty},
    )


def _git_files(root: Path, *args: str) -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z", *args],
        text=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return [item.decode("utf-8") for item in result.stdout.split(b"\0") if item]


def _memory_total_gib() -> float | None:
    if not hasattr(os, "sysconf"):
        return None
    try:
        page_size = os.sysconf("SC_PAGE_SIZE")
        pages = os.sysconf("SC_PHYS_PAGES")
    except (ValueError, OSError):
        return None
    return float(page_size * pages) / (1024**3)


def _resource_pressure_ref(generated_at: str) -> str:
    token = "".join(character if character.isalnum() else "-" for character in str(generated_at or "current")).strip("-")
    return f"production-preflight://arxiv-daily-push/{token or 'current'}"


def _gate(gate_id: str, passed: bool, blocking_reasons: Sequence[str], extra: Mapping[str, Any] | None = None) -> dict[str, Any]:
    gate = {"gate_id": gate_id, "passed": passed, "blocking_reasons": list(blocking_reasons)}
    if extra:
        gate.update(extra)
    return gate
