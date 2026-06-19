# Release Checklist

Release candidate requirements:

- `make verify` passes.
- `make verify-g2-db` passes in an environment with Docker/PostgreSQL.
- Required GitHub status checks pass:
  - `EEI validation / verify`
  - `governance-validation / validate`
  - `governance-validation / visual-validation`
- `manifest.txt`, `DIRECTORY_TREE.txt` and `CHECKSUMS.sha256` are regenerated when package files change.
- `sha256sum -c CHECKSUMS.sha256` passes when the checksum file is present.
- `data/task_backlog.csv`, `data/acceptance_matrix.csv`, `data/acceptance_traceability.csv`, `data/development_status_ledger.csv` and `data/risk_control_traceability.csv` are synchronized.
- Every release note cites task IDs, Acceptance IDs, commands, CI run IDs and rollback steps.
- Fixture-only data, synthetic evidence and missing live-data coverage are explicitly disclosed.
- The rollback path is documented for migrations, catalog changes, model changes and UI deployments.
