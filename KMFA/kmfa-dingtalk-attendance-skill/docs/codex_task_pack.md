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
- `scripts/prepare_database_landing_bundle.py` materializes an accepted
  stage-2 artifact folder into a private PostgreSQL landing bundle: load order,
  policy version, canonical snapshot row, stage-2 runs, accepted certificate,
  attendance day facts, payroll baseline rows, and a SQL load manifest.
- `scripts/prepare_postgres_landing_loader.py` generates private normalized
  JSONL load payloads plus `postgres_load_plan.sql` with JSONB staging tables
  and idempotent `ON CONFLICT DO NOTHING` inserts.
- `scripts/validate_postgres_load_plan.py` statically validates the generated
  plan against `database/postgres_schema.sql` for table order, inserted
  columns, payload presence, and schema-backed conflict targets.
- `scripts/execute_postgres_load_plan.py` is the fail-closed executor guard:
  it performs static validation by default and invokes `psql` only when
  `--execute`, `--acknowledge-nonprod-mutation`,
  `KMFA_ALLOW_NONPROD_POSTGRES_EXECUTION=1`, a non-production target env, and a
  database URL are all present.
- `scripts/inspect_raw_archive_month.py` inspects a private OneDrive-style
  monthly raw archive without printing names, DingTalk IDs, raw rows, or local
  paths. It checks manifest/raw count parity, raw sha256 parity, punch location
  coverage, and stable replay hashes before any database import. Record-only
  `s19_seed_*` raw files are isolated as supplemental seed evidence only when
  `--allow-seed-raw-without-manifest` is explicitly set.
- `scripts/prepare_raw_replay_day_fact_bundle.py` materializes a private raw
  replay day-fact/linkage bundle after archive inspection passes. It writes
  `attendance_day_fact.jsonl`, `raw_detail_linkage.jsonl`, and a canonical
  replay snapshot under private runtime while keeping stdout and summary
  manifests public-safe.
- `scripts/prepare_stage2_source_from_raw_replay.py` converts a private raw
  replay day-fact/linkage bundle into a Stage-2 source snapshot with
  employee-key hashes, day facts, payroll baseline candidates, raw-detail
  lineage references, and fail-closed database commit/verification gates.
- `scripts/resolve_stage2_source.py` can now use
  `KMFA_STAGE2_SOURCE_MODE=raw_replay_day_fact` plus
  `KMFA_STAGE2_RAW_REPLAY_DAY_FACT_DIR` so eligible evening automation can
  materialize that Stage-2 source without live DWS or database mutation.
- `scripts/prepare_preconsensus_postgres_landing_bundle.py` breaks the
  stage-2/database proof loop by materializing a pre-consensus PostgreSQL
  landing bundle from a Stage-2 source before accepted payroll baseline. It
  loads only `policy_version`, `canonical_month_snapshot`, and
  `attendance_day_fact`.
- `scripts/apply_stage2_database_proof.py` consumes a fail-closed
  non-production PostgreSQL execution proof and writes a DB-verified Stage-2
  source where `database_transaction_committed` and
  `database_transaction_verified` are true. It does not itself connect to
  PostgreSQL or mutate a database.
- Real private 202606 replay has produced an ignored private day-fact/linkage
  bundle with raw count/hash parity, location threshold pass, every day fact
  linked to raw detail IDs, and matching canonical replay hashes across two
  local replays.
- The dry-run uses no PostgreSQL connection, no database mutation, no private
  raw data, and no live DWS.

Remaining work:

1. Add migration runner according to the repo's migration pattern.
2. Add idempotent import batch logic.
3. Add raw result/detail ingestion.
4. Add derived fact insertion.
5. Review, statically validate, and pass the fail-closed execution guard for the generated PostgreSQL JSONB/COPY loader SQL.
6. Run against an explicitly configured non-production PostgreSQL target.
7. Run private raw archive inspection and day-fact replay on future completed
   months before import, including seed-raw isolation and an explicit location
   coverage threshold; keep only public-safe summaries in review evidence.
8. Run the pre-consensus PostgreSQL load plan against an explicitly approved
   non-production target and apply the execution proof so Stage-2 day-5
   consensus can satisfy database transaction gates instead of failing closed.

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
4. If accepted, create DB landing bundle, then DB certificate and payroll
   baseline table rows only through the approved loader.
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
