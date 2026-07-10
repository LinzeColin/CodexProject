#!/usr/bin/env python3
"""Local Git backup control for Memory Atlas S04 P3.

Dry-run reports the backup contract without writing. Apply stages and commits
the configured backup scope locally; it never pushes to a remote.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


BACKUP_TARGETS = [
    "data/public_raw",
    "data/derived",
    "data/run_logs",
    "docs/reviews",
    "reports",
]
DEFAULT_MESSAGE = "Memory Atlas GitHub backup snapshot"
MANUAL_PUSH_COMMAND = "git push origin HEAD:main"


def run_git(repo_root: Path, args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if check and result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or f"git {' '.join(args)} failed")
    return result


def find_git_root(database_dir: Path) -> Path | None:
    result = subprocess.run(
        ["git", "-C", str(database_dir), "rev-parse", "--show-toplevel"],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    return Path(result.stdout.strip()).resolve()


def relative_to_git(repo_root: Path, path: Path) -> str:
    return path.resolve().relative_to(repo_root).as_posix()


def target_exists_or_tracked(repo_root: Path, database_dir: Path, target: str) -> bool:
    absolute = database_dir / target
    if absolute.exists():
        return True
    relative = relative_to_git(repo_root, absolute)
    result = run_git(repo_root, ["ls-files", "--error-unmatch", relative], check=False)
    return result.returncode == 0


def git_target_paths(repo_root: Path, database_dir: Path) -> list[str]:
    return [
        relative_to_git(repo_root, database_dir / target)
        for target in BACKUP_TARGETS
        if target_exists_or_tracked(repo_root, database_dir, target)
    ]


def status_files(repo_root: Path, targets: list[str]) -> list[str]:
    if not targets:
        return []
    result = run_git(repo_root, ["status", "--short", "--untracked-files=all", "--", *targets])
    files: list[str] = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        files.append(line[3:].strip())
    return sorted(files)


def staged_files(repo_root: Path) -> list[str]:
    result = run_git(repo_root, ["diff", "--cached", "--name-only"])
    return sorted(line for line in result.stdout.splitlines() if line.strip())


def base_contract(database_dir: Path, repo_root: Path | None, dry_run: bool, apply: bool) -> dict[str, Any]:
    return {
        "status": "PASS",
        "command": "push",
        "task_id": "MA-V12-S04P3",
        "acceptance_id": "ACC-MA-V12-S04P3",
        "database_dir": str(database_dir),
        "git_root": str(repo_root) if repo_root else "",
        "dry_run": dry_run,
        "apply": apply,
        "writes_files": apply,
        "backup_targets": BACKUP_TARGETS,
        "remote_push": False,
        "pushed": False,
        "manual_push_command": MANUAL_PUSH_COMMAND,
        "automation_mode": "local_commit_then_human_or_final_workflow_push",
        "中文原因": "GitHub 备份流程仅在本地记录可提交范围；本阶段不上传远端 main。",
        "fallback建议": "如 dry-run 显示无变更，先运行 sync/build-atlas；最终整体上传阶段再执行远端 push。",
    }


def fail_not_git(database_dir: Path, dry_run: bool, apply: bool) -> dict[str, Any]:
    return {
        "status": "FAIL",
        "reason": "not_git_worktree",
        "task_id": "MA-V12-S04P3",
        "acceptance_id": "ACC-MA-V12-S04P3",
        "database_dir": str(database_dir),
        "dry_run": dry_run,
        "apply": apply,
        "writes_files": False,
        "remote_push": False,
        "pushed": False,
        "中文原因": "当前 database-dir 不在 Git worktree 内，无法生成可恢复的 GitHub 备份提交。",
        "fallback建议": "切换到 LinzeColin/CodexProject/OpenAIDatabase 的规范 checkout 后重试；不要在临时目录伪造备份。",
    }


def installed_source_dry_run(database_dir: Path) -> dict[str, Any] | None:
    manifest_path = database_dir / "memory_atlas_source_workspace.json"
    if not manifest_path.is_file() or manifest_path.is_symlink() or (database_dir / ".git").exists():
        return None
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    original_repo_value = manifest.get("original_repo_root")
    if (
        manifest.get("schema_version") != "memory_atlas_source_workspace.v1"
        or not isinstance(original_repo_value, str)
        or not original_repo_value.strip()
        or Path(original_repo_value).expanduser().resolve() == database_dir.resolve()
    ):
        return None
    result = base_contract(database_dir, None, dry_run=True, apply=False)
    result.update(
        {
            "backup_scope_check": "installed_source_copy_no_git",
            "candidate_targets": [target for target in BACKUP_TARGETS if (database_dir / target).exists()],
            "changed_files": [],
            "writes_files": False,
            "remote_push": False,
            "github_main_upload": False,
            "中文原因": "已安装 source 副本不含 Git 元数据；本步骤只确认备份范围，最终 GitHub main 上传仍由 R8 整体交付执行。",
        }
    )
    return result


def dry_run(database_dir: Path, repo_root: Path) -> dict[str, Any]:
    targets = git_target_paths(repo_root, database_dir)
    result = base_contract(database_dir, repo_root, dry_run=True, apply=False)
    result.update({
        "writes_files": False,
        "candidate_targets": targets,
        "changed_files": status_files(repo_root, targets),
    })
    return result


def apply_backup(database_dir: Path, repo_root: Path, message: str) -> dict[str, Any]:
    targets = git_target_paths(repo_root, database_dir)
    result = base_contract(database_dir, repo_root, dry_run=False, apply=True)
    if not targets:
        result.update({
            "committed": False,
            "reason": "no_backup_targets",
            "writes_files": False,
            "中文原因": "没有找到 raw/derived/reports/run logs 备份目录。",
            "fallback建议": "先运行同步或构建命令生成可备份数据，再重新执行 backup apply。",
        })
        return result

    run_git(repo_root, ["add", "--", *targets])
    files = staged_files(repo_root)
    if not files:
        result.update({
            "committed": False,
            "reason": "no_changes",
            "writes_files": False,
            "committed_files": [],
            "中文原因": "备份范围内没有新的 Git 变更。",
            "fallback建议": "如预期有新数据，先运行 sync/build-atlas 并确认输出目录位于 backup scope。",
        })
        return result

    run_git(repo_root, ["commit", "-m", message])
    result.update({
        "committed": True,
        "commit_message": message,
        "committed_files": files,
    })
    return result


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Memory Atlas S04 P3 local GitHub backup control.")
    parser.add_argument("--database-dir", type=Path, default=Path("."))
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    parser.add_argument("--message", default=DEFAULT_MESSAGE)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    database_dir = args.database_dir.resolve()
    repo_root = find_git_root(database_dir)
    if repo_root is None:
        installed_result = installed_source_dry_run(database_dir) if args.dry_run else None
        if installed_result is not None:
            print(json.dumps(installed_result, ensure_ascii=False, indent=2, sort_keys=True))
            return 0
        print(json.dumps(fail_not_git(database_dir, args.dry_run, args.apply), ensure_ascii=False, indent=2, sort_keys=True))
        return 2

    try:
        result = dry_run(database_dir, repo_root) if args.dry_run else apply_backup(database_dir, repo_root, args.message)
    except RuntimeError as exc:
        result = {
            "status": "FAIL",
            "reason": "git_backup_failed",
            "task_id": "MA-V12-S04P3",
            "acceptance_id": "ACC-MA-V12-S04P3",
            "database_dir": str(database_dir),
            "writes_files": False,
            "remote_push": False,
            "pushed": False,
            "error": str(exc),
            "中文原因": "Git 本地备份命令失败。",
            "fallback建议": "检查 git status、权限和用户配置后重试；不要跳过失败继续伪造备份。",
        }
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 3

    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
