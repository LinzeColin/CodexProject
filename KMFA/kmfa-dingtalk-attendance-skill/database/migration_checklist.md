# Database Migration Checklist

## Phase 0 - Local verification

- [ ] Create database `kmfa_attendance`.
- [ ] Apply `database/postgres_schema.sql`.
- [ ] Apply `database/views_payroll_baseline.sql`.
- [ ] Confirm schema exists: `select schema_name from information_schema.schemata where schema_name='kmfa_attendance';`
- [ ] Insert one synthetic import batch.
- [ ] Insert one synthetic raw result and detail record with location fields.
- [ ] Generate one synthetic day fact and canonical snapshot.
- [ ] Insert five synthetic stage-2 runs with identical hash.
- [ ] Insert accepted stage-2 certificate.
- [ ] Insert payroll baseline rows.
- [ ] Query `v_payroll_baseline_active`.

## Phase 1 - Replay from OneDrive raw

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
- [ ] Confirm payroll baseline rows appear only after accepted certificate.
