-- ADP D1 只读镜像 schema（本机 SQLite 为主库，单向推送；云端只写 events_inbox 回传队列）
CREATE TABLE IF NOT EXISTS mirror_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS lessons_mirror (
  id TEXT PRIMARY KEY, as_of_date TEXT NOT NULL, doc_title TEXT NOT NULL,
  canonical_url TEXT NOT NULL, sections_json TEXT NOT NULL,
  generator TEXT NOT NULL, status TEXT NOT NULL, template_ver TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS selections_mirror (
  run_id TEXT PRIMARY KEY, as_of_date TEXT NOT NULL, score REAL,
  why TEXT, why_not_next TEXT, abstain INTEGER NOT NULL, abstain_reason TEXT
);

CREATE TABLE IF NOT EXISTS manifests_mirror (
  run_id TEXT PRIMARY KEY, result TEXT NOT NULL, trigger_kind TEXT NOT NULL,
  counts_json TEXT NOT NULL, note TEXT
);

CREATE TABLE IF NOT EXISTS review_mirror (
  item_id TEXT PRIMARY KEY, due_at TEXT, stability REAL, difficulty REAL,
  evidence_state TEXT, manual_state TEXT
);

-- 云端唯一可写面：Owner 在手机上的回忆评分回传队列（本机 adp mirror pull 消费）
CREATE TABLE IF NOT EXISTS events_inbox (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  lesson_id TEXT NOT NULL, grade INTEGER NOT NULL CHECK (grade BETWEEN 1 AND 4),
  created_at TEXT NOT NULL, applied INTEGER NOT NULL DEFAULT 0
);
