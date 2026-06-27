# PFI Big Data Simulator Changelog

## 0.1.0 - 2026-06-24

- Added Other8 S3PCT02 lifecycle evidence for bounded multiprocessing, temporary cache, SQLite import/export/unlink, cancel checkpoints and resume idempotence.
- `run_task_manifest` now supports an optional `cancel_after_tasks` checkpoint and writes `run_control.json`; default behavior is unchanged.
- SQLite warehouse helpers now explicitly close connections so temporary database files can be cleaned up on Windows.
- Strategy validity, live account readiness, production QuantLab writes and large pressure runs remain out of scope and unapproved.

## 0.1.0 - 2026-06-20

- Governance-only baseline: created canonical model, formula, parameter, development, delivery, version and traceability files under `docs/governance/`.
- Product version is provisional and follows existing `QUANTLAB_INTEGRATION_CONTRACT.json` version evidence.
- No `qbvs` source, model runtime logic, trading behavior, data generation logic or product feature behavior changed.
- Calibration/source rationale gaps remain tracked by `TASK-PFI-B-001` through `TASK-PFI-B-010`.
- PFI_BIG_DATA_SIMULATOR governance was validated and promoted from advisory to required in `governance/projects.yaml`; focused tests passed with `32 passed`.
