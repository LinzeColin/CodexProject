from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout
from copy import deepcopy
from pathlib import Path

from arxiv_daily_push.cli import main
from arxiv_daily_push.owner_controls import load_owner_controls
from arxiv_daily_push.source_registry import (
    CONNECTOR_CONTRACT_VERSION,
    SOURCE_REGISTRY_MODEL_ID,
    STAGE1_ACTIVE_ADAPTER_ID,
    STAGE1_MAX_CANARY_RESULTS,
    build_source_registry_report,
    validate_source_registry_report,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = Path(__file__).parent / "fixtures" / "arxiv_atom_sample.xml"
CONTROLS = ROOT / "config" / "owner_controls.yaml"


class SourceRegistryTests(unittest.TestCase):
    def test_source_registry_passes_with_owner_controls_and_fixture(self) -> None:
        controls = load_owner_controls(CONTROLS)
        report = build_source_registry_report(
            controls,
            generated_at="2026-06-22T19:30:00+10:00",
            fixture_atom=FIXTURE.read_text(encoding="utf-8"),
        )

        self.assertEqual(report["model_id"], SOURCE_REGISTRY_MODEL_ID)
        self.assertEqual(report["contract_version"], CONNECTOR_CONTRACT_VERSION)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["active_source_ids"], ["SRC-ARXIV"])
        self.assertEqual(report["active_adapter"]["source_adapter"], STAGE1_ACTIVE_ADAPTER_ID)
        self.assertEqual(report["connector_contract"]["max_canary_results"], STAGE1_MAX_CANARY_RESULTS)
        self.assertEqual(report["fixture_validation"]["source_ids"], ["arxiv:2401.00001"])
        self.assertEqual(validate_source_registry_report(report, controls=controls), [])

    def test_source_registry_blocks_non_arxiv_enabled_source_in_window_a(self) -> None:
        controls = load_owner_controls(CONTROLS)
        changed = deepcopy(controls)
        for source in changed["sources"]:
            if source["source_id"] == "SRC-TOP-JOURNALS":
                source["enabled"] = True
                source["health_status"] = "active"

        report = build_source_registry_report(
            changed,
            generated_at="2026-06-22T19:30:00+10:00",
            fixture_atom=FIXTURE.read_text(encoding="utf-8"),
        )

        self.assertEqual(report["status"], "blocked")
        self.assertIn("Stage 1 Window A may enable only SRC-ARXIV", " ".join(report["blocking_reasons"]))

    def test_source_registry_cli_outputs_json_without_network(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            result = main([
                "source-registry",
                "--controls",
                str(CONTROLS),
                "--fixture-atom",
                str(FIXTURE),
                "--generated-at",
                "2026-06-22T19:30:00+10:00",
                "--json",
            ])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["status"], "pass")
        self.assertFalse(payload["connector_contract"]["pdf_download_enabled"])
        self.assertFalse(payload["connector_contract"]["bulk_harvest_enabled"])


if __name__ == "__main__":
    unittest.main()
