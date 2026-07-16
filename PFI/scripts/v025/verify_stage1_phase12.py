#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import plistlib
import re
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


REPO_ROOT = Path(__file__).resolve().parents[3]
PFI_ROOT = REPO_ROOT / "PFI"
PHASE_BASE = "1a995226d34822b5e98191a716bca665136e300f"
RELEASE_CONTENT_COMMIT = "b3885f15cd2e983c0839be6a20d7e4a9391c6324"
SUPERSEDED_RELEASE_CONTENT_COMMIT = "5edd378828bc7795cd2920a73be19657a3f749b7"
SUPERSEDED_CACHE_BINDING_COMMIT = "df7e2add249f3547d1f6c37438c0b8085dc3480d"
ROADMAP_SHA256 = "fc2f406eef45d9a09f852aad1a2234b2c37547f8ae9c002d6230c54f7ca1071b"
TASK_PACK_SHA256 = "591c839992963a631e079498ec98f6e83a5686ead4ce4ea2c8aea39ab3346dd2"
PHASE_DIR = "PFI/reports/pfi_v025/stage_1/phase_1_2"
EXPECTED_PATHS = [
    "PFI/CHANGELOG.md",
    "PFI/StartPFI.command",
    "PFI/config/release_manifest.json",
    "PFI/docs/governance/DEVELOPMENT_LEDGER.md",
    "PFI/docs/governance/OWNER_STATUS.md",
    "PFI/docs/governance/STATUS.md",
    "PFI/docs/governance/TRACEABILITY_MATRIX.csv",
    "PFI/docs/governance/VERSION_MATRIX.yaml",
    "PFI/docs/governance/delivery_tasks.yaml",
    "PFI/docs/governance/development_events.jsonl",
    "PFI/docs/pfi_v025/stage_1/PHASE_1_2_CACHE_GOVERNANCE_IMPLEMENTATION_PLAN.md",
    f"{PHASE_DIR}/asset_identity.json",
    f"{PHASE_DIR}/bfcache_mismatch.png",
    f"{PHASE_DIR}/browser_validation.json",
    f"{PHASE_DIR}/cache_audit.md",
    f"{PHASE_DIR}/cache_headers.json",
    f"{PHASE_DIR}/changed_files.txt",
    f"{PHASE_DIR}/evidence.json",
    f"{PHASE_DIR}/playwright_trace.zip",
    f"{PHASE_DIR}/privacy_scan.txt",
    f"{PHASE_DIR}/risk_and_rollback.md",
    f"{PHASE_DIR}/service_worker_audit.md",
    f"{PHASE_DIR}/streamlit_cache_policy.json",
    f"{PHASE_DIR}/terminal.log",
    "PFI/scripts/pfiReleaseIdentity.sh",
    "PFI/scripts/startPFI.sh",
    "PFI/scripts/v025/browser_validate_stage1_phase12.mjs",
    "PFI/scripts/v025/release_cache_contract.py",
    "PFI/scripts/v025/run_streamlit_with_release_cache.py",
    "PFI/scripts/v025/verify_stage1_phase12.py",
    "PFI/src/pfi_v02/stage_v021_runtime_api.py",
    "PFI/tests/test_v025_stage1_cache_policy.py",
    "PFI/web/app/version.js",
    "PFI/web/index.html",
    "PFI/web/tests/v025/stage1_cache_policy.test.mjs",
    "PFI/web/tests/v025/stage1_release_identity.test.mjs",
]
CACHE_DIMENSION_FIELDS = (
    "build_id",
    "git_commit",
    "frontend_bundle_hash",
    "backend_build_hash",
    "data_hash",
    "parameter_hash",
    "formula_hash",
    "fx_snapshot_id",
    "fx_snapshot_hash",
    "read_model_hash",
    "streamlit_version",
    "requirements_lock_hash",
)


def run(*args: str, check: bool = True) -> bytes:
    result = subprocess.run(args, cwd=REPO_ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if check and result.returncode != 0:
        raise AssertionError(
            f"command failed ({result.returncode}): {' '.join(args)}\n{result.stderr.decode(errors='replace')}"
        )
    return result.stdout


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def repo_bytes(path: str, candidate: str | None) -> bytes:
    if candidate:
        return run("git", "show", f"{candidate}:{path}")
    return (REPO_ROOT / path).read_bytes()


def repo_text(path: str, candidate: str | None) -> str:
    return repo_bytes(path, candidate).decode("utf-8")


def repo_json(path: str, candidate: str | None) -> dict[str, Any]:
    payload = json.loads(repo_text(path, candidate))
    assert isinstance(payload, dict), path
    return payload


def changed_paths(candidate: str | None) -> list[str]:
    if candidate:
        output = run("git", "diff", "--name-only", f"{PHASE_BASE}..{candidate}").decode()
        return sorted(line for line in output.splitlines() if line.startswith("PFI/"))
    tracked = run("git", "diff", "--name-only", PHASE_BASE).decode().splitlines()
    untracked = run("git", "ls-files", "--others", "--exclude-standard").decode().splitlines()
    return sorted({line for line in [*tracked, *untracked] if line.startswith("PFI/")})


def task_pack_schemas(task_pack: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    with zipfile.ZipFile(task_pack) as archive:
        assert archive.testzip() is None
        release_schema = json.loads(
            archive.read("PFI_v0.2.5_TaskPack/schemas/release_manifest.schema.json").decode("utf-8")
        )
        evidence_schema = json.loads(
            archive.read("PFI_v0.2.5_TaskPack/schemas/evidence_pack.schema.json").decode("utf-8")
        )
    return release_schema, evidence_schema


def frontend_hash(candidate: str | None) -> tuple[str, list[str]]:
    source = repo_text("PFI/web/index.html", candidate)
    canonical, count = re.subn(
        r'(<script\s+type="application/json"\s+id="pfi-release-manifest">).*?(</script>)',
        r"\1{}\2",
        source,
        count=1,
        flags=re.DOTALL,
    )
    assert count == 1
    script_refs = re.findall(r'<script\s+src="\./([^"?#]+)"', source)
    paths = {
        "PFI/web/index.html",
        "PFI/web/styles/tokens.css",
        "PFI/web/styles.css",
        *(f"PFI/web/{ref}" for ref in script_refs),
    }
    records = []
    for path in sorted(paths):
        payload = canonical.encode("utf-8") if path == "PFI/web/index.html" else repo_bytes(path, candidate)
        records.append(f"{path}\0{sha256_bytes(payload)}\n".encode("utf-8"))
    return sha256_bytes(b"".join(records)), sorted(paths)


def embedded_manifest(candidate: str | None) -> dict[str, Any]:
    match = re.search(
        r'<script\s+type="application/json"\s+id="pfi-release-manifest">(.*?)</script>',
        repo_text("PFI/web/index.html", candidate),
        re.DOTALL,
    )
    assert match
    payload = json.loads(match.group(1))
    assert isinstance(payload, dict)
    return payload


def compute_cache_key(policy: dict[str, Any]) -> str:
    dimensions = {field: policy[field] for field in CACHE_DIMENSION_FIELDS}
    raw = json.dumps(dimensions, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256_bytes(raw)


def verify_attestation(candidate: str, evidence: dict[str, Any]) -> str:
    common = Path(run("git", "rev-parse", "--git-common-dir").decode().strip()).resolve()
    path = common / "codex-review" / "pfi-v025" / "stage_1" / "phase_1_2" / candidate / "phase_1_2_attestation.json"
    assert path.is_file(), path
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["schema"] == "PFIV025Stage1Phase12ExternalAttestationV1"
    assert payload["release_content_commit"] == RELEASE_CONTENT_COMMIT
    assert payload["cache_binding_commit"] == candidate
    assert payload["manifest_sha256"] == sha256_bytes(repo_bytes("PFI/config/release_manifest.json", candidate))
    assert payload["evidence_sha256"] == sha256_bytes(repo_bytes(f"{PHASE_DIR}/evidence.json", candidate))
    assert payload["changed_files"] == EXPECTED_PATHS
    assert payload["verifier_result"] == "PASS"
    assert payload["review_findings_after_remediation"] == {"critical": 0, "important": 0, "minor": 0}
    assert len(payload["independent_reviewers"]) == 3
    assert payload["push_performed"] is False
    assert payload["app_install_performed"] is False
    assert payload["final_human_acceptance"] is False
    return sha256_bytes(path.read_bytes())


def verify(
    *,
    candidate_arg: str | None,
    task_pack: Path,
    roadmap: Path,
    require_attestation: bool,
) -> dict[str, Any]:
    candidate = None
    if candidate_arg:
        candidate = run("git", "rev-parse", candidate_arg).decode().strip()
        assert candidate == run("git", "rev-parse", "HEAD").decode().strip()
        assert run("git", "status", "--porcelain") == b""
        parents = run("git", "rev-list", "--parents", "-n", "1", candidate).decode().split()
        assert parents == [candidate, RELEASE_CONTENT_COMMIT], parents
    else:
        assert run("git", "rev-parse", "HEAD").decode().strip() == RELEASE_CONTENT_COMMIT

    assert sha256_bytes(task_pack.read_bytes()) == TASK_PACK_SHA256
    assert sha256_bytes(roadmap.read_bytes()) == ROADMAP_SHA256
    release_schema, evidence_schema = task_pack_schemas(task_pack)
    assert changed_paths(candidate) == EXPECTED_PATHS, (EXPECTED_PATHS, changed_paths(candidate))

    manifest = repo_json("PFI/config/release_manifest.json", candidate)
    Draft202012Validator(release_schema, format_checker=FormatChecker()).validate(manifest)
    assert manifest["version"] == "v0.2.5"
    assert manifest["git_commit"] == RELEASE_CONTENT_COMMIT
    computed_frontend, frontend_files = frontend_hash(candidate)
    computed_backend = sha256_bytes(repo_bytes("PFI/src/pfi_v02/stage_v021_runtime_api.py", candidate))
    assert manifest["frontend_bundle_hash"] == computed_frontend
    assert manifest["backend_build_hash"] == computed_backend
    assert embedded_manifest(candidate) == manifest

    asset = repo_json(f"{PHASE_DIR}/asset_identity.json", candidate)
    assert asset["valid"] is True
    assert asset["release_content_commit"] == RELEASE_CONTENT_COMMIT
    assert asset["frontend_bundle_hash"] == computed_frontend
    assert asset["backend_build_hash"] == computed_backend
    assert asset["running_backend_hash"] == computed_backend
    assert asset["frontend_file_count"] == len(frontend_files)

    policy = repo_json(f"{PHASE_DIR}/streamlit_cache_policy.json", candidate)
    assert policy["schema"] == "PFIV025Stage1ReleaseCachePolicyV1"
    assert policy["valid"] is True and policy["asset_identity_valid"] is True
    assert policy["persistent"] is False and policy["ttl_seconds"] == 30
    assert policy["cache_mode"] == "streamlit_cache_data_composite_key_v1"
    assert policy["git_commit"] == RELEASE_CONTENT_COMMIT
    assert policy["frontend_bundle_hash"] == computed_frontend
    assert policy["backend_build_hash"] == computed_backend == policy["running_backend_hash"]
    assert all(isinstance(policy[field], str) and policy[field] for field in CACHE_DIMENSION_FIELDS)
    assert set(CACHE_DIMENSION_FIELDS).issubset(policy["invalidation"])
    assert policy["streamlit_cache_key"] == compute_cache_key(policy) == policy["process_cache_key"]

    headers = repo_json(f"{PHASE_DIR}/cache_headers.json", candidate)
    assert headers["live_ports_8501_8502_accessed"] is False
    assert headers["html"]["cache_control"] == "no-cache, private"
    assert headers["html"]["conditional_if_none_match_status"] == 304
    assert headers["hashed_asset"]["cache_control"] == "public, max-age=31536000, immutable"
    assert headers["unhashed_asset"]["cache_control"] == "no-cache, private"
    assert all(headers["checks"].values())

    browser = repo_json(f"{PHASE_DIR}/browser_validation.json", candidate)
    assert browser["live_ports_8501_8502_accessed"] is False
    assert browser["bfcache"]["real_persisted_observed"] is False
    assert browser["bfcache"]["synthetic_event_used_only_for_deterministic_mismatch_path"] is True
    assert browser["console_errors"] == [] and browser["page_errors"] == []
    assert all(browser["checks"].values())
    assert len(repo_bytes(f"{PHASE_DIR}/bfcache_mismatch.png", candidate)) > 10_000
    assert len(repo_bytes(f"{PHASE_DIR}/playwright_trace.zip", candidate)) > 10_000

    evidence = repo_json(f"{PHASE_DIR}/evidence.json", candidate)
    Draft202012Validator(evidence_schema, format_checker=FormatChecker()).validate(evidence)
    assert evidence["schema"] == "PFIV025Stage1Phase12EvidenceV1"
    assert evidence["status"] == "candidate_pass"
    assert evidence["git_commit"] == RELEASE_CONTENT_COMMIT
    assert evidence["cache_binding_commit"] == "PENDING_POSTCOMMIT_ATTESTATION"
    assert evidence["allowed_files_obeyed"] is True
    assert evidence["changed_files"] == EXPECTED_PATHS
    assert evidence["contains_private_values"] is False
    assert evidence["production_accepted"] is False
    assert evidence["stage_1_status"] == "in_progress"
    assert evidence["phase_1_3_status"] == "not_started"
    assert evidence["push_performed"] is False and evidence["app_install_performed"] is False
    assert evidence["superseded_pair"] == {
        "release_content_commit": SUPERSEDED_RELEASE_CONTENT_COMMIT,
        "cache_binding_commit": SUPERSEDED_CACHE_BINDING_COMMIT,
        "review_findings": {"critical": 0, "important": 4, "minor": 0},
        "attestation_created": False,
    }
    assert evidence["review_findings_before_remediation"] == {"critical": 0, "important": 4, "minor": 0}
    for path, expected_sha256 in evidence["artifact_hashes"].items():
        assert sha256_bytes(repo_bytes(path, candidate)) == expected_sha256, path
    assert any("Phase 1.3" in item for item in evidence["explicitly_not_done"])
    assert any("final Stage 12 human acceptance" in item for item in evidence["explicitly_not_done"])

    changed_file_lines = repo_text(f"{PHASE_DIR}/changed_files.txt", candidate).splitlines()
    assert changed_file_lines == EXPECTED_PATHS
    terminal = repo_text(f"{PHASE_DIR}/terminal.log", candidate)
    for marker in (
        "[RED-001]",
        "[RED-002]",
        "[GREEN-003]",
        "[GREEN-004]",
        "[GREEN-006]",
        "[INDEPENDENT-REVIEW-001]",
        "[REMEDIATION-RED-001]",
        "[REMEDIATION-GREEN-005]",
    ):
        assert marker in terminal
    privacy = repo_text(f"{PHASE_DIR}/privacy_scan.txt", candidate)
    assert "private_value_findings=0" in privacy
    assert "absolute_home_path_findings=0" in privacy
    assert "zip_integrity_scan=PASS" in privacy
    assert "zip_decompressed_member_scan=PASS" in privacy

    privacy_paths = [
        path
        for path in EXPECTED_PATHS
        if path.startswith(f"{PHASE_DIR}/")
        or path.startswith("PFI/scripts/v025/")
        or path.startswith("PFI/tests/test_v025_stage1_cache_policy.py")
        or path.startswith("PFI/web/tests/v025/stage1_cache_policy.test.mjs")
        or path == "PFI/docs/pfi_v025/stage_1/PHASE_1_2_CACHE_GOVERNANCE_IMPLEMENTATION_PLAN.md"
    ]
    absolute_home_marker = b"/Users/" + b"linzezhang"
    for path in privacy_paths:
        if path.endswith(".png"):
            continue
        payload = repo_bytes(path, candidate)
        if path.endswith(".zip"):
            with zipfile.ZipFile(io.BytesIO(payload)) as archive:
                assert archive.testzip() is None, path
                for member in archive.infolist():
                    if member.is_dir():
                        continue
                    assert absolute_home_marker not in archive.read(member), f"{path}:{member.filename}"
            continue
        assert absolute_home_marker not in payload, path
    for path in (
        "PFI/StartPFI.command",
        "PFI/scripts/startPFI.sh",
        "PFI/scripts/pfiReleaseIdentity.sh",
    ):
        source = repo_text(path, candidate)
        assert "PFI_STREAMLIT_CACHE_KEY" in source or "pfi_release_cache_key_init" in source
    for path in ("PFI/StartPFI.command", "PFI/scripts/startPFI.sh"):
        source = repo_text(path, candidate)
        assert "run_streamlit_with_release_cache.py" in source
        assert "PFI_V021_RUNTIME_API_PORT=0" in source
    version_source = repo_text("PFI/web/app/version.js", candidate)
    for token in (
        "disableLegacyServiceWorkers",
        "validateReleaseCachePolicy",
        "installBfcacheRevalidation",
        "event?.persisted",
        "runtime:stale_gate_epoch",
    ):
        assert token in version_source
    wrapper_source = repo_text("PFI/scripts/v025/run_streamlit_with_release_cache.py", candidate)
    assert "cache_data(ttl=ttl_seconds" in wrapper_source
    assert "public, max-age=31536000, immutable" in wrapper_source
    assert "ensure_ephemeral_runtime_api_owner" in wrapper_source
    assert "ensure_v021_runtime_api_server" in wrapper_source

    trace_rows = list(csv.reader(repo_text("PFI/docs/governance/TRACEABILITY_MATRIX.csv", candidate).splitlines()))
    assert all(len(row) == len(trace_rows[0]) for row in trace_rows)
    assert sum("ACC-PFI-V025-S1-P12-CACHE-GOVERNANCE" in row for row in trace_rows) == 4
    for path, token in (
        ("PFI/docs/governance/STATUS.md", "Stage 1 Phase 1.2 Cache Governance Overlay"),
        ("PFI/docs/governance/OWNER_STATUS.md", "Stage 1 Phase 1.2 Cache Governance Overlay"),
        ("PFI/docs/governance/DEVELOPMENT_LEDGER.md", "ITER-20260712-PFI-V025-S1-P12"),
        ("PFI/CHANGELOG.md", "Stage 1 Phase 1.2 Cache Governance"),
    ):
        assert token in repo_text(path, candidate)

    attestation_sha256 = None
    if require_attestation:
        assert candidate is not None
        attestation_sha256 = verify_attestation(candidate, evidence)
    return {
        "status": "PASS",
        "candidate": candidate or "WORKTREE",
        "release_content_commit": RELEASE_CONTENT_COMMIT,
        "changed_path_count": len(EXPECTED_PATHS),
        "frontend_file_count": len(frontend_files),
        "python_expected": "22 passed",
        "node_expected": "23 passed",
        "http_checks": 4,
        "browser_checks": 10,
        "real_bfcache_persisted_observed": False,
        "attestation_sha256": attestation_sha256,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate")
    parser.add_argument(
        "--task-pack",
        type=Path,
        default=Path.home() / "Downloads" / "PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip",
    )
    parser.add_argument(
        "--roadmap",
        type=Path,
        default=Path.home() / "Downloads" / "PFI_v0.2.5_Production_Truth_Human_Workflow_Roadmap.md",
    )
    parser.add_argument("--require-attestation", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = verify(
        candidate_arg=args.candidate,
        task_pack=args.task_pack,
        roadmap=args.roadmap,
        require_attestation=args.require_attestation,
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
