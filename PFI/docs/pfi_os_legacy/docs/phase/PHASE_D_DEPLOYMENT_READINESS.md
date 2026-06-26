# Phase D Deployment Readiness

Schema: `PFIOSPhaseDDeploymentReadinessContractV1`

Status: deployment readiness and backup/restore acceptance complete.

As of: 2026-06-20 Australia/Sydney

## Goal

Establish a local deployment readiness contract, then prove backup/restore
acceptance without committing private SQLite, runtime manifests, local logs, or
absolute local paths to public Git.

## Deployment Readiness Slice

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

## Backup/Restore Acceptance Slice

- Adds `pfi_os.application.deployment_backup_restore`.
- Declares contract schema `PFIOSPhaseDBackupRestoreContractV1`.
- Declares acceptance schema `PFIOSPhaseDBackupRestoreAcceptanceV1`.
- Requires existing Operational SQLite at
  `$PFI_OS_DATA_HOME/private/operational/pfi.sqlite`.
- Writes backup SQLite only under `$PFI_OS_DATA_HOME/runtime/backups`.
- Restores into staging only under
  `$PFI_OS_DATA_HOME/runtime/restore_staging`.
- Writes a private manifest outside Git with checksums, byte sizes, official
  Operational Store table counts, and `commit_to_git: false`.
- Exposes only a sanitized public summary with `$PFI_OS_DATA_HOME` scoped paths,
  no absolute local paths, no private holdings, and no raw SQLite content.
- Verifies SQLite `PRAGMA integrity_check` and official table row-count parity
  between source, backup, and restore.
- Does not mutate Operational SQLite, holdings, providers, brokers, orders,
  services, or model endpoints.

## Contract Tests

- `tests/contract/test_phase_d_deployment_readiness.py`
- `tests/contract/test_phase_d_backup_restore_acceptance.py`

The tests verify:

1. Contract fields, required repo surfaces, local-model policy, backup/restore
   policy, and safety boundary.
2. A minimal local project with data home outside the repo passes readiness
   without creating backup or restore directories.
3. Missing deployment surfaces and repo-local data home fail closed to
   `Blocked`.
4. Optional local model settings remain non-blocking and perform no network
   probe.
5. Backup/restore acceptance creates private runtime artifacts only under
   `$PFI_OS_DATA_HOME`.
6. Public summaries and private manifests are sanitized for GitHub-safe
   reporting.
7. Missing Operational SQLite and repo-local data homes fail closed without
   creating backup/restore artifacts.

## Out Of Scope

- Starting or stopping local services.
- Installing or codesigning macOS apps.
- Probing Ollama or any model endpoint.
- Docker or cloud deployment.
- Phase 5 final acceptance package.

## Next Iterations

1. Add local macOS deployment acceptance only when the release gate requires a
   controlled service start.
2. Build the Phase 5 acceptance package for Phase 6 deployment preparation.
