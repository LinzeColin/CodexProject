from __future__ import annotations

import hashlib
import json
import threading
import time
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from pfi_v02 import stage_v021_runtime_api as runtime_api


AUTH_TOKEN = "stage10-runtime-jobs-test-token"


def _hash(label: str) -> str:
    return hashlib.sha256(f"stage10-api:{label}".encode()).hexdigest()


def _policy() -> dict[str, object]:
    return {
        "dependency_registry_sha256": _hash("registry"),
        "data_hash": _hash("data"),
        "formula_hash": _hash("formula"),
        "parameter_hash": _hash("parameter"),
        "read_model_hash": _hash("read-model"),
        "streamlit_cache_key": _hash("cache"),
        "dependency_snapshot_valid": True,
        "ordinary_run_network_allowed": False,
        "no_diff_network_allowed": False,
    }


def _request(
    base_url: str,
    path: str,
    *,
    method: str = "GET",
    payload: dict[str, object] | None = None,
    token: str = AUTH_TOKEN,
) -> tuple[int, dict[str, object]]:
    body = json.dumps(payload).encode() if payload is not None else None
    request = Request(
        base_url + path,
        data=body,
        method=method,
        headers={
            "Content-Type": "application/json",
            "X-PFI-Runtime-Token": token,
        },
    )
    try:
        with urlopen(request, timeout=5) as response:
            return response.status, json.loads(response.read().decode())
    except HTTPError as exc:
        return exc.code, json.loads(exc.read().decode())


def test_runtime_jobs_api_is_authenticated_durable_and_db_ui_ready(
    tmp_path: Path,
    monkeypatch,
) -> None:
    db_path = tmp_path / "private" / "operational" / "pfi.sqlite"
    monkeypatch.setattr(runtime_api, "build_v025_release_cache_policy", lambda **_kwargs: _policy())
    handler = runtime_api._handler_factory(db_path, auth_token=AUTH_TOKEN)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}"
    try:
        forbidden_status, forbidden = _request(base_url, "/api/jobs", token="wrong")
        assert forbidden_status == 403
        assert forbidden["error"] == "forbidden"

        submit_status, submitted = _request(
            base_url,
            "/api/jobs/cache-refresh",
            method="POST",
            payload={"request_id": "api-offline-refresh"},
        )
        assert submit_status == 202
        assert submitted["schema"] == "PFIV025RuntimeJobSupervisorV1"
        assert submitted["external_network_calls"] == 0
        poll_uri = str(submitted["poll_uri"])

        current: dict[str, object] = {}
        for _ in range(100):
            poll_status, current = _request(base_url, poll_uri)
            assert poll_status == 200
            if current["job"]["status"] in {"succeeded", "failed", "cancelled", "dead_letter"}:
                break
            time.sleep(0.01)
        assert current["job"]["status"] == "succeeded"
        assert current["job"]["progress"]["timer_based"] is False
        assert current["job"]["progress"]["percent"] == 100.0
        assert current["job"]["trace"]["trace_id"]
        assert current["job"]["observability"]["external_network_calls"] == 0
        assert len(current["events"]) == len(current["logs"]) == 6

        list_status, listed = _request(base_url, "/api/jobs?limit=20")
        assert list_status == 200
        assert listed["job_count"] == 1
        assert listed["jobs"][0]["job_id"] == current["job"]["job_id"]
        serialized = json.dumps(current, ensure_ascii=False, sort_keys=True)
        assert str(tmp_path) not in serialized
        assert "/Users/" not in serialized
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_candidate_jobs_surface_is_empty_and_never_creates_a_database(
    tmp_path: Path,
    monkeypatch,
) -> None:
    db_path = tmp_path / "candidate" / "pfi.sqlite"
    monkeypatch.setenv("PFI_STAGE1_CANDIDATE_MODE", "1")
    handler = runtime_api._handler_factory(db_path, auth_token=AUTH_TOKEN)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}"
    try:
        status, payload = _request(base_url, "/api/jobs")
        assert status == 200
        assert payload["candidate_read_only"] is True
        assert payload["jobs"] == []
        write_status, rejected = _request(
            base_url,
            "/api/jobs/cache-refresh",
            method="POST",
            payload={"request_id": "must-not-write"},
        )
        assert write_status == 403
        assert rejected["error"] == "candidate_read_only"
        assert not db_path.exists()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
