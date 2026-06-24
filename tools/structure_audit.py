#!/usr/bin/env python3
"""Generate bounded structure evidence for selected tracked projects."""

from __future__ import annotations

import argparse
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


TASK_ID = "S4PAT01"
ACCEPTANCE_ID = "ACC-S4PAT01"
DEFAULT_OUTPUT_DIR = Path("governance/stage_gates/s4pa")
ALLOWED_CATEGORIES = ["KEEP", "MERGE", "ARCHIVE", "GENERATED", "PRIVATE", "DELETE_CANDIDATE"]
TEXT_SUFFIXES = {
    ".cfg",
    ".csv",
    ".css",
    ".env",
    ".example",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".jsonl",
    ".jsx",
    ".lock",
    ".md",
    ".py",
    ".sh",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}
TEXT_FILENAMES = {
    ".gitignore",
    "AGENTS.md",
    "CHANGELOG.md",
    "Dockerfile",
    "HANDOFF.md",
    "Procfile",
    "README.md",
    "VERSION",
    "功能清单",
    "开发记录",
    "模型参数文件",
}
ROOT_KEEP = {
    ".env.example",
    ".gitignore",
    "AGENTS.md",
    "CHANGELOG.md",
    "Procfile",
    "README.md",
    "VERSION",
    "pyproject.toml",
    "requirements.txt",
    "package.json",
    "package-lock.json",
    "docker-compose.yml",
    "功能清单",
    "开发记录",
    "模型参数文件",
}


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


def tracked_files(repo: Path, project: str) -> list[str]:
    output = run_git(repo, ["ls-files", "--", project])
    return [line.strip() for line in output.splitlines() if line.strip()]


def classify(project: str, repo_path: str) -> dict[str, str]:
    rel = repo_path[len(project) + 1 :] if repo_path.startswith(project + "/") else repo_path
    parts = rel.split("/")
    name = parts[-1]
    top = parts[0]

    if len(parts) == 1 and name in ROOT_KEEP:
        return {
            "category": "KEEP",
            "owner": "project_owner",
            "reason": "root owner entry, runtime entry, or project identity file retained in place",
        }
    if len(parts) == 1 and name.endswith(".md"):
        return {
            "category": "MERGE",
            "owner": "project_owner",
            "reason": "root markdown noise candidate; merge into canonical docs before any movement",
        }
    if top == "docs" and len(parts) > 1 and parts[1] == "governance":
        return {
            "category": "KEEP",
            "owner": "governance_owner",
            "reason": "active governance truth retained; no structure move in S4PAT01",
        }
    if top in {"backend", "frontend", "src", "app", "scripts", "systems", "tests", "config", "configs"}:
        return {
            "category": "KEEP",
            "owner": "runtime_owner",
            "reason": "source, config, script, or test path required for existing execution/import behavior",
        }
    if top in {".github", ".codex"}:
        return {
            "category": "KEEP",
            "owner": "automation_owner",
            "reason": "automation or CI entry retained in place",
        }
    if top in {"outputs", "reports", "backups", "cleanup", "handoff_packs"}:
        return {
            "category": "ARCHIVE",
            "owner": "project_owner",
            "reason": "tracked historical output or handoff artifact; archive only after S4PAT02 checksum manifest",
        }
    if top in {"assets", "app_bundle"} or name.endswith((".png", ".icns", ".ico", ".pdf", ".zip", ".gz", ".b64")):
        return {
            "category": "GENERATED",
            "owner": "asset_owner",
            "reason": "binary/generated asset retained until reference graph and rollback manifest are bound",
        }
    if top == "data":
        return {
            "category": "PRIVATE",
            "owner": "data_owner",
            "reason": "tracked data path requires owner/privacy review before merge or archive decisions",
        }
    if top in {"samples", "work"}:
        return {
            "category": "ARCHIVE",
            "owner": "project_owner",
            "reason": "sample/work artifact candidate; keep original path until archive manifest exists",
        }
    return {
        "category": "KEEP",
        "owner": "project_owner",
        "reason": "conservative default because use is not proven removable",
    }


def is_text_candidate(path: Path) -> bool:
    if path.name in TEXT_FILENAMES:
        return True
    return path.suffix.lower() in TEXT_SUFFIXES


def read_text_if_small(path: Path, max_bytes: int) -> str | None:
    try:
        if path.stat().st_size > max_bytes:
            return None
        raw = path.read_bytes()
    except OSError:
        return None
    if b"\x00" in raw:
        return None
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("utf-8", errors="ignore")


def existing_metadata(output_dir: Path) -> dict[str, str]:
    path = output_dir / "wave1_structure_map.json"
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


def build_evidence(repo: Path, projects: list[str], output_dir: Path, max_text_bytes: int) -> tuple[dict, dict, str]:
    metadata = existing_metadata(output_dir)
    generated_at = metadata.get("generated_at") or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    source_commit = metadata.get("source_commit") or run_git(repo, ["rev-parse", "HEAD"]).strip()
    project_entries = []
    graph_nodes = []
    graph_edges = []

    for project in projects:
        files = tracked_files(repo, project)
        classified = []
        category_counts: Counter[str] = Counter()
        root_baseline = []
        text_sources: dict[str, str] = {}

        for repo_path in files:
            rel = repo_path[len(project) + 1 :] if repo_path.startswith(project + "/") else repo_path
            info = classify(project, repo_path)
            category_counts[info["category"]] += 1
            item = {
                "path": repo_path,
                "project_relative_path": rel,
                "category": info["category"],
                "owner": info["owner"],
                "reason": info["reason"],
                "root_level": "/" not in rel,
            }
            classified.append(item)
            graph_nodes.append(
                {
                    "id": repo_path,
                    "project_id": project,
                    "category": info["category"],
                    "root_level": item["root_level"],
                }
            )
            if item["root_level"]:
                root_baseline.append(item)
            abs_path = repo / repo_path
            if is_text_candidate(abs_path):
                text = read_text_if_small(abs_path, max_text_bytes)
                if text:
                    text_sources[repo_path] = text

        targets = []
        for item in classified:
            target_strings = [item["path"]]
            if "/" in item["project_relative_path"]:
                target_strings.append(item["project_relative_path"])
            elif item["project_relative_path"] not in {project, ""}:
                target_strings.append(item["project_relative_path"])
            targets.append((item["path"], tuple(dict.fromkeys(target_strings))))

        for source_path, text in text_sources.items():
            for target_path, needles in targets:
                if source_path == target_path:
                    continue
                if any(needle and needle in text for needle in needles):
                    graph_edges.append(
                        {
                            "source": source_path,
                            "target": target_path,
                            "relation": "textual_reference",
                            "confidence": "STATIC_EXACT_PATH_OR_NAME",
                        }
                    )

        project_entries.append(
            {
                "project_id": project,
                "tracked_file_count": len(files),
                "category_counts": {category: category_counts.get(category, 0) for category in ALLOWED_CATEGORIES},
                "root_noise_baseline": {
                    "root_file_count": len(root_baseline),
                    "items": root_baseline,
                },
                "tracked_files": classified,
            }
        )

    structure_map = {
        "schema_version": "codexproject.structure_audit.v1",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": generated_at,
        "source_commit": source_commit,
        "projects": projects,
        "classification_policy": {
            "allowed_categories": ALLOWED_CATEGORIES,
            "delete_policy": "S4PAT01 records DELETE_CANDIDATE capacity but emits no deletion action.",
            "dynamic_reference_limit": "Static textual scan cannot prove dynamic imports, shell expansion, runtime generated paths, or external references.",
        },
        "project_maps": project_entries,
        "stop_conditions": {
            "unknown_file_marked_delete": False,
            "archive_location_runtime_written": False,
            "project_files_moved": False,
        },
    }
    reference_graph = {
        "schema_version": "codexproject.reference_graph.v1",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": generated_at,
        "source_commit": source_commit,
        "projects": projects,
        "node_count": len(graph_nodes),
        "edge_count": len(graph_edges),
        "nodes": graph_nodes,
        "edges": sorted(graph_edges, key=lambda edge: (edge["source"], edge["target"])),
        "limitations": [
            "Only tracked files under selected projects are scanned.",
            "Only text files at or below max_text_bytes are scanned for exact textual references.",
            "Dynamic imports, subprocess paths, glob expansion, runtime writes, and external references require follow-up in S4PAT02/S4PB/S4PC.",
        ],
    }
    archive_plan = render_archive_plan(project_entries, reference_graph)
    return structure_map, reference_graph, archive_plan


def render_archive_plan(project_entries: list[dict], reference_graph: dict) -> str:
    lines = [
        "# Other8 S4PAT01 Wave 1 Archive Plan Draft",
        "",
        f"task_id: {TASK_ID}",
        f"acceptance_id: {ACCEPTANCE_ID}",
        "mode: STRUCTURE_BASELINE_ONLY",
        "",
        "## Decision",
        "",
        "S4PAT01 does not move, archive, delete, or rewrite project files. It records a Wave 1 tracked-file map, root noise baseline, and static reference graph so S4PAT02 can bind checksums and rollback steps before any physical structure migration.",
        "",
        "## Stop Conditions",
        "",
        "- Unknown file marked DELETE_CANDIDATE: false",
        "- Archive location still written by runtime code: false, because no archive location is activated in S4PAT01",
        "- Runtime/import entry moved: false",
        "",
        "## Project Baseline",
        "",
    ]
    for project in project_entries:
        counts = ", ".join(f"{key}={value}" for key, value in project["category_counts"].items())
        noisy = [
            item["project_relative_path"]
            for item in project["root_noise_baseline"]["items"]
            if item["category"] in {"MERGE", "ARCHIVE", "GENERATED", "PRIVATE", "DELETE_CANDIDATE"}
        ]
        lines.extend(
            [
                f"### {project['project_id']}",
                "",
                f"- tracked_file_count: {project['tracked_file_count']}",
                f"- root_file_count: {project['root_noise_baseline']['root_file_count']}",
                f"- category_counts: {counts}",
                f"- root_noise_candidates: {', '.join(noisy) if noisy else 'none'}",
                "",
            ]
        )
    lines.extend(
        [
            "## Reference Graph",
            "",
            f"- node_count: {reference_graph['node_count']}",
            f"- edge_count: {reference_graph['edge_count']}",
            "- limitation: static textual references only; dynamic references remain a follow-up risk.",
            "",
            "## Rollback",
            "",
            "Rollback for S4PAT01 is to remove this baseline evidence and keep all original project paths untouched. Any later archive or merge action must be bound by S4PAT02 checksum manifest and an explicit old-to-new map.",
            "",
            "## Next Task",
            "",
            "S4PAT02 may generate the Wave 1 archive manifest, checksums, and rollback list. S4PAT01 itself is not permission to relocate files.",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(output_dir: Path, structure_map: dict, reference_graph: dict, archive_plan: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "wave1_structure_map.json").write_text(
        machine_json(structure_map),
        encoding="utf-8",
    )
    (output_dir / "reference_graph.json").write_text(
        machine_json(reference_graph),
        encoding="utf-8",
    )
    (output_dir / "archive_plan.md").write_text(archive_plan, encoding="utf-8")


def machine_json(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--projects", nargs="+")
    parser.add_argument("--wave", choices=["1"], help="Run a completed-wave gate verifier.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--max-text-bytes", type=int, default=512_000)
    parser.add_argument("--check", action="store_true", help="Fail if generated outputs differ from disk.")
    args = parser.parse_args()

    repo = repo_root()
    if args.wave == "1":
        import wave1_gate

        gate_args = ["--check"] if args.check else []
        return wave1_gate.main(gate_args)
    if not args.projects:
        parser.error("--projects is required unless --wave is used")
    output_dir = repo / args.output_dir
    structure_map, reference_graph, archive_plan = build_evidence(repo, args.projects, output_dir, args.max_text_bytes)
    expected = {
        output_dir / "wave1_structure_map.json": machine_json(structure_map),
        output_dir / "reference_graph.json": machine_json(reference_graph),
        output_dir / "archive_plan.md": archive_plan,
    }
    if args.check:
        mismatched = [str(path.relative_to(repo)) for path, content in expected.items() if not path.exists() or path.read_text(encoding="utf-8") != content]
        if mismatched:
            print(json.dumps({"result": "FAIL", "mismatched": mismatched}, ensure_ascii=False, sort_keys=True))
            return 1
    else:
        write_outputs(output_dir, structure_map, reference_graph, archive_plan)
    print(
        json.dumps(
            {
                "result": "PASS",
                "task_id": TASK_ID,
                "acceptance_id": ACCEPTANCE_ID,
                "projects": args.projects,
                "output_dir": str(output_dir.relative_to(repo)),
                "node_count": reference_graph["node_count"],
                "edge_count": reference_graph["edge_count"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
