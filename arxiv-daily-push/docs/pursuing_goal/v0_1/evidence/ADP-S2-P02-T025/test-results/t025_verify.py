#!/usr/bin/env python3
"""ADP-S2-P02-T025 DocumentVersion migration+rollback verification on an ISOLATED
in-memory SQLite copy. Never touches production D1. Acceptance:
  - 迁移前后行数/关系校验 (row-count + relationship checks before/after migration)
  - 回滚在隔离副本成功 (rollback succeeds on an isolated copy; scoped, keeps prior data)
"""
import sqlite3, pathlib, sys

SCHEMA_DIR = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/arxiv-daily-push/docs/pursuing_goal/v0_1/schemas")
MIG = (SCHEMA_DIR / "document_version.migration.sql").read_text(encoding="utf-8")
RBK = (SCHEMA_DIR / "document_version.rollback.sql").read_text(encoding="utf-8")

db = sqlite3.connect(":memory:")
db.execute("PRAGMA foreign_keys=ON")

# --- production-like precondition: cn_meta already exists with an unrelated row ---
db.execute("CREATE TABLE cn_meta(key TEXT PRIMARY KEY, value TEXT)")
db.execute("INSERT INTO cn_meta(key,value) VALUES('cn_schema','adp.v03')")
db.commit()

def tables():
    return sorted(r[0] for r in db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"))
def indexes():
    return sorted(r[0] for r in db.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_docver%'"))

print("PRE-migration tables:", tables())
print("PRE-migration cn_meta rows:", db.execute("SELECT count(*) FROM cn_meta").fetchone()[0])

# --- apply migration (idempotent: run twice to prove IF NOT EXISTS / INSERT OR IGNORE) ---
db.executescript(MIG); db.commit()
db.executescript(MIG); db.commit()   # second apply must not error or duplicate
print("POST-migration tables:", tables())
print("POST-migration indexes:", indexes())

# --- seed: one canonical document with an append-only 2-version chain ---
db.execute("INSERT INTO cn_documents(canonical_id,title_norm,sources_json,current_version_no,created_at,first_seen_at)"
           " VALUES('doi:10.1000/x','a title','[\"nature\"]',2,'2016-03-01','2016-03-01')")
db.execute("INSERT INTO cn_document_versions(version_id,canonical_id,version_no,content_hash,status,doc_date,artifact_keys_json,created_at)"
           " VALUES('doi:10.1000/x#1','doi:10.1000/x',1,'hashv1','superseded','2016-03-01','[\"raw/nature/1/aa/bb/h1.xml\"]','2016-03-01')")
db.execute("INSERT INTO cn_document_versions(version_id,canonical_id,version_no,content_hash,status,doc_date,artifact_keys_json,created_at)"
           " VALUES('doi:10.1000/x#2','doi:10.1000/x',2,'hashv2','active','2016-06-01','[\"raw/nature/2/cc/dd/h2.xml\"]','2016-06-01')")
db.commit()

docs = db.execute("SELECT count(*) FROM cn_documents").fetchone()[0]
vers = db.execute("SELECT count(*) FROM cn_document_versions").fetchone()[0]
orphans = db.execute("SELECT count(*) FROM cn_document_versions v "
                     "LEFT JOIN cn_documents d ON v.canonical_id=d.canonical_id WHERE d.canonical_id IS NULL").fetchone()[0]
v1_hash = db.execute("SELECT content_hash FROM cn_document_versions WHERE version_no=1").fetchone()[0]
v2_hash = db.execute("SELECT content_hash FROM cn_document_versions WHERE version_no=2").fetchone()[0]
history_preserved = (vers == 2 and v1_hash == 'hashv1' and v2_hash == 'hashv2')
print(f"rows: docs={docs} versions={vers} | orphan versions (FK relationship)={orphans} | "
      f"history preserved (v1 not overwritten by v2)={history_preserved}")

# --- UNIQUE(canonical_id,version_no) must block a duplicate version_no ---
try:
    db.execute("INSERT INTO cn_document_versions(version_id,canonical_id,version_no,content_hash,artifact_keys_json)"
               " VALUES('doi:10.1000/x#2b','doi:10.1000/x',2,'dupe','[]')")
    db.commit(); unique_enforced = False
except sqlite3.IntegrityError:
    db.rollback(); unique_enforced = True
print("UNIQUE(canonical_id,version_no) enforced:", "YES" if unique_enforced else "NO")

meta_schema = db.execute("SELECT value FROM cn_meta WHERE key='document_version_schema'").fetchone()
print("schema_version registered in cn_meta:", meta_schema[0] if meta_schema else None)

# --- rollback on the isolated copy ---
db.executescript(RBK); db.commit()
post_tables = tables(); post_idx = indexes()
mig_objs_gone = (post_tables == ['cn_meta'] and post_idx == [])
cn_meta_kept = db.execute("SELECT count(*) FROM cn_meta WHERE key='cn_schema'").fetchone()[0] == 1
schema_key_gone = db.execute("SELECT count(*) FROM cn_meta WHERE key='document_version_schema'").fetchone()[0] == 0
print("POST-rollback tables:", post_tables, "| indexes:", post_idx)
print("rollback: migration objects removed:", mig_objs_gone,
      "| pre-existing cn_meta kept:", cn_meta_kept,
      "| schema_version key removed:", schema_key_gone)

ok = all([docs == 1, vers == 2, orphans == 0, history_preserved, unique_enforced,
          meta_schema is not None, mig_objs_gone, cn_meta_kept, schema_key_gone])
print("\nACCEPTANCE (migration row/relationship checks + isolated rollback) =", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
