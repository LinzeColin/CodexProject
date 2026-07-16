from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
PFI_ROOT = REPO_ROOT / "PFI"
SRC_ROOT = PFI_ROOT / "src"

import sys

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from pfi_os.app import streamlit_app  # noqa: E402
from pfi_v02 import stage_v021_runtime_api as runtime_api  # noqa: E402


WRAPPER_PATH = PFI_ROOT / "scripts" / "v025" / "run_streamlit_with_release_cache.py"
STARTER_PATH = PFI_ROOT / "StartPFI.command"
BROWSER_VALIDATOR_PATH = PFI_ROOT / "scripts" / "v025" / "browser_validate_stage1_phase13.mjs"
AUTH_TOKEN = "stage1-whole-review-test-token"


def _runtime_request(
    url: str,
    *,
    data: bytes | None = None,
    method: str | None = None,
    headers: dict[str, str] | None = None,
) -> Request:
    return Request(
        url,
        data=data,
        method=method,
        headers={"X-PFI-Runtime-Token": AUTH_TOKEN, **(headers or {})},
    )


def _load_wrapper():
    spec = importlib.util.spec_from_file_location("pfi_v025_release_wrapper_review", WRAPPER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _runtime_config(markup: str) -> dict[str, object]:
    match = re.search(
        r'<script type="application/json" id="pfi-runtime-config">(.*?)</script>',
        markup,
        flags=re.DOTALL,
    )
    assert match, "official candidate must embed the runtime config"
    payload = json.loads(match.group(1))
    assert isinstance(payload, dict)
    return payload


def test_candidate_launcher_uses_the_official_production_entry() -> None:
    source = STARTER_PATH.read_text(encoding="utf-8")
    assert 'APP_ENTRY="src/pfi_os/app/streamlit_app.py"' in source
    assert 'APP_ENTRY="src/pfi_os/app/isolated_candidate_app.py"' not in source
    assert not (PFI_ROOT / "src" / "pfi_os" / "app" / "isolated_candidate_app.py").exists()


def test_candidate_mode_unconditionally_enables_the_official_shell(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class ForbiddenQueryParams:
        def get(self, *_args: object, **_kwargs: object) -> object:
            raise AssertionError("candidate mode must not inspect the legacy query override")

    class CandidateStreamlit:
        query_params = ForbiddenQueryParams()

    monkeypatch.setenv("PFI_STAGE1_CANDIDATE_MODE", "1")
    monkeypatch.setenv("PFI_UI_V2", "0")
    monkeypatch.setattr(streamlit_app, "st", CandidateStreamlit())

    assert streamlit_app._pfi_ui_v2_enabled() is True


def test_candidate_wrapper_installs_real_cache_and_ephemeral_runtime_api(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    wrapper = _load_wrapper()
    calls: list[tuple[str, str]] = []
    monkeypatch.setattr(
        wrapper,
        "install_read_model_cache_adapter",
        lambda cache_key, **_kwargs: calls.append(("cache", cache_key)),
    )
    monkeypatch.setattr(
        wrapper,
        "ensure_ephemeral_runtime_api_owner",
        lambda: calls.append(("api", "ephemeral")) or "http://127.0.0.1:49152",
    )
    install = getattr(wrapper, "install_release_runtime_guards", None)
    assert callable(install), "whole-stage remediation needs one shared production guard installer"
    isolated_root = Path("/private/tmp") / f"pfi-v025-s1p13-test-{tmp_path.name}"
    runtime_dir = isolated_root / "runtime"
    for relative in ("home", "data", "runtime", "tmp", "cache", "browser-profile", "python-pycache"):
        (isolated_root / relative).mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("PFI_STAGE1_CANDIDATE_MODE", "1")
    monkeypatch.setenv("PFI_STAGE1_ISOLATED_ROOT", str(isolated_root))
    monkeypatch.setenv("HOME", str(isolated_root / "home"))
    monkeypatch.setenv("PFI_DATA_HOME", str(isolated_root / "data"))
    monkeypatch.setenv("PFI_RUNTIME_DIR", str(runtime_dir))
    monkeypatch.setenv("TMPDIR", str(isolated_root / "tmp"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(isolated_root / "cache"))
    monkeypatch.setenv("PFI_BROWSER_PROFILE_DIR", str(isolated_root / "browser-profile"))
    monkeypatch.setenv("PYTHONPYCACHEPREFIX", str(isolated_root / "python-pycache"))
    assert install("a" * 64) == "http://127.0.0.1:49152"
    assert calls == [("cache", "a" * 64), ("api", "ephemeral")]
    assert (runtime_dir / "pfi_runtime_api.env").read_text(encoding="ascii") == (
        "PFI_RUNTIME_API_SCHEMA=PFIV025Stage1OfficialCandidateRuntimeAPIV1\n"
        "PFI_RUNTIME_API_PORT=49152\n"
    )


def test_official_candidate_html_loads_the_full_frontend_and_real_release_apis(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PFI_STAGE1_CANDIDATE_MODE", "1")
    monkeypatch.setattr(
        runtime_api,
        "ensure_v021_runtime_api_server",
        lambda: "http://127.0.0.1:49153",
    )
    monkeypatch.setattr(
        runtime_api,
        "v021_runtime_api_client_token",
        lambda: AUTH_TOKEN,
    )
    status_builder = getattr(streamlit_app, "build_stage1_candidate_read_model_status", None)
    assert callable(status_builder), "candidate needs an explicit empty-data read-model contract"
    status = status_builder()
    markup = streamlit_app._pfi_web_shell_html(
        streamlit_app.build_stage1_candidate_home_summary(),
        read_model_status=status,
    )
    config = _runtime_config(markup)

    assert config["stage1OfficialCandidate"] is True
    assert config["runtimeApiEnabled"] is True
    assert config["releaseManifestApi"] is True
    assert config["releaseCachePolicyApi"] is True
    assert config["readModelStatusApi"] is True
    assert config["apiBaseUrl"] == "http://127.0.0.1:49153"
    assert "/Users/" not in json.dumps(config, ensure_ascii=False)
    assert "release-only" not in markup
    assert "隔离候选验收" not in markup
    assert "市场与研究" in markup

    embedded_sources = set(re.findall(r'data-pfi-source="([^"]+)"', markup))
    frontend_hash, frontend_paths = runtime_api._v025_frontend_bundle_hash(PFI_ROOT)
    expected_sources = {
        str(Path(path).relative_to("PFI").as_posix())
        for path in frontend_paths
        if path != "PFI/web/index.html"
    }
    assert len(frontend_paths) == len(expected_sources) + 1
    assert frontend_paths.count("PFI/web/index.html") == 1
    assert embedded_sources == expected_sources
    assert re.fullmatch(r"[0-9a-f]{64}", frontend_hash)
    assert status["source"]["storage_mode"] == "isolated_empty"
    assert all(metric["value"] is None for metric in status["core_metric_states"])


def test_backend_build_hash_binds_the_actual_official_runtime_sources() -> None:
    builder = getattr(runtime_api, "build_v025_backend_build_identity", None)
    assert callable(builder), "backend identity must cover the running API, wrapper, cache contract and official app"
    identity = builder(PFI_ROOT)
    assert identity["files"] == [
        "PFI/StartPFI.command",
        "PFI/config/jobs/v025_dependency_registry.json",
        "PFI/macos/PFI_launcher.c",
        "PFI/scripts/pfiReleaseIdentity.sh",
        "PFI/scripts/pfiRuntime.sh",
        "PFI/scripts/v025/release_cache_contract.py",
        "PFI/scripts/v025/run_streamlit_with_release_cache.py",
        "PFI/scripts/v025/stage1_phase13_candidate_env.sh",
        "PFI/src/pfi_os/app/streamlit_app.py",
        "PFI/src/pfi_os/application/jobs/__init__.py",
        "PFI/src/pfi_os/application/jobs/lifecycle.py",
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
            "PFI/src/pfi_os/migrations/v025_stage7_holding_idempotency.sql",
            "PFI/src/pfi_os/migrations/v025_stage7_holding_settings.sql",
            "PFI/src/pfi_os/migrations/v025_stage7_import_review_ledger.sql",
            "PFI/src/pfi_os/observability/__init__.py",
            "PFI/src/pfi_os/observability/job_trace.py",
        "PFI/src/pfi_os/system/shutdown_monitor.py",
        "PFI/src/pfi_v02/runtime_diff_v025.py",
        "PFI/src/pfi_v02/stage_v021_runtime_api.py",
        "PFI/src/pfi_v02/stage_v024_stage2_entry_consistency.py",
    ]
    records = []
    for relative in identity["files"]:
        payload_hash = hashlib.sha256((REPO_ROOT / relative).read_bytes()).hexdigest()
        records.append(f"{relative}\0{payload_hash}\n".encode("utf-8"))
    assert identity["sha256"] == hashlib.sha256(b"".join(records)).hexdigest()
    manifest = json.loads((PFI_ROOT / "config" / "release_manifest.json").read_text(encoding="utf-8"))
    assert manifest["backend_build_hash"] == identity["sha256"]

    node = shutil.which("node")
    assert node, "Node.js is required to cross-check the browser-side release identity"
    script = f"""
import {{ __test }} from {json.dumps(BROWSER_VALIDATOR_PATH.as_uri())};
const identity = await __test.computeReleaseSourceIdentity({json.dumps(str(PFI_ROOT))});
process.stdout.write(JSON.stringify(identity.backend));
"""
    completed = subprocess.run(
        [node, "--input-type=module", "--eval", script],
        check=True,
        capture_output=True,
        text=True,
    )
    browser_identity = json.loads(completed.stdout)
    assert [record["path"] for record in browser_identity["files"]] == identity["files"]
    assert browser_identity["file_count"] == identity["file_count"]
    assert browser_identity["sha256"] == identity["sha256"]
    assert [record["sha256"] for record in browser_identity["files"]] == [
        record.decode("utf-8").split("\0", 1)[1].rstrip("\n") for record in records
    ]


def test_candidate_runtime_api_is_real_but_read_only(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("PFI_STAGE1_CANDIDATE_MODE", "1")
    data_home = tmp_path / "isolated-data"
    data_home.mkdir()
    monkeypatch.setenv("PFI_DATA_HOME", str(data_home))
    manifest = json.loads((PFI_ROOT / "config" / "release_manifest.json").read_text(encoding="utf-8"))
    manifest_raw = json.dumps(manifest, ensure_ascii=False).encode("utf-8")
    manifest_sha256 = hashlib.sha256(manifest_raw).hexdigest()
    monkeypatch.setattr(
        runtime_api,
        "load_v025_release_manifest_record",
        lambda: (dict(manifest), manifest_raw, manifest_sha256),
    )
    monkeypatch.setattr(
        runtime_api,
        "build_v025_release_cache_policy",
        lambda: {
            "schema": "PFIV025Stage1ReleaseCachePolicyV1",
            "valid": True,
            "running_backend_hash": manifest["backend_build_hash"],
        },
    )
    monkeypatch.setattr(
        runtime_api,
        "V025_RUNNING_BACKEND_SHA256",
        manifest["backend_build_hash"],
    )
    def forbidden_canonical_read(*_args, **_kwargs):
        raise AssertionError("candidate attempted a canonical data read")

    for name in (
        "load_v021_holdings_payload",
        "build_v021_holdings_sync_read_model",
        "build_v021_holdings_report",
        "build_v021_operational_trends",
        "_real_alipay_consumption_model",
    ):
        monkeypatch.setattr(runtime_api, name, forbidden_canonical_read)
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        runtime_api._handler_factory(None, auth_token=AUTH_TOKEN),
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        for path in ("/health", "/api/release-manifest", "/api/release-cache-policy"):
            with urlopen(_runtime_request(f"{base}{path}"), timeout=5) as response:
                assert response.status == 200
        with urlopen(_runtime_request(f"{base}/api/holdings"), timeout=5) as response:
            assert response.status == 200
            payload = json.loads(response.read().decode("utf-8"))
            assert payload["rows"] == []
            assert payload["summary"]["storage_mode"] == "isolated_empty"
            assert response.headers["X-PFI-Data-Boundary"] == "isolated-empty-read-only"
        with urlopen(_runtime_request(f"{base}/api/trends"), timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
            assert payload["readModel"]["consumption"]["has_real_transactions"] is False
            assert "MetaDatabase" not in json.dumps(payload, ensure_ascii=False)
        with urlopen(_runtime_request(f"{base}/api/read-model-status"), timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
            assert all(metric["value"] is None for metric in payload["core_metric_states"])
            assert response.headers["X-PFI-Read-Model-SHA256"] == payload["read_model_hash"]
        assert list(data_home.iterdir()) == []
        request = _runtime_request(
            f"{base}/api/holdings",
            data=b"{}",
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with pytest.raises(HTTPError) as post_error:
            urlopen(request, timeout=5)
        assert post_error.value.code == 403
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_browser_evidence_cannot_self_attest_manifest_values() -> None:
    source = BROWSER_VALIDATOR_PATH.read_text(encoding="utf-8")
    forbidden_shortcuts = (
        'running_backend_sha256_header: manifest.backend_build_hash',
        'runtime_api: "disabled"',
        'release_manifest_api: "disabled"',
        'candidateShell === "release_only"',
    )
    for shortcut in forbidden_shortcuts:
        assert shortcut not in source
    for required in (
        "X-PFI-Running-Backend-SHA256",
        "/api/release-manifest",
        "/api/release-cache-policy",
        "/api/read-model-status",
        "Accessibility.getFullAXTree",
        "frontend_source_hash",
    ):
        assert required in source
