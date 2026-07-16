#!/usr/bin/env python3
"""Fail-closed Automation C publisher for one MacData device snapshot.

The publisher never writes directly to ``main`` and never uses a persistent
device branch. It creates one unique ``automation-c/*`` branch, opens one
same-repository PR, waits for trusted Settlement, verifies the exact files on
``main``, and requires the repository to return to zero open objects and only
the ``main`` branch. A caller invokes it once for raw data and, only after that
transaction is settled, once for the final report.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


SHA_RE = re.compile(r"^[0-9a-f]{40}$")
TASK_RE = re.compile(r"^TSK\.[A-Z][A-Za-z0-9]*\.[A-Z][A-Za-z0-9]*\.[0-9]{4}$")
ACCEPTANCE_RE = re.compile(r"^ACC\.[A-Z][A-Za-z0-9]*\.[A-Z][A-Za-z0-9]*\.[0-9]{4}$")
BRANCH_RE = re.compile(r"^automation-c/[A-Za-z0-9][A-Za-z0-9._/-]{0,180}$")
STAGE_RE = re.compile(r"^[a-z][a-z0-9-]{0,31}$")
REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
TRUSTED_SETTLEMENT_ACTOR = "github-actions"

PUBLISHED_PATHS = (
    "data/current_3days",
    "data/latest",
    "reports/current_3days",
    "reports/latest",
)

HIGH_RISK_SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"ghp_[A-Za-z0-9_]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(
        r"(?i)(api[_-]?key|access[_-]?token|auth[_-]?token|bearer[_-]?token|"
        r"password|passwd|secret)\s*[:=]\s*['\"]?[A-Za-z0-9_\-./+=]{12,}"
    ),
)


class AutomationCError(RuntimeError):
    """A fail-closed transaction or validation error."""


def _sanitize(text: str) -> str:
    result = text or ""
    for pattern in HIGH_RISK_SECRET_PATTERNS:
        result = pattern.sub("[REDACTED_CREDENTIAL]", result)
    return result


def _run(
    args: Sequence[str],
    *,
    cwd: Path | None = None,
    timeout: int = 30,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    try:
        process = subprocess.run(
            list(args),
            cwd=str(cwd) if cwd else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        raise AutomationCError(f"command unavailable or timed out: {args[0]}") from exc
    if check and process.returncode != 0:
        detail = _sanitize(process.stdout.strip())
        raise AutomationCError(
            f"command failed ({process.returncode}): {args[0]}: {detail[:500]}"
        )
    return process


def _safe_relative(value: str, field: str) -> str:
    path = Path(value)
    if path.is_absolute() or not value or ".." in path.parts:
        raise AutomationCError(f"{field} must be a safe repository-relative path")
    return path.as_posix()


def validate_config(config: Mapping[str, Any]) -> dict[str, Any]:
    required = {
        "device_key",
        "local_relative_dir",
        "default_remote",
        "repository",
        "base_branch",
        "legacy_archive_branch",
        "transaction_branch_prefix",
        "transaction_task_id",
        "transaction_acceptance_id",
        "settlement_timeout_seconds",
        "settlement_poll_seconds",
        "published_paths",
        "retention_days",
    }
    missing = sorted(required - set(config))
    if missing:
        raise AutomationCError(f"transaction config missing keys: {missing}")

    normalized = dict(config)
    repository = str(normalized["repository"])
    if REPOSITORY_RE.fullmatch(repository) is None:
        raise AutomationCError("repository must be owner/name")
    if normalized["base_branch"] != "main":
        raise AutomationCError("Automation C base_branch must be main")
    legacy = str(normalized["legacy_archive_branch"])
    if not legacy or legacy == "main" or legacy.startswith("automation-c/"):
        raise AutomationCError("legacy_archive_branch must identify the retired branch")
    prefix = str(normalized["transaction_branch_prefix"])
    if BRANCH_RE.fullmatch(prefix) is None:
        raise AutomationCError("transaction_branch_prefix must be reserved under automation-c/")
    task_id = str(normalized["transaction_task_id"])
    acceptance_id = str(normalized["transaction_acceptance_id"])
    if TASK_RE.fullmatch(task_id) is None or ACCEPTANCE_RE.fullmatch(acceptance_id) is None:
        raise AutomationCError("transaction task/acceptance IDs must use namespaced V2 format")
    if acceptance_id != task_id.replace("TSK.", "ACC.", 1):
        raise AutomationCError("transaction acceptance ID must match transaction task ID")
    local_relative_dir = _safe_relative(
        str(normalized["local_relative_dir"]), "local_relative_dir"
    )
    expected_suffix = f"OpenAIDatabase/macdata/{normalized['device_key']}"
    if local_relative_dir != expected_suffix:
        raise AutomationCError("local_relative_dir must match the selected device_key")
    published_paths = tuple(
        _safe_relative(str(item), "published_paths")
        for item in normalized["published_paths"]
    )
    if published_paths != PUBLISHED_PATHS:
        raise AutomationCError(
            f"published_paths must exactly equal {list(PUBLISHED_PATHS)}"
        )
    timeout = int(normalized["settlement_timeout_seconds"])
    poll = int(normalized["settlement_poll_seconds"])
    if timeout < 60 or timeout > 3600 or poll < 2 or poll > 60 or poll >= timeout:
        raise AutomationCError("settlement timeout/poll values are outside the safe bounds")
    if int(normalized["retention_days"]) < 1:
        raise AutomationCError("retention_days must be positive")
    normalized["local_relative_dir"] = local_relative_dir
    normalized["published_paths"] = list(published_paths)
    normalized["settlement_timeout_seconds"] = timeout
    normalized["settlement_poll_seconds"] = poll
    return normalized


def transaction_branch_name(config: Mapping[str, Any], stage: str, run_value: str) -> str:
    normalized = validate_config(config)
    if STAGE_RE.fullmatch(stage) is None:
        raise AutomationCError("stage must be a short lowercase slug")
    run_slug = re.sub(r"[^A-Za-z0-9._-]+", "-", run_value).strip("-.")
    if not run_slug:
        raise AutomationCError("run identifier cannot be empty")
    device_prefix = f"{normalized['device_key']}-"
    if run_slug.startswith(device_prefix):
        run_slug = run_slug[len(device_prefix) :]
    branch = f"{normalized['transaction_branch_prefix']}-{run_slug}-{stage}"
    if BRANCH_RE.fullmatch(branch) is None or ".." in branch or "//" in branch:
        raise AutomationCError("generated transaction branch is invalid")
    return branch


def _iter_snapshot_files(device_root: Path, published_paths: Iterable[str]) -> list[Path]:
    device_root = device_root.resolve()
    files: list[Path] = []
    for relative in published_paths:
        root = (device_root / _safe_relative(relative, "published path")).resolve()
        if root != device_root and device_root not in root.parents:
            raise AutomationCError("published path escapes device root")
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if path.is_symlink():
                raise AutomationCError(f"snapshot symlink is forbidden: {path}")
            if path.is_file():
                files.append(path)
    return files


def scan_for_secrets(paths: Iterable[Path]) -> list[str]:
    findings: list[str] = []
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError as exc:
            raise AutomationCError(f"cannot read snapshot file for secret scan: {path}") from exc
        for pattern in HIGH_RISK_SECRET_PATTERNS:
            if pattern.search(text):
                findings.append(path.as_posix())
                break
    return findings


def snapshot_manifest(device_root: Path, published_paths: Iterable[str]) -> dict[str, Any]:
    device_root = device_root.resolve()
    entries: dict[str, dict[str, Any]] = {}
    aggregate = hashlib.sha256()
    total_bytes = 0
    for path in _iter_snapshot_files(device_root, published_paths):
        relative = path.relative_to(device_root).as_posix()
        size = path.stat().st_size
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        entries[relative] = {"bytes": size, "sha256": digest}
        aggregate.update(f"{relative}\0{size}\0{digest}\n".encode("utf-8"))
        total_bytes += size
    return {
        "file_count": len(entries),
        "total_bytes": total_bytes,
        "aggregate_sha256": aggregate.hexdigest(),
        "files": entries,
    }


def simulate_snapshot(
    device_root: Path,
    config: Mapping[str, Any],
    stage: str,
    run_value: str,
) -> dict[str, Any]:
    normalized = validate_config(config)
    files = _iter_snapshot_files(device_root, normalized["published_paths"])
    findings = scan_for_secrets(files)
    if findings:
        raise AutomationCError(
            f"snapshot contains {len(findings)} high-risk credential-pattern files"
        )
    return {
        "mode": "LOCAL_SIMULATION_NO_REMOTE_WRITE",
        "device_key": normalized["device_key"],
        "repository": normalized["repository"],
        "base_branch": "main",
        "legacy_archive_branch": normalized["legacy_archive_branch"],
        "transaction_branch": transaction_branch_name(normalized, stage, run_value),
        "task_id": normalized["transaction_task_id"],
        "acceptance_id": normalized["transaction_acceptance_id"],
        "issue_mutations": 0,
        "preconditions": [
            "open_pr=0",
            "open_issue=0",
            "non_main_branch=0",
            "legacy_archive_branch_absent",
            "main_sha_stable",
        ],
        "steps": [
            "clone exact main",
            "create one unique automation-c branch",
            "copy only declared device snapshot paths",
            "scan and commit",
            "push exact temporary branch",
            "create one non-draft PR with exact head/base metadata",
            "wait for trusted Project Governance and Settlement",
            "verify exact snapshot hashes on main",
            "verify PR/Issue/non-main branch=0/0/0",
        ],
        "snapshot": snapshot_manifest(device_root, normalized["published_paths"]),
    }


def _remote_ref_sha(origin_url: str, branch: str) -> str | None:
    process = _run(
        ["git", "ls-remote", "--heads", origin_url, f"refs/heads/{branch}"],
        timeout=60,
    )
    line = process.stdout.strip()
    if not line:
        return None
    sha = line.split()[0]
    if SHA_RE.fullmatch(sha) is None:
        raise AutomationCError(f"remote returned invalid SHA for {branch}")
    return sha


def _remote_heads(origin_url: str) -> dict[str, str]:
    process = _run(["git", "ls-remote", "--heads", origin_url], timeout=60)
    heads: dict[str, str] = {}
    for line in process.stdout.splitlines():
        fields = line.split()
        if len(fields) != 2 or not fields[1].startswith("refs/heads/"):
            raise AutomationCError("unexpected git ls-remote output")
        name = fields[1][len("refs/heads/") :]
        if SHA_RE.fullmatch(fields[0]) is None:
            raise AutomationCError(f"invalid SHA for remote branch {name}")
        heads[name] = fields[0]
    return heads


def _gh_json(args: Sequence[str], *, cwd: Path | None = None) -> Any:
    process = _run(["gh", *args], cwd=cwd, timeout=60)
    try:
        return json.loads(process.stdout)
    except json.JSONDecodeError as exc:
        raise AutomationCError("GitHub CLI returned non-JSON output") from exc


def _open_counts(repository: str, *, cwd: Path | None = None) -> tuple[int, int]:
    pulls = _gh_json(
        ["api", f"repos/{repository}/pulls?state=open&per_page=100"], cwd=cwd
    )
    issues = _gh_json(
        ["api", f"repos/{repository}/issues?state=open&per_page=100"], cwd=cwd
    )
    if not isinstance(pulls, list) or not isinstance(issues, list):
        raise AutomationCError("unexpected GitHub open-object response")
    standalone = [item for item in issues if "pull_request" not in item]
    return len(pulls), len(standalone)


def _require_at_rest(repository: str, origin_url: str, base_branch: str) -> dict[str, Any]:
    open_pr, open_issue = _open_counts(repository)
    heads = _remote_heads(origin_url)
    non_main = sorted(name for name in heads if name != base_branch)
    if open_pr or open_issue or non_main:
        raise AutomationCError(
            "Automation C at-rest precheck failed: "
            f"open_pr={open_pr} open_issue={open_issue} non_main={non_main}"
        )
    if base_branch not in heads:
        raise AutomationCError("remote main branch is missing")
    return {
        "open_pr": open_pr,
        "open_issue": open_issue,
        "non_main_branches": non_main,
        "base_sha": heads[base_branch],
    }


def _automation_c_body(
    config: Mapping[str, Any],
    *,
    stage: str,
    run_value: str,
    head_sha: str,
    base_sha: str,
    manifest: Mapping[str, Any],
) -> str:
    for value in (head_sha, base_sha):
        if SHA_RE.fullmatch(value) is None:
            raise AutomationCError("PR metadata requires exact 40-character SHAs")
    marker = (
        "<!-- AUTOMATION_C_TRANSACTION_V1\n"
        f"task_id={config['transaction_task_id']}\n"
        f"acceptance_id={config['transaction_acceptance_id']}\n"
        f"head_sha={head_sha}\n"
        f"base_sha={base_sha}\n"
        "END_AUTOMATION_C_TRANSACTION_V1 -->"
    )
    return (
        f"{marker}\n\n"
        f"# MacData {config['device_key']} {stage}\n\n"
        f"- run: `{run_value}`\n"
        f"- source files: `{manifest['file_count']}`\n"
        f"- source bytes: `{manifest['total_bytes']}`\n"
        f"- aggregate SHA-256: `{manifest['aggregate_sha256']}`\n"
        "- issue mutation: `0`\n"
        "- persistent target: `main`\n"
    )


def _create_pr(
    config: Mapping[str, Any],
    *,
    branch: str,
    stage: str,
    run_value: str,
    body: str,
    cwd: Path,
) -> int:
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as handle:
        handle.write(body)
        body_path = Path(handle.name)
    try:
        process = _run(
            [
                "gh",
                "pr",
                "create",
                "--repo",
                str(config["repository"]),
                "--head",
                branch,
                "--base",
                "main",
                "--title",
                f"[macdata-{config['device_key']}] {stage} {run_value}"[:240],
                "--body-file",
                str(body_path),
            ],
            cwd=cwd,
            timeout=60,
        )
    finally:
        body_path.unlink(missing_ok=True)
    match = re.search(r"/pull/([0-9]+)(?:\s*)$", process.stdout.strip())
    if match is None:
        raise AutomationCError("gh pr create did not return a PR URL")
    return int(match.group(1))


def _wait_for_settlement(
    repository: str,
    pr_number: int,
    *,
    expected_branch: str,
    expected_head_sha: str,
    timeout_seconds: int,
    poll_seconds: int,
    cwd: Path,
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        payload = _gh_json(
            [
                "pr",
                "view",
                str(pr_number),
                "--repo",
                repository,
                "--json",
                "state,mergedAt,mergedBy,mergeCommit,headRefName,headRefOid,baseRefName",
            ],
            cwd=cwd,
        )
        if not isinstance(payload, dict):
            raise AutomationCError("unexpected PR settlement response")
        if payload.get("state") == "MERGED" and payload.get("mergedAt"):
            if payload.get("baseRefName") != "main":
                raise AutomationCError("settled PR base changed from main")
            if payload.get("headRefName") != expected_branch:
                raise AutomationCError("settled PR head branch changed")
            if payload.get("headRefOid") != expected_head_sha:
                raise AutomationCError("settled PR head SHA changed")
            merged_by = payload.get("mergedBy")
            actor = (
                str(merged_by.get("login") or "").casefold().removesuffix("[bot]")
                if isinstance(merged_by, dict)
                else ""
            )
            if actor != TRUSTED_SETTLEMENT_ACTOR:
                raise AutomationCError("PR was not merged by trusted Settlement")
            merge_commit = payload.get("mergeCommit")
            merge_sha = (
                str(merge_commit.get("oid") or "")
                if isinstance(merge_commit, dict)
                else ""
            )
            if SHA_RE.fullmatch(merge_sha) is None:
                raise AutomationCError("trusted Settlement merge SHA is missing")
            return payload
        if payload.get("state") == "CLOSED":
            raise AutomationCError("transaction PR closed without merge")
        time.sleep(poll_seconds)
    raise AutomationCError("trusted Settlement timed out")


def _delete_transaction_branch(origin_url: str, branch: str, *, cwd: Path) -> None:
    if BRANCH_RE.fullmatch(branch) is None:
        raise AutomationCError("refusing to delete a non-Automation-C branch")
    if _remote_ref_sha(origin_url, branch) is None:
        return
    _run(["git", "push", origin_url, "--delete", branch], cwd=cwd, timeout=60)
    if _remote_ref_sha(origin_url, branch) is not None:
        raise AutomationCError("transaction branch deletion did not settle")


def _compensate(
    repository: str,
    origin_url: str,
    branch: str,
    *,
    pr_number: int | None,
    cwd: Path,
) -> list[str]:
    actions: list[str] = []
    if pr_number is not None:
        process = _run(
            [
                "gh",
                "pr",
                "close",
                str(pr_number),
                "--repo",
                repository,
                "--delete-branch",
            ],
            cwd=cwd,
            timeout=60,
            check=False,
        )
        actions.append(f"close_pr_rc={process.returncode}")
    try:
        _delete_transaction_branch(origin_url, branch, cwd=cwd)
        actions.append("delete_branch=verified")
    except AutomationCError as exc:
        actions.append(f"delete_branch=failed:{_sanitize(str(exc))[:200]}")
    return actions


def _copy_snapshot(device_root: Path, destination: Path, published_paths: Iterable[str]) -> None:
    for relative in published_paths:
        source = device_root / relative
        target = destination / relative
        if target.exists():
            shutil.rmtree(target)
        if source.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(source, target, symlinks=False)


def _apply_retention(device_root: Path, retention_days: int) -> None:
    cutoff = dt.datetime.now().astimezone().date() - dt.timedelta(
        days=retention_days - 1
    )
    for relative in ("data/current_3days/raw", "reports/current_3days"):
        base = device_root / relative
        if not base.exists():
            continue
        for child in base.iterdir():
            if not child.is_dir():
                continue
            try:
                child_date = dt.date.fromisoformat(child.name)
            except ValueError:
                continue
            if child_date < cutoff:
                shutil.rmtree(child)


def publish_snapshot(
    repo_root: Path,
    device_root: Path,
    config: Mapping[str, Any],
    stage: str,
    run_value: str,
) -> dict[str, Any]:
    """Publish one device snapshot through a settled, short-lived PR."""

    normalized = validate_config(config)
    branch = transaction_branch_name(normalized, stage, run_value)
    source_files = _iter_snapshot_files(device_root, normalized["published_paths"])
    findings = scan_for_secrets(source_files)
    if findings:
        return {
            "ok": False,
            "status": "凭证扫描失败",
            "message": f"{len(findings)} 个文件命中高风险凭证模式，未创建 GitHub 对象。",
            "finding_count": len(findings),
        }

    origin_process = _run(
        [
            "git",
            "-C",
            str(repo_root),
            "remote",
            "get-url",
            str(normalized["default_remote"]),
        ],
        timeout=10,
    )
    origin_url = origin_process.stdout.strip()
    if not origin_url:
        return {"ok": False, "status": "上传失败", "message": "git remote URL 为空。"}

    pr_number: int | None = None
    branch_pushed = False
    tmp = Path(tempfile.mkdtemp(prefix=f"macdata-{normalized['device_key']}-{stage}-"))
    work = tmp / "repo"
    try:
        at_rest = _require_at_rest(
            str(normalized["repository"]), origin_url, "main"
        )
        if _remote_ref_sha(origin_url, str(normalized["legacy_archive_branch"])) is not None:
            raise AutomationCError("legacy archive branch still exists")
        base_sha = str(at_rest["base_sha"])

        _run(
            [
                "git",
                "clone",
                "--depth",
                "1",
                "--single-branch",
                "--branch",
                "main",
                origin_url,
                str(work),
            ],
            timeout=180,
        )
        cloned_sha = _run(["git", "rev-parse", "HEAD"], cwd=work).stdout.strip()
        if cloned_sha != base_sha:
            raise AutomationCError("cloned main SHA differs from locked base SHA")
        _run(["git", "checkout", "-b", branch], cwd=work)
        _run(["git", "config", "user.name", "Codex Automation C"], cwd=work)
        _run(
            ["git", "config", "user.email", "68840188+LinzeColin@users.noreply.github.com"],
            cwd=work,
        )

        destination = work / str(normalized["local_relative_dir"])
        _copy_snapshot(device_root, destination, normalized["published_paths"])
        _apply_retention(destination, int(normalized["retention_days"]))
        receipt_dir = destination / "reports" / "current_3days" / dt.date.today().isoformat()
        receipt_dir.mkdir(parents=True, exist_ok=True)
        receipt_path = receipt_dir / f"{stage}_automation_c_receipt.json"
        receipt_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "device_key": normalized["device_key"],
                    "stage": stage,
                    "run_id": run_value,
                    "task_id": normalized["transaction_task_id"],
                    "acceptance_id": normalized["transaction_acceptance_id"],
                    "persistent_branch": "main",
                    "transaction_branch": branch,
                    "issue_mutations": 0,
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        staged_files = _iter_snapshot_files(destination, normalized["published_paths"])
        staged_findings = scan_for_secrets(staged_files)
        if staged_findings:
            raise AutomationCError("staged snapshot failed credential scan")
        expected_manifest = snapshot_manifest(destination, normalized["published_paths"])

        _run(["git", "add", str(normalized["local_relative_dir"])], cwd=work, timeout=60)
        if not _run(["git", "status", "--porcelain=v1"], cwd=work).stdout.strip():
            raise AutomationCError("snapshot transaction produced no tracked change")
        commit_message = (
            f"data(macdata-{normalized['device_key']}): {stage} {run_value} via Automation C"
        )
        _run(["git", "commit", "-m", commit_message], cwd=work, timeout=60)
        head_sha = _run(["git", "rev-parse", "HEAD"], cwd=work).stdout.strip()
        if SHA_RE.fullmatch(head_sha) is None:
            raise AutomationCError("local transaction commit SHA is invalid")
        if _remote_ref_sha(origin_url, "main") != base_sha:
            raise AutomationCError("main drifted before transaction push")
        if _remote_ref_sha(origin_url, branch) is not None:
            raise AutomationCError("transaction branch already exists")
        if _open_counts(str(normalized["repository"]), cwd=work) != (0, 0):
            raise AutomationCError("single-flight open-object precheck drifted")

        _run(
            ["git", "push", "origin", f"HEAD:refs/heads/{branch}"],
            cwd=work,
            timeout=120,
        )
        branch_pushed = True
        if _remote_ref_sha(origin_url, branch) != head_sha:
            raise AutomationCError("remote transaction branch SHA verification failed")
        if _remote_ref_sha(origin_url, "main") != base_sha:
            raise AutomationCError("main drifted after transaction push")
        if _open_counts(str(normalized["repository"]), cwd=work) != (0, 0):
            raise AutomationCError("another transaction opened before PR creation")

        body = _automation_c_body(
            normalized,
            stage=stage,
            run_value=run_value,
            head_sha=head_sha,
            base_sha=base_sha,
            manifest=expected_manifest,
        )
        pr_number = _create_pr(
            normalized,
            branch=branch,
            stage=stage,
            run_value=run_value,
            body=body,
            cwd=work,
        )
        settlement = _wait_for_settlement(
            str(normalized["repository"]),
            pr_number,
            expected_branch=branch,
            expected_head_sha=head_sha,
            timeout_seconds=int(normalized["settlement_timeout_seconds"]),
            poll_seconds=int(normalized["settlement_poll_seconds"]),
            cwd=work,
        )

        _delete_transaction_branch(origin_url, branch, cwd=work)
        _run(["git", "fetch", "--depth", "1", "origin", "main"], cwd=work, timeout=120)
        _run(["git", "checkout", "--detach", "FETCH_HEAD"], cwd=work, timeout=30)
        main_sha = _run(["git", "rev-parse", "HEAD"], cwd=work).stdout.strip()
        if main_sha != _remote_ref_sha(origin_url, "main"):
            raise AutomationCError("verified checkout does not match current remote main")
        if settlement["mergeCommit"]["oid"] != main_sha:
            raise AutomationCError("remote main moved after trusted Settlement")
        actual_manifest = snapshot_manifest(
            work / str(normalized["local_relative_dir"]),
            normalized["published_paths"],
        )
        if actual_manifest != expected_manifest:
            raise AutomationCError("remote main snapshot hash reconciliation failed")
        final_state = _require_at_rest(
            str(normalized["repository"]), origin_url, "main"
        )
        return {
            "ok": True,
            "status": "Automation C 已合并并验证",
            "message": "短命 PR 已由 trusted Settlement 合并，main 文件哈希一致，终态 0/0/0。",
            "base_branch": "main",
            "transaction_branch": branch,
            "pr_number": pr_number,
            "head_commit_hash": head_sha,
            "main_commit_hash": main_sha,
            "remote_verified": True,
            "manifest": expected_manifest,
            "settlement": settlement,
            "final_state": final_state,
            "commit_message": commit_message,
        }
    except AutomationCError as exc:
        compensation: list[str] = []
        if branch_pushed:
            compensation = _compensate(
                str(normalized["repository"]),
                origin_url,
                branch,
                pr_number=pr_number,
                cwd=work if work.exists() else repo_root,
            )
        return {
            "ok": False,
            "status": "Automation C 事务失败",
            "message": _sanitize(str(exc)),
            "base_branch": "main",
            "transaction_branch": branch,
            "pr_number": pr_number,
            "remote_verified": False,
            "compensation": compensation,
        }
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
