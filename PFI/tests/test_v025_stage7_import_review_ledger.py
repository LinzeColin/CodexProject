from __future__ import annotations

import base64
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import sqlite3
import sys
import threading
import zipfile
from io import BytesIO
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from pfi_os.application.use_cases.import_review_ledger import (
    ImportReviewLedgerService,
    ImportWorkflowError,
    UploadedImportFile,
)
from pfi_v02.stage_v021_runtime_api import _handler_factory
from pfi_os.application.use_cases.metric_lineage_drilldown import build_stage7_phase73_payload


PROJECT_ROOT = Path(__file__).resolve().parents[2]
WEB_TEST_DIR = PROJECT_ROOT / "PFI/web/tests/v025"
if str(WEB_TEST_DIR) not in sys.path:
    sys.path.insert(0, str(WEB_TEST_DIR))
from stage7_trace_privacy import sanitize_playwright_trace  # noqa: E402

AUTH_TOKEN = "stage7-import-review-test-token"
ALIPAY_BYTES = (
    "交易时间,交易分类,交易对方,商品说明,收/支,金额\n"
    "2026-01-02 10:30:00,餐饮,本地商户,咖啡,支出,18.50\n"
    "2026-01-03 11:00:00,其他,未知,未知,支出,20.00\n"
).encode("utf-8")


def _service(tmp_path: Path) -> ImportReviewLedgerService:
    return ImportReviewLedgerService(
        db_path=tmp_path / "private" / "operational" / "pfi.sqlite",
        raw_store_dir=tmp_path / "private" / "imports" / "raw",
    )


def _upload(content: bytes = ALIPAY_BYTES, name: str = "支付宝交易明细.csv") -> UploadedImportFile:
    return UploadedImportFile(name=name, content=content, media_type="text/csv")


def _table_count(db_path: Path, table: str) -> int:
    with sqlite3.connect(db_path) as conn:
        return int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])


def test_trace_sanitizer_redacts_tmp_paths_and_cleans_temporary_files(tmp_path: Path) -> None:
    raw = tmp_path / "raw-trace.zip"
    output = tmp_path / "sanitized-trace.zip"
    with zipfile.ZipFile(raw, "w") as archive:
        archive.writestr(
            "trace.trace",
            '{"path":"/tmp/pfi-private/trace.zip","value":"CNY 12.34",'
            '"escaped":"{\\\"value\\\":987654.32,\\\"source\\\":\\\"MetaDatabase\\\"}"}',
        )

    result = sanitize_playwright_trace(
        raw, output, private_payloads=(b"987654.32", b"MetaDatabase")
    )
    assert result["status"] == "pass"
    with zipfile.ZipFile(output) as archive:
        serialized = archive.read("trace.trace")
    assert b"/tmp/" not in serialized
    assert b"987654.32" not in serialized
    assert b"MetaDatabase" not in serialized
    assert b"[PRIVATE_PAYLOAD_REDACTED]" in serialized
    assert b"[LOCAL_PATH_REDACTED]" in serialized
    assert not output.with_suffix(".sanitizing.zip").exists()

    corrupt = tmp_path / "corrupt.zip"
    failed_output = tmp_path / "failed.zip"
    corrupt.write_bytes(b"not-a-zip")
    with pytest.raises(zipfile.BadZipFile):
        sanitize_playwright_trace(corrupt, failed_output)
    assert not failed_output.with_suffix(".sanitizing.zip").exists()


def test_preview_identifies_source_hash_parser_mapping_without_posting_ledger(tmp_path: Path) -> None:
    service = _service(tmp_path)
    preview = service.preview_upload((_upload(),))

    assert preview["schema"] == "PFIV025Stage7ImportPreviewV1"
    assert preview["status"] == "preview_ready"
    assert preview["write_state"] == "staged_only"
    assert preview["file_count"] == 1
    assert preview["valid_file_count"] == 1
    assert preview["transaction_count"] == 2
    assert preview["review_count"] == 1
    assert preview["ledger_count"] == 0
    assert preview["file_summaries"] == [
        {
            "file_name": "支付宝交易明细.csv",
            "content_sha256": hashlib.sha256(ALIPAY_BYTES).hexdigest(),
            "bytes_count": len(ALIPAY_BYTES),
            "source_id": "alipay_daily",
            "parser_version": "alipay_bill_csv_v1",
            "status": "ready",
            "error_code": None,
        }
    ]
    mapped = {item["canonical_field"] for item in preview["field_mapping"]}
    assert {"occurred_at", "amount", "currency", "account_id", "description"} <= mapped
    assert _table_count(service.db_path, "import_staged_transactions") == 2
    assert _table_count(service.db_path, "ledger_entries") == 0
    assert len(tuple(service.raw_store_dir.glob("*.bin"))) == 1


def test_import_migration_backup_uses_canonical_runtime_directory(tmp_path: Path) -> None:
    db_path = tmp_path / "private" / "operational" / "pfi.sqlite"
    db_path.parent.mkdir(parents=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE existing_state(key TEXT PRIMARY KEY)")
        conn.execute("INSERT INTO existing_state VALUES ('preserve')")

    service = _service(tmp_path)
    backups = list((tmp_path / "runtime" / "backups").glob("*.sqlite"))
    assert len(backups) == 1
    assert not (tmp_path / "private" / "runtime" / "backups").exists()
    with sqlite3.connect(backups[0]) as backup:
        assert backup.execute("SELECT key FROM existing_state").fetchone()[0] == "preserve"


def test_raw_files_are_cleaned_when_multifile_parse_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    service = _service(tmp_path)
    original_write = service.store.write_raw
    calls = 0

    def flaky_write(content_sha256: str, content: bytes) -> str:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("forced raw write failure")
        return original_write(content_sha256, content)

    monkeypatch.setattr(service.store, "write_raw", flaky_write)
    other = ALIPAY_BYTES.replace(b"18.50", b"19.50")
    with pytest.raises(OSError, match="forced raw write failure"):
        service.preview_upload((_upload(), _upload(other, "第二份.csv")))
    assert list(service.raw_store_dir.glob("*.bin")) == []


def test_shared_raw_digest_survives_concurrent_failed_preview(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    failing = _service(tmp_path)
    successful = _service(tmp_path)
    successful_extra = ALIPAY_BYTES.replace(b"18.50", b"19.50")
    failing_extra = b"forced-write-failure"
    failing_digest = hashlib.sha256(failing_extra).hexdigest()
    original_write = failing.store.write_raw

    def fail_one_digest(content_sha256: str, content: bytes) -> str:
        if content_sha256 == failing_digest:
            raise OSError("forced shared-digest preview failure")
        return original_write(content_sha256, content)

    monkeypatch.setattr(failing.store, "write_raw", fail_one_digest)
    start = threading.Barrier(2)

    def run_failing() -> None:
        start.wait(timeout=5)
        failing.preview_upload((_upload(), _upload(failing_extra, "失败文件.csv")))

    def run_successful() -> dict[str, object]:
        start.wait(timeout=5)
        return successful.preview_upload((_upload(), _upload(successful_extra, "第二份.csv")))

    with ThreadPoolExecutor(max_workers=2) as pool:
        failed_future = pool.submit(run_failing)
        succeeded_future = pool.submit(run_successful)
        with pytest.raises(OSError, match="forced shared-digest preview failure"):
            failed_future.result()
        result = succeeded_future.result()

    for item in result["file_summaries"]:
        digest = str(item["content_sha256"])
        assert successful.store.read_raw(digest)


def test_confirm_is_atomic_idempotent_and_duplicate_preview_reuses_batch(tmp_path: Path) -> None:
    service = _service(tmp_path)
    preview = service.preview_upload((_upload(),))

    with sqlite3.connect(service.db_path) as conn:
        conn.execute(
            """
            CREATE TRIGGER force_stage7_ledger_failure
            BEFORE INSERT ON ledger_entries
            BEGIN
              SELECT RAISE(ABORT, 'forced atomicity failure');
            END;
            """
        )
    with pytest.raises(ImportWorkflowError, match="forced atomicity failure"):
        service.confirm_batch(preview["batch_id"])
    assert service.get_batch(preview["batch_id"])["status"] == "preview_ready"
    assert _table_count(service.db_path, "ledger_entries") == 0

    with sqlite3.connect(service.db_path) as conn:
        conn.execute("DROP TRIGGER force_stage7_ledger_failure")
    confirmed = service.confirm_batch(preview["batch_id"])
    assert confirmed["status"] == "confirmed"
    assert confirmed["idempotent_replay"] is False
    assert confirmed["ledger_count"] == 2
    assert confirmed["review_count"] == 1

    replay = service.confirm_batch(preview["batch_id"])
    assert replay["status"] == "confirmed"
    assert replay["idempotent_replay"] is True
    assert _table_count(service.db_path, "ledger_entries") == 2

    duplicate = service.preview_upload((_upload(),))
    assert duplicate["batch_id"] == preview["batch_id"]
    assert duplicate["idempotent_replay"] is True
    assert duplicate["status"] == "confirmed"
    assert _table_count(service.db_path, "import_batches") == 1


def test_concurrent_identical_previews_atomically_reuse_one_batch(tmp_path: Path) -> None:
    first = _service(tmp_path)
    second = _service(tmp_path)
    start = threading.Barrier(2)

    def preview(service: ImportReviewLedgerService) -> dict[str, object]:
        start.wait(timeout=5)
        return service.preview_upload((_upload(),))

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(preview, (first, second)))

    assert results[0]["batch_id"] == results[1]["batch_id"]
    assert sorted(result["idempotent_replay"] for result in results) == [False, True]
    assert _table_count(first.db_path, "import_batches") == 1
    assert _table_count(first.db_path, "import_staged_transactions") == 2


def test_duplicate_files_and_overlapping_batches_never_double_post(tmp_path: Path) -> None:
    service = _service(tmp_path)
    deduplicated = service.preview_upload((_upload(), _upload(name="同内容副本.csv")))
    assert deduplicated["file_count"] == 1
    assert deduplicated["transaction_count"] == 2
    service.confirm_batch(deduplicated["batch_id"])

    second_bytes = (
        "交易时间,交易分类,交易对方,商品说明,收/支,金额\n"
        "2026-01-04 09:00:00,交通,公共交通,车票,支出,6.00\n"
    ).encode("utf-8")
    overlap = service.preview_upload((_upload(), _upload(second_bytes, "第二批.csv")))
    assert overlap["file_count"] == 2
    assert overlap["transaction_count"] == 1
    confirmed = service.confirm_batch(overlap["batch_id"])
    assert confirmed["ledger_count"] == 1
    assert _table_count(service.db_path, "ledger_entries") == 3
    service.rollback_batch(deduplicated["batch_id"])
    assert service.get_batch(overlap["batch_id"])["ledger_count"] == 3
    assert _table_count(service.db_path, "ledger_entries") == 3
    service.rollback_batch(overlap["batch_id"])
    assert _table_count(service.db_path, "ledger_entries") == 0


def test_batches_previewed_before_confirm_are_globally_idempotent(tmp_path: Path) -> None:
    service = _service(tmp_path)
    first = service.preview_upload((_upload(),))
    archive = BytesIO()
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as output:
        output.writestr("支付宝交易明细.csv", ALIPAY_BYTES)
    wrapped = service.preview_upload((_upload(archive.getvalue(), "支付宝交易明细.zip"),))

    assert first["batch_id"] != wrapped["batch_id"]
    assert first["transaction_count"] == wrapped["transaction_count"] == 2
    assert service.confirm_batch(first["batch_id"])["ledger_count"] == 2
    duplicate_confirm = service.confirm_batch(wrapped["batch_id"])
    assert duplicate_confirm["status"] == "confirmed"
    assert duplicate_confirm["ledger_count"] == 0
    assert _table_count(service.db_path, "ledger_entries") == 2
    service.rollback_batch(first["batch_id"])
    assert service.get_batch(wrapped["batch_id"])["ledger_count"] == 2
    assert _table_count(service.db_path, "ledger_entries") == 2
    service.rollback_batch(wrapped["batch_id"])
    assert _table_count(service.db_path, "ledger_entries") == 0


def test_explicit_income_direction_wins_over_description_text(tmp_path: Path) -> None:
    content = (
        "交易时间,交易分类,交易对方,商品说明,收/支,金额\n"
        "2026-01-05 09:00:00,退款,本地商户,付款退款到账,收入,9.50\n"
    ).encode("utf-8")
    service = _service(tmp_path)
    batch = service.preview_upload((_upload(content),))
    service.confirm_batch(batch["batch_id"])
    ledger = service.list_ledger(batch_id=batch["batch_id"])
    assert ledger["entries"][0]["amount"] == "9.5"


def test_explicit_non_cashflow_direction_is_transfer_not_consumption(tmp_path: Path) -> None:
    content = (
        "交易时间,交易分类,交易对方,商品说明,收/支,金额\n"
        "2026-01-05 09:00:00,转账,本人账户,余额调拨,不计收支,9.50\n"
    ).encode("utf-8")
    service = _service(tmp_path)
    batch = service.preview_upload((_upload(content),))
    service.confirm_batch(batch["batch_id"])
    ledger = service.list_ledger(batch_id=batch["batch_id"])
    assert ledger["entries"][0]["event_type"] == "TRANSFER"
    assert ledger["entries"][0]["ledger_state"] == "posted"
    runtime = service.build_ledger_runtime_read_model()
    assert runtime["consumption"]["spending_transaction_count"] == 0


@pytest.mark.parametrize(
    ("content", "name"),
    [
        (b"not a bill", "alipay.csv"),
        (
            "交易时间,金额,收/支\nnot-a-date,1.00,支出\n".encode("utf-8"),
            "支付宝交易明细.csv",
        ),
        (
            "交易时间,金额,收/支\n2026-01-01,NaN,支出\n".encode("utf-8"),
            "支付宝交易明细.csv",
        ),
        (
            "交易时间,金额,收/支\n2026-01-01,1.00,收入/支出\n".encode("utf-8"),
            "支付宝交易明细.csv",
        ),
        (
            "交易时间,金额\n2026-01-01,1.00\n".encode("utf-8"),
            "支付宝交易明细.csv",
        ),
        (
            "交易时间,金额,收/支\n2026-01-01,1.00,未知\n".encode("utf-8"),
            "支付宝交易明细.csv",
        ),
    ],
)
def test_source_and_financial_parsing_fail_closed(tmp_path: Path, content: bytes, name: str) -> None:
    failed = _service(tmp_path).preview_upload((_upload(content, name),))
    assert failed["status"] == "failed"
    assert failed["transaction_count"] == 0
    assert failed["ledger_count"] == 0


def test_zip_compression_ratio_limit_fails_closed(tmp_path: Path) -> None:
    archive = BytesIO()
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as output:
        output.writestr("支付宝交易明细.csv", b"A" * (1024 * 1024))
    failed = _service(tmp_path).preview_upload((_upload(archive.getvalue(), "支付宝账单.zip"),))
    assert failed["status"] == "failed"
    assert failed["errors"][0]["code"] == "parse_failed"


def test_pending_only_ledger_blocks_lineage_without_false_zero(tmp_path: Path) -> None:
    content = (
        "交易时间,交易分类,交易对方,商品说明,收/支,金额\n"
        "2026-01-05 09:00:00,其他,未知,未知,支出,9.50\n"
    ).encode("utf-8")
    service = _service(tmp_path)
    batch = service.preview_upload((_upload(content),))
    service.confirm_batch(batch["batch_id"])
    runtime = service.build_ledger_runtime_read_model()
    assert runtime["status"] == "partial_pending_review"
    assert runtime["consumption"]["has_real_transactions"] is False
    assert runtime["consumption"]["month_spend_cny"] is None
    assert runtime["economic_event_adapter_ready"] is False
    assert "metric_components" not in runtime
    payload = build_stage7_phase73_payload(
        PROJECT_ROOT / "PFI", operational_ledger=runtime
    )
    assert payload["interconnection_map"]["status"] == "blocked"
    assert payload["metric_drilldown"]["status"] == "blocked"
    assert payload["metric_drilldown"]["non_ready_false_zero_count"] == 0
    assert all(item["value"] is None for item in payload["metric_drilldown"]["metrics"])


def test_review_resolution_is_persistent_reversible_and_batch_can_rollback_retry(tmp_path: Path) -> None:
    service = _service(tmp_path)
    batch_id = service.preview_upload((_upload(),))["batch_id"]
    service.confirm_batch(batch_id)

    queue = service.list_review_queue(status="pending")
    assert queue["pending_count"] == 1
    review = queue["items"][0]
    resolved = service.resolve_review(
        review["review_id"],
        decision="reclassify",
        category="餐饮食品",
    )
    assert resolved["status"] == "resolved"
    assert resolved["ledger_state"] == "posted"
    assert resolved["category"] == "餐饮食品"
    assert service.list_review_queue(status="pending")["pending_count"] == 0

    undone = service.undo_review(review["review_id"])
    assert undone["status"] == "pending"
    assert undone["ledger_state"] == "pending_review"
    assert service.list_review_queue(status="pending")["pending_count"] == 1

    rolled_back = service.rollback_batch(batch_id)
    assert rolled_back["status"] == "rolled_back"
    assert rolled_back["ledger_count"] == 0
    assert _table_count(service.db_path, "ledger_entries") == 0
    assert _table_count(service.db_path, "import_staged_transactions") == 2

    retried = service.retry_batch(batch_id)
    assert retried["status"] == "preview_ready"
    reconfirmed = service.confirm_batch(batch_id)
    assert reconfirmed["status"] == "confirmed"
    assert reconfirmed["ledger_count"] == 2


def test_concurrent_retry_cannot_reopen_a_confirmed_batch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    setup = _service(tmp_path)
    batch_id = setup.preview_upload((_upload(),))["batch_id"]
    setup.confirm_batch(batch_id)
    setup.rollback_batch(batch_id)

    slow = _service(tmp_path)
    fast = _service(tmp_path)
    slow_parsed = threading.Event()
    release_slow = threading.Event()
    original_parse = ImportReviewLedgerService._parse_files

    def controlled_parse(
        service: ImportReviewLedgerService, files: tuple[UploadedImportFile, ...]
    ) -> dict[str, object]:
        parsed = original_parse(service, files)
        if service is slow:
            slow_parsed.set()
            assert release_slow.wait(timeout=10)
        return parsed

    monkeypatch.setattr(ImportReviewLedgerService, "_parse_files", controlled_parse)
    with ThreadPoolExecutor(max_workers=1) as pool:
        slow_future = pool.submit(slow.retry_batch, batch_id)
        assert slow_parsed.wait(timeout=10)
        assert fast.retry_batch(batch_id)["status"] == "preview_ready"
        confirmed = fast.confirm_batch(batch_id)
        assert confirmed["status"] == "confirmed"
        release_slow.set()
        slow_result = slow_future.result(timeout=10)

    assert slow_result["status"] == "confirmed"
    assert slow_result["idempotent_replay"] is True
    final = setup.get_batch(batch_id)
    assert final["status"] == "confirmed"
    assert final["ledger_count"] == 2


def test_parse_failure_is_recorded_without_fabricated_preview_or_ledger(tmp_path: Path) -> None:
    service = _service(tmp_path)
    failed = service.preview_upload((_upload(b"not a bill", "unknown.xlsx"),))

    assert failed["status"] == "failed"
    assert failed["valid_file_count"] == 0
    assert failed["transaction_count"] == 0
    assert failed["ledger_count"] == 0
    assert failed["errors"][0]["code"] in {"unsupported_source", "parse_failed"}
    assert _table_count(service.db_path, "import_staged_transactions") == 0
    assert _table_count(service.db_path, "ledger_entries") == 0

    retry = service.retry_batch(failed["batch_id"])
    assert retry["status"] == "failed"
    assert retry["attempt_count"] == 2
    assert retry["transaction_count"] == 0


def _json_request(base_url: str, path: str, *, method: str = "GET", payload: dict | None = None) -> tuple[int, dict]:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
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


def test_runtime_api_closes_preview_confirm_review_undo_and_ledger_loop(tmp_path: Path) -> None:
    db_path = tmp_path / "private" / "operational" / "pfi.sqlite"
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        _handler_factory(db_path, auth_token=AUTH_TOKEN),
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}"
    try:
        status, preview = _json_request(
            base_url,
            "/api/imports/alipay",
            method="POST",
            payload={
                "files": [
                    {
                        "name": "支付宝交易明细.csv",
                        "type": "text/csv",
                        "contentBase64": base64.b64encode(ALIPAY_BYTES).decode("ascii"),
                    }
                ]
            },
        )
        assert status == 200
        assert preview["status"] == "preview_ready"
        assert preview["ledger_count"] == 0

        status, confirmed = _json_request(
            base_url,
            "/api/imports/alipay/confirm",
            method="POST",
            payload={"batch_id": preview["batch_id"]},
        )
        assert status == 200
        assert confirmed["status"] == "confirmed"
        assert confirmed["ledger_count"] == 2

        status, queue = _json_request(base_url, "/api/imports/review-queue?status=pending")
        assert status == 200
        assert queue["pending_count"] == 1
        review_id = queue["items"][0]["review_id"]

        status, resolved = _json_request(
            base_url,
            "/api/imports/review",
            method="POST",
            payload={"review_id": review_id, "decision": "reclassify", "category": "餐饮食品"},
        )
        assert status == 200
        assert resolved["ledger_state"] == "posted"

        status, undone = _json_request(
            base_url,
            "/api/imports/review/undo",
            method="POST",
            payload={"review_id": review_id},
        )
        assert status == 200
        assert undone["ledger_state"] == "pending_review"

        status, ledger = _json_request(base_url, f"/api/ledger?batch_id={preview['batch_id']}")
        assert status == 200
        assert ledger["ledger_count"] == 2
        assert ledger["pending_review_count"] == 1
        status, trends = _json_request(base_url, "/api/trends")
        assert status == 200
        projection = trends["readModel"]["operational_ledger"]
        assert projection["ledger_count"] == 2
        assert projection["ledger_projection_hash"].startswith("sha256:")
        assert projection["financial_values_emitted"] == 0
        assert trends["readModel"]["accounts"]["net_worth_cny"] is None
        assert trends["readModel"]["legacy_metadatabase_consumption_suppressed"] is True
        assert all(not item["values"] for item in trends["investment"]["series"])
        assert trends["consumption"]["source"] == "SQLite v0.2.5 unified operational ledger"

        status, runtime_status = _json_request(base_url, "/api/read-model-status")
        assert status == 200
        assert runtime_status["stage7_operational_authority"] is True
        assert runtime_status["legacy_metadatabase_suppressed"] is True
        assert runtime_status["source"]["status"] == "partial_pending_review"
        assert all(item["value"] is None for item in runtime_status["core_metric_states"])
        assert {
            item["status"] for item in runtime_status["core_metric_states"]
        } <= {
            "partial_coverage", "source_missing", "valuation_missing",
            "not_loaded", "calculation_failed",
        }
        assert "stage5_financial_model" not in runtime_status
        investment_status = next(
            item
            for item in runtime_status["core_metric_states"]
            if item["metric_id"] == "investment_market_value_cny"
        )
        assert investment_status["as_of"] is None

        status, lineage = _json_request(base_url, "/api/lineage")
        assert status == 200
        assert lineage["interconnection_map"]["source_id"] == "v025_sqlite_unified_operational_ledger"
        assert lineage["interconnection_map"]["operational_ledger_authority"] is True
        assert lineage["interconnection_map"]["status"] == "blocked"
        assert lineage["interconnection_map"]["economic_event_adapter_ready"] is False
        assert lineage["interconnection_map"]["lineage_complete_count"] == 0
        assert lineage["interconnection_map"]["lineage_missing_count"] == 2
        assert lineage["interconnection_map"]["event_types"] == []
        metrics = {item["metric_id"]: item for item in lineage["metric_drilldown"]["metrics"]}
        assert metrics["living_consumption_cny"]["source_ids"] == ["alipay_daily"]
        assert metrics["living_consumption_cny"]["data_hash"] == trends["readModel"]["operational_ledger_runtime"]["data_hash"]
        assert metrics["living_consumption_cny"]["status"] == "blocked_economic_event_adapter"
        assert metrics["living_consumption_cny"]["value"] is None
        assert metrics["living_consumption_cny"]["event_lineage"] == {}
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    with sqlite3.connect(db_path) as conn:
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_runtime_api_requires_token_and_restricts_cors_to_loopback(tmp_path: Path) -> None:
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        _handler_factory(tmp_path / "pfi.sqlite", auth_token=AUTH_TOKEN),
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        with pytest.raises(HTTPError) as unauthorized:
            urlopen(Request(f"{base}/health"), timeout=5)
        assert unauthorized.value.code == 403

        allowed_origin = "http://127.0.0.1:8501"
        request = Request(
            f"{base}/health",
            headers={
                "X-PFI-Runtime-Token": AUTH_TOKEN,
                "Origin": allowed_origin,
            },
        )
        with urlopen(request, timeout=5) as response:
            assert response.status == 200
            assert response.headers["Access-Control-Allow-Origin"] == allowed_origin
            assert response.headers["Vary"] == "Origin"

        preflight = Request(
            f"{base}/api/holdings",
            method="OPTIONS",
            headers={
                "Origin": allowed_origin,
                "Access-Control-Request-Headers": "Content-Type, X-PFI-Runtime-Token",
            },
        )
        with urlopen(preflight, timeout=5) as response:
            assert response.status == 204
            assert response.headers["Access-Control-Allow-Origin"] == allowed_origin

        forbidden_origin = Request(
            f"{base}/api/holdings",
            method="OPTIONS",
            headers={
                "Origin": "https://example.com",
                "Access-Control-Request-Headers": "X-PFI-Runtime-Token",
            },
        )
        with pytest.raises(HTTPError) as forbidden:
            urlopen(forbidden_origin, timeout=5)
        assert forbidden.value.code == 403
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_formal_shell_uses_backend_contract_for_every_stage7_mutation() -> None:
    shell = (PROJECT_ROOT / "PFI" / "web" / "app" / "shell.js").read_text(encoding="utf-8")

    upload_flow = shell[shell.index("async function handleUploadSelection"):shell.index("function validateUploadFile")]
    review_flow = shell[shell.index("async function refreshStage7WorkflowState"):shell.index("function exportLedgerReview")]

    assert 'runtimeApiJson("/api/imports/alipay"' in upload_flow
    assert 'runtimeApiJson("/api/imports/alipay/confirm"' in upload_flow
    assert "JSON.stringify({ batch_id: preview.batch_id })" in upload_flow
    pre_confirm = upload_flow[: upload_flow.index("async function confirmStage3Import")]
    assert pre_confirm.index('if (manifest.status === "confirmed")') < pre_confirm.index("applyAlipayImportSummary")
    assert "localStorage" not in upload_flow
    assert "sessionStorage" not in upload_flow

    assert 'runtimeApiJson("/api/imports/review"' in review_flow
    assert 'runtimeApiJson("/api/imports/review/undo"' in review_flow
    assert "localStorage" not in review_flow
    assert "sessionStorage" not in review_flow
    assert "preview.replaceChildren()" in shell
    assert "detail.appendChild(document.createTextNode(value))" in shell
    assert "const safe = /^[=+\\-@\\t\\r]/.test(text)" in shell
    assert "localStorage.setItem(HOLDINGS_DRAFT_STORAGE_KEY" not in shell
