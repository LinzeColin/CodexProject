#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import plistlib
import re
import subprocess
import sys
import threading
import zipfile
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from jsonschema import Draft202012Validator, FormatChecker


REPO_ROOT = Path(__file__).resolve().parents[3]
PFI_ROOT = REPO_ROOT / "PFI"
PHASE_BASE = "9380fdf4a500f48a2b15859044ab7926b4924391"
RELEASE_CONTENT_COMMIT = "a9592b8ce457492fd0e6817f74388f146ca657c6"
ROADMAP_SHA256 = "fc2f406eef45d9a09f852aad1a2234b2c37547f8ae9c002d6230c54f7ca1071b"
TASK_PACK_SHA256 = "591c839992963a631e079498ec98f6e83a5686ead4ce4ea2c8aea39ab3346dd2"
RELEASE_SCHEMA_SHA256 = "5fdfa06d0d72580c5b497a62882e8f31a0e4d3b878902c90cb7901ee65d67a7f"
PHASE_DIR = "PFI/reports/pfi_v025/stage_1/phase_1_1"
EXPECTED_PATHS = sorted(
    [
        "PFI/CHANGELOG.md",
        "PFI/StartPFI.command",
        "PFI/VERSION",
        "PFI/config/release_manifest.json",
        "PFI/docs/governance/DEVELOPMENT_LEDGER.md",
        "PFI/docs/governance/OWNER_STATUS.md",
        "PFI/docs/governance/STATUS.md",
        "PFI/docs/governance/TRACEABILITY_MATRIX.csv",
        "PFI/docs/governance/VERSION_MATRIX.yaml",
        "PFI/docs/governance/delivery_tasks.yaml",
        "PFI/docs/governance/development_events.jsonl",
        "PFI/docs/pfi_v025/stage_0/interim_stage_transition_authorization.json",
        "PFI/docs/pfi_v025/stage_1/PHASE_1_1_RELEASE_IDENTITY_IMPLEMENTATION_PLAN.md",
        "PFI/macos/PFI.app/Contents/Info.plist",
        "PFI/macos/PFI.app/Contents/MacOS/PFI",
        "PFI/macos/PFI.app/Contents/_CodeSignature/CodeResources",
        "PFI/macos/PFI_launcher.c",
        f"{PHASE_DIR}/app_info_plist.json",
        f"{PHASE_DIR}/asset_hashes.json",
        f"{PHASE_DIR}/backend_manifest_response.json",
        f"{PHASE_DIR}/browser_validation.json",
        f"{PHASE_DIR}/changed_files.txt",
        f"{PHASE_DIR}/evidence.json",
        f"{PHASE_DIR}/identity_matrix.json",
        f"{PHASE_DIR}/mismatch_chinese_error.png",
        f"{PHASE_DIR}/privacy_scan.txt",
        f"{PHASE_DIR}/release_manifest_schema_validation.json",
        f"{PHASE_DIR}/risk_and_rollback.md",
        f"{PHASE_DIR}/terminal.log",
        "PFI/scripts/pfiReleaseIdentity.sh",
        "PFI/scripts/startPFI.sh",
        "PFI/scripts/v025/verify_stage1_phase11.py",
        "PFI/src/pfi_v02/stage_v021_runtime_api.py",
        "PFI/tests/test_v025_stage1_release_identity.py",
        "PFI/web/app/version.js",
        "PFI/web/index.html",
        "PFI/web/tests/v025/stage1_release_identity.test.mjs",
    ]
)
MANIFEST_FIELDS = (
    "product",
    "version",
    "build_id",
    "git_commit",
    "frontend_bundle_hash",
    "backend_build_hash",
    "app_short_version",
    "app_build_version",
    "data_schema_version",
    "formula_version",
    "parameter_version",
    "generated_at",
)


def run(*args: str, check: bool = True, env: dict[str, str] | None = None) -> bytes:
    completed = subprocess.run(
        args,
        cwd=REPO_ROOT,
        env=env,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and completed.returncode != 0:
        raise AssertionError(
            f"command failed ({completed.returncode}): {' '.join(args)}\n"
            f"stdout={completed.stdout.decode(errors='replace')}\n"
            f"stderr={completed.stderr.decode(errors='replace')}"
        )
    return completed.stdout


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def repo_bytes(ref: str, candidate: str | None) -> bytes:
    if candidate:
        return run("git", "show", f"{candidate}:{ref}")
    return (REPO_ROOT / ref).read_bytes()


def repo_text(ref: str, candidate: str | None) -> str:
    return repo_bytes(ref, candidate).decode("utf-8")


def repo_json(ref: str, candidate: str | None) -> dict[str, Any]:
    payload = json.loads(repo_text(ref, candidate))
    assert isinstance(payload, dict), ref
    return payload


def changed_paths(candidate: str | None) -> list[str]:
    if candidate:
        output = run("git", "diff", "--name-only", PHASE_BASE, candidate).decode()
        return sorted(filter(None, output.splitlines()))
    tracked = run("git", "diff", "--name-only", PHASE_BASE).decode().splitlines()
    untracked = run("git", "ls-files", "--others", "--exclude-standard", "PFI").decode().splitlines()
    return sorted(set(filter(None, [*tracked, *untracked])))


def frontend_hash(candidate: str | None) -> tuple[str, dict[str, str]]:
    index_ref = "PFI/web/index.html"
    source = repo_text(index_ref, candidate)
    canonical, count = re.subn(
        r'(<script\s+type="application/json"\s+id="pfi-release-manifest">).*?(</script>)',
        r"\1{}\2",
        source,
        count=1,
        flags=re.DOTALL,
    )
    assert count == 1
    refs = re.findall(r'<script\s+src="\./([^"?#]+)"', source)
    paths = {
        index_ref,
        "PFI/web/styles/tokens.css",
        "PFI/web/styles.css",
        *(f"PFI/web/{ref}" for ref in refs),
    }
    hashes: dict[str, str] = {}
    records: list[bytes] = []
    for ref in sorted(paths):
        payload = canonical.encode("utf-8") if ref == index_ref else repo_bytes(ref, candidate)
        digest = sha256_bytes(payload)
        hashes[ref] = digest
        records.append(f"{ref}\0{digest}\n".encode("utf-8"))
    return sha256_bytes(b"".join(records)), hashes


def embedded_manifest(candidate: str | None) -> dict[str, Any]:
    source = repo_text("PFI/web/index.html", candidate)
    match = re.search(
        r'<script\s+type="application/json"\s+id="pfi-release-manifest">(.*?)</script>',
        source,
        re.DOTALL,
    )
    assert match
    payload = json.loads(match.group(1))
    assert isinstance(payload, dict)
    return payload


def schema_payloads(task_pack: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    with zipfile.ZipFile(task_pack) as archive:
        release_raw = archive.read("PFI_v0.2.5_TaskPack/schemas/release_manifest.schema.json")
        evidence_raw = archive.read("PFI_v0.2.5_TaskPack/schemas/evidence_pack.schema.json")
    assert sha256_bytes(release_raw) == RELEASE_SCHEMA_SHA256
    return json.loads(release_raw), json.loads(evidence_raw)


def verify_endpoint(manifest: dict[str, Any], manifest_sha256: str) -> None:
    sys.path.insert(0, str(PFI_ROOT / "src"))
    try:
        from pfi_v02.stage_v021_runtime_api import _handler_factory

        auth_token = "stage1-phase11-verifier-token"
        server = ThreadingHTTPServer(
            ("127.0.0.1", 0),
            _handler_factory(None, auth_token=auth_token),
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            try:
                request = Request(
                    f"http://127.0.0.1:{server.server_port}/api/release-manifest",
                    headers={"X-PFI-Runtime-Token": auth_token},
                )
                with urlopen(request, timeout=3) as response:
                    status = response.status
                    response_manifest_sha256 = response.headers.get(
                        "X-PFI-Release-Manifest-SHA256"
                    )
                    payload = json.loads(response.read().decode("utf-8"))
            except HTTPError as error:
                status = error.code
                response_manifest_sha256 = error.headers.get(
                    "X-PFI-Release-Manifest-SHA256"
                )
                payload = json.loads(error.read().decode("utf-8"))
            assert status == 200, payload
            assert payload == manifest
            assert response_manifest_sha256 == manifest_sha256
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)
    finally:
        sys.path.pop(0)


def verify_launcher() -> None:
    binary = PFI_ROOT / "macos" / "PFI.app" / "Contents" / "MacOS" / "PFI"
    env = {**os.environ, "PFI_HOME": str(PFI_ROOT), "PFI_APP_LAUNCH_DRY_RUN": "1"}
    legacy = run(str(binary), env=env).decode()
    assert legacy == (
        f"PFI_APP_LAUNCH: project={PFI_ROOT} command=./StartPFI.command "
        f"command_path={PFI_ROOT / 'StartPFI.command'} mode=spawn-command\n"
    )
    env.pop("PFI_APP_LAUNCH_DRY_RUN")
    env["PFI_APP_LAUNCH_IDENTITY_DRY_RUN"] = "1"
    identity = run(str(binary), env=env).decode()
    assert f"app_path={PFI_ROOT / 'macos' / 'PFI.app'}" in identity
    run("codesign", "--verify", "--strict", "--verbose=2", "PFI/macos/PFI.app")


def added_text(candidate: str | None) -> str:
    args = ["git", "diff", "--no-ext-diff", "--unified=0", PHASE_BASE]
    if candidate:
        args.append(candidate)
    diff = run(*args).decode("utf-8", errors="replace")
    lines = [line[1:] for line in diff.splitlines() if line.startswith("+") and not line.startswith("+++")]
    if not candidate:
        for ref in run("git", "ls-files", "--others", "--exclude-standard", "PFI").decode().splitlines():
            path = REPO_ROOT / ref
            if path.suffix.lower() in {".png", ".zip"} or "/MacOS/" in ref:
                continue
            try:
                lines.append(path.read_text(encoding="utf-8"))
            except UnicodeDecodeError:
                continue
    return "\n".join(lines)


def verify_privacy(candidate: str | None) -> int:
    text = added_text(candidate)
    absolute_home_marker = "/" + "Users" + "/"
    patterns = {
        "absolute_home": re.escape(absolute_home_marker),
        "private_key": r"BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY",
        "aws_key": r"AKIA[0-9A-Z]{16}",
        "openai_key": r"\bsk-[A-Za-z0-9_-]{20,}",
    }
    findings = {name: len(re.findall(pattern, text)) for name, pattern in patterns.items()}
    assert sum(findings.values()) == 0, findings
    return len(text.splitlines())


def verify_attestation(candidate: str, evidence: dict[str, Any]) -> str:
    common_dir = Path(run("git", "rev-parse", "--git-common-dir").decode().strip()).resolve()
    ref = (
        common_dir
        / "codex-review"
        / "pfi-v025"
        / "stage_1"
        / "phase_1_1"
        / candidate
        / "phase_1_1_attestation.json"
    )
    payload = json.loads(ref.read_text(encoding="utf-8"))
    assert payload["identity_binding_commit"] == candidate
    assert payload["release_content_commit"] == RELEASE_CONTENT_COMMIT
    assert payload["manifest_sha256"] == sha256_bytes(repo_bytes("PFI/config/release_manifest.json", candidate))
    assert payload["evidence_sha256"] == sha256_bytes(repo_bytes(f"{PHASE_DIR}/evidence.json", candidate))
    assert payload["changed_files"] == EXPECTED_PATHS
    assert payload["review_findings_after_remediation"] == {"critical": 0, "important": 0, "minor": 0}
    assert payload["push_performed"] is False
    assert payload["app_install_performed"] is False
    assert payload["final_human_acceptance"] is False
    assert payload["verifier_result"] == "PASS"
    return sha256_bytes(ref.read_bytes())


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
    with zipfile.ZipFile(task_pack) as archive:
        assert archive.testzip() is None
    release_schema, evidence_schema = schema_payloads(task_pack)

    actual_paths = changed_paths(candidate)
    assert actual_paths == EXPECTED_PATHS, (EXPECTED_PATHS, actual_paths)

    manifest = repo_json("PFI/config/release_manifest.json", candidate)
    Draft202012Validator(release_schema, format_checker=FormatChecker()).validate(manifest)
    assert list(manifest) == list(MANIFEST_FIELDS)
    assert manifest["version"] == "v0.2.5"
    assert manifest["build_id"] == "pfi-v025-s1p1-20260712.1"
    assert manifest["git_commit"] == RELEASE_CONTENT_COMMIT
    assert re.fullmatch(r"[0-9a-f]{64}", manifest["frontend_bundle_hash"])
    assert re.fullmatch(r"[0-9a-f]{64}", manifest["backend_build_hash"])
    assert manifest["data_schema_version"] == "PFIV021HoldingsPersistenceV1"
    assert manifest["formula_version"] == "v0.2.3"
    assert manifest["parameter_version"] == "v0.2.2"

    computed_frontend, frontend_files = frontend_hash(candidate)
    assert computed_frontend == manifest["frontend_bundle_hash"]
    assert sha256_bytes(repo_bytes("PFI/src/pfi_v02/stage_v021_runtime_api.py", candidate)) == manifest[
        "backend_build_hash"
    ]
    assert embedded_manifest(candidate) == manifest
    assert repo_text("PFI/VERSION", candidate).strip() == manifest["version"]
    plist = plistlib.loads(repo_bytes("PFI/macos/PFI.app/Contents/Info.plist", candidate))
    assert plist["CFBundleShortVersionString"] == manifest["app_short_version"]
    assert plist["CFBundleVersion"] == manifest["app_build_version"]
    app_info = repo_json(f"{PHASE_DIR}/app_info_plist.json", candidate)
    assert app_info["CFBundleIdentifier"] == plist["CFBundleIdentifier"]
    assert app_info["CFBundleShortVersionString"] == plist["CFBundleShortVersionString"]
    assert app_info["CFBundleVersion"] == plist["CFBundleVersion"]
    assert app_info["plist_sha256"] == sha256_bytes(
        repo_bytes("PFI/macos/PFI.app/Contents/Info.plist", candidate)
    )
    assert app_info["launcher_binary_sha256"] == sha256_bytes(
        repo_bytes("PFI/macos/PFI.app/Contents/MacOS/PFI", candidate)
    )
    assert app_info["code_resources_sha256"] == sha256_bytes(
        repo_bytes("PFI/macos/PFI.app/Contents/_CodeSignature/CodeResources", candidate)
    )
    assert app_info["codesign"] == {
        "kind": "adhoc",
        "identifier": "com.linze.pfi.launcher.binary",
        "strict_verify": "pass",
    }
    assert app_info["installed_bundle_checked"] is False
    assert app_info["result"] == "pass_repository_template"

    helper = repo_text("PFI/scripts/pfiReleaseIdentity.sh", candidate)
    for key in (
        "pfi_app_version",
        "pfi_app_build",
        "pfi_build",
        "pfi_commit",
        "pfi_frontend_hash",
        "pfi_backend_hash",
        "pfi_manifest_sha256",
    ):
        assert key in helper
    for ref in ("PFI/StartPFI.command", "PFI/scripts/startPFI.sh"):
        assert "pfiReleaseIdentity.sh" in repo_text(ref, candidate)
    version_source = repo_text("PFI/web/app/version.js", candidate)
    index_source = repo_text("PFI/web/index.html", candidate)
    for phrase in ("版本冲突", "重新启动", "重新安装", "清除缓存"):
        assert phrase in version_source or phrase in index_source
    assert "window.PFI_RELEASE_IDENTITY_READY" in version_source
    assert "normalizeRuntimeConfig(window.document, embeddedManifest)" in version_source
    assert 'response.headers?.get?.("X-PFI-Release-Manifest-SHA256")' in version_source
    assert "value !== backendManifestSha256" in version_source
    assert "resolveLauncherSearch" in version_source
    assert "windowRef.parent.location?.search" in version_source
    assert "documentRef?.referrer" in version_source
    assert 'validateManifest("embedded", embedded, staticIssues)' in version_source
    assert re.search(r'class="app-shell"[^>]*\bhidden\b', index_source)

    runtime_source = repo_text("PFI/src/pfi_v02/stage_v021_runtime_api.py", candidate)
    assert "release manifest is unavailable or invalid" in runtime_source
    assert 'extra_headers={"X-PFI-Release-Manifest-SHA256": manifest_sha256}' in runtime_source

    helper_source = repo_text("PFI/scripts/pfiReleaseIdentity.sh", candidate)
    command_source = repo_text("PFI/StartPFI.command", candidate)
    launcher_source = repo_text("PFI/macos/PFI_launcher.c", candidate)
    assert "pfi_release_show_conflict_dialog" in helper_source
    assert "if ! pfi_release_identity_init" in command_source
    assert "pfi_release_show_conflict_dialog" in command_source
    for phrase in ("版本冲突", "重新启动", "重新安装", "清除缓存"):
        assert phrase in helper_source
        assert phrase in launcher_source

    authorization = repo_json(
        "PFI/docs/pfi_v025/stage_0/interim_stage_transition_authorization.json", candidate
    )
    exact_message = "在最终验收前我全部都同意授权，不允许block"
    assert authorization["user_decision"]["exact_message"] == exact_message
    assert authorization["user_decision"]["sha256"] == sha256_bytes(exact_message.encode())
    assert authorization["authorized_transitions"] == [f"{stage}->{stage + 1}" for stage in range(12)]
    assert authorization["final_acceptance_boundary"]["is_human_release_acceptance"] is False
    assert authorization["final_acceptance_boundary"]["final_stage_12_human_acceptance_required"] is True

    evidence = repo_json(f"{PHASE_DIR}/evidence.json", candidate)
    Draft202012Validator(evidence_schema, format_checker=FormatChecker()).validate(evidence)
    assert evidence["status"] == "candidate_pass"
    assert evidence["git_commit"] == RELEASE_CONTENT_COMMIT
    assert evidence["release_content_commit"] == RELEASE_CONTENT_COMMIT
    assert evidence["identity_binding_commit"] == "PENDING_POSTCOMMIT_ATTESTATION"
    assert evidence["changed_files"] == EXPECTED_PATHS
    assert evidence["contains_private_values"] is False
    assert evidence["production_accepted"] is False
    assert evidence["final_human_acceptance"] is False
    assert evidence["stage_1_status"] == "in_progress"
    assert evidence["stage_2_status"] == "not_started"

    changed_file_rows = repo_text(f"{PHASE_DIR}/changed_files.txt", candidate).splitlines()
    assert changed_file_rows == EXPECTED_PATHS
    for ref, expected in evidence["artifact_hashes"].items():
        assert ref not in {f"{PHASE_DIR}/evidence.json", f"{PHASE_DIR}/changed_files.txt"}
        assert sha256_bytes(repo_bytes(ref, candidate)) == expected, ref

    assets = repo_json(f"{PHASE_DIR}/asset_hashes.json", candidate)
    assert assets["frontend_bundle_hash"] == manifest["frontend_bundle_hash"]
    assert assets["frontend_files"] == frontend_files
    assert assets["backend_build_hash"] == manifest["backend_build_hash"]
    backend_response = repo_json(f"{PHASE_DIR}/backend_manifest_response.json", candidate)
    assert backend_response["response"] == manifest
    manifest_sha256 = sha256_bytes(repo_bytes("PFI/config/release_manifest.json", candidate))
    assert backend_response["response_headers"] == {
        "X-PFI-Release-Manifest-SHA256": manifest_sha256
    }
    assert backend_response["database_accessed"] is False
    identity_matrix = repo_json(f"{PHASE_DIR}/identity_matrix.json", candidate)
    assert identity_matrix["identity"]["git_commit"] == RELEASE_CONTENT_COMMIT
    assert identity_matrix["result"] == "pass"
    browser = repo_json(f"{PHASE_DIR}/browser_validation.json", candidate)
    screenshot_ref = browser["screenshot"]["ref"]
    screenshot = repo_bytes(screenshot_ref, candidate)
    assert screenshot.startswith(b"\x89PNG\r\n\x1a\n")
    assert len(screenshot) == browser["screenshot"]["bytes"] > 10_000
    assert sha256_bytes(screenshot) == browser["screenshot"]["sha256"]
    assert browser["observed_title_zh"] == "版本冲突"
    assert browser["old_shell_visible"] is False
    assert browser["streamlit_srcdoc_topology"] == {
        "evidence": "Node VM tests model empty iframe-local search with launcher query on parent or document.referrer",
        "complete_parent_query": "pass_app_launcher",
        "partial_or_tampered_parent_query": "pass_blocked",
        "inaccessible_parent_referrer_fallback": "pass_app_launcher",
        "conflicting_sources": "pass_blocked",
        "real_live_streamlit_trace": "deferred_to_phase_1_3",
    }

    terminal = repo_text(f"{PHASE_DIR}/terminal.log", candidate)
    for required in (
        "PYTHON_RED",
        "NODE_RED",
        "PYTHON_GREEN",
        "NODE_GREEN",
        "REMEDIATION_RED",
        "REMEDIATION_GREEN",
        "IFRAME_REMEDIATION_RED",
        "VISIBLE_ERROR_REMEDIATION_RED",
        "POST_REVIEW_REMEDIATION_GREEN",
        "10 passed",
        "tests 15",
        "NO_PUSH_NO_INSTALL_NO_DATA_DB_MUTATION",
    ):
        assert required in terminal
    assert "PRIVACY_SCAN=PASS" in repo_text(f"{PHASE_DIR}/privacy_scan.txt", candidate)

    verify_endpoint(manifest, manifest_sha256)
    verify_launcher()
    privacy_lines = verify_privacy(candidate)
    attestation_sha = None
    if require_attestation:
        assert candidate is not None
        attestation_sha = verify_attestation(candidate, evidence)

    return {
        "result": "PASS",
        "candidate": candidate or "working_tree",
        "exact_paths": len(actual_paths),
        "release_content_commit": RELEASE_CONTENT_COMMIT,
        "identity_binding_commit": candidate or "PENDING_POSTCOMMIT_ATTESTATION",
        "frontend_file_count": len(frontend_files),
        "frontend_bundle_hash": manifest["frontend_bundle_hash"],
        "backend_build_hash": manifest["backend_build_hash"],
        "manifest_sha256": sha256_bytes(repo_bytes("PFI/config/release_manifest.json", candidate)),
        "evidence_sha256": sha256_bytes(repo_bytes(f"{PHASE_DIR}/evidence.json", candidate)),
        "privacy_added_lines_scanned": privacy_lines,
        "attestation_sha256": attestation_sha,
        "human_acceptance": "absent",
        "stage_1": "in_progress",
        "stage_2": "not_started",
        "push": "not_performed",
        "app_install": "not_performed",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", help="Committed Phase 1.1 identity-binding SHA")
    parser.add_argument(
        "--task-pack",
        type=Path,
        default=Path(os.environ.get("PFI_V025_TASK_PACK", "~/Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip")).expanduser(),
    )
    parser.add_argument(
        "--roadmap",
        type=Path,
        default=Path(os.environ.get("PFI_V025_ROADMAP", "~/Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_Roadmap.md")).expanduser(),
    )
    parser.add_argument("--require-attestation", action="store_true")
    args = parser.parse_args()
    result = verify(
        candidate_arg=args.candidate,
        task_pack=args.task_pack,
        roadmap=args.roadmap,
        require_attestation=args.require_attestation,
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
