SET search_path TO kmfa_attendance, public;

-- View showing only active payroll baseline rows backed by accepted stage-2 certificate.
CREATE OR REPLACE VIEW v_payroll_baseline_active AS
SELECT
  p.target_month,
  p.employee_internal_id,
  p.dingtalk_userid,
  p.work_date,
  p.required_attendance_state,
  p.actual_attendance_state,
  p.first_in_time,
  p.last_out_time,
  p.late_minutes,
  p.early_leave_minutes,
  p.absent_flag,
  p.missing_punch_count,
  p.location_result,
  p.location_evidence_count,
  p.trajectory_evidence_count,
  p.source_day_fact_id,
  p.stage2_certificate_id,
  p.canonical_hash,
  p.baseline_version,
  p.created_at
FROM payroll_baseline_attendance p
JOIN stage2_consensus_certificate c
  ON c.stage2_certificate_id = p.stage2_certificate_id
WHERE p.status = 'active'
  AND c.status = 'accepted'
  AND c.accepted = true;

-- View for monthly baseline completeness.
CREATE OR REPLACE VIEW v_monthly_baseline_summary AS
SELECT
  target_month,
  COUNT(*) AS baseline_rows,
  COUNT(DISTINCT employee_internal_id) AS employees,
  SUM(CASE WHEN absent_flag THEN 1 ELSE 0 END) AS absent_days,
  SUM(missing_punch_count) AS missing_punches,
  SUM(late_minutes) AS late_minutes,
  SUM(early_leave_minutes) AS early_leave_minutes,
  MIN(created_at) AS first_created_at,
  MAX(created_at) AS last_created_at,
  MIN(canonical_hash) AS canonical_hash
FROM v_payroll_baseline_active
GROUP BY target_month;

-- View for unresolved blockers by month.
CREATE OR REPLACE VIEW v_stage2_blockers AS
SELECT
  target_month,
  priority,
  COUNT(*) AS unresolved_count
FROM exception_case
WHERE status <> 'resolved'
  AND priority IN ('P0', 'P1')
GROUP BY target_month, priority;
