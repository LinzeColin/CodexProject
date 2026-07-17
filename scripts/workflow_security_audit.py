#!/usr/bin/env python3
"""Fail-closed audit and deterministic renderer for GitHub workflow security."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = ROOT / "governance" / "workflow_policy.json"
DEFAULT_MATRIX = ROOT / "docs" / "governance" / "WORKFLOW_ROLE_MATRIX.md"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
ACTION_RE = re.compile(r"^([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_./-]+)?)@(.+)$")


def load_policy(path: Path = DEFAULT_POLICY) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"workflow policy must be a JSON object: {path}")
    return payload


def _duplicates(values: Iterable[str]) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return duplicates


def _nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_policy(policy: dict[str, Any], *, root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    if policy.get("schema_version") != 1:
        errors.append("schema_version must equal 1")
    for field in ("policy_id", "owner", "resolved_at"):
        if not _nonempty(policy.get(field)):
            errors.append(f"{field} must be non-empty")

    requirements = policy.get("requirements")
    if not isinstance(requirements, dict):
        errors.append("requirements must be an object")
        requirements = {}
    for field in (
        "workflow_directory",
        "codeowners_rule",
        "required_check_role",
        "settlement_role",
    ):
        if not _nonempty(requirements.get(field)):
            errors.append(f"requirements.{field} must be non-empty")
    if requirements.get("nested_project_workflows_allowed") is not False:
        errors.append("nested_project_workflows_allowed must be false")
    for field in ("forbidden_triggers", "forbidden_direct_run_contexts"):
        if not isinstance(requirements.get(field), list):
            errors.append(f"requirements.{field} must be an array")

    pins = policy.get("action_pins")
    pins = pins if isinstance(pins, list) else []
    pin_keys: list[str] = []
    for index, item in enumerate(pins):
        if not isinstance(item, dict):
            errors.append(f"action_pins[{index}] must be an object")
            continue
        for field in ("repository", "requested_tag", "commit_sha", "source"):
            if not _nonempty(item.get(field)):
                errors.append(f"action_pins[{index}].{field} must be non-empty")
        sha = str(item.get("commit_sha") or "")
        if not SHA_RE.fullmatch(sha):
            errors.append(f"action_pins[{index}].commit_sha must be a full SHA")
        key = f"{item.get('repository', '')}@{sha}"
        pin_keys.append(key)
    for duplicate in sorted(_duplicates(pin_keys)):
        errors.append(f"duplicate action pin: {duplicate}")

    workflows = policy.get("workflows")
    workflows = workflows if isinstance(workflows, list) else []
    paths: list[str] = []
    names: list[str] = []
    roles: list[str] = []
    for index, item in enumerate(workflows):
        if not isinstance(item, dict):
            errors.append(f"workflows[{index}] must be an object")
            continue
        for field in (
            "path",
            "name",
            "role",
            "owner",
            "purpose",
            "trust_boundary",
            "failure_behavior",
        ):
            if not _nonempty(item.get(field)):
                errors.append(f"workflows[{index}].{field} must be non-empty")
        for field in ("triggers", "expected_jobs", "local_dependencies"):
            if not isinstance(item.get(field), list):
                errors.append(f"workflows[{index}].{field} must be an array")
        if not isinstance(item.get("permissions"), dict):
            errors.append(f"workflows[{index}].permissions must be an object")
        if not isinstance(item.get("untrusted_prompt_input"), bool):
            errors.append(f"workflows[{index}].untrusted_prompt_input must be boolean")
        path = str(item.get("path") or "")
        paths.append(path)
        names.append(str(item.get("name") or ""))
        roles.append(str(item.get("role") or ""))
        if path and not (root / path).is_file():
            errors.append(f"workflow policy path missing: {path}")
        for dependency in item.get("local_dependencies") or []:
            if not (root / str(dependency)).exists():
                errors.append(f"workflow local dependency missing: {path} -> {dependency}")
    for label, values in (("path", paths), ("name", names), ("role", roles)):
        for duplicate in sorted(_duplicates(values)):
            errors.append(f"duplicate workflow {label}: {duplicate}")

    required_role = str(requirements.get("required_check_role") or "")
    settlement_role = str(requirements.get("settlement_role") or "")
    if roles.count(required_role) != 1:
        errors.append(f"required-check role must be unique: {required_role}")
    if roles.count(settlement_role) != 1:
        errors.append(f"settlement role must be unique: {settlement_role}")

    dispositions = policy.get("retired_or_merged")
    dispositions = dispositions if isinstance(dispositions, list) else []
    for index, item in enumerate(dispositions):
        if not isinstance(item, dict):
            errors.append(f"retired_or_merged[{index}] must be an object")
            continue
        for field in ("path", "disposition", "owner", "replacement", "reason"):
            if not _nonempty(item.get(field)):
                errors.append(f"retired_or_merged[{index}].{field} must be non-empty")
        source = root / str(item.get("path") or "")
        replacement = root / str(item.get("replacement") or "")
        if source.exists():
            errors.append(f"retired nested workflow still exists: {source.relative_to(root)}")
        replacement_ref = str(item.get("replacement") or "")
        # 跨仓替代物记法 owner/repo:path —— 项目迁出本仓后，其专属工作流随项目走，
        # 替代物不在本仓，无法做本地存在性校验，只校验记法完整。
        external = bool(re.match(r"^[\w.-]+/[\w.-]+:.+$", replacement_ref))
        if replacement_ref and not external and not replacement.is_file():
            errors.append(f"workflow replacement missing: {replacement.relative_to(root)}")
    return errors


def _block_lines(text: str, top_key: str) -> list[str]:
    lines = text.splitlines()
    start = None
    for index, line in enumerate(lines):
        if line == f"{top_key}:":
            start = index + 1
            break
    if start is None:
        return []
    block: list[str] = []
    for line in lines[start:]:
        if line and not line[0].isspace() and not line.lstrip().startswith("#"):
            break
        block.append(line)
    return block


def _strip_scalar(value: str) -> str:
    value = value.split(" #", 1)[0].strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def parse_workflow(text: str) -> dict[str, Any]:
    name_match = re.search(r"^name:\s*(.+?)\s*$", text, re.MULTILINE)
    name = _strip_scalar(name_match.group(1)) if name_match else ""

    trigger_lines = _block_lines(text, "on")
    triggers = sorted(
        {
            match.group(1)
            for line in trigger_lines
            if (match := re.match(r"^  ([A-Za-z0-9_-]+):", line))
        }
    )
    permission_lines = _block_lines(text, "permissions")
    permissions = {
        match.group(1): _strip_scalar(match.group(2))
        for line in permission_lines
        if (match := re.match(r"^  ([A-Za-z0-9_-]+):\s*(.+?)\s*$", line))
    }
    concurrency_lines = _block_lines(text, "concurrency")
    concurrency = {
        match.group(1): _strip_scalar(match.group(2))
        for line in concurrency_lines
        if (match := re.match(r"^  ([A-Za-z0-9_-]+):\s*(.+?)\s*$", line))
    }

    job_lines = _block_lines(text, "jobs")
    jobs: dict[str, list[str]] = {}
    current: str | None = None
    for line in job_lines:
        job_match = re.match(r"^  ([A-Za-z0-9_-]+):\s*$", line)
        if job_match:
            current = job_match.group(1)
            jobs[current] = []
        elif current is not None:
            jobs[current].append(line)
    missing_timeouts = sorted(
        job
        for job, lines in jobs.items()
        if not any(re.match(r"^    timeout-minutes:\s*[0-9]+\s*$", line) for line in lines)
    )
    job_permission_overrides = sorted(
        job
        for job, lines in jobs.items()
        if any(re.match(r"^    permissions:", line) for line in lines)
    )
    action_uses = [
        match.group(1)
        for line in text.splitlines()
        if (match := re.match(r"^\s*(?:-\s+)?uses:\s*([^\s#]+)", line))
    ]
    return {
        "name": name,
        "triggers": triggers,
        "permissions": permissions,
        "concurrency": concurrency,
        "jobs": sorted(jobs),
        "missing_timeouts": missing_timeouts,
        "job_permission_overrides": job_permission_overrides,
        "action_uses": action_uses,
    }


def extract_run_blocks(text: str) -> list[str]:
    lines = text.splitlines()
    blocks: list[str] = []
    index = 0
    while index < len(lines):
        match = re.match(r"^(\s+)run:\s*(.*)$", lines[index])
        if not match:
            index += 1
            continue
        indent = len(match.group(1))
        suffix = match.group(2).strip()
        if suffix and suffix not in {"|", ">", "|-", ">-"}:
            blocks.append(suffix)
            index += 1
            continue
        payload: list[str] = []
        index += 1
        while index < len(lines):
            line = lines[index]
            if line.strip() and len(line) - len(line.lstrip()) <= indent:
                break
            payload.append(line)
            index += 1
        blocks.append("\n".join(payload))
    return blocks


def audit_workflow_text(
    text: str,
    expected: dict[str, Any],
    *,
    allowed_pins: set[str],
    forbidden_triggers: set[str],
    forbidden_direct_contexts: list[str],
) -> tuple[list[str], dict[str, int]]:
    path = str(expected.get("path") or "<fixture>")
    errors: list[str] = []
    parsed = parse_workflow(text)
    if parsed["name"] != expected.get("name"):
        errors.append(f"{path}: workflow name drift")
    if parsed["triggers"] != sorted(expected.get("triggers") or []):
        errors.append(f"{path}: trigger matrix drift: {parsed['triggers']}")
    forbidden_present = sorted(set(parsed["triggers"]) & forbidden_triggers)
    if forbidden_present:
        errors.append(f"{path}: forbidden triggers: {', '.join(forbidden_present)}")
    if parsed["permissions"] != (expected.get("permissions") or {}):
        errors.append(f"{path}: permission matrix drift: {parsed['permissions']}")
    if parsed["jobs"] != sorted(expected.get("expected_jobs") or []):
        errors.append(f"{path}: job topology drift: {parsed['jobs']}")
    if parsed["missing_timeouts"]:
        errors.append(f"{path}: jobs missing timeout: {', '.join(parsed['missing_timeouts'])}")
    if not parsed["concurrency"].get("group") or "cancel-in-progress" not in parsed["concurrency"]:
        errors.append(f"{path}: workflow concurrency contract missing")
    if parsed["job_permission_overrides"]:
        errors.append(
            f"{path}: job permission overrides are not policy-owned: "
            + ", ".join(parsed["job_permission_overrides"])
        )

    unpinned = 0
    unapproved = 0
    for action in parsed["action_uses"]:
        if action.startswith("./"):
            continue
        match = ACTION_RE.fullmatch(action)
        if not match or not SHA_RE.fullmatch(match.group(2)):
            unpinned += 1
            errors.append(f"{path}: action is not pinned to a full SHA: {action}")
            continue
        if action not in allowed_pins:
            unapproved += 1
            errors.append(f"{path}: action SHA is not in the resolved allowlist: {action}")

    direct_context_violations = 0
    for run_block in extract_run_blocks(text):
        for forbidden in forbidden_direct_contexts:
            if f"${{{{ {forbidden}" in run_block:
                direct_context_violations += 1
                errors.append(f"{path}: untrusted context interpolated directly in run block: {forbidden}")

    high_privilege_violations = 0
    if expected.get("trust_boundary") == "trusted_default_branch_live_api_only":
        forbidden_fragments = (
            "actions/checkout",
            "download-artifact",
            "upload-artifact",
            "restore-cache",
            "github.event.pull_request.",
        )
        for fragment in forbidden_fragments:
            if fragment in text:
                high_privilege_violations += 1
                errors.append(f"{path}: high-privilege live-API role contains {fragment}")
        if parsed["action_uses"]:
            high_privilege_violations += 1
            errors.append(f"{path}: high-privilege live-API role must not invoke actions")
        if re.search(r"method\s*=\s*['\"]POST['\"]", text):
            high_privilege_violations += 1
            errors.append(f"{path}: settlement must not create GitHub objects")

    if expected.get("untrusted_prompt_input"):
        if "sandbox: read-only" not in text:
            errors.append(f"{path}: untrusted prompt role lacks read-only sandbox")
        if "persist-credentials: false" not in text:
            errors.append(f"{path}: untrusted prompt role persists checkout credentials")
        if not any(action.startswith("openai/codex-action@") for action in parsed["action_uses"]):
            errors.append(f"{path}: untrusted prompt role lacks the pinned Codex action")

    return errors, {
        "external_action_refs": len(parsed["action_uses"]),
        "unpinned_actions": unpinned,
        "unapproved_actions": unapproved,
        "missing_timeouts": len(parsed["missing_timeouts"]),
        "missing_concurrency": int(not parsed["concurrency"].get("group")),
        "overbroad_permissions": int(parsed["permissions"] != (expected.get("permissions") or {})),
        "forbidden_triggers": len(forbidden_present),
        "direct_context_violations": direct_context_violations,
        "high_privilege_violations": high_privilege_violations,
    }


def _tracked_workflows(root: Path) -> tuple[list[str], list[str]]:
    result = subprocess.run(
        ["git", "ls-files", "--", ".github/workflows", ":(glob)**/.github/workflows/*"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        root_paths = [
            path.relative_to(root).as_posix()
            for path in (root / ".github" / "workflows").glob("*.y*ml")
        ]
        nested_paths = [
            path.relative_to(root).as_posix()
            for path in root.glob("*/.github/workflows/*.y*ml")
        ]
        return sorted(root_paths), sorted(nested_paths)
    # ``git ls-files`` keeps staged deletions until the next commit.  Audit the
    # effective worktree so a deliberately retired nested workflow is not
    # reported as still active during its removal commit.
    paths = [
        line
        for line in result.stdout.splitlines()
        if line and (root / line).is_file()
    ]
    root_paths = [
        path
        for path in paths
        if path.startswith(".github/workflows/") and path.endswith((".yml", ".yaml"))
    ]
    nested_paths = [
        path
        for path in paths
        if "/.github/workflows/" in path and path.endswith((".yml", ".yaml"))
    ]
    return sorted(root_paths), sorted(nested_paths)


def audit_repository(*, root: Path = ROOT, policy_path: Path | None = None) -> dict[str, Any]:
    policy_file = policy_path or root / "governance" / "workflow_policy.json"
    errors: list[str] = []
    try:
        policy = load_policy(policy_file)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        return {"schema_version": 1, "status": "FAIL", "errors": [str(exc)]}
    errors.extend(validate_policy(policy, root=root))
    requirements = policy.get("requirements") or {}

    codeowners_path = root / ".github" / "CODEOWNERS"
    codeowners = codeowners_path.read_text(encoding="utf-8") if codeowners_path.is_file() else ""
    rule = str(requirements.get("codeowners_rule") or "")
    if rule not in {line.strip() for line in codeowners.splitlines()}:
        errors.append(f"CODEOWNERS missing workflow owner rule: {rule}")

    root_paths, nested_paths = _tracked_workflows(root)
    expected_by_path = {
        str(item["path"]): item
        for item in policy.get("workflows") or []
        if isinstance(item, dict) and item.get("path")
    }
    missing_policy = sorted(set(root_paths) - set(expected_by_path))
    stale_policy = sorted(set(expected_by_path) - set(root_paths))
    if missing_policy:
        errors.append("unowned workflows: " + ", ".join(missing_policy))
    if stale_policy:
        errors.append("policy references missing workflows: " + ", ".join(stale_policy))
    if nested_paths:
        errors.append("invalid nested workflows: " + ", ".join(nested_paths))

    allowed_pins = {
        f"{item['repository']}@{item['commit_sha']}"
        for item in policy.get("action_pins") or []
        if isinstance(item, dict) and item.get("repository") and item.get("commit_sha")
    }
    totals = {
        "external_action_refs": 0,
        "unpinned_actions": 0,
        "unapproved_actions": 0,
        "missing_timeouts": 0,
        "missing_concurrency": 0,
        "overbroad_permissions": 0,
        "forbidden_triggers": 0,
        "direct_context_violations": 0,
        "high_privilege_violations": 0,
    }
    for path in sorted(set(root_paths) & set(expected_by_path)):
        text = (root / path).read_text(encoding="utf-8")
        workflow_errors, metrics = audit_workflow_text(
            text,
            expected_by_path[path],
            allowed_pins=allowed_pins,
            forbidden_triggers={str(item) for item in requirements.get("forbidden_triggers") or []},
            forbidden_direct_contexts=[
                str(item) for item in requirements.get("forbidden_direct_run_contexts") or []
            ],
        )
        errors.extend(workflow_errors)
        for key, value in metrics.items():
            totals[key] += value

    roles = [
        str(item.get("role") or "")
        for item in policy.get("workflows") or []
        if isinstance(item, dict)
    ]
    duplicate_roles = len(_duplicates(roles))
    required_role = str(requirements.get("required_check_role") or "")
    settlement_role = str(requirements.get("settlement_role") or "")
    summary = {
        "schema_version": 1,
        "status": "PASS" if not errors else "FAIL",
        "policy_id": policy.get("policy_id"),
        "workflow_count": len(root_paths),
        "owned_workflow_count": len(set(root_paths) & set(expected_by_path)),
        "unowned_workflow_count": len(missing_policy),
        "duplicate_role_count": duplicate_roles,
        "transaction_ci_role_count": roles.count(required_role),
        "settlement_role_count": roles.count(settlement_role),
        "invalid_nested_workflow_count": len(nested_paths),
        "resolved_action_pin_count": len(allowed_pins),
        **totals,
        "errors": errors,
    }
    return summary


def _table_cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_policy(policy: dict[str, Any]) -> str:
    lines = [
        "# Workflow Role Matrix",
        "",
        f"- Policy: `{policy['policy_id']}`",
        f"- Owner: `{policy['owner']}`",
        f"- Action pins resolved: `{policy['resolved_at']}`",
        "",
        "## Active root workflows",
        "",
        "| Workflow | Role | Purpose | Triggers | Permissions | Jobs | Trust boundary | Failure behavior |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for item in sorted(policy.get("workflows") or [], key=lambda value: value["path"]):
        permissions = ", ".join(
            f"{key}:{value}" for key, value in sorted((item.get("permissions") or {}).items())
        )
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{item['path']}`",
                    f"`{item['role']}`",
                    _table_cell(item["purpose"]),
                    ", ".join(f"`{value}`" for value in sorted(item["triggers"])),
                    f"`{permissions}`",
                    ", ".join(f"`{value}`" for value in sorted(item["expected_jobs"])),
                    f"`{item['trust_boundary']}`",
                    _table_cell(item["failure_behavior"]),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Resolved third-party action pins",
            "",
            "| Repository | Requested tag | Commit SHA | Resolution source |",
            "|---|---|---|---|",
        ]
    )
    for item in sorted(
        policy.get("action_pins") or [],
        key=lambda value: (value["repository"], value["requested_tag"]),
    ):
        lines.append(
            f"| `{item['repository']}` | `{item['requested_tag']}` | "
            f"`{item['commit_sha']}` | {item['source']} |"
        )
    lines.extend(["", "## Merged or retired workflow paths", ""])
    for item in policy.get("retired_or_merged") or []:
        lines.append(
            f"- `{item['path']}` → `{item['replacement']}`: "
            f"{item['disposition']}. {item['reason']}"
        )
    lines.extend(
        [
            "",
            "## Hard gates",
            "",
            "- Every root workflow has one owner, purpose, unique role, trigger set, exact permissions, timeout, concurrency, and failure behavior.",
            "- Third-party actions use allowlisted 40-character commit SHAs; movable tags are comments only.",
            "- `pull_request_target` and nested project workflows are forbidden.",
            "- Untrusted strings enter shell only through environment variables; prompt-bearing workflows use a read-only Codex sandbox.",
            "- The one Settlement role uses trusted default-branch code and live APIs only; it never checks out PR code or consumes artifacts/caches.",
        ]
    )
    return "\n".join(lines) + "\n"


def check_render(
    *,
    root: Path = ROOT,
    policy_path: Path | None = None,
    matrix_path: Path | None = None,
) -> dict[str, Any]:
    policy_file = policy_path or root / "governance" / "workflow_policy.json"
    matrix_file = matrix_path or root / "docs" / "governance" / "WORKFLOW_ROLE_MATRIX.md"
    expected = render_policy(load_policy(policy_file))
    actual = matrix_file.read_text(encoding="utf-8") if matrix_file.is_file() else ""
    return {
        "schema_version": 1,
        "status": "PASS" if actual == expected else "FAIL",
        "matches": actual == expected,
        "render_bytes": len(expected.encode("utf-8")),
        "render_sha256": hashlib.sha256(expected.encode("utf-8")).hexdigest(),
        "errors": [] if actual == expected else [f"workflow role matrix drift: {matrix_file}"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    audit = subparsers.add_parser("audit", help="Audit workflow topology, ownership, permissions, and pins.")
    audit.add_argument("--json", action="store_true", help="Retained for explicit machine-output compatibility.")
    subparsers.add_parser("render", help="Render the canonical workflow policy to Markdown on stdout.")
    subparsers.add_parser("check-render", help="Compare the tracked role matrix with deterministic rendering.")
    args = parser.parse_args(argv)
    if args.command == "audit":
        summary = audit_repository()
        print(json.dumps(summary, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        return 0 if summary.get("status") == "PASS" else 1
    if args.command == "render":
        print(render_policy(load_policy()), end="")
        return 0
    if args.command == "check-render":
        summary = check_render()
        print(json.dumps(summary, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        return 0 if summary.get("status") == "PASS" else 1
    parser.error(f"unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
