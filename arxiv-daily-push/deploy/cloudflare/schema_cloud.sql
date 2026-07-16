-- ADP 云端原生 schema（Owner 2026-07-15 指令：网页即主体，系统整体跑在 Cloudflare，
-- 不再依赖 Mac）。所有环节（抓取→选择→讲义→主动回忆→FSRS 排程）都在 Worker + D1 里完成。
-- 与旧镜像表并存；镜像表 R6 退役后可删。

-- 数据源注册表（由 cron 从内置 REGISTRY 播种；对应 boards_v0_3.yaml）
CREATE TABLE IF NOT EXISTS cn_sources (
  id TEXT PRIMARY KEY, board_id TEXT NOT NULL, name TEXT NOT NULL,
  platform TEXT, website TEXT, method TEXT NOT NULL, feed_url TEXT,
  official INTEGER NOT NULL DEFAULT 0, cadence TEXT,
  health TEXT NOT NULL DEFAULT 'active', consecutive_failures INTEGER NOT NULL DEFAULT 0,
  last_fetch TEXT
);

-- 统一候选条目（arXiv 论文 / bioRxiv / 各板块 feed）——全部可进每日精选（Owner 指令）
CREATE TABLE IF NOT EXISTS cn_items (
  id TEXT PRIMARY KEY,             -- 稳定 id：arxiv id 或 sha1(source|link)
  board_id TEXT NOT NULL,
  source_id TEXT NOT NULL,
  kind TEXT NOT NULL,             -- paper | feed
  title TEXT NOT NULL,
  url TEXT NOT NULL,
  summary TEXT NOT NULL DEFAULT '',
  categories TEXT NOT NULL DEFAULT '',   -- 逗号分隔（arXiv）
  authors TEXT NOT NULL DEFAULT '',
  published_at TEXT,
  fetched_at TEXT NOT NULL,
  first_seen_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_cn_items_board ON cn_items (board_id, fetched_at DESC);
CREATE INDEX IF NOT EXISTS idx_cn_items_source ON cn_items (source_id);
CREATE INDEX IF NOT EXISTS idx_cn_items_seen ON cn_items (first_seen_at DESC);

-- 每日精选（跨全部板块选 1）
CREATE TABLE IF NOT EXISTS cn_selections (
  as_of_date TEXT PRIMARY KEY,
  item_id TEXT, score REAL, why TEXT,
  abstain INTEGER NOT NULL DEFAULT 0, abstain_reason TEXT,
  contributions_json TEXT, board_id TEXT, run_at TEXT NOT NULL
);

-- 讲义（确定性模板，八段）
CREATE TABLE IF NOT EXISTS cn_lessons (
  id TEXT PRIMARY KEY, as_of_date TEXT NOT NULL, item_id TEXT NOT NULL,
  doc_title TEXT NOT NULL, url TEXT NOT NULL, sections_json TEXT NOT NULL,
  generator TEXT NOT NULL, template_ver TEXT NOT NULL, created_at TEXT NOT NULL
);

-- FSRS 复习卡（每条学习项一张）
CREATE TABLE IF NOT EXISTS cn_reviews (
  item_id TEXT PRIMARY KEY,
  due_at TEXT, stability REAL, difficulty REAL, reps INTEGER NOT NULL DEFAULT 0,
  lapses INTEGER NOT NULL DEFAULT 0, state INTEGER NOT NULL DEFAULT 0,
  last_review TEXT, last_grade INTEGER, evidence_state TEXT
);

-- 事件流（追加写）：reveal / grade
CREATE TABLE IF NOT EXISTS cn_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  item_id TEXT NOT NULL, kind TEXT NOT NULL, grade INTEGER,
  at TEXT NOT NULL, dedup_key TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_cn_events_dedup ON cn_events (dedup_key) WHERE dedup_key IS NOT NULL;

-- 运行日志（每日流水线的五态 manifest）
CREATE TABLE IF NOT EXISTS cn_run_log (
  run_id TEXT PRIMARY KEY, as_of_date TEXT NOT NULL, result TEXT NOT NULL,
  counts_json TEXT NOT NULL, note TEXT, at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS cn_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);

-- S2-P01-T022 不可变原始证据 R2 双写台账（object_key 作主键 => 幂等，重试不产生重复行）
CREATE TABLE IF NOT EXISTS cn_artifacts (
  object_key TEXT PRIMARY KEY, sha256 TEXT NOT NULL, source_id TEXT NOT NULL,
  url TEXT, mime TEXT, content_length INTEGER, compression TEXT,
  content_version TEXT DEFAULT 'v1', created_at TEXT
);
