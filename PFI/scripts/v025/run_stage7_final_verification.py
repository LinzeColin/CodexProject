#!/usr/bin/env python3
"""Run and content-bind Stage 7 final verification without synthesizing results."""

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


REPO_ROOT = Path(__file__).resolve().parents[3]
PFI_ROOT = REPO_ROOT / "PFI"
REPORT_DIR = PFI_ROOT / "reports/pfi_v025/stage_7/whole_stage_review"


GROUPS: tuple[tuple[str, tuple[tuple[str, ...], ...]], ...] = (
    (
        "focused_stage7",
        ((
            sys.executable, "-m", "pytest", "-q",
            "PFI/tests/test_stage2_alipay_import.py",
            "PFI/tests/test_v025_stage7_import_review_ledger.py",
            "PFI/tests/test_v025_stage7_metric_drilldown.py",
            "PFI/tests/test_v025_stage7_holding_persistence.py",
            "PFI/tests/test_v025_stage1_release_identity.py",
            "PFI/tests/test_v025_stage1_whole_review_remediation.py",
        ),),
    ),
    (
        "syntax_and_diff",
        (
            (
                sys.executable, "-m", "py_compile",
                "PFI/src/pfi_os/application/use_cases/import_review_ledger.py",
                "PFI/src/pfi_os/application/use_cases/metric_lineage_drilldown.py",
                "PFI/src/pfi_os/infrastructure/operational_import_store.py",
                "PFI/src/pfi_os/infrastructure/operational_holding_settings_store.py",
                "PFI/src/pfi_os/app/streamlit_app.py",
                "PFI/src/pfi_v02/stage2_import.py",
                "PFI/src/pfi_v02/stage_v021_runtime_api.py",
                "PFI/web/tests/v025/stage7_trace_privacy.py",
                "PFI/web/tests/v025/stage7_whole_review_browser.py",
                "PFI/scripts/v025/build_stage7_whole_review.py",
                "PFI/scripts/v025/run_stage7_final_verification.py",
            ),
            ("node", "--check", "PFI/web/app/shell.js"),
            ("node", "--check", "PFI/web/tests/v025/stage7_metric_drilldown_cdp.mjs"),
            ("git", "diff", "--check"),
        ),
    ),
)


def _sanitized_output(value: str) -> str:
    return value.replace(str(Path.home()), "$HOME")


def _sanitized_command(value: str) -> str:
    return value.replace(sys.executable, "$PYTHON").replace(str(Path.home()), "$HOME")


def _current_overlay() -> dict[str, object]:
    raw = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z", "-uall"],
        cwd=REPO_ROOT, check=True, stdout=subprocess.PIPE,
    ).stdout.decode("utf-8")
    review_prefix = REPORT_DIR.relative_to(REPO_ROOT).as_posix() + "/"
    paths: set[str] = set()
    for entry in raw.split("\0"):
        if len(entry) < 4:
            continue
        status = entry[:2]
        if any(marker in status for marker in ("D", "R", "C")):
            raise RuntimeError(
                f"unsupported delete/rename/copy worktree state in verified overlay: {status!r}"
            )
        path = entry[3:]
        if path.startswith(review_prefix):
            continue
        if (REPO_ROOT / path).is_file():
            paths.add(path)
    files = [
        {
            "path": path,
            "sha256": "sha256:" + hashlib.sha256((REPO_ROOT / path).read_bytes()).hexdigest(),
        }
        for path in sorted(paths)
    ]
    records = "".join(
        f"{item['path']}\0{item['sha256']}\n" for item in files
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
    chunks: list[str] = []
    exit_code = 0
    exact_commands: list[str] = []
    for command in commands:
        exact = shlex.join(command)
        exact_commands.append(_sanitized_command(exact))
        completed = subprocess.run(
            list(command), cwd=REPO_ROOT, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            env=os.environ.copy(),
        )
        chunks.append(f"$ {_sanitized_command(exact)}\n{completed.stdout}")
        if completed.returncode != 0:
            exit_code = completed.returncode
            break
    output = _sanitized_output("\n".join(chunks).rstrip() + "\n")
    output_path = REPORT_DIR / f"verification_{command_id}.log"
    output_path.write_text(output, encoding="utf-8")
    return {
        "command_id": command_id,
        "command": " && ".join(exact_commands),
        "subcommands": exact_commands,
        "exit_code": exit_code,
        "output_ref": output_path.relative_to(REPO_ROOT).as_posix(),
        "output_sha256": "sha256:" + hashlib.sha256(output.encode("utf-8")).hexdigest(),
    }


def _overlay_current_pfi(isolated_root: Path) -> int:
    raw = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z", "-uall", "--", "PFI"],
        cwd=REPO_ROOT, check=True, stdout=subprocess.PIPE,
    ).stdout.decode("utf-8")
    records = raw.split("\0")
    paths: set[str] = set()
    index = 0
    while index < len(records):
        record = records[index]
        index += 1
        if len(record) < 4:
            continue
        status = record[:2]
        path = record[3:]
        paths.add(path)
        if "R" in status or "C" in status:
            if index < len(records) and records[index]:
                old_path = records[index]
                index += 1
                old_target = isolated_root / old_path
                if old_target.is_file() or old_target.is_symlink():
                    old_target.unlink()
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
    chunks: list[str] = []
    exit_code = 0
    exact_commands = [
        "git archive --format=tar HEAD -> $ISOLATED_COMPLETE_ROOT",
        "overlay current PFI tracked/untracked changes -> $ISOLATED_COMPLETE_ROOT/PFI",
        f"{shlex.join((sys.executable, 'scripts/validate_project_governance.py', '--project', 'PFI'))} (cwd=$ISOLATED_COMPLETE_ROOT)",
        shlex.join((sys.executable, "scripts/lean_governance.py", "check-render", "--project", "PFI")),
    ]
    exact_commands = [_sanitized_command(command) for command in exact_commands]
    temp_parent = "/private/tmp" if Path("/private/tmp").is_dir() else None
    with tempfile.TemporaryDirectory(
        prefix="pfi-v025-stage7-governance-", dir=temp_parent,
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
            chunks.append("$ git archive --format=tar HEAD\n" + archived.stderr.decode("utf-8"))
        else:
            with tarfile.open(archive_path) as archive:
                archive.extractall(isolated_root, filter="data")
            overlay_count = _overlay_current_pfi(isolated_root)
            chunks.append(
                "$ git archive --format=tar HEAD -> $ISOLATED_COMPLETE_ROOT\n"
                f"complete root assembled; current PFI overlay files={overlay_count}\n"
            )
            completed = subprocess.run(
                [sys.executable, "scripts/validate_project_governance.py", "--project", "PFI"],
                cwd=isolated_root, text=True,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                env=os.environ.copy(),
            )
            chunks.append(
                f"$ {exact_commands[2]}\n{completed.stdout}"
            )
            if completed.returncode != 0:
                exit_code = completed.returncode
        rendered = subprocess.run(
            [sys.executable, "scripts/lean_governance.py", "check-render", "--project", "PFI"],
            cwd=REPO_ROOT, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            env=os.environ.copy(),
        )
        chunks.append(f"$ {exact_commands[3]}\n{rendered.stdout}")
        if rendered.returncode != 0 and exit_code == 0:
            exit_code = rendered.returncode
    output = _sanitized_output("\n".join(chunks).rstrip() + "\n")
    output_path = REPORT_DIR / f"verification_{command_id}.log"
    output_path.write_text(output, encoding="utf-8")
    return {
        "command_id": command_id,
        "command": " && ".join(exact_commands),
        "subcommands": exact_commands,
        "exit_code": exit_code,
        "output_ref": output_path.relative_to(REPO_ROOT).as_posix(),
        "output_sha256": "sha256:" + hashlib.sha256(output.encode("utf-8")).hexdigest(),
        "validation_scope": "complete_git_archive_root_plus_current_pfi_overlay",
    }


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    overlay_before = _current_overlay()
    rows = [_run_group(command_id, commands) for command_id, commands in GROUPS]
    rows.append(_run_changed_scope_governance())
    overlay_after = _current_overlay()
    overlay_stable = overlay_before == overlay_after
    commands_pass = all(row["exit_code"] == 0 for row in rows)
    payload = {
        "schema": "PFIV025Stage7FinalVerificationResultsV1",
        "status": "pass" if commands_pass and overlay_stable else "fail",
        "generated_at": datetime.now().astimezone().replace(microsecond=0).isoformat(),
        "commands": rows,
        "verified_overlay": overlay_before,
        "overlay_stable_during_verification": overlay_stable,
        "contains_private_values": False,
        "external_network_performed": False,
        "finder_used": False,
    }
    (REPORT_DIR / "verification_results.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": payload["status"], "command_count": len(rows)}, ensure_ascii=False))
    return 0 if payload["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
