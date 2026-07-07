# Implementation README

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

## Automation

Use `automation/morning_prompt.md` for the morning automation and `automation/evening_prompt.md` for the evening automation. The evening prompt explicitly invokes `$kmfa-dingtalk-attendance-skill` and runs stage-2 only when eligible.
