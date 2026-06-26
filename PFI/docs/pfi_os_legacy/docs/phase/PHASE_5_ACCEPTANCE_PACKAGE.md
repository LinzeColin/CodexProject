# Phase 5 Acceptance Package

Schema: `PFIOSPhase5AcceptancePackageV1`

Status: engineering package complete; user walk-through materials remain
external to public Git.

As of: 2026-06-20 Australia/Sydney

## Goal

Provide a GitHub-safe Phase 5 handoff package for Phase 6 deployment on the
next Mac without committing private runtime data, SQLite backups, local logs,
account identifiers, raw holdings, model caches, or secrets.

## Package Contents

- Product contract files: product constitution, information architecture,
  feature disposition, data boundaries, source-of-truth, UX contract, Web Shell
  acceptance, target architecture, and legacy migration archive.
- Development record: completed work, open backlog, key file map, model
  contracts, data/security contracts, and verification commands.
- Phase records: Phase A data foundation and audit, Phase B vertical workflow
  records, Phase C workflow runtime, Phase D deployment readiness and
  backup/restore acceptance.
- Runtime contracts: Operational Store, deployment readiness,
  backup/restore acceptance, Phase 5 package builder, Web Shell, start/status
  scripts, and `PFI_OS.app` source bundle.
- Contract tests: product contracts, Phase D readiness, Phase D backup/restore,
  and Phase 5 package tests.

## Validation Evidence

- `python -m pytest tests/test_pfi_product_contracts.py -q` -> 8 passed.
- `python -m pytest tests/contract/test_phase_d_deployment_readiness.py
  tests/contract/test_phase_d_backup_restore_acceptance.py -q` -> 10 passed.
- `python -m pytest tests/contract/test_phase_c_workflow_runtime_scheduler.py
  tests/contract/test_phase_c_workflow_runtime_read_model.py -q` -> 10 passed.
- `python -m pytest tests/contract/test_pfi_web_shell_contract.py
  tests/e2e/test_pfi_web_shell_static_flow.py
  tests/visual/test_pfi_web_shell_visual_baseline.py -q` -> 19 passed.
- `python -m compileall src/pfi_os/application src/pfi_os/app/streamlit_app.py` -> passed.
- `git diff --check` -> passed.
- Backup/restore smoke with temporary `$PFI_OS_DATA_HOME` -> Pass, no failed
  checks, manifest written, official table counts matched, public summary did
  not leak the temporary path, and `commit_to_git=false`.

## Phase 6 Preparation

Phase 6 should start from the GitHub draft PR branch and recreate private
runtime data on the target Mac:

- Public code/docs/tests: `LinzeColin/CodexProject/PFI_OS`.
- Private data root: `$PFI_OS_DATA_HOME`.
- Operational SQLite:
  `$PFI_OS_DATA_HOME/private/operational/pfi.sqlite`.
- Backup scope: `$PFI_OS_DATA_HOME/runtime/backups`.
- Restore staging scope: `$PFI_OS_DATA_HOME/runtime/restore_staging`.
- Default model provider: `DisabledProvider`.
- Optional local model provider: `OllamaProvider`, only after hardware/disk
  audit and never inside the Fast Path.

The following materials must stay external to public Git until the target Mac
deployment run supplies sanitized fixtures or private local paths:

- Local repository backup.
- Hardware and disk audit.
- Sanitized test holdings.
- Representative symbols and policy/government documents.
- Fast Path target source list.
- Four workflow walk-through examples.
- User subjective acceptance score.

## Safety Boundary

- Research-only and human-reviewed.
- No live trading.
- No autonomous order execution.
- No broker calls from package generation.
- No payment, bank, betting, or account mutation.
- No holdings mutation.
- No service start.
- No network call.
- No private runtime artifacts committed to public Git.

## Known Gaps

- Controlled local deployment acceptance is deferred unless the release gate
  requires real service start/stop evidence.
- User subjective MVP acceptance remains external and must be collected during
  the target-Mac walk-through.
