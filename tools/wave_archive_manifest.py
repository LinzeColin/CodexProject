#!/usr/bin/env python3
"""Generate and verify Wave 1 archive manifest evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


TASK_ID = "S4PAT02"
ACCEPTANCE_ID = "ACC-S4PAT02"
DEFAULT_STRUCTURE_MAP = Path("governance/stage_gates/s4pa/wave1_structure_map.json")
DEFAULT_OUTPUT_DIR = Path("governance/stage_gates/s4pa")
ARCHIVE_ROOT = "governance/archive/other8_wave1_pending"
CANDIDATE_CATEGORIES = {"MERGE", "ARCHIVE", "GENERATED", "PRIVATE", "DELETE_CANDIDATE"}


def run_git(repo: Path, args: list[str]) -> str:
    return subprocess.check_output(
        ["git", "-c", "core.quotePath=false", *args],
        cwd=repo,
        encoding="utf-8",
        errors="replace",
        text=True,
    )


def repo_root() -> Path:
    return Path(run_git(Path.cwd(), ["rev-parse", "--show-toplevel"]).strip())


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def machine_json(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n"


def existing_metadata(output_dir: Path) -> dict[str, str]:
    path = output_dir / "wave1_archive_manifest.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return {
        "generated_at": str(data.get("generated_at") or ""),
        "source_commit": str(data.get("source_commit") or ""),
    }


def action_for(category: str) -> str:
    if category == "MERGE":
        return "MERGE_AFTER_PROJECT_TASK"
    if category == "PRIVATE":
        return "OWNER_REVIEW_BEFORE_ARCHIVE"
    if category == "DELETE_CANDIDATE":
        return "BLOCKED_UNTIL_OWNER_APPROVAL"
    return "ARCHIVE_AFTER_CHECKSUM_AND_ROLLBACK_BINDING"


def proposed_target(source_path: str) -> str:
    return f"{ARCHIVE_ROOT}/{source_path}"


def build_manifest(repo: Path, structure_map_path: Path, output_dir: Path) -> tuple[dict, str, str]:
    structure_map = json.loads(structure_map_path.read_text(encoding="utf-8"))
    metadata = existing_metadata(output_dir)
    generated_at = metadata.get("generated_at") or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    source_commit = metadata.get("source_commit") or run_git(repo, ["rev-parse", "HEAD"]).strip()
    candidates = []
    category_counts: Counter[str] = Counter()
    project_counts: Counter[str] = Counter()

    for project in structure_map["project_maps"]:
        project_id = project["project_id"]
        for item in project["tracked_files"]:
            category = item["category"]
            if category not in CANDIDATE_CATEGORIES:
                continue
            source_path = item["path"]
            abs_path = repo / source_path
            checksum = sha256_file(abs_path)
            record = {
                "source_path": source_path,
                "project_id": project_id,
                "category": category,
                "owner": item["owner"],
                "reason": item["reason"],
                "sha256": checksum,
                "size_bytes": abs_path.stat().st_size,
                "proposed_target": proposed_target(source_path),
                "proposed_action": action_for(category),
                "rollback_action": "restore original source_path from git at recorded sha256; no rollback file move is needed before S4PB/S4PC",
                "current_path_must_remain": True,
            }
            candidates.append(record)
            category_counts[category] += 1
            project_counts[project_id] += 1

    candidates.sort(key=lambda item: (item["project_id"], item["category"], item["source_path"]))
    checksum_text = "".join(f"{item['sha256']}  {item['source_path']}\n" for item in candidates)
    manifest = {
        "schema_version": "codexproject.wave_archive_manifest.v1",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": generated_at,
        "source_commit": source_commit,
        "source_structure_map": str(structure_map_path.relative_to(repo)).replace("\\", "/"),
        "archive_root": ARCHIVE_ROOT,
        "mode": "MANIFEST_ONLY_NO_FILE_MOVES",
        "candidate_count": len(candidates),
        "category_counts": {category: category_counts.get(category, 0) for category in sorted(CANDIDATE_CATEGORIES)},
        "project_counts": {project: project_counts.get(project, 0) for project in structure_map["projects"]},
        "stop_conditions": {
            "files_moved": False,
            "archive_written": False,
            "checksum_missing": False,
            "delete_candidate_without_owner_approval": False,
        },
        "candidates": candidates,
        "checksum_file": "governance/stage_gates/s4pa/wave1_archive_manifest.sha256",
        "rollback_plan": "governance/stage_gates/s4pa/rollback_plan.md",
        "limitations": [
            "This manifest binds current tracked files only; untracked local files are outside S4PAT02.",
            "No archive directory is created and no source path is moved in S4PAT02.",
            "PRIVATE candidates require owner review before any future archive or merge action.",
        ],
    }
    rollback_plan = render_rollback_plan(manifest)
    return manifest, checksum_text, rollback_plan


def render_rollback_plan(manifest: dict) -> str:
    lines = [
        "# Other8 S4PAT02 Wave 1 Rollback Plan",
        "",
        f"task_id: {TASK_ID}",
        f"acceptance_id: {ACCEPTANCE_ID}",
        "mode: MANIFEST_ONLY_NO_FILE_MOVES",
        "",
        "## Decision",
        "",
        "S4PAT02 records checksums and rollback metadata only. It does not move files into the archive root and does not delete or rewrite project files.",
        "",
        "## Checksum Gate",
        "",
        "- checksum_file: governance/stage_gates/s4pa/wave1_archive_manifest.sha256",
        f"- candidate_count: {manifest['candidate_count']}",
        "- local verifier: python tools/wave_archive_manifest.py --check",
        "- coreutils verifier when available: sha256sum -c governance/stage_gates/s4pa/wave1_archive_manifest.sha256",
        "",
        "## Rollback Rule",
        "",
        "Because S4PAT02 performs no file movement, rollback is to remove the S4PAT02 manifest/checksum/rollback evidence. Later S4PB/S4PC migrations must use the source_path and sha256 fields in wave1_archive_manifest.json to restore original paths.",
        "",
        "## Project Counts",
        "",
    ]
    for project_id, count in manifest["project_counts"].items():
        lines.append(f"- {project_id}: {count}")
    lines.extend(["", "## Candidate Paths", ""])
    for item in manifest["candidates"]:
        lines.append(
            f"- {item['project_id']} | {item['category']} | {item['source_path']} | sha256={item['sha256']}"
        )
    lines.extend(
        [
            "",
            "## Next Task",
            "",
            "S4PBT01 may start Alpha structure simplification only after this checksum manifest is merged and CI-bound.",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(output_dir: Path, manifest: dict, checksum_text: str, rollback_plan: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "wave1_archive_manifest.json").write_text(machine_json(manifest), encoding="utf-8")
    (output_dir / "wave1_archive_manifest.sha256").write_text(checksum_text, encoding="utf-8")
    (output_dir / "rollback_plan.md").write_text(rollback_plan, encoding="utf-8")


def verify_checksum_text(repo: Path, checksum_text: str) -> list[str]:
    mismatches = []
    for line in checksum_text.splitlines():
        if not line.strip():
            continue
        expected, source_path = line.split("  ", 1)
        observed = sha256_file(repo / source_path)
        if observed != expected:
            mismatches.append(source_path)
    return mismatches


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--structure-map", default=str(DEFAULT_STRUCTURE_MAP))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--check", action="store_true", help="Fail if generated outputs differ or checksums do not match.")
    args = parser.parse_args()

    repo = repo_root()
    structure_map_path = repo / args.structure_map
    output_dir = repo / args.output_dir
    manifest, checksum_text, rollback_plan = build_manifest(repo, structure_map_path, output_dir)
    expected = {
        output_dir / "wave1_archive_manifest.json": machine_json(manifest),
        output_dir / "wave1_archive_manifest.sha256": checksum_text,
        output_dir / "rollback_plan.md": rollback_plan,
    }
    mismatches = verify_checksum_text(repo, checksum_text)
    if args.check:
        disk_mismatches = [
            str(path.relative_to(repo)).replace("\\", "/")
            for path, content in expected.items()
            if not path.exists() or path.read_text(encoding="utf-8") != content
        ]
        if disk_mismatches or mismatches:
            print(
                json.dumps(
                    {
                        "result": "FAIL",
                        "disk_mismatches": disk_mismatches,
                        "checksum_mismatches": mismatches,
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                )
            )
            return 1
    else:
        write_outputs(output_dir, manifest, checksum_text, rollback_plan)
    print(
        json.dumps(
            {
                "result": "PASS",
                "task_id": TASK_ID,
                "acceptance_id": ACCEPTANCE_ID,
                "candidate_count": manifest["candidate_count"],
                "checksum_count": len(checksum_text.splitlines()),
                "output_dir": str(output_dir.relative_to(repo)).replace("\\", "/"),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
