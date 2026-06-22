from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from arxiv_daily_push.storage import (
    STORAGE_OBJECT_TABLES,
    STORAGE_RELATION_TYPES,
    STORAGE_SCHEMA_VERSION,
    inspect_database,
    migrate_database,
    rollback_database,
    store_source_item,
    validate_storage_report,
)


def sample_source_item() -> dict:
    return {
        "source_id": "arxiv:2401.00001",
        "source_type": "arxiv",
        "source_adapter": "arxiv.atom.v1",
        "stable_id": "2401.00001",
        "title": "A Useful Storage Paper",
        "retrieved_at": "2026-07-01T05:00:00+10:00",
        "published_at": "2026-06-30T12:00:00Z",
        "updated_at": "2026-06-30T12:00:00Z",
        "canonical_url": "https://arxiv.org/abs/2401.00001",
        "metadata": {"authors": ["Example Author"], "categories": ["cs.AI"], "summary": "SQLite evidence graph"},
        "content_refs": [{"ref_id": "abstract", "ref_type": "html", "uri": "https://arxiv.org/abs/2401.00001"}],
        "license": {"status": "unknown", "usage": "private_learning_link_only"},
    }


class StorageTests(unittest.TestCase):
    def test_migrate_creates_wal_fts_and_required_object_tables(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "adp.sqlite3"
            report = migrate_database(db_path)

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["schema_version"], STORAGE_SCHEMA_VERSION)
            self.assertEqual(report["journal_mode"], "wal")
            self.assertTrue(report["fts5_ready"])
            self.assertEqual(set(report["object_tables"]), set(STORAGE_OBJECT_TABLES))
            self.assertIn("VERSION_OF", report["relation_types"])
            self.assertIn("DERIVED_FROM", report["relation_types"])
            self.assertFalse(validate_storage_report(report))

    def test_store_source_item_is_idempotent_and_searchable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "adp.sqlite3"
            migrate_database(db_path)

            first = store_source_item(db_path, sample_source_item(), fetch_run_id="fetch-001")
            second = store_source_item(db_path, sample_source_item(), fetch_run_id="fetch-001")

            self.assertEqual(first["status"], "pass")
            self.assertEqual(first["document_id"], second["document_id"])
            conn = sqlite3.connect(db_path)
            try:
                doc_count = conn.execute("SELECT COUNT(*) FROM canonical_documents").fetchone()[0]
                version_count = conn.execute("SELECT COUNT(*) FROM document_versions").fetchone()[0]
                fts_hits = conn.execute("SELECT COUNT(*) FROM document_fts WHERE document_fts MATCH 'SQLite'").fetchone()[0]
            finally:
                conn.close()
            self.assertEqual(doc_count, 1)
            self.assertEqual(version_count, 1)
            self.assertEqual(fts_hits, 1)

    def test_rollback_drops_stage1_schema(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "adp.sqlite3"
            migrate_database(db_path)
            report = rollback_database(db_path)

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["schema_version"], 0)
            self.assertIn("canonical_documents", report["dropped_tables"])
            inspect_report = inspect_database(db_path)
            self.assertEqual(inspect_report["status"], "blocked")
            self.assertIn("schema_version is 0", " ".join(inspect_report["blocking_reasons"]))


if __name__ == "__main__":
    unittest.main()
