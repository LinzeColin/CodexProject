"""Fail-closed GitHub Release delivery boundary."""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any


RELEASE_DELIVERY_MODEL_ID = "adp-release-delivery-v1"
RELEASE_TARGET_ENV_KEY = "ADP_RELEASE_TARGET"
DEFAULT_RELEASE_REPO = "LinzeColin/CodexProject"
MAX_RELEASE_ASSET_MIB = 20
FORBIDDEN_RELEASE_NAMES = {".env", "auth.json", "id_ed25519", "id_rsa"}
FORBIDDEN_RELEASE_SUFFIXES = {
    ".ckpt",
    ".key",
    ".pem",
    ".pt",
    ".pth",
    ".safetensors",
}

CommandResolver = Callable[[str], str | None]
CommandRunner = Callable[[Sequence[str]], Mapping[str, Any] | subprocess.CompletedProcess[str]]


def deliver_release(
    *,
    tag: str,
    title: str,
    notes: str,
    asset_paths: Sequence[str | Path],
    generated_at: str,
    target: str | None = None,
    repo: str = DEFAULT_RELEASE_REPO,
    draft: bool = True,
    allow_upload: bool = False,
    env: Mapping[str, str] | None = None,
    command_resolver: CommandResolver | None = None,
    command_runner: CommandRunner | None = None,
    max_asset_mib: int = MAX_RELEASE_ASSET_MIB,
) -> dict[str, Any]:
    """Return Release delivery evidence and create a Release only when explicitly allowed."""

    environment = env if env is not None else os.environ
    resolver = command_resolver or shutil.which
    release_target = target or environment.get(RELEASE_TARGET_ENV_KEY, "")
    max_bytes = int(max_asset_mib) * 1024 * 1024
    inspected_assets, asset_reasons = _inspect_assets(asset_paths, max_bytes=max_bytes)
    tag_value = str(tag or "")
    title_value = str(title or "")
    notes_value = str(notes or "")
    repo_value = str(repo or "")
    release_id = _release_id(repo_value, tag_value, generated_at)
    gh_available = resolver("gh") is not None
    command = _release_command(
        tag=tag_value,
        title=title_value,
        notes=notes_value,
        assets=[asset["path"] for asset in inspected_assets],
        target=release_target,
        repo=repo_value,
        draft=draft,
    )
    base: dict[str, Any] = {
        "delivery_id": release_id,
        "validator_id": RELEASE_DELIVERY_MODEL_ID,
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "repo": repo_value,
        "tag": tag_value,
        "target": release_target,
        "title": title_value,
        "status": "dry_run",
        "dry_run": not allow_upload,
        "release_upload_enabled": bool(allow_upload),
        "draft": bool(draft),
        "private_channel_expected": True,
        "notes": {
            "notes_sha256": hashlib.sha256(notes_value.encode("utf-8")).hexdigest(),
            "notes_logged": False,
        },
        "asset_policy": {
            "max_asset_mib": int(max_asset_mib),
            "forbidden_names": sorted(FORBIDDEN_RELEASE_NAMES),
            "forbidden_suffixes": sorted(FORBIDDEN_RELEASE_SUFFIXES),
            "clobber_enabled": False,
            "secret_values_logged": False,
        },
        "assets": inspected_assets,
        "command": {
            "gh_required": True,
            "gh_available": gh_available,
            "command_preview": _command_preview(command),
            "stdout_logged": False,
            "stderr_logged": False,
        },
        "blocking_reasons": [],
    }

    basic_reasons = _basic_reasons(
        tag=tag_value,
        title=title_value,
        notes=notes_value,
        repo=repo_value,
        target=release_target,
        allow_upload=allow_upload,
        gh_available=gh_available,
    )
    reasons = asset_reasons + basic_reasons
    if reasons:
        return _blocked(base, reasons)
    if not allow_upload:
        return base

    runner = command_runner or _run_command
    try:
        result = _normalize_command_result(runner(command))
    except Exception as error:  # noqa: BLE001 - report class only; never echo command output.
        return _blocked(base, [f"gh release create failed: {error.__class__.__name__}"])

    if result["returncode"] != 0:
        return _blocked(base, [f"gh release create failed with exit code {result['returncode']}"])
    created = dict(base)
    created["status"] = "created"
    created["dry_run"] = False
    created["release_ref"] = f"github-release://{repo_value}/{tag_value}"
    return created


def validate_release_delivery_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("validator_id") != RELEASE_DELIVERY_MODEL_ID:
        errors.append("release delivery validator_id must be adp-release-delivery-v1")
    if report.get("status") not in {"dry_run", "created", "blocked"}:
        errors.append("release delivery status must be dry_run, created, or blocked")
    if not report.get("repo"):
        errors.append("release delivery repo is required")
    if not report.get("tag"):
        errors.append("release delivery tag is required")
    notes = report.get("notes")
    if not isinstance(notes, Mapping) or not notes.get("notes_sha256") or notes.get("notes_logged") is not False:
        errors.append("release delivery report must include notes_sha256 and must not log notes")
    policy = report.get("asset_policy")
    if not isinstance(policy, Mapping):
        errors.append("release delivery asset_policy is required")
    elif policy.get("secret_values_logged") is not False or policy.get("clobber_enabled") is not False:
        errors.append("release delivery must avoid secret logging and clobber upload")
    assets = report.get("assets")
    if not isinstance(assets, list):
        errors.append("release delivery assets must be a list")
    elif not assets and report.get("status") != "blocked":
        errors.append("release delivery requires at least one asset")
    else:
        for index, asset in enumerate(assets):
            if not isinstance(asset, Mapping):
                errors.append(f"release asset {index} must be an object")
                continue
            if not asset.get("path") or not asset.get("name"):
                errors.append(f"release asset {index} requires path and name")
            if int(asset.get("size_bytes") or 0) <= 0:
                errors.append(f"release asset {index} requires positive size_bytes")
            if len(str(asset.get("sha256") or "")) != 64:
                errors.append(f"release asset {index} requires sha256")
    command = report.get("command")
    if not isinstance(command, Mapping):
        errors.append("release delivery command evidence is required")
    elif command.get("stdout_logged") is not False or command.get("stderr_logged") is not False:
        errors.append("release delivery must not log gh stdout or stderr")
    if report.get("status") == "created" and not report.get("release_ref"):
        errors.append("created release delivery requires release_ref")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked release delivery requires blocking_reasons")
    if report.get("status") == "dry_run" and report.get("blocking_reasons"):
        errors.append("dry_run release delivery cannot include blocking_reasons")
    return errors


def _inspect_assets(asset_paths: Sequence[str | Path], *, max_bytes: int) -> tuple[list[dict[str, Any]], list[str]]:
    assets: list[dict[str, Any]] = []
    reasons: list[str] = []
    seen_paths: set[str] = set()
    seen_names: dict[str, str] = {}
    if not asset_paths:
        return assets, ["at least one release asset path is required"]
    for value in asset_paths:
        path = Path(value)
        asset_reasons = _asset_reasons(path, max_bytes=max_bytes)
        if asset_reasons:
            reasons.extend(asset_reasons)
            continue
        resolved_path = str(path.resolve())
        if resolved_path in seen_paths:
            continue
        if path.name in seen_names:
            reasons.append(f"release asset name duplicates existing asset: {path.name}")
            continue
        seen_paths.add(resolved_path)
        seen_names[path.name] = resolved_path
        assets.append(
            {
                "path": str(path),
                "name": path.name,
                "size_bytes": path.stat().st_size,
                "sha256": _sha256_file(path),
            }
        )
    return assets, reasons


def _asset_reasons(path: Path, *, max_bytes: int) -> list[str]:
    if not path.exists():
        return [f"release asset missing: {path}"]
    if path.is_symlink():
        return [f"release asset must not be a symlink: {path}"]
    if not path.is_file():
        return [f"release asset must be a file: {path}"]
    name = path.name
    if name in FORBIDDEN_RELEASE_NAMES or name.startswith(".env"):
        return [f"release asset has forbidden secret-like name: {path}"]
    if path.suffix.lower() in FORBIDDEN_RELEASE_SUFFIXES:
        return [f"release asset has forbidden secret/model suffix: {path}"]
    size = path.stat().st_size
    if size <= 0:
        return [f"release asset is empty: {path}"]
    if size > max_bytes:
        mib = max_bytes // (1024 * 1024)
        return [f"release asset exceeds {mib} MiB: {path}"]
    return []


def _basic_reasons(
    *,
    tag: str,
    title: str,
    notes: str,
    repo: str,
    target: str,
    allow_upload: bool,
    gh_available: bool,
) -> list[str]:
    reasons = []
    if not tag:
        reasons.append("release tag is required")
    if not title:
        reasons.append("release title is required")
    if not notes:
        reasons.append("release notes are required")
    if not repo:
        reasons.append("release repo is required")
    if allow_upload and not target:
        reasons.append(f"{RELEASE_TARGET_ENV_KEY} or --target is required for real Release upload")
    if allow_upload and not gh_available:
        reasons.append("gh command is required for real Release upload")
    return reasons


def _release_command(
    *,
    tag: str,
    title: str,
    notes: str,
    assets: Sequence[str],
    target: str,
    repo: str,
    draft: bool,
) -> list[str]:
    command = [
        "gh",
        "release",
        "create",
        tag,
        *assets,
        "--repo",
        repo,
        "--target",
        target,
        "--title",
        title,
        "--notes",
        notes,
    ]
    if draft:
        command.append("--draft")
    return command


def _command_preview(command: Sequence[str]) -> list[str]:
    preview = list(command)
    for index, item in enumerate(preview):
        if item == "--notes" and index + 1 < len(preview):
            preview[index + 1] = "<redacted-notes>"
    return preview


def _run_command(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(command),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _normalize_command_result(result: Mapping[str, Any] | subprocess.CompletedProcess[str]) -> dict[str, int]:
    if isinstance(result, subprocess.CompletedProcess):
        return {"returncode": int(result.returncode)}
    return {"returncode": int(result.get("returncode", 1))}


def _blocked(base: Mapping[str, Any], reasons: list[str]) -> dict[str, Any]:
    blocked = dict(base)
    blocked["status"] = "blocked"
    blocked["blocking_reasons"] = reasons
    return blocked


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _release_id(repo: str, tag: str, generated_at: str) -> str:
    payload = "|".join([generated_at, repo, tag])
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return f"release-delivery:{digest}"
