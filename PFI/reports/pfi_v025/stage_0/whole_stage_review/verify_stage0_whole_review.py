#!/usr/bin/env python3
"""Read-only verifier for the PFI v0.2.5 Stage 0 whole-review candidate."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import subprocess
import zipfile
from collections import Counter
from pathlib import Path

from jsonschema import Draft202012Validator


SCRIPT_PATH = Path(__file__).resolve()
ROOT = Path(
    subprocess.check_output(
        ["git", "-C", str(SCRIPT_PATH.parent), "rev-parse", "--show-toplevel"],
        text=True,
    ).strip()
)
REVIEW_DIR = ROOT / "PFI/reports/pfi_v025/stage_0/whole_stage_review"
ROADMAP = Path(
    os.environ.get(
        "PFI_V025_ROADMAP",
        Path.home() / "Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_Roadmap.md",
    )
)
TASK_PACK = Path(
    os.environ.get(
        "PFI_V025_TASK_PACK",
        Path.home()
        / "Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip",
    )
)
ROADMAP_SHA256 = "fc2f406eef45d9a09f852aad1a2234b2c37547f8ae9c002d6230c54f7ca1071b"
TASK_PACK_SHA256 = "591c839992963a631e079498ec98f6e83a5686ead4ce4ea2c8aea39ab3346dd2"
REVIEW_BASE = "a590a3da20f2cf569c11114a3f46e1ff1a0ef6f2"
EXPECTED_PATHS = sorted(
    [
        "PFI/CHANGELOG.md",
        "PFI/docs/governance/DEVELOPMENT_LEDGER.md",
        "PFI/docs/governance/OWNER_STATUS.md",
        "PFI/docs/governance/STATUS.md",
        "PFI/docs/governance/TRACEABILITY_MATRIX.csv",
        "PFI/docs/governance/VERSION_MATRIX.yaml",
        "PFI/docs/governance/delivery_tasks.yaml",
        "PFI/docs/governance/development_events.jsonl",
        "PFI/docs/pfi_v025/stage_0/STAGE_0_WHOLE_STAGE_REVIEW.md",
        "PFI/docs/pfi_v025/stage_0/stage_0_acceptance_request.md",
        "PFI/reports/pfi_v025/stage_0/whole_stage_review/changed_files.txt",
        "PFI/reports/pfi_v025/stage_0/whole_stage_review/evidence.json",
        "PFI/reports/pfi_v025/stage_0/whole_stage_review/review_audit.json",
        "PFI/reports/pfi_v025/stage_0/whole_stage_review/risk_and_rollback.md",
        "PFI/reports/pfi_v025/stage_0/whole_stage_review/terminal.log",
        "PFI/reports/pfi_v025/stage_0/whole_stage_review/verify_stage0_whole_review.py",
    ]
)


def run(*args: str) -> bytes:
    return subprocess.check_output(args, cwd=ROOT)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def repo_bytes(ref: str, candidate: str | None) -> bytes:
    if candidate:
        return run("git", "show", f"{candidate}:{ref}")
    return (ROOT / ref).read_bytes()


def repo_text(ref: str, candidate: str | None) -> str:
    return repo_bytes(ref, candidate).decode("utf-8")


def repo_sha256(ref: str, candidate: str | None) -> str:
    return sha256_bytes(repo_bytes(ref, candidate))


def parse_yaml(text: str) -> object:
    ruby = (
        'require "yaml"; require "json"; '
        "print JSON.generate(YAML.safe_load(STDIN.read, permitted_classes: [], "
        "permitted_symbols: [], aliases: true))"
    )
    output = subprocess.check_output(
        ["ruby", "-e", ruby], input=text, text=True, cwd=ROOT
    )
    return json.loads(output)


def changed_paths(candidate: str | None) -> list[str]:
    if candidate:
        output = run("git", "diff", "--name-only", f"{candidate}^..{candidate}")
        return sorted(output.decode().splitlines())
    tracked = run("git", "diff", "HEAD", "--name-only").decode().splitlines()
    untracked = run("git", "ls-files", "--others", "--exclude-standard").decode().splitlines()
    return sorted(tracked + untracked)


def added_text(candidate: str | None) -> str:
    diff_args = (
        ("git", "diff", "--unified=0", "--no-color", f"{candidate}^", candidate, "--")
        if candidate
        else ("git", "diff", "HEAD", "--unified=0", "--no-color", "--")
    )
    added_lines = [
        line[1:]
        for line in run(*diff_args).decode(errors="replace").splitlines()
        if line.startswith("+") and not line.startswith("+++")
    ]
    if not candidate:
        untracked = run("git", "ls-files", "--others", "--exclude-standard").decode().splitlines()
        for ref in untracked:
            if ref in EXPECTED_PATHS:
                added_lines.extend((ROOT / ref).read_text(encoding="utf-8").splitlines())
    return "\n".join(added_lines)


def verify(candidate: str | None) -> dict[str, object]:
    if not __debug__:
        raise RuntimeError("optimized Python is forbidden because verification assertions must run")

    evidence_ref = "PFI/reports/pfi_v025/stage_0/whole_stage_review/evidence.json"
    audit_ref = "PFI/reports/pfi_v025/stage_0/whole_stage_review/review_audit.json"
    request_ref = "PFI/docs/pfi_v025/stage_0/stage_0_acceptance_request.md"
    changed_file_ref = (
        "PFI/reports/pfi_v025/stage_0/whole_stage_review/changed_files.txt"
    )
    evidence = json.loads(repo_text(evidence_ref, candidate))
    audit = json.loads(repo_text(audit_ref, candidate))

    assert sha256_file(ROADMAP) == ROADMAP_SHA256
    assert sha256_file(TASK_PACK) == TASK_PACK_SHA256
    assert evidence["source_hashes"] == {
        "roadmap_sha256": ROADMAP_SHA256,
        "task_pack_sha256": TASK_PACK_SHA256,
    }

    if candidate:
        assert run("git", "rev-parse", candidate).decode().strip() == run(
            "git", "rev-parse", "HEAD"
        ).decode().strip()
        assert run("git", "status", "--porcelain") == b""
        assert run("git", "rev-list", "--parents", "-n", "1", candidate).decode().split() == [
            run("git", "rev-parse", candidate).decode().strip(),
            REVIEW_BASE,
        ]

    with zipfile.ZipFile(TASK_PACK) as archive:
        schema = json.loads(
            archive.read("PFI_v0.2.5_TaskPack/schemas/evidence_pack.schema.json")
        )
    Draft202012Validator(schema).validate(evidence)

    request_match = re.search(
        r"^evidence_sha256=([0-9a-f]{64})$",
        repo_text(request_ref, candidate),
        re.MULTILINE,
    )
    assert request_match
    review_sha = repo_sha256(evidence_ref, candidate)
    assert request_match.group(1) == review_sha

    expected_paths = sorted(repo_text(changed_file_ref, candidate).splitlines())
    actual_paths = changed_paths(candidate)
    assert expected_paths == EXPECTED_PATHS
    assert expected_paths == actual_paths
    assert sorted(evidence["changed_files"]) == actual_paths
    assert len(actual_paths) == 16
    assert not any("/stage_1/" in path for path in actual_paths)
    assert not any(
        path.startswith(("PFI/src/", "PFI/web/", "PFI/tests/", "PFI/macos/"))
        for path in actual_paths
    )

    excluded_from_artifact_hashes = {
        "PFI/docs/pfi_v025/stage_0/stage_0_acceptance_request.md",
        "PFI/reports/pfi_v025/stage_0/whole_stage_review/evidence.json",
    }
    expected_artifact_paths = set(actual_paths) - excluded_from_artifact_hashes
    assert set(evidence["artifact_hashes"]) == expected_artifact_paths
    for ref, expected in evidence["artifact_hashes"].items():
        actual = repo_sha256(ref, candidate)
        assert actual == expected, (ref, expected, actual)

    assert set(evidence["evidence_files"]) == {
        "PFI/docs/pfi_v025/stage_0/STAGE_0_WHOLE_STAGE_REVIEW.md",
        "PFI/docs/pfi_v025/stage_0/stage_0_acceptance_request.md",
        "PFI/reports/pfi_v025/stage_0/whole_stage_review/changed_files.txt",
        "PFI/reports/pfi_v025/stage_0/whole_stage_review/evidence.json",
        "PFI/reports/pfi_v025/stage_0/whole_stage_review/review_audit.json",
        "PFI/reports/pfi_v025/stage_0/whole_stage_review/risk_and_rollback.md",
        "PFI/reports/pfi_v025/stage_0/whole_stage_review/terminal.log",
        "PFI/reports/pfi_v025/stage_0/whole_stage_review/verify_stage0_whole_review.py",
    }

    common_dir = Path(run("git", "rev-parse", "--git-common-dir").decode().strip()).resolve()
    compensation_sha = (
        "2161efc16fdd178dba81ff5da5b97633656d433da8a26c1f71896625b1905b13"
    )
    compensation_candidates = list(
        common_dir.glob(
            "codex-review/pfi-v025/stage_0/phase_0_3/compensations/"
            "a590a3da20f2cf569c11114a3f46e1ff1a0ef6f2.attempt.*/"
            "phase_0_3_compensation_attestation.json"
        )
    )
    compensation_matches = [
        path for path in compensation_candidates if sha256_file(path) == compensation_sha
    ]
    assert compensation_matches
    compensation_attestation = compensation_matches[0]
    attestation = json.loads(compensation_attestation.read_text(encoding="utf-8"))
    assert attestation["status"] == "resolved_by_approved_compensation_override"
    assert attestation["blocks_phase_candidate"] is False

    commit_refs = [
        (
            "332953e002162bce1b28aa616b24ddaa936f1935",
            "PFI/reports/pfi_v025/stage_0/phase_0_1/evidence.json",
            "2f45b6b9774b24a0bc990d9476e13448604cdd9169e82e37f0c14c7c8daddf35",
        ),
        (
            "7433be0d70bdae42959c1b71753d93f8737db60d",
            "PFI/reports/pfi_v025/stage_0/phase_0_2/evidence.json",
            "d0e7e3c4413404c0dee91b1173b8d3e270c50faa6f06c3fc4cdd24ff90b6a1f8",
        ),
        (
            "31368570082c34eca50c72c7d7b2ef46b0e6854d",
            "PFI/reports/pfi_v025/stage_0/phase_0_3/evidence.json",
            "599648821cc2275693b8495516e342c3db6a3cc9e211c3a1e187da0fe4a09d31",
        ),
        (
            "31368570082c34eca50c72c7d7b2ef46b0e6854d",
            "PFI/docs/pfi_v025/stage_0/acceptance_request.md",
            "f71c70d15dc1c4c8f873833ba0df94ae3539a35352e7697ef523cd5ffbef4814",
        ),
        (
            "a590a3da20f2cf569c11114a3f46e1ff1a0ef6f2",
            "PFI/reports/pfi_v025/stage_0/phase_0_3/evidence.json",
            "06201b1ed07c85970a2af1f91f4c8da72161d8cc04755f02c2e5741e7e8aa864",
        ),
        (
            "a590a3da20f2cf569c11114a3f46e1ff1a0ef6f2",
            "PFI/docs/pfi_v025/stage_0/acceptance_request.md",
            "fc7327bb5cdec0dd34dac86fe0fa82389949707c360ea914ad44be7e672bad44",
        ),
    ]
    for commit, ref, expected in commit_refs:
        assert sha256_bytes(run("git", "show", f"{commit}:{ref}")) == expected

    findings = list(
        csv.DictReader(
            io.StringIO(
                repo_text("PFI/docs/pfi_v025/stage_0/finding_ledger.csv", candidate)
            )
        )
    )
    assert len(findings) == len({row["finding_id"] for row in findings}) == 38
    assert Counter(row["current_status"] for row in findings) == Counter(
        {"StillPresent": 23, "Fixed": 7, "N/A": 4, "New": 4}
    )
    open_p0_p1 = [
        row
        for row in findings
        if row["blocks_v025_production_acceptance"] == "true"
        and row["priority"] in {"P0", "P1"}
    ]
    assert len(open_p0_p1) == 27

    active = json.loads(
        repo_text("PFI/config/pfi_v025_active_requirements.json", candidate)
    )
    assert active["official_nav"] == [
        "首页总览",
        "账户与资产",
        "账本流水",
        "投资管理",
        "消费管理",
        "数据源与上传",
        "建议与复盘",
        "报告与洞察",
        "市场与研究",
        "设置",
    ]
    assert "GAP-P1-04" not in repo_text(
        "PFI/docs/pfi_v025/stage_0/gap_register.md", candidate
    )

    selector = audit["selector_compensation"]["selector"]
    design_lines = repo_text(
        audit["selector_compensation"]["artifact_ref"], candidate
    ).splitlines()
    matches = [line for line in design_lines if line == selector]
    assert len(matches) == 1
    assert sha256_bytes(matches[0].encode()) == audit["selector_compensation"][
        "source_text_sha256"
    ]
    assert audit["post_remediation_counts"] == {
        "critical": 0,
        "important": 0,
        "minor": 0,
    }

    assert not (ROOT / "PFI/reports/pfi_v025/stage_0/human_acceptance.json").exists()
    assert evidence["requires_user_acceptance"] is True
    assert evidence["contains_private_values"] is False
    assert evidence["allowed_files_obeyed"] is True
    assert evidence["status"] == "candidate_pass"
    assert evidence["stage_1_status"] == "not_started"
    assert evidence["stage_0_codex_verdict"] == (
        "candidate_pass_pending_review_commit_attestation_and_user_acceptance"
    )
    assert evidence["review_findings"]["post_remediation_counts"] == {
        "critical": 0,
        "important": 0,
        "minor": 0,
    }
    assert evidence["no_side_effects_observed"] == {
        "git_push": False,
        "git_fetch_or_ref_update": False,
        "app_install_or_mutation": False,
        "runtime_mutation": False,
        "data_write": False,
        "database_write": False,
        "product_or_test_path_changed": False,
    }

    privacy_text = added_text(candidate)
    high_risk_patterns = {
        "private_key": r"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----",
        "github_token": r"\bgh[pousr]_[A-Za-z0-9]{20,}\b",
        "aws_access_key": r"\bAKIA[0-9A-Z]{16}\b",
        "openai_key": r"\bsk-[A-Za-z0-9]{20,}\b",
        "private_database_path": r"/Users/[^/]+/\.pfi/[^\s\"']+",
    }
    privacy_findings = {
        name: len(re.findall(pattern, privacy_text, flags=re.IGNORECASE))
        for name, pattern in high_risk_patterns.items()
    }
    assert all(count == 0 for count in privacy_findings.values()), privacy_findings

    event_matches = [
        json.loads(line)
        for line in repo_text(
            "PFI/docs/governance/development_events.jsonl", candidate
        ).splitlines()
        if json.loads(line).get("event_id")
        == "EVENT-20260712-PFI-V025-S0-WHOLE-REVIEW"
    ]
    assert len(event_matches) == 1
    event = event_matches[0]
    assert event["files_changed"] == evidence["changed_files"]
    assert event["result"] == (
        "codex_candidate_pass_pending_review_commit_attestation_and_explicit_user_acceptance"
    )
    assert event["binding_status"] == "pending_external_postcommit_attestation"
    assert event["requires_user_acceptance"] is True
    assert event["human_acceptance_status"] == "absent"
    assert event["stage_1_status"] == "not_started"

    trace_rows = list(
        csv.DictReader(
            repo_text("PFI/docs/governance/TRACEABILITY_MATRIX.csv", candidate).splitlines()
        )
    )
    trace_matches = [
        row for row in trace_rows if row["requirement_id"] == "REQ-PFI-V025-S0-WHOLE-REVIEW"
    ]
    assert len(trace_matches) == 1
    trace = trace_matches[0]
    assert trace["test_ref"] == (
        "PFI/reports/pfi_v025/stage_0/whole_stage_review/verify_stage0_whole_review.py"
    )
    assert trace["evidence_ref"] == (
        "PFI/reports/pfi_v025/stage_0/whole_stage_review/evidence.json"
    )
    assert trace["status"] == (
        "codex_candidate_pass_pending_review_commit_attestation_and_user_acceptance"
    )

    delivery_text = repo_text("PFI/docs/governance/delivery_tasks.yaml", candidate)
    delivery = parse_yaml(delivery_text)
    delivery_matches = [
        item
        for item in delivery["phase_contracts"]
        if item.get("iteration_id") == "ITER-20260712-PFI-V025-S0-WHOLE-REVIEW"
    ]
    assert len(delivery_matches) == 1
    delivery_contract = delivery_matches[0]
    assert delivery_contract["lifecycle"] == (
        "codex_candidate_pass_pending_review_commit_attestation_and_user_acceptance"
    )
    assert delivery_contract["binding_status"] == (
        "tracked_candidate_requires_external_postcommit_attestation"
    )
    assert delivery_contract["human_acceptance_status"] == (
        "absent_pending_explicit_user_acceptance"
    )
    assert delivery_contract["stage_1_status"] == "not_started"

    request_text = repo_text(request_ref, candidate)
    for expected_line in (
        "status=prepared_pending_review_commit_attestation_and_user_acceptance",
        "review_commit=BOUND_BY_EXTERNAL_POSTCOMMIT_ATTESTATION",
        "确认前：`Stage 1 = not_started`。",
    ):
        assert expected_line in request_text

    diff_check_args = (
        ("git", "diff", "--check", f"{candidate}^", candidate)
        if candidate
        else ("git", "diff", "HEAD", "--check")
    )
    assert run(*diff_check_args) == b""

    return {
        "result": "PASS",
        "candidate": candidate or "working_tree",
        "exact_paths": len(actual_paths),
        "review_evidence_sha256": review_sha,
        "artifact_hashes": len(evidence["artifact_hashes"]),
        "commit_qualified_bindings": len(commit_refs),
        "finding_count": len(findings),
        "open_p0_p1": len(open_p0_p1),
        "selector_match_count": len(matches),
        "post_remediation": "C0/I0/M0",
        "privacy_high_risk_findings": sum(privacy_findings.values()),
        "privacy_added_lines_scanned": len(privacy_text.splitlines()),
        "human_acceptance": "absent",
        "stage_1": "not_started",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", help="Committed whole-review candidate SHA")
    args = parser.parse_args()
    print(json.dumps(verify(args.candidate), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
