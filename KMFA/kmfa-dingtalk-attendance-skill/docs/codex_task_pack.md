# Codex Task Pack - kmfa-dingtalk-attendance

## Conclusion

Implement `kmfa-dingtalk-attendance-skill` as a repo-scoped Codex Skill plus deterministic scripts, PostgreSQL schema, automation prompts, and stage-2 consensus protocol. The target is direct v0.3-grade operation with database and payroll-baseline readiness.

## Scope

### Read first

```text
KMFA/kmfa-dingtalk-attendance-skill/SKILL.md
KMFA/kmfa-dingtalk-attendance-skill/references/operating_contract.md
KMFA/kmfa-dingtalk-attendance-skill/references/source_of_truth_contract.md
KMFA/kmfa-dingtalk-attendance-skill/references/stage2_shadow_payroll_acceptance.md
KMFA/kmfa-dingtalk-attendance-skill/references/database_schema_contract.md
KMFA/kmfa-dingtalk-attendance-skill/references/payroll_baseline_contract.md
```

### Files to add

```text
KMFA/kmfa-dingtalk-attendance-skill/**
database/postgres_schema.sql
database/views_payroll_baseline.sql
automation/morning_prompt.md
automation/evening_prompt.md
schemas/*.schema.json
docs/*.md
```

### Repo files to inspect before integration

Use read-only inspection first. Do not scan unrelated directories.

```text
KMFA project root
metadata/dingtalk_attendance/
current DingTalk attendance module/package
current OneDrive raw ingestion scripts
current DWS wrapper/config scripts
current ledger validation scripts
current notification target resolver
current tests for S19 attendance logic
```

## Implementation tasks

### Task 1 - Install Skill

1. Copy `KMFA/kmfa-dingtalk-attendance-skill` into repo root.
2. Ensure scripts are executable.
3. Run offline skill validation.
4. Confirm `$kmfa-dingtalk-attendance-skill` invocation is available in Codex.

### Task 2 - Wire existing KMFA pipeline into stage-2 adapter

Current status:

- `scripts/run_stage2_evening.sh` has a portable offline replay path.
- `scripts/resolve_stage2_source.py` now records per-run source adapter status.
- Set `KMFA_STAGE2_SOURCE_JSON` to an approved snapshot to write deterministic
  stage-2 artifacts.
- Set `KMFA_STAGE2_SOURCE_MODE=dws_live` only after explicit DWS authorization;
  without authorization it fails closed and writes `source_adapter_status.json`.
- If no approved source is configured, the runner fails closed with
  `STAGE2_ADAPTER_SOURCE_MISSING`.
- The future live materializer still needs explicit authorization, result/detail
  coverage validation, private archive writes, and no-secret proof before it may
  replace replay input.

The live-safe adapter must eventually connect:

```text
KMFA/kmfa-dingtalk-attendance-skill/scripts/run_stage2_evening.sh
```

to the repo-specific command that:

- acquires/replays DingTalk attendance result records
- acquires/replays DingTalk attendance detail records
- writes raw and derived artifacts
- writes canonical snapshot
- writes run manifest
- writes quality/exception reports
- writes payroll baseline candidate JSON
- writes `source_adapter_status.json` on every eligible day

### Task 3 - Add PostgreSQL schema

Current status:

- `database/postgres_schema.sql` and `database/views_payroll_baseline.sql` exist.
- `scripts/validate_database_contract.py` performs an offline contract dry-run
  over required tables, enums, views, and the synthetic accepted stage-2 ->
  payroll baseline query path.
- The dry-run uses no PostgreSQL connection, no database mutation, no private
  raw data, and no live DWS.

Remaining work:

1. Add migration runner according to the repo's migration pattern.
2. Add idempotent import batch logic.
3. Add raw result/detail ingestion.
4. Add derived fact insertion.
5. Add stage-2 and payroll baseline insertion.
6. Run against an explicitly configured non-production PostgreSQL target.

### Task 4 - Enforce location and trajectory evidence

1. Extend source adapter to request and store attendance detail.
2. Normalize `userLatitude`, `userLongitude`, `userAddress`, `baseAddress`, base coordinates when present.
3. Store one trajectory point per punch when only one location point exists.
4. Store multiple points when raw JSON provides path-like evidence.
5. Add data-quality issue when evidence is missing.

### Task 5 - Implement canonical snapshot

1. Include raw batch hashes, employee/month facts, punch facts, location summary, exception summary, payroll baseline candidate rows.
2. Exclude volatile fields.
3. Sort employees, dates, punches, and JSON keys deterministically.
4. Hash with SHA-256.

### Task 6 - Implement stage-2 consensus

1. Ensure evening automation writes `run_01` to `run_05` on next month days 1-5.
2. Ensure morning automation never writes stage-2 artifacts.
3. On day 5, call `stage2_consensus_gate.py`.
4. If accepted, create DB certificate and payroll baseline table rows.
5. If failed, create divergence report.

### Task 7 - Tests

Minimum tests:

```bash
python3 -m py_compile KMFA/kmfa-dingtalk-attendance-skill/scripts/*.py
python3 KMFA/kmfa-dingtalk-attendance-skill/scripts/month_gate.py --run-slot evening --today 2026-08-01 --print-json
python3 KMFA/kmfa-dingtalk-attendance-skill/scripts/month_gate.py --run-slot morning --today 2026-08-01 --print-json
python3 tests/test_stage2_consensus.py
```

Add repo-specific tests for:

- raw result ingestion idempotency
- raw detail/location ingestion idempotency
- GPS range constraints
- raw-to-derived reconciliation
- canonical hash stability
- stage-2 mismatch failure
- stage-2 exact match acceptance

## Rollback plan

1. Remove `KMFA/kmfa-dingtalk-attendance-skill` directory.
2. Disable automation prompts referencing `$kmfa-dingtalk-attendance-skill`.
3. Do not drop database tables until raw import batches and payroll baseline rows are backed up.
4. Revert repo integration commit.
5. Keep private runtime stage-2 artifacts for forensic comparison.

## Definition of done

The project reaches this task pack's target state when:

- Skill is installed and callable.
- Evening automation can run stage-2 gate.
- PostgreSQL schema exists.
- Location and trajectory evidence are captured.
- Canonical snapshot generation is deterministic.
- Five-run exact consensus produces Q5 and payroll baseline candidate.
