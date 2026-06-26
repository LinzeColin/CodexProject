# AI-Research-System Codex Workflow Layer

## Purpose

Codex Workflow Layer makes AI-Research-System easier to continue across future Codex runs, other agents, and automation contexts.

It provides:

- Project-level `AGENTS.md`.
- Explicit Run Contract.
- Read-only `doctor.py` health check.
- Non-networked `setup.sh`.
- Fixed `Makefile` validation targets.
- Formal workflow doctor PDF output.
- Audit stack coverage through Report Layer.

This layer improves reliability, auditability, and context efficiency. It does not change business logic, reports, evidence classification, data refresh, or trading boundaries.

## Files

| File | Role |
| --- | --- |
| `AGENTS.md` | Project-specific Codex instructions and safety boundaries. |
| `docs/RunContract.md` | Per-run execution contract and completion criteria. |
| `doctor.py` | Read-only workflow health check with JSON output and optional PDF report. |
| `setup.sh` | Creates required local folders and runs doctor; no package install or external refresh. |
| `Makefile` | Stable command shortcuts for doctor, tests, audit stack, and cleanup. |
| `docs/CodexWorkflowLayer.md` | Human-readable documentation for this layer. |
| `docs/ReportLayer.md` | Report Layer gate and formal report downgrade policy. |

## Commands

Initial local check:

```bash
./setup.sh 2026-06-06
```

Doctor:

```bash
python3 doctor.py --date 2026-06-06 --json
python3 doctor.py --date 2026-06-06 --write-report --json
make doctor DATE=2026-06-06
```

Audit stack:

```bash
make audit-stack DATE=2026-06-06
```

Current stack order:

1. `data-trust-audit`
2. `reconciliation-audit`
3. `manual-review-audit`
4. `entity-registry-audit`
5. `evidence-decision-audit`
6. `report-layer-audit`
7. `doctor --write-report`

Tests:

```bash
make test-monitoring
make test
```

Cleanup:

```bash
make clean-cache
```

## Doctor Checks

`doctor.py` checks:

- Required workflow files.
- Python version.
- Required runtime modules.
- Existence of major CLI commands.
- Existence of system audit artifacts for the selected date.
- Script executability.

Status logic:

- `Pass`: all checks pass.
- `Review`: non-blocking warnings exist.
- `Blocked`: required `P0` checks fail.

`doctor.py` is read-only unless `--write-report` is used. With `--write-report`, it writes only its own audit bundle to:

```text
data/report_artifacts/system_audit/
```

## Formal Outputs

Workflow doctor output bundle:

- `codex_workflow_doctor_YYYY-MM-DD.json`
- `codex_workflow_doctor_YYYY-MM-DD.md`
- `codex_workflow_doctor_YYYY-MM-DD.pdf`

The PDF is a formal workflow audit report. JSON is the machine-readable source.

Report Layer output bundle:

- `report_layer_audit_YYYY-MM-DD.json`
- `report_layer_audit_YYYY-MM-DD.csv`
- `report_layer_audit_YYYY-MM-DD.md`
- `report_layer_audit_YYYY-MM-DD.pdf`

## Safety Boundaries

This layer must not:

- Open moomoo, browser pages, or external apps.
- Refresh OpenD, policy bridge, PFIOS, ResearchBus, or Alipay data.
- Generate live trading instructions.
- Modify historical report content.
- Suppress existing `Reject`, `Watch`, `OBSERVATION`, or manual-review items.

## Current 2026-06-06 Acceptance

Minimum acceptance for this layer:

- `AGENTS.md` exists.
- `docs/RunContract.md` exists.
- `docs/CodexWorkflowLayer.md` exists.
- `docs/ReportLayer.md` exists.
- `doctor.py --date 2026-06-06 --json` runs.
- `make test-monitoring` passes.
- `make test` passes.
- `make audit-stack DATE=2026-06-06` produces `report_layer_audit_2026-06-06.pdf`.
- `doctor.py --date 2026-06-06 --write-report --json` creates a valid PDF.
