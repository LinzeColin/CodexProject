from __future__ import annotations

import hashlib
import json
import os
import plistlib
import re
import subprocess
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from jsonschema import Draft202012Validator, FormatChecker
import pytest

from pfi_v02.stage_v021_runtime_api import _handler_factory, load_v025_release_manifest


REPO_ROOT = Path(__file__).resolve().parents[2]
PFI_ROOT = REPO_ROOT / "PFI"
MANIFEST_PATH = PFI_ROOT / "config" / "release_manifest.json"
INDEX_PATH = PFI_ROOT / "web" / "index.html"
VERSION_JS_PATH = PFI_ROOT / "web" / "app" / "version.js"
PLIST_PATH = PFI_ROOT / "macos" / "PFI.app" / "Contents" / "Info.plist"
AUTHORIZATION_PATH = PFI_ROOT / "docs" / "pfi_v025" / "stage_0" / "interim_stage_transition_authorization.json"
EXPECTED_BUILD_ID = "pfi-v025-s1p1-20260712.1"
AUTH_TOKEN = "stage1-release-identity-test-token"
EXPECTED_QUERY_KEYS = (
    "pfi_app_version",
    "pfi_app_build",
    "pfi_build",
    "pfi_commit",
    "pfi_frontend_hash",
    "pfi_backend_hash",
    "pfi_manifest_sha256",
)
IDENTITY_FIELDS = (
    "version",
    "build_id",
    "git_commit",
    "frontend_bundle_hash",
    "backend_build_hash",
)
BACKEND_IDENTITY_PATHS = (
    "PFI/StartPFI.command",
    "PFI/config/data_domains/stage11_distribution_boundaries.json",
    "PFI/config/jobs/v025_dependency_registry.json",
    "PFI/macos/PFI_launcher.c",
    "PFI/scripts/pfiReleaseIdentity.sh",
    "PFI/scripts/pfiRuntime.sh",
    "PFI/scripts/v025/pfi_context_export.py",
    "PFI/scripts/v025/pfi_operational_backup_restore.py",
    "PFI/scripts/v025/release_cache_contract.py",
    "PFI/scripts/v025/run_streamlit_with_release_cache.py",
    "PFI/scripts/v025/scan_stage11_distribution_boundaries.py",
    "PFI/scripts/v025/stage1_phase13_candidate_env.sh",
    "PFI/scripts/v025/stage11_readonly_backup_rehearsal.py",
    "PFI/shared/context/pfi_context_v1.schema.json",
    "PFI/src/pfi_os/app/streamlit_app.py",
    "PFI/src/pfi_os/application/homepage_summary.py",
    "PFI/src/pfi_os/application/jobs/__init__.py",
    "PFI/src/pfi_os/application/jobs/lifecycle.py",
    "PFI/src/pfi_os/application/operational_store.py",
    "PFI/src/pfi_os/application/read_model_status.py",
    "PFI/src/pfi_os/application/supervisor/__init__.py",
    "PFI/src/pfi_os/application/supervisor/runtime_jobs.py",
    "PFI/src/pfi_os/application/use_cases/__init__.py",
    "PFI/src/pfi_os/application/use_cases/holding_settings_persistence.py",
    "PFI/src/pfi_os/application/use_cases/import_review_ledger.py",
    "PFI/src/pfi_os/application/use_cases/metric_lineage_drilldown.py",
    "PFI/src/pfi_os/infrastructure/__init__.py",
    "PFI/src/pfi_os/infrastructure/jobs/__init__.py",
    "PFI/src/pfi_os/infrastructure/jobs/sqlite_store.py",
    "PFI/src/pfi_os/infrastructure/operational_holding_settings_store.py",
    "PFI/src/pfi_os/infrastructure/operational_import_store.py",
    "PFI/src/pfi_os/infrastructure/operational_store_backup.py",
    "PFI/src/pfi_os/infrastructure/operational_store_runtime.py",
    "PFI/src/pfi_os/migrations/v025_stage7_holding_idempotency.sql",
    "PFI/src/pfi_os/migrations/v025_stage7_holding_settings.sql",
    "PFI/src/pfi_os/migrations/v025_stage7_import_review_ledger.sql",
    "PFI/src/pfi_os/observability/__init__.py",
    "PFI/src/pfi_os/observability/job_trace.py",
    "PFI/src/pfi_os/security/__init__.py",
    "PFI/src/pfi_os/security/pfi_context_export.py",
    "PFI/src/pfi_os/system/shutdown_monitor.py",
    "PFI/src/pfi_v02/runtime_diff_v025.py",
    "PFI/src/pfi_v02/stage5_advice_report_alpha.py",
    "PFI/src/pfi_v02/stage6_e2e_stabilization.py",
    "PFI/src/pfi_v02/stage_v021_runtime_api.py",
    "PFI/src/pfi_v02/stage_v024_stage2_entry_consistency.py",
)


FALLBACK_RELEASE_MANIFEST_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": [
        "product",
        "version",
        "build_id",
        "git_commit",
        "frontend_bundle_hash",
        "backend_build_hash",
        "generated_at",
    ],
    "properties": {
        "product": {"const": "PFI"},
        "version": {"pattern": r"^v0\.2\.5(?:[-+].*)?$"},
        "build_id": {"type": "string", "minLength": 1},
        "git_commit": {"type": "string", "minLength": 7},
        "frontend_bundle_hash": {"type": "string"},
        "backend_build_hash": {"type": "string"},
        "app_short_version": {"type": ["string", "null"]},
        "app_build_version": {"type": ["string", "null"]},
        "data_schema_version": {"type": "string"},
        "formula_version": {"type": "string"},
        "parameter_version": {"type": "string"},
        "generated_at": {"type": "string", "format": "date-time"},
    },
    "additionalProperties": False,
}


def _release_schema() -> dict[str, object]:
    configured = os.environ.get("PFI_V025_TASK_PACK")
    task_pack = Path(configured).expanduser() if configured else Path.home() / "Downloads" / "PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip"
    if not task_pack.is_file():
        return FALLBACK_RELEASE_MANIFEST_SCHEMA

    import zipfile

    with zipfile.ZipFile(task_pack) as archive:
        return json.loads(archive.read("PFI_v0.2.5_TaskPack/schemas/release_manifest.schema.json"))


def _load_manifest() -> dict[str, object]:
    assert MANIFEST_PATH.is_file(), "S1-P1-T1 requires PFI/config/release_manifest.json"
    payload = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _embedded_manifest() -> dict[str, object]:
    source = INDEX_PATH.read_text(encoding="utf-8")
    match = re.search(
        r'<script\s+type="application/json"\s+id="pfi-release-manifest">(.*?)</script>',
        source,
        re.DOTALL,
    )
    assert match, "frontend must embed #pfi-release-manifest"
    payload = json.loads(match.group(1))
    assert isinstance(payload, dict)
    return payload


def _canonical_index_bytes() -> bytes:
    source = INDEX_PATH.read_text(encoding="utf-8")
    canonical, count = re.subn(
        r'(<script\s+type="application/json"\s+id="pfi-release-manifest">).*?(</script>)',
        r"\1{}\2",
        source,
        count=1,
        flags=re.DOTALL,
    )
    assert count == 1, "frontend hash requires one canonicalizable manifest block"
    return canonical.encode("utf-8")


def _frontend_bundle_hash() -> str:
    source = INDEX_PATH.read_text(encoding="utf-8")
    script_refs = re.findall(r'<script\s+src="\./([^"?#]+)"', source)
    paths = {
        INDEX_PATH,
        PFI_ROOT / "web" / "styles" / "tokens.css",
        PFI_ROOT / "web" / "styles.css",
        *(PFI_ROOT / "web" / ref for ref in script_refs),
    }
    records: list[bytes] = []
    for path in sorted(paths, key=lambda item: item.relative_to(REPO_ROOT).as_posix()):
        assert path.is_file(), path
        payload = _canonical_index_bytes() if path == INDEX_PATH else path.read_bytes()
        payload_hash = hashlib.sha256(payload).hexdigest()
        relative = path.relative_to(REPO_ROOT).as_posix()
        records.append(f"{relative}\0{payload_hash}\n".encode("utf-8"))
    return hashlib.sha256(b"".join(records)).hexdigest()


def _backend_build_hash() -> str:
    records = []
    for relative in BACKEND_IDENTITY_PATHS:
        payload_hash = hashlib.sha256((REPO_ROOT / relative).read_bytes()).hexdigest()
        records.append(f"{relative}\0{payload_hash}\n".encode("utf-8"))
    return hashlib.sha256(b"".join(records)).hexdigest()


def test_standing_transition_authorization_is_exact_and_not_final_acceptance() -> None:
    payload = json.loads(AUTHORIZATION_PATH.read_text(encoding="utf-8"))
    decision = payload["user_decision"]
    exact_message = "在最终验收前我全部都同意授权，不允许block"
    assert decision["exact_message"] == exact_message
    assert decision["sha256"] == hashlib.sha256(exact_message.encode("utf-8")).hexdigest()
    assert payload["authorized_transitions"] == [f"{stage}->{stage + 1}" for stage in range(12)]
    assert payload["no_reprompt_before_final"] is True
    assert payload["current_transition"] == {
        "stage_0_transition": "authorized",
        "stage_1_entry_authorized": True,
    }
    final = payload["final_acceptance_boundary"]
    assert final["is_human_release_acceptance"] is False
    assert final["human_acceptance_json_created"] is False
    assert final["final_stage_12_human_acceptance_required"] is True
    assert final["production_accepted"] is False


def test_release_manifest_matches_taskpack_schema_and_exact_identity_sources() -> None:
    manifest = _load_manifest()
    validator = Draft202012Validator(_release_schema(), format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(manifest), key=lambda error: list(error.path))
    assert errors == [], [error.message for error in errors]
    assert manifest["product"] == "PFI"
    assert manifest["version"] == "v0.2.5"
    assert manifest["build_id"] == EXPECTED_BUILD_ID
    assert re.fullmatch(r"[0-9a-f]{40}", str(manifest["git_commit"]))
    assert re.fullmatch(r"[0-9a-f]{64}", str(manifest["frontend_bundle_hash"]))
    assert re.fullmatch(r"[0-9a-f]{64}", str(manifest["backend_build_hash"]))
    assert manifest["data_schema_version"] == "PFIV025Stage7MetricLineageV1"
    assert manifest["formula_version"] == "v0.2.3"
    assert manifest["parameter_version"] == "v0.2.2"


def test_release_manifest_hashes_match_declared_payloads() -> None:
    manifest = _load_manifest()
    assert manifest["frontend_bundle_hash"] == _frontend_bundle_hash()
    assert manifest["backend_build_hash"] == _backend_build_hash()


def test_version_plist_and_launchers_consume_the_manifest() -> None:
    manifest = _load_manifest()
    assert (PFI_ROOT / "VERSION").read_text(encoding="utf-8").strip() == manifest["version"]
    with PLIST_PATH.open("rb") as file_obj:
        plist = plistlib.load(file_obj)
    assert plist["CFBundleShortVersionString"] == manifest["app_short_version"]
    assert plist["CFBundleVersion"] == manifest["app_build_version"]

    helper = (PFI_ROOT / "scripts" / "pfiReleaseIdentity.sh").read_text(encoding="utf-8")
    for key in EXPECTED_QUERY_KEYS:
        assert key in helper
    for launcher in (PFI_ROOT / "StartPFI.command", PFI_ROOT / "scripts" / "startPFI.sh"):
        source = launcher.read_text(encoding="utf-8")
        assert "pfiReleaseIdentity.sh" in source
        assert "PFI_VERSION_QUERY" in source

    launcher_c = (PFI_ROOT / "macos" / "PFI_launcher.c").read_text(encoding="utf-8")
    assert "PFI_LAUNCHER_APP_PATH" in launcher_c
    assert "PFI_APP_LAUNCH_IDENTITY_DRY_RUN" in launcher_c
    assert "PFI_APP_LAUNCH_DRY_RUN" in launcher_c


def test_launcher_identity_failure_has_visible_chinese_recovery(tmp_path: Path) -> None:
    helper_path = PFI_ROOT / "scripts" / "pfiReleaseIdentity.sh"
    helper_source = helper_path.read_text(encoding="utf-8")
    command_source = (PFI_ROOT / "StartPFI.command").read_text(encoding="utf-8")
    launcher_source = (PFI_ROOT / "macos" / "PFI_launcher.c").read_text(encoding="utf-8")
    launcher_binary = (PFI_ROOT / "macos" / "PFI.app" / "Contents" / "MacOS" / "PFI").read_bytes()

    assert "pfi_release_show_conflict_dialog" in helper_source
    assert "pfi_release_show_conflict_dialog" in command_source
    assert "if ! pfi_release_identity_init" in command_source
    for phrase in ("版本冲突", "重新启动", "重新安装", "清除缓存"):
        assert phrase in helper_source
        assert phrase in launcher_source
        assert phrase.encode("utf-8") in launcher_binary

    capture_path = tmp_path / "dialog-arguments.txt"
    fake_osascript = tmp_path / "osascript"
    fake_osascript.write_text(
        "#!/bin/zsh\nprintf '%s\\n' \"$@\" > \"$PFI_TEST_DIALOG_CAPTURE\"\n",
        encoding="utf-8",
    )
    fake_osascript.chmod(0o755)
    completed = subprocess.run(
        [
            "/bin/zsh",
            "-f",
            "-c",
            'source "$PFI_TEST_HELPER"\npfi_release_show_conflict_dialog',
        ],
        env={
            **os.environ,
            "PFI_TEST_HELPER": str(helper_path),
            "PFI_OSASCRIPT_BIN": str(fake_osascript),
            "PFI_TEST_DIALOG_CAPTURE": str(capture_path),
        },
        check=False,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 0, completed.stderr
    captured = capture_path.read_text(encoding="utf-8")
    for phrase in ("版本冲突", "重新启动", "重新安装", "清除缓存"):
        assert phrase in captured


def test_native_launcher_preserves_legacy_dry_run_and_reports_actual_app_path() -> None:
    binary = PFI_ROOT / "macos" / "PFI.app" / "Contents" / "MacOS" / "PFI"
    base_env = {**os.environ, "PFI_HOME": str(PFI_ROOT)}
    legacy = subprocess.run(
        [str(binary)],
        env={**base_env, "PFI_APP_LAUNCH_DRY_RUN": "1"},
        check=True,
        text=True,
        capture_output=True,
    )
    assert legacy.stderr == ""
    assert legacy.stdout == (
        f"PFI_APP_LAUNCH: project={PFI_ROOT} command=./StartPFI.command "
        f"command_path={PFI_ROOT / 'StartPFI.command'} mode=spawn-command\n"
    )

    identity = subprocess.run(
        [str(binary)],
        env={**base_env, "PFI_APP_LAUNCH_IDENTITY_DRY_RUN": "1"},
        check=True,
        text=True,
        capture_output=True,
    )
    assert identity.stderr == ""
    assert f"app_path={PFI_ROOT / 'macos' / 'PFI.app'}" in identity.stdout
    assert f"project={PFI_ROOT}" in identity.stdout


def test_runtime_release_manifest_endpoint_returns_exact_manifest_without_db() -> None:
    manifest = _load_manifest()
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        _handler_factory(None, auth_token=AUTH_TOKEN),
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        try:
            request = Request(
                f"http://127.0.0.1:{server.server_port}/api/release-manifest",
                headers={"X-PFI-Runtime-Token": AUTH_TOKEN},
            )
            with urlopen(request, timeout=3) as response:
                status = response.status
                manifest_sha256 = response.headers.get("X-PFI-Release-Manifest-SHA256")
                etag = response.headers.get("ETag")
                raw_body = response.read()
                payload = json.loads(raw_body.decode("utf-8"))
        except HTTPError as error:
            status = error.code
            manifest_sha256 = error.headers.get("X-PFI-Release-Manifest-SHA256")
            etag = error.headers.get("ETag")
            raw_body = error.read()
            payload = json.loads(raw_body.decode("utf-8"))
        assert status == 200, payload
        assert payload == manifest
        assert raw_body == MANIFEST_PATH.read_bytes()
        assert manifest_sha256 == hashlib.sha256(raw_body).hexdigest()
        assert etag == f'"{manifest_sha256}"'
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def test_missing_release_manifest_error_does_not_expose_local_path(tmp_path: Path) -> None:
    missing = tmp_path / "private-owner-directory" / "release_manifest.json"
    with pytest.raises(ValueError) as error:
        load_v025_release_manifest(manifest_path=missing)
    assert str(error.value) == "release manifest is unavailable or invalid"
    assert str(tmp_path) not in str(error.value)


def test_frontend_embedded_manifest_is_the_machine_manifest() -> None:
    assert _embedded_manifest() == _load_manifest()


def test_frontend_gate_is_fail_visible_in_chinese_and_hides_old_shell() -> None:
    index_source = INDEX_PATH.read_text(encoding="utf-8")
    version_source = VERSION_JS_PATH.read_text(encoding="utf-8")
    for phrase in ("版本冲突", "重新启动", "重新安装", "清除缓存"):
        assert phrase in index_source or phrase in version_source
    assert re.search(r'class="app-shell"[^>]*\bhidden\b', index_source)
    assert "releaseManifestApi" in index_source
    assert "fetch" in version_source
    assert "PFI_RELEASE_IDENTITY" in version_source
    assert "PFI_RELEASE_IDENTITY_READY" in version_source
    for field in IDENTITY_FIELDS:
        assert field in version_source
