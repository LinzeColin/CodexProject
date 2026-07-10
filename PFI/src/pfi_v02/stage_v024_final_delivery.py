from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import plistlib
import re
import subprocess
import tempfile
from typing import Any, Callable, Mapping, Sequence

from pfi_v02.stage_v024_stage2_entry_consistency import build_v024_stage2_web_bundle_manifest


FINAL_DELIVERY_SCHEMA = "PFIV024FinalDeliveryPayloadV1"
FINAL_DELIVERY_EVIDENCE_SCHEMA = "PFIV024FinalDeliveryEvidenceV1"
FINAL_DELIVERY_ACCEPTANCE_ID = "ACC-PFI-V024-FINAL-DELIVERY"
FINAL_DELIVERY_GATE = "PFI-V024-FINAL-DELIVERY"
TARGET_VERSION = "v0.2.4"
SOURCE_PACKAGE_VERSION = "v0.2.3-repair"
EXPECTED_APP_SHORT_VERSION = "0.2.3"
EXPECTED_APP_BUILD_VERSION = "20260629.1"
EXPECTED_REMOTE_URL = "git@github.com:LinzeColin/CodexProject.git"
EXPECTED_UPSTREAM = "origin/main"
EVIDENCE_RELATIVE_PATH = Path("docs/pfi_v024/FINAL_DELIVERY_EVIDENCE.json")

CommandRunner = Callable[..., subprocess.CompletedProcess[str]]


def build_v024_final_delivery_payload(pfi_root: Path | None = None) -> dict[str, Any]:
    root = _resolve_pfi_root(pfi_root)
    evidence, load_issues = _load_delivery_evidence(root)
    app_audit = audit_v024_installed_apps(root)
    runtime_audit = audit_v024_read_only_runtime(root)
    evidence_issues = load_issues or validate_v024_final_delivery_evidence(evidence, app_audit, runtime_audit)
    product_commit = evidence.get("product_commit") if isinstance(evidence, dict) else None
    git_audit = audit_v024_git_delivery(root, product_commit=product_commit)
    evidence_audit = {
        "status": "pass" if not evidence_issues else "fail",
        "issues": evidence_issues,
        "path": str(root / EVIDENCE_RELATIVE_PATH),
        "product_commit": product_commit,
        "runtime_audit": runtime_audit,
    }
    return evaluate_v024_final_delivery(git_audit, app_audit, evidence_audit)


def evaluate_v024_final_delivery(
    git_audit: Mapping[str, Any],
    app_audit: Mapping[str, Any],
    evidence_audit: Mapping[str, Any],
) -> dict[str, Any]:
    git_passed = git_audit.get("status") == "pass" and not git_audit.get("issues")
    app_passed = app_audit.get("status") == "pass" and not app_audit.get("issues")
    evidence_passed = evidence_audit.get("status") == "pass" and not evidence_audit.get("issues")
    gate_passed = git_passed and app_passed and evidence_passed

    issues = [
        *[f"git:{issue}" for issue in git_audit.get("issues", [])],
        *[f"app:{issue}" for issue in app_audit.get("issues", [])],
        *[f"evidence:{issue}" for issue in evidence_audit.get("issues", [])],
    ]
    return {
        "schema": FINAL_DELIVERY_SCHEMA,
        "acceptance_id": FINAL_DELIVERY_ACCEPTANCE_ID,
        "target_version": TARGET_VERSION,
        "source_package_version": SOURCE_PACKAGE_VERSION,
        "gate_result": "pass" if gate_passed else "fail",
        "delivery_requirements": {
            "current_changes_uploaded": git_passed,
            "app_reinstalled": app_passed,
            "github_app_local_consistency_proven": gate_passed,
        },
        "git_delivery": dict(git_audit),
        "app_delivery": dict(app_audit),
        "delivery_evidence": dict(evidence_audit),
        "issues": issues,
        "product_goal_complete": gate_passed,
        "next_gate": None if gate_passed else FINAL_DELIVERY_GATE,
        "explicitly_not_done": [
            "future version work",
            "financial data mutation",
            "trading password collection or testing",
            "broker orders, payments, or automated real-money actions",
        ],
    }


def audit_v024_git_delivery(
    pfi_root: Path,
    *,
    product_commit: object,
    command_runner: CommandRunner = subprocess.run,
) -> dict[str, Any]:
    root = _resolve_pfi_root(pfi_root)
    repo_root = root.parent
    issues: list[str] = []

    branch = _git_output(repo_root, ["rev-parse", "--abbrev-ref", "HEAD"], command_runner, issues, "branch")
    upstream = _git_output(
        repo_root,
        ["rev-parse", "--abbrev-ref", "@{upstream}"],
        command_runner,
        issues,
        "upstream",
    )
    remote_url = _git_output(repo_root, ["remote", "get-url", "origin"], command_runner, issues, "remote_url")
    head = _git_output(repo_root, ["rev-parse", "HEAD^{commit}"], command_runner, issues, "head")
    origin_tracking = _git_output(
        repo_root,
        ["rev-parse", "refs/remotes/origin/main^{commit}"],
        command_runner,
        issues,
        "origin_tracking",
    )
    head_parent = _git_output(repo_root, ["rev-parse", "HEAD^1^{commit}"], command_runner, issues, "head_parent")
    status_output = _git_output(
        repo_root,
        ["status", "--porcelain=v1", "--untracked-files=all"],
        command_runner,
        issues,
        "worktree_status",
    )
    pfi_tree = _git_output(repo_root, ["rev-parse", "HEAD:PFI"], command_runner, issues, "pfi_tree")
    remote_main = _resolve_remote_main(repo_root, command_runner, issues)
    product_commit_is_ancestor = _is_ancestor(repo_root, product_commit, head, command_runner)
    product_commit_is_parent = bool(product_commit) and str(product_commit) == head_parent

    if branch != "codex/pfi":
        issues.append("branch_mismatch")
    if upstream != EXPECTED_UPSTREAM:
        issues.append("upstream_mismatch")
    if remote_url != EXPECTED_REMOTE_URL:
        issues.append("remote_url_mismatch")
    if not head or origin_tracking != head:
        issues.append("origin_tracking_mismatch")
    if not head or remote_main != head:
        issues.append("remote_main_mismatch")
    if status_output:
        issues.append("worktree_not_clean")
    if not pfi_tree:
        issues.append("pfi_tree_unresolved")
    if not product_commit_is_ancestor:
        issues.append("product_commit_not_ancestor")
    if not product_commit_is_parent:
        issues.append("product_commit_not_direct_parent")

    return {
        "status": "pass" if not issues else "fail",
        "issues": _dedupe(issues),
        "branch": branch,
        "upstream": upstream,
        "remote_url": remote_url,
        "head": head,
        "head_parent": head_parent,
        "origin_tracking": origin_tracking,
        "remote_main": remote_main,
        "pfi_tree": pfi_tree,
        "worktree_clean": not status_output,
        "product_commit": product_commit,
        "product_commit_is_ancestor": product_commit_is_ancestor,
        "product_commit_is_parent": product_commit_is_parent,
    }


def audit_v024_installed_apps(
    pfi_root: Path,
    *,
    app_paths: Mapping[str, Path] | None = None,
    command_runner: CommandRunner = subprocess.run,
    expected_launcher_fingerprint: str | None = None,
) -> dict[str, Any]:
    root = _resolve_pfi_root(pfi_root)
    targets = dict(app_paths or _default_app_paths())
    issues: list[str] = []
    entries: dict[str, dict[str, Any]] = {}
    source_plist = root / "macos" / "PFI.app" / "Contents" / "Info.plist"
    source_plist_fingerprint = _sha256_file(source_plist) if source_plist.is_file() else None
    if source_plist_fingerprint is None:
        issues.append("source_info_plist_missing")
    compiled_launcher_fingerprint = expected_launcher_fingerprint or _compile_launcher_fingerprint(
        root,
        command_runner,
    )
    if compiled_launcher_fingerprint is None:
        issues.append("launcher_compile_failed")

    for label, raw_path in targets.items():
        app_path = Path(raw_path).expanduser()
        entry_issues: list[str] = []
        contents = app_path / "Contents"
        plist_path = contents / "Info.plist"
        launcher_path = contents / "MacOS" / "PFI"
        binding_path = contents / "Resources" / "PFI_PROJECT_ROOT"

        if not app_path.exists():
            entry_issues.append("app_missing")
        binding = _read_text(binding_path)
        if binding != str(root):
            entry_issues.append("binding_mismatch")
        plist = _read_plist(plist_path)
        if plist.get("CFBundleShortVersionString") != EXPECTED_APP_SHORT_VERSION:
            entry_issues.append("short_version_mismatch")
        if plist.get("CFBundleVersion") != EXPECTED_APP_BUILD_VERSION:
            entry_issues.append("build_version_mismatch")
        plist_fingerprint = _sha256_file(plist_path)
        if source_plist_fingerprint and plist_fingerprint != source_plist_fingerprint:
            entry_issues.append("source_plist_mismatch")
        launcher_fingerprint = _sha256_file(launcher_path)
        launcher_code_fingerprint = (
            _sha256_file(launcher_path)
            if expected_launcher_fingerprint is not None
            else _macho_section_fingerprint(launcher_path, command_runner, root)
        )
        if launcher_fingerprint is None or not os.access(launcher_path, os.X_OK):
            entry_issues.append("launcher_missing_or_not_executable")
        if launcher_code_fingerprint is None:
            entry_issues.append("launcher_code_fingerprint_unavailable")
        if compiled_launcher_fingerprint and launcher_code_fingerprint != compiled_launcher_fingerprint:
            entry_issues.append("compiled_launcher_mismatch")

        codesign_result = _run_command(
            command_runner,
            ["/usr/bin/codesign", "--verify", "--deep", "--strict", str(app_path)],
            cwd=root,
            timeout=15,
        )
        if codesign_result.returncode != 0:
            entry_issues.append("codesign_failed")

        dry_run_result = _run_command(
            command_runner,
            [str(launcher_path)],
            cwd=root,
            timeout=15,
            env={**os.environ, "PFI_APP_LAUNCH_DRY_RUN": "1"},
        )
        dry_run_output = f"{dry_run_result.stdout}\n{dry_run_result.stderr}".strip()
        expected_dry_run_output = (
            f"PFI_APP_LAUNCH: project={root} command=./StartPFI.command "
            f"command_path={root / 'StartPFI.command'} mode=spawn-command"
        )
        if dry_run_result.returncode != 0 or dry_run_output != expected_dry_run_output:
            entry_issues.append("launcher_dry_run_mismatch")

        if label == "desktop":
            applications = targets.get("applications")
            if not app_path.is_symlink() or applications is None or app_path.resolve() != Path(applications).resolve():
                entry_issues.append("desktop_link_mismatch")

        issues.extend(f"{label}:{issue}" for issue in entry_issues)
        entries[label] = {
            "path": str(app_path),
            "resolved_path": str(app_path.resolve(strict=False)),
            "project_root": binding,
            "short_version": plist.get("CFBundleShortVersionString"),
            "build_version": plist.get("CFBundleVersion"),
            "launcher_sha256": launcher_fingerprint,
            "launcher_code_sha256": launcher_code_fingerprint,
            "info_plist_sha256": plist_fingerprint,
            "codesign_verified": "codesign_failed" not in entry_issues,
            "dry_run_verified": "launcher_dry_run_mismatch" not in entry_issues,
            "issues": entry_issues,
        }

    launcher_fingerprints = sorted(
        {entry["launcher_sha256"] for entry in entries.values() if entry.get("launcher_sha256")}
    )
    launcher_code_fingerprints = sorted(
        {entry["launcher_code_sha256"] for entry in entries.values() if entry.get("launcher_code_sha256")}
    )
    plist_fingerprints = sorted(
        {entry["info_plist_sha256"] for entry in entries.values() if entry.get("info_plist_sha256")}
    )
    if len(launcher_fingerprints) != 1:
        issues.append("launcher_fingerprint_mismatch")
    if len(launcher_code_fingerprints) != 1:
        issues.append("launcher_code_fingerprint_mismatch")
    if len(plist_fingerprints) != 1:
        issues.append("plist_fingerprint_mismatch")

    return {
        "status": "pass" if not issues else "fail",
        "issues": _dedupe(issues),
        "project_root": str(root),
        "entries": entries,
        "compiled_launcher_code_sha256": compiled_launcher_fingerprint,
        "launcher_fingerprints": launcher_fingerprints,
        "launcher_code_fingerprints": launcher_code_fingerprints,
        "plist_fingerprints": plist_fingerprints,
    }


def audit_v024_read_only_runtime(
    pfi_root: Path,
    *,
    command_runner: CommandRunner = subprocess.run,
    expected_bundle_hash: str | None = None,
) -> dict[str, Any]:
    root = _resolve_pfi_root(pfi_root)
    expected_hash = expected_bundle_hash or str(build_v024_stage2_web_bundle_manifest(root)["webBundleHash"])
    script = root / "scripts" / "validate_v024_final_delivery_read_only.js"
    result = _run_command(
        command_runner,
        ["node", str(script)],
        cwd=root.parent,
        timeout=120,
    )
    issues: list[str] = []
    try:
        snapshot = json.loads(result.stdout)
    except json.JSONDecodeError:
        snapshot = {}
        issues.append("runtime_probe_output_invalid")
    if result.returncode != 0:
        issues.append("runtime_probe_failed")
    if not isinstance(snapshot, dict):
        snapshot = {}
        issues.append("runtime_probe_payload_not_object")
    summary = snapshot.get("summary")
    if snapshot.get("schema") != "PFIV024ReadOnlyRuntimeSnapshotV1":
        issues.append("runtime_probe_schema_mismatch")
    if snapshot.get("status") != "Pass" or not isinstance(summary, dict) or summary.get("fail") != 0:
        issues.append("runtime_probe_status_failed")
    if snapshot.get("mode") != "read_only_no_pfi_data_or_reports_write":
        issues.append("runtime_probe_mode_mismatch")
    if snapshot.get("disk_web_bundle_hash") != expected_hash:
        issues.append("runtime_disk_bundle_hash_mismatch")
    if snapshot.get("runtime_disk_bundle_hash_match") is not True:
        issues.append("runtime_bundle_not_bound_to_disk")
    if snapshot.get("app_localhost_same_bundle_hash") is not True:
        issues.append("app_localhost_bundle_hash_mismatch")
    expected_loaded_assets = {
        relative: (_sha256_file(root / relative) or "").removeprefix("sha256:")
        for relative in (
            "web/styles/tokens.css",
            "web/app/version.js",
            "web/app/entry_audit.js",
            "web/app/routes.js",
            "web/app/shell.js",
        )
    }
    if snapshot.get("loaded_asset_sha256") != expected_loaded_assets:
        issues.append("loaded_asset_hash_mismatch")
    expected_loaded_assets_by_entry = {
        "app": expected_loaded_assets,
        "localhost": expected_loaded_assets,
    }
    if snapshot.get("loaded_asset_sha256_by_entry") != expected_loaded_assets_by_entry:
        issues.append("loaded_asset_entry_map_mismatch")
    if snapshot.get("loaded_assets_match_disk") is not True:
        issues.append("loaded_assets_not_bound_to_disk")
    if not snapshot.get("healthy_urls"):
        issues.append("runtime_health_missing")
    for error_key in ("console_errors", "page_errors", "http_errors"):
        if snapshot.get(error_key) != []:
            issues.append(f"runtime_{error_key}")
    if snapshot.get("project_roots") != [str(root)]:
        issues.append("runtime_project_root_mismatch")
    if snapshot.get("app_paths") != ["/Applications/PFI.app"]:
        issues.append("runtime_app_path_mismatch")
    return {
        "status": "pass" if not issues else "fail",
        "issues": _dedupe(issues),
        "snapshot": snapshot,
        "stderr": result.stderr.strip(),
    }


def validate_v024_final_delivery_evidence(
    evidence: Mapping[str, Any],
    app_audit: Mapping[str, Any],
    runtime_audit: Mapping[str, Any],
) -> list[str]:
    issues: list[str] = []
    if evidence.get("schema") != FINAL_DELIVERY_EVIDENCE_SCHEMA:
        issues.append("schema_mismatch")
    if evidence.get("acceptance_id") != FINAL_DELIVERY_ACCEPTANCE_ID:
        issues.append("acceptance_id_mismatch")
    if evidence.get("target_version") != TARGET_VERSION:
        issues.append("target_version_mismatch")
    if evidence.get("source_package_version") != SOURCE_PACKAGE_VERSION:
        issues.append("source_package_version_mismatch")
    if not re.fullmatch(r"[0-9a-f]{40}", str(evidence.get("product_commit", ""))):
        issues.append("product_commit_invalid")
    if evidence.get("install_command") != "PFI/scripts/installPFIEntryApps.sh --all":
        issues.append("install_command_mismatch")

    fingerprints = evidence.get("app_fingerprints", {})
    if not isinstance(fingerprints, dict) or (
        fingerprints.get("launcher_sha256") != app_audit.get("launcher_fingerprints")
        or fingerprints.get("launcher_code_sha256") != app_audit.get("launcher_code_fingerprints")
        or fingerprints.get("info_plist_sha256") != app_audit.get("plist_fingerprints")
    ):
        issues.append("app_fingerprint_mismatch")

    if not _acceptance_passed(
        evidence.get("app_acceptance"),
        expected_schema="PFIOSMacOSAppAcceptanceLiteV1",
    ):
        issues.append("app_acceptance_failed")
    if not _runtime_snapshot_passed(evidence.get("runtime_snapshot")):
        issues.append("runtime_snapshot_failed")
    if runtime_audit.get("status") != "pass" or runtime_audit.get("issues"):
        issues.append("live_runtime_audit_failed")
    if evidence.get("runtime_snapshot") != runtime_audit.get("snapshot"):
        issues.append("runtime_snapshot_mismatch")

    protected_paths = evidence.get("protected_paths")
    if not isinstance(protected_paths, dict) or (
        protected_paths.get("before_metadata_sha256") != protected_paths.get("after_metadata_sha256")
        or protected_paths.get("mutated") is not False
    ):
        issues.append("protected_paths_changed")

    review = evidence.get("independent_review")
    if not isinstance(review, dict) or review.get("status") != "approved" or review.get("findings") != []:
        issues.append("independent_review_not_approved")
    return _dedupe(issues)


def _acceptance_passed(value: object, *, expected_schema: str) -> bool:
    if not isinstance(value, dict):
        return False
    summary = value.get("summary")
    return (
        value.get("schema") == expected_schema
        and value.get("status") == "Pass"
        and isinstance(summary, dict)
        and summary.get("fail") == 0
    )


def _runtime_snapshot_passed(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    summary = value.get("summary")
    return (
        value.get("schema") == "PFIV024ReadOnlyRuntimeSnapshotV1"
        and value.get("status") == "Pass"
        and value.get("mode") == "read_only_no_pfi_data_or_reports_write"
        and isinstance(summary, dict)
        and summary.get("fail") == 0
        and bool(value.get("healthy_urls"))
        and re.fullmatch(r"[0-9a-f]{64}", str(value.get("disk_web_bundle_hash", ""))) is not None
        and isinstance(value.get("runtime_web_bundle_hashes"), dict)
        and value.get("app_localhost_same_bundle_hash") is True
        and value.get("runtime_disk_bundle_hash_match") is True
        and value.get("loaded_assets_match_disk") is True
        and bool(value.get("loaded_asset_sha256"))
        and value.get("loaded_asset_sha256_by_entry")
        == {
            "app": value.get("loaded_asset_sha256"),
            "localhost": value.get("loaded_asset_sha256"),
        }
        and value.get("console_errors") == []
        and value.get("page_errors") == []
        and value.get("http_errors") == []
        and bool(value.get("project_roots"))
        and value.get("app_paths") == ["/Applications/PFI.app"]
    )


def _load_delivery_evidence(root: Path) -> tuple[dict[str, Any], list[str]]:
    path = root / EVIDENCE_RELATIVE_PATH
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}, ["evidence_file_missing"]
    except (OSError, json.JSONDecodeError):
        return {}, ["evidence_file_invalid"]
    if not isinstance(value, dict):
        return {}, ["evidence_payload_not_object"]
    return value, []


def _compile_launcher_fingerprint(root: Path, runner: CommandRunner) -> str | None:
    launcher_source = root / "macos" / "PFI_launcher.c"
    if not launcher_source.is_file():
        return None
    with tempfile.TemporaryDirectory(prefix="pfi-final-launcher-") as tmp:
        target = Path(tmp) / "PFI"
        result = _run_command(
            runner,
            [
                "clang",
                "-O2",
                "-Wall",
                "-Wextra",
                "-Wl,-no_uuid",
                "-o",
                str(target),
                str(launcher_source),
            ],
            cwd=root,
            timeout=30,
        )
        if result.returncode != 0:
            return None
        return _macho_section_fingerprint(target, runner, root)


def _macho_section_fingerprint(path: Path, runner: CommandRunner, cwd: Path) -> str | None:
    result = _run_command(
        runner,
        ["otool", "-l", str(path)],
        cwd=cwd,
        timeout=30,
    )
    if result.returncode != 0:
        return None
    lines = result.stdout.splitlines()
    sections: list[tuple[str, str, int, int]] = []
    for index, line in enumerate(lines):
        if not line.strip().startswith("sectname "):
            continue
        values: dict[str, str] = {}
        for detail in lines[index : index + 10]:
            parts = detail.strip().split(maxsplit=1)
            if len(parts) == 2:
                values.setdefault(parts[0], parts[1])
        try:
            sections.append(
                (
                    values["segname"],
                    values["sectname"],
                    int(values["offset"], 0),
                    int(values["size"], 0),
                )
            )
        except (KeyError, ValueError):
            return None
    if not sections:
        return None
    try:
        binary = path.read_bytes()
    except OSError:
        return None
    digest = hashlib.sha256()
    for segment, section, offset, size in sections:
        section_bytes = binary[offset : offset + size]
        if len(section_bytes) != size:
            return None
        digest.update(segment.encode("utf-8"))
        digest.update(b"\0")
        digest.update(section.encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(size).encode("ascii"))
        digest.update(b"\0")
        digest.update(section_bytes)
        digest.update(b"\0")
    return f"sha256:{digest.hexdigest()}"


def _default_app_paths() -> dict[str, Path]:
    return {
        "applications": Path("/Applications/PFI.app"),
        "downloads": Path.home() / "Downloads" / "PFI.app",
        "desktop": Path.home() / "Desktop" / "PFI.app",
    }


def _resolve_remote_main(repo_root: Path, runner: CommandRunner, issues: list[str]) -> str:
    result = _run_command(
        runner,
        ["git", "ls-remote", "origin", "refs/heads/main"],
        cwd=repo_root,
        timeout=30,
        git_environment=True,
    )
    if result.returncode != 0:
        issues.append("remote_main_unavailable")
        return ""
    fields = result.stdout.strip().split()
    if len(fields) != 2 or fields[1] != "refs/heads/main":
        issues.append("remote_main_invalid")
        return ""
    return fields[0]


def _is_ancestor(
    repo_root: Path,
    product_commit: object,
    head: str,
    runner: CommandRunner,
) -> bool:
    if not re.fullmatch(r"[0-9a-f]{40}", str(product_commit or "")) or not head:
        return False
    result = _run_command(
        runner,
        ["git", "merge-base", "--is-ancestor", str(product_commit), head],
        cwd=repo_root,
        timeout=15,
        git_environment=True,
    )
    return result.returncode == 0


def _git_output(
    repo_root: Path,
    arguments: Sequence[str],
    runner: CommandRunner,
    issues: list[str],
    label: str,
) -> str:
    result = _run_command(
        runner,
        ["git", *arguments],
        cwd=repo_root,
        timeout=20,
        git_environment=True,
    )
    if result.returncode != 0:
        issues.append(f"{label}_unavailable")
        return ""
    return result.stdout.strip()


def _run_command(
    runner: CommandRunner,
    command: list[str],
    *,
    cwd: Path,
    timeout: int,
    env: Mapping[str, str] | None = None,
    git_environment: bool = False,
) -> subprocess.CompletedProcess[str]:
    command_env = dict(env or os.environ)
    if git_environment:
        command_env.update({"GIT_NO_LAZY_FETCH": "1", "GIT_TERMINAL_PROMPT": "0"})
    try:
        return runner(
            command,
            cwd=str(cwd),
            env=command_env,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return subprocess.CompletedProcess(command, 124, "", str(exc))


def _read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError:
        return None


def _read_plist(path: Path) -> dict[str, Any]:
    try:
        with path.open("rb") as handle:
            value = plistlib.load(handle)
    except (OSError, plistlib.InvalidFileException):
        return {}
    return value if isinstance(value, dict) else {}


def _sha256_file(path: Path) -> str | None:
    try:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None
    return f"sha256:{digest}"


def _resolve_pfi_root(pfi_root: Path | None) -> Path:
    root = Path(pfi_root) if pfi_root is not None else Path(__file__).resolve().parents[2]
    return root.expanduser().resolve()


def _dedupe(values: Sequence[str]) -> list[str]:
    return list(dict.fromkeys(values))


def main() -> int:
    payload = build_v024_final_delivery_payload()
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["gate_result"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
