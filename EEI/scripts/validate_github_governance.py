#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    target = ROOT / path
    if not target.is_file():
        raise AssertionError(f"missing required file: {path}")
    return target.read_text(encoding="utf-8")


def require_contains(path: str, phrases: list[str]) -> None:
    text = read_text(path)
    missing = [phrase for phrase in phrases if phrase not in text]
    if missing:
        raise AssertionError(f"{path} missing required phrases: {missing}")


def load_yaml(path: str) -> object:
    return yaml.safe_load(read_text(path))


def validate_issue_templates() -> None:
    required_templates = [
        ".github/ISSUE_TEMPLATE/bug.yml",
        ".github/ISSUE_TEMPLATE/data_relationship.yml",
        ".github/ISSUE_TEMPLATE/data_scope_change.yml",
        ".github/ISSUE_TEMPLATE/feature.yml",
        ".github/ISSUE_TEMPLATE/model_change.yml",
        ".github/ISSUE_TEMPLATE/risk_control.yml",
    ]
    for path in required_templates:
        payload = load_yaml(path)
        if not isinstance(payload, dict):
            raise AssertionError(f"{path} must be a YAML object")
        body = payload.get("body")
        if not isinstance(body, list) or len(body) < 3:
            raise AssertionError(f"{path} must define structured body fields")
        required_count = 0
        for field in body:
            if not isinstance(field, dict):
                continue
            validations = field.get("validations")
            if isinstance(validations, dict) and validations.get("required") is True:
                required_count += 1
            attributes = field.get("attributes")
            if isinstance(attributes, dict):
                for option in attributes.get("options", []):
                    if isinstance(option, dict) and option.get("required") is True:
                        required_count += 1
        if required_count < 3:
            raise AssertionError(f"{path} must have at least three required fields")


def validate_codeowners() -> None:
    require_contains(
        ".github/CODEOWNERS",
        [
            "* @linzezhang35",
            "/docs/ @linzezhang35",
            "/data/ @linzezhang35",
            "/models/ @linzezhang35",
            "/config/ @linzezhang35",
            "/specs/ @linzezhang35",
            "/.github/ @linzezhang35",
            "/scripts/ @linzezhang35",
        ],
    )


def validate_pull_request_template() -> None:
    require_contains(
        ".github/pull_request_template.md",
        [
            "关联 Issue",
            "影响功能 ID",
            "影响模型/公式/参数 ID",
            "data/function_catalog.csv",
            "data/development_status_ledger.csv",
            "data/acceptance_traceability.csv",
            "data/risk_control_traceability.csv",
            "manifest.txt",
            "CHECKSUMS.sha256",
            "测试命令",
            "Acceptance ID",
            "回滚方案",
            "未解决问题",
        ],
    )


def validate_workflow() -> None:
    workflow = load_yaml(".github/workflows/governance-validation.yml")
    if not isinstance(workflow, dict):
        raise AssertionError("governance workflow must be a YAML object")
    events = workflow.get(True) or workflow.get("on")
    if not isinstance(events, dict):
        raise AssertionError("governance workflow must define events")
    for event in ["pull_request", "push", "workflow_dispatch"]:
        if event not in events:
            raise AssertionError(f"governance workflow missing event: {event}")
    jobs = workflow.get("jobs")
    if not isinstance(jobs, dict):
        raise AssertionError("governance workflow missing jobs")
    for job_name in ["validate", "visual-validation"]:
        if job_name not in jobs:
            raise AssertionError(f"governance workflow missing job: {job_name}")
    require_contains(
        ".github/workflows/governance-validation.yml",
        [
            "python scripts/validate_catalog_integrity.py",
            "python scripts/validate_governance.py",
            "python scripts/validate_task_pack.py",
            "python scripts/validate_governance_consistency.py",
            "python scripts/validate_visual_coverage.py",
            "sha256sum -c CHECKSUMS.sha256",
        ],
    )


def validate_branch_and_release_contracts() -> None:
    required_checks = [
        "EEI validation / verify",
        "governance-validation / validate",
        "governance-validation / visual-validation",
    ]
    require_contains(
        ".github/branch_protection.md",
        [
            "main",
            "Require pull request before merge",
            "Require review from CODEOWNERS",
            "Block force pushes",
            *required_checks,
        ],
    )
    require_contains(
        ".github/release_checklist.md",
        [
            "make verify",
            "make verify-g2-db",
            "manifest.txt",
            "DIRECTORY_TREE.txt",
            "CHECKSUMS.sha256",
            "Acceptance IDs",
            "CI run IDs",
            "rollback",
            *required_checks,
        ],
    )
    release_config = load_yaml(".github/release.yml")
    if not isinstance(release_config, dict):
        raise AssertionError(".github/release.yml must be a YAML object")
    categories = release_config.get("changelog", {}).get("categories", [])
    titles = {item.get("title") for item in categories if isinstance(item, dict)}
    for title in ["功能", "数据与关系", "模型", "UI/UX", "修复"]:
        if title not in titles:
            raise AssertionError(f"release.yml missing category: {title}")


def validate_backup_registry() -> None:
    require_contains(
        "data/github_document_registry.csv",
        [
            ".github/CODEOWNERS",
            ".github/branch_protection.md",
            ".github/release_checklist.md",
            ".github/workflows/governance-validation.yml",
            "GITHUB_REPOSITORY_BACKUP_INDEX.md",
            "CHECKSUMS.sha256",
        ],
    )
    require_contains(
        "docs/34_GITHUB_DOCUMENTATION_AND_BACKUP.md",
        [
            ".github/CODEOWNERS",
            ".github/pull_request_template.md",
            ".github/workflows/governance-validation.yml",
            "branch protection",
            "CHECKSUMS.sha256",
        ],
    )


def main() -> int:
    validate_issue_templates()
    validate_codeowners()
    validate_pull_request_template()
    validate_workflow()
    validate_branch_and_release_contracts()
    validate_backup_registry()
    result = {
        "valid": True,
        "issue_templates": 6,
        "required_checks": [
            "EEI validation / verify",
            "governance-validation / validate",
            "governance-validation / visual-validation",
        ],
    }
    print("GitHub governance validation: PASS")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, yaml.YAMLError) as exc:
        print(f"GitHub governance validation: FAIL - {exc}")
        raise SystemExit(1) from None
