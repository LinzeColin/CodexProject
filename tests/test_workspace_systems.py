from __future__ import annotations

import json
import tempfile
from pathlib import Path

from quantlab.integrations.workspace_systems import compact_workspace_system_payload, load_workspace_system_summary


def test_workspace_summary_compacts_manifest_without_legacy_paths() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        systems_root = Path(tmp) / "systems"
        system_root = systems_root / "finance_ledger"
        sample_root = system_root / "source" / "data" / "sample"
        sample_root.mkdir(parents=True)
        (sample_root / "sample.json").write_text("{}", encoding="utf-8")
        (system_root / "SYSTEM_MANIFEST.json").write_text(
            json.dumps(
                {
                    "system_id": "finance_ledger",
                    "display_name": "Finance Ledger / Consumption Analysis",
                    "status": "source_migrated",
                    "migration_phase": "source_tests_docs_migrated",
                    "legacy_local_roots": ["/Users/local/private/source"],
                    "source_root": "source",
                    "entrypoints": ["a", "b", "c", "d"],
                    "verification": ["v1", "v2", "v3", "v4"],
                    "next_actions": ["n1", "n2", "n3", "n4"],
                    "data_policy": {"runtime": "private", "samples": "synthetic", "secrets": "excluded", "extra": "drop"},
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        summary = load_workspace_system_summary("finance_ledger", systems_root=systems_root)
        payload = summary.to_dict()

        assert payload["adapter_status"] == "Ready"
        assert payload["legacy_root_count"] == 1
        assert "/Users/local/private/source" not in json.dumps(payload, ensure_ascii=False)
        assert payload["entrypoints"] == ["a", "b", "c"]
        assert payload["sample_file_count"] == 1


def test_compact_workspace_payload_reports_review_systems() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        systems_root = Path(tmp) / "systems"
        payload = compact_workspace_system_payload(systems_root=systems_root, system_ids=("missing_system",))

        assert payload["schema"] == "WorkspaceSystemSummaryV1"
        assert payload["ready_count"] == 0
        assert payload["review_systems"] == ["missing_system"]
