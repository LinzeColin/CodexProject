#!/usr/bin/env python3
"""Run and content-bind PFI v0.2.5 Stage 8 final verification."""

from __future__ import annotations

from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import shlex
import subprocess
import sys
import tarfile
import tempfile
from typing import Sequence


REPO_ROOT = Path(__file__).resolve().parents[4]
PFI_ROOT = REPO_ROOT / "PFI"
REVIEW_DIR = PFI_ROOT / "reports/pfi_v025/stage_8/whole_stage_review"
REVIEW_BASE = "2c7b25efd2916c909027333283b499a119d088e0"

PYTHON_SYNTAX = (
    "import ast,pathlib; "
    "paths=("
    "'PFI/web/tests/v025/stage8_whole_review_evidence.py',"
    "'PFI/web/tests/v025/stage8_whole_review_verify.py',"
    "'PFI/web/tests/v025/stage8_whole_review_finalize.py'"
    "); "
    "[ast.parse(pathlib.Path(p).read_text(encoding='utf-8'), filename=p) for p in paths]"
)

GROUPS: tuple[tuple[str, tuple[tuple[str, ...], ...]], ...] = (
    (
        "focused_stage8",
        ((
            sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
            "PFI/tests/test_v025_stage8_phase81_design_system.py",
            "PFI/tests/test_v025_stage8_phase82_motion_feedback.py",
            "PFI/tests/test_v025_stage8_phase83_accessibility_uat.py",
            "PFI/tests/test_v025_stage8_whole_review.py",
            "PFI/tests/test_v025_stage1_release_identity.py",
        ),),
    ),
    (
        "syntax_and_diff",
        (
            (sys.executable, "-c", PYTHON_SYNTAX),
            ("node", "--check", "PFI/web/app/shell.js"),
            ("node", "--check", "PFI/web/app/components/jobTimeline.js"),
            ("node", "--check", "PFI/web/tests/v025/stage8_phase81_cdp.mjs"),
            ("node", "--check", "PFI/web/tests/v025/stage8_phase82_cdp.mjs"),
            ("node", "--check", "PFI/web/tests/v025/stage8_phase83_cdp.mjs"),
            ("git", "diff", "--check"),
        ),
    ),
)


def _sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _sanitized(value: str) -> str:
    return value.replace(str(Path.home()), "$HOME").replace(sys.executable, "$PYTHON")


def _current_overlay() -> dict[str, object]:
    raw = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z", "-uall"],
        cwd=REPO_ROOT, check=True, stdout=subprocess.PIPE,
    ).stdout.decode("utf-8")
    review_prefix = REVIEW_DIR.relative_to(REPO_ROOT).as_posix() + "/"
    paths: set[str] = set()
    for entry in raw.split("\0"):
        if len(entry) < 4:
            continue
        status = entry[:2]
        if any(marker in status for marker in ("D", "R", "C")):
            raise RuntimeError(f"unsupported overlay state: {status!r}")
        path = entry[3:]
        if path.startswith(review_prefix):
            continue
        if (REPO_ROOT / path).is_file():
            paths.add(path)
    files = [
        {"path": path, "sha256": _sha(REPO_ROOT / path)}
        for path in sorted(paths)
    ]
    records = "".join(
        f"{row['path']}\0{row['sha256']}\n" for row in files
    ).encode("utf-8")
    return {
        "base_commit": subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT,
            check=True, text=True, capture_output=True,
        ).stdout.strip(),
        "file_count": len(files),
        "files": files,
        "content_manifest_sha256": "sha256:" + hashlib.sha256(records).hexdigest(),
    }


def _run_group(command_id: str, commands: Sequence[Sequence[str]]) -> dict[str, object]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPATH"] = "PFI/src"
    chunks: list[str] = []
    exact_commands: list[str] = []
    exit_code = 0
    for command in commands:
        exact = _sanitized(shlex.join(command))
        exact_commands.append(exact)
        completed = subprocess.run(
            list(command), cwd=REPO_ROOT, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env,
        )
        chunks.append(f"$ {exact}\n{_sanitized(completed.stdout)}")
        if completed.returncode != 0:
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


def _overlay_current_pfi(isolated_root: Path) -> int:
    raw = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z", "-uall", "--", "PFI"],
        cwd=REPO_ROOT, check=True, stdout=subprocess.PIPE,
    ).stdout.decode("utf-8")
    review_prefix = REVIEW_DIR.relative_to(REPO_ROOT).as_posix() + "/"
    paths: set[str] = set()
    for record in raw.split("\0"):
        if len(record) < 4:
            continue
        status = record[:2]
        if any(marker in status for marker in ("D", "R", "C")):
            raise RuntimeError(f"unsupported isolated-overlay state: {status!r}")
        path = record[3:]
        if not path.startswith(review_prefix):
            paths.add(path)
    for relative in sorted(paths):
        source = REPO_ROOT / relative
        target = isolated_root / relative
        if source.is_symlink():
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists() or target.is_symlink():
                target.unlink()
            target.symlink_to(os.readlink(source))
        elif source.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        elif target.is_file() or target.is_symlink():
            target.unlink()
    return len(paths)


def _run_changed_scope_governance() -> dict[str, object]:
    command_id = "changed_scope_governance"
    exact_commands = [
        "git archive --format=tar HEAD -> $ISOLATED_COMPLETE_ROOT",
        "overlay current PFI source changes -> $ISOLATED_COMPLETE_ROOT/PFI",
        "$PYTHON scripts/validate_project_governance.py --project PFI (cwd=$ISOLATED_COMPLETE_ROOT)",
        "$PYTHON scripts/lean_governance.py check-render --project PFI",
    ]
    chunks: list[str] = []
    exit_code = 0
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    temp_parent = "/private/tmp" if Path("/private/tmp").is_dir() else None
    with tempfile.TemporaryDirectory(
        prefix="pfi-v025-stage8-governance-", dir=temp_parent,
    ) as temp_name:
        temp_root = Path(temp_name)
        isolated_root = temp_root / "complete-root"
        isolated_root.mkdir()
        archive_path = temp_root / "repo.tar"
        with archive_path.open("wb") as archive_file:
            archived = subprocess.run(
                ["git", "archive", "--format=tar", "HEAD"],
                cwd=REPO_ROOT, stdout=archive_file, stderr=subprocess.PIPE,
            )
        if archived.returncode != 0:
            exit_code = archived.returncode
            chunks.append(f"$ {exact_commands[0]}\n{_sanitized(archived.stderr.decode('utf-8'))}")
        else:
            with tarfile.open(archive_path) as archive:
                archive.extractall(isolated_root, filter="data")
            overlay_count = _overlay_current_pfi(isolated_root)
            chunks.append(
                f"$ {exact_commands[0]}\ncomplete root assembled\n"
                f"$ {exact_commands[1]}\noverlay files={overlay_count}\n"
            )
            completed = subprocess.run(
                [sys.executable, "scripts/validate_project_governance.py", "--project", "PFI"],
                cwd=isolated_root, text=True,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env,
            )
            chunks.append(f"$ {exact_commands[2]}\n{_sanitized(completed.stdout)}")
            if completed.returncode != 0 and exit_code == 0:
                exit_code = completed.returncode
        rendered = subprocess.run(
            [sys.executable, "scripts/lean_governance.py", "check-render", "--project", "PFI"],
            cwd=REPO_ROOT, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, env=env,
        )
        chunks.append(f"$ {exact_commands[3]}\n{_sanitized(rendered.stdout)}")
        if rendered.returncode != 0 and exit_code == 0:
            exit_code = rendered.returncode
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
        "validation_scope": "complete_git_archive_root_plus_current_pfi_source_overlay",
    }


def main() -> int:
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    overlay_before = _current_overlay()
    if overlay_before["base_commit"] != REVIEW_BASE:
        raise RuntimeError("verification base is not the Stage 8 remediation commit")
    rows = [_run_group(command_id, commands) for command_id, commands in GROUPS]
    rows.append(_run_changed_scope_governance())
    overlay_after = _current_overlay()
    stable = overlay_before == overlay_after
    passed = stable and all(row["exit_code"] == 0 for row in rows)
    payload = {
        "schema": "PFIV025Stage8FinalVerificationResultsV1",
        "status": "pass" if passed else "fail",
        "generated_at": datetime.now().astimezone().replace(microsecond=0).isoformat(),
        "commands": rows,
        "verified_overlay": overlay_before,
        "overlay_stable_during_verification": stable,
        "browser_evidence_precondition": "current-content headless Chrome evidence already generated under whole_stage_review",
        "financial_data_loaded": False,
        "database_changed": False,
        "contains_private_values": False,
        "finder_used": False,
        "launchservices_used": False,
        "external_network_performed": False,
        "push_performed": False,
        "app_install_performed": False,
    }
    (REVIEW_DIR / "verification_results.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": payload["status"],
        "command_count": len(rows),
        "overlay_file_count": overlay_before["file_count"],
        "overlay_sha256": overlay_before["content_manifest_sha256"],
    }, ensure_ascii=False))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
