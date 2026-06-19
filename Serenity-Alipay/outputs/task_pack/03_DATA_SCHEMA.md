# 03 Data Schema

## SQLite MVP Schema

Use SQLite for MVP. Every table should include `created_at` where useful. Store raw data paths rather than bloating the DB with large blobs.

```sql
CREATE TABLE IF NOT EXISTS run_log (
  run_id TEXT PRIMARY KEY,
  run_time_bj TEXT NOT NULL,
  run_time_au TEXT NOT NULL,
  schedule_slot TEXT NOT NULL,
  model_profile TEXT NOT NULL,
  status TEXT NOT NULL,
  data_quality_status TEXT NOT NULL,
  notification_status TEXT,
  notes TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS asset_master (
  asset_id TEXT PRIMARY KEY,
  asset_code TEXT NOT NULL,
  asset_name TEXT NOT NULL,
  asset_type TEXT NOT NULL,
  market TEXT,
  fund_company TEXT,
  risk_level TEXT,
  is_excluded INTEGER NOT NULL DEFAULT 0,
  exclusion_reason TEXT
);

CREATE TABLE IF NOT EXISTS source_log (
  source_id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL,
  asset_id TEXT,
  source_name TEXT NOT NULL,
  source_type TEXT NOT NULL,
  source_priority INTEGER NOT NULL,
  url_or_path TEXT,
  observed_at TEXT,
  fetched_at TEXT NOT NULL,
  evidence_level TEXT NOT NULL,
  field_list TEXT NOT NULL,
  fallback_aggregated INTEGER NOT NULL DEFAULT 0,
  conflict_group TEXT,
  FOREIGN KEY (run_id) REFERENCES run_log(run_id)
);

CREATE TABLE IF NOT EXISTS fund_nav_snapshot (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT NOT NULL,
  asset_id TEXT NOT NULL,
  nav_date TEXT NOT NULL,
  nav REAL,
  accumulated_nav REAL,
  daily_return REAL,
  nav_source_id TEXT,
  freshness_status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS market_kline_snapshot (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT NOT NULL,
  asset_id TEXT NOT NULL,
  bar_interval TEXT NOT NULL,
  start_time TEXT NOT NULL,
  end_time TEXT NOT NULL,
  open REAL,
  high REAL,
  low REAL,
  close REAL,
  volume REAL,
  turnover REAL,
  source_id TEXT
);

CREATE TABLE IF NOT EXISTS fund_rule_snapshot (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT NOT NULL,
  asset_id TEXT NOT NULL,
  subscription_status TEXT,
  redemption_status TEXT,
  cutoff_time TEXT,
  confirm_lag TEXT,
  redeem_lag TEXT,
  subscription_fee REAL,
  redemption_fee REAL,
  management_fee REAL,
  custody_fee REAL,
  sales_service_fee REAL,
  min_purchase_amount REAL,
  source_id TEXT
);

CREATE TABLE IF NOT EXISTS position_snapshot (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT NOT NULL,
  asset_id TEXT NOT NULL,
  platform TEXT NOT NULL,
  current_amount REAL,
  current_weight REAL,
  cost_basis REAL,
  unrealized_pnl REAL,
  imported_by TEXT NOT NULL,
  source_id TEXT
);

CREATE TABLE IF NOT EXISTS score_snapshot (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT NOT NULL,
  asset_id TEXT NOT NULL,
  total_score REAL NOT NULL,
  data_score REAL NOT NULL,
  timeliness_score REAL NOT NULL,
  source_score REAL NOT NULL,
  return_score REAL NOT NULL,
  risk_score REAL NOT NULL,
  executable_score REAL NOT NULL,
  evidence_coverage REAL NOT NULL,
  grade TEXT NOT NULL,
  hard_block_reason TEXT
);

CREATE TABLE IF NOT EXISTS recommendation_snapshot (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT NOT NULL,
  asset_id TEXT NOT NULL,
  rank INTEGER,
  target_weight REAL,
  current_weight REAL,
  deviation REAL,
  action_label TEXT NOT NULL,
  trigger_reason TEXT NOT NULL,
  next_check_by TEXT,
  manual_review_required INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS comparison_snapshot (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT NOT NULL,
  asset_id TEXT NOT NULL,
  compare_type TEXT NOT NULL,
  base_run_id TEXT,
  delta_rank REAL,
  delta_score REAL,
  delta_weight REAL,
  top5_changed INTEGER,
  key_field_sigma REAL
);

CREATE TABLE IF NOT EXISTS audit_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  severity TEXT NOT NULL,
  message TEXT NOT NULL,
  context_json TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS notification_log (
  notification_id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL,
  channel TEXT NOT NULL,
  severity TEXT NOT NULL,
  title TEXT NOT NULL,
  body_path TEXT NOT NULL,
  send_status TEXT NOT NULL,
  sent_at TEXT,
  error_message TEXT
);
```

## Required CSV Import: Alipay Positions

`app/templates/alipay_positions_template.csv`

```csv
asset_code,asset_name,platform,current_amount,current_weight,cost_basis,unrealized_pnl,as_of,source_note
```

## Required Config Keys

```yaml
timezone_primary: Asia/Shanghai
timezone_display_secondary: Australia/Sydney
recipient_email: linzezhang35@gmail.com
dry_run: true
max_drawdown_block: 0.40
recovery_time_block_days: 365
deviation_threshold: 0.01
top5_change_rate_threshold: 0.20
drawdown_7d_worsen_threshold: 0.05
min_official_sources_action_ready: 2
```
