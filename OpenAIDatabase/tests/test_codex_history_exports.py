import importlib.util
import json
import sqlite3
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPORTER = ROOT / "scripts/export_codex_history_archives.py"
AUTO_UPDATE = ROOT / "scripts/run_codex_memory_auto_update.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CodexHistoryExportTests(unittest.TestCase):
    def test_exports_token_usage_and_session_snapshot_without_mutating_codex_home(self) -> None:
        module = load_module(EXPORTER, "export_codex_history_archives")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            codex_home = root / ".codex"
            database_dir = root / "OpenAIDatabase"
            session_path = codex_home / "sessions/2026/06/30/session.jsonl"
            session_path.parent.mkdir(parents=True)
            session_path.write_text('{"type":"session_meta","payload":{"id":"s1"}}\n', encoding="utf-8")
            index_path = codex_home / "session_index.jsonl"
            index_path.write_text('{"id":"s1","thread_name":"history export"}\n', encoding="utf-8")
            logs_path = codex_home / "logs_2.sqlite"
            con = sqlite3.connect(logs_path)
            con.execute(
                "CREATE TABLE logs (id INTEGER, ts INTEGER, ts_nanos INTEGER, level TEXT, target TEXT, "
                "thread_id TEXT, process_uuid TEXT, estimated_bytes INTEGER, feedback_log_body TEXT)"
            )
            con.execute(
                "INSERT INTO logs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    1,
                    1782730000,
                    0,
                    "INFO",
                    "codex",
                    "thread-1",
                    "process-1",
                    100,
                    '{"usage":{"input_tokens":10,"output_tokens":3,"total_tokens":13,'
                    '"input_tokens_details":{"cached_tokens":4},'
                    '"output_tokens_details":{"reasoning_tokens":2}}}',
                ),
            )
            con.commit()
            con.close()

            before = {
                "session": session_path.read_text(encoding="utf-8"),
                "index": index_path.read_text(encoding="utf-8"),
                "logs_bytes": logs_path.read_bytes(),
            }
            token = module.export_token_usage(codex_home, database_dir / "token_usage/current-mac-latest")
            session = module.export_session_history(
                codex_home,
                database_dir / "session_history/current-mac-latest",
                part_bytes=1024,
            )

            self.assertEqual(token["deduped_totals"]["total_tokens"], 13)
            self.assertEqual(session["session_jsonl_count"], 1)
            self.assertTrue((database_dir / "token_usage/current-mac-latest/data/summary.json").exists())
            self.assertTrue((database_dir / "session_history/current-mac-latest/manifest.json").exists())
            self.assertEqual(session_path.read_text(encoding="utf-8"), before["session"])
            self.assertEqual(index_path.read_text(encoding="utf-8"), before["index"])
            self.assertEqual(logs_path.read_bytes(), before["logs_bytes"])

    def test_auto_update_exports_session_history_on_mondays_only(self) -> None:
        module = load_module(AUTO_UPDATE, "run_codex_memory_auto_update")
        self.assertTrue(module.should_export_session_history(datetime(2026, 7, 6, 3, 0)))
        self.assertFalse(module.should_export_session_history(datetime(2026, 7, 8, 3, 0)))
        self.assertFalse(module.should_export_session_history(datetime(2026, 7, 10, 3, 0)))


if __name__ == "__main__":
    unittest.main()
