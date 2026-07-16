from __future__ import annotations

import json
import multiprocessing
import sqlite3
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from pfi_os.application.use_cases.holding_settings_persistence import (
    DEFAULT_SETTINGS,
    HoldingSettingsPersistenceService,
    HoldingSettingsWorkflowError,
)
from pfi_os.infrastructure.operational_holding_settings_store import (
    HOLDING_IDEMPOTENCY_MIGRATION_ID,
    HOLDING_SETTINGS_MIGRATION_ID,
)
from pfi_v02.stage_v021_runtime_api import _handler_factory


REPO_ROOT = Path(__file__).resolve().parents[2]
PFI_ROOT = REPO_ROOT / "PFI"
PHASE_ID = "V025-S7-P7.2"
TASK_IDS = ("S7-P2-T1", "S7-P2-T2", "S7-P2-T3", "S7-P2-T4")
ACCEPTANCE_ID = "ACC-PFI-V025-S7-P72-HOLDINGS-SETTINGS"
AUTH_TOKEN = "stage7-holding-settings-test-token"


def _initialize_holding_service_process(
    db_path: str,
    backup_dir: str,
    start: object,
    results: object,
) -> None:
    try:
        start.wait(timeout=10)
        HoldingSettingsPersistenceService(db_path=db_path, backup_dir=backup_dir)
        results.put("ok")
    except Exception as exc:  # pragma: no cover - surfaced through parent assertion
        results.put(f"{type(exc).__name__}: {exc}")


def _service(tmp_path: Path) -> HoldingSettingsPersistenceService:
    return HoldingSettingsPersistenceService(
        db_path=tmp_path / "private" / "operational" / "pfi.sqlite",
        backup_dir=tmp_path / "runtime" / "backups",
    )


def _holding(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "instrument_id": "CONTRACT-SENTINEL",
        "display_name": "持久化合同哨兵（非财务验收）",
        "quantity": "2.5",
        "average_cost": None,
        "market_price": None,
        "currency": "CNY",
        "portfolio_id": "contract-sentinel",
        "as_of": "2026-07-15",
        "note": "仅验证 CRUD/SQLite/restart；不作为真实持仓或估值证据",
    }
    row.update(overrides)
    return row


def _json_request(
    base_url: str,
    path: str,
    *,
    method: str = "GET",
    payload: dict[str, object] | None = None,
) -> tuple[int, dict[str, object]]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
    request = Request(
        base_url + path,
        data=data,
        method=method,
        headers={
            "Content-Type": "application/json",
            "X-PFI-Runtime-Token": AUTH_TOKEN,
        },
    )
    try:
        with urlopen(request, timeout=5) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def test_phase_contract_is_exactly_phase_72_and_financial_sentinel_is_not_acceptance() -> None:
    service = HoldingSettingsPersistenceService.__new__(HoldingSettingsPersistenceService)
    contract = service.phase_contract()

    assert contract["phase_id"] == PHASE_ID
    assert contract["task_ids"] == list(TASK_IDS)
    assert contract["acceptance_id"] == ACCEPTANCE_ID
    assert contract["current_phase_only"] is True
    assert contract["financial_sentinel_counts_as_real_acceptance"] is False
    assert contract["finder_used"] is False
    assert contract["external_network_allowed"] is False
    assert contract["phase_7_3_started"] is False
    assert contract["whole_stage_review_started"] is False


def test_additive_migration_records_version_and_creates_consistent_backup(tmp_path: Path) -> None:
    db_path = tmp_path / "private" / "operational" / "pfi.sqlite"
    db_path.parent.mkdir(parents=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE existing_private_state(key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        conn.execute("INSERT INTO existing_private_state VALUES ('preserve', 'yes')")

    service = _service(tmp_path)
    service.store.initialize()

    backups = list((tmp_path / "runtime" / "backups").glob("*.sqlite"))
    assert len(backups) == 1
    with sqlite3.connect(backups[0]) as backup:
        assert backup.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert backup.execute("SELECT value FROM existing_private_state WHERE key='preserve'").fetchone()[0] == "yes"
    with sqlite3.connect(db_path) as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM pfi_schema_migrations WHERE migration_id = ?",
            (HOLDING_SETTINGS_MIGRATION_ID,),
        ).fetchone()[0] == 1
        assert conn.execute(
            "SELECT COUNT(*) FROM pfi_schema_migrations WHERE migration_id = ?",
            (HOLDING_IDEMPOTENCY_MIGRATION_ID,),
        ).fetchone()[0] == 1


def test_migration_backup_is_serialized_across_processes(tmp_path: Path) -> None:
    db_path = tmp_path / "private" / "operational" / "pfi.sqlite"
    backup_dir = tmp_path / "runtime" / "backups"
    db_path.parent.mkdir(parents=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE existing_private_state(key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        conn.execute("INSERT INTO existing_private_state VALUES ('preserve', 'yes')")

    context = multiprocessing.get_context("spawn")
    start = context.Event()
    results = context.Queue()
    processes = [
        context.Process(
            target=_initialize_holding_service_process,
            args=(str(db_path), str(backup_dir), start, results),
        )
        for _ in range(2)
    ]
    for process in processes:
        process.start()
    start.set()
    for process in processes:
        process.join(timeout=20)
        assert process.exitcode == 0

    assert sorted(results.get(timeout=5) for _ in processes) == ["ok", "ok"]
    backups = list(backup_dir.glob("*.sqlite"))
    assert len(backups) == 1
    with sqlite3.connect(backups[0]) as backup:
        assert backup.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert backup.execute(
            "SELECT value FROM existing_private_state WHERE key='preserve'"
        ).fetchone()[0] == "yes"
    with sqlite3.connect(db_path) as current:
        assert current.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert current.execute(
            "SELECT value FROM existing_private_state WHERE key='preserve'"
        ).fetchone()[0] == "yes"


def test_holding_commit_is_atomic_validated_revisioned_and_fail_closed_for_money(tmp_path: Path) -> None:
    service = _service(tmp_path)
    with pytest.raises(HoldingSettingsWorkflowError, match="quantity"):
        service.commit_holdings(
            request_id="atomic-invalid",
            operations=[
                {"operation": "create", "client_ref": "first", "holding": _holding()},
                {"operation": "create", "client_ref": "invalid", "holding": _holding(quantity="0")},
            ],
        )
    assert service.list_holdings()["summary"]["active_count"] == 0

    with pytest.raises(HoldingSettingsWorkflowError, match="quantity must be finite"):
        service.commit_holdings(
            request_id="overflow-invalid",
            operations=[
                {
                    "operation": "create",
                    "client_ref": "overflow",
                    "holding": _holding(quantity="1e100000"),
                }
            ],
        )
    assert service.list_holdings()["summary"]["active_count"] == 0

    created = service.commit_holdings(
        request_id="create-one",
        operations=[{"operation": "create", "client_ref": "sentinel-1", "holding": _holding()}],
    )
    assert created["summary"]["active_count"] == 1
    row = created["rows"][0]
    assert row["revision"] == 1
    assert row["source_id"] == "manual_user_entry"
    projection = created["projection"]
    assert projection["financial_acceptance_input"] is False
    assert projection["financial_values_emitted"] == 0
    assert projection["valuation_status"] == "valuation_missing"
    assert projection["home"]["investment_market_value_cny"] is None
    assert projection["investment"]["market_value_cny"] is None
    assert projection["report"]["market_value_cny"] is None
    assert len(
        {
            projection["home"]["projection_hash"],
            projection["investment"]["projection_hash"],
            projection["report"]["projection_hash"],
        }
    ) == 1

    updated = service.commit_holdings(
        request_id="update-one",
        expected_projection_hash=projection["projection_hash"],
        operations=[
            {
                "operation": "update",
                "holding_id": row["holding_id"],
                "expected_revision": 1,
                "holding": _holding(quantity="3.75", note="已更新；仍是非财务合同哨兵"),
            }
        ],
    )
    assert updated["rows"][0]["quantity"] == "3.75"
    assert updated["rows"][0]["revision"] == 2
    assert updated["projection"]["projection_hash"] != projection["projection_hash"]

    with pytest.raises(HoldingSettingsWorkflowError, match="revision"):
        service.commit_holdings(
            request_id="stale-update",
            operations=[
                {
                    "operation": "update",
                    "holding_id": row["holding_id"],
                    "expected_revision": 1,
                    "holding": _holding(quantity="99"),
                }
            ],
        )
    assert service.list_holdings()["rows"][0]["quantity"] == "3.75"

    deleted = service.commit_holdings(
        request_id="delete-one",
        operations=[
            {
                "operation": "delete",
                "holding_id": row["holding_id"],
                "expected_revision": 2,
            }
        ],
    )
    assert deleted["summary"]["active_count"] == 0
    assert deleted["summary"]["deleted_count"] == 1
    assert deleted["projection"]["valuation_status"] == "not_loaded"


def test_holding_request_id_replays_only_the_same_command(tmp_path: Path) -> None:
    service = _service(tmp_path)
    command = [{"operation": "create", "client_ref": "stable", "holding": _holding()}]
    created = service.commit_holdings(request_id="stable-command", operations=command)
    replay = service.commit_holdings(request_id="stable-command", operations=command)
    assert replay["idempotent_replay"] is True
    assert replay["command_hash"] == created["command_hash"]
    assert replay["summary"]["active_count"] == 1

    with pytest.raises(HoldingSettingsWorkflowError, match="request_id conflict"):
        service.commit_holdings(
            request_id="stable-command",
            operations=[{"operation": "create", "client_ref": "changed", "holding": _holding(quantity="9")}],
        )
    assert service.list_holdings()["summary"]["active_count"] == 1


def test_holdings_and_settings_survive_service_reopen_and_settings_are_isolated(tmp_path: Path) -> None:
    service = _service(tmp_path)
    created = service.commit_holdings(
        request_id="restart-create",
        operations=[{"operation": "create", "client_ref": "restart-sentinel", "holding": _holding()}],
    )
    saved_settings = service.save_settings(
        {
            "default_account": "投资复盘",
            "theme_language": "跟随系统",
            "feedback_haptic": False,
            "feedback_sound": True,
            "feedback_motion": False,
        },
        expected_revision=0,
    )

    reopened = _service(tmp_path)
    holdings = reopened.list_holdings()
    settings = reopened.get_settings()
    read_model = reopened.build_holding_projection()
    report = reopened.build_holding_report()

    assert holdings["rows"][0]["holding_id"] == created["rows"][0]["holding_id"]
    assert holdings["rows"][0]["revision"] == 1
    assert settings["preferences"] == saved_settings["preferences"]
    assert settings["revision"] == 1
    assert settings["surface_scope"] == "settings_only"
    assert read_model["projection"]["projection_hash"] == report["projection_hash"]
    assert read_model["home"]["holding_count"] == 1
    assert read_model["investment"]["holding_count"] == 1
    assert read_model["report"]["holding_count"] == 1

    reset = reopened.save_settings(DEFAULT_SETTINGS, expected_revision=1)
    assert reset["preferences"] == DEFAULT_SETTINGS
    assert reset["revision"] == 2
    with pytest.raises(HoldingSettingsWorkflowError, match="default_account"):
        reopened.save_settings({**DEFAULT_SETTINGS, "default_account": "不存在"}, expected_revision=2)


def test_runtime_api_closes_commit_projection_settings_and_restart_loop(tmp_path: Path) -> None:
    db_path = tmp_path / "private" / "operational" / "pfi.sqlite"

    def run_server() -> tuple[ThreadingHTTPServer, threading.Thread, str]:
        server = ThreadingHTTPServer(
            ("127.0.0.1", 0),
            _handler_factory(db_path, auth_token=AUTH_TOKEN),
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return server, thread, f"http://127.0.0.1:{server.server_port}"

    server, thread, base = run_server()
    try:
        status, empty = _json_request(base, "/api/holdings")
        assert status == 200
        assert empty["summary"]["active_count"] == 0

        status, retired = _json_request(
            base,
            "/api/holdings",
            method="POST",
            payload={"rows": [_holding()]},
        )
        assert status == 400
        assert retired["error"] == "workflow_error"
        assert "/api/holdings/commit" in retired["message"]
        assert _json_request(base, "/api/holdings")[1]["summary"]["active_count"] == 0

        status, created = _json_request(
            base,
            "/api/holdings/commit",
            method="POST",
            payload={
                "request_id": "http-create",
                "expected_projection_hash": empty["projection"]["projection_hash"],
                "operations": [{"operation": "create", "client_ref": "http-sentinel", "holding": _holding()}],
            },
        )
        assert status == 200
        assert created["summary"]["active_count"] == 1

        status, model = _json_request(base, "/api/read-model")
        assert status == 200
        status, report = _json_request(base, "/api/reports/holdings")
        assert status == 200
        assert model["projection"]["projection_hash"] == report["projection_hash"]
        status, trends = _json_request(base, "/api/trends")
        assert status == 200
        assert trends["readModel"]["holding_source_authority"] == "v025_sqlite_holding_records"
        assert trends["readModel"]["holding_projection"]["projection_hash"] == model["projection"]["projection_hash"]
        assert trends["readModel"]["investment"]["market_value_cny"] is None
        assert trends["readModel"]["accounts"]["net_worth_cny"] is None
        assert all(not item["values"] for item in trends["accounts"]["series"])
        assert all(not item["values"] for item in trends["investment"]["series"])

        status, settings = _json_request(
            base,
            "/api/settings/preferences",
            method="POST",
            payload={"preferences": {**DEFAULT_SETTINGS, "feedback_sound": True}, "expected_revision": 0},
        )
        assert status == 200
        assert settings["preferences"]["feedback_sound"] is True
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    restarted, restarted_thread, restarted_base = run_server()
    try:
        status, holdings = _json_request(restarted_base, "/api/holdings")
        assert status == 200
        assert holdings["summary"]["active_count"] == 1
        status, settings = _json_request(restarted_base, "/api/settings/preferences")
        assert status == 200
        assert settings["preferences"]["feedback_sound"] is True
        status, trends = _json_request(restarted_base, "/api/trends")
        assert status == 200
        assert trends["readModel"]["holding_projection"]["projection_hash"] == holdings["projection"]["projection_hash"]
    finally:
        restarted.shutdown()
        restarted.server_close()
        restarted_thread.join(timeout=5)

    with sqlite3.connect(db_path) as conn:
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_formal_shell_uses_backend_for_holding_and_settings_saves() -> None:
    shell = (PFI_ROOT / "web" / "app" / "shell.js").read_text(encoding="utf-8")
    html = (PFI_ROOT / "web" / "index.html").read_text(encoding="utf-8")

    holding_flow = shell[shell.index("async function refreshHoldingsFromBackend"):shell.index("function setHoldingsStatus")]
    settings_flow = shell[shell.index("function bindSettingsOperationEvents"):shell.index("function readHomeSummary")]

    assert 'runtimeApiJson("/api/holdings/commit"' in holding_flow
    assert "expected_projection_hash" in holding_flow
    assert "localStorage.setItem" not in holding_flow[holding_flow.index("async function saveHoldingsEdits"):]
    assert 'runtimeApiJson("/api/settings/preferences"' in settings_flow
    assert "async function saveSettingsOperationFlow" in settings_flow
    assert "async function resetSettingsOperationFlow" in settings_flow
    assert "localStorage" not in settings_flow
    assert "sessionStorage" not in settings_flow
    assert "IndexedDB" not in settings_flow
    assert "设置只在本页显示" in html
    assert "保存到当前本机页面状态" not in shell
