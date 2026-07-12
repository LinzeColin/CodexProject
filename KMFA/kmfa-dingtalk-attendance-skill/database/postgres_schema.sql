-- kmfa-dingtalk-attendance PostgreSQL schema
-- Target: payroll-grade attendance evidence, stage-2 consensus, and payroll baseline standard.

CREATE SCHEMA IF NOT EXISTS kmfa_attendance;
SET search_path TO kmfa_attendance, public;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- -------------------------
-- Types
-- -------------------------
DO $$ BEGIN
  CREATE TYPE quality_grade AS ENUM ('Q0','Q1','Q2','Q3','Q4','Q5');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE run_slot AS ENUM ('morning','evening','manual');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE exception_priority AS ENUM ('P0','P1','P2','P3');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE stage2_status AS ENUM ('not_eligible','pending','accepted','failed','superseded');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- -------------------------
-- Source and batch metadata
-- -------------------------
CREATE TABLE IF NOT EXISTS raw_import_batch (
  batch_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_system TEXT NOT NULL DEFAULT 'dingtalk',
  source_adapter TEXT NOT NULL,
  target_month CHAR(6) NOT NULL CHECK (target_month ~ '^[0-9]{6}$'),
  request_start_at TIMESTAMPTZ,
  request_end_at TIMESTAMPTZ,
  acquired_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  acquired_by TEXT,
  endpoint TEXT NOT NULL,
  request_scope JSONB NOT NULL DEFAULT '{}'::jsonb,
  pagination_status JSONB NOT NULL DEFAULT '{}'::jsonb,
  response_count INTEGER NOT NULL DEFAULT 0 CHECK (response_count >= 0),
  raw_archive_path TEXT,
  raw_batch_hash TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'acquired',
  UNIQUE (target_month, endpoint, raw_batch_hash)
);

CREATE TABLE IF NOT EXISTS employee_identity_map (
  employee_internal_id TEXT NOT NULL,
  dingtalk_userid TEXT NOT NULL,
  dingtalk_openid TEXT,
  employee_name TEXT,
  employment_status TEXT,
  effective_from DATE NOT NULL,
  effective_to DATE,
  identity_version TEXT NOT NULL,
  attributes JSONB NOT NULL DEFAULT '{}'::jsonb,
  PRIMARY KEY (employee_internal_id, effective_from, identity_version),
  UNIQUE (dingtalk_userid, effective_from, identity_version),
  CHECK (effective_to IS NULL OR effective_to >= effective_from)
);

-- -------------------------
-- Raw DingTalk attendance evidence
-- -------------------------
CREATE TABLE IF NOT EXISTS raw_attendance_result (
  raw_result_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  batch_id UUID NOT NULL REFERENCES raw_import_batch(batch_id) ON DELETE RESTRICT,
  target_month CHAR(6) NOT NULL CHECK (target_month ~ '^[0-9]{6}$'),
  dingtalk_userid TEXT NOT NULL,
  work_date DATE NOT NULL,
  check_type TEXT,
  time_result TEXT,
  location_result TEXT,
  user_check_time TIMESTAMPTZ,
  base_check_time TIMESTAMPTZ,
  source_type TEXT,
  proc_inst_id TEXT,
  approve_id TEXT,
  record_source_key TEXT NOT NULL,
  raw_payload JSONB NOT NULL,
  raw_hash TEXT NOT NULL,
  inserted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (record_source_key),
  UNIQUE (raw_hash)
);

CREATE INDEX IF NOT EXISTS idx_raw_attendance_result_month_user ON raw_attendance_result(target_month, dingtalk_userid, work_date);
CREATE INDEX IF NOT EXISTS idx_raw_attendance_result_payload_gin ON raw_attendance_result USING gin(raw_payload);

CREATE TABLE IF NOT EXISTS raw_attendance_detail (
  raw_detail_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  batch_id UUID NOT NULL REFERENCES raw_import_batch(batch_id) ON DELETE RESTRICT,
  target_month CHAR(6) NOT NULL CHECK (target_month ~ '^[0-9]{6}$'),
  dingtalk_userid TEXT NOT NULL,
  work_date DATE,
  check_time TIMESTAMPTZ,
  check_type TEXT,
  time_result TEXT,
  location_result TEXT,
  source_type TEXT,
  device_id_hash TEXT,
  user_latitude NUMERIC(10,7),
  user_longitude NUMERIC(10,7),
  user_address TEXT,
  base_latitude NUMERIC(10,7),
  base_longitude NUMERIC(10,7),
  base_address TEXT,
  outside_remark TEXT,
  proc_inst_id TEXT,
  approve_id TEXT,
  detail_source_key TEXT NOT NULL,
  raw_payload JSONB NOT NULL,
  raw_hash TEXT NOT NULL,
  inserted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (user_latitude IS NULL OR (user_latitude BETWEEN -90 AND 90)),
  CHECK (user_longitude IS NULL OR (user_longitude BETWEEN -180 AND 180)),
  CHECK (base_latitude IS NULL OR (base_latitude BETWEEN -90 AND 90)),
  CHECK (base_longitude IS NULL OR (base_longitude BETWEEN -180 AND 180)),
  UNIQUE (detail_source_key),
  UNIQUE (raw_hash)
);

CREATE INDEX IF NOT EXISTS idx_raw_attendance_detail_month_user ON raw_attendance_detail(target_month, dingtalk_userid, work_date);
CREATE INDEX IF NOT EXISTS idx_raw_attendance_detail_geo ON raw_attendance_detail(user_latitude, user_longitude);
CREATE INDEX IF NOT EXISTS idx_raw_attendance_detail_payload_gin ON raw_attendance_detail USING gin(raw_payload);

CREATE TABLE IF NOT EXISTS attendance_trajectory_point (
  trajectory_point_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  raw_detail_id UUID REFERENCES raw_attendance_detail(raw_detail_id) ON DELETE CASCADE,
  target_month CHAR(6) NOT NULL CHECK (target_month ~ '^[0-9]{6}$'),
  dingtalk_userid TEXT NOT NULL,
  work_date DATE,
  point_index INTEGER NOT NULL DEFAULT 0 CHECK (point_index >= 0),
  point_time TIMESTAMPTZ,
  latitude NUMERIC(10,7),
  longitude NUMERIC(10,7),
  address TEXT,
  base_address TEXT,
  distance_meters NUMERIC(12,2),
  evidence_kind TEXT NOT NULL DEFAULT 'punch_location',
  raw_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  inserted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (latitude IS NULL OR (latitude BETWEEN -90 AND 90)),
  CHECK (longitude IS NULL OR (longitude BETWEEN -180 AND 180)),
  UNIQUE (raw_detail_id, point_index)
);

CREATE INDEX IF NOT EXISTS idx_trajectory_month_user ON attendance_trajectory_point(target_month, dingtalk_userid, work_date);
CREATE INDEX IF NOT EXISTS idx_trajectory_geo ON attendance_trajectory_point(latitude, longitude);

-- -------------------------
-- Group/shift reference snapshots
-- -------------------------
CREATE TABLE IF NOT EXISTS attendance_group_snapshot (
  group_snapshot_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  batch_id UUID REFERENCES raw_import_batch(batch_id) ON DELETE RESTRICT,
  group_id TEXT NOT NULL,
  group_name TEXT,
  effective_month CHAR(6) NOT NULL CHECK (effective_month ~ '^[0-9]{6}$'),
  raw_payload JSONB NOT NULL,
  raw_hash TEXT NOT NULL,
  UNIQUE (group_id, effective_month, raw_hash)
);

CREATE TABLE IF NOT EXISTS shift_snapshot (
  shift_snapshot_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  batch_id UUID REFERENCES raw_import_batch(batch_id) ON DELETE RESTRICT,
  shift_id TEXT NOT NULL,
  shift_name TEXT,
  effective_month CHAR(6) NOT NULL CHECK (effective_month ~ '^[0-9]{6}$'),
  raw_payload JSONB NOT NULL,
  raw_hash TEXT NOT NULL,
  UNIQUE (shift_id, effective_month, raw_hash)
);

CREATE TABLE IF NOT EXISTS site_geofence (
  site_id TEXT PRIMARY KEY,
  site_name TEXT NOT NULL,
  base_latitude NUMERIC(10,7),
  base_longitude NUMERIC(10,7),
  radius_meters NUMERIC(12,2),
  effective_from DATE NOT NULL,
  effective_to DATE,
  source_group_id TEXT,
  raw_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  CHECK (base_latitude IS NULL OR (base_latitude BETWEEN -90 AND 90)),
  CHECK (base_longitude IS NULL OR (base_longitude BETWEEN -180 AND 180)),
  CHECK (radius_meters IS NULL OR radius_meters >= 0),
  CHECK (effective_to IS NULL OR effective_to >= effective_from)
);

-- -------------------------
-- Policy/rule versioning
-- -------------------------
CREATE TABLE IF NOT EXISTS policy_version (
  policy_version_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  policy_code TEXT NOT NULL,
  policy_name TEXT NOT NULL,
  effective_from DATE NOT NULL,
  effective_to DATE,
  locked_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  description TEXT,
  UNIQUE (policy_code, effective_from),
  CHECK (effective_to IS NULL OR effective_to >= effective_from)
);

CREATE TABLE IF NOT EXISTS rule_config_snapshot (
  rule_config_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  policy_version_id UUID NOT NULL REFERENCES policy_version(policy_version_id) ON DELETE RESTRICT,
  target_month CHAR(6) NOT NULL CHECK (target_month ~ '^[0-9]{6}$'),
  config_hash TEXT NOT NULL,
  config JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (policy_version_id, target_month, config_hash)
);

-- -------------------------
-- Normalized derived facts
-- -------------------------
CREATE TABLE IF NOT EXISTS attendance_day_fact (
  day_fact_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  target_month CHAR(6) NOT NULL CHECK (target_month ~ '^[0-9]{6}$'),
  employee_internal_id TEXT NOT NULL,
  dingtalk_userid TEXT NOT NULL,
  work_date DATE NOT NULL,
  policy_version_id UUID NOT NULL REFERENCES policy_version(policy_version_id) ON DELETE RESTRICT,
  required_attendance_state TEXT NOT NULL,
  actual_attendance_state TEXT NOT NULL,
  first_in_time TIMESTAMPTZ,
  last_out_time TIMESTAMPTZ,
  late_minutes INTEGER NOT NULL DEFAULT 0 CHECK (late_minutes >= 0),
  early_leave_minutes INTEGER NOT NULL DEFAULT 0 CHECK (early_leave_minutes >= 0),
  absent_flag BOOLEAN NOT NULL DEFAULT false,
  missing_punch_count INTEGER NOT NULL DEFAULT 0 CHECK (missing_punch_count >= 0),
  location_evidence_count INTEGER NOT NULL DEFAULT 0 CHECK (location_evidence_count >= 0),
  trajectory_evidence_count INTEGER NOT NULL DEFAULT 0 CHECK (trajectory_evidence_count >= 0),
  source_result_ids UUID[] NOT NULL DEFAULT '{}',
  source_detail_ids UUID[] NOT NULL DEFAULT '{}',
  derivation_hash TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (target_month, employee_internal_id, work_date, policy_version_id)
);

CREATE INDEX IF NOT EXISTS idx_day_fact_month_employee ON attendance_day_fact(target_month, employee_internal_id, work_date);

CREATE TABLE IF NOT EXISTS attendance_punch_fact (
  punch_fact_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  day_fact_id UUID NOT NULL REFERENCES attendance_day_fact(day_fact_id) ON DELETE CASCADE,
  target_month CHAR(6) NOT NULL CHECK (target_month ~ '^[0-9]{6}$'),
  employee_internal_id TEXT NOT NULL,
  dingtalk_userid TEXT NOT NULL,
  work_date DATE NOT NULL,
  check_type TEXT,
  scheduled_time TIMESTAMPTZ,
  actual_time TIMESTAMPTZ,
  time_result TEXT,
  location_result TEXT,
  user_latitude NUMERIC(10,7),
  user_longitude NUMERIC(10,7),
  user_address TEXT,
  base_latitude NUMERIC(10,7),
  base_longitude NUMERIC(10,7),
  base_address TEXT,
  distance_meters NUMERIC(12,2),
  raw_result_id UUID REFERENCES raw_attendance_result(raw_result_id) ON DELETE RESTRICT,
  raw_detail_id UUID REFERENCES raw_attendance_detail(raw_detail_id) ON DELETE RESTRICT,
  derivation_hash TEXT NOT NULL,
  UNIQUE (day_fact_id, check_type, actual_time, raw_detail_id)
);

-- -------------------------
-- Classification and exceptions
-- -------------------------
CREATE TABLE IF NOT EXISTS classification_result (
  classification_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  target_month CHAR(6) NOT NULL CHECK (target_month ~ '^[0-9]{6}$'),
  day_fact_id UUID REFERENCES attendance_day_fact(day_fact_id) ON DELETE CASCADE,
  employee_internal_id TEXT NOT NULL,
  work_date DATE NOT NULL,
  policy_version_id UUID NOT NULL REFERENCES policy_version(policy_version_id) ON DELETE RESTRICT,
  classification_code TEXT NOT NULL,
  classification_value JSONB NOT NULL,
  evidence JSONB NOT NULL DEFAULT '{}'::jsonb,
  derivation_hash TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_classification_month_employee ON classification_result(target_month, employee_internal_id, work_date);

CREATE TABLE IF NOT EXISTS exception_case (
  exception_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  target_month CHAR(6) NOT NULL CHECK (target_month ~ '^[0-9]{6}$'),
  priority exception_priority NOT NULL,
  employee_internal_id TEXT,
  dingtalk_userid TEXT,
  work_date DATE,
  issue_code TEXT NOT NULL,
  issue_message TEXT NOT NULL,
  evidence JSONB NOT NULL DEFAULT '{}'::jsonb,
  status TEXT NOT NULL DEFAULT 'open',
  opened_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  resolved_at TIMESTAMPTZ,
  resolution TEXT,
  CHECK ((status = 'resolved' AND resolved_at IS NOT NULL) OR (status <> 'resolved'))
);

CREATE INDEX IF NOT EXISTS idx_exception_month_priority ON exception_case(target_month, priority, status);

-- -------------------------
-- Stage-2 shadow payroll consensus
-- -------------------------
CREATE TABLE IF NOT EXISTS canonical_month_snapshot (
  snapshot_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  target_month CHAR(6) NOT NULL CHECK (target_month ~ '^[0-9]{6}$'),
  policy_version_id UUID NOT NULL REFERENCES policy_version(policy_version_id) ON DELETE RESTRICT,
  identity_version TEXT NOT NULL,
  snapshot_json JSONB NOT NULL,
  canonical_hash TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (target_month, policy_version_id, identity_version, canonical_hash)
);

CREATE TABLE IF NOT EXISTS stage2_shadow_run (
  stage2_run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  target_month CHAR(6) NOT NULL CHECK (target_month ~ '^[0-9]{6}$'),
  run_index INTEGER NOT NULL CHECK (run_index BETWEEN 1 AND 5),
  run_slot run_slot NOT NULL DEFAULT 'evening',
  run_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  snapshot_id UUID NOT NULL REFERENCES canonical_month_snapshot(snapshot_id) ON DELETE RESTRICT,
  canonical_hash TEXT NOT NULL,
  quality quality_grade NOT NULL,
  p0_unresolved INTEGER NOT NULL DEFAULT 0 CHECK (p0_unresolved >= 0),
  p1_unresolved INTEGER NOT NULL DEFAULT 0 CHECK (p1_unresolved >= 0),
  run_manifest JSONB NOT NULL,
  UNIQUE (target_month, run_index)
);

CREATE TABLE IF NOT EXISTS stage2_consensus_certificate (
  stage2_certificate_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  target_month CHAR(6) NOT NULL CHECK (target_month ~ '^[0-9]{6}$'),
  status stage2_status NOT NULL,
  accepted BOOLEAN NOT NULL DEFAULT false,
  canonical_hash TEXT,
  run_ids UUID[] NOT NULL DEFAULT '{}',
  certificate_json JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  supersedes UUID REFERENCES stage2_consensus_certificate(stage2_certificate_id) ON DELETE RESTRICT,
  UNIQUE (target_month, status, canonical_hash)
);

-- -------------------------
-- Payroll baseline
-- -------------------------
CREATE TABLE IF NOT EXISTS payroll_baseline_attendance (
  payroll_baseline_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  target_month CHAR(6) NOT NULL CHECK (target_month ~ '^[0-9]{6}$'),
  employee_internal_id TEXT NOT NULL,
  dingtalk_userid TEXT NOT NULL,
  work_date DATE NOT NULL,
  required_attendance_state TEXT NOT NULL,
  actual_attendance_state TEXT NOT NULL,
  first_in_time TIMESTAMPTZ,
  last_out_time TIMESTAMPTZ,
  late_minutes INTEGER NOT NULL DEFAULT 0 CHECK (late_minutes >= 0),
  early_leave_minutes INTEGER NOT NULL DEFAULT 0 CHECK (early_leave_minutes >= 0),
  absent_flag BOOLEAN NOT NULL DEFAULT false,
  missing_punch_count INTEGER NOT NULL DEFAULT 0 CHECK (missing_punch_count >= 0),
  location_result TEXT,
  location_evidence_count INTEGER NOT NULL DEFAULT 0 CHECK (location_evidence_count >= 0),
  trajectory_evidence_count INTEGER NOT NULL DEFAULT 0 CHECK (trajectory_evidence_count >= 0),
  source_day_fact_id UUID NOT NULL REFERENCES attendance_day_fact(day_fact_id) ON DELETE RESTRICT,
  stage2_certificate_id UUID NOT NULL REFERENCES stage2_consensus_certificate(stage2_certificate_id) ON DELETE RESTRICT,
  canonical_hash TEXT NOT NULL,
  baseline_version INTEGER NOT NULL DEFAULT 1,
  status TEXT NOT NULL DEFAULT 'active',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (target_month, employee_internal_id, work_date, baseline_version)
);

CREATE INDEX IF NOT EXISTS idx_payroll_baseline_month_employee ON payroll_baseline_attendance(target_month, employee_internal_id, work_date);

CREATE TABLE IF NOT EXISTS payroll_export_audit (
  payroll_export_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  target_month CHAR(6) NOT NULL CHECK (target_month ~ '^[0-9]{6}$'),
  stage2_certificate_id UUID NOT NULL REFERENCES stage2_consensus_certificate(stage2_certificate_id) ON DELETE RESTRICT,
  exported_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  exported_by TEXT,
  export_format TEXT NOT NULL,
  row_count INTEGER NOT NULL CHECK (row_count >= 0),
  export_hash TEXT NOT NULL,
  export_path TEXT,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS integrity_audit_log (
  audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  event_type TEXT NOT NULL,
  target_month CHAR(6),
  actor TEXT,
  object_type TEXT,
  object_id TEXT,
  details JSONB NOT NULL DEFAULT '{}'::jsonb
);
