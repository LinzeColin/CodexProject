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
- run stage-2 on eligible days
- generate day-5 consensus certificate if all five runs match

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
