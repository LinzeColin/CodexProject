CREATE TABLE IF NOT EXISTS run_log (
  run_id TEXT PRIMARY KEY,
  run_type TEXT NOT NULL CHECK (run_type IN ('morning', 'evening', 'manual')),
  timezone TEXT NOT NULL,
  started_at TEXT NOT NULL,
  finished_at TEXT,
  status TEXT NOT NULL,
  config_status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS employee_snapshot (
  run_id TEXT NOT NULL,
  dingtalk_user_id TEXT NOT NULL,
  employee_name TEXT NOT NULL,
  department_name TEXT,
  snapshot_json TEXT NOT NULL,
  PRIMARY KEY (run_id, dingtalk_user_id)
);

CREATE TABLE IF NOT EXISTS attendance_result_raw (
  run_id TEXT NOT NULL,
  dingtalk_user_id TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  payload_sha256 TEXT NOT NULL,
  PRIMARY KEY (run_id, dingtalk_user_id, payload_sha256)
);

CREATE TABLE IF NOT EXISTS attendance_record_raw (
  run_id TEXT NOT NULL,
  dingtalk_user_id TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  payload_sha256 TEXT NOT NULL,
  PRIMARY KEY (run_id, dingtalk_user_id, payload_sha256)
);

CREATE TABLE IF NOT EXISTS attendance_normalized (
  run_id TEXT NOT NULL,
  dingtalk_user_id TEXT NOT NULL,
  work_date TEXT NOT NULL,
  check_type TEXT NOT NULL,
  expected_time TEXT,
  actual_time TEXT,
  normalized_status TEXT NOT NULL,
  PRIMARY KEY (run_id, dingtalk_user_id, work_date, check_type)
);

CREATE TABLE IF NOT EXISTS anomaly_event (
  anomaly_id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL,
  dingtalk_user_id TEXT NOT NULL,
  employee_name TEXT NOT NULL,
  department_name TEXT,
  anomaly_type TEXT NOT NULL,
  basis TEXT NOT NULL,
  recommended_action TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS report_dispatch (
  dispatch_id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL,
  report_type TEXT NOT NULL CHECK (report_type IN ('management', 'hr')),
  recipient_ref TEXT NOT NULL,
  channel TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS cleanup_audit (
  cleanup_id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL,
  retention_days INTEGER NOT NULL,
  database_size_bytes INTEGER NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS onedrive_archive_manifest (
  archive_id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL,
  month_folder TEXT NOT NULL,
  archive_file_ref TEXT NOT NULL,
  sha256 TEXT,
  created_at TEXT NOT NULL
);
