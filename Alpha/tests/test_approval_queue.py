from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from backend.app.services.approval_queue import ApprovalQueue


def test_approval_queue_persists_ticket(tmp_path):
    path = tmp_path / "approval_queue.json"
    ticket = {"ticket_id": "ticket_1", "status": "pending_owner_approval"}

    queue = ApprovalQueue(path)
    assert queue.enqueue(ticket)["status"] == "queued"

    reloaded = ApprovalQueue(path)
    assert reloaded.list_tickets() == [ticket]


def test_approval_queue_summarizes_fresh_and_expired_pending_tickets(tmp_path):
    now = datetime(2026, 6, 13, 0, 0, tzinfo=timezone.utc)
    queue = ApprovalQueue(tmp_path / "approval_queue.json")
    fresh_ticket = {
        "ticket_id": "ticket_fresh",
        "status": "pending_owner_approval",
        "intent": {"expires_at": (now + timedelta(seconds=300)).isoformat()},
    }
    expired_ticket = {
        "ticket_id": "ticket_expired",
        "status": "pending_owner_approval",
        "intent": {"expires_at": (now - timedelta(seconds=1)).isoformat()},
    }

    queue.extend([fresh_ticket, expired_ticket])

    summary = queue.summary(now=now)
    latest = queue.latest_with_freshness(now=now)

    assert summary["total_count"] == 2
    assert summary["fresh_pending_count"] == 1
    assert summary["expired_pending_count"] == 1
    assert latest[0]["actionability"] == "fresh_pending_owner_approval"
    assert latest[0]["freshness"]["seconds_until_expiry"] == 300
    assert latest[1]["actionability"] == "expired_owner_approval"
    assert latest[1]["freshness"]["status"] == "expired"


def test_approval_queue_concurrent_enqueue_serializes_without_lost_tickets(tmp_path):
    path = tmp_path / "approval_queue.json"

    def enqueue_ticket(index: int) -> str:
        ticket = {"ticket_id": f"ticket_{index:03d}", "status": "pending_owner_approval"}
        return ApprovalQueue(path).enqueue(ticket)["status"]

    with ThreadPoolExecutor(max_workers=8) as pool:
        statuses = list(pool.map(enqueue_ticket, range(40)))

    reloaded = ApprovalQueue(path).list_tickets()
    assert statuses.count("queued") == 40
    assert len(reloaded) == 40
    assert sorted(ticket["ticket_id"] for ticket in reloaded) == [f"ticket_{index:03d}" for index in range(40)]


def test_approval_queue_atomic_write_keeps_previous_file_when_replace_fails(tmp_path):
    path = tmp_path / "approval_queue.json"
    original = {"ticket_id": "ticket_original", "status": "pending_owner_approval"}
    ApprovalQueue(path).enqueue(original)

    with patch("backend.app.services.atomic_json_store.os.replace", side_effect=OSError("simulated replace failure")):
        try:
            ApprovalQueue(path).enqueue({"ticket_id": "ticket_new", "status": "pending_owner_approval"})
        except OSError:
            pass
        else:
            raise AssertionError("expected atomic replace failure")

    assert ApprovalQueue(path).list_tickets() == [original]
    assert list(tmp_path.glob(".approval_queue.json.*.tmp")) == []
