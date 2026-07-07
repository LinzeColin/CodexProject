# Database Migration Checklist

## Phase -1 - Offline contract dry-run

- [x] Validate required PostgreSQL tables, enums, and payroll baseline views exist in repo SQL.
- [x] Simulate one accepted five-run stage-2 certificate in memory.
- [x] Simulate one active payroll baseline row backed by the accepted certificate.
- [x] Simulate `v_payroll_baseline_active`, `v_monthly_baseline_summary`, and `v_stage2_blockers` semantics.
- [x] Confirm dry-run uses no PostgreSQL connection, no database mutation, and no live DWS.

## Phase -0.5 - Offline landing bundle

- [x] From accepted stage-2 artifacts, write a private `db_landing/YYYYMM/` bundle.
- [x] Emit `load_order.json`, `policy_version.json`, `canonical_month_snapshot.json`, `stage2_shadow_run.jsonl`, `stage2_consensus_certificate.json`, `attendance_day_fact.jsonl`, `payroll_baseline_attendance.jsonl`, and `postgres_copy_manifest.sql`.
- [x] Confirm bundle generation uses no PostgreSQL connection, no database mutation, and no live DWS.
- [x] Build the approved offline PostgreSQL JSONB/COPY load plan generator for the bundle.
- [x] Generate `postgres_load_payloads/*.jsonl`, `postgres_load_plan.sql`, and `postgres_load_plan_manifest.json` without opening PostgreSQL.
- [x] Statically validate generated load plans against repo schema columns, load order, payload files, and `ON CONFLICT` targets.
- [x] Provide a fail-closed PostgreSQL execution guard that refuses `psql` unless the target is explicitly marked non-production.
- [ ] Execute the loader only against an explicitly configured non-production PostgreSQL target.

## Phase 0 - Local verification

- [ ] Create database `kmfa_attendance`.
- [ ] Apply `database/postgres_schema.sql`.
- [ ] Apply `database/views_payroll_baseline.sql`.
- [ ] Review and execute `postgres_load_plan.sql` only after confirming the target is non-production.
- [ ] Confirm schema exists: `select schema_name from information_schema.schemata where schema_name='kmfa_attendance';`
- [ ] Insert one synthetic import batch.
- [ ] Insert one synthetic raw result and detail record with location fields.
- [ ] Generate one synthetic day fact and canonical snapshot.
- [ ] Insert five synthetic stage-2 runs with identical hash.
- [ ] Insert accepted stage-2 certificate.
- [ ] Insert payroll baseline rows.
- [ ] Query `v_payroll_baseline_active`.

## Phase 1 - Replay from OneDrive raw

- [x] Provide a public-safe private raw archive month inspector for manifest/raw count parity, hash parity, location coverage, and stable replay hashes.
- [x] Isolate record-only `s19_seed_*` raw files as supplemental seed evidence without treating missing formal run manifests as acceptable.
- [ ] Load one completed historical month from OneDrive raw archive.
- [ ] Verify raw counts match manifest.
- [ ] Verify detail/location coverage.
- [ ] Verify every derived day fact links to raw IDs.
- [ ] Verify canonical hash is stable across two local replays.

## Phase 2 - Automation shadow payroll

- [ ] Enable evening automation for days 1-5.
- [ ] Confirm each run writes `run_manifest.json`.
- [ ] Confirm each run writes canonical snapshot and hash.
- [ ] Confirm day-5 consensus gate compares all five runs.
- [ ] Confirm accepted certificate appears only when all five hashes match exactly.
- [x] Confirm accepted certificate also requires per-run location, raw-to-derived, and database transaction commit/verification gates.
- [ ] Confirm payroll baseline rows appear only after accepted certificate.
