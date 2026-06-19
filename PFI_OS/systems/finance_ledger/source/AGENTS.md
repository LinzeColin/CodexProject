# AGENTS.md

## Project

This project is the local Consumption Analysis System / Economic Bleed Ledger.

It imports Alipay and WeChat bill files, builds a local SQLite ledger, generates static HTML workbenches and formal PDF reports, and provides read-only evidence for the wider personal research platform.

## Boundaries

- Do not execute payments, transfers, trades, or any real-money action.
- Do not expose the local HTTP API to the public internet.
- Do not store account passwords, API keys, cookies, or private tokens in the repository.
- Do not change production amount formulas, category rules, review decisions, or source files unless the current task explicitly targets that behavior and tests are updated.
- Ambiguous, missing, high-value, high-risk, or action-linked records must remain reviewable instead of being silently upgraded.

## Required First Reads

For every non-trivial run:

1. Read `HANDOFF.md`.
2. Read this `AGENTS.md`.
3. Inspect the current files that prove the target state.
4. If `HANDOFF.md` conflicts with current files or the newest user instruction, follow current files and the newest user instruction.

## System Layers

The current upgrade sequence is:

1. Data Trust Layer.
2. Reconciliation Layer.
3. Manual Review Queue.
4. Entity Registry and Alias Map.
5. Evidence Classification and Decision Grade.
6. Report Layer.
7. Codex Workflow Layer.
8. Cross-system integration.

Completed layers must remain read-only audit layers unless a specific task says otherwise.

## Standard Commands

Run a lightweight workflow check:

```bash
python3 scripts/doctor.py
```

Run the workflow check plus output validation:

```bash
python3 scripts/doctor.py --require-output
```

Run the weekly rebuild with explicit paths:

```bash
python3 scripts/weekly_update.py \
  --input data/finance_ledger/sources \
  --ledger-db data/finance_ledger/finance_ledger.sqlite \
  --output outputs/finance_ledger_20220605_20260603
```

Validate current outputs and ledger:

```bash
python3 scripts/validate_outputs.py \
  --output outputs/finance_ledger_20220605_20260603 \
  --db data/finance_ledger/finance_ledger.sqlite \
  --require-ledger
```

Run tests:

```bash
PYTHONPATH=src python3 -m pytest tests -q
```

## Run Contract

Every run that edits files must end with:

- Objective.
- Files changed.
- Key decisions.
- Validation commands and results.
- Generated outputs.
- Risks and unresolved issues.
- Rollback suggestion.
- Progress percentage.
- Remaining tasks.
- Estimated remaining time and run count.

Use `docs/run_contract_template.md` for the exact structure.

## Reporting Rules

- Formal reports should be PDF when practical.
- Markdown, CSV, JSON, SQLite, and HTML are valid support artifacts.
- Any conclusion must state evidence source, evidence layer, decision grade, run time, assumptions, and gaps when applicable.
- If evidence is insufficient, downgrade the conclusion instead of overstating it.

## Cleanup Rules

- It is safe to remove local `__pycache__`, `.pytest_cache`, and temporary test cache directories after validation.
- Do not delete `outputs/`, `data/`, source files, review files, user-uploaded files, or generated reports unless explicitly requested.
