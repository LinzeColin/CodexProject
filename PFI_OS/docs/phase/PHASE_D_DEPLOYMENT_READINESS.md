# Phase D Deployment Readiness

Schema: `PFIOSPhaseDDeploymentReadinessContractV1`

Status: first Phase D local-readiness slice complete.

As of: 2026-06-20 Australia/Sydney

## Goal

Establish a read-only deployment readiness contract before real backup,
restore, service-launch, local-model, or Phase 5 packaging work begins.

## Current Slice

- Adds `pfi_os.application.deployment_readiness`.
- Declares read model schema `PFIOSPhaseDLocalDeploymentReadinessV1`.
- Checks required local deployment surfaces:
  `pyproject.toml`, `web/index.html`,
  `src/pfi_os/application/operational_store.py`, `scripts/startPFIOS.sh`,
  `scripts/statusPFIOS.sh`, and `macos/PFI_OS.app`.
- Verifies `$PFI_OS_DATA_HOME` and Operational SQLite resolve outside public
  Git, with Operational SQLite under
  `$PFI_OS_DATA_HOME/private/operational/pfi.sqlite`.
- Declares backup and restore target paths under
  `$PFI_OS_DATA_HOME/runtime/backups` and
  `$PFI_OS_DATA_HOME/runtime/restore_staging`.
- Confirms this readiness check creates no directories, starts no services,
  performs no network/model/provider calls, and does not mutate holdings.
- Keeps `DisabledProvider` as the default local-model posture. Optional
  `OllamaProvider` configuration enters `Review` and does not block core
  workflows.

## Contract Tests

- `tests/contract/test_phase_d_deployment_readiness.py`

The tests verify:

1. Contract fields, required repo surfaces, local-model policy, backup/restore
   policy, and safety boundary.
2. A minimal local project with data home outside the repo passes readiness
   without creating backup or restore directories.
3. Missing deployment surfaces and repo-local data home fail closed to
   `Blocked`.
4. Optional local model settings remain non-blocking and perform no network
   probe.

## Out Of Scope

- Creating backups.
- Restoring from backups.
- Starting or stopping local services.
- Installing or codesigning macOS apps.
- Probing Ollama or any model endpoint.
- Docker or cloud deployment.
- Phase 5 final acceptance package.

## Next Iterations

1. Add real backup and restore acceptance evidence using private/runtime
   paths outside Git.
2. Add local macOS deployment acceptance only when the release gate requires a
   controlled service start.
3. Build the Phase 5 acceptance package for Phase 6 deployment preparation.
