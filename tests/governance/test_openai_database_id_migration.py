from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from governance_id_audit import _load_path, collect_references  # noqa: E402
from governance_ids import load_registry, parse_identifier  # noqa: E402
from lean_governance import load_project_facts, rendered_project_texts  # noqa: E402


class OpenAIDatabaseIdMigrationTests(unittest.TestCase):
    project_root = ROOT / "OpenAIDatabase"

    def test_mutable_current_and_roadmap_references_are_v2(self) -> None:
        project = _load_path(self.project_root / "docs/governance/project.yaml")
        roadmap = _load_path(self.project_root / "docs/governance/roadmap.yaml")
        references = [
            *collect_references(
                project,
                project="OpenAIDatabase",
                path="OpenAIDatabase/docs/governance/project.yaml",
            ),
            *collect_references(
                roadmap,
                project="OpenAIDatabase",
                path="OpenAIDatabase/docs/governance/roadmap.yaml",
            ),
        ]
        identifier_references = []
        for reference in references:
            parsed = parse_identifier(reference.value, reference.kind)
            identifier_references.append(parsed)
            self.assertEqual(
                parsed.generation,
                "v2",
                f"{reference.path}:{reference.field}={reference.value}",
            )
        self.assertTrue(identifier_references)
        self.assertEqual(
            roadmap["current_task_id"], "TSK.OpenAIDatabase.CLEAN1.0003"
        )
        self.assertEqual(
            roadmap["next_gate_id"], "ACC.OpenAIDatabase.CLEAN1.0003"
        )

    def test_registry_aliases_are_unique_and_migration_is_strict(self) -> None:
        registry = load_registry(ROOT / "governance/id_registry.json")
        self.assertIn("OpenAIDatabase", registry["migrated_projects"])
        aliases = [
            item
            for item in registry["aliases"]
            if item["project"] == "OpenAIDatabase"
        ]
        keys = [
            (item["project"], item["kind"], item["legacy_id"])
            for item in aliases
        ]
        self.assertEqual(len(aliases), 87)
        self.assertEqual(len(keys), len(set(keys)))

    def test_historical_events_stay_append_only_but_render_as_v2(self) -> None:
        events_path = self.project_root / "docs/governance/events.jsonl"
        historical_text = events_path.read_text(encoding="utf-8")
        self.assertIn('"task_id": "S5PBT03"', historical_text)
        project, roadmap, events = load_project_facts(self.project_root)
        development_record = rendered_project_texts(project, roadmap, events)[
            "开发记录.md"
        ]
        self.assertNotIn("| S5PBT03 |", development_record)
        self.assertIn("| TSK.OpenAIDatabase.OPS1.0012 |", development_record)
        self.assertIn("TSK.OpenAIDatabase.CLEAN1.0003", development_record)

    def test_superseded_conversation_drafts_were_not_added(self) -> None:
        canonical = "\n".join(
            (
                self.project_root / "docs/governance/roadmap.yaml"
            ).read_text(encoding="utf-8").splitlines()
        )
        self.assertNotIn("S6PAT01", canonical)
        self.assertNotIn("S11PBT03", canonical)


if __name__ == "__main__":
    unittest.main()
