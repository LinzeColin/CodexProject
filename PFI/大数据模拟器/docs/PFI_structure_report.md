# PFI S5PCT01 Structure Report

task_id: `S5PCT01`
acceptance_id: `ACC-S5PCT01`
project_id: `PFI_BIG_DATA_SIMULATOR`
mode: `BOUNDARY_ONLY_NO_ALGORITHM_CHANGE`

## Owner Summary

S5PCT01 binds the current PFI/QBVS structure into explicit layers:

- Active QBVS package: `PFI/大数据模拟器/qbvs/`
- Config layer: `PFI/大数据模拟器/config/`
- Test layer: `PFI/大数据模拟器/tests/`
- Root contracts and handoff: `QUANTLAB_INTEGRATION_CONTRACT.json`,
  `HANDSHAKE_PROTOCOL.json`, `HANDOFF.md`, `BACKUP_MANIFEST.md`
- Date-stamped generator scripts: `PFI/大数据模拟器/tools/`
- Output/evidence layers: `PFI/大数据模拟器/runs/` and
  `PFI/大数据模拟器/reports/`

No files are moved in S5PCT01. The existing Wave 2 manifest records 42 PFI
archive/merge candidates: 40 `ARCHIVE` and 2 `MERGE`. Those candidates remain
checksum-bound by `governance/stage_gates/s5pa/wave2_archive_manifest.json`.

## Boundary Decisions

- `qbvs/` remains the only default active runtime package.
- `config/` may feed `qbvs/` commands, but does not contain runtime algorithms.
- `tests/` verifies lifecycle and active runtime behavior.
- Root contracts describe QuantLab read-only interoperability and recovery.
- Date-stamped tools are report or handoff generators; S5PCT01 does not rewrite
  their logic and does not make them default runtime entries.
- `runs/` and `reports/` are output/evidence layers and are not source truth
  for strategy, backtest, cache, warehouse, or adapter algorithms.

## Smoke Evidence

- `python -B -m pytest "PFI/大数据模拟器/tests" -q`: `NOT_RUN`, local Python
  environments do not include `pytest`.
- `python -B -m unittest tests.test_s3pct02_lifecycle -q`: `PASS`, 1 test OK.
- Active `qbvs/` direct smoke: `PASS`, generated 240 strategy specs, ran
  backtest/buy-hold, and created/refreshed one OHLCV cache index.

Result: `PASS_WITH_PYTEST_ENV_BLOCKER_RECORDED`.

## Stop Conditions

- PFI date-stamped script integration changes algorithm: `false`
- Root contracts used as active algorithm source: `false`
- `runs/` or `reports/` imported as source truth by default: `false`
- `qbvs/` active runtime path changed: `false`
- Archive written or files moved: `false`

## Rollback

Rollback is documentation/governance-only: remove the S5PCT01 report, contract,
smoke log, run manifest, README/AGENTS boundary text, and S5PCT01 governance
test. Because no runtime files, generated outputs, or PFI artifacts are moved,
git restore is sufficient.
