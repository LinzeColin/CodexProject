#!/usr/bin/env python3
"""Audit and deterministically render root governance evidence boundaries."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = ROOT / "governance" / "artifact_policy.json"
FULL_LOG_SUFFIXES = (".log", ".stdout", ".stderr", ".transcript")
FULL_LOG_NAME_PARTS = ("full-log", "full_log", "raw-log", "raw_log")


def load_policy(path: Path = DEFAULT_POLICY) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Policy must be a JSON object: {path}")
    return data


def _nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _duplicates(values: Iterable[str]) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return duplicates


def validate_policy(policy: dict[str, Any], *, root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    if policy.get("schema_version") != 1:
        errors.append("schema_version must equal 1")
    for field in ("policy_id", "owner"):
        if not _nonempty(policy.get(field)):
            errors.append(f"{field} must be non-empty")

    canonical = policy.get("canonical_resources")
    canonical = canonical if isinstance(canonical, list) else []
    canonical_paths = [str(item.get("path") or "") for item in canonical if isinstance(item, dict)]
    fact_domains = [str(item.get("fact_domain") or "") for item in canonical if isinstance(item, dict)]
    for duplicate in sorted(_duplicates(canonical_paths)):
        errors.append(f"duplicate canonical path: {duplicate}")
    for duplicate in sorted(_duplicates(fact_domains)):
        errors.append(f"duplicate editable canonical fact domain: {duplicate}")
    for index, item in enumerate(canonical):
        if not isinstance(item, dict):
            errors.append(f"canonical_resources[{index}] must be an object")
            continue
        for field in ("path", "fact_domain", "writer", "retention"):
            if not _nonempty(item.get(field)):
                errors.append(f"canonical_resources[{index}].{field} must be non-empty")
        path = root / str(item.get("path") or "")
        if str(item.get("path") or "") and not path.is_file():
            errors.append(f"canonical resource missing: {path.relative_to(root)}")

    derived = policy.get("derived_views")
    derived = derived if isinstance(derived, list) else []
    derived_paths: list[str] = []
    for index, item in enumerate(derived):
        if not isinstance(item, dict):
            errors.append(f"derived_views[{index}] must be an object")
            continue
        path_value = str(item.get("path") or "")
        derived_paths.append(path_value)
        if item.get("editable_fact_source") is not False:
            errors.append(f"derived view must not be an editable fact source: {path_value}")
        if not item.get("source_refs"):
            errors.append(f"derived view missing source_refs: {path_value}")
        for field in ("path", "writer", "retention"):
            if not _nonempty(item.get(field)):
                errors.append(f"derived_views[{index}].{field} must be non-empty")
        if path_value and not (root / path_value).is_file():
            errors.append(f"derived view missing: {path_value}")
    for overlap in sorted(set(canonical_paths) & set(derived_paths)):
        errors.append(f"resource cannot be both canonical and derived: {overlap}")

    contracts = policy.get("contract_resources")
    contracts = contracts if isinstance(contracts, list) else []
    for index, item in enumerate(contracts):
        if not isinstance(item, dict):
            errors.append(f"contract_resources[{index}] must be an object")
            continue
        for field in ("path", "owner", "writer", "retention"):
            if not _nonempty(item.get(field)):
                errors.append(f"contract_resources[{index}].{field} must be non-empty")
        path_value = str(item.get("path") or "")
        if path_value and not (root / path_value).is_file():
            errors.append(f"contract resource missing: {path_value}")

    compact = policy.get("compact_receipts")
    if not isinstance(compact, dict):
        errors.append("compact_receipts must be an object")
    else:
        for field in ("directory", "basename_prefix", "extension", "writer", "retention"):
            if not _nonempty(compact.get(field)):
                errors.append(f"compact_receipts.{field} must be non-empty")
        if compact.get("append_only") is not True:
            errors.append("compact_receipts.append_only must be true")
        if not isinstance(compact.get("max_bytes"), int) or int(compact.get("max_bytes") or 0) <= 0:
            errors.append("compact_receipts.max_bytes must be a positive integer")
        for field in ("required_pointer_fields", "forbidden_recursive_keys"):
            if not isinstance(compact.get(field), list):
                errors.append(f"compact_receipts.{field} must be an array")

    legacy = policy.get("retained_legacy_collections")
    legacy = legacy if isinstance(legacy, list) else []
    legacy_keys: list[str] = []
    for index, item in enumerate(legacy):
        if not isinstance(item, dict):
            errors.append(f"retained_legacy_collections[{index}] must be an object")
            continue
        key = f"{item.get('path', '')}|{item.get('selector', '')}"
        legacy_keys.append(key)
        for field in ("path", "selector", "owner", "retention", "reason"):
            if not _nonempty(item.get(field)):
                errors.append(f"retained_legacy_collections[{index}].{field} must be non-empty")
        if item.get("mutable") is not False:
            errors.append(f"retained legacy collection must be read-only: {item.get('path', '')}")
        baseline = item.get("baseline")
        if not isinstance(baseline, dict):
            errors.append(f"retained_legacy_collections[{index}].baseline must be an object")
        else:
            if not isinstance(baseline.get("count"), int) or int(baseline.get("count") or 0) < 0:
                errors.append(f"retained_legacy_collections[{index}].baseline.count is invalid")
            if not isinstance(baseline.get("bytes"), int) or int(baseline.get("bytes") or 0) < 0:
                errors.append(f"retained_legacy_collections[{index}].baseline.bytes is invalid")
            digest = str(baseline.get("sha256") or "")
            if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
                errors.append(f"retained_legacy_collections[{index}].baseline.sha256 is invalid")
    for duplicate in sorted(_duplicates(legacy_keys)):
        errors.append(f"duplicate retained legacy collection: {duplicate}")

    transient = policy.get("transient_artifacts")
    transient = transient if isinstance(transient, list) else []
    for index, item in enumerate(transient):
        if not isinstance(item, dict):
            errors.append(f"transient_artifacts[{index}] must be an object")
            continue
        if item.get("tracked") is not False:
            errors.append(f"transient_artifacts[{index}].tracked must be false")
        for field in ("locator", "writer"):
            if not _nonempty(item.get(field)):
                errors.append(f"transient_artifacts[{index}].{field} must be non-empty")
        if not isinstance(item.get("retention_days"), int) or int(item.get("retention_days") or 0) <= 0:
            errors.append(f"transient_artifacts[{index}].retention_days must be positive")
    return errors


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )


def _tracked_files(root: Path, directory: str) -> list[Path]:
    result = _git(root, "ls-files", "--", directory)
    if result.returncode == 0:
        return [root / line for line in result.stdout.splitlines() if line]
    base = root / directory
    return sorted(path for path in base.rglob("*") if path.is_file()) if base.is_dir() else []


def _select_collection_files(root: Path, item: dict[str, Any]) -> list[Path]:
    paths = _tracked_files(root, str(item.get("path") or ""))
    selector = str(item.get("selector") or "")
    if selector == "all_files":
        return paths
    allowlist_marker = "basename_allowlist:"
    if selector.startswith(allowlist_marker):
        names = selector[len(allowlist_marker) :].split(",")
        if not names or any(not name or Path(name).name != name for name in names):
            raise ValueError(f"Invalid legacy basename allowlist: {selector}")
        if len(set(names)) != len(names):
            raise ValueError(f"Duplicate legacy basename allowlist entry: {selector}")
        return [path for path in paths if path.name in set(names)]
    prefix_marker = "basename_not_prefix:"
    if selector.startswith(prefix_marker):
        prefix = selector[len(prefix_marker) :]
        return [path for path in paths if not path.name.startswith(prefix)]
    raise ValueError(f"Unsupported legacy selector: {selector}")


def collection_metrics(root: Path, item: dict[str, Any]) -> dict[str, Any]:
    paths = sorted(_select_collection_files(root, item), key=lambda path: path.relative_to(root).as_posix())
    aggregate = hashlib.sha256()
    total_bytes = 0
    for path in paths:
        payload = path.read_bytes()
        relative = path.relative_to(root).as_posix()
        total_bytes += len(payload)
        aggregate.update(f"{hashlib.sha256(payload).hexdigest()}  {relative}\n".encode("utf-8"))
    return {"count": len(paths), "bytes": total_bytes, "sha256": aggregate.hexdigest()}


def _recursive_keys(value: object) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            keys.add(str(key).casefold())
            keys.update(_recursive_keys(child))
    elif isinstance(value, list):
        for child in value:
            keys.update(_recursive_keys(child))
    return keys


def validate_compact_receipt(path: Path, contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    max_bytes = int(contract.get("max_bytes") or 0)
    size = path.stat().st_size
    if size > max_bytes:
        errors.append(f"compact receipt exceeds {max_bytes} bytes: {path} ({size})")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return errors + [f"compact receipt is not valid UTF-8 JSON: {path}: {exc}"]
    if not isinstance(payload, dict):
        return errors + [f"compact receipt must be a JSON object: {path}"]
    for field in contract.get("required_pointer_fields") or []:
        if field not in payload or payload[field] in (None, "", []):
            errors.append(f"compact receipt missing pointer field {field}: {path}")
    forbidden = {str(key).casefold() for key in contract.get("forbidden_recursive_keys") or []}
    found = sorted(_recursive_keys(payload) & forbidden)
    if found:
        errors.append(f"compact receipt embeds full-output keys {', '.join(found)}: {path}")
    return errors


def compact_receipt_paths(root: Path, contract: dict[str, Any]) -> list[Path]:
    directory = str(contract.get("directory") or "")
    prefix = str(contract.get("basename_prefix") or "")
    extension = str(contract.get("extension") or "")
    return sorted(
        (
            path
            for path in _tracked_files(root, directory)
            if path.name.startswith(prefix) and path.name.endswith(extension)
        ),
        key=lambda path: path.relative_to(root).as_posix(),
    )


def _changed_entries(root: Path, base_ref: str) -> tuple[list[dict[str, str]], list[str]]:
    verify = _git(root, "rev-parse", "--verify", f"{base_ref}^{{commit}}")
    if verify.returncode != 0:
        return [], [f"base ref is not a commit: {base_ref}"]
    result = _git(root, "diff", "--name-status", "--find-renames", base_ref, "--")
    if result.returncode != 0:
        return [], [f"git diff failed for base ref {base_ref}: {result.stderr.strip()}"]
    entries: list[dict[str, str]] = []
    for line in result.stdout.splitlines():
        parts = line.split("\t")
        status = parts[0]
        if status.startswith(("R", "C")) and len(parts) >= 3:
            entries.append({"status": status, "old_path": parts[1], "path": parts[2]})
        elif len(parts) >= 2:
            entries.append({"status": status, "path": parts[1]})
    return entries, []


def _path_in_collection(path: str, item: dict[str, Any]) -> bool:
    directory = str(item.get("path") or "").rstrip("/")
    if not (path == directory or path.startswith(f"{directory}/")):
        return False
    selector = str(item.get("selector") or "")
    if selector == "all_files":
        return True
    allowlist_marker = "basename_allowlist:"
    if selector.startswith(allowlist_marker):
        return Path(path).name in set(selector[len(allowlist_marker) :].split(","))
    marker = "basename_not_prefix:"
    if selector.startswith(marker):
        return not Path(path).name.startswith(selector[len(marker) :])
    return True


def _is_compact_receipt_path(path: str, contract: dict[str, Any]) -> bool:
    directory = str(contract.get("directory") or "").rstrip("/")
    name = Path(path).name
    return (
        path.startswith(f"{directory}/")
        and name.startswith(str(contract.get("basename_prefix") or ""))
        and name.endswith(str(contract.get("extension") or ""))
    )


def validate_changed_entries(entries: list[dict[str, str]], policy: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    compact = policy.get("compact_receipts") or {}
    transient_locators = [
        str(item.get("locator") or "")
        for item in policy.get("transient_artifacts") or []
        if isinstance(item, dict) and not str(item.get("locator") or "").startswith("$")
    ]
    for entry in entries:
        status = entry.get("status", "")
        path = entry.get("path", "")
        for legacy in policy.get("retained_legacy_collections") or []:
            if isinstance(legacy, dict) and _path_in_collection(path, legacy):
                errors.append(f"retained legacy evidence is read-only ({status}): {path}")
                break
        if _is_compact_receipt_path(path, compact):
            if not status.startswith("A"):
                errors.append(f"compact Task receipt is append-only ({status}): {path}")
        elif path.startswith(f"{str(compact.get('directory') or '').rstrip('/')}/"):
            errors.append(f"new run evidence must use the compact Task receipt namespace: {path}")
        lower_name = Path(path).name.casefold()
        if status.startswith("A") and (
            lower_name.endswith(FULL_LOG_SUFFIXES)
            or any(part in lower_name for part in FULL_LOG_NAME_PARTS)
        ):
            errors.append(f"new full log/output must remain an untracked artifact: {path}")
        for locator in transient_locators:
            pattern = locator.replace("**", "*")
            if fnmatch.fnmatch(path, pattern) or path.startswith(locator.split("/**", 1)[0].rstrip("/") + "/"):
                errors.append(f"transient artifact path must not be tracked ({status}): {path}")
                break
    return errors


def validate_gitignore(policy: dict[str, Any], *, root: Path = ROOT) -> list[str]:
    path = root / ".gitignore"
    if not path.is_file():
        return [".gitignore is missing"]
    lines = {line.strip() for line in path.read_text(encoding="utf-8").splitlines()}
    return [
        f".gitignore missing required artifact pattern: {pattern}"
        for pattern in policy.get("required_gitignore_patterns") or []
        if pattern not in lines
    ]


def validate_human_entry(policy: dict[str, Any], *, root: Path = ROOT) -> list[str]:
    contract = policy.get("human_entry") or {}
    path = root / str(contract.get("path") or "")
    if not path.is_file():
        return [f"human entry missing: {path}"]
    text = path.read_text(encoding="utf-8")
    heading = str(contract.get("heading") or "")
    if heading not in text:
        return [f"human entry heading missing: {heading}"]
    section = text.split(heading, 1)[1]
    next_heading = section.find("\n## ")
    if next_heading >= 0:
        section = section[:next_heading]
    errors = [
        f"human entry section missing required term: {term}"
        for term in contract.get("required_terms") or []
        if str(term) not in section
    ]
    minimum = int(contract.get("min_section_chars") or 0)
    if len(section.strip()) < minimum:
        errors.append(
            f"human entry section is link-only or incomplete: {len(section.strip())} < {minimum} chars"
        )
    return errors


def render_policy(policy: dict[str, Any]) -> str:
    lines = [
        "# Governance truth and artifact map",
        "",
        f"Policy: `{policy['policy_id']}`  ",
        f"Owner: `{policy['owner']}`",
        "",
        "## Canonical resources",
        "",
        "| Fact domain | Canonical path | Unique writer | Retention |",
        "|---|---|---|---|",
    ]
    for item in sorted(policy.get("canonical_resources") or [], key=lambda value: value["fact_domain"]):
        lines.append(
            f"| `{item['fact_domain']}` | `{item['path']}` | `{item['writer']}` | `{item['retention']}` |"
        )
    lines.extend(
        [
            "",
            "## Derived views",
            "",
            "| Path | Canonical sources | Editable fact source |",
            "|---|---|---|",
        ]
    )
    for item in sorted(policy.get("derived_views") or [], key=lambda value: value["path"]):
        refs = ", ".join(f"`{ref}`" for ref in item["source_refs"])
        lines.append(f"| `{item['path']}` | {refs} | `false` |")
    compact = policy["compact_receipts"]
    lines.extend(
        [
            "",
            "## Compact receipts",
            "",
            f"- Namespace: `{compact['directory']}/{compact['basename_prefix']}*{compact['extension']}`",
            f"- Maximum bytes: `{compact['max_bytes']}`",
            f"- Append-only: `{str(compact['append_only']).lower()}`",
            f"- Retention: `{compact['retention']}`",
            "",
            "## Retained legacy collections",
            "",
            "| Path | Selector | Owner | Mutable | Count | Bytes | SHA-256 |",
            "|---|---|---|---:|---:|---:|---|",
        ]
    )
    for item in sorted(policy.get("retained_legacy_collections") or [], key=lambda value: value["path"]):
        baseline = item["baseline"]
        lines.append(
            f"| `{item['path']}` | `{item['selector']}` | `{item['owner']}` | "
            f"`{str(item['mutable']).lower()}` | {baseline['count']} | {baseline['bytes']} | "
            f"`{baseline['sha256']}` |"
        )
    lines.extend(["", "## Transient artifacts", ""])
    for item in sorted(policy.get("transient_artifacts") or [], key=lambda value: value["locator"]):
        lines.append(
            f"- `{item['locator']}`: writer `{item['writer']}`, tracked `false`, "
            f"retention `{item['retention_days']} days`."
        )
    return "\n".join(lines) + "\n"


def audit_repository(
    *,
    root: Path = ROOT,
    policy_path: Path | None = None,
    base_ref: str | None = None,
) -> dict[str, Any]:
    policy_file = policy_path or root / "governance" / "artifact_policy.json"
    errors: list[str] = []
    try:
        policy = load_policy(policy_file)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        return {"schema_version": 1, "status": "FAIL", "errors": [str(exc)]}
    errors.extend(validate_policy(policy, root=root))

    legacy_metrics: list[dict[str, Any]] = []
    for item in policy.get("retained_legacy_collections") or []:
        try:
            current = collection_metrics(root, item)
        except (OSError, ValueError) as exc:
            errors.append(f"cannot measure legacy collection {item.get('path', '')}: {exc}")
            continue
        expected = item.get("baseline") or {}
        legacy_metrics.append(
            {
                "path": item.get("path"),
                "selector": item.get("selector"),
                "current": current,
                "expected": expected,
                "matches": current == expected,
            }
        )
        if current != expected:
            errors.append(
                f"retained legacy collection drift: {item.get('path', '')} "
                f"selector={item.get('selector', '')} expected={expected} current={current}"
            )

    compact = policy.get("compact_receipts") or {}
    receipts = compact_receipt_paths(root, compact)
    for path in receipts:
        errors.extend(validate_compact_receipt(path, compact))

    changed_entries: list[dict[str, str]] = []
    if base_ref:
        changed_entries, diff_errors = _changed_entries(root, base_ref)
        errors.extend(diff_errors)
        errors.extend(validate_changed_entries(changed_entries, policy))
        for entry in changed_entries:
            path = root / entry.get("path", "")
            if _is_compact_receipt_path(entry.get("path", ""), compact) and path.is_file():
                errors.extend(validate_compact_receipt(path, compact))

    errors.extend(validate_gitignore(policy, root=root))
    errors.extend(validate_human_entry(policy, root=root))
    duplicate_truth_count = len(
        _duplicates(
            str(item.get("fact_domain") or "")
            for item in policy.get("canonical_resources") or []
            if isinstance(item, dict)
        )
    )
    return {
        "schema_version": 1,
        "status": "PASS" if not errors else "FAIL",
        "policy_id": policy.get("policy_id"),
        "base_ref": base_ref or "CURRENT_TREE",
        "canonical_resource_count": len(policy.get("canonical_resources") or []),
        "duplicate_editable_truth_count": duplicate_truth_count,
        "compact_receipt_count": len(receipts),
        "compact_receipt_bytes": sum(path.stat().st_size for path in receipts),
        "retained_legacy": legacy_metrics,
        "changed_file_count": len(changed_entries),
        "errors": errors,
    }


def check_render(*, root: Path = ROOT, policy_path: Path | None = None) -> dict[str, Any]:
    policy_file = policy_path or root / "governance" / "artifact_policy.json"
    before = _git(root, "status", "--porcelain=v1").stdout
    policy = load_policy(policy_file)
    first = render_policy(policy)
    second = render_policy(policy)
    after = _git(root, "status", "--porcelain=v1").stdout
    deterministic = first == second
    zero_write = before == after
    return {
        "schema_version": 1,
        "status": "PASS" if deterministic and zero_write else "FAIL",
        "deterministic": deterministic,
        "zero_tracked_write": zero_write,
        "render_sha256": hashlib.sha256(first.encode("utf-8")).hexdigest(),
        "render_bytes": len(first.encode("utf-8")),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    audit = subparsers.add_parser("audit", help="Audit canonical, compact, legacy, and transient boundaries.")
    audit.add_argument("--base-ref", help="Optional commit/ref for changed-file append-only checks.")
    audit.add_argument("--json", action="store_true", help="Retained for an explicit machine-output contract.")
    subparsers.add_parser("render", help="Render the policy to deterministic Markdown on stdout.")
    subparsers.add_parser("check-render", help="Render twice in memory and prove zero repository writes.")
    args = parser.parse_args(argv)
    if args.command == "audit":
        summary = audit_repository(base_ref=args.base_ref)
        print(json.dumps(summary, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        return 0 if summary.get("status") == "PASS" else 1
    if args.command == "render":
        print(render_policy(load_policy()), end="")
        return 0
    if args.command == "check-render":
        summary = check_render()
        print(json.dumps(summary, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        return 0 if summary.get("status") == "PASS" else 1
    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
