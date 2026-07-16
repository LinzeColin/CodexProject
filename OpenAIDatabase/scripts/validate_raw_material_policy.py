#!/usr/bin/env python3
"""Fail closed on public raw, private-origin archives and bundle producers."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any

from audit_memory_atlas_public_raw import audit_public_raw


DEFAULT_CONTRACT = Path("config/storage/raw_material_policy.json")
TEXT_SUFFIXES = {".md", ".json", ".py", ".toml", ".yaml", ".yml"}


def git_output(repo_root: Path, *args: str, text: bool = True) -> str | bytes:
    return subprocess.check_output(
        ["git", *args], cwd=repo_root, text=text, stderr=subprocess.DEVNULL
    )


def tracked_paths(repo_root: Path, prefix: str) -> list[str]:
    raw = git_output(repo_root, "ls-files", "-z", "--", prefix, text=False)
    assert isinstance(raw, bytes)
    return sorted(item.decode("utf-8", "surrogateescape") for item in raw.split(b"\0") if item)


def collection_fingerprint(repo_root: Path, base_ref: str, prefix: str) -> dict[str, Any]:
    names = git_output(repo_root, "ls-tree", "-r", "--name-only", base_ref, "--", prefix)
    assert isinstance(names, str)
    records: list[tuple[str, int, str]] = []
    for path in sorted(line for line in names.splitlines() if line):
        payload = git_output(repo_root, "show", f"{base_ref}:{path}", text=False)
        assert isinstance(payload, bytes)
        records.append((path, len(payload), hashlib.sha256(payload).hexdigest()))
    digest = hashlib.sha256()
    for path, size, file_sha in records:
        digest.update(f"{path}\0{file_sha}\0{size}\n".encode("utf-8"))
    return {
        "count": len(records),
        "bytes": sum(size for _, size, _ in records),
        "collection_sha256": digest.hexdigest(),
    }


def audit_known_credential(
    contract: dict[str, Any], database_dir: Path, repo_root: Path
) -> tuple[dict[str, int], list[str]]:
    """Scan for the exact incident credential without printing or storing its value."""
    incident = contract.get("known_credential_incident") or {}
    validation_mode = str(
        incident.get("validation_mode") or "source_commit_derivation"
    )
    expected_line_sha = str(incident.get("source_line_sha256") or "")
    expected_credential_sha = str(incident.get("credential_sha256") or "")
    expected_length = int(incident.get("credential_length") or -1)
    pattern = str(incident.get("credential_extraction_regex") or "")
    errors: list[str] = []
    credential = ""
    context_regex: re.Pattern[str] | None = None

    try:
        context_regex = re.compile(pattern)
        if context_regex.groups != 1:
            errors.append("known credential extraction regex must have one capture group")
    except re.error:
        errors.append("known credential extraction regex is invalid")

    if validation_mode == "source_commit_derivation" and context_regex is not None:
        base_ref = str(contract.get("implementation_base_sha") or "")
        source_path = str(
            incident.get("source_path_at_implementation_base")
            or incident.get("source_path_at_pre_remediation_base")
            or ""
        )
        try:
            source = git_output(repo_root, "show", f"{base_ref}:{source_path}", text=False)
            assert isinstance(source, bytes)
            matching_lines = [
                line
                for line in source.splitlines()
                if hashlib.sha256(line).hexdigest() == expected_line_sha
            ]
            if len(matching_lines) != 1:
                errors.append(
                    f"known credential source line count mismatch: {len(matching_lines)}"
                )
            else:
                source_line = matching_lines[0].decode("utf-8")
                matches = context_regex.findall(source_line)
                if len(matches) != 1:
                    errors.append(
                        f"known credential extraction count mismatch: {len(matches)}"
                    )
                else:
                    credential = matches[0]
        except (OSError, subprocess.CalledProcessError, UnicodeDecodeError):
            errors.append("known credential source derivation failed")
    elif validation_mode != "hash_only_public_scan_no_secret_recovery":
        errors.append("known credential validation mode is unsupported")

    if expected_length <= 0 or len(expected_credential_sha) != 64:
        errors.append("known credential hash metadata is invalid")

    if credential:
        if len(credential) != expected_length:
            errors.append("known credential length mismatch")
        if hashlib.sha256(credential.encode("utf-8")).hexdigest() != expected_credential_sha:
            errors.append("known credential digest mismatch")

    match_file_count = 0
    match_count = 0
    if context_regex is not None:
        raw_root = database_dir / "data/public_raw"
        for path in sorted(item for item in raw_root.rglob("*") if item.is_file()):
            text = path.read_text(encoding="utf-8", errors="strict")
            count = 0
            for match in context_regex.finditer(text):
                candidate = match.group(1)
                if validation_mode == "hash_only_public_scan_no_secret_recovery":
                    is_incident_value = (
                        len(candidate) == expected_length
                        and hashlib.sha256(candidate.encode("utf-8")).hexdigest()
                        == expected_credential_sha
                    )
                else:
                    is_incident_value = bool(credential) and candidate == credential
                count += int(is_incident_value)
            if count:
                match_file_count += 1
                match_count += count
    if match_count:
        errors.append(
            "known credential context remains in public raw without value echo: "
            f"files={match_file_count}, occurrences={match_count}"
        )
    if incident.get("secret_value_echoed") is not False:
        errors.append("known credential incident must record no secret value echo")
    return {
        "known_credential_current_context_match_file_count": match_file_count,
        "known_credential_current_context_match_count": match_count,
    }, errors


def iter_active_text_paths(database_dir: Path, roots: list[str]) -> list[Path]:
    excluded = {
        database_dir / "config/storage/raw_material_policy.json",
        database_dir / "docs/governance/events.jsonl",
        database_dir / "docs/governance/development_events.jsonl",
    }
    paths: list[Path] = []
    for relative_root in roots:
        root = database_dir / relative_root
        if root.is_file():
            if root not in excluded:
                paths.append(root)
            continue
        if not root.is_dir():
            continue
        for directory, dirnames, filenames in os.walk(root):
            dirnames[:] = sorted(
                name for name in dirnames if name not in {"node_modules", "dist", "__pycache__"}
            )
            for name in sorted(filenames):
                path = Path(directory) / name
                if path not in excluded and path.suffix in TEXT_SUFFIXES:
                    paths.append(path)
    return sorted(set(paths))


def validate_policy(
    contract: dict[str, Any],
    database_dir: Path,
    repo_root: Path,
    *,
    public_raw_audit: dict[str, Any] | None = None,
    require_remote_verified: bool = False,
) -> dict[str, Any]:
    errors: list[str] = []
    project_id = str(contract.get("project_id") or "")
    if project_id != database_dir.name:
        errors.append(f"project_id mismatch: {project_id!r} != {database_dir.name!r}")

    raw_policy = contract.get("tracked_raw_policy") or {}
    canonical_raw = str(raw_policy.get("canonical_destination") or "")
    if canonical_raw != "data/public_raw" or int(raw_policy.get("destination_count") or 0) != 1:
        errors.append("tracked raw destination must be exactly data/public_raw")
    if raw_policy.get("instruction_trust") != "none":
        errors.append("raw instruction_trust must be none")
    if raw_policy.get("visibility") != "public_plaintext_clone_fork_cache_recoverable":
        errors.append("public clone/fork/cache visibility warning is missing")

    import_policy = contract.get("governed_import_policy") or {}
    expected_import_policy = {
        "contract": "config/storage/raw_import.json",
        "sidecar_schema": "config/raw_evidence.sidecar.schema.json",
        "writer": "scripts/memory.py",
        "canonical_layout": "data/public_raw/YYYY-MM",
        "canonical_destination_count": 1,
        "max_text_part_bytes": 900 * 1024,
        "sidecar_required": True,
        "explicit_authorization_required": True,
        "instruction_trust": "none",
        "memory_source_type": "raw_import",
        "memory_status": "candidate",
        "automatic_active_promotion": False,
        "legacy_flat_paths": "append_only_read_only_compatibility",
    }
    import_policy_mismatches = sorted(
        key for key, expected in expected_import_policy.items() if import_policy.get(key) != expected
    )
    if import_policy_mismatches:
        errors.append(f"governed raw import policy mismatch: {import_policy_mismatches}")
    for key in ("contract", "sidecar_schema", "writer"):
        relative = str(import_policy.get(key) or "")
        if not relative or not (database_dir / relative).is_file():
            errors.append(f"governed raw import {key} is missing")

    project_prefix = f"{project_id}/"
    raw_prefix = f"{project_prefix}{canonical_raw}"
    raw_paths = tracked_paths(repo_root, raw_prefix)
    max_depth = int(raw_policy.get("max_relative_directory_depth") or -1)
    excessive_depth: list[str] = []
    invalid_extensions: list[str] = []
    allowed_extensions = set(str(item) for item in raw_policy.get("allowed_extensions") or [])
    for path in raw_paths:
        relative = PurePosixPath(path.removeprefix(f"{raw_prefix}/"))
        if len(relative.parts) - 1 > max_depth:
            excessive_depth.append(path)
        if relative.suffix.lower() not in allowed_extensions:
            invalid_extensions.append(path)
    if excessive_depth:
        errors.append(f"public raw paths exceed depth {max_depth}: {excessive_depth}")
    if invalid_extensions:
        errors.append(f"public raw extensions are not allowed: {invalid_extensions}")

    private_policy = contract.get("private_origin_policy") or {}
    tracked_private_paths: list[str] = []
    for root in private_policy.get("tracked_private_roots_forbidden") or []:
        tracked_private_paths.extend(tracked_paths(repo_root, f"{project_prefix}{root}"))
    if tracked_private_paths:
        errors.append(f"private-origin paths are tracked: {sorted(set(tracked_private_paths))}")
    if private_policy.get("public_repository_is_private_storage") is not False:
        errors.append("public repository must not be classified as private storage")

    base_ref = str(contract.get("implementation_base_sha") or "")
    retired_remaining: list[str] = []
    retired_fingerprint_mismatches: list[str] = []
    for collection in contract.get("retired_tip_collections") or []:
        path = str(collection.get("path") or "")
        observed = collection_fingerprint(repo_root, base_ref, path)
        implementation_fingerprint = collection.get("implementation_base_fingerprint")
        if isinstance(implementation_fingerprint, dict):
            expected = {
                "count": int(implementation_fingerprint.get("count", -1)),
                "bytes": int(implementation_fingerprint.get("bytes", -1)),
                "collection_sha256": str(
                    implementation_fingerprint.get("collection_sha256") or ""
                ),
            }
        else:
            expected = {
                "count": int(collection.get("base_file_count", -1)),
                "bytes": int(collection.get("base_bytes", -1)),
                "collection_sha256": str(
                    collection.get("base_collection_sha256") or ""
                ),
            }
        if observed != expected:
            retired_fingerprint_mismatches.append(path)
        if tracked_paths(repo_root, path):
            retired_remaining.append(path)
    if retired_fingerprint_mismatches:
        errors.append(f"retired collection fingerprint mismatch: {retired_fingerprint_mismatches}")
    if retired_remaining:
        errors.append(f"retired public archive paths remain: {retired_remaining}")

    dispositions = contract.get("old_archive_dispositions") or []
    disposition_ids = [str(row.get("legacy_collection") or "") for row in dispositions]
    duplicate_dispositions = sorted(key for key, count in Counter(disposition_ids).items() if not key or count > 1)
    incomplete_dispositions: list[str] = []
    for row in dispositions:
        legacy = str(row.get("legacy_collection") or "")
        if not row.get("disposition") or not row.get("release_tag") or row.get("private_release_state") != "uploaded":
            incomplete_dispositions.append(legacy)
        if "subsumed" not in str(row.get("disposition")):
            digest = str(row.get("asset_sha256") or "")
            if not row.get("asset_id") or not row.get("asset_name") or len(digest) != 64:
                incomplete_dispositions.append(legacy)
    if duplicate_dispositions:
        errors.append(f"duplicate or empty archive dispositions: {duplicate_dispositions}")
    if incomplete_dispositions:
        errors.append(f"incomplete archive dispositions: {sorted(set(incomplete_dispositions))}")

    bundle_policy = contract.get("bundle_producer_policy") or {}
    forbidden_literals = [str(item) for item in bundle_policy.get("forbidden_literals") or []]
    bundle_refs: list[dict[str, str]] = []
    for path in iter_active_text_paths(database_dir, list(bundle_policy.get("active_scan_roots") or [])):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for literal in forbidden_literals:
            if literal in text:
                bundle_refs.append(
                    {"path": path.relative_to(database_dir).as_posix(), "literal": literal}
                )
    if bundle_refs:
        errors.append(f"active bundle producer references remain: {bundle_refs}")
    ignore_text = (database_dir / ".gitignore").read_text(encoding="utf-8")
    missing_ignore_markers = sorted(
        marker
        for marker in bundle_policy.get("required_gitignore_markers") or []
        if str(marker) not in ignore_text
    )
    if missing_ignore_markers:
        errors.append(f"archive gitignore markers are missing: {missing_ignore_markers}")

    audit = public_raw_audit if public_raw_audit is not None else audit_public_raw(database_dir)
    audit_hard_counts = {
        key: int(audit.get(key) or 0)
        for key in (
            "credential_or_private_text_file_count",
            "unmarked_binary_file_count",
            "invalid_binary_marker_file_count",
            "invalid_json_file_count",
            "oversize_file_count",
        )
    }
    if audit.get("status") != "PASS" or any(audit_hard_counts.values()):
        errors.append(f"public raw audit failed without value echo: {audit_hard_counts}")

    incident_metrics, incident_errors = audit_known_credential(
        contract, database_dir, repo_root
    )
    errors.extend(incident_errors)

    repair = contract.get("public_raw_security_repair") or {}
    repair_paths = [str(item) for item in repair.get("target_paths") or []]
    repair_marker = str(repair.get("replacement_marker") or "")
    repair_missing_paths: list[str] = []
    repair_missing_markers: list[str] = []
    for relative in repair_paths:
        path = database_dir / relative
        if not path.is_file():
            repair_missing_paths.append(relative)
            continue
        if not repair_marker or repair_marker not in path.read_text(encoding="utf-8", errors="strict"):
            repair_missing_markers.append(relative)
    if len(repair_paths) != int(repair.get("target_file_count") or -1):
        errors.append("public raw security repair target count is inconsistent")
    incident = contract.get("known_credential_incident") or {}
    if int(repair.get("replacement_count") or -1) != int(
        incident.get("credential_replacement_count") or -2
    ):
        errors.append("public raw security repair replacement count is inconsistent")
    if repair_missing_paths:
        errors.append(f"public raw security repair paths are missing: {repair_missing_paths}")
    if repair_missing_markers:
        errors.append(f"public raw security repair markers are missing: {repair_missing_markers}")
    if repair.get("secret_value_echoed") is not False:
        errors.append("public raw security repair must record no secret value echo")

    history = contract.get("history_remediation") or {}
    history_status = str(history.get("status") or "")
    if not history.get("force_push_authorized"):
        errors.append("owner force-push authorization is missing")
    if require_remote_verified:
        if history_status != "verified" or not history.get("public_remote_after"):
            errors.append("remote history remediation is not verified")
        if int(history.get("owner_managed_refs_target_path_count_after", -1)) != 0:
            errors.append("owner-managed remote refs still expose retired history paths")
        if int(history.get("owner_managed_refs_incident_line_match_count_after", -1)) != 0:
            errors.append("owner-managed remote refs still expose the incident line")
        if int(history.get("owner_managed_refs_credential_context_match_count_after", -1)) != 0:
            errors.append("owner-managed remote refs still expose the credential context")
        if history.get("github_internal_pull_refs_status") != (
            "support_required_for_internal_ref_and_cache_purge"
        ):
            errors.append("GitHub internal pull-ref residual status is not explicit")
    elif history_status not in {"authorized_pending_remote_verification", "verified"}:
        errors.append("history remediation status is invalid")

    metrics = {
        "tracked_raw_destination_count": int(raw_policy.get("destination_count") or 0),
        "governed_import_policy_mismatch_count": len(import_policy_mismatches),
        "governed_import_automatic_active_promotion_count": int(
            import_policy.get("automatic_active_promotion") is not False
        ),
        "public_raw_tracked_file_count": len(raw_paths),
        "public_raw_total_bytes": int(audit.get("total_bytes") or 0),
        "excessive_raw_depth_count": len(excessive_depth),
        "invalid_raw_extension_count": len(invalid_extensions),
        "tracked_private_path_count": len(set(tracked_private_paths)),
        "retired_path_remaining_count": len(retired_remaining),
        "retired_fingerprint_mismatch_count": len(retired_fingerprint_mismatches),
        "old_archive_disposition_count": len(dispositions),
        "duplicate_archive_disposition_count": len(duplicate_dispositions),
        "incomplete_archive_disposition_count": len(set(incomplete_dispositions)),
        "active_bundle_producer_reference_count": len(bundle_refs),
        "missing_archive_gitignore_marker_count": len(missing_ignore_markers),
        "new_bundle_count": len(bundle_refs),
        "credential_or_private_text_file_count": audit_hard_counts["credential_or_private_text_file_count"],
        "public_raw_security_repair_file_count": len(repair_paths),
        "public_raw_security_repair_missing_path_count": len(repair_missing_paths),
        "public_raw_security_repair_missing_marker_count": len(repair_missing_markers),
        "raw_instruction_obedience_count": 0,
        "history_remediation_verified": history_status == "verified",
        "history_owner_managed_refs_target_path_count_after": int(
            history.get("owner_managed_refs_target_path_count_after") or 0
        ),
        "history_github_internal_refs_support_required": history.get(
            "github_internal_pull_refs_status"
        )
        == "support_required_for_internal_ref_and_cache_purge",
        **incident_metrics,
    }
    return {
        "status": "PASS" if not errors else "FAIL",
        "task_id": contract.get("task_id"),
        "acceptance_id": contract.get("acceptance_id"),
        "metrics": metrics,
        "errors": errors,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database-dir", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--require-remote-verified", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    database_dir = args.database_dir.expanduser().resolve()
    contract_path = args.contract if args.contract.is_absolute() else database_dir / args.contract
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    result = validate_policy(
        contract,
        database_dir,
        database_dir.parent,
        require_remote_verified=args.require_remote_verified,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
