from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
MANIFEST_SCRIPT = SCRIPTS / "raw_archive_manifest.py"
AUDIT_SCRIPT = SCRIPTS / "audit_memory_atlas_public_raw.py"
FACET_SCRIPT = SCRIPTS / "extract_memory_atlas_facets.py"


def load_module(name: str, path: Path):
    sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def seed_all_source_families(database: Path) -> None:
    write_json(database / "data/public_raw/chatgpt/conversation.aaa.json", {"text": "chat"})
    write_json(database / "data/public_raw/codex/session.aaa.json", {"text": "codex"})
    write_json(
        database / "data/public_raw/agents/reviewer/event.aaa.json",
        {"text": "review"},
    )


class RawManifestIntegrityTests(unittest.TestCase):
    def test_manifest_run_is_immutable_and_identical_regeneration_is_idempotent(self) -> None:
        module = load_module("r7_raw_manifest_immutable", MANIFEST_SCRIPT)
        with tempfile.TemporaryDirectory() as temp_dir:
            database = Path(temp_dir)
            seed_all_source_families(database)

            first = module.generate_raw_manifest(
                database,
                "v1_2_r7_unit",
                imported_at="2026-07-11T00:00:00Z",
                require_non_empty=True,
            )
            manifest_path = database / first["manifest_path"]
            first_bytes = manifest_path.read_bytes()
            first_mtime = manifest_path.stat().st_mtime_ns

            second = module.generate_raw_manifest(
                database,
                "v1_2_r7_unit",
                imported_at="2026-07-11T00:00:00Z",
                require_non_empty=True,
            )
            self.assertEqual(manifest_path.read_bytes(), first_bytes)
            self.assertEqual(manifest_path.stat().st_mtime_ns, first_mtime)
            self.assertEqual(second["manifest_sha256"], first["manifest_sha256"])
            self.assertTrue(second["idempotent"])

            with self.assertRaises(module.ManifestConflict):
                module.generate_raw_manifest(
                    database,
                    "v1_2_r7_unit",
                    imported_at="2026-07-11T00:00:01Z",
                    require_non_empty=True,
                )
            with self.assertRaises(module.ManifestConflict):
                module.manifest_path_for(database, " v1_2_r7_unit")

            write_json(
                database / "data/public_raw/chatgpt/conversation.bbb.json",
                {"text": "new immutable version"},
            )
            with self.assertRaises(module.ManifestConflict):
                module.generate_raw_manifest(
                    database,
                    "v1_2_r7_unit",
                    imported_at="2026-07-11T00:00:00Z",
                    require_non_empty=True,
                )

    def test_union_ledger_preserves_versions_and_rejects_drift_or_deletion(self) -> None:
        module = load_module("r7_raw_manifest_union", MANIFEST_SCRIPT)
        old = {
            "source_id": "chatgpt",
            "relative_path": "chatgpt/conversation.aaa.json",
            "sha256": "a" * 64,
            "imported_at": "2026-07-11T00:00:00Z",
            "size_bytes": 10,
        }
        new = {
            "source_id": "chatgpt",
            "relative_path": "chatgpt/conversation.bbb.json",
            "sha256": "b" * 64,
            "imported_at": "2026-07-11T00:01:00Z",
            "size_bytes": 11,
        }

        union = module.update_hash_ledger([old], [old, new])
        self.assertEqual(union, [old, new])
        with self.assertRaises(module.ManifestConflict):
            module.update_hash_ledger([old], [{**old, "sha256": "c" * 64}])
        with self.assertRaises(module.ManifestConflict):
            module.update_hash_ledger([old], [])

    def test_non_empty_gate_requires_chatgpt_codex_and_agent_sources(self) -> None:
        module = load_module("r7_raw_manifest_sources", MANIFEST_SCRIPT)
        with tempfile.TemporaryDirectory() as temp_dir:
            database = Path(temp_dir)
            with self.assertRaises(module.ManifestConflict):
                module.generate_raw_manifest(
                    database,
                    "empty",
                    imported_at="2026-07-11T00:00:00Z",
                    require_non_empty=True,
                )

            write_json(database / "data/public_raw/chatgpt/conversation.json", {"text": "chat"})
            write_json(database / "data/public_raw/codex/session.json", {"text": "codex"})
            with self.assertRaises(module.ManifestConflict):
                module.generate_raw_manifest(
                    database,
                    "missing_agent",
                    imported_at="2026-07-11T00:00:00Z",
                    require_non_empty=True,
                )

            write_json(
                database / "data/public_raw/agents/reviewer/event.json",
                {"text": "review"},
            )
            result = module.generate_raw_manifest(
                database,
                "complete",
                imported_at="2026-07-11T00:00:00Z",
                require_non_empty=True,
            )

        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["source_families"], ["agent:reviewer", "chatgpt", "codex"])

    def test_invalid_ledger_error_does_not_expose_database_absolute_path(self) -> None:
        module = load_module("r7_raw_manifest_private_error", MANIFEST_SCRIPT)
        with tempfile.TemporaryDirectory() as temp_dir:
            database = Path(temp_dir)
            ledger = module.hash_ledger_path(database)
            ledger.parent.mkdir(parents=True)
            ledger.write_text("{not-json}\n", encoding="utf-8")

            with self.assertRaises(module.ManifestConflict) as captured:
                module.generate_raw_manifest(
                    database,
                    "private_error",
                    imported_at="2026-07-11T00:00:00Z",
                )

        self.assertNotIn(str(database), str(captured.exception))
        self.assertIn("raw_hash_ledger.jsonl", str(captured.exception))


class PublicRawAuditTests(unittest.TestCase):
    def test_all_size_audit_finds_private_text_and_unmarked_binary_without_echoing_it(self) -> None:
        module = load_module("r7_public_raw_audit", AUDIT_SCRIPT)
        with tempfile.TemporaryDirectory() as temp_dir:
            database = Path(temp_dir)
            synthetic_secret = "sk-" + "A" * 24
            synthetic_path = "/Users/example/private/source.json"
            large_text = "ordinary transcript " * 70_000
            unsafe_path = database / "data/public_raw/chatgpt/large.jsonl"
            write_jsonl(
                unsafe_path,
                [{"text": large_text + synthetic_secret + " " + synthetic_path}],
            )
            data_url_path = database / "data/public_raw/codex/session.jsonl"
            write_jsonl(
                data_url_path,
                [{"payload": "data:application/octet-stream;base64,AAECAwQ="}],
            )

            failed = module.audit_public_raw(database)
            serialized = json.dumps(failed, ensure_ascii=False)
            self.assertGreater(unsafe_path.stat().st_size, 1_000_000)
            self.assertEqual(failed["status"], "FAIL")
            self.assertGreaterEqual(failed["credential_or_private_text_file_count"], 1)
            self.assertEqual(failed["unmarked_binary_file_count"], 1)
            self.assertNotIn(synthetic_secret, serialized)
            self.assertNotIn(synthetic_path, serialized)

            marker_source = "data:application/octet-stream;base64,AAECAwQ="
            marker = (
                "[REDACTED_BINARY sha256="
                + hashlib.sha256(marker_source.encode("utf-8")).hexdigest()
                + f" bytes={len(marker_source.encode('utf-8'))} "
                + "reason=non_text_binary_not_transcript]"
            )
            write_jsonl(unsafe_path, [{"text": large_text}])
            write_jsonl(data_url_path, [{"payload": marker}])
            passed = module.audit_public_raw(database)
            limited = module.audit_public_raw(database, max_file_bytes=128)

        self.assertEqual(passed["status"], "PASS", passed)
        self.assertEqual(passed["file_count"], 2)
        self.assertEqual(passed["binary_marker_count"], 1)
        self.assertEqual(limited["status"], "FAIL")
        self.assertEqual(limited["oversize_file_count"], 2)


class VersionAwareFacetTests(unittest.TestCase):
    def test_facets_use_only_current_version_and_exact_raw_transcript_refs(self) -> None:
        module = load_module("r7_version_aware_facets", FACET_SCRIPT)
        with tempfile.TemporaryDirectory() as temp_dir:
            database = Path(temp_dir)

            write_json(
                database / "data/public_raw/chatgpt/conv-1.aaaaaaaaaaaa.json",
                {
                    "conversation_id": "conv-1",
                    "title": "Old ChatGPT version",
                    "updated_at": "2026-07-10T00:00:00Z",
                    "message_count": 1,
                },
            )
            current_chatgpt = "data/public_raw/chatgpt/conv-1.bbbbbbbbbbbb.json"
            write_json(
                database / current_chatgpt,
                {
                    "conversation_id": "conv-1",
                    "title": "Current ChatGPT version",
                    "updated_at": "2026-07-11T00:00:00Z",
                    "message_count": 2,
                },
            )
            write_json(
                database / "data/public_raw/chatgpt/conv-stale.cccccccccccc.json",
                {
                    "conversation_id": "conv-stale",
                    "title": "Historical conversation absent from current export",
                    "updated_at": "2026-07-11T00:00:01Z",
                    "message_count": 1,
                },
            )
            write_jsonl(
                database / "data/processed/conversations/conversation_manifest.jsonl",
                [
                    {
                        "conversation_id": "conv-1",
                        "raw_ref": current_chatgpt,
                        "updated_at": "2026-07-11T00:00:00Z",
                    }
                ],
            )

            old_chunk = "data/public_raw/codex/sessions/session-1.old.part-0001.jsonl"
            current_chunk = "data/public_raw/codex/sessions/session-1.new.part-0001.jsonl"
            write_jsonl(database / old_chunk, [{"type": "message", "payload": {"text": "old"}}])
            write_jsonl(database / current_chunk, [{"type": "message", "payload": {"text": "new"}}])
            write_json(
                database / "data/public_raw/codex/codex_public_raw_snapshot.old.json",
                {
                    "generated_at": "2026-07-10T00:00:00Z",
                    "sessions": [{"session_id": "session-1", "thread_name": "Old Codex"}],
                    "public_transcript_exports": [
                        {"session_id": "session-1", "chunk_refs": [old_chunk]}
                    ],
                },
            )
            write_json(
                database / "data/public_raw/codex/codex_public_raw_snapshot.new.json",
                {
                    "generated_at": "2026-07-11T00:00:00Z",
                    "sessions": [
                        {
                            "session_id": "session-1",
                            "thread_name": "Current Codex transcript",
                            "updated_at": "2026-07-11T00:00:00Z",
                            "message_count": 3,
                        }
                    ],
                    "public_transcript_exports": [
                        {"session_id": "session-1", "chunk_refs": [current_chunk]}
                    ],
                },
            )

            write_json(
                database / "data/public_raw/agents/codex-reviewer/review-1.old.json",
                {
                    "agent_id": "codex-reviewer",
                    "agent_name": "Codex Reviewer",
                    "event_id": "review-1",
                    "title": "Old review",
                    "updated_at": "2026-07-10T00:00:00Z",
                },
            )
            current_agent = "data/public_raw/agents/codex-reviewer/review-1.new.json"
            write_json(
                database / current_agent,
                {
                    "agent_id": "codex-reviewer",
                    "agent_name": "Codex Reviewer",
                    "adapter_mode": "manual_markdown_import",
                    "source_format": "markdown_report",
                    "event_id": "review-1",
                    "title": "Current real reviewer report",
                    "updated_at": "2026-07-11T00:00:00Z",
                    "message_count": 1,
                },
            )

            result = module.extract_facets(
                database,
                dry_run=True,
                generated_at="2026-07-11T00:01:00Z",
            )

        self.assertEqual(result["event_count"], 3, result)
        by_source = {event["source"]: event for event in result["events"]}
        self.assertEqual(by_source["chatgpt"]["raw_ref"], current_chatgpt)
        self.assertEqual(by_source["codex"]["raw_ref"], current_chunk)
        self.assertEqual(by_source["future_agent"]["raw_ref"], current_agent)
        self.assertNotIn("evidence_missing_reason", by_source["codex"])
        self.assertEqual(
            by_source["future_agent"]["future_agent_source"]["source_type"],
            "other_agent",
        )


if __name__ == "__main__":
    unittest.main()
