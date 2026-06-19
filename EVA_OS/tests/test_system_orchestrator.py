from __future__ import annotations

import json
import sqlite3
import os
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from quantlab.integrations.research_bus_api import process_pending_bus_requests, submit_bus_request, submit_chat_input
from quantlab.config import PROJECT_ROOT
from quantlab.integrations.system_orchestrator import (
    ChildSystemDefinition,
    default_child_systems,
    orchestrate_child_system,
    orchestration_runs_frame,
    register_child_systems,
    sync_child_system_artifacts,
    system_artifacts_frame,
    system_registry_frame,
)


class SystemOrchestratorTest(unittest.TestCase):
    def test_registers_child_systems_and_indexes_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "ResearchBus.sqlite"
            child_root = root / "child"
            child_root.mkdir()
            (child_root / "report.md").write_text("# Report\n", encoding="utf-8")
            system = _test_system(child_root)

            registry = register_child_systems([system], db_path=db_path)
            artifacts = sync_child_system_artifacts([system], db_path=db_path)
            registry_frame = system_registry_frame(db_path)
            artifact_frame = system_artifacts_frame(db_path)

            self.assertEqual(registry["registered_systems"], 1)
            self.assertEqual(artifacts["system_artifacts"], 1)
            self.assertEqual(registry_frame.iloc[0]["system_name"], "UnitChildSystem")
            self.assertEqual(artifact_frame.iloc[0]["title"], "report.md")

    def test_orchestration_dry_run_records_command_without_executing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "ResearchBus.sqlite"

            result = orchestrate_child_system("IndependentValidation", action="health", execute=False, db_path=db_path)
            runs = orchestration_runs_frame(db_path)

            self.assertEqual(result.status, "Planned")
            self.assertEqual(result.mode, "dry_run")
            self.assertEqual(runs.iloc[0]["target_system"], "IndependentValidation")

    def test_registered_test_system_can_execute_health_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "ResearchBus.sqlite"
            child_root = root / "child"
            child_root.mkdir()
            system = _test_system(child_root)
            register_child_systems([system], db_path=db_path)

            # Execute through the public request path using a default built-in system for stable lookup.
            request = submit_bus_request(
                "orchestrate_system",
                {"system_name": "IndependentValidation", "action": "health", "execute": False},
                db_path=db_path,
            )
            processed = process_pending_bus_requests(system_name="ResearchBus", db_path=db_path)

            with sqlite3.connect(db_path) as conn:
                response = json.loads(conn.execute("SELECT response_json FROM bus_api_requests WHERE request_id=?", (request.request_id,)).fetchone()[0])

            self.assertEqual(processed["processed"], 1)
            self.assertEqual(response["status"], "Planned")

    def test_chat_input_routes_fifa_health_to_orchestration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "ResearchBus.sqlite"
            chat = submit_chat_input("检查 FIFA 子系统状态", source_system="UnitTestChat", db_path=db_path)
            processed = process_pending_bus_requests(system_name="ResearchBus", db_path=db_path)

            with sqlite3.connect(db_path) as conn:
                run = conn.execute("SELECT target_system, action, status FROM orchestration_runs").fetchone()

            self.assertEqual(chat["classification"], "orchestration")
            self.assertEqual(processed["processed"], 1)
            self.assertEqual(run, ("FIFA-Research-System", "health", "Planned"))

    def test_default_child_roots_can_be_configured_by_environment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch.dict(os.environ, {"EVA_AI_RESEARCH_ROOT": str(root / "ai"), "EVA_GOVERNMENT_POLICY_ROOT": str(root / "policy")}):
                systems = {system.system_name: system for system in default_child_systems()}

            self.assertEqual(systems["AI-Research-System"].root_path, str(root / "ai"))
            self.assertEqual(systems["GovernmentPolicySystem"].root_path, str(root / "policy"))

    def test_default_child_systems_include_current_workspace_manifests(self) -> None:
        systems = {system.system_name: system for system in default_child_systems()}

        for system_id in ["finance_ledger", "industry_research", "policy_intelligence"]:
            with self.subTest(system_id=system_id):
                system = systems[system_id]
                summary = system.payload["manifest_summary"]
                self.assertEqual(system.role, "WorkspaceChildSystem")
                self.assertEqual(system.root_path, str(PROJECT_ROOT / "systems" / system_id))
                self.assertEqual(summary["system_id"], system_id)
                self.assertEqual(summary["adapter_status"], "Ready")
                self.assertNotIn("/Users/", json.dumps(summary, ensure_ascii=False))

    def test_execute_orchestration_is_denied_without_explicit_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "ResearchBus.sqlite"
            with patch.dict(os.environ, {"EVA_ORCHESTRATOR_EXECUTE_ALLOWED": ""}, clear=False):
                with self.assertRaises(PermissionError):
                    orchestrate_child_system("IndependentValidation", action="health", execute=True, db_path=db_path)


def _test_system(root: Path) -> ChildSystemDefinition:
    return ChildSystemDefinition(
        system_name="UnitChildSystem",
        role="ChildSystem",
        root_path=str(root),
        standalone_command=(sys.executable, "-c", "print('run')"),
        health_command=(sys.executable, "-c", "print('health')"),
        sync_command=(sys.executable, "-c", "print('sync')"),
        capabilities=("unit_test",),
        output_globs=("*.md",),
        environment={},
        payload={},
    )


if __name__ == "__main__":
    unittest.main()
