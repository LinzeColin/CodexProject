from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

from backend.app.services.paper_broker import PaperBroker, PaperOrder


def test_paper_broker_persists_portfolio_state(tmp_path):
    path = tmp_path / "paper_portfolio.json"
    broker = PaperBroker(cash=1000)
    result = broker.submit_order(PaperOrder(idempotency_key="k1", symbol="TLT", side="buy", quantity=2, price=10))
    assert result["status"] == "filled"
    broker.save(path)

    reloaded = PaperBroker.load(path)
    assert reloaded.cash == 980
    assert reloaded.positions == {"TLT": 2}
    assert reloaded.seen_keys == {"k1"}
    assert reloaded.trade_log[0]["notional"] == 20


def test_paper_broker_persisted_submit_serializes_without_lost_orders(tmp_path):
    path = tmp_path / "paper_portfolio.json"

    def submit_order(index: int) -> str:
        result, _broker = PaperBroker.submit_order_to_path(
            path,
            PaperOrder(idempotency_key=f"k{index:03d}", symbol="TLT", side="buy", quantity=1, price=10),
            initial_cash=1000,
        )
        return result["status"]

    with ThreadPoolExecutor(max_workers=8) as pool:
        statuses = list(pool.map(submit_order, range(40)))

    reloaded = PaperBroker.load(path, initial_cash=1000)
    assert statuses.count("filled") == 40
    assert reloaded.cash == 600
    assert reloaded.positions == {"TLT": 40}
    assert len(reloaded.seen_keys) == 40
    assert len(reloaded.trade_log) == 40


def test_paper_broker_atomic_save_keeps_previous_snapshot_when_replace_fails(tmp_path):
    path = tmp_path / "paper_portfolio.json"
    original = PaperBroker(cash=1000)
    original.submit_order(PaperOrder(idempotency_key="k1", symbol="TLT", side="buy", quantity=1, price=10))
    original.save(path)

    replacement = PaperBroker(cash=1000)
    replacement.submit_order(PaperOrder(idempotency_key="k2", symbol="TLT", side="buy", quantity=3, price=10))
    with patch("backend.app.services.atomic_json_store.os.replace", side_effect=OSError("simulated replace failure")):
        try:
            replacement.save(path)
        except OSError:
            pass
        else:
            raise AssertionError("expected atomic replace failure")

    reloaded = PaperBroker.load(path, initial_cash=1000)
    assert reloaded.cash == 990
    assert reloaded.positions == {"TLT": 1}
    assert reloaded.seen_keys == {"k1"}
    assert list(tmp_path.glob(".paper_portfolio.json.*.tmp")) == []
