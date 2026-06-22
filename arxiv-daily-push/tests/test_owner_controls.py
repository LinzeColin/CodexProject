import csv
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from copy import deepcopy
from pathlib import Path

from arxiv_daily_push.cli import main
from arxiv_daily_push.owner_controls import (
    OWNER_CONTROL_DOCS,
    CONTENT_LEDGER_COLUMNS,
    build_owner_impact_preview,
    load_owner_controls,
    render_owner_documents,
    validate_owner_controls,
)


ROOT = Path(__file__).resolve().parents[1]
CONTROLS = ROOT / "config" / "owner_controls.yaml"


class OwnerControlsTests(unittest.TestCase):
    def test_default_owner_controls_validate(self):
        controls = load_owner_controls(CONTROLS)
        report = validate_owner_controls(controls)
        self.assertEqual(report["status"], "pass", report["errors"])
        self.assertFalse(report["production_enabled"])
        self.assertEqual(report["owner_view_files"], list(OWNER_CONTROL_DOCS))
        totals = {item["group_id"]: item for item in report["weight_groups"]}
        self.assertEqual(totals["owner_sources"]["total"], 100.0)
        self.assertEqual(totals["owner_scoring_phase12_roi"]["status"], "pass")

    def test_weight_group_mismatch_blocks_validation(self):
        controls = load_owner_controls(CONTROLS)
        mutated = deepcopy(controls)
        mutated["scoring"]["research"]["relevance"] = 21
        report = validate_owner_controls(mutated)
        self.assertEqual(report["status"], "blocked")
        self.assertTrue(any("owner_scoring_research" in error for error in report["errors"]))

    def test_preview_uses_no_side_effect_replay_boundary(self):
        controls = load_owner_controls(CONTROLS)
        preview = build_owner_impact_preview(controls, days=30)
        self.assertEqual(preview["status"], "pass")
        self.assertEqual(preview["days"], 30)
        self.assertEqual(preview["ranking_change_preview"], "NOT_RUN_UNTIL_S1_06_REPLAY_DATA_EXISTS")
        self.assertIn("SRC-ARXIV", preview["enabled_sources"])

    def test_render_owner_documents_writes_four_generated_views(self):
        controls = load_owner_controls(CONTROLS)
        with tempfile.TemporaryDirectory() as tmp:
            report = render_owner_documents(
                controls,
                project_path=tmp,
                generated_at="2026-06-22T16:30:00+10:00",
                write=True,
            )
            self.assertEqual(report["status"], "rendered")
            for relative_path in OWNER_CONTROL_DOCS:
                path = Path(tmp) / relative_path
                self.assertTrue(path.is_file(), relative_path)
                text = path.read_text(encoding="utf-8")
                self.assertNotIn("['", text)
                self.assertNotIn("{'", text)
            ledger = Path(tmp) / "docs/owner/CONTENT_LEDGER.csv"
            rows = list(csv.DictReader(io.StringIO(ledger.read_text(encoding="utf-8"))))
            self.assertEqual(list(rows[0].keys()), list(CONTENT_LEDGER_COLUMNS))
            self.assertEqual(rows[0]["item_id"], "NO_PRODUCTION_CONTENT_ROWS_S1_03")

    def test_owner_cli_commands(self):
        commands = [
            ["owner", "validate", "--controls", str(CONTROLS), "--json"],
            ["owner", "preview-impact", "--controls", str(CONTROLS), "--days", "30", "--json"],
        ]
        for command in commands:
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                result = main(command)
            self.assertEqual(result, 0, command)
            self.assertEqual(json.loads(buffer.getvalue())["status"], "pass")
        with tempfile.TemporaryDirectory() as tmp:
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                result = main(
                    [
                        "owner",
                        "render-docs",
                        "--controls",
                        str(CONTROLS),
                        "--project-path",
                        tmp,
                        "--generated-at",
                        "2026-06-22T16:30:00+10:00",
                        "--write",
                        "--json",
                    ]
                )
            self.assertEqual(result, 0)
            payload = json.loads(buffer.getvalue())
            self.assertEqual(payload["status"], "rendered")
            self.assertEqual(payload["written_files"], list(OWNER_CONTROL_DOCS))


if __name__ == "__main__":
    unittest.main()
