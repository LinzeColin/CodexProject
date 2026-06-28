from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

from pfi_v02.stage_v022_database_governance import V022_STAGE2_TASK_IDS, build_v022_stage2_contract
from pfi_v02.stage_v022_fx import (
    BASE_CURRENCY,
    DEFAULT_FX_PAIR,
    FX_SNAPSHOT_SCHEMA,
    FxRateFetch,
    amount_display_label,
    effective_fx_date,
    fx_snapshot_path,
    ledger_amount_fields,
    read_effective_fx_snapshot,
    refresh_daily_fx_snapshot,
    validate_snapshot_hash,
)


ROOT = Path(__file__).resolve().parents[1]
SYDNEY = ZoneInfo("Australia/Sydney")


class V022FxEffectiveDateTest(unittest.TestCase):
    def test_stage2_contract_locks_cny_fx_tasks(self) -> None:
        contract = build_v022_stage2_contract()

        self.assertEqual(contract["schema"], "PFIV022CnyFxGovernanceStage2ContractV1")
        self.assertEqual(contract["stage"], "Stage 2")
        self.assertEqual(contract["task_ids"], V022_STAGE2_TASK_IDS)
        self.assertEqual(contract["currency_policy"]["base_currency"], BASE_CURRENCY)
        self.assertEqual(contract["currency_policy"]["display_pair"], DEFAULT_FX_PAIR)
        self.assertFalse(contract["currency_policy"]["ordinary_runtime_network_refresh"])
        self.assertIn("PFI/src/pfi_v02/stage_v022_fx.py", contract["deliverables"])
        self.assertIn("PFI/data/fx_snapshots/AUD_CNY/<YYYY-MM-DD>.json", contract["deliverables"])

    def test_effective_fx_date_uses_yesterday_before_0600_and_today_after_0600(self) -> None:
        self.assertEqual(
            effective_fx_date(datetime(2026, 6, 28, 3, 0, tzinfo=SYDNEY)),
            date(2026, 6, 27),
        )
        self.assertEqual(
            effective_fx_date(datetime(2026, 6, 28, 6, 0, tzinfo=SYDNEY)),
            date(2026, 6, 28),
        )
        self.assertEqual(
            effective_fx_date(datetime(2026, 6, 28, 8, 0, tzinfo=SYDNEY)),
            date(2026, 6, 28),
        )

    def test_default_refresh_refuses_network_until_explicitly_allowed(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "forbids default network refresh"):
            refresh_daily_fx_snapshot(now=datetime(2026, 6, 28, 8, 0, tzinfo=SYDNEY))

    def test_explicit_refresh_writes_hashable_snapshot_and_read_path_does_not_fetch_network(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            snapshot_root = Path(tmp)
            fake_fetch = FxRateFetch(
                rate=Decimal("4.8123"),
                provider_date=date(2026, 6, 28),
                source_url="https://api.frankfurter.dev/v2/rate/AUD/CNY?date=2026-06-28",
            )
            with patch("pfi_v02.stage_v022_fx.fetch_frankfurter_rate", return_value=fake_fetch) as fetcher:
                payload = refresh_daily_fx_snapshot(
                    snapshot_root=snapshot_root,
                    now=datetime(2026, 6, 28, 8, 0, tzinfo=SYDNEY),
                    allow_network=True,
                )

            fetcher.assert_called_once()
            self.assertEqual(payload["schema"], FX_SNAPSHOT_SCHEMA)
            self.assertEqual(payload["display_pair"], "AUD/CNY")
            self.assertEqual(payload["rate"], "4.8123")
            self.assertTrue(validate_snapshot_hash(payload))
            self.assertTrue(fx_snapshot_path(snapshot_root, date(2026, 6, 28)).exists())

            with patch("pfi_v02.stage_v022_fx.fetch_frankfurter_rate", side_effect=AssertionError("network")):
                cached = read_effective_fx_snapshot(
                    snapshot_root=snapshot_root,
                    now=datetime(2026, 6, 28, 8, 0, tzinfo=SYDNEY),
                )
            self.assertEqual(cached["snapshot_id"], payload["snapshot_id"])

    def test_amount_display_and_ledger_fields_keep_original_currency_and_snapshot_id(self) -> None:
        snapshot = {
            "snapshot_id": "fx_AUD_CNY_20260628",
            "display_pair": "AUD/CNY",
            "pair_base": "AUD",
            "rate": "4.8100",
        }

        self.assertEqual(
            amount_display_label(500, "AUD", snapshot),
            "¥2,405.00 / 约 500.00 AUD / AUD/CNY=4.81",
        )
        fields = ledger_amount_fields(original_amount=500, original_currency="AUD", snapshot=snapshot)
        self.assertEqual(fields["original_amount"], "500.00")
        self.assertEqual(fields["original_currency"], "AUD")
        self.assertEqual(fields["amount_cny"], "2405.00")
        self.assertEqual(fields["fx_snapshot_id"], "fx_AUD_CNY_20260628")

    def test_committed_real_snapshot_is_traceable_to_frankfurter_and_hash_valid(self) -> None:
        snapshots = sorted((ROOT / "data" / "fx_snapshots" / "AUD_CNY").glob("*.json"))

        self.assertTrue(snapshots, "Stage 2 must include at least one real cached AUD/CNY snapshot.")
        payload = json.loads(snapshots[-1].read_text(encoding="utf-8"))
        self.assertEqual(payload["schema"], FX_SNAPSHOT_SCHEMA)
        self.assertEqual(payload["display_pair"], "AUD/CNY")
        self.assertIn("api.frankfurter.dev", payload["source_url"])
        self.assertTrue(payload["network_refresh_used"])
        self.assertFalse(payload["ordinary_runtime_network_refresh"])
        self.assertTrue(validate_snapshot_hash(payload))

    def test_web_shell_stage2_visible_fx_and_main_amounts_use_cny(self) -> None:
        html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        js = (ROOT / "web" / "app" / "shell.js").read_text(encoding="utf-8")

        self.assertIn("AUD/CNY=", html)
        self.assertIn("data-fx-cache-state=\"cached\"", html)
        self.assertIn("CNY 0.00", html)
        self.assertNotIn(">AUD 0.00<", html)
        self.assertIn("AUD/CNY 06:00 快照", js)
        self.assertIn("rateAudToCny: 4.6874", js)
        self.assertIn("const FX_TO_CNY", js)
        self.assertIn('moneyLabel(invSummary.total_market_value_aud, "AUD")', js)
        self.assertIn("formatCnyAmount(toCnyAmount(value, sourceCurrency))", js)


if __name__ == "__main__":
    unittest.main()
