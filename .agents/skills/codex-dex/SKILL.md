---
name: codex-dex
description: >
  Mandatory governed software-development workflow for building, implementing,
  debugging, refactoring, changing model or business behavior, preparing
  releases, or completing multi-file engineering tasks. Use for FULL_CODEX_DEV
  and IMPLEMENTATION_ONLY work. Do not use for read-only Q&A, translation,
  summaries, or pure typo-only edits.
---

# Codex Dex - Governed Software Development

Use this skill for non-trivial CodexProject implementation work. It does not
replace `AGENTS.md` or `docs/governance/STANDARD.md`; it operationalizes them
for a single bounded run.

## Mandatory Governance Gate

For every applicable run, resolve or create:

- `PROJECT_PATH`
- `TASK_ID`
- `ACCEPTANCE_ID`
- current product version
- current model version
- current parameter profile
- current phase and gate

New IDs may initially be `proposed`; they must not be marked `completed`
without evidence.

## Preflight

Before editing, output:

- objective
- scope and non-scope
- files to inspect
- files likely to change
- focused test commands
- governance validation command
- risks
- rollback
- stop conditions

Begin with a bounded PLAN / READ-ONLY pass unless the user has already provided
a narrow implementation contract.

## Canonical Governance

For behavior-changing work, update the applicable files:

- `MODEL_SPEC.md`
- `model_registry.yaml`
- `formula_registry.yaml`
- `parameter_registry.csv`
- `DEVELOPMENT_LEDGER.md`
- `development_events.jsonl`
- `DELIVERY_PLAN.md`
- `delivery_tasks.yaml`
- `VERSION_MATRIX.yaml`
- `TRACEABILITY_MATRIX.csv`
- `VERSION`
- `CHANGELOG.md`

Do not create duplicate editable fact sources. Keep legacy files as indexes or
compatibility entries when needed.

## Model Documentation

Each active model must define:

- stable model ID
- purpose
- assumptions
- inputs and outputs
- exact formula or exact pseudocode
- variable names, types, and units
- normalization
- constraints
- missing-data behavior
- fallback
- failure conditions
- implementation reference
- test reference
- validation metrics

Each active parameter must distinguish:

- default value
- initial or prior value
- active value
- calibrated value
- range
- weight and weight group
- source or rationale
- calibration method
- sensitivity
- code/config/test references

Use `UNKNOWN` only with a concrete unresolved task. Use `NOT_APPLICABLE` only
with evidence.

## Development Ledger

Never derive iteration count from Git commit count.

Separate:

- confirmed iterations
- reconstructed development events
- unknown historical periods

Every event is append-only and records:

- version before and after
- task and acceptance IDs
- objectives
- changed files
- model and parameter deltas
- commands
- observed test results
- decisions
- failures
- risks
- rollback
- next task

## Completion Gate

Before reporting completion, run:

```bash
python scripts/validate_project_governance.py --project "$PROJECT_PATH"
```

Then run the smallest relevant focused tests.

If either fails:

- do not mark the task completed
- keep status `in_progress` or `blocked`
- perform at most three focused repair loops
- report the real failure if still unresolved

For root governance changes, run:

```bash
python scripts/validate_project_governance.py --all
python -m unittest discover -s tests/governance -p 'test_*.py' -q
```

## Final Response

Report:

- diff summary
- model delta
- formula and parameter delta
- version delta
- task and acceptance delta
- commands actually run
- observed results
- remaining risks
- rollback path
- next single task
