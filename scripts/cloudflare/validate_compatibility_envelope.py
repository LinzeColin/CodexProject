#!/usr/bin/env python3
"""Validate the Cloudflare compatibility registry and deployment truth."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROJECTS = REPO_ROOT / "governance/cloudflare/projects.yaml"
DEFAULT_DEPLOYMENTS = REPO_ROOT / "governance/cloudflare/deployments.json"
REQUIRED_PROJECTS = {
    "linze-home-hub",
    "nab",
    "eei",
    "openaidatabase",
    "pfi",
    "serenity-alipay",
}
REQUIRED_FIELDS = {
    "project_id",
    "source_repo",
    "source_path",
    "compatibility_level",
    "public_surface",
    "deploy_target",
    "worker_name",
    "preferred_domain",
    "actual_url",
    "status",
    "data_boundary",
    "private_data_allowed_in_dist",
    "build_command",
    "output_dir",
    "wrangler_config",
    "homehub_visibility",
    "required_for_this_task",
    "deployment_required",
    "deployment_result",
    "blockers",
    "acceptance",
    "rollback",
    "future_l3_extensions",
}
ALLOWED_LEVELS = {"L1", "L2", "L3"}
ALLOWED_DEPLOYMENT_RESULTS = {
    "not_required",
    "deployed_custom_domain_verified",
    "deployed_workers_dev_domain_pending",
    "deploy_ready_auth_blocked",
    "blocked_private_scan",
    "blocked_build_or_dry_run",
}


def load_json_compatible_yaml(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"root must be an object: {path}")
    return value


def is_https_url(value: object) -> bool:
    if not isinstance(value, str) or not value:
        return False
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.netloc)


def validate(projects_doc: dict[str, Any], deployments_doc: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    projects_value = projects_doc.get("projects")
    deployments_value = deployments_doc.get("projects")
    if not isinstance(projects_value, list):
        return ["projects must be a list"]
    if not isinstance(deployments_value, list):
        return ["deployments projects must be a list"]

    projects: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(projects_value):
        if not isinstance(item, dict):
            errors.append(f"project at index {index} must be an object")
            continue
        project_id = item.get("project_id")
        if not isinstance(project_id, str) or not project_id:
            errors.append(f"project at index {index} missing project_id")
            continue
        if project_id in projects:
            errors.append(f"duplicate project_id: {project_id}")
            continue
        projects[project_id] = item
        missing_fields = sorted(REQUIRED_FIELDS - item.keys())
        if missing_fields:
            errors.append(f"{project_id}: missing fields: {', '.join(missing_fields)}")
        level = item.get("compatibility_level")
        if level not in ALLOWED_LEVELS:
            errors.append(f"{project_id}: invalid compatibility_level: {level}")
        if item.get("private_data_allowed_in_dist") is not False:
            errors.append(f"{project_id}: private_data_allowed_in_dist must be false")
        result = item.get("deployment_result")
        if result not in ALLOWED_DEPLOYMENT_RESULTS:
            errors.append(f"{project_id}: invalid deployment_result: {result}")
        actual_url = item.get("actual_url")
        if level == "L1" and actual_url:
            errors.append(f"{project_id}: L1 project cannot have actual_url")
        if project_id in REQUIRED_PROJECTS:
            if level == "L1":
                errors.append(f"{project_id}: required project cannot be L1")
            if not item.get("public_surface"):
                errors.append(f"{project_id}: required project missing public_surface")
            if item.get("required_for_this_task") is not True:
                errors.append(f"{project_id}: required_for_this_task must be true")
            if item.get("deployment_required") is not True:
                errors.append(f"{project_id}: deployment_required must be true")
        if isinstance(result, str) and result.startswith("deployed_") and not is_https_url(actual_url):
            errors.append(f"{project_id}: deployed result requires verified actual_url")

    for project_id in sorted(REQUIRED_PROJECTS - projects.keys()):
        errors.append(f"missing required project: {project_id}")

    deployments: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(deployments_value):
        if not isinstance(item, dict):
            errors.append(f"deployment at index {index} must be an object")
            continue
        project_id = item.get("project_id")
        if isinstance(project_id, str) and project_id:
            if project_id in deployments:
                errors.append(f"duplicate deployment project_id: {project_id}")
            deployments[project_id] = item

    for project_id in sorted(REQUIRED_PROJECTS):
        project = projects.get(project_id)
        deployment = deployments.get(project_id)
        if deployment is None:
            errors.append(f"missing deployment record: {project_id}")
            continue
        if project is None:
            continue
        if deployment.get("deploy_result") != project.get("deployment_result"):
            errors.append(f"{project_id}: registry/deployment result mismatch")
        if deployment.get("actual_url", "") != project.get("actual_url", ""):
            errors.append(f"{project_id}: registry/deployment actual_url mismatch")
        result = deployment.get("deploy_result")
        if isinstance(result, str) and result.startswith("deployed_"):
            if deployment.get("http_verification") != "verified_200":
                errors.append(f"{project_id}: deployed result requires verified_200 HTTP evidence")

    return errors


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--projects", type=Path, default=DEFAULT_PROJECTS)
    parser.add_argument("--deployments", type=Path, default=DEFAULT_DEPLOYMENTS)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        projects_doc = load_json_compatible_yaml(args.projects)
        deployments_doc = load_json_compatible_yaml(args.deployments)
    except ValueError as exc:
        print(f"FAIL: {exc}")
        return 1
    errors = validate(projects_doc, deployments_doc)
    if errors:
        print("FAIL: Cloudflare compatibility envelope")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"PASS: Cloudflare compatibility envelope ({len(projects_doc['projects'])} projects)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

