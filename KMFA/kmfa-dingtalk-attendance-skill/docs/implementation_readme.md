# Implementation README

legacy_classification: `historical_identifier`; retained legacy archive examples are historical/read-only inputs, not current identity.

## Install

```bash
cd /Users/linzezhang/CodexProject/KMFA
mkdir -p .agents/skills
cp -R /path/to/kmfa-dingtalk-attendance_task_pack/KMFA/kmfa-dingtalk-attendance-skill .agents/skills/
chmod +x KMFA/kmfa-dingtalk-attendance-skill/scripts/*.sh
chmod +x KMFA/kmfa-dingtalk-attendance-skill/scripts/*.py
```

## Configure local runtime

```bash
mkdir -p metadata/dingtalk_attendance/private_runtime
cp KMFA/kmfa-dingtalk-attendance-skill/templates/env.local.example \
  metadata/dingtalk_attendance/private_runtime/.env.local
cp KMFA/kmfa-dingtalk-attendance-skill/templates/kmfa.attendance.config.example.json \
  metadata/dingtalk_attendance/private_runtime/kmfa.attendance.config.json
```

Edit local values in private runtime.

## Validate

```bash
KMFA/kmfa-dingtalk-attendance-skill/scripts/preflight.sh
KMFA/kmfa-dingtalk-attendance-skill/scripts/inspect_runtime.sh
KMFA/kmfa-dingtalk-attendance-skill/scripts/validate_offline.sh
```

## Test month gate

```bash
KMFA_RUN_SLOT=evening python3 KMFA/kmfa-dingtalk-attendance-skill/scripts/month_gate.py --today 2026-08-01 --print-json
KMFA_RUN_SLOT=morning python3 KMFA/kmfa-dingtalk-attendance-skill/scripts/month_gate.py --today 2026-08-01 --print-json
KMFA_RUN_SLOT=evening python3 KMFA/kmfa-dingtalk-attendance-skill/scripts/month_gate.py --today 2026-08-06 --print-json
```

Expected:

- 2026-08-01 evening => eligible for 202607 run 1
- 2026-08-01 morning => not eligible
- 2026-08-06 evening => not eligible

## Database

```bash
psql "$KMFA_DATABASE_URL" -f database/postgres_schema.sql
psql "$KMFA_DATABASE_URL" -f database/views_payroll_baseline.sql
```

Before any database connection, generate a private landing bundle from an
accepted stage-2 folder:

```bash
python3 scripts/prepare_database_landing_bundle.py \
  --stage2-root "$KMFA_PRIVATE_RUNTIME/stage2/202607" \
  --target-month 202607 \
  --out-dir "$KMFA_PRIVATE_RUNTIME/db_landing/202607" \
  --print-json
```

The bundle generator is offline only: no PostgreSQL connection, no database
mutation, and no live DWS.

Then generate the private PostgreSQL load plan:

```bash
python3 scripts/prepare_postgres_landing_loader.py \
  --bundle-dir "$KMFA_PRIVATE_RUNTIME/db_landing/202607" \
  --print-json
```

Review `postgres_load_plan.sql` and run it only against an explicitly approved
non-production PostgreSQL target.

Validate the load plan offline before any database mutation:

```bash
python3 scripts/validate_postgres_load_plan.py \
  --schema database/postgres_schema.sql \
  --bundle-dir "$KMFA_PRIVATE_RUNTIME/db_landing/202607" \
  --print-json
```

Run the PostgreSQL execution guard in dry-run mode:

```bash
python3 scripts/execute_postgres_load_plan.py \
  --schema database/postgres_schema.sql \
  --views database/views_payroll_baseline.sql \
  --bundle-dir "$KMFA_PRIVATE_RUNTIME/db_landing/202607" \
  --print-json
```

Actual execution is fail-closed and requires all of the following:

```bash
export KMFA_ALLOW_NONPROD_POSTGRES_EXECUTION=1
export KMFA_POSTGRES_TARGET_ENV=local
export KMFA_ATTENDANCE_POSTGRES_DSN='postgresql://localhost/kmfa_attendance_local'

python3 scripts/execute_postgres_load_plan.py \
  --schema database/postgres_schema.sql \
  --views database/views_payroll_baseline.sql \
  --bundle-dir "$KMFA_PRIVATE_RUNTIME/db_landing/202607" \
  --execute \
  --acknowledge-nonprod-mutation \
  --print-json
```

Inspect a private OneDrive-style raw archive month before replay/import:

```bash
python3 scripts/inspect_raw_archive_month.py \
  --archive-root /Users/linzezhang/OneDrive/dingtalk_attendance \
  --target-month 202607 \
  --allow-seed-raw-without-manifest \
  --min-location-coverage-ratio 0.01 \
  --out "$KMFA_PRIVATE_RUNTIME/raw_replay/202607/readiness_manifest.json" \
  --print-json
```

The output is public-safe by design: it includes counts, coverage ratios, and
hashes, but not employee names, DingTalk IDs, raw row bodies, or local raw file
paths. Use `--allow-seed-raw-without-manifest` only for record-only
`s19_seed_*` monthly accumulation seed files; it must not mask missing manifests
for formal full-flow runs.

Materialize a private raw replay day-fact/linkage bundle after inspection
passes:

```bash
python3 scripts/prepare_raw_replay_day_fact_bundle.py \
  --archive-root /Users/linzezhang/OneDrive/dingtalk_attendance \
  --target-month 202607 \
  --allow-seed-raw-without-manifest \
  --min-location-coverage-ratio 0.01 \
  --out-dir "$KMFA_PRIVATE_RUNTIME/raw_replay_day_fact/202607" \
  --print-json
```

Convert the private raw replay day-fact/linkage bundle into a Stage-2 source
snapshot:

```bash
python3 scripts/prepare_stage2_source_from_raw_replay.py \
  --raw-replay-day-fact-dir "$KMFA_PRIVATE_RUNTIME/raw_replay_day_fact/202607" \
  --target-month 202607 \
  --out-json "$KMFA_PRIVATE_RUNTIME/stage2_source/202607/source_snapshot.json" \
  --print-json
```

The Stage-2 resolver can also materialize this source during an eligible
evening run:

```bash
export KMFA_STAGE2_SOURCE_MODE=raw_replay_day_fact
export KMFA_STAGE2_RAW_REPLAY_DAY_FACT_DIR="$KMFA_PRIVATE_RUNTIME/raw_replay_day_fact/202607"
KMFA_RUN_SLOT=evening KMFA_TODAY_OVERRIDE=2026-08-01 scripts/run_stage2_evening.sh
```

This bridge does not claim PostgreSQL commit/verification. Its Stage-2 source
keeps `database_transaction_committed=false` and
`database_transaction_verified=false`, so day-5 consensus remains fail-closed
until an approved non-production database execution proof exists.

Generate a pre-consensus PostgreSQL landing bundle from that Stage-2 source:

```bash
python3 scripts/prepare_preconsensus_postgres_landing_bundle.py \
  --source-json "$KMFA_PRIVATE_RUNTIME/stage2_source/202607/source_snapshot.json" \
  --target-month 202607 \
  --out-dir "$KMFA_PRIVATE_RUNTIME/db_landing_preconsensus/202607" \
  --print-json
```

This bundle intentionally contains only the pre-consensus tables needed to
prove database landing before payroll acceptance:

```text
policy_version
canonical_month_snapshot
attendance_day_fact
```

It does not create `stage2_consensus_certificate` or
`payroll_baseline_attendance` rows.

Generate, validate, and guard-execute its PostgreSQL load plan the same way as
the accepted bundle, but only against an approved non-production target:

```bash
python3 scripts/prepare_postgres_landing_loader.py \
  --bundle-dir "$KMFA_PRIVATE_RUNTIME/db_landing_preconsensus/202607" \
  --print-json

python3 scripts/validate_postgres_load_plan.py \
  --schema database/postgres_schema.sql \
  --bundle-dir "$KMFA_PRIVATE_RUNTIME/db_landing_preconsensus/202607" \
  --print-json

python3 scripts/execute_postgres_load_plan.py \
  --schema database/postgres_schema.sql \
  --views database/views_payroll_baseline.sql \
  --bundle-dir "$KMFA_PRIVATE_RUNTIME/db_landing_preconsensus/202607" \
  --execute \
  --acknowledge-nonprod-mutation \
  --print-json > "$KMFA_PRIVATE_RUNTIME/db_landing_preconsensus/202607/postgres_execution_proof.json"

python3 scripts/verify_postgres_landing_state.py \
  --bundle-dir "$KMFA_PRIVATE_RUNTIME/db_landing_preconsensus/202607" \
  --acknowledge-nonprod-read \
  --print-json > "$KMFA_PRIVATE_RUNTIME/db_landing_preconsensus/202607/postgres_state_verification.json"
```

Apply both the non-production execution proof and the post-load state
verification proof to the Stage-2 source:

```bash
python3 scripts/apply_stage2_database_proof.py \
  --source-json "$KMFA_PRIVATE_RUNTIME/stage2_source/202607/source_snapshot.json" \
  --bundle-dir "$KMFA_PRIVATE_RUNTIME/db_landing_preconsensus/202607" \
  --execution-proof-json "$KMFA_PRIVATE_RUNTIME/db_landing_preconsensus/202607/postgres_execution_proof.json" \
  --state-verification-json "$KMFA_PRIVATE_RUNTIME/db_landing_preconsensus/202607/postgres_state_verification.json" \
  --out-json "$KMFA_PRIVATE_RUNTIME/stage2_source/202607/source_snapshot.db_verified.json" \
  --print-json
```

Only this DB-verified source may make Stage-2 run manifests carry
`database_transaction_committed=true` and
`database_transaction_verified=true`.
The execution proof JSON is intentionally report-redacted: it may prove guard
status, `psql` invocation, target environment, and return code, but it must not
print the raw PostgreSQL DSN or absolute local bundle paths.
The state verification proof is read-only and must show database row counts
matching the private landing bundle before `database_transaction_verified` may
be true.

Run a private five-run accepted rehearsal and generate the accepted DB landing
bundle without opening PostgreSQL:

```bash
python3 scripts/run_stage2_accepted_rehearsal.py \
  --source-json "$KMFA_PRIVATE_RUNTIME/stage2_source/202607/source_snapshot.db_verified.json" \
  --target-month 202607 \
  --out-root "$KMFA_PRIVATE_RUNTIME" \
  --print-json
```

This writes `stage2/202607/run_01` through `run_05`, the accepted consensus
certificate, `db_landing/202607`, `postgres_load_plan.sql`, and
`postgres_load_plan_manifest.json`. The summary is public-safe and reports no
private runtime paths.

The command writes private `attendance_day_fact.jsonl`,
`raw_detail_linkage.jsonl`, a canonical replay snapshot, and a public-safe
summary manifest. The summary must show every derived day fact links to raw
detail IDs and that the canonical replay hash is stable. It does not open
PostgreSQL, mutate a database, or call live DWS.

## Automation

Use `automation/morning_prompt.md` for the morning automation and `automation/evening_prompt.md` for the evening automation. The evening prompt explicitly invokes `$kmfa-dingtalk-attendance-skill` and runs stage-2 only when eligible.
