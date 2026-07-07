-- Public-safe registry schema for mgmt-monthly-report-skill.
-- Do not store raw business row values or sensitive plaintext in these tables.

CREATE TABLE IF NOT EXISTS monthly_report_run (
  run_id TEXT PRIMARY KEY,
  period TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  metadata_policy TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS monthly_report_input_file (
  run_id TEXT NOT NULL,
  slot_id TEXT NOT NULL,
  file_sha256 TEXT NOT NULL,
  file_size_bytes INTEGER NOT NULL,
  extension TEXT NOT NULL,
  sheet_count INTEGER,
  sheet_names_sha256 TEXT,
  matched_pattern TEXT,
  is_symlink INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (run_id, slot_id, file_sha256),
  FOREIGN KEY (run_id) REFERENCES monthly_report_run(run_id)
);

CREATE TABLE IF NOT EXISTS monthly_report_output_index (
  run_id TEXT NOT NULL,
  output_type TEXT NOT NULL,
  file_sha256 TEXT,
  file_size_bytes INTEGER,
  retained_locally INTEGER NOT NULL,
  committed_plaintext_to_git INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (run_id, output_type),
  FOREIGN KEY (run_id) REFERENCES monthly_report_run(run_id)
);

