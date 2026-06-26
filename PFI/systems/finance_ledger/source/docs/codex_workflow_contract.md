# Codex Workflow Contract

## Purpose

This contract defines how future Codex agents should inspect, modify, validate, and hand off this Consumption Analysis System.

The goal is not to create more files for its own sake. The goal is to keep the local ledger system reproducible, auditable, low-risk, and useful as a data source for the wider personal research platform.

## Current Authority Order

When continuing work, use this authority order:

1. Newest user instruction.
2. Current files and command outputs.
3. `HANDOFF.md`.
4. `AGENTS.md`.
5. `README.md`.
6. Docs and historical reports.

If a `system_upgrade_taskpack` or upgrade-total-report file is not present in this project, do not fabricate one. Treat the active goal, `HANDOFF.md`, current files, and generated audit artifacts as the current authority until the user provides the missing file.

## Workflow

Each run must have one clear objective.

1. Intake: read `HANDOFF.md`, `AGENTS.md`, relevant docs, and relevant code.
2. Scope: state the one objective and confirm no production amount/category rule changes are intended unless explicitly required.
3. Implement: make focused changes only.
4. Validate: run targeted checks, then broader checks when risk justifies it.
5. Document: update README/docs/HANDOFF only when they materially improve future continuity.
6. Report: end with a Run Contract.

## Required Gates

Use these gates depending on the change type:

| Change Type | Minimum Validation |
|---|---|
| Workflow/docs only | `python3 scripts/doctor.py` and targeted tests |
| Ledger/report output changes | `scripts/weekly_update.py`, `scripts/validate_outputs.py --require-ledger`, targeted tests |
| Browser/UI changes | browser visual acceptance or documented headless substitute |
| Delivery packaging | `scripts/finalize_delivery.py` or documented final gate equivalent |

## Fail-Closed Rules

- Missing source data stays missing; do not infer real bills.
- Missing ChatGPT reference files stay `missing`; do not fabricate a comparison source.
- Pending large-review transactions stay outside production totals.
- Failed validation blocks delivery claims.
- Output freshness must be checked before claiming that reports reflect current files.

## Shared Evidence Terms

Evidence layer:

- `FACT`: directly observed current file, database row, command output, or generated artifact.
- `INFERENCE`: derived from facts with stated logic.
- `OBSERVATION`: inspection or heuristic signal that needs confirmation.
- `OPINION`: subjective or preference-level assessment.

Decision grade:

- `Actionable`: enough evidence to proceed with the stated non-money action.
- `Watch`: useful but needs monitoring or follow-up.
- `Observe`: contextual information only.
- `Reject`: do not use until fixed or clarified.

## Standard Paths

```text
Output directory: outputs/finance_ledger_20220605_20260603
Ledger DB: data/finance_ledger/finance_ledger.sqlite
Workflow doctor: scripts/doctor.py
Run contract template: docs/run_contract_template.md
```

## Handoff Update Triggers

Update `HANDOFF.md` when:

- A core layer is completed.
- A report, database schema, command, or gate changes.
- Tests or validation results materially change.
- A blocker is discovered or resolved.
- A future agent would waste time without the new state.

Do not paste long logs into `HANDOFF.md`. Record the command, result, affected files, and key evidence.
