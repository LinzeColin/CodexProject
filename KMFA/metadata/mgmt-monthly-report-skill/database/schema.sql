-- Public-safe aggregate registry schema for mgmt-monthly-report-skill v2.
-- Raw/source filenames, file-derived digests, sizes, sheet labels and report details are prohibited.

CREATE TABLE IF NOT EXISTS monthly_report_run (
  run_id TEXT PRIMARY KEY,
  period TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  metadata_policy TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS monthly_report_input_slot_aggregate (
  run_id TEXT NOT NULL,
  source_group_ref TEXT NOT NULL,
  status TEXT NOT NULL,
  selection_status TEXT NOT NULL,
  candidate_count INTEGER NOT NULL,
  selected_count INTEGER NOT NULL,
  alternate_candidate_count INTEGER NOT NULL,
  minimum_required_count INTEGER NOT NULL,
  recommended_count INTEGER NOT NULL,
  required_sheet_group_count INTEGER NOT NULL,
  passed_sheet_group_count INTEGER NOT NULL,
  failed_sheet_group_count INTEGER NOT NULL,
  PRIMARY KEY (run_id, source_group_ref),
  FOREIGN KEY (run_id) REFERENCES monthly_report_run(run_id)
);

CREATE TABLE IF NOT EXISTS monthly_report_output_status (
  run_id TEXT NOT NULL,
  output_ref TEXT NOT NULL,
  status TEXT NOT NULL,
  retained_locally INTEGER NOT NULL,
  committed_plaintext_to_git INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (run_id, output_ref),
  FOREIGN KEY (run_id) REFERENCES monthly_report_run(run_id)
);
