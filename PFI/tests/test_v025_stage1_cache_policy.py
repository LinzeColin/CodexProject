from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import re
import signal
import socket
import subprocess
import sys
import time
from http.server import ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
PFI_ROOT = REPO_ROOT / "PFI"
SRC_ROOT = PFI_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from pfi_v02 import stage_v021_runtime_api as runtime_api  # noqa: E402


WRAPPER_PATH = PFI_ROOT / "scripts" / "v025" / "run_streamlit_with_release_cache.py"
CONTRACT_CLI_PATH = PFI_ROOT / "scripts" / "v025" / "release_cache_contract.py"
STARTERS = (PFI_ROOT / "StartPFI.command", PFI_ROOT / "scripts" / "startPFI.sh")
HEX64 = "a" * 64
AUTH_TOKEN = "stage1-cache-policy-test-token"


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


def _require_callable(module: object, name: str):
    value = getattr(module, name, None)
    assert callable(value), f"S1-P2 requires callable {name}"
    return value


def _load_wrapper():
    assert WRAPPER_PATH.is_file(), "S1-P2-T2 requires the same-process Streamlit wrapper"
    spec = importlib.util.spec_from_file_location("pfi_v025_streamlit_cache_wrapper", WRAPPER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_contract_cli():
    assert CONTRACT_CLI_PATH.is_file(), "S1 whole review requires the release cache contract CLI"
    spec = importlib.util.spec_from_file_location("pfi_v025_release_cache_contract", CONTRACT_CLI_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _status_fixture() -> dict[str, object]:
    return {
        "schema": "PFIV024Stage4ReadModelStatusV1",
        "contract_version": "PFI-V024-STAGE4-PHASE42-READ-MODEL-STATUS",
        "generated_at_utc": "2026-07-11T00:00:00Z",
        "read_model_hash": "1" * 64,
        "source": {
            "status": "ready",
            "evidence_hash": f"sha256:{'2' * 64}",
            "as_of": "2026-06-03",
            "record_count": 10,
            "raw_file_count": 2,
            "date_range": {"start": "2026-01-01", "end": "2026-06-03"},
            "data_root": "/private/old/path",
            "transactions_path": "/private/old/path/transactions.jsonl",
            "manifest_path": "/private/old/path/manifest.json",
        },
        "core_metric_states": [
            {
                "metric_id": "consumption_outflow_cny",
                "status": "ready",
                "value": 123.45,
                "currency": "CNY",
                "record_count": 10,
                "as_of": "2026-06-03",
                "formula_id": "total_consumption_outflow_v1",
                "calculation_state": "calculated",
            }
        ],
        "blocked_metric_ids": ["net_worth_cny"],
        "surface_ids": ["home", "accounts"],
    }


def _dimension_fixture() -> dict[str, str]:
    return {
        "build_id": "pfi-v025-s1p1-20260712.1",
        "git_commit": "b" * 40,
        "frontend_bundle_hash": "c" * 64,
        "backend_build_hash": "d" * 64,
        "data_hash": "e" * 64,
        "parameter_hash": "f" * 64,
        "formula_hash": "0" * 64,
        "fx_snapshot_id": "fx_AUD_CNY_20260628",
        "fx_snapshot_hash": "1" * 64,
        "read_model_hash": "2" * 64,
        "streamlit_version": "1.35.0",
        "requirements_lock_hash": "3" * 64,
    }


def _policy_fixture() -> dict[str, object]:
    dimensions = _dimension_fixture()
    compute_key = _require_callable(runtime_api, "compute_v025_streamlit_cache_key")
    key = compute_key(dimensions)
    return {
        "schema": "PFIV025Stage1ReleaseCachePolicyV1",
        **dimensions,
        "streamlit_cache_key": key,
        "process_cache_key": key,
        "ttl_seconds": 30,
        "cache_mode": "streamlit_cache_data_composite_key_v1",
        "persistent": False,
        "invalidation": list(dimensions),
        "running_backend_hash": dimensions["backend_build_hash"],
        "asset_identity_valid": True,
        "valid": True,
    }


def test_phase12_contract_files_are_declared() -> None:
    assert WRAPPER_PATH.is_file(), WRAPPER_PATH
    assert CONTRACT_CLI_PATH.is_file(), CONTRACT_CLI_PATH


def test_stable_read_model_hash_excludes_volatile_and_private_paths() -> None:
    stable_hash = _require_callable(runtime_api, "stable_v025_read_model_hash")
    first = _status_fixture()
    second = copy.deepcopy(first)
    second["generated_at_utc"] = "2026-07-11T00:00:01Z"
    second["read_model_hash"] = "9" * 64
    second["source"]["data_root"] = "/private/new/path"
    second["source"]["transactions_path"] = "/private/new/path/transactions.jsonl"
    second["source"]["manifest_path"] = "/private/new/path/manifest.json"
    assert stable_hash(first) == stable_hash(second)
    assert re.fullmatch(r"[0-9a-f]{64}", stable_hash(first))

    value_only = copy.deepcopy(second)
    value_only["core_metric_states"][0]["value"] = 124.45
    value_only["core_metric_states"][0]["amount"] = 999999.99
    value_only["core_metric_states"][0]["rate_float"] = 3.14159
    assert stable_hash(first) == stable_hash(value_only)

    semantic_changes = (
        ("source", "evidence_hash", f"sha256:{'3' * 64}"),
        ("source", "record_count", 11),
        ("source", "as_of", "2026-06-04"),
        ("metric", "status", "blocked"),
        ("metric", "formula_id", "total_consumption_outflow_v2"),
    )
    for scope, field, value in semantic_changes:
        changed = copy.deepcopy(second)
        target = changed["source"] if scope == "source" else changed["core_metric_states"][0]
        target[field] = value
        assert stable_hash(first) != stable_hash(changed), (scope, field)


def test_composite_key_changes_for_every_cache_dimension() -> None:
    compute_key = _require_callable(runtime_api, "compute_v025_streamlit_cache_key")
    dimensions = _dimension_fixture()
    baseline = compute_key(dimensions)
    assert re.fullmatch(r"[0-9a-f]{64}", baseline)
    for field in dimensions:
        changed = dict(dimensions)
        changed[field] = f"{changed[field]}-changed"
        assert compute_key(changed) != baseline, field


def test_policy_is_explicit_validated_and_privacy_safe() -> None:
    build_record = _require_callable(runtime_api, "build_v025_release_cache_policy_record")
    dimensions = _dimension_fixture()
    key = _require_callable(runtime_api, "compute_v025_streamlit_cache_key")(dimensions)
    policy = build_record(
        dimensions,
        process_cache_key=key,
        running_backend_hash=dimensions["backend_build_hash"],
        asset_identity_valid=True,
    )
    assert policy["valid"] is True
    assert policy["ttl_seconds"] == 30
    assert policy["persistent"] is False
    assert policy["cache_mode"] == "streamlit_cache_data_composite_key_v1"
    assert set(dimensions).issubset(policy["invalidation"])
    raw = json.dumps(policy, ensure_ascii=False, sort_keys=True)
    for forbidden in ("/Users/", "/private/", "amount", "rate_float", "transactions_path", "data_root"):
        assert forbidden not in raw

    stale = build_record(
        dimensions,
        process_cache_key="9" * 64,
        running_backend_hash=dimensions["backend_build_hash"],
        asset_identity_valid=True,
    )
    assert stale["valid"] is False


def test_runtime_api_release_endpoints_are_private_no_store_and_revalidatable(monkeypatch) -> None:
    manifest = {
        "product": "PFI",
        "version": "v0.2.5",
        "build_id": "pfi-v025-s1p1-20260712.1",
        "git_commit": "b" * 40,
        "frontend_bundle_hash": "c" * 64,
        "backend_build_hash": "d" * 64,
        "generated_at": "2026-07-11T00:00:00Z",
    }
    policy = _policy_fixture()
    manifest_raw = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    manifest_sha256 = hashlib.sha256(manifest_raw).hexdigest()
    monkeypatch.setattr(
        runtime_api,
        "load_v025_release_manifest_record",
        lambda: (dict(manifest), manifest_raw, manifest_sha256),
    )
    monkeypatch.setattr(runtime_api, "build_v025_release_cache_policy", lambda: dict(policy), raising=False)
    monkeypatch.setattr(runtime_api, "V025_RUNNING_BACKEND_SHA256", manifest["backend_build_hash"], raising=False)

    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        runtime_api._handler_factory(None, auth_token=AUTH_TOKEN),
    )
    import threading

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        for path in ("/api/release-manifest", "/api/release-cache-policy"):
            with urlopen(_runtime_request(f"{base}{path}"), timeout=5) as response:
                raw_body = response.read()
                payload = json.loads(raw_body.decode("utf-8"))
                assert payload
                assert response.headers["Cache-Control"] == "no-store, private"
                assert response.headers["ETag"]
                assert response.headers["Last-Modified"]
                assert response.headers["X-PFI-Running-Backend-SHA256"] == manifest["backend_build_hash"]
                if path == "/api/release-manifest":
                    assert raw_body == manifest_raw
                    assert int(response.headers["Content-Length"]) == len(manifest_raw)
                    assert response.headers["X-PFI-Release-Manifest-SHA256"] == manifest_sha256
                    assert response.headers["ETag"] == f'"{manifest_sha256}"'
                etag = response.headers["ETag"]
            request = _runtime_request(f"{base}{path}", headers={"If-None-Match": etag})
            with pytest.raises(HTTPError) as exc_info:
                urlopen(request, timeout=5)
            assert exc_info.value.code == 304

            wrong_etag_with_future_date = _runtime_request(
                f"{base}{path}",
                headers={
                    "If-None-Match": '"not-the-current-entity"',
                    "If-Modified-Since": "Fri, 31 Dec 2099 23:59:59 GMT",
                },
            )
            with urlopen(wrong_etag_with_future_date, timeout=5) as response:
                assert response.status == 200

            weak_list_match = _runtime_request(
                f"{base}{path}",
                headers={"If-None-Match": f'W/"not-current", W/{etag}'},
            )
            with pytest.raises(HTTPError) as exc_info:
                urlopen(weak_list_match, timeout=5)
            assert exc_info.value.code == 304

            wildcard_match = _runtime_request(f"{base}{path}", headers={"If-None-Match": "*"})
            with pytest.raises(HTTPError) as exc_info:
                urlopen(wildcard_match, timeout=5)
            assert exc_info.value.code == 304
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_runtime_api_uses_the_frozen_process_cache_policy_after_data_changes(
    monkeypatch,
) -> None:
    frozen_policy = _policy_fixture()
    monkeypatch.setattr(
        runtime_api,
        "build_v025_release_cache_policy",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("frozen process policy must not be recomputed")
        ),
    )
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        runtime_api._handler_factory(
            None,
            auth_token=AUTH_TOKEN,
            release_cache_policy=frozen_policy,
        ),
    )
    import threading

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with urlopen(
            _runtime_request(
                f"http://127.0.0.1:{server.server_port}/api/release-cache-policy"
            ),
            timeout=5,
        ) as response:
            assert json.loads(response.read().decode("utf-8")) == frozen_policy
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_runtime_api_non_release_routes_keep_original_non_validator_semantics() -> None:
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        runtime_api._handler_factory(None, auth_token=AUTH_TOKEN),
    )
    import threading

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_port}/health"
    try:
        request = _runtime_request(
            url,
            headers={
                "If-None-Match": "*",
                "If-Modified-Since": "Fri, 31 Dec 2099 23:59:59 GMT",
            },
        )
        with urlopen(request, timeout=5) as response:
            assert response.status == 200
            assert response.headers.get("ETag") is None
            assert response.headers.get("Last-Modified") is None
            assert response.headers.get("Cache-Control") is None
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_candidate_runtime_api_keeps_real_read_routes_and_denies_every_write(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PFI_STAGE1_CANDIDATE_MODE", "1")
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        runtime_api._handler_factory(None, auth_token=AUTH_TOKEN),
    )
    import threading

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        expected_empty_reads = {
            "/api/holdings": (("summary", "storage_mode"), "isolated_empty"),
            "/api/read-model-status": (("source", "storage_mode"), "isolated_empty"),
            "/api/trends": (("readModel", "consumption", "has_real_transactions"), False),
        }
        for path, (fields, expected) in expected_empty_reads.items():
            with urlopen(_runtime_request(f"{base}{path}"), timeout=5) as response:
                payload = json.loads(response.read().decode("utf-8"))
                assert response.status == 200
                assert response.headers["Cache-Control"] == "no-store, private"
                assert response.headers["X-PFI-Data-Boundary"] == "isolated-empty-read-only"
                nested = payload
                for field in fields:
                    nested = nested[field]
                assert nested == expected
                assert "/Users/" not in json.dumps(payload, ensure_ascii=False, sort_keys=True)

        for path in ("/api/holdings", "/api/imports/alipay", "/api/not-a-write-route"):
            request = _runtime_request(
                f"{base}{path}",
                data=b"{}",
                method="POST",
                headers={"Content-Type": "application/json"},
            )
            with pytest.raises(HTTPError) as exc_info:
                urlopen(request, timeout=5)
            assert exc_info.value.code == 403
            payload = json.loads(exc_info.value.read().decode("utf-8"))
            assert payload["error"] == "candidate_read_only"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_official_candidate_cli_and_runtime_api_policy_use_the_same_composite_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    contract = _load_contract_cli()
    manifest = runtime_api.load_v025_release_manifest()
    monkeypatch.setenv("PFI_STAGE1_CANDIDATE_MODE", "1")
    monkeypatch.setattr(
        runtime_api,
        "build_v025_release_asset_identity",
        lambda *_args, **_kwargs: {"valid": True},
    )
    monkeypatch.setattr(
        runtime_api,
        "V025_RUNNING_BACKEND_SHA256",
        manifest["backend_build_hash"],
    )

    process_key, cli_policy = contract.build_official_candidate_contract(PFI_ROOT)
    api_policy = runtime_api.build_v025_release_cache_policy(
        PFI_ROOT,
        process_cache_key=process_key,
    )
    assert cli_policy["schema"] == "PFIV025Stage1ReleaseCachePolicyV1"
    assert api_policy["schema"] == "PFIV025Stage1ReleaseCachePolicyV1"
    assert cli_policy["streamlit_cache_key"] == process_key
    assert api_policy["streamlit_cache_key"] == process_key
    assert api_policy["process_cache_key"] == process_key
    assert cli_policy["persistent"] is False
    assert api_policy["valid"] is True


def test_wrapper_classifies_only_hash_named_assets_as_immutable() -> None:
    wrapper = _load_wrapper()
    classify = _require_callable(wrapper, "cache_control_for_static_path")
    assert classify("") == "no-cache, private"
    assert classify("index.html") == "no-cache, private"
    assert classify("static/js/main.7e42f54d.js") == "public, max-age=31536000, immutable"
    assert classify("static/css/main.3aaaea00.css") == "public, max-age=31536000, immutable"
    assert classify("favicon.png") == "no-cache, private"
    assert classify("asset-manifest.json") == "no-cache, private"


def test_wrapper_binds_real_st_cache_data_key_and_ttl() -> None:
    wrapper = _load_wrapper()
    install = _require_callable(wrapper, "install_read_model_cache_adapter")

    class FakeStreamlit:
        observed_ttl = None

        @classmethod
        def cache_data(cls, *, ttl, show_spinner, persist):
            cls.observed_ttl = ttl
            assert show_spinner is False
            assert persist is None

            def decorator(function):
                values = {}

                def cached(*args):
                    if args not in values:
                        values[args] = function(*args)
                    return values[args]

                cached.clear = values.clear
                return cached

            return decorator

    calls: list[tuple[str | None, str | None]] = []

    def original(project_root=None, *, data_root=None):
        calls.append((str(project_root) if project_root else None, str(data_root) if data_root else None))
        return {"call": len(calls)}

    fake_module = SimpleNamespace(build_v024_read_model_status=original)
    adapter = install(
        HEX64,
        ttl_seconds=30,
        streamlit_module=FakeStreamlit,
        read_model_module=fake_module,
        original_builder=original,
    )
    assert fake_module.build_v024_read_model_status is adapter
    assert adapter.__pfi_streamlit_cache_key__ == HEX64
    assert adapter.__pfi_streamlit_cache_ttl_seconds__ == 30
    assert FakeStreamlit.observed_ttl == 30
    assert fake_module.build_v024_read_model_status(PFI_ROOT)["call"] == 1
    assert fake_module.build_v024_read_model_status(PFI_ROOT)["call"] == 1
    assert len(calls) == 1
    adapter.clear()
    assert fake_module.build_v024_read_model_status(PFI_ROOT)["call"] == 2
    assert len(calls) == 2


def test_wrapper_prestarts_only_an_ephemeral_same_process_runtime_api(monkeypatch) -> None:
    wrapper = _load_wrapper()
    ensure_owner = _require_callable(wrapper, "ensure_ephemeral_runtime_api_owner")

    with pytest.raises(RuntimeError, match="must be exactly 0"):
        ensure_owner(environ={}, ensure_server=lambda: "http://127.0.0.1:49152")
    with pytest.raises(RuntimeError, match="must be exactly 0"):
        ensure_owner(
            environ={"PFI_V021_RUNTIME_API_PORT": "8766"},
            ensure_server=lambda: "http://127.0.0.1:49152",
        )
    with pytest.raises(RuntimeError, match="protected or reserved port"):
        ensure_owner(
            environ={"PFI_V021_RUNTIME_API_PORT": "0"},
            ensure_server=lambda: "http://127.0.0.1:8766",
        )
    for reserved_port, reserved_env in (
        (49152, {"PFI_STREAMLIT_PORT": "49152", "PFI_HEARTBEAT_PORT": "49153"}),
        (49153, {"PFI_STREAMLIT_PORT": "49152", "PFI_HEARTBEAT_PORT": "49153"}),
    ):
        with pytest.raises(RuntimeError, match="protected or reserved port"):
            ensure_owner(
                environ={"PFI_V021_RUNTIME_API_PORT": "0", **reserved_env},
                ensure_server=lambda port=reserved_port: f"http://127.0.0.1:{port}",
            )
    with pytest.raises(RuntimeError, match="loopback"):
        ensure_owner(
            environ={"PFI_V021_RUNTIME_API_PORT": "0"},
            ensure_server=lambda: "http://192.0.2.1:49152",
        )
    assert ensure_owner(
        environ={"PFI_V021_RUNTIME_API_PORT": "0"},
        ensure_server=lambda: "http://127.0.0.1:49152",
    ) == "http://127.0.0.1:49152"

    monkeypatch.setenv("PFI_STREAMLIT_CACHE_KEY", HEX64)
    monkeypatch.setenv("PFI_V021_RUNTIME_API_PORT", "0")
    monkeypatch.setattr(wrapper, "force_tornado_server", lambda _args: None)
    monkeypatch.setattr(wrapper, "install_streamlit_cache_headers", lambda: None)
    monkeypatch.setattr(wrapper, "install_read_model_cache_adapter", lambda _key: None)
    monkeypatch.setattr(
        wrapper,
        "ensure_ephemeral_runtime_api_owner",
        lambda: (_ for _ in ()).throw(RuntimeError("prestart failed")),
    )
    assert wrapper.main(["run", "unused.py"]) == 2


def test_adapter_hits_inside_real_streamlit_runtime(tmp_path: Path) -> None:
    import __main__

    wrapper = _load_wrapper()
    import streamlit as st
    from pfi_os.application import read_model_status as read_model_module
    from streamlit.testing.v1 import AppTest

    calls: list[tuple[str | None, str | None]] = []

    def original(project_root=None, *, data_root=None):
        calls.append((str(project_root) if project_root else None, str(data_root) if data_root else None))
        return {"call": len(calls)}

    previous = read_model_module.build_v024_read_model_status
    previous_main_module = sys.modules.get("__main__")
    main_file_was_present = hasattr(__main__, "__file__")
    previous_main_file = getattr(__main__, "__file__", None)
    main_spec_was_present = hasattr(__main__, "__spec__")
    previous_main_spec = getattr(__main__, "__spec__", None)
    try:
        adapter = wrapper.install_read_model_cache_adapter(
            "7" * 64,
            ttl_seconds=30,
            streamlit_module=st,
            read_model_module=read_model_module,
            original_builder=original,
        )
        app_path = tmp_path / "cache_adapter_app.py"
        app_path.write_text(
            "from pfi_os.application.read_model_status import build_v024_read_model_status\n"
            "import streamlit as st\n"
            "first = build_v024_read_model_status('isolated-project', data_root='isolated-data')\n"
            "second = build_v024_read_model_status('isolated-project', data_root='isolated-data')\n"
            "st.write(f\"cache_calls={first['call']}:{second['call']}\")\n",
            encoding="utf-8",
        )
        app = AppTest.from_file(str(app_path), default_timeout=10).run()
        assert not app.exception
        assert len(calls) == 1
        assert any("cache_calls=1:1" in str(item.value) for item in app.markdown)
        adapter.clear()
    finally:
        read_model_module.build_v024_read_model_status = previous
        if previous_main_module is not None:
            sys.modules["__main__"] = previous_main_module
        if main_file_was_present:
            __main__.__file__ = previous_main_file
        elif hasattr(__main__, "__file__"):
            delattr(__main__, "__file__")
        if main_spec_was_present:
            __main__.__spec__ = previous_main_spec
        elif hasattr(__main__, "__spec__"):
            delattr(__main__, "__spec__")


def test_canonical_launchers_bind_cache_key_wrapper_and_ephemeral_runtime_api() -> None:
    identity_source = (PFI_ROOT / "scripts" / "pfiReleaseIdentity.sh").read_text(encoding="utf-8")
    assert "PFI_STREAMLIT_CACHE_KEY" in identity_source
    assert "release_cache_contract.py" in identity_source
    assert "pfi_release_identity_marker_matches" in identity_source
    for path in STARTERS:
        source = path.read_text(encoding="utf-8")
        assert "pfi_release_cache_key_init" in source, path
        assert "run_streamlit_with_release_cache.py" in source, path
        assert "PFI_V021_RUNTIME_API_PORT=0" in source, path
        assert "-m streamlit run src/pfi_os/app/streamlit_app.py" not in source, path


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def _wait_http(url: str, process: subprocess.Popen[bytes], timeout: float = 20.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise AssertionError(f"isolated Streamlit exited early: {process.returncode}")
        try:
            with urlopen(url, timeout=0.5) as response:
                if response.status == 200:
                    return
        except (URLError, TimeoutError):
            time.sleep(0.1)
    raise AssertionError(f"isolated Streamlit was not ready: {url}")


def test_same_process_wrapper_real_http_headers_and_conditional_304(tmp_path: Path) -> None:
    wrapper = _load_wrapper()
    assert callable(getattr(wrapper, "main", None))
    app_path = tmp_path / "minimal_streamlit.py"
    app_path.write_text("import streamlit as st\nst.title('PFI cache header probe')\n", encoding="utf-8")
    port = _free_port()
    env = os.environ.copy()
    env.update(
        {
            "HOME": str(tmp_path / "home"),
            "PYTHONPATH": str(SRC_ROOT),
            "PFI_STREAMLIT_CACHE_KEY": HEX64,
            "PFI_V021_RUNTIME_API_PORT": "0",
            "PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION": "python",
        }
    )
    process = subprocess.Popen(
        [
            sys.executable,
            str(WRAPPER_PATH),
            "run",
            str(app_path),
            "--server.port",
            str(port),
            "--server.address",
            "127.0.0.1",
            "--server.headless",
            "true",
            "--server.fileWatcherType",
            "none",
            "--browser.gatherUsageStats",
            "false",
        ],
        cwd=PFI_ROOT,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    base = f"http://127.0.0.1:{port}"
    try:
        _wait_http(f"{base}/_stcore/health", process)
        with urlopen(f"{base}/", timeout=5) as response:
            html = response.read().decode("utf-8")
            assert response.headers["Cache-Control"] == "no-cache, private"
            assert response.headers["ETag"]
            assert response.headers["Last-Modified"]
            etag = response.headers["ETag"]
        asset_match = re.search(
            r'(?:src|href)="(?:\./|/)?(static/(?:js|css)/[^"?]+\.[0-9a-f]{8,}\.(?:js|css))',
            html,
        )
        assert asset_match, html[:500]
        with urlopen(f"{base}/{asset_match.group(1)}", timeout=5) as response:
            response.read(1)
            assert response.headers["Cache-Control"] == "public, max-age=31536000, immutable"
        request = Request(f"{base}/", headers={"If-None-Match": etag})
        with pytest.raises(HTTPError) as exc_info:
            urlopen(request, timeout=5)
        assert exc_info.value.code == 304
    finally:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=5)
