# Automation Contract

## Assumed cadence

The user currently has two daily automations.

| Automation | Purpose | Stage-2 allowed |
|---|---|---:|
| Morning | Freshness, health, gaps, anomaly preview | No |
| Evening | Acquisition, validation, DB ingest, reconciliation, monthly stage-2 | Yes, only on days 1-5 |

## Morning automation instruction

Morning run must set:

```bash
export KMFA_RUN_SLOT=morning
```

Morning run may:

- check repo health
- inspect OneDrive raw freshness
- check previous evening run status
- surface missing data warnings
- create a short status report

Morning run must not:

- perform stage-2 consensus
- mark Q5
- generate payroll baseline candidate acceptance

## Evening automation instruction

Evening run must set:

```bash
export KMFA_RUN_SLOT=evening
```

Evening run may:

- acquire attendance result and detail data
- collect location and trajectory evidence
- ingest database
- run quality gates
- write canonical snapshot
- run `scripts/run_stage2_evening.sh` on eligible days
- generate day-5 consensus certificate if all five runs match

The current portable stage-2 runner is fail-closed:

- If `KMFA_STAGE2_SOURCE_JSON` points to an approved replay snapshot, it writes
  deterministic run artifacts without live DWS or database credentials.
- If `KMFA_STAGE2_SOURCE_MODE=raw_replay_day_fact` and
  `KMFA_STAGE2_RAW_REPLAY_DAY_FACT_DIR` points to a private raw replay
  day-fact/linkage bundle, `scripts/resolve_stage2_source.py` materializes a
  Stage-2 source snapshot in the run folder without live DWS or database
  mutation. The resulting source keeps database commit/verification gates
  false until approved non-production PostgreSQL execution and state
  verification proofs exist.
- To satisfy the database gates, run
  `scripts/prepare_preconsensus_postgres_landing_bundle.py`, generate and
  guard-execute the PostgreSQL load plan against a non-production target, run
  `scripts/verify_postgres_landing_state.py` to confirm post-load row counts,
  then run `scripts/apply_stage2_database_proof.py` to produce the
  DB-verified Stage-2 source used by `scripts/write_stage2_run_artifacts.py`.
- If no DB execution proof or state verification proof is available, keep
  `database_transaction_committed=false` and
  `database_transaction_verified=false`; day-5 consensus must fail closed.
- `scripts/resolve_stage2_source.py` records `source_adapter_status.json` for
  each eligible run, including fail-closed DWS safety status.
- If `KMFA_STAGE2_SOURCE_MODE=dws_live` is set but `KMFA_S19_ALLOW_DWS_COMMANDS`
  and browser policy are not READY, the run exits with
  `STAGE2_ADAPTER_SOURCE_MISSING` before any live call.
- If no approved source adapter is configured, it exits with
  `STAGE2_ADAPTER_SOURCE_MISSING` and must be reported as a blocker.
- A future live materializer may replace the replay source only after explicit
  authorization, validated raw/result/detail coverage, and private archive
  write proof.

## Required explicit skill invocation

Use this in Codex automation prompts:

```text
Use $kmfa-dingtalk-attendance-skill.
```

## Recommended automation output

Automation should report only these fields in the final message:

```text
status: passed | warning | failed
run_slot: morning | evening
target_month: YYYYMM
stage2_eligible: true | false
stage2_status: not_eligible | pending | accepted | failed
canonical_hash: sha256:...
quality_grade: Q0-Q5
P0/P1 unresolved: N/N
next_action: ...
```

## Non-interactive runner option

If using Codex CLI instead of app automation, wrap the evening prompt with `codex exec` and JSON output. Store final machine-readable results in `private_runtime/automation_runs/`.
