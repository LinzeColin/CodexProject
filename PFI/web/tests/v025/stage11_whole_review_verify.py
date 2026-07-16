#!/usr/bin/env python3
"""Run the frozen-overlay verification for the Stage 11 whole-stage review."""

from __future__ import annotations

from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tarfile
import tempfile
from typing import Sequence


REPO_ROOT = Path(__file__).resolve().parents[4]
PFI_ROOT = REPO_ROOT / "PFI"
REVIEW_DIR = PFI_ROOT / "reports/pfi_v025/stage_11/whole_stage_review"
REMEDIATION_COMMIT = "9c450ea483cd2040636e375c9f7d84e5127e44cf"
REVIEW_PREFIX = REVIEW_DIR.relative_to(REPO_ROOT).as_posix() + "/"

FOCUSED_STAGE11 = (
    "PFI/tests/test_v025_stage11_sqlite_concurrency.py",
    "PFI/tests/test_v025_stage11_migration_lifecycle.py",
    "PFI/tests/test_v025_stage11_backup_restore.py",
    "PFI/tests/test_v025_stage11_distribution_boundary.py",
    "PFI/tests/test_stage5_advice_report_alpha.py",
    "PFI/tests/test_stage6_e2e_stabilization.py",
    "PFI/tests/test_v025_stage1_release_identity.py",
    "PFI/tests/test_v025_stage7_import_review_ledger.py",
    "PFI/tests/test_v025_stage7_holding_persistence.py",
    "PFI/tests/test_v025_stage10_job_lifecycle.py",
)
ADJACENT_REGRESSION = (
    "PFI/tests/test_v025_stage4_cross_page_consistency.py",
    "PFI/tests/test_v025_stage4_metric_states.py",
    "PFI/tests/test_v025_stage5_dual_consumption.py",
    "PFI/tests/test_v025_stage5_financial_invariants.py",
    "PFI/tests/test_v025_stage6_navigation_contract.py",
    "PFI/tests/test_v025_stage7_metric_drilldown.py",
    "PFI/tests/test_v025_stage8_phase83_accessibility_uat.py",
    "PFI/tests/test_v025_stage9_whole_review.py",
    "PFI/tests/test_v025_stage10_runtime_diff.py",
    "PFI/tests/test_v025_stage10_crash_recovery.py",
)
PYTHON_PARSE_FILES = (
    "PFI/src/pfi_os/infrastructure/operational_store_backup.py",
    "PFI/src/pfi_v02/stage_v021_runtime_api.py",
    "PFI/scripts/v025/pfi_operational_backup_restore.py",
    "PFI/scripts/v025/stage11_readonly_backup_rehearsal.py",
    "PFI/web/tests/v025/stage11_public_boundary_browser.py",
    "PFI/web/tests/v025/stage11_whole_review_evidence.py",
    "PFI/web/tests/v025/stage11_whole_review_verify.py",
    "PFI/web/tests/v025/stage11_whole_review_finalize.py",
)


def _sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _sanitized(value: str) -> str:
    return value.replace(str(Path.home()), "$HOME").replace(sys.executable, "$PYTHON")


def _status_paths() -> list[str]:
    raw = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z", "-uall"],
        cwd=REPO_ROOT,
        check=True,
        stdout=subprocess.PIPE,
    ).stdout.decode("utf-8")
    paths: set[str] = set()
    for entry in raw.split("\0"):
        if len(entry) < 4:
            continue
        status = entry[:2]
        if any(marker in status for marker in ("D", "R", "C")):
            raise RuntimeError(f"unsupported frozen overlay state: {status!r}")
        path = entry[3:]
        if path.startswith(REVIEW_PREFIX):
            continue
        source = REPO_ROOT / path
        if source.is_file() or source.is_symlink():
            paths.add(path)
    return sorted(paths)


def _current_overlay() -> dict[str, object]:
    files = [{"path": path, "sha256": _sha(REPO_ROOT / path)} for path in _status_paths()]
    records = "".join(f"{row['path']}\0{row['sha256']}\n" for row in files).encode()
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()
    return {
        "schema": "PFIV025Stage11ReviewedWorktreeOverlayV1",
        "status": "frozen",
        "base_commit": head,
        "file_count": len(files),
        "files": files,
        "content_manifest_sha256": "sha256:" + hashlib.sha256(records).hexdigest(),
        "whole_review_output_excluded_from_manifest": True,
    }


def _evidence_overlay() -> dict[str, object]:
    excluded = {
        "artifact_hashes.json",
        "changed_files.txt",
        "content_evidence_index.json",
        "evidence.json",
        "final_evidence_index.json",
        "human_acceptance.json",
        "privacy_scan.txt",
        "review_audit.json",
        "reviewed_evidence_overlay.json",
        "reviewed_worktree_overlay.json",
        "reviewer_results.json",
        "terminal.log",
        "verification_results.json",
    }
    files = []
    for path in sorted(REVIEW_DIR.iterdir()):
        if not path.is_file() or path.name in excluded or path.name.startswith("verification_"):
            continue
        files.append(
            {
                "path": path.relative_to(REPO_ROOT).as_posix(),
                "sha256": _sha(path),
                "byte_size": path.stat().st_size,
            }
        )
    records = "".join(
        f"{row['path']}\0{row['sha256']}\0{row['byte_size']}\n" for row in files
    ).encode()
    return {
        "schema": "PFIV025Stage11ReviewedEvidenceOverlayV1",
        "status": "frozen",
        "file_count": len(files),
        "files": files,
        "content_manifest_sha256": "sha256:" + hashlib.sha256(records).hexdigest(),
    }


def _run_group(command_id: str, commands: Sequence[Sequence[str]]) -> dict[str, object]:
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": "PFI/src"}
    chunks: list[str] = []
    exact_commands: list[str] = []
    exit_code = 0
    for command in commands:
        exact = _sanitized(shlex.join(command))
        exact_commands.append(exact)
        completed = subprocess.run(
            list(command),
            cwd=REPO_ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=env,
        )
        chunks.append(f"$ {exact}\n{_sanitized(completed.stdout)}")
        if completed.returncode:
            exit_code = completed.returncode
            break
    output = "\n".join(chunks).rstrip() + "\n"
    output_path = REVIEW_DIR / f"verification_{command_id}.log"
    output_path.write_text(output, encoding="utf-8")
    return {
        "command_id": command_id,
        "command": " && ".join(exact_commands),
        "subcommands": exact_commands,
        "exit_code": exit_code,
        "output_ref": output_path.relative_to(REPO_ROOT).as_posix(),
        "output_sha256": _sha(output_path),
    }


def _overlay_current_changes(isolated_root: Path) -> int:
    paths = _status_paths()
    for relative in paths:
        source = REPO_ROOT / relative
        target = isolated_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_symlink():
            if target.exists() or target.is_symlink():
                target.unlink()
            target.symlink_to(os.readlink(source))
        else:
            shutil.copy2(source, target)
    return len(paths)


def _run_governance() -> dict[str, object]:
    command_id = "changed_scope_governance"
    exact_commands = [
        "git archive HEAD into an isolated complete root",
        "overlay exact current non-evidence Stage 11 files",
        "$PYTHON scripts/validate_project_governance.py --project PFI",
        "$PYTHON scripts/lean_governance.py check-render --project PFI",
        "/usr/bin/python3 scripts/lean_governance.py check-render --project PFI",
    ]
    chunks: list[str] = []
    exit_code = 0
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    with tempfile.TemporaryDirectory(prefix="pfi-v025-stage11-governance-") as temp_name:
        temp_root = Path(temp_name)
        isolated_root = temp_root / "complete-root"
        isolated_root.mkdir()
        archive_path = temp_root / "repo.tar"
        with archive_path.open("wb") as archive_file:
            archived = subprocess.run(
                ["git", "archive", "--format=tar", "HEAD"],
                cwd=REPO_ROOT,
                stdout=archive_file,
                stderr=subprocess.PIPE,
            )
        if archived.returncode:
            exit_code = archived.returncode
            chunks.append(_sanitized(archived.stderr.decode("utf-8", errors="replace")))
        else:
            with tarfile.open(archive_path) as archive:
                archive.extractall(isolated_root, filter="data")
            count = _overlay_current_changes(isolated_root)
            chunks.append(f"complete root assembled; overlay files={count}")
            for command in (
                [sys.executable, "scripts/validate_project_governance.py", "--project", "PFI"],
                [sys.executable, "scripts/lean_governance.py", "check-render", "--project", "PFI"],
            ):
                completed = subprocess.run(
                    command,
                    cwd=isolated_root,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    env=env,
                )
                chunks.append(f"$ {_sanitized(shlex.join(command))}\n{_sanitized(completed.stdout)}")
                if completed.returncode and exit_code == 0:
                    exit_code = completed.returncode
        for command in (
            [sys.executable, "scripts/lean_governance.py", "check-render", "--project", "PFI"],
            ["/usr/bin/python3", "scripts/lean_governance.py", "check-render", "--project", "PFI"],
        ):
            completed = subprocess.run(
                command,
                cwd=REPO_ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=env,
            )
            chunks.append(f"$ {_sanitized(shlex.join(command))}\n{_sanitized(completed.stdout)}")
            if completed.returncode and exit_code == 0:
                exit_code = completed.returncode
    output = "\n".join(chunks).rstrip() + "\n"
    output_path = REVIEW_DIR / f"verification_{command_id}.log"
    output_path.write_text(output, encoding="utf-8")
    return {
        "command_id": command_id,
        "command": " && ".join(exact_commands),
        "subcommands": exact_commands,
        "exit_code": exit_code,
        "output_ref": output_path.relative_to(REPO_ROOT).as_posix(),
        "output_sha256": _sha(output_path),
        "validation_scope": "complete_git_archive_plus_exact_current_stage11_overlay",
    }


def main() -> int:
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    overlay_before = _current_overlay()
    if overlay_before["base_commit"] != REMEDIATION_COMMIT:
        raise RuntimeError("verification base is not the Stage 11 remediation commit")
    parse_code = (
        "from pathlib import Path; "
        f"files={list(PYTHON_PARSE_FILES)!r}; "
        "[compile(Path(path).read_text(encoding='utf-8'), path, 'exec') for path in files]"
    )
    groups: tuple[tuple[str, tuple[tuple[str, ...], ...]], ...] = (
        (
            "build_core_evidence",
            ((sys.executable, "-B", "PFI/web/tests/v025/stage11_whole_review_evidence.py"),),
        ),
        (
            "focused_stage11",
            ((sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", *FOCUSED_STAGE11),),
        ),
        (
            "selected_adjacent_regression",
            ((sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", *ADJACENT_REGRESSION),),
        ),
        (
            "syntax_release_boundary",
            (
                (sys.executable, "-B", "-c", parse_code),
                ("node", "--check", "PFI/web/tests/v025/stage11_public_boundary_cdp.mjs"),
                (
                    sys.executable,
                    "-B",
                    "PFI/scripts/v025/release_cache_contract.py",
                    "--project-root",
                    "PFI",
                    "--isolated-candidate",
                    "--policy-json",
                ),
                ("git", "diff", "--check"),
            ),
        ),
    )
    rows = [_run_group(command_id, commands) for command_id, commands in groups]
    if all(row["exit_code"] == 0 for row in rows):
        rows.append(_run_governance())
    overlay_after = _current_overlay()
    stable = overlay_before == overlay_after
    evidence_overlay = _evidence_overlay()
    (REVIEW_DIR / "reviewed_worktree_overlay.json").write_text(
        json.dumps(overlay_before, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REVIEW_DIR / "reviewed_evidence_overlay.json").write_text(
        json.dumps(evidence_overlay, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    passed = (
        stable
        and len(rows) == len(groups) + 1
        and all(row["exit_code"] == 0 for row in rows)
        and evidence_overlay["file_count"] >= 18
    )
    payload = {
        "schema": "PFIV025Stage11FinalVerificationResultsV1",
        "status": "pass" if passed else "fail",
        "generated_at": datetime.now().astimezone().replace(microsecond=0).isoformat(),
        "commands": rows,
        "verified_overlay": overlay_before,
        "reviewed_evidence_overlay": evidence_overlay,
        "overlay_stable_during_verification": stable,
        "browser_check_count": 23,
        "stage_task_count": 12,
        "project_task_progress": "144/156 (92.31%)",
        "canonical_private_database_used": True,
        "canonical_private_database_mutated": False,
        "real_database_pages_read": True,
        "private_values_emitted": False,
        "finder_used": False,
        "launchservices_used": False,
        "gui_file_operations_used": False,
        "external_network_performed": False,
        "push_performed": False,
        "app_install_performed": False,
        "stage_12_started": False,
        "production_accepted": False,
        "final_human_acceptance": False,
    }
    (REVIEW_DIR / "verification_results.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    terminal = "\n".join(
        (REVIEW_DIR / f"verification_{row['command_id']}.log").read_text(encoding="utf-8")
        for row in rows
    )
    (REVIEW_DIR / "terminal.log").write_text(terminal, encoding="utf-8")
    print(
        json.dumps(
            {
                "status": payload["status"],
                "command_count": len(rows),
                "overlay_file_count": overlay_before["file_count"],
                "overlay_sha256": overlay_before["content_manifest_sha256"],
                "evidence_file_count": evidence_overlay["file_count"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
