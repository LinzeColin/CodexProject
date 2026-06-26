from __future__ import annotations

import unittest

from pfi_v02.stage2_registry import (
    REQUIRED_STAGE2_SOURCE_IDS,
    build_connector_profile,
    build_stage2_registry,
    build_stage2_registry_contract,
    validate_stage2_registry,
)


class Stage2DataSourceRegistryTest(unittest.TestCase):
    def test_registry_contains_all_core_sources(self) -> None:
        registry = build_stage2_registry()

        self.assertEqual(set(REQUIRED_STAGE2_SOURCE_IDS), set(registry))
        for source_id in REQUIRED_STAGE2_SOURCE_IDS:
            registry[source_id].validate()

    def test_registry_declares_modes_credentials_freshness_and_boundaries(self) -> None:
        registry = build_stage2_registry()

        for source_id, profile in registry.items():
            self.assertTrue(profile.primary_acquisition, source_id)
            self.assertTrue(profile.credential_requirements, source_id)
            self.assertTrue(profile.freshness_target, source_id)
            self.assertTrue(profile.parser_contracts, source_id)
            self.assertTrue(profile.ledger_boundaries, source_id)
            self.assertTrue(profile.read_only, source_id)
            self.assertFalse(profile.requires_trading_password, source_id)

    def test_non_csv_sources_do_not_assume_csv_primary_contracts(self) -> None:
        registry = build_stage2_registry()

        self.assertNotIn("CSV", " ".join(registry["alipay_fund"].primary_acquisition))
        self.assertNotIn("CSV", " ".join(registry["cn_broker"].primary_acquisition))
        self.assertNotIn("CSV", " ".join(registry["abc_bullion"].primary_acquisition))
        self.assertIn("do_not_assume_csv", registry["alipay_fund"].ledger_boundaries)
        self.assertIn("do_not_assume_universal_csv", registry["cn_broker"].ledger_boundaries)
        self.assertIn("do_not_rely_on_csv", registry["abc_bullion"].ledger_boundaries)

    def test_moomoo_contract_references_existing_qbvs_runtime(self) -> None:
        registry = build_stage2_registry()

        refs = registry["moomoo_au"].active_runtime_refs
        self.assertIn("PFI/modules/qbvs_lab/qbvs/datasources.py", refs)
        self.assertIn("PFI/modules/qbvs_lab/qbvs/moomoo_batch.py", refs)

    def test_new_platform_extends_by_profile_without_core_ledger_rewrite(self) -> None:
        profile = build_connector_profile(
            source_id="new_wallet",
            display_name="New Wallet",
            domains=("cashflow",),
            primary_acquisition=("NEW_WALLET_STATEMENT",),
            field_mapping=("date_field", "amount_field", "description_field"),
        )

        self.assertEqual(profile.extension_kind, "PLUGIN")
        self.assertIn("new_platform_must_not_rewrite_core_ledger", profile.ledger_boundaries)
        profile.validate()

    def test_registry_contract_is_serializable_and_validated(self) -> None:
        contract = build_stage2_registry_contract()

        self.assertEqual(contract["stage"], "PFI V0.2 Stage 2")
        self.assertIn("No trading password", contract["boundaries"])
        self.assertIn("cba_bank", contract["sources"])
        validate_stage2_registry(build_stage2_registry())


if __name__ == "__main__":
    unittest.main()
