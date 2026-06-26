#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


EMAIL_V1_MERGED_STATE = "EMAIL_LEARNING_V1_MERGED_TO_MAIN_NO_PRODUCTION_SIDE_EFFECTS"
CURRENT_STAGE2_TASK = "S2PMT07"
CURRENT_SHADOW_SOURCE_NEXT = "NONE_WHILE_S2PMT07_BLOCKED"
EMAIL_V1_REQUIRED_TASKS = {
    "S2PHT01V1.1-T00",
    "S2PHT01V1.1-T01",
    "S2PHT01V1.1-T02",
    "S2PHT01V1.1-T03",
    "S2PHT01V1.1-T04",
    "S2PHT01V1.1-T05",
}
DEPENDENCY_KEYS = {"dependencies", "depends_on", "required_dependencies"}
TASK_REF_SCALAR_KEYS = {"task_id", "next_task", "global_current_task", "canonical_parent_task", "alias_parent"}
TASK_REF_LIST_KEYS = {"completed_tasks"}


def repo_root_from_v7_2(root: Path) -> Path:
    return root.parents[3]


def load_yaml(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        return yaml.safe_load(text) or {}
    except ModuleNotFoundError:
        repo_root = path.resolve()
        while repo_root != repo_root.parent and not (repo_root / "scripts/validate_project_governance.py").is_file():
            repo_root = repo_root.parent
        if not (repo_root / "scripts/validate_project_governance.py").is_file():
            raise
        scripts_dir = repo_root / "scripts"
        sys.path.insert(0, str(scripts_dir))
        from validate_project_governance import fallback_yaml_load

        return fallback_yaml_load(text) or {}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def count_audit_severities(path: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    for match in re.finditer(r"(?m)^  severity: (P[0-3])$", path.read_text(encoding="utf-8")):
        severity = match.group(1)
        counts[severity] = counts.get(severity, 0) + 1
    return counts


def path_label(parts: tuple[str, ...]) -> str:
    return ".".join(parts) if parts else "<root>"


def walk_dicts(value: Any, path: tuple[str, ...] = ()) -> list[tuple[tuple[str, ...], dict[str, Any]]]:
    nodes: list[tuple[tuple[str, ...], dict[str, Any]]] = []
    if isinstance(value, dict):
        nodes.append((path, value))
        for key, child in value.items():
            nodes.extend(walk_dicts(child, path + (str(key),)))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            nodes.extend(walk_dicts(child, path + (str(index),)))
    return nodes


def collect_registered_stop_codes(root: Path, repo: Path, stop_registry: dict[str, Any]) -> tuple[set[str], list[str]]:
    errors: list[str] = []
    stop_codes = stop_registry.get("stop_codes")
    if not isinstance(stop_codes, dict) or not stop_codes:
        return set(), ["stop_codes_v7_2.yaml must define non-empty stop_codes mapping"]
    codes = {str(code) for code in stop_codes}

    inherited = stop_registry.get("inherits")
    if inherited:
        inherited_path = str(inherited)
        candidates = [
            repo / "arxiv-daily-push" / inherited_path,
            repo / inherited_path,
            root / inherited_path,
        ]
        inherited_file = next((path for path in candidates if path.is_file()), None)
        if inherited_file is None:
            errors.append(f"stop code registry inherits missing file: {inherited_path}")
        else:
            inherited_data = load_yaml(inherited_file)
            inherited_codes = inherited_data.get("stop_codes")
            if not isinstance(inherited_codes, dict) or not inherited_codes:
                errors.append(f"inherited stop code registry has no stop_codes mapping: {inherited_file}")
            else:
                codes.update(str(code) for code in inherited_codes)

    return codes, errors


def validate_roadmap_machine_gate(roadmap: dict[str, Any], registered_stop_codes: set[str]) -> tuple[list[str], dict[str, int]]:
    errors: list[str] = []
    nodes = walk_dicts(roadmap)
    task_defs: dict[str, tuple[str, ...]] = {}
    task_refs: set[str] = set()

    for path, node in nodes:
        for key in TASK_REF_SCALAR_KEYS:
            if key not in node:
                continue
            value = node.get(key)
            if isinstance(value, str) and value.strip():
                if key == "task_id" and value in task_defs:
                    errors.append(f"duplicate task id {value} at {path_label(path)}")
                if key == "task_id":
                    task_defs[value] = path
                task_refs.add(value)
            elif value is not None:
                errors.append(f"{path_label(path)}.{key} must be a non-empty string")

        for key in TASK_REF_LIST_KEYS:
            if key not in node:
                continue
            value = node.get(key)
            if not isinstance(value, list):
                errors.append(f"{path_label(path)}.{key} must be a list")
                continue
            for index, item in enumerate(value):
                if isinstance(item, str) and item.strip():
                    task_refs.add(item)
                else:
                    errors.append(f"{path_label(path)}.{key}.{index} must be a non-empty string")

    dependency_edges: dict[str, list[str]] = {}
    stop_condition_count = 0
    dependency_count = 0
    for path, node in nodes:
        if "stop_conditions" in node:
            value = node.get("stop_conditions")
            if not isinstance(value, list):
                errors.append(f"{path_label(path)}.stop_conditions must be a list of registered stop codes")
            else:
                for index, code in enumerate(value):
                    if not isinstance(code, str) or not code.strip():
                        errors.append(f"{path_label(path)}.stop_conditions.{index} must be a non-empty string")
                        continue
                    stop_condition_count += 1
                    if code not in registered_stop_codes:
                        errors.append(f"unknown stop code {code} at {path_label(path)}.stop_conditions.{index}")

        task_id = node.get("task_id")
        parent_task = task_id if isinstance(task_id, str) and task_id.strip() else None
        for key in DEPENDENCY_KEYS:
            if key not in node:
                continue
            value = node.get(key)
            if not isinstance(value, list):
                errors.append(f"{path_label(path)}.{key} must be a list")
                continue
            for index, dep in enumerate(value):
                if not isinstance(dep, str) or not dep.strip():
                    errors.append(f"{path_label(path)}.{key}.{index} must be a non-empty string")
                    continue
                dependency_count += 1
                if dep not in task_refs:
                    errors.append(f"{path_label(path)}.{key}.{index} references unknown task {dep}")
                if parent_task and dep == parent_task:
                    errors.append(f"{parent_task} cannot depend on itself")
                if parent_task and dep in task_defs:
                    dependency_edges.setdefault(parent_task, []).append(dep)

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(task_id: str, stack: list[str]) -> None:
        if task_id in visiting:
            if task_id in stack:
                start = stack.index(task_id)
                cycle = stack[start:] + [task_id]
            else:
                cycle = stack + [task_id]
            errors.append(f"task dependency graph contains a cycle: {' -> '.join(cycle)}")
            return
        if task_id in visited:
            return
        visiting.add(task_id)
        for dependency in dependency_edges.get(task_id, []):
            visit(dependency, stack + [dependency])
        visiting.remove(task_id)
        visited.add(task_id)

    for task_id in task_defs:
        visit(task_id, [task_id])

    metrics = {
        "registered_stop_code_count": len(registered_stop_codes),
        "roadmap_task_count": len(task_defs),
        "roadmap_task_reference_count": len(task_refs),
        "roadmap_dependency_count": dependency_count,
        "roadmap_stop_condition_count": stop_condition_count,
    }
    return errors, metrics


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    repo = repo_root_from_v7_2(root)
    pursuing = root.parent
    errors: list[str] = []
    warnings: list[str] = []

    required = {
        "current": pursuing / "CURRENT.yaml",
        "lock": root / "V7_2_ROOT_LOCK.yaml",
        "product": root / "machine_readable/product_contract_v7_2.yaml",
        "requirements": root / "machine_readable/requirements_v7_2.yaml",
        "decisions": root / "machine_readable/decision_log_v7_2.yaml",
        "migration": root / "machine_readable/migration_matrix_v7_1_to_v7_2.yaml",
        "roadmap": root / "machine_readable/roadmap_v7_2.yaml",
        "stops": root / "machine_readable/stop_codes_v7_2.yaml",
        "dual_plane": root / "machine_readable/dual_plane_governance_v7_2.yaml",
        "overlay": root / "machine_readable/email_learning_frontstage_overlay_v1.yaml",
        "pointer": root / "machine_readable/current_pointer_registry_v7_2.yaml",
        "review": root / "AUDIT/final_review_matrix.yaml",
        "handoff": root / "HANDOFF/00_下一Agent先读.md",
    }
    for key, path in required.items():
        if not path.is_file():
            errors.append(f"missing {key}: {path}")
    if errors:
        print(json.dumps({"status": "FAIL", "errors": errors, "warnings": warnings}, ensure_ascii=False, indent=2))
        return 2

    data = {key: load_yaml(path) for key, path in required.items() if path.suffix in {".yaml", ".yml"}}
    current = data["current"]
    lock = data["lock"]
    product = data["product"]
    migration = data["migration"]
    decisions = data["decisions"]
    review = data["review"]
    roadmap = data["roadmap"]
    pointer = data["pointer"]
    stops = data["stops"]

    registered_stop_codes, stop_registry_errors = collect_registered_stop_codes(root, repo, stops)
    errors.extend(stop_registry_errors)
    roadmap_machine_gate_errors, roadmap_machine_gate = validate_roadmap_machine_gate(roadmap, registered_stop_codes)
    errors.extend(roadmap_machine_gate_errors)

    if current.get("current_product_contract", {}).get("version") != "ADP-PRODUCT-CONTRACT-V7.2":
        errors.append("CURRENT.yaml does not point to ADP-PRODUCT-CONTRACT-V7.2")
    if current.get("previous_read_only_contract", {}).get("version") != "ADP-PRODUCT-CONTRACT-V7.1":
        errors.append("CURRENT.yaml does not preserve V7.1 as previous read-only contract")
    if not current.get("agent_revalidation_required"):
        errors.append("CURRENT.yaml does not require agent revalidation")

    if lock.get("current_contract", {}).get("contract_version") != "ADP-PRODUCT-CONTRACT-V7.2":
        errors.append("V7_2_ROOT_LOCK current contract mismatch")
    if product.get("contract_version") != "ADP-PRODUCT-CONTRACT-V7.2":
        errors.append("product_contract_v7_2 contract_version mismatch")
    if product.get("parent_contract", {}).get("version") != "ADP-PRODUCT-CONTRACT-V7.1":
        errors.append("product_contract_v7_2 parent version mismatch")
    inherited = product.get("production_stop_gate", {}).get("inherited_v7_1_open_findings", {})
    if inherited.get("P0") != 8 or inherited.get("P1") != 37:
        errors.append("product_contract_v7_2 must preserve inherited V7.1 open P0=8/P1=37")
    baseline = product.get("production_stop_gate", {}).get("v7_2_baseline_migration_open_findings", {})
    if baseline.get("P0") != 0 or baseline.get("P1") != 0:
        errors.append("product_contract_v7_2 V7.2 baseline migration blockers must be P0=0/P1=0")

    expected_v7_1 = {
        repo / "arxiv-daily-push/docs/pursuing_goal/v7_1/machine_readable/product_contract_v7.yaml": "e51f306755629870f5a3693a50191c2291131d2224b91a8f3ef976e272eec7ad",
        repo / "arxiv-daily-push/docs/pursuing_goal/v7_1/ROADMAP/roadmap_v7.yaml": "b3e9860042fcbbf67ef5c49c12d3da30dbf0ae217ff1fe44bd25580a52f7c1a6",
        repo / "arxiv-daily-push/docs/pursuing_goal/v7_1/machine_readable/audit_findings_v7_1.yaml": "f102af13006e5a18de6ad71e6c2e6b9080ba06384dd6d26fd99019a9437dc165",
    }
    for path, expected in expected_v7_1.items():
        actual = sha256(path)
        if actual != expected:
            errors.append(f"V7.1 read-only input hash mismatch: {path} actual={actual} expected={expected}")
    audit_counts = count_audit_severities(repo / "arxiv-daily-push/docs/pursuing_goal/v7_1/machine_readable/audit_findings_v7_1.yaml")
    if audit_counts.get("P0") != 8 or audit_counts.get("P1") != 37:
        errors.append(f"V7.1 inherited audit blocker count mismatch: {audit_counts}")

    lock_hash_fields = {
        "contract_sha256": required["product"],
        "roadmap_sha256": required["roadmap"],
        "migration_matrix_sha256": required["migration"],
        "final_review_sha256": required["review"],
    }
    current_contract = lock.get("current_contract", {})
    for field, path in lock_hash_fields.items():
        expected = current_contract.get(field)
        actual = sha256(path)
        if expected != actual:
            errors.append(f"V7.2 root lock {field} mismatch actual={actual} expected={expected}")
    inherited_lock = lock.get("inherited_v7_1_audit_blockers", {})
    if inherited_lock.get("open_p0_findings") != 8 or inherited_lock.get("open_p1_findings") != 37:
        errors.append("V7_2_ROOT_LOCK must preserve inherited V7.1 open P0=8/P1=37")
    baseline_lock = lock.get("v7_2_baseline_migration_blockers", {})
    if baseline_lock.get("open_p0_findings") != 0 or baseline_lock.get("open_p1_findings") != 0:
        errors.append("V7_2_ROOT_LOCK V7.2 baseline migration blockers must be P0=0/P1=0")

    decision_ids = {item.get("decision_id") for item in decisions.get("decisions", [])}
    for required_decision in {"DEC-EMAIL-V1-FRONTSTAGE", "DEC-ADP-V7-2-CURRENT-20260624", "DEC-ADP-V7-2-AGENT-REVALIDATION"}:
        if required_decision not in decision_ids:
            errors.append(f"missing decision {required_decision}")

    for section in ["v7_1_retained_requirements", "v7_1_replaced_requirements", "v1_1_new_requirements", "file_migration_matrix", "task_id_mapping", "stop_gate_migration", "rollback"]:
        if section not in migration or not migration.get(section):
            errors.append(f"migration matrix missing {section}")
    strengthened = set(migration.get("stop_gate_migration", {}).get("added_or_strengthened", []))
    if "SCOPE-ESCAPE" not in strengthened:
        errors.append("migration matrix must include SCOPE-ESCAPE as a V7.2 strengthened stop code")

    agents = review.get("agents", {})
    for agent in ("A", "B", "C"):
        if agents.get(agent, {}).get("status") != "pass_with_required_controls":
            errors.append(f"final review agent {agent} did not pass with required controls")
    if review.get("baseline_publication_verdict", {}).get("status") != "pass":
        errors.append("final review did not pass V7.2 baseline publication")

    if roadmap.get("global_current_task") != CURRENT_STAGE2_TASK:
        errors.append(f"roadmap global_current_task must be {CURRENT_STAGE2_TASK}")
    if roadmap.get("stage2_shadow_source_next") != CURRENT_SHADOW_SOURCE_NEXT:
        errors.append(f"roadmap stage2_shadow_source_next must be {CURRENT_SHADOW_SOURCE_NEXT}")
    if roadmap.get("email_v1_workstream_next") != EMAIL_V1_MERGED_STATE:
        errors.append("roadmap does not record Email V1 as merged to main with no production side effects")
    if current.get("current_pointer_registry", {}).get("email_v1_workstream_next") != EMAIL_V1_MERGED_STATE:
        errors.append("CURRENT.yaml contextual Email V1 status mismatch")
    if product.get("current_pointer_policy", {}).get("email_v1_workstream_next") != EMAIL_V1_MERGED_STATE:
        errors.append("product contract Email V1 pointer policy mismatch")
    if lock.get("stage2_boundary", {}).get("email_v1_workstream_next") != EMAIL_V1_MERGED_STATE:
        errors.append("V7_2_ROOT_LOCK Email V1 boundary status mismatch")
    if pointer.get("single_current_product_contract", {}).get("current_contract_version") != "ADP-PRODUCT-CONTRACT-V7.2":
        errors.append("current pointer registry does not identify V7.2 as current")
    pointer_context = pointer.get("contextual_next_tasks", {})
    if pointer_context.get("global_current_task", {}).get("task_id") != CURRENT_STAGE2_TASK:
        errors.append(f"current pointer registry global current task must be {CURRENT_STAGE2_TASK}")
    if pointer_context.get("email_v1_workstream_next", {}).get("task_id") != EMAIL_V1_MERGED_STATE:
        errors.append("current pointer registry Email V1 workstream status mismatch")

    baseline_workstream = next(
        (item for item in roadmap.get("workstreams", []) if item.get("workstream_id") == "V7_2_BASELINE_UPGRADE"),
        {},
    )
    completed_tasks = set(baseline_workstream.get("completed_tasks", []))
    if not EMAIL_V1_REQUIRED_TASKS.issubset(completed_tasks):
        errors.append("V7.2 baseline completed_tasks must include Email V1 T00-T05")
    if baseline_workstream.get("next_task") != CURRENT_STAGE2_TASK:
        errors.append(f"V7.2 baseline next_task must route to {CURRENT_STAGE2_TASK}")

    email_workstream = next(
        (item for item in roadmap.get("workstreams", []) if item.get("workstream_id") == "EMAIL_LEARNING_V1"),
        {},
    )
    if email_workstream.get("status") != "merged_to_main_no_production_side_effects":
        errors.append("EMAIL_LEARNING_V1 workstream must be merged_to_main_no_production_side_effects")
    task_status = {item.get("task_id"): item.get("status") for item in email_workstream.get("tasks", [])}
    for task_id in EMAIL_V1_REQUIRED_TASKS:
        if task_status.get(task_id) != "completed":
            errors.append(f"EMAIL_LEARNING_V1 task {task_id} must be completed")

    handoff_text = required["handoff"].read_text(encoding="utf-8")
    for token in ("CURRENT 产品合同：`ADP-PRODUCT-CONTRACT-V7.2`", "所有 Stage2 agent", EMAIL_V1_MERGED_STATE, CURRENT_STAGE2_TASK):
        if token not in handoff_text:
            errors.append(f"handoff missing token: {token}")

    result = {
        "status": "PASS" if not errors else "FAIL",
        "contract_version": "ADP-PRODUCT-CONTRACT-V7.2",
        "current_pointer": current.get("current_product_contract", {}).get("root_lock"),
        "roadmap_machine_gate": {
            "status": "PASS" if not roadmap_machine_gate_errors and not stop_registry_errors else "FAIL",
            **roadmap_machine_gate,
        },
        "errors": errors,
        "warnings": warnings,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
